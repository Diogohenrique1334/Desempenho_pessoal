import pandas as pd
from PIL import Image
from streamlit_echarts import st_echarts
from utils.tratamente_dados import preparar_df
from utils.graficos import liquid_fill,meia_rosca, barras_simples,barras_empilhadas_laterais, barras_empilhadas_horizontais,mapa_correlacao
from utils.transformadores import serei_semana_mes_options,dados_grafico_barras,get_delta,serei_dia_semana_options,serei_mes_ano_options
from funcoes import graficos
import streamlit as st
import datetime as dt
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os

import numpy as np
load_dotenv()

import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from backend.app.models.dependencies import pegar_sessao


#Importando o dataset

@st.cache_data
def carregar_dados():
    """
    Conecta-se ao banco de dados Neon e carrega a tabela 'minha_vida' em um DataFrame.
    """
    db_url = os.getenv("DATABASE_URL")

    engine = create_engine(db_url)
    # Carrega toda a tabela em um DataFrame
    return pd.read_sql_table('minha_vida', engine, index_col='id')

df = carregar_dados()

@st.cache_data
def dados_tratados():

    return preparar_df(df)

df = dados_tratados()

df = df[df.user_phone_number == 'Diogo'].reset_index(drop = 'id')

#variaveis
categorias1 = df[
    [
        'secreto', 
        'Estudar', 
        'Leitura',
        'Exercício aeróbico', 
        'Alimentação saudável',
        'Consumo de água',
#        'Atenção plena', 
        'Academia',
        'Atividade sexual'
    ]
    ].melt()['variable'].unique()

Hiper_categoria = {'secreto':'Lazer', 'Estudar':'Evolução pessoal', 'Leitura':'Evolução pessoal','Exercício aeróbico':'Saúde do corpo', 
    'Alimentação saudável':'Saúde do corpo', 'Consumo de água':'Saúde do corpo','Atenção plena':'Saúde da mente', 'Academia':'Saúde do corpo',
    'Atividade sexual':'Lazer'}

#imagem do painel de filtros
imagem = Image.open("foto_diogo.jpg")

def transformacao_serie(df, agregadores = 'Data'):
    
    return serie_temporal.pivot_table(index = agregadores,
                                       values = 'value',
                                      aggfunc = 'mean')

#-----------------------------------Inicio do app---------------------------------------------

st.set_page_config(layout="wide", page_title='Análise da vida')

st.success("Análise da vida de Diogo")

st.sidebar.title('Painel de filtros')
st.sidebar.image(imagem,caption='-------------------------------------')

#----------------------------------Filtros do app------------------------------------------------

month = st.sidebar.multiselect('Selecione os meses de análise', df["Data"].dt.strftime('%m - %Y').unique())
if month != []:
    df_filtrado = df[df['mes'].isin(month)].set_index('Data')
else:
    df_filtrado = df.set_index('Data')


Horario_despertar = st.sidebar.multiselect('Selecione a hora do despertar', sorted(df_filtrado[df_filtrado['Hora que eu acordei'].dt.hour != 0]\
['Hora que eu acordei'].dt.hour.unique())) 


if Horario_despertar != []:
    df_filtrado = df_filtrado[df_filtrado['Hora que eu acordei'].dt.hour.isin(Horario_despertar)]


categoria = st.sidebar.multiselect('Selecione as categorias da análise', categorias1)


if categoria != []:
    categorias = categoria
else:
    categorias = categorias1



Hcategoria = st.sidebar.multiselect('Selecione a hiper categoria',df_filtrado[categorias].rename(columns=Hiper_categoria).columns.unique())


if Hcategoria != []:
    categorias = {chave: valor for chave, valor in Hiper_categoria.items() if valor in Hcategoria }.keys()

#-------------------------------------graficos do app -------------------------------------

