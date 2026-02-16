import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

# --- PASO 1: CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Atlas Copco Tracker - Automático", layout="wide")

# --- PASO 2: BASE DE DATOS DE EQUIPOS (17 TAGS) ---
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

# --- PASO 3: RECOPILLACIÓN DE TEXTOS AUTOMÁTICOS (Según tu solicitud) ---
plantillas = {
    "INSPECCIÓN": {
        "actividades": "• Inspección de fugas: Revisión visual de circuitos de aire/aceite.\n• Verificación de lubricante: Chequeo por visor de separador si está dentro del rango establecido.\n• Revisión enfriador: Inspección visual en enfriador de aire/aceite.\n• Monitoreo de controlador: Validación de funcionamiento de controlador, realizando prueba en carga/descarga del equipo.\n• Estado operacional: Verificación de parámetros de operación.\n• Purga condensado: Drenado de condensado del equipo.",
        "condicion": "El equipo se encuentra funcionando bajo parámetros estables, a excepción de temperatura de trabajo con un alza considerable, con nivel de aceite dentro del rango establecido y con filtros sin saturación.\nSe observa alta saturación por contaminación en enfriadores y fuga de aceite en enfriador de aceite, causando derrame exterior en enfriador de aire.\nSe encuentran flexibles y sensores con exceso de corrosión.\nLa lluvia elevó la humedad relativa provocando acumulación excesiva de condensado.",
        "recomendaciones": "• Nota técnica: El equipo supera las horas recomendadas para su intervención mayor (40.000 horas). Se recomienda enviar a overhaul o reemplazar equipo.\n• Mantenimiento correctivo: Programar reparación de la fuga detectada en los enfriadores de aceite o el cambio en su totalidad."
    },
    "P1": {
        "actividades": "• Inspección de fugas: Revisión visual de circuitos de aire/aceite.\n• Limpieza general: Limpieza general de equipo compresor.\n• Verificación de lubricante: Revisión por visor de nivel óptimo.\n• Chequeo enfriador: Inspección visual en enfriador de aire/aceite.\n• Cambio filtros: Cambio de filtros de aire/aceite.\n• Monitoreo de controlador: Validación de parámetros de operación, realizando prueba en carga/descarga del equipo.\n• Estado operacional: Verificación de parámetros.",
        "condicion": "El equipo se encuentra funcionando bajo parámetros estables, nivel de aceite dentro del rango establecido y con filtros sin saturación.\nSe detectan enfriadores saturados por contaminación, pero sin fugas visibles.\nSe encuentran flexibles y sensores con exceso de corrosión.",
        "recomendaciones": "• Plan de mantenimiento: Mantener frecuencia de inspección y drenado de condensados según plan preventivo vigente.\n• Control ambiental: Considerar limpieza preventiva del entorno y radiadores debido a la alta contaminación del sector."
    },
    "P2": {
        "actividades": "• Inspección de fugas: Revisión visual de circuitos de aire/aceite.\n• Limpieza general: Limpieza general de equipo compresor.\n• Cambio de lubricante: Se realiza drenado con cambio de aceite y revisión por visor.\n• Chequeo enfriador: Inspección visual en enfriador de aire/aceite.\n• Cambio filtros: Cambio de filtros de aire/aceite.\n• Monitoreo de controlador: Validación de parámetros de operación, realizando prueba en carga/descarga del equipo.\n• Estado operacional: Verificación de parámetros.",
        "condicion": "El equipo se encuentra funcionando bajo parámetros estables, nivel de aceite dentro del rango establecido y con filtros sin saturación.\nSe detectan enfriadores saturados por contaminación, pero sin fugas visibles.\nSe encuentran flexibles y sensores con exceso de corrosión.",
        "recomendaciones": "• Plan de mantenimiento: Mantener frecuencia de inspección y drenado de condensados según plan preventivo vigente.\n• Control ambiental: Considerar limpieza preventiva del entorno y radiadores debido a la alta contaminación del sector."
    }
}

# --- PASO 4: CARGAR HISTORIAL ---
DB_FILE = "historial_horas.csv"
def cargar_datos():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        return df
    return pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])

df_historial = cargar_datos()

