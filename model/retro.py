# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
LA PRUEBA HACIA ATRAS: que habria dicho el modelo antes de cada gala.

Un pronostico que solo se mira hacia adelante no se puede juzgar. La forma
honesta de juzgarlo es rehacerlo con los datos que habia ANTES de cada gala ya
jugada y comparar con lo que paso.

POR QUE NO SE PUEDE HACER CON LAS EDICIONES ANTERIORES. Hace falta el reparto
completo de votos de cada gala para estimar el rechazo, y de 2024 y 2025 nadie
lo publico: se cantaron los porcentajes del mano a mano final y poco mas. Sin
ese reparto no hay mu que ajustar, y un "modelo de 2024" seria un modelo con
otros datos al que se le pone el nombre de un modelo. De esas dos temporadas
solo se puede sacar tipologia -quien gana se parece a quien-, que es lo que ya
hace la seccion de analogos.

Con ESTA temporada si se puede, porque el reparto esta publicado. Para cada gala
con datos completos se reajusta el rechazo usando solo las galas anteriores, se
calcula el riesgo de cada nominado, y se anota en que puesto quedo quien
realmente salio. Un modelo que no sirve para nada pondria al eliminado en un
puesto al azar de la placa; uno que sirve lo pone arriba.

    python3 model/retro.py       ->  data/retro.json
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
from variance_components import ajustar as vc_ajustar        # noqa: E402

MIN_GALAS = 3          # con menos de tres galas previas el ajuste no dice nada


def escala_con(cfg, vig):
    """final_model.escala_rechazo sobre un cfg recortado y un plantel dado."""
    r = vc_ajustar(cfg)
    om2 = r["omega"] ** 2
    n = np.array([r["n_obs"][j] for j in r["jugadores"]])
    var_true = max(float(np.var(r["mu"], ddof=1)) - om2 * float(np.mean(1 / n)), 1e-3)
    k = var_true / (var_true + om2 / n)
    mu = {j: float(k[i] * r["mu"][i]) for i, j in enumerate(r["jugadores"])}
    for j in vig:
        mu.setdefault(j, 0.0)
    return mu, float(r["omega"])


