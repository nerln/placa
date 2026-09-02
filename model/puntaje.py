# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
EL PUNTAJE: cuánto se acercó cada predicción, con la regla escrita de antes.

EVALUACION.md fija cómo se puntúa la pregunta «quién se va en cada gala»: Brier
multiclase sobre las nominadas, contra dos baselines declaradas. Esto lo aplica
sobre lo que quedó congelado en data/historial_pronostico.json ANTES de la gala,
que es la única forma de que el puntaje signifique algo.

Se puntúan por separado las dos cosas que la página publica para la misma
pregunta, porque son dos afirmaciones distintas y mezclarlas sería elegir
después cuál defender:

    * la del MODELO, en `predicciones_gala`
    * la APUESTA declarada, en `apuestas`

Y se reporta también el puesto en que cada una dejó al que efectivamente salió,
que es lo que se entiende sin saber qué es un Brier.

    python3 model/puntaje.py --gala 29 --eliminado Luana
    python3 model/puntaje.py                 (toma la última gala resuelta)

Escribe data/puntaje.json, append-only: una entrada por gala y no se reescribe.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _leer(n):
    return json.loads((ROOT / "data" / n).read_text())


def brier(p, quien, universo):
    """Brier multiclase sobre el universo de nominadas de esa gala."""
    return sum((p.get(n, 0.0) - (1.0 if n == quien else 0.0)) ** 2 for n in universo)


def puntuar(dist, quien, universo):
    """Brier, log-verosimilitud y puesto, con las baselines al lado."""
    if not dist:
        return None
    orden = sorted(universo, key=lambda n: -dist.get(n, 0.0))
    p = dist.get(quien, 0.0)
    unif = {n: 1.0 / len(universo) for n in universo}
    return {
        "p_del_eliminado": round(p, 4),
        "puesto": orden.index(quien) + 1 if quien in orden else None,
        "de": len(universo),
        "acerto": bool(orden and orden[0] == quien),
        "brier": round(brier(dist, quien, universo), 4),
        "brier_uniforme": round(brier(unif, quien, universo), 4),
        "log_verosimilitud": round(math.log(p), 4) if p > 0 else None,
        "log_verosimilitud_uniforme": round(math.log(1.0 / len(universo)), 4),
        "orden": orden,
    }


def main():
    ap = argparse.ArgumentParser(description="Puntúa las predicciones congeladas de una gala")
    ap.add_argument("--gala", type=int)
    ap.add_argument("--eliminado")
    a = ap.parse_args()

    galas = _leer("galas.json")
    H = _leer("historial_pronostico.json")

    if a.gala and a.eliminado:
        gala, quien = a.gala, a.eliminado
    else:
        jugadas = [g for g in galas["galas"] if g.get("eliminado")]
        if not jugadas:
            print("no hay ninguna gala resuelta que puntuar")
            return
        ult = max(jugadas, key=lambda g: g["fecha"])
        gala, quien = ult.get("gala"), ult["eliminado"]
    print(f"gala {gala} · salió {quien}")

    def ultima(lista):
        cand = [e for e in (H.get(lista) or []) if e.get("gala") == gala]
        return cand[-1] if cand else None

    pm, pa = ultima("predicciones_gala"), ultima("apuestas")
    pd = ultima("predicciones_dos_tiempos")
    pc = ultima("cruces")
    if not (pm or pa):
        print(f"no hay ninguna predicción congelada para la gala {gala}: no se puntúa")
        return

    universo = (pm or pa)["placa"]
    if quien not in universo:
        print(f"ojo: {quien} no estaba en la placa congelada {universo}. No se puntúa: "
              "una predicción sobre otra placa no se puede puntuar con ésta.")
        return

    salida = {
        "gala": gala, "fecha": (pm or pa).get("fecha_gala"), "eliminado": quien,
        "placa": universo,
        "regla": "EVALUACION.md, escrita antes de que terminara la temporada",
        "modelo": puntuar((pm or {}).get("p_sale"), quien, universo) if pm else None,
        "dos_tiempos": puntuar((pd or {}).get("p_sale"), quien, universo) if pd else None,
        "apuesta": puntuar((pa or {}).get("p_sale"), quien, universo) if pa else None,
        "cruce": puntuar((pc or {}).get("p_sale"), quien, universo) if pc else None,
        "congeladas": {"modelo": (pm or {}).get("corrida"),
                       "dos_tiempos": (pd or {}).get("corrida"),
                       "apuesta": (pa or {}).get("escrita"),
                       "cruce": (pc or {}).get("escrita")},
    }

    reg = H.setdefault("puntajes", [])
    if not any(x.get("gala") == gala for x in reg):
        reg.append(salida)
        (ROOT / "data" / "historial_pronostico.json").write_text(
            json.dumps(H, ensure_ascii=False, indent=1))
    (ROOT / "data" / "puntaje.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1))

    for cual in ("modelo", "dos_tiempos", "apuesta", "cruce"):
        r = salida[cual]
        if not r:
            print(f"  {cual}: sin predicción congelada")
            continue
        print(f"  {cual:8} le daba {100*r['p_del_eliminado']:.1f}% · puesto {r['puesto']} de "
              f"{r['de']} · Brier {r['brier']} contra {r['brier_uniforme']} del azar"
              f"{'  ACERTÓ' if r['acerto'] else ''}")


if __name__ == "__main__":
    main()
