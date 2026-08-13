# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
LAS SENDAS: que pasa si sale esta, y despues aquella.

model/ramas.py contesta una pregunta ("si esta noche sale X, como queda el
cuadro"). La pregunta que la gente hace de verdad tiene dos pasos: si sale X y
despues sale Y, entonces que. Y el segundo paso no se puede adivinar del
primero, porque quien queda cambia las placas siguientes.

Aca se calcula la conjunta de las DOS primeras eliminaciones sobre la misma
corrida de Monte Carlo del pronostico. De cada temporada simulada se guarda:

    quien se fue primero · quien se fue segundo · quien gano

Con eso se leen las tres capas sin volver a simular nada:

    P(gana i)                          = el cuadro general
    P(gana i | sale j)                 = una rama
    P(gana i | sale j, luego sale k)   = una senda

Que sea condicional sobre la MISMA corrida y no una simulacion nueva es lo que
hace que las sendas sumen exactamente a su rama, y las ramas al caso base. Lo
unico que hay que vigilar es el n efectivo de la senda mas fina, que se declara
en el JSON y la pagina no dibuja las que no aguantan.

    python3 model/sendas.py       ->  data/sendas.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "model"))

import final_model as fm                                     # noqa: E402
import fit_psi                                               # noqa: E402

# Dos pasos multiplican las celdas: con nueve en juego son 9x8 = 72 sendas, y
# cada una necesita bastantes corridas para que su reparto no sea ruido. Por eso
# aca se simula bastante mas que en el pronostico.
N_SIMS = 600_000
SEMILLA = 20260810          # la de ramas.py: son la misma corrida ampliada
MIN_N = 400                 # una senda con menos corridas no se publica


def simular(mu, se_mu, omega, psi, se_psi, placa28, m28, s28, prop,
            n_sims=N_SIMS, kappa=0.0, sigma_psi_sem=0.20, beta_mu=0.85,
            beta_sd=0.30, p3=0.70, semanas_a_final=4.0, seed=SEMILLA,
            usar_estado28=True):
    """El Monte Carlo del pronostico, guardando las dos primeras salidas."""
    rng = np.random.default_rng(seed)
    VIG = fm.VIG
    K = len(VIG)
    ix = {n: i for i, n in enumerate(VIG)}
    MU = np.array([mu[n] for n in VIG]); SE = np.array([se_mu[n] for n in VIG])
    PS = np.array([psi[n] for n in VIG]); SP = np.array([se_psi[n] for n in VIG])
    PR = np.array([prop[n] for n in VIG])
    p28 = [ix[n] for n in placa28]

    # [primero, segundo, ganador] y [primero, segundo] para el denominador
    conj = np.zeros((K, K, K), dtype=np.int32)
    pares = np.zeros((K, K), dtype=np.int32)

    for _ in range(n_sims):
        m = MU + SE * rng.standard_normal(K)
        s = np.full(K, np.nan)
        if usar_estado28:
            s[p28] = m28 + s28 * rng.standard_normal(len(p28))
            for j, i in enumerate(p28):
                pv, ov = SE[i] ** 2, omega ** 2
                m[i] = (MU[i] / pv + s[i] / ov) / (1 / pv + 1 / ov)
        drift = sigma_psi_sem * np.sqrt(semanas_a_final)
        ps = PS + np.sqrt(SP ** 2 + drift ** 2) * rng.standard_normal(K)
        bet = max(rng.normal(beta_mu, beta_sd), 0.15)
        n_fin = 3 if rng.random() < p3 else 4

        vivos = list(range(K))
        paso = 0
        primero = segundo = -1
        while len(vivos) > n_fin:
            if paso == 0 and usar_estado28:
                placa = list(p28); st = s[placa]
            else:
                lider = vivos[int(rng.random() * len(vivos))]
                cand = [i for i in vivos if i != lider]
                tam = max(3, min(len(cand), int(round(0.62 * len(cand)))))
                sel = fm._topk(PR[cand], tam, rng)
                placa = [cand[j] for j in sel]
                st = m[placa] + omega * rng.standard_normal(tam)
            p = np.exp(st - st.max())
            fuera = placa[fm._elegir(p, rng.random())]
            vivos.remove(fuera)
            if paso == 0:
                primero = fuera
            elif paso == 1:
                segundo = fuera
            paso += 1

        score = ps - kappa * m
        f = list(vivos)
        while len(f) > 1:
            sc = score[f]
            pv = np.exp(bet * (sc - sc.max())); pv /= pv.sum()
            f.pop(fm._elegir(1 / np.maximum(pv, 1e-12), rng.random()))

        if segundo >= 0:
            conj[primero, segundo, f[0]] += 1
            pares[primero, segundo] += 1
        else:
            # Una temporada tan corta que no hubo segunda eliminacion. No puede
            # pasar con nueve en juego y una final de tres o cuatro, pero si el
            # plantel se achica esto deja de ser imposible y no debe romperse.
            pass

    return conj, pares


