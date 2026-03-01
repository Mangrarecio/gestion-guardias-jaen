import streamlit as st
import pandas as pd
import os
from datetime import date

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión Guardias Jaén", layout="centered")

PROF_FILE = "base_datos_profesionales.csv"
SOLICITUDES_FILE = "registro_guardias.csv"

# --- INICIALIZACIÓN DE BASES DE DATOS ---
def init_dbs():
    if not os.path.exists(PROF_FILE):
        pd.DataFrame(columns=["Nombre y Apellidos", "SUAP", "Correo"]).to_csv(PROF_FILE, index=False)
    if not os.path.exists(SOLICITUDES_FILE):
        pd.DataFrame(columns=[
            "ID", "Fecha_Solicitud", "Tipo", "Solicitante", "SUAP_Origen", 
            "Correo_Solicitante", "Fecha_Evento", "Receptor", "Estado"
        ]).to_csv(SOLICITUDES_FILE, index=False)

init_dbs()

# --- GESTIÓN DE NAVEGACIÓN ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

def ir_a(nombre_pagina):
    st.session_state.pagina = nombre_pagina
    st.rerun()

# ---------------------------------------------------------
# 1. PANTALLA INICIAL (ELECCIÓN DE ROL)
# ---------------------------------------------------------
if st.session_state.pagina == 'inicio':
    st.title("🏥 Gestión de Guardias")
    st.write("### Distrito Sanitario Jaén / Jaén Sur")
    st.info("Bienvenido. Seleccione su perfil para acceder al sistema.")
    
    col1, col2 = st.columns(2)
    if col1.button("ACCESO PROFESIONAL", use_container_width=True):
        ir_a('profesional')
    if col2.button("ACCESO ADMINISTRADOR", use_container_width=True):
        ir_a('admin_login')

# ---------------------------------------------------------
# 2. LOGIN ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_login':
    st.title("🔐 Acceso Admin")
    pwd = st.text_input("Introduzca la contraseña:", type="password")
    c1, c2 = st.columns(2)
    if c1.button("Entrar", use_container_width=True):
        if pwd == "@1234#":
            ir_a('admin_panel')
        else:
            st.error("Contraseña incorrecta")
    if c2.button("Volver", use_container_width=True):
        ir_a('inicio')

# ---------------------------------------------------------
# 3. VENTANA PROFESIONAL (SOLICITUDES)
# ---------------------------------------------------------
elif st.session_state.pagina == 'profesional':
    st.title("📝 Nueva Solicitud")
    if st.button("← Volver al Menú"):
        ir_a('inicio')

    df_p = pd.read_csv(PROF_FILE)
    if df_p.empty:
        st.warning("No hay profesionales registrados. El administrador debe dar de alta al personal.")
    else:
        lista_nombres = df_p["Nombre y Apellidos"].tolist()
        
        with st.form("form_registro_solicitud"):
            solicitante = st.selectbox("Seleccione su Nombre:", [""] + lista_nombres)
            tipo = st.radio("Tipo de Operación:", ["Cambio de guardia", "Cesión de guardia"], horizontal=True)
            
            col1, col2 = st.columns(2)
            fecha_g = col1.date_input("Fecha de la guardia:", format="DD/MM/YYYY")
            receptor = col2.selectbox("Profesional que asume la guardia:", [""] + lista_nombres)
            
            if st.form_submit_button("REGISTRAR Y ENVIAR"):
                if not solicitante or not receptor or solicitante == receptor:
                    st.error("Error: Debe seleccionar dos profesionales distintos.")
                else:
                    # Obtener datos automáticos del solicitante
                    datos_sol = df_p[df_p["Nombre y Apellidos"] == solicitante].iloc[0]
                    df_s = pd.read_csv(SOLICITUDES_FILE)
                    
                    # ID Incremental seguro
                    nuevo_id = 1 if df_s.empty else int(df_s["ID"].max() + 1)
                    
                    nueva_fila = {
                        "ID": nuevo_id,
                        "Fecha_Solicitud": date.today().strftime('%d/%m/%Y'),
                        "Tipo": tipo,
                        "Solicitante": solicitante,
                        "SUAP_Origen": datos_sol["SUAP"],
                        "Correo_Solicitante": datos_sol["Correo"],
                        "Fecha_Evento": fecha_g.strftime('%d/%m/%Y'),
                        "Receptor": receptor,
                        "Estado": "Pendiente"
                    }
                    df_s = pd.concat([df_s, pd.DataFrame([nueva_fila])], ignore_index=True)
                    df_s.to_csv(SOLICITUDES_FILE, index=False)
                    st.success(f"✅ Solicitud registrada con ID: {nuevo_id}. Pendiente de validación.")

