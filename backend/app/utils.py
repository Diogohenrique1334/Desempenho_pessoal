import pytz
import datetime

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