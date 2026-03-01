import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Guardias Jaén", layout="wide", page_icon="🏥")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(pestana):
    # ttl=0 asegura que siempre leamos los datos reales del Google Sheet
    return conn.read(worksheet=pestana, ttl=0)

def guardar_datos(pestana, df):
    # Actualiza la hoja en la nube y limpia la memoria caché
    conn.update(worksheet=pestana, data=df)
    st.cache_data.clear()

# --- LÓGICA DE NAVEGACIÓN ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

def navegar_a(p):
    st.session_state.pagina = p
    st.rerun()

# ---------------------------------------------------------
# PANTALLA DE INICIO
# ---------------------------------------------------------
if st.session_state.pagina == 'inicio':
    st.title("🏥 Sistema de Gestión de Guardias")
    st.subheader("Distrito Sanitario Jaén")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 ACCESO PROFESIONAL", use_container_width=True):
            navegar_a('profesional')
    with col2:
        if st.button("🔐 ACCESO ADMINISTRADOR", use_container_width=True):
            navegar_a('admin_login')

# ---------------------------------------------------------
# LOGIN ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_login':
    st.title("Acceso Restringido")
    password = st.text_input("Introduce la contraseña:", type="password")
    c1, c2 = st.columns(2)
    if c1.button("Entrar", use_container_width=True):
        if password == "@1234#":
            navegar_a('admin_panel')
        else:
            st.error("Contraseña incorrecta")
    if c2.button("Volver", use_container_width=True):
        navegar_a('inicio')

