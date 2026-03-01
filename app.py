import streamlit as st
import pandas as pd
import os
from datetime import date

# --- CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="Gestión de Guardias Jaén", layout="wide", page_icon="🏥")

PROF_FILE = "base_datos_profesionales.csv"
SOLICITUDES_FILE = "registro_guardias.csv"

def init_dbs():
    # Base de datos de profesionales (Nombre, SUAP, Correo)
    if not os.path.exists(PROF_FILE):
        pd.DataFrame(columns=["Nombre y Apellidos", "SUAP", "Correo"]).to_csv(PROF_FILE, index=False)
    # Registro de solicitudes
    if not os.path.exists(SOLICITUDES_FILE):
        pd.DataFrame(columns=[
            "ID", "Fecha Solicitud", "Tipo", "Solicitante", "SUAP", "Correo", 
            "Fecha Cambio/Cesión", "Receptor", "Estado"
        ]).to_csv(SOLICITUDES_FILE, index=False)

init_dbs()

# --- FUNCIONES DE APOYO ---
def cargar_datos(archivo):
    return pd.read_csv(archivo)

def guardar_datos(df, archivo):
    df.to_csv(archivo, index=False)

# --- NAVEGACIÓN ---
st.sidebar.title("🏥 Sistema de Guardias")
rol = st.sidebar.radio("Ir a:", ["Vista Profesional", "Panel Administrador"])

# ---------------------------------------------------------
# VISTA PROFESIONAL
# ---------------------------------------------------------
if rol == "Vista Profesional":
    st.title("Solicitud de Cambio o Cesión de Guardia")
    st.info("Complete los datos para registrar su petición en el sistema.")

    df_profs = cargar_datos(PROF_FILE)
    nombres_profs = ["Seleccione..."] + df_profs["Nombre y Apellidos"].tolist()

    with st.form("form_registro"):
        tipo = st.selectbox("Tipo de operación:", ["Cambio de guardia", "Cesión de guardia"])
        
        col1, col2 = st.columns(2)
        with col1:
            # El profesional se elige de la base de datos creada por el administrador
            solicitante = st.selectbox("Nombre y Apellidos (Solicitante):", nombres_profs)
            fecha_evento = st.date_input("Fecha del cambio/cesión:", format="DD/MM/YYYY")
        
        with col2:
            receptor = st.selectbox("Profesional Receptor:", nombres_profs)
            # Buscamos datos automáticos si el solicitante existe
            suap_sol = ""
            email_sol = ""
            if solicitante != "Seleccione...":
                row = df_profs[df_profs["Nombre y Apellidos"] == solicitante].iloc[0]
                suap_sol = row["SUAP"]
                email_sol = row["Correo"]
            
            st.text_input("SUAP (Automático):", value=suap_sol, disabled=True)
            st.text_input("Correo (Automático):", value=email_sol, disabled=True)

        enviar = st.form_submit_button("Registrar Solicitud")

        if enviar:
            if solicitante == "Seleccione..." or receptor == "Seleccione..." or solicitante == receptor:
                st.error("Error: Seleccione profesionales válidos y distintos.")
            else:
                df_sol = cargar_datos(SOLICITUDES_FILE)
                nueva_sol = {
                    "ID": len(df_sol) + 1,
                    "Fecha Solicitud": date.today().strftime('%d/%m/%Y'),
                    "Tipo": tipo,
                    "Solicitante": solicitante,
                    "SUAP": suap_sol,
                    "Correo": email_sol,
                    "Fecha Cambio/Cesión": fecha_evento.strftime('%d/%m/%Y'),
                    "Receptor": receptor,
                    "Estado": "Pendiente"
                }
                df_sol = pd.concat([df_sol, pd.DataFrame([nueva_sol])], ignore_index=True)
                guardar_datos(df_sol, SOLICITUDES_FILE)
                st.success(f"✅ {tipo} registrado correctamente. Pendiente de aprobación.")

# ---------------------------------------------------------
# PANEL ADMINISTRADOR
# ---------------------------------------------------------
else:
    st.title("Panel de Control Administrativo")
    password = st.sidebar.text_input("Contraseña:", type="password")

    if password == "@1234#":
        tabs = st.tabs(["📋 Gestión de Solicitudes", "👥 Base de Datos Profesionales", "📊 Exportar Datos"])

        # TAB 1: GESTIÓN DE SOLICITUDES (ACEPTAR/RECHAZAR)
        with tabs[0]:
            st.subheader("Solicitudes en tiempo real")
            df_sol = cargar_datos(SOLICITUDES_FILE)
            
            if df_sol.empty:
                st.write("No hay solicitudes registradas.")
            else:
                # Mostrar tabla con estados
                st.dataframe(df_sol, use_container_width=True)
                
                st.divider()
                st.write("### Acciones de validación")
                col_id, col_act = st.columns([1, 2])
                id_modificar = col_id.number_input("ID de la solicitud:", min_value=1, step=1)
                accion = col_act.selectbox("Acción:", ["Aceptar", "Rechazar"])
                
                if st.button("Actualizar Estado"):
                    if id_modificar in df_sol["ID"].values:
                        idx = df_sol[df_sol["ID"] == id_modificar].index
                        nuevo_estado = "Aceptada ✅" if accion == "Aceptar" else "Rechazada ❌"
                        df_sol.at[idx[0], "Estado"] = nuevo_estado
                        guardar_datos(df_sol, SOLICITUDES_FILE)
                        st.success(f"Solicitud {id_modificar} marcada como {nuevo_estado}")
                        st.rerun()
                    else:
                        st.error("ID no encontrado.")

        # TAB 2: AGREGAR PROFESIONALES
        with tabs[1]:
            st.subheader("Añadir Profesional a la Base de Datos")
            
            # Usamos una clave en session_state para limpiar los campos
            if 'form_key' not in st.session_state:
                st.session_state.form_key = 0

            with st.form(key=f"add_prof_{st.session_state.form_key}"):
                new_nombre = st.text_input("Nombre y Apellidos")
                new_suap = st.text_input("SUAP")
                new_correo = st.text_input("Correo electrónico")
                
                submit_prof = st.form_submit_button("Agregar Profesional")
                
                if submit_prof:
                    if new_nombre and new_suap and new_correo:
                        df_p = cargar_datos(PROF_FILE)
                        nueva_p = {"Nombre y Apellidos": new_nombre, "SUAP": new_suap, "Correo": new_correo}
                        df_p = pd.concat([df_p, pd.DataFrame([nueva_p])], ignore_index=True)
                        guardar_datos(df_p, PROF_FILE)
                        
                        st.success(f"Profesional {new_nombre} añadido.")
                        # Al cambiar la key, el formulario se vacía completamente
                        st.session_state.form_key += 1
                        st.rerun()
                    else:
                        st.warning("Rellene todos los campos.")
            
            st.write("---")
            st.write("### Lista de Profesionales Actuales")
            st.dataframe(cargar_datos(PROF_FILE), use_container_width=True)

        # TAB 3: EXPORTAR
        with tabs[2]:
            st.subheader("Descargar Histórico")
            df_final = cargar_datos(SOLICITUDES_FILE)
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar Excel de Solicitudes (CSV)", csv, "registro_completo.csv", "text/csv")

    elif password != "":
        st.error("Contraseña incorrecta")