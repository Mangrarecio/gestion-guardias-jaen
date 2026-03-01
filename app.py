import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Guardias Jaén", layout="wide", page_icon="🏥")

PROF_FILE = "base_datos_profesionales.csv"
SOLICITUDES_FILE = "registro_guardias.csv"

# --- INICIALIZACIÓN ---
def init_dbs():
    if not os.path.exists(PROF_FILE):
        pd.DataFrame(columns=["Nombre y Apellidos", "SUAP", "Correo"]).to_csv(PROF_FILE, index=False, encoding='utf-8-sig')
    if not os.path.exists(SOLICITUDES_FILE):
        pd.DataFrame(columns=[
            "ID", "Fecha_Solicitud", "Tipo", "Solicitante", "SUAP_Origen", 
            "Correo_Solicitante", "Fecha_Evento", "Receptor", "Estado"
        ]).to_csv(SOLICITUDES_FILE, index=False, encoding='utf-8-sig')

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
    if col1.button("ACCESO PROFESIONAL", use_container_width=True):
        ir_a('profesional')
    if col2.button("ACCESO ADMINISTRADOR", use_container_width=True):
        ir_a('admin_login')

# ---------------------------------------------------------
# 2. LOGIN ADMIN
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_login':
    st.title("🔐 Acceso Administrativo")
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
# 3. VENTANA PROFESIONAL
# ---------------------------------------------------------
elif st.session_state.pagina == 'profesional':
    st.title("📝 Nueva Solicitud")
    if st.button("← Volver"):
        ir_a('inicio')

    df_p = pd.read_csv(PROF_FILE)
    if df_p.empty:
        st.warning("No hay profesionales registrados.")
    else:
        lista_nombres = sorted(df_p["Nombre y Apellidos"].tolist())
        with st.form("form_solicitud"):
            solicitante = st.selectbox("Seleccione su Nombre:", [""] + lista_nombres)
            tipo = st.radio("Operación:", ["Cambio de guardia", "Cesión de guardia"], horizontal=True)
            col1, col2 = st.columns(2)
            fecha_g = col1.date_input("Fecha de la guardia:", format="DD/MM/YYYY")
            receptor = col2.selectbox("¿Quién asume la guardia?", [""] + lista_nombres)
            
            if st.form_submit_button("REGISTRAR SOLICITUD"):
                if solicitante and receptor and solicitante != receptor:
                    df_s = pd.read_csv(SOLICITUDES_FILE)
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
                    df_final.to_csv(SOLICITUDES_FILE, index=False, encoding='utf-8-sig')
                    st.success(f"Guardado con ID {nuevo_id}")
                else:
                    st.error("Verifique los nombres.")

