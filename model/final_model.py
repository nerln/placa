# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
MODELO FINAL - Gran Hermano Argentina: Generacion Dorada 2026.
Probabilidad de ganar por participante. Corrida del 08/08/2026.

Dos escalas latentes, estimadas por separado de datos oficiales de votacion:

  mu_i   RECHAZO. Logit condicional sobre las 8 galas de voto negativo cuya
         aritmetica prueba que la placa esta completa. Descomposicion de
         varianza: 52% rasgo estable, 48% ruido semanal (omega = 1,75 logits).
         Decide QUIEN SOBREVIVE cada semana.

  psi_i  APOYO POSITIVO. Plackett-Luce sobre las 12 instancias de voto positivo
         de la temporada, incluido el ranking COMPLETO de 16 del 16/07.
         Decide QUIEN GANA LA FINAL.

Las dos escalas son casi ortogonales: es el hallazgo central de la calibracion
sobre GH 2024-2025. Nicolas Grosman llego a la final de 2024 con el mismo
rechazo nulo que el campeon y saco 2%; Juliana "Furia", la mas rechazada, fue la
mas votada en positivo. Por eso el modelo NO usa el rechazo para predecir la
final (kappa = 0 en el caso base) y lo reporta como sensibilidad.

La encuesta de Fefe Bongiorno entra como observacion calibrada del estado de la
gala 28: su puesto 1 se mide con sesgo -0,25 y desvio 0,53 logits contra
resultados oficiales; sus puestos 2+ con desvio 1,6 y sesgo positivo (aplasta la
concentracion real del voto).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "model"))

from variance_components import ajustar as vc_ajustar      # noqa: E402
from calibrar_encuesta import calibrar                     # noqa: E402
import fit_psi                                             # noqa: E402

PLANTEL = json.loads((ROOT / "data" / "plantel.json").read_text())
VIG = [j["apodo"] for j in PLANTEL["jugadores"]]

# Propension a caer en placa: frecuencia de placas desde el 01/06 y puntos de
# nominacion interna recibidos en las ultimas 4 galas, ambos estandarizados. El
# canal "fulminante" va aparte porque no pasa por el voto de la casa: Charlotte
# cayo en placa 2 de 2 veces por fulminante, y a Zilli la fulmino una visitante.
# Todo esto vive en data/plantel.json para que model/actualizar.py lo edite sin
# tocar el codigo.
PLACAS_DESDE_JUNIO = {j["apodo"]: j["placas_recientes"] for j in PLANTEL["jugadores"]}
VOTOS_RECIENTES = {j["apodo"]: j["votos_recientes"] for j in PLANTEL["jugadores"]}
BONO_FULMINANTE = {j["apodo"]: j.get("bono_fulminante", 0.0) for j in PLANTEL["jugadores"]}


def z(d):
    v = np.array([d[k] for k in VIG], float)
    return {k: float((d[k] - v.mean()) / v.std()) for k in VIG}


def propension_nominacion():
    a, b = z(PLACAS_DESDE_JUNIO), z(VOTOS_RECIENTES)
    return {k: 0.5 * a[k] + 0.5 * b[k] + BONO_FULMINANTE.get(k, 0.0) for k in VIG}


# ---------------------------------------------------------------------------

def escala_rechazo():
    cfg = json.loads((ROOT / "data" / "galas.json").read_text())
    r = vc_ajustar(cfg)
    om2 = r["omega"] ** 2
    n = np.array([r["n_obs"][j] for j in r["jugadores"]])
    var_true = max(float(np.var(r["mu"], ddof=1)) - om2 * float(np.mean(1 / n)), 1e-3)
    k = var_true / (var_true + om2 / n)
    mu = {j: float(k[i] * r["mu"][i]) for i, j in enumerate(r["jugadores"])}
    se = {j: float(np.sqrt(var_true * (1 - k[i]))) for i, j in enumerate(r["jugadores"])}
    nobs = {j: int(r["n_obs"].get(j, 0)) for j in VIG}
    for j in VIG:
        if j not in mu:                        # sin observaciones: prior puro
            mu[j], se[j] = 0.0, float(np.sqrt(var_true))
    return cfg, mu, se, float(r["omega"]), var_true, nobs


