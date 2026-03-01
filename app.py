import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Guardias Jaén", layout="wide", page_icon="🏥")

# --- SOLUCIÓN DIRECTA (Sin depender de Secrets externos) ---
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xfmfV4Rj3OXC1NL9BU89Lmh11DRk7LC9VcLApBsznnU/edit?usp=sharing"

try:
    # Forzamos la conexión con la URL escrita aquí mismo
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.error("Error al inicializar la conexión.")

def cargar_datos(pestana):
    try:
        # Le pasamos la URL directamente en el comando read
        return conn.read(spreadsheet=URL_HOJA, worksheet=pestana, ttl=0)
    except Exception as e:
        st.error(f"Error al leer '{pestana}': {e}")
        return pd.DataFrame()

def guardar_datos(pestana, df):
    try:
        # Le pasamos la URL directamente en el comando update
        conn.update(spreadsheet=URL_HOJA, worksheet=pestana, data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# ... (El resto del código de navegación y paneles que ya tienes)