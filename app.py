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
    "35-GC-006": ["GA 250", "AIF095420", "chancado secundario", "área seca"],
    "35-GC-007": ["GA 250", "AIF095421", "chancado secundario", "área seca"],
    "35-GC-008": ["GA 250", "AIF095302", "chancado secundario", "área seca"],
    "TALLER-01": ["GA18", "API335343", "taller", "área seca"]
}

# --- 3. PLANTILLAS DINÁMICAS (TEXTOS QUE ME PASASTE) ---
def obtener_plantilla(tipo, tag, mod, loc, area):
    if tipo == "INSPECCIÓN":
        return {
            "alcance": f"Se realizó inspección a equipo compresor {mod} con identificación TAG {tag} de {area}, {loc}, conforme a procedimientos internos y buenas prácticas de mantenimiento.",
            "actividades": "• Inspección de fugas: Revisión visual de circuitos de aire/aceite.\n• Verificación de lubricante: Chequeo por visor de separador si está dentro del rango establecido.\n• Revisión enfriador: Inspección visual en enfriador de aire/aceite.\n• Monitoreo de controlador: Validación de funcionamiento de controlador, realizando prueba en carga/descarga del equipo.\n• Estado operacional: Verificación de parámetros operativos.\n• Purga condensado: Drenado de condensado del equipo.",
            "condicion": "El equipo se encuentra funcionando bajo parámetros estables, a excepción de temperatura de trabajo con un alza considerable, con nivel de aceite dentro del rango establecido y con filtros sin saturación.\nSe observa alta saturación por contaminación en enfriadores y fuga de aceite en enfriador de aceite, causando derrame exterior en enfriador de aire y a su vez generando alza de temperatura del elemento compresor.\nSe encuentran flexibles y sensores con exceso de corrosión, lo cual puede provocar una detención no deseada en cualquier momento.\nLa lluvia elevó la humedad relativa y el punto de rocío, provocando una acumulación excesiva de condensado en el interior del equipo, drenando todo el acumulado.",
            "recomendaciones": "• Nota técnica: El equipo supera las horas recomendadas para su intervención mayor (40.000 horas). Se recomienda enviar a overhaul o reemplazar de equipo.\n• Mantenimiento correctivo: Programar reparación de la fuga detectada en los enfriadores de aceite o el cambio en su totalidad.",
            "p_c": "6.2", "p_d": "6.7", "t_s": "86"
        }
    elif tipo == "P1":
        return {
            "alcance": f"Se realizó mantención a equipo compresor {mod} con identificación TAG {tag} de {area}, {loc}, conforme a procedimientos internos y buenas prácticas de mantenimiento.",
            "actividades": "• Inspección de fugas: Revisión visual de circuitos de aire/aceite.\n• Limpieza general: Limpieza general de equipo compresor.\n• Verificación de lubricante: Revisión por visor de nivel óptimo.\n• Chequeo enfriador: Inspección visual en enfriador de aire/aceite.\n• Cambio filtros: Cambio de filtros de aire/aceite.\n• Monitoreo de controlador: Validación de parámetros de operación, realizando prueba en carga/descarga del equipo.",
            "condicion": "El equipo se encuentra funcionando bajo parámetros estables, nivel de aceite dentro del rango establecido y con filtros sin saturación.\nSe detecta enfriadores saturados por contaminación, pero sin fugas visibles.\nSe encuentran flexibles y sensores con exceso de corrosión.",
            "recomendaciones": "• Plan de mantenimiento: Mantener frecuencia de inspección y drenado de condensados según plan preventivo vigente.\n• Control ambiental: Considerar limpieza preventiva del entorno y radiadores debido a la alta contaminación del sector.",
            "p_c": "7.6", "p_d": "7.0", "t_s": "70"
        }
    else: # P2
        return {
            "alcance": f"Se realizó mantención a equipo compresor {mod} con identificación TAG {tag} de {area}, {loc}, conforme a procedimientos internos y buenas prácticas de mantenimiento.",
            "actividades": "• Inspección de fugas: Revisión visual de circuitos de aire/aceite.\n• Limpieza general: Limpieza general de equipo compresor.\n• Cambio de lubricante: Se realiza drenado con cambio de aceite y revisión por visor.\n• Chequeo enfriador: Inspección visual en enfriador de aire/aceite.\n• Cambio filtros: Cambio de filtros de aire/aceite.\n• Monitoreo de controlador: Validación de parámetros de operación.",
            "condicion": "El equipo se encuentra funcionando bajo parámetros estables, nivel de aceite dentro del rango establecido y con filtros sin saturación.\nSe detecta enfriadores saturados por contaminación, pero sin fugas visibles.",
            "recomendaciones": "• Plan de mantenimiento: Mantener frecuencia de inspección y drenado de condensados.\n• Control ambiental: Considerar limpieza preventiva del entorno y radiadores.",
            "p_c": "7.6", "p_d": "7.0", "t_s": "70"
        }

