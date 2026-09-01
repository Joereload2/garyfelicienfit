"""Marketing cover JPEG for the landing mockup."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "web" / "img" / "gary-lift.jpg"
OUT = ROOT / "web" / "img" / "guia-cover.jpg"
W, H = 1240, 1754


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(str(Path(r"C:\Windows\Fonts") / name), size)


def main() -> None:
    img = Image.open(SRC).convert("RGB")
    iw, ih = img.size
    scale = max(W / iw, H / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    top = max(0, (nh - H) // 2 - 80)
    img = img.crop((left, top, left + W, top + H))
    img = ImageEnhance.Color(img).enhance(0.88)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rectangle([0, 0, W, H], fill=(15, 26, 61, 95))
    band_h = int(H * 138 / 297)
    d.rectangle([0, 0, W, band_h], fill=(15, 28, 64, 235))
    d.rectangle([0, band_h, W, band_h + 9], fill=(212, 160, 23, 255))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    m = 84
    draw.text((m, 72), "GARY FELICIEN FIT", font=font(28, True), fill=(255, 255, 255))
    draw.text((W - m, 72), "Guía 12 semanas", font=font(22), fill=(201, 191, 168), anchor="ra")
    y = band_h - 200
    draw.text((m, y), "PLAN PERSONALIZADO  ·  12 SEMANAS", font=font(22, True), fill=(240, 199, 94))
    draw.text((m, y + 52), "Tu plan", font=font(72, True), fill=(255, 255, 255))
    draw.text((m, y + 142), "Nutrición y entrenamiento", font=font(34), fill=(243, 237, 226))
    draw.text((m, y + 188), "hecho a tu medida", font=font(34), fill=(243, 237, 226))
    draw.text((m, H - 90), "4 menús  ·  recetario  ·  rutina  ·  planner", font=font(24), fill=(201, 191, 168))
    img.save(OUT, "JPEG", quality=92)
    print(OUT)


if __name__ == "__main__":
    main()
