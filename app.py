import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Atlas Copco Tracker - Spence", layout="wide")

# ─────────────────────────────────────────────
# BASE DE DATOS CSV
# ─────────────────────────────────────────────
DB_FILE = "historial_horas.csv"
COLUMNAS = ["Fecha", "TAG", "Horas_Marcha", "Horas_Carga", "Tecnico_1", "Tecnico_2", "Contacto", "Tipo"]

def cargar_datos():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            for col in COLUMNAS:
                if col not in df.columns:
                    df[col] = ""
            if not df.empty:
                df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
            return df
        except Exception as e:
            st.warning(f"⚠️ No se pudo leer el historial: {e}")
            return pd.DataFrame(columns=COLUMNAS)
    return pd.DataFrame(columns=COLUMNAS)

def guardar_datos(df):
    try:
        df.to_csv(DB_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"❌ Error guardando datos: {e}")
        return False

if "df_historial" not in st.session_state:
    st.session_state["df_historial"] = cargar_datos()

# ─────────────────────────────────────────────
# EQUIPOS  [modelo, serie, ubicacion, area]
# ─────────────────────────────────────────────
equipos_db = {
    "70-GC-013":  ["GA 132", "AIF095296", "descarga acido",       "área húmeda"],
    "70-GC-014":  ["GA 132", "AIF095297", "descarga acido",       "área húmeda"],
    "050-GD-001": ["GA 45",  "API542705", "planta sx",            "área húmeda"],
    "050-GD-002": ["GA 45",  "API542706", "planta sx",            "área húmeda"],
    "050-GC-003": ["ZT 37",  "API791692", "planta sx",            "área húmeda"],
    "050-GC-004": ["ZT 37",  "API791693", "planta sx",            "área húmeda"],
    "050-CD-001": ["CD 80+", "API095825", "planta sx",            "área húmeda"],
    "050-CD-002": ["CD 80+", "API095826", "planta sx",            "área húmeda"],
    "050-GC-015": ["GA 30",  "API501440", "planta borra",         "área húmeda"],
    "65-GC-011":  ["GA 250", "APF253581", "patio estanques",      "área húmeda"],
    "65-GC-009":  ["GA 250", "APF253608", "patio estanques",      "área húmeda"],
    "65-GD-011":  ["CD 630", "WXF300015", "patio estanques",      "área húmeda"],
    "65-GD-012":  ["CD 630", "WXF300016", "patio estanques",      "área húmeda"],
    "35-GC-006":  ["GA 250", "AIF095420", "chancado secundario",  "área seca"],
    "35-GC-007":  ["GA 250", "AIF095421", "chancado secundario",  "área seca"],
    "35-GC-008":  ["GA 250", "AIF095302", "chancado secundario",  "área seca"],
    "20-GC-004":  ["GA 37",  "AII390776", "mina",                 "mina"],
    "20-GC-001":  ["GA 75",  "AII482673", "truck shop",           "mina"],
    "20-GC-002":  ["GA 75",  "AII482674", "truck shop",           "mina"],
    "20-GC-003":  ["GA 90",  "AIF095178", "truck shop",           "mina"],
    "TALLER-01":  ["GA 18",  "API335343", "taller",               "área seca"],
}