# --- 4. INTERFAZ ---
st.title("🚀 Atlas Copco Tracker - Spence")

tag_sel = st.selectbox("Seleccione el Equipo (TAG)", list(equipos_db.keys()))
tipo_sel = st.selectbox("Tipo de Trabajo", ["INSPECCIÓN", "P1", "P2"])

mod, ser, loc, area = equipos_db[tag_sel]
datos_p = obtener_plantilla(tipo_sel, tag_sel, mod, loc, area)

with st.form("main_form"):
    c1, c2 = st.columns(2)
    with c1:
        fecha = st.date_input("Fecha", datetime.now())
        cliente = st.text_input("Contacto Cliente", "Pamela Tapia")
        tec1 = st.text_input("Técnico 1", "Ignacio Morales")
    with c2:
        h_m = st.number_input("Horas Marcha", value=0)
        h_c = st.number_input("Horas Carga", value=0)
        tec2 = st.text_input("Técnico 2", "Emian Sanchez")

    st.subheader("⚙️ Parámetros")
    p1, p2, p3 = st.columns(3)
    with p1: pc = st.text_input("Presión Carga", datos_p["p_c"])
    with p2: pd = st.text_input("Presión Descarga", datos_p["p_d"])
    with p3: ts = st.text_input("Temp Salida", datos_p["t_s"])

    alcance = st.text_area("Alcance", value=datos_p["alcance"])
    actividades = st.text_area("Actividades Ejecutadas", value=datos_p["actividades"], height=150)
    condicion = st.text_area("Condición Final", value=datos_p["condicion"])
    recom = st.text_area("Recomendaciones", value=datos_p["recomendaciones"])

    generar = st.form_submit_button("GENERAR REPORTE")

if generar:
    try:
        doc = DocxTemplate("InformeInspección.docx")
        contexto = {
            "fecha": fecha.strftime("%d/%m/%Y"),
            "cliente_contact": cliente,
            "alcanze_intervencion": alcance,
            "operaciones_dinamicas": actividades, # REEMPLAZA TEXTO FIJO
            "estado_entrega": condicion,
            "recomendaciones": recom,           # REEMPLAZA TEXTO FIJO
            "p_carga": pc, "p_descarga": pd, "temp_salida": ts,
            "tecnico_1": tec1, "tecnico_2": tec2, "act_1": "Mantenimiento",
            "h_1": "8", "h_2": "8",
            "equipo_modelo": mod, "serie": ser, "horas_marcha": f"{h_m} Hrs.",
            "tipo_orden": tipo_sel, "tag": tag_sel,
            "horas_totales_despues": h_m, "horas_carga_despues": h_c
        }
        doc.render(contexto)
        bio = io.BytesIO()
        doc.save(bio)
        st.success("✅ Reporte generado correctamente")
        st.download_button("📥 Descargar Word", bio.getvalue(), f"Reporte_{tag_sel}.docx")
    except Exception as e:
        st.error(f"Error: {e}")
