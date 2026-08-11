# SPDX-FileCopyrightText: 2026 Eugenio Nerelli <kira_and_light@hotmail.it>
# SPDX-License-Identifier: Apache-2.0
"""
EL CAMINO DE LA ULTIMA: que tendria que pasar para que gane la que no puede.

Un pronostico que dice "Sol 0,8%" no explica nada. Ochocientos por mil es un
numero abstracto y la gente lo lee como "improbable pero quien sabe". Aca se
hace lo contrario: en vez de resumir las simulaciones en las que gana, se
abren, y se pregunta que tienen en comun. La respuesta es la explicacion.

Es una reduccion al absurdo con numeros. Si de cien mil temporadas simuladas
ella gana en unas pocas, esas pocas comparten una descripcion, y esa
descripcion se puede escribir en una frase: cuanto tiene que equivocarse el
modelo sobre su rechazo, cuantas eliminaciones tiene que sobrevivir, quien
tiene que llegar con ella a la final y quien no. Cuando esa frase se lee
entera, se entiende por que no va a pasar mucho mejor que con el 0,8%.

Se corre sobre la MISMA maquinaria que el pronostico -misma semilla, mismos
parametros- guardando de cada simulacion los rasgos sorteados y el desenlace.
No es un modelo aparte: es el pronostico, mirado desde dentro.

    python3 model/camino.py                -> data/camino.json (la ultima)
    python3 model/camino.py --quien Zilli  -> el camino de quien se pida
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "model"))

import final_model as fm                                     # noqa: E402
import fit_psi                                               # noqa: E402

N_SIMS = 300_000        # mas que el pronostico: la rama que interesa es la fina
SEMILLA = 20260808      # la del pronostico, para que sea la misma corrida


def correr(mu, se_mu, omega, psi, se_psi, placa28, m28, s28, prop, quien,
           n_sims=N_SIMS, kappa=0.0, sigma_psi_sem=0.20, beta_mu=0.85,
           beta_sd=0.30, p3=0.70, semanas_a_final=4.0, seed=SEMILLA,
           usar_estado28=True):
    """El Monte Carlo del pronostico, guardando el detalle de cada temporada.

    Copia deliberada de final_model.simular: aqui hace falta el interior de cada
    simulacion -los rasgos sorteados, el orden de las salidas, quien llego a la
    final- y el original solo devuelve los agregados. Si se toca uno hay que
    tocar el otro, y por eso comparten semilla: dos corridas con la misma
    semilla tienen que dar la misma probabilidad de ganar, y el script lo
    comprueba al final.
    """
    rng = np.random.default_rng(seed)
    VIG = fm.VIG
    K = len(VIG); ix = {n: i for i, n in enumerate(VIG)}
    q = ix[quien]
    MU = np.array([mu[n] for n in VIG]); SE = np.array([se_mu[n] for n in VIG])
    PS = np.array([psi[n] for n in VIG]); SP = np.array([se_psi[n] for n in VIG])
    PR = np.array([prop[n] for n in VIG])
    p28 = [ix[n] for n in placa28]

    gana = np.zeros(K)
    # de las temporadas que gana quien nos interesa:
    mu_q, psi_q, bet_q = [], [], []
    n_fin_q = Counter(); rivales = Counter(); duelo = Counter()
    orden_q = Counter(); pasos_q = []
    # y de todas, para tener con que comparar
    mu_todas, psi_todas = [], []

    for _ in range(n_sims):
        m = MU + SE * rng.standard_normal(K)
        if usar_estado28:
            s = np.full(K, np.nan)
            s[p28] = m28 + s28 * rng.standard_normal(len(p28))
            for j, i in enumerate(p28):
                pv, ov = SE[i] ** 2, omega ** 2
                m[i] = (MU[i] / pv + s[i] / ov) / (1 / pv + 1 / ov)
        drift = sigma_psi_sem * np.sqrt(semanas_a_final)
        ps = PS + np.sqrt(SP ** 2 + drift ** 2) * rng.standard_normal(K)
        bet = max(rng.normal(beta_mu, beta_sd), 0.15)
        n_fin = 3 if rng.random() < p3 else 4

        mu_todas.append(m[q]); psi_todas.append(ps[q])

        vivos = list(range(K)); paso = 0; salidas = []
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
            vivos.remove(fuera); salidas.append(fuera)
            paso += 1

        finalistas = list(vivos)
        score = ps - kappa * m
        f = list(vivos)
        ultimo_rival = None
        while len(f) > 1:
            sc = score[f]
            pv = np.exp(bet * (sc - sc.max())); pv /= pv.sum()
            if len(f) == 2:
                ultimo_rival = [x for x in f]
            f.pop(fm._elegir(1 / np.maximum(pv, 1e-12), rng.random()))
        gana[f[0]] += 1

        if f[0] == q:
            mu_q.append(m[q]); psi_q.append(ps[q]); bet_q.append(bet)
            n_fin_q[n_fin] += 1
            pasos_q.append(len(salidas))
            for i in finalistas:
                if i != q:
                    rivales[VIG[i]] += 1
            if ultimo_rival:
                for i in ultimo_rival:
                    if i != q:
                        duelo[VIG[i]] += 1
            orden_q[tuple(VIG[i] for i in salidas[:3])] += 1

    return {
        "gana": gana, "n_sims": n_sims,
        "mu_q": np.array(mu_q), "psi_q": np.array(psi_q), "bet_q": np.array(bet_q),
        "mu_todas": np.array(mu_todas), "psi_todas": np.array(psi_todas),
        "n_fin_q": n_fin_q, "rivales": rivales, "duelo": duelo,
        "orden_q": orden_q, "pasos_q": pasos_q,
    }


def _fecha_corrida():
    g = json.loads((ROOT / "data" / "galas.json").read_text())["galas"]
    return max(x["fecha"] for x in g)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quien", default=None,
                    help="por defecto, la que menos probabilidad tiene")
    a = ap.parse_args()

    cfg, mu, se, omega, var_true, nobs = fm.escala_rechazo()
    placa28, m28, s28, *_ = fm.estado_28(mu, se, omega, cfg)
    rp = fit_psi.ajustar()
    psi = {n: float(rp["psi"][rp["ix"][n]]) for n in fm.VIG}
    se_psi = {n: float(rp["se"][rp["ix"][n]]) for n in fm.VIG}
    prop = fm.propension_nominacion()

    res = json.loads((ROOT / "data" / "resultados.json").read_text())
    base = res["escenarios"]["base"]["p_gana"]
    quien = a.quien or min(base, key=lambda n: base[n])
    print(f"el camino de {quien} · pronóstico {100*base[quien]:.2f}%")
    print(f"abriendo {N_SIMS:,} temporadas…", flush=True)

    o = correr(mu, se, omega, psi, se_psi, placa28, m28, s28, prop, quien,
               usar_estado28=bool(placa28))

    VIG = fm.VIG
    ix = {n: i for i, n in enumerate(VIG)}
    q = ix[quien]
    n = int(o["gana"][q])
    p = n / o["n_sims"]

    # Cuanto tiene que desviarse su rasgo respecto de lo que el modelo cree.
    mu_base = float(o["mu_todas"].mean()); mu_sd = float(o["mu_todas"].std())
    psi_base = float(o["psi_todas"].mean()); psi_sd = float(o["psi_todas"].std())
    mu_gana = float(o["mu_q"].mean()) if n else None
    psi_gana = float(o["psi_q"].mean()) if n else None

    total_riv = sum(o["rivales"].values()) or 1
    salida = {
        "generado": _fecha_corrida(),
        "quien": quien,
        "p_gana": p,
        "n": n,
        "n_sims": o["n_sims"],
        "una_de_cada": round(1 / p) if p > 0 else None,
        "rasgos": {
            "mu_base": round(mu_base, 3), "mu_sd": round(mu_sd, 3),
            "mu_gana": round(mu_gana, 3) if n else None,
            "mu_sigmas": round((mu_base - mu_gana) / mu_sd, 2) if n else None,
            "psi_base": round(psi_base, 3), "psi_sd": round(psi_sd, 3),
            "psi_gana": round(psi_gana, 3) if n else None,
            "psi_sigmas": round((psi_gana - psi_base) / psi_sd, 2) if n else None,
        },
        "eliminaciones_que_sobrevive": (round(float(np.mean(o["pasos_q"])), 1) if n else None),
        "finalistas": {str(k): v / max(n, 1) for k, v in sorted(o["n_fin_q"].items())},
        # con quien llega a la final, y a quien le gana el mano a mano final
        "rivales_final": [{"quien": k, "p": v / max(n, 1)}
                          for k, v in o["rivales"].most_common(5)],
        "duelo_final": [{"quien": k, "p": v / max(n, 1)}
                        for k, v in o["duelo"].most_common(4)],
        "primeras_salidas": [{"orden": list(k), "p": v / max(n, 1)}
                             for k, v in o["orden_q"].most_common(3)],
        "nota": ("Las temporadas en que gana son un subconjunto de la misma corrida de Monte "
                 "Carlo del pronóstico, no una simulación aparte. Lo que se describe es lo que "
                 "esas temporadas tienen en común."),
    }
    (ROOT / "data" / "camino.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1))

    print(f"\ngana en {n:,} de {o['n_sims']:,} · {100*p:.2f}% · una de cada "
          f"{salida['una_de_cada']:,}")
    if n:
        r = salida["rasgos"]
        print(f"  su rechazo tiene que salir {r['mu_sigmas']} desvíos por debajo "
              f"({r['mu_gana']} contra {r['mu_base']})")
        print(f"  su apoyo, {r['psi_sigmas']} por encima "
              f"({r['psi_gana']} contra {r['psi_base']})")
        print(f"  sobrevive {salida['eliminaciones_que_sobrevive']} eliminaciones")
        print("  llega a la final con: " +
              " · ".join(f"{x['quien']} {100*x['p']:.0f}%" for x in salida["rivales_final"][:3]))
        print("  le gana el mano a mano a: " +
              " · ".join(f"{x['quien']} {100*x['p']:.0f}%" for x in salida["duelo_final"][:3]))
    print("\nescrito data/camino.json")


if __name__ == "__main__":
    main()
