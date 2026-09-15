# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
EL CIERRE: la ganadora, cargada una sola vez, con dos fuentes.

Es el unico paso del ciclo que no existia. La ganadora no «sale», asi que
actualizar.py no sirve: aca se escribe el resultado de la pregunta 2 de
EVALUACION.md (log-loss de cada corrida publicada contra el azar de ese dia),
se puntua la final como una gala mas de la pregunta 1 (quien se va = la
segunda), se deja la placa vacia para que ningun guion vuelva a simular una
temporada con una sola persona, y se marca actualidad.cerrada para que la
tarea horaria deje de correr.

    python3 model/cerrar.py --ganadora Sol --pct 55.3 --fecha 2026-09-16 \
        --fuente URL1 --fuente URL2

Se niega si la ganadora no esta en la placa vigente, si hay menos de dos
fuentes, o si ya esta cerrado. No recalcula el modelo: lo ultimo publicado
antes de la gala es lo que se puntua, y tocarlo despues seria acomodarlo.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"


def leer(n):
    return json.loads((D / n).read_text())


def escribir(n, obj):
    (D / n).write_text(json.dumps(obj, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description="Carga la ganadora y cierra la temporada")
    ap.add_argument("--ganadora", required=True)
    ap.add_argument("--pct", type=float, help="porcentaje publicado de la ganadora")
    ap.add_argument("--fecha", required=True, help="AAAA-MM-DD de la noche de la ganadora")
    ap.add_argument("--fuente", action="append", default=[], help="dos como minimo")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    act = leer("actualidad.json")
    galas = leer("galas.json")
    H = leer("historial_pronostico.json")
    if act.get("cerrada"):
        sys.exit("ya esta cerrado: no se cierra dos veces")
    if len(a.fuente) < 2:
        sys.exit("hacen falta dos fuentes independientes, como con cualquier gala")
    pv = galas.get("placa_vigente") or {}
    placa = list(pv.get("integrantes") or [])
    if a.ganadora not in placa:
        sys.exit(f"{a.ganadora} no esta en la placa vigente {placa}: no se cierra sobre otra placa")
    if len(placa) != 2:
        sys.exit(f"la placa vigente tiene {len(placa)} nombres y una final se cierra con dos")
    segunda = [n for n in placa if n != a.ganadora][0]
    G = act.get("proxima_gala") or {}
    gala = G.get("gala") or (pv.get("gala"))

    # --- pregunta 2: log-loss de cada corrida publicada -------------------
    corridas = []
    for c in H.get("corridas") or []:
        pg = c.get("p_gana") or {}
        if a.ganadora not in pg or c.get("reconstruida"):
            continue
        ej = c.get("en_juego")
        n = int(ej) if isinstance(ej, int) else len(ej or pg)
        p = max(float(pg[a.ganadora]), 1e-4)
        corridas.append({
            "fecha": c.get("fecha"), "en_juego": n, "p_ganadora": round(p, 4),
            "puesto": sorted(pg, key=lambda k: -pg[k]).index(a.ganadora) + 1,
            "log_loss": round(-math.log(p), 4), "log_loss_uniforme": round(math.log(n), 4),
            "brier": round(sum((float(v) - (1.0 if k == a.ganadora else 0.0)) ** 2 for k, v in pg.items()), 4),
            "brier_uniforme": round(sum((1 / n - (1.0 if k == a.ganadora else 0.0)) ** 2 for k in pg), 4),
        })
    antes = [c for c in corridas if c["fecha"] and c["fecha"] < a.fecha]
    ultima = antes[-1] if antes else None

    cierre = {
        "_nota": ("Resultado de la temporada y puntaje de la pregunta 2 de EVALUACION.md: "
                  "log-loss de la probabilidad de ganar publicada en cada corrida, contra el "
                  "azar de ese dia (uniforme sobre quienes seguian en juego). Escrito por "
                  "model/cerrar.py, una sola vez, con dos fuentes."),
        "ganadora": a.ganadora, "segunda": segunda, "pct": a.pct, "fecha": a.fecha,
        "gala": gala, "fuentes": a.fuente,
        "cerrado": dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))).strftime("%Y-%m-%dT%H:%M%z"),
        "ultima_corrida": ultima,
        "corridas": corridas,
        "mejor_que_azar_en": sum(1 for c in corridas if c["log_loss"] < c["log_loss_uniforme"]),
        "de_corridas": len(corridas),
    }

    print(f"· Gano {a.ganadora}" + (f" con el {a.pct}%" if a.pct is not None else "") +
          f" · segunda {segunda} · {a.fecha}")
    if ultima:
        print(f"  ultima corrida antes de la final ({ultima['fecha']}): le daba {100*ultima['p_ganadora']:.1f}% "
              f"· log-loss {ultima['log_loss']} contra {ultima['log_loss_uniforme']} del azar")
    print(f"  mejor que el azar en {cierre['mejor_que_azar_en']} de {len(corridas)} corridas publicadas")
    if a.dry_run:
        print("\n(dry-run: no se escribio nada)")
        return

    # --- la final como gala de la pregunta 1: se va la segunda ---------------
    galas["galas"].append({
        "gala": gala, "fecha": a.fecha, "tipo": "final",
        "placa": placa, "salvados_cuota": {},
        "versus": ({a.ganadora: a.pct, segunda: round(100 - a.pct, 1)} if a.pct is not None else {}),
        "completa": False, "eliminado": segunda,
        "_nota": "Noche de la ganadora: la que «sale» es la segunda. Los porcentajes son los publicados.",
    })
    galas["placa_vigente"] = {"gala": None, "fecha": "", "fecha_nominacion": None,
                              "integrantes": [], "inmune_lider": "", "libres": []}
    galas["final"]["resultado"] = {"ganadora": a.ganadora, "segunda": segunda, "pct": a.pct}
    escribir("galas.json", galas)

    plantel = leer("plantel.json")
    for j in plantel["jugadores"]:
        j["puesto_final"] = 1 if j["apodo"] == a.ganadora else 2
    plantel["cerrado"] = a.fecha
    escribir("plantel.json", plantel)

    act["cerrada"] = True
    G = dict(act.get("proxima_gala") or {})
    G["final"] = dict(G.get("final") or {})
    G["final"]["cerrada"] = {"ganadora": a.ganadora, "segunda": segunda, "pct": a.pct, "fecha": a.fecha}
    G["fases"] = []
    G["_nota"] = "Temporada terminada. Queda como registro de la ultima noche."
    act["proxima_gala"] = G
    escribir("actualidad.json", act)
    escribir("cierre.json", cierre)
    print("  escritos galas.json, plantel.json, actualidad.json (cerrada), cierre.json")

    r = subprocess.run([sys.executable, str(ROOT / "model" / "puntaje.py"), "--gala", str(gala),
                        "--eliminado", segunda], cwd=ROOT, capture_output=True, text=True)
    print("\n".join(l for l in r.stdout.splitlines() if l.strip())[-1200:])
    if r.returncode:
        print(r.stderr[-800:]); sys.exit("fallo puntaje.py")
    print("\n  ahora: python3 gui/build.py && python3 gui/tarjeta.py && python3 gui/verificar.py "
          "&& node gui/mirar/comprobar.mjs, y publicar con bin/publicar.sh --solo-web")


if __name__ == "__main__":
    main()
