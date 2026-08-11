# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
ETAPA 2 - Estimacion del APOYO POSITIVO (psi) con un modelo Plackett-Luce.

Por que importa mas que el rechazo: la final se decide con VOTO POSITIVO, y la
calibracion sobre GH 2024 y 2025 muestra que las dos escalas son casi
ortogonales. Nicolas Grosman llego a la final de 2024 con un rechazo tan bajo
como el del campeon y saco 2%. Juliana "Furia", la mas rechazada de esa
temporada, fue a la vez la MAS votada en las fases positivas. El voto positivo
premia protagonismo, no ausencia de conflicto.

Datos: Telefe no publica porcentajes en las fases positivas, pero anuncia los
salvados EN ORDEN de mas a menos votado. Cada fase es entonces un ranking
parcial, y un ranking parcial es exactamente el dato que consume un modelo
Plackett-Luce:

    P(orden i1 > i2 > ... > ik | conjunto S)
        = prod_j  exp(psi_ij) / sum_{m en S menos los ya elegidos} exp(psi_m)

Tres tipos de observacion:
  * "orden"      -> Plackett-Luce secuencial (11 fases, incluida la del 16/07
                    que es un ranking COMPLETO de los 16 de la casa)
  * "porcentaje" -> multinomial sobre las cuotas (solo el repechaje del 20/05)
  * "conjunto"   -> top-k sin orden interno: se aproxima con las comparaciones
                    pareadas top vs resto (Bradley-Terry)

Ponderacion temporal exponencial y ridge, igual que en la escala negativa.
"""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parent.parent
HOY = date(2026, 8, 8)


def _dias(f):
    y, m, d = (int(x) for x in f.split("-"))
    return (HOY - date(y, m, d)).days


def _lse(x):
    m = float(np.max(x))
    return m + float(np.log(np.sum(np.exp(x - m))))


def ajustar(tau=45.0, ridge=0.12, peso_orden=1.0, peso_pct=4.0, peso_par=1.0,
            fases_override=None, con_hessiano=True):
    """
    peso_par se normaliza por el numero de comparaciones pareadas: una fase con
    top-12 sobre 19 genera 84 pares NO independientes y, sin normalizar,
    dominaria por completo al ranking completo del 16/07 (15 terminos). Tras
    normalizar, cada fase aporta informacion proporcional a cuantos puestos
    revela, que es lo correcto.
    """
    cfg = json.loads((ROOT / "data" / "voto_positivo.json").read_text())
    fases = cfg["fases"] if fases_override is None else fases_override
    jug = sorted({n for f in fases for n in f["candidatos"]})
    ix = {n: i for i, n in enumerate(jug)}
    K = len(jug)

    obs = []
    for f in fases:
        w = math.exp(-_dias(f["fecha"]) / tau)
        S = [ix[n] for n in f["candidatos"]]
        if f["tipo"] == "orden":
            obs.append(("pl", [ix[n] for n in f["orden"]], S, w * peso_orden))
        elif f["tipo"] == "porcentaje":
            q = np.array([f["porcentajes"][n] for n in f["candidatos"]], float)
            obs.append(("multi", S, q / q.sum(), w * peso_pct))
        else:
            top = [ix[n] for n in f["top"]]
            resto = [i for i in S if i not in top]
            npares = max(len(top) * len(resto), 1)
            obs.append(("par", top, resto, w * peso_par * len(top) / npares))

    def nll(psi):
        t = 0.0
        for kind, a, b, w in obs:
            if kind == "pl":
                restantes = list(b)
                for i in a:
                    t -= w * (psi[i] - _lse(psi[restantes]))
                    restantes.remove(i)
            elif kind == "multi":
                sub = psi[a]
                t -= w * float(np.dot(b, sub - _lse(sub)))
            else:
                for i in a:
                    for j in b:
                        d = _lse(np.array([psi[i], psi[j]]))
                        t -= w * (psi[i] - d)
        return t + ridge * float(np.dot(psi, psi))

    best = None
    for s in range(3):
        x0 = np.zeros(K) if s == 0 else np.random.default_rng(s).normal(0, .4, K)
        r = minimize(nll, x0, method="L-BFGS-B",
                     options={"maxiter": 10000, "ftol": 1e-14, "gtol": 1e-11})
        if best is None or r.fun < best.fun:
            best = r
    psi = best.x - best.x.mean()

    if not con_hessiano:
        apar0 = {n_: sum(1 for f in fases if n_ in f["candidatos"]) for n_ in jug}
        return {"jugadores": jug, "psi": psi, "se": np.zeros(K), "ix": ix,
                "apariciones": apar0}

    # covarianza por hessiano numerico
    n = K
    H = np.zeros((n, n))
    eps = 1e-3
    for i in range(n):
        for j in range(i, n):
            xa = best.x.copy(); xa[i] += eps; xa[j] += eps
            xb = best.x.copy(); xb[i] += eps; xb[j] -= eps
            xc = best.x.copy(); xc[i] -= eps; xc[j] += eps
            xd = best.x.copy(); xd[i] -= eps; xd[j] -= eps
            H[i, j] = H[j, i] = (nll(xa) - nll(xb) - nll(xc) + nll(xd)) / (4 * eps * eps)
    cov = np.linalg.pinv(H)
    P = np.eye(n) - np.ones((n, n)) / n
    cov = P @ cov @ P.T
    se = np.sqrt(np.clip(np.diag(cov), 1e-9, None))

    apar = {n_: sum(1 for f in fases if n_ in f["candidatos"]) for n_ in jug}
    return {"jugadores": jug, "psi": psi, "se": se, "ix": ix, "apariciones": apar}


if __name__ == "__main__":
    VIG = ["Charlotte", "Hanssen", "Luana", "Majluf", "Mariela",
           "Pincoya", "Sol", "Tamara", "Yipio", "Zilli"]
    r = ajustar()
    print("### Apoyo positivo psi (Plackett-Luce sobre 12 instancias de voto positivo)")
    print(f"{'jugador':<16}{'psi':>8}{'se':>7}{'fases':>7}")
    for i in np.argsort(-r["psi"]):
        n = r["jugadores"][i]
        marca = " <-" if n in VIG else ""
        print(f"{n:<16}{r['psi'][i]:>8.2f}{r['se'][i]:>7.2f}{r['apariciones'][n]:>7}{marca}")

    print("\n### Solo los 10 en competencia, ordenados por apoyo positivo")
    sub = [(n, r["psi"][r["ix"][n]], r["se"][r["ix"][n]]) for n in VIG]
    for n, p, s in sorted(sub, key=lambda z: -z[1]):
        print(f"   {n:<12}{p:>7.2f}  +-{s:.2f}")

    print("\n### Sensibilidad de psi al horizonte temporal tau")
    for tau in (25, 35, 45, 70, 120, 1e6):
        rr = ajustar(tau=tau)
        o = sorted(VIG, key=lambda n: -rr["psi"][rr["ix"][n]])
        print(f"   tau={tau:<8} " + " > ".join(o[:5]))