def main():
    cfg = json.loads((ROOT / "data" / "galas.json").read_text())
    completas = [g for g in cfg["galas"] if g.get("completa") and g.get("versus")]
    completas.sort(key=lambda g: g["gala"])

    filas = []
    for i, g in enumerate(completas):
        previas = completas[:i]
        if len(previas) < MIN_GALAS:
            continue
        # el mundo tal como era antes de esa noche: solo las galas anteriores
        recorte = copy.deepcopy(cfg)
        recorte["galas"] = [x for x in cfg["galas"] if x["gala"] < g["gala"]]

        placa = list(g["placa"])
        try:
            mu, omega = escala_con(recorte, placa)
        except Exception as e:                      # ajuste degenerado
            filas.append({"gala": g["gala"], "fecha": g["fecha"], "error": type(e).__name__})
            continue

        # El riesgo dentro de esa placa, integrando el shock semanal. Esto es lo
        # que hace el modelo de verdad y no se puede saltear: omega vale casi 2
        # logits, mas que la distancia tipica entre dos mu, asi que un softmax
        # sobre mu a secas da una distribucion mucho mas puntiaguda que la del
        # modelo. Con mu pelado el retro medía una caricatura del modelo:
        # anunciaba 0,98 de probabilidad para una persona y fallaba.
        vals = np.array([mu.get(n, 0.0) for n in placa])
        rng = np.random.default_rng(20260811)
        acum = np.zeros(len(placa))
        for _ in range(20000):
            st = vals + omega * rng.standard_normal(len(placa))
            acum[int(np.argmax(st))] += 1
        p = acum / acum.sum()
        orden = [placa[j] for j in np.argsort(-p)]
        real = g["eliminado"]
        puesto = orden.index(real) + 1 if real in orden else None

        filas.append({
            "gala": g["gala"], "fecha": g["fecha"],
            "n_placa": len(placa), "galas_previas": len(previas),
            "eliminado": real,
            "puesto_del_modelo": puesto,
            "acierto": puesto == 1,
            "p_modelo": round(float(p[placa.index(real)]), 4) if real in placa else None,
            "p_azar": round(1 / len(placa), 4),
            "orden": [{"quien": n, "p": round(float(p[placa.index(n)]), 4)} for n in orden],
        })

    utiles = [f for f in filas if f.get("puesto_del_modelo")]
    aciertos = sum(1 for f in utiles if f["acierto"])
    puesto_medio = float(np.mean([f["puesto_del_modelo"] for f in utiles])) if utiles else None
    azar_medio = float(np.mean([(f["n_placa"] + 1) / 2 for f in utiles])) if utiles else None
    # log-verosimilitud media: cuanta probabilidad le dio al que de verdad salio
    ll = float(np.mean([np.log(max(f["p_modelo"], 1e-4)) for f in utiles])) if utiles else None
    ll_azar = float(np.mean([np.log(f["p_azar"]) for f in utiles])) if utiles else None

    # Con seis galas hay que decir si esto se distingue del azar. Test de
    # permutacion: bajo la hipotesis nula el eliminado ocupa un puesto uniforme
    # dentro de su propia placa, que tienen tamanos distintos.
    rng2 = np.random.default_rng(7)
    tam = [f["n_placa"] for f in utiles]
    nulo = np.array([[rng2.integers(1, t + 1) for t in tam] for _ in range(200_000)]).mean(1)
    p_peor = float((nulo >= puesto_medio).mean()) if utiles else None

    salida = {
        "generado": max(x["fecha"] for x in cfg["galas"]),
        "p_valor": round(p_peor, 4) if p_peor is not None else None,
        "aciertos_esperados_azar": round(sum(1 / t for t in tam), 2) if tam else None,
        "min_galas": MIN_GALAS,
        "n": len(utiles),
        "aciertos": aciertos,
        "puesto_medio": round(puesto_medio, 2) if puesto_medio else None,
        "puesto_medio_azar": round(azar_medio, 2) if azar_medio else None,
        "log_verosimilitud": round(ll, 3) if ll is not None else None,
        "log_verosimilitud_azar": round(ll_azar, 3) if ll_azar is not None else None,
        "filas": filas,
        "por_que_no_hay_ediciones_anteriores": (
            "Hace falta el reparto completo de votos de cada gala para estimar el rechazo, y de "
            "2024 y 2025 nadie lo publicó: se cantaron los porcentajes del mano a mano final y "
            "poco más. Sin ese reparto no hay μ que ajustar. De esas dos temporadas solo se "
            "puede sacar tipología, que es lo que hace la sección de analogías."),
        "nota": ("Cada gala se predice reajustando el rechazo SOLO con las galas anteriores. El "
                 "puesto es la posición que el modelo le daba dentro de esa placa a quien "
                 "realmente salió; el azar daría (n+1)/2."),
    }
    (ROOT / "data" / "retro.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1))

    print(f"{len(utiles)} galas evaluadas (con al menos {MIN_GALAS} previas)\n")
    print(f"{'gala':>5} {'fecha':>11} {'placa':>6} {'salió':<12} {'puesto':>7} {'p':>7}")
    for f in filas:
        if not f.get("puesto_del_modelo"):
            continue
        print(f"{f['gala']:>5} {f['fecha']:>11} {f['n_placa']:>6} {f['eliminado']:<12} "
              f"{f['puesto_del_modelo']:>7} {100*(f['p_modelo'] or 0):>6.1f}%")
    if utiles:
        print(f"\nacierta el nombre en {aciertos} de {len(utiles)}")
        print(f"puesto medio {puesto_medio:.2f} contra {azar_medio:.2f} del azar")
        print(f"log-verosimilitud {ll:.3f} contra {ll_azar:.3f} del azar")
    print("\nescrito data/retro.json")


if __name__ == "__main__":
    main()
