import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io

# Configuración de la página
st.set_page_config(page_title="Atlas Copco App", layout="wide")

st.title("🚀 Sistema de Informes Automatizado")

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

with st.form("editor_informe"):
    st.subheader("1. Selección de Equipo")
    tag_sel = st.selectbox("Seleccione el TAG del compresor", list(equipos_db.keys()))
    modelo_aut, serie_aut, area_aut, clase_aut = equipos_db[tag_sel]
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_sel = st.date_input("Fecha", datetime.now())
        cliente_nom = st.text_input("Cliente", "MINERA SPENCE S.A")
        tipo_servicio = st.selectbox("Tipo de Mantención", ["INSPECCIÓN", "P1", "P2", "P3"])
    with col2:
        st.info(f"📍 Localización: {clase_aut} ({area_aut})")
        h_marcha_val = st.number_input("Horas Totales Marcha", value=0)
        h_carga_val = st.number_input("Horas Carga", value=0)

    st.subheader("2. Confirmación de Tiempos (Personal)")
    t1, t2 = st.columns(2)
    with t1:
        tec1 = st.text_input("Técnico 1", "Ignacio Morales")
        act1 = st.text_input("Actividad 1", "M.OB.ST")
        h1 = st.text_input("Hora/Km 1", "8")
    with t2:
        tec2 = st.text_input("Técnico 2", "Emian Sanchez")
        act2 = st.text_input("Actividad 2", "M.OB.ST")
        h2 = st.text_input("Hora/Km 2", "8")

    st.subheader("3. Textos del Informe")
    alcance_final = f"Se realizó inspección a equipo compresor {modelo_aut} con identificación TAG {tag_sel} de {clase_aut} {area_aut}, conforme a procedimientos internos y buenas prácticas de mantenimiento."
    alcance_manual = st.text_area("Alcance de la Intervención", value=alcance_final, height=100)
    
    texto_conclusiones_default = "El equipo se encuentra funcionando en óptimas condiciones, bajo parámetros normales de funcionamiento, con nivel de aceite dentro del rango establecido, sin fugas en circuitos de aire/aceite y con filtros sin saturación."
    conclusiones_manual = st.text_area("Conclusiones y Estado de Entrega", value=texto_conclusiones_default, height=150)

    generar = st.form_submit_button("GENERAR WORD")

if generar:
    try:
        doc = DocxTemplate("InformeInspección.docx")
        meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
        fecha_texto = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"

        contexto = {
            "fecha": fecha_texto,
            "cliente": cliente_nom,
            "equipo_modelo": modelo_aut,
            "area": area_aut,
            "clase_area": clase_aut,
            "tag": tag_sel,
            "serie": serie_aut,
            "tipo_orden": tipo_servicio,
            # Etiquetas para la tabla de tiempos
            "tecnico_1": tec1, "act_1": act1, "h_1": h1,
            "tecnico_2": tec2, "act_2": act2, "h_2": h2,
            # Lecturas
            "horas_marcha": f"{h_marcha_val} Hrs.",
            "horas_carga_despues": f"{h_carga_val} Hrs.",
            "alcanze_intervencion": alcance_manual,
            "estado_entrega": conclusiones_manual
        }
        
        doc.render(contexto)
        bio = io.BytesIO()
        doc.save(bio)
        bio.seek(0)
        
        st.download_button(
            label="📥 DESCARGAR INFORME LISTO",
            data=bio,
            file_name=f"Reporte_{tag_sel}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        st.error(f"Error: {e}")
