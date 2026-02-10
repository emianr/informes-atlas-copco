import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io

# Configuración visual de la página
st.set_page_config(page_title="Atlas Copco Reports", layout="wide")

# --- DICCIONARIO DE ACTIVIDADES (ESTRUCTURA PARA EL WORD) ---
datos_manto = {
    "INSPECCIÓN": "Se realizó inspección visual técnica, verificación de posibles fugas de aire y aceite, chequeo de niveles de lubricante, limpieza de sistema de condensado y monitoreo de parámetros en panel Elektronikon.",
    "P1": "MANTENCIÓN P1: Se ejecutó cambio de filtros de aire (PowerCell), cambio de filtros de aceite, toma de muestra de lubricante para análisis de laboratorio y limpieza general de la unidad.",
    "P2": "MANTENCIÓN P2: Incluye actividades P1 + Limpieza técnica profunda de radiadores/enfriadores, engrase de rodamientos de motor principal y revisión de kit de válvulas termostáticas.",
    "P3": "MANTENCIÓN P3 (OVERHAUL): Incluye actividades P2 + Intervención mayor con cambio de kit de descarga, kit de válvula de presión mínima, cambio de separador aire/aceite y revisión de elemento compresor."
}

st.title("🚀 Generador de Informes Atlas Copco")
st.markdown("Llene los datos a continuación para generar el informe en Word.")

# --- FORMULARIO DE DATOS ---
with st.form("editor_informe"):
    st.subheader("1. Identificación y Equipo")
    col1, col2 = st.columns(2)
    with col1:
        fecha_sel = st.date_input("Fecha del Servicio", datetime.now())
        cliente_nom = st.text_input("Nombre del Cliente", "MINERA SPENCE S.A")
        contacto = st.text_input("Contacto / Dueño de Área", "Pamela Tápia")
        tipo_servicio = st.selectbox("Tipo de Servicio", ["INSPECCIÓN", "P1", "P2", "P3"])
    
    with col2:
        tag_equipo = st.text_input("TAG del Equipo", "35-GC-005")
        serie = st.text_input("Número de Serie", "AIF095301")
        h_marcha = st.number_input("Horas Totales de Marcha", value=65287)
        h_carga = st.number_input("Horas Carga", value=30550)

    st.subheader("2. Personal Técnico")
    t1, t2 = st.columns(2)
    with t1:
        tec1 = st.text_input("Técnico 1", "Ignacio Morales")
        act1 = st.text_input("Actividad Técnico 1", "M.OB.ST")
    with t2:
        tec2 = st.text_input("Técnico 2", "Emian Sanchez")
        act2 = st.text_input("Actividad Técnico 2", "M.OB.ST")

    st.subheader("3. Observaciones")
    obs_final = st.text_area("Estado final del equipo", "El equipo queda operativo y funcionando bajo parámetros normales de trabajo.")

    # Botón para procesar
    preparar = st.form_submit_button("1. GENERAR ESTRUCTURA")

# --- LÓGICA DE PROCESAMIENTO ---
if preparar:
    try:
        # Cargar la plantilla (Asegúrate de que el nombre sea exacto en GitHub)
        doc = DocxTemplate("InformeInspección.docx")
        
        # --- Lógica de Fecha en Español ---
        meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
        fecha_texto = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"

        # --- Lógica de Overhaul ---
        aviso_overhaul = ""
        if h_marcha > 40000:
            aviso_overhaul = "NOTA TÉCNICA: El equipo ha superado las 40.000 horas de operación. Se recomienda coordinar Overhaul para asegurar la disponibilidad del activo."

        # --- MAPEO DE DATOS PARA EL WORD ---
        contexto = {
            "fecha": fecha_texto,
            "cliente": cliente_nom,
            "cliente_contacto": contacto,
            "tipo_orden": tipo_servicio,
            "tag": tag_equipo,
            "serie": serie,
            "tecnico_1": tec1,
            "act_1": act1,
            "tecnico_2": tec2,
            "act_2": act2,
            "horas_totales_despues": f"{h_marcha} Hrs.",
            "horas_carga_despues": f"{h_carga} Hrs.",
            "actividades_ejecutadas": datos_manto[tipo_servicio],
            "estado_entrega": obs_final,
            "nota_overhaul": aviso_overhaul
        }
        
        # Inyectar datos en el Word
        doc.render(contexto)
        
        # Guardar en memoria para descarga
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        st.success("✅ ¡Informe procesado con éxito!")
        
        # --- BOTÓN DE DESCARGA FINAL ---
        st.download_button(
            label="📥 CLIC AQUÍ PARA DESCARGAR EL WORD",
            data=output,
            file_name=f"Informe_{tag_equipo}_{tipo_servicio}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        st.error(f"Error crítico: {e}. Asegúrese de que el archivo 'InformeInspección.docx' esté en GitHub.")
