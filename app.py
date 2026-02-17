import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

# --- 1. CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="Atlas Copco Tracker - Spence", layout="wide")

# --- 2. GESTIÓN DE LA BASE DE DATOS (CSV) ---
DB_FILE = "historial_horas.csv"

def cargar_datos():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if not df.empty:
                df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
            return df
        except:
            return pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])
    return pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])

df_historial = cargar_datos()

# --- 3. DICCIONARIOS DE DATOS (EQUIPOS COMPLETOS) ---
# Formato: "TAG": ["Modelo", "Serie", "Ubicación", "Área"]
equipos_db = {
    "70-GC-013": ["GA 132", "AIF095296", "descarga acido", "área húmeda"],
    "70-GC-014": ["GA 132", "AIF095297", "descarga acido", "área húmeda"],
    "050-GD-001": ["GA 45", "API542705", "planta sx", "área húmeda"],
    "050-GD-002": ["GA 45", "API542706", "planta sx", "área húmeda"],
    "050-GC-003": ["ZT 37", "API791692", "planta sx", "área húmeda"],
    "050-GC-004": ["ZT 37", "API791693", "planta sx", "área húmeda"],
    "050-CD-001": ["CD 80+", "API095825", "planta sx", "área húmeda"],
    "050-CD-002": ["CD 80+", "API095826", "planta sx", "área húmeda"],
    "050-GC-015": ["GA 30", "API501440", "planta borra", "área húmeda"],
    "65-GC-011": ["GA 250", "APF253581", "patio estanques", "área húmeda"],
    "65-GC-009": ["GA 250", "APF253608", "patio estanques", "área húmeda"],
    "65-GD-011": ["CD 630", "WXF300015", "patio estanques", "área húmeda"],  
    "65-GD-012": ["CD 630", "WXF300016", "patio estanques", "área húmeda"],  
    "35-GC-006": ["GA 250", "AIF095420", "chancado secundario", "área seca"],
    "35-GC-007": ["GA 250", "AIF095421", "chancado secundario", "área seca"],
    "35-GC-008": ["GA 250", "AIF095302", "chancado secundario", "área seca"],
    "20-GC-004": ["GA 37", "AII390776", "mina", "mina"],
    "20-GC-001": ["GA 75", "AII482673", "truck shop", "mina"],
    "20-GC-002": ["GA 75", "AII482674", "truck shop", "mina"],
    "20-GC-003": ["GA 90", "AIF095178", "truck shop", "mina"],
    "TALLER-01": ["GA18", "API335343", "taller", "área seca"]
}

plantillas = {
    "INSPECCIÓN": {
        "actividades": "• Inspección de fugas: Revisión visual de circuitos de aire y aceite.\n• Verificación de lubricante: Chequeo del nivel de aceite por medio del visor.\n• Revisión enfriador: Inspección visual en enfriador de aire/aceite.\n• Monitoreo de controlador: Prueba carga/descarga del equipo.",
        "condicion": "El equipo opera bajo parámetros estables. Se observa saturación normal en enfriadores.",
        "recomendaciones": "• Nota técnica: El equipo supera las horas recomendadas. Se recomienda overhaul."
    },
    "P1": {
        "actividades": "• Cambio de filtros de aire y aceite.\n• Limpieza general del equipo.\n• Verificación de parámetros operativos.",
        "condicion": "Equipo operativo tras mantenimiento preventivo P1.",
        "recomendaciones": "• Mantener plan de mantenimiento preventivo mensual."
    },
    "P2": {
        "actividades": "• Cambio de aceite y kit de filtros.\n• Limpieza de enfriadores.\n• Engrase de rodamientos motor.",
        "condicion": "Equipo en óptimas condiciones tras servicio P2.",
        "recomendaciones": "• Considerar limpieza preventiva del entorno."
    }
}

# --- 4. INTERFAZ ---
st.title("🚀 Atlas Copco Tracker - Spence")
tab1, tab2 = st.tabs(["📋 Generar Informe", "📊 Historial"])

with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        tag_sel = st.selectbox("Seleccione TAG del equipo", list(equipos_db.keys()))
    with col_b:
        tipo_mant = st.selectbox("Tipo de Servicio", ["INSPECCIÓN", "P1", "P2"])

    mod_aut, ser_aut, loc_aut, area_aut = equipos_db[tag_sel]
    
    # Buscar últimas horas en el historial
    ultimo = df_historial[df_historial["TAG"] == tag_sel].tail(1)
    h_sug = int(ultimo["Horas_Marcha"].values[0]) if not ultimo.empty else 0

    with st.form("editor_informe"):
        c1, c2 = st.columns(2)
        with c1:
            fecha_sel = st.date_input("Fecha", datetime.now())
            cliente = st.text_input("Contacto Cliente", "Pamela Tapia")
            tec1 = st.text_input("Técnico 1", "Ignacio Morales")
        with c2:
            h_m = st.number_input("Horas Marcha", value=h_sug)
            h_c = st.number_input("Horas Carga", value=0)
            tec2 = st.text_input("Técnico 2", "Emian Sanchez")

        st.subheader("⚙️ Parámetros Operacionales")
        p1, p2, p3 = st.columns(3)
        with p1: v_p_carga = st.text_input("Presión Carga (bar)", "6.4")
        with p2: v_p_desc = st.text_input("Presión Descarga (bar)", "6.8")
        with p3: v_t_sal = st.text_input("Temp Salida (°C)", "80")

        alcance_val = f"Se realizó {tipo_mant.lower()} a equipo compresor {mod_aut} TAG {tag_sel} de {area_aut}, {loc_aut}."
        alcance = st.text_area("Alcance", value=alcance_val)
        ops = st.text_area("Actividades", value=plantillas[tipo_mant]["actividades"], height=150)
        cond = st.text_area("Condición Final", value=plantillas[tipo_mant]["condicion"])

        enviar = st.form_submit_button("GENERAR REPORTE")

    if enviar:
        try:
            doc = DocxTemplate("InformeInspección.docx")
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            fecha_txt = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"

            contexto = {
                "fecha": fecha_txt, "cliente_contact": cliente, "tag": tag_sel,
                "alcanze_intervencion": alcance, "p_carga": v_p_carga, "p_descarga": v_p_desc,
                "temp_salida": v_t_sal, "estado_entrega": cond, "operaciones_dinamicas": ops,
                "tecnico_1": tec1, "tecnico_2": tec2, "act_1": "Mantenimiento",
                "h_1": "8", "h_2": "8", "equipo_modelo": mod_aut, "serie": ser_aut,
                "horas_marcha": f"{h_m} Hrs.", "tipo_orden": tipo_mant,
                "horas_totales_despues": h_m, "horas_carga_despues": h_c
            }

            doc.render(contexto)
            output = io.BytesIO()
            doc.save(output)
            
            # Guardar en CSV
            nuevo = pd.DataFrame([[fecha_sel, tag_sel, h_m, h_c, tec1, tec2, cliente]], columns=df_historial.columns)
            pd.concat([df_historial, nuevo]).to_csv(DB_FILE, index=False)

            st.success("✅ Reporte listo")
            st.download_button("📥 Descargar Word", output.getvalue(), f"Informe_{tag_sel}.docx")
        except Exception as e:
            st.error(f"Error: {e}")

with tab2:
    st.subheader("🛠️ Historial")
    st.data_editor(cargar_datos(), num_rows="dynamic")

