import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io

# Configuración
st.set_page_config(page_title="Atlas Copco Reports", layout="wide")

# Diccionario de actividades basado en tu informe real
actividades_dict = {
    "INSPECCIÓN": "Inspección de fugas, verificación de lubricante, monitoreo de controlador y purga de condensado.",
    "P1": "Mantenimiento P1: Cambio de filtros de aire/aceite y actividades de inspección.",
    "P2": "Mantenimiento P2: Limpieza de enfriadores, engrase y cambio de filtros.",
    "P3": "Mantenimiento P3: Overhaul preventivo, cambio de kits de válvulas y filtros."
}

st.title("Generador de Informes Atlas Copco")

# Formulario
with st.form("form_reporte"):
    col1, col2 = st.columns(2)
    with col1:
        fecha_inf = st.date_input("Fecha", datetime.now())
        cliente = st.text_input("Cliente", "MINERA SPENCE S.A")
        tipo = st.selectbox("Tipo de Actividad", ["INSPECCIÓN", "P1", "P2", "P3"])
    with col2:
        tag = st.text_input("TAG", "35-GC-005")
        h_marcha = st.number_input("Horas Marcha", value=65287)
    
    boton_preparar = st.form_submit_button("1. PREPARAR DOCUMENTO")

if boton_preparar:
    try:
        # IMPORTANTE: Asegúrate de que el nombre coincida con tu archivo en GitHub
        doc = DocxTemplate("InformeInspección.docx") 
        
        # Lógica de aviso de Overhaul
        aviso = "Nota técnica: El equipo supera las 40.000 horas. Se recomienda overhaul." if h_marcha > 40000 else ""

        # Datos para el Word
        contexto = {
            "fecha": fecha_inf.strftime("%d/%m/%Y"),
            "cliente": cliente,
            "tipo_orden": tipo,
            "tag": tag,
            "horas_totales_despues": f"{h_marcha} Hrs.",
            "actividades_ejecutadas": actividades_dict[tipo],
            "nota_overhaul": aviso
        }
        
        doc.render(contexto)
        
        # Crear el archivo en memoria
        bio = io.BytesIO()
        doc.save(bio)
        bio.seek(0)

        st.success("✅ ¡Documento listo para descargar!")
        
        # Botón de descarga
        st.download_button(
            label="📥 CLIC AQUÍ PARA DESCARGAR WORD",
            data=bio,
            file_name=f"Informe_{tag}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        st.error(f"Error: No se encontró la plantilla. Asegúrate de que el nombre sea 'InformeInspección.docx' en GitHub. Detalle: {e}")
