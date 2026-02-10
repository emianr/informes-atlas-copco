import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Atlas Copco Reports", layout="wide")

st.title("Generador de Informes Atlas Copco")

# --- ENTRADA DE DATOS ---
with st.form("formulario_informe"):
    st.subheader("1. Identificación del Servicio")
    col1, col2 = st.columns(2)
    with col1:
        fecha_inf = st.date_input("Fecha del Informe", datetime.now())
        cliente_nombre = st.text_input("Cliente", "MINERA SPENCE S.A")
        duena_area = st.text_input("Dueña de Área", "Pamela Tápia")
        tipo_manto = st.selectbox("Tipo de Actividad", ["INSPECCIÓN", "P1", "P2", "P3"])
    
    with col2:
        equipo_mod = st.text_input("Equipo", "GA250")
        serie_num = st.text_input("Número de Serie", "AIF095301")
        tag_id = st.text_input("TAG", "35-GC-005")
        orden_tipo = st.text_input("Tipo de Orden", "INSPECCIÓN")

    st.subheader("2. Técnicos y Tiempos")
    t_col1, t_col2, t_col3 = st.columns(3)
    with t_col1:
        tec1 = st.text_input("Técnico 1", "Ignacio Morales")
    with t_col2:
        act1 = st.text_input("Actividad 1", "M.OB.ST")
    with t_col3:
        hrs1 = st.text_input("Hora/Km 1", "1 hora")

    st.subheader("3. Lecturas")
    l_col1, l_col2 = st.columns(2)
    with l_col1:
        h_marcha = st.number_input("Horas Totales de Marcha", value=65287)
    with l_col2:
        h_carga = st.number_input("Horas Carga", value=30550)

    # Botón dentro del formulario
    submit = st.form_submit_button("GENERAR DOCUMENTO")

# --- LÓGICA AL PRESIONAR EL BOTÓN ---
if submit:
    try:
        # Intenta cargar la plantilla
        doc = DocxTemplate("InformeInspección.docx")
        
        # Lógica de Overhaul automática basada en el informe
        # El equipo supera las 40.000 horas recomendadas para intervención mayor
        aviso_over = ""
        if h_marcha > 40000:
            aviso_over = "Nota técnica: El equipo supera las horas recomendadas para su intervención mayor (40.000 horas). Se recomienda enviar a overhaul o reemplazar equipo."

        # Mapeo de datos para el Word basándonos en tu informe
        contexto = {
            "fecha": fecha_inf.strftime("%d/%m/%Y"), # Fecha única para todo el doc
            "cliente": cliente_nombre,
            "cliente_contacto": duena_area,
            "tipo_orden": tipo_manto,
            "equipo_modelo": equipo_mod,
            "serie": serie_num,
            "tag": tag_id,
            "tecnico_1": tec1,
            "act_1": act1,
            "h_1": hrs1,
            "horas_totales_despues": f"{h_marcha} Hrs.",
            "horas_carga_despues": f"{h_carga} Hrs.",
            "nota_overhaul": aviso_over
        }

        doc.render(contexto)
        nombre_final = f"Reporte_{tag_id}.docx"
        doc.save(nombre_final)
        st.success(f"✅ ¡Informe creado con éxito! Se ha guardado como: {nombre_final}")
    
    except Exception as e:
        st.error(f"Error al generar: Asegúrate de que el archivo 'InformeInspección.docx' esté cerrado y en la misma carpeta que este script. Detalle: {e}")