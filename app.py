import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Atlas Copco Tracker", layout="wide")
DB_FILE = "historial_horas.csv"

# --- BASE DE DATOS DE EQUIPOS ---
equipos_db = {
    "70-GC-013": ["GA 132", "AIF095296", "Descarga acido", "ÁREA HÚMEDA"],
    "70-GC-014": ["GA 132", "AIF095297", "Descarga acido", "ÁREA HÚMEDA"],
    "TALLER-01": ["GA18", "API335343", "TALLER", "ÁREA SECA"]
}

# --- TEXTOS DINÁMICOS (Lo que me pediste recopilar) ---
plantillas = {
    "INSPECCIÓN": {
        "actividades": "• Inspección de fugas: Revisión visual.\n• Verificación de lubricante: Chequeo por visor.\n• Revisión enfriador: Inspección visual.\n• Monitoreo de controlador: Prueba carga/descarga.\n• Purga condensado: Drenado realizado.",
        "condicion": "El equipo opera bajo parámetros estables, con alza de temperatura por saturación de enfriadores y alta humedad por lluvias.",
        "recomendaciones": "• Nota técnica: Equipo supera 40.000 horas. Se recomienda overhaul o reemplazo."
    },
    "P1": {
        "actividades": "• Cambio de filtros de aire y aceite.\n• Limpieza general del equipo.\n• Verificación de parámetros operativos.",
        "condicion": "Equipo funcionando bajo parámetros estables tras mantenimiento preventivo P1.",
        "recomendaciones": "• Mantener frecuencia de inspección según plan preventivo."
    },
    "P2": {
        "actividades": "• Cambio de aceite y kit de filtros.\n• Limpieza de enfriadores con aire comprimido.\n• Engrase de rodamientos de motor.",
        "condicion": "Equipo en óptimas condiciones tras servicio P2. Parámetros en rango ideal.",
        "recomendaciones": "• Considerar limpieza preventiva del entorno por alta contaminación."
    }
}

# --- INTERFAZ ---
st.title("🚀 Generador Automático de Reportes")

c1, c2 = st.columns(2)
with c1:
    tag_sel = st.selectbox("Seleccione TAG", list(equipos_db.keys()))
with c2:
    tipo_sel = st.selectbox("Tipo de Servicio", ["INSPECCIÓN", "P1", "P2"])

mod, ser, loc, are = equipos_db[tag_sel]
txt = plantillas[tipo_sel]

with st.form("form_final"):
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha", datetime.now())
        cliente = st.text_input("Contacto Cliente", "Pamela Tapia")
        tec1 = st.text_input("Técnico 1", "Ignacio Morales")
    with col2:
        h_m = st.number_input("Horas Marcha", value=0)
        h_c = st.number_input("Horas Carga", value=0)
        tec2 = st.text_input("Técnico 2", "Emian Sanchez")

    st.subheader("⚙️ Parámetros Operativos")
    p1, p2, p3 = st.columns(3)
    with p1: p_c = st.text_input("Presión Carga (bar)", "6.4")
    with p2: p_d = st.text_input("Presión Descarga (bar)", "6.8")
    with p3: t_s = st.text_input("Temp Salida (°C)", "80")

    # Campos de texto cargados automáticamente
    alcance = st.text_area("Alcance", value=f"Se realizó {tipo_sel.lower()} a equipo {mod} TAG {tag_sel} en {are}.")
    actividades = st.text_area("Actividades Ejecutadas", value=txt["actividades"], height=150)
    condicion = st.text_area("Condición Final", value=txt["condicion"])
    recom = st.text_area("Recomendaciones", value=txt["recomendaciones"])

    boton = st.form_submit_button("💾 GENERAR REPORTE")

if boton:
    try:
        doc = DocxTemplate("InformeInspección.docx")
        
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        fecha_es = f"{fecha.day} de {meses[fecha.month - 1]} de {fecha.year}"

        contexto = {
            "fecha": fecha_es,
            "cliente_contact": cliente,
            "alcanze_intervencion": alcance, # 
            "actividades_ejecutadas": actividades, # Debes agregar esto al Word
            "estado_entrega": condicion, # [cite: 17]
            "recomendaciones": recom, # Debes agregar esto al Word
            "p_carga": p_c, "p_descarga": p_d, "temp_salida": t_s, # [cite: 15]
            "tecnico_1": tec1, "tecnico_2": tec2, "act_1": "Mantenimiento", # 
            "h_1": "8", "h_2": "8",
            "equipo_modelo": mod, "serie": ser, "horas_marcha": f"{h_m} Hrs.", "tipo_orden": tipo_sel, # 
            "horas_totales_despues": h_m, "horas_carga_despues": h_c, # 
            "operaciones_dinamicas": actividades # [cite: 26]
        }
        
        doc.render(contexto)
        bio = io.BytesIO()
        doc.save(bio)
        st.success("✅ Reporte generado.")
        st.download_button("📥 Descargar", bio.getvalue(), f"Reporte_{tag_sel}.docx")
    except Exception as e:
        st.error(f"Error: {e}")
