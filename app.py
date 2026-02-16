import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Atlas Copco Tracker - Spence", layout="wide")

# --- 2. BASE DE DATOS DE EQUIPOS (DICCIONARIO CENTRAL) ---
# Aquí se guarda la información técnica de cada TAG.
equipos_db = {
    "70-GC-013": ["GA 132", "AIF095296", "descarga acido", "área húmeda"],
    "70-GC-014": ["GA 132", "AIF095297", "descarga acido", "área húmeda"],
    "050-GD-001": ["GA 45", "API542705", "planta sx", "área húmeda"],
    "050-GD-002": ["GA 45", "API542706", "planta sx", "área húmeda"],
    "050-GC-003": ["ZT 37", "API791692", "planta sx", "área húmeda"],
    "050-GC-004": ["ZT 37", "API791693", "planta sx", "área húmeda"],
    "050-CD-001": ["CD 80+", "API095825", "planta sx", "área húmeda"],
    "050-CD-002": ["CD 80+", "API095826", "planta sx", "área húmeda"],
    "050-GC-015": ["GA 30", "API501440", "planta borra", "área húmeda"],
    "65-GC-011": ["GA 250", "APF253581", "patio estanques", "área húmeda"],
    "65-GC-009": ["GA 250", "APF253608", "patio estanques", "área húmeda"],
    "65-GD-011": ["CD 630", "WXF300015", "patio estanques", "área húmeda"], 
    "65-GD-012": ["CD 630", "WXF300016", "patio estanques", "área húmeda"],  
    "35-GC-006": ["GA 250", "AIF095420", "chancado secundario", "área seca"],
    "35-GC-007": ["GA 250", "AIF095421", "chancado secundario", "área seca"],
    "35-GC-008": ["GA 250", "AIF095302", "chancado secundario", "área seca"],
    "20-GC-004": ["GA 37", "AII390776", "mina", "mina"],
    "20-GC-001": ["GA 75", "AII482673", "truck shop", "mina"],
    "20-GC-002": ["GA 75", "AII482674", "truck shop", "mina"],
    "20-GC-003": ["GA 90", "AIF095178", "truck shop", "mina"],
    "TALLER-01": ["GA18", "API335343", "taller", "área seca"]
}

# --- 3. CEREBRO DE TEXTOS DINÁMICOS ---
# Estos textos cargan automáticamente según el tipo de mantenimiento seleccionado.
plantillas_mantenimiento = {
    "INSPECCIÓN": {
        "actividades": "• Inspección de fugas: Revisión visual de circuitos de aire/aceite.\n• Verificación de lubricante: Chequeo por visor de nivel.\n• Revisión enfriador: Inspección visual en enfriador de aire/aceite.\n• Monitoreo de controlador: Validación de carga/descarga.\n• Purga condensado: Drenado de condensado acumulado.",
        "condicion": "El equipo opera bajo parámetros estables, excepto temperatura con alza considerable. Se observa saturación en enfriadores y fuga en enfriador de aceite. Flexibles y sensores con exceso de corrosión. La lluvia elevó la humedad acumulando condensado excesivo.",
        "recomendaciones": "• Nota técnica: El equipo supera las 40.000 horas. Se recomienda overhaul o reemplazo.\n• Mantenimiento correctivo: Programar reparación de fuga en enfriadores para evitar alzas de temperatura fuera de lo normal."
    },
    "P1": {
        "actividades": "• Inspección de fugas: Revisión visual de circuitos.\n• Limpieza general: Limpieza de equipo compresor.\n• Verificación de lubricante: Revisión por visor de nivel óptimo.\n• Chequeo enfriador: Inspección visual.\n• Cambio filtros: Cambio de filtros de aire/aceite.\n• Monitoreo de controlador: Prueba de carga/descarga.",
        "condicion": "El equipo se encuentra funcionando bajo parámetros estables, nivel de aceite en rango y filtros sin saturación. Se detectan enfriadores saturados por contaminación ambiental pero sin fugas visibles.",
        "recomendaciones": "• Plan de mantenimiento: Mantener frecuencia de inspección y drenado según plan preventivo.\n• Control ambiental: Considerar limpieza preventiva del entorno y radiadores debido a la alta contaminación."
    },
    "P2": {
        "actividades": "• Inspección de fugas: Revisión visual.\n• Limpieza general: Limpieza de equipo compresor.\n• Cambio de lubricante: Se realiza drenado con cambio de aceite completo.\n• Chequeo enfriador: Inspección visual.\n• Cambio filtros: Cambio de filtros de aire/aceite.\n• Monitoreo de controlador: Validación de parámetros operativos.",
        "condicion": "Equipo funcionando bajo parámetros estables, lubricante nuevo y filtros sin saturación. Enfriadores saturados por contaminación pero sin fugas. Flexibles presentan corrosión superficial.",
        "recomendaciones": "• Plan de mantenimiento: Continuar con plan preventivo vigente.\n• Control ambiental: Realizar limpieza de radiadores para prolongar la vida útil de los componentes nuevos."
    }
}

