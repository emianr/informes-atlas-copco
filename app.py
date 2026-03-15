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

st.set_page_config(page_title="Centinela - Minera Spence", layout="wide", page_icon="🛡️")

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Rajdhani', sans-serif; letter-spacing: 0.03em; }

.equipo-card {
    background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
}
.equipo-card:hover { border-color: #4a9eff; transform: translateY(-1px); }
.equipo-card::before {
    content: '';
    position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
}
.equipo-card.operativo::before { background: #48bb78; }
.equipo-card.fuera::before { background: #f56565; }

.tag-label {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.1rem; font-weight: 700;
    color: #e2e8f0; letter-spacing: 0.05em;
}
.modelo-label { font-size: 0.85rem; color: #718096; margin-top: 2px; }
.estado-badge {
    display: inline-block; padding: 2px 10px;
    border-radius: 20px; font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.06em; text-transform: uppercase;
}
.badge-op  { background: rgba(72,187,120,0.15); color: #48bb78; border: 1px solid rgba(72,187,120,0.3); }
.badge-fs  { background: rgba(245,101,101,0.15); color: #f56565; border: 1px solid rgba(245,101,101,0.3); }

.ficha-header {
    background: linear-gradient(135deg, #1a1f2e, #0f3460);
    border-radius: 16px; padding: 2rem;
    border: 1px solid #2d3748; margin-bottom: 1.5rem;
}
.ficha-tag { font-family:'Rajdhani',sans-serif; font-size:2.2rem; font-weight:700; color:#fff; }
.ficha-modelo { font-size:1rem; color:#90cdf4; margin-top:4px; }
.dato-box {
    background: #1a1f2e; border-radius:10px; padding:1rem;
    border:1px solid #2d3748; text-align:center;
}
.dato-label { font-size:0.7rem; color:#718096; text-transform:uppercase; letter-spacing:0.08em; }
.dato-valor { font-family:'Rajdhani',sans-serif; font-size:1.3rem; font-weight:600; color:#e2e8f0; margin-top:4px; }

.comp-row {
    background:#1a1f2e; border-radius:8px; padding:0.8rem 1rem;
    border:1px solid #2d3748; margin-bottom:0.5rem;
    display:flex; justify-content:space-between; align-items:center;
}
.comp-tipo { font-size:0.75rem; color:#718096; text-transform:uppercase; letter-spacing:0.06em; }
.comp-parte { font-family:'Rajdhani',sans-serif; font-size:1rem; font-weight:600; color:#90cdf4; }

.metric-card {
    background: linear-gradient(135deg, #1a1f2e, #16213e);
    border-radius:12px; padding:1.2rem;
    border:1px solid #2d3748; text-align:center;
}
.metric-n { font-family:'Rajdhani',sans-serif; font-size:2.5rem; font-weight:700; }
.metric-l { font-size:0.75rem; color:#718096; text-transform:uppercase; letter-spacing:0.08em; margin-top:4px; }
</style>
""", unsafe_allow_html=True)

# ── Supabase ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# ── DB helpers ────────────────────────────────────────────────────────────────
def cargar_equipos():
    try:
        res = supabase.table("equipos").select("*").order("tag").execute()
        return res.data or []
    except Exception as e:
        st.warning(f"Error cargando equipos: {e}")
        return []

def cargar_componentes(tag):
    try:
        res = supabase.table("componentes").select("*").eq("equipo_tag", tag).execute()
        return res.data or []
    except:
        return []

def upsert_equipo(datos):
    try:
        supabase.table("equipos").upsert(datos, on_conflict="tag").execute()
        return True
    except Exception as e:
        st.error(f"Error guardando equipo: {e}")
        return False

def guardar_componente(datos):
    try:
        supabase.table("componentes").insert(datos).execute()
        return True
    except Exception as e:
        st.error(f"Error guardando componente: {e}")
        return False

def eliminar_componente(id):
    try:
        supabase.table("componentes").delete().eq("id", id).execute()
        return True
    except Exception as e:
        st.error(f"Error eliminando: {e}")
        return False

def cargar_historial():
    try:
        res = supabase.table("historial").select("*").order("creado_en", desc=True).execute()
        return res.data or []
    except Exception as e:
        st.warning(f"Error cargando historial: {e}")
        return []

def guardar_registro(datos):
    try:
        res = supabase.table("historial").insert(datos).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        st.error(f"Error guardando registro: {e}")
        return None

def guardar_informe_storage(historial_id, nombre, archivo_bytes):
    try:
        path = f"informes/{historial_id}/{nombre}"
        supabase.storage.from_("informes").upload(
            path, archivo_bytes,
            {"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        )
        supabase.table("informes").insert({"historial_id": historial_id, "nombre": nombre, "ruta": path}).execute()
        return path
    except Exception as e:
        logger.error(f"Error storage: {e}")
        return None

def obtener_url_informe(ruta):
    try:
        res = supabase.storage.from_("informes").create_signed_url(ruta, 3600)
        return res.get("signedURL")
    except:
        return None

def eliminar_registro_hist(id):
    try:
        supabase.table("historial").delete().eq("id", id).execute()
        return True
    except Exception as e:
        st.error(f"Error eliminando: {e}")
        return False

# ── Plantillas ────────────────────────────────────────────────────────────────
def get_plantilla(tipo, modelo, tag, ubicacion, area, p_carga, p_descarga, temp_salida):
    verbo = "inspeccion" if tipo == "INSPECCION" else ("mantencion mayor" if tipo == "P3" else "mantencion")
    alcance = f"Se realizo {verbo} a equipo compresor {modelo} TAG {tag} de {area}, {ubicacion}, conforme a procedimientos internos y buenas practicas de mantenimiento."
    estado_op = f"- Estado operacional: Presion de carga: {p_carga} bar / descarga: {p_descarga} bar, temperatura salida elemento: {temp_salida} C."

    plantillas = {
        "INSPECCION": {
            "actividades": (
                "- Inspeccion de fugas: Revision visual circuitos aire y aceite.\n"
                "- Nivel de lubricante: Chequeo por visor.\n"
                "- Revision enfriador: Inspeccion visual enfriador aire/aceite.\n"
                "- Revision general: Filtros, valvula de corte y lineas.\n"
                "- Monitoreo controlador: Prueba carga/descarga.\n" + estado_op + "\n"
                "- Purga condensado: Drenado de condensado."
            ),
            "condicion": "El equipo se encuentra funcionando bajo parametros estables, nivel de aceite dentro del rango y filtros sin saturacion.",
            "recomendaciones": "- Nota tecnica: El equipo supera horas recomendadas para mantenimiento mayor. Se recomienda enviar a overhaul o reemplazar.",
            "proxima_visita": "El proximo servicio recomendado es Inspeccion estimada requerida",
            "tipo_orden_txt": "INSPECCION",
        },
        "P1": {
            "actividades": (
                "- Inspeccion de fugas: Revision visual circuitos aire/aceite.\n"
                "- Limpieza general del equipo.\n"
                "- Verificacion de lubricante por visor.\n"
                "- Chequeo enfriador: Inspeccion visual.\n"
                "- Cambio de filtros de aire/aceite.\n"
                "- Monitoreo controlador: Prueba carga/descarga.\n" + estado_op
            ),
            "condicion": "El equipo funciona bajo parametros estables, nivel de aceite correcto y filtros sin saturacion.",
            "recomendaciones": "- Plan de mantenimiento: Mantener frecuencia de inspeccion y drenado.\n- Control ambiental: Limpieza preventiva de radiadores.",
            "proxima_visita": "El proximo servicio recomendado es P2 estimada requerida",
            "tipo_orden_txt": "Mantencion P1",
        },
        "P2": {
            "actividades": (
                "- Inspeccion de fugas: Revision visual circuitos aire/aceite.\n"
                "- Limpieza general del equipo.\n"
                "- Cambio de lubricante: Drenado y cambio de aceite.\n"
                "- Chequeo enfriador: Inspeccion visual.\n"
                "- Cambio de filtros de aire/aceite.\n"
                "- Monitoreo controlador: Prueba carga/descarga.\n" + estado_op
            ),
            "condicion": "El equipo funciona bajo parametros estables. Se detectan enfriadores saturados sin fugas visibles.",
            "recomendaciones": "- Plan de mantenimiento: Mantener frecuencia de inspeccion.\n- Control ambiental: Limpieza preventiva de radiadores.",
            "proxima_visita": "El proximo servicio recomendado es P3 estimada requerida",
            "tipo_orden_txt": "Mantencion P2",
        },
        "P3": {
            "actividades": (
                "- Inspeccion de fugas: Revision visual circuitos aire/aceite.\n"
                "- Limpieza profunda de enfriadores y componentes internos.\n"
                "- Cambio de lubricante completo.\n"
                "- Cambio de filtros de aire, aceite y separador.\n"
                "- Engrase de rodamientos motor electrico.\n"
                "- Revision valvulas de minima y anti-retorno.\n"
                "- Monitoreo controlador: Prueba carga/descarga.\n" + estado_op
            ),
            "condicion": "El equipo en optimas condiciones tras mantencion mayor. Parametros nominales, aceite correcto y filtros nuevos.",
            "recomendaciones": "- Continuar plan preventivo.\n- Programar proxima mantencion mayor segun horas operacion.",
            "proxima_visita": "El proximo servicio recomendado es Inspeccion estimada requerida",
            "tipo_orden_txt": "Mantencion P3",
        },
    }
    tpl = plantillas.get(tipo, plantillas["INSPECCION"])
    return {"alcance": alcance, **tpl}

# ── DATOS INICIALES CENTINELA ─────────────────────────────────────────────────
EQUIPOS_INICIALES = [
    # SULFURO
    {"tag":"211-GC-001","serie":"API515199","modelo":"GA75","marca":"ATLASCOPCO","subarea":"CHANCADO PRIMARIO","area":"CONMINUCION","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"211-GC-002","serie":"API616532","modelo":"GA75","marca":"ATLASCOPCO","subarea":"CHANCADO PRIMARIO","area":"CONMINUCION","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"318-GC-001","serie":"WUX409578","modelo":"G132","marca":"ATLASCOPCO","subarea":"CHANCADO SECUNDARIO","area":"CONMINUCION","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"318-GC-002","serie":"WUX409516","modelo":"G132","marca":"ATLASCOPCO","subarea":"CHANCADO SECUNDARIO","area":"CONMINUCION","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"318-GC-003","serie":"WUX409537","modelo":"G132","marca":"ATLASCOPCO","subarea":"CHANCADO SECUNDARIO","area":"CONMINUCION","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"318-OSC-001","serie":"---","modelo":"OSC1200","marca":"ATLASCOPCO","subarea":"CHANCADO SECUNDARIO","area":"CONMINUCION","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"344-GC-001","serie":"APIS44785601","modelo":"GA55","marca":"ATLASCOPCO","subarea":"FISEMO","area":"MOLIBDENO","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"346-GC-001","serie":"API624285","modelo":"GA90","marca":"ATLASCOPCO","subarea":"MOLIBDENO","area":"MOLIBDENO","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"346-GC-002","serie":"API624286","modelo":"GA90","marca":"ATLASCOPCO","subarea":"MOLIBDENO","area":"MOLIBDENO","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"LAB-GC-001","serie":"CAI878332","modelo":"GA15FF","marca":"ATLASCOPCO","subarea":"LABORATORIO","area":"LABORATORIO","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"LAB-GC-002","serie":"ITJ182547","modelo":"GA15P","marca":"ATLASCOPCO","subarea":"LABORATORIO","area":"LABORATORIO","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"411-GC-001","serie":"API310344","modelo":"GA30","marca":"ATLASCOPCO","subarea":"FLOCULANTE","area":"FLOCULANTE","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"411-GC-501","serie":"API323529","modelo":"GA30","marca":"ATLASCOPCO","subarea":"FLOCULANTE","area":"FLOCULANTE","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"122-GC-001","serie":"APF135735","modelo":"GA90+","marca":"ATLASCOPCO","subarea":"TALLER DE CAMIONES","area":"TALLER DE CAMIONES","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"122-GC-002","serie":"APF135800","modelo":"GA90+","marca":"ATLASCOPCO","subarea":"TALLER DE CAMIONES","area":"TALLER DE CAMIONES","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"122-GD-002","serie":"API690916","modelo":"CD185","marca":"ATLASCOPCO","subarea":"TALLER DE CAMIONES","area":"TALLER DE CAMIONES","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"335-GC-001","serie":"APF143254","modelo":"GA315","marca":"ATLASCOPCO","subarea":"MOLIENDA","area":"CONMINUCION","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"335-GC-002","serie":"APF143370","modelo":"GA315","marca":"ATLASCOPCO","subarea":"MOLIENDA","area":"CONMINUCION","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"335-GC-003","serie":"APF143685","modelo":"GA315","marca":"ATLASCOPCO","subarea":"MOLIENDA","area":"CONMINUCION","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"335-GD-004","serie":"APF226020","modelo":"CD330+","marca":"ATLASCOPCO","subarea":"MOLIENDA","area":"CONMINUCION","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"324-GC-001","serie":"APF143377","modelo":"GA500","marca":"ATLASCOPCO","subarea":"FLOTACION","area":"FLOTACION","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"324-GC-002","serie":"APF143426","modelo":"GA500","marca":"ATLASCOPCO","subarea":"FLOTACION","area":"FLOTACION","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"CM871A1-1","serie":"CAI721030","modelo":"GA7FF","marca":"ATLASCOPCO","subarea":"OSMOSIS","area":"RO","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"ZE-GC-001","serie":"APF209860","modelo":"ZE2","marca":"ATLASCOPCO","subarea":"OSMOSIS","area":"RO","ubicacion":"SULFURO","estado":"OPERATIVO"},
    {"tag":"335-GD-001","serie":"API080552","modelo":"BD250","marca":"ATLASCOPCO","subarea":"Molienda","area":"CONMINUCION","ubicacion":"SULFURO","estado":"FUERA DE SERVICIO"},
    {"tag":"335-GD-002","serie":"API080554","modelo":"BD250","marca":"ATLASCOPCO","subarea":"Molienda","area":"CONMINUCION","ubicacion":"SULFURO","estado":"FUERA DE SERVICIO"},
    {"tag":"335-GD-601","serie":"APF193048","modelo":"BD550","marca":"ATLASCOPCO","subarea":"Molienda","area":"CONMINUCION","ubicacion":"SULFURO","estado":"FUERA DE SERVICIO"},
    {"tag":"346-GD-001","serie":"APF207186","modelo":"CD150+","marca":"ATLASCOPCO","subarea":"Molibdeno","area":"Flotacion molibdeno floculantes Ro","ubicacion":"SULFURO","estado":"FUERA DE SERVICIO"},
    {"tag":"122-GC-003","serie":"APF135734","modelo":"GA110+","marca":"ATLASCOPCO","subarea":"Taller de camiones","area":"TALLER DE CAMIONES","ubicacion":"SULFURO","estado":"FUERA DE SERVICIO"},
    {"tag":"122-GD-001","serie":"API690915","modelo":"CD300","marca":"ATLASCOPCO","subarea":"Taller de camiones","area":"TALLER DE CAMIONES","ubicacion":"SULFURO","estado":"FUERA DE SERVICIO"},
    {"tag":"318-GD-001","serie":"UTF123UQ1","modelo":"BD630","marca":"ATLASCOPCO","subarea":"Chancado Secundario","area":"CONMINUCION","ubicacion":"SULFURO","estado":"FUERA DE SERVICIO"},
    # OXE
    {"tag":"3210-C2-1001","serie":"API623258","modelo":"GA90","marca":"ATLASCOPCO","subarea":"Chancado Primario","area":"OXE","ubicacion":"OXE","estado":"OPERATIVO"},
    {"tag":"3210-C1-1001","serie":"API623260","modelo":"GA90","marca":"ATLASCOPCO","subarea":"Chancado Primario","area":"OXE","ubicacion":"OXE","estado":"OPERATIVO"},
    {"tag":"3230-C3-2001","serie":"API543531","modelo":"GA45","marca":"ATLASCOPCO","subarea":"Harnero Secundario","area":"OXE","ubicacion":"OXE","estado":"OPERATIVO"},
    {"tag":"3230-C4-3001","serie":"API543590","modelo":"GA30+","marca":"ATLASCOPCO","subarea":"Chancado Secundario","area":"OXE","ubicacion":"OXE","estado":"OPERATIVO"},
    {"tag":"3240-C5-4001","serie":"API623259","modelo":"GA90","marca":"ATLASCOPCO","subarea":"Harnero Terciario","area":"OXE","ubicacion":"OXE","estado":"OPERATIVO"},
    {"tag":"3240-C6-5001","serie":"API543530","modelo":"GA45","marca":"ATLASCOPCO","subarea":"Chancado Terciario","area":"OXE","ubicacion":"OXE","estado":"OPERATIVO"},
    {"tag":"3240-C7-6001","serie":"API329314","modelo":"GA15+","marca":"ATLASCOPCO","subarea":"Silo Refino","area":"OXE","ubicacion":"OXE","estado":"OPERATIVO"},
    {"tag":"3300-C7-600","serie":"CAI884389","modelo":"GX4","marca":"ATLASCOPCO","subarea":"Aglomerado","area":"OXE","ubicacion":"OXE","estado":"OPERATIVO"},
    # OXIDO
    {"tag":"200-GC-001","serie":"API629823","modelo":"GA55","marca":"ATLASCOPCO","subarea":"Chancado Primario","area":"AREA SECA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"200-GC-002","serie":"API629822","modelo":"GA55","marca":"ATLASCOPCO","subarea":"Chancado Primario","area":"AREA SECA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"220-GC-001","serie":"API629825","modelo":"GA55","marca":"ATLASCOPCO","subarea":"Chancado Secundario","area":"AREA SECA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"220-GC-002","serie":"API629834","modelo":"GA55","marca":"ATLASCOPCO","subarea":"Chancado Secundario","area":"AREA SECA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"220-GC-003","serie":"API629826","modelo":"GA90+","marca":"ATLASCOPCO","subarea":"Chancado Secundario","area":"AREA SECA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"220-GD-001","serie":"APF235378","modelo":"CD630","marca":"ATLASCOPCO","subarea":"Chancado Secundario","area":"AREA SECA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"AGL-GC-001","serie":"API333775","modelo":"GA30","marca":"ATLASCOPCO","subarea":"Aglomerado","area":"AREA SECA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"AGL-GC-002","serie":"API334806","modelo":"GA30","marca":"ATLASCOPCO","subarea":"Aglomerado","area":"AREA SECA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"OSM-GC-001","serie":"1148","modelo":"SM15","marca":"KAESER","subarea":"Osmosis","area":"OSMOSIS","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"OSM-GC-004","serie":"ITJ242366","modelo":"G11P","marca":"ATLASCOPCO","subarea":"Osmosis","area":"OSMOSIS","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"TCN-GC-002","serie":"APF227050","modelo":"GA90+","marca":"ATLASCOPCO","subarea":"Taller Camiones Norte","area":"TALLER DE CAMIONES","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"MNE-GD-001","serie":"API249242","modelo":"CD35","marca":"ATLASCOPCO","subarea":"Martillo Neumatico SX","area":"AREA HUMEDA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"600-DP-002","serie":"ITJ242345","modelo":"G11","marca":"ATLASCOPCO","subarea":"Martillo Neumatico SX","area":"AREA HUMEDA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"CAL-GC-001","serie":"ITJ242285","modelo":"GA18","marca":"ATLASCOPCO","subarea":"Calentadores SX","area":"AREA HUMEDA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"ENZ-GC-001","serie":"ITJ242306","modelo":"GA15","marca":"ATLASCOPCO","subarea":"Enzunchadora SX","area":"AREA HUMEDA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"MDC-GC-001","serie":"ITJ242307","modelo":"GA18","marca":"ATLASCOPCO","subarea":"Maquina Despegadora SX","area":"AREA HUMEDA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"POST-GC-001","serie":"API587024","modelo":"GA37","marca":"ATLASCOPCO","subarea":"Post-Decantador SX","area":"AREA HUMEDA","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"LAB-GC-004","serie":"ITR1354539","modelo":"LF3FF","marca":"ATLASCOPCO","subarea":"Laboratorio","area":"LABORATORIO","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"LAB-GC-003","serie":"ITJ242308","modelo":"GA18P","marca":"ATLASCOPCO","subarea":"Laboratorio","area":"LABORATORIO","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"DES-GC-002","serie":"1118-6854188","modelo":"BSD65","marca":"KAESER","subarea":"Descarga de Acido","area":"DESCARGA DE ACIDO","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"DES-GC-001","serie":"1120-6867842","modelo":"BSD65","marca":"KAESER","subarea":"Descarga de Acido","area":"DESCARGA DE ACIDO","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"LAB-GC-006","serie":"AII661966","modelo":"GX18","marca":"ATLASCOPCO","subarea":"Laboratorio","area":"LABORATORIO","ubicacion":"OXIDO","estado":"FUERA DE SERVICIO"},
    {"tag":"LAB-GC-005","serie":"---","modelo":"FX1AD","marca":"ATLASCOPCO","subarea":"Laboratorio","area":"LABORATORIO","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"TCN-GC-001","serie":"349006/0334","modelo":"RA-086","marca":"COMP AIR","subarea":"Taller Camiones Norte","area":"TALLER DE CAMIONES","ubicacion":"OXIDO","estado":"OPERATIVO"},
    {"tag":"SOPLADOR-1","serie":"APF155559","modelo":"ZS75+VSD","marca":"ATLASCOPCO","subarea":"SX","area":"Area humeda hidro","ubicacion":"OXIDO","estado":"OPERATIVO"},
    # MUELLE
    {"tag":"621-GC-001","serie":"APFS99645701","modelo":"GR200","marca":"ATLASCOPCO","subarea":"Muelle","area":"MUELLE","ubicacion":"MUELLE","estado":"OPERATIVO"},
    {"tag":"621-GC-003","serie":"APF143505","modelo":"GA355","marca":"ATLASCOPCO","subarea":"Muelle","area":"MUELLE","ubicacion":"MUELLE","estado":"OPERATIVO"},
    {"tag":"621-GC-004","serie":"APFS99645702","modelo":"GA355","marca":"ATLASCOPCO","subarea":"Muelle","area":"MUELLE","ubicacion":"MUELLE","estado":"OPERATIVO"},
    {"tag":"621-GC-002","serie":"APFS99645702","modelo":"GR200","marca":"ATLASCOPCO","subarea":"Muelle","area":"MUELLE","ubicacion":"MUELLE","estado":"OPERATIVO"},
    {"tag":"OSM-GC-002","serie":"3019853","modelo":"2475","marca":"INGERSOLLRAND","subarea":"Osmosis","area":"OSMOSIS","ubicacion":"MUELLE","estado":"OPERATIVO"},
    {"tag":"OSM-GC-005","serie":"CAI721652","modelo":"GA5FF","marca":"ATLASCOPCO","subarea":"Osmosis","area":"OSMOSIS","ubicacion":"MUELLE","estado":"OPERATIVO"},
    {"tag":"OSM-GC-003","serie":"3019858","modelo":"2475","marca":"INGERSOLL RAND","subarea":"Osmosis","area":"OSMOSIS","ubicacion":"MUELLE","estado":"FUERA DE SERVICIO"},
    {"tag":"641-DC-003M","serie":"1045","modelo":"CSV150","marca":"KAESER","subarea":"Muelle","area":"MUELLE","ubicacion":"MUELLE","estado":"FUERA DE SERVICIO"},
    {"tag":"621-GC-001B","serie":"APFS99645701","modelo":"GR200","marca":"ATLASCOPCO","subarea":"Muelle","area":"MUELLE","ubicacion":"MUELLE","estado":"OPERATIVO"},
]

def inicializar_equipos():
    """Carga equipos iniciales si la tabla está vacía."""
    try:
        res = supabase.table("equipos").select("id").limit(1).execute()
        if not res.data:
            for eq in EQUIPOS_INICIALES:
                supabase.table("equipos").upsert(eq, on_conflict="tag").execute()
    except Exception as e:
        logger.error(f"Error inicializando equipos: {e}")

inicializar_equipos()

# ── Login ────────────────────────────────────────────────────────────────────
def verificar_usuario(username: str, pin: str):
    try:
        # Busca por username exacto (acepta correo o nombre.apellido)
        res = supabase.table("usuarios").select("*") \
            .eq("username", username.lower().strip()) \
            .eq("pin", pin.strip()) \
            .eq("activo", True).execute()
        return res.data[0] if res.data else None
    except:
        return None

def get_usuario_activo():
    return st.session_state.get("usuario_activo")

# Pantalla de login
if "usuario_activo" not in st.session_state:
    st.session_state["usuario_activo"] = None

if not st.session_state["usuario_activo"]:
    st.markdown(
        '<style>'
        '@import url(https://fonts.googleapis.com/css2?family=Rajdhani:wght@700&family=Inter:wght@400;500&display=swap);'
        'html,body,[class*="css"]{font-family:Inter,sans-serif;}'
        '.stApp{background-image:url(data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAgICAgJCAkKCgkNDgwODRMREBARExwUFhQWFBwrGx8bGx8bKyYuJSMlLiZENS8vNUROQj5CTl9VVV93cXecnNEBCAgICAkICQoKCQ0ODA4NExEQEBETHBQWFBYUHCsbHxsbHxsrJi4lIyUuJkQ1Ly81RE5CPkJOX1VVX3dxd5yc0f/CABEIAkQDdgMBIgACEQEDEQH/xAAxAAEAAwEBAQEAAAAAAAAAAAAAAwQFAgEGBwEBAQEBAQAAAAAAAAAAAAAAAAIBAwT/2gAMAwEAAhADEAAAAPxIdLAAAAAAALNbZDKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPbmzSXzKtqGsX7GT9JU6/wm3m1NUcu4AAAAAAA9PGlW2KyybWWRWWRWWRWWZCkMoAAAAAAAAAAAAAAAAAAAAAAAAAABfr91EMc0OaGUAAAABe+y+M97cLVXYzMRKlqOmno5H03bhD8h2i6sdqrz6hlAAAAAANKhcqKAmwAAAANSpWu1FJoZ+aGUAAAAAAAAAAJU3e97E7ccyLXc+mQ1xkL0eVVWoDgZQAAAAAAA0tlm++E8E0IGUAAAAuU7uxT8MvUZ2rfLncvYnXkbnyJmDz+rRp+2655wnoAAAAAO03829R3AywAAAAAJNLJbFqr9R85uRCegAAAAAAADr3rZ67q6W5r/AD21h3zswwzx0qrlPNsySz1NPbr6vTlS061KpyaezV5d81YRVd75lAAACRM3M1GsCbmh672YhlAAAAWYrNLYJNMguVKtTuZF3up3fk9HIJ6NyeLzL8NbNs1tfI0E2AAASS7NbTq/TVHyAjqAAAAAAABPBPBsy+wj3yT0ie+ZQAAAA6OZeoNnvgxcm8dInzvsseo+e1us+OmxNhKySC3TitDSly+nKtezOpuxLStYrQ6ebmycw+ZskE05SXa7YhlNDmtUR+E2Amhm2YRlAAAJob2zXnv1qizmczZtJd6zaf3vyK4zvLqLpS2B3LX7qYLNm1U/NJO+fWBZFex5XLKsJYjC7Sa740M8DKAAAAAAA79jn2YBlASexNnviT0id8YBQlT4861EuW9zL031PTni62DNUamFoZGb5c5zJvT6zfS/9J855UX8+bNzbubLLNVK21UmpLubv9I+b4+ipRWI2K2VRv8AkRozZmhfPOpXPY6Unvk2Amhm2YRlAACzsvo8GjUX+aUuV3H7Hmyc8MAoAACxZzmx9BhaGZuBPQAAAC7V6n2KYywAAAAAAE8E+zAMoAADvqJs9+WPoqnFlt5dRZiiTflO7Lm1dvKl2dSh9383345vmfNy6o1eKk691Nz3CtVd2/LUs7lTi3BG8eWRNLjXtyvJHzlaLN0dmlxt0DiK/iZoT0ue0myXDKYy5oZ4NkMoX9nj3yDc478jzZYjAKAAAAAA0s6x7UVRNgAAALtKzsxR2K4GUAAAAAAmhl2YnXOUAALOzFLHEdW6V1lW1SNvVo7LI+b9LUNmWtj6nirU7cXNnPm5vbvz2NG3Pi7nqSaLqbNfS6c86henzfMPZy8q3natCdjksxndaUS6Pz82rdWqnbSqbaVRZh5nO3nWzDDp5maGXp1/adR3wToKAAAAAAAAs++e1FUTYAAAAFyvNHsQjLAAAAAAAngmh2QykksWzLWAMpdpXdikMtY452eNOrWZahjsN7+h+d+s68fkd+Ho6ofXVbj473fh59KnkfObNoZI18j2/WVWrb2fkLXlHl1te0Zc2IZazWs7NYZQAAAAAFiusbNcZQAAAAAAAAFmOStsSxWqrQygAAAJJK+3UZMVmtmhlAAAAAATQ2WxHJFG0MoABdpXdil3xZbz35WYLTas88LOrNGLVyOuze3DHvgoAB1yLHVafYjjvUWpYuzh3xjvvutoMoAAAAABYr+7PieDAKAAAAAAAAn4982ZqtqqBlEkmzXWBBPzySODO93ClvPvfkNfX7eb4hNHx7ywfU/I1Mas5drKMyQ9133WjNDzNF+KqxaVTbNZaKq0Kq1AcXaWmyt5bi3Klnypm3a0RvvhlAAAAAAAOuRZmo26imu0s2WKWIs1rNYDKAAAAAAAsV5GzGMoAAAAAAACXz2xsVt2z8/0jr2KvzuxxEbKiEkZgFWqtqrs6f1nxm724WJN/wCa68qeD48vq67ijypEY98MoAAAAABYrtm1fxm5LEToKAAAAAAAAAAAvRVtOoox2O8R1zNBQAAAAAACxXl2YnfGAUAAAAAO08S9xate1tipl+d0c7Ektb3K8W6gGUA74tbPMleRlf6Ona6c/u/ye3V3Ihx9AAAAAAAAAAAAAAAAAAAAAAAAAGpzU+p68fjxy7AAAAAAAAAWK9iHZ5GUAAAAS97Lju/uZHetyy3f+Z4uK7SR0zV+hmrdQe+WYiMZS1Db2Obkljpz5+f4R0Wa3Wb1HZgORlAAAAAAAAAAAAAAAAAAAAAAALXcex15VNliv0AMoAAAAAAABrZLZuqRl1SFivLOU10VtefBqdXzHZulQ4ZQZQAEl7NbOlxQ63ObFkVYNamdbU+X05TYBy6hlgdzVpNmNYrgZQAAAAAAAAAAAAAAAAAAAAkTxdVaz2InQVdp+X9igMsAAAAAAAAAAAAAAAAAAAAABp5ljYv5A0MoAACxxFa2arvjAKAAAAAAAAAAAAAAAAAAFnZ4l5hZ7GZoKAX6HWzyvUQMoAAAAAAAAAAAAAAAAAAAABYr2NmuMoAAAAC3U9s7FUZYAAAAAAAAAAAAAAAADrvZqKkXtNk/NdlWEfbPXg9eDuSrGbmPZ9rKKwmq4ygAAAAAAAAAAAAAAAAAAAFivY2a4ygAAAAEkZNivO1AMoAAAAAAAAAAAAAAlbJ52QfV/N/VdOXz1b2vz6ToDe+DAKAAaWbeqK0VmDNmVx3xL2V08GAUAAAAAAAAAAAAAAAAAscc7PAygAAAABKl3B5oMoAAAAAAAAAAAAkm2YenjPUJvfBld/S0KvXjxHJHF1xNgAAAL1G9sUbNbtvCaHAK6mrtmxD1fZmNdrIE2AAAAAAAAAAAAAABYr2K+yGUAAAAey7PsPjAKAAAAAAAAAAEyYWzxU0JO4m+QWPcVV30orworo0cb6j5fpHc9SzF0k8E6CgAAEsRNmteo6m4kvbmVLNHmyKgsXOc/ZuPBSE9AAAAAAAAAAAAAAALFexX2QygAAHvXWyiMAoAAAAAAAAAAWdn6LJzJKjyxV4m5vO4CTngBlAO+L2zu5nEXTlTkv5EdLdTTzMBlgAHU+zWlliPtfmc+/05UOdqpF1q8vmVHej83OYCdtulTSE9AAAAAAAAAAAAAAFidUaXz1j6mo+ObGVF8DLASPNn2MwCgAAAAAAAAAAFqCXZrjKk9i62ebPMJ7zZgORlANDP0KjifP19zKuUeJ27Vv8Am5mnc1ws+646h4LNYAypI5I0+3KTWxqfMaV8vMnZzJuET0uvFc6YnoAAAAAALezUWBXWBXWBXWBXWBXWBX1tKnfPLr6yayWv6S2aNvpzzaf6z8jU/Hy/RfN8e3PhPQAAAAAAAAAAAACbmarshlAJYie5oetRLNYDKn7npVC9m6JBDP2UvvfmfqOvH4mO9l8uwTYACSOTZjGUBJz3Fs37ObFs3KWr2VAUhPQAAAAABLFLsxDKAAAAAd8E2VZqzzB6eLIk28Ce406mnHfP5+C3zx7VnfGaCgAAAAAAAAAEsUuyiliAygAAJpqcuzEv0C/Ut87NLXrSktWr9PcsXQ+eZ9Dh6+XNV0kcWCgEkcmzGMpLy2eBlTQzwbKzENhmriqOfUAAAAABJGT75LEAoAAAAAAABaqy7Mv2HxGpfPqpW1TOj1aU1U5kZUYygAAAAAAAAO+/GzxyZQAAAAHe78/drnv0LPnXliNLdmseP6v3tx+MydzD83puWsnf1jwp5quMoBJHJsxkuEQDsl4np7nVqndKbxl2K9mtshlAAAAAASxSxbIZQAAAAAAAAFmaFUeV71HNuaWD7uatK93s5XM3U1UWK7QygAAAAABKk461GMoAAAAAD6PB0618u/qfnLnTnT3OcM3syh9Iz47Sv0puhV2caOliv1LmwDK757j2fe/Yg9kx55w137HMQ3YDIRl2a1ivshlAAAAAASxSxbIZQAAAAAAAAElqje2FHQzwMtZrWtnUzZdTpyxJLM+bl1fpqzcJaRdVajIUoiSiJKIkoilsRM4iliaGUAAAAABpWc37Dtwy/atrZyKXLj30Zsj3c++y8P6zv5smj9f8PN0+rfnLtVjnjzfT04964OozAKTQz7M1K7SYGX1NXs7NYZQAAAAAEsUsWyGUAAAAAAAAAs1vdnWyNzD2Ut3tscDg7s5jGvl3oNzy7U4K69RykkbEqJqVECSQr2Jm5a+6/Ovr+/m6+B++qZXxg8/qAAO+kxJWopPYyTruTcl+k+Pu3z+/zfjaFx95F8ZLNfY+fI97n0UeRIfQbXwstTPH9Z8syfPsaM185X+mwpuhxqdxeQ1xkNU3KsXNHcxahNBlLNazs1hlAAAAAAduJdmIZQAAAAAAAAAH1FTJ768vK15FUVqrmhlSy1b+xJW8s7kdPq22gJsAnt7FWaTnc46iqtv/AGf57s3z3L+R124zfG/c04v5RE4eiVEPfDKPbWzBb7g2SGLNlkrWW9VLdQDKAAAamW2blO/3uU7mbfKCzWzQygGvn3K55gnoAs1rGzXe+ZQAAAAACWLU2MsZYAAAAAAAACSOfZj4MAqWzRbN/ml6zvyeQsUduh0mpYrSxtfzSzWrVzjZ5gijze4/Y8qREJfIx9F5W668dHd+a1unLDwvtsfn1wSTj2jnte1nsUEJJEToKWa1nZ7p3KYGUAAAAs1mzp0JJ9nulb8KDviaBW3ibeJXMJ6AAWK92lshlAAAAAO+BrZNqSudET0AAAAAAAATc8bPgygAAAF6i2dSTHbn01bCbk8Eiajd8YBQAF+9h7d8kk9C42syn9lUfO5n1HzE3BB7Hy7BlAALVWzs9VLlNgZYAAAACeAmzfzfKmzR26pnX6G02jTM0MoADSzdLNqAmwAAAAAGpltmxXAMoAAAAAACeCeDZDKAAAAAAAA76iJkjSajSeY4CmvkX6jTiiu9OWX+jYM/Xjh5Ghmce/PUsEdK63DmxDKASxE6OdqZdYE2AAAAAAngJtWqU1Tfq28u8rDl1AAFzZmzZoWBlgAAAAAAAAAAAAAAJYp9mAZQAAAAAAAAAADvgmRG0SD6GZz38+tjfT/N3zyK9zJ8/qscSeTvapITQWe9UFivmhla2Tq5VQE2AAAAAAAs1mz9P8xZrbIT0AAaGe2QygAAAAAAAAAAAAAAAEvUGyGUAAAAAAAAAAAAABp7PyejfLU0cv67v5/j8nTy+PeWbLnm+4bVYikmYk6h93IYtXgkydjHAnoAAAAAAAAAAAAAAAAAAAAAAAAAAAAALGzzDcpgZQAAAAAAAAAAAAAAGls/L6fXjt5drF2bleb3K88ozzvip1lWZOO9yfXr1+nL674Gl9MfLNjH49wygAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFqq2fr/mtiLrxwrNmXn0tT53XTnYyvrIdz5rZlx82tV03PpQtqbfqfn6ZgT0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAfQnbhn8GoeSLhHPoAAAAAAAAAAAAAAAB//EAEIQAAICAQEFBQYDBwQBAwQDAAECAwQREgAFEyExFCIyQVEQIDAzQFIjQmEGFSQ0UFNiQ3Fyc2AlRFRjdIGRJkVk/9oACAEBAAESAP8Az4DJwNpKduKJJpa8iRuSFb/yqKvPO2mGJ3Pnt2EJ8+zDH+mvd0Xhjlmb1q2bM0uiEpWjUFnbfEsUm7hS0lVrSQodmVlYqwwynBH/AIvTSNAbUyBoo2GFmULLIo6Bjj4oBYhVBJJwAm7rbAM0XDQ/m4FKL5touft7XBH8imgP3S3LUw0yTOU8l2VWYhVBLMcAUYYhahpkgxwkz22Sd7VPfUj83aSKdtpfxY1mHiXCP9EiM7KqglicAW5IoJBBFHEwiGhm7Qh61oTtxoT1qINuJWPWuRtrpn/RlG38GfKYbaaZ/wBSYbaKp6WGG3BgPS0g27PH5WoTt2bPSaE7R0LMraYuG7YyFIKkgggjkR/V60DWJQikAdWa3OsrKkQIhjGlFm5lG+5B8WizQM1wHDQ4KGa6296Ytx2p4bAGJhYsb4r6S1yZkbwSfvPeP/zJTt+87/8A8pzt+8r399jsm8blSuJmlBnlGIhu594Puq1MrIGmcR6942KlDdkVYqJJLmDNJp7NOyOcowwTIhikZG548/oKf8PFNdPJl7kXxASCCDgjzFqC4Al06Zfy2bNSasyrIvJhlG+q3Tuyfet6OpC6K7AnVNuTecTOvZy+k4JeCaL5kTrj6kAsQACSeQE5FWDsykF25yNs3egQ/axHxbf4SQ1h1Qan23fbatOG1sqNgM0vFzPLXVBKo1Wa/Aq2xmswilP+jJHJFI0ciMjqcMtSCNtc0wPAi8eyVZbjdsuOY4GbSNrYQyV6yRgU6uESHeVtrlySUuzLnSrRfxEQgPORecR+bB/nEPoI0aR1RVJZiFUX3VWStGwMcA05+LWuNEpikRZYGOWjmpK0bT1HaSFRl1+oVAAGc4U9BuM9lq3LTKA5qyFRxkkZoZmYPESqTNf3pVYK07MCMqf3mj/Oqof117ul8kU7djif5cZfZ60KHDSSRt6dlDeCxC23YrXlEW2dJEOGRgfoq6itF2hvGR3FZixLHqfZHzinX9Aw+JTRRI0zAFYV1kO7MzMxyzHJO1aWSSNeG5WzX78TTRx3IntV0CyKMzw05pLbx1Jo+Mp5I1ujVqQq4BnhhXWkO5xZ3nvVZZHGIVMg2v31lE9iIEQrmCqNgSpBBII5gu+rTcQDOdMqzxiN+RyjDUh+NU/h4Zrh5MPw4foIppYJFkikZHXo2K1/pogtHynoXayhp6s0altIb6RVJICgkny7kXoz+lWLtM/4jEIAXkbjs27N4zEAGWIYWdiJQ6nBKo2UnXh6XTXAT3lnrGIK6uJIm8L+xLlqNcLM+n7e1o3zqsLfr/AP0M8R2p7k33ZGacrMmMkyVqtUlb28I3cdUlpfs72R1etLDOdJL2qDQSNHrGQcAPG8ZwyEfFqwq5LuDw16izM0shJOQPbX5yhfuBX4k34NeKAeNsSv7Ud4nV0Yh1OVKQzNNDcpApqbaB9zVt3vYhfRamcxuUSlHOZiN4Bw2Wlezu47pfskLwSXG4bS7zjeGSKDH4cSaUb2V5uE+SMow0urw90wg5GOJC3xY0eWRI0UlmYKq33TWleJgYoBoVvobf7R2rm4627poYzFCyLnhq3y2yftIKnBBBHl9CiFsnoo6szhQVTkD1bZ1aGrHXUfjWMO4tMF3ZbCnKNbihUyc4oG/wASp2RyrZxkHkQkrV2OAHicd5Za6MhmrljGPEvU4G0O6b0o1cLQn3LU3ZEQstp7D/Z+8oavKrUhR/ItesQRJDPIzzTRPPOIpoqsaybxfM+SKzyxzRwgTBZOPxpDJVlhtRCq74ccoi0NiLXwSSinDx64W5PGUPr2ct8p1f8AQqQSGBBHl8CKJpZAi9T1NiVVRY48hQMJ7isVYMOoOdp1AmcDpnI+FUjWSYF/loC77SyNLI8jeJiSfbDTAQTWX4cXltXtmUtVjjKVXXS+1aGOJL1B8SylOMgN6w2FkKyIOiXVhrxVlVxG9aBAqq9ir3HTMbcynZ4rHOsTr84SCpIIII5EbVHLqIC2GDaoWsoAwdVwr57vxKqmtXkuMCHbMUH0cfOKdf0DD2CU40sAy7aEb5b8/tZWU6WBBHl8YIFGqTI9Fdy3XAA6DanEkkpeUHgxLrfavK8t2S1JglA0x2s5Tc1FD+eWWXbxVv8AjJsAWIABJPQQ7ttlcTIsKN0KRUd3y6nsu8i+QvxtGx3dWjhlHNlleec8S1M5B5jZpeRWNdKnrtumtG8xmmzwYQZH2ojjT2d5XNOHSYpHfnktGOy7EswKttXuPWnpQMA0WiPWs1SJ1eWBiVHj2UPbUcyLkYyjcXjeLSH9G4YJVkZGHXYO5AXiLIvkrJEeqvEdmryAFlAdR5+8VFeNoz4uspdixLN1PuzcxC33IB8J/wAGoq/nmOtvZFFJNIEjQszdAkcFUhQosWj0WZlMhktSGST7JLEkg08lQdEo2GJglUZnqkOoj3ah39HSXJhaZSDv+2Zrrpnoxd9o7Esa6QQVPVcVpehML+kjsQq3Yyynkk0tV414isHizjXshFyBifmctexBBIIwR5fASGWU9yNmx127MF+bNGn6aqidEeQ+u/d/PvrdlAdlSIVmKOPoq3OUL9wK+4srAYYBl9NEb+BsH7WRlOGUg/DVWY6VGTtlY+mGf7iSTknJPn7LP8NXjqjk7Yll2rxSNWKRqTJYlSJF3x+zW8q8NCGUIEihILJUqV45g8c8nINk7zMQKwBYx02ezM5PexnrtEjTjSBzXowdISDHzdT4mZL3iIWyfMQyGXhMpVgcMFgii3egl1CKQh2VbT2Lb5I0iCYAQqZYZohzYEOu1x/4yYqeSvpUzSSQXZHicq2slSjxWTmLRDOCDw7FcXBLLGhS3H8+EOGGiYHlyDPGyEZwVPRld18LEfosuCCUGR58aN/Hg/r2ZHGY5Mfo8MsYyyHH3eyBOEgmK5djiJZXBOlTkDqfdPOuP8Xx8GtFxplQnC9WaxLxpmfGFPJVrUnlUyuwjhU4LyPHBGYk1QxnqHsnSUiURoeRHsjkeKRZEbDqcg1GrioN+KFAr05ICjuzszMSWJyT7I55Ys6WwD1WKxEG1KTA55EyVYpV1KEic9GUzU5xqjIYeJb8SkJajJKS9T7iqScKCSfLssw5yaYxtoqp4pHkPp2hF+VAg/V55pRh5WIHQeyi44rQt4Zl0HZ0MbsrdQfokco6sOqkHaZNMsqjoGOPdWVlGk4K/bpifwtpPo6MpwykfARMjLHCfczjGlBhfP2pHJIdKIzH0p1ER2nsugjhGplTdocm1cLIrnWXS9DDLHWq/gwwwcWeTf297NkwztgsmEda9i40ma9ycgqQVS9vKQ4DvITsvbAMzUUkb7XaVwFk3XAFHQNDUlBZ6yqw8QSlu6VtKzSBj5VNzbvnCRWt5+cYZ97q9m1Nm3XRgSqw1N3zLOe/CcxSjG7aFxL1djAzIG7+1ipbikcSwyAhjk2ubxt6xKfZXvc0EzMGTGia/UDQi0iq0R5OVLRqdOJIz4g8YYF4iSg6j2KCT3QSdoU3mT+HBM+duxTP86g0Z9V3BMY2nEsZhQZcWHkVmZ0KO3dVfei5pMvquofBRTFUJUEyWDoQJu+GmolvEBzzWGzvGSQjhjTgYVo4LEx/DieQnb932F+YY49uz1V8dxT+iij+WGeTHn2uCLwVYM7He+8eGY1sFIycmPt0p8ccD7dprN4qUY/XVu5vyWE24NJvDcYbdjz4LVdto6m8YjmGNiT12E4CcG7UdU2rVFMcsccomqS9TNFJDK8Ui4dSVYJVncaghC/dwYV+ZYXP28SuvggLH1a1ORpV9Cny94Eg5BwRtbAlVZlHNlyfo7HNkb7kQ++kjKNPVftxE/Q6G9HR08Qxnofc0KnN+bfa7sxyT06COCaXmkbEDqUqqSFaQFvt7I8YyayR/q3COElvM4J5JVelBuNZqNYGaKd1lcO9y0hkiWYM41vbucKsAsEQluNxnFm3I29LdVRGFkzGm0Fu4jpK07RorA5n3g8kkkTTSIwYrxHgtM4XQ7lua7dl0fOmRP8AFZqsLBoomkYecIlnUTOxWtqAEV20QFjUgKjZxvEC9osD50kQlXbd7utgKGOCknKo4AsyMinTC/OWw4EMsdmZNaDO0lu+0FdhZaTk6nZrs4OJIYCdu1Qt4qMB/XczAScqzJCxCOs9fcfaJBRaYnPcV5YK8uG3asUo2a0pOFp1o5PIHeNtSVAijI8hvHeT8ltz49GeVziWd3Y/lzHB1VS/ktt3jqQV5GOpsTzjtjvynQSr5Ds0cvOs+T/bZWUlWBBHUe5XP4yA9G7p2IwcHqPfqVXsyaVICDm7zbw3RVOKTyu6roE0lqqzFuys7Hq3b5V+XHDHtJbsyjEs8jj0WNmGo4C+uY16DUfVnZvEeQ6D4CW7UXy7Eq7R71vROHWUFh0beO8LFmKnbKxLIyFHZ3dzqd2Y+vwq75idSM6O+BImhyucjqD9C/OCFvQuvwUd15A8j1H4T/4Ns6OvMjkehRGY4UbV6VuX+Wgdz/c/dscXOzciQ+a8TdkPgDyH1feCnw1kOOhe/cYFeMyqfy9dh+Emr87Du7fs67SvaoB9LWY8xNu2rHZlntc4eFGe0BbMm8d5KzwqeJKmBZRH3jO1Yl5+ISBvKmy2ONPKsayqJFWxJVSTKQl2ZQ2obxs6TGzAxN1iMKSgtAST1McVcKFeUE5OEj4vAi1swJZSqibJfP5SO7tXd3oSBWIkrSCZDAiSzx2YgAG1iRU7tKdvNpI0Gyd+rIvnGwcbAFqmACSsvRS0Yw8hA+1BDDGJbEQQMMpGlnVFNbZtGAYYEeJmijZSGxldo7tiJRDIqyRD/SSKpMO4/Zyf9OavwyqTRuWI7jNDOfGwEY/MZVQFYQQOhbddZJ7WZVJghUyyi5ZexPI7MCzOWY+xbRYBZ0EqDkD2VZedZ9f+BBBIIwR1HsBIII6jawAJnI6MdQ96tVacsxYJEnN5LNtWjFeupSBTnHs4ZHNyFG2tF8Cc/uZmY5Ykn4o7+7wnmoLj4kMnCkV8ZAPMTR4DIDkx81P0Kc4JF9GRvhxo0Y1yOUVvypvOhVWOFaEUTGON+LamaddUmuZPVjSU4arYU7Z3efKwNtG7z/rWBtwqJ6W3G0dWpjW1xNKno9eN2LdurknarE1exDMlmuSjhgN7bv7BUNyGcAXpVlcwLXNypLXqMEE6F0s3LEryAyEIWJ0pI7bvYKx1QPnEjxSRwMyEHSVLcAn5bB/0EYrAPMMy9UjqabIaxcBz/cvvK8mpsFD4WRgRoY4U9DRkWvcTi8o2zHJtQ4lPenBcZwzxOtuDhQVkiJdJGklRqojSZVlfk3cZYRNItmvFGQ3IhfwaXTTLZHm7yTSFmZndjzN5Srx1Yxla66WKIgikVnyVw2BZkUYTkNtYdu9Hlj5wWOxgqZSQ3WAT1bg0ygRkjGLm6rFZOMq64D0eQ9h3ZHCOU9rEr+702FrWAthOIOgY1RIC1Z+IOpUjBwfZLzSFvVcH3a1UShpZm4cCnDvbtcYLHGnDgTwRgFjhQSfTQq+Nsf48THJF0/r15n49dworajhSxRtnQozKwwykg/EDkwxygZaM8NxIgVsA5U81P0EHMuvqhHwUjeQkKOnMnXFF4MO/3MzMSzMSx6m78yH/AO3i2SSSNtSOQfVbKMMSKVJ/M0IZSyqsijq2hG8Lj/ZYJCQCML5tI4YhVGEXko2ULAAzAGQ81VLk8m4lmDB2gl0SrukkWltUpm4aJI0sFhlaMWEhjeFjhhSlp9oCujokoMbl6q8NolmXXHLpK9klrDIQSTelZbFmcROC+Tltt4T1mxWhfQqciU48IJADRnxDhRzc4OTf20R5hoCnWvTZVSSfdtonUz4icSWFYR0ZWCRcJCpjpTNI6MAgjPfaSwgZkrLgTwuXl4bAZYhRtR4UPFt6SeABoLyO/iYn9IecgX7gV2hqTzZZY20jqxjeIFY9CeRfhQr4rC/7JUj0h2Dqh6NS3lHUmVKod2chSbu8u2WpppKsBLHkOJVPWsw2/gj/AHl24dVvDZYbdmQ+G1CduxzHwmNtjTtgZNeTHqVdDzVgRsLQkGLKa/8AM1C4LV34qjmV61z/AIv7laohj7TZYpADgbTzy2mAVAsaDCJpjXxNk+hkYjSuFX0+hPOqP0bO1vnKsv8AdQP8SqQXMTHCyjRsAWjZCMPHkgfQQMFmjY9Awzs6lWZT1U498QrGA0xI8wjzM4CgBUHRfZd+ZD/9vF7VZlIZSQR0IsLLymjDk/mMTKClWXWx8al+emSME+e2iGHnrxN5K0cnNiNWeZb9n2E0tvd7HlagdUG6XkhnsTKxV4q0rA15EtSM0KIk7DEkE9RldTCrsjtpUWmEcbTIQZpYgXbJznPPZrE27KSxs7GxMuSvaEY/iQIT6xiFjqRpoyOraKx6vFK3q6SzKBIGKjwtuyrJJJwWXJMkcqGWqHsTWJ8rAXOgSGXeFcJocNCMpHUR8Rg8OPhyjOzRRKSHsAkHntbNavFBU0yMV/Ek2EqA4SumfLYTPAQzlQw6JYe1bnKjW+ear2WKL+YnUH7O1pHyrwqh+93eRizuzMerVeRkk+yMn3wxU5UkHZbdpRhbEgHp2yc+Io2y28EMa8JI6GXeEc0MivUTiMABJ7K9JViW1aBER8CWLPFk1OdRAwqs7MME8vT6Nedcj9Ds3fpofONyp+LM5Dx2F/OMnaVArZXwMMr9DZ5ylvuAb3Y4nkyRgKOrcSOLlDzf+4SSck5J9y78yH/7eL3E/CXWfG3gAyTy5nYWjAAsqiWQbGKKU5hl7x/KySRPpZWVhtVuy17EE4Cs0bhxtegght75eMkRywJIhjqzSuFiAcnaDeVc6q1hssw0POaEtcWKr5KlTNC27oY41e9YXMMJwiyvNZleaRubHJaOFmOIYXmbb9z71kAaSHQnk37trRn8feldf0VtzQHKvcmcedf9ppacitVpxD9Z7lfeX4wnepN+bazX3hUaOaQsV1ZSZAsjrPEABL+HIscSDeFiWRcxQkysumWzJJM7dWLO6QyBMwroQ8jP/BRfdO+1i1NJEihgiEYKe0d2ox85JAPjWpZLAind2ZsCNvpk5xAevE2q94TxffGSPixfiQzReY/ETZO/GU/MveX6GXvRwN/iVPtAJOAMk7cOOLnMct/bkleTAOAo6L7t3xwf9EXtjQHLN4F67MzyvnGWPIAkVxhSDL5t7EsyKArYdB+XRXl8DmNvTsti5uCMrGxnQis5G5t8GMpBu+dI/N03LcA/Ht0lHpuwbtqGOG5vFHi1cluybgjkSCFJZoYBpTZrcY+TXgQ+TSW95y8v3iyjph6MjnLWVLHz/dz/AN+Pb92yf3otv3bL/dh2SjYjYMssGRtDDerapKliFVI/EirR1ZJMyCCszDS533Rp0ljMtpGSzibZ7yggQwqoXwtJJJKxaR2Zj57DvQsPRgfcsd1a8fpGGPxoO9qhPRxy26fSx+BB6s42hk4U0cmM6WBxYj4U8iA5CsQD8OJzFIrjmVOcSrwZzoPdBDIZVAIZR3GGR9B4qx/xk9iQs4LEhUHVjMsYKwgjyL+/d8cH/RF7ERnYKvU7OdZWKIEqOShmWAFUIMh5M3tSvK41YAT7v4WL1mbZL28olKxWXrRt1V7LsctPLI3qbU5GFdgPTiSH87ba3+9ttTfcdsn195HZGDKcEbOiyAvGMEc3WvKhUwTH8NjkNLE8MjRuMMPbFzZl9VI9saGSREHVmCjay4knkZfCWOn4wODkbWAGKyjpIMn6WI4EP/bsRgkem1nvJXl+6PSfiwbp3jf3e9mCs7rWOlyEkAaF0ZX8Sj49ZHlE0aIzMyZA0RRePDv9skjyEFj05AfAu+OD/oi9mhlAhUEyN4tmdYlKRnLHk77AEnAGSdhVZRmZ1jHopRBmGEf9juHbVLI8jbcVh4QF2JJOScn4qsysGU4I6FkWUF4xhhzZYitmMQOcSL8piCpIIII5EbI2l1b0OdpF0yMo6A8vZV5SPJ/bR2+gi78bxefjT6VTiIH0faQYlcejHZO/UkXzjcOPgKrMcKpJ9OzSjxAJtogHimz+muBfDET+vaZB4dKbbn3vNuqetKXcpKxM43nWmkeVqFxopEwzV7VuWOQrZoVy3Rl427H8dOVD68Hdj+C5Ih9Itx3LIzUeKwNrW6N5VHVLFV42K6gOySjq0Y27MB4p4RtwYR1tIdtFUdZ3O38GPOY7a6g6QyHZSjc1p5HqvPpBXG3GjTxGP/b94lfloM+p3rvE+G3KgxjHa5W+YqSba6jdYXQ+vAgb5dpR+hp2QMrHrUeZBBwRgjy9274oP+iLaCNuTBcufAHdUBSNsk+N44pJTpRCT57LVjUZkfOPI2FjGI8RjYy4PdUD9WYk5Ykn1+gVmUhlJBHQsqzAsgAcc2V/4yMuB+Oi5ceyXnob7lHsTu1ZG83cKPoEdkZWU4KnI2nRVfUowjDUv0g+Sf8AmNpvmsfXntU5zcM9JVMfuJDK4yqMR68DHjkRdsVl6s7nbjIvghQfqZ52GA7Y9BFKekbnbgyeYA24R83QbJCHdUWRSzEAC00DTNpdii4RdqNk26EaxM/a6ndjNCLd++KVgzRJrSEyxrNcatK8P7qqQujFWX987xX5ciRbUK1hKjb135aneBADHBvC/Y3haksztl26LsAScAEnbgyea6dtEa+KUH9AiYyI2I+7iKvRlH6NMW8sn1Z3bxMSPT3gSpyCQR5i5Yxhn1j041dvHWUfroqN4Z3Q+nY5W+WySbPHJGdLoyn02lgMssA6KtaMsWjmlUiFNMR5NJopQ+JzM/pJbdhpVVCDorOzHLMT9KrFSGUkEdCjlmEsR0zLzxOiSR9ohAAJxIu3WD/i3sn7sVeP0TWfoU/EgZfzJ3l+kHyW/wCabS9VPqibRLI0iiJSXzkDfG6BQvOk1uLmdWP4Jemtz69ojHgXGzzK5y2tttaDpEu3FI6Ig240nkQNjLKervsST1JPtq93jTf207vs3TJwrepiRDoImNNzH+0Ne6V7rM8M67zqx7xSwYk07xpEpNFuTcojlSW0gMoGsJv/AHkd4WQqygQREhBiAdWdtg65wsS52LT4wz6B6fhDqWY7cQjwqq7Eljkkk/HS1YjGlZX0/b2lW+ZXjb9Zt6xmKOOCoiYRAzSzzTNmSRmP1IJBBBwR5wSkvrVQXxh0sQBNMkeTE/gMfMSL6rkbIhd1VerEAbWnDTyFfCDpX6GJ+HIrYzg8xMgjkKg5Xqp+iX5L/wDJdnhVVhaZiO74dxrHGWvTRqIIQzohtytLM8vf4rF3WSEBeLG2qMnGfgv+HViTzcmRvZP+DGK48edUu26t4CI1bLDIrvHFOqbpenvifeLYDw1S67b3uvHB2GEuzt3pn0AeJ1H6aox0Qn9TI5GAcD0/p4ODkddq8qShopfzeIPG1awFYgqCCGrKY52Y/wCkHb6M/iQA/miOD9EkLMNRIVPuWVI4nEIIII79es9t4IwwGS+tr1lF3eFiUrHM3DiXaOR4myp/Qh40kUyQ55DLp78aNJIiL4mIA2tOrzsV8I7qbVwIlNlh4ThASSSSck9TueIVZYpZkLGYaRFv66aG7YU4yTS2H4yB5ZJWLO7Ek5J/qkMiXI+zTECXOY3mR4Ypy6lWcohH0ULhJBnwN3W2dDG7K3VTj46I8h0qpJ2/Bi9JG2d3kbUzZ9Nk+VJ/+NjHJXpR1Yxm1aZNY3pIjWzFG2YoFECH2I7IwZWIYcwSq2TlFCy+akYOD71buCab7Ewu0UbSyKi9T52ZFdgseeGg0ptRqYCzyoDkZRJ5Y1jZ5XYq/PE9ue8ycV8vGgSIONalwO8PGP6pBXeZiFwFXmzb23pR3huOrXgq4mptGHm+jf8AEiST8y9x/igZOBtwlj5zEg/Y8zMNKgKn27IjyMFRGZj0G6t29+Z7T100KGWGPde9qwu7ytRZZBxEYjBwfc6bBks8pGCy+TujIxVlIYdR7kn4daGPzYmRtj/DwY/1JRk7bv3drAsTqBGOarctRwlgy65Dz0SSSSyM8jlnY5J2DFsyDxr4w6AYZfA3T+p16pkGt20Rjq1iyHAiiXRCOi05VinHE+W4KPtPC8E0kTY1KxB+jrsNRjY4WQaSWUqxDDBBwR8JIWZdTEIn3GVUGIVI9Wiq2J8tHE7AdWTdEgAaaVUXbTuyD8yuw2feSAFUjYr6dunXlGUiGyWrCnUsr5PXb948QYswJKPXhbum+XM8Lfa+7bSjUqCRPuIIOCMEe1JUdRHN0HJHkjeJtLDrzB9kaGWVIx1ZgBt+HLPNMw/AixgbuoPcla1YB4ZbkN4704bcOuwLr+Ykkkk5J6n2KxUhlOCNu4QWA7jeIOpU6T/UYq4TDTAdM6Z7DSnSOSjoPZP+PVhsDm6Yhk+kmj3bJFWkW6wnZPxl7LAfDeh/27ET4bNc7fu+yfDwm2/d1/yqyHZ6lpPFXkGxBBwQQfbHG8raVXJ2j3TaVdZgwPvetQU5tbx4j/b2+hD/AC1BSR+aXet2Uj8TTjps7u5y7szHz95JJIm1Ruyn1G8pHGmxFHMPXRu2bwvJA3o27bOC0ISZB5kFSQQQR5RzYXhyDVGTnEsJjAZWDI3hbaqrASSKCWC6EFLdgsL+I2mnXOZJN573WUcCoNEKjTn3Uco2cZB5EMgZQAcg+A/05VZmCqpLHkAiJDnmpdfE0khc4GdOc+5RdeK0LkBJl4ZLoyMysCGUkEfTpPOnhlcbDeN8DHa5iPT94Wj4nRthefOWgrna/wDtLdtSaoI4ai6QCskssrFpXd2PVviq7KwZWIYdCN5TsNM6pOu3/psvlLXY7R07C5MDR2UYd5Zq+nLIG0g4Zd2buRaC27UnBrglmfee+HuhYIUENOPlHF76OFyreBuu0qE5bqw5k/0yON5Gwo6cyV0AMsTEIBh5ZH1YVRhV6L7tz8aOC0OZcaJP6cCQcg4I2g3pdUqrOsy9Au+N5zXrGkhY4Ie5DF8GJ8d1jj7TKmk5AIB8v6VHFqBZm0xjqxcOpVcxwKeezuWwAMIPCvvUvxRJVP8AqjKf0+qAbEZPRW1HYkkknqfhxuJBw264wNnQqSp//f8ASEiVVEk3IHmqszS9+Q4jXkA7liOWFHhX31YqQykgg5BvKGdLKgBZxrx/Ta/IzN6Rv8TpsMWI8Z7689iMHB/oyI8jqiIzMxwqmlYrNiSs5mH5RUsuTLMj4zs8NlzzjwByC9lm+0bdml/w27NJ90e3Z3++Pbs5/uR7cD/6se3AH9+PZKpbwyoduxEdbEQ2rVY569iqtuJnX8aNXhkjGWXuno39MTlXnb1KL8VWKkMpwRtKqypxkGCPGv8AQ+pwNuGBzkbH+O4NJ3nHKUxFWV7D7WBxJO1SkkSjWdnkZ2yf9gPYsUreFHO3AceIoNuHEOsy7fw4/uNtxIx4YV/37RIPCEGzyyt4pGPs3c4S7Bk4Vm0MZGlUtIpKsDplXXC/jTSfuNdmGYmEg26HB/pTd2rGPV3PxopGicMvPyImjChZE5xt0/oXDxzc4/TiYGEGkeoBJwASTtu6v2XcW87c2FMzrWTZxHLAS02TG22a46I524qjwwoP17RKPCwXZndvE7H4AODkbW30XXlABSZRIyyx6G7pyhGUYHByNu0MwxKokHrw4X+XJg/a8ckZwyEZ6f0ifktdfSPJ+PDIFJVwTG3JhPXkhI1A6WGUb67h45udP6cTHJBj9UikcagML92mFPExc+hnfGFAQekqKm4d3UjyeYPO21bnIYzy1gp8Wx36lOXzUPEdoiHHBY4ycoWUqxDDBBwR7EmkQaVbunquqvJ4lMberV5ACy4dR5/0W1ynZftwnx1QABn8PkJrU84jWR2KxLpRfrBHgZc6R6KxJ0woc+vCC85XAP28RF+Wgz9zu7nLMSfYiF3VR1YgDbfz/wAbPXU92tHFAptc3SdeQkGrayBxSwGFcBx8SLv0LK+cbxyj2P8AjRa/zoMOPcVmVgysQR0PHDfOjDf5cFH+VICftdHQ4ZSD6f0GBNc8anozgHZ31yOx82J+MECAM4yT4Vd2ZtTHJ+sEZAyx0jZUYDKqEH3Ewqc96RvVppGGkEBft9zcECzb3qKwGhX1vs9g2Z7M7dZZ9bbRDiQzQnxL+Imzd+sjecbaT8Td/emeH+9FInsR2jcMvUbTIq4dM6G8PvJFJKcRozN6RRSqVjllTBOBHvWtTqiua8jliGEn9BrcpC32o7fGwIubAF/Qkkkk5J6n6pK8j88ED1xDF+fvbGfByiAH7mYscsSSfP3t0fg1d6WiPBVdFKfKl/8AwdtZisCRR0bUBwws00K80kTKH4cEphnhlXqjhhtciEVqeNfCrnT7IXXnG57jebo0blWGCp9kcE0pIjjZsdT2aNPnWEB+3i1o/l19R+57U8g0s5CfbyoQ/wD+uRdpf5Sp/vJ/QYuUVhv8Qo+IqliFUEk9BkRclIL+bfUwVrFmQRwQvI56Km5yrgXrkFRT1DR065KrIhcdWfTJ4rikenCg/wDlJtwoP/krsK8R6T52FRT0kY7dkXzlI27JF52FG3ZYPO2m3Z6vncXbgU//AJm3Yv8A+PWOyyGRzZj1qngm/wCI2k56G9VGyOWgSRfHAw2sIFlYL4T3l+Jd73ZZv7kCZ9kdaeUakjYqOrCGB4wJbCmRByXtEKfJrrn7pLE8oAeRiB0X2V1WpGtqVAXb5CO7OzMzEsxyTL/J1P8AlJ/QelQ/5SfDRGZtKjJ2LBAVQ5J8TfU27O44pEWhusGRUAfafe9uZDEzkR/2uIvlEmyTrIoR0QEckZ3kRirIgI6jjS+TY24839x9jJIesjHYknqSfdRdTqvkTz2jkfRJVVirLGGUhUupPJEgWwEzJG3ONT6Ejaq6pKA57jDQ+1hGWNQw78bGJvhxwyy50ISB1Nbc25rH7OxSS7zQXFkkxHaSei2lqIhJ6NJNLKcyOzEdNlZlYMpIZTkGZVYCZBhWOGHsq104bWpx+ChwFsTyWJWlkOWPltP/ACNT/nJ/QZe7DXX1Bb4SIXPLAA5ks4A0pyXzP1NVQZQzeFO8dmYsxYnmTk7a1k5Pyb7nRlOGHXodkZZQI3IDDkjMrKSrAhhyI9/d8avOC3gUEttBK8ljUT3pY5Tl2KWWmiJXWnFQlVvwyPEgFgYZ02P41fV1Zkw3wFUsQqgknoOyleczrH/jxII/lxaj90k0suNbkgdA/KOMeuTtV3pZrqYmYvEeqsm7rILBGjPUs+7Z9JkgZLEY5loZAhIYZRhhhJGY3Kk5HUNUrCZmZ30QoNUj2rHHcBV0RINMaeyX+Sqf85f6BWqzWZOHEuTjLGzuaWWFZ6E8dyONFWTYgqSCCCOo99E1ZYnCDqzvkaVGFHl9UPw67ere1HKjSwyh8mTlqQ5Xz9iMsyhHIDjkjMrKSrAgg4I96H8KjYl83IjXaFxFbqseimMnbQeFNGfFXaRDtA7KxKsQwBILqt4GSNQLIGXSg+JTF1140iZOHK69QDyPuJXlcaguF+7TVj8TtK3o1qTBWMLGp8vbLyZV9FHsVmUhlYhh0K2FZgzExyjmJZLTMAb1dLCN0m3RuODfcpq1boQopkC72XstiTdyckrSFGPtl/kav/ZL9fWpcSPtE78GsDgvZu64+z114VcHOmrbsVJlmgkZHXoVuUN8rixEiWtrO6WSTRC+W6iJ0eNijoyuvIr7iIMamOE2dy2BjCjov1SLqYL0yeszZVQOWe9j2qzKdSnB2wkvhwrehBUkMCCOoVhOArECQDCMQQSrAgjkR7tz8OCpB5hTI203zCPQAbKc7ydScLZj57R8pVDcueDsGZGDKSGU5BwLn4kQC2l7zLvABxXsqOUqc/YiPI2ERmY+XZ0T50qqft48afJiAP3SSSSNqd2Y+vuAZIA89pTmRyOmTj3I5pIidJ5HxLWkSOWN4HMMxIJV5VnkNfeBZJVOlJ7FaWtJokXGRlW9k38hV/7Zfreuy1YKQWS6uuU80rWbU1mTVK2cDCr7ASDkHBG1beYlj7PbVXQnI2kjmKlUXtcarkwdmq2OdabQ5/0pYZoHKTRsjjy2VFUan6Hwq7lmyf8A8D6uNTpJHVjoXaVg0jY6DkPeDhhpkGR5M6FcHqp6MCJwFY4kHJWIIJBGCOo9taIzTwxKMlmA2uSCa3IynKltK7SnMrn/ACOzkt2GQdTGVJt85VmXkJVEm0vzG/U52VmUhlJDA5B3NuOX9o6Fk5EEkcgYOezQkgBpWBxl7MrDTqCp9vvxfMU+hz7qKMlm8K9dmYsxY9TtNYPEZZFEiNhgIJV4RhIM9YnUUs0zCFljcSwMcLJtJ/IVf+2X6CBahr2GmEvFUpo2/hf/AKm38L6ybYq/dJtir98m2mr/AHJNtNX+7Jtorf3ZNtFb+8+2iv8A3m24df8AvNtw4P7524cH9/apHuqCFGg3motkZZ5N3Uly8m8JTk5Ldm3QP/7GY7cHc4/95OduHuUf+4sHbRuQdXsnbG4x0Fk7Q3N0xhVKzlQcof3ruC7uUUpEB1gAySS7ops1WZLwVTgwtu3dluGxPuyWZmh0F4XDhyHBDef1o7rY/tKfgI5X0KnqpQMNUeT6qCJwFJxKOhIIOCMEe2h3O02P7URxtEMyIPVhsTlifU7Rd6tX/wALONh+JTYfmhfVstSWVUlOlIyoBkpxRSTrDVQSSHm01vfA3am7YYZHKNJxZW3nT7NasKvRW5/Bj5a29FPuAEkADJPTaQgYRTkL1O03NYG+6MbAlSCpII6GrvAxs3EUHUNLm1u1WhNqm2uIc3ST+Qrf9830EXMTL6p8ZHkjOpHZT69qdvGiSbaqreKN0PrwIz4J0P6PWnUajGxX7vZRsNDNjI0SDQ6xvBei7NLyaMYXagjbvtzJMjGIxlZVsposS1bLKZI20rI8DKzAAkr1X6qIYJY9FGds4iJPVm+CCQcg4I89SSeLCv8AcyGU6WGJgOWxGDg+x/wt2ov5ppSx2h+YD6ZPs3dXllhscgqK0b66slOvPw1HFL5jZ3Fu3JHG2p5tZjCwJHGI6VbDvIQZJN6WVsXpXRsxqdCG2xnoUrq83RODJtIijDJko3T4C8onPqQPcTuJr/M3Jfa/OvGfRnX21LFmvMr13ZXHPO9bFaWlSMcHDnZ5ZJB8eDnJj1Uj6JHdDlWIPr2qRvGEk211m6xOh9eDE3gsL/tYgsqyWFVuYBLbu3jXuGGrcISUZSKfelOV60LyoqWIMQSBHHyp9SsvJHkXDYmGGIyHdGXmeYPRvqG7sSr5sdR2l5FV+1QPhpJgaWGV8tnTtC6lOXHn5423j3Z1gHSCNItqlWaXWyqAiqQz66lfwLx3HnVsTT2sSyE6o3UB1JlZQCTqIAmVacMzMPxpVBnaF2ggtWWP4ip123U4kgt1W5gjiAc4JHicZTOG2kQocZyCMq3vHlEo9WJ9qJqOM4A5ku+o5xgDkB7E515B6Mh9ipkZY4X1LFsIi4BPTeGDOYlblEFQfQRNiWNvRhs64Zl9Dj6WJmMDqrEMh1qVtzBgzFXwc7bs3lQeW3u3eMbGrIjmMvSZogyOtmDoJMmJeHMuuEnkXR4cMrBo26NpR/D3W+1lIJDAgjy+lRdTBfU7DEkw+3PRmLMWPUnJ+Ijsh1KcHbddVd57wrLGoE+rUyTbg3lC7u275bMxJLGXd2/ZA5moWsBcKHo3U8VSYbVWMFuu7KQFkQkNXfd9hjy7W7twhA8c8M6YJirAy7bwdkgqwMe+wM8vsoT8C3BJqwNWGO8oNEhIXGk6SI2Vhw3OFPhZlZWKsMEdR7r8ljX0X2v3F0fmPNvcgGRMo5lo+W2lU8XNvtZixyx2ogCwJGGViBkO2TknOSev0M/znPqc/SwOElVm8PRhIhjkZD1U42rEG/u1j0fhqdoppq8mqNyrDkdo7kU40sERyMFeAqsyKGQkZeCzTeJRIoJjboVk5aXGV8tjHkakOpfP6VO7GzeZ7o2TlHI36aR8bdto1L9WxnAjkBbbeU0lK68MqCaDJMe0U1p4nNDec+cgcH9975rOUeUhx1Xcu+b1u0O0OeAhBdv3/uq+5j3pRhWeUfNj3VuqKWRHhtVURDLYbfdG3FbksPiSGYmSOX2SMs9eCVjyZeG5ZSpKsMFTghfxlCfnUd0+7L8wj05eyMBQXYcl6Akkkk5J9qIW6cgOpruqzKqfmyhb2J+HSmbzlcRj2Oq9nhYAA6nU/QTcyjeqJ9NN344ZfMjQ20b4jqSecc2DtbTRbsp6SuPZDbdFEciiSIHIWJi2p6spbI76zQ1pAXVGjYDLLwJV78TBwOerUj+Lk33OjL1HI9D9FLyKp9o57PyjjX1yx+Pb/jKiHq5gSdNukP8Au+0W8JWVYZ4xYToqxVYIYZ+yuD2dJA0dWhI08k14OkMJ1yta30kcabuswM0HidY52p18Ssbe6pW5S7x3UsQSZXWSCUZjsSQyRYLAFT0agRLBNXY8s8trILKkxGGbuvsDg5GzgSqXHjHjHtjXMiL6kbMcsW9TnZVLEKOp2kYEhV8K8h7QgUan5DyVnJ5dFHQI2l1b7SDtMumaRfRiPZa7iVoftjDN7E51ZB9ro30D84oT6Ar9ND34povPGtdo+dawvoUfbeXO9Zb7n1+1WZWDKxDA5BhvxyEC0CGByJbNByFnrkHPMHtGrlMgf/JEU/JkBz1R4cHGko32kFTgggjy+PEBq1Hoo1bAFmA6ljtKQZGx0HIfHgndKEEy4L1bXS/CkLKI8mJyZIzuyLQHuNgaDpiKor7sEjsYq7WOZXeZirq00SmCLHDhevXtFpYZsOSWZa9m9uqckLp1DDpu6WvMsvYkLxONVnd9+k1RBahczU5DgSVY4HmBRwgcFH2swyCZo5EINhdYGyOyMGU4I2kQEcRBhCcEeyLkxPopPsHcjz+Zhy9iqWOFGTtlU6YL+pJYkk5J8/ZY5yBvVUO1aLjTwxk4DMATYl408kmMBmJA2r8xOvrEfoOsA/xf6aNzHIrjng5wiBLE0Q5q0bhdt4c50b7oIT7tW3YqtmJ8A+JXSnvTnCVguH8km7r8LFZKc6sOoDWohpaNiv2h60o0uDGfIyVJEUuuHj+74x7sYXzY6jtFyJb7VJ+g3d+ILlf+7A5XaCF79OGqgzPEdSC2kQQQBytSuNDvYRrd2nVSNVirwJiPeNpZpQkbExRZCEEqQVJBHnFfdV4ciq6eixV3YS1ZjBIDkbbv3sOJwd5RrG8q6Wfff7Py0SbVTWa/Uh7fFgLOgYEJONrNSOYies4IkGoq6MjFWUhh1Eb6DzGVPJlkTSQVOVbmrbJySQ/oBsiBmy3JV5nZ3LMWP/6VMjUxwvqz8sKML5+7Lzjgb/EqdqvcjszfbHoX21CBYjB6M2k7EEEg9R8dOcUw9MN9PG4HZZj/AKbhH23ihQ1Qeoh0n3YKksqmQlUiB70naYK3KqhL/wB7t9m5TVmtypPFhGdLm/AzKty4Cvi2/eu8k+dvmyT9tT9od4rbrLFM4zIgLb0sObLzKkbJMznbtEbeKJRtriboI9tOekCHZjGpw0JB21QfY42/A/zG2mD73G2iHylO3Dj8pk24Q8pUO3BbydDtwJPLSdqu7rludIIYWd2PIWUljmZZYnRhy09If1ZvoKc/ZrdeYjISQMRUqxblM96yRgMYIRajazvWCsCBAzoIhvGx2eCQjlPdYysParMpypIO0N10BVsaT1Xc+/oqwWGYkQHljeW4ohAt7d44lYMWdAjpx65JDxsWQpbVwEsxCRR0Z6esF6r8VRzKo4AMb+EnZ0ZGKt1Gw5Rf7vs/dAjHXq22lU8XNvtZixyT7x51l/SQ7Sfh0oE85GMh9qkqwYdQcja0ALE2OhbUPjxc+Ivqh+nr97iQ/evLbeXeipyeqn2wwTTvoiQs2MnbFOr1K2Jh5PJauSDOp2Awq9mRPnTIv6VbdetKCsBZGGlzaeR5DWszZ0/KkdHjYqykMvUU/wCbrf8Aamy4mmt1G6vI7RkjBwfaJZFGA5x6cTPijQ7ZhPVXG2hD4ZB/twZPyrnYgg4IIPtSDuh5W0J5bbsvdn3lRaIaI1sxlhZknvTtVaxotKxCpvbc9W5AxpQcK3WJR4viLHIwyEbHrw8eKRBsqRlgql3Y9BorVxmZAz+UVr9p4rLQLe3bWYCFAj7pNeyhsKlGZa6PoD1N5W5Xlmp01Zjkl92yoO89AfoIIQcPYo7aKa9Vhk2M+7kHPdE7fq+9t2RnH7jQ7D9oKKeDcNYHan+2bVDiDd1aFScsrJubfERv092q9xe9JBPW/Z0yaeLdrFhq2TdNVjqq75rEjoH3RfkQNZpPMp6Tvu2Qqyh1fR0KVpFjVu5lckbFJF5IjE+bFHHVGHvxAtFMoGT3GAvEdoZFOViAjHuWefAf7oh8eD5qj1yv06MVZWU4KnI23iFO7qTqO6JJMbAFiFUEknAC0khYdqLa/KCZpWThO0daHOeFrqx+CNnb7nszSDSXwn2+wfxNMjrLXGRsjpKohmbBHJHrxvFero64YSptZJW1OQSCJHINwCUJaUACXOse+JZAMayR6IWlYKIVZjt/CQ+rSbNA0h4ks6gN5nWg/BjIHm28pGqCa0uO0214ke26762a6pK7YVxwX3xuntYa3WQGfBd195Y5GGVRiPXh48ToNsRDq7HbXGPDGDtxnHhIGzMzHJJJ2iqs41OQiddTWUiBSsunPV0ryyc+i+bTtXijrMq8R+HjUksksNxncnEaAexZZV8LuNlu3F8NqYbfvC55zsdl3jbU5DJsu+boGNSkeg31N0avCf1/esTeOmDtBvaCGVZYktROpyGbev7Nb4pE2w0e8fCpll3RXcpJUulhsm9d2wsGioYcdGH7Y21GFVAB0FveUe9oBJwIRNAvfXtFM9YIzsLNIf6IG3aqR6o+3G3afFHJtr3SeqyDbTug/nmG3B3Oelycbdl3Yem8WG27KdESzzDeUZWGF5SCSSSTkn3H51YW9Hdfjo2mRW9GB2kXTI6+jEfT0KR3huR1MyIILYOZbFajmKvXlD4wzvamIKqQinqvu15mgmSVcEqeluFYpQY8mKQa4zu+VJJ60Mx5CRND3o3it2FZcHiE7U2WQvVcgLLjSWUqSrAgg4I95IO6HlbQh6bKJJVKxJw4fMhViOFC6vuNdVOuxIwJ57drii/l4FDD89DfLXd2KtzRK8OVL6KdWeVmpOkTJnXUkSvOBDvCAwzYlh23/uN3jk3jWqPERzswLHI3NUYj14RHidBtpiHV2O2uMeGPO3FceHA2ZmY5LE+4kbyE6RyHVgsNcam7z+WziaYgudKnoMwRdF1PtJNJIe83L0fnVrn0aRdoP5e5/wAE+HBaSZBBaGoDkrWKjxAOp1xMeTbV53rzJKh5qdrldCO0Q+A82X32HZt0KvR7cmo+6nOtOvoyP9BP81j64b6eTupGnnjUdku2o10iUlPt7RUk+dVCn17NWk+TaUH7ZKdmLBZDg9CQQcEEH3K/8TXesebrmSLap/N1v+1NpZUeaeGY90SPoaSN4n0sOfUG1+PHHbHibuS+6laaQgLGeeyQwx5wwldep1o0n4cZnlPnISedmxk/2zaKjEMYjH3EknJOSfZueSSKZgUJRlyVrstWwas1gaIzqhkeKtJA9Z00SRN4dzbxt1rsFeYvFJXcatv2k3OscktuoDwgcyRe8qliFUEk9AkCq2H7z/a7EABmVQOgLKh1YIJ83lZs4yAevt60v+Mu0H8vc/4J8StadWxkEnkVerHMC9YEMPHD02pzMDwsAnnoFiFVxJHkxN4T7taBrE8cK8izYzveZZbjKnKOFREg9ytzMyfdE/0EvMRt6oPpo01yKp5AnmXfW7N0yentjnmi+W7LnqBdyMTQo49dNKXo5Q+j0nALKcr93CfqBkbI7xSK6sQykFSUQ3KdiNQI5pEOLX81Y/7H2jlVlEM2dH5WrrwpXrTECOZQupoJlkeNo2DqSrDhgeJ1H6ZiXorNtFHKwDHuKeY206lKquUB720kkAADOZCOiSWZWXQMIn2iKQjOggeuhB4pB/tqhXojHbjOPCFXaOV0lSTUSysCNrIEkKMgy8A1JsJ4+1GvMSYLCAo+7pZIrsVS4upowxglkeVJ+IgLRTIJoTvPd0ax9upgGsxGtfcSAlQznQh6baBEuWPBQjoZiFxGohj9TJgnQCCere5Hzq2R6NG20H8tc/4p8WOQsVIcrKvgcmK2dEoEVjONUkcsMhR1KuuwlVkLsMxSELMs8LQyaSQQRlW9zdYFeKxdYc1UqmxJJJJyT7tVgtiEnpqAOzKVYqeoOD8evGlyqYFUCzFrdPpk7sTt5t3B8BHZCGViGHn2uRvmokn68Ws/VnQ+m64llmSv3HV5EZGu0ZY7M/EBizI+AYVUZOpx6xWU08F0AT8rX0lkhjnZssuEcxxySuEjQsx8kpRVQHsOmrqBJPnOmInPnI5kIMs+cdF1RL0QnbjOPDhdiSxySSfdrzMKqSqMtA2CL8KcCBoiSqgmM1Z1eeIyjMM0cjZWWeKlTkEx1LlOJxkrzrPEqKs+Vmr743StYC1VDGo7YxtHDJKcIucdSkUUR051ybGUqS0eC/m7OAxYZdz1ZmJOWJJ96vzjtL6xZ2g/lrn/ABT4wYSqFc4YclZLI0ivaQtGvIMYTXOoniVpO7rUKNVWZhjOY3kR43ZGUhlOCPYASQAMk+W8CK9WOqp6HS3vA4ORtaH8RKw6MdY+OjvG6ujEMpBVriLbhN+JVDasWI/pJeQSP0GT8MEg5BwRtFvPeUIxFdnVfQb5tk/iJBJ+v7yqyfO3XXPq1TeG4wksM1a4kEikMrbwSKMxbvrqi+bPYmZiS2GPUkknJOT8HdzjjNE3hlUriqGerYrNzeu/EQUEGbEOc8OOWVDu2x/6fZhcMVWQONo6636jwakJcZjbd++pqRetai41Zhw5Id5bmgoGOwXkkrTRiWFeJNKuFAihHRXeNRpUZHozs3U9Og9+rzlZfWOQbQfytv8A2T46sJFCucEclaGeWs7LgFTydGrxXK5arkvEC3CT+LjCH56LhD7N3JiVp9ORENSi6+ZyobKxgRg+9aikEVSZkIWWLut8enaarMJAodSCrpeqrAyPCxeCYaom+ihUGQavCObbOxZix6scn6ESEjDAMNtMbeFsH0ZGXxDkeh99HZGVlOGUgguxjtiaLkJoda7V1jFhLKj8IwzNiovZ7FuJuYCatqlyXd1pl8SK+GWPclXe1+tvOJg9OTvTjft9JLscztzkjwiyyLZYq+IZAcaXjeI4dSD8GmcWof1bG0QxVuD/AIfQKyuArnBHhZHlrzK6sySIcgy9nuFJlKwzNzDWomcM7IVnT5ybRfw0EY81XtD/AAN4cot2p9tQfQ7uljkzRnZRDOwCvarmtZmgMkbmNiur6Fe7CzebHSPpFdl8LEbao28SYPrwyeakN79dw9NHPNq0oJ23ScTW6bjP4cujaND2ioW6kmBy9aWzagSNcvMo2hkj3V+zu8ooO8McJxveKElV1cNlbQpmhk4Ydk7yjDGOwVXQ4Dp9rQK41QtkeakYOD19+FtM0bejg7FdMe8V9HQfQo6uoRzjHhaPuloZeSN5wXGhdYbKkiM4Vn3YplimjYGnISWe3MXiLsMNYkMmPf3rytIn2VoF/ok3IrH9gwfp+ITyYBhtpjbwtg+jIy+IYz0Pt3aw7RwWOEmUxHZNcdud+j9mdtnxYgE8eAWAJ2sY3TTkshf4qeR+AJyYwN1A84a0cT7W3SZr6scL21yjRTz1ZCvkDh0kSsxGk8PIypeKaE6vIfmEkcoxKMN9zwunPqvr7oOCD6bTDAv/AKmM/RI6sAkh5DwtKjPFlh+JGAG23TNYjo74SJyBLBHFi26mdlU5RAI198AkgDqdt8EHel1R0WZ0H9DgA4mSMhRqOxJJJPMn6lXZfCcZ6jVG3iXB9eGTzUhh7ASpBBwRzBsgSL2oAaZakh2/ZlEBnmtYFOMjVs6Gxv7jW1JiEPaZBuueSzcsWJD3pLcDsbC4O8VPlODsPx0wfmqOW0f4imE9TzQpNJEcA8vtzBL1Gh9gs0XId5R5FI5QWU4Pns6Mpww/2PuS84LDeqQn6OCfQVDc1HQ1YhU3bvOcHK64OGff3fHxb9OP75412tScWzPJ11yO39D8MH6ufreITyYBhtpjbwtg+m6Ks17d9mmqjiocob1S9OIIKVWVKNfkkoUvuIurwPYDxwTndNOxCL2YyeHzzOp1WiQRrgjk2BKkMDgg5BkAlUzKACPGsn4iiYdejjZJXXA6geSvG5B6NsFzleRPmrw88LkN9pGDg+1+e7y3+MY+k7XY7J2TiHgcQSaff3U6R7xrSO6qqNrz/QgCSAOp2nI16R0UaR9fune1rdVoTwOQCNLreoV94ScalO/EddaxbhdoLr0bJKRXF4JaJWRd7iYCKdYQrO0tuOOMO5Oasg27QjeOBD+sclZWDBXXyI4EKsHjkzC/IiWpJExUspHUEwygZ0Ej1IIOCMbLIwAVsFR5JMGGkgOv2tGsuQpLEeTxMuSOajqdhz3Sx9HA/r8PJi56INX9BqSqy9llfSpbVG4uidzX3l3Jw2DPveu025LF/uCWxFFG+1R3SAQyoSivKpV64KmSFi6Dm3sicLlHyY28Q/EAMQc6lGpGEzZ7yqdhYBGG1jbVEfNDtw1bpGTsGVcKznA6BDxMYkQt5bSVMnmhjfbhSR7rsq6EETR4/r7d2BV83Oo/0L+dg8zZhXnt+zt+cwXt2DDrNGZIo93X0s6kUoMGM8N3twyAxogfqFFxZ+Rhgjmz0e3JGxV6sYYdRDfD6YzGgYHKNNYQd/gkAnDL2qP7HG3aY/Vxtx4/7jjYWyBgWWx6KXYameMKfzUEWVWbtBeJfG0/DTdk9VYo5kd42Ne9R7Polifi1pc8OX+uVYO02YIOIicRwmu/GIbc8IdHWJjGG/oMcjxSLJGxDqcqWcxSQbyqLpCyAstiKOLfHEhGILUXHiHapoHkiBDRhzmMSUrQAc8N/LaSvNEoSZGlix3DJXKrxEYPH01ROsylW8eMNs6MjFW6g7JBK4yEwv3JUXGWLMPXXDFyV0U+leiigz2YQAOotb4OQtdiWUYWTiScTicRtedWqlvWtZ1xX1UGXAdt7bom3dIp8UD845P/AB+pYEMhDqWicaZFhizThUtqNKZZY2vLpuWV9JX9le5Yr8o37hOStZ4LbFgjQSnkWk3G8RWbiKhzkCVqhiMkUZMkfJw9yRjlVUH7q9a5vCcRxK8rnzB3dugcmFm4OrWrli0waV8geFQM9NlhmbpG52Tde8XXK1JNPru6WerC1S89Z6T+OK/FVitypVscaAHuSf8Aj+4L0UVpK1o/gSZjzvmhZXfV2BIndw4JC7u08550T/FRBF8mk7t9znekowAVXyFWvvWBi0IlGfEsMJssrWN32YZcaeLL+y615jJZnWOoe8jWLcSQGrWevVrnxL/6anWRmPp2ukvgqOT6/vSVflwQps2877dLLoPR5JJDqd2Y+v8A5FvH9q99WpVLzqo4Y5DfG9G/97KNjvfepbBv2cbNvG83W3OdmnnbrM52JJPMk/0H/8QARRAAAQICBQgIBQIFAwQCAwAAAQACESEDMUFRYRAScYGRobHRICIwMkBScsETQlBi4YKSBKKywtIjYGMzQ+LxU/Bzk6P/2gAIAQEAEz8A/wB/uaQHHA/7raCYKOe7YyO+CecxuwRKo25pY1tZzu8dEa0TEtfTse+JN8oFXf7YPzusbotOCF3ai1UpFGN8I6lRNiP3PhuBVKfiO2SagYNGoSyCslCYd8IRzdAWOcR/euB8ELSiI5z/AJjG6MhgoOHAoF3NB55IUg/xUQVmA/3I0f5Ra7kusP7VnQ4ptI0uOgRiTgEfrBqaLSVxJxK9Mvbtf+T5dlao3uhFom7MBmLTCYTaQuY7QfatFxRKICLW9Rtr6tQTmtDWUbZucTCqMkWBjhRtIIgABC8RQqc11RHFXiw+B/5HCvUJ6e1AiThSD5hjWgYteLwbR4t5IaA0EzgqIh43IgjxItQ/pyeqY7X73WahJNrbc4YgzUI0dI2v4rW3ETIsTz1Xehx4FOECCrXmxoxO4TQE33Mo26JXBEypKd0xnn5gO8SjWQ23Sa1eKy33GKvb+D4AWlyFTnfM7bu7Z1UbwflOIRHXo/WLvuEvEisofI1wIB0kpveaG33hHrhwvBNibCP84ensc3ewlUVK15/aQCqWjI4ErOzf6wEwh/BEQ8EbBfyy+kw9+0NpsGs7kbTkFbm1luqsYIVD72Dy3ixEwfRi0h1wFhiEJPi6ulpRWAVUxgbVAWAExVRg7vvOJEsgsQqi63Q/irx2/wB7hM6hv8ACu7RUmjyFPYWgm4E1+FCrA5q5ra+QxQqa1z2hrdQYsYc0K2OvabEOBuOGUmLdhkgMw/yQCMKQeyJdRiGh4EVQ/wAPnnRnPDIJz4mjzqs5okMRYE6UdBqRFfa+Y2NQkMvqEO01dUbJ68osKHyPbWNFuhUbWvYwtgSGl5AEU97aKemD4okOz4SEQAIAkmoBCbXmtzgbZ5fM1eZto3VX9sLS6pCpzvmdrO7wQiHENBzUZH8o+CNQRrOS0N+RuvvK8UDTzivSfyrwnVOGOIR7zNN4xyUhzBvX8OJfuPsv+o4aXH2RPdbmnNZhKahF0LH0g+YXWoHviAgYjEKk7rvsJ4GxGDi04hM5FCTth9kexNQFpKNcHVuOJ4dHB1XZfa2zXUhl+Z2gWoVgWOJwNlSnmZ1ECZWmLSU4dVugWaoJ1QpaUEwj9hJKcItdiOYTu9+g/NxRyH5XXaDxXldaO1Irc4dZw0A7T4P0n85DWNaMjttR7e08kKhkvDbNJMkBIFvdGiMlfUz+1eof+KCpTmmN4FZ1BMGa04TiSNIChF5F7CZ6kTEnQFa7SVg2vkMVCT81ps8oWLUbM+cRcYOUJs9Ys0iSB/6zW42uG8Ijqu5FCzUeafZt9iiM5p900xhy6fBnPpemXt2VzG1DWZ5AEJtYcbzoTTIYE1DQE0QaOeteejaYlp0K+id1wf2K97uQEE4RadSMSzbWE2Bdtqdrmm1DA3HTk+6prtdRxn2QEYIHOO73TjmjYInegY94CBFw8H6h0DZouTj7o9pYNCOXGHVbqBjpQtzZkbSECXCLiSRAAlUg+Cw5p1uNaohmfzTcdoQlHSazrRkNBKIqOARMG0mm52NRThDNvihJz2t7jBie+TYIJog0ZtG6AAuFi3HisGSHBC501GDHm9h+U7rkRAuveBfeFa3mEKioodU7k4T/AHD3CM949wEJjblx82rivMbT0vUPx2Pla2ZOxeVrZAbEbcALTgFXTP0+UYIVu0m3h0BZSOIY0aM16NpymYOkWoDOo3aWmxAxon6/lOBRqcHWaCrjjj0QE8wOyvcmDNG08k4Z53y3ImQ1ZcbN/hMOiZhOq29ifZWnTlaIqOcXH5WwF5VNJz860MBjrJATQPilvfIzqmxiAM2cUa25wiCDYa6lnnObLfpCLA+O0FD+HaNpYAgX0cP5oJv8UwRxmCgRSncAjR5rg1xEGExNdkZhdZvw23Dq13lfEaD1mOsJBTet1bakWkL0iHtkE3s/yGBVHU03t+03GYKs/BRrbp55QswujuQIo9z5LPbnmdQAJESoQzG3dP0nl2IrzWme0yUZ64cArQLhY0aEASn0jWnZGKomOdxgE5wY3XIqBf8A1kpoDWk6AjRtB2gApjnN4khBzX+wVJRkcCVn5n9YCoyHx2RioEZugGrVJAdaidY4i683LFO6rdpkmDOPsN6pDHcIJgDRu7AbDsO7weqB4dMzCMxtVh6PNWBQkNaohnu3S3r+IeGnU2XAqgozm78wbiqQ57g6EQ5o5CITqR7oC0mYgoRhRx6gnehRt7zZtsvkhInQAok52kckIuzheFHOdsFWuCpTAftHMqjGbnvsYAK9KaZOpLxgKsSvOKnjSHCSs7pQketBn9yBMItkatEUTnRzTGp+lGhYDuAKBe07nQRpIsfnSzc0tMTNUtK2jDh9pzSCNJBVI58NxHJZmc12iJKbQsaRsCa4gbkCXEoGMNJ9gqoZw/02bDFGRboNY4J0n6rDqmiKuj6pe/YHusbaSjRiOa3yRPVvjAlUtIXR/ZBNo2x2mJRcSEZBGQ2KwdiHEIsaTtIimUYaXFhMCTfBOMezvFThsmrx4Lf79iZgqtv4QmCrlCA1RQMTrhNBo4v5KlJpCNUmpgDG7GQGTyi9VQpaLrsMUBDN8zm/pjKwoSzGxAAjcBKaIk0tNl+uC7x61YAFxkqQwFXlHMoANadQtxR7w0XoVvPsEJZrai4aamIVQQrDXQDthgUPkc5p3FYTJWDpH2Q+8f8AihM7Kk0wpH4k/KMYTsQHVYXiZGhttcUDrq1qlEQNFrdRCpzFh9DqxrCN2BEnjWvl1XnCtHvO5BC1rbNJMGoVEuuwsGUmD26Hc4hEQeNVupHoeqfv0nVNHubhaj3nnzOxwqGU17EZ7ke19Lp7ndpeLRsXmY6YO/wW0e/ZwiX6vcqHxCS4AzjUhTmA1EQGhfEH+Ci08l8Np/uCNFDg4oscIm6QUHj+1Z8I5tk0wZxcM0HNAqIe6ZVJFuYY15orFxJKaM1uwKsFj5VYO4pv2m7WhXsRsxfyQkSKoHTVGwTTe67RoEoWLylfY8QO4xVjggKxITxEJoTgHSmU0RJLXQ91Iso/8juCMy4oVF7puO2WhCeFetGfFNMCU8ZzP11z0CKBz6PUO81NOcBpIVraNsmDX0oweNduuKhB41W6svpPLowiSfK0WlAx1k2k3oITKrO3wGD4g9re11XJXjwPpn7diZAaSiOqNA9yia1+kIFMAhrbUVRmBGlqcIKwC+K98hqbieScM5r2Pkc/cAnGJYGtJ/U1EQcx1xLIajagQ4AOlGGBnWnAtMXShaPlTSHhmmFvBPESBprCra48V3mnSnGeo26K1hcU2rPooCvFsChUx7hnx0TgU6TWaTyrREHvLQYjARbUjXsRqNI7uywr1KxepQMAnOAcdUZJoJ4wVIRRg6BMnUnk/Dg69sesNKAc0ANkAIGwCCbSQ4grqu5J1HDgSoubxAQpGn3QaSERBAweNdutAQe3S3lFeofjofNSHys9zUEO6wf/AGsmtNq2oeC281jUd47S42HasLR7+Bw7Ad48kKvzl/SMoKEn/nWhJ+iFuqKhmlOEQzTC1AxUYDPaCWoVgwgqqOnH2XOwvRHWa61rxeEDENewgOAxtjkd1sxrsDehFp3S3KIcBrkgfhcZFAQLdknbYoCRcwz0RaZhDvPAMBC4SrMlRg5rm4k1uAttCLhnZr5HFNBPGCiG9d4EjXUJaUSXHimANI0kf+0ImAdOpUfXdyCd137TIagnGJKxdIbz0ws4wTmNdxCALf6CE0mImDO/XljA0nJuKAzWMFgAuQkPCawsHTG8dr9zZHmsPA+oR6LpAJwnqFnHo/pHQuxyGtmg1x3BUhgdRqKMiiJ9U3qERm072PEEDVibkZZ4ufbKx1a8wcIHcQdSP/cpLG+5RkEASNgVKW0bRtIVFnUp3CCGbQj+8qlc+lO8gIDOogdXWaE12exxwcJRwrQqY91R0EiKNs+q3WTBGqLpqkObHR+IlTYzmUwZrerxlf0MGCfHtiYwLRLd4bUCsWz9odr6axsmuI8D6TyPQaZ6zZxTZAdL9Iy3m5DgEPkwGOOVwiNVo1J5i3UeaExmNcaRplWFSN+Hn63wgE+ma52wRKDKSNGTKLTmmAvRa4NJtdG0kp1E9zhrhBMo3s/oai2lj/SoP/xUXclnL4gmjSsc06QTAjSqOnY6ieMWl0W3xEZqi6xeGtAGAEU4BxGgVDZFExOT1V9DF8+B7b7m1cvDeoBXq8WdpesHTCuvHgPUPxkNX5R7x5dh+kZLla43oVNwHPoOMG7VNrOZVG40YOoVouMOaBIyx7C7EYKHcdfzQqOIwy7xwy+pYWbu3udbz8LsyYslw7UVlrpiArMERAxu1+AAjNpB4IGQ0n2CEgNA7H9IyCzDmhwGGV03H9POCpYbhUoy3oV7e3HEYI2/YfZGzo41DefAYtrGzwurJg6R3w7ABOIbuKYCeME4+wgmgA7a0TGNH3KsE5+dRODqnUcYgAp1F8NzXNrB+HmFUVLIangqlopbWEphLY6ngJ0BEVI0jeaiTwCAceICFHzKgBzRpB/iiXHhBdZ3uU2jZxgUR7BMcWiGpOaI7RPemOiNh5qkBad0RvTCHjcj0v0r3OAXmwGHFAVJhENbjLZFUfeOlx9lWdqPgQhbiOS87W/NpFuX0y9smDZn28DdhqMvCajkxdVv6AElHOO6KADRtmjFx3y3JshsCgUSAox4IA1u1ICxshapRe11TDeCBmwvgFSvINHmGB6wIJov6UWOeQW//kcVRUbKP+gBPpHE0rnd0GNhQkGtsaBYBkCJhxTRHknGATR7lOOcewCpAH8VRuLTviE9sRtEeCY4E7K9ycIZLhBHqgi4RswQk38oCWypHwoQtxHJD5HYYHJ6v/WTF55eBwt5+E1FakAqMOfAurbVCIRkNiDQDtMSi+PsiTzUI8UAAo9D7nSHPIKwy8YgzGKb3Wucw5sPteOsF/8AJRslnMvgnCLaIeakjKNzSic4vNrjC0oCCMXFVbgqggJ7Ue3JiNhkgMw7pbk8/ELi0QjUAifFGqkFutGsXtOIXpnkwbIbh4G8WhXh1Xg9qHeMzsXncwRiTbDiQnfMXGMcDirWm49lhU3JjY3VxRto86LH6WFOkwPaPhBzjiRnIxzjnWG4m0WBCZRPsE2X1EfMbHD7hvQqc11oWLat/g/tdyPgnVar0a7arkamNbMuOAE0axQURrOL3mJxGQ1EXFVluIvHY/a2Q4I/M/8AFaK+x1bnRqArEVWHyBB9IcS4A1lE2/VTVG46Ua+rN28eDwd4H5RzVgyCtjHQzWfrhnFCohlZ1meUISD9GOGzp/c6Q5o1AWlG0XnE1oyBDfmfc0b1U+n/AMWcUJBrG1MFwFi9/qrpNaLyiAHPbmlmdrNfhOB2S7Yd46bkPe/IBEqmpWsdSujJsCZCNcU17XxpHxYCMwmqOd0jU7B+OO1Ho7hzXlZZt4IyDsT9vGoIi2w0gwsZZajbk8wv5q7D6mbdCHzG8r7XV7K0Kjj4O42Hb2ht0Xo948lCQ0mpDrbyQ1El52CA/mKJ+Gw/po4cSqMBp2170TGKhB21PERtsVGc4c+gK24YhCYIvHQvDZNbrgvObhghUzNuxF9QsR6A+Q3/AFI2C99wwrKqjl9I6p2CGrwhozBrmyrtjWiHj+1fEA4wQpWO4FAF3BFpCOWwKlIo6MaM+GcqAF2xxkqU5xOrkmiBGg1omJ6YME4QdtE04Z7domqI526tFWtN4Q4G44ZBa58huVQe+0A3CqKAhnC4XDpG0L+0/TxajNrOZRMybzj0DYflOo7kbD4gEhF5ITqNruIXwmjgAqBgaSb86EU4kntgYFUoif3Vr/qM9iFRmJI9MnDTBOEHMNx5q0l0gGXugJXRTeJvPYXYofML/ppqAvKImcAvc49L72VnWJ6fp9KA+V0TMaimSYxrZSxMJnsjZ+CjYbvpZG4XlWuPueCFnTupG93bV9PwbPtL/wAq/wCkit3IJogNACFnYCxCx3zDbPR9O9Uvftb/AKOBEk3AItMGHG84IibjcFYAohZ7eaz2818RvNZ4UVE8kA4+yJI4hAOrb3hGEJhCYOv6btPt212P0UTP4VpFEM8ROJEFa93zb0KgMoCLhwQBPJSbzTiSg0BE5Lg/qHcUKo3wuPFM5coIVjVX9L9IEO2NRCuNx+hWq068hMD53A2zATW1NdphKIRIHsjE+6aA3giY9jYQ8AkbSrxkPe2p8t9SNv0j1En37e7EYqEni8ePtOpWomA2oSG1NlvrVznEhhRvs39r6TEbnI/K7kegZg6k2bdibOGkVj6N6RD27e1yJkwRjADxtp1Kt34Q6xTuseSJyizMaSULHW75r1fntMJsO8jJ5hfz6IMEOq7bbrTuqeRREPoWvt/c+NNZ1J5mdH4RkOZTRAdE+VsyvUTHivT3hsmsHTG/tMYRbvGQ2q42jpARR/1HE3ACo6wojNDgaho0n6DqMN/beXTij4shDrHbUEes7afZHp3OpSKPg4rWr8F/O3l2npMVeLN2Tymw5QJDSmdd26W9UpjuEBtimjNbsEl/8TXf3EbAtY+g+ojl2gQ+XR4pjS47AnOz3j9DIkKkDtwAWa6GyCzXclmuQY5fDciwhEQ91D8rMKFGVDNJaxrjIWzctYXpl7L7XGI2FYOmO0xZ1P7chk0azJUQzi5t0ZCWkyVIc87KtyjIaBVlcJH7yLhZeUayVrH0H0j/AMu0v0eKp3ud17cwRgUw/DZ+1kAonmiKsDhwWY3kgAECo9MGBFJnAjY50EBAOgQS5g4jWMmDrdVa9Mxx7OoDSal8RjQS4jqzTxnk6CeqdQRMYIWLyu5ZYwNI7yj3NgQkALABYBk2fQfUYe3ZGoK13ivTk5qw5DwOCPYYW7l9zs4jeEDCBrloKAgHi1zRfeNYyfdRVHW3sAjN2we8FST/AJRLbFWDQLFrh7IwI2GIOsFUQiB66MmI0gwVEYkDFveGsLC/ShUReoVC4Xk2BCpo9zaTl/b9AJg1ovJqAxVFHOYYTi0gGEaiEexvxPjj7K1unIbcDzRs6fq/AgsKyvtcDwIQMCC2fsgICkHmaL7xrC+5tW2pXizouOa3aU3qt2mZ2JghHSaz0NWQGBCo5GOIHEJpzXn9YEz6gSqVhz2iIBEpELzvbIuPtcOh+3x5ES43NHzHcLSoxc830htO4IcDeFNufocJjQQQqSDXEXtPdeNBThAjo2nQhZ4u5XCobh0bDyRR+bA80eli5aljStzxkBgQU2XxIfMz7rxbWELHNkRkaIpvWdyG1P6x5DYiY9kREHSFEgQjUDZHFERcLhSeYY1hAxa4WEG0ZdTfHRgdNIbBhWUBBrBcBYOg/uxvlNp+4KlnTMbexwmW4tMFTEDY+o64Jwhktd+Fd4zisGy6QrHNCoo/NgcUej9rZDcMmLSRwWNu8L1IGBBRbFr3OBicI2o9Vu6ZTRmj89h6Z9G+4ZCZtzhGRsrVVJRm1zEBCdzhYcMmpngGkZsJ50Y7lJQCgOazRzWYOa+GP8l8Mf5LMHNZn5WZ+VmlZpT6M/6eDIyj9yFASDrihQf+S+EB7rNAUQP7UXD/ABUesw3tIhBZoYM+NZdPNJNpCpcylaNEmEaQQqZobJxhFhDjG6BR8b93/s9gairRzXnwOPQ+50hxy+sCH9K+18jvTzBvVlrqqEVSjqNFpzcMUe9SUfcnpnJC0OqcMD2Pql79G85PSSPZBQiHi5zbdMiEDFzOYxrC1M8B6SD2zTBET2iaac4bDzTotPLehMbRlIi0h143pxi6jzbCay3GtqtDHV/yzBEkTAPFhjZETBRHWGrxfDesG9iFYdKPzjnxy/ayQ3lasjpNBa6Fd8HJ4gxudaG2wM5q7DAIHvmMAB9sTAYTV7WSB1wirw2U1cbj2G/26HE5dhyj3VHJhzoCIAqm3wHqB8EDBOAJ21ppiNh5p4LT7jemGMHNkZjagO7nygcDGpDuvbAmjcDcQC1Q6zMDeE2pwvxQqPicLFjWePZ2jQh8+m53HJi2bv5iiYNbK9OBFGNArOuCqAlEACoTCC8pqNEDeTN6/wCSlBDRqZE4HJ6ZHXAoW3EIWjp7MtwVwy7Rkv0K0r0iB3z+jA2VFPAJ21pk3MMQ8ARqCZ32YEGepCtpwuOChJ2nFEyOgo+Hua38dreiYB4YImBNskBGjBdoMShQuDWzEgAIBFhHsiISjNH/ALTYn/VON1yPz3x0kDUvupah+0R15Lg6RVwrbsq1Lynl0/VPLwHQ9JB9lYNOT0iI3y8F6p+FwdI7smv4ZVhwItVJOjfrrbwVLURexwrwKuwPNWjQVaNI8LxXq/A7a8RmESQ5giQQ14mIEQtCpKQtcNBjByfRtjvEUKSlboEA8Bd2Tqm0jgM4KLaSjDXAgC84QVHNjmuqhdCqGW7OqOpwjrVy8wu5dL0yyXnoGoI1nOENVeXBvXO+GS+o+/gPSIe3hsW/hYSIWvITAtxaawiIki34jKnDEawmnOAxAtGIMkwzGqsICWsIVHweNvgL8wfDpR/JnL0j8p3eHoNYTyJ09KMyGdUQwGCcJuNjReSUHQpKEumM11rhWYqik+idfD5XYGTlRDqPH3traRaEDEHWjYHwEf3AK5zeYnkvx59O+85bShk15MXz4ZMJg+A1x9/DYtr3LXD+5eqfvlBgQmCccR7hUZ6rtFxwXddtt1xVJKPsU6Wwo+A4b8mDZdubW0oqOEWI+V0IaxVpTqg+Ec79AnpgvmIohIC9zy8ojO/1HTaJ1wHWJVKaz6uaeIse24iohOMx99CbwgOs0+WlbVFTzYOlG8QrtCupGyO05fKbsurJcMtg5o5dQVwtKuFgyenr+3gPUPx4a9XiEWr9Ajv6Jm12kJxgyk0ONR0o0bh7J7YjfUu8BrrCbMDTd2+Fixs3+A+6i/1BubBXse6DhqM0BN7qy1t5Jngo9Vpf1yCdLoEoibi6bnHElBERGz3ECiTmg4OrbrRA+FTj77I/cEO9R6bwse4/XnCMoFEwgbQNaIgQrwr8mvJdktOno+knmsXy4Ry4Ol7+A3e/h8IxG6S9D3M6LzBo5nARKeJ/obUNMys8jOHyl09UbEKRwDdJimUjn7yYJ5z3GeMkWCTmnrDbPQgByRBHAppJ91EhZw5KRWaOaLUQ7konks4IOB90JpwLSBoKwb/78BeIzGxGt7fmLdIlFCoUb5g6YGJN68lE4yGER0AiM5h0t9xBE5zW+g1jQUyeax4g/MwCF7a4aRNCTmr526rVa03q9ekflC03aldpV3S9QHJYN6g9+hg6Y7f0z9vD/c2Y5LF0Hne7KLBeTYED/pN11u3BASaLgBIBN67t0tpTzEua6uAq2xVTS10xK4jYitYV1I0mA1iWnoRkoQ4IGKIIQMeCOW12gIGbhnCMSngUlHSiPzseCGn7kBAU4bMvoxYTGIFo7WElGPBNFaBiR6zZorTKMEsELnxiI2AoMbROcHAwbB9RibCQiaCk4TR/hI/0NKH8C73aE3+Eoxxch/C0YHunUbRwyAdV2mATKU0byG2tra5PY2kaMJEFOJoXf/0AC/hwKQjSaOIKgWubg5pERwRIkY16oKETqRHT1w916BAnWZ9D09T27f1CHiMHBpA1VIWqjnSHT5eKFZ0gTJ0qkMB+0c00Zrdgy+ajjPYTsR+XA4cFrCFk0Ple2vbX2BmEBDgpOY3hHgnRBOgIHOdtFWpERhRvAe4/riW6AUD16N0Cc2N1gjWmiApg3vOAsePnb04KMeCAgiY8kAAiUbRgj3jyRMAj3RmuNlqsHXbULMgJCDyjPijRs5KYG4oh0eKFI9qZTgw2tQGa55vj3JovowNmYnGJGthCcx9JD/8AZSFMoAA5vmAzqxavhuHB6GeP71E+8VFv+KiPYBAR90aMH3RoT7FGjeI5sIWQ73R2Ecfo5MXFrmmIDRMmKpOo93uBoTBmx02nX0jURaDgRJHyus0gyKtZOo4cFeI1o/K9vdPtoRs6cJu0BGt2k26AnzOpqPeOqvbBPGcdQqCexri0Nm0mIqVA8lvV64ix8YGUpgKlJoi26JMpVRBiER3L3sIk5t5CgiY8EAiY8IIABE9AyA1ojgPco26qyj/9gMmw+6/UOz+Ya0OBuOS9D5c63RwMuw/46Kra7o7R7+A9Qj4fF34ThnN2FURzdxiFSDNO2pCcUehf5m6wI6VrCtZPhghUReF97bdYnp6JkgP9Nms18E6JA1WqjgYbJBCbj+rlDKZB2bWNYiEBnRo3WEVFpE4WIu6hzqnUZujZFAkRo22G8Kv4c4RH29MIGrSbFCQ9Dfcp03nkoxJ0nL6h+F+odo7uvFxxxR7zdF4yGp17TgeKNbTa04jpXYq4Ml0fT1/bwHpl7eGuFqu6AMjqTeqeW5OBG8R4BDrDayO9AxQrBahU10RnN1HctarLDywVg8rxhHcoVFqEzuRMBsCaOs7RzqQMG/rfboCZ1aMe5TRAa79aMhvTRH8ImG4c0B71olH5qKuGoFWs+KAY6M6sIGYEDIG1puKDY5lI5sKShcDY8Co1lAx+E51mLTYeiRN2gWqulfyCM3FGs8ujtHuv1DtQYajzRk15xuOOQfK6xwxtQqcLCOjjbxA19LB0j4AV0ray3SKxf4bj2AMCnDrfuECnAUjfYhMdNr2mUjOdSpQWmtNq2qGc5hvEeCBiHeVw0gQ0oI1DVbsgqTqtOq3WSgIgaBIBE+wQEN6PRNrZyOkEq0sjGGkRggJse1pDiNlVqbMPDSS1wFpZaLk4xonu+doNkYxAMiEe9RP8j/Y2jJYFCMNXNExhrt1J3JHpelwK/UO2PAod9mjDBCoj2IrgrGl39pRs6AtLe8f3GGrp+qfv24MwW2oCGY51TgPK/cfC4un2gpHQOqKfQMJ/dCKY57TvJCFIykhiyIZCYROdSu0mW5CR21o9jivM2Ye3XWrw5higYOaYRzmY9RCQLm1HCuBFidIwujhYgIPDXVCksCaK+elAyOk28FYOw/SV+rtzwKcItdpCJi8NtA8wFa87W/LpFmW97pNG2avzazrM+mbcwlh4eAdU9rqwUa4WtOIqPg8G+CNe1GrarOwxQsLRGG5XNcx0RqJV4Y4E/wAqjXm2i4q0UjawbooVMFbY6nQVTDyV/Y+qS1+AuwOCBmChJjnWg+U41KEI/cPfJi6VGN8dfYet73/3eBJlRPqD9FhVGc5rs20G0eCwbM+EvQ5IV7On9jzzWOaQRrC9QzAdhRsLZEnWIo2mp50wOoozY4NYwV1ipCYcLDHcjZouR7w7DWv1HwN2nBH5TY5ARczDFuBTZhgaIuGEqooWMbJo0dhj8NsfomNu/wAOa9qdzVh6Hqq3q45sDvXleyato6N5iDyX/LTmLl5S7O3SRmDeCFW08k2pBDp+qfgvL+F5m2HVUrCX0jRwiFeGyjrr7DBhh9D9P58VYU3khXsyiwxEf5iUfne7utHEqsAfwxMtBDYL1UkStbh7rzi7SFjdrRyCscuChxHuFYejt8HcLRoKvzg+GwjsPU4Beo/Q8G/nxpr2p3NEwAY8gOMbgREqkHwm0jvmpS58BEqjpA6FFHPMxKebBCc2ZxsRvi2KCFhvGBWN+vIbNFyjA7ajrREI6R7hG3Qbeh6SfCQHegRGNdvYEwEWiI3j6Jx3+Psc11YVK4uLxfRkzOLawjU13yOGhyq63WozGGNoR6wOYSYg2yTRmqMQRcUYbNI0KqI1oTyGzRcnGB1ORlSN9ioVaRZk1n6/jZv+gx/6b79BqKIJif8AlAmfUJqILXOY8dZjqiHhGRGeyw2d1Q6zNI96sgsxGKaZObd7oie0KMRsKLS3gmODtyeCCNBCJgfaKI6p1q8QP1/Bsh9C89G33ZwTxnNNIzrwhiAqVjICeZ1XAfdajRtDjohJw0Itgx3+J3KBHupCBuqqQLeq60d1RYf7VmtPsvhtPujRthxTqMM2XosIaNBzYk4BFwH8QaOBLngVg1EQQEI3tIscLR9deYNbnGsm5MMWuDZRB+hCwoVMpGzhoMIhXBwz4anCCeItrus0hOMRqfXqdFDvtF4No0RCAqwIsK8wbUdI4ZHSG0pvVb+58lRjPd+41alSvjm3fENTfTAuKIzWswomVN0mJUZxvjeoQZS3F8O68WPC9jCUdx/3BHvDmKwvP/DU7oO2OWvIRFp1e6AzqN2DsNMU0xa70E8FCY/eEes7aatSJjDSbE09Rmg2ICDW6BkAKcIDaU+maXMxo4RLSiC0kQtBtH+4KoB4g4aDuKaCe8Adib/qO2CQ1lUsh+1MgIbJoUb3B2kQgUyge6jIucK4LPbnP+1gNuJgEKR1I9+L3UYMdCZRy2vcnOaBsDQVAv8A6yUyDP6IJxj/ALjYwAIFfFcjSOWcfoX/xAAsEQACAgAEBQQCAgMBAAAAAAAAAQIRICEiMQMQEjBAMkFCURNQUmIjYXGi/9oACAECAQE/AP3lSZ0mRC3I4j6s+1RRRRRT81ZZjxwn0ZDv2kXIhe5OfVIfYWWeO73Gq7vRBQhfqKR0lSK7KVjeNclmVSzJ6Ict+w/rsJkkvbtomb7lCUyCh7mlfAajuisT+uw/oSsujdQo4jVlGw1hogo9Mn1avF/0S4ck8zJHVWwxaekuW5p6h8tJXLbsRKrNmbKITjAyKMxK8jpKNJfJD8KpEIRbE6zRN3Oyy/sTis3AddZpoaiQzyY4UVE0i6fcee3NYVPp2LljuRJyeL499Qi9xqKLZUmQydk4V0ItPrG5ewlbJv2F8CtVFFmwnFjXuh5Rrlf2V9cnySs/52ntiXZWL2LMho2E/Sz/AGh0h5Roogsyr3GP6KXJTp5DbZZpMjSPk37Ly3h+PO65cO3GSEpraI+HHfrOmP8AMr+onNbGp7nRps0ovkvEeJJvJD7vxwUXWx1Sxvn8fGrAm1mhr8mxp9ycIKP9jLnZ1MuRZpKKFsUaS+0h8n4lRUMyy8DOG6dDhGD65jbcrfb6n3lnkV2l2lmTdvCj/ZBVqOLxPyPy1mpX4STexS95CnBFfQ1JYEJJZsbvy9ty9Vj7SZcTSaTSaF/Y6/obk98CbRaP+DQkoK2Ntyz8vbnuvITkhuTdvz06Hl46x7+GlbodYNJpNLRX7Dhr1MbLwr08r8X28asCyhjW+GrHGnX6Xofvy1FSKkUTVdCFje5VmRZt4T8NybLwrOQ3Y8h4nNP+o0+Syz8KvsqM9tMhqS38FY0IsrTyrDZBxvMn99pFFFFFFHTRUjpE/uRLhRXzHBrxviIqzhJLOfpHay7F5lXmuyuxZlyTaRWjIrxGh70KkxZk3lRLPPsPk55+GjhzaZpY14cHqzGoXQoQcqUj8d+iekn1dQs412VvyfiPcUyrzXhyzzIPTmeiOgVTyZ0Uxrse3L4+GiXq5Lq9jS9/UaRqNWiisFFSq+zw1Z/Mbtl/YpQmqmcSLWTK+sb5fHw4kvUV9ll1sPMWUR5YaOG6UjiQ649ax0Qm1HIfFyjoPyR/gflifk/v/wCRcX2nLqiSjBatB/ie8hqK2KX8yv7nSKDsfJeJ1lXzWeRuj4865WjhzakJnEhFrrWCjYvk8KdFXsL6wLJXzW/YSvvXIsyGtNiHGpFVuXgv3IPSTh7rlRfNDx74JZZYHv2Hnn4CckdTPySxQYsiFz9HqOIknlhW4+wmNEdx4Jb9hOvIjuLY4a6Or+ROurlWB9lP6HVZYFmPN+CvAXwmNO4j9XKyuc+1N30VgTp3+ihPT0MitOXxH1CY650T+H6B+DCdOxt+5qLexcjULLNjnHiZPSNNOn+xlnC0JSRl7xHw5vNGmG3qMveRpHO1X7Hh7SLfh//EAC4RAAICAAQFBAEEAgMAAAAAAAABAhESISIxAxAgMEIyQEFRE1BSYWJxciOCov/aAAgBAwEBPwDsXf6o3FF/RmTpROGsOXassssste9eeQuucMWvyFXzEahV4SdbEIYYi7Dzy66rYTvu45ucq9Jif7TGXEtdluhKhdT+uTVSsu3kQ1z5bS7C++w0QbrX25HDRVbCdjcCbn8Gp+ZFy2ZfUs8+Xl1L7G6KsyTnZw4PBmXRvET6bJuWKCw6fayzzI8SDWRrZgvcR6sRUdjOhMo1F8t+wy7ygUluWcSEpFy/YX9mXxIcqzLLNRXJqxO+z5dj/I5o4nEkkNSeTIQqFYCr/qV9DU3kpEFLAasQnInlmhTvwLbHY8fwLLfm+huhxx7lR66iyKiuraXZfU5yW0ROTKXyXFE840QmnjZUlhEl8jdIgqzH5F6bLGjcakhT+JCzd8q+i/vkuTdH8vtL1dTF2H1eQ0akJ2XY4epC+mK2LOVlk3lZdbEchfZbP8DhazFBIo1Go1fAuSXy/drp8udWajiUpRZNwe8hcSW2ExS/YX/Yag9zTDY/Jqo1Mrk+x5dxbdTcVmxdiyvvo8h8rLKvcwx6mJ8/LsPuLlZfOaTyYn+Pcz+CE5uVeJqP+3KjAjAijUWWh7lmpldpoTEL2ltzy8SrKK5o4qtWRm5rBAhBKNIrtYE+88sy+0+08jhqlyvmz+CbvSjhcP8AGvdvKUUu2uqxtLcxy+IDhNl/YnF7cr5MbbdIhCuS9zd7FZULtNWVL95qNRqNb30mD7EorboaiypfBf3ETG3OVIhBQVLm/cb89pe4aTWYlFKl07e236GrE79u+vb2c3SsVmrnqKkalIv2z7H8ey4r9CIorpe4iva+XYrvXyrk9U/9RdT2HzouhStX+i4l8crRaMaLRB3KbH1r0l0aijf/AF9kvZrhpFdLdREqFmLos1ChNeWIUlyeeS9lfwi5w31RE4vb2L639DGhPVyvpaJqSWRDau03RZZZZZY53kYoox/0GvqJDiyeWAU1Lvrr8hl0cVt5Q9RGnG+xWkusn2X2KNXKSTkXrzL7y6aExbWStoeTOGtVkMpSXYQ8xQy9mycE0akJ+zknhnXqE54bJTmo24n5GvXDUcPDRLKV9jyHtyXYXcXpHCxOsn7OGWRxFqyPW7mNOGaMdxIO11+R88vL2bIenk8NZmpbek1CnO6cSy+VlllxuuzxHR+0SqNGH6HGfDdxOHOLzgX99a5eXs2cPYxfQkVe4sh5yE76bOLG5Ro4c5Qlgn12Sgm8xcDOTxn4pfvPxSPxf0/9D4PlCOGRGU3lrxH/ACraJBye8DG/2GP+hjHNYRZcn2PLuYJF0XfJ5Zm0zy5tospnF4aaGr3OHxHF4J8q5Wblcl5dLVl1uP76HnKK5vbsN1n23zpFSM/kTWKh/wACdou9hLnRXwTWo4fE+Hyv6K5sj5dewv45wzz6Ft2Fll7BqL3MCPxrqmh54iVQ9fpOG21mLoexHy7DQmS2I5dEduw1a7S70th72cR/kw/tIXXK+iHZa+xXdPobqIlS9i/YNrXAg1UhenlRdc4dqCaxX0NWq/Qpw1Y0TevPyI4RoV8v8GP7IeX6AvT7GcLVEEnmjSUtyomkevJChLh5rUJpq1+oPMhp4skxuLGpfEhcSCyZqlv6RX4wNYoU7/UeL6olL2f/2Q==);background-size:cover;background-position:center;background-attachment:fixed;}'
        '.stApp::before{content:"";position:fixed;inset:0;background:rgba(6,10,22,0.85);z-index:0;}'
        '.block-container{position:relative;z-index:1;padding-top:1.5rem!important;}'
        '.lcard{background:rgba(16,22,42,0.96);border:1px solid rgba(0,160,198,0.35);border-radius:24px;padding:2.4rem 2rem;box-shadow:0 30px 80px rgba(0,0,0,0.7);backdrop-filter:blur(20px);max-width:420px;margin:0 auto;}'
        '.lrow{display:flex;justify-content:center;align-items:center;gap:24px;margin-bottom:1.8rem;}'
        '.lrow img{height:52px;object-fit:contain;}'
        '.lsep{width:1px;height:44px;background:rgba(255,255,255,0.15);}'
        '.ltitle{font-family:Rajdhani,sans-serif;font-size:2.6rem;font-weight:700;color:#fff;text-align:center;letter-spacing:0.1em;text-shadow:0 0 40px rgba(0,160,198,0.6);margin-bottom:0.2rem;}'
        '.lsub{text-align:center;color:#90cdf4;font-size:0.8rem;letter-spacing:0.06em;}'
        '.lemp{text-align:center;color:#4a5568;font-size:0.75rem;margin-bottom:1.8rem;}'
        'div[data-testid="stTextInput"] input{background:rgba(255,255,255,0.04)!important;border:1px solid rgba(0,160,198,0.3)!important;border-radius:12px!important;color:#e2e8f0!important;font-size:1rem!important;min-height:50px!important;}'
        'div[data-testid="stTextInput"] label{color:#90cdf4!important;font-size:0.8rem!important;font-weight:500!important;}'
        'div[data-testid="stFormSubmitButton"] button{background:linear-gradient(135deg,#005B8E,#00A0C6)!important;border:none!important;border-radius:12px!important;color:white!important;font-family:Rajdhani,sans-serif!important;font-size:1.1rem!important;font-weight:700!important;letter-spacing:0.12em!important;min-height:52px!important;box-shadow:0 4px 24px rgba(0,160,198,0.4)!important;}'
        'header[data-testid="stHeader"]{display:none;}#MainMenu{visibility:hidden;}footer{visibility:hidden;}'
        '</style>',
        unsafe_allow_html=True
    )
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown(
            "<div class='lcard'>"
            "<div class='lrow'>"
            "<img src='data:image/jpeg;base64,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AAAAAAAAAAAAAAAAAGqd1TKeYsy41Qnh0LV2dGnpHulVxer28mjPE8Vea+isffP/ACn0ZzgzKd9VpxUI9Eauvwe2r1HUmvVnzktynNUmlKnYpN8r7s+T/pPoLCbSNhhlrawSUaNOMOT0Iywede5qV9N/se9pw+jaNukuoABjmaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACtScacJTm9IpatgFgYSxSzf/rRJ752nTRLbJYPPmwyjMBh987Tpokd9LTpojZLA5sMozQYffO06aJHfO06aI2SwObDKM0GH3ztOmiO+dp00Rslgc2GUZgMLvpadNEd9LTpojZLA5sMozQYXfO06aI76WnTRGyWBzYZRmgwu+lp00R3ztOmiNksDmwyjNBh987TpojvnadNEbJYHNhkzAYffO06aJHfS06aI2SwTzYZM0GH3ztOmiR30tOmiNksDmwyZoMLvpadNEd9LTpojZLA5sMmaDC76WnTRHfS06aI2SwObDJmgwu+lp00R30tOmiNksDmwyZoMLvpadNEd9LTpojZLA5sMmaDC76Wev8AbRHfS06aI2SwOZDJmgwu+lp00R30tOmiNksDmwyZoMLvpadNEd9LTpojZLA5sMmaDC76WnTRHfS06aI2SwObDJmgwu+lp00R30tOmiNksDmwyZoMLvpadNEd9LTpojZLA5sMmaDC76WnTRHfO06aI2SwObDKM0GH3ztOmiR30tOmiNksEc2GUZoMLvpadNEd9LTpojZLA5sMozQYXfO06aI752nTRGyWBzYZRmgwu+dp00Se+dp00Rslgc2GUZgMPvnadNEd87TpojZLA5sMozAYXfO06aJPfO06aI2SwObDKMwGH3zs+miO+dp00Rslgc2GUZgMPvnadNEd87TpojZLA5sMozAYffO06aI752nTRGyWBzYZRmAw++dp00R3zs+miNksDmwyjMBh987TpojvnadNEbJYHNhlGYDD752nTRHfO06aI2SwObDKMwGH3ztOmiO+dp00Rslgc2GUZgMPvnadNEd87TpojZLA5sMozAYffO06aI752nTRGyWBzYZRmAw++dp00R3ztOmiNksDmwyjMBh987TpojvnadNEbJYHNhlGYDD752nTRHfO06aI2SwTzYZMwGH3ztOmiO+dp00Rslgc2GTMBh98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' alt='Atlas Copco'>"
            "<div class='lsep'></div>"
            "<img src='data:image/jpeg;base64,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uFTpaj6N25nqJDaO8UUl9wD4yWuPg9ob/TVwoaNmH0ojpG5WC9hc6XJPHvKwVWDwVbZRURhwmAElye1l3cdLdyCr7Il020NRNPe89Oyax4NdJKGD/wAbG+1awpGV2x+GRVIu18zWkdxjlV3joY46oyRtAcWBhP2WkkC27TMfesUeEwx00UbGdmFwdGLnskAgHfro47+aCsYbVSP2rpoMQN5oIp2ud9dp6LJJ/SAN/tArNs8ysMMvmD4AzzmbR7Hl35119WuA+5WZ9BG+vbO5g6RrS0O45SdR37uKj37L0j5XOMbgXOLjaWQXJNybB1t5QaWNGYbW0/0cIy/zeX84SBbPF9XW97L5s1UWpKisxNzWvJPTMAsIuiaRlNybm1zfiCLaKebQRtqGPDe0xhY03OjTa436+iNTrosNRg8FQJRKy4mt0guQH5d17HkLHmNDdBRqSqkopIa2pp52OdM508jg3J0U1gBcOLrMAjIuP1TuVs/43/7T+9UtVUzKuldHUNDmOaWubzBFiFo1mz9PWyNdUMJLWZAQ94OUcLtcL+1Bj2ggjqnwMfKYpelzQuAv2wx1xYixu0u0Nu5YKGplh2gEOKthdI6FzmTRtLSWtc27XNdct1eCLOIOq3X4FTyYd0EseaO9wHOcSDe9w4nMD3gr1hmCwYW9xo2Wc4WLnOLnEDcMzyTbuQSCIiAiIgIiIC1MShM1P2N4N7LbRIYtG40qUjSXWA15Kcweg81jzSjtu+4clIW1X1bzfaKmGKzsREWiZiqqdtVTlku4j/RVKq6N1FOWzDwPAjmFel8IzDVb1v0osmKLqvguHmqlzSjsD7+5WlEWLW2zjxxSNCIi1SOebfbOujlNRQtJa784APRP1rcjx5FUCCgkxOrEVAwveTaw4d5PAd5X6CXlrA30QArFORNY1pz8vw+t79UTqGrg9F9G4VFDe/RxtbfnYAXW4iKvM7X4jUagRERkREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREH/2Q==' alt='Centinela'>"
            "</div>"
            "<div class='ltitle'>&#128737;&#65039; CENTINELA</div>"
            "<div class='lsub'>SISTEMA DE GESTIÓN DE EQUIPOS</div>"
            "<div class='lemp'>Minera Spence &middot; Atlas Copco</div>"
            "</div>",
            unsafe_allow_html=True
        )
        with st.form('form_login'):
            username_l = st.text_input('USUARIO O CORREO', placeholder='nombre.apellido@atlascopco.com')
            pin_l      = st.text_input('PIN', type='password', placeholder='••••')
            entrar     = st.form_submit_button('INGRESAR →', use_container_width=True, type='primary')
        if entrar:
            if not username_l or not pin_l:
                st.error('Ingresa usuario y PIN')
            else:
                user = verificar_usuario(username_l, pin_l)
                if user:
                    st.session_state['usuario_activo'] = user
                    # Registrar último acceso
                    try:
                        supabase.table("usuarios").update({"ultimo_acceso": datetime.now().isoformat()}).eq("id", user["id"]).execute()
                    except:
                        pass
                    st.rerun()
                else:
                    st.error('❌ Usuario o PIN incorrecto')
    st.stop()

# ── Usuario logueado ──
usuario = st.session_state["usuario_activo"]
rol_icons = {"admin": "⚙️", "supervisor": "👁️", "tecnico": "🔧"}

# ── UI ────────────────────────────────────────────────────────────────────────
col_titulo, col_user = st.columns([3, 1])
with col_titulo:
    st.markdown("<h1 style='font-family:Rajdhani,sans-serif;font-size:2.4rem;color:#e2e8f0;'>🛡️ CENTINELA</h1><p style='color:#718096;margin-top:-10px;'>Sistema de Gestión de Equipos — Minera Spence</p>", unsafe_allow_html=True)
with col_user:
    rol_icon = rol_icons.get(usuario.get("rol","tecnico"), "🔧")
    st.markdown(f"""
    <div style='background:#1a1f2e;border-radius:10px;padding:0.6rem 1rem;
         border:1px solid #2d3748;text-align:right;margin-top:0.5rem;'>
        <div style='font-size:0.75rem;color:#718096'>{rol_icon} {usuario.get("rol","").upper()}</div>
        <div style='font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:700;color:#e2e8f0'>{usuario.get("nombre","")}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Salir", key="btn_logout", use_container_width=True):
        st.session_state["usuario_activo"] = None
        st.session_state["wizard_paso"] = 1
        st.session_state["wizard_datos"] = {}
        st.rerun()

tabs_list = ["🏭 Equipos", "📋 Generar Informe", "📅 OT Semanal", "📊 Historial", "📁 Informes", "👤 Mi Perfil"]
if usuario.get("rol") in ["admin", "supervisor"]:
    tabs_list.append("👥 Usuarios")
_tabs = st.tabs(tabs_list)
tab1 = _tabs[0]
tab2 = _tabs[1]
tab_ot = _tabs[2]
tab3 = _tabs[3]
tab4 = _tabs[4]
tab_perfil = _tabs[5]
tab5 = _tabs[6] if len(_tabs) > 6 else None

# ════════════════════════════════════════════════
# TAB 1 — EQUIPOS
# ════════════════════════════════════════════════
with tab1:
    equipos = cargar_equipos()

    if "equipo_sel" not in st.session_state:
        st.session_state["equipo_sel"] = None
    if "pagina_equipo" not in st.session_state:
        st.session_state["pagina_equipo"] = "lista"

    # ════ VISTA FICHA INDIVIDUAL ════
    if st.session_state["pagina_equipo"] == "ficha" and st.session_state["equipo_sel"]:
        sel_tag = st.session_state["equipo_sel"]
        eq_data = next((e for e in equipos if e["tag"] == sel_tag), None)
        if eq_data:
            if st.button("← Volver a equipos", key="btn_volver"):
                st.session_state["pagina_equipo"] = "lista"
                st.session_state["equipo_sel"] = None
                st.rerun()

            es_op    = eq_data.get("estado") == "OPERATIVO"
            badge_cl = "badge-op" if es_op else "badge-fs"
            badge_tx = "OPERATIVO" if es_op else "FUERA DE SERVICIO"
            borde    = "#48bb78" if es_op else "#f56565"

            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#1a1f2e,#0f3460);border-radius:16px;
                 padding:2rem;border:1px solid {borde};margin-bottom:1.5rem;'>
                <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;'>
                    <div>
                        <div style='font-family:Rajdhani,sans-serif;font-size:2.4rem;font-weight:700;color:#fff;'>🔧 {eq_data["tag"]}</div>
                        <div style='font-size:1rem;color:#90cdf4;margin-top:4px;'>{eq_data.get("marca","")} · {eq_data.get("modelo","")} · Serie: {eq_data.get("serie","—")}</div>
                    </div>
                    <span class='estado-badge {badge_cl}' style='font-size:0.9rem;padding:8px 20px;'>{badge_tx}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            d1, d2, d3, d4, d5 = st.columns(5)
            datos_cols = [(d1,"Modelo",eq_data.get("modelo","—")),(d2,"Marca",eq_data.get("marca","—")),(d3,"Subarea",eq_data.get("subarea","—")),(d4,"Area",eq_data.get("area","—")),(d5,"Ubicacion",eq_data.get("ubicacion","—"))]
            for col, lbl, val in datos_cols:
                with col:
                    st.markdown(f"<div class='dato-box'><div class='dato-label'>{lbl}</div><div class='dato-valor' style='font-size:0.95rem'>{val}</div></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            try:
                ult_res = supabase.table("historial").select("fecha,tipo,horas_marcha").eq("tag", sel_tag).order("creado_en", desc=True).limit(1).execute()
                ult = ult_res.data[0] if ult_res.data else None
            except:
                ult = None

            if ult:
                st.markdown(f"""
                <div style='background:#1a1f2e;border-radius:12px;padding:1.2rem 1.6rem;border:1px solid #2d3748;margin-bottom:1.5rem;'>
                    <div style='font-size:0.7rem;color:#718096;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.8rem'>Ultimo Mantenimiento</div>
                    <div style='display:flex;gap:3rem;flex-wrap:wrap;'>
                        <div><div style='color:#718096;font-size:0.8rem'>Fecha</div><div style='color:#e2e8f0;font-weight:600;font-size:1.1rem'>{ult["fecha"]}</div></div>
                        <div><div style='color:#718096;font-size:0.8rem'>Tipo</div><div style='color:#90cdf4;font-weight:600;font-size:1.1rem'>{ult["tipo"]}</div></div>
                        <div><div style='color:#718096;font-size:0.8rem'>Horas Marcha</div><div style='color:#f6ad55;font-weight:600;font-size:1.1rem'>{ult["horas_marcha"]} hrs</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("<div style='background:#1a1f2e;border-radius:12px;padding:1rem;border:1px solid #2d3748;color:#718096;margin-bottom:1.5rem;'>Sin mantenimientos registrados aun.</div>", unsafe_allow_html=True)

            col_comp, col_edit = st.columns(2)

            with col_comp:
                st.markdown("### 🔩 Componentes / Repuestos")
                comps = cargar_componentes(sel_tag)
                if comps:
                    for c in comps:
                        cc1, cc2, cc3 = st.columns([2, 3, 1])
                        with cc1: st.markdown(f"<div style='font-size:0.75rem;color:#718096;text-transform:uppercase'>{c.get('tipo','')}</div>", unsafe_allow_html=True)
                        with cc2: st.markdown(f"<div style='font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:600;color:#90cdf4'>{c.get('numero_parte','—')}</div><div style='font-size:0.75rem;color:#718096'>{c.get('descripcion','')}</div>", unsafe_allow_html=True)
                        with cc3:
                            if st.button("🗑", key=f"del_c_{c['id']}"):
                                eliminar_componente(c["id"])
                                st.rerun()
                else:
                    st.caption("Sin componentes registrados.")
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("➕ Agregar componente"):
                    nc1, nc2 = st.columns(2)
                    with nc1: n_tipo  = st.selectbox("Tipo", ["Filtro de aire","Filtro de aceite","Filtro separador","Aceite (referencia)","Kit de mantenimiento","Otro"], key=f"nt_{sel_tag}")
                    with nc2: n_parte = st.text_input("Numero de parte", key=f"np_{sel_tag}")
                    n_desc = st.text_input("Descripcion (opcional)", key=f"nd_{sel_tag}")
                    if st.button("Guardar componente", key=f"gc_{sel_tag}"):
                        if n_parte:
                            guardar_componente({"equipo_tag": sel_tag, "tipo": n_tipo, "numero_parte": n_parte, "descripcion": n_desc})
                            st.success("Componente guardado.")
                            st.rerun()
                        else:
                            st.warning("Ingresa el numero de parte.")

            with col_edit:
                st.markdown("### ✏️ Editar Datos")
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_modelo  = st.text_input("Modelo",    value=eq_data.get("modelo",""),    key=f"em_{sel_tag}")
                    e_serie   = st.text_input("Serie",     value=eq_data.get("serie",""),     key=f"es_{sel_tag}")
                    e_marca   = st.text_input("Marca",     value=eq_data.get("marca",""),     key=f"emk_{sel_tag}")
                with ec2:
                    e_subarea = st.text_input("Subarea",   value=eq_data.get("subarea",""),   key=f"esa_{sel_tag}")
                    e_area    = st.text_input("Area",      value=eq_data.get("area",""),      key=f"ea_{sel_tag}")
                    e_ubic    = st.text_input("Ubicacion", value=eq_data.get("ubicacion",""), key=f"eu_{sel_tag}")
                e_estado = st.selectbox("Estado", ["OPERATIVO","FUERA DE SERVICIO"],
                                        index=0 if eq_data.get("estado")=="OPERATIVO" else 1,
                                        key=f"ee_{sel_tag}")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Guardar cambios", key=f"save_{sel_tag}", use_container_width=True):
                    upsert_equipo({"tag": sel_tag, "modelo": e_modelo, "serie": e_serie, "marca": e_marca,
                        "subarea": e_subarea, "area": e_area, "ubicacion": e_ubic, "estado": e_estado,
                        "actualizado_en": datetime.now().isoformat()})
                    st.success("Equipo actualizado.")
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("← Volver a equipos", key="btn_volver2"):
                st.session_state["pagina_equipo"] = "lista"
                st.session_state["equipo_sel"] = None
                st.rerun()

    else:
        # ════ VISTA GRID ════
        total = len(equipos)
        op    = sum(1 for e in equipos if e.get("estado") == "OPERATIVO")
        fs    = total - op
        locs  = sorted(set(e.get("ubicacion","") for e in equipos if e.get("ubicacion")))

        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f"<div class='metric-card'><div class='metric-n' style='color:#90cdf4'>{total}</div><div class='metric-l'>Total Equipos</div></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='metric-card'><div class='metric-n' style='color:#48bb78'>{op}</div><div class='metric-l'>Operativos</div></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-card'><div class='metric-n' style='color:#f56565'>{fs}</div><div class='metric-l'>Fuera de Servicio</div></div>", unsafe_allow_html=True)
        with m4: st.markdown(f"<div class='metric-card'><div class='metric-n' style='color:#f6ad55'>{len(locs)}</div><div class='metric-l'>Ubicaciones</div></div>", unsafe_allow_html=True)

        st.divider()

        cf1, cf2, cf3, cf4 = st.columns(4)
        with cf1: f_loc   = st.selectbox("Ubicacion", ["Todas"] + locs, key="f_loc")
        with cf2: f_est   = st.selectbox("Estado", ["Todos","OPERATIVO","FUERA DE SERVICIO"], key="f_est")
        with cf3: f_marca = st.selectbox("Marca", ["Todas"] + sorted(set(e.get("marca","") for e in equipos if e.get("marca"))), key="f_marca")
        with cf4: f_bus   = st.text_input("Buscar TAG / Modelo", key="f_bus")

        ef = equipos
        if f_loc   != "Todas": ef = [e for e in ef if e.get("ubicacion") == f_loc]
        if f_est   != "Todos": ef = [e for e in ef if e.get("estado") == f_est]
        if f_marca != "Todas": ef = [e for e in ef if e.get("marca") == f_marca]
        if f_bus:               ef = [e for e in ef if f_bus.upper() in e.get("tag","").upper() or f_bus.upper() in e.get("modelo","").upper()]

        st.caption(f"Mostrando {len(ef)} equipos — clic en una tarjeta para ver la ficha")

        cols_per_row = 4
        rows = [ef[i:i+cols_per_row] for i in range(0, len(ef), cols_per_row)]
        for row in rows:
            cols = st.columns(cols_per_row)
            for idx, eq in enumerate(row):
                with cols[idx]:
                    es_op    = eq.get("estado") == "OPERATIVO"
                    borde    = "#48bb78" if es_op else "#f56565"
                    badge_cl = "badge-op" if es_op else "badge-fs"
                    badge_tx = "OPERATIVO" if es_op else "FUERA DE SERVICIO"
                    st.markdown(f"""
                    <div style='background:#1a1f2e;border-left:4px solid {borde};border-radius:12px;
                         padding:1rem;border:1px solid #2d3748;margin-bottom:0.2rem;'>
                        <div style='font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:700;color:#e2e8f0;'>{eq["tag"]}</div>
                        <div style='font-size:0.8rem;color:#90cdf4;margin:3px 0'>{eq.get("modelo","")}</div>
                        <div style='font-size:0.75rem;color:#718096;margin-bottom:8px'>{eq.get("subarea","")}</div>
                        <span class='estado-badge {badge_cl}'>{badge_tx}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Ver ficha ›", key=f"btn_{eq['tag']}", use_container_width=True):
                        st.session_state["equipo_sel"] = eq["tag"]
                        st.session_state["pagina_equipo"] = "ficha"
                        st.rerun()


# ════════════════════════════════════════════════
# ════════════════════════════════════════════════
# ════════════════════════════════════════════════
# TAB 2 — GENERAR INFORME (wizard móvil)
# ════════════════════════════════════════════════
with tab2:

    # CSS móvil
    st.markdown("""
    <style>
    .paso-header {
        background: linear-gradient(135deg, #005B8E, #0099CC);
        border-radius: 12px; padding: 1rem 1.2rem;
        margin-bottom: 1rem; color: white;
    }
    .paso-num {
        font-size: 0.75rem; opacity: 0.8;
        text-transform: uppercase; letter-spacing: 0.1em;
    }
    .paso-titulo {
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.4rem; font-weight: 700; margin-top: 2px;
    }
    .progreso-bar {
        background: #2d3748; border-radius: 20px;
        height: 6px; margin-bottom: 1.5rem; overflow: hidden;
    }
    .progreso-fill {
        background: linear-gradient(90deg, #005B8E, #00A0C6);
        height: 100%; border-radius: 20px;
        transition: width 0.3s ease;
    }
    .equipo-card-sel {
        background: linear-gradient(135deg, #1a1f2e, #0f3460);
        border: 2px solid #0099CC; border-radius: 14px;
        padding: 1.2rem; margin: 0.5rem 0 1rem 0;
    }
    .eq-modelo { font-family: Rajdhani,sans-serif; font-size: 1.5rem;
                 font-weight: 700; color: #fff; }
    .eq-info   { font-size: 0.85rem; color: #90cdf4; margin-top: 4px; }
    .eq-serie  { font-size: 0.8rem; color: #718096; margin-top: 2px; }
    .param-box {
        background: #1a1f2e; border-radius: 10px;
        padding: 0.8rem; border: 1px solid #2d3748;
        margin-bottom: 0.5rem;
    }
    .resumen-row {
        display: flex; justify-content: space-between;
        padding: 0.5rem 0; border-bottom: 1px solid #2d3748;
        font-size: 0.88rem;
    }
    .resumen-label { color: #718096; }
    .resumen-val   { color: #e2e8f0; font-weight: 600; }
    div[data-testid="stSelectbox"] > div,
    div[data-testid="stTextInput"] > div > div > input,
    div[data-testid="stNumberInput"] > div > div > input {
        font-size: 1rem !important;
        min-height: 48px !important;
    }
    div[data-testid="stFormSubmitButton"] > button {
        min-height: 56px !important;
        font-size: 1.1rem !important;
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    equipos_list = cargar_equipos()
    tags_list    = [e["tag"] for e in equipos_list]

    # ── Estado del wizard ──
    if "wizard_paso" not in st.session_state:
        st.session_state["wizard_paso"] = 1
    if "wizard_datos" not in st.session_state:
        st.session_state["wizard_datos"] = {}

    paso   = st.session_state["wizard_paso"]
    datos_w = st.session_state["wizard_datos"]
    PASOS  = 4

    # ── Barra de progreso ──
    pct = int((paso / PASOS) * 100)
    pasos_labels = ["Equipo", "Técnicos", "Parámetros", "Confirmar"]
    st.markdown(f"""
    <div style='display:flex;justify-content:space-between;margin-bottom:6px;'>
        {''.join([
            f"<span style='font-size:0.75rem;color:{'#00A0C6' if i+1<=paso else '#4a5568'};font-weight:{'700' if i+1==paso else '400'}'>"
            f"{'✓ ' if i+1<paso else ''}{l}</span>"
            for i,l in enumerate(pasos_labels)
        ])}
    </div>
    <div class='progreso-bar'>
        <div class='progreso-fill' style='width:{pct}%'></div>
    </div>
    """, unsafe_allow_html=True)

    # ════════════════════════════════
    # PASO 1 — EQUIPO Y TIPO
    # ════════════════════════════════
    if paso == 1:
        st.markdown("""
        <div class='paso-header'>
            <div class='paso-num'>Paso 1 de 4</div>
            <div class='paso-titulo'>🏭 Seleccionar Equipo</div>
        </div>
        """, unsafe_allow_html=True)

        tag_p1 = st.selectbox(
            "TAG del equipo",
            tags_list,
            index=tags_list.index(datos_w.get("tag", tags_list[0])) if datos_w.get("tag") in tags_list else 0,
            key="p1_tag"
        )
        tipo_p1 = st.selectbox(
            "Tipo de Orden",
            ["INSPECCIÓN", "2.000 hrs", "4.000 hrs", "8.000 hrs", "16.000 hrs"],
            index=["INSPECCIÓN","2.000 hrs","4.000 hrs","8.000 hrs","16.000 hrs"].index(datos_w.get("tipo_orden","INSPECCIÓN")) if datos_w.get("tipo_orden") else 0,
            key="p1_tipo"
        )
        fecha_p1 = st.date_input("Fecha del servicio", datetime.now(), key="p1_fecha")
        ot_p1    = st.text_input("Número OT", datos_w.get("orden_servicio",""), key="p1_ot",
                                  placeholder="Ej: 4724006")

        eq = next((e for e in equipos_list if e["tag"] == tag_p1), {})
        if eq:
            st.markdown(f"""
            <div class='equipo-card-sel'>
                <div class='eq-modelo'>{eq.get('modelo','')} &nbsp;
                    <span style='font-size:1rem;color:#48bb78;'>✓</span>
                </div>
                <div class='eq-info'>{eq.get('subarea','')} · {eq.get('area','')} · {eq.get('ubicacion','')}</div>
                <div class='eq-serie'>Serie: {eq.get('serie','—')}</div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("Siguiente →", key="p1_next", use_container_width=True, type="primary"):
            st.session_state["wizard_datos"].update({
                "tag": tag_p1, "tipo_orden": tipo_p1,
                "fecha": fecha_p1.strftime("%d/%m/%Y"),
                "fecha_obj": str(fecha_p1),
                "orden_servicio": ot_p1,
                "equipo_modelo": eq.get("modelo",""),
                "serie": eq.get("serie",""),
                "ubicacion": eq.get("subarea",""),
                "planta": eq.get("ubicacion",""),
                "area": eq.get("area",""),
            })
            st.session_state["wizard_paso"] = 2
            st.rerun()

    # ════════════════════════════════
    # PASO 2 — TÉCNICOS
    # ════════════════════════════════
    elif paso == 2:
        st.markdown("""
        <div class='paso-header'>
            <div class='paso-num'>Paso 2 de 4</div>
            <div class='paso-titulo'>👷 Técnicos</div>
        </div>
        """, unsafe_allow_html=True)

        nombre_usuario = usuario.get("nombre", st.secrets.get("tec1_default","Ignacio Morales"))
        tec1_p2   = st.text_input("Técnico 1 (Líder)", datos_w.get("tecnico_1", nombre_usuario), key="p2_t1")
        tec2_p2   = st.text_input("Técnico 2", datos_w.get("tecnico_2", st.secrets.get("tec2_default","Emian Sanchez")), key="p2_t2")
        horas_p2  = st.text_input("Horas trabajadas por técnico", datos_w.get("horas_1","2"), key="p2_hrs")
        cont_p2   = st.text_input("Contacto cliente", datos_w.get("contacto", st.secrets.get("contacto_default","Pamela Arancibia")), key="p2_cont")

        try:
            ur2 = supabase.table("historial").select("horas_marcha").eq("tag", datos_w.get("tag","")).order("creado_en", desc=True).limit(1).execute()
            h_prev = int(ur2.data[0]["horas_marcha"]) if ur2.data else 0
        except:
            h_prev = 0

        h_marcha_p2 = st.number_input("Horas Marcha del equipo", value=h_prev, step=1, key="p2_hm")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Atrás", key="p2_back", use_container_width=True):
                st.session_state["wizard_paso"] = 1
                st.rerun()
        with c2:
            if st.button("Siguiente →", key="p2_next", use_container_width=True, type="primary"):
                st.session_state["wizard_datos"].update({
                    "tecnico_1": tec1_p2, "tecnico_2": tec2_p2,
                    "horas_1": horas_p2, "contacto": cont_p2,
                    "horas_marcha": str(h_marcha_p2),
                })
                st.session_state["wizard_paso"] = 3
                st.rerun()

    # ════════════════════════════════
    # PASO 3 — PARÁMETROS
    # ════════════════════════════════
    elif paso == 3:
        st.markdown("""
        <div class='paso-header'>
            <div class='paso-num'>Paso 3 de 4</div>
            <div class='paso-titulo'>⚙️ Parámetros Operacionales</div>
        </div>
        """, unsafe_allow_html=True)

        nivel_p3   = st.text_input("Nivel de aceite", datos_w.get("nivel_aceite","100%"), key="p3_ace", placeholder="100%")
        presion_p3 = st.text_input("Presión de Salida", datos_w.get("presion_salida",""), key="p3_pres", placeholder="Ej: 92 psi")
        temp_p3    = st.text_input("Temp. salida elemento", datos_w.get("temp_elemento",""), key="p3_temp", placeholder="Ej: 7°C")

        st.markdown("**Banda de presión**")
        bc1, bc2 = st.columns(2)
        with bc1: bcarga_p3  = st.text_input("Carga", datos_w.get("banda_carga",""), key="p3_bc", placeholder="Ej: 76 psi")
        with bc2: bdesc_p3   = st.text_input("Descarga", datos_w.get("banda_descarga",""), key="p3_bd", placeholder="Ej: 94 psi")

        st.markdown("**Comentarios**")
        tipo_actual = datos_w.get("tipo_orden","INSPECCIÓN")
        _tipo_lower = tipo_actual.lower()
        coment_default = datos_w.get("comentarios", (
            "Se realiza " + _tipo_lower + " programada.\n"
            "Se chequea parámetros en módulo de control óptimos.\n"
            "Se chequea existencia de fugas y filtraciones. Sin observaciones\n"
            "Se chequea carrocería. Sin observaciones\n"
            "Se realizan pruebas operacionales en carga y descarga de equipo, "
            "operando de forma óptima según configuración en módulo de control.\n"
            "Equipo operativo."
        ))
        coment_p3 = st.text_area("", value=coment_default, height=150, key="p3_com")

        proximas_map = {
            "INSPECCIÓN": "Corresponde pauta de: [ 2.000 hrs ]",
            "2.000 hrs":  "Corresponde pauta de: [ 4.000 hrs ]",
            "4.000 hrs":  "Corresponde pauta de: [ 8.000 hrs ]",
            "8.000 hrs":  "Corresponde pauta de: [ 16.000 hrs ]",
            "16.000 hrs": "Corresponde pauta de: [ 2.000 hrs ]",
        }
        prox_p3 = st.text_input("Próxima Visita", datos_w.get("proxima_visita", proximas_map.get(tipo_actual,"")), key="p3_prox")

        # ── Fotos opcionales ──
        st.markdown("**📷 Registro Fotográfico** *(opcional)*")
        st.caption("Puedes agregar hasta 2 fotos desde tu cámara o galería")
        fc1, fc2 = st.columns(2)
        with fc1:
            foto1_p3 = st.file_uploader("Foto 1", type=["jpg","jpeg","png"],
                                         key="p3_foto1", label_visibility="collapsed",
                                         help="Foto 1 del equipo")
            st.caption("Foto 1")
        with fc2:
            foto2_p3 = st.file_uploader("Foto 2", type=["jpg","jpeg","png"],
                                         key="p3_foto2", label_visibility="collapsed",
                                         help="Foto 2 del equipo")
            st.caption("Foto 2")

        if foto1_p3 or foto2_p3:
            st.success(f"✅ {sum(1 for f in [foto1_p3,foto2_p3] if f)} foto(s) cargada(s)")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Atrás", key="p3_back", use_container_width=True):
                st.session_state["wizard_paso"] = 2
                st.rerun()
        with c2:
            if st.button("Siguiente →", key="p3_next", use_container_width=True, type="primary"):
                # Guardar fotos como bytes en session_state
                foto1_bytes = foto1_p3.read() if foto1_p3 else None
                foto2_bytes = foto2_p3.read() if foto2_p3 else None
                st.session_state["wizard_fotos"] = {
                    "foto1": foto1_bytes,
                    "foto2": foto2_bytes,
                    "foto1_nombre": foto1_p3.name if foto1_p3 else None,
                    "foto2_nombre": foto2_p3.name if foto2_p3 else None,
                }
                st.session_state["wizard_datos"].update({
                    "nivel_aceite": nivel_p3, "presion_salida": presion_p3,
                    "temp_elemento": temp_p3, "banda_carga": bcarga_p3,
                    "banda_descarga": bdesc_p3, "comentarios": coment_p3,
                    "proxima_visita": prox_p3,
                    "tiene_fotos": bool(foto1_bytes or foto2_bytes),
                })
                st.session_state["wizard_paso"] = 4
                st.rerun()

    # ════════════════════════════════
    # PASO 4 — RESUMEN Y GENERAR
    # ════════════════════════════════
    elif paso == 4:
        st.markdown("""
        <div class='paso-header'>
            <div class='paso-num'>Paso 4 de 4</div>
            <div class='paso-titulo'>✅ Confirmar y Generar</div>
        </div>
        """, unsafe_allow_html=True)

        d = datos_w
        st.markdown(f"""
        <div style='background:#1a1f2e;border-radius:12px;padding:1.2rem;border:1px solid #2d3748;margin-bottom:1rem;'>
            <div style='font-size:0.7rem;color:#718096;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.8rem'>Resumen del Informe</div>
            <div class='resumen-row'><span class='resumen-label'>Equipo</span><span class='resumen-val'>{d.get('tag','')} — {d.get('equipo_modelo','')}</span></div>
            <div class='resumen-row'><span class='resumen-label'>Tipo de Orden</span><span class='resumen-val'>{d.get('tipo_orden','')}</span></div>
            <div class='resumen-row'><span class='resumen-label'>Fecha</span><span class='resumen-val'>{d.get('fecha','')}</span></div>
            <div class='resumen-row'><span class='resumen-label'>OT</span><span class='resumen-val'>{d.get('orden_servicio','—')}</span></div>
            <div class='resumen-row'><span class='resumen-label'>Técnico 1</span><span class='resumen-val'>{d.get('tecnico_1','')}</span></div>
            <div class='resumen-row'><span class='resumen-label'>Técnico 2</span><span class='resumen-val'>{d.get('tecnico_2','')}</span></div>
            <div class='resumen-row'><span class='resumen-label'>Horas Marcha</span><span class='resumen-val'>{d.get('horas_marcha','')}</span></div>
            <div class='resumen-row'><span class='resumen-label'>Nivel aceite</span><span class='resumen-val'>{d.get('nivel_aceite','')}</span></div>
            <div class='resumen-row'><span class='resumen-label'>Presión salida</span><span class='resumen-val'>{d.get('presion_salida','')}</span></div>
            <div class='resumen-row'><span class='resumen-label'>Temp. elemento</span><span class='resumen-val'>{d.get('temp_elemento','')}</span></div>
            <div class='resumen-row'><span class='resumen-label'>Banda carga/desc.</span><span class='resumen-val'>{d.get('banda_carga','')} / {d.get('banda_descarga','')}</span></div>
            <div class='resumen-row' style='border:none'><span class='resumen-label'>Próxima visita</span><span class='resumen-val'>{d.get('proxima_visita','')}</span></div>
            <div class='resumen-row' style='border:none'><span class='resumen-label'>Fotos</span><span class='resumen-val'>{'✅ Incluidas' if d.get('tiene_fotos') else '— Sin fotos'}</span></div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Atrás", key="p4_back", use_container_width=True):
                st.session_state["wizard_paso"] = 3
                st.rerun()
        with c2:
            if st.button("🔄 Nuevo informe", key="p4_nuevo", use_container_width=True):
                st.session_state["wizard_paso"] = 1
                st.session_state["wizard_datos"] = {}
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📄 GENERAR PDF", key="p4_generar", use_container_width=True, type="primary"):
            try:
                from generar_informe_pdf import generar_pdf, ACTIVIDADES_DEFAULT
                fotos_w = st.session_state.get("wizard_fotos", {})
                datos_pdf = {
                    **d,
                    "actividades": ACTIVIDADES_DEFAULT,
                    "foto1_bytes": fotos_w.get("foto1"),
                    "foto2_bytes": fotos_w.get("foto2"),
                }
                pdf_bytes = generar_pdf(datos_pdf)
                nombre_pdf = f"Informe_{d.get('tipo_orden','INS')}_{d.get('tag','')}_{d.get('fecha_obj','')}.pdf"

                with st.spinner("Guardando..."):
                    rid = guardar_registro({
                        "fecha": d.get("fecha_obj",""), "tag": d.get("tag",""),
                        "tipo": d.get("tipo_orden",""), "horas_marcha": int(d.get("horas_marcha",0)),
                        "horas_carga": 0, "tecnico_1": d.get("tecnico_1",""),
                        "tecnico_2": d.get("tecnico_2",""), "contacto": d.get("contacto",""),
                        "p_carga": d.get("banda_carga",""), "p_descarga": d.get("banda_descarga",""),
                        "temp_salida": d.get("temp_elemento",""),
                        "alcance": d.get("comentarios","")[:500],
                        "actividades": "", "condicion": "", "recomendaciones": "",
                    })
                    if rid:
                        guardar_informe_storage(rid, nombre_pdf, pdf_bytes)

                st.success(f"✅ Informe generado — {d.get('tipo_orden','')} | {d.get('tag','')} | {d.get('fecha','')}")
                st.download_button(
                    "📥 DESCARGAR PDF",
                    pdf_bytes, nombre_pdf,
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())



# ════════════════════════════════════════════════
# TAB OT SEMANAL — Consolidado OTs
# ════════════════════════════════════════════════
with tab_ot:
    st.markdown("### 📅 Consolidado OT Semanal")

    # CSS semáforo y tabla
    st.markdown("""
    <style>
    .ot-card {
        background:#1a1f2e; border-radius:10px;
        padding:0.8rem 1rem; margin-bottom:0.4rem;
        border-left:4px solid #2d3748;
        border:1px solid #2d3748;
    }
    .ot-desc { font-size:0.88rem; color:#e2e8f0; font-weight:500; }
    .ot-meta { font-size:0.75rem; color:#718096; margin-top:3px; }
    .ot-obs  { font-size:0.75rem; color:#f6ad55; margin-top:2px; }
    .badge-pend  { background:rgba(246,173,85,0.15);  color:#f6ad55; border:1px solid rgba(246,173,85,0.3);  border-radius:20px; padding:2px 10px; font-size:0.7rem; font-weight:600; }
    .badge-comp  { background:rgba(72,187,120,0.15);  color:#48bb78; border:1px solid rgba(72,187,120,0.3);  border-radius:20px; padding:2px 10px; font-size:0.7rem; font-weight:600; }
    .badge-atras { background:rgba(245,101,101,0.15); color:#f56565; border:1px solid rgba(245,101,101,0.3); border-radius:20px; padding:2px 10px; font-size:0.7rem; font-weight:600; }
    .dia-header { font-family:Rajdhani,sans-serif; font-size:1.1rem; font-weight:700;
                  color:#90cdf4; border-bottom:1px solid #2d3748; padding-bottom:4px; margin:1rem 0 0.5rem 0; }
    </style>
    """, unsafe_allow_html=True)

    # ── Subir Excel ──
    col_up, col_semana = st.columns([2, 1])
    with col_up:
        archivo_xl = st.file_uploader(
            "📂 Subir consolidado Excel (.xlsx)",
            type=["xlsx", "xls"],
            help="Sube el consolidado semanal de OTs"
        )
    with col_semana:
        from datetime import datetime as _dt3, timedelta
        hoy = _dt3.now()
        semana_actual = hoy.strftime("%Y-W%V")
        st.markdown(f"""
        <div style='background:#1a1f2e;border-radius:10px;padding:0.8rem 1rem;
             border:1px solid #2d3748;margin-top:1.6rem;'>
            <div style='font-size:0.7rem;color:#718096;text-transform:uppercase;'>Semana actual</div>
            <div style='font-family:Rajdhani,sans-serif;font-size:1.3rem;
                 font-weight:700;color:#90cdf4;'>{semana_actual}</div>
            <div style='font-size:0.75rem;color:#4a5568;'>
                {(hoy - timedelta(days=hoy.weekday())).strftime("%d/%m")} — 
                {(hoy - timedelta(days=hoy.weekday()) + timedelta(days=6)).strftime("%d/%m/%Y")}
            </div>
        </div>
        """, unsafe_allow_html=True)

    if archivo_xl:
        try:
            import pandas as pd
            import re

            df = pd.read_excel(archivo_xl, header=None)

            # Encontrar fila de encabezado buscando "Centro" o "Task description"
            header_row = None
            for i, row in df.iterrows():
                row_vals = [str(v).strip().lower() for v in row.values if pd.notna(v)]
                if any("centro" in v for v in row_vals) or any("task" in v for v in row_vals):
                    header_row = i
                    break

            if header_row is None:
                header_row = 0

            df.columns = df.iloc[header_row]
            df = df.iloc[header_row+1:].reset_index(drop=True)
            df.columns = [str(c).strip() if pd.notna(c) else f"col_{i}" for i, c in enumerate(df.columns)]

            # Mapear columnas flexiblemente
            col_map = {}
            for col in df.columns:
                cl = str(col).lower().strip()
                if "centro" in cl:           col_map["centro"] = col
                elif "wbs" in cl:            col_map["wbs"] = col
                elif "task" in cl or "desc" in cl: col_map["descripcion"] = col
                elif "plan" in cl:           col_map["plan"] = col
                elif cl == "ot":             col_map["ot"] = col
                elif "obs" in cl:            col_map["obs"] = col
                elif "start" in cl:          col_map["fecha_inicio"] = col
                elif "finish" in cl:         col_map["fecha_fin"] = col
                elif cl in ["lu","lun"]:     col_map["lu"] = col
                elif cl in ["ma","mar"]:     col_map["ma"] = col
                elif cl in ["mi","mie","mié"]: col_map["mi"] = col
                elif cl in ["ju","jue"]:     col_map["ju"] = col
                elif cl in ["vi","vie"]:     col_map["vi"] = col
                elif cl in ["sa","sab","sáb"]: col_map["sa"] = col
                elif cl in ["do","dom"]:     col_map["do"] = col

            # Filtrar filas válidas (que tengan OT numérico)
            ot_col = col_map.get("ot")
            if ot_col:
                df = df[df[ot_col].notna()]
                df = df[df[ot_col].astype(str).str.match(r'^\d+$')]

            st.success(f"✅ Excel leído — {len(df)} OTs encontradas")

            # Guardar en session_state para que no se pierda al presionar botón
            import json
            st.session_state["ot_df_json"] = df.to_json()
            st.session_state["ot_col_map"] = col_map

            # Parsear tipo de trabajo y equipo desde descripción
            def parsear_descripcion(desc):
                desc = str(desc)
                tipo = "inspeccion"
                if "mant" in desc.lower() or "4000" in desc or "2000" in desc or "8000" in desc:
                    tipo = "mantencion"
                elif "mec" in desc.lower() or "mecánico" in desc.lower():
                    tipo = "mecanico"

                # Detectar horas de mantención
                for hrs in ["16000","8000","4000","2000"]:
                    if hrs in desc:
                        tipo = f"mantencion_{hrs}hrs"
                        break
                return tipo

            def detectar_estado(obs):
                obs = str(obs).lower() if pd.notna(obs) else ""
                if "atrasad" in obs:
                    return "atrasado"
                elif "cerrar" in obs or "cerrado" in obs:
                    return "completado"
                return "pendiente"

            # Construir semana desde fecha inicio
            def get_semana(fecha):
                try:
                    if pd.notna(fecha):
                        return pd.to_datetime(fecha).strftime("%Y-W%V")
                except:
                    pass
                return semana_actual

            # Preview antes de importar
            st.markdown("#### Vista previa (primeras 5 OTs)")
            preview_data = []
            for _, row in df.head(5).iterrows():
                desc = row.get(col_map.get("descripcion",""), "")
                ot_n = row.get(col_map.get("ot",""), "")
                fi   = row.get(col_map.get("fecha_inicio",""), "")
                obs  = row.get(col_map.get("obs",""), "")
                preview_data.append({
                    "OT": str(ot_n),
                    "Descripción": str(desc)[:60],
                    "Inicio": str(fi)[:10],
                    "Estado": detectar_estado(obs)
                })
            if preview_data:
                import pandas as _pd2
                st.dataframe(_pd2.DataFrame(preview_data), hide_index=True, use_container_width=True)

            col_imp1, col_imp2 = st.columns(2)
            with col_imp1:
                sobrescribir = st.checkbox("Sobrescribir OTs existentes de esta semana", value=False, key="ot_sobrescribir")
            with col_imp2:
                importar_btn = st.button("📥 IMPORTAR OTs", use_container_width=True, type="primary", key="ot_importar_btn")

            if importar_btn:
                import pandas as _pd3, json as _json
                df_import = _pd3.read_json(st.session_state.get("ot_df_json", "{}"))
                col_map_imp = st.session_state.get("ot_col_map", col_map)
                importadas = 0
                errores = 0
                with st.spinner("Importando OTs..."):
                    for _, row in df_import.iterrows():
                        try:
                            ot_num = str(row.get(col_map_imp.get("ot",""), "")).strip()
                            if not ot_num or not ot_num.isdigit():
                                continue
                            desc = str(row.get(col_map_imp.get("descripcion",""), ""))
                            _obs_raw = row.get(col_map_imp.get("obs",""), "")
                            obs  = str(_obs_raw) if _pd3.notna(_obs_raw) else ""
                            fi   = row.get(col_map_imp.get("fecha_inicio",""), None)
                            ff   = row.get(col_map_imp.get("fecha_fin",""), None)

                            def safe_date(d):
                                try:
                                    return pd.to_datetime(d).strftime("%Y-%m-%d") if pd.notna(d) else None
                                except:
                                    return None

                            def safe_num(v):
                                try:
                                    return float(v) if pd.notna(v) else 0
                                except:
                                    return 0

                            registro = {
                                "centro":       str(row.get(col_map_imp.get("centro",""), "")),
                                "wbs":          str(row.get(col_map_imp.get("wbs",""), "")),
                                "descripcion":  desc,
                                "plan":         str(row.get(col_map_imp.get("plan",""), "")),
                                "ot":           ot_num,
                                "obs":          obs,
                                "fecha_inicio": safe_date(fi),
                                "fecha_fin":    safe_date(ff),
                                "horas_lu":     safe_num(row.get(col_map_imp.get("lu",""), 0)),
                                "horas_ma":     safe_num(row.get(col_map_imp.get("ma",""), 0)),
                                "horas_mi":     safe_num(row.get(col_map_imp.get("mi",""), 0)),
                                "horas_ju":     safe_num(row.get(col_map_imp.get("ju",""), 0)),
                                "horas_vi":     safe_num(row.get(col_map_imp.get("vi",""), 0)),
                                "horas_sa":     safe_num(row.get(col_map_imp.get("sa",""), 0)),
                                "horas_do":     safe_num(row.get(col_map_imp.get("do",""), 0)),
                                "estado":       detectar_estado(obs),
                                "tipo_trabajo": parsear_descripcion(desc),
                                "semana":       get_semana(fi),
                            }

                            if st.session_state.get("ot_sobrescribir", False):
                                supabase.table("ots").upsert(registro, on_conflict="ot").execute()
                            else:
                                supabase.table("ots").insert(registro).execute()
                            importadas += 1
                        except Exception as ex:
                            errores += 1

                st.success(f"✅ {importadas} OTs importadas correctamente")
                if errores:
                    st.warning(f"⚠️ {errores} filas con error (OTs duplicadas o datos inválidos)")
                st.rerun()

        except Exception as e:
            st.error(f"Error leyendo Excel: {e}")
            import traceback
            st.code(traceback.format_exc())

    st.divider()

    # ── Ver OTs por semana ──
    st.markdown("#### 📋 OTs de la semana")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        semana_ver = st.text_input("Semana", value=semana_actual, placeholder="2026-W11")
    with col_f2:
        filtro_estado = st.selectbox("Estado", ["Todos","pendiente","completado","atrasado"], key="ot_fest")
    with col_f3:
        filtro_centro = st.selectbox("Centro", ["Todos","CE01","CE02"], key="ot_fcen")

    try:
        q = supabase.table("ots").select("*").eq("semana", semana_ver)
        if filtro_estado != "Todos":
            q = q.eq("estado", filtro_estado)
        if filtro_centro != "Todos":
            q = q.eq("centro", filtro_centro)
        ots_data = q.order("fecha_inicio").execute().data or []
    except:
        ots_data = []

    if not ots_data:
        st.info("No hay OTs para esta semana. Sube el consolidado Excel arriba.")
    else:
        # Métricas rápidas
        total_ots = len(ots_data)
        pend  = sum(1 for o in ots_data if o.get("estado") == "pendiente")
        comp  = sum(1 for o in ots_data if o.get("estado") == "completado")
        atras = sum(1 for o in ots_data if o.get("estado") == "atrasado")

        m1,m2,m3,m4 = st.columns(4)
        with m1: st.markdown(f"<div class='metric-card'><div class='metric-n' style='color:#90cdf4'>{total_ots}</div><div class='metric-l'>Total OTs</div></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='metric-card'><div class='metric-n' style='color:#f6ad55'>{pend}</div><div class='metric-l'>Pendientes</div></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-card'><div class='metric-n' style='color:#48bb78'>{comp}</div><div class='metric-l'>Completadas</div></div>", unsafe_allow_html=True)
        with m4: st.markdown(f"<div class='metric-card'><div class='metric-n' style='color:#f56565'>{atras}</div><div class='metric-l'>Atrasadas</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Agrupar por día
        dias = ["Lu","Ma","Mi","Ju","Vi","Sa","Do"]
        dia_keys = ["horas_lu","horas_ma","horas_mi","horas_ju","horas_vi","horas_sa","horas_do"]

        # Agrupar OTs por su día principal (el que tiene horas)
        from collections import defaultdict
        por_dia = defaultdict(list)
        sin_dia = []

        for ot in ots_data:
            asignado = False
            for i, dk in enumerate(dia_keys):
                if ot.get(dk, 0) and float(ot.get(dk, 0)) > 0:
                    por_dia[dias[i]].append(ot)
                    asignado = True
            if not asignado:
                sin_dia.append(ot)

        for dia in dias:
            if por_dia[dia]:
                st.markdown(f"<div class='dia-header'>📆 {dia}nes" if dia=="Lu" else
                            f"<div class='dia-header'>📆 {dia}</div>" if dia!="Lu" else "", unsafe_allow_html=True)
                # Nombre completo del día
                nombres_dias = {"Lu":"Lunes","Ma":"Martes","Mi":"Miércoles",
                               "Ju":"Jueves","Vi":"Viernes","Sa":"Sábado","Do":"Domingo"}
                st.markdown(f"<div class='dia-header'>📆 {nombres_dias[dia]}</div>", unsafe_allow_html=True)

                for ot in por_dia[dia]:
                    estado = ot.get("estado","pendiente")
                    badge_cls = {"pendiente":"badge-pend","completado":"badge-comp","atrasado":"badge-atras"}.get(estado,"badge-pend")
                    borde_color = {"pendiente":"#f6ad55","completado":"#48bb78","atrasado":"#f56565"}.get(estado,"#f6ad55")
                    horas_dia = ot.get(dia_keys[dias.index(dia)], 0)
                    obs_html = f"<div class='ot-obs'>⚠️ {ot['obs']}</div>" if ot.get("obs") and ot["obs"] not in ["nan",""] else ""

                    st.markdown(f"""
                    <div class='ot-card' style='border-left-color:{borde_color};'>
                        <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                            <div style='flex:1;'>
                                <div class='ot-desc'>{ot.get('descripcion','')}</div>
                                <div class='ot-meta'>OT: {ot.get('ot','')} &nbsp;·&nbsp; Plan: {ot.get('plan','')} &nbsp;·&nbsp; {ot.get('centro','')} &nbsp;·&nbsp; {horas_dia} hrs</div>
                                {obs_html}
                            </div>
                            <span class='{badge_cls}'>{estado.upper()}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Botón marcar completado
                    if estado != "completado":
                        if st.button(f"✅ Marcar completado", key=f"comp_{ot['id']}"):
                            supabase.table("ots").update({"estado":"completado"}).eq("id", ot["id"]).execute()
                            st.rerun()

        if sin_dia:
            st.markdown("<div class='dia-header'>📋 Sin día asignado</div>", unsafe_allow_html=True)
            for ot in sin_dia:
                estado = ot.get("estado","pendiente")
                badge_cls = {"pendiente":"badge-pend","completado":"badge-comp","atrasado":"badge-atras"}.get(estado,"badge-pend")
                st.markdown(f"""
                <div class='ot-card'>
                    <div style='display:flex;justify-content:space-between;'>
                        <div>
                            <div class='ot-desc'>{ot.get('descripcion','')}</div>
                            <div class='ot-meta'>OT: {ot.get('ot','')} · {ot.get('fecha_inicio','')} → {ot.get('fecha_fin','')}</div>
                        </div>
                        <span class='{badge_cls}'>{estado.upper()}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ════════════════════════════════════════════════
# TAB 3 — HISTORIAL
# ════════════════════════════════════════════════
with tab3:
    st.subheader("Historial de Mantenciones")
    hc1, hc2, hc3 = st.columns(3)
    with hc1: hf_tag  = st.selectbox("TAG",  ["Todos"] + sorted(set(e["tag"] for e in cargar_equipos())), key="hf_t")
    with hc2: hf_tipo = st.selectbox("Tipo", ["Todos","INSPECCIÓN","2.000 hrs","4.000 hrs","8.000 hrs","16.000 hrs"], key="hf_tp")
    with hc3:
        if st.button("Actualizar"): st.rerun()

    hist = cargar_historial()
    if hf_tag  != "Todos": hist = [h for h in hist if h["tag"]  == hf_tag]
    if hf_tipo != "Todos": hist = [h for h in hist if h["tipo"] == hf_tipo]

    if hist:
        df = pd.DataFrame(hist)[["id","fecha","tag","tipo","horas_marcha","horas_carga","tecnico_1","tecnico_2","contacto"]]
        df.columns = ["ID","Fecha","TAG","Tipo","Hrs Marcha","Hrs Carga","Tecnico 1","Tecnico 2","Contacto"]
        st.dataframe(df, use_container_width=True, hide_index=True)
        with st.expander("Eliminar registro"):
            id_b = st.number_input("ID a eliminar", min_value=1, step=1)
            if st.button("Eliminar", type="primary"):
                if eliminar_registro_hist(id_b):
                    st.success(f"Registro {id_b} eliminado.")
                    st.rerun()
    else:
        st.info("No hay registros aun.")

# ════════════════════════════════════════════════
# TAB 4 — INFORMES GUARDADOS
# ════════════════════════════════════════════════
with tab4:
    st.subheader("Informes Word Guardados")
    if st.button("Actualizar lista"): st.rerun()
    try:
        ir = supabase.table("informes").select("*, historial(fecha,tag,tipo)").order("creado_en", desc=True).execute()
        informes = ir.data or []
    except Exception as e:
        informes = []
        st.warning(f"Error cargando informes: {e}")

    if informes:
        for inf in informes:
            hist_d = inf.get("historial",{}) or {}
            ia, ib, ic, id_ = st.columns([3,1,2,1])
            with ia: st.write(f"**{inf['nombre']}**")
            with ib: st.write(hist_d.get("fecha","—"))
            with ic: st.write(f"{hist_d.get('tag','—')} — {hist_d.get('tipo','—')}")
            with id_:
                url = obtener_url_informe(inf.get("ruta",""))
                if url: st.link_button("Descargar", url)
            st.divider()
    else:
        st.info("No hay informes guardados aun.")

# ════════════════════════════════════════════════
# ════════════════════════════════════════════════
# TAB PERFIL — Mi Perfil
# ════════════════════════════════════════════════
with tab_perfil:

    u = st.session_state["usuario_activo"]
    rol_color = {"admin": "#f6ad55", "supervisor": "#90cdf4", "tecnico": "#48bb78"}.get(u.get("rol",""), "#718096")
    rol_icon  = {"admin": "⚙️", "supervisor": "👁️", "tecnico": "🔧"}.get(u.get("rol",""), "👤")

    # ── CSS modo claro/oscuro ──
    tema_actual = u.get("tema", "oscuro")
    if tema_actual == "claro":
        st.markdown("""
        <style>
        .stApp { background: #f7f8fa !important; }
        .stApp::before { display:none; }
        .block-container { background: #f7f8fa; }
        p, label, .stMarkdown { color: #1a202c !important; }
        </style>
        """, unsafe_allow_html=True)

    import base64 as _b64

    # ── Header perfil ──
    foto_html = ""
    if u.get("foto_perfil"):
        foto_html = f"<img src='{u['foto_perfil']}' style='width:90px;height:90px;border-radius:50%;object-fit:cover;border:3px solid {rol_color};'>"
    else:
        iniciales = "".join([n[0].upper() for n in u.get("nombre","?").split()[:2]])
        foto_html = f"<div style='width:90px;height:90px;border-radius:50%;background:linear-gradient(135deg,#005B8E,#00A0C6);display:flex;align-items:center;justify-content:center;font-family:Rajdhani,sans-serif;font-size:2rem;font-weight:700;color:white;border:3px solid {rol_color};'>{iniciales}</div>"

    ultimo = u.get("ultimo_acceso","")
    if ultimo:
        try:
            from datetime import datetime as _dt
            ultimo_fmt = _dt.fromisoformat(ultimo).strftime("%d/%m/%Y %H:%M")
        except:
            ultimo_fmt = ultimo[:16]
    else:
        ultimo_fmt = "Primera sesión"

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#1a1f2e,#0f3460);border-radius:20px;
         padding:2rem;border:1px solid #2d3748;margin-bottom:1.5rem;
         display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;'>
        {foto_html}
        <div style='flex:1;min-width:200px;'>
            <div style='font-family:Rajdhani,sans-serif;font-size:1.8rem;
                 font-weight:700;color:#fff;'>{u.get("nombre","")}</div>
            <div style='color:#718096;font-size:0.85rem;margin:3px 0;'>{u.get("username","")}</div>
            <span style='background:rgba(0,160,198,0.15);color:{rol_color};
                border:1px solid {rol_color}33;border-radius:20px;
                padding:3px 12px;font-size:0.75rem;font-weight:600;
                letter-spacing:0.06em;'>{rol_icon} {u.get("rol","").upper()}</span>
        </div>
        <div style='text-align:right;min-width:160px;'>
            <div style='font-size:0.72rem;color:#4a5568;text-transform:uppercase;letter-spacing:0.08em;'>Último acceso</div>
            <div style='color:#90cdf4;font-size:0.85rem;margin-top:2px;'>{ultimo_fmt}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Estadísticas ──
    try:
        res_stats = supabase.table("historial").select("id, tipo, fecha").eq("tecnico_1", u.get("nombre","")).execute()
        mis_informes = res_stats.data or []
    except:
        mis_informes = []

    from datetime import datetime as _dt2
    mes_actual = _dt2.now().strftime("%Y-%m")
    este_mes   = [i for i in mis_informes if str(i.get("fecha","")).startswith(mes_actual)]
    total_inf  = len(mis_informes)
    mes_inf    = len(este_mes)

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-n' style='color:#90cdf4;font-size:2rem;'>{total_inf}</div>
            <div class='metric-l'>Informes Total</div></div>""", unsafe_allow_html=True)
    with s2:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-n' style='color:#48bb78;font-size:2rem;'>{mes_inf}</div>
            <div class='metric-l'>Este Mes</div></div>""", unsafe_allow_html=True)
    with s3:
        tipos = {}
        for i in mis_informes:
            t = i.get("tipo","")
            tipos[t] = tipos.get(t, 0) + 1
        top_tipo = max(tipos, key=tipos.get) if tipos else "—"
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-n' style='color:#f6ad55;font-size:1.3rem;'>{top_tipo}</div>
            <div class='metric-l'>Tipo más frecuente</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Editar perfil ──
    col_edit, col_pin = st.columns(2)

    with col_edit:
        st.markdown("#### ✏️ Editar Perfil")

        with st.form("form_perfil"):
            nuevo_tel   = st.text_input("📱 Teléfono", value=u.get("telefono",""), placeholder="+56 9 1234 5678")
            nueva_esp   = st.text_input("🏷️ Especialidad", value=u.get("especialidad",""), placeholder="Ej: Compresores rotativos")
            nueva_foto  = st.file_uploader("📸 Foto de perfil", type=["jpg","jpeg","png"], key="foto_perfil_up")
            nuevo_tema  = st.selectbox("🌙 Tema", ["oscuro", "claro"],
                                        index=0 if u.get("tema","oscuro")=="oscuro" else 1)
            guardar_p   = st.form_submit_button("💾 Guardar cambios", use_container_width=True, type="primary")

        if guardar_p:
            update_data = {
                "telefono":    nuevo_tel,
                "especialidad": nueva_esp,
                "tema":        nuevo_tema,
            }
            if nueva_foto:
                foto_bytes = nueva_foto.read()
                ext = nueva_foto.name.split(".")[-1].lower()
                mime = "image/jpeg" if ext in ["jpg","jpeg"] else "image/png"
                foto_b64 = _b64.b64encode(foto_bytes).decode()
                update_data["foto_perfil"] = f"data:{mime};base64,{foto_b64}"

            try:
                supabase.table("usuarios").update(update_data).eq("id", u["id"]).execute()
                # Actualizar session
                for k, v in update_data.items():
                    st.session_state["usuario_activo"][k] = v
                st.success("✅ Perfil actualizado")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with col_pin:
        st.markdown("#### 🔑 Cambiar PIN")

        with st.form("form_pin_perfil"):
            pin_act  = st.text_input("PIN actual", type="password", max_chars=4, placeholder="••••")
            pin_new  = st.text_input("Nuevo PIN", type="password", max_chars=4, placeholder="••••")
            pin_conf = st.text_input("Confirmar PIN", type="password", max_chars=4, placeholder="••••")
            cambiar  = st.form_submit_button("🔑 Cambiar PIN", use_container_width=True)

        if cambiar:
            if pin_act != u.get("pin",""):
                st.error("PIN actual incorrecto")
            elif pin_new != pin_conf:
                st.error("Los PINs no coinciden")
            elif len(pin_new) < 4:
                st.error("El PIN debe tener 4 dígitos")
            else:
                try:
                    supabase.table("usuarios").update({"pin": pin_new}).eq("id", u["id"]).execute()
                    st.session_state["usuario_activo"]["pin"] = pin_new
                    st.success("✅ PIN actualizado")
                except Exception as e:
                    st.error(f"Error: {e}")

        # Info de contacto si tiene teléfono
        if u.get("telefono") or u.get("especialidad"):
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📋 Mi Información")
            if u.get("telefono"):
                st.markdown(f"📱 **Teléfono:** {u.get('telefono')}")
            if u.get("especialidad"):
                st.markdown(f"🏷️ **Especialidad:** {u.get('especialidad')}")

# ════════════════════════════════════════════════
# TAB 5 — GESTIÓN DE USUARIOS (admin/supervisor)
# ════════════════════════════════════════════════
if tab5:
    with tab5:
        if usuario.get("rol") not in ["admin","supervisor"]:
            st.info("No tienes acceso a esta sección")
            st.stop()
        st.subheader("👥 Gestión de Usuarios")

        # Listar usuarios
        try:
            res_u = supabase.table("usuarios").select("*").order("rol").execute()
            usuarios_list = res_u.data or []
        except:
            usuarios_list = []

        if usuarios_list:
            for u in usuarios_list:
                rol_color = {"admin": "#f6ad55", "supervisor": "#90cdf4", "tecnico": "#48bb78"}.get(u.get("rol",""), "#718096")
                estado = "✅" if u.get("activo") else "❌"
                ua, ub, uc, ud = st.columns([2, 2, 1, 1])
                with ua: st.markdown("**" + u.get('nombre','') + "**  \n`" + u.get('username','') + "`")
                with ub: st.markdown(f"<span style='color:{rol_color};font-weight:600'>{u.get('rol','').upper()}</span>", unsafe_allow_html=True)
                with uc: st.markdown(estado)
                with ud:
                    if usuario.get("rol") == "admin":
                        if st.button("🗑️", key=f"del_u_{u['id']}", help="Desactivar"):
                            supabase.table("usuarios").update({"activo": False}).eq("id", u["id"]).execute()
                            st.rerun()
            st.divider()

        if usuario.get("rol") == "admin":
            st.markdown("#### ➕ Agregar Usuario")
            with st.form("form_nuevo_usuario"):
                nu1, nu2 = st.columns(2)
                with nu1:
                    nuevo_nombre   = st.text_input("Nombre completo")
                    nuevo_username = st.text_input("Usuario (sin espacios)")
                with nu2:
                    nuevo_pin  = st.text_input("PIN (4 dígitos)", max_chars=4)
                    nuevo_rol  = st.selectbox("Rol", ["tecnico", "supervisor", "admin"])
                guardar_u = st.form_submit_button("Guardar Usuario", use_container_width=True, type="primary")

            if guardar_u:
                if nuevo_nombre and nuevo_username and nuevo_pin:
                    try:
                        supabase.table("usuarios").insert({
                            "nombre": nuevo_nombre,
                            "username": nuevo_username.lower().strip(),
                            "pin": nuevo_pin,
                            "rol": nuevo_rol,
                            "activo": True
                        }).execute()
                        st.success(f"✅ Usuario {nuevo_nombre} creado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Completa todos los campos")

        st.divider()
        st.markdown("#### 🔑 Cambiar mi PIN")
        with st.form("form_cambiar_pin"):
            pin_actual  = st.text_input("PIN actual", type="password", max_chars=4)
            pin_nuevo   = st.text_input("Nuevo PIN", type="password", max_chars=4)
            pin_confirm = st.text_input("Confirmar nuevo PIN", type="password", max_chars=4)
            cambiar_pin = st.form_submit_button("Cambiar PIN", use_container_width=True)

        if cambiar_pin:
            if pin_nuevo != pin_confirm:
                st.error("Los PINs nuevos no coinciden")
            elif pin_actual != usuario.get("pin",""):
                st.error("PIN actual incorrecto")
            elif len(pin_nuevo) < 4:
                st.error("El PIN debe tener 4 dígitos")
            else:
                try:
                    supabase.table("usuarios").update({"pin": pin_nuevo}).eq("id", usuario["id"]).execute()
                    st.session_state["usuario_activo"]["pin"] = pin_nuevo
                    st.success("✅ PIN actualizado correctamente")
                except Exception as e:
                    st.error(f"Error: {e}")
