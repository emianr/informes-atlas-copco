import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

# --- 1. CONFIGURACIÓN DE LA INTERFAZ ---
# Establece el nombre de la pestaña y expande el diseño a lo ancho de la pantalla.
st.set_page_config(page_title="Atlas Copco Tracker - Spence", layout="wide")

# --- 2. GESTIÓN DE LA BASE DE DATOS (CSV) ---
# Define el nombre del archivo donde se guardará todo el historial.
DB_FILE = "historial_horas.csv"

def cargar_datos():
    """
    Lee el archivo CSV. Si el archivo no existe (primera vez), 
    crea un DataFrame vacío con las columnas necesarias.
    """
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if not df.empty:
                # Convierte la columna 'Fecha' a formato de fecha real de Python.
                df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
            return df
        except:
            return pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])
    else:
        return pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])

# Cargamos los datos existentes al iniciar la app.
df_historial = cargar_datos()

# --- 3. DICCIONARIOS DE DATOS (CONFIGURACIÓN TÉCNICA) ---

# Define el texto largo que irá al Word según la opción de mantenimiento elegida.
operaciones_dict = {
    "INSPECCIÓN": "Inspección visual de equipo",
    "P1": "Mantenimiento Preventivo P1 - Cambio de filtros y revisión general",
    "P2": "Mantenimiento Preventivo P2 - Cambio de kit de filtros y aceite",
    "P3": "Mantenimiento Preventivo P3 - Intervención mayor según pauta técnica"
}

# Base de datos de equipos: [Modelo, Serie, Ubicación, Área]
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

# --- 4. INTERFAZ DE USUARIO (TABS) ---
st.title("🚀 Atlas Copco Tracker - Spence")
tab1, tab2 = st.tabs(["📋 Generar Informe", "📊 Historial Editable"])

with tab1:
    # SELECCIÓN DE TAG (Fuera del form para actualizar los datos del equipo al instante)
    tag_sel = st.selectbox("Seleccione el TAG del equipo", list(equipos_db.keys()))
    modelo_aut, serie_aut, area_aut, clase_aut = equipos_db[tag_sel]
    
    # Busca las últimas horas de marcha registradas para este equipo específico.
    ultimo = df_historial[df_historial["TAG"] == tag_sel].tail(1)
    h_sug = int(ultimo["Horas_Marcha"].values[0]) if not ultimo.empty else 0

    # FORMULARIO PRINCIPAL
    with st.form("editor_informe"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_sel = st.date_input("Fecha de atención", datetime.now())
            cliente_cont = st.text_input("Contacto del Cliente", "Pamela Tapia")
            tipo_servicio = st.selectbox("Tipo de Mantención", list(operaciones_dict.keys()))
        with col2:
            h_marcha_val = st.number_input("Horas Totales Marcha", value=h_sug)
            h_carga_val = st.number_input("Horas Carga", value=0)
            tec1_input = st.text_input("Técnico 1 (Líder)", "Ignacio Morales")
            tec2_input = st.text_input("Técnico 2", "Emian Sanchez")

        st.subheader("⚙️ Parámetros y Unidades")
        # Columnas para elegir unidades (bar/psi y C/F)
        u1, u2, u3, u4 = st.columns(4)
        with u1: p_val = st.text_input("Presión de Carga", "6.4")
        with u2: p_unit = st.selectbox("Unidad Presión", ["bar", "psi"])
        with u3: t_val = st.text_input("Temperatura", "80")
        with u4: t_unit = st.selectbox("Unidad Temp.", ["°C", "°F"])

        # Generación de textos automáticos para el Word
        alcance_val = f"Se realizó inspección a equipo compresor {modelo_aut} con identificación TAG {tag_sel} de {clase_aut}, {area_aut}."
        alcance_manual = st.text_area("Alcance del Trabajo", value=alcance_val, height=70)
        
        concl_val = f"El equipo queda operativo bajo parámetros normales (Presión: {p_val} {p_unit}, Temp: {t_val} {t_unit}), con niveles de fluidos en rango."
        concl_manual = st.text_area("Condición Final", value=concl_val, height=70)

        # Botón para procesar todo el formulario
        enviar = st.form_submit_button("💾 GUARDAR Y GENERAR REPORTE")

    if enviar:
        # 5. GUARDADO DE DATOS
        nuevo_registro = pd.DataFrame([[fecha_sel, tag_sel, h_marcha_val, h_carga_val, tec1_input, tec2_input, cliente_cont]], 
                             columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])
        df_historial = pd.concat([df_historial, nuevo_registro], ignore_index=True)
        df_historial.to_csv(DB_FILE, index=False)
        
        try:
            # 6. LÓGICA DEL DOCUMENTO WORD
            doc = DocxTemplate("InformeInspección.docx")
            
            # Formateo de Fecha en Español (Día de Mes de Año)
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            fecha_espanol = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"
            
            # Mapeo de campos: "Etiqueta_Word": Valor_App
            contexto = {
                "fecha": fecha_espanol,
                "cliente_contact": cliente_cont,
                "tag": tag_sel,
                "equipo_modelo": modelo_aut,
                "serie": serie_aut,
                "area": area_aut,
                "clase_area": clase_aut,
                "tipo_orden": tipo_servicio,
                "tecnico_1": tec1_input,
                "tecnico_2": tec2_input,
                "horas_marcha": f"{h_marcha_val} Hrs.",
                "horas_totales_despues": f"{h_marcha_val}",
                "horas_carga_despues": f"{h_carga_val}",
                "alcanze_intervencion": alcance_manual.strip(),
                "estado_entrega": concl_manual.strip(),
                "operaciones_dinamicas": operaciones_dict.get(tipo_servicio, "Inspección técnica"),
                # Nuevas variables para unidades flexibles
                "p_unidad": p_unit,
                "t_unidad": t_unit
            }
            
            # Crea el archivo Word final
            doc.render(contexto)
            output = io.BytesIO()
            doc.save(output)
            output.seek(0)
            
            st.success("✅ Datos guardados y reporte listo.")
            st.download_button("📥 DESCARGAR REPORTE", output, f"Informe_{tag_sel}.docx")
        except Exception as e:
            st.error(f"❌ Error al generar el Word: {e}")

# --- 5. PESTAÑA DE ADMINISTRACIÓN (HISTORIAL) ---
with tab2:
    st.subheader("🛠️ Panel de Control de Datos")
    st.write("Usa esta tabla para corregir errores o borrar registros.")
    
    # Recarga el CSV para mostrar los cambios más recientes
    df_fresco = cargar_datos()
    
    # Editor de datos: permite editar como si fuera un Excel
    df_editado = st.data_editor(df_fresco, num_rows="dynamic", use_container_width=True, key="admin_edit_v3")
    
    if st.button("💾 CONFIRMAR TODOS LOS CAMBIOS"):
        df_editado.to_csv(DB_FILE, index=False)
        st.success("Historial actualizado satisfactoriamente.")
        st.rerun()
