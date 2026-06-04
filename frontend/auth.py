"""
Mapeia o email Google (via st.login) para o usuario_id no banco.
Se o email não estiver vinculado a nenhum usuário, retorna None.
"""

import os
import uuid

import streamlit as st
from sqlalchemy import create_engine, text


def get_engine():
    return create_engine(os.getenv("DATABASE_URL", ""))


def get_usuario_id(email: str) -> uuid.UUID | None:
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM usuarios WHERE email = :email AND ativo = true"),
            {"email": email},
        ).fetchone()
    return uuid.UUID(str(row[0])) if row else None


def exigir_login() -> uuid.UUID:
    """
    Garante que o usuário está logado e vinculado a um usuário do banco.
    Retorna o usuario_id ou interrompe com st.stop().
    """
    user = st.experimental_user
    if not user or not getattr(user, "email", None):
        st.warning("Faça login com o Google para continuar.")
        if st.button("Entrar com Google"):
            st.login()
        st.stop()

    usuario_id = get_usuario_id(user.email)
    if usuario_id is None:
        st.error(
            "Seu e-mail ainda não está vinculado a nenhuma conta. "
            "Entre em contato com o administrador."
        )
        st.stop()

    return usuario_id
