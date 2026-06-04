import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.models import HabitoConfig, Usuario


def get_by_phone(session: Session, phone: str) -> Optional[Usuario]:
    return session.query(Usuario).filter_by(phone=phone).first()


def criar_usuario(session: Session, phone: str) -> Usuario:
    usuario = Usuario(phone=phone, onboarding_step="aguardando_nome")
    session.add(usuario)
    session.commit()
    return usuario


def get_habitos_ativos(session: Session, usuario_id: uuid.UUID) -> list[HabitoConfig]:
    return (
        session.query(HabitoConfig)
        .filter_by(usuario_id=usuario_id, ativo=True)
        .order_by(HabitoConfig.ordem)
        .all()
    )


def criar_habitos(session: Session, usuario_id: uuid.UUID, habitos: list[dict]) -> None:
    """habitos: [{"nome": str, "tipo": str}, ...]"""
    for i, h in enumerate(habitos):
        session.add(HabitoConfig(usuario_id=usuario_id, nome=h["nome"], tipo=h["tipo"], ordem=i))
    session.commit()


def finalizar_onboarding(session: Session, usuario: Usuario) -> None:
    usuario.onboarding_step = None
    session.commit()
