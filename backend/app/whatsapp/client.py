import json
import os

import requests


class WhatsAppClient:
    def __init__(self):
        version = os.getenv("API_VERSION", "v19.0")
        phone_id = os.getenv("PHONE_NUMBER_ID", "")
        self.token = os.getenv("ACCESS_TOKEN", "")
        self.url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _post(self, payload: dict) -> None:
        try:
            r = requests.post(self.url, headers=self.headers, data=json.dumps(payload), timeout=10)
            r.raise_for_status()
        except requests.RequestException as e:
            body = e.response.text if getattr(e, "response", None) else str(e)
            print(f"[WhatsApp] Erro ao enviar: {body}")

    def send_text(self, to: str, text: str) -> None:
        self._post({
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        })

    def send_buttons(self, to: str, body: str, buttons: list[dict]) -> None:
        """buttons: [{"title": str, "payload": str}, ...]  — máx 3."""
        self._post({
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": b["payload"], "title": b["title"][:20]}}
                        for b in buttons[:3]
                    ]
                },
            },
        })

    def send_list(
        self,
        to: str,
        header: str,
        body: str,
        button_label: str,
        sections: list[dict],
    ) -> None:
        """
        sections: [{"title": str, "rows": [{"id": str, "title": str, "description": str}, ...]}]
        Limites WhatsApp: título de linha ≤ 24 chars, descrição ≤ 72 chars.
        """
        self._post({
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": header[:60]},
                "body": {"text": body[:1024]},
                "action": {
                    "button": button_label[:20],
                    "sections": sections,
                },
            },
        })


whatsapp = WhatsAppClient()
