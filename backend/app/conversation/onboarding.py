"""
Fluxo de onboarding para novos usuários.

onboarding_step possíveis:
  "aguardando_nome"                  → bot perguntou o nome, esperando texto
  "selecionando_habitos:<keys>"      → exibindo lista de hábitos; keys = selecionados (csv)
                                        keys podem ser uma chave de DEFAULT_HABITS ou "custom:<nome>"
  "aguardando_outro_habito:<keys>"   → esperando o nome de um hábito personalizado digitado
"""

from sqlalchemy.orm import Session

from ..models.models import Usuario
from ..services import usuario_service
from ..utils import truncar
from ..whatsapp.client import whatsapp

# Hábitos selecionáveis no onboarding — o usuário escolhe quais quer acompanhar.
DEFAULT_HABITS: list[dict] = [
    {"key": "academia",     "nome": "Academia",                  "categoria": "Saúde do corpo",   "emoji": "🏋️"},
    {"key": "aerobico",     "nome": "Exercício aeróbico",         "categoria": "Saúde do corpo",   "emoji": "🏃"},
    {"key": "alimentacao",  "nome": "Alimentação saudável",       "categoria": "Saúde do corpo",   "emoji": "🥗"},
    {"key": "agua",         "nome": "Consumo de água",            "categoria": "Saúde do corpo",   "emoji": "💧"},
    {"key": "estudar",      "nome": "Estudar/Cursos",             "categoria": "Evolução pessoal", "emoji": "📚"},
    {"key": "leitura",      "nome": "Leitura",                    "categoria": "Evolução pessoal", "emoji": "📖"},
    {"key": "organizacao",  "nome": "Organização/produtividade",  "categoria": "Evolução pessoal", "emoji": "🎯"},
    {"key": "meditacao",    "nome": "Meditação",                  "categoria": "Bem-estar",        "emoji": "🧘"},
    {"key": "gratidao",     "nome": "Gratidão/diário",            "categoria": "Bem-estar",        "emoji": "📝"},
    {"key": "ar_livre",     "nome": "Tempo ao ar livre",          "categoria": "Bem-estar",        "emoji": "☀️"},
    {"key": "social",       "nome": "Tempo com família/amigos",   "categoria": "Lazer",            "emoji": "👨‍👩‍👧"},
    {"key": "intimidade",   "nome": "Vida íntima",                "categoria": "Lazer",            "emoji": "❤️"},
]

# Métricas criadas automaticamente para todo usuário — não são selecionáveis.
DEFAULT_METRICS: list[dict] = [
    {"nome": "Humor ao acordar",       "tipo": "nota",          "emoji": "📊"},
    {"nome": "Hora que acordou",       "tipo": "hora",          "emoji": "⏰"},
    {"nome": "Hora que foi dormir",    "tipo": "hora_anterior", "emoji": "⏰"},
    {"nome": "Humor antes de dormir",  "tipo": "nota",          "emoji": "📊"},
]

EMOJI_HABITO_PERSONALIZADO = "⭐"


def iniciar(session: Session, phone: str) -> None:
    """Chamado quando um número novo manda a primeira mensagem."""
    usuario_service.criar_usuario(session, phone)
    whatsapp.send_text(
        phone,
        "Olá! 👋 Bem-vindo ao seu rastreador de hábitos pessoais.\n\nPrimeiro, qual é o seu nome?",
    )


def processar_nome(session: Session, usuario: Usuario, texto: str) -> None:
    nome = texto.strip()[:100]
    usuario.nome = nome
    usuario.onboarding_step = "selecionando_habitos:"
    session.commit()
    _enviar_lista_habitos(usuario.phone, selecionados=[])


def processar_selecao(session: Session, usuario: Usuario, payload: str) -> None:
    """payload: 'onboarding_toggle_<key>' | 'onboarding_outro' | 'onboarding_confirmar'"""
    selecionados = _extrair_selecionados(usuario.onboarding_step)

    if payload == "onboarding_confirmar":
        _finalizar(session, usuario, selecionados)
        return

    if payload == "onboarding_outro":
        usuario.onboarding_step = "aguardando_outro_habito:" + ",".join(selecionados)
        session.commit()
        whatsapp.send_text(usuario.phone, "Digite o nome do hábito personalizado:")
        return

    key = payload.removeprefix("onboarding_toggle_")
    if key in selecionados:
        selecionados.remove(key)
    else:
        selecionados.append(key)

    usuario.onboarding_step = "selecionando_habitos:" + ",".join(selecionados)
    session.commit()
    _enviar_lista_habitos(usuario.phone, selecionados)