# ---------------------------------------------------------
# 4. VENTANA ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_panel':
    st.title("⚙️ Panel de Gestión Administrativa")
    if st.sidebar.button("Cerrar Sesión"):
        ir_a('inicio')

    t1, t2, t3, t4 = st.tabs(["Validar Solicitudes", "Gestionar Personal", "📊 Estadísticas", "Descargar Excel"])

    # TAB 1: VALIDACIÓN (Listado General)
    with t1:
        df_s = pd.read_csv(SOLICITUDES_FILE)
        st.subheader("🔍 Buscador y Filtros")
        c_f1, c_f2, c_f3 = st.columns([2, 1, 1])
        busqueda = c_f1.text_input("Buscar por Nombre:")
        mes_v = c_f2.selectbox("Mes:", ["Todos", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"], key="mv")
        anio_v = c_f3.selectbox("Año:", ["Todos"] + [str(a) for a in range(2024, 2031)], key="av")

        df_filtrado = df_s.copy()
        if busqueda:
            df_filtrado = df_filtrado[df_filtrado["Solicitante"].str.contains(busqueda, case=False, na=False) | df_filtrado["Receptor"].str.contains(busqueda, case=False, na=False)]
        if mes_v != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Fecha_Evento"].str.split('/').str[1] == mes_v]
        if anio_v != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Fecha_Evento"].str.split('/').str[2] == anio_v]

        st.dataframe(df_filtrado, use_container_width=True)
        
        if not df_filtrado.empty:
            st.divider()
            c1, c2, c3 = st.columns(3)
            id_sel = c1.selectbox("ID Seleccionado:", df_filtrado["ID"].tolist())
            accion = c2.selectbox("Acción:", ["Aceptar ✅", "Rechazar ❌", "ELIMINAR 🗑️"])
            if c3.button("Ejecutar", use_container_width=True):
                df_original = pd.read_csv(SOLICITUDES_FILE)
                if accion == "ELIMINAR 🗑️":
                    df_original = df_original[df_original["ID"] != id_sel]
                else:
                    df_original.loc[df_original["ID"] == id_sel, "Estado"] = accion
                df_original.to_csv(SOLICITUDES_FILE, index=False, encoding='utf-8-sig')
                st.rerun()

    # TAB 2: PERSONAL
    with t2:
        st.subheader("Alta de Profesionales")
        if 'rk' not in st.session_state: st.session_state.rk = 0
        with st.form(key=f"f_p_{st.session_state.rk}"):
            n, s, m = st.text_input("Nombre"), st.text_input("SUAP"), st.text_input("Email")
            if st.form_submit_button("GUARDAR"):
                if n and s and m:
                    df_p = pd.read_csv(PROF_FILE)
                    df_p = pd.concat([df_p, pd.DataFrame([{"Nombre y Apellidos": n, "SUAP": s, "Correo": m}])], ignore_index=True)
                    df_p.to_csv(PROF_FILE, index=False, encoding='utf-8-sig')
                    st.session_state.rk += 1
                    st.rerun()
        df_p_list = pd.read_csv(PROF_FILE)
        st.dataframe(df_p_list, use_container_width=True)
        if not df_p_list.empty:
            borrar_p = st.selectbox("Eliminar profesional:", df_p_list["Nombre y Apellidos"].tolist())
            if st.button("🗑️ Eliminar"):
                df_p_list = df_p_list[df_p_list["Nombre y Apellidos"] != borrar_p]
                df_p_list.to_csv(PROF_FILE, index=False, encoding='utf-8-sig')
                st.rerun()

    # TAB 3: ESTADÍSTICAS CON FILTRO TEMPORAL
    with t3:
        st.subheader("📊 Análisis de Actividad")
        df_s = pd.read_csv(SOLICITUDES_FILE)
        df_aceptadas = df_s[df_s["Estado"] == "Aceptada ✅"]

        # Filtro específico para las estadísticas
        st.write("---")
        st.write("#### 📅 Filtrar periodo de estadísticas")
        ce1, ce2 = st.columns(2)
        mes_e = ce1.selectbox("Mes Estadísticas:", ["Todos", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"], key="me")
        anio_e = ce2.selectbox("Año Estadísticas:", ["Todos"] + [str(a) for a in range(2024, 2031)], key="ae")

        df_stats = df_aceptadas.copy()
        if mes_e != "Todos":
            df_stats = df_stats[df_stats["Fecha_Evento"].str.split('/').str[1] == mes_e]
        if anio_e != "Todos":
            df_stats = df_stats[df_stats["Fecha_Evento"].str.split('/').str[2] == anio_e]

        if df_stats.empty:
            st.info("No hay datos para el periodo seleccionado.")
        else:
            col_est1, col_est2 = st.columns(2)
            with col_est1:
                st.write("#### Por Profesional")
                conteo_p = df_stats["Solicitante"].value_counts().reset_index()
                conteo_p.columns = ["Profesional", "Cambios"]
                st.dataframe(conteo_p, hide_index=True, use_container_width=True)
                st.bar_chart(conteo_p.set_index("Profesional"))

            with col_est2:
                st.write("#### Por SUAP / Centro")
                conteo_s = df_stats["SUAP_Origen"].value_counts().reset_index()
                conteo_s.columns = ["SUAP", "Total"]
                st.dataframe(conteo_s, hide_index=True, use_container_width=True)
                st.bar_chart(conteo_s.set_index("SUAP"))

    # TAB 4: EXPORTAR
    with t4:
        df_final = pd.read_csv(SOLICITUDES_FILE)
        csv = df_final.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 Descargar Registro Único", csv, "registro_guardias_jaen.csv", "text/csv")