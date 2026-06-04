import datetime
import pytz

FUSO_BRASIL = pytz.timezone("America/Sao_Paulo")


def agora_brasil() -> datetime.datetime:
    return datetime.datetime.now(FUSO_BRASIL)


def data_hoje_brasil() -> datetime.date:
    return agora_brasil().date()


def data_ontem_brasil() -> datetime.date:
    return data_hoje_brasil() - datetime.timedelta(days=1)


def data_para_dia(dia: str) -> datetime.date:
    """Converte 'hoje' ou 'ontem' para um objeto date."""
    return data_hoje_brasil() if dia == "hoje" else data_ontem_brasil()


def truncar(texto: str, limite: int) -> str:
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"
