import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Guardias Jaén", layout="wide", page_icon="🏥")

# --- CONEXIÓN A GOOGLE SHEETS (MÉTODO GRATUITO) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet_name):
    # Lee los datos directamente de la pestaña indicada
    return conn.read(worksheet=worksheet_name, ttl="0")

def save_data(worksheet_name, df):
    # Actualiza la hoja en la nube instantáneamente
    conn.update(worksheet=worksheet_name, data=df)
    st.cache_data.clear() # Limpia caché para ver cambios en tiempo real

# --- NAVEGACIÓN ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

def ir_a(nombre_pagina):
    st.session_state.pagina = nombre_pagina
    st.rerun()

# ---------------------------------------------------------
# PANTALLA INICIAL
# ---------------------------------------------------------
if st.session_state.pagina == 'inicio':
    st.title("🏥 Gestión de Guardias - Distrito Jaén")
    st.write("---")
    col1, col2 = st.columns(2)
    if col1.button("ACCESO PROFESIONAL", use_container_width=True):
        ir_a('profesional')
    if col2.button("ACCESO ADMINISTRADOR", use_container_width=True):
        ir_a('admin_login')

# ---------------------------------------------------------
# VENTANA PROFESIONAL
# ---------------------------------------------------------
elif st.session_state.pagina == 'profesional':
    st.title("📝 Nueva Solicitud")
    if st.button("← Volver"):
        ir_a('inicio')

    df_p = load_data("Profesionales")
    
    if df_p.empty:
        st.warning("No hay profesionales registrados.")
    else:
        lista_nombres = sorted(df_p["Nombre y Apellidos"].tolist())
        with st.form("form_solicitud"):
            solicitante = st.selectbox("Seleccione su Nombre:", [""] + lista_nombres)
            tipo = st.radio("Operación:", ["Cambio de guardia", "Cesión de guardia"], horizontal=True)
            col1, col2 = st.columns(2)
            fecha_g = col1.date_input("Fecha de la guardia:", format="DD/MM/YYYY")
            receptor = st.selectbox("¿Quién asume la guardia?", [""] + lista_nombres)
            
            if st.form_submit_button("REGISTRAR SOLICITUD"):
                if solicitante and receptor and solicitante != receptor:
                    df_s = load_data("Solicitudes")
                    datos_sol = df_p[df_p["Nombre y Apellidos"] == solicitante].iloc[0]
                    
                    nuevo_id = 1 if df_s.empty else int(df_s["ID"].max() + 1)
                    
                    nueva_fila = pd.DataFrame([{
                        "ID": nuevo_id,
                        "Fecha_Solicitud": datetime.now().strftime('%d/%m/%Y'),
                        "Tipo": tipo,
                        "Solicitante": solicitante,
                        "SUAP_Origen": datos_sol["SUAP"],
                        "Correo_Solicitante": datos_sol["Correo"],
                        "Fecha_Evento": fecha_g.strftime('%d/%m/%Y'),
                        "Receptor": receptor,
                        "Estado": "Pendiente"
                    }])
                    
                    df_final = pd.concat([df_s, nueva_fila], ignore_index=True)
                    save_data("Solicitudes", df_final)
                    st.success(f"✅ Registrado con éxito en la nube (ID {nuevo_id})")
                else:
                    st.error("Error en los datos seleccionados.")

# ---------------------------------------------------------
# VENTANA ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_panel':
    st.title("⚙️ Panel de Gestión Administrativa")
    if st.sidebar.button("Cerrar Sesión"):
        ir_a('inicio')

    t1, t2, t3 = st.tabs(["Validar Solicitudes", "Gestionar Personal", "📊 Estadísticas"])

    with t1:
        df_s = load_data("Solicitudes")
        st.subheader("Buscador")
        busqueda = st.text_input("Buscar por Nombre:")
        
        df_f = df_s[df_s["Solicitante"].str.contains(busqueda, case=False, na=False)] if busqueda else df_s
        st.dataframe(df_f, use_container_width=True)
        
        if not df_f.empty:
            st.divider()
            c1, c2, c3 = st.columns(3)
            id_sel = c1.selectbox("ID:", df_f["ID"].tolist())
            accion = c2.selectbox("Acción:", ["Aceptar ✅", "Rechazar ❌", "ELIMINAR 🗑️"])
            
            if c3.button("Confirmar Cambio"):
                if accion == "ELIMINAR 🗑️":
                    df_s = df_s[df_s["ID"] != id_sel]
                else:
                    df_s.loc[df_s["ID"] == id_sel, "Estado"] = accion
                save_data("Solicitudes", df_s)
                st.rerun()

    with t2:
        st.subheader("Alta de Personal")
        with st.form("nuevo_p"):
            n, s, m = st.text_input("Nombre"), st.text_input("SUAP"), st.text_input("Email")
            if st.form_submit_button("Añadir a Google Sheets"):
                df_p = load_data("Profesionales")
                df_p = pd.concat([df_p, pd.DataFrame([{"Nombre y Apellidos": n, "SUAP": s, "Correo": m}])], ignore_index=True)
                save_data("Profesionales", df_p)
                st.rerun()

    with t3:
        st.subheader("Estadísticas")
        df_s = load_data("Solicitudes")
        if not df_s.empty:
            df_ok = df_s[df_s["Estado"] == "Aceptada ✅"]
            st.bar_chart(df_ok["Solicitante"].value_counts())