# --- PASO 5: INTERFAZ GRÁFICA ---
tab1, tab2 = st.tabs(["📋 Generar Informe", "⚙️ Administración"])

with tab1:
    # Selectores principales (Al cambiar estos, cambia TODO el texto de abajo)
    c1, c2 = st.columns(2)
    with c1:
        tag_sel = st.selectbox("Seleccione TAG", list(equipos_db.keys()))
    with c2:
        tipo_sel = st.selectbox("Tipo de Servicio", ["INSPECCIÓN", "P1", "P2"])

    # Datos automáticos del equipo y textos de la plantilla
    mod, ser, loc, are = equipos_db[tag_sel]
    t_plantilla = plantillas[tipo_sel]

    with st.form("form_auto"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_sel = st.date_input("Fecha", datetime.now())
            cliente = st.text_input("Contacto Cliente", "Pamela Tapia")
        with col2:
            h_m = st.number_input("Horas Marcha", value=0)
            tec1 = st.text_input("Técnico 1", "Ignacio Morales")
            tec2 = st.text_input("Técnico 2", "Emian Sanchez")

        st.subheader("⚙️ Parámetros Operacionales")
        p1, p2, p3, p4 = st.columns(4)
        with p1: p_val = st.text_input("Presión Carga", "6.4")
        with p2: p_uni = st.selectbox("Unidad", ["bar", "psi"])
        with p3: t_val = st.text_input("Temp Salida", "80")
        with p4: t_uni = st.selectbox("Unidad", ["°C", "°F"])

        st.subheader("📝 Contenido Dinámico (Se actualiza solo)")
        # Aquí la magia: el valor por defecto cambia según el tipo de servicio seleccionado arriba
        alcance = st.text_area("Alcance de la intervención", 
                               value=f"Se realizó {tipo_sel.lower()} a equipo compresor {mod} con identificación TAG {tag_sel} de {are}, {loc}, conforme a procedimientos internos y buenas prácticas de mantenimiento.")
        
        actividades = st.text_area("Actividades ejecutadas", value=t_plantilla["actividades"], height=200)
        
        # Agregamos los parámetros de presión al texto de condición automáticamente
        cond_final_texto = f"{t_plantilla['condicion']}\n\nParámetros verificados: Carga {p_val} {p_uni} / Temp {t_val} {t_uni}."
        condicion = st.text_area("Condición final y estado de entrega", value=cond_final_texto, height=150)
        
        recomendaciones = st.text_area("Recomendaciones", value=t_plantilla["recomendaciones"], height=120)

        boton = st.form_submit_button("💾 GUARDAR Y GENERAR WORD")

    if boton:
        # Guardado en CSV
        nuevo = pd.DataFrame([[fecha_sel, tag_sel, h_m, 0, tec1, tec2, cliente]], 
                             columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])
        pd.concat([df_historial, nuevo]).to_csv(DB_FILE, index=False)
        
        try:
            doc = DocxTemplate("InformeInspección.docx")
            
            # Fecha en español
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            fecha_es = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"

            contexto = {
                "fecha": fecha_es, "cliente_contact": cliente, "tag": tag_sel, "equipo_modelo": mod,
                "serie": ser, "area": are, "clase_area": loc, "tipo_orden": tipo_sel,
                "tecnico_1": tec1, "tecnico_2": tec2, "horas_marcha": f"{h_m} Hrs.",
                "alcance": alcance, "actividades_ejecutadas": actividades,
                "estado_entrega": condicion, "recomendaciones": recomendaciones
            }
            
            doc.render(contexto)
            bio = io.BytesIO()
            doc.save(bio)
            st.success("✅ Registro exitoso.")
            st.download_button("📥 DESCARGAR REPORTE", bio.getvalue(), f"Reporte_{tag_sel}_{tipo_sel}.docx")
        except Exception as e:
            st.error(f"Error: {e}")

with tab2:
    st.subheader("📊 Historial de Intervenciones")
    df_f = cargar_datos()
    df_ed = st.data_editor(df_f, num_rows="dynamic", use_container_width=True)
    if st.button("💾 CONFIRMAR CAMBIOS"):
        df_ed.to_csv(DB_FILE, index=False)
        st.success("Cambios guardados.")
