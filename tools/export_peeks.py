"""Crop teaser fragments from the sample PDF for the landing."""
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "data" / "pdfs" / "preview-gff-12.pdf"
OUT = ROOT / "web" / "img"

# page index (0-based), crop box as fractions of width/height
PEEKS = [
    ("peek-menus.jpg", 7, (0.045, 0.065, 0.955, 0.60)),
    ("peek-rutina.jpg", 12, (0.045, 0.255, 0.955, 0.72)),
    ("peek-medidas.jpg", 14, (0.04, 0.47, 0.96, 0.935)),
    ("peek-planner.jpg", 17, (0.04, 0.055, 0.96, 0.545)),
]


def crop_frac(im: Image.Image, box: tuple[float, float, float, float]) -> Image.Image:
    w, h = im.size
    l, t, r, b = box
    return im.crop((int(l * w), int(t * h), int(r * w), int(b * h)))


def gold_frame(im: Image.Image) -> Image.Image:
    framed = Image.new("RGB", (im.width + 8, im.height + 8), (212, 160, 23))
    inner = Image.new("RGB", (im.width + 4, im.height + 4), (11, 12, 15))
    framed.paste(inner, (2, 2))
    framed.paste(im, (4, 4))
    return framed


def main() -> None:
    doc = pdfium.PdfDocument(str(PDF))
    for name, page_i, box in PEEKS:
        page = doc[page_i]
        bitmap = page.render(scale=2.0)
        im = bitmap.to_pil().convert("RGB")
        cut = crop_frac(im, box)
        gold_frame(cut).save(OUT / name, "JPEG", quality=90)
        print(name, cut.size)
    doc.close()


if __name__ == "__main__":
    main()
