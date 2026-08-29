# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
EL MANO A MANO, QUE ES OTRO PARTIDO.

Diagnostico primero, porque el modelo de esta pagina falla y falla en un sitio
concreto. Sobre las siete galas del backtest, su favorito a irse:

    llego al mano a mano 4 de 7 veces   (el azar daria 2,3)
    y lo GANO las 4                     (0 de 4 aciertos)

O sea que acertar quien acumula mas rechazo no es el problema. Acumular rechazo
es justamente lo que te LLEVA al mano a mano. Ganarlo es otra cosa, y en los
datos va en la direccion contraria: de las cinco personas que llegaron a mas de
un versus esta temporada, ganaron 10 de 13.

El modelo usa un solo numero, mu, para las dos preguntas. Este archivo agrega el
segundo: una fuerza de mano a mano por persona, estilo Bradley-Terry, ajustada
sobre los versus publicados y usada SOLO en el segundo tiempo.

    P(i pierde contra j) = 1 / (1 + exp(theta_i - theta_j))

Con once versus y catorce personas, la mitad con una sola aparicion, sin castigo
esto se va al infinito: quien gano todas tendria fuerza infinita. Asi que theta
lleva un prior normal centrado en cero y se estima el maximo a posteriori. El
prior es fuerte a proposito: sin datos, todos iguales.

QUE NO ES ESTO. No es invertir mu. Invertir un ranking porque fallo siete veces
es ajustarse a siete puntos y romperse en el octavo. Aca se agrega un parametro
que se estima sobre otros datos -los versus- y que puede salir cero si no hay
senal.

QUE HAY QUE SABER ANTES DE CREERLE. La regularidad tiene una parte tautologica:
solo se acumulan versus ganandolos, asi que "el que gano mas gana" se muerde la
cola. Bradley-Terry lo trata bien en principio, pero el n es minusculo. Por eso
esto se publica AL LADO del modelo y no en su lugar, y las dos predicciones se
congelan antes de cada gala para que EVALUACION.md las puntue por separado.

    python3 model/versus.py              ajusta, valida y escribe data/versus.json
    python3 model/versus.py --backtest   solo la validacion, sin escribir
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# LO QUE HAY QUE SUPONER.
# ---------------------------------------------------------------------------

# Cuanto se deja mover theta desde cero. Es la desviacion del prior, en unidades
# de logit. 1,0 quiere decir que a priori una diferencia de fuerza de un logit
# (73% contra 27%) es una desviacion tipica: generosa pero no infinita. Bajarlo
# acerca todo a la moneda; subirlo deja que cuatro victorias valgan una certeza.
SIGMA = 1.0
# El piso que se le pone a una probabilidad cero antes de tomarle el logaritmo.
# Tiene que ser el mismo que usa model/retro.py: ver el comentario de abajo.
PISO_CERO = 1e-4

N_SIMS = 200_000
SEMILLA = 20260818


def _leer(n):
    return json.loads((ROOT / "data" / n).read_text())


def versus_historicos(hasta_fecha=None):
    """Los mano a mano publicados. Cada uno: (sobrevive, sale, cuota_del_que_sale)."""
    out = []
    for g in sorted(_leer("galas.json")["galas"], key=lambda x: x["fecha"]):
        v = g.get("versus") or {}
        if len(v) != 2:
            continue
        if hasta_fecha and g["fecha"] >= hasta_fecha:
            continue
        (a, pa), (b, pb) = sorted(v.items(), key=lambda kv: kv[1])
        out.append({"gala": g.get("gala"), "fecha": g["fecha"],
                    "gana": a, "pierde": b, "cuota": pb})
    return out


