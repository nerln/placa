# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
Bootstrap de la pipeline completa.

El caso base deja a Tamara y Pincoya practicamente empatadas (22,5% vs 21,2%),
y esa diferencia es menor que la incertidumbre de los datos. La pregunta
"a quien elijo" no se contesta mirando el punto estimado: se contesta
remuestreando la evidencia y viendo con que frecuencia cada una queda arriba.

Se remuestrean con reposicion las dos fuentes primarias:
  * las 8 galas de voto negativo con reparto completo -> reestima mu y omega
  * las 12 instancias de voto positivo                -> reestima psi
y se vuelve a correr el Monte Carlo. La fase del 16/07 se protege del
remuestreo porque es la unica observacion completa de voto positivo: sin ella
el modelo pierde su ancla y el bootstrap mediria ruido de especificacion en vez
de incertidumbre muestral.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "model"))

import fit_psi                                             # noqa: E402
import variance_components as vc                           # noqa: E402
from final_model import (VIG, propension_nominacion, estado_28, simular)  # noqa: E402

B = 60
N_SIMS = 30_000


def main():
    cfg_neg = json.loads((ROOT / "data" / "galas.json").read_text())
    cfg_pos = json.loads((ROOT / "data" / "voto_positivo.json").read_text())
    completas = [g for g in cfg_neg["galas"] if g["completa"] and g["versus"]]
    otras = [g for g in cfg_neg["galas"] if not (g["completa"] and g["versus"])]
    fases = cfg_pos["fases"]
    ancla = [f for f in fases if f["id"] == "gala24_16jul"]
    resto_fases = [f for f in fases if f["id"] != "gala24_16jul"]
    prop = propension_nominacion()

    rng = np.random.default_rng(7)
    ganadores, tops, rank_sum = [], Counter(), {n: [] for n in VIG}

    for b in range(B):
        gs = [completas[i] for i in rng.integers(0, len(completas), len(completas))]
        cfgb = {"galas": gs + otras, "placa_vigente": cfg_neg["placa_vigente"]}
        try:
            r = vc.ajustar(cfgb)
        except Exception:
            continue
        om2 = r["omega"] ** 2
        nn = np.array([r["n_obs"][j] for j in r["jugadores"]])
        var_true = max(float(np.var(r["mu"], ddof=1)) - om2 * float(np.mean(1 / nn)), 1e-3)
        k = var_true / (var_true + om2 / nn)
        mu = {j: float(k[i] * r["mu"][i]) for i, j in enumerate(r["jugadores"])}
        se = {j: float(np.sqrt(var_true * (1 - k[i]))) for i, j in enumerate(r["jugadores"])}
        for j in VIG:
            mu.setdefault(j, 0.0); se.setdefault(j, float(np.sqrt(var_true)))
        omega = float(r["omega"])

        fb = ancla + [resto_fases[i] for i in rng.integers(0, len(resto_fases), len(resto_fases))]
        rp = fit_psi.ajustar(fases_override=fb, con_hessiano=False)
        psi = {n: float(rp["psi"][rp["ix"][n]]) if n in rp["ix"] else 0.0 for n in VIG}
        se_psi = {n: 1.0 for n in VIG}

        try:
            placa, m28, s28, *_ = estado_28(mu, se, omega, cfgb)
        except Exception:
            continue
        # Sin placa definida la primera eliminacion se sortea como las demas.
        # Sin esta bandera, simular intenta reducir sobre una placa vacia.
        out = simular(mu, se, omega, psi, se_psi, placa, m28, s28, prop,
                      n_sims=N_SIMS, seed=1000 + b, usar_estado28=bool(placa))
        p = out["p_gana"]
        ganadores.append(p)
        tops[VIG[int(np.argmax(p))]] += 1
        orden = np.argsort(-p)
        for pos, i in enumerate(orden, 1):
            rank_sum[VIG[i]].append(pos)
        if (b + 1) % 10 == 0:
            print(f"  ... {b+1}/{B}")

    P = np.array(ganadores)
    n = len(P)
    print(f"\n### Bootstrap de {n} remuestreos\n")
    print(f"{'jugador':<12}{'P(gana) media':>15}{'IC 90% bootstrap':>22}{'P(ser el favorito)':>21}{'puesto mediano':>16}")
    orden = np.argsort(-P.mean(0))
    for i in orden:
        nm = VIG[i]
        lo, hi = np.percentile(P[:, i], [5, 95])
        print(f"{nm:<12}{100*P[:,i].mean():>14.1f}%{100*lo:>12.1f}-{100*hi:<8.1f}"
              f"{100*tops[nm]/n:>19.0f}%{int(np.median(rank_sum[nm])):>16}")

    (ROOT / "data" / "bootstrap.json").write_text(json.dumps({
        "B": n,
        "media": {VIG[i]: float(P[:, i].mean()) for i in range(len(VIG))},
        "ic90": {VIG[i]: [float(np.percentile(P[:, i], 5)),
                          float(np.percentile(P[:, i], 95))] for i in range(len(VIG))},
        "p_favorito": {nm: tops[nm] / n for nm in VIG},
        "puesto_mediano": {nm: float(np.median(rank_sum[nm])) for nm in VIG},
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
