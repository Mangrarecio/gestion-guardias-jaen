import streamlit as st
import pandas as pd
import os
from datetime import date

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Gestión de Guardias Jaén", layout="centered")
DB_FILE = "registro_guardias.csv"

# Inicializar base de datos si no existe
def init_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=[
            "Fecha de Firma", "Tipo", "Profesional 1", "Fecha Guardia 1", "SUAP 1",
            "Profesional 2", "Fecha Guardia 2", "SUAP 2", "Estado"
        ])
        df.to_csv(DB_FILE, index=False)

init_db()

# --- DATOS DE EJEMPLO (Simulando la base de datos de profesionales y centros) ---
lista_profesionales = ["Selecciona un profesional...", "Juan Pérez (11111111A)", "María Gómez (22222222B)", "Carlos López (33333333C)"]
lista_suap = ["Selecciona un SUAP...", "SUAP Jaén 1", "SUAP Jaén Sur", "SUAP Martos", "SUAP Alcalá la Real"]

# --- BARRA LATERAL: CONTROL DE ACCESO ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Junta_de_Andaluc%C3%ADa_logo.svg/1200px-Junta_de_Andaluc%C3%ADa_logo.svg.png", width=150) # Imagen genérica de ejemplo
st.sidebar.title("Acceso")
rol = st.sidebar.radio("Selecciona tu perfil:", ["Profesional", "Administrador"])

# --- VISTA: PROFESIONAL (Acceso Libre) ---
if rol == "Profesional":
    st.title("Aplicación para Cambios/Cesiones de Guardia")
    st.subheader("Distrito Sanitario Jaén / Jaén Sur")
    
    tipo_solicitud = st.radio("Tipo de solicitud:", ["Cambio de guardia (mutuo)", "Cesión de guardia (unidireccional)"])

    st.write("---")
    
    # Formulario basado en la imagen
    with st.form("formulario_guardias"):
        profesional_1 = st.selectbox("Listado de profesionales con DNI (Solicitante):", lista_profesionales, key="p1")
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_1 = st.date_input("Cambia la guardia del día:", format="DD/MM/YYYY")
        with col2:
            suap_1 = st.selectbox("en el SUAP:", lista_suap, key="s1")
            
        st.write("**con**")
        
        profesional_2 = st.selectbox("Listado de profesionales con DNI (Receptor):", lista_profesionales, key="p2")
        
        # Si es un cambio, se pide la fecha de retorno. Si es cesión, se oculta.
        if tipo_solicitud == "Cambio de guardia (mutuo)":
            col3, col4 = st.columns(2)
            with col3:
                fecha_2 = st.date_input("que la tiene el día:", format="DD/MM/YYYY")
            with col4:
                suap_2 = st.selectbox("el SUAP (Receptor):", lista_suap, key="s2")
        else:
            fecha_2 = None
            suap_2 = "N/A (Cesión)"
            
        st.write("---")
        st.write("### Quedando la planificación:")
        
        if tipo_solicitud == "Cambio de guardia (mutuo)":
            st.info(f"**{profesional_1 if profesional_1 != 'Selecciona un profesional...' else '[Prof. 1]'}** hace la guardia del día **{fecha_2.strftime('%d/%m/%Y') if fecha_2 else '[Fecha 2]'}**.")
            st.info(f"Y **{profesional_2 if profesional_2 != 'Selecciona un profesional...' else '[Prof. 2]'}** hace la guardia del día **{fecha_1.strftime('%d/%m/%Y')}**.")
        else:
            st.info(f"**{profesional_2 if profesional_2 != 'Selecciona un profesional...' else '[Prof. 2]'}** asume la guardia del día **{fecha_1.strftime('%d/%m/%Y')}**.")

        st.write("---")
        fecha_firma = st.date_input("Firmado digitalmente con DNI identificados arriba a fecha:", value=date.today(), format="DD/MM/YYYY")
        
        submitted = st.form_submit_button("Enviar Solicitud")
        
        if submitted:
            # Validaciones básicas
            if "Selecciona" in profesional_1 or "Selecciona" in profesional_2 or "Selecciona" in suap_1:
                st.error("Por favor, selecciona profesionales y centros válidos en todos los campos.")
            else:
                # Guardar en base de datos (CSV)
                nuevo_registro = {
                    "Fecha de Firma": fecha_firma.strftime('%d/%m/%Y'),
                    "Tipo": tipo_solicitud,
                    "Profesional 1": profesional_1,
                    "Fecha Guardia 1": fecha_1.strftime('%d/%m/%Y'),
                    "SUAP 1": suap_1,
                    "Profesional 2": profesional_2,
                    "Fecha Guardia 2": fecha_2.strftime('%d/%m/%Y') if fecha_2 else "N/A",
                    "SUAP 2": suap_2,
                    "Estado": "Pendiente"
                }
                
                df = pd.read_csv(DB_FILE)
                df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
                df.to_csv(DB_FILE, index=False)
                
                # Feedback de aceptación (Solicitado en nota manuscrita)
                st.success("✅ ¡Solicitud registrada correctamente! Tu petición está pendiente de revisión por administración.")

# --- VISTA: ADMINISTRADOR (Acceso con contraseña) ---
elif rol == "Administrador":
    st.title("Panel de Administración")
    
    password = st.text_input("Introduce la contraseña de administrador:", type="password")
    
    if password == "@1234#":
        st.success("Acceso concedido.")
        st.write("Aquí puedes visualizar y descargar el listado histórico de todas las solicitudes volcadas.")
        
        try:
            df_admin = pd.read_csv(DB_FILE)
            st.dataframe(df_admin, use_container_width=True)
            
            # Botón para descargar a Excel (CSV)
            csv = df_admin.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar datos para Excel (CSV)",
                data=csv,
                file_name='historico_guardias_jaen.csv',
                mime='text/csv',
            )
            
        except FileNotFoundError:
            st.warning("Todavía no hay registros en la base de datos.")
    elif password != "":
        st.error("Contraseña incorrecta.")