import streamlit as st
import pandas as pd
import os
from datetime import date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Guardias Jaén", layout="centered")

PROF_FILE = "base_datos_profesionales.csv"
SOLICITUDES_FILE = "registro_guardias.csv"

# --- INICIALIZACIÓN DE ARCHIVOS ---
def init_dbs():
    if not os.path.exists(PROF_FILE):
        pd.DataFrame(columns=["Nombre y Apellidos", "SUAP", "Correo"]).to_csv(PROF_FILE, index=False)
    if not os.path.exists(SOLICITUDES_FILE):
        pd.DataFrame(columns=[
            "ID", "Fecha_Solicitud", "Tipo", "Solicitante", "SUAP_Origen", 
            "Correo_Solicitante", "Fecha_Evento", "Receptor", "Estado"
        ]).to_csv(SOLICITUDES_FILE, index=False)

init_dbs()

# --- GESTIÓN DE NAVEGACIÓN (Session State) ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

def ir_a(nombre_pagina):
    st.session_state.pagina = nombre_pagina
    st.rerun()

# ---------------------------------------------------------
# 1. PANTALLA INICIAL
# ---------------------------------------------------------
if st.session_state.pagina == 'inicio':
    st.title("🏥 Gestión de Guardias")
    st.subheader("Distrito Sanitario Jaén")
    st.write("Seleccione su perfil para continuar:")
    
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
# 3. VENTANA PROFESIONAL (Solicitudes)
# ---------------------------------------------------------
elif st.session_state.pagina == 'profesional':
    st.title("📝 Nueva Solicitud")
    if st.button("← Volver"):
        ir_a('inicio')

    df_p = pd.read_csv(PROF_FILE)
    if df_p.empty:
        st.warning("No hay profesionales en la base de datos. El administrador debe agregarlos primero.")
    else:
        # Cargamos nombres para los desplegables
        lista_nombres = df_p["Nombre y Apellidos"].tolist()
        
        with st.form("form_solicitud"):
            solicitante = st.selectbox("Seleccione su Nombre:", [""] + lista_nombres)
            tipo = st.radio("Operación:", ["Cambio de guardia", "Cesión de guardia"], horizontal=True)
            
            col1, col2 = st.columns(2)
            fecha_g = col1.date_input("Fecha de la guardia:", format="DD/MM/YYYY")
            receptor = col2.selectbox("Profesional que la asume:", [""] + lista_nombres)
            
            submit = st.form_submit_button("REGISTRAR SOLICITUD")
            
            if submit:
                if not solicitante or not receptor or solicitante == receptor:
                    st.error("Por favor, seleccione profesionales distintos.")
                else:
                    # Buscamos los datos del profesional solicitante para el Excel
                    datos_sol = df_p[df_p["Nombre y Apellidos"] == solicitante].iloc[0]
                    
                    df_s = pd.read_csv(SOLICITUDES_FILE)
                    nueva_fila = {
                        "ID": len(df_s) + 1,
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
                    st.success("✅ ¡Solicitud guardada con éxito!")

# ---------------------------------------------------------
# 4. VENTANA ADMINISTRADOR (Gestión Total)
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_panel':
    st.title("⚙️ Panel de Control")
    if st.sidebar.button("Cerrar Sesión"):
        ir_a('inicio')

    tab1, tab2, tab3 = st.tabs(["Validar Solicitudes", "Añadir Profesionales", "Descargar Excel"])

    # TAB 1: GESTIÓN DE PETICIONES
    with tab1:
        df_sol = pd.read_csv(SOLICITUDES_FILE)
        pendientes = df_sol[df_sol["Estado"] == "Pendiente"]
        
        st.subheader("Solicitudes a Revisar")
        if pendientes.empty:
            st.info("No hay solicitudes pendientes.")
        else:
            st.dataframe(pendientes, use_container_width=True)
            
            st.divider()
            c1, c2, c3 = st.columns([1, 1, 1])
            id_sel = c1.number_input("ID de Solicitud:", min_value=1, step=1)
            accion = c2.selectbox("Decisión:", ["Aceptar", "Rechazar"])
            if c3.button("Ejecutar", use_container_width=True):
                if id_sel in df_sol["ID"].values:
                    idx = df_sol[df_sol["ID"] == id_sel].index
                    df_sol.at[idx[0], "Estado"] = "Aceptada ✅" if accion == "Aceptar" else "Rechazada ❌"
                    df_sol.to_csv(SOLICITUDES_FILE, index=False)
                    st.success(f"ID {id_sel} actualizado.")
                    st.rerun()

    # TAB 2: AGREGAR PROFESIONALES (Se vacía al guardar)
    with tab2:
        st.subheader("Alta de Profesionales")
        if 'reset_key' not in st.session_state: st.session_state.reset_key = 0
        
        with st.form(key=f"alta_prof_{st.session_state.reset_key}"):
            nom = st.text_input("Nombre y Apellidos")
            sua = st.text_input("Centro / SUAP")
            mail = st.text_input("Correo electrónico")
            
            if st.form_submit_button("GUARDAR PROFESIONAL"):
                if nom and sua and mail:
                    df_p = pd.read_csv(PROF_FILE)
                    df_p = pd.concat([df_p, pd.DataFrame([{"Nombre y Apellidos": nom, "SUAP": sua, "Correo": mail}])], ignore_index=True)
                    df_p.to_csv(PROF_FILE, index=False)
                    st.session_state.reset_key += 1 # Esto limpia el formulario
                    st.success(f"Añadido: {nom}")
                    st.rerun()
                else:
                    st.warning("Rellene todos los campos.")
        
        st.write("---")
        st.write("Profesionales en el sistema:")
        st.dataframe(pd.read_csv(PROF_FILE), use_container_width=True)

    # TAB 3: EXCEL LIMPIO
    with tab3:
        st.subheader("Exportar Datos")
        df_final = pd.read_csv(SOLICITUDES_FILE)
        st.dataframe(df_final)
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Registro (Excel)", csv, "registro_guardias.csv", "text/csv")