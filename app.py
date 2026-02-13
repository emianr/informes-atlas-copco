import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

st.set_page_config(page_title="Atlas Copco Tracker - Spence", layout="wide")

# --- BASE DE DATOS LOCAL ---
DB_FILE = "historial_horas.csv"

def cargar_datos():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if not df.empty:
                df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
            return df
        except:
            return pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico", "Contacto"])
    else:
        return pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico", "Contacto"])

df_historial = cargar_datos()

# --- DICCIONARIO DE OPERACIONES ---
operaciones_dict = {
    "INSPECCIÓN": "Inspección visual de equipo",
    "P1": "Mantenimiento Preventivo P1 - Cambio de filtros y revisión general",
    "P2": "Mantenimiento Preventivo P2 - Cambio de kit de filtros y aceite",
    "P3": "Mantenimiento Preventivo P3 - Intervención mayor según pauta técnica"
}

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

st.title("🚀 Atlas Copco Tracker - Spence")

tab1, tab2 = st.tabs(["Generar Informe", "📊 Historial Editable"])

with tab1:
    # 1. Selección de TAG fuera del form para actualizar variables automáticamente
    tag_sel = st.selectbox("Seleccione el TAG", list(equipos_db.keys()))
    
    # Definición de variables del equipo para evitar el NameError
    modelo_aut, serie_aut, area_aut, clase_aut = equipos_db[tag_sel]
    
    # Buscar horas previas
    ultimo = df_historial[df_historial["TAG"] == tag_sel].tail(1)
    h_sug = int(ultimo["Horas_Marcha"].values[0]) if not ultimo.empty else 0

    # 2. Inicio del Formulario
    with st.form("formulario_principal"):
        c1, c2 = st.columns(2)
        with c1:
            fecha_sel = st.date_input("Fecha", datetime.now())
            cliente_cont = st.text_input("Contacto", "Pamela Tapia")
            tipo_servicio = st.selectbox("Tipo de Mantención", list(operaciones_dict.keys()))
        with c2:
            h_marcha_val = st.number_input("Horas Totales Marcha", value=h_sug)
            h_carga_val = st.number_input("Horas Carga", value=0)
            tec1_input = st.text_input("Técnico", "Ignacio Morales")

        st.subheader("📊 Parámetros Operacionales")
        p1, p2, p3 = st.columns(3)
        with p1: p_carga = st.text_input("Carga (bar)", "6.4")
        with p2: p_descarga = st.text_input("Descarga (bar)", "6.8")
        with p3: temp_sal = st.text_input("Temp (°C)", "80")

        # El alcance usa las variables definidas arriba
        alcance_val = f"Se realizó inspección a equipo compresor {modelo_aut} con identificación TAG {tag_sel} de {clase_aut}, {area_aut}, conforme a procedimientos internos y buenas prácticas de mantenimiento."
        alcance_manual = st.text_area("Alcance", value=alcance_val, height=80)
        
        concl_val = f"El equipo se encuentra funcionando en óptimas condiciones, bajo parámetros normales de funcionamiento (Carga: {p_carga} bar / Descarga: {p_descarga} bar, Temp: {temp_sal} °C), con nivel de aceite en rango."
        concl_manual = st.text_area("Condición Final", value=concl_val, height=80)

        # BOTÓN DE ENVÍO (Obligatorio dentro del form)
        enviar = st.form_submit_button("💾 GUARDAR E IMPRIMIR")

    if enviar:
        # Guardar datos en el CSV
        nuevo = pd.DataFrame([[fecha_sel, tag_sel, h_marcha_val, h_carga_val, tec1_input, cliente_cont]], 
                             columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico", "Contacto"])
        df_historial = pd.concat([df_historial, nuevo], ignore_index=True)
        df_historial.to_csv(DB_FILE, index=False)
        
        try:
            doc = DocxTemplate("InformeInspección.docx")
            meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
            fecha_txt = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"
            
            # Contexto para el Word
            contexto = {
                "fecha": fecha_txt, "cliente_contact": cliente_cont, "tag": tag_sel, "equipo_modelo": modelo_aut,
                "serie": serie_aut, "area": area_aut, "clase_area": clase_aut, "tipo_orden": tipo_servicio,
                "tecnico_1": tec1_input, "tecnico_2": "Emian Sanchez", "act_1": "M.OB.ST", "h_1": "8", "h_2": "8",
                "horas_marcha": f"{h_marcha_val} Hrs.", "horas_totales_despues": f"{h_marcha_val} Hrs.",
                "horas_carga_despues": f"{h_carga_val} Hrs.", "alcanze_intervencion": alcance_manual.strip(),
                "estado_entrega": concl_manual.strip(),
                "operaciones_dinamicas": operaciones_dict.get(tipo_servicio, "Inspección visual de equipo")
            }
            
            doc.render(contexto)
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            st.success("✅ Registro y Reporte generados correctamente.")
            st.download_button("📥 DESCARGAR REPORTE", bio, f"Reporte_{tag_sel}.docx")
        except Exception as e:
            st.error(f"Error al generar Word: {e}")

# --- PESTAÑA HISTORIAL ---
with tab2:
    st.subheader("📝 Gestión del Historial")
    df_fresco = cargar_datos()
    df_editado = st.data_editor(df_fresco, num_rows="dynamic", use_container_width=True, key="editor_v3")
    if st.button("💾 GUARDAR CAMBIOS EN EL HISTORIAL"):
        df_editado.to_csv(DB_FILE, index=False)
        st.success("Base de datos actualizada.")
        st.rerun()
