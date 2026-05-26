import pandas as pd
from PIL import Image
from streamlit_echarts import st_echarts
import funcoes as fc
from funcoes import graficos
import streamlit as st
import datetime as dt
import re
import plotly.express as px


#Ajustes variáveis
#df = fc(fc(fc(df).tratamento_hora()).tempo_sono_n()).Humor()
#df = fc(df).tratamento_hora()
df = fc.dados().carregar_dados()

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

#df_filtrado['Tempo de sono'] = df_filtrado['Tempo de sono'].map(lambda x: x.total_seconds() / 3600)

with st.container(border = True, height = 400 ):
    col1, col2 = st.columns([2,5])

    with col1.container(border = True, height = 350 ):

        st.plotly_chart(px.violin(
            df_filtrado, 
            y="Tempo de sono", 
            box=True,
            color_discrete_sequence=['#18990b']
            ))

    with col2.container(border = True, height = 350 ):
        st.plotly_chart(graficos(df_filtrado.pivot_table(index='Dia da semana',
                    values='Tempo de sono',
                    aggfunc='mean')['Tempo de sono']).grafico_barras('horas de sono por dia da semana'))

    st.plotly_chart(graficos(df_filtrado.pivot_table(index='mes',
                values='Tempo de sono',
                aggfunc='mean')['Tempo de sono']).grafico_barras('horas de sono por mês'))
    
    st.plotly_chart(graficos(df_filtrado.pivot_table(index=df_filtrado.reset_index().Data.dt.isocalendar()['week'].values,
                values='Tempo de sono',
                aggfunc='mean')['Tempo de sono']).grafico_barras('horas de sono por semana'))
    
with st.container(border = True, height = 400):
    st.subheader('Horas de sono por dia')
    st_echarts(graficos(table=df_filtrado).grefico_calendario(categorias='Tempo de sono',ano_1=2024,ano_2=2025,ano_3=2026), height=500, key="echarts")

