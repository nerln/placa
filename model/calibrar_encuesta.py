"""
Calibracion de la unica encuesta con historial verificable (Fefe Bongiorno, X).

Bongiorno acerto el eliminado 5 de 5 veces, y en 3 de esas 5 le gano al modelo
de rasgo estable: cada vez que Sol Abraham estuvo en placa, el modelo de rasgo
la daba eliminada y la encuesta (y la realidad) dieron a otro. Por eso la
encuesta NO se puede ignorar. Pero tampoco se puede tomar literal: sus cifras no
suman 100 y aplasta la concentracion real del voto.

Aca se estima cuanto vale, comparando cada encuesta contra el resultado oficial
de la gala siguiente en la escala logit centrada dentro de la gala:

    error_i = [log p_encuesta_i - media(log p_encuesta)] - [log q_real_i - media(log q_real)]

sobre los jugadores presentes en ambas. De ahi salen:
  * sigma_enc : desvio del error -> ruido de observacion de la encuesta
  * sesgo por posicion : si sobreestima sistematicamente a los que no son el blanco
  * tasa de acierto del puesto 1
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

# El historial vive en data/encuestas.json para que model/actualizar.py pueda
# incorporar la encuesta de cada gala nueva sin tocar el codigo.
HISTORIAL = json.loads((ROOT / "data" / "encuestas.json").read_text())["historial"]


def reales(cfg):
    out = {}
    for g in cfg["galas"]:
        if not (g["completa"] and g["versus"]):
            continue
        resto = 1 - sum(g["salvados_cuota"].values()) / 100
        q = {k: v / 100 for k, v in g["salvados_cuota"].items()}
        for k, v in g["versus"].items():
            q[k] = v / 100 * resto
        out[g["gala"]] = (q, g["eliminado"])
    return out


def calibrar(cfg):
    R = reales(cfg)
    errores, filas, aciertos = [], [], []
    for h in HISTORIAL:
        if h["gala"] not in R:
            continue
        q, elim = R[h["gala"]]
        comunes = [n for n in h["encuesta"] if n in q]
        if len(comunes) < 2:
            continue
        le = np.log(np.array([h["encuesta"][n] for n in comunes]))
        lr = np.log(np.array([max(q[n], 3e-4) for n in comunes]))
        e = (le - le.mean()) - (lr - lr.mean())
        top_enc = max(h["encuesta"], key=h["encuesta"].get)
        aciertos.append(top_enc == elim)
        for n, ei, rank in zip(comunes, e,
                               np.argsort(np.argsort(-le)) + 1):
            filas.append((h["gala"], n, int(rank), float(ei),
                          h["encuesta"][n], 100 * q[n]))
            errores.append((int(rank), float(ei)))
    return filas, errores, aciertos


if __name__ == "__main__":
    cfg = json.loads((ROOT / "data" / "galas.json").read_text())
    filas, errores, aciertos = calibrar(cfg)

    print("### Encuesta de Bongiorno vs resultado oficial")
    print(f"{'gala':>5} {'jugador':<11}{'puesto':>7}{'encuesta':>10}{'real':>9}{'error logit':>13}")
    for g, n, rk, e, pe, pr in filas:
        print(f"{g:>5} {n:<11}{rk:>7}{pe:>9.1f}%{pr:>8.2f}%{e:>13.2f}")

    arr = np.array(errores)
    print(f"\n   acierto del puesto 1: {sum(aciertos)}/{len(aciertos)}")
    print(f"   error logit global: media {arr[:,1].mean():+.2f}  desvio {arr[:,1].std(ddof=1):.2f}")
    for rk in sorted(set(arr[:, 0].astype(int))):
        s = arr[arr[:, 0] == rk][:, 1]
        print(f"   puesto {rk}: n={len(s)}  sesgo medio {s.mean():+.2f}  desvio {s.std(ddof=1) if len(s)>1 else float('nan'):.2f}")

    # sigma de observacion para el puesto 1 (lo unico que la encuesta mide bien)
    top = arr[arr[:, 0] == 1][:, 1]
    print(f"\n   -> el puesto 1 se mide con sesgo {top.mean():+.2f} y desvio {top.std(ddof=1):.2f} logits")
    print("   -> los puestos 2+ estan inflados: la encuesta no reproduce la concentracion real")
