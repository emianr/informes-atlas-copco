import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Atlas Copco Tracker - Spence", layout="wide")
DB_FILE = "historial_horas.csv"

# --- 2. BASE DE DATOS DE EQUIPOS ---
equipos_db = {
    "70-GC-013": ["GA 132", "AIF095296", "descarga acido", "área húmeda"],
    "70-GC-014": ["GA 132", "AIF095297", "descarga acido", "área húmeda"],
    "050-GD-001": ["GA 45", "API542705", "planta sx", "área húmeda"],
    "050-GD-002": ["GA 45", "API542706", "planta sx", "área húmeda"],
    "050-GC-003": ["ZT 37", "API791692", "planta sx", "área húmeda"],
    "050-GC-004": ["ZT 37", "API791693", "planta sx", "área húmeda"],
    "050-CD-001": ["CD 80+", "API095825", "planta sx", "área húmeda"],
    "050-GC-015": ["GA 30", "API501440", "planta borra", "área húmeda"],
    "65-GC-011": ["GA 250", "APF253581", "patio estanques", "área húmeda"],
    "TALLER-01": ["GA18", "API335343", "taller", "área seca"]
}

# --- 3. PLANTILLAS DE TEXTO AUTOMÁTICO ---
plantillas_servicios = {
    "INSPECCIÓN": {
        "actividades": "• Inspección de fugas: Revisión visual.\n• Verificación de lubricante: Chequeo por visor.\n• Revisión enfriador: Inspección visual.\n• Monitoreo de controlador: Prueba carga/descarga.",
        "condicion": "El equipo opera bajo parámetros estables, con alza de temperatura por saturación de enfriadores y humedad por lluvias.",
        "recomendaciones": "• Nota técnica: Equipo supera 40.000 horas. Se recomienda overhaul."
    },
    "P1": {
        "actividades": "• Cambio de filtros de aire.\n• Limpieza general.\n• Verificación de parámetros operativos.",
        "condicion": "Equipo funcionando bajo parámetros estables tras mantenimiento P1.",
        "recomendaciones": "• Seguir plan de mantenimiento preventivo vigente."
    },
    "P2": {
        "actividades": "• Cambio de aceite y filtros.\n• Limpieza de radiadores.\n• Engrase de componentes.",
        "condicion": "Equipo en óptimas condiciones tras servicio P2.",
        "recomendaciones": "• Mantener limpieza del entorno para evitar saturación de enfriadores."
    }
}

# --- 4. INTERFAZ ---
st.title("🚀 Atlas Copco Tracker - Spence")

# Selectores principales fuera del form para actualizar todo al instante
tag_sel = st.selectbox("Seleccione el TAG del equipo", list(equipos_db.keys()))
tipo_mant = st.selectbox("Tipo de Mantención", ["INSPECCIÓN", "P1", "P2"])

# Obtener datos del equipo y plantilla
mod_aut, ser_aut, loc_aut, area_aut = equipos_db[tag_sel]
txt_auto = plantillas_servicios[tipo_mant]

with st.form("editor_informe"):
    c1, c2 = st.columns(2)
    with c1:
        fecha_sel = st.date_input("Fecha de atención", datetime.now())
        cliente_cont = st.text_input("Contacto Cliente", "Pamela Tapia")
        tec1 = st.text_input("Técnico 1 (Líder)", "Ignacio Morales")
    with c2:
        h_marcha = st.number_input("Horas Totales Marcha", value=0)
        h_carga = st.number_input("Horas Carga", value=0)
        tec2 = st.text_input("Técnico 2", "Emian Sanchez")

    st.subheader("⚙️ Parámetros Operacionales")
    p1, p2, p3 = st.columns(3)
    with p1: p_carga_val = st.text_input("Presión de Carga (bar)", "6.4")
    with p2: p_desc_val = st.text_input("Presión de Descarga (bar)", "6.8")
    with p3: t_sal_val = st.text_input("Temperatura (°C)", "80")

    # Textos que se llenan solos pero puedes editar
    alcance_val = f"Se realizó {tipo_mant.lower()} a equipo compresor {mod_aut} TAG {tag_sel} de {area_aut}, {loc_aut}."
    alcance_manual = st.text_area("Alcance del Trabajo", value=alcance_val)
    
    # Esta variable irá a {{ operaciones_dinamicas }}
    ops_manual = st.text_area("Actividades Realizadas", value=txt_auto["actividades"], height=150)
    
    # Esta variable irá a {{ estado_entrega }}
    cond_manual = st.text_area("Condición Final", value=txt_auto["condicion"])

    generar = st.form_submit_button("💾 GUARDAR Y GENERAR REPORTE")

if generar:
    try:
        doc = DocxTemplate("InformeInspección.docx")
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        fecha_txt = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"

        # MAPEO ESTRICTO CON LAS ETIQUETAS DEL WORD 
        contexto = {
            "fecha": fecha_txt,
            "cliente_contact": cliente_cont,
            "alcanze_intervencion": alcance_manual, # Sincronizado con {{ alcanze_intervencion }} 
            "p_carga": p_carga_val,              # Sincronizado con {{ p_carga }} 
            "p_descarga": p_desc_val,            # Sincronizado con {{ p_descarga }} 
            "temp_salida": t_sal_val,            # Sincronizado con {{ temp_salida }} 
            "estado_entrega": cond_manual,       # Sincronizado con {{ estado_entrega }} [cite: 17]
            "tecnico_1": tec1,                   # Sincronizado con {{ tecnico_1 }} 
            "tecnico_2": tec2,                   # Sincronizado con {{ tecnico_2 }} 
            "act_1": "Mantenimiento",            # Sincronizado con {{ act_1 }} 
            "h_1": "8", "h_2": "8",              # Horas por técnico 
            "equipo_modelo": mod_aut,            # Sincronizado con {{ equipo_modelo }} 
            "serie": ser_aut,                    # Sincronizado con {{ serie }} 
            "horas_marcha": f"{h_marcha} Hrs",   # Sincronizado con {{ horas_marcha }} 
            "tipo_orden": tipo_mant,             # Sincronizado con {{ tipo_orden }} 
            "horas_totales_despues": h_marcha,   # Sincronizado con {{ horas_totales_despues }} 
            "horas_carga_despues": h_carga,      # Sincronizado con {{ horas_carga_despues }} 
            "operaciones_dinamicas": ops_manual, # Sincronizado con {{ operaciones_dinamicas }} [cite: 26]
            "tag": tag_sel                       # Etiqueta {{ tag }} 
        }

        doc.render(contexto)
        output = io.BytesIO()
        doc.save(output)
        st.success("✅ Reporte generado exitosamente.")
        st.download_button("📥 DESCARGAR REPORTE", output.getvalue(), f"Informe_{tag_sel}.docx")
    except Exception as e:
        st.error(f"❌ Error al procesar el Word: {e}")
