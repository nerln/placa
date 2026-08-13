# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
Actualizacion del pronostico despues de cada gala.

Toma el resultado oficial de una gala, lo incorpora a los datos, vuelve a
estimar las dos escalas, vuelve a simular y regenera la interfaz. Es lo que
ejecuta la tarea programada de los martes, y tambien lo que conviene correr a
mano si una gala se adelanta o hay una doble eliminacion.

Ejemplo (gala 28, si saliera Hanssen):

  python3 model/actualizar.py \\
    --gala 28 --fecha 2026-08-10 \\
    --placa "Charlotte,Majluf,Sol,Hanssen,Pincoya,Zilli" \\
    --salvados "Zilli:0.8,Pincoya:1.1,Majluf:2.4,Charlotte:5.2" \\
    --versus "Sol:47.9,Hanssen:52.1" \\
    --eliminado Hanssen \\
    --nueva-placa "Sol,Majluf,Mariela,Luana,Tamara" --nuevo-lider Pincoya \\
    --fecha-proxima 2026-08-17

Salida por gente que se va sin votacion (abandono, expulsion, evacuacion):

  python3 model/actualizar.py --abandono Juanicar --fecha 2026-08-06 \\
    --motivo "problema de salud de su madre"

Comprobacion que hace siempre: la identidad aritmetica de Telefe

    suma publicada - 100  ==  suma de los porcentajes que no son del versus

Si cuadra, la gala entra como multinomial COMPLETA y pesa en la estimacion de
mu. Si no cuadra, entra igual pero marcada como parcial, porque significa que
hubo nominados cuyo porcentaje no se publico.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"


def leer(n):
    return json.loads((D / n).read_text())


def escribir(n, d):
    (D / n).write_text(json.dumps(d, ensure_ascii=False, indent=1))


def pares(s):
    """'Sol:46.7,Hanssen:53.3' -> {'Sol': 46.7, 'Hanssen': 53.3}"""
    if not s:
        return {}
    out = {}
    for t in s.split(","):
        k, v = t.split(":")
        out[k.strip()] = float(v)
    return out


def lista(s):
    return [x.strip() for x in s.split(",") if x.strip()] if s else []


def verificar_identidad(salvados, versus):
    """Devuelve (completa, suma_publicada, exceso, suma_no_versus)."""
    if not versus or len(versus) != 2:
        return False, None, None, None
    total = sum(salvados.values()) + sum(versus.values())
    exceso = round(total - 100, 2)
    no_versus = round(sum(salvados.values()), 2)
    return abs(exceso - no_versus) < 0.35, round(total, 2), exceso, no_versus


def sacar_jugador(plantel, apodo, fecha, modo, detalle):
    j = [x for x in plantel["jugadores"] if x["apodo"] == apodo]
    if not j:
        print(f"  aviso: {apodo} ya no figuraba en el plantel")
        return plantel
    plantel["jugadores"] = [x for x in plantel["jugadores"] if x["apodo"] != apodo]
    # Se guarda la ficha ENTERA, no solo el nombre. Antes se tiraba, y con ella
    # la posibilidad de reconstruir cualquier estado pasado del modelo: para
    # comparar el pronostico de antes con el de despues de una gala hace falta
    # volver a armar el plantel de aquella semana.
    plantel["eliminados_recientes"].insert(
        0, {"apodo": apodo, "fecha": fecha, "modo": modo, "detalle": detalle,
            "ficha": j[0]})
    plantel["eliminados_recientes"] = plantel["eliminados_recientes"][:8]
    return plantel


