import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io

# Configuración de la página
st.set_page_config(page_title="Atlas Copco App", layout="wide")

st.title("🚀 Sistema de Informes Automatizado")

# --- BASE DE DATOS ACTUALIZADA CON CLASIFICACIÓN (Seca, Humeda, Mina) ---
# Formato: "TAG": ["Modelo", "Serie", "Área Específica", "Clasificación"]
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
    st.subheader("Selección de Equipo y Datos")
    
    # Menú para elegir el TAG
    tag_sel = st.selectbox("Seleccione el TAG del compresor", list(equipos_db.keys()))
    
    # Obtener datos automáticos
    modelo_aut, serie_aut, area_aut, clase_aut = equipos_db[tag_sel]
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_sel = st.date_input("Fecha", datetime.now())
        cliente_nom = st.text_input("Cliente", "MINERA SPENCE S.A")
        tipo_servicio = st.selectbox("Tipo de Mantención", ["INSPECCIÓN", "P1", "P2", "P3"])
    
    with col2:
        st.success(f"📌 **Localización:** {clase_aut} ({area_aut})")
        tec1 = st.text_input("Técnico", "Ignacio Morales")
        h_marcha = st.number_input("Horas Marcha", value=0)
        h_carga = st.number_input("Horas Carga", value=0)

    st.subheader("Textos del Informe (Se editan solos)")
    # El Alcance ahora incluye la clasificación automática (Húmeda, Seca o Mina)
    alcance_final = f"Se realizó inspección a equipo compresor {modelo_aut} con identificación TAG {tag_sel} de {clase_aut} {area_aut}, conforme a procedimientos internos y buenas prácticas de mantenimiento."
    alcance_manual = st.text_area("Alcance de la Intervención", value=alcance_final, height=100)
    
    conclusiones_manual = st.text_area("Conclusiones", value="El equipo queda operativo y funcionando bajo parámetros normales.")

    generar = st.form_submit_button("GENERAR WORD")

if generar:
    try:
        doc = DocxTemplate("InformeInspección.docx")
        
        # Fecha en español
        meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
        fecha_texto = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"

        contexto = {
            "fecha": fecha_texto,
            "cliente": cliente_nom,
            "equipo_modelo": modelo_aut,
            "area": area_aut,
            "clase_area": clase_aut, # Nueva etiqueta para Humeda/Seca/Mina
            "tag": tag_sel,
            "serie": serie_aut,
            "tipo_orden": tipo_servicio,
            "tecnico_1": tec1,
            "horas_totales_despues": f"{h_marcha} Hrs.",
            "horas_carga_despues": f"{h_carga} Hrs.",
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