with st.container(border=True, height = 250):

    total, saude_corpo, saude_mente, evolucao_pessoal = st.columns(4)

    serie_temporal = df_filtrado[categorias1].reset_index().melt("Data")
    serie_temporal_total = df_filtrado[categorias].reset_index().melt("Data")

    def transformacao_serie(df, agregadores = 'Data'):
    
        return df.pivot_table(index = agregadores,
                                        values = 'value',
                                        aggfunc = 'mean')

    with total:

        _total = transformacao_serie(serie_temporal_total, [serie_temporal_total.Data.dt.isocalendar()['year'],serie_temporal_total.Data.dt.isocalendar()['week']])

        val = _total.value.mean()

        delta = (
            get_delta(_total.tail(1).value.values[0], val)
        )
        st.metric(
            "Aderencia Total",
            f"{val:0,.0%}",
            delta=delta,
            border=True,
            #delta_color="inverse",
            chart_data=_total.value.tolist(),
            chart_type="area",
        )

    with saude_corpo:

        _saude_corpo = serie_temporal[serie_temporal.variable.map(Hiper_categoria) == "Saúde do corpo"]

        _saude_corpo = transformacao_serie(_saude_corpo, [_saude_corpo.Data.dt.isocalendar()['year'],_saude_corpo.Data.dt.isocalendar()['week']])

        val = _saude_corpo.value.mean() 

        delta = (
            get_delta(_saude_corpo.tail(1).value.values[0], val)
        )
        st.metric(
            "Aderencia saúde do corpo",
            f"{val:0,.0%}",
            delta=delta,
            border=True,
            #delta_color="inverse",
            chart_data=_saude_corpo.value.tolist(),
            chart_type="area",
        )

    with saude_mente:

        _saude_mente = serie_temporal[serie_temporal.variable.map(Hiper_categoria) == "Lazer"]

        _saude_mente = transformacao_serie(_saude_mente, [_saude_mente.Data.dt.isocalendar()['year'],_saude_mente.Data.dt.isocalendar()['week']])

        val = _saude_mente.value.mean() + 0

        delta = (
            get_delta(_saude_mente.tail(1).value.values[0], val)
        )
        st.metric(
            "Aderencia Lazer",
            f"{val:0,.0%}",
            delta=delta,
            border=True,
            #delta_color="inverse",
            chart_data=_saude_mente.value.tolist(),
            chart_type="area",
        )

    with evolucao_pessoal:

        _evolucao_pessoal = serie_temporal[serie_temporal.variable.map(Hiper_categoria) == "Evolução pessoal"]

        _evolucao_pessoal = transformacao_serie(_evolucao_pessoal, [_evolucao_pessoal.Data.dt.isocalendar()['year'],_evolucao_pessoal.Data.dt.isocalendar()['week']])

        val = _evolucao_pessoal.value.mean() + 0

        delta = (
            get_delta(_evolucao_pessoal.tail(1).value.values[0], val)
        )
        st.metric(
            "Aderencia evolução pessoal",
            f"{val:0,.0%}",
            delta=delta,
            border=True,
            #delta_color="inverse",
            chart_data=_evolucao_pessoal.value.tolist(),
            chart_type="area",
        )

with st.container(border=True, height = 380):

    pcol1, pcol2 = st.columns([2,5])

    with pcol1.container(border=True,height=350):

        liquid_fill(valor=dados_grafico_barras(df_filtrado[categorias].melt(),'variable','value',_agg = "mean")[1],tamanho="300px")

    with pcol2.container(border=True,height=350):

        barras_simples(*dados_grafico_barras(df_filtrado[categorias].melt(),'variable','value',_agg = "mean"))

    #with st.container(border = True, height = 350):
    #    st.plotly_chart(graficos(df).grafico_linhas_tempo(coluna_data='Data',categorias=categorias,titulo='Aderência total por mês'))


with st.container(border=True,height=540):

    st.subheader('Aderência acumulada por categoria')

    col1, col2 = st.columns(2)
    
    with col1.container(border=True,height=450):

        barras_empilhadas_horizontais(*serei_dia_semana_options(serie_temporal_total,'Data','value','variable','mean'),"400px")

    with col2.container(border=True,height=450):

        barras_empilhadas_horizontais(*serei_semana_mes_options(serie_temporal_total,'Data','value','variable','mean'),"400px")

    with st.container(border = True, height = 350):
        
        barras_empilhadas_horizontais(*serei_mes_ano_options(serie_temporal_total,'Data','value','variable','mean'),"300px")

with st.container(border=True, height=450):
    st.subheader('Correlação de pearson das minhas tarefas')

    mapa_correlacao(df_filtrado,categorias=categorias, tamanho =  "400px")

with st.container(border=True, height=600):
    st.subheader('Atividades realizadas por dia')
    st_echarts(graficos(table=df_filtrado).grefico_calendario(categorias=categorias,ano_1=2024,ano_2=2025,ano_3=2026), height=500, key="echarts")