def main():
    ap = argparse.ArgumentParser(description="Incorpora una gala y recalcula el pronostico")
    ap.add_argument("--gala", type=int)
    ap.add_argument("--fecha", required=True, help="AAAA-MM-DD de la gala")
    ap.add_argument("--placa", help="nominados de la gala que se resolvio, separados por coma")
    ap.add_argument("--salvados", help="'Nombre:pct,...' de los salvados progresivos")
    ap.add_argument("--versus", help="'Nombre:pct,Nombre:pct' del mano a mano final")
    ap.add_argument("--eliminado")
    ap.add_argument("--abandono", help="quien se fue sin votacion (abandono/expulsion/evacuacion)")
    ap.add_argument("--modo", default="abandono")
    ap.add_argument("--motivo", default="")
    ap.add_argument("--nueva-placa", help="nominados de la semana siguiente")
    ap.add_argument("--nuevo-lider")
    ap.add_argument("--fecha-proxima")
    ap.add_argument("--encuesta", help="'Nombre:pct,...' de la encuesta previa a la proxima gala")
    ap.add_argument("--encuesta-fecha")
    ap.add_argument("--encuesta-n", type=int, default=0)
    ap.add_argument("--encuesta-resto", type=float, default=0.0)
    ap.add_argument("--encuesta-resto-miembros", default="")
    ap.add_argument("--positivo-candidatos", help="fase de voto positivo: conjunto completo")
    ap.add_argument("--positivo-orden", help="fase de voto positivo: salvados en orden")
    ap.add_argument("--nota-plantel", help="'Nombre:placas:votos,...' para refrescar propensiones")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sin-recalcular", action="store_true")
    a = ap.parse_args()

    galas = leer("galas.json")
    encuestas = leer("encuestas.json")
    plantel = leer("plantel.json")
    positivo = leer("voto_positivo.json")

    # --- salida sin votacion ------------------------------------------------
    if a.abandono:
        print(f"· {a.abandono} sale por {a.modo} el {a.fecha}")
        plantel = sacar_jugador(plantel, a.abandono, a.fecha, a.modo, a.motivo)
        if a.nueva_placa:
            galas["placa_vigente"]["integrantes"] = lista(a.nueva_placa)
        vivos = [j["apodo"] for j in plantel["jugadores"]]
        galas["placa_vigente"]["libres"] = [
            v for v in vivos if v not in galas["placa_vigente"]["integrantes"]]

    # --- gala con votacion ---------------------------------------------------
    if a.eliminado:
        salvados, versus = pares(a.salvados), pares(a.versus)
        placa = lista(a.placa) or list(salvados) + list(versus)
        completa, total, exceso, no_versus = verificar_identidad(salvados, versus)
        print(f"· Gala {a.gala} · {a.fecha} · sale {a.eliminado}")
        if total is not None:
            estado = "CUADRA, placa completa" if completa else "NO CUADRA, placa parcial"
            print(f"  identidad de Telefe: suma {total} − 100 = {exceso} "
                  f"vs no-versus {no_versus}  →  {estado}")
        if a.eliminado not in versus and versus:
            print(f"  aviso: {a.eliminado} no figura en el versus")

        galas["galas"].append({
            "gala": a.gala, "fecha": a.fecha, "tipo": "negativo",
            "placa": placa, "salvados_cuota": salvados, "versus": versus,
            "completa": bool(completa), "eliminado": a.eliminado,
        })
        galas["galas"].sort(key=lambda g: (g["fecha"], g["gala"] or 0))

        # la encuesta que apuntaba a esta gala pasa al historial calibrable
        prox = encuestas.get("proxima")
        if prox and prox.get("cuota"):
            encuestas["historial"].insert(0, {
                "fecha": prox.get("fecha"), "gala": a.gala,
                "encuesta": prox["cuota"]})
            print(f"  encuesta de {prox.get('fecha')} incorporada al historial de calibracion")

        plantel = sacar_jugador(plantel, a.eliminado, a.fecha, "eliminado",
                                a.motivo or f"eliminado en la gala {a.gala}")

    # --- fase de voto positivo, si la gala tuvo -----------------------------
    if a.positivo_orden and a.positivo_candidatos:
        positivo["fases"].append({
            "id": f"gala{a.gala}_pos", "fecha": a.fecha, "tipo": "orden",
            "candidatos": lista(a.positivo_candidatos),
            "orden": lista(a.positivo_orden)})
        print(f"  fase de voto positivo agregada: {len(lista(a.positivo_orden))} puestos revelados")

    # --- placa de la semana siguiente ---------------------------------------
    # Entre la gala del lunes y la de nominacion del miercoles NO hay placa. Si
    # no se pasa una nueva, la vigente se vacia en vez de quedarse con la que se
    # acaba de resolver: si no, el modelo arranca condicionando sobre una placa
    # que incluye a quien acaba de salir, y revienta o miente.
    if a.eliminado and not a.nueva_placa:
        vivos = [j["apodo"] for j in plantel["jugadores"]]
        galas["placa_vigente"] = {
            "gala": (a.gala or galas["placa_vigente"]["gala"]) + 1,
            "fecha": a.fecha_proxima or "",
            "fecha_nominacion": a.fecha,
            "integrantes": [],
            "inmune_lider": a.nuevo_lider or "",
            "libres": vivos,
        }
        print("  sin placa nueva todavia: la proxima gala se simula sin placa observada")

    if a.nueva_placa:
        vivos = [j["apodo"] for j in plantel["jugadores"]]
        nueva = [x for x in lista(a.nueva_placa) if x in vivos]
        galas["placa_vigente"] = {
            "gala": (a.gala or galas["placa_vigente"]["gala"]) + 1,
            "fecha": a.fecha_proxima or "",
            "fecha_nominacion": a.fecha,
            "integrantes": nueva,
            "inmune_lider": a.nuevo_lider or "",
            "libres": [v for v in vivos if v not in nueva],
        }
        print(f"  nueva placa: {', '.join(nueva)} · líder {a.nuevo_lider or '—'}")

    # --- encuesta de la proxima gala ----------------------------------------
    if a.encuesta:
        cuota = pares(a.encuesta)
        miembros = lista(a.encuesta_resto_miembros) or [
            x for x in galas["placa_vigente"]["integrantes"] if x not in cuota]
        encuestas["proxima"] = {
            "_nota": "Medicion previa a la gala que todavia no se jugo.",
            "fuente": "Fefe Bongiorno via prensa", "fecha": a.encuesta_fecha or a.fecha,
            "n_nominal": a.encuesta_n, "gala": galas["placa_vigente"]["gala"],
            "placa": galas["placa_vigente"]["integrantes"],
            "cuota": cuota, "resto_agregado": a.encuesta_resto,
            "resto_miembros": miembros,
        }
        print(f"  encuesta nueva: {cuota}")
    elif a.eliminado:
        # sin encuesta de la proxima gala, el modelo usa solo preferencia revelada
        encuestas["proxima"] = {
            "_nota": "Sin encuesta disponible: el estado de la proxima gala se estima "
                     "solo con preferencia revelada. cuota vacia = sin observacion.",
            "fuente": "", "fecha": "", "n_nominal": 0,
            "gala": galas["placa_vigente"]["gala"],
            "placa": galas["placa_vigente"]["integrantes"],
            "cuota": {}, "resto_agregado": 0.0, "resto_miembros": [],
        }
        print("  sin encuesta para la proxima gala: se usara solo preferencia revelada")

    # --- refresco de propensiones -------------------------------------------
    if a.nota_plantel:
        for t in a.nota_plantel.split(","):
            nom, pl, vo = t.split(":")
            for j in plantel["jugadores"]:
                if j["apodo"] == nom.strip():
                    j["placas_recientes"], j["votos_recientes"] = int(pl), int(vo)

    plantel["actualizado"] = a.fecha
    for j in plantel["jugadores"]:
        if a.eliminado and j["apodo"] in galas["placa_vigente"]["integrantes"]:
            j["placas_recientes"] = j.get("placas_recientes", 0) + 1

    if a.dry_run:
        print("\n(dry-run: no se escribio nada)")
        return

    escribir("galas.json", galas)
    escribir("encuestas.json", encuestas)
    escribir("plantel.json", plantel)
    escribir("voto_positivo.json", positivo)
    print(f"\n  datos actualizados · quedan {len(plantel['jugadores'])} en juego")

    if a.sin_recalcular:
        return
    # ramas.py va despues de final_model.py porque reusa su ajuste, y antes de
    # build.py porque la pagina incrusta data/ramas.json. Si se olvida, la
    # pagina queda con las ramas de la gala anterior, que es peor que no
    # tenerlas: son numeros que parecen frescos y no lo son. tarjeta.py va
    # ultimo por lo mismo, con la previsualizacion del enlace.
    for paso in ("model/final_model.py", "model/ramas.py", "model/evolucion.py",
                 "model/bootstrap.py", "model/camino.py", "model/sendas.py",
                 "model/campana.py", "model/retro.py", "gui/build.py",
                 "gui/tarjeta.py"):
        print(f"\n>>> {paso}")
        r = subprocess.run([sys.executable, str(ROOT / paso)], cwd=ROOT,
                           capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-3000:]); print(r.stderr[-3000:])
            sys.exit(f"fallo {paso}")
        cola = [l for l in r.stdout.splitlines() if l.strip()][-14:]
        print("\n".join(cola))

    res = leer("resultados.json")["escenarios"]["base"]["p_gana"]
    top = sorted(res.items(), key=lambda z: -z[1])[:3]
    print("\n=== PRONOSTICO ACTUALIZADO ===")
    for n, p in top:
        print(f"   {n:<12}{100*p:>6.1f}%")


if __name__ == "__main__":
    main()
