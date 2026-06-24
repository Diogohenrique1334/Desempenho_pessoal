"""
Dispatcher central: recebe cada mensagem do WhatsApp e decide qual fluxo acionar.
"""

from sqlalchemy.orm import Session

from ..services import registro_service, usuario_service
from ..whatsapp.client import whatsapp
from . import onboarding, registro

TRIGGERS_MENU = {"iniciar", "oi", "olá", "ola", "menu", "diario", "diário"}


def processar(session: Session, phone: str, message: dict) -> None:
    usuario = usuario_service.get_by_phone(session, phone)

    # --- NOVO USUÁRIO ---
    if usuario is None:
        onboarding.iniciar(session, phone)
        return

    # --- ONBOARDING EM ANDAMENTO ---
    if usuario.onboarding_step is not None:
        _processar_onboarding(session, usuario, message)
        return

    # --- USUÁRIO ATIVO ---
    if message.get("type") == "text":
        _processar_texto(session, phone, usuario, message["text"]["body"].strip())
        return

    if message.get("type") == "interactive":
        payload = _extrair_payload(message)
        _processar_interativo(session, phone, usuario, payload)


def _processar_texto(session: Session, phone: str, usuario, texto: str) -> None:
    if texto.lower() in TRIGGERS_MENU:
        registro.menu_seletor_dia(session, phone, usuario.id)
        return

    pendente = registro_service.get_registro_com_status(session, usuario.id)
    if not pendente:
        registro.menu_seletor_dia(session, phone, usuario.id)
        return

    status = pendente.status_conversa
    if status == "aguardando_data_livre":
        registro.processar_data_livre(session, phone, usuario, texto)
    elif status.startswith("criando_habito_nome"):
        registro.processar_nome_habito(session, phone, pendente, texto)
    elif status.startswith("aguardando_"):
        registro.processar_resposta_metrica(session, phone, usuario, pendente, texto)
    else:
        registro.menu_seletor_dia(session, phone, usuario.id)


def _processar_onboarding(session: Session, usuario, message: dict) -> None:
    step = usuario.onboarding_step

    if step == "aguardando_nome":
        if message.get("type") == "text":
            onboarding.processar_nome(session, usuario, message["text"]["body"])
        return

    if step.startswith("selecionando_habitos:"):
        if message.get("type") == "interactive":
            payload = _extrair_payload(message)
            onboarding.processar_selecao(session, usuario, payload)
        return


def _processar_interativo(session: Session, phone: str, usuario, payload: str) -> None:
    uid = usuario.id

    if payload == "dia_outra_data":
        registro.pedir_data_livre(session, phone, uid)
        return

    if payload.startswith("dia_"):
        dia_iso = payload.removeprefix("dia_")
        registro.menu_categoria(phone, dia_iso)
        return

    if payload.startswith("menu_habitos_"):
        dia_iso = payload.removeprefix("menu_habitos_")
        registro.menu_habitos(session, phone, uid, dia_iso)
        return

    if payload.startswith("menu_metricas_"):
        dia_iso = payload.removeprefix("menu_metricas_")
        registro.menu_metricas(session, phone, uid, dia_iso)
        return

    if payload.startswith("voltar_dia_"):
        dia_iso = payload.removeprefix("voltar_dia_")
        registro.menu_categoria(phone, dia_iso)
        return

    if payload.startswith("toggle_"):
        rest = payload.removeprefix("toggle_")
        habito_id_str, _, dia_iso = rest.rpartition("_")
        registro.toggle_habito(session, phone, uid, habito_id_str, dia_iso)
        return

    if payload.startswith("ask_"):
        rest = payload.removeprefix("ask_")
        habito_id_str, _, dia_iso = rest.rpartition("_")
        registro.pedir_metrica(session, phone, uid, habito_id_str, dia_iso)
        return

    if payload.startswith("gerenciar_"):
        dia_iso = payload.removeprefix("gerenciar_")
        registro.menu_gerenciar(phone, dia_iso)
        return

    if payload.startswith("criar_habito_"):
        dia_iso = payload.removeprefix("criar_habito_")
        registro.iniciar_criar_habito(session, phone, uid, dia_iso)
        return

    if payload in ("tipo_bool", "tipo_nota", "tipo_hora"):
        tipo = payload.removeprefix("tipo_")
        pendente = registro_service.get_registro_com_status(session, uid)
        if pendente:
            registro.escolher_tipo_habito(session, phone, uid, pendente, tipo)
        return

    if payload.startswith("congelar_lista_"):
        dia_iso = payload.removeprefix("congelar_lista_")
        registro.menu_congelar(session, phone, uid, dia_iso)
        return

    if payload.startswith("congelar_toggle_"):
        rest = payload.removeprefix("congelar_toggle_")
        habito_id_str, _, dia_iso = rest.rpartition("_")
        registro.toggle_congelar(session, phone, uid, habito_id_str, dia_iso)
        return

    whatsapp.send_text(phone, "Não entendi. Mande *menu* para recomeçar.")


def _extrair_payload(message: dict) -> str:
    interactive = message.get("interactive", {})
    itype = interactive.get("type", "")
    return interactive.get(itype, {}).get("id", "")
