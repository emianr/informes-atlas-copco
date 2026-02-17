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
        "actividades": "• Inspección de fugas: Revisión visual de circuitos de aire y aceite.\n• Verificación de lubricante: Chequeo de nivel por visor.\n• Revisión enfriador: Inspección visual.\n• Monitoreo de controlador: Prueba carga/descarga.",
        "condicion": "El equipo opera bajo parámetros estables. Se observa saturación normal en enfriadores.",
        "recomendaciones": "• Nota técnica: Equipo supera horas recomendadas. Se sugiere overhaul."
    },
    "P1": {
        "actividades": "• Cambio de filtros de aire y aceite.\n• Limpieza general del equipo.\n• Verificación de parámetros operativos bajo carga.",
        "condicion": "Equipo operativo tras mantenimiento P1. Parámetros en rango nominal.",
        "recomendaciones": "• Continuar con plan de mantenimiento preventivo."
    },
    "P2": {
        "actividades": "• Cambio de aceite y kit de filtros.\n• Limpieza profunda de radiadores.\n• Engrase de rodamientos motor.",
        "condicion": "Equipo en óptimas condiciones tras servicio P2.",
        "recomendaciones": "• Se sugiere limpieza frecuente del área para evitar saturación."
    }
}

# --- 4. INTERFAZ DE USUARIO ---
st.title("🚀 Atlas Copco Tracker - Spence")
tab1, tab2 = st.tabs(["📋 Generar Informe", "📊 Historial Editable"])

with tab1:
    c_sel1, c_sel2 = st.columns(2)
    with c_sel1:
        tag_sel = st.selectbox("Seleccione el TAG del equipo", list(equipos_db.keys()))
    with c_sel2:
        tipo_mant = st.selectbox("Tipo de Mantención", ["INSPECCIÓN", "P1", "P2"])

    mod_aut, ser_aut, loc_aut, area_aut = equipos_db[tag_sel]
    txt_auto = plantillas[tipo_mant]
    
    # Sugerencia de horas según último registro
    ultimo = df_historial[df_historial["TAG"] == tag_sel].tail(1)
    h_sug = int(ultimo["Horas_Marcha"].values[0]) if not ultimo.empty else 0

    with st.form("editor_informe"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_sel = st.date_input("Fecha de atención", datetime.now())
            cliente_cont = st.text_input("Contacto Cliente", "Pamela Tapia")
            tec1 = st.text_input("Técnico 1 (Líder)", "Ignacio Morales")
        with col2:
            h_marcha = st.number_input("Horas Totales Marcha", value=h_sug)
            h_carga = st.number_input("Horas Carga", value=0)
            tec2 = st.text_input("Técnico 2", "Emian Sanchez")

        st.subheader("⚙️ Parámetros Operacionales (Dinámicos)")
        p1, p2, p3 = st.columns(3)
        with p1: v_p_carga = st.text_input("Presión de Carga (bar)", "6.4")
        with p2: v_p_descarga = st.text_input("Presión de Descarga (bar)", "6.8")
        with p3: v_t_salida = st.text_input("Temp. Salida Elemento (°C)", "80")

        # Áreas de texto con carga automática de plantillas
        alcance_val = f"Se realizó {tipo_mant.lower()} a equipo compresor {mod_aut} TAG {tag_sel} de {area_aut}, {loc_aut}."
        alcance_manual = st.text_area("Alcance del Trabajo", value=alcance_val)
        ops_manual = st.text_area("Actividades Realizadas (Operaciones)", value=txt_auto["actividades"], height=150)
        cond_manual = st.text_area("Condición Final", value=txt_auto["condicion"])

        enviar = st.form_submit_button("💾 GUARDAR Y GENERAR REPORTE")

    if enviar:
        try:
            doc = DocxTemplate("InformeInspección.docx")
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            fecha_txt = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"

            # MAPEO COMPLETO HACIA ETIQUETAS {{ }} DEL WORD
            contexto = {
                "fecha": fecha_txt,
                "cliente_contact": cliente_cont,
                "alcanze_intervencion": alcance_manual,
                "p_carga": v_p_carga,
                "p_descarga": v_p_descarga,
                "temp_salida": v_t_salida,
                "estado_entrega": cond_manual,
                "tecnico_1": tec1,
                "tecnico_2": tec2,
                "act_1": "Mantenimiento",
                "h_1": "8", "h_2": "8",
                "equipo_modelo": mod_aut,
                "serie": ser_aut,
                "horas_marcha": f"{h_marcha} Hrs.",
                "tipo_orden": tipo_mant,
                "horas_totales_despues": h_marcha,
                "horas_carga_despues": h_carga,
                "operaciones_dinamicas": ops_manual,
                "tag": tag_sel
            }

            doc.render(contexto)
            output = io.BytesIO()
            doc.save(output)
            
            # Guardado en base de datos CSV
            nuevo_reg = pd.DataFrame([[fecha_sel, tag_sel, h_marcha, h_carga, tec1, tec2, cliente_cont]], 
                                     columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])
            df_historial = pd.concat([df_historial, nuevo_reg], ignore_index=True)
            df_historial.to_csv(DB_FILE, index=False)

            st.success("✅ Registro guardado y reporte generado.")
            st.download_button("📥 DESCARGAR REPORTE", output.getvalue(), f"Informe_{tag_sel}.docx")
        except Exception as e:
            st.error(f"❌ Error al procesar el Word: {e}")

with tab2:
    st.subheader("🛠️ Administración de Historial")
    df_actualizado = cargar_datos()
    st.data_editor(df_actualizado, num_rows="dynamic", use_container_width=True)
