
import datetime as dt
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import plotly.express as px
from streamlit_echarts import st_echarts
from dotenv import load_dotenv
load_dotenv()
import os
from sqlalchemy import create_engine
"""
Melhorias:
1° grafico por tarefas: usar a mesma funçao para mês e horas

2° grafico de calendário, selecionar os meses automáticamente
"""

scaler = MinMaxScaler()

#funcoes_globais
def substituir_outliers(valor):
    if pd.isna(valor):
        return valor
    # Definindo o limite de tempo de sono
    limite = pd.Timedelta(days=1)
    
    if valor > limite:
        return pd.NaT
    return valor

class ajustes_variaveis:

    def __init__(self,table):

        self.table = table

    def Humor(self,table = None):

        if table is None:
            table = self.table
        else:
            table

        table['Humor'] = table.apply(lambda x: (x['Nota do humor'] + x['Nota do humor fim do dia']) / 2, axis = 1)

        return table
    
class graficos:

    def __init__(self,table = None, colunas = None):
        
        self.table = table
        self.colunas = colunas

    def aderencia_hora(self, categoria_x, categorias, titulo):
        self.table = self.table
        self.categoria_x = categoria_x
        self.categorias = categorias
        self.titulo = titulo

        aderencia_por_hora = px.bar(
            self.table[self.table[self.categoria_x].dt.hour != 0].pivot_table(index=self.table[self.categoria_x].dt.hour, values=self.categorias, aggfunc='mean')
            ,title=self.titulo)
        
        aderencia_por_hora.update_layout(yaxis_title='')
        
        return aderencia_por_hora
    
    def aderencia_mes(self, categoria_x, categorias, titulo):
        self.table = self.table
        self.categoria_x = categoria_x
        self.categorias = categorias
        self.titulo = titulo

        aderencia_por_hora = px.bar(
            self.table.pivot_table(index=self.categoria_x, values=self.categorias, aggfunc='mean')
            ,title=self.titulo
            
            )
        
        aderencia_por_hora.update_layout(yaxis_title='')
        
        return aderencia_por_hora
        
    def grafico_barras(self,titulo,cor = None, tamanho = 350):

        if cor is None:
            cor = ['#18990b']

        aderencia_categorias = px.bar(self.table, x=self.table.index, y=self.table.values, title=titulo,height=tamanho, color_discrete_sequence=cor)

        aderencia_categorias.update_layout(yaxis_title='',xaxis_title='')

        return aderencia_categorias
    
    def liquid_fill(self, valor):
        liquidfill_option = {
            "title": {
                "text": "Aderência total",
                "left": "center",
                "textStyle": {
                    "fontSize": 20,
                    "fontWeight": "bold",
                    "color": "#ffffff"
                }
            },
            "series": [{
                "type": 'liquidFill',
                "data": [valor],
                "center": ['50%', '50%'],
                "radius": '50%',
                "waveAnimation": True,
                "outline": {
                    "show": True,
                    "borderDistance": 8,
                    "itemStyle": {
                        "borderWidth": 4,
                        "borderColor": "#ffffff"
                    }
                },
                "backgroundStyle": {
                    "color": "#ffffff"
                },
                "label": {
                    "normal": {
                        
                        "textStyle": {
                            "fontSize": 20,
                            "color": '#18990b'
                        }
                    }
                },
                "color":['#18990b']
            }]
        }

        return liquidfill_option

    def grafico_linhas_tempo(self,coluna_data,categorias,titulo,cor = ['#18990b'],tamanho = 350 ):

        linha_tempo_aderencia = px.bar(
            self.table.set_index(coluna_data)[categorias].squeeze().resample('m').mean().asfreq('m').reset_index().melt(coluna_data).dropna(subset = 'value').drop(columns ='variable').groupby(coluna_data)['value'].mean()
        , title=titulo,height=tamanho,color_discrete_sequence=cor)

        #linha_tempo_aderencia.update_traces(mode='lines+markers')

        linha_tempo_aderencia.update_layout(
            showlegend=False,
            yaxis_title='Aderência',
            xaxis_title='Data',
            #title_x=0.5, # Centralizar o título
            #title_font=dict(size=20, family='Arial', color='#30509c'), # Personalizar fonte do título
            xaxis=dict(
                tickangle=-45, # Rotacionar rótulos do eixo x para melhor legibilidade
                showgrid=False, # Mostrar linhas de grade
                gridcolor='LightGray' # Personalizar cor da grade
            ),
            yaxis=dict(
                showgrid=True, # Mostrar linhas de grade
                gridcolor='LightGray' # Personalizar cor da grade
            ),
            plot_bgcolor='rgba(0,0,0,0)', # Definir cor de fundo do gráfico como transparente
            paper_bgcolor='rgba(0,0,0,0)' # Definir cor de fundo do papel como transparente
        )

        return linha_tempo_aderencia
    
    def grefico_calendario(self, categorias, ano_1, ano_2, ano_3):

        # --- 1) Preparação dos dados ---
        # categorias deve ser uma lista de colunas; 'Data' precisa estar no index do self.table
        # Vamos derreter -> somar por dia -> garantir tipos corretos
        df = (
            self.table[categorias]
            .reset_index()  # traz 'Data' para coluna
            .melt(id_vars='Data', var_name='Categoria', value_name='value')
        )

        # Tipos corretos
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df['value'] = pd.to_numeric(df['value'], errors='coerce')

        # Remove linhas inválidas e agrega por dia
        datas = (
            df.dropna(subset=['Data'])  # mantém linhas com Data válida (valor pode ser NaN e virar None)
            .pivot_table(index='Data', values='value', aggfunc='sum')
            .sort_index()
        )

        # --- 2) Helpers para converter para tipos nativos/serializáveis ---
        def _to_date_str(idx):
            # ECharts (calendário) gosta de "YYYY-MM-DD"
            return idx.strftime("%Y-%m-%d")

        def _to_native_val(x):
            # None para NaN/<NA>; int nativo para numéricos
            if pd.isna(x):
                return None  # ou 0, se preferir preencher vazio
            return int(x)

        def _build_year(y: int):
            out = []
            if datas.empty:
                return out
            # Evita iterrows; usamos index + values e filtramos pelo ano
            for idx, val in zip(datas.index, datas['value'].values):
                if isinstance(idx, pd.Timestamp) and not pd.isna(idx) and idx.year == y:
                    out.append([_to_date_str(idx), _to_native_val(val)])
            return out

        data_1 = _build_year(ano_1)
        data_2 = _build_year(ano_2)
        data_3 = _build_year(ano_3)

        # Max para o visualMap (float nativo; fallback quando NaN)
        if datas.empty:
            vmax_native = 1.0
        else:
            vmax = pd.to_numeric(datas['value'], errors='coerce').max()
            vmax_native = float(vmax) if pd.notna(vmax) else 1.0

        # --- 3) Opções do ECharts ---
        option1 = {
            "tooltip": {"position": "top"},
            "visualMap": {
                "min": 0,
                "max": vmax_native,
                "calculable": True,
                "orient": "horizontal",
                "left": "center",
                # Use o esquema de cores padrão do ECharts via inRange
                "inRange": {"color": ["#cac2c2", "#18990b"]},  # claro -> escuro
            },
            "calendar": [
                {  # Calendário ano_1
                    "range": str(ano_1),
                    "cellSize": ["auto", 14],
                    "top": "7%",
                    "splitLine": {"lineStyle": {"color": "#000000"}},
                    "itemStyle": {"color": "#ffffff"},
                    "dayLabel": {"color": "#ffffff"},
                    "monthLabel": {"color": "#ffffff"},
                    "yearLabel": {"color": "#cac2c2"},
                },
                {  # Calendário ano_2
                    "range": str(ano_2),
                    "cellSize": ["auto", 14],
                    "top": "33%",
                    "splitLine": {"lineStyle": {"color": "#000000"}},
                    "itemStyle": {"color": "#ffffff"},
                    "dayLabel": {"color": "#ffffff"},
                    "monthLabel": {"color": "#ffffff"},
                    "yearLabel": {"color": "#cac2c2"},
                },
                {  # Calendário ano_3
                    "range": str(ano_3),
                    "cellSize": ["auto", 14],
                    "top": "60%",
                    "splitLine": {"lineStyle": {"color": "#000000"}},
                    "itemStyle": {"color": "#ffffff"},
                    "dayLabel": {"color": "#ffffff"},
                    "monthLabel": {"color": "#ffffff"},
                    "yearLabel": {"color": "#cac2c2"},
                },
            ],
            "series": [
                {
                    "type": "heatmap",
                    "coordinateSystem": "calendar",
                    "calendarIndex": 0,
                    "data": data_1,
                },
                {
                    "type": "heatmap",
                    "coordinateSystem": "calendar",
                    "calendarIndex": 1,
                    "data": data_2,
                },
                {
                    "type": "heatmap",
                    "coordinateSystem": "calendar",
                    "calendarIndex": 2,
                    "data": data_3,
                },
            ],
        }

        # --- 4) Blindagem final contra tipos NumPy/Pandas no dicionário ---
        def to_native(obj):
            from datetime import date, datetime
            if isinstance(obj, (np.integer,)):  # np.int64 -> int
                return int(obj)
            if isinstance(obj, (np.floating,)):  # np.float64 -> float
                return float(obj)
            if isinstance(obj, (np.bool_,)):  # np.bool_ -> bool
                return bool(obj)
            if isinstance(obj, (pd.Timestamp, datetime)):  # datas -> string ISO
                return obj.isoformat()
            if obj is pd.NaT:
                return None
            if isinstance(obj, np.ndarray):
                return [to_native(x) for x in obj.tolist()]
            if isinstance(obj, (list, tuple, set)):
                return [to_native(x) for x in obj]
            if isinstance(obj, dict):
                return {str(k): to_native(v) for k, v in obj.items()}
            return obj

        return to_native(option1)

    def mapa_valor(self, categorias):

        corr = self.table[np.append([x for x in categorias],['Tempo de sono','Humor'])].squeeze().resample('W').mean().asfreq('W').corr()

        data_serialized = corr.fillna(0).round(2).reset_index().melt(id_vars='index').values.tolist()


        option = {
            "tooltip": {"position": "top"},
            "grid": {"height": "50%", "top": "10%"},
            "xAxis": {"type": "category", "data": corr.columns.tolist(), "splitArea": {"show": True},"axisLabel": {"rotate": "20"}},
            "yAxis": {"type": "category", "data": corr.index.tolist(), "splitArea": {"show": True}},
            "visualMap": {
                "min": -1,
                "max": 1,
                "calculable": True,
                "orient": "horizontal",
                "left": "center",
                "top":"top",
                "bottom": "15%",
                "color": ['#18990b', '#cac2c2'],
            },
            "series": [
                {
                    "name": "Punch Card",
                    "type": "heatmap",
                    "data": data_serialized,
                    "label": {"show": True},
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowColor": "rgba(0, 0, 0, 0.47)",
                            "color": "#000000",  # Cor do item
                            "borderColor": "#000000",  # Cor da borda
                            "borderWidth": 2,  # Largura da borda
                            "borderType": "solid",  # Tipo de borda
                            "shadowOffsetX": 5,  # Deslocamento horizontal da sombra
                            "shadowOffsetY": 5,  # Deslocamento vertical da sombra
                            "opacity": 0.8  # Opacidade do item
                        }
                    },
                }
            ],
        }

        return option
