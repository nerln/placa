# SPDX-FileCopyrightText: 2026 Eugenio Nerelli <kira_and_light@hotmail.it>
# SPDX-License-Identifier: Apache-2.0
"""
ETAPA 1-ter - Descomposicion de varianza del voto negativo.

Hallazgo que obliga a cambiar de modelo: la cuota de voto negativo de un mismo
jugador en galas consecutivas correlaciona -0,13 (Spearman -0,27). No hay
persistencia semana a semana. Casos: Emanuel 0,4% -> 53,8%; Cola 0,5% -> 68,2%;
Majluf 20,2% -> 0,9%. El publico no reparte rechazo segun un rasgo fijo: elige
un blanco por semana, y el blanco cambia cuando el anterior ya se fue.

Pero SI hay un efecto de piso: Hanssen midio <=2,5% seis galas seguidas. O sea,
hay una parte estable y una parte volatil. Este script las separa.

Modelo de efectos mixtos sobre la escala logit. Bajo el logit condicional,

      log q_{i,g} = theta_{i,g} - log Z_g

y centrando dentro de cada gala se elimina el termino de normalizacion:

      y_{i,g} = log q_{i,g} - media_j(log q_{j,g})
              = (mu_i - media_j mu_j) + (eps_{i,g} - media_j eps_{j,g})

con mu_i el rasgo estable de rechazo y eps_{i,g} ~ N(0, omega^2) el "turno"
semanal. Se estima mu por minimos cuadrados con efectos fijos de gala y omega
por la varianza residual, con correccion de grados de libertad.

El cociente omega^2 / (var(mu) + omega^2) mide que fraccion del voto negativo es
IMPREDECIBLE desde el pasado. Es el numero que fija cuanta confianza puede tener
el pronostico semanal.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def cuotas_completas(cfg):
    """Solo las galas cuya aritmetica prueba que la placa esta completa."""
    out = []
    for g in cfg["galas"]:
        if not (g["completa"] and g["versus"]):
            continue
        resto = 1 - sum(g["salvados_cuota"].values()) / 100
        q = {k: v / 100 for k, v in g["salvados_cuota"].items()}
        for k, v in g["versus"].items():
            q[k] = v / 100 * resto
        s = sum(q.values())
        out.append({"gala": g["gala"], "fecha": g["fecha"],
                    "q": {k: v / s for k, v in q.items()},
                    "eliminado": g["eliminado"]})
    return out


def ajustar(cfg, piso=3e-4):
    galas = cuotas_completas(cfg)
    jug = sorted({n for g in galas for n in g["q"]})
    ji = {n: i for i, n in enumerate(jug)}
    K, G = len(jug), len(galas)

    filas = []
    for gi, g in enumerate(galas):
        for n, v in g["q"].items():
            filas.append((ji[n], gi, np.log(max(v, piso))))
    y = np.array([f[2] for f in filas])

    # diseno: efecto de jugador + efecto de gala (este ultimo absorbe log Z_g)
    X = np.zeros((len(filas), K + G))
    for r, (i, gi, _) in enumerate(filas):
        X[r, i] = 1.0
        X[r, K + gi] = 1.0
    # restriccion de identificacion: suma de los efectos de jugador = 0
    R = np.zeros((1, K + G)); R[0, :K] = 1.0
    A = np.vstack([X, 1e3 * R])
    b = np.concatenate([y, [0.0]])
    coef, *_ = np.linalg.lstsq(A, b, rcond=None)
    mu = coef[:K]

    resid = y - X @ coef
    df = len(filas) - (K + G - 1)
    omega2 = float(resid @ resid) / max(df, 1)

    n_obs = {n: sum(1 for f in filas if f[0] == ji[n]) for n in jug}
    var_mu = float(np.var(mu, ddof=1))

    return {"jugadores": jug, "mu": mu, "ji": ji, "omega": float(np.sqrt(omega2)),
            "var_mu": var_mu, "n_obs": n_obs, "df": df, "galas": galas,
            "resid": resid, "filas": filas}


if __name__ == "__main__":
    cfg = json.loads((ROOT / "data" / "galas.json").read_text())
    r = ajustar(cfg)
    print("### Componentes de varianza del voto negativo (escala logit)")
    print(f"   galas completas usadas : {len(r['galas'])}")
    print(f"   observaciones          : {len(r['filas'])}")
    print(f"   grados de libertad     : {r['df']}")
    print(f"   var(mu)  rasgo estable  = {r['var_mu']:.3f}")
    print(f"   omega^2  turno semanal  = {r['omega']**2:.3f}   (omega = {r['omega']:.3f})")
    icc = r["var_mu"] / (r["var_mu"] + r["omega"] ** 2)
    print(f"   fraccion ESTABLE (ICC)  = {100*icc:.1f}%")
    print(f"   fraccion IMPREDECIBLE   = {100*(1-icc):.1f}%")

    print("\n### Rasgo estable de rechazo mu (mas alto = mas votado para eliminar)")
    orden = np.argsort(-r["mu"])
    for i in orden:
        n = r["jugadores"][i]
        print(f"   {n:<12}{r['mu'][i]:>8.2f}   ({r['n_obs'][n]} galas)")
