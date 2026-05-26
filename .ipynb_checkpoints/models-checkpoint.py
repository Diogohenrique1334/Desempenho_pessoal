# models.py - VERSÃO CORRIGIDA

from sqlalchemy import create_engine, Column, Integer, Boolean, Float, DateTime, String, UniqueConstraint
from sqlalchemy.orm import declarative_base
import datetime

# Renomeei 'db' para 'engine' para ficar mais claro o que é
import os
from dotenv import load_dotenv

load_dotenv() # Carrega as variáveis do arquivo .env (para testes locais)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não foi definida.")

engine = create_engine(DATABASE_URL, echo=False) # 'echo=False' para um log mais limpo

Base = declarative_base()

class Minha_vida(Base):
    __tablename__ = "minha_vida"
    id = Column("id", Integer, primary_key = True, autoincrement = True)
    data = Column("data", DateTime, default=datetime.datetime.utcnow) # Usar datetime.utcnow é uma boa prática
    nota_humor = Column("nota_humor", Float,nullable = True)
    secreto = Column("secreto", Boolean, nullable=True)
    Estudar = Column("Estudar", Boolean, nullable=True)
    Leitura = Column("Leitura", Boolean, nullable=True)
    Exercício_aerobico = Column("Exercício_aerobico", Boolean, nullable=True)
    Alimentação_saudavel = Column("Alimentação_saudavel", Boolean, nullable=True)
    Consumo_de_agua = Column("Consumo_de_agua", Boolean, nullable=True)
    Atencao_plena = Column("Atencao_plena", Boolean, nullable=True)
    Diario_e_fixacao = Column("Diario_e_fixacao", Boolean, nullable=True)
    Academia = Column("Academia", Boolean, nullable=True)
    Atividade_sexual = Column("Atividade_sexual", Boolean, nullable=True)
    data_hora_acordei = Column("data_hora_acordei", DateTime, nullable=True)
    data_hora_dormi = Column("data_hora_dormi", DateTime, nullable=True)
    Nota_humor_fim_dia = Column("Nota_humor_fim_dia", Float,nullable = True)
    status_conversa = Column(String, nullable=True)
    user_phone_number = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint('user_phone_number', 'data', name='_user_date_uc'),)


    def __repr__(self):
        return f"<Minha_vida(id={self.id}, data={self.data})>"