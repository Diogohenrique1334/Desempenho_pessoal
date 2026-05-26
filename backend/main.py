import logging
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import os
from app.models.dependencies import pegar_sessao
from app.models.models import Minha_vida
from app.conversa import menu_principal,fazer_registro_banco,menu_dinamico,TOPICOS_SIM_NAO,TOPICOS_TEXTO
from app.whats import manda_mensagem_botao,manda_msg_whatsapp
from app.utils import data_hoje_brasil, data_ontem_brasil, agora_brasil, FUSO_BRASIL
import json
import datetime
import traceback
import uvicorn
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


load_dotenv()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")


app = FastAPI()

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
                    menu_principal(sender_phone)
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
                        
                        registro = fazer_registro_banco(session, data_referencia, sender_phone)
                        
                        texto = f"Você selecionou {dia_escolhido}. O que você gostaria de registrar?"
                        botoes = [
                            {"title": "💪 Registrar Hábitos", "payload": f"show_menu_habitos_{dia_escolhido}"},
                            {"title": "📊 Registrar Métricas", "payload": f"show_menu_metricas_{dia_escolhido}"}
                        ]
                        manda_mensagem_botao(sender_phone, texto, botoes)
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
                        
                        registro = fazer_registro_banco(session, data_referencia, sender_phone)
                        
                        if category == 'principal':
                            menu_principal(sender_phone)
                        else:
                            menu_dinamico(sender_phone, session, registro, category, dia_escolhido)
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

                        registro = fazer_registro_banco(session, data_referencia, sender_phone)

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
                            manda_msg_whatsapp(sender_phone, f"✅ Hábito {acao}!")
                            
                            # Atualizar o menu
                            menu_dinamico(sender_phone, session, registro, 'habitos', dia_escolhido)
                            
                        elif topic_key in TOPICOS_TEXTO:
                            # Para métricas, manter o comportamento original
                            topic_info = TOPICOS_TEXTO[topic_key]
                            texto_pergunta = topic_info['texto'].format(dia=dia_escolhido)
                            registro.status_conversa = f"aguardando_{topic_key}_{dia_escolhido}"
                            session.commit()
                            manda_msg_whatsapp(sender_phone, texto_pergunta)
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
                        registro = fazer_registro_banco(session, data_referencia, sender_phone)

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
                                manda_msg_whatsapp(sender_phone, "Anotado! ✅")
                                menu_dinamico(sender_phone, session, registro, 'metricas', dia_escolhido)
                            except ValueError:
                                manda_msg_whatsapp(sender_phone, "Resposta inválida. Por favor, tente novamente.")
                                # Reenviar a pergunta
                                texto_pergunta = topic_info['texto'].format(dia=dia_escolhido)
                                manda_msg_whatsapp(sender_phone, texto_pergunta)
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