def estado_28(mu, se, omega, cfg):
    """Posterior del estado s = mu + eps para la gala del 10/08."""
    _, errores, aciertos = calibrar(cfg)
    arr = np.array(errores)
    bias = {rk: float(arr[arr[:, 0] == rk][:, 1].mean()) for rk in (1, 2)}
    sdv = {rk: float(arr[arr[:, 0] == rk][:, 1].std(ddof=1)) for rk in (1, 2)}
    bajos = arr[arr[:, 0] >= 3][:, 1]
    bias[3], sdv[3] = float(bajos.mean()), float(bajos.std(ddof=1))

    e = json.loads((ROOT / "data" / "encuestas.json").read_text())["proxima"]
    placa = cfg["placa_vigente"]["integrantes"]

    # Sin placa definida (entre la gala y la nominacion) no hay nada observado
    # sobre quien esta en riesgo: la proxima eliminacion se simula como todas
    # las demas, sorteando la placa por propension.
    if not placa:
        # bias y sdv son la calibracion historica del agregador y NO dependen de
        # que haya encuesta esta semana: devolverlos vacios rompia la tabla de
        # calibracion de la pagina, que es informacion valida igual.
        return [], np.array([]), np.array([]), bias, sdv, (sum(aciertos), len(aciertos))

    # Sin encuesta para la proxima gala, el estado es el prior puro: rasgo
    # estimado mas el ruido semanal. Es el caso normal cuando nadie publica una
    # medicion, y el modelo tiene que poder correr igual.
    if not e.get("cuota"):
        pri = np.array([mu[p] for p in placa]); pri = pri - pri.mean()
        sd = np.array([np.sqrt(se[p] ** 2 + omega ** 2) for p in placa])
        return placa, pri, sd, bias, sdv, (sum(aciertos), len(aciertos))

    pct = dict(e["cuota"])
    for m in e["resto_miembros"]:
        pct[m] = e["resto_agregado"] / len(e["resto_miembros"])

    pri_m = np.array([mu[p] for p in placa]); pri_m = pri_m - pri_m.mean()
    pri_v = np.array([se[p] ** 2 + omega ** 2 for p in placa])
    v = np.array([pct[p] for p in placa], float)
    l = np.log(v); l = l - l.mean()
    rk = np.argsort(np.argsort(-v)) + 1
    obs = l - np.array([bias[min(r, 3)] for r in rk])
    ov = np.array([sdv[min(r, 3)] ** 2 for r in rk])

    prec = 1 / pri_v + 1 / ov
    m28 = (pri_m / pri_v + obs / ov) / prec
    m28 = m28 - m28.mean()
    return placa, m28, np.sqrt(1 / prec), bias, sdv, (sum(aciertos), len(aciertos))


def _elegir(p, u):
    """Muestreo por CDF inversa: mucho mas rapido que rng.choice(p=...)."""
    c = np.cumsum(p)
    return int(np.searchsorted(c, u * c[-1]))


def _topk(logw, k, rng):
    """Top-k sin reemplazo por el truco de Gumbel (equivale a muestreo secuencial)."""
    g = logw - np.log(-np.log(rng.random(len(logw))))
    return np.argpartition(-g, k - 1)[:k]


N_SIMS_BASE = 120_000


