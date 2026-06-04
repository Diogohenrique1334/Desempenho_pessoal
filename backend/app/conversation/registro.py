"""
Fluxo de registro diário de hábitos e métricas.
"""

import uuid
from sqlalchemy.orm import Session

from ..models.models import HabitoConfig, Registro, Usuario
from ..services import registro_service, usuario_service
from ..utils import data_para_dia, truncar
from ..whatsapp.client import whatsapp


def menu_principal(phone: str, nome: str) -> None:
    whatsapp.send_buttons(
        phone,
        body=f"Olá, {nome}! 😊 Para qual dia você quer registrar?",
        buttons=[
            {"title": "📅 Hoje",  "payload": "dia_hoje"},
            {"title": "📅 Ontem", "payload": "dia_ontem"},
        ],
    )


def menu_categoria(phone: str, dia: str) -> None:
    whatsapp.send_buttons(
        phone,
        body=f"O que você quer registrar para *{dia}*?",
        buttons=[
            {"title": "💪 Hábitos",  "payload": f"menu_habitos_{dia}"},
            {"title": "📊 Métricas", "payload": f"menu_metricas_{dia}"},
        ],
    )


def menu_habitos(session: Session, phone: str, usuario_id: uuid.UUID, dia: str) -> None:
    data = data_para_dia(dia)
    registro = registro_service.get_or_create_registro(session, usuario_id, data)
    habitos = usuario_service.get_habitos_ativos(session, usuario_id)
    bool_habitos = [h for h in habitos if h.tipo == "bool"]

    if not bool_habitos:
        whatsapp.send_text(phone, "Você não tem hábitos do tipo Sim/Não configurados.")
        return

    rows = _rows_habitos(session, registro, bool_habitos, dia)
    rows.append({"id": f"voltar_dia_{dia}", "title": "⬅️ Voltar", "description": ""})

    whatsapp.send_list(
        phone,
        header=f"Hábitos — {dia.capitalize()}",
        body="Clique para marcar como feito, não feito, ou pendente.",
        button_label="Ver hábitos",
        sections=[{"title": dia.capitalize(), "rows": rows}],
    )


def menu_metricas(session: Session, phone: str, usuario_id: uuid.UUID, dia: str) -> None:
    data = data_para_dia(dia)
    registro = registro_service.get_or_create_registro(session, usuario_id, data)
    habitos = usuario_service.get_habitos_ativos(session, usuario_id)
    metricas = [h for h in habitos if h.tipo != "bool"]

    if not metricas:
        whatsapp.send_text(phone, "Você não tem métricas (nota/hora) configuradas.")
        return

    rows = _rows_metricas(session, registro, metricas, dia)
    rows.append({"id": f"voltar_dia_{dia}", "title": "⬅️ Voltar", "description": ""})

    whatsapp.send_list(
        phone,
        header=f"Métricas — {dia.capitalize()}",
        body="Clique em uma métrica para registrar.",
        button_label="Ver métricas",
        sections=[{"title": dia.capitalize(), "rows": rows}],
    )


def toggle_habito(session: Session, phone: str, usuario_id: uuid.UUID, habito_id_str: str, dia: str) -> None:
    habito_id = uuid.UUID(habito_id_str)
    data = data_para_dia(dia)
    registro = registro_service.get_or_create_registro(session, usuario_id, data)
    emoji = registro_service.toggle_bool(session, registro, habito_id)
    whatsapp.send_text(phone, f"{emoji} Registrado!")
    menu_habitos(session, phone, usuario_id, dia)


def pedir_metrica(session: Session, phone: str, usuario_id: uuid.UUID, habito_id_str: str, dia: str) -> None:
    habito_id = uuid.UUID(habito_id_str)
    data = data_para_dia(dia)
    registro = registro_service.get_or_create_registro(session, usuario_id, data)

    habito = session.get(HabitoConfig, habito_id)
    if not habito:
        return

    if habito.tipo == "nota":
        pergunta = f"Qual sua nota para *{habito.nome}* {dia}? (0 a 10)"
    elif habito.tipo in ("hora", "hora_anterior"):
        pergunta = f"Que horas foi *{habito.nome}* {dia}? (ex: 07:30)"
    else:
        return

    registro_service.set_status_conversa(session, registro, f"aguardando_{habito_id_str}_{dia}")
    whatsapp.send_text(phone, pergunta)


def processar_resposta_texto(session: Session, phone: str, usuario: Usuario, texto: str) -> None:
    """Chamado quando o usuário manda texto e tem status_conversa pendente."""
    registro = registro_service.get_registro_com_status(session, usuario.id)
    if not registro or not registro.status_conversa:
        menu_principal(phone, usuario.nome or "")
        return

    # "aguardando_{habito_id}_{dia}"
    partes = registro.status_conversa.removeprefix("aguardando_").rsplit("_", 1)
    if len(partes) != 2:
        return
    habito_id_str, dia = partes

    habito = session.get(HabitoConfig, uuid.UUID(habito_id_str))
    if not habito:
        return

    data = data_para_dia(dia)
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
        menu_metricas(session, phone, usuario.id, dia)

    except (ValueError, Exception):
        whatsapp.send_text(phone, "Formato inválido. Tente novamente.")
        if habito.tipo == "nota":
            whatsapp.send_text(phone, "Digite um número de 0 a 10 (ex: 7.5)")
        else:
            whatsapp.send_text(phone, "Digite no formato HH:MM (ex: 07:30)")


# --- helpers internos ---

def _rows_habitos(session: Session, registro: Registro, habitos: list[HabitoConfig], dia: str) -> list[dict]:
    rows = []
    for h in habitos:
        valor = registro_service.get_valor(session, registro.id, h.id)
        emoji = registro_service.emoji_status(valor, h.tipo)
        desc = registro_service.valor_para_exibicao(valor, h.tipo)
        rows.append({
            "id": f"toggle_{h.id}_{dia}",
            "title": truncar(f"{emoji} {h.nome}", 24),
            "description": truncar(desc, 72),
        })
    return rows


def _rows_metricas(session: Session, registro: Registro, habitos: list[HabitoConfig], dia: str) -> list[dict]:
    rows = []
    for h in habitos:
        valor = registro_service.get_valor(session, registro.id, h.id)
        emoji = registro_service.emoji_status(valor, h.tipo)
        desc = registro_service.valor_para_exibicao(valor, h.tipo)
        rows.append({
            "id": f"ask_{h.id}_{dia}",
            "title": truncar(f"{emoji} {h.nome}", 24),
            "description": truncar(desc, 72),
        })
    return rows
