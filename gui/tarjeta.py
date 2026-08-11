# SPDX-FileCopyrightText: 2026 Eugenio Nerelli <kira_and_light@hotmail.it>
# SPDX-License-Identifier: Apache-2.0
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
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

sys.path.insert(0, str(Path(__file__).resolve().parent))
from firma import firma_corrida                                    # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TIPO = ROOT / "gui" / "tipos" / "Archivo.ttf"
W, H = 1200, 630

PAPEL = (255, 255, 255)
TINTA = (20, 22, 26)
TINTA3 = (96, 104, 116)
LINEA = (223, 227, 232)
RECHAZO = (179, 18, 47)
SUP2 = (247, 248, 250)


def firma(p_gana, generado):
    """Lo que identifica una corrida: su fecha, su hash y las cinco primeras.

    El hash viene de gui/firma.py y es el mismo que va en web/datos.json y en
    la etiqueta de git. Las cinco primeras van ademas en claro porque asi la
    tarjeta se puede leer sin herramientas: quien abra el PNG con cualquier
    lector de metadatos ve de que corrida es.
    """
    orden = sorted(p_gana, key=lambda n: -p_gana[n])[:5]
    return (generado + "|" + firma_corrida() + "|" +
            "|".join(f"{n}:{p_gana[n]:.4f}" for n in orden))


def fuente(px, peso=400):
    """Archivo es variable y sus ejes van en este orden: peso, ancho.

    Al reves no falla: fija el peso en 100 -y sale todo en Thin- y el ancho en
    700, que se sale del eje y se recorta al maximo. La tarjeta quedaba fina y
    ancha sin que nada avisara.
    """
    f = ImageFont.truetype(str(TIPO), px)
    f.set_variation_by_axes([peso, 100])
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

    d.text((64, 138), "¿Quién gana los 70 millones?", font=fuente(58, 700),
           fill=TINTA)

    # las cinco primeras, con su barra. La escala es relativa a la primera y no
    # al 100%: con nueve en juego nadie pasa del 25% y una barra sobre 100 seria
    # una fila de muñones que no dejaria ver la unica diferencia que importa,
    # que es la de arriba.
    y, paso = 236, 56
    x0, x1 = 330, 990
    top = base[orden[0]]
    for n in orden[:5]:
        p = base[n]
        primera = n == orden[0]
        d.text((64, y), n, font=fuente(30, 700 if primera else 500),
               fill=TINTA if primera else TINTA3)
        d.rounded_rectangle([x0, y + 8, x1, y + 30], 7, fill=SUP2)
        ancho = int((x1 - x0) * p / top)
        if ancho > 14:
            d.rounded_rectangle([x0, y + 8, x0 + ancho, y + 30], 7,
                                fill=TINTA if primera else (156, 164, 176))
        d.text((W - 64, y), f"{100*p:.1f}".replace(".", ",") + "%",
               font=fuente(30, 700), anchor="ra",
               fill=TINTA if primera else TINTA3)
        y += paso

    d.line([64, H - 86, W - 64, H - 86], fill=LINEA, width=2)
    d.text((64, H - 62), "nerln.github.io/placa", font=fuente(26, 700), fill=TINTA)
    d.text((W - 64, H - 62), "Eugenio Nerelli", font=fuente(26, 400), fill=TINTA3,
           anchor="ra")

    # La firma de la corrida viaja dentro del PNG, en un trozo de texto. Es para
    # que gui/verificar.py pueda decir "esta tarjeta se dibujo con estos
    # numeros" sin tener que redibujarla ni comparar pixeles, que dependen de la
    # version de la libreria. Sirve contra el unico fallo silencioso que tiene
    # esto: reconstruir la pagina y olvidarse de la tarjeta, y que el enlace
    # compartido siga cantando el pronostico de la semana pasada.
    meta = PngImagePlugin.PngInfo()
    meta.add_text("corrida", firma(base, res["generado"]))

    salida = ROOT / "web" / "og.png"
    salida.parent.mkdir(exist_ok=True)
    img.save(salida, "PNG", optimize=True, pnginfo=meta)
    kb = salida.stat().st_size / 1024
    print(f"escrito web/og.png ({kb:.0f} KB) · {orden[0]} {100*base[orden[0]]:.1f}%")


if __name__ == "__main__":
    main()
