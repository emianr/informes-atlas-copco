import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import os
import pandas as pd

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Atlas Copco Tracker - Spence", layout="wide")
BASE_DIR = "Informes_Generados" # Carpeta principal

# --- 2. BASE DE DATOS DE EQUIPOS ---
equipos_db = {
    "70-GC-013": ["GA 132", "AIF095296", "descarga acido", "área húmeda"],
    "70-GC-014": ["GA 132", "AIF095297", "descarga acido", "área húmeda"],
    "050-GD-001": ["GA 45", "API542705", "planta sx", "área húmeda"],
    "35-GC-006": ["GA 250", "AIF095420", "chancado secundario", "área seca"],
    "TALLER-01": ["GA18", "API335343", "taller", "área seca"]
}

# --- 3. FUNCIONES DE APOYO ---
def obtener_plantilla(tipo, tag, mod, loc, area):
    # (Mantenemos la lógica de textos que definimos antes)
    if tipo == "INSPECCIÓN":
        return {
            "alcance": f"Se realizó inspección a equipo {mod} TAG {tag}...",
            "actividades": "• Inspección de fugas...\n• Verificación de lubricante...\n• Purga condensado...",
            "condicion": "Equipo estable pero con alza de temperatura...",
            "recomendaciones": "• Nota técnica: Sugerir overhaul...",
            "p_c": "6.2", "p_d": "6.7", "t_s": "86"
        }
    # ... (P1 y P2 se mantienen igual)
    return {}

# --- 4. INTERFAZ ---
tag_sel = st.selectbox("Seleccione el Equipo (TAG)", list(equipos_db.keys()))
tipo_sel = st.selectbox("Tipo de Trabajo", ["INSPECCIÓN", "P1", "P2"])

mod, ser, loc, area = equipos_db[tag_sel]
plantilla = obtener_plantilla(tipo_sel, tag_sel, mod, loc, area)

with st.form("main_form"):
    c1, c2 = st.columns(2)
    with c1:
        fecha = st.date_input("Fecha", datetime.now())
        cliente = st.text_input("Contacto", "Pamela Tapia")
        tec1 = st.text_input("Técnico 1", "Ignacio Morales")
    with c2:
        h_m = st.number_input("Horas Marcha", value=0)
        h_c = st.number_input("Horas Carga", value=0)
        tec2 = st.text_input("Técnico 2", "Emian Sanchez")

    st.subheader("⚙️ Parámetros")
    p1, p2, p3 = st.columns(3)
    with p1: pc = st.text_input("Presión Carga", plantilla.get("p_c", "0"))
    with p2: pd = st.text_input("Presión Descarga", plantilla.get("p_d", "0"))
    with p3: ts = st.text_input("Temp Salida", plantilla.get("t_s", "0"))

    alcance = st.text_area("Alcance", value=plantilla.get("alcance", ""))
    actividades = st.text_area("Actividades", value=plantilla.get("actividades", ""), height=150)
    condicion = st.text_area("Condición Final", value=plantilla.get("condicion", ""))
    recom = st.text_area("Recomendaciones", value=plantilla.get("recomendaciones", ""))

    generar = st.form_submit_button("💾 GENERAR Y ARCHIVAR REPORTE")

if generar:
    try:
        doc = DocxTemplate("InformeInspección.docx")
        fecha_str = fecha.strftime("%Y-%m-%d")
        
        contexto = {
            "fecha": fecha_str, "cliente_contact": cliente, "alcanze_intervencion": alcance,
            "operaciones_dinamicas": actividades, "estado_entrega": condicion, "recomendaciones": recom,
            "p_carga": pc, "p_descarga": pd, "temp_salida": ts,
            "tecnico_1": tec1, "tecnico_2": tec2, "act_1": "Mantenimiento",
            "h_1": "8", "h_2": "8", "equipo_modelo": mod, "serie": ser,
            "horas_marcha": f"{h_m} Hrs.", "tipo_orden": tipo_sel, "tag": tag_sel,
            "horas_totales_despues": h_m, "horas_carga_despues": h_c
        }
        
        doc.render(contexto)
        
        # --- LÓGICA DE CARPETAS ---
        # 1. Crear carpeta principal si no existe
        if not os.path.exists(BASE_DIR):
            os.makedirs(BASE_DIR)
        
        # 2. Crear carpeta del TAG específico
        path_equipo = os.path.join(BASE_DIR, tag_sel)
        if not os.path.exists(path_equipo):
            os.makedirs(path_equipo)
        
        # 3. Definir nombre del archivo
        nombre_archivo = f"Reporte_{tag_sel}_{fecha_str}.docx"
        ruta_final = os.path.join(path_equipo, nombre_archivo)
        
        # Guardar físicamente en el servidor/PC
        doc.save(ruta_final)
        
        # Preparar para descarga en navegador (opcional)
        bio = io.BytesIO()
        doc.save(bio)
        
        st.success(f"✅ Reporte guardado en: {ruta_final}")
        st.download_button("📥 Descargar copia", bio.getvalue(), nombre_archivo)
        
    except Exception as e:
        st.error(f"Error: {e}")
