import streamlit as st
import pandas as pd
import os
from datetime import date

# --- CONFIGURACIÓN ---
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
            "Fecha_Evento", "Receptor", "Estado"
        ]).to_csv(SOLICITUDES_FILE, index=False)

init_dbs()

# --- SESIÓN DE NAVEGACIÓN ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

def cambiar_pagina(nombre):
    st.session_state.pagina = nombre

# ---------------------------------------------------------
# 1. PANTALLA INICIAL
# ---------------------------------------------------------
if st.session_state.pagina == 'inicio':
    st.title("Sistema de Gestión de Guardias")
    st.subheader("Distrito Sanitario Jaén / Jaén Sur")
    st.write("Seleccione su perfil para acceder:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("ACCESO PROFESIONAL", use_container_width=True):
            cambiar_pagina('profesional')
            st.rerun()
    with col2:
        if st.button("ACCESO ADMINISTRADOR", use_container_width=True):
            cambiar_pagina('admin_login')
            st.rerun()

# ---------------------------------------------------------
# 2. LOGIN ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_login':
    st.title("Acceso Restringido")
    pwd = st.text_input("Introduzca la contraseña de administrador:", type="password")
    col1, col2 = st.columns(2)
    if col1.button("Entrar"):
        if pwd == "@1234#":
            cambiar_pagina('admin_panel')
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    if col2.button("Volver"):
        cambiar_pagina('inicio')
        st.rerun()

# ---------------------------------------------------------
# 3. VENTANA PROFESIONAL
# ---------------------------------------------------------
elif st.session_state.pagina == 'profesional':
    st.title("Solicitud de Guardia")
    if st.button("← Volver al inicio"):
        cambiar_pagina('inicio')
        st.rerun()

    df_p = pd.read_csv(PROF_FILE)
    if df_p.empty:
        st.warning("No hay profesionales registrados. Contacte con el administrador.")
    else:
        nombres = ["Seleccione su nombre..."] + df_p["Nombre y Apellidos"].tolist()
        
        with st.form("solicitud_prof"):
            solicitante = st.selectbox("Identifíquese:", nombres)
            tipo = st.radio("Tipo:", ["Cambio de guardia", "Cesión de guardia"], horizontal=True)
            
            col1, col2 = st.columns(2)
            fecha_g = col1.date_input("Fecha de la guardia:", format="DD/MM/YYYY")
            receptor = col2.selectbox("¿Quién la hace en su lugar?", nombres)
            
            if st.form_submit_button("Enviar Solicitud"):
                if solicitante == "Seleccione su nombre..." or receptor == "Seleccione su nombre..." or solicitante == receptor:
                    st.error("Error en la selección de profesionales.")
                else:
                    df_s = pd.read_csv(SOLICITUDES_FILE)
                    # Obtener SUAP del solicitante automáticamente
                    suap_org = df_p[df_p["Nombre y Apellidos"] == solicitante]["SUAP"].values[0]
                    
                    nueva_fila = {
                        "ID": len(df_s) + 1,
                        "Fecha_Solicitud": date.today().strftime('%d/%m/%Y'),
                        "Tipo": tipo,
                        "Solicitante": solicitante,
                        "SUAP_Origen": suap_org,
                        "Fecha_Evento": fecha_g.strftime('%d/%m/%Y'),
                        "Receptor": receptor,
                        "Estado": "Pendiente"
                    }
                    df_s = pd.concat([df_s, pd.DataFrame([nueva_fila])], ignore_index=True)
                    df_s.to_csv(SOLICITUDES_FILE, index=False)
                    st.success("Solicitud enviada correctamente.")

# ---------------------------------------------------------
# 4. VENTANA ADMINISTRADOR (PANEL TOTAL)
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_panel':
    st.title("Panel Total de Administración")
    if st.sidebar.button("Cerrar Sesión"):
        cambiar_pagina('inicio')
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["Validar Solicitudes", "Gestionar Profesionales", "Base de Datos/Excel"])

    # --- TAB 1: VALIDACIÓN ---
    with tab1:
        st.subheader("Solicitudes Pendientes")
        df_sol = pd.read_csv(SOLICITUDES_FILE)
        st.dataframe(df_sol[df_sol["Estado"] == "Pendiente"], use_container_width=True)
        
        st.divider()
        col_id, col_acc = st.columns(2)
        id_mod = col_id.number_input("ID de Solicitud:", min_value=1, step=1)
        accion = col_acc.selectbox("Acción:", ["Aceptar", "Rechazar"])
        
        if st.button("Confirmar Acción"):
            if id_mod in df_sol["ID"].values:
                idx = df_sol[df_sol["ID"] == id_mod].index
                df_sol.at[idx[0], "Estado"] = "Aceptada ✅" if accion == "Aceptar" else "Rechazada ❌"
                df_sol.to_csv(SOLICITUDES_FILE, index=False)
                st.success(f"Solicitud {id_mod} actualizada.")
                st.rerun()

    # --- TAB 2: AGREGAR PROFESIONALES ---
    with tab2:
        st.subheader("Alta de Nuevo Profesional")
        # Usamos un contenedor para limpiar tras agregar
        if 'key_form' not in st.session_state: st.session_state.key_form = 0
        
        with st.form(key=f"prof_form_{st.session_state.key_form}"):
            nom = st.text_input("Nombre y Apellidos")
            sua = st.text_input("SUAP")
            cor = st.text_input("Correo")
            if st.form_submit_button("Guardar Profesional"):
                if nom and sua and cor:
                    df_p = pd.read_csv(PROF_FILE)
                    df_p = pd.concat([df_p, pd.DataFrame([{"Nombre y Apellidos": nom, "SUAP": sua, "Correo": cor}])], ignore_index=True)
                    df_p.to_csv(PROF_FILE, index=False)
                    st.session_state.key_form += 1
                    st.success("Guardado. Campos vaciados.")
                    st.rerun()
        
        st.write("### Lista Actual")
        st.dataframe(pd.read_csv(PROF_FILE), use_container_width=True)

    # --- TAB 3: EXPORTAR ---
    with tab3:
        st.subheader("Control de Datos")
        df_final = pd.read_csv(SOLICITUDES_FILE)
        st.write("Vista completa del Excel:")
        st.dataframe(df_final)
        
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Excel Actualizado", csv, "registro_limpio.csv", "text/csv")