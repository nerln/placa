# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
LAS CONSIGNAS, LEIDAS SOLAS.

Hasta ahora esto se hacia a mano: alguien abria trends24, contaba en cuantas
tarjetas horarias aparecia cada «X AL 9009» y a que puesto habia llegado, y
copiaba los numeros a data/actualidad.json. Se hizo tres veces y las tres salio
bien, pero es exactamente la clase de tarea que una persona hace peor que un
guion y solo cuando se acuerda.

QUE LEE. trends24.in/argentina publica gratis las ultimas 24 horas del top-50
argentino, en tarjetas por hora. Cada tarjeta es un <ol> con los terminos EN
ORDEN, asi que de ahi salen las dos cosas que importan: cuantas horas estuvo
arriba una consigna y a que puesto llego.

EL SIGNO NO LO PONE ESTE GUION. «X AL 9009» dice a que numero mandar el
mensaje, y para que sirve ese mensaje lo decide la fase de la placa: en negativa
pide que la echen, en positiva que se quede. Aca solo se cuenta; el signo lo
aplica model/campana.py leyendo la fase. Si la fase falta, este guion igual
escribe las cuentas y campana.py se niega a seguir, que es el orden correcto.

LO QUE NO HACE. No inventa. Si la pagina no responde o cambia de forma, sale
con error y no toca nada: es preferible que la pagina siga mostrando la
medicion de hace tres horas, fechada, a que muestre una vacia sin decirlo.

    python3 model/tendencias.py            escribe si consigue leer
    python3 model/tendencias.py --ver      solo imprime, no escribe
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import re
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = dt.timezone(dt.timedelta(hours=-3))
URL = "https://trends24.in/argentina/"
UA = "Mozilla/5.0 (compatible; placa/1.0; +https://github.com/nerln/placa)"
CONSIGNA = re.compile(r"\bAL ?9009\b", re.I)


def _plano(t):
    return "".join(c for c in unicodedata.normalize("NFD", t.upper())
                   if unicodedata.category(c) != "Mn")


def bajar(url=URL, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def leer(html, nombres):
    """(por_nombre, n_tarjetas). Por nombre: mejor puesto y cuantas tarjetas."""
    tarjetas = re.findall(r'<ol[^>]*trend-card__list[^>]*>(.*?)</ol>', html, re.S)
    mejor, horas, texto = {}, collections.Counter(), {}
    for c in tarjetas:
        for i, it in enumerate(re.findall(r'<li[^>]*>(.*?)</li>', c, re.S), 1):
            t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", it)).strip()
            if not CONSIGNA.search(t):
                continue
            p = _plano(t)
            for n in nombres:
                k = _plano(n)
                if p.startswith(k) or f" {k} " in f" {p} ":
                    horas[n] += 1
                    if n not in mejor or i < mejor[n]:
                        mejor[n], texto[n] = i, t
                    break
    return {n: {"mejor": mejor[n], "horas": horas[n], "txt": texto[n]} for n in mejor}, len(tarjetas)


def main():
    ap = argparse.ArgumentParser(description="Lee las consignas del top-50 argentino")
    ap.add_argument("--ver", action="store_true", help="no escribe, solo imprime")
    a = ap.parse_args()

    act = json.loads((ROOT / "data" / "actualidad.json").read_text())
    G = act.get("proxima_gala") or {}
    placa = G.get("placa") or []
    if not placa:
        print("sin placa vigente: no hay a quien buscarle consigna")
        return 0
    fase = ((act.get("tendencias") or {}).get("fase")
            or (G.get("fases") or [{}])[-1].get("signo") or "")

    html = bajar()
    hallados, n_tarjetas = leer(html, placa)
    if n_tarjetas < 4:
        raise SystemExit(f"solo {n_tarjetas} tarjetas: la pagina cambio de forma o no cargo. "
                         "No se escribe nada.")

    ahora = dt.datetime.now(ART).strftime("%Y-%m-%dT%H:%M%z")
    term = [{"txt": v["txt"], "mejor": v["mejor"], "horas": v["horas"],
             "tipo": "campaña de voto"}
            for _, v in sorted(hallados.items(), key=lambda kv: kv[1]["mejor"])]
    sin = [n for n in placa if n not in hallados]

    print(f"{n_tarjetas} tarjetas · fase {fase or '(sin declarar)'} · {ahora}")
    for t in term:
        print(f"  {t['txt'][:28]:30} pico #{t['mejor']:<3} · {t['horas']} tarjetas")
    if sin:
        print("  sin consigna:", ", ".join(sin))
    if a.ver:
        return 0

    T = act.setdefault("tendencias", {})
    T.update({
        "ventana": f"{n_tarjetas} tarjetas horarias de trends24.in/argentina",
        "hasta": ahora, "medido": ahora, "terminos": term,
        "sin_consigna": {"quienes": sin,
                         "_nota": ("No aparecen con consigna en las tarjetas de la ventana. "
                                   "En placa positiva eso quiere decir que nadie está pidiendo "
                                   "que se queden; en negativa, que nadie pide que se vayan.")},
        "_nota_momento": ("trends24 publica gratis sólo las últimas 24 horas, así que las horas "
                          "son un piso y no un total."),
        "_recogido_por": "model/tendencias.py, automático",
    })
    act["termometro_placa"] = {
        "_nota": (act.get("termometro_placa") or {}).get("_nota", ""),
        "fase": fase, "medido": ahora,
        "significado": (act.get("termometro_placa") or {}).get("significado", ""),
        "ventana": {"desde": None, "hasta": ahora,
                    "_nota": f"{n_tarjetas} tarjetas horarias, que es lo que el sitio publica gratis."},
        "horas_son_piso": True,
        "consignas": [{"termino": t["txt"], "quien": next(
                          (n for n in placa if _plano(n) in _plano(t["txt"])), ""),
                       "pico": t["mejor"], "horas": t["horas"], "fuentes": 1,
                       "fuente": f"trends24.in/argentina, {n_tarjetas} tarjetas horarias"}
                      for t in term],
        "sin_consigna": T["sin_consigna"],
        "aviso": (act.get("termometro_placa") or {}).get("aviso", ""),
    }
    (ROOT / "data" / "actualidad.json").write_text(json.dumps(act, ensure_ascii=False, indent=1))
    print("escrito data/actualidad.json → tendencias y termometro_placa")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
