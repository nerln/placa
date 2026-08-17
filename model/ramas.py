# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
LAS RAMAS - que pasa con el pronostico segun quien salga esta noche.

El pronostico de una linea ("Tamara 22,4%") promedia sobre todos los futuros
posibles, y eso esconde justo lo que la gente quiere saber sentada en el sofa:
que cambia si esta noche sale ella, o si sale la otra.

Aca eso no se estima aparte ni se vuelve a simular. Es la MISMA corrida de Monte
Carlo del modelo final, guardando ademas quien se fue en la primera eliminacion
de cada simulacion. Con el conjunto y el ganador de cada corrida basta para leer
la conjunta:

    P(gana i | sale j en la gala 28) = corridas donde sale j y gana i
                                       -------------------------------
                                            corridas donde sale j

Que sea condicional sobre la misma corrida y no una simulacion nueva importa:
las ramas suman exactamente al caso base, sin ruido de por medio. Lo unico que
hay que vigilar es el n efectivo de la rama menos probable, que se declara.

    python3 model/ramas.py       ->  data/ramas.json
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

N_SIMS = 400_000            # cinco veces la corrida base: la rama mas fina de la
                            # placa se queda si no en unos pocos miles de casos


def simular_conjunta(mu, se_mu, omega, psi, se_psi, placa28, m28, s28, prop,
                     n_sims=N_SIMS, kappa=0.0, sigma_psi_sem=0.20, beta_mu=0.85,
                     beta_sd=0.30, p3=0.70, semanas_a_final=4.0, seed=20260810,
                     usar_estado28=True):
    """Igual que final_model.simular, pero devolviendo la conjunta (sale, gana).

    Entre la gala del lunes y la nominacion del miercoles no hay placa, y
    entonces la primera eliminacion se sortea por propension como todas las
    demas. Las ramas siguen teniendo sentido: son "si la proxima en irse es
    esta, como queda la carrera", solo que ahora quien se va puede ser
    cualquiera y no solo una de las seis nominadas."""
    rng = np.random.default_rng(seed)
    VIG = fm.VIG
    K = len(VIG)
    ix = {n: i for i, n in enumerate(VIG)}
    MU = np.array([mu[n] for n in VIG]); SE = np.array([se_mu[n] for n in VIG])
    PS = np.array([psi[n] for n in VIG]); SP = np.array([se_psi[n] for n in VIG])
    PR = np.array([prop[n] for n in VIG])
    p28 = [ix[n] for n in placa28]

    conj_gana = np.zeros((K, K))      # [sale, gana]
    conj_final = np.zeros((K, K))     # [sale, llega a la final]
    sale = np.zeros(K)

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
        primero = -1
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
                sale[fuera] += 1
            paso += 1

        for i in vivos:
            conj_final[primero, i] += 1

        score = ps - kappa * m
        f = list(vivos)
        while len(f) > 1:
            sc = score[f]
            pv = np.exp(bet * (sc - sc.max())); pv /= pv.sum()
            f.pop(fm._elegir(1 / np.maximum(pv, 1e-12), rng.random()))
        conj_gana[primero, f[0]] += 1

    return conj_gana, conj_final, sale, n_sims


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


def congelar_prediccion(salida, placa_vigente):
    """Guarda la prediccion de eliminacion ANTES de que se juegue la gala.

    EVALUACION.md puntua la pregunta «quien se va en cada gala» con Brier, y
    solo cuenta lo que estaba publicado antes del hecho. Pero la distribucion
    vivia unicamente en data/ramas.json, que cada corrida sobrescribe: despues
    de la gala ya no habia con que puntuar. Esto la deja escrita en el registro
    append-only, con fecha y con la placa que habia en ese momento.

    Se guarda una entrada por corrida, no una por gala. Si una corrida repite
    exactamente lo mismo que la anterior no se anota de nuevo, para que
    reconstruir la web varias veces el mismo dia no ensucie el registro. Lo que
    no se hace nunca es reescribir una entrada vieja: la gracia es justamente
    que quede lo que se dijo, aunque despues cambie.
    """
    if not salida["hay_placa"]:
        return
    ph = ROOT / "data" / "historial_pronostico.json"
    H = json.loads(ph.read_text())
    reg = H.setdefault("predicciones_gala", [])
    dist = {k: round(v["p_sale"], 6) for k, v in salida["ramas"].items()}
    entrada = {
        "gala": placa_vigente.get("gala"),
        "fecha_gala": placa_vigente.get("fecha"),
        "corrida": salida["generado"],
        "placa": salida["placa"],
        "p_sale": dist,
        "n_sims": salida["n_sims"],
    }
    if reg and all(reg[-1].get(k) == entrada[k] for k in ("gala", "corrida", "p_sale")):
        return
    reg.append(entrada)
    H.setdefault("_nota_predicciones", (
        "Append-only, y a proposito: es la promesa que despues hay que puntuar. "
        "Cada entrada es la distribucion de quien se va que la pagina publicaba "
        "antes de esa gala. No se reescribe ninguna aunque la corrida siguiente "
        "diga otra cosa."))
    ph.write_text(json.dumps(H, ensure_ascii=False, indent=1))
    print(f"registrada la prediccion de la gala {entrada['gala']} "
          f"({len(reg)} en el registro)")


