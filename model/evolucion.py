# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
POR QUE CAMBIO LA FAVORITA - la anatomia de una gala.

Una gala contesta DOS preguntas y la pagina solo anticipaba una. Antes de cada
eliminacion se publica una rama que dice "si sale fulana, queda asi". Sale
fulana, y al dia siguiente el pronostico no coincide con esa rama. Da la
sensacion de que algo no cierra, y la explicacion es lo interesante del modelo.

La rama contestaba QUIEN se va. La gala ademas dice POR CUANTO, y ese segundo
dato es informacion nueva sobre el rechazo de todas las que estaban en placa.
Salvarse con el 1,9% no es lo mismo que salvarse con el 4,5%: mueve el rasgo mu
en direcciones opuestas, y mu es lo que decide quien sobrevive semana a semana.
La rama no podia anticiparlo, porque se calculo antes de que esos porcentajes
existieran.

Este script separa las dos cosas corriendo el modelo de hoy dos veces:

    CON  los porcentajes de la ultima gala informando mu
    SIN  esos porcentajes, pero con el eliminado ya fuera del plantel

La diferencia entre las dos es, exactamente, lo que dijeron esos numeros. Todo
lo demas -codigo, plantel, psi, propensiones, semilla- es identico.

La gala que se explica se elige sola: la ultima resuelta que tenga el reparto
completo. Estuvo escrita a mano un tiempo, apuntando siempre a la misma noche,
y la seccion siguio explicando una gala vieja durante una semana sin que
ninguna comprobacion lo notara.

    python3 model/evolucion.py      ->  data/evolucion.json
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "model"))

import final_model as fm                                     # noqa: E402
import fit_psi                                               # noqa: E402
from variance_components import ajustar as vc_ajustar        # noqa: E402

N_SIMS = 150_000
def _ultima_gala_completa(cfg):
    """La ultima gala resuelta con reparto completo, que es la unica que informa mu."""
    utiles = [g for g in cfg["galas"]
              if g.get("completa") and g.get("eliminado") and g.get("salvados_cuota")]
    if not utiles:
        return None
    return max(utiles, key=lambda g: (g["fecha"], g.get("gala") or 0))["gala"]


def escala_con(cfg):
    """final_model.escala_rechazo pero sobre un cfg que se le pasa."""
    r = vc_ajustar(cfg)
    om2 = r["omega"] ** 2
    n = np.array([r["n_obs"][j] for j in r["jugadores"]])
    var_true = max(float(np.var(r["mu"], ddof=1)) - om2 * float(np.mean(1 / n)), 1e-3)
    k = var_true / (var_true + om2 / n)
    mu = {j: float(k[i] * r["mu"][i]) for i, j in enumerate(r["jugadores"])}
    se = {j: float(np.sqrt(var_true * (1 - k[i]))) for i, j in enumerate(r["jugadores"])}
    for j in fm.VIG:
        if j not in mu:
            mu[j], se[j] = 0.0, float(np.sqrt(var_true))
    return mu, se, float(r["omega"])


def correr(cfg, psi, se_psi, prop, seed):
    mu, se, omega = escala_con(cfg)
    placa, m28, s28, *_ = fm.estado_28(mu, se, omega, cfg)
    out = fm.simular(mu, se, omega, psi, se_psi, placa, m28, s28, prop,
                     n_sims=N_SIMS, seed=seed, usar_estado28=bool(placa))
    return mu, out


def _fecha_corrida():
    """La fecha del ultimo hecho observado que entra al modelo, no la de hoy.
    Es lo que fecha el pronostico: dos corridas sobre los mismos datos dicen lo
    mismo aunque se hagan en dias distintos.

    Cuenta la ultima gala resuelta y tambien la nominacion de la placa vigente.
    Una placa nueva cambia el pronostico sin que se haya ido nadie, asi que
    fechar solo por galas resueltas dejaba a la pagina diciendo una fecha vieja
    con numeros nuevos."""
    d = json.loads((ROOT / "data" / "galas.json").read_text())
    fechas = [x["fecha"] for x in d["galas"]]
    nom = (d.get("placa_vigente") or {}).get("fecha_nominacion")
    if nom:
        fechas.append(nom)
    return max(fechas)


