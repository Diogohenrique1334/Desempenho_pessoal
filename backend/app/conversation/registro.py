"""
Fluxo de registro diário de hábitos e métricas, seletor de dia e gerenciamento de hábitos.

Convenções de status_conversa (guardado no Registro mais recente do usuário):
  "aguardando_{habito_id}_{dia_iso}"        → esperando texto de uma métrica (nota/hora)
  "aguardando_data_livre"                   → esperando o usuário digitar uma data
  "criando_habito_nome##{dia_iso}"          → esperando o nome do novo hábito
  "criando_habito_tipo##{dia_iso}##{nome}"  → esperando clique no tipo do novo hábito
"""

import datetime
import uuid
from typing import List
from sqlalchemy.orm import Session

from ..models.models import HabitoConfig, Registro, Usuario
from ..services import registro_service, usuario_service
from ..utils import data_hoje_brasil, dia_label, parse_data_usuario, truncar
from ..whatsapp.client import whatsapp

_DIAS_NO_SELETOR = 8
_SEP = "##"


# --- seletor de dia ---

def menu_seletor_dia(session: Session, phone: str, usuario_id: uuid.UUID) -> None:
    hoje = data_hoje_brasil()
    rows = []
    for i in range(_DIAS_NO_SELETOR):
        dia = hoje - datetime.timedelta(days=i)
        emoji = "✅" if registro_service.dia_tem_dados(session, usuario_id, dia) else "⬜️"
        rows.append({
            "id": f"dia_{dia.isoformat()}",
            "title": truncar(f"{emoji} {dia_label(dia, hoje)}", 24),
            "description": dia.strftime("%d/%m/%Y"),
        })
    rows.append({"id": "dia_outra_data", "title": "📅 Outra data", "description": "Digitar uma data específica"})

    whatsapp.send_list(
        phone,
        header="Diário",
        body="Para qual dia você quer registrar?",
        button_label="Selecionar dia",
        sections=[{"title": "Últimos dias", "rows": rows}],
    )


def pedir_data_livre(session: Session, phone: str, usuario_id: uuid.UUID) -> None:
    registro = registro_service.get_or_create_registro(session, usuario_id, data_hoje_brasil())
    registro_service.set_status_conversa(session, registro, "aguardando_data_livre")
    whatsapp.send_text(phone, "Digite a data (ex: 05/06 ou 05/06/2025):")


def processar_data_livre(session: Session, phone: str, usuario: Usuario, texto: str) -> None:
    hoje = data_hoje_brasil()
    try:
        dia = parse_data_usuario(texto, ano_padrao=hoje.year)
        if dia > hoje:
            raise ValueError("data no futuro")
    except ValueError:
        whatsapp.send_text(phone, "Data inválida ou no futuro. Tente novamente (ex: 05/06):")
        return

    registro_hoje = registro_service.get_or_create_registro(session, usuario.id, hoje)
    registro_service.set_status_conversa(session, registro_hoje, None)
    menu_categoria(phone, dia.isoformat())


# --- menu de categoria (Hábitos / Métricas / Gerenciar) ---

def menu_categoria(phone: str, dia_iso: str) -> None:
    dia = datetime.date.fromisoformat(dia_iso)
    hoje = data_hoje_brasil()
    whatsapp.send_buttons(
        phone,
        body=f"O que você quer registrar para *{dia_label(dia, hoje)}*?",
        buttons=[
            {"title": "💪 Hábitos",   "payload": f"menu_habitos_{dia_iso}"},
            {"title": "📊 Métricas",  "payload": f"menu_metricas_{dia_iso}"},
            {"title": "⚙️ Gerenciar", "payload": f"gerenciar_{dia_iso}"},
        ],
    )


def menu_habitos(session: Session, phone: str, usuario_id: uuid.UUID, dia_iso: str) -> None:
    data = datetime.date.fromisoformat(dia_iso)
    registro = registro_service.get_or_create_registro(session, usuario_id, data)
    habitos = usuario_service.get_habitos_ativos(session, usuario_id)
    bool_habitos = [h for h in habitos if h.tipo == "bool"]

    if not bool_habitos:
        whatsapp.send_text(phone, "Você não tem hábitos do tipo Sim/Não configurados.")
        return

    rows = _rows_habitos(session, registro, bool_habitos, dia_iso)
    rows.append({"id": f"voltar_dia_{dia_iso}", "title": "⬅️ Voltar", "description": ""})

    whatsapp.send_list(
        phone,
        header=f"Hábitos — {dia_label(data, data_hoje_brasil())}",
        body="Clique para marcar como feito, não feito, ou pendente.",
        button_label="Ver hábitos",
        sections=[{"title": "Hábitos", "rows": rows}],
    )