def simular(mu, se_mu, omega, psi, se_psi, placa28, m28, s28, prop,
            n_sims=N_SIMS_BASE, kappa=0.0, sigma_psi_sem=0.20, beta_mu=0.85,
            beta_sd=0.30, p3=0.70, semanas_a_final=4.0, seed=20260808,
            usar_estado28=True):
    rng = np.random.default_rng(seed)
    K = len(VIG); ix = {n: i for i, n in enumerate(VIG)}
    MU = np.array([mu[n] for n in VIG]); SE = np.array([se_mu[n] for n in VIG])
    PS = np.array([psi[n] for n in VIG]); SP = np.array([se_psi[n] for n in VIG])
    PR = np.array([prop[n] for n in VIG])
    p28 = [ix[n] for n in placa28]

    gana = np.zeros(K); fin = np.zeros(K); sale28 = np.zeros(K); podio = np.zeros(K)
    lotes = []; n_lotes = 25; por = max(n_sims // n_lotes, 1)

    for _ in range(n_lotes):
        wl = np.zeros(K)
        for _ in range(por):
            m = MU + SE * rng.standard_normal(K)
            # el estado observado de la gala 28 informa tambien el rasgo de largo plazo
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

            vivos = list(range(K)); paso = 0
            while len(vivos) > n_fin:
                if paso == 0 and usar_estado28:
                    placa = list(p28); st = s[placa]
                else:
                    lider = vivos[int(rng.random() * len(vivos))]
                    cand = [i for i in vivos if i != lider]
                    tam = max(3, min(len(cand), int(round(0.62 * len(cand)))))
                    sel = _topk(PR[cand], tam, rng)
                    placa = [cand[j] for j in sel]
                    st = m[placa] + omega * rng.standard_normal(tam)
                p = np.exp(st - st.max())
                fuera = placa[_elegir(p, rng.random())]
                vivos.remove(fuera)
                if paso == 0:
                    sale28[fuera] += 1
                paso += 1

            for i in vivos:
                fin[i] += 1
            score = ps - kappa * m
            f = list(vivos)
            while len(f) > 1:
                if len(f) == 3:
                    for i in f:
                        podio[i] += 1
                sc = score[f]
                pv = np.exp(bet * (sc - sc.max())); pv /= pv.sum()
                f.pop(_elegir(1 / np.maximum(pv, 1e-12), rng.random()))
            gana[f[0]] += 1; wl[f[0]] += 1
        lotes.append(wl / por)

    tot = n_lotes * por; L = np.array(lotes)
    return {"p_gana": gana / tot, "p_final": fin / tot, "p_podio": podio / tot,
            "p_sale28": sale28 / tot,
            "ic": np.stack([np.percentile(L, 5, 0), np.percentile(L, 95, 0)], 1)}


def _fecha_corrida():
    """La fecha de la ultima gala cargada, no la de hoy ni una escrita a mano.
    Es lo que fecha el pronostico: dos corridas sobre los mismos datos dicen lo
    mismo aunque se hagan en dias distintos."""
    g = json.loads((ROOT / "data" / "galas.json").read_text())["galas"]
    return max(x["fecha"] for x in g)


def main():
    cfg, mu, se, omega, var_true, nobs = escala_rechazo()
    placa28, m28, s28, bias, sdv, aciertos = estado_28(mu, se, omega, cfg)
    rp = fit_psi.ajustar()
    psi = {n: float(rp["psi"][rp["ix"][n]]) for n in VIG}
    se_psi = {n: float(rp["se"][rp["ix"][n]]) for n in VIG}
    fases_psi = {n: int(rp["apariciones"].get(n, 0)) for n in VIG}
    prop = propension_nominacion()

    hay_placa = bool(placa28)
    if not hay_placa:
        print("sin placa observada: la proxima gala se sortea por propension")
    base = simular(mu, se, omega, psi, se_psi, placa28, m28, s28, prop,
                   usar_estado28=hay_placa)

    esc = {"base": base}
    esc["sin_encuesta"] = simular(
        mu, se, omega, psi, se_psi, placa28,
        (np.array([mu[p] for p in placa28]) - np.mean([mu[p] for p in placa28]))
        if hay_placa else m28,
        np.array([np.sqrt(se[p] ** 2 + omega ** 2) for p in placa28])
        if hay_placa else s28,
        prop, usar_estado28=hay_placa)
    esc["psi_plano"] = simular(mu, se, omega, {n: 0.0 for n in VIG},
                               {n: 0.5 for n in VIG}, placa28, m28, s28, prop, usar_estado28=hay_placa)
    esc["kappa_0.4"] = simular(mu, se, omega, psi, se_psi, placa28, m28, s28, prop, usar_estado28=hay_placa, kappa=0.4)
    esc["kappa_-0.4"] = simular(mu, se, omega, psi, se_psi, placa28, m28, s28, prop, usar_estado28=hay_placa, kappa=-0.4)
    esc["4_finalistas"] = simular(mu, se, omega, psi, se_psi, placa28, m28, s28, prop, usar_estado28=hay_placa, p3=0.0)
    esc["beta_alto"] = simular(mu, se, omega, psi, se_psi, placa28, m28, s28, prop, usar_estado28=hay_placa, beta_mu=1.5)
    esc["beta_bajo"] = simular(mu, se, omega, psi, se_psi, placa28, m28, s28, prop, usar_estado28=hay_placa, beta_mu=0.45)
    esc["deriva_alta"] = simular(mu, se, omega, psi, se_psi, placa28, m28, s28, prop, usar_estado28=hay_placa, sigma_psi_sem=0.45)

    # Tasa base de nacionalidad: los DOS ultimos campeones de GH Argentina fueron
    # uruguayos (Bautista Mascia 2024, 56,2%; Tato Algorta 2025, 62,8%), sobre 13
    # ediciones y 2 finalistas uruguayos de 2. Mecanismo documentado: el voto es
    # pago y sin tope, o sea que mide gasto y no censo, y Uruguay tiene canal
    # propio en simultaneo desde 2022. Contras: n=2, ambos comparten el arquetipo
    # "outsider simpatico", y el 48,2% -> 62,8% de Tato muestra arrastre argentino
    # y no un bloque uruguayo cerrado. Se aplica como ajuste MODESTO y etiquetado,
    # no como parte del caso base. Chile entra por primera vez esta edicion y sin
    # historial, con senales de fandom dividido, asi que su ajuste es menor.
    psi_nac = dict(psi); psi_nac["Yipio"] += 0.45; psi_nac["Pincoya"] += 0.25
    se_nac = dict(se_psi); se_nac["Yipio"] = (se_psi["Yipio"] ** 2 + 0.35 ** 2) ** .5
    se_nac["Pincoya"] = (se_psi["Pincoya"] ** 2 + 0.40 ** 2) ** .5
    esc["base_rate_extranjeras"] = simular(mu, se, omega, psi_nac, se_nac,
                                           placa28, m28, s28, prop, usar_estado28=hay_placa)

    out = {
        "generado": _fecha_corrida(),
        # n_sims se publica en vez de quedar solo en la firma de simular():
        # la pagina lo dice en dos sitios y la animacion en otro, y escrito tres
        # veces a mano es cuestion de tiempo que uno de los tres mienta.
        "meta": {"n_sims": N_SIMS_BASE, "omega": omega, "var_rasgo": var_true,
                 "icc_estable": var_true / (var_true + omega ** 2),
                 "encuesta_sesgo": bias, "encuesta_desvio": sdv,
                 "encuesta_aciertos_puesto1": list(aciertos),
                 "corr_mu_psi": float(np.corrcoef([mu[n] for n in VIG],
                                                  [psi[n] for n in VIG])[0, 1])},
        "jugadores": VIG,
        "mu": mu and {n: mu[n] for n in VIG}, "se_mu": {n: se[n] for n in VIG},
        "n_galas_negativas": nobs,
        "psi": psi, "se_psi": se_psi, "fases_psi": fases_psi,
        "propension_nominacion": prop,
        "placa28": placa28,
        "estado28": {p: [float(m28[i]), float(s28[i])] for i, p in enumerate(placa28)},
        "escenarios": {k: {"p_gana": dict(zip(VIG, map(float, v["p_gana"]))),
                           "p_final": dict(zip(VIG, map(float, v["p_final"]))),
                           "p_podio": dict(zip(VIG, map(float, v["p_podio"]))),
                           "p_sale28": dict(zip(VIG, map(float, v["p_sale28"]))),
                           "ic": {n: [float(a), float(b)] for n, (a, b) in zip(VIG, v["ic"])}}
                       for k, v in esc.items()},
    }
    (ROOT / "data" / "resultados.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))

    # Registro append-only de lo publicado. Sin esto no se puede contrastar
    # despues lo que se dijo con lo que paso, que es la unica forma de saber si
    # el modelo sirve. La clave es la gala, no la fecha: una rama publicada
    # antes de la gala y el caso base posterior comparten dia.
    hp = ROOT / "data" / "historial_pronostico.json"
    reg = json.loads(hp.read_text()) if hp.exists() else {"corridas": []}
    hasta = max(g["gala"] for g in cfg["galas"])
    reg["corridas"] = [c for c in reg["corridas"]
                       if not (c.get("galas_hasta") == hasta and not c.get("rama_de"))]
    reg["corridas"].append({
        "fecha": _fecha_corrida(),
        "galas_hasta": hasta,
        "en_juego": len(VIG),
        "p_gana": {n: round(float(base["p_gana"][i]), 4) for i, n in enumerate(VIG)},
    })
    reg["corridas"].sort(key=lambda c: (c.get("galas_hasta", 0), bool(c.get("rama_de"))))
    hp.write_text(json.dumps(reg, ensure_ascii=False, indent=1))

    print(f"omega={omega:.2f}  ICC estable={100*out['meta']['icc_estable']:.0f}%  "
          f"corr(mu,psi)={out['meta']['corr_mu_psi']:+.2f}  "
          f"encuesta puesto1 {aciertos[0]}/{aciertos[1]}\n")
    print(f"{'jugador':<11}{'mu':>7}{'psi':>7}{'P(gana)':>9}{'IC90':>15}{'P(final)':>10}{'P(sale 10/8)':>13}")
    for i in np.argsort(-base["p_gana"]):
        n = VIG[i]
        print(f"{n:<11}{mu[n]:>7.2f}{psi[n]:>7.2f}{100*base['p_gana'][i]:>8.1f}%"
              f"{100*base['ic'][i,0]:>7.1f}-{100*base['ic'][i,1]:<7.1f}"
              f"{100*base['p_final'][i]:>9.1f}%{100*base['p_sale28'][i]:>12.1f}%")
    print("\n### Conversion: P(gana | llega a la final)")
    for i in np.argsort(-base["p_gana"]):
        n = VIG[i]
        c = base["p_gana"][i] / max(base["p_final"][i], 1e-9)
        print(f"   {n:<11}{100*base['p_final'][i]:>7.1f}% en la final -> {100*c:>5.1f}% de convertir")

    print("\n### Sensibilidad: P(gana) %")
    ks = list(esc)
    print("jugador".ljust(11) + "".join(f"{k:>13}" for k in ks))
    for i in np.argsort(-base["p_gana"]):
        print(VIG[i].ljust(11) + "".join(f"{100*esc[k]['p_gana'][i]:>12.1f}%" for k in ks))


if __name__ == "__main__":
    main()
