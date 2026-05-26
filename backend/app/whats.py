from dotenv import load_dotenv
import os
import json
import requests

load_dotenv()

API_VERSION = os.getenv("API_VERSION")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")


# função de mandar mensagem
def manda_msg_whatsapp(recipient_id, message_text):
    print(f"Tentando enviar '{message_text}' para {recipient_id}")
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": recipient_id, "type": "text", "text": {"body": message_text}}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"--- ERRO AO ENVIAR MENSAGEM: {e.response.text if e.response else e} ---")


#Função de mandar botão
def manda_mensagem_botao(recipient_id, question_text, buttons):
    print(f"Tentando enviar pergunta com botões para {recipient_id}")
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    action_buttons = [{"type": "reply", "reply": {"id": b["payload"], "title": b["title"]}} for b in buttons]
    data = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": question_text},
            "action": {"buttons": action_buttons}
        }
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"--- ERRO AO ENVIAR BOTÕES: {e.response.text if e.response else e} ---")

#Função de mandar lista
def send_list_message(recipient_id, header_text, body_text, button_text, sections):
    print(f"Tentando enviar lista para {recipient_id}")
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    
    data = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": header_text[:60]
            },
            "body": {
                "text": body_text[:1024]
            },
            "action": {
                "button": button_text[:20],
                "sections": sections
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"Status: {response.status_code}, Resposta: {response.text}")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"--- ERRO AO ENVIAR LISTA: {e.response.text if e.response else e} ---")