def processar_outro_habito(session: Session, usuario: Usuario, texto: str) -> None:
    """Chamado quando o usuário digita o nome de um hábito personalizado."""
    selecionados = _extrair_selecionados(usuario.onboarding_step, prefixo="aguardando_outro_habito:")
    nome = texto.strip().replace(",", "")[:80]

    if not nome:
        whatsapp.send_text(usuario.phone, "Nome inválido. Digite o nome do hábito:")
        return

    selecionados.append(f"custom:{nome}")
    usuario.onboarding_step = "selecionando_habitos:" + ",".join(selecionados)
    session.commit()
    whatsapp.send_text(usuario.phone, f"'{nome}' adicionado! ⭐")
    _enviar_lista_habitos(usuario.phone, selecionados)


def _finalizar(session: Session, usuario: Usuario, selecionados: list[str]) -> None:
    if not selecionados:
        whatsapp.send_text(usuario.phone, "Selecione ao menos um hábito antes de confirmar. 😊")
        _enviar_lista_habitos(usuario.phone, selecionados)
        return

    habitos_finais = []
    for h in DEFAULT_HABITS:
        if h["key"] in selecionados:
            habitos_finais.append({"nome": h["nome"], "tipo": "bool", "emoji": h["emoji"]})
    for key in selecionados:
        if key.startswith("custom:"):
            habitos_finais.append({
                "nome": key.removeprefix("custom:"), "tipo": "bool", "emoji": EMOJI_HABITO_PERSONALIZADO,
            })

    usuario_service.criar_habitos(session, usuario.id, habitos_finais)
    usuario_service.criar_habitos(session, usuario.id, DEFAULT_METRICS)
    usuario_service.finalizar_onboarding(session, usuario)

    nomes = ", ".join(h["nome"] for h in habitos_finais)
    whatsapp.send_text(
        usuario.phone,
        f"Perfeito, {usuario.nome}! 🎉\n\nVou acompanhar: {nomes}.\n\n"
        "Suas métricas de humor e sono já estão configuradas automaticamente.\n\n"
        "Mande *iniciar* a qualquer momento para registrar seu dia.",
    )


def _extrair_selecionados(step: str, prefixo: str = "selecionando_habitos:") -> list[str]:
    _, _, keys_csv = (step or prefixo).partition(prefixo)
    return [k for k in keys_csv.split(",") if k]


def _enviar_lista_habitos(phone: str, selecionados: list[str]) -> None:
    categorias: dict[str, list[dict]] = {}
    for h in DEFAULT_HABITS:
        categorias.setdefault(h["categoria"], []).append(h)

    sections = []
    for nome_categoria, habitos in categorias.items():
        rows = []
        for h in habitos:
            check = "✅" if h["key"] in selecionados else "⬜"
            rows.append({
                "id": f"onboarding_toggle_{h['key']}",
                "title": truncar(f"{check} {h['emoji']} {h['nome']}", 24),
                "description": "Clique para selecionar/remover",
            })
        sections.append({"title": nome_categoria, "rows": rows})

    customizados = [k.removeprefix("custom:") for k in selecionados if k.startswith("custom:")]
    outro_desc = f"{len(customizados)} adicionado(s): {', '.join(customizados)}" if customizados else "Adicionar um hábito que não está na lista"
    sections.append({
        "title": "Personalizado",
        "rows": [{"id": "onboarding_outro", "title": "➕ Outro hábito", "description": truncar(outro_desc, 72)}],
    })

    n = len(selecionados)
    sections.append({
        "title": "Ação",
        "rows": [{
            "id": "onboarding_confirmar",
            "title": "✅ Confirmar seleção",
            "description": f"{n} hábito(s) selecionado(s)",
        }],
    })

    whatsapp.send_list(
        phone,
        header="Seus hábitos",
        body="Selecione os hábitos que quer acompanhar. Clique em um item para marcar/desmarcar.",
        button_label="Ver opções",
        sections=sections,
    )
