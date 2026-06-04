import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from auth import exigir_login

st.set_page_config(layout="wide", page_title="Habit Tracker")

usuario_id = exigir_login()

st.title("🏠 Habit Tracker")
st.write("Use o menu lateral para navegar entre Dashboard e Configurações.")
st.info("Registre seus hábitos pelo WhatsApp e acompanhe sua evolução aqui.")
