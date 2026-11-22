import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ASSETS = Path(__file__).resolve().parent.parent / "assets"
LADO = 1024
FONDO = (10, 10, 10, 255)
BORDE = (51, 51, 51, 255)
MARGEN = 0.20


def leer_svg(ruta: Path):
    svg = ruta.read_text(encoding="utf-8")
    vb = [float(x) for x in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    d = re.search(r' d="([^"]+)"', svg).group(1)
    poligonos, actual = [], []
    for tok in re.findall(r"[MLZ]|-?\d+(?:\.\d+)?", d):
        if tok == "M":
            actual = []
        elif tok == "Z":
            poligonos.append(actual)
        elif tok != "L":
            actual.append(float(tok))
    return vb, poligonos


def main():
    (x0, y0, w, h), poligonos = leer_svg(ASSETS / "logo_zx.svg")
    util = LADO * (1 - 2 * MARGEN)
    escala = util / max(w, h)
    dx = (LADO - w * escala) / 2 - x0 * escala
    dy = (LADO - h * escala) / 2 - y0 * escala

    mascara = Image.new("1", (LADO, LADO), 0)
    for pol in poligonos:
        capa = Image.new("1", (LADO, LADO), 0)
        pts = [(pol[i] * escala + dx, pol[i + 1] * escala + dy) for i in range(0, len(pol), 2)]
        ImageDraw.Draw(capa).polygon(pts, fill=1)
        mascara = ImageChops.logical_xor(mascara, capa)

    img = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
    dib = ImageDraw.Draw(img)
    dib.rounded_rectangle([0, 0, LADO - 1, LADO - 1], radius=int(LADO * 0.22), fill=FONDO,
                          outline=BORDE, width=int(LADO * 0.012))
    img.paste((255, 255, 255, 255), mask=mascara)

    img.resize((256, 256), Image.LANCZOS).save(ASSETS / "icono.png")
    img.save(ASSETS / "icono.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("OK:", ASSETS / "icono.ico")


if __name__ == "__main__":
    main()
