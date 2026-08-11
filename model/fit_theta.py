# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
ETAPA 1 - Estimacion del rechazo latente (theta) por logit condicional.

Modelo de observacion (derivado de la mecanica real de revelacion de Telefe,
verificada aritmeticamente en 8 de 11 galas):

  * Los porcentajes de las salvaciones progresivas son cuota sobre el TOTAL de
    votos de la placa.
  * El versus final se RENORMALIZA sobre el residuo: r_a + r_b = 100, y la cuota
    absoluta es  q_a = (r_a/100) * (1 - suma de las salvaciones).
  * Comprobacion: suma_total_publicada - 100 == suma de los no-versus. Se cumple
    exactamente en las galas 18, 20, 21, 22, 23, 25, 26 y 27 -> la lista de
    nominados esta completa y la gala es una MULTINOMIAL COMPLETA observada.

Verosimilitud por gala g con placa N_g y cuotas q_i:

      L_g = n_g * sum_i  q_i * log( exp(theta_i) / sum_{j in N_g} exp(theta_j) )

Cuando faltan cuotas, las incognitas se agregan en una categoria "resto" cuya
probabilidad es la suma de sus softmax; cuando solo se conoce el versus, se usa
la binomial de la comparacion pareada (informacion valida e independiente del
resto de la placa).

Ponderacion temporal exponencial (tau) porque el apoyo deriva, y ridge para
regularizar a los jugadores con una sola observacion.
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


def dias(f: str) -> int:
    y, m, d = (int(x) for x in f.split("-"))
    return (HOY - date(y, m, d)).days


def cargar():
    return json.loads((ROOT / "data" / "galas.json").read_text())


def construir_observaciones(cfg, tau=45.0, n_eff=400.0, usar_encuesta=True,
                            n_eff_encuesta=90.0):
    """Devuelve (jugadores, lista de observaciones)."""
    galas = cfg["galas"]
    jugadores = sorted({n for g in galas for n in g["placa"]})
    if usar_encuesta:
        for n in cfg["encuesta_gala28"]["placa"]:
            if n not in jugadores:
                jugadores.append(n)
        jugadores = sorted(set(jugadores))
    idx = {n: i for i, n in enumerate(jugadores)}

    obs = []
    for g in galas:
        w = math.exp(-dias(g["fecha"]) / tau) * n_eff
        placa = [idx[n] for n in g["placa"]]
        sal = {idx[k]: v / 100.0 for k, v in g["salvados_cuota"].items()}
        vs = {idx[k]: v / 100.0 for k, v in g.get("versus", {}).items()}

        if g["completa"] and vs:
            resto = 1.0 - sum(sal.values())
            cuotas = dict(sal)
            for k, v in vs.items():
                cuotas[k] = v * resto
            q = np.array([cuotas.get(i, 0.0) for i in placa])
            q = np.clip(q, 1e-6, None)
            q = q / q.sum()
            obs.append({"tipo": "multinomial", "placa": placa, "q": q, "w": w,
                        "gala": g["gala"]})
        else:
            if sal:
                conocidos = list(sal.keys())
                desconocidos = [i for i in placa if i not in sal]
                q_con = np.array([sal[i] for i in conocidos])
                q_resto = max(1.0 - q_con.sum(), 1e-6)
                obs.append({"tipo": "parcial", "placa": placa,
                            "conocidos": conocidos, "q_con": q_con,
                            "desconocidos": desconocidos, "q_resto": q_resto,
                            "w": w, "gala": g["gala"]})
            if vs and len(vs) == 2:
                (a, pa), (b, pb) = list(vs.items())
                obs.append({"tipo": "par", "a": a, "b": b,
                            "pa": pa / (pa + pb), "w": w, "gala": g["gala"]})

    if usar_encuesta:
        e = cfg["encuesta_gala28"]
        w = math.exp(-dias(e["fecha"]) / tau) * n_eff_encuesta
        placa = [idx[n] for n in e["placa"]]
        conocidos = [idx[k] for k in e["cuota"]]
        q_con = np.array([v / 100.0 for v in e["cuota"].values()])
        desconocidos = [i for i in placa if i not in conocidos]
        obs.append({"tipo": "parcial", "placa": placa, "conocidos": conocidos,
                    "q_con": q_con, "desconocidos": desconocidos,
                    "q_resto": max(1 - q_con.sum(), 1e-6), "w": w,
                    "gala": "encuesta-28"})
    return jugadores, obs, idx


