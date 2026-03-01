import streamlit as st
import pandas as pd
import os
from datetime import date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Guardias Jaén", layout="wide")

# Nombres de archivos fijos para que sea un registro único
PROF_FILE = "base_datos_profesionales.csv"
SOLICITUDES_FILE = "registro_guardias.csv"

# --- INICIALIZACIÓN (Solo se ejecuta una vez) ---
def init_dbs():
    # Solo creamos los archivos si NO existen
    if not os.path.exists(PROF_FILE):
        df_p = pd.DataFrame(columns=["Nombre y Apellidos", "SUAP", "Correo"])
        df_p.to_csv(PROF_FILE, index=False, encoding='utf-8-sig')
    
    if not os.path.exists(SOLICITUDES_FILE):
        # Definimos las columnas exactas para un Excel limpio
        df_s = pd.DataFrame(columns=[
            "ID", "Fecha_Solicitud", "Tipo", "Solicitante", "SUAP_Origen", 
            "Correo_Solicitante", "Fecha_Evento", "Receptor", "Estado"
        ])
        df_s.to_csv(SOLICITUDES_FILE, index=False, encoding='utf-8-sig')

init_dbs()

# --- NAVEGACIÓN ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

def ir_a(nombre_pagina):
    st.session_state.pagina = nombre_pagina
    st.rerun()

# ---------------------------------------------------------
# 1. PANTALLA INICIAL
# ---------------------------------------------------------
if st.session_state.pagina == 'inicio':
    st.title("🏥 Gestión de Guardias - Distrito Jaén")
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Personal")
        if st.button("ACCESO PROFESIONAL", use_container_width=True):
            ir_a('profesional')
    with col2:
        st.subheader("Gestión")
        if st.button("ACCESO ADMINISTRADOR", use_container_width=True):
            ir_a('admin_login')

# ---------------------------------------------------------
# 2. LOGIN ADMIN
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_login':
    st.title("🔐 Acceso Administrativo")
    pwd = st.text_input("Contraseña:", type="password")
    c1, c2 = st.columns(2)
    if c1.button("Entrar"):
        if pwd == "@1234#":
            ir_a('admin_panel')
        else:
            st.error("Contraseña incorrecta")
    if c2.button("Volver"):
        ir_a('inicio')

# ---------------------------------------------------------
# 3. VENTANA PROFESIONAL (ÚNICO REGISTRO)
# ---------------------------------------------------------
elif st.session_state.pagina == 'profesional':
    st.title("📝 Formulario de Solicitud")
    if st.button("← Volver"):
        ir_a('inicio')

    df_p = pd.read_csv(PROF_FILE)
    if df_p.empty:
        st.warning("No hay profesionales registrados. Avise al administrador.")
    else:
        lista_nombres = sorted(df_p["Nombre y Apellidos"].tolist())
        
        with st.form("nueva_peticion"):
            solicitante = st.selectbox("Seleccione su Nombre:", [""] + lista_nombres)
            tipo = st.radio("Operación:", ["Cambio de guardia", "Cesión de guardia"], horizontal=True)
            
            col1, col2 = st.columns(2)
            fecha_g = col1.date_input("Fecha de la guardia:", format="DD/MM/YYYY")
            receptor = col2.selectbox("Profesional Receptor:", [""] + lista_nombres)
            
            if st.form_submit_button("REGISTRAR"):
                if solicitante and receptor and solicitante != receptor:
                    # 1. Leer el archivo único
                    df_s = pd.read_csv(SOLICITUDES_FILE)
                    
                    # 2. Obtener datos del solicitante
                    datos_sol = df_p[df_p["Nombre y Apellidos"] == solicitante].iloc[0]
                    
                    # 3. Crear nueva fila con ID incremental
                    nuevo_id = 1 if df_s.empty else df_s["ID"].max() + 1
                    nueva_fila = pd.DataFrame([{
                        "ID": int(nuevo_id),
                        "Fecha_Solicitud": date.today().strftime('%d/%m/%Y'),
                        "Tipo": tipo,
                        "Solicitante": solicitante,
                        "SUAP_Origen": datos_sol["SUAP"],
                        "Correo_Solicitante": datos_sol["Correo"],
                        "Fecha_Evento": fecha_g.strftime('%d/%m/%Y'),
                        "Receptor": receptor,
                        "Estado": "Pendiente"
                    }])
                    
                    # 4. Añadir y SOBRESCRIBIR el mismo archivo
                    df_final = pd.concat([df_s, nueva_fila], ignore_index=True)
                    df_final.to_csv(SOLICITUDES_FILE, index=False, encoding='utf-8-sig')
                    
                    st.success(f"Guardado en el registro único con ID {nuevo_id}")
                else:
                    st.error("Revise que los nombres sean distintos y estén seleccionados.")

# ---------------------------------------------------------
# 4. VENTANA ADMINISTRADOR (GESTIÓN Y LIMPIEZA)
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_panel':
    st.title("⚙️ Panel de Control")
    if st.sidebar.button("Cerrar Sesión"):
        ir_a('inicio')

    t1, t2, t3 = st.tabs(["Solicitudes", "Profesionales", "Descargar Único Excel"])

    with t1:
        df_s = pd.read_csv(SOLICITUDES_FILE)
        if not df_s.empty:
            st.dataframe(df_s, use_container_width=True)
            
            st.write("### Modificar o Borrar")
            c1, c2, c3 = st.columns(3)
            id_sel = c1.selectbox("ID:", df_s["ID"].tolist())
            accion = c2.selectbox("Acción:", ["Aceptar ✅", "Rechazar ❌", "ELIMINAR 🗑️"])
            
            if c3.button("Confirmar"):
                if accion == "ELIMINAR 🗑️":
                    df_s = df_s[df_s["ID"] != id_sel]
                else:
                    df_s.loc[df_s["ID"] == id_sel, "Estado"] = accion
                
                df_s.to_csv(SOLICITUDES_FILE, index=False, encoding='utf-8-sig')
                st.rerun()
        else:
            st.info("Registro vacío.")

    with t2:
        st.subheader("Alta de Personal")
        if 'k' not in st.session_state: st.session_state.k = 0
        with st.form(key=f"f_{st.session_state.k}"):
            n = st.text_input("Nombre completo")
            s = st.text_input("Centro")
            m = st.text_input("Email")
            if st.form_submit_button("Añadir"):
                df_p = pd.read_csv(PROF_FILE)
                df_p = pd.concat([df_p, pd.DataFrame([{"Nombre y Apellidos": n, "SUAP": s, "Correo": m}])], ignore_index=True)
                df_p.to_csv(PROF_FILE, index=False, encoding='utf-8-sig')
                st.session_state.k += 1
                st.rerun()
        
        df_p_list = pd.read_csv(PROF_FILE)
        st.dataframe(df_p_list, use_container_width=True)
        if not df_p_list.empty:
            borrar_p = st.selectbox("Borrar profesional:", df_p_list["Nombre y Apellidos"].tolist())
            if st.button("Eliminar"):
                df_p_list = df_p_list[df_p_list["Nombre y Apellidos"] != borrar_p]
                df_p_list.to_csv(PROF_FILE, index=False, encoding='utf-8-sig')
                st.rerun()

    with t3:
        # Aquí siempre se descarga el archivo centralizado
        df_final = pd.read_csv(SOLICITUDES_FILE)
        csv = df_final.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 Descargar Registro Único", csv, "registro_guardias_jaen.csv", "text/csv")