def menu_metricas(session: Session, phone: str, usuario_id: uuid.UUID, dia_iso: str) -> None:
    data = datetime.date.fromisoformat(dia_iso)
    registro = registro_service.get_or_create_registro(session, usuario_id, data)
    habitos = usuario_service.get_habitos_ativos(session, usuario_id)
    metricas = [h for h in habitos if h.tipo != "bool"]

    if not metricas:
        whatsapp.send_text(phone, "Você não tem métricas (nota/hora) configuradas.")
        return

    rows = _rows_metricas(session, registro, metricas, dia_iso)
    rows.append({"id": f"voltar_dia_{dia_iso}", "title": "⬅️ Voltar", "description": ""})

    whatsapp.send_list(
        phone,
        header=f"Métricas — {dia_label(data, data_hoje_brasil())}",
        body="Clique em uma métrica para registrar.",
        button_label="Ver métricas",
        sections=[{"title": "Métricas", "rows": rows}],
    )


def toggle_habito(session: Session, phone: str, usuario_id: uuid.UUID, habito_id_str: str, dia_iso: str) -> None:
    habito_id = uuid.UUID(habito_id_str)
    data = datetime.date.fromisoformat(dia_iso)
    registro = registro_service.get_or_create_registro(session, usuario_id, data)
    emoji = registro_service.toggle_bool(session, registro, habito_id)
    whatsapp.send_text(phone, f"{emoji} Registrado!")
    menu_habitos(session, phone, usuario_id, dia_iso)


def pedir_metrica(session: Session, phone: str, usuario_id: uuid.UUID, habito_id_str: str, dia_iso: str) -> None:
    habito_id = uuid.UUID(habito_id_str)
    data = datetime.date.fromisoformat(dia_iso)
    registro = registro_service.get_or_create_registro(session, usuario_id, data)

    habito = session.get(HabitoConfig, habito_id)
    if not habito:
        return

    dia_txt = dia_label(data, data_hoje_brasil()).lower()
    if habito.tipo == "nota":
        pergunta = f"Qual sua nota para *{habito.nome}* {dia_txt}? (0 a 10)"
    elif habito.tipo in ("hora", "hora_anterior"):
        pergunta = f"Que horas foi *{habito.nome}* {dia_txt}? (ex: 07:30)"
    else:
        return

    registro_service.set_status_conversa(session, registro, f"aguardando_{habito_id_str}_{dia_iso}")
    whatsapp.send_text(phone, pergunta)


def processar_resposta_metrica(session: Session, phone: str, usuario: Usuario, registro: Registro, texto: str) -> None:
    partes = registro.status_conversa.removeprefix("aguardando_").rsplit("_", 1)
    if len(partes) != 2:
        return
    habito_id_str, dia_iso = partes

    habito = session.get(HabitoConfig, uuid.UUID(habito_id_str))
    if not habito:
        return

    data = datetime.date.fromisoformat(dia_iso)
    registro_dia = registro_service.get_or_create_registro(session, usuario.id, data)

    try:
        if habito.tipo == "nota":
            valor = registro_service.parse_nota(texto)
        elif habito.tipo == "hora":
            valor = registro_service.parse_hora(texto, data, anterior=False)
        elif habito.tipo == "hora_anterior":
            valor = registro_service.parse_hora(texto, data, anterior=True)
        else:
            return

        registro_service.set_valor(session, registro_dia, habito.id, valor)
        registro_service.set_status_conversa(session, registro, None)
        whatsapp.send_text(phone, "Anotado! ✅")
        menu_metricas(session, phone, usuario.id, dia_iso)

    except (ValueError, Exception):
        whatsapp.send_text(phone, "Formato inválido. Tente novamente.")
        if habito.tipo == "nota":
            whatsapp.send_text(phone, "Digite um número de 0 a 10 (ex: 7.5)")
        else:
            whatsapp.send_text(phone, "Digite no formato HH:MM (ex: 07:30)")


# --- gerenciar hábitos ---

def menu_gerenciar(phone: str, dia_iso: str) -> None:
    whatsapp.send_list(
        phone,
        header="Gerenciar hábitos",
        body="O que você quer fazer?",
        button_label="Ver opções",
        sections=[{
            "title": "Opções",
            "rows": [
                {"id": f"criar_habito_{dia_iso}", "title": truncar("➕ Criar hábito", 24), "description": "Adicionar um novo hábito"},
                {"id": f"congelar_lista_{dia_iso}", "title": truncar("🧊 Congelar/Reativar", 24), "description": "Pausar ou retomar um hábito"},
                {"id": f"voltar_dia_{dia_iso}", "title": truncar("⬅️ Voltar", 24), "description": ""},
            ],
        }],
    )


