import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import io
import urllib.parse

# --- 1. CONFIGURACIÓN Y PRIVACIDAD ---
st.set_page_config(page_title="Gestión Guardias Jaén", layout="wide", page_icon="🏥")

hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

try:
    st.image("images.png", width=150)
except:
    pass

# --- 2. CONEXIÓN SEGURA CON GOOGLE SHEETS ---
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
        st.error(f"Error crítico al guardar en la pestaña '{pestana}'. Verifica que la pestaña existe en el Excel y los encabezados son correctos.")
        return False

# --- 3. FUNCIONES AUXILIARES ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

def ir_a(p):
    st.session_state.pagina = p
    st.rerun()

def generar_link_email(email_destino, nombre, estado, fecha, suap):
    asunto = f"Resolución de Cambio de Guardia - {fecha}"
    cuerpo = f"Estimado/a {nombre},\n\nDesde la Administración le notificamos que su solicitud de cambio de guardia en el centro {suap} para la fecha {fecha} ha sido revisada.\n\nESTADO DE LA SOLICITUD: {estado.upper()}.\n\nPara cualquier duda, póngase en contacto con la administración del distrito.\n\nUn cordial saludo."
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
    st.title("📝 Solicitud de Cambio de Guardia")
    if st.button("← Volver"): ir_a('inicio')
    
    df_p = cargar_datos("Profesionales")
    df_suap = cargar_datos("SUAP")
    
    if df_p.empty or df_suap.empty:
        st.warning("⚠️ Faltan datos básicos. El administrador debe añadir Profesionales y centros SUAP primero.")
    else:
        nombres = sorted(df_p["Nombre y Apellidos"].tolist())
        suaps = sorted(df_suap["Nombre_SUAP"].tolist())
        
        st.info("💡 Completa todos los campos. El DNI actúa como firma digital de conformidad.")
        
        with st.form("form_cambio_guardia"):
            st.markdown("### Tus Datos (Solicitante)")
            c1, c2 = st.columns(2)
            solicitante = c1.selectbox("Tu Nombre:", ["Selecciona..."] + nombres)
            dni_sol = c2.text_input("Tu DNI (Firma digital):", max_chars=12)
            
            c3, c4 = st.columns(2)
            suap_sol = c3.selectbox("Tu SUAP actual:", ["Selecciona..."] + suaps)
            fecha_sol = c4.date_input("Día de tu guardia:")
            
            st.markdown("### Datos del Compañero (Receptor)")
            c5, c6 = st.columns(2)
            receptor = c5.selectbox("Nombre del compañero:", ["Selecciona..."] + nombres)
            dni_rec = c6.text_input("DNI del compañero (Firma digital):", max_chars=12)
            
            c7, c8 = st.columns(2)
            suap_rec = c7.selectbox("SUAP del compañero:", ["Selecciona..."] + suaps)
            fecha_rec = c8.date_input("Día de su guardia:")
            
            st.markdown("---")
            if st.form_submit_button("SOLICITAR CAMBIO", use_container_width=True):
                if "Selecciona..." in [solicitante, suap_sol, receptor, suap_rec]:
                    st.error("Por favor, selecciona los nombres y SUAP de los desplegables.")
                elif not dni_sol.strip() or not dni_rec.strip():
                    st.error("Es obligatorio introducir el DNI de ambos profesionales como firma digital.")
                elif solicitante == receptor:
                    st.error("El solicitante y el receptor no pueden ser la misma persona.")
                else:
                    df_s = cargar_datos("Solicitudes")
                    if df_s.empty:
                        df_s = pd.DataFrame(columns=[
                            "ID", "Fecha_Peticion", "Solicitante", "DNI_Solicitante", "SUAP_Solicitante", "Fecha_Guardia_Sol", 
                            "Receptor", "DNI_Receptor", "SUAP_Receptor", "Fecha_Guardia_Rec", "Estado", "Resumen"
                        ])
                    
                    nuevo_id = 1 if df_s.empty else int(pd.to_numeric(df_s["ID"]).max() + 1)
                    
                    texto_resumen = f"{solicitante} con guardia en {suap_sol} el día {fecha_sol.strftime('%d/%m/%Y')} CAMBIA LA GUARDIA a {receptor} con guardia en {suap_rec} el día {fecha_rec.strftime('%d/%m/%Y')}."
                    
                    nueva_fila = pd.DataFrame([{
                        "ID": nuevo_id,
                        "Fecha_Peticion": datetime.now().strftime('%d/%m/%Y %H:%M'),
                        "Solicitante": solicitante,
                        "DNI_Solicitante": dni_sol.upper(),
                        "SUAP_Solicitante": suap_sol,
                        "Fecha_Guardia_Sol": fecha_sol.strftime('%d/%m/%Y'),
                        "Receptor": receptor,
                        "DNI_Receptor": dni_rec.upper(),
                        "SUAP_Receptor": suap_rec,
                        "Fecha_Guardia_Rec": fecha_rec.strftime('%d/%m/%Y'),
                        "Estado": "Pendiente",
                        "Resumen": texto_resumen
                    }])
                    
                    if guardar_datos("Solicitudes", pd.concat([df_s, nueva_fila], ignore_index=True)):
                        st.balloons()
                        st.success(f"✅ ¡Solicitud firmada y enviada!\n\n**Resumen:** {texto_resumen}")
                        st.button("Ir al Inicio", on_click=lambda: ir_a('inicio'))

