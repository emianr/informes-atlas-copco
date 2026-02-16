import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os
import locale

# --- CONFIGURACIÓN DE PÁGINA ---
# Define el título de la pestaña del navegador y el ancho de la interfaz.
st.set_page_config(page_title="Atlas Copco Tracker - Spence", layout="wide")

# --- MANEJO DE IDIOMA (FECHA EN ESPAÑOL) ---
# Intentamos configurar el sistema para que las fechas salgan en español.
try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8") 
except:
    # Si el servidor no soporta el cambio de locale, usaremos un diccionario manual más adelante.
    pass

# --- BASE DE DATOS LOCAL (CSV) ---
DB_FILE = "historial_horas.csv"

def cargar_datos():
    """Función para leer el historial guardado. Si no existe el archivo, crea uno vacío."""
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if not df.empty:
                df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
            return df
        except:
            return pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])
    else:
        return pd.DataFrame(columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])

df_historial = cargar_datos()

# --- DICCIONARIO DE OPERACIONES ---
# Define qué texto se escribirá en el Word según la opción elegida en el menú desplegable.
operaciones_dict = {
    "INSPECCIÓN": "Inspección visual de equipo",
    "P1": "Mantenimiento Preventivo P1 - Cambio de filtros y revisión general",
    "P2": "Mantenimiento Preventivo P2 - Cambio de kit de filtros y aceite",
    "P3": "Mantenimiento Preventivo P3 - Intervención mayor según pauta técnica"
}

# --- BASE DE DATOS DE EQUIPOS ---
# Contiene la información técnica amarrada a cada TAG.
equipos_db = {
    "70-GC-013": ["GA 132", "AIF095296", "descarga ácido", "área húmeda"],
    "70-GC-014": ["GA 132", "AIF095297", "descarga +acido", "área húmeda"],
    "50-GC-001": ["GA 45", "API542705", "planta SX", "área húmeda"],
    "50-GC-002": ["GA 45", "API542706", "planta SX", "área húmeda"],
    "50-GC-003": ["ZT 37", "API791692", "planta SX", "área húmeda"],
    "50-GC-004": ["ZT 37", "API791693", "planta SX", "área húmeda"],
    "50-CD-001": ["CD 80+", "API095825", "planta SX", "área húmeda"],
    "050-CD-002": ["CD 80+", "API095826", "planta SX", "área húmeda"],
    "50-GC-015": ["GA 30", "API501440", "planta borra", "área húmeda"],
    "65-GC-011": ["GA 250", "APF253581", "patio estanques", "área húmeda"],
    "65-GC-009": ["GA 250", "APF253608", "patio estanques", "área húmeda"],
    "65-CD-011": ["CD 630", "WXF300015", "patio estanques", "área húmeda"],  
    "65-CD-012": ["CD 630", "WXF300016", "patio estanques", "área húmeda"],  
    "35-GC-006": ["GA 250", "AIF095420", "chancado secundario", "área seca"],
    "35-GC-007": ["GA 250", "AIF095421", "chancado secundario", "área seca"],
    "35-GC-008": ["GA 250", "AIF095302", "chancado secundario", "área seca"],
    "20-GC-004": ["GA 37", "AII390776", "truck shop", "mina"],
    "20-GC-001": ["GA 75", "AII482673", "truck shop", "mina"],
    "20-GC-002": ["GA 75", "AII482674", "truck shop", "mina"],
    "20-GC-003": ["GA 90", "AIF095178", "truck shop", "mina"],
    "TALLER-01": ["GA18", "API335343", "taller", "área seca"]
}

st.title("🚀 Atlas Copco Tracker - Spence")

# Creamos dos pestañas para separar la creación de informes de la edición de datos.
tab1, tab2 = st.tabs(["Generar Informe", "📊 Historial Editable"])

