"""
Recebe o payload bruto do webhook e delega ao engine.
Garante idempotência checando message_id antes de processar.
"""

import os
from fastapi import HTTPException, Request

from ..conversation import engine
from ..models.database import pegar_sessao

_processados: set[str] = set()  # cache em memória; reinicia com o processo
_MAX_CACHE = 500


def verificar_webhook(request: Request) -> int:
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == os.getenv("VERIFY_TOKEN"):
        return int(challenge)
    raise HTTPException(status_code=403, detail="Token inválido")


async def processar_webhook(request: Request) -> dict:
    data = await request.json()

    try:
        value = data["entry"][0]["changes"][0]["value"]
        if "messages" not in value:
            return {"status": "ok"}

        message = value["messages"][0]
        message_id = message.get("id", "")
        phone = message.get("from", "")

        # deduplicação: WhatsApp re-envia webhooks em caso de timeout
        if message_id and message_id in _processados:
            return {"status": "ok"}
        _registrar_processado(message_id)

        with pegar_sessao() as session:
            engine.processar(session, phone, message)

    except Exception as exc:
        import traceback
        print(f"[Webhook] Erro: {exc}")
        traceback.print_exc()

    return {"status": "ok"}


def _registrar_processado(message_id: str) -> None:
    if not message_id:
        return
    if len(_processados) >= _MAX_CACHE:
        # descarta metade dos mais antigos (set não tem ordem, mas evita crescimento ilimitado)
        older = list(_processados)[: _MAX_CACHE // 2]
        for m in older:
            _processados.discard(m)
    _processados.add(message_id)
