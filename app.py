import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Guardias Jaén", layout="wide", page_icon="🏥")

# --- URL DIRECTA ---
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xfmfV4Rj3OXC1NL9BU89Lmh11DRk7LC9VcLApBsznnU/edit?usp=sharing"

# --- INICIALIZAR CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(nombre_pestana):
    try:
        # ttl=0 es vital para leer datos reales, no de memoria
        return conn.read(spreadsheet=URL_HOJA, worksheet=nombre_pestana, ttl=0)
    except Exception:
        return pd.DataFrame()

def guardar_datos(nombre_pestana, df):
    try:
        # Guardamos en la nube
        conn.update(spreadsheet=URL_HOJA, worksheet=nombre_pestana, data=df)
        # IMPORTANTE: Limpiamos TODA la caché de Streamlit para que vea el cambio
        st.cache_data.clear()
        time.sleep(1) # Damos 1 segundo de margen a Google
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- NAVEGACIÓN ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

# Contador para resetear formularios
if 'form_count' not in st.session_state:
    st.session_state.form_count = 0

def ir_a(p):
    st.session_state.pagina = p
    st.rerun()

# ---------------------------------------------------------
# PANTALLA INICIAL
# ---------------------------------------------------------
if st.session_state.pagina == 'inicio':
    st.title("🏥 Gestión de Guardias - Distrito Jaén")
    st.write("---")
    col1, col2 = st.columns(2)
    if col1.button("📝 ACCESO PROFESIONAL", use_container_width=True): ir_a('profesional')
    if col2.button("🔐 ACCESO ADMINISTRADOR", use_container_width=True): ir_a('admin_login')

# ---------------------------------------------------------
# LOGIN ADMIN
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_login':
    st.title("🔐 Acceso Administrativo")
    pwd = st.text_input("Contraseña:", type="password")
    if st.button("Entrar"):
        if pwd == "@1234#": ir_a('admin_panel')
        else: st.error("Contraseña incorrecta")
    if st.button("Volver"): ir_a('inicio')

# ---------------------------------------------------------
# PANEL PROFESIONAL
# ---------------------------------------------------------
elif st.session_state.pagina == 'profesional':
    st.title("Nueva Solicitud")
    if st.button("← Volver"): ir_a('inicio')
    
    df_p = cargar_datos("Profesionales")
    
    if df_p.empty:
        st.warning("⚠️ No hay profesionales. Regístralos primero en el Panel Admin.")
    else:
        nombres = sorted(df_p["Nombre y Apellidos"].tolist())
        # El key=st.session_state.form_count hace que el formulario se limpie al cambiar el número
        with st.form(key=f"form_sol_{st.session_state.form_count}"):
            sol = st.selectbox("Tu Nombre:", [""] + nombres)
            tipo = st.radio("Operación:", ["Cambio de guardia", "Cesión de guardia"], horizontal=True)
            fecha = st.date_input("Fecha de la guardia:")
            rec = st.selectbox("¿Quién asume la guardia?", [""] + nombres)
            
            if st.form_submit_button("REGISTRAR SOLICITUD"):
                if sol and rec and sol != rec:
                    df_s = cargar_datos("Solicitudes")
                    datos_sol = df_p[df_p["Nombre y Apellidos"] == sol].iloc[0]
                    
                    nuevo_id = 1 if df_s.empty else int(pd.to_numeric(df_s["ID"]).max() + 1)
                    nueva_fila = pd.DataFrame([{
                        "ID": nuevo_id,
                        "Fecha_Solicitud": datetime.now().strftime('%d/%m/%Y'),
                        "Tipo": tipo,
                        "Solicitante": sol,
                        "SUAP_Origen": datos_sol["SUAP"],
                        "Correo_Solicitante": datos_sol["Correo"],
                        "Fecha_Evento": fecha.strftime('%d/%m/%Y'),
                        "Receptor": rec,
                        "Estado": "Pendiente"
                    }])
                    
                    if guardar_datos("Solicitudes", pd.concat([df_s, nueva_fila], ignore_index=True)):
                        st.session_state.form_count += 1 # Esto limpia los campos
                        st.success(f"✅ ¡Guardado en Google Sheets! (ID {nuevo_id})")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("Datos incompletos o nombres iguales.")

# ---------------------------------------------------------
# PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_panel':
    st.title("⚙️ Gestión Administrativa")
    if st.sidebar.button("Cerrar Sesión"): ir_a('inicio')

    t1, t2 = st.tabs(["Solicitudes", "Gestionar Personal"])

    with t1:
        df_s = cargar_datos("Solicitudes")
        st.dataframe(df_s, use_container_width=True, hide_index=True)
        if not df_s.empty:
            id_sel = st.selectbox("Gestionar ID:", df_s["ID"].tolist())
            acc = st.selectbox("Acción:", ["Aceptar ✅", "Rechazar ❌", "ELIMINAR 🗑️"])
            if st.button("Confirmar en la Nube"):
                if acc == "ELIMINAR 🗑️": df_s = df_s[df_s["ID"] != id_sel]
                else: df_s.loc[df_s["ID"] == id_sel, "Estado"] = acc
                if guardar_datos("Solicitudes", df_s):
                    st.success("Actualizado."); st.rerun()

    with t2:
        st.subheader("Alta de Profesionales")
        # Formulario que se limpia solo tras guardar
        with st.form(key=f"form_prof_{st.session_state.form_count}"):
            n = st.text_input("Nombre y Apellidos")
            s = st.text_input("SUAP / Centro")
            m = st.text_input("Email")
            if st.form_submit_button("Añadir Profesional"):
                if n and s:
                    df_p = cargar_datos("Profesionales")
                    nueva_p = pd.DataFrame([{"Nombre y Apellidos": n, "SUAP": s, "Correo": m}])
                    if guardar_datos("Profesionales", pd.concat([df_p, nueva_p], ignore_index=True)):
                        st.session_state.form_count += 1 # Limpia campos
                        st.success("Profesional añadido con éxito.")
                        time.sleep(1)
                        st.rerun()
        
        st.write("---")
        df_p_list = cargar_datos("Profesionales")
        st.dataframe(df_p_list, use_container_width=True)