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
        st.warning(f"No se pudo cargar el historial: {e}")
        return []

def guardar_registro(datos):
    try:
        res = supabase.table("historial").insert(datos).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        st.error(f"Error guardando registro: {e}")
        return None

def guardar_informe(historial_id, nombre, archivo_bytes):
    try:
        path = f"informes/{historial_id}/{nombre}"
        supabase.storage.from_("informes").upload(
            path, archivo_bytes,
            {"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        )
        supabase.table("informes").insert({
            "historial_id": historial_id, "nombre": nombre, "ruta": path
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
        st.error(f"Error eliminando: {e}")
        return False

equipos_lista = [
    ["API515199","GA75","211-GC-001","CHANCADO PRIMARIO","OPERATIVO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["API616532","GA75","211-GC-002","CHANCADO PRIMARIO","OPERATIVO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["WUX409578","G132","318-GC-001","CHANCADO SECUNDARIO","OPERATIVO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["WUX409516","G132","318-GC-002","CHANCADO SECUNDARIO","OPERATIVO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["WUX409537","G132","318-GC-003","CHANCADO SECUNDARIO","OPERATIVO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["---","OSC1200","318-OSC-001","CHANCADO SECUNDARIO","OPERATIVO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["APIS44785601","GA55","344-GC-001","FISEMO","OPERATIVO","ATLASCOPCO","MOLIBDENO","SULFURO"],
    ["API624285","GA90","346-GC-001","MOLIBDENO","OPERATIVO","ATLASCOPCO","MOLIBDENO","SULFURO"],
    ["API624286","GA90","346-GC-002","MOLIBDENO","OPERATIVO","ATLASCOPCO","MOLIBDENO","SULFURO"],
    ["CAI878332","GA15FF","LAB-GC-001","LABORATORIO","OPERATIVO","ATLASCOPCO","LABORATORIO","SULFURO"],
    ["ITJ182547","GA15P","LAB-GC-002","LABORATORIO","OPERATIVO","ATLASCOPCO","LABORATORIO","SULFURO"],
    ["API310344","GA30","411-GC-001","FLOCULANTE","OPERATIVO","ATLASCOPCO","FLOCULANTE","SULFURO"],
    ["API323529","GA30","411-GC-501","FLOCULANTE","OPERATIVO","ATLASCOPCO","FLOCULANTE","SULFURO"],
    ["APF135735","GA90+","122-GC-001","TALLER DE CAMIONES","OPERATIVO","ATLASCOPCO","TALLER DE CAMIONES","SULFURO"],
    ["APF135800","GA90+","122-GC-002","TALLER DE CAMIONES","OPERATIVO","ATLASCOPCO","TALLER DE CAMIONES","SULFURO"],
    ["API690916","CD185","122-GD-002","TALLER DE CAMIONES","OPERATIVO","ATLASCOPCO","TALLER DE CAMIONES","SULFURO"],
    ["APF143254","GA315","335-GC-001","MOLIENDA","OPERATIVO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["APF143370","GA315","335-GC-002","MOLIENDA","OPERATIVO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["APF143685","GA315","335-GC-003","MOLIENDA","OPERATIVO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["APF226020","CD330+","335-GD-004","MOLIENDA","OPERATIVO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["APF143377","GA500","324-GC-001","FLOTACION","OPERATIVO","ATLASCOPCO","FLOTACION","SULFURO"],
    ["APF143426","GA500","324-GC-002","FLOTACION","OPERATIVO","ATLASCOPCO","FLOTACION","SULFURO"],
    ["CAI721030","GA7FF","CM871A1-1","OSMOSIS","OPERATIVO","ATLASCOPCO","RO","SULFURO"],
    ["APF209860","ZE2","ZE-GC-001","OSMOSIS","OPERATIVO","ATLASCOPCO","RO","SULFURO"],
    ["API080552","BD250","335-GD-001","MOLIENDA","FUERA DE SERVICIO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["API080554","BD250","335-GD-002","MOLIENDA","FUERA DE SERVICIO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["APF193048","BD550","335-GD-601","MOLIENDA","FUERA DE SERVICIO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["APF207186","CD150+","346-GD-001","MOLIBDENO","FUERA DE SERVICIO","ATLASCOPCO","FLOTACION MOLIBDENO","SULFURO"],
    ["APF135734","GA110+","122-GC-003","TALLER DE CAMIONES","FUERA DE SERVICIO","ATLASCOPCO","TALLER DE CAMIONES","SULFURO"],
    ["API690915","CD300","122-GD-001","TALLER DE CAMIONES","FUERA DE SERVICIO","ATLASCOPCO","TALLER DE CAMIONES","SULFURO"],
    ["UTF123UQ1","BD630","318-GD-001","CHANCADO SECUNDARIO","FUERA DE SERVICIO","ATLASCOPCO","CONMINUCION","SULFURO"],
    ["API623258","GA90","3210-C2-1001","CHANCADO PRIMARIO","OPERATIVO","ATLASCOPCO","OXE","OXE"],
    ["API623260","GA90","3210-C1-1001","CHANCADO PRIMARIO","OPERATIVO","ATLASCOPCO","OXE","OXE"],
    ["API543531","GA45","3230-C3-2001","HARNERO SECUNDARIO","OPERATIVO","ATLASCOPCO","OXE","OXE"],
    ["API543590","GA30+","3230-C4-3001","CHANCADO SECUNDARIO","OPERATIVO","ATLASCOPCO","OXE","OXE"],
    ["API623259","GA90","3240-C5-4001","HARNERO TERCIARIO","OPERATIVO","ATLASCOPCO","OXE","OXE"],
    ["API543530","GA45","3240-C6-5001","CHANCADO TERCIARIO","OPERATIVO","ATLASCOPCO","OXE","OXE"],
    ["API329314","GA15+","3240-C7-6001","SILO REFINO","OPERATIVO","ATLASCOPCO","OXE","OXE"],
    ["CAI884389","GX4","3300-C7-600","AGLOMERADO","OPERATIVO","ATLASCOPCO","OXE","OXE"],
    ["API629823","GA55","200-GC-001","CHANCADO PRIMARIO","OPERATIVO","ATLASCOPCO","AREA SECA","OXIDO"],
    ["API629822","GA55","200-GC-002","CHANCADO PRIMARIO","OPERATIVO","ATLASCOPCO","AREA SECA","OXIDO"],
    ["API629825","GA55","220-GC-001","CHANCADO SECUNDARIO","OPERATIVO","ATLASCOPCO","AREA SECA","OXIDO"],
    ["API629834","GA55","220-GC-002","CHANCADO SECUNDARIO","OPERATIVO","ATLASCOPCO","AREA SECA","OXIDO"],
    ["API629826","GA90+","220-GC-003","CHANCADO SECUNDARIO","OPERATIVO","ATLASCOPCO","AREA SECA","OXIDO"],
    ["APF235378","CD630","220-GD-001","CHANCADO SECUNDARIO","OPERATIVO","ATLASCOPCO","AREA SECA","OXIDO"],
    ["API333775","GA30","AGL-GC-001","AGLOMERADO","OPERATIVO","ATLASCOPCO","AREA SECA","OXIDO"],
    ["API334806","GA30","AGL-GC-002","AGLOMERADO","OPERATIVO","ATLASCOPCO","AREA SECA","OXIDO"],
    ["1148","SM15","OSM-GC-001","OSMOSIS","OPERATIVO","KAESER","OSMOSIS","OXIDO"],
    ["ITJ242366","G11P","OSM-GC-004","OSMOSIS","OPERATIVO","ATLASCOPCO","OSMOSIS","OXIDO"],
    ["APF227050","GA90+","TCN-GC-002","TALLER DE CAMIONES NORTE","OPERATIVO","ATLASCOPCO","TALLER DE CAMIONES","OXIDO"],
    ["API249242","CD35","MNE-GD-001","MARTILLO NEUMATICO SX","OPERATIVO","ATLASCOPCO","AREA HUMEDA","OXIDO"],
    ["ITJ242345","G11","600-DP-002","MARTILLO NEUMATICO SX","OPERATIVO","ATLASCOPCO","AREA HUMEDA","OXIDO"],
    ["ITJ242285","GA18","CAL-GC-001","CALENTADORES SX","OPERATIVO","ATLASCOPCO","AREA HUMEDA","OXIDO"],
    ["ITJ242306","GA15","ENZ-GC-001","ENZUNCHADORA SX","OPERATIVO","ATLASCOPCO","AREA HUMEDA","OXIDO"],
    ["ITJ242307","GA18","MDC-GC-001","MAQUINA DESPEGADORA SX","OPERATIVO","ATLASCOPCO","AREA HUMEDA","OXIDO"],
    ["API587024","GA37","POST-GC-001","POST-DECANTADOR SX","OPERATIVO","ATLASCOPCO","AREA HUMEDA","OXIDO"],
    ["ITR1354539","LF3FF","LAB-GC-004","LABORATORIO","OPERATIVO","ATLASCOPCO","LABORATORIO","OXIDO"],
    ["ITJ242308","GA18P","LAB-GC-003","LABORATORIO","OPERATIVO","ATLASCOPCO","LABORATORIO","OXIDO"],
    ["1118-6854188","BSD65","DES-GC-002","DESCARGA DE ACIDO","OPERATIVO","KAESER","DESCARGA DE ACIDO","OXIDO"],
    ["1120-6867842","BSD65","DES-GC-001","DESCARGA DE ACIDO","OPERATIVO","KAESER","DESCARGA DE ACIDO","OXIDO"],
    ["AII661966","GX18","LAB-GC-006","LABORATORIO","FUERA DE SERVICIO","ATLASCOPCO","LABORATORIO","OXIDO"],
    ["---","FX1AD","LAB-GC-005","LABORATORIO","OPERATIVO","ATLASCOPCO","LABORATORIO",""],
    ["349016/0334","RA-086","TCN-GC-001","TALLER DE CAMIONES NORTE","OPERATIVO","COMP AIR","",""],
    ["APF155559","ZS75+VSD","SOPLADOR-1","SX","OPERATIVO","ATLASCOPCO","AREA HUMEDA HIDRO",""],
    ["APFS99645701","GR200","621-GC-001","MUELLE","OPERATIVO","ATLASCOPCO","MUELLE","MUELLE"],
    ["APF143505","GA355","621-GC-003","MUELLE","OPERATIVO","ATLASCOPCO","MUELLE","MUELLE"],
    ["APFS99645702","GA355","621-GC-004","MUELLE","OPERATIVO","ATLASCOPCO","MUELLE","MUELLE"],
    ["APFS99645702","GR200","621-GC-002","MUELLE","OPERATIVO","ATLASCOPCO","MUELLE","MUELLE"],
    ["3019853","2475","OSM-GC-002","OSMOSIS","OPERATIVO","INGERSOLLRAND","OSMOSIS",""],
    ["CAI721652","GA5FF","OSM-GC-005","OSMOSIS","OPERATIVO","ATLASCOPCO","OSMOSIS",""],
    ["3019858","2475","OSM-GC-003","OSMOSIS","FUERA DE SERVICIO","INGERSOLL RAND","OSMOSIS",""],
    ["1045","CSV150","641-DC-003M","MUELLE","FUERA DE SERVICIO","KAESER","MUELLE","MUELLE"],
]

equipos_db = {e[2]: [e[1], e[0], e[3], e[6], e[7]] for e in equipos_lista}

def get_plantilla(tipo, modelo, tag, subarea, area, p_carga, p_descarga, temp_salida):
    verbo = "inspeccion" if tipo == "INSPECCION" else ("mantencion mayor" if tipo == "P3" else "mantencion")
    alcance = (f"Se realizo {verbo} a equipo compresor {modelo} con identificacion TAG {tag} "
               f"de {area}, {subarea}, conforme a procedimientos internos y buenas practicas de mantenimiento.")
    estado_op = (f"- Estado operacional: Verificacion de parametros de operacion "
                 f"(Presion de carga: {p_carga} bar / descarga: {p_descarga} bar) "
                 f"y temperatura de salida del elemento ({temp_salida} C).")
    if tipo == "INSPECCION":
        act = ("- Inspeccion de fugas: Revision visual de circuitos de aire y aceite.\n"
               "- Nivel de lubricante: Chequeo del nivel de aceite por medio del visor.\n"
               "- Revision enfriador: Inspeccion visual en enfriador de aire/aceite.\n"
               "- Revision general: Se verifica estado de filtros de aire, valvula de corte y lineas de aire.\n"
               "- Monitoreo de controlador: Validacion de parametros de operacion, realizando prueba en carga/descarga del equipo.\n"
               f"{estado_op}\n- Purga condensado: Drenado de condensado del equipo.")
        cond = "El equipo se encuentra funcionando bajo parametros estables, con nivel de aceite dentro del rango establecido y con filtros sin saturacion."
        rec  = "- Nota tecnica: El equipo supera las horas recomendadas por fabrica para mantenimiento mayor, se recomienda enviar a overhaul o reemplazar por equipo nuevo."
        pv   = "El proximo servicio recomendado es Inspeccion estimada requerida"
        tot  = "INSPECCION"
    elif tipo == "P1":
        act = ("- Inspeccion de fugas: Revision visual de circuitos de aire/aceite.\n"
               "- Limpieza general: Limpieza general de equipo compresor.\n"
               "- Verificacion de lubricante: Revision por visor de nivel optimo.\n"
               "- Chequeo enfriador: Inspeccion visual en enfriador de aire/aceite.\n"
               "- Cambio filtros: Cambio de filtros de aire/aceite.\n"
               "- Monitoreo de controlador: Validacion de parametros de operacion, realizando prueba en carga/descarga del equipo.\n"
               f"{estado_op}")
        cond = "El equipo se encuentra funcionando bajo parametros estables, nivel de aceite dentro del rango establecido y con filtros sin saturacion."
        rec  = ("- Plan de mantenimiento: Mantener frecuencia de inspeccion y drenado de condensados segun plan preventivo vigente.\n"
                "- Control ambiental: Considerar limpieza preventiva del entorno y radiadores.")
        pv   = "El proximo servicio recomendado es P2 estimada requerida"
        tot  = "Mantencion P1"
    elif tipo == "P2":
        act = ("- Inspeccion de fugas: Revision visual de circuitos de aire/aceite.\n"
               "- Limpieza general: Limpieza general de equipo compresor.\n"
               "- Cambio de lubricante: Se realiza drenado con cambio de aceite y revision por visor.\n"
               "- Chequeo enfriador: Inspeccion visual en enfriador de aire/aceite.\n"
               "- Cambio filtros: Cambio de filtros de aire/aceite.\n"
               "- Monitoreo de controlador: Validacion de parametros de operacion, realizando prueba en carga/descarga del equipo.\n"
               f"{estado_op}")
        cond = ("El equipo se encuentra funcionando bajo parametros estables, nivel de aceite dentro del rango establecido y con filtros sin saturacion.\n"
                "Se detectan enfriadores saturados por contaminacion, pero sin fugas visibles.")
        rec  = ("- Plan de mantenimiento: Mantener frecuencia de inspeccion y drenado de condensados segun plan preventivo vigente.\n"
                "- Control ambiental: Considerar limpieza preventiva del entorno y radiadores.")
        pv   = "El proximo servicio recomendado es P3 estimada requerida"
        tot  = "Mantencion P2"
    else:
        act = ("- Inspeccion de fugas: Revision visual de circuitos de aire/aceite.\n"
               "- Limpieza profunda: Limpieza profunda de enfriadores y componentes internos.\n"
               "- Cambio de lubricante: Drenado completo con cambio de aceite y revision por visor.\n"
               "- Cambio filtros: Cambio de filtros de aire, aceite y separador.\n"
               "- Engrase rodamientos: Engrase de rodamientos del motor electrico.\n"
               "- Revision valvulas: Inspeccion y limpieza de valvula de minima y anti-retorno.\n"
               "- Monitoreo de controlador: Validacion de parametros de operacion, realizando prueba en carga/descarga del equipo.\n"
               f"{estado_op}")
        cond = "El equipo se encuentra en optimas condiciones tras mantencion mayor. Parametros en rango nominal, nivel de aceite correcto y filtros nuevos instalados."
        rec  = ("- Plan de mantenimiento: Continuar con plan de mantenimiento preventivo.\n"
                "- Proxima intervencion: Programar proxima mantencion mayor segun horas de operacion del equipo.")
        pv   = "El proximo servicio recomendado es Inspeccion estimada requerida"
        tot  = "Mantencion P3"
    return {"alcance": alcance, "actividades": act, "condicion": cond,
            "recomendaciones": rec, "proxima_visita": pv, "tipo_orden_txt": tot}

# ── UI ──
st.title("Atlas Copco Tracker - Spence")
tab0, tab1, tab2, tab3 = st.tabs(["Equipos", "Generar Informe", "Historial", "Informes Guardados"])

with tab0:
    st.subheader("Panel de Equipos - Centinela")
    total     = len(equipos_lista)
    operativo = sum(1 for e in equipos_lista if e[4] == "OPERATIVO")
    fuera     = total - operativo
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Equipos", total)
    m2.metric("Operativos", operativo, delta=f"{round(operativo/total*100)}%")
    m3.metric("Fuera de Servicio", fuera, delta=f"-{fuera}", delta_color="inverse")
    st.divider()

    f1, f2, f3 = st.columns(3)
    with f1: filtro_ubi    = st.selectbox("Ubicacion", ["Todas"] + sorted(set(e[7] for e in equipos_lista if e[7])))
    with f2: filtro_area   = st.selectbox("Area",      ["Todas"] + sorted(set(e[6] for e in equipos_lista if e[6])))
    with f3: filtro_estado = st.selectbox("Estado",    ["Todos", "OPERATIVO", "FUERA DE SERVICIO"])

    df_eq = pd.DataFrame(equipos_lista, columns=["Serie","Modelo","TAG","Subarea","Estado","Marca","Area","Ubicacion"])
    if filtro_ubi    != "Todas": df_eq = df_eq[df_eq["Ubicacion"] == filtro_ubi]
    if filtro_area   != "Todas": df_eq = df_eq[df_eq["Area"]      == filtro_area]
    if filtro_estado != "Todos": df_eq = df_eq[df_eq["Estado"]    == filtro_estado]

    def color_estado(val):
        if val == "OPERATIVO":        return "background-color:#d4edda;color:#155724"
        if val == "FUERA DE SERVICIO":return "background-color:#f8d7da;color:#721c24"
        return ""

    st.dataframe(df_eq.style.applymap(color_estado, subset=["Estado"]),
                 use_container_width=True, hide_index=True, height=500)
    st.caption(f"Mostrando {len(df_eq)} de {total} equipos")

with tab1:
    col_tag, col_tipo = st.columns(2)
    with col_tag:  tag_sel   = st.selectbox("TAG del equipo", list(equipos_db.keys()))
    with col_tipo: tipo_mant = st.selectbox("Tipo de Mantencion", ["INSPECCION","P1","P2","P3"])

    mod_aut, ser_aut, sub_aut, area_aut, ubi_aut = equipos_db[tag_sel]
    eq_info = next((e for e in equipos_lista if e[2] == tag_sel), None)
    if eq_info:
        estado_eq = eq_info[4]
        color = "green" if estado_eq == "OPERATIVO" else "red"
        st.markdown(f"**Equipo:** {mod_aut} | **Serie:** {ser_aut} | **Subarea:** {sub_aut} | **Area:** {area_aut} | Estado: :{color}[{estado_eq}]")

    try:
        ur = supabase.table("historial").select("*").eq("tag", tag_sel).order("creado_en", desc=True).limit(1).execute()
        ultimo = ur.data[0] if ur.data else None
    except: ultimo = None

    h_sug       = int(ultimo["horas_marcha"]) if ultimo else 0
    h_sug_carga = int(ultimo["horas_carga"])  if ultimo else 0
    if ultimo: st.caption(f"Ultimo registro: {ultimo['fecha']} — {ultimo['tipo']} — {h_sug} hrs marcha")
    st.divider()

    with st.form("editor_informe"):
        st.subheader("Datos Generales")
        c1, c2 = st.columns(2)
        with c1:
            fecha_sel    = st.date_input("Fecha de atencion", datetime.now())
            tec1         = st.text_input("Tecnico 1 (Lider)", st.secrets.get("tec1_default","Ignacio Morales"))
        with c2:
            cliente_cont = st.text_input("Contacto Cliente",  st.secrets.get("contacto_default","Pamela Tapia"))
            tec2         = st.text_input("Tecnico 2",         st.secrets.get("tec2_default","Emian Sanchez"))

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
        st.caption("Pre-llenado automatico segun TAG y tipo.")
        tpl = get_plantilla(tipo_mant, mod_aut, tag_sel, sub_aut, area_aut, v_p_carga, v_p_descarga, v_t_salida)
        alcance_manual     = st.text_area("Alcance",         value=tpl["alcance"],         height=80)
        actividades_manual = st.text_area("Actividades",     value=tpl["actividades"],     height=230)
        condicion_manual   = st.text_area("Condicion Final", value=tpl["condicion"],       height=100)
        rec_manual         = st.text_area("Recomendaciones", value=tpl["recomendaciones"], height=100)
        st.divider()
        enviar = st.form_submit_button("GUARDAR Y GENERAR REPORTE", use_container_width=True)

    if enviar:
        TEMPLATE_PATH = "InformeInspección.docx"
        if not os.path.exists(TEMPLATE_PATH):
            st.error(f"Template Word no encontrado: '{TEMPLATE_PATH}'"); st.stop()
        try:
            doc   = DocxTemplate(TEMPLATE_PATH)
            meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
            fecha_txt = f"{fecha_sel.day} de {meses[fecha_sel.month-1]} de {fecha_sel.year}"
            contexto = {
                "fecha": fecha_txt, "cliente_contact": cliente_cont,
                "alcanze_intervencion": alcance_manual, "operaciones_dinamicas": actividades_manual,
                "p_carga": v_p_carga, "p_descarga": v_p_descarga, "temp_salida": v_t_salida,
                "estado_entrega": condicion_manual, "recomendaciones": rec_manual,
                "proxima_visita": tpl["proxima_visita"], "tecnico_1": tec1, "tecnico_2": tec2,
                "act_1": "Mantenimiento", "h_1": "8", "h_2": "8",
                "equipo_modelo": mod_aut, "serie": ser_aut,
                "horas_marcha": f"{h_marcha} Hrs.", "tipo_orden": tpl["tipo_orden_txt"],
                "horas_totales_despues": h_marcha, "horas_carga_despues": h_carga, "tag": tag_sel,
            }
            doc.render(contexto)
            output = io.BytesIO(); doc.save(output)
            archivo_bytes  = output.getvalue()
            nombre_archivo = f"Informe_{tipo_mant}_{tag_sel}_{fecha_sel}.docx"
            with st.spinner("Guardando en base de datos..."):
                rid = guardar_registro({
                    "fecha": str(fecha_sel), "tag": tag_sel, "tipo": tipo_mant,
                    "horas_marcha": h_marcha, "horas_carga": h_carga,
                    "tecnico_1": tec1, "tecnico_2": tec2, "contacto": cliente_cont,
                    "p_carga": v_p_carga, "p_descarga": v_p_descarga, "temp_salida": v_t_salida,
                    "alcance": alcance_manual, "actividades": actividades_manual,
                    "condicion": condicion_manual, "recomendaciones": rec_manual,
                })
                if rid: guardar_informe(rid, nombre_archivo, archivo_bytes)
            st.success(f"Guardado — {tpl['tipo_orden_txt']} | {tag_sel} | {fecha_txt}")
            st.download_button("DESCARGAR REPORTE", archivo_bytes, nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True)
        except Exception as e:
            st.error(f"Error al procesar: {e}"); logger.error(f"Error: {e}")

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
            id_borrar = st.number_input("ID a eliminar", min_value=1, step=1)
            if st.button("Eliminar", type="primary"):
                if eliminar_registro(id_borrar):
                    st.success(f"Registro {id_borrar} eliminado."); st.rerun()
    else:
        st.info("No hay registros aun.")

with tab3:
    st.subheader("Informes Word Guardados")
    if st.button("Actualizar lista", key="act_inf"): st.rerun()
    try:
        ir = supabase.table("informes").select("*, historial(fecha, tag, tipo)").order("creado_en", desc=True).execute()
        informes = ir.data if ir.data else []
    except Exception as e:
        informes = []; st.warning(f"No se pudieron cargar: {e}")
    if informes:
        for inf in informes:
            hist = inf.get("historial", {}) or {}
            ca, cb, cc, cd = st.columns([3,1,2,1])
            with ca: st.write(inf["nombre"])
            with cb: st.write(hist.get("fecha","-"))
            with cc: st.write(f"{hist.get('tag','-')} — {hist.get('tipo','-')}")
            with cd:
                url = obtener_url_informe(inf["ruta"])
                if url: st.link_button("Descargar", url)
            st.divider()
    else:
        st.info("No hay informes guardados aun.")
