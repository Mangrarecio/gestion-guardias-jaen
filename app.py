import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import io
import urllib.parse

# --- 1. CONFIGURACIÓN, LOGO Y ESTILO (PROTECCIÓN DE PRIVACIDAD) ---
st.set_page_config(page_title="Gestión Guardias Jaén", layout="wide", page_icon="🏥")

# Este bloque oculta los menús de Streamlit para que no vean tus otros proyectos
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# Mostrar logo del SAS (debes tener el archivo images.png en tu GitHub)
try:
    st.image("images.png", width=150)
except:
    pass

# --- 2. CONEXIÓN CON GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(pestana):
    try:
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
        st.error(f"Error crítico al guardar: {e}")
        return False

# --- 3. FUNCIONES AUXILIARES ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

def ir_a(p):
    st.session_state.pagina = p
    st.rerun()

def generar_link_email(email_destino, nombre, estado, fecha):
    asunto = f"Respuesta Solicitud Guardia - {fecha}"
    cuerpo = f"Hola {nombre},\n\nEn contestación a su solicitud de cambio de guardia para la fecha {fecha}, se le notifica que ha sido: {estado.upper()}."
    # Codificar para URL
    return f"mailto:{email_destino}?subject={urllib.parse.quote(asunto)}&body={urllib.parse.quote(cuerpo)}"

# ---------------------------------------------------------
# 🏠 PANTALLA DE INICIO
# ---------------------------------------------------------
if st.session_state.pagina == 'inicio':
    st.title("🏥 Gestión de Guardias - Distrito Jaén")
    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("📝 ACCESO PROFESIONAL", use_container_width=True): ir_a('profesional')
    if c2.button("🔐 ACCESO ADMINISTRADOR", use_container_width=True): ir_a('admin_login')

# ---------------------------------------------------------
# 🔐 LOGIN ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_login':
    st.title("🔐 Acceso Administrativo")
    pwd = st.text_input("Contraseña:", type="password")
    if st.button("Entrar", use_container_width=True):
        if pwd == "@1234#": ir_a('admin_panel')
        else: st.error("Contraseña incorrecta")
    if st.button("Volver"): ir_a('inicio')

# ---------------------------------------------------------
# 🧑‍⚕️ PANEL PROFESIONAL
# ---------------------------------------------------------
elif st.session_state.pagina == 'profesional':
    st.title("📝 Nueva Solicitud")
    if st.button("← Volver"): ir_a('inicio')
    
    df_p = cargar_datos("Profesionales")
    if df_p.empty:
        st.warning("No hay profesionales registrados. Avise al administrador.")
    else:
        nombres = sorted(df_p["Nombre y Apellidos"].tolist())
        with st.form("f_sol"):
            solicitante = st.selectbox("Tu Nombre:", ["Selecciona..."] + nombres)
            tipo = st.radio("Tipo de operación:", ["Cambio de guardia", "Cesión de guardia"], horizontal=True)
            fecha_g = st.date_input("Fecha de la guardia:")
            receptor = st.selectbox("¿Quién asume la guardia?", ["Selecciona..."] + nombres)
            
            if st.form_submit_button("REGISTRAR SOLICITUD"):
                if solicitante != "Selecciona..." and receptor != "Selecciona..." and solicitante != receptor:
                    df_s = cargar_datos("Solicitudes")
                    if df_s.empty:
                        df_s = pd.DataFrame(columns=["ID", "Fecha_Solicitud", "Tipo", "Solicitante", "Fecha_Evento", "Receptor", "Estado"])
                    
                    nuevo_id = 1 if df_s.empty else int(pd.to_numeric(df_s["ID"]).max() + 1)
                    nueva_fila = pd.DataFrame([{
                        "ID": nuevo_id,
                        "Fecha_Solicitud": datetime.now().strftime('%d/%m/%Y'),
                        "Tipo": tipo, "Solicitante": solicitante,
                        "Fecha_Evento": fecha_g.strftime('%d/%m/%Y'),
                        "Receptor": receptor, "Estado": "Pendiente"
                    }])
                    
                    if guardar_datos("Solicitudes", pd.concat([df_s, nueva_fila], ignore_index=True)):
                        st.balloons()
                        st.success(f"✅ Solicitud ID {nuevo_id} enviada correctamente.")
                        ir_a('inicio')
                else:
                    st.error("Revisa que los nombres no estén vacíos y no sean iguales.")

# ---------------------------------------------------------
# ⚙️ PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_panel':
    st.title("⚙️ Panel de Control")
    if st.sidebar.button("Cerrar Sesión"): ir_a('inicio')

    tab1, tab2 = st.tabs(["📋 Solicitudes", "👥 Gestión de Personal"])

    with tab1:
        df_s = cargar_datos("Solicitudes")
        df_p = cargar_datos("Profesionales")
        
        if not df_s.empty:
            # Botón de descarga Excel
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_s.to_excel(writer, index=False, sheet_name='Solicitudes')
            st.download_button(label="📥 Descargar todo a Excel", data=buf, file_name="registro_guardias.xlsx", mime="application/vnd.ms-excel")
            
            # Tabla con colores
            def color_est(val):
                c = 'green' if 'Aceptada' in str(val) else 'red' if 'Rechazada' in str(val) else 'orange'
                return f'color: {c}'
            st.dataframe(df_s.style.applymap(color_est, subset=['Estado']), use_container_width=True, hide_index=True)
            
            st.divider()
            col1, col2 = st.columns(2)
            id_sel = col1.selectbox("Gestionar ID:", df_s["ID"].tolist())
            acc = col2.selectbox("Nueva Acción:", ["Aceptada ✅", "Rechazada ❌", "ELIMINAR 🗑️"])
            
            if st.button("Aplicar Cambio de Estado"):
                if acc == "ELIMINAR 🗑️":
                    df_s = df_s[df_s["ID"] != id_sel]
                else:
                    df_s.loc[df_s["ID"] == id_sel, "Estado"] = acc
                if guardar_datos("Solicitudes", df_s):
                    st.success("Estado actualizado."); st.rerun()
            
            # SECCIÓN DE NOTIFICACIÓN
            st.markdown("---")
            fila = df_s[df_s["ID"] == id_sel].iloc[0]
            try:
                email_solicitante = df_p[df_p["Nombre y Apellidos"] == fila["Solicitante"]]["Correo"].values[0]
                link = generar_link_email(email_solicitante, fila["Solicitante"], fila["Estado"], fila["Fecha_Evento"])
                st.markdown(f'<a href="{link}" target="_blank" style="text-decoration:none;"><div style="background-color:#28a745;color:white;padding:10px;border-radius:5px;text-align:center;">📧 Notificar resultado a {fila["Solicitante"]}</div></a>', unsafe_allow_html=True)
            except:
                st.info("Añade el email del profesional para poder notificarle.")

    with tab2:
        st.subheader("Alta de Personal")
        with st.form("alta_p"):
            nom = st.text_input("Nombre y Apellidos")
            centro = st.text_input("SUAP / Centro")
            correo = st.text_input("Email")
            if st.form_submit_button("Guardar Profesional"):
                if nom and centro:
                    df_prof = cargar_datos("Profesionales")
                    if df_prof.empty: df_prof = pd.DataFrame(columns=["Nombre y Apellidos", "SUAP", "Correo"])
                    if guardar_datos("Profesionales", pd.concat([df_prof, pd.DataFrame([{"Nombre y Apellidos": nom, "SUAP": centro, "Correo": correo}])], ignore_index=True)):
                        st.success("Añadido."); st.rerun()
        
        st.dataframe(cargar_datos("Profesionales"), use_container_width=True, hide_index=True)