def main():
    cfg, mu, se, omega, var_true, nobs = fm.escala_rechazo()
    placa28, m28, s28, *_ = fm.estado_28(mu, se, omega, cfg)
    rp = fit_psi.ajustar()
    psi = {n: float(rp["psi"][rp["ix"][n]]) for n in fm.VIG}
    se_psi = {n: float(rp["se"][rp["ix"][n]]) for n in fm.VIG}
    prop = fm.propension_nominacion()

    hay_placa = bool(placa28)
    print(f"placa: {', '.join(placa28) if hay_placa else 'sin definir todavia'}")
    print(f"simulando {N_SIMS:,} temporadas…", flush=True)
    cg, cf, sale, n = simular_conjunta(mu, se, omega, psi, se_psi,
                                       placa28, m28, s28, prop,
                                       usar_estado28=hay_placa)

    VIG = fm.VIG
    ix = {v: i for i, v in enumerate(VIG)}
    base_gana = cg.sum(0) / n
    base_final = cf.sum(0) / n

    # Con placa, una rama por nominada. Sin placa, una por cada una que tenga
    # posibilidad real de irse: por debajo del 1,5% la rama se apoya en tan
    # pocas corridas que su reordenamiento es ruido.
    if hay_placa:
        candidatas = list(placa28)
    else:
        candidatas = [v for v in VIG if sale[ix[v]] / n >= 0.015]
        candidatas.sort(key=lambda v: -sale[ix[v]])

    ramas = {}
    for nombre in candidatas:
        j = ix[nombre]
        nj = sale[j]
        if nj < 1:
            continue
        ramas[nombre] = {
            "p_sale": float(nj / n),
            "n_efectivo": int(nj),
            # el que sale ya no puede ganar: su fila vale 0 para el mismo
            "p_gana": {v: float(cg[j, ix[v]] / nj) for v in VIG},
            "p_final": {v: float(cf[j, ix[v]] / nj) for v in VIG},
        }

    # quien se beneficia mas de cada salida, en puntos porcentuales
    for nombre, r in ramas.items():
        delta = {v: r["p_gana"][v] - float(base_gana[ix[v]]) for v in VIG if v != nombre}
        orden = sorted(delta.items(), key=lambda kv: -kv[1])
        r["mas_gana"] = [{"quien": k, "delta_pp": round(100 * v, 2)} for k, v in orden[:3]]
        r["mas_pierde"] = [{"quien": k, "delta_pp": round(100 * v, 2)} for k, v in orden[-2:]]

    salida = {
        "generado": _fecha_corrida(),
        "n_sims": n,
        "hay_placa": hay_placa,
        "placa": placa28,
        "candidatas": candidatas,
        "jugadores": VIG,
        "base": {"p_gana": {v: float(base_gana[ix[v]]) for v in VIG},
                 "p_final": {v: float(base_final[ix[v]]) for v in VIG}},
        "ramas": ramas,
        "nota": ("Cada rama es el subconjunto de las mismas simulaciones en que esa "
                 "persona es la proxima en irse, asi que las ramas ponderadas por su "
                 "probabilidad devuelven exactamente el caso base."),
    }
    (ROOT / "data" / "ramas.json").write_text(json.dumps(salida, ensure_ascii=False))
    congelar_prediccion(salida, cfg.get("placa_vigente") or {})

    print(f"\n{'quien sale':<12} {'prob':>7} {'n':>8}   quien mas gana con esa salida")
    for nombre in sorted(ramas, key=lambda x: -ramas[x]["p_sale"]):
        r = ramas[nombre]
        top = " · ".join(f"{d['quien']} {d['delta_pp']:+.1f}" for d in r["mas_gana"][:2])
        print(f"{nombre:<12} {100*r['p_sale']:6.1f}% {r['n_efectivo']:8,}   {top}")
    print(f"\nescrito data/ramas.json · rama mas fina: "
          f"{min(r['n_efectivo'] for r in ramas.values()):,} corridas")


if __name__ == "__main__":
    main()