def ajustar_theta(vs, sigma=SIGMA):
    """Bradley-Terry con prior normal. Maximo a posteriori por Newton amortiguado.

    theta alto = dificil de sacar en un mano a mano. El prior evita que quien
    gano todas se vaya al infinito, que es lo que pasa con n chico.
    """
    nombres = sorted({x["gana"] for x in vs} | {x["pierde"] for x in vs})
    if not nombres:
        return {}, nombres
    ix = {n: i for i, n in enumerate(nombres)}
    th = np.zeros(len(nombres))
    for _ in range(200):
        grad = -th / sigma**2
        hess = -np.eye(len(nombres)) / sigma**2
        for x in vs:
            i, j = ix[x["gana"]], ix[x["pierde"]]
            p = 1.0 / (1.0 + math.exp(-(th[i] - th[j])))   # prob de que gane i
            grad[i] += 1 - p
            grad[j] -= 1 - p
            w = p * (1 - p)
            hess[i, i] -= w; hess[j, j] -= w
            hess[i, j] += w; hess[j, i] += w
        paso = np.linalg.solve(hess, grad)
        th -= paso
        if np.max(np.abs(paso)) < 1e-9:
            break
    th -= th.mean()          # la escala es relativa: se centra
    return {n: float(th[ix[n]]) for n in nombres}, nombres


def p_pierde(a, b, theta):
    """Probabilidad de que a pierda el mano a mano contra b."""
    ta, tb = theta.get(a, 0.0), theta.get(b, 0.0)
    return 1.0 / (1.0 + math.exp(ta - tb))


def dos_tiempos(pesos, theta, n_sims=N_SIMS, semilla=SEMILLA):
    """La placa resuelta como lo que es: primero se salvan, despues el versus.

    `pesos` es la fuerza de rechazo relativa de cada nominada, que es de donde
    sale el orden en que se salvan. Se muestrea un orden de Plackett-Luce sobre
    esos pesos: se salva primero la menos rechazada. Las dos ultimas van al mano
    a mano, y ahi decide theta, no el rechazo.
    """
    nombres = list(pesos)
    w = np.array([max(pesos[n], 1e-9) for n in nombres], dtype=float)
    if len(nombres) < 2:
        return {n: 1.0 for n in nombres}
    rng = np.random.default_rng(semilla)
    cuenta = np.zeros(len(nombres))
    # Plackett-Luce por Gumbel: ordenar por log(w) + Gumbel da exactamente el
    # muestreo secuencial sin reemplazo, y de una sola vez.
    lw = np.log(w)
    for _ in range(0, n_sims, 20_000):
        lote = min(20_000, n_sims)
        g = rng.gumbel(size=(lote, len(nombres)))
        orden = np.argsort(-(lw + g), axis=1)      # el mas rechazado primero
        pares = orden[:, :2]                       # los dos que no se salvan
        for i, j in pares:
            a, b = nombres[i], nombres[j]
            cuenta[i if rng.random() < p_pierde(a, b, theta) else j] += 1
    return {n: float(cuenta[i] / cuenta.sum()) for i, n in enumerate(nombres)}


def _versus_de(gala):
    """Los dos nombres del mano a mano de esa gala, si lo hubo."""
    for g in _leer("galas.json").get("galas", []):
        if g.get("gala") == gala:
            return list((g.get("versus") or {}).keys())
    return []


def backtest():
    """Las mismas siete galas del backtest del modelo, con los dos tiempos.

    Para cada gala se usan SOLO los versus anteriores a esa fecha, igual que
    retro.py usa solo las galas anteriores para mu. Los pesos de rechazo se
    toman de retro.json, que ya los guardo por gala: asi la unica diferencia
    entre las dos columnas es el segundo tiempo.
    """
    retro = _leer("retro.json")
    filas = []
    for f in retro["filas"]:
        pesos = {o["quien"]: o["p"] for o in f["orden"]}
        vs_previos = versus_historicos(hasta_fecha=f["fecha"])
        theta, _ = ajustar_theta(vs_previos)
        p2 = dos_tiempos(pesos, theta)
        orden2 = sorted(p2, key=lambda n: -p2[n])
        salio = f["eliminado"]
        # A quien senalaba el modelo, y que le paso en el mano a mano de esa
        # noche. Se guarda porque la pagina lo afirmaba en una frase escrita a
        # mano — «llego al mano a mano cuatro veces y lo gano las cuatro» — que
        # dejaba de ser cierta cada vez que se jugaba una gala mas, sin que
        # nada se enterara. Es el hallazgo central de la variante de dos
        # tiempos: si tiene que salir de algun lado, que salga de los datos.
        favorito = max(pesos, key=pesos.get) if pesos else None
        par = _versus_de(f["gala"])
        filas.append({
            "gala": f["gala"], "fecha": f["fecha"], "eliminado": salio,
            "n_placa": f["n_placa"], "versus_previos": len(vs_previos),
            "modelo_favorito": favorito,
            "favorito_al_versus": bool(par and favorito in par),
            "favorito_gano_versus": bool(par and favorito in par and favorito != salio),
            "modelo_puesto": f["puesto_del_modelo"], "modelo_p": f["p_modelo"],
            "dos_tiempos_puesto": orden2.index(salio) + 1,
            "dos_tiempos_p": round(p2[salio], 4),
            "theta_usado": {n: round(v, 3) for n, v in theta.items() if n in pesos},
        })
    return filas


