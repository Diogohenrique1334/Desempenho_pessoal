import os
import uuid

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from streamlit_echarts import st_echarts

from auth import exigir_login

st.set_page_config(layout="wide", page_title="Dashboard")


@st.cache_data(ttl=300)
def carregar_dados(usuario_id: str) -> pd.DataFrame:
    engine = create_engine(os.getenv("DATABASE_URL", ""))
    query = text("""
        SELECT
            r.data,
            hc.nome    AS habito,
            hc.tipo,
            rv.valor
        FROM registros r
        JOIN registros_valor rv ON rv.registro_id = r.id
        JOIN habitos_config  hc ON hc.id = rv.habito_id
        WHERE r.usuario_id = :uid
          AND hc.ativo = true
        ORDER BY r.data
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"uid": usuario_id})


def preparar_bool(df: pd.DataFrame) -> pd.DataFrame:
    df_bool = df[df["tipo"] == "bool"].copy()
    df_bool["feito"] = df_bool["valor"] == "true"
    return df_bool


def aderencia_por_habito(df_bool: pd.DataFrame) -> pd.DataFrame:
    return (
        df_bool.groupby("habito")["feito"]
        .mean()
        .reset_index()
        .rename(columns={"feito": "aderencia"})
        .sort_values("aderencia", ascending=False)
    )


# --- RENDER ---

usuario_id = exigir_login()
df = carregar_dados(str(usuario_id))

if df.empty:
    st.info("Nenhum dado registrado ainda. Comece pelo WhatsApp! 💬")
    st.stop()

df_bool = preparar_bool(df)
ader = aderencia_por_habito(df_bool)

st.title("📊 Seu Desempenho")

# Métricas de topo
total_dias = df["data"].nunique()
aderencia_total = df_bool["feito"].mean() if not df_bool.empty else 0

col1, col2 = st.columns(2)
col1.metric("Total de dias registrados", total_dias)
col2.metric("Aderência geral", f"{aderencia_total:.0%}")

st.divider()

# Gráfico de barras — aderência por hábito
if not ader.empty:
    st.subheader("Aderência por hábito")
    options = {
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": ader["habito"].tolist()},
        "yAxis": {"type": "value", "max": 1, "axisLabel": {"formatter": "{value:.0%}"}},
        "series": [{
            "type": "bar",
            "data": [round(v, 4) for v in ader["aderencia"].tolist()],
            "itemStyle": {"color": "#18990b"},
            "label": {"show": True, "formatter": "{c:.0%}", "position": "top"},
        }],
    }
    st_echarts(options, height="350px")

# Evolução semanal
st.subheader("Aderência semanal")
if not df_bool.empty:
    df_bool["semana"] = pd.to_datetime(df_bool["data"]).dt.to_period("W").dt.start_time.dt.strftime("%d/%m")
    semanal = df_bool.groupby("semana")["feito"].mean().reset_index()
    options_sem = {
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": semanal["semana"].tolist()},
        "yAxis": {"type": "value", "max": 1, "axisLabel": {"formatter": "{value:.0%}"}},
        "series": [{
            "type": "line",
            "data": [round(v, 4) for v in semanal["feito"].tolist()],
            "smooth": True,
            "itemStyle": {"color": "#18990b"},
            "areaStyle": {"opacity": 0.2},
        }],
    }
    st_echarts(options_sem, height="300px")
