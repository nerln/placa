# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
EL SENTIMIENTO, LEIDO EN LOS COMENTARIOS.

El termometro de la pagina cuenta consignas en tendencias: mide cuanto se
grita un nombre y con que signo, pero no lee lo que la gente escribe. Esto si.

De donde salen los comentarios: de los videos que el propio programa sube a
YouTube. Es el unico corpus publico de reacciones al que se puede llegar sin
credenciales. Se probaron y se descartaron, en este orden:

  * Las respuestas al posteo oficial que pregunta quien debe irse. Tiene 372 y
    ninguna via publica devuelve su texto, solo el conteo.
  * Los comentarios de Instagram. El marco de incrustacion no los trae.
  * Reddit. Devuelve 403 a cualquier peticion anonima.

COMO SE CLASIFICA, y por que asi. No hay un modelo de lenguaje detras: hay un
lexico escrito abajo, a la vista, que cualquiera puede discutir linea por linea.
Un comentario cuenta para alguien si la nombra, y cuenta con signo solo si
ademas trae una marca de signo. La regla que decide casi todo es que en una
placa negativa "X AL 9009" pide que la echen, y en una positiva pide lo
contrario: el signo del lexico se da vuelta con la fase.

LO QUE NO SE HACE: contar como neutral al que no se pudo clasificar. Quien
nombra a alguien sin marca de signo queda SIN CLASIFICAR, que no es lo mismo que
indiferente. Se publica cuantos quedaron afuera, porque esa cifra es la que dice
cuanto vale el resto.

    python3 model/comentarios.py            recoge y clasifica
    python3 model/comentarios.py --recoger  solo recoge, sin clasificar
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36")

# ---------------------------------------------------------------------------
# EL LEXICO. Todo lo que decide un signo esta aca y no en otra parte.
# ---------------------------------------------------------------------------

# Pide que se vaya. En una placa negativa "al 9009" es esto; en una positiva se
# da vuelta, y de eso se encarga FASE mas abajo.
CONTRA = [
    r"\bal ?9009\b", r"\bafuera\b", r"\bque se vaya\b", r"\bchau\b", r"\bfuera\b",
    r"\binsoportable\b", r"\binsufrible\b", r"\bhorrible\b", r"\bhorror\b",
    r"\bno la banco\b", r"\bno la soporto\b", r"\bfalsa\b", r"\bmentirosa\b",
    r"\btramposa\b", r"\bagrand", r"\bsoberbi", r"\bvag[ao]\b", r"\bque asco\b",
]
# Pide que se quede.
FAVOR = [
    r"\bvamos\b", r"\bgenia\b", r"\bcapa\b", r"\bidola\b", r"\bla mejor\b",
    r"\bte amo\b", r"\bhermosa\b", r"\bmerece\b", r"\bcampeona\b",
    r"\ba la final\b", r"\bque se quede\b", r"\bque siga\b", r"\bbancamos\b",
    r"\bla amo\b", r"\bfavorita\b", r"\breina\b",
]
# La marca que se da vuelta con la fase.
DEPENDE_DE_FASE = r"\bal ?9009\b|\bpositiva\b"

# Como se nombra a cada una. Se compara sin tildes y en minuscula.
ALIAS = {
    "Luana": ["luana", "lu "],
    "Majluf": ["majluf", "alejandra", "male"],
    "Charlotte": ["charlotte", "charlot", "caniggia"],
    "Tamara": ["tamara", "tami", "paganini"],
    "Zilli": ["zilli", "yanina"],
    "Sol": ["sol ", "solange", "soli"],
    "Yipio": ["yipio", "yisela"],
    "Pincoya": ["pincoya", "jennifer", "yenifer"],
    "Mariela": ["mariela", "prieto"],
}


def plano(t):
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _pedir(video, paginas):
    """Baja los comentarios de un video, siguiendo las continuaciones."""
    r = subprocess.run(["curl", "-s", "--max-time", "30", "-A", UA,
                        "-H", "Accept-Language: es-AR,es;q=0.9",
                        f"https://www.youtube.com/watch?v={video}"],
                       capture_output=True, text=True)
    h = r.stdout
    k = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', h)
    v = re.search(r'"clientVersion":"([\d.]+)"', h)
    if not (k and v):
        return []
    key, ver = k.group(1), v.group(1)
    toks = re.findall(r'"continuationCommand":\{"token":"([^"]{40,})"', h)
    salida, vistos = [], set()
    for tok in toks[:2]:
        for _ in range(paginas):
            if not tok:
                break
            body = json.dumps({"context": {"client": {"clientName": "WEB",
                                                      "clientVersion": ver,
                                                      "hl": "es", "gl": "AR"}},
                               "continuation": tok})
            p = subprocess.run(["curl", "-s", "--max-time", "30", "-X", "POST",
                                f"https://www.youtube.com/youtubei/v1/next?key={key}"
                                "&prettyPrint=false",
                                "-H", "Content-Type: application/json",
                                "-H", "Accept-Language: es-AR,es;q=0.9", "-A", UA,
                                "--data-binary", body], capture_output=True, text=True)
            if "commentEntityPayload" not in p.stdout:
                break
            d = json.loads(p.stdout)
            nuevos = []

            def rec(o):
                if isinstance(o, dict):
                    if "commentEntityPayload" in o:
                        e = o["commentEntityPayload"]
                        t = ((e.get("properties") or {}).get("content") or {}).get("content")
                        if t and t not in vistos:
                            vistos.add(t)
                            nuevos.append({"video": video, "texto": t})
                    for x in o.values():
                        rec(x)
                elif isinstance(o, list):
                    for x in o:
                        rec(x)

            rec(d)
            salida += nuevos
            sig = re.findall(r'"continuationCommand":\{"token":"([^"]{40,})"', p.stdout)
            tok = sig[-1] if sig and nuevos else None
    return salida