def _resumen(filas):
    import statistics as st
    def brier(p, n):
        return (1 - p) ** 2 + (n - 1) * (p / max(n - 1, 1)) ** 2   # aproximacion grosera
    m = {
        "n": len(filas),
        "modelo_aciertos": sum(1 for f in filas if f["modelo_puesto"] == 1),
        "dos_tiempos_aciertos": sum(1 for f in filas if f["dos_tiempos_puesto"] == 1),
        "modelo_puesto_medio": round(st.mean(f["modelo_puesto"] for f in filas), 2),
        "dos_tiempos_puesto_medio": round(st.mean(f["dos_tiempos_puesto"] for f in filas), 2),
        "azar_puesto_medio": round(st.mean((f["n_placa"] + 1) / 2 for f in filas), 2),
        # PISO_CERO y no 1e-6: en la gala 23 el modelo le dio probabilidad cero
        # al que salio, y el piso que se le ponga a ese cero decide el numero.
        # Con 1e-6 aca y 1e-4 en model/retro.py, el MISMO modelo sobre la MISMA
        # serie publicaba dos log-verosimilitudes distintas —4,434 y 3,776— y
        # con tres series publicadas eso es la puerta abierta a citar el piso
        # que convenga. Un solo piso, fijado en EVALUACION.md.
        "modelo_logver": round(st.mean(math.log(max(f["modelo_p"], PISO_CERO)) for f in filas), 3),
        "dos_tiempos_logver": round(
            st.mean(math.log(max(f["dos_tiempos_p"], PISO_CERO)) for f in filas), 3),
        "azar_logver": round(st.mean(math.log(1 / f["n_placa"]) for f in filas), 3),
    }
    return m