# --- 4. GESTIÓN DEL HISTORIAL (CSV) ---
DB_FILE = "historial_horas.csv"
def cargar_datos():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        return df
    return pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])

df_historial = cargar_datos()

# --- 5. INTERFAZ DE USUARIO ---
st.title("🚀 Atlas Copco Tracker - Spence")
tab1, tab2 = st.tabs(["📋 Generar Informe", "⚙️ Administrar Historial"])

with tab1:
    # SELECCIÓN SUPERIOR (Fuera del form para actualizar textos automáticamente)
    c_top1, c_top2 = st.columns(2)
    with c_top1:
        tag_sel = st.selectbox("Seleccione el TAG del Equipo", list(equipos_db.keys()))
    with c_top2:
        tipo_m_sel = st.selectbox("Tipo de Intervención", ["INSPECCIÓN", "P1", "P2"])

    # Extraer datos automáticos según la selección
    mod, ser, loc, are = equipos_db[tag_sel]
    textos_base = plantillas_mantenimiento[tipo_m_sel]

    # FORMULARIO DE RELLENO
    with st.form("form_inteligente"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_sel = st.date_input("Fecha", datetime.now())
            cliente = st.text_input("Contacto Cliente", "Pamela Tapia")
        with col2:
            h_m = st.number_input("Horas Totales Marcha", value=0)
            tec1 = st.text_input("Técnico 1", "Ignacio Morales")
            tec2 = st.text_input("Técnico 2", "Emian Sanchez")

        st.subheader("📊 Parámetros Técnicos")
        p1, p2, p3, p4 = st.columns(4)
        with p1: p_c = st.text_input("Presión de Carga", "6.4")
        with p2: p_u = st.selectbox("Unidad", ["bar", "psi"])
        with p3: t_s = st.text_input("Temperatura Salida", "80")
        with p4: t_u = st.selectbox("Unidad", ["°C", "°F"])

        st.subheader("📝 Contenido del Reporte (Auto-completado)")
        # El alcance se arma solo usando el TAG y Área
        alcance = st.text_area("Alcance", value=f"Se realizó {tipo_m_sel.lower()} a equipo compresor {mod} TAG {tag_sel} de {are}, {loc}, conforme a procedimientos internos.")
        actividades = st.text_area("Actividades Ejecutadas", value=textos_base["actividades"], height=150)
        condicion = st.text_area("Condición Final y Entrega", value=textos_base["condicion"], height=100)
        recomendaciones = st.text_area("Recomendaciones", value=textos_base["recomendaciones"], height=100)

        enviar = st.form_submit_button("💾 GUARDAR Y GENERAR REPORTE WORD")

    if enviar:
        # Guardar en base de datos
        nuevo = pd.DataFrame([[fecha_sel, tag_sel, h_m, 0, tec1, tec2, cliente]], 
                             columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])
        pd.concat([df_historial, nuevo]).to_csv(DB_FILE, index=False)
        
        try:
            doc = DocxTemplate("InformeInspección.docx")
            # FECHA EN ESPAÑOL
            meses_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            fecha_final = f"{fecha_sel.day} de {meses_es[fecha_sel.month - 1]} de {fecha_sel.year}"

            # MAPEO DE ETIQUETAS DEL WORD
            contexto = {
                "fecha": fecha_final, "cliente_contact": cliente, "tag": tag_sel, "equipo_modelo": mod,
                "serie": ser, "area": are, "clase_area": loc, "tipo_orden": tipo_m_sel,
                "tecnico_1": tec1, "tecnico_2": tec2, "horas_marcha": f"{h_m} Hrs.",
                "p_unidad": p_u, "t_unidad": t_u,
                "alcance": alcance, "actividades_ejecutadas": actividades,
                "estado_entrega": condicion, "recomendaciones": recomendaciones
            }
            doc.render(contexto)
            bio = io.BytesIO()
            doc.save(bio)
            st.success(f"✅ ¡Reporte de {tag_sel} generado!")
            st.download_button("📥 DESCARGAR REPORTE", bio.getvalue(), f"Reporte_{tag_sel}_{tipo_m_sel}.docx")
        except Exception as e:
            st.error(f"Error técnico: {e}")

# --- 6. PESTAÑA DE ADMINISTRACIÓN ---
with tab2:
    st.subheader("🛠️ Administrar Historial (CSV)")
    df_f = cargar_datos()
    # El editor permite borrar filas o corregir errores de dedo
    df_ed = st.data_editor(df_f, num_rows="dynamic", use_container_width=True, key="admin_csv")
    if st.button("💾 GUARDAR CAMBIOS EN LA BASE DE DATOS"):
        df_ed.to_csv(DB_FILE, index=False)
        st.success("Cambios aplicados correctamente.")

