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

    # --- USUÁRIO ATIVO: verificar se há status_conversa aguardando texto ---
    if message.get("type") == "text":
        texto = message["text"]["body"].strip()

        if texto.lower() in TRIGGERS_MENU:
            registro.menu_principal(phone, usuario.nome or phone)
            return

        # checar se está aguardando resposta de métrica
        pendente = registro_service.get_registro_com_status(session, usuario.id)
        if pendente:
            registro.processar_resposta_texto(session, phone, usuario, texto)
            return

        # texto livre sem contexto → menu
        registro.menu_principal(phone, usuario.nome or phone)
        return

    # --- INTERATIVOS (botões e listas) ---
    if message.get("type") == "interactive":
        payload = _extrair_payload(message)
        _processar_interativo(session, phone, usuario, payload)


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

    if payload in ("dia_hoje", "dia_ontem"):
        dia = payload.removeprefix("dia_")
        registro.menu_categoria(phone, dia)
        return

    if payload.startswith("menu_habitos_"):
        dia = payload.removeprefix("menu_habitos_")
        registro.menu_habitos(session, phone, uid, dia)
        return

    if payload.startswith("menu_metricas_"):
        dia = payload.removeprefix("menu_metricas_")
        registro.menu_metricas(session, phone, uid, dia)
        return

    if payload.startswith("voltar_dia_"):
        dia = payload.removeprefix("voltar_dia_")
        registro.menu_categoria(phone, dia)
        return

    if payload.startswith("toggle_"):
        # "toggle_{habito_id}_{dia}"
        rest = payload.removeprefix("toggle_")
        habito_id_str, _, dia = rest.rpartition("_")
        registro.toggle_habito(session, phone, uid, habito_id_str, dia)
        return

    if payload.startswith("ask_"):
        # "ask_{habito_id}_{dia}"
        rest = payload.removeprefix("ask_")
        habito_id_str, _, dia = rest.rpartition("_")
        registro.pedir_metrica(session, phone, uid, habito_id_str, dia)
        return

    # fallback
    whatsapp.send_text(phone, "Não entendi. Mande *menu* para recomeçar.")


def _extrair_payload(message: dict) -> str:
    interactive = message.get("interactive", {})
    itype = interactive.get("type", "")
    return interactive.get(itype, {}).get("id", "")