def iniciar_criar_habito(session: Session, phone: str, usuario_id: uuid.UUID, dia_iso: str) -> None:
    registro = registro_service.get_or_create_registro(session, usuario_id, data_hoje_brasil())
    registro_service.set_status_conversa(session, registro, f"criando_habito_nome{_SEP}{dia_iso}")
    whatsapp.send_text(phone, "Qual o nome do novo hábito?")


def processar_nome_habito(session: Session, phone: str, registro: Registro, texto: str) -> None:
    _, _, dia_iso = registro.status_conversa.partition(_SEP)
    nome = texto.strip()[:80]
    if not nome:
        whatsapp.send_text(phone, "Nome inválido. Digite o nome do hábito:")
        return

    registro_service.set_status_conversa(session, registro, f"criando_habito_tipo{_SEP}{dia_iso}{_SEP}{nome}")
    whatsapp.send_buttons(
        phone,
        body=f"'{nome}' é um hábito de qual tipo?",
        buttons=[
            {"title": "✅ Sim/Não",  "payload": "tipo_bool"},
            {"title": "📊 Nota 0-10", "payload": "tipo_nota"},
            {"title": "⏰ Horário",   "payload": "tipo_hora"},
        ],
    )


def escolher_tipo_habito(session: Session, phone: str, usuario_id: uuid.UUID, registro: Registro, tipo: str) -> None:
    _, _, resto = registro.status_conversa.partition(_SEP)
    dia_iso, _, nome = resto.partition(_SEP)
    if not nome:
        return

    usuario_service.criar_habito_unico(session, usuario_id, nome, tipo, emoji="⭐")
    registro_service.set_status_conversa(session, registro, None)
    whatsapp.send_text(phone, f"Hábito '{nome}' criado! 🎉")
    menu_categoria(phone, dia_iso)


def menu_congelar(session: Session, phone: str, usuario_id: uuid.UUID, dia_iso: str) -> None:
    habitos = usuario_service.listar_todos_habitos(session, usuario_id)
    if not habitos:
        whatsapp.send_text(phone, "Você ainda não tem hábitos cadastrados.")
        return

    rows = []
    for h in habitos:
        status_emoji = "✅" if h.ativo else "🧊"
        status = "Ativo" if h.ativo else "Congelado"
        rows.append({
            "id": f"congelar_toggle_{h.id}_{dia_iso}",
            "title": truncar(f"{status_emoji} {h.emoji or ''} {h.nome}", 24),
            "description": status,
        })
    rows.append({"id": f"gerenciar_{dia_iso}", "title": "⬅️ Voltar", "description": ""})

    whatsapp.send_list(
        phone,
        header="Congelar/Reativar",
        body="Clique para alternar entre ativo e congelado. Congelar preserva o histórico.",
        button_label="Ver hábitos",
        sections=[{"title": "Seus hábitos", "rows": rows}],
    )


def toggle_congelar(session: Session, phone: str, usuario_id: uuid.UUID, habito_id_str: str, dia_iso: str) -> None:
    novo_ativo = usuario_service.toggle_ativo_habito(session, uuid.UUID(habito_id_str))
    whatsapp.send_text(phone, "✅ Reativado!" if novo_ativo else "🧊 Congelado!")
    menu_congelar(session, phone, usuario_id, dia_iso)


# --- helpers internos ---

def _rows_habitos(session: Session, registro: Registro, habitos: List[HabitoConfig], dia_iso: str) -> List[dict]:
    rows = []
    for h in habitos:
        valor = registro_service.get_valor(session, registro.id, h.id)
        status_emoji = registro_service.emoji_status(valor, h.tipo)
        desc = registro_service.valor_para_exibicao(valor, h.tipo)
        rows.append({
            "id": f"toggle_{h.id}_{dia_iso}",
            "title": truncar(f"{status_emoji} {h.emoji or ''} {h.nome}", 24),
            "description": truncar(desc, 72),
        })
    return rows


def _rows_metricas(session: Session, registro: Registro, habitos: List[HabitoConfig], dia_iso: str) -> List[dict]:
    rows = []
    for h in habitos:
        valor = registro_service.get_valor(session, registro.id, h.id)
        status_emoji = registro_service.emoji_status(valor, h.tipo)
        desc = registro_service.valor_para_exibicao(valor, h.tipo)
        rows.append({
            "id": f"ask_{h.id}_{dia_iso}",
            "title": truncar(f"{status_emoji} {h.emoji or ''} {h.nome}", 24),
            "description": truncar(desc, 72),
        })
    return rows
