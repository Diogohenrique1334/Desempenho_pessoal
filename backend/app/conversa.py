from backend.app.whats import manda_mensagem_botao, manda_msg_whatsapp, send_list_message
from models.models import Minha_vida
from utils import FUSO_BRASIL
from sqlalchemy import func
import datetime



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

#manda menu inicial da conversa
def menu_principal(sender_phone):
    texto = "Olá! Bem-vindo(a) ao seu diário. 😄\n\nPara qual dia você gostaria de registrar informações?"
    botoes = [
        {"title": "📅 Hoje", "payload": "escolher_dia_hoje"},
        {"title": "📅 Ontem", "payload": "escolher_dia_ontem"}
    ]
    manda_mensagem_botao(sender_phone, texto, botoes)

#manda menu pós primeira seleção
def menu_dinamico(sender_phone, session, registro, category, dia="hoje"):
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

#Alimenta o banco
def fazer_registro_banco(session, data, sender_phone):
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