import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey,
    Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nome: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    onboarding_step: Mapped[Optional[str]] = mapped_column(String(500))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    habitos: Mapped[List["HabitoConfig"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    registros: Mapped[List["Registro"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")


class HabitoConfig(Base):
    __tablename__ = "habitos_config"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    emoji: Mapped[Optional[str]] = mapped_column(String(10))
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuario: Mapped["Usuario"] = relationship(back_populates="habitos")
    valores: Mapped[List["RegistroValor"]] = relationship(back_populates="habito", cascade="all, delete-orphan")


class Registro(Base):
    __tablename__ = "registros"
    __table_args__ = (UniqueConstraint("usuario_id", "data"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    status_conversa: Mapped[Optional[str]] = mapped_column(String(200))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuario: Mapped["Usuario"] = relationship(back_populates="registros")
    valores: Mapped[List["RegistroValor"]] = relationship(back_populates="registro", cascade="all, delete-orphan")


class RegistroValor(Base):
    __tablename__ = "registros_valor"
    __table_args__ = (UniqueConstraint("registro_id", "habito_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registro_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("registros.id"), nullable=False)
    habito_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("habitos_config.id"), nullable=False)
    valor: Mapped[Optional[str]] = mapped_column(Text)

    registro: Mapped["Registro"] = relationship(back_populates="valores")
    habito: Mapped["HabitoConfig"] = relationship(back_populates="valores")
