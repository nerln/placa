# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
EL ARCHIVO: el pronostico de cada gala, congelado antes de que se juegue.

Una prediccion que no quedo escrita antes no se puede puntuar despues. El
registro (data/historial_pronostico.json) ya guarda los numeros, pero un numero
suelto en un JSON no es lo que un lector puede auditar: lo que se audita es la
PAGINA tal como se publico, con su fecha, antes del resultado.

POR QUE SE COPIA gui/pronostico.html Y NO web/index.html. Parece el mismo
archivo y no lo es. `web/index.html` carga los datos aparte, con
`src="datos.js?v=<corrida>"`, y `datos.js` se sobrescribe despues de cada gala:
una copia de index.html se reescribiria sola el martes siguiente y el "archivo"
mostraria los numeros de la semana que viene con la fecha de esta. Es el peor
fallo posible en un archivo, porque no se ve. `gui/pronostico.html` lleva los
datos adentro (`const D = {...}`), sin un solo <script src> ni hoja de estilo
externa: copiarlo congela de verdad.

POR QUE web/galas/ NO ROMPE LA CI. `gui/verificar.py::reconstruible()` rehace
la pagina y la compara byte a byte, pero recorre `WEB.glob("*")` filtrando por
sufijo `.html/.json/.js`: un directorio tiene sufijo vacio, asi que no entra.
Y `gui/mirar/comprobar.mjs` solo mira `web/index.html`. El archivo convive con
las dos puertas sin tocarlas, y eso es a proposito: el dia que una comprobacion
empiece a rehacer los archivos, los archivos dejan de ser archivos.

    python3 gui/archivar.py            archiva la gala vigente si falta
    python3 gui/archivar.py --forzar   la reescribe aunque ya exista
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
GALAS = WEB / "galas"
REPO = "https://github.com/nerln/placa"
ART = dt.timezone(dt.timedelta(hours=-3))
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre")


def fecha_larga(iso):
    """«2026-08-24» → «24 de agosto de 2026». Una fecha ISO en la cara del
    lector es una fecha que no se leyo."""
    if not iso:
        return "la gala"
    try:
        d = dt.date.fromisoformat(str(iso)[:10])
    except ValueError:
        return str(iso)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def _leer(n):
    return json.loads((ROOT / "data" / n).read_text())


def _sello(gala, fecha_gala, cuando, llamadas):
    """La cinta que se le pega arriba a la copia archivada.

    Dice tres cosas y ninguna es opinion: que esto no se actualiza, cuando se
    congelo, y donde mirar la prueba. El enlace va al historial del archivo en
    GitHub y no a un hash: el hash no existe todavia cuando se escribe esto, y
    el historial lo puede leer cualquiera sin creerle a nadie.
    """
    tres = "".join(
        f"<span><b>{q}</b> {n}</span>" for q, n in llamadas)
    return f"""<div id="archivo-sello" role="note">
  <div class="as-i">
    <div class="as-t">Archivo · gala {gala}</div>
    <p class="as-p">Ésta es la página tal como se publicó el <b>{cuando}</b>, antes de la gala
    del {fecha_gala}. <b>No se actualiza:</b> los números son los que estaban escritos antes de
    que se supiera el resultado.</p>
    <div class="as-tres">{tres}</div>
    <p class="as-p"><a href="{REPO}/commits/main/web/galas/{gala}.html">Cuándo se subió este
    archivo, en GitHub</a> · <a href="../">el pronóstico de ahora</a></p>
  </div>
</div>
<style>
#archivo-sello{{position:sticky; top:0; z-index:99; background:#0F2B4D; color:#fff;
  border-bottom:2px solid #E8C463; font-family:system-ui,-apple-system,sans-serif}}
#archivo-sello .as-i{{max-width:52rem; margin-inline:auto; padding:12px 16px}}
#archivo-sello .as-t{{font-size:11px; font-weight:800; letter-spacing:.1em;
  text-transform:uppercase; color:#E8C463}}
#archivo-sello .as-p{{font-size:13px; line-height:1.5; margin:5px 0 0; color:#D8E4F0}}
#archivo-sello .as-tres{{display:flex; flex-wrap:wrap; gap:6px; margin:8px 0 0}}
#archivo-sello .as-tres span{{font-size:12px; padding:3px 8px; border-radius:6px;
  border:1px solid #2A4A6E; color:#C8D8E8}}
#archivo-sello .as-tres b{{color:#fff}}
#archivo-sello a{{color:#F0CE6E}}
@media print{{#archivo-sello{{position:static}}}}
</style>
"""


def destino_existe(gala):
    return (GALAS / f"{gala}.html").exists()