def clasificar(comentarios, jugadoras, fase):
    """Cada comentario, contra quien nombra y con que signo.

    El signo de "al 9009" y de "positiva" se da vuelta segun la fase: en una
    placa negativa piden que la echen y en una positiva que la salven. El resto
    del lexico no depende de la fase.
    """
    vuelta = -1 if fase == "negativo" else 1
    contra = [re.compile(p) for p in CONTRA]
    favor = [re.compile(p) for p in FAVOR]
    fase_rx = re.compile(DEPENDE_DE_FASE)
    alias = {n: [plano(a) for a in ALIAS.get(n, [n.lower()])] for n in jugadoras}

    cuenta = {n: {"contra": 0, "favor": 0, "sin_signo": 0} for n in jugadoras}
    total, nombrados, con_signo = 0, 0, 0
    ejemplos = {n: [] for n in jugadoras}

    for c in comentarios:
        total += 1
        t = plano(c["texto"])
        quienes = [n for n, aa in alias.items() if any(a in t for a in aa)]
        if not quienes:
            continue
        nombrados += 1
        s = 0
        if fase_rx.search(t):
            s += vuelta
        if any(r.search(t) for r in contra):
            s -= 1
        if any(r.search(t) for r in favor):
            s += 1
        for n in quienes:
            if s < 0:
                cuenta[n]["contra"] += 1
            elif s > 0:
                cuenta[n]["favor"] += 1
            else:
                cuenta[n]["sin_signo"] += 1
            if s and len(ejemplos[n]) < 3:
                ejemplos[n].append({"texto": c["texto"][:180],
                                    "signo": "contra" if s < 0 else "favor"})
        if s:
            con_signo += 1

    return {"cuenta": cuenta, "ejemplos": ejemplos, "total": total,
            "nombran_a_alguien": nombrados, "con_signo": con_signo}


def main():
    ap = argparse.ArgumentParser(description="Sentimiento en los comentarios del programa")
    ap.add_argument("--recoger", action="store_true", help="solo recoger")
    ap.add_argument("--paginas", type=int, default=6)
    a = ap.parse_args()

    vids = json.loads((ROOT / "data" / "videos.json").read_text())["videos"]
    todos = []
    for v in vids:
        c = _pedir(v["id"], a.paginas)
        print(f"  {v['id']}  {len(c):4} comentarios · {v['que'][:52]}")
        todos += c
    print(f"total: {len(todos)} comentarios de {len(vids)} videos")
    (ROOT / "data" / "comentarios_crudos.json").write_text(
        json.dumps({"videos": vids, "comentarios": todos}, ensure_ascii=False))
    if a.recoger:
        return

    galas = json.loads((ROOT / "data" / "galas.json").read_text())
    act = json.loads((ROOT / "data" / "actualidad.json").read_text())
    placa = (galas.get("placa_vigente") or {}).get("integrantes") or []
    fase = ((act.get("tendencias") or {}).get("fase")) or "negativo"
    res = clasificar(todos, placa, fase)

    salida = {
        "generado": act.get("generado"),
        "fase": fase,
        "fuente": "comentarios de los videos oficiales del programa en YouTube",
        "metodo": ("Léxico escrito en model/comentarios.py, sin modelo de lenguaje detrás: un "
                   "comentario cuenta para quien nombra, y cuenta con signo sólo si además trae "
                   "una marca del léxico. «Al 9009» y «positiva» cambian de signo con la fase de "
                   "la placa."),
        "limites": ("Son los comentarios de los videos del propio programa, o sea de un público "
                    "que ya entró a mirarlo. No es una muestra de nada y no se pondera. Y quien "
                    "nombra a alguien sin marca de signo queda sin clasificar, que no es lo mismo "
                    "que indiferente."),
        "no_alcanzables": ["las respuestas al posteo oficial de X, que son 372 y no publican texto",
                           "los comentarios de Instagram, que el marco de incrustación no trae",
                           "Reddit, que responde 403 a cualquier petición anónima"],
        "total": res["total"],
        "nombran_a_alguien": res["nombran_a_alguien"],
        "con_signo": res["con_signo"],
        "por_jugadora": res["cuenta"],
        "ejemplos": res["ejemplos"],
    }
    (ROOT / "data" / "sentimiento.json").write_text(
        json.dumps(salida, ensure_ascii=False, indent=1))

    print(f"\n{res['nombran_a_alguien']} nombran a alguien · {res['con_signo']} con signo")
    print(f"\n{'quien':<12} {'contra':>7} {'favor':>7} {'sin signo':>10}   saldo")
    for n in placa:
        c = res["cuenta"][n]
        saldo = c["contra"] - c["favor"]
        print(f"{n:<12} {c['contra']:>7} {c['favor']:>7} {c['sin_signo']:>10}   {saldo:+d}")


if __name__ == "__main__":
    main()
