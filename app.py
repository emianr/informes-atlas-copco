import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Atlas Copco Tracker - Inteligente", layout="wide")

DB_FILE = "historial_horas.csv"

# --- 2. EL CEREBRO DE TEXTOS (LOGICA SEGUN TIPO DE MANTENCION) ---
# Aquí guardamos los textos que me pasaste para que cambien solos.
plantillas_mantenimiento = {
    "INSPECCIÓN": {
        "actividades": "• Inspección de fugas: Revisión visual de circuitos de aire/aceite.\n• Verificación de lubricante: Chequeo por visor de nivel.\n• Revisión enfriador: Inspección visual.\n• Monitoreo de controlador: Prueba de carga/descarga.\n• Purga condensado: Drenado de humedad.",
        "condicion": "El equipo se encuentra funcionando bajo parámetros estables, a excepción de temperatura de trabajo con un alza considerable. Se observa saturación en enfriadores y corrosión en flexibles/sensores. La lluvia elevó la humedad drenando exceso de condensado.",
        "recomendaciones": "• Nota técnica: Supera horas para overhaul (40k hrs). Se recomienda reemplazo.\n• Mantenimiento correctivo: Programar reparación de fuga en enfriadores para evitar corrosión mayor."
    },
    "P1": {
        "actividades": "• Inspección de fugas: Revisión visual.\n• Limpieza general: Limpieza de equipo compresor.\n• Verificación de lubricante: Revisión de nivel óptimo.\n• Cambio filtros: Cambio de filtros de aire y aceite.\n• Monitoreo de controlador: Validación de carga/descarga.",
        "condicion": "Equipo funcionando bajo parámetros estables, nivel de aceite en rango y filtros nuevos. Se detectan enfriadores saturados por contaminación ambiental. Flexibles y sensores presentan corrosión.",
        "recomendaciones": "• Plan de mantenimiento: Mantener frecuencia de inspección y drenado según plan vigente.\n• Control ambiental: Realizar limpieza preventiva de radiadores por alta contaminación del sector."
    },
    "P2": {
        "actividades": "• Inspección de fugas: Revisión visual.\n• Limpieza general: Limpieza de equipo compresor.\n• Cambio de lubricante: Drenado y cambio de aceite completo.\n• Cambio filtros: Cambio de kit de filtros (aire/aceite).\n• Monitoreo de controlador: Validación de parámetros operativos.",
        "condicion": "Equipo entregado en óptimas condiciones de lubricación, parámetros estables y filtros nuevos. Enfriadores con saturación externa. Presencia de corrosión en componentes periféricos.",
        "recomendaciones": "• Plan de mantenimiento: Continuar con plan preventivo.\n• Control ambiental: Mejorar limpieza del entorno para prolongar vida útil de componentes nuevos."
    }
}

# --- 3. BASE DE DATOS DE EQUIPOS ---
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

# --- 4. CARGA DE DATOS ---
def cargar_datos():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        return df
    return pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])

df_historial = cargar_datos()

# --- 5. INTERFAZ ---
tab1, tab2 = st.tabs(["📋 Generar Informe", "📊 Historial"])

with tab1:
    # Selección de TAG y Tipo de Mantención (Fuera del form para actualizar textos)
    c_top1, c_top2 = st.columns(2)
    with c_top1:
        tag_sel = st.selectbox("Seleccione el TAG", list(equipos_db.keys()))
    with c_top2:
        tipo_m_sel = st.selectbox("Seleccione Tipo de Intervención", ["INSPECCIÓN", "P1", "P2"])

    mod, ser, loc, are = equipos_db[tag_sel]
    textos_base = plantillas_mantenimiento[tipo_m_sel]

    with st.form("form_inteligente"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_sel = st.date_input("Fecha", datetime.now())
            cliente = st.text_input("Contacto", "Pamela Tapia")
        with col2:
            h_m = st.number_input("Horas Marcha", value=0)
            tec1 = st.text_input("Técnico 1", "Ignacio Morales")
            tec2 = st.text_input("Técnico 2", "Emian Sanchez")

        st.subheader("⚙️ Parámetros Operacionales")
        p1, p2, p3, p4 = st.columns(4)
        with p1: p_c = st.text_input("P. Carga", "6.4")
        with p2: p_u = st.selectbox("Unidad", ["bar", "psi"])
        with p3: t_s = st.text_input("Temp Salida", "80")
        with p4: t_u = st.selectbox("Unidad", ["°C", "°F"])

        # Estos textos se llenan SOLOS según si es Inspección, P1 o P2
        st.subheader("📝 Contenido del Reporte")
        alcance = st.text_area("Alcance", value=f"Se realizó {tipo_m_sel.lower()} a equipo compresor {mod} TAG {tag_sel} de {are}, {loc}.")
        actividades = st.text_area("Actividades Ejecutadas", value=textos_base["actividades"], height=150)
        condicion = st.text_area("Condición Final", value=textos_base["condicion"], height=100)
        recomendaciones = st.text_area("Recomendaciones", value=textos_base["recomendaciones"], height=100)

        enviar = st.form_submit_button("💾 GUARDAR Y GENERAR")

    if enviar:
        # Guardado de datos
        nuevo = pd.DataFrame([[fecha_sel, tag_sel, h_m, 0, tec1, tec2, cliente]], 
                             columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])
        pd.concat([df_historial, nuevo]).to_csv(DB_FILE, index=False)
        
        try:
            doc = DocxTemplate("InformeInspección.docx")
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            fecha_es = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"

            # Mapeo de campos para el Word
            contexto = {
                "fecha": fecha_es,
                "cliente_contact": cliente,
                "tag": tag_sel,
                "equipo_modelo": mod,
                "serie": ser,
                "area": are,
                "clase_area": loc,
                "tipo_orden": tipo_m_sel,
                "tecnico_1": tec1,
                "tecnico_2": tec2,
                "horas_marcha": f"{h_m} Hrs.",
                "p_unidad": p_u, "t_unidad": t_u,
                # NUEVOS CAMPOS DINÁMICOS
                "alcance": alcance,
                "actividades_ejecutadas": actividades,
                "estado_entrega": condicion,
                "recomendaciones": recomendaciones
            }
            doc.render(contexto)
            bio = io.BytesIO()
            doc.save(bio)
            st.success("✅ ¡Reporte generado con éxito!")
            st.download_button("📥 DESCARGAR", bio.getvalue(), f"Reporte_{tag_sel}_{tipo_m_sel}.docx")
        except Exception as e:
            st.error(f"Error: {e}")

with tab2:
    st.subheader("📊 Historial y Administración")
    df_f = cargar_datos()
    df_ed = st.data_editor(df_f, num_rows="dynamic", use_container_width=True)
    if st.button("💾 GUARDAR CAMBIOS"):
        df_ed.to_csv(DB_FILE, index=False)
        st.success("Base de datos actualizada.")