# ---------------------------------------------------------
# 4. VENTANA ADMINISTRADOR (PANEL INTEGRAL)
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_panel':
    st.title("⚙️ Panel de Gestión Administrativa")
    if st.sidebar.button("Cerrar Sesión"):
        ir_a('inicio')

    tab1, tab2, tab3 = st.tabs(["Validar Solicitudes", "Gestión de Profesionales", "Excel y Backup"])

    # TAB 1: VALIDACIÓN Y BORRADO DE SOLICITUDES
    with tab1:
        st.subheader("Control de Solicitudes")
        df_sol = pd.read_csv(SOLICITUDES_FILE)
        
        if df_sol.empty:
            st.info("No hay solicitudes grabadas.")
        else:
            st.dataframe(df_sol, use_container_width=True)
            st.divider()
            
            c1, c2, c3 = st.columns([1, 1, 1])
            id_sel = c1.selectbox("Seleccione ID de Solicitud:", df_sol["ID"].tolist(), key="sel_sol")
            accion = c2.selectbox("Acción a realizar:", ["Aceptar ✅", "Rechazar ❌", "BORRAR REGISTRO 🗑️"])
            
            if c3.button("Ejecutar Acción", use_container_width=True):
                if accion == "BORRAR REGISTRO 🗑️":
                    df_sol = df_sol[df_sol["ID"] != id_sel]
                    st.warning(f"Registro {id_sel} eliminado.")
                else:
                    df_sol.loc[df_sol["ID"] == id_sel, "Estado"] = accion
                    st.success(f"Solicitud {id_sel} actualizada.")
                
                df_sol.to_csv(SOLICITUDES_FILE, index=False)
                st.rerun()

    # TAB 2: AGREGAR Y BORRAR PROFESIONALES
    with tab2:
        st.subheader("Alta de Nuevo Personal")
        if 'key_f' not in st.session_state: st.session_state.key_f = 0
        
        with st.form(key=f"alta_p_{st.session_state.key_f}"):
            nombre_n = st.text_input("Nombre y Apellidos")
            suap_n = st.text_input("Centro / SUAP")
            mail_n = st.text_input("Correo electrónico")
            
            if st.form_submit_button("GUARDAR PROFESIONAL"):
                if nombre_n and suap_n and mail_n:
                    df_p = pd.read_csv(PROF_FILE)
                    nueva_p = {"Nombre y Apellidos": nombre_n, "SUAP": suap_n, "Correo": mail_n}
                    df_p = pd.concat([df_p, pd.DataFrame([nueva_p])], ignore_index=True)
                    df_p.to_csv(PROF_FILE, index=False)
                    st.session_state.key_f += 1
                    st.success("Profesional añadido con éxito.")
                    st.rerun()
                else:
                    st.error("Todos los campos son obligatorios.")
        
        st.divider()
        st.subheader("Lista de Personal / Borrado")
        df_p_list = pd.read_csv(PROF_FILE)
        if not df_p_list.empty:
            st.dataframe(df_p_list, use_container_width=True)
            prof_a_borrar = st.selectbox("Seleccione Profesional para eliminar:", df_p_list["Nombre y Apellidos"].tolist())
            if st.button("🗑️ Eliminar Profesional seleccionado"):
                df_p_list = df_p_list[df_p_list["Nombre y Apellidos"] != prof_a_borrar]
                df_p_list.to_csv(PROF_FILE, index=False)
                st.error(f"Se ha eliminado a {prof_a_borrar} de la base de datos.")
                st.rerun()

    # TAB 3: DESCARGA DE EXCEL
    with tab3:
        st.subheader("Descargar histórico")
        df_final = pd.read_csv(SOLICITUDES_FILE)
        csv_data = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Excel de Guardias", csv_data, "registro_guardias_limpio.csv", "text/csv")