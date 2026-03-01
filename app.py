import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Guardias Jaén", layout="wide", page_icon="🏥")

# --- CONEXIÓN ---
# Utiliza los Secrets configurados con la Cuenta de Servicio
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(pestana):
    try:
        # Lee los datos eliminando filas que estén totalmente vacías
        df = conn.read(worksheet=pestana, ttl=0)
        return df.dropna(how="all")
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

# --- GESTIÓN DE NAVEGACIÓN ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

def ir_a(p):
    st.session_state.pagina = p
    st.rerun()

# ---------------------------------------------------------
# 🏠 PANTALLA DE INICIO
# ---------------------------------------------------------
if st.session_state.pagina == 'inicio':
    st.title("🏥 Gestión de Guardias - Distrito Jaén")
    st.markdown("### Bienvenido al sistema de gestión de cambios y cesiones")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("Área para que los profesionales soliciten cambios.")
        if st.button("📝 ACCESO PROFESIONAL", use_container_width=True):
            ir_a('profesional')
    with col2:
        st.warning("Área restringida para gestión de cuadrantes.")
        if st.button("🔐 ACCESO ADMINISTRADOR", use_container_width=True):
            ir_a('admin_login')

# ---------------------------------------------------------
# 🔐 LOGIN ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_login':
    st.title("🔐 Acceso Administrativo")
    pwd = st.text_input("Introduce la contraseña maestra:", type="password")
    c1, c2 = st.columns(2)
    if c1.button("Entrar", use_container_width=True):
        if pwd == "@1234#":
            ir_a('admin_panel')
        else:
            st.error("Contraseña incorrecta")
    if c2.button("Volver al Inicio", use_container_width=True):
        ir_a('inicio')

# ---------------------------------------------------------
# 🧑‍⚕️ PANEL PROFESIONAL
# ---------------------------------------------------------
elif st.session_state.pagina == 'profesional':
    st.title("📝 Nueva Solicitud")
    if st.button("← Volver al Menú"):
        ir_a('inicio')
    
    df_p = cargar_datos("Profesionales")
    
    if df_p.empty:
        st.error("⚠️ No hay profesionales registrados en el sistema. Contacte con administración.")
    else:
        # Ordenamos nombres alfabéticamente
        lista_nombres = sorted(df_p["Nombre y Apellidos"].tolist())
        
        with st.form("nueva_solicitud"):
            st.markdown("##### Datos del cambio")
            solicitante = st.selectbox("Selecciona tu nombre:", [""] + lista_nombres)
            tipo = st.radio("Tipo de solicitud:", ["Cambio de guardia", "Cesión de guardia"], horizontal=True)
            fecha_g = st.date_input("Fecha de la guardia a gestionar:", format="DD/MM/YYYY")
            receptor = st.selectbox("¿Quién asume la guardia?", [""] + lista_nombres)
            
            if st.form_submit_button("ENVIAR SOLICITUD PARA VALIDACIÓN"):
                if solicitante and receptor and solicitante != receptor:
                    df_s = cargar_datos("Solicitudes")
                    
                    # Si es la primera vez, creamos el DataFrame con columnas
                    if df_s.empty:
                        df_s = pd.DataFrame(columns=["ID", "Fecha_Solicitud", "Tipo", "Solicitante", "Fecha_Evento", "Receptor", "Estado"])
                    
                    nuevo_id = 1 if df_s.empty else int(pd.to_numeric(df_s["ID"]).max() + 1)
                    
                    nueva_fila = pd.DataFrame([{
                        "ID": nuevo_id,
                        "Fecha_Solicitud": datetime.now().strftime('%d/%m/%Y'),
                        "Tipo": tipo,
                        "Solicitante": solicitante,
                        "Fecha_Evento": fecha_g.strftime('%d/%m/%Y'),
                        "Receptor": receptor,
                        "Estado": "Pendiente"
                    }])
                    
                    if guardar_datos("Solicitudes", pd.concat([df_s, nueva_fila], ignore_index=True)):
                        st.success(f"✅ ¡Éxito! Tu solicitud ha sido registrada con el ID {nuevo_id}.")
                        time.sleep(2)
                        ir_a('inicio')
                else:
                    st.error("Por favor, selecciona los nombres y asegúrate de que no sean la misma persona.")

# ---------------------------------------------------------
# ⚙️ PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_panel':
    st.title("⚙️ Panel de Control Administrativo")
    if st.sidebar.button("Cerrar Sesión"):
        ir_a('inicio')

    tab1, tab2 = st.tabs(["📋 Gestión de Solicitudes", "👥 Gestión de Personal"])

    with tab1:
        st.subheader("Solicitudes Pendientes y Registro")
        df_sol = cargar_datos("Solicitudes")
        
        if df_sol.empty:
            st.info("No hay solicitudes registradas aún.")
        else:
            st.dataframe(df_sol, use_container_width=True, hide_index=True)
            
            st.divider()
            st.markdown("#### Validar o Eliminar Solicitud")
            col_id, col_acc, col_btn = st.columns([1, 1, 1])
            
            id_a_gestionar = col_id.selectbox("Selecciona ID:", df_sol["ID"].tolist())
            nueva_accion = col_acc.selectbox("Cambiar estado a:", ["Aceptada ✅", "Rechazada ❌", "ELIMINAR 🗑️"])
            
            if col_btn.button("Aplicar Cambios", use_container_width=True):
                if nueva_accion == "ELIMINAR 🗑️":
                    df_sol = df_sol[df_sol["ID"] != id_a_gestionar]
                else:
                    df_sol.loc[df_sol["ID"] == id_a_gestionar, "Estado"] = nueva_accion
                
                if guardar_datos("Solicitudes", df_sol):
                    st.success("Registro actualizado correctamente.")
                    st.rerun()

    with tab2:
        st.subheader("Personal del Distrito")
        
        with st.expander("➕ Añadir Nuevo Profesional"):
            with st.form("alta_personal"):
                nom = st.text_input("Nombre y Apellidos")
                suap = st.text_input("SUAP / Centro")
                mail = st.text_input("Correo electrónico")
                if st.form_submit_button("Guardar Profesional"):
                    if nom and suap:
                        df_prof = cargar_datos("Profesionales")
                        if df_prof.empty:
                            df_prof = pd.DataFrame(columns=["Nombre y Apellidos", "SUAP", "Correo"])
                        
                        nuevo_p = pd.DataFrame([{"Nombre y Apellidos": nom, "SUAP": suap, "Correo": mail}])
                        if guardar_datos("Profesionales", pd.concat([df_prof, nuevo_p], ignore_index=True)):
                            st.success(f"{nom} añadido correctamente.")
                            st.rerun()
        
        st.divider()
        df_listado = cargar_datos("Profesionales")
        st.dataframe(df_listado, use_container_width=True, hide_index=True)