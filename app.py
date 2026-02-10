import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io

st.set_page_config(page_title="Atlas Copco App", layout="wide")

# --- AQUÍ ESTÁ LA ESTRUCTURA DE LAS MANTENCIONES ---
# Estos textos reemplazarán a {{ actividades_ejecutadas }} en tu Word
datos_manto = {
    "INSPECCIÓN": "Se realizó inspección visual, verificación de fugas, niveles de aceite, limpieza de condensado y chequeo de parámetros operacionales.",
    "P1": "MANTENCIÓN P1: Se realiza cambio de filtros de aire y aceite, toma de muestras de lubricante y limpieza general del equipo.",
    "P2": "MANTENCIÓN P2: Incluye P1 + Limpieza técnica de enfriadores de aire/aceite, engrase de motor y revisión de válvulas termostáticas.",
    "P3": "MANTENCIÓN P3 (OVERHAUL): Incluye P2 + Cambio de kit de descarga, revisión de elemento compresor y separador de aire/aceite."
}

st.title("Sistema de Informes Atlas Copco")

with st.form("editor_informe"):
    col1, col2 = st.columns(2)
    with col1:
        fecha_sel = st.date_input("Fecha del Servicio", datetime.now())
        cliente_nom = st.text_input("Nombre del Cliente", "MINERA SPENCE S.A")
        contacto = st.text_input("Contacto/Dueño de Área", "Pamela Tápia")
        tipo_servicio = st.selectbox("Tipo de Servicio", ["INSPECCIÓN", "P1", "P2", "P3"])
    
    with col2:
        tag_equipo = st.text_input("TAG del Equipo", "35-GC-005")
        h_marcha = st.number_input("Horas Totales de Marcha", value=65287)
        h_carga = st.number_input("Horas Carga", value=30550)
        serie = st.text_input("Número de Serie", "AIF095301")

    # Sección para los técnicos
    st.subheader("Personal en Terreno")
    t1, t2 = st.columns(2)
    with t1:
        tec1 = st.text_input("Técnico 1", "Ignacio Morales")
    with t2:
        tec2 = st.text_input("Técnico 2", "Emian Sanchez")

    preparar = st.form_submit_button("1. PROCESAR DATOS")

if preparar:
    try:
        doc = DocxTemplate("InformeInspección.docx")
        
        # Lógica para la nota de Overhaul automática
        aviso = ""
        if h_marcha > 40000:
            aviso = "NOTA: El equipo supera las 40.000 horas. Se recomienda realizar Overhaul según manual del fabricante."

        # ESTA ES LA ESTRUCTURA QUE SE ENVÍA AL WORD
        contexto = {
            "fecha": fecha_sel.strftime("%d de %B, %Y"),
            "cliente": cliente_nom,
            "cliente_contacto": contacto,
            "tipo_orden": tipo_servicio,
            "tag": tag_equipo,
            "serie": serie,
            "tecnico_1": tec1,
            "tecnico_2": tec2,
            "horas_totales_despues": f"{h_marcha} Hrs.",
            "horas_carga_despues": f"{h_carga} Hrs.",
            "actividades_ejecutadas": datos_manto[tipo_servicio], # Aquí se elige P1, P2 o P3
            "nota_overhaul": aviso
        }
        
        doc.render(contexto)
        
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        st.success("✅ ¡Estructura generada correctamente!")
        
        st.download_button(
            label="📥 DESCARGAR INFORME EDITADO",
            data=output,
            file_name=f"Informe_{tag_equipo}_{tipo_servicio}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        st.error(f"Error al editar el Word: {e}")
