"""
Fluxo de onboarding para novos usuários.

onboarding_step possíveis:
  "aguardando_nome"              → bot perguntou o nome, esperando texto
  "selecionando_habitos:<keys>"  → exibindo lista de hábitos; keys = selecionados (csv)
"""

from sqlalchemy.orm import Session

from ..models.models import Usuario
from ..services import usuario_service
from ..utils import truncar
from ..whatsapp.client import whatsapp

DEFAULT_HABITS: list[dict] = [
    {"key": "academia",     "nome": "Academia",             "tipo": "bool"},
    {"key": "leitura",      "nome": "Leitura",              "tipo": "bool"},
    {"key": "estudar",      "nome": "Estudar/Cursos",       "tipo": "bool"},
    {"key": "alimentacao",  "nome": "Alimentação saudável", "tipo": "bool"},
    {"key": "agua",         "nome": "Consumo de água",      "tipo": "bool"},
    {"key": "aerobico",     "nome": "Exercício aeróbico",   "tipo": "bool"},
    {"key": "meditacao",    "nome": "Meditação",            "tipo": "bool"},
    {"key": "humor_manha",  "nome": "Humor (manhã)",        "tipo": "nota"},
    {"key": "hora_acordar", "nome": "Hora de acordar",      "tipo": "hora"},
]


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
    """payload: 'onboarding_toggle_<key>' ou 'onboarding_confirmar'"""
    step = usuario.onboarding_step or "selecionando_habitos:"
    _, _, keys_csv = step.partition("selecionando_habitos:")
    selecionados = [k for k in keys_csv.split(",") if k]

    if payload == "onboarding_confirmar":
        if not selecionados:
            whatsapp.send_text(usuario.phone, "Selecione ao menos um hábito antes de confirmar. 😊")
            _enviar_lista_habitos(usuario.phone, selecionados)
            return
        habitos_finais = [h for h in DEFAULT_HABITS if h["key"] in selecionados]
        usuario_service.criar_habitos(session, usuario.id, habitos_finais)
        usuario_service.finalizar_onboarding(session, usuario)
        nomes = ", ".join(h["nome"] for h in habitos_finais)
        whatsapp.send_text(
            usuario.phone,
            f"Perfeito, {usuario.nome}! 🎉\n\nVou acompanhar: {nomes}.\n\n"
            "Mande *iniciar* a qualquer momento para registrar seu dia.",
        )
        return

    # toggle
    key = payload.removeprefix("onboarding_toggle_")
    if key in selecionados:
        selecionados.remove(key)
    else:
        selecionados.append(key)

    usuario.onboarding_step = "selecionando_habitos:" + ",".join(selecionados)
    session.commit()
    _enviar_lista_habitos(usuario.phone, selecionados)


def _enviar_lista_habitos(phone: str, selecionados: list[str]) -> None:
    rows = []
    for h in DEFAULT_HABITS:
        emoji = "✅" if h["key"] in selecionados else "⬜"
        rows.append({
            "id": f"onboarding_toggle_{h['key']}",
            "title": truncar(f"{emoji} {h['nome']}", 24),
            "description": "Clique para selecionar/remover",
        })

    n = len(selecionados)
    sections = [
        {"title": "Hábitos disponíveis", "rows": rows},
        {
            "title": "Ação",
            "rows": [{
                "id": "onboarding_confirmar",
                "title": "✅ Confirmar seleção",
                "description": f"{n} hábito(s) selecionado(s)",
            }],
        },
    ]
    whatsapp.send_list(
        phone,
        header="Seus hábitos",
        body="Selecione os hábitos que quer acompanhar. Clique em um item para marcar/desmarcar.",
        button_label="Ver opções",
        sections=sections,
    )
