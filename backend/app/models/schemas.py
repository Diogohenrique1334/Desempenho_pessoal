import datetime
from typing import Optional
from pydantic import BaseModel, Field

# Schema para RECEBER dados na sua API (ex: em um POST)
class VidaCreateSchema(BaseModel):
    # Deixei opcionais os campos que podem não ser preenchidos no início do dia
    nota_humor: Optional[float] = None
    secreto: bool
    Estudar: bool
    Leitura: bool
    Exercício_aerobico: bool
    Alimentação_saudavel: bool
    Consumo_de_agua: bool
    Atencao_plena: bool
    Diario_e_fixacao: bool
    Academia: bool
    Atividade_sexual: bool
    
    # Usando datetime.time para validar os horários
    Hora_que_eu_acordei: Optional[datetime.time] = None
    Horario_que_eu_fui_dormir: Optional[datetime.time] = None
    Nota_humor_fim_dia: Optional[float] = None

# Schema para ENVIAR dados da sua API (ex: em um GET)
# Ele inclui os campos que o banco de dados gera sozinho (id, data)
class VidaReadSchema(VidaCreateSchema): # Herda todos os campos do schema de criação
    id: int
    data: datetime.datetime

    class Config:
        # Nome da classe e do atributo corrigidos
        from_attributes = True