import pandas as pd
from PIL import Image
from streamlit_echarts import st_echarts
from funcoes import ajustes_variaveis as fc
from funcoes import graficos
import streamlit as st
import datetime as dt
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# --- 2. PRÉ-PROCESSAMENTO E CRIAÇÃO DE ATRIBUTOS ---

df = pd.read_sql_table('minha_vida', create_engine(os.getenv("DATABASE_URL")), index_col='id')

usuario = {'5511959536031':"Diogo",'5511991422452':"Michele"}

# Garante que a coluna 'data' é do tipo datetime e ajusta para o fuso horário correto
df['data'] = pd.to_datetime(df['data'].dt.date)

# Criação das colunas de data/hora a partir da coluna 'data'
df['Data'] = df['data']
df['Dia da semana'] = df['data'].dt.weekday.map({6:'Dom',0:'Seg',1:'Ter',2:'Qua',3:'Qui',4:'Sex',5:'Sab'})
df['mes'] = df["data"].dt.strftime('%m - %Y')
df['mes_ordenacao'] = pd.to_datetime(df['data']).dt.to_period('M')
df['mes'] = pd.Categorical(df['mes'], categories=df.sort_values('mes_ordenacao')['mes'].unique(), ordered=True)
df = df.drop(columns=['mes_ordenacao'])
df['Dia da semana'] = pd.Categorical(df['Dia da semana'], categories=['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom'], ordered=True)
df['user_phone_number'] = df['user_phone_number'].map(usuario).astype('category')


# Converte colunas booleanas para 0 e 1 para cálculos
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].astype('bool').astype(int)

#variaveis
categorias1 = df[
    [
        'secreto', 
        'Estudar', 
        'Leitura',
        'Exercício_aerobico', 
        'Alimentação saudável',
        'Consumo de água',
#        'Atenção plena', 
        'Academia',
        'Atividade sexual'
    ]
    ].melt()['variable'].unique()

Hiper_categoria = {'secreto':'Lazer', 'Estudar':'Evolução pessoal', 'Leitura':'Evolução pessoal','Exercício_aerobico':'Saúde do corpo', 
    'Alimentação saudável':'Saúde do corpo', 'Consumo de água':'Saúde do corpo','Atenção plena':'Saúde da mente', 'Academia':'Saúde do corpo',
    'Atividade sexual':'Lazer'}

#Ajustes variáveis
df = fc(fc(fc(df).tratamento_hora()).tempo_sono_n()).Humor()
#df = fc(df).tratamento_hora()

#df = fc(df).tempo_sono_n()

#imagem do painel de filtros
imagem = Image.open("foto_diogo.jpg")

#-----------------------------------Inicio do app---------------------------------------------

st.set_page_config(layout="wide", page_title='Análise da vida')


st.success("Análise da vida")

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
    categorias = [x for x in categorias1 if x in categoria]
else:
    categorias = categorias1


Hcategoria = st.sidebar.multiselect('Selecione a hiper categoria',df_filtrado[categorias].rename(columns=Hiper_categoria).columns.unique())


if Hcategoria != []:
    categorias = {chave: valor for chave, valor in Hiper_categoria.items() if valor in Hcategoria }.keys()

#-------------------------------------graficos do app -------------------------------------


with st.container(border=True, height = 380):

    pcol1, pcol2 = st.columns([2,5])

    with pcol1.container(border=True,height=350):

        st_echarts(graficos().liquid_fill(df_filtrado[categorias].melt()['value'].dropna().mean()),height="300px")

    with pcol2.container(border=True,height=350):

        st.plotly_chart(graficos(df_filtrado[categorias].mean().sort_values(ascending = False)).grafico_barras('Aderência acumulada por categoria'))

    with st.container(border = True, height = 350):
        st.plotly_chart(graficos(df).grafico_linhas_tempo(coluna_data='Data',categorias=categorias,titulo='Aderência total por mês'))




with st.container(border=True,height=540):

    st.subheader('Aderência acumulada por categoria')

    col1, col2 = st.columns([2,1.5])
    
    with col1.container(border=True,height=450):
        st.plotly_chart(
            graficos(table=df).aderencia_mes(
                categoria_x=df['Dia da semana'],
                categorias=categorias,
                titulo='Aderência acumulada por dia da semana'), 
            height = "200px"
        )

    with col2.container(border=True,height=450):
        left, right = st.columns(2)
        if left.button("Horario de dormir", use_container_width=True):
            st.plotly_chart(
                graficos(table=df).aderencia_mes(
                    categoria_x=df['Horario que eu fui dormir'].dt.hour,
                    categorias=categorias,
                    titulo='Horario de dormir'),
                height = "50px"
            )

        if right.button("Hora dispertar", use_container_width=True):
            st.plotly_chart(
                graficos(table=df).aderencia_mes(
                    categoria_x=df['Hora que eu acordei'].dt.hour,
                    categorias=categorias,
                    titulo='Hora dispertar'),
                height = "100px"
            )

    with st.container(border = True, height = 350):
        st.plotly_chart(
            graficos(table=df).aderencia_mes(
                categoria_x=df.mes,
                categorias=categorias,
                titulo='Aderencia acumulada por mês'),
            height = "320px"
        )

with st.container(border=True, height=450):
    st.subheader('Correlação de pearson das minhas tarefas')
    st_echarts(graficos(table=df_filtrado).mapa_valor(categorias=categorias), height="500px")
        

with st.container(border=True, height=400):
    st.subheader('Atividades realizadas por dia')
    st_echarts(graficos(table=df_filtrado).grefico_calendario(categorias=categorias), height="300px", key="echarts")

