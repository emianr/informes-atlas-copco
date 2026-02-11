import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

st.set_page_config(page_title="Atlas Copco Tracker", layout="wide")

# --- BASE DE DATOS LOCAL ---
DB_FILE = "historial_horas.csv"
if os.path.exists(DB_FILE):
    df_historial = pd.read_csv(DB_FILE)
else:
    df_historial = pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico", "Contacto"])

# --- BASE DE DATOS DE EQUIPOS ---
equipos_db = {
    "70-GC-013": ["GA 132", "AIF095296", "Descarga acido", "ÁREA HÚMEDA"],
    "70-GC-014": ["GA 132", "AIF095297", "Descarga acido", "ÁREA HÚMEDA"],
    "050-GD-001": ["GA 45", "API542705", "PLANTA SX", "ÁREA HÚMEDA"],
    "050-GD-002": ["GA 45", "API542706", "PLANTA SX", "ÁREA HÚMEDA"],
    "050-GC-003": ["ZT 37", "API791692", "PLANTA SX", "ÁREA HÚMEDA"],
    "050-GC-004": ["ZT 37", "API791693", "PLANTA SX", "ÁREA HÚMEDA"],
    "050-GC-015": ["GA 30", "API501440", "PLANTA BORRA", "ÁREA HÚMEDA"],
    "65-GC-011": ["GA 250", "APF253581", "PATIO ESTANQUES", "ÁREA HÚMEDA"],
    "65-GC-009": ["GA 250", "APF253608", "PATIO ESTANQUES", "ÁREA HÚMEDA"],
    "35-GC-006": ["GA 250", "AIF095420", "Chancado secundario", "ÁREA SECA"],
    "35-GC-007": ["GA 250", "AIF095421", "Chancado secundario", "ÁREA SECA"],
    "35-GC-008": ["GA 250", "AIF095302", "Chancado secundario", "ÁREA SECA"],
    "20-GC-004": ["GA 37", "AII390776", "Mina", "MINA"],
    "20-GC-001": ["GA 75", "AII482673", "TRUCK SHOP", "MINA"],
    "20-GC-002": ["GA 75", "AII482674", "TRUCK SHOP", "MINA"],
    "20-GC-003": ["GA 90", "AIF095178", "TRUCK SHOP", "MINA"],
    "TALLER-01": ["GA18", "API335343", "TALLER", "ÁREA SECA"]
}

st.title("🚀 Gestión de Compresores")

tab1, tab2 = st.tabs(["Generar Informe", "Historial"])

with tab1:
    with st.form("editor_informe"):
        tag_sel = st.selectbox("Seleccione el TAG", list(equipos_db.keys()))
        modelo_aut, serie_aut, area_aut, clase_aut = equipos_db[tag_sel]
        
        c1, c2 = st.columns(2)
        with c1:
            fecha_sel = st.date_input("Fecha", datetime.now())
            # Ajustado a 'cliente_contacto' según tu imagen de plantilla
            cliente_cont = st.text_input("Contacto / Dueño de Área", "Pamela Tapia")
            tipo_servicio = st.selectbox("Tipo de Mantención", ["INSPECCIÓN", "P1", "P2", "P3"])
        with c2:
            h_marcha_val = st.number_input("Horas Totales Marcha", value=0)
            h_carga_val = st.number_input("Horas Carga", value=0)
            tec1_input = st.text_input("Técnico Responsable", "Ignacio Morales")

        st.subheader("📊 Parámetros Operacionales")
        p1, p2, p3 = st.columns(3)
        with p1: p_carga = st.text_input("Carga (bar)", "6.4")
        with p2: p_descarga = st.text_input("Descarga (bar)", "6.8")
        with p3: temp_sal = st.text_input("Temp (°C)", "80")

        # Texto de alcance solicitado: compacto y sin saltos de línea
        alcance_val = f"Se realizó inspección a equipo compresor {modelo_aut} con identificación TAG {tag_sel} de {clase_aut}, {area_aut}, conforme a procedimientos internos y buenas prácticas de mantenimiento."
        alcance_manual = st.text_area("Alcance", value=alcance_val, height=70)
        
        concl_val = f"El equipo se encuentra funcionando en óptimas condiciones, bajo parámetros normales de funcionamiento (Carga: {p_carga} bar / Descarga: {p_descarga} bar, Temp: {temp_sal} °C), con nivel de aceite en rango, sin fugas y filtros operativos."
        conclusiones_manual = st.text_area("Condición Final", value=concl_val, height=70)

        enviar = st.form_submit_button("GENERAR INFORME SIN ESPACIOS")

    if enviar:
        try:
            doc = DocxTemplate("InformeInspección.docx")
            meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
            fecha_txt = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"
            
            contexto = {
                "fecha": fecha_txt,
                "cliente_contacto": cliente_cont, # Coincide con tu imagen
                "tag": tag_sel,
                "equipo_modelo": modelo_aut,
                "serie": serie_aut,
                "area": area_aut,
                "clase_area": clase_aut,
                "tipo_orden": tipo_servicio,
                "tecnico_1": tec1_input,
                "tecnico_2": "Emian Sanchez",
                "act_1": "M.OB.ST",
                "h_1": "8", "h_2": "8",
                "horas_marcha": f"{h_marcha_val} Hrs.",
                "horas_totales_despues": f"{h_marcha_val} Hrs.",
                "horas_carga_despues": f"{h_carga_val} Hrs.",
                # .strip() elimina espacios invisibles que crean hojas extra
                "alcanze_intervencion": alcance_manual.strip(),
                "estado_entrega": conclusiones_manual.strip()
            }
            
            doc.render(contexto)
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            st.success("✅ ¡Hecho! Revisa que el espacio haya desaparecido.")
            st.download_button("📥 DESCARGAR", bio, f"Reporte_{tag_sel}.docx")
        except Exception as e:
            st.error(f"Error: {e}")
