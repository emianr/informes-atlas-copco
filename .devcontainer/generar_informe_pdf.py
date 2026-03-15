"""
Generador de Informe PDF - Centinela / Atlas Copco
Formato basado en el informe oficial de Minera Spence
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import Flowable
from reportlab.platypus import Image as RLImage
import io
from datetime import datetime

# ── Colores Atlas Copco ──────────────────────────────────────────
AC_BLUE   = colors.HexColor("#005B8E")
AC_TEAL   = colors.HexColor("#00A0C6")
LINE_BLUE = colors.HexColor("#0099CC")
DARK      = colors.HexColor("#1a1a1a")
GRAY      = colors.HexColor("#666666")
LIGHT_BG  = colors.HexColor("#F5F5F5")

# ── Estilos de texto ─────────────────────────────────────────────
def get_styles():
    return {
        "normal": ParagraphStyle("normal", fontName="Helvetica", fontSize=9, leading=13, textColor=DARK),
        "small":  ParagraphStyle("small",  fontName="Helvetica", fontSize=8, leading=11, textColor=DARK),
        "bold":   ParagraphStyle("bold",   fontName="Helvetica-Bold", fontSize=9, leading=13, textColor=DARK),
        "bold_blue": ParagraphStyle("bold_blue", fontName="Helvetica-Bold", fontSize=10,
                                    leading=14, textColor=AC_BLUE),
        "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=9,
                                   leading=13, textColor=DARK),
        "header_right": ParagraphStyle("header_right", fontName="Helvetica", fontSize=9,
                                        leading=13, textColor=DARK, alignment=TA_LEFT),
        "tag_title": ParagraphStyle("tag_title", fontName="Helvetica-Bold", fontSize=11,
                                     leading=15, textColor=DARK),
        "right": ParagraphStyle("right", fontName="Helvetica", fontSize=9,
                                 leading=13, textColor=DARK, alignment=TA_RIGHT),
    }


class HorizontalLine(Flowable):
    def __init__(self, width, color=LINE_BLUE, thickness=1):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)

    def wrap(self, *args):
        return (self.width, self.thickness + 2)


def generar_pdf(datos: dict) -> bytes:
    """
    datos = {
        "fecha": "13/03/2026",
        "contacto": "Pamela Arancibia",
        "tag": "DES-GC-001",
        "equipo_modelo": "BSD-65",
        "serie": "1120-6867842",
        "ubicacion": "Descarga de ácido, planta hidrometalurgia",
        "planta": "Planta Hidrometalurgia",
        "nivel_aceite": "100%",
        "presion_salida": "92 psi",
        "temp_elemento": "7°C",
        "banda_carga": "76 psi",
        "banda_descarga": "94 psi",
        "comentarios": "Se realiza inspección programada...",
        "tecnico_1": "Ariel Molina",
        "tecnico_2": "Emian Sanchez",
        "horas_1": "2",
        "horas_marcha": "44856",
        "orden_servicio": "4724006",
        "tipo_orden": "INSPECCIÓN",
        "proxima_visita": "2000 Hrs / Corresponde pauta de: [ 2.000hrs ]",
        "actividades": [
            ("1.-Inspección visual de equipo", True, "Inspección general"),
            ("2.-Chequeo y/o limpieza filtro de aire", True, "Inspección y limpieza"),
            ...
        ]
    }
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    W = A4[0] - 36*mm  # ancho útil
    S = get_styles()
    story = []

    # ══════════════════════════════════════════════
    # CABECERA: Logo + datos empresa
    # ══════════════════════════════════════════════
    import os
    logo_ac_path   = os.path.join(os.path.dirname(__file__), "logo_atlascopco.jpeg")
    logo_her_path  = os.path.join(os.path.dirname(__file__), "logo_herramienta.jpg")

    logos_content = []
    if os.path.exists(logo_ac_path):
        logos_content.append(RLImage(logo_ac_path, width=42*mm, height=18*mm))
    else:
        logos_content.append(Paragraph("<b>Atlas Copco</b>", S["bold_blue"]))

    if os.path.exists(logo_her_path):
        logos_content.append(RLImage(logo_her_path, width=16*mm, height=18*mm))

    logo_cell = Table(
        [logos_content],
        colWidths=[44*mm, 18*mm] if len(logos_content) == 2 else [44*mm],
    )
    logo_cell.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 3*mm),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    header_info = [
        Paragraph(f"Date:{datos.get('fecha','')}", S["header_right"]),
        Paragraph("<b>Minera Centinela</b>", S["header_right"]),
        Paragraph("APOQUINDO 4001 OF 1802 LAS CONDES", S["header_right"]),
        Paragraph("7550162, SANTIAGO/XIII", S["header_right"]),
        Paragraph(f"Contacto:{datos.get('contacto','')}", S["header_right"]),
    ]

    header_table = Table(
        [[logo_cell, [p for p in header_info]]],
        colWidths=[W * 0.38, W * 0.62],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════
    # TÍTULO TAG + línea
    # ══════════════════════════════════════════════
    story.append(Paragraph(
        f"<b>Comentarios Equipo T.A.G. :{datos.get('tag','')}</b>",
        S["bold_blue"]
    ))
    story.append(HorizontalLine(W, LINE_BLUE, 1.5))
    story.append(Spacer(1, 4*mm))

    # Fecha y OT
    story.append(Paragraph(datos.get("fecha", "").replace("/", "-").replace("/", "-"), S["normal"]))
    story.append(Paragraph(f"OT: {datos.get('orden_servicio','')}", S["normal"]))
    story.append(Spacer(1, 3*mm))

    # Equipo y TAG
    story.append(Paragraph(f"Equipo compresor: {datos.get('equipo_modelo','')}", S["normal"]))
    story.append(Paragraph(f"TAG: {datos.get('tag','')}.", S["normal"]))
    story.append(Spacer(1, 3*mm))

    # Parámetros
    story.append(Paragraph("Parámetros:", S["normal"]))
    params = [
        f"Nivel de aceite: {datos.get('nivel_aceite','')}",
        f"Presión de Salida: {datos.get('presion_salida','')}",
        f"Temperatura salida elemento: {datos.get('temp_elemento','')}",
        f"Banda de presión: carga {datos.get('banda_carga','')}, descarga {datos.get('banda_descarga','')}",
    ]
    for p in params:
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;• &nbsp;{p}", S["normal"]))
    story.append(Spacer(1, 3*mm))

    # Ubicación
    story.append(Paragraph(
        f"Ubicado en {datos.get('ubicacion','')}, {datos.get('planta','')}.",
        S["normal"]
    ))
    story.append(Spacer(1, 3*mm))

    # Comentarios / cuerpo del informe
    comentarios = datos.get("comentarios", "")
    for linea in comentarios.split("\n"):
        if linea.strip():
            story.append(Paragraph(linea.strip(), S["normal"]))
    story.append(Spacer(1, 8*mm))

    # ══════════════════════════════════════════════
    # CONFIRMACIÓN DE TIEMPOS
    # ══════════════════════════════════════════════
    story.append(Paragraph("<b>Confirmacion de Tiempos</b>", S["bold_blue"]))
    story.append(HorizontalLine(W, LINE_BLUE, 1.5))
    story.append(Spacer(1, 2*mm))

    tiempos_header = [
        Paragraph("<b>Fecha</b>", S["bold"]),
        Paragraph("<b>Tecnicos</b>", S["bold"]),
        Paragraph("<b>Tipo de Actividad</b>", S["bold"]),
        Paragraph("<b>Horas / Kilometros</b>", S["bold"]),
    ]
    tiempos_rows = [tiempos_header]

    tec1 = datos.get("tecnico_1", "")
    tec2 = datos.get("tecnico_2", "")
    hrs1 = datos.get("horas_1", "2")
    fecha = datos.get("fecha", "")

    if tec1:
        tiempos_rows.append([
            Paragraph(fecha, S["normal"]),
            Paragraph(tec1, S["normal"]),
            Paragraph("M.obra.St / H.traslado", S["normal"]),
            Paragraph(f"{hrs1} / 0 / 0", S["normal"]),
        ])
    if tec2:
        tiempos_rows.append([
            Paragraph(fecha, S["normal"]),
            Paragraph(tec2, S["normal"]),
            Paragraph("M.obra.St / H.traslado", S["normal"]),
            Paragraph(f"{hrs1} / 0 / 0", S["normal"]),
        ])

    tiempos_table = Table(
        tiempos_rows,
        colWidths=[W*0.18, W*0.28, W*0.32, W*0.22],
    )
    tiempos_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.lightgrey),
    ]))
    story.append(tiempos_table)
    story.append(Spacer(1, 2*mm))

    # ══════════════════════════════════════════════
    # TABLA EQUIPO (2 columnas)
    # ══════════════════════════════════════════════
    equipo_data = [
        [
            Paragraph("<b>Equipo</b>", S["bold"]), "",
            "", ""
        ],
        [
            Paragraph("<b>Equipo:</b>", S["bold"]),
            Paragraph(datos.get("equipo_modelo", ""), S["normal"]),
            Paragraph("<b>Fecha de Servicio:</b>", S["bold"]),
            Paragraph(datos.get("fecha", ""), S["normal"]),
        ],
        [
            Paragraph("<b>Numero de Serie:</b>", S["bold"]),
            Paragraph(datos.get("serie", ""), S["normal"]),
            Paragraph("<b>Orden de servicio:</b>", S["bold"]),
            Paragraph(datos.get("orden_servicio", ""), S["normal"]),
        ],
        [
            Paragraph("<b>Horas Marcha:</b>", S["bold"]),
            Paragraph(str(datos.get("horas_marcha", "")), S["normal"]),
            Paragraph("<b>Tipo de Orden:</b>", S["bold"]),
            Paragraph(datos.get("tipo_orden", ""), S["bold"]),
        ],
    ]

    equipo_table = Table(
        equipo_data,
        colWidths=[W*0.22, W*0.28, W*0.22, W*0.28],
    )
    equipo_table.setStyle(TableStyle([
        ("SPAN", (0, 0), (3, 0)),
        ("BACKGROUND", (0, 0), (3, 0), LIGHT_BG),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, LINE_BLUE),
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, LINE_BLUE),
    ]))
    story.append(equipo_table)
    story.append(Spacer(1, 1*mm))

    # Próxima visita
    story.append(Paragraph("<b>Proxima Visita</b>", S["section"]))
    story.append(HorizontalLine(W, LINE_BLUE, 0.8))
    story.append(Paragraph(datos.get("proxima_visita", ""), S["normal"]))
    story.append(Spacer(1, 2*mm))

    # ══════════════════════════════════════════════
    # SERVICIO EJECUTADO / ACTIVIDADES
    # ══════════════════════════════════════════════
    story.append(Paragraph("<b>Servicio Ejecutado</b>", S["section"]))
    story.append(HorizontalLine(W, LINE_BLUE, 0.8))
    story.append(Paragraph("<b>Actividades</b>", S["section"]))
    story.append(Spacer(1, 2*mm))

    # Lista de actividades con checkmark
    actividades = datos.get("actividades", ACTIVIDADES_DEFAULT)
    act_rows = []
    for act, ok, descripcion in actividades:
        check = "✓" if ok else "○"
        act_rows.append([
            Paragraph(f"• {act}", S["small"]),
            Paragraph(f"• {check}", S["small"]),
            Paragraph(f"• {descripcion}", S["small"]),
        ])

    # Dividir en dos mitades para dos columnas
    mid = len(act_rows) // 2 + len(act_rows) % 2
    col1 = act_rows[:mid]
    col2 = act_rows[mid:]

    # Rellenar col2 si es más corta
    while len(col2) < len(col1):
        col2.append(["", "", ""])

    # Combinar en tabla de 6 columnas (3+3)
    combined = []
    for i in range(len(col1)):
        row = col1[i] + (col2[i] if i < len(col2) else ["", "", ""])
        combined.append(row)

    act_table = Table(
        combined,
        colWidths=[W*0.27, W*0.05, W*0.18, W*0.27, W*0.05, W*0.18],
    )
    act_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(act_table)
    story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════════════
    # REGISTRO FOTOGRÁFICO
    # ══════════════════════════════════════════════
    story.append(Paragraph("<b>Registro Fotografico</b>", S["bold_blue"]))
    story.append(HorizontalLine(W, LINE_BLUE, 1.5))
    story.append(Spacer(1, 2*mm))

    # Dos cajas vacías para fotos
    foto_cell_w = (W - 6*mm) / 2
    foto_cell_h = 50*mm

    class FotoBox(Flowable):
        def __init__(self, w, h):
            Flowable.__init__(self)
            self.w = w
            self.h = h
        def wrap(self, *args):
            return (self.w, self.h)
        def draw(self):
            self.canv.setStrokeColor(colors.HexColor("#AAAAAA"))
            self.canv.setFillColor(colors.HexColor("#E8E8E8"))
            self.canv.rect(0, 0, self.w, self.h, fill=1)
            self.canv.setFillColor(colors.HexColor("#BBBBBB"))
            cx, cy = self.w/2, self.h/2
            # Silueta montaña
            self.canv.setFillColor(colors.HexColor("#CCCCCC"))
            from reportlab.graphics.shapes import Drawing
            self.canv.setLineWidth(0)

    foto_table = Table(
        [[FotoBox(foto_cell_w, foto_cell_h), FotoBox(foto_cell_w, foto_cell_h)]],
        colWidths=[foto_cell_w, foto_cell_w],
        spaceBefore=0,
    )
    foto_table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3*mm),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(foto_table)

    # ── Build ────────────────────────────────────
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# Actividades por defecto (INSPECCIÓN)
ACTIVIDADES_DEFAULT = [
    ("1.-Inspección visual de equipo", True, "Inspección general"),
    ("2.-Chequeo y/o limpieza filtro de aire", True, "Inspección y limpieza"),
    ("3.-Revisión enfriadores de aceite", True, "Inspección general"),
    ("4.-Revisión enfriadores de aire", True, "Inspección general y soplado"),
    ("16.-Inspección visual de flexibles", True, "Inspección"),
    ("17.-Inspección de Arnes de cables", True, "Inspección"),
    ("18.-Revisión de ventiladores", True, "Inspección general"),
    ("19.-Inspección de fugas de aire", True, "Inspección sin fugas"),
    ("20.-Inspección de fugas de aceite", True, "Inspección sin fugas"),
    ("21.-Chequeo y/o cambio de filtro pañete", True, "Inspección y soplado"),
    ("22.-Chequeo y/o cambio correas", True, "N/A"),
    ("23.-Revisan de drenaje automático / manual", True, "Reemplazado"),
    ("24.-Estado estructural", True, "Inspección general"),
    ("25.-Chequeo operacional", True, "Pruebas operacionales en carga y descarga de equipo."),
]


