import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Guardias Jaén", layout="wide", page_icon="🏥")

# --- CONEXIÓN OFICIAL ---
# Automáticamente usará los Secrets que configuramos
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(pestana):
    try:
        return conn.read(worksheet=pestana, ttl=0).dropna(how="all")
    except:
        return pd.DataFrame()

def guardar_datos(pestana, df):
    try:
        conn.update(worksheet=pestana, data=df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- GESTIÓN DE PÁGINAS ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

def ir_a(p):
    st.session_state.pagina = p
    st.rerun()

# ---------------------------------------------------------
# 🏠 INICIO
# ---------------------------------------------------------
if st.session_state.pagina == 'inicio':
    st.title("🏥 Gestión de Guardias - Distrito Jaén")
    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("📝 ACCESO PROFESIONAL", use_container_width=True): ir_a('profesional')
    if c2.button("🔐 ACCESO ADMINISTRADOR", use_container_width=True): ir_a('admin_login')

# ---------------------------------------------------------
# 🔐 LOGIN ADMIN
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_login':
    st.title("Acceso Administrativo")
    pwd = st.text_input("Contraseña:", type="password")
    if st.button("Entrar"):
        if pwd == "@1234#": ir_a('admin_panel')
        else: st.error("Incorrecta")
    if st.button("Volver"): ir_a('inicio')

# ---------------------------------------------------------
# 🧑‍⚕️ PANEL PROFESIONAL
# ---------------------------------------------------------
elif st.session_state.pagina == 'profesional':
    st.title("Nueva Solicitud")
    if st.button("← Volver"): ir_a('inicio')
    
    df_p = cargar_datos("Profesionales")
    
    if df_p.empty:
        st.warning("No hay profesionales registrados. Contacte con el administrador.")
    else:
        nombres = sorted(df_p["Nombre y Apellidos"].tolist())
        with st.form("form_sol"):
            sol = st.selectbox("Tu Nombre:", [""] + nombres)
            tipo = st.radio("Tipo:", ["Cambio de guardia", "Cesión de guardia"], horizontal=True)
            f_g = st.date_input("Fecha de la guardia:")
            rec = st.selectbox("¿Quién asume la guardia?", [""] + nombres)
            
            if st.form_submit_button("REGISTRAR"):
                if sol and rec and sol != rec:
                    df_s = cargar_datos("Solicitudes")
                    if df_s.empty:
                        df_s = pd.DataFrame(columns=["ID", "Fecha_Solicitud", "Tipo", "Solicitante", "Fecha_Evento", "Receptor", "Estado"])
                    
                    nuevo_id = 1 if df_s.empty else int(pd.to_numeric(df_s["ID"]).max() + 1)
                    nueva_fila = pd.DataFrame([{
                        "ID": nuevo_id,
                        "Fecha_Solicitud": datetime.now().strftime('%d/%m/%Y'),
                        "Tipo": tipo,
                        "Solicitante": sol,
                        "Fecha_Evento": f_g.strftime('%d/%m/%Y'),
                        "Receptor": rec,
                        "Estado": "Pendiente"
                    }])
                    
                    if guardar_datos("Solicitudes", pd.concat([df_s, nueva_fila], ignore_index=True)):
                        st.success(f"✅ Registrado ID {nuevo_id}"); time.sleep(2); ir_a('inicio')
                else:
                    st.error("Revisa los nombres.")

# ---------------------------------------------------------
# ⚙️ PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_panel':
    st.title("⚙️ Panel de Control")
    if st.sidebar.button("Cerrar Sesión"): ir_a('inicio')

    tab1, tab2 = st.tabs(["Solicitudes", "Gestionar Personal"])

    with tab1:
        df_s = cargar_datos("Solicitudes")
        st.dataframe(df_s, use_container_width=True)
        if not df_s.empty:
            id_sel = st.selectbox("Selecciona ID:", df_s["ID"].tolist())
            acc = st.selectbox("Acción:", ["Aceptada ✅", "Rechazada ❌", "ELIMINAR 🗑️"])
            if st.button("Ejecutar"):
                if acc == "ELIMINAR 🗑️": df_s = df_s[df_s["ID"] != id_sel]
                else: df_s.loc[df_s["ID"] == id_sel, "Estado"] = acc
                if guardar_datos("Solicitudes", df_s):
                    st.success("Hecho"); st.rerun()

    with tab2:
        st.subheader("Alta de Profesionales")
        with st.form("alta_p"):
            n = st.text_input("Nombre y Apellidos")
            s = st.text_input("SUAP")
            e = st.text_input("Email")
            if st.form_submit_button("Añadir"):
                df_p = cargar_datos("Profesionales")
                if df_p.empty: df_p = pd.DataFrame(columns=["Nombre y Apellidos", "SUAP", "Correo"])
                nuevo = pd.DataFrame([{"Nombre y Apellidos": n, "SUAP": s, "Correo": e}])
                if guardar_datos("Profesionales", pd.concat([df_p, nuevo], ignore_index=True)):
                    st.success("Guardado"); st.rerun()
        
        st.dataframe(cargar_datos("Profesionales"), use_container_width=True)