def main():
    ap = argparse.ArgumentParser(description="Archiva el pronóstico congelado de la gala vigente")
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--gala", type=int)
    a = ap.parse_args()

    act = _leer("actualidad.json")
    prox = act.get("proxima_gala") or {}
    gala = a.gala or prox.get("gala")
    fecha_gala = prox.get("fecha")
    if not gala:
        print("no hay gala vigente que archivar")
        return 0

    # Volver a archivar DESPUES de la gala convertiria el archivo en algo que se
    # puede acomodar al resultado, que es justo lo contrario de para que existe.
    # Antes de la gala, en cambio, rehacerlo es legitimo: las predicciones ya
    # estan congeladas en el registro con su fecha y no cambian por volver a
    # dibujar la pagina. Por eso el limite no es «una sola vez» sino «hasta que
    # se juegue», y por eso es una comprobacion y no una recomendacion.
    jugada = any(g.get("gala") == gala and g.get("eliminado")
                 for g in (_leer("galas.json").get("galas") or []))
    if jugada and destino_existe(gala):
        print(f"la gala {gala} ya se jugó y ya está archivada: NO se reescribe. "
              "Un archivo que se puede rehacer con el resultado a la vista no prueba nada.")
        return 0

    destino = GALAS / f"{gala}.html"
    if destino.exists() and not a.forzar:
        print(f"la gala {gala} ya está archivada: no se toca "
              "(para rehacerla antes de la gala, --forzar)")
        return 0

    fuente = ROOT / "gui" / "pronostico.html"
    if not fuente.exists():
        print("falta gui/pronostico.html: correr gui/build.py antes")
        return 1
    html = fuente.read_text()
    # Un archivo con una referencia externa no esta congelado: se actualiza solo
    # cuando cambia lo que referencia. Se comprueba, no se supone.
    fuera = re.findall(r'<script[^>]+src=|<link[^>]+stylesheet', html)
    if fuera:
        print(f"NO se archiva: gui/pronostico.html tiene {len(fuera)} referencia(s) externa(s). "
              "Una copia con referencias externas se reescribe sola y miente con fecha vieja.")
        return 1

    # Las tres llamadas congeladas, para que el sello las diga sin que haya que
    # abrir el JSON.
    H = _leer("historial_pronostico.json")
    etiqueta = {"predicciones_gala": "modelo",
                "predicciones_dos_tiempos": "dos tiempos",
                "apuestas": "apuesta"}
    llamadas = []
    for k, q in etiqueta.items():
        e = [x for x in (H.get(k) or []) if x.get("gala") == gala]
        if not e:
            continue
        p = e[-1]["p_sale"]
        n = max(p, key=p.get)
        llamadas.append((q, f"{n} {100 * p[n]:.1f}%".replace(".", ",")))
    if not llamadas:
        print(f"NO se archiva: no hay ninguna predicción congelada para la gala {gala}. "
              "Archivar una página sin predicción congelada es archivar nada.")
        return 1

    ahora = dt.datetime.now(ART)
    cuando = ahora.strftime("%d/%m/%Y a las %H:%M") + " (hora de la Argentina)"

    GALAS.mkdir(parents=True, exist_ok=True)
    marca = _sello(gala, fecha_larga(fecha_gala), cuando, llamadas)
    i = html.find("<body")
    i = html.find(">", i) + 1 if i >= 0 else 0
    destino.write_text(html[:i] + "\n" + marca + html[i:])

    # El indice del archivo, que es de donde sale la tabla de la pagina.
    idx = ROOT / "data" / "archivo.json"
    reg = json.loads(idx.read_text()) if idx.exists() else {
        "_nota": ("Un renglón por gala archivada. Lo escribe gui/archivar.py en el momento del "
                  "congelamiento y no se edita a mano: la fecha de este renglón y la fecha del "
                  "commit que subió el archivo tienen que coincidir, y ésa es la prueba."),
        "galas": []}
    reg["galas"] = [g for g in reg["galas"] if g.get("gala") != gala]
    reg["galas"].append({
        "gala": gala,
        "fecha_gala": fecha_gala,
        "congelado": ahora.strftime("%Y-%m-%dT%H:%M%z"),
        "archivo": f"galas/{gala}.html",
        "historial": f"{REPO}/commits/main/web/galas/{gala}.html",
        "llamadas": {q: n for q, n in llamadas},
        "placa": prox.get("placa") or [],
    })
    reg["galas"].sort(key=lambda g: g["gala"])
    idx.write_text(json.dumps(reg, ensure_ascii=False, indent=1))

    kb = destino.stat().st_size / 1024
    print(f"archivado web/galas/{gala}.html ({kb:.0f} KB) · congelado {cuando}")
    for q, n in llamadas:
        print(f"    {q:12} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
