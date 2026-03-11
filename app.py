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

# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='font-family:Rajdhani,sans-serif;font-size:2.4rem;color:#e2e8f0;'>🛡️ CENTINELA</h1><p style='color:#718096;margin-top:-10px;'>Sistema de Gestión de Equipos — Minera Spence</p>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🏭 Equipos", "📋 Generar Informe", "📊 Historial", "📁 Informes"])

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
# TAB 2 — GENERAR INFORME
# ════════════════════════════════════════════════
with tab2:
    equipos_list = cargar_equipos()
    tags_list    = [e["tag"] for e in equipos_list]

    ct1, ct2 = st.columns(2)
    with ct1: tag_sel   = st.selectbox("TAG del equipo", tags_list, key="inf_tag")
    with ct2: tipo_mant = st.selectbox("Tipo de Mantencion", ["INSPECCION","P1","P2","P3"])

    eq_inf = next((e for e in equipos_list if e["tag"] == tag_sel), {})
    mod_aut  = eq_inf.get("modelo","")
    ser_aut  = eq_inf.get("serie","")
    loc_aut  = eq_inf.get("subarea","")
    area_aut = eq_inf.get("area","")
    st.info(f"Equipo: {mod_aut} | Serie: {ser_aut} | Subarea: {loc_aut} | Area: {area_aut}")

    try:
        ur = supabase.table("historial").select("*").eq("tag", tag_sel).order("creado_en", desc=True).limit(1).execute()
        ult_inf = ur.data[0] if ur.data else None
    except:
        ult_inf = None

    h_sug   = int(ult_inf["horas_marcha"]) if ult_inf else 0
    hc_sug  = int(ult_inf["horas_carga"])  if ult_inf else 0
    if ult_inf:
        st.caption(f"Ultimo registro: {ult_inf['fecha']} — {ult_inf['tipo']} — {h_sug} hrs marcha")

    st.divider()
    with st.form("form_informe"):
        st.subheader("Datos Generales")
        fi1, fi2 = st.columns(2)
        with fi1:
            fecha_sel    = st.date_input("Fecha", datetime.now())
            tec1         = st.text_input("Tecnico 1", st.secrets.get("tec1_default","Ignacio Morales"))
        with fi2:
            cliente_cont = st.text_input("Contacto Cliente", st.secrets.get("contacto_default","Pamela Tapia"))
            tec2         = st.text_input("Tecnico 2", st.secrets.get("tec2_default","Emian Sanchez"))

        st.subheader("Horas")
        fh1, fh2 = st.columns(2)
        with fh1: h_marcha = st.number_input("Horas Marcha", value=h_sug, step=1)
        with fh2: h_carga  = st.number_input("Horas Carga",  value=hc_sug, step=1)

        st.subheader("Parametros")
        fp1, fp2, fp3 = st.columns(3)
        with fp1: v_p_carga    = st.text_input("Presion Carga (bar)", "6.4")
        with fp2: v_p_descarga = st.text_input("Presion Descarga (bar)", "6.8")
        with fp3: v_t_salida   = st.text_input("Temp. Salida (C)", "80")

        st.subheader("Contenido del Informe")
        tpl = get_plantilla(tipo_mant, mod_aut, tag_sel, loc_aut, area_aut, v_p_carga, v_p_descarga, v_t_salida)
        alcance_m     = st.text_area("Alcance",        value=tpl["alcance"],         height=70)
        actividades_m = st.text_area("Actividades",    value=tpl["actividades"],     height=220)
        condicion_m   = st.text_area("Condicion Final",value=tpl["condicion"],       height=90)
        rec_m         = st.text_area("Recomendaciones",value=tpl["recomendaciones"], height=90)
        st.divider()
        enviar = st.form_submit_button("GUARDAR Y GENERAR REPORTE", use_container_width=True)

    if enviar:
        TEMPLATE_PATH = "InformeInspección.docx"
        if not os.path.exists(TEMPLATE_PATH):
            st.error(f"Template Word no encontrado: '{TEMPLATE_PATH}'")
            st.stop()
        try:
            doc   = DocxTemplate(TEMPLATE_PATH)
            meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
            fecha_txt = f"{fecha_sel.day} de {meses[fecha_sel.month-1]} de {fecha_sel.year}"
            contexto = {
                "fecha": fecha_txt, "cliente_contact": cliente_cont,
                "alcanze_intervencion": alcance_m, "operaciones_dinamicas": actividades_m,
                "p_carga": v_p_carga, "p_descarga": v_p_descarga, "temp_salida": v_t_salida,
                "estado_entrega": condicion_m, "recomendaciones": rec_m,
                "proxima_visita": tpl["proxima_visita"],
                "tecnico_1": tec1, "tecnico_2": tec2,
                "act_1": "Mantenimiento", "h_1": "8", "h_2": "8",
                "equipo_modelo": mod_aut, "serie": ser_aut,
                "horas_marcha": f"{h_marcha} Hrs.", "tipo_orden": tpl["tipo_orden_txt"],
                "horas_totales_despues": h_marcha, "horas_carga_despues": h_carga, "tag": tag_sel,
            }
            doc.render(contexto)
            output = io.BytesIO()
            doc.save(output)
            ab = output.getvalue()
            nf = f"Informe_{tipo_mant}_{tag_sel}_{fecha_sel}.docx"

            with st.spinner("Guardando..."):
                rid = guardar_registro({
                    "fecha": str(fecha_sel), "tag": tag_sel, "tipo": tipo_mant,
                    "horas_marcha": h_marcha, "horas_carga": h_carga,
                    "tecnico_1": tec1, "tecnico_2": tec2, "contacto": cliente_cont,
                    "p_carga": v_p_carga, "p_descarga": v_p_descarga, "temp_salida": v_t_salida,
                    "alcance": alcance_m, "actividades": actividades_m,
                    "condicion": condicion_m, "recomendaciones": rec_m,
                })
                if rid: guardar_informe_storage(rid, nf, ab)

            st.success(f"Guardado — {tpl['tipo_orden_txt']} | {tag_sel} | {fecha_txt}")
            st.download_button("DESCARGAR REPORTE", ab, nf,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

# ════════════════════════════════════════════════
# TAB 3 — HISTORIAL
# ════════════════════════════════════════════════
with tab3:
    st.subheader("Historial de Mantenciones")
    hc1, hc2, hc3 = st.columns(3)
    with hc1: hf_tag  = st.selectbox("TAG",  ["Todos"] + sorted(set(e["tag"] for e in cargar_equipos())), key="hf_t")
    with hc2: hf_tipo = st.selectbox("Tipo", ["Todos","INSPECCION","P1","P2","P3"], key="hf_tp")
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



