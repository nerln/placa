# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
EL INDICE DE CAMPANA: lo que el termometro dice con signo.

El termometro de la pagina lista que terminos estuvieron en tendencias y en que
posicion. Eso solo no distingue amor de odio: "Mariela" en el puesto 2 no dice
si la quieren o la quieren afuera. Pero una parte de esos terminos SI lleva el
signo escrito adentro, porque son consignas: "HANSSEN AL 9009" pide que lo
echen, "SOL A LA FINAL" pide lo contrario.

Se llama indice de campana y no indice de sentimiento a proposito. Llamarlo
sentimiento obligaria a defender que mide lo que siente el publico. Llamarlo
campana obliga a defender solo lo que es cierto: que hubo una consigna publica
con signo, y con cuanta fuerza estuvo arriba.

LA DISTINCION QUE SOSTIENE TODO: quien no tiene ningun termino con signo queda
en null, no en cero. Un participante sin campana no es un participante neutral,
es un participante NO MEDIDO. Codificarlo como cero seria afirmar que nadie
pide que se vaya, que es justamente lo que no se sabe.

Y NO ENTRA AL MODELO. Para que entrara habria que estimar cuanto pesa contra
las galas ya jugadas, y con una sola ventana de tendencias no hay con que. Se
publica como descripcion. Que una senal aparezca en la pagina sin entrar al
pronostico es un resultado, no una carencia.

    python3 model/campana.py       ->  data/campana.json
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Consignas cuyo signo esta en el texto y no cambia nunca.
NEGATIVO = re.compile(r"AFUERA|\bFUERA\b|QUE SE VAYA|CHAU ", re.I)

# «X AL 9009» NO lleva el signo adentro: dice a que numero mandar el mensaje, y
# para que sirve ese mensaje lo decide la FASE de la placa. Estaba en la lista
# de negativos, escrito a mano, y el 1 de septiembre de 2026 se abrio la placa
# positiva final —«se va la que menos votos positivos tenga»— con lo cual la
# misma consigna paso a pedir lo contrario. Publicarlo sin mirar la fase habria
# dado vuelta la senal entera el dia de una gala. Es el mismo error de signo
# que esta pagina ya cometio una vez en un pie de grafico.
DEPENDE_DE_FASE = re.compile(r"AL ?9009", re.I)
POSITIVO = re.compile(r"A LA FINAL|CAMPEONA|CAMPEON|GANADORA|SALVEN|LA MEJOR|"
                      r"VAMOS ", re.I)


def _plano(t):
    return "".join(c for c in unicodedata.normalize("NFD", t.upper())
                   if unicodedata.category(c) != "Mn")


def peso(rank):
    """Cuanto pesa haber llegado a esa posicion del top-50. Lineal: el 1 vale 1
    y el 50 vale 0,02. No hay teoria detras; hay que elegir algo y decirlo."""
    return (51 - rank) / 50


def indice(terminos, jugadores, alias, fase=None):
    """Suma de consignas con signo, pesada por su mejor posicion.

    `fase` es «negativo» o «positivo» y decide que quiere decir «AL 9009». Si no
    se pasa, esas consignas se ignoran en vez de suponerles un signo: suponer es
    lo que rompe esto.
    """
    de_fase = {"negativo": -1, "positivo": 1}.get(fase, 0)
    out = {}
    for n in jugadores:
        claves = [_plano(x) for x in ([n] + alias.get(n, []))]
        vistos = []
        total = 0.0
        for t in terminos:
            txt = _plano(t["txt"])
            if not any(k in txt for k in claves):
                continue
            s = (-1 if NEGATIVO.search(t["txt"])
                 else 1 if POSITIVO.search(t["txt"])
                 else de_fase if DEPENDE_DE_FASE.search(t["txt"])
                 else 0)
            if s == 0:
                continue                       # el nombre suelto no lleva signo
            w = peso(t.get("mejor") or 50)
            total += s * w
            vistos.append({"txt": t["txt"], "signo": s, "mejor": t.get("mejor"),
                           "peso": round(w, 3)})
        out[n] = {
            "icd": round(total, 3) if vistos else None,
            "n_terminos": len(vistos),
            "estado": "observado" if vistos else "sin_observacion",
            "terminos": vistos,
        }
    return out


def main():
    act = json.loads((ROOT / "data" / "actualidad.json").read_text())
    res = json.loads((ROOT / "data" / "resultados.json").read_text())
    jug = res["jugadores"]
    T = act.get("tendencias") or {}
    alias_p = ROOT / "data" / "alias.json"
    alias = json.loads(alias_p.read_text()) if alias_p.exists() else {}

    # La fase sale del dato de la placa vigente, no de un valor por defecto:
    # con la fase equivocada este indice dice exactamente lo contrario.
    fase = (T.get("fase")
            or ((act.get("proxima_gala") or {}).get("fases") or [{}])[-1].get("signo"))
    if fase not in ("negativo", "positivo"):
        raise SystemExit("no se sabe el signo de la placa: sin fase, «AL 9009» no significa "
                         "nada y el indice saldria al reves. Poner tendencias.fase o "
                         "proxima_gala.fases[].signo.")
    idx = indice(T.get("terminos", []), jug, alias, fase)
    obs = [n for n in jug if idx[n]["estado"] == "observado"]

    salida = {
        "generado": act.get("generado"),
        "ventana": T.get("ventana"),
        "fuente": "posiciones del top-50 de X en Argentina archivadas por trends24",
        "formula": "ICD(i) = Σ signo(t) · (51 − mejor_posición(t)) / 50, sobre los términos "
                   "que nombran a i y llevan consigna. Una sola consigna que llega al puesto 1 vale 1,00; al puesto 10, 0,82; al 50, 0,02. Dos consignas suman.",
        "entra_al_modelo": False,
        "por_que_no": ("Para que entrara habría que estimar cuánto pesa contra las galas ya "
                       "jugadas, y con una sola ventana de tendencias no hay con qué. Se "
                       "publica como descripción."),
        "null_no_es_cero": ("Quien no tiene ningún término con consigna queda en null. Sin "
                            "campaña no es lo mismo que con campaña neutra: es no medido."),
        "indice": idx,
        "observados": len(obs),
        "de": len(jug),
    }
    (ROOT / "data" / "campana.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1))

    print(f"ventana: {salida['ventana']}")
    print(f"{len(obs)} de {len(jug)} con campaña con signo\n")
    for n in sorted(jug, key=lambda x: (idx[x]["icd"] is None, idx[x]["icd"] or 0)):
        v = idx[n]
        s = "—" if v["icd"] is None else f"{v['icd']:+.2f}"
        det = " · ".join(f"{t['txt']} ({t['signo']:+d}, #{t['mejor']})" for t in v["terminos"])
        print(f"  {n:<11}{s:>7}  {det}")
    print("\nescrito data/campana.json")


if __name__ == "__main__":
    main()
