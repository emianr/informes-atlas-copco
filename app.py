import streamlit as st
from docxtpl import DocxTemplate
import pandas as pd
import io
import os

# Configuración de la página
st.set_page_config(page_title="Admin Atlas Copco", layout="wide")

# Diccionario de operaciones para que cambie según la selección
operaciones_dict = {
    "INSPECCIÓN": "Inspección visual de equipo",
    "P1": "Mantenimiento Preventivo P1 - Cambio de filtros y revisión general",
    "P2": "Mantenimiento Preventivo P2 - Cambio de kit de filtros y aceite",
    "P3": "Mantenimiento Preventivo P3 - Intervención mayor (Overhaul)"
}

# Base de datos de equipos (GA 132, etc.)
equipos_db = {
    "70-GC-013": ["GA 132", "AIF095296", "Descarga acido", "ÁREA HÚMEDA"],
    "70-GC-014": ["GA 132", "AIF095297", "Descarga acido", "ÁREA HÚMEDA"]
}

st.title("🚀 Panel de Administración Atlas Copco")

tab1, tab2 = st.tabs(["Generar Reporte", "⚙️ Administrar Historial"])

with tab1:
    tag_sel = st.selectbox("Seleccione TAG", list(equipos_db.keys()))
    mod, ser, are, cla = equipos_db[tag_sel]

    with st.form("form_final"):
        c1, c2 = st.columns(2)
        with c1:
            tipo_mantenimiento = st.selectbox("Tipo de Mantención", list(operaciones_dict.keys()))
            tec1 = st.text_input("Técnico 1", "Ignacio Morales")
        with c2:
            tec2 = st.text_input("Técnico 2", "Emian Sanchez")
            h_marcha = st.number_input("Horas de Marcha", value=0)
        
        # Botón de envío para evitar el error "Missing Submit Button"
        boton_enviar = st.form_submit_button("💾 GUARDAR Y GENERAR REPORTE")

    if boton_enviar:
        try:
            doc = DocxTemplate("InformeInspección.docx")
            contexto = {
                "tag": tag_sel,
                "equipo_modelo": mod,
                "serie": ser,
                "tecnico_1": tec1,
                "tecnico_2": tec2,
                "horas_totales_despues": f"{h_marcha} Hrs.",
                "operaciones_dinamicas": operaciones_dict[tipo_mantenimiento] # Cambia el texto dinámicamente
            }
            doc.render(contexto)
            bio = io.BytesIO()
            doc.save(bio)
            st.success(f"Reporte de {tipo_mantenimiento} listo para descargar.")
            st.download_button("📥 Descargar Reporte", bio.getvalue(), f"Reporte_{tag_sel}.docx")
        except Exception as e:
            st.error(f"Error: {e}")

with tab2:
    st.subheader("Edición de Datos")
    st.info("Aquí el otro administrador puede corregir el historial directamente.")
    # Código para cargar y editar el CSV aquí...