def _fecha_corrida():
    """Igual que en final_model: cuenta la ultima gala resuelta y tambien la
    nominacion de la placa vigente, que cambia el pronostico sin que se vaya
    nadie."""
    d = json.loads((ROOT / "data" / "galas.json").read_text())
    fechas = [x["fecha"] for x in d["galas"]]
    nom = (d.get("placa_vigente") or {}).get("fecha_nominacion")
    if nom:
        fechas.append(nom)
    return max(fechas)


def main():
    cfg, mu, se, omega, var_true, nobs = fm.escala_rechazo()
    placa28, m28, s28, *_ = fm.estado_28(mu, se, omega, cfg)
    rp = fit_psi.ajustar()
    psi = {n: float(rp["psi"][rp["ix"][n]]) for n in fm.VIG}
    se_psi = {n: float(rp["se"][rp["ix"][n]]) for n in fm.VIG}
    prop = fm.propension_nominacion()

    hay_placa = bool(placa28)
    print(f"placa: {', '.join(placa28) if hay_placa else 'sin definir todavia'}")
    print(f"simulando {N_SIMS:,} temporadas y guardando las dos primeras salidas…",
          flush=True)
    conj, pares = simular(mu, se, omega, psi, se_psi, placa28, m28, s28, prop,
                          usar_estado28=hay_placa)

    VIG = fm.VIG
    K = len(VIG)
    total = int(pares.sum())
    base = conj.sum((0, 1)) / total
    sale1 = pares.sum(1) / total

    sendas = {}
    finas = []
    for a in range(K):
        if pares[a].sum() < MIN_N:
            continue
        rama = {
            "p": float(sale1[a]),
            "n": int(pares[a].sum()),
            # el cuadro despues de esa salida, antes de saber la siguiente
            "p_gana": {VIG[i]: float(conj[a].sum(0)[i] / pares[a].sum()) for i in range(K)},
            # y quien es el siguiente candidato a irse, en ese mundo
            "sale2": {VIG[b]: float(pares[a, b] / pares[a].sum())
                      for b in range(K) if pares[a, b] > 0},
            "sendas": {},
        }
        for b in range(K):
            n = int(pares[a, b])
            if n < MIN_N:
                if n:
                    finas.append((VIG[a], VIG[b], n))
                continue
            rama["sendas"][VIG[b]] = {
                "p": float(n / pares[a].sum()),
                "n": n,
                "p_gana": {VIG[i]: float(conj[a, b, i] / n) for i in range(K)},
            }
        sendas[VIG[a]] = rama

    salida = {
        "generado": _fecha_corrida(),
        "n_sims": total,
        "semilla": SEMILLA,
        "min_n": MIN_N,
        "hay_placa": hay_placa,
        "jugadores": VIG,
        "base": {VIG[i]: float(base[i]) for i in range(K)},
        "ramas": sendas,
        "descartadas": len(finas),
        "nota": ("Las tres capas -cuadro general, rama y senda- son subconjuntos de la misma "
                 "corrida de Monte Carlo, no simulaciones distintas. Por eso las sendas pesadas "
                 "por su probabilidad devuelven su rama, y las ramas devuelven el cuadro. "
                 f"No se publican las sendas con menos de {MIN_N} temporadas: su reparto seria "
                 "ruido con forma de dato."),
    }
    (ROOT / "data" / "sendas.json").write_text(json.dumps(salida, ensure_ascii=False))

    print(f"\n{total:,} temporadas · {len(sendas)} ramas · "
          f"{sum(len(r['sendas']) for r in sendas.values())} sendas publicadas · "
          f"{len(finas)} descartadas por finas")
    for a in sorted(sendas, key=lambda x: -sendas[x]["p"])[:3]:
        r = sendas[a]
        sig = sorted(r["sale2"].items(), key=lambda z: -z[1])[:3]
        print(f"  si sale {a} ({100*r['p']:.1f}%) → después: " +
              " · ".join(f"{k} {100*v:.0f}%" for k, v in sig))


if __name__ == "__main__":
    main()
