import datetime
import pytz

FUSO_BRASIL = pytz.timezone("America/Sao_Paulo")

_FORMATOS_DATA = ("%d/%m/%Y", "%d/%m/%y", "%d/%m", "%d-%m-%Y", "%d-%m-%y", "%d-%m")
_DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def agora_brasil() -> datetime.datetime:
    return datetime.datetime.now(FUSO_BRASIL)


def data_hoje_brasil() -> datetime.date:
    return agora_brasil().date()


def data_ontem_brasil() -> datetime.date:
    return data_hoje_brasil() - datetime.timedelta(days=1)


def parse_data_usuario(texto: str, ano_padrao: int) -> datetime.date:
    """Aceita '5/6', '05/06', '05/06/2025', '5-6', '05-06-2025'. Sem ano explícito, usa ano_padrao."""
    texto = texto.strip()
    for fmt in _FORMATOS_DATA:
        try:
            d = datetime.datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
        if "%Y" not in fmt and "%y" not in fmt:
            d = d.replace(year=ano_padrao)
        return d
    raise ValueError(f"Data inválida: {texto}")


def dia_label(d: datetime.date, hoje: datetime.date) -> str:
    if d == hoje:
        return "Hoje"
    if d == hoje - datetime.timedelta(days=1):
        return "Ontem"
    return f"{_DIAS_SEMANA[d.weekday()]} {d.strftime('%d/%m')}"


def truncar(texto: str, limite: int) -> str:
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"
