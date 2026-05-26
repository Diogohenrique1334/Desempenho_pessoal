import uvicorn
import requests
import json
import datetime
from fastapi import FastAPI, Request, HTTPException
from sqlalchemy import func, cast, Date
import traceback
from dotenv import load_dotenv
import os
import pytz

load_dotenv()

API_VERSION = os.getenv("API_VERSION")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

from app.models.models import Minha_vida
from app.models.dependencies import pegar_sessao

app = FastAPI()

# Configuração do fuso horário do Brasil
FUSO_BRASIL = pytz.timezone('America/Sao_Paulo')

# --- FUNÇÕES AUXILIARES ---
def agora_brasil():
    """Retorna o datetime atual no fuso horário do Brasil"""
    return datetime.datetime.now(FUSO_BRASIL)

def data_hoje_brasil():
    """Retorna a data atual no fuso horário do Brasil"""
    return agora_brasil().date()

def data_ontem_brasil():
    """Retorna a data de ontem no fuso horário do Brasil"""
    return data_hoje_brasil() - datetime.timedelta(days=1)

# --- FUNÇÕES DE ENVIO DE MENSAGEM ---
def send_whatsapp_message(recipient_id, message_text):
    print(f"Tentando enviar '{message_text}' para {recipient_id}")
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": recipient_id, "type": "text", "text": {"body": message_text}}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"--- ERRO AO ENVIAR MENSAGEM: {e.response.text if e.response else e} ---")

def send_button_message(recipient_id, question_text, buttons):
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

# --- LÓGICA DA CONVERSA ---

TOPICOS_SIM_NAO = {
    'academia': {'coluna': 'Academia', 'texto': 'Você foi à academia {dia}?', 'titulo': 'Academia'},
    'leitura': {'coluna': 'Leitura', 'texto': 'E sobre leitura, você praticou {dia}?', 'titulo': 'Leitura'},
    'estudar': {'coluna': 'Estudar', 'texto': 'Reservou um tempo para os estudos {dia}?', 'titulo': 'Estudar'},
    'alimentacao_saudavel': {'coluna': 'Alimentação_saudavel', 'texto': 'Sua alimentação foi saudável {dia}?', 'titulo': 'Alimentação'},
    'consumo_de_agua': {'coluna': 'Consumo_de_agua', 'texto': 'Bebeu água o suficiente {dia}?', 'titulo': 'Água'},
    'secreto': {'coluna': 'secreto', 'texto': 'Fumou {dia}?', 'titulo': 'Secreto'},
    'exercicio_aerobico': {'coluna': 'Exercício_aerobico', 'texto': 'Praticou atividade física {dia}?', 'titulo': 'Exercício'},
    'atividade_sexual': {'coluna': 'Atividade_sexual', 'texto': 'Fez sexo {dia}?', 'titulo': 'Sexo'}
}

TOPICOS_TEXTO = {
    'nota_humor_inicio': {'coluna': 'nota_humor', 'texto': 'Qual sua nota de humor ao acordar {dia}? (de 0 a 10)', 'tipo': 'nota', 'titulo': 'Humor Início'},
    'hora_acordei': {'coluna': 'data_hora_acordei', 'texto': 'Beleza. E que horas você acordou {dia}? (ex: 07:30)', 'tipo': 'hora', 'titulo': 'Hora Acordar'},
    'hora_dormir': {'coluna': 'data_hora_dormi', 'texto': 'Entendido. E que horas você foi dormir na noite anterior? (ex: 23:30)', 'tipo': 'hora_anterior', 'titulo': 'Hora Dormir'},
    'nota_humor_fim': {'coluna': 'Nota_humor_fim_dia', 'texto': 'Para finalizar, qual sua nota de humor ao ir dormir {dia}? (de 0 a 10)', 'tipo': 'nota', 'titulo': 'Humor Fim'}
}

