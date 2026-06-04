import datetime
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from ..models.models import Registro, RegistroValor
from ..utils import FUSO_BRASIL


def get_or_create_registro(session: Session, usuario_id: uuid.UUID, data: datetime.date) -> Registro:
    registro = session.query(Registro).filter_by(usuario_id=usuario_id, data=data).first()
    if not registro:
        registro = Registro(usuario_id=usuario_id, data=data)
        session.add(registro)
        session.commit()
    return registro


def get_valor(session: Session, registro_id: uuid.UUID, habito_id: uuid.UUID) -> Optional[str]:
    rv = session.query(RegistroValor).filter_by(registro_id=registro_id, habito_id=habito_id).first()
    return rv.valor if rv else None


def toggle_bool(session: Session, registro: Registro, habito_id: uuid.UUID) -> str:
    """Cicla None → 'true' → 'false' → None. Retorna emoji do novo estado."""
    rv = session.query(RegistroValor).filter_by(registro_id=registro.id, habito_id=habito_id).first()

    if rv is None:
        session.add(RegistroValor(registro_id=registro.id, habito_id=habito_id, valor="true"))
        session.commit()
        return "✅"

    if rv.valor == "true":
        rv.valor = "false"
        session.commit()
        return "❌"

    session.delete(rv)
    session.commit()
    return "⬜"


def set_valor(session: Session, registro: Registro, habito_id: uuid.UUID, valor: str) -> None:
    rv = session.query(RegistroValor).filter_by(registro_id=registro.id, habito_id=habito_id).first()
    if rv:
        rv.valor = valor
    else:
        session.add(RegistroValor(registro_id=registro.id, habito_id=habito_id, valor=valor))
    session.commit()


def set_status_conversa(session: Session, registro: Registro, status: Optional[str]) -> None:
    registro.status_conversa = status
    session.commit()


def get_registro_com_status(session: Session, usuario_id: uuid.UUID) -> Optional[Registro]:
    """Retorna o registro mais recente que tem status_conversa preenchido."""
    return (
        session.query(Registro)
        .filter(Registro.usuario_id == usuario_id, Registro.status_conversa.isnot(None))
        .order_by(Registro.data.desc())
        .first()
    )


def valor_para_exibicao(valor: Optional[str], tipo: str) -> str:
    if valor is None:
        return "Pendente"
    if tipo == "bool":
        return "Sim" if valor == "true" else "Não"
    if tipo in ("hora", "hora_anterior"):
        try:
            dt = datetime.datetime.fromisoformat(valor)
            dt_br = dt.astimezone(FUSO_BRASIL)
            return dt_br.strftime("%H:%M")
        except Exception:
            return valor
    return valor


def emoji_status(valor: Optional[str], tipo: str) -> str:
    if valor is None:
        return "⬜"
    if tipo == "bool":
        return "✅" if valor == "true" else "❌"
    return "📊" if tipo == "nota" else "⏰"


def parse_hora(texto: str, data_ref: datetime.date, anterior: bool = False) -> str:
    """Valida HH:MM e retorna ISO string com fuso Brasil."""
    hora_obj = datetime.datetime.strptime(texto.strip(), "%H:%M").time()
    data_base = data_ref - datetime.timedelta(days=1) if anterior else data_ref
    dt = datetime.datetime.combine(data_base, hora_obj)
    dt_br = FUSO_BRASIL.localize(dt)
    return dt_br.isoformat()


def parse_nota(texto: str) -> str:
    """Valida nota 0-10 e retorna string."""
    nota = float(texto.replace(",", "."))
    if not (0 <= nota <= 10):
        raise ValueError("Nota fora do intervalo 0-10")
    return str(nota)
