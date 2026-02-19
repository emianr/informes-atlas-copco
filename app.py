import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
from supabase import create_client
import io
import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Atlas Copco Tracker - Spence", layout="wide")

@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

def cargar_historial():
    try:
        res = supabase.table("historial").select("*").order("creado_en", desc=True).execute()
        return res.data if res.data else []
    except Exception as e:
        st.warning(f"⚠️ No se pudo cargar el historial: {e}")
        return []

def guardar_registro(datos):
    try:
        res = supabase.table("historial").insert(datos).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        st.error(f"❌ Error guardando registro: {e}")
        return None

def guardar_informe(historial_id, nombre, archivo_bytes):
    try:
        path = f"informes/{historial_id}/{nombre}"
        supabase.storage.from_("informes").upload(
            path, archivo_bytes,
            {"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        )
        supabase.table("informes").insert({
            "historial_id": historial_id,
            "nombre": nombre,
            "ruta": path
        }).execute()
        return path
    except Exception as e:
        logger.error(f"Error guardando informe: {e}")
        return None

def obtener_url_informe(ruta):
    try:
        res = supabase.storage.from_("informes").create_signed_url(ruta, 3600)
        return res.get("signedURL")
    except Exception as e:
        logger.error(f"Error obteniendo URL: {e}")
        return None

def eliminar_registro(id):
    try:
        supabase.table("historial").delete().eq("id", id).execute()
        return True
    except Exception as e:
        st.error(f"❌ Error eliminando: {e}")
        return False

equipos_db = {
    "70-GC-013":  ["GA 132", "AIF095296", "descarga acido",      "area humeda"],
    "70-GC-014":  ["GA 132", "AIF095297", "descarga acido",      "area humeda"],
    "050-GD-001": ["GA 45",  "API542705", "planta sx",           "area humeda"],
    "050-GD-002": ["GA 45",  "API542706", "planta sx",           "area humeda"],
    "050-GC-003": ["ZT 37",  "API791692", "planta sx",           "area humeda"],
    "050-GC-004": ["ZT 37",  "API791693", "planta sx",           "area humeda"],
    "050-CD-001": ["CD 80+", "API095825", "planta sx",           "area humeda"],
    "050-CD-002": ["CD 80+", "API095826", "planta sx",           "area humeda"],
    "050-GC-015": ["GA 30",  "API501440", "planta borra",        "area humeda"],
    "65-GC-011":  ["GA 250", "APF253581", "patio estanques",     "area humeda"],
    "65-GC-009":  ["GA 250", "APF253608", "patio estanques",     "area humeda"],
    "65-GD-011":  ["CD 630", "WXF300015", "patio estanques",     "area humeda"],
    "65-GD-012":  ["CD 630", "WXF300016", "patio estanques",     "area humeda"],
    "35-GC-006":  ["GA 250", "AIF095420", "chancado secundario", "area seca"],
    "35-GC-007":  ["GA 250", "AIF095421", "chancado secundario", "area seca"],
    "35-GC-008":  ["GA 250", "AIF095302", "chancado secundario", "area seca"],
    "20-GC-004":  ["GA 37",  "AII390776", "mina",                "mina"],
    "20-GC-001":  ["GA 75",  "AII482673", "truck shop",          "mina"],
    "20-GC-002":  ["GA 75",  "AII482674", "truck shop",          "mina"],
    "20-GC-003":  ["GA 90",  "AIF095178", "truck shop",          "mina"],
    "TALLER-01":  ["GA 18",  "API335343", "taller",              "area seca"],
}

def get_plantilla(tipo, modelo, tag, ubicacion, area, p_carga, p_descarga, temp_salida):
    verbo = "inspeccion" if tipo == "INSPECCION" else ("mantencion mayor" if tipo == "P3" else "mantencion")
    alcance = (
        f"Se realizo {verbo} a equipo compresor {modelo} con identificacion TAG {tag} "
        f"de {area}, {ubicacion}, conforme a procedimientos internos y buenas practicas de mantenimiento."
    )
    estado_op = (
        f"- Estado operacional: Verificacion de parametros de operacion "
        f"(Presion de carga: {p_carga} bar / descarga: {p_descarga} bar) "
        f"y temperatura de salida del elemento ({temp_salida} C)."
    )

    if tipo == "INSPECCION":
        actividades = (
            "- Inspeccion de fugas: Revision visual de circuitos de aire y aceite.\n"
            "- Nivel de lubricante: Chequeo del nivel de aceite por medio del visor.\n"
            "- Revision enfriador: Inspeccion visual en enfriador de aire/aceite.\n"
            "- Revision general: Se verifica estado de filtros de aire, valvula de corte y lineas de aire.\n"
            "- Monitoreo de controlador: Validacion de parametros de operacion, realizando prueba en carga/descarga del equipo.\n"
            f"{estado_op}\n"
            "- Purga condensado: Drenado de condensado del equipo."
        )
        condicion = "El equipo se encuentra funcionando bajo parametros estables, con nivel de aceite dentro del rango establecido y con filtros sin saturacion."
        recomendaciones = "- Nota tecnica: El equipo supera las horas recomendadas por fabrica para mantenimiento mayor, se recomienda enviar a overhaul o reemplazar por equipo nuevo."
        proxima_visita = "El proximo servicio recomendado es Inspeccion estimada requerida"
        tipo_orden_txt = "INSPECCION"

    elif tipo == "P1":
        actividades = (
            "- Inspeccion de fugas: Revision visual de circuitos de aire/aceite.\n"
            "- Limpieza general: Limpieza general de equipo compresor.\n"
            "- Verificacion de lubricante: Revision por visor de nivel optimo.\n"
            "- Chequeo enfriador: Inspeccion visual en enfriador de aire/aceite.\n"
            "- Cambio filtros: Cambio de filtros de aire/aceite.\n"
            "- Monitoreo de controlador: Validacion de parametros de operacion, realizando prueba en carga/descarga del equipo.\n"
            f"{estado_op}"
        )
        condicion = "El equipo se encuentra funcionando bajo parametros estables, nivel de aceite dentro del rango establecido y con filtros sin saturacion."
        recomendaciones = (
            "- Plan de mantenimiento: Mantener frecuencia de inspeccion y drenado de condensados segun plan preventivo vigente.\n"
            "- Control ambiental: Considerar limpieza preventiva del entorno y radiadores."
        )
        proxima_visita = "El proximo servicio recomendado es P2 estimada requerida"
        tipo_orden_txt = "Mantencion P1"

    elif tipo == "P2":
        actividades = (
            "- Inspeccion de fugas: Revision visual de circuitos de aire/aceite.\n"
            "- Limpieza general: Limpieza general de equipo compresor.\n"
            "- Cambio de lubricante: Se realiza drenado con cambio de aceite y revision por visor.\n"
            "- Chequeo enfriador: Inspeccion visual en enfriador de aire/aceite.\n"
            "- Cambio filtros: Cambio de filtros de aire/aceite.\n"
            "- Monitoreo de controlador: Validacion de parametros de operacion, realizando prueba en carga/descarga del equipo.\n"
            f"{estado_op}"
        )
        condicion = (
            "El equipo se encuentra funcionando bajo parametros estables, nivel de aceite dentro del rango establecido y con filtros sin saturacion.\n"
            "Se detectan enfriadores saturados por contaminacion, pero sin fugas visibles."
        )
        recomendaciones = (
            "- Plan de mantenimiento: Mantener frecuencia de inspeccion y drenado de condensados segun plan preventivo vigente.\n"
            "- Control ambiental: Considerar limpieza preventiva del entorno y radiadores."
        )
        proxima_visita = "El proximo servicio recomendado es P3 estimada requerida"
        tipo_orden_txt = "Mantencion P2"

    else:  # P3
        actividades = (
            "- Inspeccion de fugas: Revision visual de circuitos de aire/aceite.\n"
            "- Limpieza profunda: Limpieza profunda de enfriadores y componentes internos.\n"
            "- Cambio de lubricante: Drenado completo con cambio de aceite y revision por visor.\n"
            "- Cambio filtros: Cambio de filtros de aire, aceite y separador.\n"
            "- Engrase rodamientos: Engrase de rodamientos del motor electrico.\n"
            "- Revision valvulas: Inspeccion y limpieza de valvula de minima y anti-retorno.\n"
            "- Monitoreo de controlador: Validacion de parametros de operacion, realizando prueba en carga/descarga del equipo.\n"
            f"{estado_op}"
        )
        condicion = "El equipo se encuentra en optimas condiciones tras mantencion mayor. Parametros en rango nominal, nivel de aceite correcto y filtros nuevos instalados."
        recomendaciones = (
            "- Plan de mantenimiento: Continuar con plan de mantenimiento preventivo.\n"
            "- Proxima intervencion: Programar proxima mantencion mayor segun horas de operacion del equipo."
        )
        proxima_visita = "El proximo servicio recomendado es Inspeccion estimada requerida"
        tipo_orden_txt = "Mantencion P3"

    return {
        "alcance": alcance, "actividades": actividades,
        "condicion": condicion, "recomendaciones": recomendaciones,
        "proxima_visita": proxima_visita, "tipo_orden_txt": tipo_orden_txt,
    }

# ─── UI ───
st.title("Atlas Copco Tracker - Spence")
tab1, tab2, tab3 = st.tabs(["Generar Informe", "Historial", "Informes Guardados"])

with tab1:
    col_tag, col_tipo = st.columns(2)
    with col_tag:
        tag_sel = st.selectbox("TAG del equipo", list(equipos_db.keys()))
    with col_tipo:
        tipo_mant = st.selectbox("Tipo de Mantencion", ["INSPECCION", "P1", "P2", "P3"])

    mod_aut, ser_aut, loc_aut, area_aut = equipos_db[tag_sel]
    st.info(f"Equipo: {mod_aut} | Serie: {ser_aut} | Ubicacion: {loc_aut} | Area: {area_aut}")

    try:
        ultimo_res = supabase.table("historial").select("*").eq("tag", tag_sel).order("creado_en", desc=True).limit(1).execute()
        ultimo = ultimo_res.data[0] if ultimo_res.data else None
    except:
        ultimo = None

    h_sug       = int(ultimo["horas_marcha"]) if ultimo else 0
    h_sug_carga = int(ultimo["horas_carga"])  if ultimo else 0
    if ultimo:
        st.caption(f"Ultimo registro: {ultimo['fecha']} — {ultimo['tipo']} — {h_sug} hrs marcha")

    st.divider()

    with st.form("editor_informe"):
        st.subheader("Datos Generales")
        c1, c2 = st.columns(2)
        with c1:
            fecha_sel    = st.date_input("Fecha de atencion", datetime.now())
            tec1         = st.text_input("Tecnico 1 (Lider)", st.secrets.get("tec1_default", "Ignacio Morales"))
        with c2:
            cliente_cont = st.text_input("Contacto Cliente", st.secrets.get("contacto_default", "Pamela Tapia"))
            tec2         = st.text_input("Tecnico 2",        st.secrets.get("tec2_default", "Emian Sanchez"))

        st.subheader("Horas del Equipo")
        ch1, ch2 = st.columns(2)
        with ch1: h_marcha = st.number_input("Horas Totales Marcha", value=h_sug, step=1)
        with ch2: h_carga  = st.number_input("Horas Carga",          value=h_sug_carga, step=1)

        st.subheader("Parametros Operacionales")
        cp1, cp2, cp3 = st.columns(3)
        with cp1: v_p_carga    = st.text_input("Presion de Carga (bar)", "6.4")
        with cp2: v_p_descarga = st.text_input("Presion de Descarga (bar)", "6.8")
        with cp3: v_t_salida   = st.text_input("Temp. Salida Elemento (C)", "80")

        st.subheader("Contenido del Informe")
        st.caption("Pre-llenado automatico segun TAG y tipo — puedes editar antes de generar.")

        tpl = get_plantilla(tipo_mant, mod_aut, tag_sel, loc_aut, area_aut,
                            v_p_carga, v_p_descarga, v_t_salida)

        alcance_manual     = st.text_area("Alcance de la Intervencion", value=tpl["alcance"],         height=80)
        actividades_manual = st.text_area("Actividades Ejecutadas",     value=tpl["actividades"],     height=230)
        condicion_manual   = st.text_area("Condicion Final",            value=tpl["condicion"],       height=100)
        rec_manual         = st.text_area("Recomendaciones",            value=tpl["recomendaciones"], height=100)

        st.divider()
        enviar = st.form_submit_button("GUARDAR Y GENERAR REPORTE", use_container_width=True)

    if enviar:
        TEMPLATE_PATH = "InformeInspección.docx"
        if not os.path.exists(TEMPLATE_PATH):
            st.error(f"Template Word no encontrado: '{TEMPLATE_PATH}'")
            st.stop()
        try:
            doc   = DocxTemplate(TEMPLATE_PATH)
            meses = ["enero","febrero","marzo","abril","mayo","junio",
                     "julio","agosto","septiembre","octubre","noviembre","diciembre"]
            fecha_txt = f"{fecha_sel.day} de {meses[fecha_sel.month - 1]} de {fecha_sel.year}"

            contexto = {
                "fecha": fecha_txt, "cliente_contact": cliente_cont,
                "alcanze_intervencion": alcance_manual,
                "operaciones_dinamicas": actividades_manual,
                "p_carga": v_p_carga, "p_descarga": v_p_descarga, "temp_salida": v_t_salida,
                "estado_entrega": condicion_manual, "recomendaciones": rec_manual,
                "proxima_visita": tpl["proxima_visita"],
                "tecnico_1": tec1, "tecnico_2": tec2,
                "act_1": "Mantenimiento", "h_1": "8", "h_2": "8",
                "equipo_modelo": mod_aut, "serie": ser_aut,
                "horas_marcha": f"{h_marcha} Hrs.",
                "tipo_orden": tpl["tipo_orden_txt"],
                "horas_totales_despues": h_marcha,
                "horas_carga_despues": h_carga,
                "tag": tag_sel,
            }
            doc.render(contexto)
            output = io.BytesIO()
            doc.save(output)
            archivo_bytes  = output.getvalue()
            nombre_archivo = f"Informe_{tipo_mant}_{tag_sel}_{fecha_sel}.docx"

            with st.spinner("Guardando en base de datos..."):
                registro_id = guardar_registro({
                    "fecha": str(fecha_sel), "tag": tag_sel, "tipo": tipo_mant,
                    "horas_marcha": h_marcha, "horas_carga": h_carga,
                    "tecnico_1": tec1, "tecnico_2": tec2, "contacto": cliente_cont,
                    "p_carga": v_p_carga, "p_descarga": v_p_descarga, "temp_salida": v_t_salida,
                    "alcance": alcance_manual, "actividades": actividades_manual,
                    "condicion": condicion_manual, "recomendaciones": rec_manual,
                })
                if registro_id:
                    guardar_informe(registro_id, nombre_archivo, archivo_bytes)

            st.success(f"Guardado — {tpl['tipo_orden_txt']} | {tag_sel} | {fecha_txt}")
            st.download_button(
                "DESCARGAR REPORTE", archivo_bytes, nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error al procesar: {e}")
            logger.error(f"Error: {e}")

with tab2:
    st.subheader("Historial de Mantenciones")

    fc1, fc2, fc3 = st.columns(3)
    with fc1: filtro_tag  = st.selectbox("Filtrar por TAG",  ["Todos"] + list(equipos_db.keys()), key="f_tag")
    with fc2: filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos","INSPECCION","P1","P2","P3"], key="f_tipo")
    with fc3:
        if st.button("Actualizar"): st.rerun()

    datos = cargar_historial()
    if filtro_tag  != "Todos": datos = [d for d in datos if d["tag"]  == filtro_tag]
    if filtro_tipo != "Todos": datos = [d for d in datos if d["tipo"] == filtro_tipo]

    if datos:
        df = pd.DataFrame(datos)[["id","fecha","tag","tipo","horas_marcha","horas_carga","tecnico_1","tecnico_2","contacto"]]
        df.columns = ["ID","Fecha","TAG","Tipo","Hrs Marcha","Hrs Carga","Tecnico 1","Tecnico 2","Contacto"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        with st.expander("Eliminar registro"):
            id_borrar = st.number_input("ID del registro a eliminar", min_value=1, step=1)
            if st.button("Eliminar", type="primary"):
                if eliminar_registro(id_borrar):
                    st.success(f"Registro {id_borrar} eliminado.")
                    st.rerun()
    else:
        st.info("No hay registros aun. Genera tu primer informe.")

with tab3:
    st.subheader("Informes Word Guardados")
    if st.button("Actualizar lista", key="act_inf"): st.rerun()

    try:
        informes_res = supabase.table("informes").select("*, historial(fecha, tag, tipo)").order("creado_en", desc=True).execute()
        informes = informes_res.data if informes_res.data else []
    except Exception as e:
        informes = []
        st.warning(f"No se pudieron cargar los informes: {e}")

    if informes:
        for inf in informes:
            hist = inf.get("historial", {}) or {}
            col_a, col_b, col_c, col_d = st.columns([3, 1, 2, 1])
            with col_a: st.write(f"{inf['nombre']}")
            with col_b: st.write(hist.get("fecha", "-"))
            with col_c: st.write(f"{hist.get('tag','-')} — {hist.get('tipo','-')}")
            with col_d:
                url = obtener_url_informe(inf["ruta"])
                if url: st.link_button("Descargar", url)
            st.divider()
    else:
        st.info("No hay informes guardados aun.")