def main():
    ap = argparse.ArgumentParser(description="El mano a mano como partido aparte")
    ap.add_argument("--backtest", action="store_true", help="solo validar")
    a = ap.parse_args()

    vs = versus_historicos()
    theta, nombres = ajustar_theta(vs)
    print(f"{len(vs)} mano a mano publicados · {len(nombres)} personas · sigma {SIGMA}")
    print(f"\n{'quien':<12} {'theta':>7} {'gana':>5} {'pierde':>7}   lectura")
    rec = {n: [0, 0] for n in nombres}
    for x in vs:
        rec[x["gana"]][0] += 1
        rec[x["pierde"]][1] += 1
    for n in sorted(nombres, key=lambda x: -theta[x]):
        w, l = rec[n]
        lect = ("muy dificil de sacar" if theta[n] > 0.6 else
                "dificil" if theta[n] > 0.2 else
                "sin senal" if abs(theta[n]) <= 0.2 else
                "facil" if theta[n] > -0.6 else "muy facil de sacar")
        print(f"{n:<12} {theta[n]:>7.2f} {w:>5} {l:>7}   {lect}")

    filas = backtest()
    res = _resumen(filas)
    print(f"\n{'gala':>5} {'salió':<11} {'n':>2} {'vs previos':>11} "
          f"{'modelo':>8} {'dos tiempos':>13}")
    for f in filas:
        print(f"{f['gala']:>5} {f['eliminado']:<11} {f['n_placa']:>2} {f['versus_previos']:>11} "
              f"{f['modelo_puesto']:>4} ({100*f['modelo_p']:4.1f}%) "
              f"{f['dos_tiempos_puesto']:>6} ({100*f['dos_tiempos_p']:4.1f}%)")
    print(f"\n{'':<22}{'modelo':>10}{'dos tiempos':>14}{'azar':>10}")
    print(f"{'aciertos':<22}{res['modelo_aciertos']:>10}{res['dos_tiempos_aciertos']:>14}"
          f"{'—':>10}")
    print(f"{'puesto medio':<22}{res['modelo_puesto_medio']:>10}"
          f"{res['dos_tiempos_puesto_medio']:>14}{res['azar_puesto_medio']:>10}")
    print(f"{'log-verosimilitud':<22}{res['modelo_logver']:>10}"
          f"{res['dos_tiempos_logver']:>14}{res['azar_logver']:>10}")

    if a.backtest:
        return

    galas = _leer("galas.json")
    placa = (galas.get("placa_vigente") or {}).get("integrantes") or []
    vigente = None
    if placa:
        ramas = _leer("ramas.json")
        pesos = {n: ramas["ramas"][n]["p_sale"] for n in placa if n in ramas["ramas"]}
        if pesos:
            p2 = dos_tiempos(pesos, theta)
            vigente = {"placa": placa, "p_sale": {n: round(v, 4) for n, v in
                       sorted(p2.items(), key=lambda kv: -kv[1])}}

    # La prediccion vigente queda congelada ANTES de la gala, igual que la del
    # modelo y la apuesta: es la unica forma de que el puntaje del martes
    # signifique algo. Una entrada por corrida, sin reescribir nunca.
    if vigente:
        ph = ROOT / "data" / "historial_pronostico.json"
        H = json.loads(ph.read_text())
        reg = H.setdefault("predicciones_dos_tiempos", [])
        pv = galas.get("placa_vigente") or {}
        entrada = {"gala": pv.get("gala"), "fecha_gala": pv.get("fecha"),
                   "corrida": _leer("ramas.json")["generado"],
                   "placa": vigente["placa"], "p_sale": vigente["p_sale"],
                   "sigma_prior": SIGMA, "n_versus": len(vs)}
        if not reg or reg[-1].get("p_sale") != entrada["p_sale"]:
            reg.append(entrada)
            H.setdefault("_nota_dos_tiempos", (
                "La variante del mano a mano, congelada antes de cada gala como las "
                "otras dos. Cada entrada lleva el prior y cuantos versus habia."))
            ph.write_text(json.dumps(H, ensure_ascii=False, indent=1))
            print(f"congelada la prediccion de dos tiempos de la gala {entrada['gala']}")

    salida = {
        "generado": _leer("ramas.json")["generado"],
        "que_es": ("Un segundo parámetro para el segundo tiempo de la placa. El modelo usa el "
                   "rechazo para las dos preguntas que tiene una gala, y en la del mano a mano "
                   "va al revés: sobre las siete galas del backtest, su favorito llegó al mano a "
                   "mano cuatro veces y lo ganó las cuatro."),
        "supuestos": {"sigma_prior": SIGMA, "n_sims": N_SIMS, "semilla": SEMILLA},
        "n_versus": len(vs),
        "theta": {n: round(theta[n], 3) for n in sorted(theta, key=lambda x: -theta[x])},
        "registro": {n: rec[n] for n in sorted(rec, key=lambda x: -theta[x])},
        "backtest": {"filas": filas, "resumen": res},
        "vigente": vigente,
        "aviso": ("La regularidad tiene una parte que se muerde la cola: sólo se acumulan versus "
                  "ganándolos. Y el n es minúsculo. Por eso esto se publica al lado del modelo y "
                  "no en su lugar, y las dos quedan congeladas antes de cada gala."),
    }
    (ROOT / "data" / "versus.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1))
    print("\nescrito data/versus.json")


if __name__ == "__main__":
    main()
