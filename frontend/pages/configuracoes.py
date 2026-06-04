import os
import uuid

import streamlit as st
from sqlalchemy import create_engine, text

from auth import exigir_login

st.set_page_config(page_title="Configurações")
st.title("⚙️ Configurações")

usuario_id = exigir_login()


@st.cache_data(ttl=60)
def carregar_habitos(uid: str) -> list[dict]:
    engine = create_engine(os.getenv("DATABASE_URL", ""))
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, nome, tipo, ativo, ordem FROM habitos_config WHERE usuario_id = :uid ORDER BY ordem"),
            {"uid": uid},
        ).fetchall()
    return [{"id": str(r[0]), "nome": r[1], "tipo": r[2], "ativo": r[3], "ordem": r[4]} for r in rows]


def toggle_habito(habito_id: str, ativo: bool) -> None:
    engine = create_engine(os.getenv("DATABASE_URL", ""))
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE habitos_config SET ativo = :ativo WHERE id = :id"),
            {"ativo": ativo, "id": habito_id},
        )
        conn.commit()
    st.cache_data.clear()


habitos = carregar_habitos(str(usuario_id))

if not habitos:
    st.info("Nenhum hábito configurado. Faça o onboarding pelo WhatsApp.")
    st.stop()

st.subheader("Seus hábitos")
st.caption("Desative hábitos que não quer mais registrar (os dados históricos são preservados).")

for h in habitos:
    col1, col2, col3 = st.columns([4, 2, 2])
    col1.write(h["nome"])
    col2.write(f"`{h['tipo']}`")
    novo = col3.toggle("Ativo", value=h["ativo"], key=h["id"])
    if novo != h["ativo"]:
        toggle_habito(h["id"], novo)
        st.rerun()
