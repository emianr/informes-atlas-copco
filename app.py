iimport streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

st.set_page_config(page_title="Atlas Copco Tracker", layout="wide")

# --- BASE DE DATOS LOCAL ---
DB_FILE = "historial_horas.csv"
if os.path.exists(DB_FILE):
    df_historial = pd.read_csv(DB_FILE)
else:
    df_historial = pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico", "Contacto"])

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

st.title("🚀 Gestión de Compresores")

tab1, tab2 = st.tabs(["Generar Informe", "Historial"])

with tab1:
    with st.form("editor_informe"):
        tag_sel = st.selectbox("Seleccione el TAG", list(equipos_db.keys()))
        modelo_aut, serie_aut, area_aut, clase_aut = equipos_db[tag_sel]
        
        ultimo_registro = df_historial[df_historial["TAG"] == tag_sel].tail(1)
        h_sugerida = int(ultimo_registro["Horas_Marcha"].values[0]) if not ultimo_registro.empty else 0
        
        c1, c2 = st.columns(2)
        with c1:
            fecha_sel = st.date_input("Fecha", datetime.now())
            cliente_cont = st.text_input("Contacto / Dueño de Área", "Pamela Tapia")
            tipo_servicio = st.selectbox("Tipo de Mantención", ["INSPECCIÓN", "P1", "P2", "P3"])
        with c2:
            h_marcha_val = st.number_input("Horas Totales Marcha", value=h_sugerida)
            h_carga_val = st.number_input("Horas Carga", value=0)
            tec1_input = st.text_input("Técnico Responsable", "Ignacio Morales")

        st.subheader("📊 Parámetros Operacionales")
        p1, p2, p3 = st.columns(3)
        with p1: p_carga = st.text_input("Carga (bar)", "6.4")
        with p2: p_descarga = st.text_input("Descarga (bar)", "6.8")
        with p3: temp_sal = st.text_input("Temp (°C)", "80")
            
        t1, t2 = st.columns(2)
        with t1:
            tec2_input = st.text_input("Técnico 2", "Emian Sanchez")
            act1 = st.text_input("Actividad", "M.OB.ST")
        with t2:
            h1 = st.text_input("Hrs T1", "8")
            h2 = st.text_input("Hrs T2", "8")

        # --- TEXTO DE ALCANCE ACTUALIZADO SEGÚN TU SOLICITUD ---
        # Se eliminan espacios en blanco extras y se usa la nueva estructura
        alcance_val = f"Se realizó inspección a equipo compresor {modelo_aut} con identificación TAG {tag_sel} de {clase_aut}, {area_aut}, conforme a procedimientos internos y buenas prácticas de mantenimiento."
        
        alcance_manual = st.text_area("Alcance de la Intervención", value=alcance_val, height=80)
        
        concl_val = f"El equipo se encuentra funcionando en óptimas condiciones, bajo parámetros normales de funcionamiento (Presión carga: {p_carga} bar / descarga: {p_descarga} bar, Temp: {temp_sal} °C), con nivel de aceite dentro del rango establecido, sin fugas en circuitos de aire/aceite y con filtros sin saturación."
        conclusiones_manual = st.text_area("Condición Final", value=concl_val, height=100)

        enviar = st.form_submit_button("GENERAR INFORME WORD")

    if enviar:
        nuevo = pd.DataFrame([[fecha_sel, tag_sel, h_marcha_val, h_carga_val, tec1_input, cliente_cont]], 
                             columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico", "Contacto"])
        df_historial = pd.concat([df_historial, nuevo], ignore_index=True)
        df_historial.to_csv(DB_FILE, index=False)
        
        try:
            doc = DocxTemplate("InformeInspección.docx")
            meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
            fecha_txt = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"
            
            contexto = {
                "fecha": fecha_txt,
                "cliente": "MINERA SPENCE S.A",
                "cliente_contact": cliente_cont,
                "tag": tag_sel,
                "equipo_modelo": modelo_aut,
                "serie": serie_aut,
                "area": area_aut,
                "clase_area": clase_aut,
                "tipo_orden": tipo_servicio,
                "tecnico_1": tec1_input, "act_1": act1, "h_1": h1,
                "tecnico_2": tec2_input, "h_2": h2,
                "horas_marcha": f"{h_marcha_val} Hrs.",
                "horas_totales_despues": f"{h_marcha_val} Hrs.",
                "horas_carga_despues": f"{h_carga_val} Hrs.",
                "alcanze_intervencion": alcance_manual.strip(),
                "estado_entrega": conclusiones_manual.strip()
            }
            
            doc.render(contexto)
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            st.success(f"✅ Informe de {tag_sel} generado correctamente.")
            st.download_button("📥 DESCARGAR REPORTE", bio, f"Reporte_{tag_sel}.docx")
        except Exception as e:
            st.error(f"Error técnico: {e}")

with tab2:
    st.subheader("Historial de Inspecciones")
    st.dataframe(df_historial)