with tab1:
    # 1. SELECCIÓN DE EQUIPO: Se hace fuera del form para que la app se actualice al cambiar el TAG.
    tag_sel = st.selectbox("Seleccione el TAG", list(equipos_db.keys()))
    modelo_aut, serie_aut, area_aut, clase_aut = equipos_db[tag_sel]
    
    # Buscamos en el historial las últimas horas registradas para ese TAG.
    ultimo = df_historial[df_historial["TAG"] == tag_sel].tail(1)
    h_sug = int(ultimo["Horas_Marcha"].values[0]) if not ultimo.empty else 0

    # 2. FORMULARIO DE ENTRADA: Agrupa los campos para que no se recargue la página por cada clic.
    with st.form("editor_informe"):
        c1, c2 = st.columns(2)
        with c1:
            fecha_sel = st.date_input("Fecha de servicio", datetime.now())
            cliente_cont = st.text_input("Contacto Cliente", "Pamela Tapia")
            tipo_servicio = st.selectbox("Tipo de Mantención", list(operaciones_dict.keys()))
        with c2:
            h_marcha_val = st.number_input("Horas Totales Marcha", value=h_sug)
            h_carga_val = st.number_input("Horas Carga", value=0)
            tec1_input = st.text_input("Técnico 1 (Responsable)", "Ignacio Morales")
            tec2_input = st.text_input("Técnico 2", "Emian Sanchez")

        st.subheader("📊 Parámetros Operacionales")
        p1, p2, p3 = st.columns(3)
        with p1: p_carga = st.text_input("Carga (bar)", "6.4")
        with p2: p_descarga = st.text_input("Descarga (bar)", "6.8")
        with p3: temp_sal = st.text_input("Temp (°C)", "80")

        # Texto de alcance autogenerado pero editable.
        alcance_val = f"Se realizó inspección a equipo compresor {modelo_aut} con identificación TAG {tag_sel} de {clase_aut}, {area_aut}."
        alcance_manual = st.text_area("Alcance del Trabajo", value=alcance_val, height=80)
        
        concl_val = f"Equipo operativo. Parámetros: Carga {p_carga} bar / Descarga {p_descarga} bar / Temp {temp_sal} °C."
        concl_manual = st.text_area("Condición Final de Entrega", value=concl_val, height=80)

        # Botón de envío: Sin esto, el formulario no se procesa.
        enviar = st.form_submit_button("💾 GUARDAR REGISTRO E IMPRIMIR")

    if enviar:
        # 3. GUARDADO EN HISTORIAL: Agregamos la nueva fila al DataFrame y lo guardamos en el CSV.
        nuevo = pd.DataFrame([[fecha_sel, tag_sel, h_marcha_val, h_carga_val, tec1_input, tec2_input, cliente_cont]], 
                             columns=["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto"])
        df_historial = pd.concat([df_historial, nuevo], ignore_index=True)
        df_historial.to_csv(DB_FILE, index=False)
        
        try:
            # 4. GENERACIÓN DEL WORD:
            doc = DocxTemplate("InformeInspección.docx")
            
            # Formateo manual de fecha en español (Día de Mes de Año)
            meses_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            fecha_txt = f"{fecha_sel.day} de {meses_es[fecha_sel.month - 1]} de {fecha_sel.year}"
            
            # Este diccionario vincula las etiquetas {{ }} del Word con los datos de la app.
            contexto = {
                "fecha": fecha_txt,
                "cliente_contact": cliente_cont,
                "tag": tag_sel,
                "equipo_modelo": modelo_aut,
                "serie": serie_aut,
                "area": area_aut,
                "clase_area": clase_aut,
                "tipo_orden": tipo_servicio,
                "tecnico_1": tec1_input,
                "tecnico_2": tec2_input,
                "act_1": "M.OB.ST", "h_1": "8", "h_2": "8",
                "horas_marcha": f"{h_marcha_val} Hrs.",
                "horas_totales_despues": f"{h_marcha_val}",
                "horas_carga_despues": f"{h_carga_val}",
                "alcanze_intervencion": alcance_manual.strip(),
                "estado_entrega": concl_manual.strip(),
                "operaciones_dinamicas": operaciones_dict.get(tipo_servicio, "Inspección visual")
            }
            
            # Renderizamos el Word (rellenamos las llaves) y lo guardamos en memoria.
            doc.render(contexto)
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            
            st.success("✅ Registro guardado en historial.")
            # Ofrece el archivo procesado para descargar.
            st.download_button("📥 DESCARGAR REPORTE", bio, f"Reporte_{tag_sel}.docx")
        except Exception as e:
            st.error(f"⚠️ Error al crear el Word: {e}")

# --- PESTAÑA DE ADMINISTRACIÓN ---
with tab2:
    st.subheader("🛠️ Administrador de Base de Datos")
    st.info("Cualquier cambio hecho aquí se guardará permanentemente en el archivo CSV.")
    
    # Recargamos los datos para asegurar que vemos lo último guardado.
    df_fresco = cargar_datos()
    
    # El editor de datos permite borrar filas, cambiar nombres o corregir horas directamente.
    df_editado = st.data_editor(df_fresco, num_rows="dynamic", use_container_width=True, key="admin_edit")
    
    if st.button("💾 CONFIRMAR CAMBIOS EN HISTORIAL"):
        df_editado.to_csv(DB_FILE, index=False)
        st.success("Base de datos actualizada con éxito.")
        st.rerun() # Reinicia la app para aplicar cambios.

