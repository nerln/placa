# SPDX-FileCopyrightText: 2026 Eugenio Nerelli <kira_and_light@hotmail.it>
# SPDX-License-Identifier: Apache-2.0
"""
La marca de la pagina: un ojo hecho con el pronostico.

POR QUE NO ES EL OJO DE GRAN HERMANO. Hubo una version anterior de este archivo
que redibujaba el logotipo oficial midiendolo: la almendra de dos arcos, los dos
parpados en simetria rotacional con la punta enroscada, el iris de oro fundido.
Salia parecidisimo, y ese era exactamente el problema. El ojo de Gran Hermano es
una marca registrada de sus titulares; una copia fiel usada como identidad de un
sitio no es cita ni comentario, es usar la marca de otro para identificar algo
propio. Esta pagina habla del programa, no es del programa, y la diferencia
tiene que verse.

QUE ES ESTE. Un ojo cuyo iris es el pronostico: un anillo partido en tantos
arcos como personas quedan en juego, cada uno del tamano de su probabilidad de
ganar, del mas probable al menos. El parpado es un trazo fino, no una medialuna
maciza. No hay remolino, ni puntas enroscadas, ni oro fundido en tres
dimensiones. De lejos es un ojo; de cerca es el grafico de la pagina.

Y cambia solo: despues de cada gala el iris se redibuja con los numeros nuevos,
que es algo que un logotipo no puede hacer y esta marca si.

    python3 gui/marca.py        imprime el SVG con los datos de ahora
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

W, H = 120.0, 78.0
CX, CY = W / 2, H / 2
A, B = W / 2 - 1.6, H / 2 - 1.6          # la almendra, con sitio para el trazo
R_FUERA, R_DENTRO = 25.5, 15.0           # el anillo del iris
HUECO = 3.0                              # grados entre arco y arco

# Los colores NO se escriben aca. La marca los toma de la pagina con
# var(--oro-*), que es lo que hace que de dia sea ambar oscuro sobre papel y de
# noche oro claro sobre azul, sin dos versiones del dibujo. Los valores que van
# detras de cada var() son solo el respaldo para cuando el SVG se sirve suelto
# -el favicon, por ejemplo- y ahi no hay pagina de la que heredar.
ORO_VIVO = "var(--oro-1,#F0CE6E)"
ORO = "var(--oro-2,#C2A550)"
ORO_APAGADO = "var(--oro-3,#7A6430)"
BORDE = "var(--oro-2,#C2A550)"
TINTA = "#0B0C0C"


def _almendra():
    """Dos arcos de circunferencia que se cortan en punta. Es la lente clasica
    y no es de nadie; lo que si es de alguien es el logotipo entero."""
    k = (B * B - A * A) / (2 * B)
    r = B - k
    return (f"M{CX-A:.2f} {CY:.2f}"
            f"A{r:.2f} {r:.2f} 0 0 1 {CX+A:.2f} {CY:.2f}"
            f"A{r:.2f} {r:.2f} 0 0 1 {CX-A:.2f} {CY:.2f}Z")


def _arco(g0, g1):
    """Un sector del anillo, entre dos angulos en grados (0 = arriba)."""
    def p(g, r):
        a = math.radians(g - 90)
        return CX + r * math.cos(a), CY + r * math.sin(a)
    x0, y0 = p(g0, R_FUERA); x1, y1 = p(g1, R_FUERA)
    x2, y2 = p(g1, R_DENTRO); x3, y3 = p(g0, R_DENTRO)
    largo = 1 if (g1 - g0) > 180 else 0
    return (f"M{x0:.2f} {y0:.2f}A{R_FUERA} {R_FUERA} 0 {largo} 1 {x1:.2f} {y1:.2f}"
            f"L{x2:.2f} {y2:.2f}A{R_DENTRO} {R_DENTRO} 0 {largo} 0 {x3:.2f} {y3:.2f}Z")


def iris(p_gana, animar=True):
    """Los arcos del iris, del mas probable al menos, empezando arriba.

    Cada arco sale con su propio retraso, de mayor a menor, asi que al cargar la
    pagina el iris se arma contando: primero la favorita, despues las que la
    siguen. No es adorno, es el mismo orden que dice la tabla de mas abajo. El
    CSS de la pagina apaga la animacion entera si el sistema pide menos
    movimiento.
    """
    orden = sorted(p_gana, key=lambda n: -p_gana[n])
    total = sum(p_gana.values()) or 1
    fuera = []
    g = 0.0
    for i, n in enumerate(orden):
        ancho = 360 * p_gana[n] / total
        if ancho <= HUECO:                       # un arco mas fino que su hueco
            g += ancho                           # no se dibuja: seria una raya
            continue
        color = ORO_VIVO if i == 0 else (ORO if i < 3 else ORO_APAGADO)
        retraso = f' style="--i:{i}"' if animar else ""
        # Cada arco dice de quien es al pasarle por encima, y los lectores de
        # pantalla lo leen. Un grafico que no se puede interrogar es un adorno.
        pct = f"{100 * p_gana[n]:.1f}".replace(".", ",")
        fuera.append(f'<path class="ojo-arco" fill="{color}"{retraso} '
                     f'd="{_arco(g, g + ancho - HUECO)}">'
                     f'<title>{n}: {pct}%</title></path>')
        g += ancho
    return "\n    ".join(fuera), orden


def svg(p_gana, fondo=True, animar=False):
    """El SVG de la marca.

    fondo=True  -> version suelta (favicon): trae su propio fondo y sus colores
                   de respaldo, porque no hay pagina de la que heredar.
    animar=True -> version de la pagina: clases para que el CSS la dibuje al
                   entrar. Sin fondo: hereda el de la cabecera.
    """
    arcos, orden = iris(p_gana, animar)
    n = arcos.count("<path")
    fondo_svg = f'<rect width="{W:.0f}" height="{H:.0f}" fill="{TINTA}"/>\n  ' if fondo else ""
    cls = ' class="ojo"' if animar else ""
    return (f'<svg{cls} viewBox="0 0 {W:.0f} {H:.0f}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-label="Un ojo cuyo iris reparte el pronóstico entre las {n} con más probabilidad de ganar">\n  '
            f'{fondo_svg}'
            f'<path class="ojo-parpado" d="{_almendra()}" fill="none" stroke="{BORDE}" '
            f'stroke-width="2.6"/>\n  '
            f'<g class="ojo-iris">\n    {arcos}\n  </g>\n'
            f'</svg>')


def main():
    res = json.loads((ROOT / "data" / "resultados.json").read_text())
    print(svg(res["escenarios"]["base"]["p_gana"]))


if __name__ == "__main__":
    main()