def send_top_level_menu(sender_phone):
    texto = "Olá! Bem-vindo(a) ao seu diário. 😄\n\nPara qual dia você gostaria de registrar informações?"
    botoes = [
        {"title": "📅 Hoje", "payload": "escolher_dia_hoje"},
        {"title": "📅 Ontem", "payload": "escolher_dia_ontem"}
    ]
    send_button_message(sender_phone, texto, botoes)

def send_dynamic_menu(sender_phone, session, registro, category, dia="hoje"):
    topicos_dict = TOPICOS_SIM_NAO if category == 'habitos' else TOPICOS_TEXTO
    header_text = "Hábitos" if category == 'habitos' else "Métricas"
    
    # Ajustar texto do dia
    dia_texto = "hoje" if dia == "hoje" else "ontem"
    
    rows = []
    for key, value in topicos_dict.items():
        resposta = getattr(registro, value['coluna'], None)
        # Usar título curto em vez do nome da coluna
        coluna_nome = value['titulo']
        
        if resposta is None:
            status_emoji = "⬜️"
            description = "Pendente"
        else:
            if category == 'habitos':
                status_emoji = "✅" if resposta else "❌"
                description = f"Resposta: {'Sim' if resposta else 'Não'}"
            else:
                status_emoji = "⏰" if 'hora' in key else "📊"
                if isinstance(resposta, datetime.datetime):
                    resposta_brasil = resposta.astimezone(FUSO_BRASIL)
                    description = f"Resposta: {resposta_brasil.strftime('%H:%M')}"
                else:
                    description = f"Resposta: {resposta}"
        
        # Garantir que o título não ultrapasse 24 caracteres
        row_title = f"{status_emoji} {coluna_nome}"
        if len(row_title) > 24:
            row_title = row_title[:21] + "..."
        
        # Garantir que a descrição não ultrapasse 72 caracteres
        row_description = description
        if len(row_description) > 72:
            row_description = row_description[:69] + "..."
        
        rows.append({
            "id": f"ask_{key}_{dia}",
            "title": row_title,
            "description": row_description
        })

    # Botão de voltar com título mais curto
    rows.append({
        "id": f"show_menu_principal_{dia}",
        "title": "⬅️ Voltar"
    })
    
    # Título da seção mais curto
    section_title = f"{dia_texto.capitalize()}"[:24]
    
    sections = [{
        "title": section_title,
        "rows": rows
    }]
    
    send_list_message(sender_phone, f"Diário - {dia_texto.capitalize()}", header_text, "Opções", sections)

def get_registro_por_data(session, data, sender_phone):
    """Busca ou cria um registro para uma data específica"""
    registro = session.query(Minha_vida).filter(
        func.date(func.timezone('America/Sao_Paulo', Minha_vida.data)) == data,
        Minha_vida.user_phone_number == sender_phone
    ).first()

    if not registro:
        # Criar registro com a data especificada
        data_inicio = FUSO_BRASIL.localize(datetime.datetime.combine(data, datetime.time(0, 0)))
        novo_registro = Minha_vida(
            data=data_inicio,
            user_phone_number=sender_phone
        )
        session.add(novo_registro)
        session.commit()
        registro = session.query(Minha_vida).filter(
            func.date(func.timezone('America/Sao_Paulo', Minha_vida.data)) == data,
            Minha_vida.user_phone_number == sender_phone
        ).first()
    
    return registro

# --- ENDPOINTS DA API ---
@app.get("/")
def root(): return {"status": "API online"}

@app.get("/webhook")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK VERIFICADO!")
        return int(challenge)
    raise HTTPException(status_code=403, detail="Token inválido")

