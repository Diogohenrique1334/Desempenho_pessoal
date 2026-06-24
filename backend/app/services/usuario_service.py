import uuid
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.models import HabitoConfig, Usuario


def get_by_phone(session: Session, phone: str) -> Optional[Usuario]:
    return session.query(Usuario).filter_by(phone=phone).first()


def criar_usuario(session: Session, phone: str) -> Usuario:
    usuario = Usuario(phone=phone, onboarding_step="aguardando_nome")
    session.add(usuario)
    session.commit()
    return usuario


def get_habitos_ativos(session: Session, usuario_id: uuid.UUID) -> List[HabitoConfig]:
    return (
        session.query(HabitoConfig)
        .filter_by(usuario_id=usuario_id, ativo=True)
        .order_by(HabitoConfig.ordem)
        .all()
    )


def listar_todos_habitos(session: Session, usuario_id: uuid.UUID) -> List[HabitoConfig]:
    """Ativos e congelados, para a tela de Gerenciar."""
    return (
        session.query(HabitoConfig)
        .filter_by(usuario_id=usuario_id)
        .order_by(HabitoConfig.ordem)
        .all()
    )


def criar_habitos(session: Session, usuario_id: uuid.UUID, habitos: List[dict]) -> None:
    """habitos: [{"nome": str, "tipo": str}, ...] — usado no onboarding."""
    for i, h in enumerate(habitos):
        session.add(HabitoConfig(usuario_id=usuario_id, nome=h["nome"], tipo=h["tipo"], ordem=i))
    session.commit()


def criar_habito_unico(session: Session, usuario_id: uuid.UUID, nome: str, tipo: str) -> HabitoConfig:
    """Cria um hábito avulso (fluxo de Gerenciar, pós-onboarding)."""
    max_ordem = session.query(func.max(HabitoConfig.ordem)).filter_by(usuario_id=usuario_id).scalar() or 0
    habito = HabitoConfig(usuario_id=usuario_id, nome=nome[:100], tipo=tipo, ordem=max_ordem + 1)
    session.add(habito)
    session.commit()
    return habito


def toggle_ativo_habito(session: Session, habito_id: uuid.UUID) -> bool:
    """Congela/reativa um hábito sem apagar histórico. Retorna o novo estado."""
    habito = session.get(HabitoConfig, habito_id)
    habito.ativo = not habito.ativo
    session.commit()
    return habito.ativo


def finalizar_onboarding(session: Session, usuario: Usuario) -> None:
    usuario.onboarding_step = None
    session.commit()
