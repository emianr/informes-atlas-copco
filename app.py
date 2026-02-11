import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io

# Configuración de la página
st.set_page_config(page_title="Atlas Copco App", layout="wide")

st.title("🚀 Generador Automatizado Atlas Copco")

# --- BASE DE DATOS DE EQUIPOS (Basada en tu imagen) ---
# Estructura: "TAG": ["Modelo", "Serie", "Área"]
equipos_db = {
    "70-GC-013": ["GA 132", "AIF095296", "Descarga acido"],
    "70-GC-014": ["GA 132", "AIF095297", "Descarga acido"],
    "050-GD-001": ["GA 45", "API542705", "PLANTA SX"],
    "050-GD-002": ["GA 45", "API542706", "PLANTA SX"],
    "050-GC-003": ["ZT 37", "API791692", "PLANTA SX"],
    "050-GC-004": ["ZT 37", "API791693", "PLANTA SX"],
    "050-GC-015": ["GA 30", "API501440", "PLANTA BORRA"],
    "65-GC-011": ["GA 250", "APF253581", "ÁREA HÚMEDA"],
    "65-GC-009": ["GA 250", "APF253608", "ÁREA HÚMEDA"],
    "35-GC-006": ["GA 250", "AIF095420", "SECA"],
    "35-GC-007": ["GA 250", "AIF095421", "SECA"],
    "35-GC-008": ["GA 250", "AIF095302", "SECA"],
    "20-GC-004": ["GA 37", "AII390776", "TRUCK SHOP"],
    "20-GC-001": ["GA 75", "AII482673", "TRUCK SHOP"],
    "20-GC-002": ["GA 75", "AII482674", "TRUCK SHOP"],
    "20-GC-003": ["GA 90", "AIF095178", "TRUCK SHOP"],
    "TALLER-01": ["GA 18", "API335343", "TALLER"] # Agregado por referencia
}

with st.form("editor_informe"):
    st.subheader("1. Selección de Equipo")
    
    # El usuario elige el TAG y lo demás se autocompleta internamente
    tag_sel = st.selectbox("Busque y seleccione el TAG del equipo", list(equipos_db.keys()))
    
    # Recuperamos los datos de la DB
    datos_equipo = equipos_db[tag_sel]
    modelo_aut = datos_equipo[0]
    serie_aut = datos_equipo[1]
    area_aut = datos_equipo[2]
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_sel = st.date_input("Fecha del Servicio", datetime.now())
        cliente_nom = st.text_input("Cliente", "MINERA SPENCE S.A")
        tipo_servicio = st.selectbox("Tipo de Servicio", ["INSPECCIÓN", "P1", "P2", "P3"])
    
    with col2:
        # Mostramos los datos automáticos (solo lectura para confirmar)
        st.info(f"**Modelo:** {modelo_aut} | **Serie:** {serie_aut} | **Área:** {area_aut}")
        tec1 = st.text_input("Técnico Responsable", "Ignacio Morales")
        h_marcha = st.number_input("Horas Totales Marcha", value=0)
        h_carga = st.number_input("Horas Carga", value=0)

    st.subheader("2. Textos del Informe")
    
    # Alcance automático generado con la nueva lógica
    alcance_final = f"Se realizó inspección a equipo compresor {modelo_aut} con identificación TAG {tag_sel} de {area_aut}."
    alcance_manual = st.text_area("Alcance de la Intervención", value=alcance_final)
    
    conclusiones_manual = st.text_area("Conclusiones y Recomendaciones", 
        value="El equipo queda operativo y funcionando bajo parámetros normales.")

    preparar = st.form_submit_button("GENERAR INFORME")

if preparar:
    try:
        doc = DocxTemplate("InformeInspección.docx")
        
        # Fecha en español
        meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
        fecha_texto = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"

        # Mapeo para el Word
        contexto = {
            "fecha": fecha_texto,
            "cliente": cliente_nom,
            "equipo_modelo": modelo_aut,
            "area": area_aut,
            "tag": tag_sel,
            "serie": serie_aut,
            "tipo_orden": tipo_servicio,
            "tecnico_1": tec1,
            "horas_totales_despues": f"{h_marcha} Hrs.",
            "horas_carga_despues": f"{h_carga} Hrs.",
            "alcanze_intervencion": alcance_manual,
            "estado_entrega": conclusiones_manual,
            "nota_overhaul": "" # Se envía vacío para eliminar la nota técnica
        }
        
        doc.render(contexto)
        
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        st.success(f"✅ ¡Informe para el TAG {tag_sel} generado!")
        
        st.download_button(
            label="📥 DESCARGAR WORD",
            data=output,
            file_name=f"Informe_{tag_sel}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        st.error(f"Error: {e}")