# ─────────────────────────────────────────────
# PLANTILLAS DINÁMICAS POR TIPO
# ─────────────────────────────────────────────
def get_plantilla(tipo, modelo, tag, ubicacion, area, p_carga, p_descarga, temp_salida):

    verbo = "inspección" if tipo == "INSPECCIÓN" else ("mantención mayor" if tipo == "P3" else "mantención")
    alcance = (
        f"Se realizó {verbo} a equipo compresor {modelo} con identificación TAG {tag} "
        f"de {area}, {ubicacion}, conforme a procedimientos internos y buenas prácticas de mantenimiento."
    )

    estado_op = (
        f"• Estado operacional: Verificación de parámetros de operación "
        f"(Presión de carga: {p_carga} bar / descarga: {p_descarga} bar) "
        f"y temperatura de salida del elemento ({temp_salida} °C)."
    )

    if tipo == "INSPECCIÓN":
        actividades = (
            "• Inspección de fugas: Revisión visual de circuitos de aire y aceite.\n"
            "• Nivel de lubricante: Chequeo del nivel de aceite por medio del visor.\n"
            "• Revisión enfriador: Inspección visual en enfriador de aire/aceite.\n"
            "• Revisión general: Se verifica estado de filtros de aire, válvula de corte y líneas de aire.\n"
            "• Monitoreo de controlador: Validación de parámetros de operación, realizando prueba en carga/descarga del equipo.\n"
            f"{estado_op}\n"
            "• Purga condensado: Drenado de condensado del equipo."
        )
        condicion = (
            "El equipo se encuentra funcionando bajo parámetros estables, con nivel de aceite "
            "dentro del rango establecido y con filtros sin saturación."
        )
        recomendaciones = (
            "• Nota técnica: El equipo supera las horas recomendadas por fábrica para mantenimiento mayor, "
            "se recomienda enviar a overhaul o reemplazar por equipo nuevo para asegurar la confiabilidad operativa."
        )
        proxima_visita = "El próximo servicio recomendado es Inspección estimada requerida"
        tipo_orden_txt = "INSPECCIÓN"

    elif tipo == "P1":
        actividades = (
            "• Inspección de fugas: Revisión visual de circuitos de aire/aceite.\n"
            "• Limpieza general: Limpieza general de equipo compresor.\n"
            "• Verificación de lubricante: Revisión por visor de nivel óptimo.\n"
            "• Chequeo enfriador: Inspección visual en enfriador de aire/aceite.\n"
            "• Cambio filtros: Cambio de filtros de aire/aceite.\n"
            "• Monitoreo de controlador: Validación de parámetros de operación, realizando prueba en carga/descarga del equipo.\n"
            f"{estado_op}"
        )
        condicion = (
            "El equipo se encuentra funcionando bajo parámetros estables, nivel de aceite "
            "dentro del rango establecido y con filtros sin saturación."
        )
        recomendaciones = (
            "• Plan de mantenimiento: Mantener frecuencia de inspección y drenado de condensados según plan preventivo vigente.\n"
            "• Control ambiental: Considerar limpieza preventiva del entorno y radiadores debido a la alta "
            "contaminación del sector, con el fin de prolongar la vida útil de los componentes."
        )
        proxima_visita = "El próximo servicio recomendado es P2 estimada requerida"
        tipo_orden_txt = "Mantención P1"

    elif tipo == "P2":
        actividades = (
            "• Inspección de fugas: Revisión visual de circuitos de aire/aceite.\n"
            "• Limpieza general: Limpieza general de equipo compresor.\n"
            "• Cambio de lubricante: Se realiza drenado con cambio de aceite y revisión por visor.\n"
            "• Chequeo enfriador: Inspección visual en enfriador de aire/aceite.\n"
            "• Cambio filtros: Cambio de filtros de aire/aceite.\n"
            "• Monitoreo de controlador: Validación de parámetros de operación, realizando prueba en carga/descarga del equipo.\n"
            f"{estado_op}"
        )
        condicion = (
            "El equipo se encuentra funcionando bajo parámetros estables, nivel de aceite "
            "dentro del rango establecido y con filtros sin saturación.\n"
            "Se detectan enfriadores saturados por contaminación, pero sin fugas visibles."
        )
        recomendaciones = (
            "• Plan de mantenimiento: Mantener frecuencia de inspección y drenado de condensados según plan preventivo vigente.\n"
            "• Control ambiental: Considerar limpieza preventiva del entorno y radiadores debido a la alta "
            "contaminación del sector, con el fin de prolongar la vida útil de los componentes."
        )
        proxima_visita = "El próximo servicio recomendado es P3 estimada requerida"
        tipo_orden_txt = "Mantención P2"

    else:  # P3
        actividades = (
            "• Inspección de fugas: Revisión visual de circuitos de aire/aceite.\n"
            "• Limpieza profunda: Limpieza profunda de enfriadores y componentes internos.\n"
            "• Cambio de lubricante: Drenado completo con cambio de aceite y revisión por visor.\n"
            "• Cambio filtros: Cambio de filtros de aire, aceite y separador.\n"
            "• Engrase rodamientos: Engrase de rodamientos del motor eléctrico.\n"
            "• Revisión válvulas: Inspección y limpieza de válvula de mínima y anti-retorno.\n"
            "• Monitoreo de controlador: Validación de parámetros de operación, realizando prueba en carga/descarga del equipo.\n"
            f"{estado_op}"
        )
        condicion = (
            "El equipo se encuentra en óptimas condiciones tras mantención mayor. "
            "Parámetros en rango nominal, nivel de aceite correcto y filtros nuevos instalados."
        )
        recomendaciones = (
            "• Plan de mantenimiento: Continuar con plan de mantenimiento preventivo.\n"
            "• Próxima intervención: Programar próxima mantención mayor según horas de operación del equipo."
        )
        proxima_visita = "El próximo servicio recomendado es Inspección estimada requerida"
        tipo_orden_txt = "Mantención P3"

    return {
        "alcance": alcance,
        "actividades": actividades,
        "condicion": condicion,
        "recomendaciones": recomendaciones,
        "proxima_visita": proxima_visita,
        "tipo_orden_txt": tipo_orden_txt,
    }

# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────
st.title("🚀 Atlas Copco Tracker - Spence")
tab1, tab2 = st.tabs(["📋 Generar Informe", "📊 Historial"])

with tab1:

    col_tag, col_tipo = st.columns(2)
    with col_tag:
        tag_sel = st.selectbox("🔧 TAG del equipo", list(equipos_db.keys()))
    with col_tipo:
        tipo_mant = st.selectbox("📋 Tipo de Mantención", ["INSPECCIÓN", "P1", "P2", "P3"])

    # Info automática del equipo seleccionado
    mod_aut, ser_aut, loc_aut, area_aut = equipos_db[tag_sel]
    st.info(f"**Equipo:** {mod_aut} &nbsp;|&nbsp; **Serie:** {ser_aut} &nbsp;|&nbsp; **Ubicación:** {loc_aut} &nbsp;|&nbsp; **Área:** {area_aut}")

    # Último registro del equipo
    df_actual = st.session_state["df_historial"]
    ultimo = df_actual[df_actual["TAG"] == tag_sel].tail(1)
    h_sug       = int(ultimo["Horas_Marcha"].values[0]) if not ultimo.empty else 0
    h_sug_carga = int(ultimo["Horas_Carga"].values[0])  if not ultimo.empty else 0
    if not ultimo.empty:
        ultimo_tipo = ultimo["Tipo"].values[0] if "Tipo" in ultimo.columns else "—"
        st.caption(f"📅 Último registro: **{ultimo['Fecha'].values[0]}** — {ultimo_tipo} — {h_sug} hrs marcha")

    st.divider()

    with st.form("editor_informe"):

        st.subheader("👤 Datos Generales")
        c1, c2 = st.columns(2)
        with c1:
            fecha_sel    = st.date_input("Fecha de atención", datetime.now())
            default_tec1 = st.secrets.get("tec1_default", "Ignacio Morales") if hasattr(st, "secrets") else "Ignacio Morales"
            tec1         = st.text_input("Técnico 1 (Líder)", default_tec1)
        with c2:
            default_contacto = st.secrets.get("contacto_default", "Pamela Tapia") if hasattr(st, "secrets") else "Pamela Tapia"
            cliente_cont     = st.text_input("Contacto Cliente", default_contacto)
            default_tec2     = st.secrets.get("tec2_default", "Emian Sanchez") if hasattr(st, "secrets") else "Emian Sanchez"
            tec2             = st.text_input("Técnico 2", default_tec2)

        st.subheader("⏱️ Horas del Equipo")
        ch1, ch2 = st.columns(2)
        with ch1:
            h_marcha = st.number_input("Horas Totales Marcha", value=h_sug, step=1)
        with ch2:
            h_carga = st.number_input("Horas Carga", value=h_sug_carga, step=1)

        st.subheader("⚙️ Parámetros Operacionales")
        cp1, cp2, cp3 = st.columns(3)
        with cp1: v_p_carga    = st.text_input("Presión de Carga (bar)", "6.4")
        with cp2: v_p_descarga = st.text_input("Presión de Descarga (bar)", "6.8")
        with cp3: v_t_salida   = st.text_input("Temp. Salida Elemento (°C)", "80")

        st.subheader("📝 Contenido del Informe")
        st.caption("Pre-llenado automático según TAG y tipo de mantención — puedes editar antes de generar.")

        tpl = get_plantilla(tipo_mant, mod_aut, tag_sel, loc_aut, area_aut,
                            v_p_carga, v_p_descarga, v_t_salida)

        alcance_manual     = st.text_area("Alcance de la Intervención", value=tpl["alcance"],      height=80)
        actividades_manual = st.text_area("Actividades Ejecutadas",     value=tpl["actividades"],  height=230)
        condicion_manual   = st.text_area("Condición Final",            value=tpl["condicion"],    height=100)
        rec_manual         = st.text_area("Recomendaciones",            value=tpl["recomendaciones"], height=100)

        st.divider()
        enviar = st.form_submit_button("💾 GUARDAR Y GENERAR REPORTE", use_container_width=True)

    if enviar:
        TEMPLATE_PATH = "templates/InformeInspección.docx"
        if not os.path.exists(TEMPLATE_PATH):
            st.error(f"❌ Template Word no encontrado en '{TEMPLATE_PATH}'.")
            st.stop()
        try:
            doc = DocxTemplate(TEMPLATE_PATH)
            meses     = ["enero","febrero","marzo","abril","mayo","junio",
                         "julio","agosto","septiembre","octubre","noviembre","diciembre"]
            fecha_txt = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"

            contexto = {
                "fecha":                  fecha_txt,
                "cliente_contact":        cliente_cont,
                "alcanze_intervencion":   alcance_manual,
                "operaciones_dinamicas":  actividades_manual,
                "p_carga":                v_p_carga,
                "p_descarga":             v_p_descarga,
                "temp_salida":            v_t_salida,
                "estado_entrega":         condicion_manual,
                "recomendaciones":        rec_manual,
                "proxima_visita":         tpl["proxima_visita"],
                "tecnico_1":              tec1,
                "tecnico_2":              tec2,
                "act_1":                  "Mantenimiento",
                "h_1":                    "8",
                "h_2":                    "8",
                "equipo_modelo":          mod_aut,
                "serie":                  ser_aut,
                "horas_marcha":           f"{h_marcha} Hrs.",
                "tipo_orden":             tpl["tipo_orden_txt"],
                "horas_totales_despues":  h_marcha,
                "horas_carga_despues":    h_carga,
                "tag":                    tag_sel,
            }

            doc.render(contexto)
            output = io.BytesIO()
            doc.save(output)

            nuevo_reg = pd.DataFrame(
                [[fecha_sel, tag_sel, h_marcha, h_carga, tec1, tec2, cliente_cont, tipo_mant]],
                columns=COLUMNAS
            )
            st.session_state["df_historial"] = pd.concat(
                [st.session_state["df_historial"], nuevo_reg], ignore_index=True
            )
            guardar_datos(st.session_state["df_historial"])

            st.success(f"✅ Informe generado: {tpl['tipo_orden_txt']} — {tag_sel} — {fecha_txt}")
            st.download_button(
                "📥 DESCARGAR REPORTE",
                output.getvalue(),
                f"Informe_{tipo_mant}_{tag_sel}_{fecha_sel}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"❌ Error al procesar el Word: {e}")
            logger.error(f"Error generando reporte: {e}")

with tab2:
    st.subheader("🛠️ Historial de Mantenciones")

    fc1, fc2 = st.columns(2)
    with fc1:
        filtro_tag  = st.selectbox("Filtrar por TAG",  ["Todos"] + list(equipos_db.keys()))
    with fc2:
        filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "INSPECCIÓN", "P1", "P2", "P3"])

    df_view = st.session_state["df_historial"].copy()
    if filtro_tag  != "Todos": df_view = df_view[df_view["TAG"]  == filtro_tag]
    if filtro_tipo != "Todos": df_view = df_view[df_view["Tipo"] == filtro_tipo]

    df_editado = st.data_editor(df_view, num_rows="dynamic", use_container_width=True, key="editor")

    cs1, cs2 = st.columns([1, 5])
    with cs1:
        if st.button("💾 Guardar cambios"):
            st.session_state["df_historial"] = df_editado
            if guardar_datos(df_editado):
                st.success("✅ Historial guardado.")
    with cs2:
        if st.button("🔄 Recargar"):
            st.session_state["df_historial"] = cargar_datos()
            st.rerun()
