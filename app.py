import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Guardias Jaén", layout="wide", page_icon="🏥")

# --- URL DIRECTA DE TU GOOGLE SHEET ---
# Usamos esta URL directamente para evitar errores de conexión con Secrets
URL_HOJA = "https://docs.google.com/spreadsheets/d/1xfmfV4Rj3OXC1NL9BU89Lmh11DRk7LC9VcLApBsznnU/edit?usp=sharing"

# --- INICIALIZAR CONEXIÓN ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")

# --- FUNCIONES DE LECTURA Y ESCRITURA ---
def cargar_datos(nombre_pestana):
    try:
        # Forzamos la lectura usando la URL directa y el nombre de la pestaña
        return conn.read(spreadsheet=URL_HOJA, worksheet=nombre_pestana, ttl=0)
    except Exception:
        # Si falla (ej. pestaña vacía o no creada), devolvemos tabla vacía
        return pd.DataFrame()

def guardar_datos(nombre_pestana, df):
    try:
        # Forzamos la actualización en la URL directa
        conn.update(spreadsheet=URL_HOJA, worksheet=nombre_pestana, data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error al guardar cambios: {e}")

# --- GESTIÓN DE NAVEGACIÓN ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

def ir_a(p):
    st.session_state.pagina = p
    st.rerun()

# ---------------------------------------------------------
# PANTALLA DE INICIO
# ---------------------------------------------------------
if st.session_state.pagina == 'inicio':
    st.title("🏥 Gestión de Guardias - Distrito Jaén")
    st.write("---")
    col1, col2 = st.columns(2)
    if col1.button("📝 ACCESO PROFESIONAL", use_container_width=True):
        ir_a('profesional')
    if col2.button("🔐 ACCESO ADMINISTRADOR", use_container_width=True):
        ir_a('admin_login')

# ---------------------------------------------------------
# LOGIN ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_login':
    st.title("🔐 Acceso Administrativo")
    pwd = st.text_input("Contraseña:", type="password")
    c1, c2 = st.columns(2)
    if c1.button("Entrar", use_container_width=True):
        if pwd == "@1234#":
            ir_a('admin_panel')
        else:
            st.error("Contraseña incorrecta")
    if c2.button("Volver", use_container_width=True):
        ir_a('inicio')

# ---------------------------------------------------------
# PANEL PROFESIONAL
# ---------------------------------------------------------
elif st.session_state.pagina == 'profesional':
    st.title("Nueva Solicitud")
    if st.button("← Volver"):
        ir_a('inicio')
    
    df_p = cargar_datos("Profesionales")
    
    if df_p.empty or "Nombre y Apellidos" not in df_p.columns:
        st.warning("⚠️ Debes registrar profesionales primero en el Panel de Administrador.")
    else:
        nombres = sorted(df_p["Nombre y Apellidos"].tolist())
        with st.form("form_registro"):
            sol = st.selectbox("Tu Nombre:", [""] + nombres)
            tipo = st.radio("Operación:", ["Cambio de guardia", "Cesión de guardia"], horizontal=True)
            fecha = st.date_input("Fecha de la guardia:")
            rec = st.selectbox("¿Quién asume la guardia?", [""] + nombres)
            
            if st.form_submit_button("REGISTRAR SOLICITUD"):
                if sol and rec and sol != rec:
                    df_s = cargar_datos("Solicitudes")
                    datos_solicitante = df_p[df_p["Nombre y Apellidos"] == sol].iloc[0]
                    
                    nuevo_id = 1 if df_s.empty else int(df_s["ID"].max() + 1)
                    nueva_fila = pd.DataFrame([{
                        "ID": nuevo_id,
                        "Fecha_Solicitud": datetime.now().strftime('%d/%m/%Y'),
                        "Tipo": tipo,
                        "Solicitante": sol,
                        "SUAP_Origen": datos_solicitante["SUAP"],
                        "Correo_Solicitante": datos_solicitante["Correo"],
                        "Fecha_Evento": fecha.strftime('%d/%m/%Y'),
                        "Receptor": rec,
                        "Estado": "Pendiente"
                    }])
                    
                    df_final = pd.concat([df_s, nueva_fila], ignore_index=True)
                    guardar_datos("Solicitudes", df_final)
                    st.success(f"✅ Registrado con ID {nuevo_id}")
                else:
                    st.error("Revisa que los nombres sean distintos.")

# ---------------------------------------------------------
# PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_panel':
    st.title("⚙️ Panel de Gestión")
    if st.sidebar.button("Cerrar Sesión"):
        ir_a('inicio')

    t1, t2, t3 = st.tabs(["Validar Solicitudes", "Gestionar Personal", "📊 Estadísticas"])

    with t1:
        df_s = cargar_datos("Solicitudes")
        st.dataframe(df_s, use_container_width=True, hide_index=True)
        if not df_s.empty:
            st.divider()
            ca, cb, cc = st.columns(3)
            id_sel = ca.selectbox("ID a gestionar:", df_s["ID"].tolist())
            accion = cb.selectbox("Acción:", ["Aceptar ✅", "Rechazar ❌", "ELIMINAR 🗑️"])
            if cc.button("Ejecutar en la Nube", use_container_width=True):
                if accion == "ELIMINAR 🗑️":
                    df_s = df_s[df_s["ID"] != id_sel]
                else:
                    df_s.loc[df_s["ID"] == id_sel, "Estado"] = accion
                guardar_datos("Solicitudes", df_s)
                st.rerun()

    with t2:
        st.subheader("Alta de Profesionales")
        with st.form("alta_p"):
            n = st.text_input("Nombre y Apellidos")
            s = st.text_input("SUAP / Centro")
            m = st.text_input("Email")
            if st.form_submit_button("Guardar en Google Sheets"):
                df_p = cargar_datos("Profesionales")
                nueva_p = pd.DataFrame([{"Nombre y Apellidos": n, "SUAP": s, "Correo": m}])
                df_p = pd.concat([df_p, nueva_p], ignore_index=True)
                guardar_datos("Profesionales", df_p)
                st.rerun()
        
        df_listado = cargar_datos("Profesionales")
        st.dataframe(df_listado, use_container_width=True)

    with t3:
        st.subheader("📊 Estadísticas de Guardias")
        df_s = cargar_datos("Solicitudes")
        if not df_s.empty:
            df_ok = df_s[df_s["Estado"].str.contains("Aceptar", na=False)]
            if not df_ok.empty:
                st.bar_chart(df_ok["Solicitante"].value_counts())
                st.bar_chart(df_ok["SUAP_Origen"].value_counts())
            else:
                st.info("No hay guardias aceptadas todavía.")