# ---------------------------------------------------------
# ⚙️ PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif st.session_state.pagina == 'admin_panel':
    st.title("⚙️ Panel de Control")
    if st.sidebar.button("Cerrar Sesión"): ir_a('inicio')

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Solicitudes", "👥 Alta Profesionales", "🏥 Alta SUAP", "🔍 Buscador/Historial"])

    # --- PESTAÑA 1: SOLICITUDES ---
    with tab1:
        df_s = cargar_datos("Solicitudes")
        df_p = cargar_datos("Profesionales")
        
        if not df_s.empty:
            st.markdown("### Registro de Solicitudes")
            def color_est(val):
                c = 'green' if 'Aceptada' in str(val) else 'red' if 'Rechazada' in str(val) else 'orange'
                return f'color: {c}'
            
            columnas_mostrar = ["ID", "Fecha_Peticion", "Resumen", "Estado"]
            columnas_existentes = [col for col in columnas_mostrar if col in df_s.columns]
            st.dataframe(df_s[columnas_existentes].style.applymap(color_est, subset=['Estado'] if 'Estado' in df_s.columns else []), use_container_width=True, hide_index=True)
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            id_sel = c1.selectbox("Gestionar ID:", df_s["ID"].tolist())
            acc = c2.selectbox("Nueva Acción:", ["Aceptada ✅", "Rechazada ❌"])
            
            if c3.button("Confirmar Estado"):
                df_s.loc[df_s["ID"] == id_sel, "Estado"] = acc
                if guardar_datos("Solicitudes", df_s):
                    st.success("Estado actualizado."); st.rerun()
            
            st.markdown("---")
            col_notif, col_borrar = st.columns(2)
            
            with col_notif:
                st.markdown("#### 📧 Notificar Resolución")
                fila = df_s[df_s["ID"] == id_sel].iloc[0]
                try:
                    email_sol = df_p[df_p["Nombre y Apellidos"] == fila["Solicitante"]]["Correo"].values[0]
                    fecha_guardia = fila.get("Fecha_Guardia_Sol", "fecha solicitada")
                    suap_sol = fila.get("SUAP_Solicitante", "su centro")
                    link = generar_link_email(email_sol, fila["Solicitante"], fila["Estado"], fecha_guardia, suap_sol)
                    st.markdown(f'<a href="{link}" target="_blank" style="text-decoration:none;"><div style="background-color:#007bff;color:white;padding:10px;border-radius:5px;text-align:center;">Enviar email a {fila["Solicitante"]}</div></a>', unsafe_allow_html=True)
                except:
                    st.info("Añade el email del profesional en 'Alta Profesionales' para poder notificarle.")
            
            with col_borrar:
                st.markdown("#### 🗑️ Eliminar Registros")
                ids_a_borrar = st.multiselect("Selecciona IDs para ELIMINAR:", df_s["ID"].tolist())
                if st.button("Eliminar Seleccionados"):
                    df_s = df_s[~df_s["ID"].isin(ids_a_borrar)]
                    if guardar_datos("Solicitudes", df_s):
                        st.success("Borrados correctamente"); st.rerun()

        else:
            st.info("No hay solicitudes registradas.")

    # --- PESTAÑA 2: ALTA PROFESIONALES ---
    with tab2:
        st.subheader("Registrar Profesional")
        with st.form("alta_pro", clear_on_submit=True):
            col_p1, col_p2 = st.columns(2)
            nom = col_p1.text_input("Nombre y Apellidos")
            dni = col_p2.text_input("DNI")
            
            col_p3, col_p4 = st.columns(2)
            suap_prof = col_p3.text_input("SUAP Habitual (Opcional)")
            correo = col_p4.text_input("Correo Electrónico")
            
            if st.form_submit_button("Guardar Profesional"):
                if nom and dni and correo:
                    df_prof = cargar_datos("Profesionales")
                    if df_prof.empty: df_prof = pd.DataFrame(columns=["Nombre y Apellidos", "DNI", "SUAP", "Correo"])
                    
                    nueva_fila_pro = pd.DataFrame([{"Nombre y Apellidos": nom, "DNI": dni.upper(), "SUAP": suap_prof, "Correo": correo}])
                    if guardar_datos("Profesionales", pd.concat([df_prof, nueva_fila_pro], ignore_index=True)):
                        st.success(f"{nom} guardado."); st.rerun()
                else:
                    st.error("El Nombre, DNI y Correo son obligatorios.")
        
        st.divider()
        df_pro_lista = cargar_datos("Profesionales")
        if not df_pro_lista.empty:
            st.dataframe(df_pro_lista, use_container_width=True, hide_index=True)
            nombres_borrar = st.multiselect("Selecciona profesionales para eliminar:", df_pro_lista["Nombre y Apellidos"].tolist())
            if st.button("Eliminar Profesionales"):
                df_pro_lista = df_pro_lista[~df_pro_lista["Nombre y Apellidos"].isin(nombres_borrar)]
                guardar_datos("Profesionales", df_pro_lista)
                st.rerun()

    # --- PESTAÑA 3: ALTA SUAP ---
    with tab3:
        st.subheader("Registrar Centro SUAP")
        with st.form("alta_suap", clear_on_submit=True):
            nombre_suap = st.text_input("Nombre del SUAP")
            if st.form_submit_button("Guardar SUAP"):
                if nombre_suap:
                    df_suap = cargar_datos("SUAP")
                    if df_suap.empty: df_suap = pd.DataFrame(columns=["Nombre_SUAP"])
                    if guardar_datos("SUAP", pd.concat([df_suap, pd.DataFrame([{"Nombre_SUAP": nombre_suap}])], ignore_index=True)):
                        st.success(f"SUAP '{nombre_suap}' creado."); st.rerun()
        
        st.divider()
        df_suap_lista = cargar_datos("SUAP")
        if not df_suap_lista.empty:
            st.dataframe(df_suap_lista, use_container_width=True, hide_index=True)
            suap_borrar = st.multiselect("Selecciona SUAPs para eliminar:", df_suap_lista["Nombre_SUAP"].tolist())
            if st.button("Eliminar SUAPs"):
                df_suap_lista = df_suap_lista[~df_suap_lista["Nombre_SUAP"].isin(suap_borrar)]
                guardar_datos("SUAP", df_suap_lista)
                st.rerun()

    # --- PESTAÑA 4: BUSCADOR HISTORIAL ---
    with tab4:
        st.subheader("🔍 Historial por Profesional")
        df_s = cargar_datos("Solicitudes")
        df_p = cargar_datos("Profesionales")
        
        if not df_p.empty and not df_s.empty:
            busqueda = st.selectbox("Escribe el nombre del profesional:", ["Selecciona..."] + sorted(df_p["Nombre y Apellidos"].tolist()))
            
            if busqueda != "Selecciona...":
                if "Solicitante" in df_s.columns and "Receptor" in df_s.columns:
                    df_historial = df_s[(df_s["Solicitante"] == busqueda) | (df_s["Receptor"] == busqueda)]
                    
                    if df_historial.empty:
                        st.info(f"No hay registros de guardias para {busqueda}.")
                    else:
                        st.success(f"Se han encontrado {len(df_historial)} registros para {busqueda}.")
                        columnas_historial = ["Fecha_Peticion", "Resumen", "Estado"]
                        col_disp = [col for col in columnas_historial if col in df_historial.columns]
                        st.dataframe(df_historial[col_disp], use_container_width=True, hide_index=True)
                else:
                    st.info("Formato antiguo detectado. Por favor, limpia las solicitudes en Google Sheets.")
        else:
            st.info("Aún no hay suficientes datos para realizar búsquedas.")