@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()
    print(f"\n--- Webhook Recebido ---\n{json.dumps(data, indent=2)}\n-----------------------\n")

    try:
        value = data["entry"][0]["changes"][0]["value"]
        if "messages" in value:
            message_info = value["messages"][0]
            sender_phone = message_info["from"]
            
            with pegar_sessao() as session:
                # 1. Iniciar a conversa (mensagem de texto simples)
                if message_info["type"] == "text" and message_info["text"]["body"].lower().strip() in ["iniciar", "oi", "diario", "menu"]:
                    send_top_level_menu(sender_phone)
                    return {"status": "ok"}
                
                # 2. Processar respostas interativas (Menus, Listas e Botões)
                elif message_info["type"] == "interactive":
                    interactive_type = message_info["interactive"]["type"]
                    payload = message_info["interactive"][interactive_type]["id"]

                    # Escolha do dia (hoje/ontem)
                    if payload.startswith('escolher_dia_'):
                        dia_escolhido = payload.replace('escolher_dia_', '')
                        
                        if dia_escolhido == 'hoje':
                            data_referencia = data_hoje_brasil()
                        else:  # ontem
                            data_referencia = data_ontem_brasil()
                        
                        registro = get_registro_por_data(session, data_referencia, sender_phone)
                        
                        texto = f"Você selecionou {dia_escolhido}. O que você gostaria de registrar?"
                        botoes = [
                            {"title": "💪 Registrar Hábitos", "payload": f"show_menu_habitos_{dia_escolhido}"},
                            {"title": "📊 Registrar Métricas", "payload": f"show_menu_metricas_{dia_escolhido}"}
                        ]
                        send_button_message(sender_phone, texto, botoes)
                        return {"status": "ok"}

                    # Navegação entre menus
                    if payload.startswith('show_menu_'):
                        parts = payload.split('_')
                        # payload exemplo: show_menu_habitos_hoje
                        # parts = ['show','menu','habitos','hoje']
                        # category é parts[2], dia parts[3]
                        category = parts[2] if len(parts) > 2 else 'principal'
                        dia_escolhido = parts[3] if len(parts) > 3 else 'hoje'
                        
                        if dia_escolhido == 'hoje':
                            data_referencia = data_hoje_brasil()
                        else:  # ontem
                            data_referencia = data_ontem_brasil()
                        
                        registro = get_registro_por_data(session, data_referencia, sender_phone)
                        
                        if category == 'principal':
                            send_top_level_menu(sender_phone)
                        else:
                            send_dynamic_menu(sender_phone, session, registro, category, dia_escolhido)
                        return {"status": "ok"}

                    # Seleção de um item na lista para responder (preserva underscores no topic_key)
                    if payload.startswith('ask_'):
                        # rest ex: "atividade_sexual_ontem"
                        rest = payload[len('ask_'):]
                        try:
                            topic_key, dia_escolhido = rest.rsplit('_', 1)
                        except ValueError:
                            topic_key = rest
                            dia_escolhido = 'hoje'

                        if dia_escolhido == 'hoje':
                            data_referencia = data_hoje_brasil()
                        else:
                            data_referencia = data_ontem_brasil()

                        registro = get_registro_por_data(session, data_referencia, sender_phone)

                        if topic_key in TOPICOS_SIM_NAO:
                            # ALTERAÇÃO PRINCIPAL: Para hábitos, marcar automaticamente como True
                            topic_info = TOPICOS_SIM_NAO[topic_key]
                            coluna = topic_info['coluna']
                            
                            # Verificar o estado atual para fazer toggle
                            estado_atual = getattr(registro, coluna)
                            novo_estado = not estado_atual if estado_atual is not None else True
                            
                            setattr(registro, coluna, novo_estado)
                            session.commit()
                            
                            # Mensagem de confirmação
                            acao = "marcada como feita" if novo_estado else "marcada como não feita"
                            send_whatsapp_message(sender_phone, f"✅ Hábito {acao}!")
                            
                            # Atualizar o menu
                            send_dynamic_menu(sender_phone, session, registro, 'habitos', dia_escolhido)
                            
                        elif topic_key in TOPICOS_TEXTO:
                            # Para métricas, manter o comportamento original
                            topic_info = TOPICOS_TEXTO[topic_key]
                            texto_pergunta = topic_info['texto'].format(dia=dia_escolhido)
                            registro.status_conversa = f"aguardando_{topic_key}_{dia_escolhido}"
                            session.commit()
                            send_whatsapp_message(sender_phone, texto_pergunta)
                        return {"status": "ok"}

                    # REMOVIDO: Não precisamos mais processar respostas 'ans_' para hábitos
                    # pois agora os hábitos são marcados diretamente no 'ask_'
                
                # 3. Processar respostas de texto (para Métricas)
                elif message_info["type"] == "text":
                    # Verificar se há um registro com status_conversa
                    registro = session.query(Minha_vida).filter(
                        Minha_vida.user_phone_number == sender_phone,
                        Minha_vida.status_conversa.isnot(None)
                    ).order_by(Minha_vida.data.desc()).first()
                    
                    if registro and registro.status_conversa:
                        texto_usuario = message_info["text"]["body"]
                        # remover prefixo "aguardando_" e separar topic + dia corretamente
                        status = registro.status_conversa
                        if status.startswith("aguardando_"):
                            rest = status[len("aguardando_"):]  # ex: "hora_acordei_hoje"
                            try:
                                topic_key, dia_escolhido = rest.rsplit('_', 1)
                            except ValueError:
                                topic_key = rest
                                dia_escolhido = 'hoje'
                        else:
                            topic_key = None
                            dia_escolhido = 'hoje'

                        if dia_escolhido == 'hoje':
                            data_referencia = data_hoje_brasil()
                        else:
                            data_referencia = data_ontem_brasil()

                        # Recarregar o registro específico para o dia
                        registro = get_registro_por_data(session, data_referencia, sender_phone)

                        if topic_key in TOPICOS_TEXTO:
                            topic_info = TOPICOS_TEXTO[topic_key]
                            coluna = topic_info['coluna']
                            try:
                                if topic_info['tipo'] == 'nota':
                                    nota = float(texto_usuario.replace(',', '.'))
                                    if not (0 <= nota <= 10): 
                                        raise ValueError("Nota fora do intervalo")
                                    setattr(registro, coluna, nota)
                                
                                elif topic_info['tipo'] == 'hora':
                                    hora_obj = datetime.datetime.strptime(texto_usuario, '%H:%M').time()
                                    # Combinar com a data de referência
                                    data_completa = datetime.datetime.combine(data_referencia, hora_obj)
                                    # Adicionar fuso horário
                                    data_completa_brasil = FUSO_BRASIL.localize(data_completa)
                                    setattr(registro, coluna, data_completa_brasil)

                                elif topic_info['tipo'] == 'hora_anterior':
                                    hora_obj = datetime.datetime.strptime(texto_usuario, '%H:%M').time()
                                    # Para hora de dormir, sempre é o dia anterior à data de referência
                                    data_anterior = data_referencia - datetime.timedelta(days=1)
                                    data_completa = datetime.datetime.combine(data_anterior, hora_obj)
                                    # Adicionar fuso horário
                                    data_completa_brasil = FUSO_BRASIL.localize(data_completa)
                                    setattr(registro, coluna, data_completa_brasil)

                                registro.status_conversa = None
                                session.commit()
                                send_whatsapp_message(sender_phone, "Anotado! ✅")
                                send_dynamic_menu(sender_phone, session, registro, 'metricas', dia_escolhido)
                            except ValueError:
                                send_whatsapp_message(sender_phone, "Resposta inválida. Por favor, tente novamente.")
                                # Reenviar a pergunta
                                texto_pergunta = topic_info['texto'].format(dia=dia_escolhido)
                                send_whatsapp_message(sender_phone, texto_pergunta)
                        return {"status": "ok"}
    except Exception as e:
        print(f"!!!!!!!!!! ERRO CRÍTICO NO WEBHOOK !!!!!!!!!!!")
        print(f"Erro: {e}")
        traceback.print_exc()
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    return {"status": "ok"}

# --- Bloco para iniciar o servidor ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)