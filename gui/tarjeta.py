"""
La tarjeta de previsualizacion: lo que se ve cuando alguien comparte el enlace.

Es la ventaja mas visible de publicar en un dominio propio en vez de en un
artefacto: un enlace pegado en X o en WhatsApp puede mostrar los numeros del
pronostico en la propia tarjeta, sin que nadie abra la pagina.

Se dibuja con los datos de la corrida, asi que despues de cada gala la tarjeta
cambia sola. 1200x630, que es lo que piden Open Graph y las tarjetas de X.

    python3 gui/tarjeta.py       ->  web/og.png
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
TIPO = ROOT / "gui" / "tipos" / "Archivo.ttf"
W, H = 1200, 630

PAPEL = (255, 255, 255)
TINTA = (20, 22, 26)
TINTA3 = (96, 104, 116)
LINEA = (223, 227, 232)
RECHAZO = (179, 18, 47)
SUP2 = (247, 248, 250)


def fuente(px, peso=400):
    f = ImageFont.truetype(str(TIPO), px)
    try:                                  # Archivo viene como variable
        f.set_variation_by_axes([100, peso])
    except Exception:
        pass
    return f


def main():
    res = json.loads((ROOT / "data" / "resultados.json").read_text())
    galas = json.loads((ROOT / "data" / "galas.json").read_text())
    base = res["escenarios"]["base"]["p_gana"]
    orden = sorted(base, key=lambda n: -base[n])

    img = Image.new("RGB", (W, H), PAPEL)
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, W, 8], fill=TINTA)
    d.text((64, 56), "GRAN HERMANO · GENERACIÓN DORADA", font=fuente(24, 700),
           fill=RECHAZO)

    ultima = max(g["fecha"] for g in galas["galas"])
    dd, mm = ultima.split("-")[2], ultima.split("-")[1]
    MES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
           "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    d.text((64, 94), f"Pronóstico tras la gala del {int(dd)} de {MES[int(mm)-1]}",
           font=fuente(30, 400), fill=TINTA3)

    d.text((64, 150), "¿Quién se lleva", font=fuente(64, 700), fill=TINTA)
    d.text((64, 218), "los 70 millones?", font=fuente(64, 700), fill=TINTA)

    # las cinco primeras, con su barra
    y = 320
    top = base[orden[0]]
    for n in orden[:5]:
        p = base[n]
        d.text((64, y), n, font=fuente(30, 700), fill=TINTA)
        x0, x1 = 330, 1000
        d.rounded_rectangle([x0, y + 6, x1, y + 26], 6, fill=SUP2)
        ancho = int((x1 - x0) * p / top)
        if ancho > 12:
            d.rounded_rectangle([x0, y + 6, x0 + ancho, y + 26], 6,
                                fill=TINTA if n == orden[0] else (150, 158, 170))
        txt = f"{100*p:.1f}".replace(".", ",") + "%"
        d.text((1020, y), txt, font=fuente(30, 700),
               fill=TINTA if n == orden[0] else TINTA3)
        y += 52

    d.line([64, H - 92, W - 64, H - 92], fill=LINEA, width=2)
    d.text((64, H - 68), "nerln.github.io/placa", font=fuente(26, 700), fill=TINTA)
    d.text((W - 64, H - 68), "Eugenio Nerelli", font=fuente(26, 400), fill=TINTA3,
           anchor="ra")

    salida = ROOT / "web" / "og.png"
    salida.parent.mkdir(exist_ok=True)
    img.save(salida, "PNG", optimize=True)
    kb = salida.stat().st_size / 1024
    print(f"escrito web/og.png ({kb:.0f} KB) · {orden[0]} {100*base[orden[0]]:.1f}%")


if __name__ == "__main__":
    main()
