"""Premium PlanFit PDF: cover + photos + cards. Numbers come from the plan, not from images."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from envload import ROOT

ASSETS = ROOT / "assets"
PAGE_W, PAGE_H = A4

BLUE = colors.HexColor("#2563eb")
NAVY = colors.HexColor("#0f1c3f")
TEXT = colors.HexColor("#17202a")
MUTED = colors.HexColor("#667085")
LINE = colors.HexColor("#e5e7eb")
BG = colors.HexColor("#f4f7fb")
WHITE = colors.white
SOFT = colors.HexColor("#eff6ff")
PROT = colors.HexColor("#2563eb")
CARB = colors.HexColor("#38bdf8")
FAT = colors.HexColor("#1e3a8a")
WARN = colors.HexColor("#fef2f2")
WARN_LINE = colors.HexColor("#fecaca")

_FONT = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"
_RESAMPLE = getattr(PILImage, "Resampling", PILImage).LANCZOS


def _register_fonts() -> None:
    global _FONT, _FONT_BOLD
    candidates = [
        (Path(r"C:\Windows\Fonts\arial.ttf"), Path(r"C:\Windows\Fonts\arialbd.ttf")),
        (Path(r"C:\Windows\Fonts\segoeui.ttf"), Path(r"C:\Windows\Fonts\segoeuib.ttf")),
        (Path(r"C:\Windows\Fonts\calibri.ttf"), Path(r"C:\Windows\Fonts\calibrib.ttf")),
    ]
    for regular, bold in candidates:
        if regular.is_file() and bold.is_file():
            pdfmetrics.registerFont(TTFont("PlanFit", str(regular)))
            pdfmetrics.registerFont(TTFont("PlanFit-Bold", str(bold)))
            _FONT = "PlanFit"
            _FONT_BOLD = "PlanFit-Bold"
            return


_register_fonts()


def _asset(name: str) -> Path | None:
    path = ASSETS / name
    return path if path.is_file() else None


def _cover_reader(path: Path) -> ImageReader:
    img = PILImage.open(path).convert("RGB")
    tw, th = 1240, 1754
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    img = img.resize((nw, nh), _RESAMPLE)
    left = max(0, (nw - tw) // 2)
    top = max(0, (nh - th) // 2)
    img = img.crop((left, top, left + tw, top + th))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=88)
    buf.seek(0)
    return ImageReader(buf)


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "kicker": ParagraphStyle(
            "kicker", parent=base["Normal"], fontName=_FONT_BOLD,
            fontSize=8, textColor=BLUE, tracking=1, spaceAfter=2,
        ),
        "h": ParagraphStyle(
            "h", parent=base["Heading1"], fontName=_FONT_BOLD,
            fontSize=18, textColor=NAVY, spaceBefore=0, spaceAfter=6, leading=22,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontName=_FONT,
            fontSize=10, textColor=TEXT, leading=14, alignment=TA_JUSTIFY, spaceAfter=8,
        ),
        "left": ParagraphStyle(
            "left", parent=base["Normal"], fontName=_FONT,
            fontSize=10, textColor=TEXT, leading=14, alignment=TA_LEFT, spaceAfter=3,
        ),
        "small": ParagraphStyle(
            "small", parent=base["Normal"], fontName=_FONT,
            fontSize=8, textColor=MUTED, leading=11, alignment=TA_JUSTIFY,
        ),
        "card_k": ParagraphStyle(
            "card_k", parent=base["Normal"], fontName=_FONT,
            fontSize=8, textColor=MUTED, alignment=TA_CENTER, leading=11,
        ),
        "card_v": ParagraphStyle(
            "card_v", parent=base["Normal"], fontName=_FONT_BOLD,
            fontSize=13, textColor=NAVY, alignment=TA_CENTER, leading=16,
        ),
        "menu_title": ParagraphStyle(
            "menu_title", parent=base["Normal"], fontName=_FONT_BOLD,
            fontSize=11, textColor=BLUE, spaceAfter=4,
        ),
        "meal": ParagraphStyle(
            "meal", parent=base["Normal"], fontName=_FONT,
            fontSize=9, textColor=TEXT, leading=13, spaceAfter=2,
        ),
        "day_title": ParagraphStyle(
            "day_title", parent=base["Normal"], fontName=_FONT_BOLD,
            fontSize=11, textColor=NAVY, leading=14,
        ),
        "day_meta": ParagraphStyle(
            "day_meta", parent=base["Normal"], fontName=_FONT,
            fontSize=8, textColor=MUTED, alignment=TA_RIGHT, leading=12,
        ),
        "ex": ParagraphStyle(
            "ex", parent=base["Normal"], fontName=_FONT,
            fontSize=9.5, textColor=TEXT, leading=13,
        ),
        "label": ParagraphStyle(
            "label", parent=base["Normal"], fontName=_FONT,
            fontSize=8, textColor=MUTED,
        ),
        "value": ParagraphStyle(
            "value", parent=base["Normal"], fontName=_FONT_BOLD,
            fontSize=10, textColor=TEXT,
        ),
        "disc": ParagraphStyle(
            "disc", parent=base["Normal"], fontName=_FONT,
            fontSize=8, textColor=MUTED, leading=11, alignment=TA_JUSTIFY,
        ),
        "th": ParagraphStyle(
            "th", parent=base["Normal"], fontName=_FONT_BOLD,
            fontSize=8, textColor=WHITE, leading=11,
        ),
        "td": ParagraphStyle(
            "td", parent=base["Normal"], fontName=_FONT,
            fontSize=8.5, textColor=TEXT, leading=12,
        ),
        "td_b": ParagraphStyle(
            "td_b", parent=base["Normal"], fontName=_FONT_BOLD,
            fontSize=8.5, textColor=NAVY, leading=12,
        ),
        "bar_l": ParagraphStyle(
            "bar_l", parent=base["Normal"], fontName=_FONT_BOLD,
            fontSize=9, textColor=NAVY, leading=12,
        ),
        "bar_r": ParagraphStyle(
            "bar_r", parent=base["Normal"], fontName=_FONT,
            fontSize=8.5, textColor=MUTED, alignment=TA_RIGHT, leading=12,
        ),
        "dont": ParagraphStyle(
            "dont", parent=base["Normal"], fontName=_FONT,
            fontSize=9.5, textColor=TEXT, leading=13,
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Normal"], fontName=_FONT_BOLD,
            fontSize=12, textColor=NAVY, spaceBefore=4, spaceAfter=6, leading=15,
        ),
    }


def _cover_page(canvas, doc) -> None:
    info = getattr(doc, "cover_info", {}) or {}
    cover = _asset("cover.jpg")
    canvas.saveState()
    if cover:
        canvas.drawImage(_cover_reader(cover), 0, 0, width=PAGE_W, height=PAGE_H)
    else:
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    canvas.setFillColor(colors.Color(0.06, 0.10, 0.24, alpha=0.42))
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    band_h = 128 * mm
    canvas.setFillColor(colors.Color(0.06, 0.11, 0.25, alpha=0.92))
    canvas.rect(0, 0, PAGE_W, band_h, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(0, band_h, PAGE_W, 3.2, fill=1, stroke=0)

    canvas.setFillColor(WHITE)
    canvas.setFont(_FONT_BOLD, 11)
    canvas.drawString(18 * mm, PAGE_H - 16 * mm, "PLANFIT")
    canvas.setFont(_FONT, 9)
    canvas.drawRightString(PAGE_W - 18 * mm, PAGE_H - 16 * mm, "Uso único · no se publica en la web")

    y = 92 * mm
    canvas.setFillColor(BLUE)
    canvas.setFont(_FONT_BOLD, 9)
    canvas.drawString(18 * mm, y + 22 * mm, "PLAN PERSONALIZADO  ·  12 SEMANAS")

    canvas.setFillColor(WHITE)
    canvas.setFont(_FONT_BOLD, 26)
    name = str(info.get("name") or "Tu plan")
    canvas.drawString(18 * mm, y, name[:42])

    canvas.setFont(_FONT, 13)
    canvas.setFillColor(colors.HexColor("#dbe7ff"))
    canvas.drawString(18 * mm, y - 10 * mm, str(info.get("goal") or ""))

    canvas.setFillColor(WHITE)
    canvas.setFont(_FONT_BOLD, 16)
    arrow = f"{info.get('weight', '')} kg   →   {info.get('target', '')} kg"
    canvas.drawString(18 * mm, y - 24 * mm, arrow)

    canvas.setFont(_FONT, 10)
    canvas.setFillColor(colors.HexColor("#c9d4ea"))
    meta = "  ·  ".join(p for p in info.get("meta_bits") or [] if p)
    canvas.drawString(18 * mm, 18 * mm, meta)
    canvas.restoreState()


def _body_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 11 * mm, PAGE_W, 11 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont(_FONT_BOLD, 9)
    canvas.drawString(16 * mm, PAGE_H - 7.2 * mm, "PlanFit")
    canvas.setFont(_FONT, 8)
    canvas.drawRightString(PAGE_W - 16 * mm, PAGE_H - 7.2 * mm, "Plan personalizado · 12 semanas")
    canvas.setFillColor(BG)
    canvas.rect(0, 0, PAGE_W, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(MUTED)
    canvas.setFont(_FONT, 7.5)
    canvas.drawString(16 * mm, 5 * mm, "Guía general · no sustituye valoración profesional")
    canvas.drawRightString(PAGE_W - 16 * mm, 5 * mm, f"Página {doc.page}")
    canvas.restoreState()


def _fitted_jpeg(path: Path, width: float, height: float, zoom: float = 1.0) -> Image:
    img = PILImage.open(path).convert("RGB")
    tw = max(8, int(width * 72 / 25.4 * 2))
    th = max(8, int(height * 72 / 25.4 * 2))
    iw, ih = img.size
    scale = max(tw / iw, th / ih) * zoom
    nw, nh = max(tw, int(iw * scale)), max(th, int(ih * scale))
    img = img.resize((nw, nh), _RESAMPLE)
    left = max(0, (nw - tw) // 2)
    top = max(0, (nh - th) // 2)
    img = img.crop((left, top, left + tw, top + th))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=86)
    buf.seek(0)
    flow = Image(buf, width=width, height=height)
    flow.hAlign = "CENTER"
    flow._keep_buf = buf
    return flow


def _photo(name: str, width: float, height: float):
    path = _asset(name)
    if not path:
        return Spacer(width, 4)
    return _fitted_jpeg(path, width, height)


def _icon(name: str, size: float = 14 * mm):
    path = _asset(name)
    if not path:
        return Spacer(size, size)
    return _fitted_jpeg(path, size, size, zoom=1.18)


def _section_head(icon_file: str, kicker: str, title: str, styles: dict):
    icon = _icon(icon_file, 16 * mm)
    text = [
        Paragraph(kicker.upper(), styles["kicker"]),
        Paragraph(title, styles["h"]),
    ]
    inner = Table([[icon, text]], colWidths=[20 * mm, 154 * mm])
    inner.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return inner


def _stat_cards(items: list[tuple[str, str]], styles: dict, col_w: float) -> Table:
    cells = []
    for label, value in items:
        block = [Paragraph(label, styles["card_k"]), Paragraph(value, styles["card_v"])]
        cells.append(block)
    table = Table([cells], colWidths=[col_w] * len(items))
    cmds = [
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("BOX", (0, 0), (-1, -1), 0.3, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]
    for i in range(len(items)):
        cmds.append(("LINEABOVE", (i, 0), (i, 0), 2.2, BLUE))
    table.setStyle(TableStyle(cmds))
    return table


def _menu_card(menu: dict, styles: dict, width: float) -> Table:
    body = [
        Paragraph(menu["name"], styles["menu_title"]),
        Paragraph(f"<b>Desayuno</b>  {menu['breakfast']}", styles["meal"]),
        Paragraph(f"<b>Almuerzo</b>  {menu['lunch']}", styles["meal"]),
        Paragraph(f"<b>Merienda</b>  {menu['snack']}", styles["meal"]),
        Paragraph(f"<b>Cena</b>  {menu['dinner']}", styles["meal"]),
    ]
    card = Table([[body]], colWidths=[width])
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("BOX", (0, 0), (-1, -1), 0.3, LINE),
                ("LINEBEFORE", (0, 0), (0, 0), 3.2, BLUE),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return card


def _workout_day(day: dict, styles: dict, width: float) -> Table:
    header = Table(
        [[
            Paragraph(day["title"], styles["day_title"]),
            Paragraph(day["sets"], styles["day_meta"]),
        ]],
        colWidths=[width * 0.68, width * 0.32],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    rows = [[header]]
    for i, ex in enumerate(day["exercises"], start=1):
        rows.append([Paragraph(f"{i}.  {ex}", styles["ex"])])
    card = Table(rows, colWidths=[width])
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 1), (-1, -1), WHITE),
                ("BOX", (0, 0), (-1, -1), 0.3, LINE),
                ("LEFTPADDING", (0, 1), (-1, -1), 10),
                ("RIGHTPADDING", (0, 1), (-1, -1), 10),
                ("TOPPADDING", (0, 1), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ]
        )
    )
    return card


def _macro_bars(macros: dict, styles: dict, width: float) -> Table:
    rows = [
        ("Proteína", macros["protein_g"], macros["protein_pct"], PROT),
        ("Carbohidratos", macros["carb_g"], macros["carb_pct"], CARB),
        ("Grasa", macros["fat_g"], macros["fat_pct"], FAT),
    ]
    bar_w = width * 0.58
    blocks = []
    for label, grams, pct, color in rows:
        filled = max(6, bar_w * (pct / 100.0))
        empty = max(1, bar_w - filled)
        fill = Table([[""]], colWidths=[filled])
        fill.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        track = Table([[fill, ""]], colWidths=[filled, empty])
        track.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        line = Table(
            [[
                Paragraph(label, styles["bar_l"]),
                track,
                Paragraph(f"{grams} g  ·  {pct}%", styles["bar_r"]),
            ]],
            colWidths=[width * 0.22, bar_w, width * 0.20],
        )
        line.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        blocks.append([line])
    wrap = Table(blocks, colWidths=[width])
    wrap.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("BOX", (0, 0), (-1, -1), 0.3, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return wrap


def _kv_rows(rows: list[tuple[str, str]], styles: dict, width: float, header: tuple[str, str] | None = None) -> Table:
    data = []
    if header:
        data.append([Paragraph(header[0], styles["th"]), Paragraph(header[1], styles["th"])])
    for left, right in rows:
        data.append([Paragraph(left, styles["td_b"]), Paragraph(right, styles["td"])])
    col0 = width * 0.32
    table = Table(data, colWidths=[col0, width - col0])
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.3, LINE),
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
    ]
    if header:
        cmds += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("BACKGROUND", (0, 1), (0, -1), BG),
        ]
    else:
        cmds.append(("BACKGROUND", (0, 0), (0, -1), BG))
    table.setStyle(TableStyle(cmds))
    return table


def _bullet_block(items: list[str], styles: dict, width: float) -> Table:
    inner = [[Paragraph(f"•  {item}", styles["left"])] for item in items]
    table = Table(inner, colWidths=[width])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("BOX", (0, 0), (-1, -1), 0.3, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def _dont_box(items: list[str], styles: dict, width: float) -> Table:
    inner = [[Paragraph(f"✕  {item}", styles["dont"])] for item in items]
    table = Table(inner, colWidths=[width])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WARN),
        ("BOX", (0, 0), (-1, -1), 0.6, WARN_LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _prog_table(rows: list[tuple[str, str, str]], styles: dict, width: float) -> Table:
    data = [[
        Paragraph("Periodo", styles["th"]),
        Paragraph("Foco", styles["th"]),
        Paragraph("Qué hacer", styles["th"]),
    ]]
    for a, b, c in rows:
        data.append([
            Paragraph(a, styles["td_b"]),
            Paragraph(b, styles["td"]),
            Paragraph(c, styles["td"]),
        ])
    table = Table(data, colWidths=[width * 0.22, width * 0.16, width * 0.62])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
        ("GRID", (0, 0), (-1, -1), 0.3, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 1), (0, -1), SOFT),
    ]))
    return table


def _chips(title: str, items: list[str], styles: dict) -> Table:
    text = Paragraph(f"<b>{title}</b>  {', '.join(items)}", styles["left"])
    table = Table([[text]], colWidths=[174 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BG),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("BOX", (0, 0), (-1, -1), 0.2, LINE),
            ]
        )
    )
    return table


def build_pdf(path: Path, user: dict, plan: dict, payment_ref: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    w = plan["workout"]
    macros = plan["macros"]
    content_w = 178 * mm

    doc = BaseDocTemplate(
        str(path),
        pagesize=A4,
        title=f"PlanFit — {user['name']}",
        author="PlanFit",
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    doc.cover_info = {
        "name": user["name"],
        "goal": plan["goal_label"],
        "weight": user["weight"],
        "target": user["targetWeight"],
        "meta_bits": [
            f"{w['days']} días / semana",
            w["location"],
            f"{w['duration']} min",
            w["experience"],
            f"Foco: {w['focus']}",
        ],
    }

    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, id="cover", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    body_frame = Frame(
        16 * mm, 14 * mm, PAGE_W - 32 * mm, PAGE_H - 28 * mm,
        id="body", showBoundary=0,
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="Cover", frames=[cover_frame], onPage=_cover_page),
            PageTemplate(id="Body", frames=[body_frame], onPage=_body_page),
        ]
    )

    sex_label = "Hombre" if user["sex"] == "male" else "Mujer"
    habits = plan.get("habits") or {}
    story: list = [NextPageTemplate("Body"), PageBreak()]

    story.append(_section_head("icon-habits.jpg", "Antes de empezar", "Cómo usar este documento", styles))
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            "Este PDF es tu plan de 12 semanas. No se publica en la web. "
            "Léelo una vez de seguido y después úsalo como referencia. "
            "Cada bloque tiene un propósito:",
            styles["body"],
        )
    )
    story.append(_kv_rows(plan.get("intro") or [], styles, content_w, ("Sección", "Para qué sirve")))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Cosas que no debes hacer", styles["h3"]))
    story.append(_dont_box(plan.get("donts") or [], styles, content_w))

    story.append(PageBreak())
    story.append(_section_head("icon-food.jpg", "Tu ficha", "Así empieza el plan", styles))
    story.append(Spacer(1, 4 * mm))
    story.append(
        _stat_cards(
            [
                ("Objetivo", plan["goal_label"]),
                ("Peso inicial", f"{user['weight']} kg"),
                ("Meta 12 sem.", f"{user['targetWeight']} kg"),
                ("IMC", str(user["bmi"])),
            ],
            styles,
            content_w / 4,
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(
        _stat_cards(
            [
                ("Edad", f"{user['age']} años"),
                ("Altura", f"{user['height']} cm"),
                ("Sexo", sex_label),
                ("Motivación", plan["motivation_label"]),
            ],
            styles,
            content_w / 4,
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            f"Referencia de pago <b>{payment_ref}</b> · {user['email']}. "
            "Este documento corresponde a un único pago y no se muestra en la web.",
            styles["small"],
        )
    )

    story.append(Spacer(1, 8 * mm))
    story.append(_section_head("icon-food.jpg", "Alimentación", "Tus números y menús guía", styles))
    story.append(Spacer(1, 3 * mm))
    story.append(_photo("food.jpg", content_w, 58 * mm))
    story.append(Spacer(1, 4 * mm))
    story.append(
        _stat_cards(
            [
                ("Calorías", f"{plan['calories']} kcal"),
                ("Proteína", f"{macros['protein_g']} g"),
                ("Carbos", f"{macros['carb_g']} g"),
                ("Grasa", f"{macros['fat_g']} g"),
            ],
            styles,
            content_w / 4,
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(_macro_bars(macros, styles, content_w))
    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            "Cifras de partida. Si el peso no se mueve en 14 días, ajusta 100–150 kcal. "
            "Alterna los 3 menús según tus preferencias; no hace falta copiarlos al gramo.",
            styles["body"],
        )
    )
    story.append(Paragraph("Cómo contar calorías y macros", styles["h3"]))
    story.append(_bullet_block(plan.get("calorie_guide") or [], styles, content_w))
    story.append(Spacer(1, 4 * mm))
    story.append(_chips("Vegetales", user["vegetables"], styles))
    story.append(Spacer(1, 2 * mm))
    story.append(_chips("Frutas", user["fruits"], styles))
    story.append(Spacer(1, 2 * mm))
    story.append(_chips("Proteínas", user["proteins"], styles))
    story.append(Spacer(1, 2 * mm))
    story.append(_chips("Carbohidratos", user["carbs"], styles))
    story.append(Spacer(1, 5 * mm))

    menu_w = (content_w - 6 * mm) / 2
    menus = plan["menus"]
    if len(menus) >= 2:
        pair = Table(
            [[_menu_card(menus[0], styles, menu_w), _menu_card(menus[1], styles, menu_w)]],
            colWidths=[menu_w, menu_w],
        )
        pair.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 6),
            ("LEFTPADDING", (1, 0), (1, 0), 0),
        ]))
        story.append(pair)
        story.append(Spacer(1, 4 * mm))
    if len(menus) >= 3:
        story.append(_menu_card(menus[2], styles, content_w))

    story.append(PageBreak())
    story.append(_section_head("icon-gym.jpg", "Entrenamiento", "Tu rutina de 12 semanas", styles))
    story.append(Spacer(1, 3 * mm))
    story.append(_photo("gym.jpg", content_w, 58 * mm))
    story.append(Spacer(1, 4 * mm))
    story.append(
        _stat_cards(
            [
                ("Frecuencia", f"{w['days']} días"),
                ("Lugar", w["location"]),
                ("Sesión", f"{w['duration']} min"),
                ("Foco", w["focus"]),
            ],
            styles,
            content_w / 4,
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        _stat_cards(
            [
                ("Descanso", w.get("rest", "75-90 s")),
                ("Tempo", "2-3 s bajada"),
                ("Reserva", "1-2 reps"),
                ("Nivel", w["experience"]),
            ],
            styles,
            content_w / 4,
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(w.get("tempo", ""), styles["body"]))
    story.append(Paragraph("Calentamiento", styles["h3"]))
    story.append(_bullet_block(w.get("warmup") or [], styles, content_w))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("Progresión de 12 semanas", styles["h3"]))
    story.append(_prog_table(w.get("progression_table") or [], styles, content_w))
    story.append(Spacer(1, 2 * mm))
    if w.get("cooldown"):
        story.append(Paragraph(w["cooldown"], styles["body"]))

    story.append(Spacer(1, 3 * mm))
    for day in w["schedule"]:
        story.append(KeepTogether([_workout_day(day, styles, content_w), Spacer(1, 3.5 * mm)]))

    story.append(PageBreak())
    story.append(_section_head("icon-food.jpg", "Sustituciones", "Si falta un alimento o un ejercicio", styles))
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            "Cambia una cosa por otra de la misma lista. No sustituyas proteína por pan, ni sentadilla por 40 minutos de bici.",
            styles["body"],
        )
    )
    if plan.get("food_swaps"):
        story.append(Paragraph("Alimentos", styles["h3"]))
        story.append(_kv_rows(plan["food_swaps"], styles, content_w, ("Eliges", "Puedes usar")))
        story.append(Spacer(1, 4 * mm))
    if plan.get("exercise_swaps"):
        story.append(Paragraph("Ejercicios", styles["h3"]))
        story.append(_kv_rows(plan["exercise_swaps"], styles, content_w, ("Programado", "Alternativa")))

    story.append(Spacer(1, 8 * mm))
    story.append(_section_head("icon-habits.jpg", "Hábitos", "Lo que sostiene el plan", styles))
    story.append(Spacer(1, 3 * mm))
    story.append(
        _stat_cards(
            [
                ("Agua", f"{habits.get('water_l', '—')} L"),
                ("Sueño", habits.get("sleep", "7-9 h")),
                ("Pasos", habits.get("steps", "8.000")),
                ("Báscula", "promedio 3 días"),
            ],
            styles,
            content_w / 4,
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            f"Agua: unos <b>{habits.get('water_ml', 0)} ml</b> al día "
            f"({habits.get('water_l', 0)} litros), repartidos. "
            f"Pasos: <b>{habits.get('steps', '')}</b>. {habits.get('steps_note', '')} "
            f"{habits.get('scale', '')}",
            styles["body"],
        )
    )

    disc = Table(
        [[
            Paragraph(
                "<b>Importante.</b> Este documento es una guía general y no sustituye la evaluación "
                "de un médico, nutricionista o profesional del ejercicio. Si tienes una condición médica, "
                "lesión, embarazo, trastorno alimentario o tomas medicamentos, consulta a un profesional "
                "antes de realizar cambios importantes en alimentación o ejercicio. "
                "Si hay un error en los datos, no reutilices el enlace: escribe a soporte.",
                styles["disc"],
            )
        ]],
        colWidths=[content_w],
    )
    disc.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BG),
                ("BOX", (0, 0), (-1, -1), 0.3, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(disc)

    doc.build(story)
    return path
