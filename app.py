import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

# Configuración de la página
st.set_page_config(page_title="Atlas Copco Tracker", layout="wide")

# --- ARCHIVO DE BASE DE DATOS ---
DB_FILE = "historial_horas.csv"

# Cargar historial o crear uno nuevo si no existe
if os.path.exists(DB_FILE):
    df_historial = pd.read_csv(DB_FILE)
else:
    df_historial = pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico"])

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

st.title("🚀 Gestión de Compresores y Reportes")

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["Generar Informe", "Historial y Correcciones"])

with tab1:
    with st.form("editor_informe"):
        tag_sel = st.selectbox("Seleccione el TAG", list(equipos_db.keys()))
        modelo_aut, serie_aut, area_aut, clase_aut = equipos_db[tag_sel]
        
        # Buscar última hora registrada para este TAG
        ultimo_registro = df_historial[df_historial["TAG"] == tag_sel].tail(1)
        h_sugerida = int(ultimo_registro["Horas_Marcha"].values[0]) if not ultimo_registro.empty else 0
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_sel = st.date_input("Fecha", datetime.now())
            tipo_servicio = st.selectbox("Tipo de Mantención", ["INSPECCIÓN", "P1", "P2", "P3"])
            h_marcha_val = st.number_input("Horas Totales Marcha", value=h_sugerida)
        with col2:
            tec1 = st.text_input("Técnico Responsable", "Ignacio Morales")
            h_carga_val = st.number_input("Horas Carga", value=0)
            
        st.subheader("Personal y Tiempos")
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            act1 = st.text_input("Actividad Técnico 1", "M.OB.ST")
            h1 = st.text_input("Hora/Km T1", "8")
        with t_col2:
            tec2 = st.text_input("Técnico 2", "Emian Sanchez")
            h2 = st.text_input("Hora/Km T2", "8")

        alcance_manual = st.text_area("Alcance", f"Se realizó inspección a equipo compresor {modelo_aut} con identificación TAG {tag_sel} de {clase_aut} {area_aut}...")
        conclusiones_manual = st.text_area("Conclusiones", "El equipo se encuentra funcionando en óptimas condiciones...")

        enviar = st.form_submit_button("GUARDAR DATOS Y GENERAR WORD")

    if enviar:
        # Guardar en el DataFrame
        nuevo_dato = pd.DataFrame([[fecha_sel, tag_sel, h_marcha_val, h_carga_val, tec1]], columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico"])
        df_historial = pd.concat([df_historial, nuevo_dato], ignore_index=True)
        df_historial.to_csv(DB_FILE, index=False)
        
        # Generar Word (Lógica anterior)
        try:
            doc = DocxTemplate("InformeInspección.docx")
            meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
            fecha_texto = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"
            contexto = {
                "fecha": fecha_texto, "tag": tag_sel, "equipo_modelo": modelo_aut, "serie": serie_aut,
                "area": area_aut, "clase_area": clase_aut, "tipo_orden": tipo_servicio,
                "tecnico_1": tec1, "act_1": act1, "h_1": h1, "tecnico_2": tec2, "h_2": h2,
                "horas_marcha": f"{h_marcha_val} Hrs.", "horas_carga_despues": f"{h_carga_val} Hrs.",
                "alcanze_intervencion": alcance_manual, "estado_entrega": conclusiones_manual
            }
            doc.render(contexto)
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            st.success(f"✅ Datos guardados. El equipo {tag_sel} ahora tiene {h_marcha_val} hrs.")
            st.download_button("📥 DESCARGAR INFORME", bio, f"Reporte_{tag_sel}.docx")
        except Exception as e:
            st.error(f"Error: {e}")

with tab2:
    st.subheader("Registros Almacenados")
    st.dataframe(df_historial)
    
    if not df_historial.empty:
        st.subheader("⚠️ Corregir Registro")
        fila_a_borrar = st.number_input("Ingrese el número de fila a eliminar para corregir", min_value=0, max_value=len(df_historial)-1, step=1)
        if st.button("Eliminar fila seleccionada"):
            df_historial = df_historial.drop(df_historial.index[fila_a_borrar])
            df_historial.to_csv(DB_FILE, index=False)
            st.warning("Registro eliminado. Refresque la página.")