# ---------------------------------------------------------
# PANEL PROFESIONAL
# ---------------------------------------------------------
elif st.session_state.pagina == 'profesional':
    st.title("Nueva Solicitud de Cambio/Cesión")
    if st.button("← Volver al Inicio"):
        navegar_a('inicio')
    
    try:
        df_p = cargar_datos("Profesionales")
        if df_p.empty:
            st.warning("No hay profesionales registrados en el sistema.")
        else:
            nombres = sorted(df_p["Nombre y Apellidos"].tolist())
            with st.form("form_nueva_solicitud"):
                solicitante = st.selectbox("Selecciona tu nombre:", [""] + nombres)
                tipo = st.radio("Tipo de operación:", ["Cambio de guardia", "Cesión de guardia"], horizontal=True)
                f_evento = st.date_input("Fecha de la guardia a cambiar/ceder:", format="DD/MM/YYYY")
                receptor = st.selectbox("¿Quién asume la guardia?", [""] + nombres)
                
                if st.form_submit_button("REGISTRAR SOLICITUD"):
                    if solicitante and receptor and solicitante != receptor:
                        df_s = cargar_datos("Solicitudes")
                        datos_prof = df_p[df_p["Nombre y Apellidos"] == solicitante].iloc[0]
                        
                        nuevo_id = 1 if df_s.empty else int(df_s["ID"].max() + 1)
                        
                        nueva_fila = pd.DataFrame([{
                            "ID": nuevo_id,
                            "Fecha_Solicitud": datetime.now().strftime('%d/%m/%Y'),
                            "Tipo": tipo,
                            "Solicitante": solicitante,
                            "SUAP_Origen": datos_prof["SUAP"],
                            "Correo_Solicitante": datos_prof["Correo"],
                            "Fecha_Evento": f_evento.strftime('%d/%m/%Y'),
                            "Receptor": receptor,
                            "Estado": "Pendiente"
                        }])
                        
                        df_final = pd.concat([df_s, nueva_fila], ignore_index=True)
                        guardar_datos("Solicitudes", df_final)
                        st.success(f"✅ Solicitud enviada correctamente (ID: {nuevo_id})")
                    else:
                        st.error("Error: Revisa que hayas seleccionado los nombres y que no sean la misma persona.")
    except Exception as e:
        st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_panel':
    st.title("⚙️ Panel de Control Administrativo")
    if st.sidebar.button("Cerrar Sesión"):
        navegar_a('inicio')

    tab1, tab2, tab3 = st.tabs(["Validar Cambios", "Gestión de Personal", "📊 Estadísticas"])

    # --- TAB 1: VALIDACIÓN ---
    with tab1:
        df_s = cargar_datos("Solicitudes")
        st.subheader("Listado de Solicitudes")
        
        # Filtros
        c1, c2, c3 = st.columns([2,1,1])
        f_nom = c1.text_input("Filtrar por nombre:")
        f_mes = c2.selectbox("Mes:", ["Todos"] + [f"{i:02d}" for i in range(1,13)])
        f_anio = c3.selectbox("Año:", ["Todos", "2024", "2025", "2026"])

        df_f = df_s.copy()
        if f_nom:
            df_f = df_f[df_f["Solicitante"].str.contains(f_nom, case=False, na=False) | df_f["Receptor"].str.contains(f_nom, case=False, na=False)]
        if f_mes != "Todos":
            df_f = df_f[df_f["Fecha_Evento"].astype(str).str.contains(f"/{f_mes}/")]
        if f_anio != "Todos":
            df_f = df_f[df_f["Fecha_Evento"].astype(str).str.contains(f"/{f_anio}")]

        st.dataframe(df_f, use_container_width=True, hide_index=True)

        if not df_f.empty:
            st.divider()
            ca, cb, cc = st.columns(3)
            id_sel = ca.selectbox("Selecciona ID para gestionar:", df_f["ID"].tolist())
            accion = cb.selectbox("Acción:", ["Aceptada ✅", "Rechazada ❌", "ELIMINAR 🗑️"])
            if cc.button("Confirmar en Google Sheets", use_container_width=True):
                if accion == "ELIMINAR 🗑️":
                    df_s = df_s[df_s["ID"] != id_sel]
                else:
                    df_s.loc[df_s["ID"] == id_sel, "Estado"] = accion
                guardar_datos("Solicitudes", df_s)
                st.rerun()

    # --- TAB 2: PERSONAL ---
    with tab2:
        st.subheader("Registro de Profesionales")
        with st.form("alta_prof"):
            col_n, col_s, col_e = st.columns(3)
            nuevo_n = col_n.text_input("Nombre y Apellidos")
            nuevo_s = col_s.text_input("SUAP")
            nuevo_e = col_e.text_input("Email")
            if st.form_submit_button("Añadir Profesional"):
                if nuevo_n and nuevo_s:
                    df_p = cargar_datos("Profesionales")
                    df_p = pd.concat([df_p, pd.DataFrame([{"Nombre y Apellidos": nuevo_n, "SUAP": nuevo_s, "Correo": nuevo_e}])], ignore_index=True)
                    guardar_datos("Profesionales", df_p)
                    st.rerun()
        
        df_p_list = cargar_datos("Profesionales")
        st.dataframe(df_p_list, use_container_width=True, hide_index=True)
        if not df_p_list.empty:
            borrar = st.selectbox("Eliminar profesional:", df_p_list["Nombre y Apellidos"].tolist())
            if st.button("Confirmar Eliminación"):
                df_p_list = df_p_list[df_p_list["Nombre y Apellidos"] != borrar]
                guardar_datos("Profesionales", df_p_list)
                st.rerun()

    # --- TAB 3: ESTADÍSTICAS ---
    with tab3:
        st.subheader("📊 Resumen de Actividad")
        df_s = cargar_datos("Solicitudes")
        df_aceptadas = df_s[df_s["Estado"] == "Aceptada ✅"]
        
        if df_aceptadas.empty:
            st.info("No hay guardias aceptadas para generar estadísticas.")
        else:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.write("**Guardias cambiadas/cedidas por Profesional:**")
                st.bar_chart(df_aceptadas["Solicitante"].value_counts())
            with col_g2:
                st.write("**Movimiento por centro (SUAP):**")
                st.bar_chart(df_aceptadas["SUAP_Origen"].value_counts())