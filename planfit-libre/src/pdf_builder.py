"""PDF Gary Felicien Fit — plan personalizado de 12 semanas (diseño negro y dorado)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    CondPageBreak,
    Flowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from contenido import build_full_plan, miles

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

PAGE_W, PAGE_H = A4
MARGIN = 45
CONTENT_W = PAGE_W - 2 * MARGIN

BLACK = colors.HexColor("#0b0c0f")
GOLD = colors.HexColor("#d4a017")
CREAM = colors.HexColor("#f6f1e8")
CREAM2 = colors.HexColor("#f3ede2")
LINE = colors.HexColor("#e6dfd2")
INK = colors.HexColor("#1a1714")
MUTED = colors.HexColor("#5a5855")
TAN = colors.HexColor("#c4a574")
BROWN = colors.HexColor("#3d3224")
NAVY = colors.HexColor("#0f1a3d")
WHITE = colors.white

FONT, FONT_B = "Helvetica", "Helvetica-Bold"


def _register_fonts() -> None:
    global FONT, FONT_B
    candidates = [
        (Path(r"C:\Windows\Fonts\arial.ttf"), Path(r"C:\Windows\Fonts\arialbd.ttf")),
        (Path("/System/Library/Fonts/Supplemental/Arial.ttf"), Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")),
        (Path("/Library/Fonts/Arial.ttf"), Path("/Library/Fonts/Arial Bold.ttf")),
        (ASSETS / "fonts" / "LiberationSans-Regular.ttf", ASSETS / "fonts" / "LiberationSans-Bold.ttf"),
    ]
    for regular, bold in candidates:
        if regular.is_file() and bold.is_file():
            pdfmetrics.registerFont(TTFont("GFF", str(regular)))
            pdfmetrics.registerFont(TTFont("GFF-Bold", str(bold)))
            pdfmetrics.registerFontFamily("GFF", normal="GFF", bold="GFF-Bold", italic="GFF", boldItalic="GFF-Bold")
            FONT, FONT_B = "GFF", "GFF-Bold"
            return


_register_fonts()


def esc(text: object) -> str:
    return escape(str(text))


# ---------------------------------------------------------------- estilos


def _styles() -> dict:
    base = dict(fontName=FONT, textColor=INK)
    return {
        "body": ParagraphStyle("body", fontSize=9.8, leading=14.2, alignment=TA_JUSTIFY, spaceAfter=6, **base),
        "bodyl": ParagraphStyle("bodyl", fontSize=9.8, leading=14.2, spaceAfter=6, **base),
        "h2": ParagraphStyle("h2", fontName=FONT_B, fontSize=12, leading=15, textColor=INK, spaceBefore=6, spaceAfter=5, keepWithNext=1),
        "h3": ParagraphStyle("h3", fontName=FONT_B, fontSize=9.8, leading=13, textColor=INK, spaceBefore=3, spaceAfter=2, keepWithNext=1),
        "cell": ParagraphStyle("cell", fontSize=7.8, leading=10.6, **base),
        "cellb": ParagraphStyle("cellb", fontName=FONT_B, fontSize=7.8, leading=10.6, textColor=INK),
        "cellh": ParagraphStyle("cellh", fontName=FONT_B, fontSize=7.6, leading=10.6, textColor=WHITE),
        "small": ParagraphStyle("small", fontSize=7, leading=10, textColor=MUTED, fontName=FONT),
        "kicker": ParagraphStyle("kicker", fontName=FONT_B, fontSize=7, leading=9, textColor=GOLD),
        "head": ParagraphStyle("head", fontName=FONT_B, fontSize=12.5, leading=16, textColor=WHITE),
        "dark": ParagraphStyle("dark", fontSize=8.6, leading=12.6, textColor=WHITE, fontName=FONT),
        "darksig": ParagraphStyle("darksig", fontName=FONT_B, fontSize=7.4, leading=10, textColor=GOLD, spaceBefore=3),
        "statl": ParagraphStyle("statl", fontSize=7, leading=9, textColor=MUTED, alignment=TA_CENTER, fontName=FONT),
        "statv": ParagraphStyle("statv", fontName=FONT_B, fontSize=11.5, leading=14, textColor=INK, alignment=TA_CENTER),
        "boxt": ParagraphStyle("boxt", fontName=FONT_B, fontSize=10, leading=13, textColor=INK),
        "boxx": ParagraphStyle("boxx", fontSize=8.4, leading=11.6, textColor=INK, fontName=FONT),
        "callout": ParagraphStyle("callout", fontSize=9.2, leading=12.6, textColor=INK, fontName=FONT),
        "mtitle": ParagraphStyle("mtitle", fontName=FONT_B, fontSize=8.8, leading=11.4, textColor=INK),
        "mdet": ParagraphStyle("mdet", fontSize=7.6, leading=10.4, textColor=MUTED, fontName=FONT),
        "mhead": ParagraphStyle("mhead", fontName=FONT_B, fontSize=12, leading=15, textColor=WHITE),
        "mdays": ParagraphStyle("mdays", fontSize=7.4, leading=10, textColor=GOLD, alignment=TA_RIGHT, fontName=FONT),
        "rtitle": ParagraphStyle("rtitle", fontName=FONT_B, fontSize=9.6, leading=12.4, textColor=INK),
        "rmeta": ParagraphStyle("rmeta", fontSize=7, leading=9.5, textColor=GOLD, fontName=FONT, spaceAfter=4),
        "rsec": ParagraphStyle("rsec", fontName=FONT_B, fontSize=7, leading=9.5, textColor=GOLD, spaceBefore=2),
        "rtxt": ParagraphStyle("rtxt", fontSize=7.8, leading=10.6, textColor=INK, fontName=FONT),
        "exn": ParagraphStyle("exn", fontName=FONT_B, fontSize=8.8, leading=11.2, textColor=INK),
        "ext": ParagraphStyle("ext", fontSize=7.2, leading=9.6, textColor=MUTED, fontName=FONT),
        "exr": ParagraphStyle("exr", fontSize=7.4, leading=10, textColor=INK, alignment=TA_RIGHT, fontName=FONT),
        "dayh": ParagraphStyle("dayh", fontName=FONT_B, fontSize=11, leading=14, textColor=WHITE),
        "dayhr": ParagraphStyle("dayhr", fontSize=7.4, leading=10, textColor=GOLD, alignment=TA_RIGHT, fontName=FONT),
        "week": ParagraphStyle("week", fontSize=9.2, leading=12, textColor=INK, fontName=FONT),
    }


S: dict = {}

# ---------------------------------------------------------------- piezas


class Divider(Flowable):
    """Línea dorada con un punto negro al centro."""

    def __init__(self, width: float = CONTENT_W + 6, space: float = 10):
        super().__init__()
        self.width = width
        self.space = space

    def wrap(self, aw, ah):
        return self.width, self.space * 2

    def draw(self):
        c = self.canv
        y = self.space
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.3)
        c.line(6, y, self.width, y)
        c.setFillColor(BLACK)
        c.circle((6 + self.width) / 2, y, 2.2, stroke=0, fill=1)


def section(kicker: str, title: str) -> list:
    t = Table(
        [[[Paragraph(esc(kicker.upper()), S["kicker"]), Spacer(1, 2), Paragraph(esc(title), S["head"])]]],
        colWidths=[CONTENT_W],
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BLACK),
                ("LINEBEFORE", (0, 0), (0, -1), 3, GOLD),
                ("LEFTPADDING", (0, 0), (-1, -1), 11),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return [t, Divider()]


def dark_box(kicker: str | None, text: str, signature: str | None, width: float = CONTENT_W) -> Table:
    inner = []
    if kicker:
        inner += [Paragraph(esc(kicker.upper()), S["kicker"]), Spacer(1, 3)]
    inner.append(Paragraph(text, S["dark"]))
    if signature:
        inner.append(Paragraph(esc(signature), S["darksig"]))
    t = Table([[inner]], colWidths=[width])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BLACK),
                ("LINEBEFORE", (0, 0), (0, -1), 3, GOLD),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return t


def pact(stage: str, text: str, name: str) -> list:
    return [Spacer(1, 4), dark_box(f"El pacto · {stage}", text, f"— {name} · Lo firmaste."), Spacer(1, 10)]


def quote(text: str, author: str) -> list:
    return [Spacer(1, 6), dark_box(None, f"“{esc(text)}”", f"— {author}"), Spacer(1, 10)]


def cream_box(flowables: list, width: float = CONTENT_W, pad: float = 10, border=GOLD) -> Table:
    t = Table([[flowables]], colWidths=[width])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CREAM2),
                ("BOX", (0, 0), (-1, -1), 0.9, border),
                ("LEFTPADDING", (0, 0), (-1, -1), pad),
                ("RIGHTPADDING", (0, 0), (-1, -1), pad),
                ("TOPPADDING", (0, 0), (-1, -1), pad - 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), pad - 2),
            ]
        )
    )
    return t


def callout_rows(lines: list[str]) -> KeepTogether:
    rows = [[Paragraph(line, S["callout"])] for line in lines]
    t = Table(rows, colWidths=[CONTENT_W])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CREAM2),
                ("BOX", (0, 0), (-1, -1), 0.9, GOLD),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return KeepTogether([t])


def data_table(header: list[str], rows: list[list], widths: list[float], first_bold: bool = True, row_h=None) -> Table:
    data = [[Paragraph(esc(h), S["cellh"]) for h in header]]
    for r in rows:
        cells = []
        for i, v in enumerate(r):
            if isinstance(v, Flowable):
                cells.append(v)
            else:
                cells.append(Paragraph(esc(v), S["cellb"] if (i == 0 and first_bold) else S["cell"]))
        data.append(cells)
    t = Table(data, colWidths=widths, rowHeights=[None] + [row_h] * len(rows) if row_h else None, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BLACK),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("INNERGRID", (0, 1), (-1, -1), 0.6, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ]
    if first_bold:
        style.append(("BACKGROUND", (0, 1), (0, -1), CREAM2))
    t.setStyle(TableStyle(style))
    return t


def stat_cards(items: list[tuple[str, str]], gold_top: bool = True) -> Table:
    cells = [[Paragraph(esc(l), S["statl"]), Spacer(1, 2), Paragraph(esc(v), S["statv"])] for l, v in items]
    t = Table([cells], colWidths=[CONTENT_W / len(items)] * len(items))
    style = [
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]
    if gold_top:
        style.append(("LINEABOVE", (0, 0), (-1, 0), 2, GOLD))
    t.setStyle(TableStyle(style))
    return t


def photo(name: str, width: float, height: float) -> Flowable | None:
    path = ASSETS / name
    if not path.is_file():
        return None
    img = PILImage.open(path).convert("RGB")
    iw, ih = img.size
    target = width / height
    if iw / ih > target:
        nw = int(ih * target)
        img = img.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
    else:
        nh = int(iw / target)
        img = img.crop((0, (ih - nh) // 2, iw, (ih - nh) // 2 + nh))
    from io import BytesIO

    buf = BytesIO()
    img.save(buf, "JPEG", quality=86)
    buf.seek(0)
    return Image(buf, width=width, height=height)


class Bar(Flowable):
    def __init__(self, pct: float, color, width: float, height: float = 15):
        super().__init__()
        self.pct, self.color, self.width, self.height = pct, color, width, height

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(CREAM2)
        c.rect(0, 0, self.width, self.height, stroke=0, fill=1)
        c.setFillColor(self.color)
        c.rect(0, 0, self.width * self.pct / 100.0, self.height, stroke=0, fill=1)


class Check(Flowable):
    """Casillas: [] sí  [] no, o una sola casilla con texto."""

    def __init__(self, labels: list[str], gap: float = 34, size: float = 8.5, font_size: float = 7.4):
        super().__init__()
        self.labels, self.gap, self.size, self.fs = labels, gap, size, font_size

    def wrap(self, aw, ah):
        self.width = aw
        return aw, self.size + 2

    def draw(self):
        c = self.canv
        c.setStrokeColor(INK)
        c.setLineWidth(0.7)
        x = 0
        for label in self.labels:
            c.rect(x, 1, self.size, self.size, stroke=1, fill=0)
            c.setFillColor(INK)
            c.setFont(FONT, self.fs)
            c.drawString(x + self.size + 3, 2.2, label)
            x += self.gap


class Water(Flowable):
    def __init__(self, size: float = 8.5):
        super().__init__()
        self.size = size

    def wrap(self, aw, ah):
        return aw, self.size + 2

    def draw(self):
        c = self.canv
        c.setStrokeColor(INK)
        c.setLineWidth(0.9)
        x = 0
        for i in range(8):
            if i == 4:
                x += 6
            c.rect(x, 1, self.size, self.size, stroke=1, fill=0)
            x += self.size + 1.6


# ---------------------------------------------------------------- portada y marco


def _cover(c, doc) -> None:
    user, plan = doc.gff_user, doc.gff_plan
    path = ASSETS / "gff-cover.jpg"
    if path.is_file():
        img = PILImage.open(path).convert("RGB")
        iw, ih = img.size
        target = PAGE_W / PAGE_H
        if iw / ih > target:
            nw = int(ih * target)
            img = img.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
        c.drawImage(ImageReader(img), 0, 0, PAGE_W, PAGE_H)
    else:
        c.setFillColor(BLACK)
        c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    split = PAGE_H * 0.433
    c.saveState()
    c.setFillColor(NAVY)
    c.setFillAlpha(0.28)
    c.rect(0, split, PAGE_W, PAGE_H - split, stroke=0, fill=1)
    c.setFillAlpha(0.9)
    c.rect(0, 0, PAGE_W, split, stroke=0, fill=1)
    c.restoreState()
    c.setStrokeColor(GOLD)
    c.setLineWidth(2.2)
    c.line(0, split, PAGE_W, split)

    c.setFillColor(WHITE)
    c.setFont(FONT_B, 10)
    c.drawString(51, PAGE_H - 45, "GARY FELICIEN FIT")
    c.setFont(FONT, 7.6)
    c.drawRightString(PAGE_W - 51, PAGE_H - 45, "Plan personal · no se publica en la web")

    y = split - 42
    c.setFillColor(GOLD)
    c.setFont(FONT_B, 7.8)
    c.drawString(51, y, "PLAN PERSONALIZADO  ·  12 SEMANAS")
    c.setFillColor(WHITE)
    c.setFont(FONT_B, 25)
    c.drawString(51, y - 56, user["name"])
    c.setFont(FONT, 12)
    c.drawString(51, y - 80, plan["goal_label"])
    c.setFont(FONT_B, 14.5)
    c.drawString(51, y - 112, f"{user['weight']:.1f} kg   →   {user['targetWeight']:.1f} kg")
    c.setFont(FONT, 8.4)
    c.setFillColor(colors.HexColor("#c9cbd3"))
    focus = "Equilibrado" if user["focusMuscle"] == "balanced" else plan["focus_label"]
    meta = "  ·  ".join(
        [
            f"{user['days']} días / semana",
            plan["location_label"],
            f"{user['duration']} min",
            plan["experience_label"],
            f"Foco: {focus}",
        ]
    )
    c.drawString(51, 52, meta)


def _frame(c, doc) -> None:
    c.saveState()
    c.setFillColor(BLACK)
    c.rect(0, PAGE_H - 30, PAGE_W, 30, stroke=0, fill=1)
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.6)
    c.line(0, PAGE_H - 32.5, PAGE_W, PAGE_H - 32.5)
    c.setFillColor(WHITE)
    c.setFont(FONT_B, 8.6)
    c.drawString(MARGIN, PAGE_H - 19, "Gary Felicien Fit")
    c.setFont(FONT, 7.4)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 19, "Plan personalizado · 12 semanas")
    c.setFillColor(CREAM2)
    c.rect(0, 0, PAGE_W, 34, stroke=0, fill=1)
    c.setFillColor(MUTED)
    c.setFont(FONT, 6.8)
    c.drawString(MARGIN, 14, "Guía general · no sustituye valoración profesional")
    c.drawRightString(PAGE_W - MARGIN, 14, f"Página {doc.page}")
    c.restoreState()


# ---------------------------------------------------------------- secciones


def _intro(user: dict, name: str) -> list:
    self_word = "mí misma" if user["sex"] == "female" else "mí mismo"
    story = section("Antes de empezar", "Nada de esto es magia")
    story += [
        Paragraph(
            "Lo que vas a leer no es información sagrada ni un atajo. Es un plan de 12 semanas: números de partida, "
            "menús guía y una rutina. Solo funciona si lo cumples con constancia. Si lo lees y no lo haces, no falló el "
            "PDF: no hubo plan.",
            S["body"],
        ),
        Paragraph(
            "Este documento no sustituye a un médico. Si algo duele de forma rara, paras y consultas. No hace falta "
            "motivación todos los días. Hace falta el mismo pacto del día 1.",
            S["body"],
        ),
        cream_box(
            [
                Paragraph(
                    f"Yo, {name}, me comprometo a cumplir el plan aquí presentado, siguiendo las instrucciones con "
                    f"honestidad. Quiero cambiar mi vida y cuidar mi salud. Sé que si no lo hago, solo me estaría "
                    f"mintiendo y perjudicándome a {self_word}.",
                    ParagraphStyle("pl", parent=S["body"], fontSize=9.4, leading=14, spaceAfter=0),
                )
            ],
            pad=12,
        ),
        Spacer(1, 12),
        Paragraph("Firma: _______________________________ Fecha: ____ / ____ / ________", S["bodyl"]),
    ]
    story += quote(
        "Odié cada minuto de entrenamiento, pero me dije: sufre ahora y vive el resto de tu vida como un campeón.",
        "Muhammad Ali · Boxeo",
    )
    story.append(Paragraph("Cómo está armado este documento", S["h2"]))
    rows = [
        ("El pacto", "Lo firmas al inicio. El resto del documento es cómo cumplirlo 12 semanas."),
        ("Glosario", "Las palabras del plan (kcal, TMB, macros, reserva). Léelo una vez; después es consulta."),
        ("Tu ficha", "Quién eres en este plan: peso, meta, objetivo. Si un dato está mal, genera el plan de nuevo."),
        ("Alimentación", "Calorías y macros de partida, 4 menús y recetario con tus alimentos."),
        ("Cómo contar y leer envases", "Para que los números no sean magia: se aprenden y se usan."),
        ("Entrenamiento", "Rutina por días, con series, descanso, pistas y por qué está armada así."),
        ("Hábitos", "Agua, sueño y pasos. Sostienen el plan más que cualquier suplemento."),
        ("Medidas y fotos", "Cinta, peso promedio, fotos y ropa testigo. Se usan para no mentirte."),
        ("Planner de 12 semanas", "La bitácora que se imprime y se marca. Aquí se ve si el pacto sigue en pie."),
        ("Lo que no debes hacer", "Errores que rompen el progreso. Léelos antes de empezar."),
    ]
    story.append(data_table(["Sección", "Para qué sirve"], rows, [CONTENT_W * 0.31, CONTENT_W * 0.69]))
    story.append(PageBreak())
    return story


DONTS = [
    "No cortes las calorías por debajo de este plan para 'ir más rápido'.",
    "No te saltes comidas para compensar un exceso.",
    "No compares el peso de cada día: usa el promedio de la semana.",
    "No entrenes con dolor agudo, mareo, o si te falta el aire de forma rara.",
    "No copies rutinas de redes ni añadas series extra en las semanas 1-4.",
    "No uses laxantes, diuréticos ni 'quemadores' para ver la báscula.",
    "No cambies de plan cada semana: 12 semanas de lo mismo ganan a 12 planes distintos.",
    "No abandones el sueño o los pasos para 'hacer más gym'. Sin eso, el plan no sostiene.",
]

GLOSSARY = [
    ("kcal", "Kilocaloría: la “caloría” de las etiquetas. Energía que da la comida y que el cuerpo gasta."),
    ("TMB", "Tasa metabólica basal: calorías que gastas en reposo, solo por estar vivo."),
    ("Gasto del día (TDEE)", "TMB más moverte, entrenar y digerir. El plan se calcula a partir de aquí."),
    ("NEAT", "Energía que gastas al caminar, estar de pie y hacer la casa. Suele ser más que la hora de gym."),
    ("Macronutrientes (macros)", "Nutrientes que comes en gramos, no en miligramos: proteína, carbohidratos y grasa. De ellos salen casi todas las calorías."),
    ("Proteína", "Nutriente hecho de aminoácidos. Está en carne, pescado, huevos, lácteos y legumbres. Aporta 4 kcal por gramo; repara músculo y sacia."),
    ("Carbohidratos", "Azúcares y almidones. Están en arroz, papa, avena, pan y fruta. El cuerpo los usa como combustible, sobre todo en el gym. 4 kcal por gramo."),
    ("Grasa (de la comida)", "Lípidos: aceite, frutos secos, yema, pescado graso, palta. No es la grasa del cuerpo. 9 kcal por gramo; sirve para hormonas y para absorber vitaminas A, D, E y K."),
    ("Déficit", "Comer un poco por debajo del gasto. Así baja la grasa corporal, sin recortar a lo loco."),
    ("Porción", "La cantidad que comes, no el envase entero."),
    ("Crudo vs cocido", "100 g de arroz crudo no son 100 g cocidos. Se pesa como indica la etiqueta."),
    ("Serie y repetición", "Una serie es un bloque. Las repeticiones son cada subida y bajada."),
    ("Reserva", "Dejar 1–2 repeticiones sin hacer. No llegas al fallo."),
    ("Tempo", "Velocidad del movimiento. Aquí: 2–3 s al bajar, subida controlada."),
    ("Empuje / tirón", "Empujas (pecho, hombros, tríceps) o tiras (espalda, bíceps)."),
    ("IMC", "Peso y altura en una cifra. Es un punto de partida, no un veredicto."),
    ("Perímetro", "Medida con cinta: cuello, pecho, cintura, cadera, brazo, muslo."),
    ("Promedio de 3 días", "Tres pesajes en ayunas. Ese número cuenta, no un martes."),
]


def _donts_glossary() -> list:
    story = [Paragraph("Cosas que no debes hacer", S["h2"])]
    lines = [f'<font color="#d4a017">▌</font> {esc(d)}' for d in DONTS]
    story.append(callout_rows(lines))
    story.append(Spacer(1, 8))
    story += section("Glosario", "Palabras que vas a ver")
    story.append(
        Paragraph(
            "No hace falta memorizarlo. Léelo una vez. Cuando más adelante aparezca TMB, macros o reserva, vuelves aquí.",
            S["body"],
        )
    )
    story.append(data_table(["Término", "Qué significa"], GLOSSARY, [CONTENT_W * 0.33, CONTENT_W * 0.67]))
    story.append(PageBreak())
    return story


def _ficha(user: dict, plan: dict, name: str) -> list:
    sex = "Mujer" if user["sex"] == "female" else "Hombre"
    story = section("Tu ficha", "Así empieza el plan")
    story += [
        Spacer(1, 2),
        stat_cards(
            [
                ("Objetivo", plan["goal_label"]),
                ("Peso inicial", f"{user['weight']:.1f} kg"),
                ("Meta 12 sem.", f"{user['targetWeight']:.1f} kg"),
                ("IMC", f"{user['bmi']:.1f}"),
            ]
        ),
        Spacer(1, 8),
        stat_cards(
            [
                ("Edad", f"{user['age']} años"),
                ("Altura", f"{user['height']} cm"),
                ("Sexo", sex),
                ("Motivación", plan["motivation_label"]),
            ]
        ),
        Spacer(1, 5),
    ]
    stamp = f"Plan generado el {date.today().strftime('%d/%m/%Y')} para {name}"
    if user.get("email"):
        stamp += f" · {esc(user['email'])}"
    story.append(Paragraph(stamp + ". Si un dato está mal, genera el plan de nuevo con los datos correctos.", S["small"]))
    story += pact(
        "Etapa 2",
        f"{name}, estos números no son un veredicto: son el punto de partida de lo que firmaste. "
        "El peso de hoy no te define. El promedio de 12 semanas, sí.",
        name,
    )
    story += section("Ciencia útil", "Por qué fuerza y comida real")
    story.append(
        Paragraph(
            "No es un tratado. Son cuatro reglas que aguantan cuando la moda pasa. El músculo es un órgano que habla "
            "con el resto del cuerpo: glucosa, inflamación, huesos, hambre.",
            S["body"],
        )
    )
    boxes = [
        ("Adherencia", "El plan que no puedes sostener no es un plan. Mejor 80% constante que 100% dos semanas."),
        ("Músculo", "La fuerza no es opcional. El músculo regula glucosa, da forma y sostiene el metabolismo."),
        ("Comida real", "No todas las calorías se sienten igual. Proteína, verdura y comida con matriz, no solo números."),
        ("Flexibilidad", "No hay alimentos malditos. Carbo y grasa son herramientas. El contexto manda."),
    ]
    cw = (CONTENT_W - 6) / 2

    def box(t, x):
        b = Table([[[Paragraph(t, S["boxt"]), Paragraph(x, S["boxx"])]]], colWidths=[cw])
        b.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, GOLD),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return b

    grid = Table(
        [[box(*boxes[0]), "", box(*boxes[1])], [box(*boxes[2]), "", box(*boxes[3])]],
        colWidths=[cw, 6, cw],
    )
    grid.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 0)]))
    story += [grid, Spacer(1, 4), Paragraph("En tu caso", S["h3"])]
    for line in plan["science"]:
        story.append(Paragraph(f"• {esc(line)}", ParagraphStyle("b", parent=S["bodyl"], spaceAfter=3)))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "Tensión mecánica, no sudor. El músculo crece o se conserva cuando tira contra una carga, con rango y "
            "control. Sudar en la cinta no le da esa orden. NEAT: los pasos del día suelen gastar más grasa que la hora "
            "de gym. El entreno dice qué tejido guardar; caminar dice cuánta grasa usar.",
            S["body"],
        )
    )
    story.append(PageBreak())
    return story


def _energy_food(user: dict, plan: dict, name: str) -> list:
    m = plan["macros"]
    kcal = miles(plan["calories"])
    story = section("Energía", "Tu gasto, no un número mágico")
    story.append(Paragraph(esc(plan["energy"]["text"]), S["body"]))
    story.append(Paragraph("De dónde sale tu gasto (estimado)", S["h3"]))
    rows = [[Paragraph(esc(a), S["cellb"]), Paragraph(esc(b), S["cell"])] for a, b in plan["energy"]["rows"]]
    t = Table(rows, colWidths=[CONTENT_W * 0.55, CONTENT_W * 0.45])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("INNERGRID", (0, 0), (-1, -1), 0.6, LINE), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [Spacer(1, 3), t, Spacer(1, 8)]
    story.append(Paragraph("Macros, sin enemigos", S["h3"]))
    story.append(
        Paragraph(
            "Proteína: ladrillos y freno del hambre. Carbohidratos: gasolina del entreno, no el villano. Grasas: "
            "hormonas y vitaminas A, D, E, K. Las vitaminas y minerales no se reemplazan bien con un puñado de "
            "pastillas: viajan mejor en la comida real (hierro + vitamina C; grasas + vitamina D). Magnesio y sueño; "
            "sodio al extremo empeora el gym.",
            S["body"],
        )
    )
    story += section("Alimentación", "Tus números y menús guía")
    img = photo("gff-food.jpg", CONTENT_W, CONTENT_W * 932 / 2860)
    if img:
        story += [img, Spacer(1, 6)]
    story.append(
        stat_cards(
            [
                ("Calorías", f"{kcal} kcal"),
                ("Proteína", f"{m['protein_g']} g"),
                ("Carbos", f"{m['carb_g']} g"),
                ("Grasa", f"{m['fat_g']} g"),
            ]
        )
    )
    story.append(Spacer(1, 12))
    bar_w = CONTENT_W * 0.5
    bars = []
    for label, g, pct, col in [
        ("Proteína", m["protein_g"], m["protein_pct"], GOLD),
        ("Carbohidratos", m["carb_g"], m["carb_pct"], TAN),
        ("Grasa", m["fat_g"], m["fat_pct"], BROWN),
    ]:
        bars.append(
            [
                Paragraph(label, S["cellb"]),
                Bar(pct, col, bar_w),
                Paragraph(f"{g} g<br/>{pct}%", ParagraphStyle("bv", parent=S["small"], alignment=TA_RIGHT)),
            ]
        )
    bt = Table(bars, colWidths=[CONTENT_W * 0.25, bar_w + 10, CONTENT_W * 0.25 - 10], rowHeights=[38] * 3)
    bt.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
    story += [bt, Spacer(1, 8)]
    story.append(
        Paragraph(
            "Cifras de partida. Si el peso no se mueve en 14 días, ajusta 100–150 kcal. Hay 4 menús para rotar. "
            "Las porciones son estimadas, no una receta de laboratorio.",
            S["body"],
        )
    )
    story.append(Paragraph("Aprende a contar tus calorías y macronutrientes", S["h2"]))
    story.append(
        Paragraph(
            f"Tu objetivo diario es de aproximadamente {kcal} kcal, con una referencia de {m['protein_g']} g de "
            f"proteína, {m['carb_g']} g de carbohidratos y {m['fat_g']} g de grasa.",
            S["body"],
        )
    )
    story.append(
        Paragraph(
            "Pero más que darte un número para seguir, queremos que aprendas cómo se obtiene y cómo controlar lo que comes.",
            S["body"],
        )
    )
    steps = [
        ("1. Registra todo lo que consumes", [
            "Durante al menos 7 días, anota tus comidas en una aplicación, hoja de cálculo o libreta.",
            "Incluye todo: comidas principales, snacks, bebidas, salsas, aceites y pequeños “picoteos”. No necesitas hacerlo perfecto; primero necesitas conocer tus hábitos.",
        ]),
        ("2. Aprende a leer las etiquetas", [
            "Busca en la información nutricional: proteínas, carbohidratos y grasas (gramos por porción) y las calorías que aporta esa cantidad.",
            "Presta atención al tamaño de la porción. Si la etiqueta indica los valores para 100 g y tú consumes 150 g, tendrás que multiplicar esos valores por 1,5.",
        ]),
        ("3. Aprende a calcular las calorías de los macros", ["Los macronutrientes aportan aproximadamente:"]),
    ]
    for title, paras in steps:
        story.append(Paragraph(title, S["h3"]))
        for p in paras:
            story.append(Paragraph(p, S["body"]))
    story.append(
        callout_rows(
            [
                "Proteína → 4 kcal por gramo",
                "Carbohidratos → 4 kcal por gramo",
                "Grasas → 9 kcal por gramo",
                "Ejemplo: 30 g de proteína, 40 g de carbohidratos y 10 g de grasa → 30 × 4 = 120 · 40 × 4 = 160 · 10 × 9 = 90. En total, unas 370 kcal.",
            ]
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "Esto te permite entender de dónde vienen las calorías que consumes, en lugar de simplemente confiar en un número.",
            S["body"],
        )
    )
    more = [
        ("4. Al principio, pesa tus alimentos", [
            "Durante las primeras semanas, utiliza una balanza de cocina para familiarizarte con las cantidades.",
            "Lo más sencillo es pesar carnes, pescados, arroz, pasta, cereales y otros alimentos principales en crudo, siempre que la información nutricional que estés utilizando también corresponda al alimento en crudo.",
            "Esto es importante porque 100 g de arroz crudo y 100 g de arroz cocido no tienen los mismos valores nutricionales.",
            "Una vez que conozcas mejor las cantidades, podrás estimar algunas porciones, aunque seguir pesando los alimentos siempre será una opción si quieres mayor precisión.",
        ]),
        ("5. No olvides las calorías pequeñas", [
            "El aceite, frutos secos, mantequilla de maní, salsas, aderezos, bebidas y alcohol pueden aportar muchas calorías aunque parezcan cantidades pequeñas.",
            "Por ejemplo, una cucharada de aceite puede aportar alrededor de 120 kcal. Si quieres un registro preciso, cuenta también aquello que utilizas para preparar o acompañar tus comidas.",
        ]),
        ("6. Compara lo que consumes con tu objetivo", ["Al finalizar el día, compara tus totales con tus objetivos:"]),
    ]
    for title, paras in more:
        story.append(Paragraph(title, S["h3"]))
        for p in paras:
            story.append(Paragraph(p, S["body"]))
    story.append(
        callout_rows(
            [
                f"Objetivo: {kcal} kcal",
                f"Proteína: {m['protein_g']} g",
                f"Carbohidratos: {m['carb_g']} g",
                f"Grasas: {m['fat_g']} g",
            ]
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "No es necesario acertar exactamente cada número todos los días. Lo importante es mantenerte cerca de tus objetivos de manera consistente.",
            S["body"],
        )
    )
    for title, paras in [
        ("7. ¿Y si un día comes de más?", [
            "No pasa nada. Un día por encima de tu objetivo no significa que hayas arruinado tu progreso. No intentes compensarlo dejando de comer o haciendo ejercicio excesivo.",
            "Simplemente vuelve a tu alimentación habitual al día siguiente.",
        ]),
        ("8. Mira la tendencia, no un solo día", [
            "El objetivo es crear hábitos que puedas mantener durante meses, no ganar una batalla de un solo día. Por eso, presta más atención a tu promedio semanal que a lo que ocurrió en una comida concreta.",
        ]),
    ]:
        story.append(Paragraph(title, S["h3"]))
        for p in paras:
            story.append(Paragraph(p, S["body"]))
    story.append(
        callout_rows(
            [
                "Aprender a contar calorías no significa vivir pendiente de una calculadora. Significa entender lo que comes para poder tomar mejores decisiones."
            ]
        )
    )
    story.append(Spacer(1, 10))
    chips = [
        [Paragraph(f"<b>Vegetales</b> {esc(', '.join(user['vegetables']))}", S["cell"]),
         Paragraph(f"<b>Frutas</b> {esc(', '.join(user['fruits']))}", S["cell"])],
        [Paragraph(f"<b>Proteínas</b> {esc(', '.join(user['proteins']))}", S["cell"]),
         Paragraph(f"<b>Carbohidratos</b> {esc(', '.join(user['carbs']))}", S["cell"])],
    ]
    ct = Table(chips, colWidths=[CONTENT_W / 2] * 2)
    ct.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("INNERGRID", (0, 0), (-1, -1), 0.6, LINE), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fbf9f5")), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(KeepTogether([ct] + pact(
        "Etapa 3",
        "El menú no se elige cada mañana. Ya lo elegiste al firmar. Rotas estos cuatro; no improvisas un quinto "
        "porque “hoy no apetece”.",
        name,
    )))
    story.append(PageBreak())
    return story


def _menu_card(menu: dict, width: float) -> Table:
    rows = [[Paragraph(esc(menu["name"]), S["mhead"]), Paragraph(esc(menu["days"]), S["mdays"])]]
    for meal in menu["meals"]:
        rows.append(
            [
                [
                    Paragraph(meal["kind"], S["kicker"]),
                    Paragraph(esc(meal["title"]), S["mtitle"]),
                    Paragraph(esc(meal["detail"]), S["mdet"]),
                ],
                "",
            ]
        )
    t = Table(rows, colWidths=[width * 0.62, width * 0.38])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BLACK),
        ("BOX", (0, 0), (-1, -1), 0.9, GOLD),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
    ]
    for i in range(1, len(rows)):
        style.append(("SPAN", (0, i), (1, i)))
        if i < len(rows) - 1:
            style.append(("LINEBELOW", (0, i), (-1, i), 0.6, LINE))
    t.setStyle(TableStyle(style))
    return t


def _menus(plan: dict) -> list:
    w = (CONTENT_W - 6) / 2
    menus = plan["menus"]
    grid = Table(
        [
            [_menu_card(menus[0], w), "", _menu_card(menus[1], w)],
            ["", "", ""],
            [_menu_card(menus[2], w), "", _menu_card(menus[3], w)],
        ],
        colWidths=[w, 6, w],
        rowHeights=[None, 14, None],
    )
    grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return [Spacer(1, 4), grid, PageBreak()]


def _recipe_card(r: dict, width: float) -> Table:
    inner = [
        Paragraph(esc(r["title"]), S["rtitle"]),
        Paragraph(esc(r["meta"]), S["rmeta"]),
        Paragraph("Ingredientes", S["rsec"]),
    ]
    inner += [Paragraph(f"• {esc(i)}", S["rtxt"]) for i in r["ingredients"]]
    inner.append(Paragraph("Preparación", S["rsec"]))
    inner += [Paragraph(f"{n}. {esc(s)}", S["rtxt"]) for n, s in enumerate(r["steps"], start=1)]
    t = Table([[inner]], colWidths=[width])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, GOLD), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    return t


def _recipes(plan: dict) -> list:
    story = section("Recetario", "Seis platos con lo que elegiste")
    story.append(
        Paragraph(
            "No hace falta ser chef. Seis recetas cortas usando tus proteínas, carbos y verduras. Cambia el orden, "
            "no el tamaño de la porción de golpe.",
            S["body"],
        )
    )
    w = (CONTENT_W - 6) / 2
    recs = plan["recipes"]
    for i in range(0, 6, 2):
        row = Table([[_recipe_card(recs[i], w), "", _recipe_card(recs[i + 1], w)]], colWidths=[w, 6, w])
        row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        story += [row, Spacer(1, 10)]
    story += section("Comer mejor", "Hambre, envase y compra")
    story.append(Paragraph("Hambre, antojo o “me pasé”", S["h2"]))
    for p in [
        "Hambre de verdad: bajó la energía, te diste cuenta a las horas, un plato del plan te calma. Come la comida que tocaba, no un extra “porque ya reventó el día”.",
        "Antojo: aparece después de pantallas, aburrimiento o el primer bocado dulce. Espera 12 minutos, agua o infusión, y si sigue, una fruta de tu lista. No abras el paquete “un poquito”.",
        "Te pasaste: esa noche cierras la cocina. Al día siguiente desayunas el menú normal. No ayunes, no agregues 40 min de cardio, no “castigues” la cena. Un exceso no es un mes. Tres excesos seguidos sí son un patrón: vuelve al planner y marca la comida con honestidad.",
    ]:
        story.append(Paragraph(p, S["body"]))
    story.append(Paragraph("Lista de compra · 7 días", S["h2"]))
    story.append(
        Paragraph(
            "Cantidades para una semana si rotas los 4 menús. Ajusta si comes fuera dos noches. Compra verdura dos "
            "veces si se te pone fea.",
            S["body"],
        )
    )
    story.append(data_table(["Producto", "Cantidad estimada"], plan["shopping"], [CONTENT_W * 0.33, CONTENT_W * 0.67]))
    story.append(PageBreak())
    return story


def _labels() -> list:
    story = [Paragraph("Aprende a leer un envase en 20 segundos", S["h2"])]
    story.append(
        Paragraph(
            "No necesitas ser nutricionista para entender una etiqueta. Con unos pocos datos puedes saber rápidamente "
            "qué estás comprando y cómo encaja en tus objetivos.",
            S["body"],
        )
    )
    items = [
        ("1. Primero, mira el tamaño de la porción", [
            "No asumas que toda la bolsa, botella o envase corresponde a una sola porción. Algunos productos contienen 2, 3 o incluso más porciones.",
            "Ejemplo: si una porción tiene 150 kcal y el envase contiene 2,5 porciones, consumir todo el envase significa aproximadamente 375 kcal.",
        ]),
        ("2. Revisa las calorías y los macronutrientes", [
            "Mira principalmente calorías, proteínas, carbohidratos y grasas. Compáralos con tus objetivos y con la cantidad que realmente vas a consumir.",
        ]),
        ("3. Fíjate en los azúcares, pero ponlos en contexto", [
            "El azúcar forma parte de los carbohidratos. No todos los azúcares tienen el mismo origen: un alimento puede contener azúcares naturalmente presentes, como ocurre en la leche o la fruta, o azúcares añadidos.",
            "Si un producto tiene una cantidad elevada de azúcar añadida, especialmente si es un alimento que esperabas que fuera bajo en azúcar, vale la pena revisar qué estás comprando.",
        ]),
        ("4. Las grasas también cuentan", [
            "Aceites, frutos secos, mantequillas, quesos, aderezos y algunas salsas pueden aumentar rápidamente las calorías de una comida.",
            "Que un producto diga “light” o “reducido en grasa” tampoco significa que sea bajo en calorías. Mira siempre la información nutricional.",
        ]),
        ("5. Lee la lista de ingredientes", [
            "Los ingredientes aparecen de mayor a menor cantidad.",
            "Si entre los primeros ingredientes aparecen azúcar, aceites u otros ingredientes que no esperabas encontrar en grandes cantidades, es una señal para mirar con más atención la información nutricional.",
        ]),
    ]
    for title, paras in items:
        story.append(Paragraph(title, S["h3"]))
        for p in paras:
            story.append(Paragraph(p, S["body"]))
    story += [Spacer(1, 6), Paragraph("La regla de los 20 segundos", S["h3"])]
    story.append(
        callout_rows(
            [
                "Porción → Calorías → Proteína → Carbohidratos → Grasas → Ingredientes.",
                "Con esta pequeña rutina puedes tomar mejores decisiones sin necesidad de memorizar cientos de reglas.",
            ]
        )
    )
    story.append(PageBreak())
    return story


def _day_table(session: dict) -> Table:
    rows = [[Paragraph(esc(session["title"]), S["dayh"]), Paragraph(esc(session["header"]), S["dayhr"]), ""]]
    for r in session["rows"]:
        rows.append(
            [
                [Paragraph(esc(r["name"]), S["exn"]), Paragraph(esc(r["tip"]), S["ext"])],
                Paragraph(esc(r["scheme"]), S["exr"]),
                Paragraph(esc(r["rest"]), S["exr"]),
            ]
        )
    t = Table(rows, colWidths=[CONTENT_W * 0.66, CONTENT_W * 0.17, CONTENT_W * 0.17])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BLACK),
        ("SPAN", (1, 0), (2, 0)),
        ("LINEABOVE", (0, 0), (-1, 0), 1.2, GOLD),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("VALIGN", (0, 1), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    for i in range(1, len(rows) - 1):
        style.append(("LINEBELOW", (0, i), (-1, i), 0.6, LINE))
    t.setStyle(TableStyle(style))
    return t


def _training(user: dict, plan: dict, name: str) -> list:
    tr = plan["training"]
    story = section("Entrenamiento", "Tu rutina de 12 semanas")
    story += pact(
        "Etapa 4",
        "La sesión de hoy es el pacto en movimiento. No se negocia el día 1. Si duele raro, paras. Si solo "
        "“no apetece”, vas igual.",
        name,
    )
    img = photo("gff-gym.jpg", CONTENT_W, CONTENT_W * 932 / 2860)
    if img:
        story += [img, Spacer(1, 6)]
    story += [stat_cards(tr["stats1"]), Spacer(1, 8), stat_cards(tr["stats2"]), Spacer(1, 6)]
    story.append(Paragraph("Bajada de 2-3 s, subida controlada, sin rebotar. Deja 1-2 repeticiones en reserva.", S["bodyl"]))
    story.append(Paragraph(esc(tr["rest_line"]), S["bodyl"]))
    story.append(Paragraph("Por qué tu rutina es así", S["h2"]))
    story.append(Paragraph(esc(tr["why"]), S["body"]))
    story.append(Paragraph("Distribución semanal recomendada", S["h2"]))
    story.append(
        Paragraph(
            "Puedes mover los días. Mantén el orden de las sesiones y no entrenes el mismo grupo al máximo dos días seguidos.",
            S["body"],
        )
    )
    story.append(data_table(["Día", "Sesión"], tr["distribution"], [CONTENT_W * 0.33, CONTENT_W * 0.67]))
    story.append(Paragraph("Peso del día 1", S["h2"]))
    story.append(Paragraph(esc(tr["first_day"]), S["body"]))
    story.append(CondPageBreak(200))
    story.append(Paragraph("Calentamiento", S["h2"]))
    warm = Table([[Paragraph(f"• {esc(w)}", S["bodyl"])] for w in tr["warmup"]], colWidths=[CONTENT_W])
    warm.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    story += [warm, Spacer(1, 6), Paragraph("Progresión de 12 semanas", S["h2"])]
    story.append(
        data_table(
            ["Periodo", "Foco", "Qué hacer"],
            [list(r) for r in tr["progression"]],
            [CONTENT_W * 0.22, CONTENT_W * 0.16, CONTENT_W * 0.62],
        )
    )
    story += [Spacer(1, 4), Paragraph(esc(tr["cooldown"]), S["bodyl"]), Spacer(1, 10)]
    for s in tr["sessions"]:
        story += [KeepTogether([_day_table(s)]), Spacer(1, 12)]
    story += quote(
        "La diferencia entre lo posible y lo imposible está en la determinación de una persona.",
        "Serena Williams · Tenis",
    )
    story.append(PageBreak())
    return story


def _swaps(plan: dict) -> list:
    story = section("Sustituciones", "Si falta un alimento o un ejercicio")
    story.append(
        Paragraph(
            "Cambia una cosa por otra de la misma lista. No sustituyas proteína por pan, ni sentadilla por 40 minutos de bici.",
            S["body"],
        )
    )
    story.append(Paragraph("Alimentos", S["h2"]))
    story.append(data_table(["Eliges", "Puedes usar"], plan["food_swaps"], [CONTENT_W * 0.33, CONTENT_W * 0.67]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Ejercicios", S["h2"]))
    story.append(
        data_table(["Programado", "Alternativa"], plan["training"]["exercise_swaps"], [CONTENT_W * 0.33, CONTENT_W * 0.67])
    )
    story.append(PageBreak())
    return story


# coordenadas relativas de los puntos de medida (x, y desde arriba)
MARKS = {
    "male": {1: (0.495, 0.22), 2: (0.495, 0.33), 3: (0.495, 0.427), 4: (0.495, 0.495), 5: (0.695, 0.356), 6: (0.59, 0.634)},
    "female": {1: (0.496, 0.224), 2: (0.496, 0.338), 3: (0.496, 0.405), 4: (0.496, 0.495), 5: (0.615, 0.351), 6: (0.588, 0.625)},
}
LEGEND = [
    (1, "Cuello — bajo la nuez, cinta horizontal"),
    (2, "Pecho / busto — a la altura de los pezones"),
    (3, "Cintura — ombligo, sin succionar"),
    (4, "Cadera — la parte más ancha"),
    (5, "Brazo — medio hombro-codo, relajado"),
    (6, "Muslo — medio cadera-rodilla"),
]


class BodyMap(Flowable):
    def __init__(self, sex: str, width: float = CONTENT_W + 6):
        super().__init__()
        self.sex = sex
        self.width = width
        self.img_h = 216
        self.img_w = self.img_h * 864 / 1152
        self.height = 12 + self.img_h + 26 + 3 * 21 + 8

    def wrap(self, aw, ah):
        return self.width, self.height

    def _mark(self, x, y, n):
        c = self.canv
        c.setFillColor(GOLD)
        c.circle(x, y, 5.6, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont(FONT_B, 6.4)
        c.drawCentredString(x, y - 2.2, str(n))

    def draw(self):
        c = self.canv
        c.setFillColor(CREAM2)
        c.roundRect(0, 0, self.width, self.height, 5, stroke=0, fill=1)
        top = self.height - 12
        cols = [self.width * 0.25, self.width * 0.75]
        for sex, cx in zip(("male", "female"), cols):
            x0 = cx - self.img_w / 2
            y0 = top - self.img_h
            path = ASSETS / ("gff-body-male.jpg" if sex == "male" else "gff-body-female.jpg")
            if path.is_file():
                c.drawImage(str(path), x0, y0, self.img_w, self.img_h)
            if sex == self.sex:
                c.setStrokeColor(GOLD)
                c.setLineWidth(1.6)
                c.roundRect(x0 - 3, y0 - 3, self.img_w + 6, self.img_h + 6, 3, stroke=1, fill=0)
            for n, (fx, fy) in MARKS[sex].items():
                self._mark(x0 + fx * self.img_w, top - fy * self.img_h, n)
            label = ("Hombre" if sex == "male" else "Mujer") + ("  ·  Tú" if sex == self.sex else "")
            c.setFillColor(INK if sex == self.sex else MUTED)
            c.setFont(FONT_B if sex == self.sex else FONT, 7.6)
            c.drawCentredString(cx, y0 - 17, label)
        y = y0 - 42
        for i, (n, text) in enumerate(LEGEND):
            col = i % 2
            row = i // 2
            x = 18 + col * self.width * 0.5
            yy = y - row * 21
            self._mark(x, yy + 2.5, n)
            c.setFillColor(INK)
            c.setFont(FONT, 7.6)
            c.drawString(x + 11, yy, text)


def _habits_measures(user: dict, plan: dict, name: str) -> list:
    h = plan["habits"]
    story = section("Hábitos", "Lo que sostiene el plan")
    story.append(
        stat_cards(
            [
                ("Agua", f"{h['water_l']} L"),
                ("Sueño", h["sleep"]),
                ("Pasos", h["steps"]),
                ("Báscula", "promedio 3 días"),
            ]
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            f"Agua: unos {miles(h['water_ml'])} ml al día ({h['water_l']} litros), repartidos. Pasos: {esc(h['steps'])}. "
            f"{esc(h['steps_note'])} {esc(h['scale'])}",
            S["body"],
        )
    )
    story += section("Registro", "Siguiendo mis medidas")
    story += pact(
        "Etapa 5",
        "Te mides para no mentirte. La cinta es el testigo del pacto. El espejo miente según la luz. La báscula "
        "miente según el agua. Las cintas no.",
        name,
    )
    story.append(
        Paragraph(
            "Mídete el día anterior a empezar y otra vez a las 12 semanas, a la misma hora, en ropa interior o similar, "
            "cinta flexible, sin apretar hasta marcar piel.",
            S["body"],
        )
    )
    story.append(BodyMap(user["sex"]))
    story.append(PageBreak())

    story.append(Paragraph("Tabla de perímetros (cm)", S["h2"]))
    zones = ["Cuello", "Pecho", "Cintura", "Cadera", "Brazo", "Muslo"]
    story.append(
        data_table(
            ["Zona", "Día 0", "Semana 12", "Cambio"],
            [[z, "", "", ""] for z in zones],
            [CONTENT_W * 0.4, CONTENT_W * 0.2, CONTENT_W * 0.2, CONTENT_W * 0.2],
            row_h=22,
        )
    )
    story.append(Spacer(1, 12))
    story += section("Registro", "El peso: promedio, no un martes")
    story.append(
        Paragraph(
            "Pésate en ayunas, después de ir al baño, 3 mañanas seguidas. Anota el promedio. Repite cada semana (o "
            "cada 15 días si la báscula te obsesiona). No compares un día con el anterior: compara promedios.",
            S["body"],
        )
    )
    story.append(
        data_table(
            ["Semana", "Día 1", "Día 2", "Día 3", "Promedio"],
            [[str(i), "", "", "", ""] for i in range(1, 13)],
            [CONTENT_W * 0.12] + [CONTENT_W * 0.22] * 4,
            first_bold=False,
            row_h=21,
        )
    )
    story.append(PageBreak())

    story += section("Avance", "Fotos, ropa y cuándo mover calorías")
    story.append(Paragraph("Fotos de progreso", S["h2"]))
    story.append(
        Paragraph(
            "Día 0 y día 84 (o cada 4 semanas). Tres tomas: frente, lado, espalda. Misma hora (mañana), misma luz "
            "(ventana, no flash del baño), misma pose, misma ropa interior o tight. Celular a la altura del ombligo, no "
            "desde arriba. No las compares a diario: el hinchazón miente.",
            S["body"],
        )
    )
    story.append(
        data_table(
            ["Toma", "Día 0 (sí/fecha)", "Semana 4", "Semana 8", "Semana 12"],
            [[t, "", "", "", ""] for t in ("Frente", "Lado", "Espalda")],
            [CONTENT_W * 0.2] * 5,
            row_h=21,
        )
    )
    story.append(Spacer(1, 6))
    story.append(Paragraph("Ropa testigo", S["h2"]))
    story.append(
        Paragraph(
            "Elige un pantalón o una polera que hoy te quede justa. No la uses de diario. Pruébatela el día 0 y el día "
            "84 (y si quieres a las 6 semanas). La cintura y el muslo suelen hablar antes que el número de la báscula. "
            "Anota: holgado / igual / más justo.",
            S["body"],
        )
    )
    story.append(
        data_table(
            ["Prenda", "Día 0", "Semana 6", "Semana 12"],
            [["Pantalón", "", "", ""], ["Polera / top", "", "", ""]],
            [CONTENT_W * 0.34, CONTENT_W * 0.22, CONTENT_W * 0.22, CONTENT_W * 0.22],
            row_h=21,
        )
    )
    story.append(Spacer(1, 6))
    story.append(Paragraph("“Esta semana no bajé” no significa fracaso", S["h2"]))
    story.append(
        Paragraph(
            "El peso sube 0,5–1,5 kg por agua si comiste más sal, entrenaste pesado (los músculos retienen), dormiste "
            "mal o estás en esos días del ciclo. Eso no es grasa ganada en 48 horas. Mira el promedio de 3 días de esta "
            "semana contra el de hace 14 días, las cintas y la ropa. Si todo eso está igual o peor 14 días seguidos, "
            "entonces sí: se ajusta. Antes, no toques el plan.",
            S["body"],
        )
    )
    story.append(Paragraph("Cuándo mover 100–150 kcal", S["h2"]))
    story.append(Paragraph("Espera 14 días de promedio de peso + cintura. Un martes no cuenta.", S["body"]))
    story.append(
        data_table(
            ["Qué ves", "Qué haces"],
            [
                ("El promedio bajó o la cinta aflojó", "No cambies calorías. Sigue. El plan está trabajando."),
                ("El promedio no se movió en 14 días (objetivo bajar)", "Resta 100–150 kcal/día. Recorta un poco de carb o aceite, no la proteína."),
                ("Bajaste de más, te sientes destrozado o el gym se cayó", "Suma 100–150 kcal. Mejor un descenso lento que abandonar."),
                ("Objetivo ganar y no subió nada en 14 días", "Suma 100–150 kcal, sobre todo en la comida post entreno."),
                ("Hambre feroz todas las noches", "Revisa sueño y proteína antes de cortar más. Casi nunca es “falta de voluntad”."),
            ],
            [CONTENT_W * 0.38, CONTENT_W * 0.62],
        )
    )
    story.append(PageBreak())
    return story


PLANNER_W = [CONTENT_W * f for f in (0.08, 0.18, 0.18, 0.24, 0.12, 0.20)]
DAYS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def week_table(n: int) -> Table:
    blank = "________"
    head = Paragraph(f"Semana {n} · del {blank} / {blank} al {blank} / {blank}", S["week"])
    rows = [[head, "", "", "", "", ""]]
    rows.append([Paragraph(h, S["cellh"]) for h in ("Día", "Entreno", "Comida", "Agua (8 vasos)", "Ánimo", "Notas")])
    for d in DAYS:
        rows.append([Paragraph(d, S["cellb"]), Check(["sí", "no"]), Check(["sí", "no"]), Water(), "", ""])
    t = Table(rows, colWidths=PLANNER_W, rowHeights=[22, 18] + [26.5] * 7)
    t.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (-1, 0)),
                ("BACKGROUND", (0, 0), (-1, 0), CREAM2),
                ("BACKGROUND", (0, 1), (-1, 1), BLACK),
                ("BOX", (0, 0), (-1, -1), 0.9, GOLD),
                ("INNERGRID", (0, 2), (-1, -1), 0.6, LINE),
                ("LINEBELOW", (0, 2), (-1, -2), 0.6, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def notes_box() -> Table:
    rows = [[Paragraph("Notas de estas semanas (sueño, dolor, hambre, ánimo)", S["cellb"])]] + [[""] for _ in range(4)]
    t = Table(rows, colWidths=[CONTENT_W], rowHeights=[22] + [23] * 4)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CREAM2),
                ("BOX", (0, 0), (-1, -1), 0.9, GOLD),
                ("LINEBELOW", (0, 1), (-1, -1), 0.5, colors.HexColor("#ddd5c5")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return t


def control_box(text: str, name: str, week: int) -> list:
    checks = Table(
        [[Check(["Entrené ≥ 80% de las sesiones"]), Check(["Comí cerca del número"]), Check(["Me pesé en promedio"])]],
        colWidths=[CONTENT_W / 3] * 3,
        rowHeights=[22],
    )
    checks.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CREAM2), ("BOX", (0, 0), (-1, -1), 0.9, GOLD), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
    return [
        Spacer(1, 8),
        dark_box(f"El pacto · Control semana {week}", text, f"— {name} · Lo firmaste."),
        Spacer(1, 8),
        checks,
        Spacer(1, 8),
    ]


def _planner(name: str) -> list:
    story = section("Bitácora", "Planner de 12 semanas")
    story.append(
        Paragraph(
            "Cada semana anota si entrenaste, cómo te sentiste y una nota corta (sueño, comida, ánimo, dolor). No hace "
            "falta un diario. Hace falta no mentirte.",
            S["body"],
        )
    )
    gap = Spacer(1, 10)
    story += [week_table(1), PageBreak()]
    story += [week_table(2), gap, week_table(3), gap, notes_box(), PageBreak()]
    story += [week_table(4)]
    story += control_box(
        f"{name}, cuatro semanas. No se mide el ánimo de un martes: se mira el planner. Si está marcado, el pacto sigue en pie.",
        name,
        4,
    )
    story += [week_table(5), gap, notes_box(), PageBreak()]
    story += [week_table(6), gap, week_table(7), gap, notes_box(), PageBreak()]
    story += [week_table(8)]
    story += control_box(
        f"{name}, semana 8. El pacto no se renegocia a mitad. Doce semanas no se sienten largas cuando dejas de contar "
        "los días y empiezas a marcarlos.",
        name,
        8,
    )
    story += [week_table(9), gap, notes_box(), PageBreak()]
    story += [week_table(10), gap, week_table(11), gap, notes_box(), PageBreak()]
    story += [week_table(12), Spacer(1, 12)]
    return story


def _closing(user: dict, plan: dict, name: str) -> list:
    m = plan["macros"]
    story = section("Cierre", "Esto se imprime y se usa")
    story += pact(
        "Etapa 6",
        f"{name}, lo firmaste. Doce semanas. El plan no falla: se cumple o se abandona. Si a las 12 semanas el "
        "planner está lleno, el trabajo ya está hecho.",
        name,
    )
    story.append(
        Paragraph(
            "No es un archivo para guardar en el celular y olvidar. Imprímelo o tenlo a mano. El planner se llena cada "
            "semana, con honestidad.",
            S["body"],
        )
    )
    story.append(
        stat_cards(
            [
                ("Calorías", f"{miles(plan['calories'])} kcal"),
                ("Proteína", f"{m['protein_g']} g"),
                ("Entreno", f"{user['days']} días · {user['duration']} min"),
                ("Meta", f"{user['targetWeight']:.1f} kg"),
            ]
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "Cada domingo (o el día que elijas) marca entreno, comida y agua. El peso se mira en promedio de 3 días, no "
            "un martes. Si un dato del formulario está mal, genera el plan de nuevo con los datos correctos.",
            S["body"],
        )
    )
    story.append(callout_rows(["Lo firmaste. El mismo pacto del día 1 es el del día 84."]))
    story.append(Spacer(1, 10))
    story.append(
        cream_box(
            [
                Paragraph(
                    "<b>Importante.</b> Este documento es una guía general y no sustituye la evaluación de un médico, "
                    "nutricionista o profesional del ejercicio. Si tienes una condición médica, lesión, embarazo, "
                    "trastorno alimentario o tomas medicamentos, consulta a un profesional antes de realizar cambios "
                    "importantes en alimentación o ejercicio.",
                    S["small"],
                )
            ],
            border=LINE,
        )
    )
    return story


# ---------------------------------------------------------------- entrada


def build_pdf(path: Path, user: dict, plan: dict | None = None, payment_ref: str = "") -> Path:
    """Genera el PDF. `plan` y `payment_ref` se aceptan por compatibilidad y se ignoran."""
    global S
    S = _styles()
    full = build_full_plan(user)
    name = esc(user["name"])
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=48,
        bottomMargin=50,
        title=f"GaryFelicienFit — {user['name']}",
        author="Gary Felicien",
    )
    doc.gff_user = user
    doc.gff_plan = full
    story: list = [Spacer(1, 1), PageBreak()]
    story += _intro(user, name)
    story += _donts_glossary()
    story += _ficha(user, full, name)
    story += _energy_food(user, full, name)
    story += _menus(full)
    story += _recipes(full)
    story += _labels()
    story += _training(user, full, name)
    story += _swaps(full)
    story += _habits_measures(user, full, name)
    story += _planner(name)
    story += _closing(user, full, name)
    doc.build(story, onFirstPage=_cover, onLaterPages=_frame)
    return path