def _lse(x):
    m = float(np.max(x))
    return m + float(np.log(np.sum(np.exp(x - m))))


def nll_factory(obs, K, ridge):
    def nll(th):
        t = 0.0
        for o in obs:
            if o["tipo"] == "multinomial":
                sub = th[o["placa"]]
                t -= o["w"] * float(np.dot(o["q"], sub - _lse(sub)))
            elif o["tipo"] == "parcial":
                Z = _lse(th[o["placa"]])
                lp_con = th[o["conocidos"]] - Z
                t -= o["w"] * float(np.dot(o["q_con"], lp_con))
                if o["desconocidos"]:
                    lp_resto = _lse(th[o["desconocidos"]]) - Z
                else:
                    lp_resto = math.log(1e-9)
                t -= o["w"] * o["q_resto"] * lp_resto
            else:  # par
                d = _lse(np.array([th[o["a"]], th[o["b"]]]))
                t -= o["w"] * (o["pa"] * (th[o["a"]] - d)
                               + (1 - o["pa"]) * (th[o["b"]] - d))
        return t + ridge * float(np.dot(th, th))
    return nll


def hessiana(f, x, eps=2e-4):
    n = len(x)
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            xa = x.copy(); xa[i] += eps; xa[j] += eps
            xb = x.copy(); xb[i] += eps; xb[j] -= eps
            xc = x.copy(); xc[i] -= eps; xc[j] += eps
            xd = x.copy(); xd[i] -= eps; xd[j] -= eps
            H[i, j] = H[j, i] = (f(xa) - f(xb) - f(xc) + f(xd)) / (4 * eps * eps)
    return H


def ajustar(tau=45.0, n_eff=400.0, ridge=1.5, usar_encuesta=True,
            n_eff_encuesta=90.0, verbose=True):
    cfg = cargar()
    jug, obs, idx = construir_observaciones(cfg, tau, n_eff, usar_encuesta,
                                            n_eff_encuesta)
    K = len(jug)
    f = nll_factory(obs, K, ridge)
    best = None
    for s in range(4):
        x0 = np.zeros(K) if s == 0 else np.random.default_rng(s).normal(0, .5, K)
        r = minimize(f, x0, method="L-BFGS-B",
                     options={"maxiter": 8000, "ftol": 1e-14, "gtol": 1e-12})
        if best is None or r.fun < best.fun:
            best = r
    th = best.x - best.x.mean()
    H = hessiana(f, best.x)
    cov = np.linalg.pinv(H)
    # proyectar la covarianza al subespacio centrado (theta identificado salvo constante)
    P = np.eye(K) - np.ones((K, K)) / K
    cov = P @ cov @ P.T
    se = np.sqrt(np.clip(np.diag(cov), 1e-9, None))

    veces = {n: sum(1 for o in obs if idx[n] in o.get("placa", [])
                    or idx[n] in (o.get("a"), o.get("b"))) for n in jug}

    if verbose:
        orden = np.argsort(-th)
        print(f"{'jugador':<14}{'theta':>9}{'se':>8}{'obs':>6}")
        for i in orden:
            print(f"{jug[i]:<14}{th[i]:>9.3f}{se[i]:>8.3f}{veces[jug[i]]:>6}")
    return {"jugadores": jug, "theta": th, "se": se, "cov": cov,
            "idx": idx, "obs": obs, "nll": best.fun, "veces": veces}


if __name__ == "__main__":
    print("=== CON encuesta Bongiorno 07/08 (n_eff=90) ===")
    a = ajustar(usar_encuesta=True)
    print("\n=== SIN encuesta (solo preferencia revelada oficial) ===")
    b = ajustar(usar_encuesta=False)

    vig = ["Charlotte", "Hanssen", "Luana", "Majluf", "Mariela",
           "Pincoya", "Sol", "Tamara", "Yipio", "Zilli"]
    print("\n=== COMPARACION jugadores vigentes ===")
    print(f"{'jugador':<14}{'con encuesta':>14}{'sin encuesta':>14}")
    for n in vig:
        ta = a["theta"][a["idx"][n]] if n in a["idx"] else float("nan")
        tb = b["theta"][b["idx"][n]] if n in b["idx"] else float("nan")
        print(f"{n:<14}{ta:>14.3f}{tb:>14.3f}")
