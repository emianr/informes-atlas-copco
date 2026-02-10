import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io

# Configuración de la página
st.set_page_config(page_title="Atlas Copco App", layout="wide")

st.title("🚀 Generador de Informes Atlas Copco")

# --- BASE DE DATOS DE EQUIPOS (Basada en tu tabla) ---
modelos_equipos = ["GA 132", "GA 45", "ZT 37", "GA 30", "GA 250", "GA 37", "GA 75", "GA 90", "GA 18"]
areas_trabajo = ["Descarga acido", "PLANTA SX", "PLANTA BORRA", "ÁREA HÚMEDA", "SECA", "TRUCK SHOP", "TALLER"]

with st.form("editor_informe"):
    st.subheader("1. Identificación del Equipo")
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_sel = st.date_input("Fecha del Servicio", datetime.now())
        cliente_nom = st.text_input("Cliente", "MINERA SPENCE S.A")
        # Nuevo: Selección de Modelo
        modelo_sel = st.selectbox("Modelo del Equipo", modelos_equipos)
        # Nuevo: Selección de Área
        area_sel = st.selectbox("Área de Trabajo", areas_trabajo)
    
    with col2:
        tag_equipo = st.text_input("TAG del Equipo", "35-GC-005")
        serie = st.text_input("Número de Serie", "AIF095301")
        tipo_servicio = st.selectbox("Tipo de Servicio", ["INSPECCIÓN", "P1", "P2", "P3"])

    st.subheader("2. Contadores y Personal")
    c1, c2, c3 = st.columns(3)
    with c1:
        h_marcha = st.number_input("Horas Totales Marcha", value=65287)
    with c2:
        h_carga = st.number_input("Horas Carga", value=30550)
    with c3:
        tec1 = st.text_input("Técnico Responsable", "Ignacio Morales")

    st.subheader("3. Edición de Textos del Informe")
    # Aquí puedes escribir lo que quieras para que aparezca en el Word
    alcance_manual = st.text_area("Alcance de la Intervención", 
        f"Se realizó inspección a equipo compresor {modelo_sel} con identificación TAG {tag_equipo} de {area_sel}.")
    
    actividades_manual = st.text_area("Actividades Ejecutadas", 
        "Escriba aquí las tareas realizadas...")

    preparar = st.form_submit_button("1. GENERAR INFORME")

if preparar:
    try:
        doc = DocxTemplate("InformeInspección.docx")
        
        # Fecha en español
        meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
        fecha_texto = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"

        # Nota de overhaul automática
        aviso_overhaul = ""
        if h_marcha > 40000:
            aviso_overhaul = "NOTA TÉCNICA: Equipo sobre 40.000 hrs. Se recomienda Overhaul."

        # Mapeo para el Word
        contexto = {
            "fecha": fecha_texto,
            "cliente": cliente_nom,
            "equipo_modelo": modelo_sel, # Nueva etiqueta
            "area": area_sel,           # Nueva etiqueta
            "tag": tag_equipo,
            "serie": serie,
            "tipo_orden": tipo_servicio,
            "tecnico_1": tec1,
            "horas_totales_despues": f"{h_marcha} Hrs.",
            "horas_carga_despues": f"{h_carga} Hrs.",
            "alcanze_intervencion": alcance_manual, # Etiqueta para el párrafo de alcance
            "actividades_ejecutadas": actividades_manual, # Etiqueta para las tareas
            "nota_overhaul": aviso_overhaul
        }
        
        doc.render(contexto)
        
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        st.success("✅ ¡Informe procesado!")
        
        st.download_button(
            label="📥 DESCARGAR WORD",
            data=output,
            file_name=f"Informe_{tag_equipo}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        st.error(f"Error: {e}")