def main():
    cfg = json.loads((ROOT / "data" / "galas.json").read_text())
    GALA = _ultima_gala_completa(cfg)
    if GALA is None:
        print("sin ninguna gala con reparto completo: no hay nada que explicar")
        return
    rp = fit_psi.ajustar()
    psi = {n: float(rp["psi"][rp["ix"][n]]) for n in fm.VIG}
    se_psi = {n: float(rp["se"][rp["ix"][n]]) for n in fm.VIG}
    prop = fm.propension_nominacion()

    # La misma semilla en las dos: cualquier diferencia que quede es la gala,
    # no el ruido de Monte Carlo.
    SEMILLA = 20260811

    print(f"corriendo CON la gala {GALA}…", flush=True)
    mu_con, con = correr(cfg, psi, se_psi, prop, SEMILLA)

    # "completa: false" saca la gala del ajuste de mu sin tocar nada mas: el
    # eliminado ya esta fuera del plantel en las dos corridas, asi que lo unico
    # que cambia es si los porcentajes de esa noche informan el rasgo.
    cfg_sin = copy.deepcopy(cfg)
    for g in cfg_sin["galas"]:
        if g["gala"] == GALA:
            g["completa"] = False
    print(f"corriendo SIN los porcentajes de la gala {GALA}…", flush=True)
    mu_sin, sin = correr(cfg_sin, psi, se_psi, prop, SEMILLA)

    VIG = fm.VIG
    ix = {v: i for i, v in enumerate(VIG)}
    gala_ = next(g for g in cfg["galas"] if g["gala"] == GALA)
    resto = 1 - sum(gala_["salvados_cuota"].values()) / 100
    cuota = dict(gala_["salvados_cuota"])
    for k, v in gala_["versus"].items():
        cuota[k] = round(v * resto, 2)

    filas = []
    for v in VIG:
        i = ix[v]
        filas.append({
            "quien": v,
            "sin_pct": float(sin["p_gana"][i]),      # solo se sabe que salio Hanssen
            "con_pct": float(con["p_gana"][i]),      # ademas se sabe por cuanto
            "delta_pp": round(100 * float(con["p_gana"][i] - sin["p_gana"][i]), 2),
            "mu_sin": round(mu_sin[v], 3),
            "mu_con": round(mu_con[v], 3),
            "d_mu": round(mu_con[v] - mu_sin[v], 3),
            "cuota_gala": cuota.get(v),               # None si no estaba en placa
        })
    filas.sort(key=lambda f: -f["con_pct"])

    salida = {
        "generado": _fecha_corrida(),
        "gala": GALA,
        "n_sims": N_SIMS,
        "semilla": SEMILLA,
        "cuotas": cuota,
        "eliminado": gala_["eliminado"],
        "filas": filas,
        "nota": ("Las dos corridas comparten codigo, plantel, psi, propensiones y "
                 "semilla. La unica diferencia es si los porcentajes de esa gala "
                 "entran al ajuste del rechazo mu. Lo que separa a las dos columnas "
                 "es, por construccion, la informacion que aportaron esos numeros."),
    }
    (ROOT / "data" / "evolucion.json").write_text(json.dumps(salida, ensure_ascii=False))

    print(f"\n{'quien':<11} {'solo salio':>11} {'con las cifras':>15} {'Δ':>7} "
          f"{'Δμ':>7} {'cuota':>7}")
    for f in filas:
        c = f"{f['cuota_gala']:.1f}%" if f["cuota_gala"] is not None else "—"
        print(f"{f['quien']:<11} {100*f['sin_pct']:10.1f}% {100*f['con_pct']:14.1f}% "
              f"{f['delta_pp']:+6.1f} {f['d_mu']:+7.2f} {c:>7}")
    print("\nescrito data/evolucion.json")


if __name__ == "__main__":
    main()