# Test rápido
if __name__ == "__main__":
    datos_prueba = {
        "fecha": "13/03/2026",
        "contacto": "Pamela Arancibia",
        "tag": "DES-GC-001",
        "equipo_modelo": "BSD-65",
        "serie": "1120-6867842",
        "ubicacion": "descarga de ácido",
        "planta": "planta hidrometalurgia",
        "nivel_aceite": "100%",
        "presion_salida": "92 psi",
        "temp_elemento": "7°C",
        "banda_carga": "76 psi",
        "banda_descarga": "94 psi",
        "comentarios": (
            "Se realiza inspección programada.\n"
            "Se chequea parámetros en módulo de control óptimos.\n"
            "Se chequea existencia de fugas y filtraciones. Sin observaciones\n"
            "Se chequea carrocería. Sin observaciones\n"
            "Se realizan pruebas operacionales en carga y descarga de equipo, "
            "operando de forma óptima según configuración en módulo de control.\n"
            "Equipo operativo."
        ),
        "tecnico_1": "Ariel Molina",
        "tecnico_2": "Emian Sanchez",
        "horas_1": "2",
        "horas_marcha": "44856",
        "orden_servicio": "4724006",
        "tipo_orden": "INSPECCIÓN",
        "proxima_visita": "2000 Hrs / Corresponde pauta de: [ 2.000hrs ]",
        "actividades": ACTIVIDADES_DEFAULT,
    }
    pdf_bytes = generar_pdf(datos_prueba)
    with open("/mnt/user-data/outputs/informe_prueba.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("PDF generado OK, tamaño:", len(pdf_bytes), "bytes")
