# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""¿Y si el modelo no está roto sino al revés?

    python3 model/signo.py

POR QUÉ SE PREGUNTA ESTO. `model/retro.py` mide el modelo contra las galas ya
jugadas y le da cero aciertos de siete, con una prueba de permutación de 0,0266.
Ese número se suele leer como «el modelo no sirve». No es lo que dice. Un modelo
que no sirve da el azar; para andar *significativamente* por debajo del azar hace
falta señal, y hace falta tenerle puesto el signo cambiado.

Así que se prueba lo obvio: dar vuelta el orden y volver a puntuar, con el mismo
procedimiento, sin tocar nada más.

LO QUE HAY QUE DECIR AL PUBLICARLO, Y ESTÁ DICHO ACÁ PARA QUE NO SE OLVIDE. El
signo se eligió DESPUÉS de ver los datos, sobre siete galas. Eso no es un
hallazgo, es una hipótesis. La prueba de permutación de la versión invertida es
la misma prueba leída de la otra cola, así que no es evidencia nueva: es la misma
evidencia contada al derecho. La única forma honesta de cobrarla es declararla
antes de las galas que faltan y puntuarla hacia adelante como cualquier otra
predicción, con la regla de `EVALUACION.md`.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SEMILLA = 20260824
N_BARAJADAS = 200_000


def cargar():
    return json.loads((RAIZ / "data" / "retro.json").read_text())


def puntuar(filas):
    """Puesto del eliminado, al derecho y al revés, y aciertos de cada uno."""
    directo = invertido = 0
    suma_d = suma_i = suma_azar = 0.0
    detalle = []
    for f in filas:
        n = f["n_placa"]
        p = f["puesto_del_modelo"]
        pi = n + 1 - p
        directo += p == 1
        invertido += pi == 1
        suma_d += p
        suma_i += pi
        suma_azar += (n + 1) / 2
        detalle.append((f["gala"], n, f["eliminado"], p, pi))
    k = len(filas)
    return {
        "detalle": detalle,
        "n": k,
        "aciertos_directo": directo,
        "aciertos_invertido": invertido,
        "puesto_directo": suma_d / k,
        "puesto_invertido": suma_i / k,
        "puesto_azar": suma_azar / k,
        "aciertos_esperados_azar": sum(1 / f["n_placa"] for f in filas),
    }


def permutacion(filas, objetivo, semilla=SEMILLA, n=N_BARAJADAS):
    """Cuántas veces el azar iguala o mejora ese puesto medio."""
    rng = random.Random(semilla)
    mejor = 0
    for _ in range(n):
        s = sum(rng.randint(1, f["n_placa"]) for f in filas) / len(filas)
        if s <= objetivo:
            mejor += 1
    return mejor / n


def main():
    r = cargar()
    filas = r["filas"]
    x = puntuar(filas)

    print(f"{x['n']} galas · lo que publica retro.py: {r['aciertos']} aciertos, "
          f"puesto medio {r['puesto_medio']}")
    print()
    print(f"{'gala':>5} {'placa':>6} {'salió':>11} {'puesto':>7} {'invertido':>10}")
    for gala, n, quien, p, pi in x["detalle"]:
        print(f"{gala:>5} {n:>6} {quien:>11} {p:>7} {pi:>10}")
    print()
    print(f"al derecho   {x['aciertos_directo']} aciertos · "
          f"puesto medio {x['puesto_directo']:.2f}")
    print(f"al revés     {x['aciertos_invertido']} aciertos · "
          f"puesto medio {x['puesto_invertido']:.2f}")
    print(f"azar         {x['aciertos_esperados_azar']:.2f} esperados · "
          f"puesto medio {x['puesto_azar']:.2f}")
    print()
    p = permutacion(filas, x["puesto_invertido"])
    print(f"permutación sobre la versión invertida ({N_BARAJADAS} barajadas): p = {p:.4f}")
    print()
    print("Es la misma prueba que condena al modelo al derecho, leída de la otra")
    print("cola. El signo se eligió después de ver los datos, sobre siete galas.")
    print("Se declara como hipótesis y se puntúa hacia adelante. No se toca el")
    print("modelo por esto.")

    salida = RAIZ / "data" / "signo.json"
    salida.write_text(json.dumps({
        "generado_por": "model/signo.py",
        "n": x["n"],
        "aciertos_directo": x["aciertos_directo"],
        "aciertos_invertido": x["aciertos_invertido"],
        "aciertos_esperados_azar": round(x["aciertos_esperados_azar"], 4),
        "puesto_directo": round(x["puesto_directo"], 4),
        "puesto_invertido": round(x["puesto_invertido"], 4),
        "puesto_azar": round(x["puesto_azar"], 4),
        "p_permutacion_invertido": round(p, 4),
        "semilla": SEMILLA,
        "barajadas": N_BARAJADAS,
        "advertencia": ("El signo se eligió después de ver los datos, sobre "
                        "siete galas. Es una hipótesis declarada, no un "
                        "resultado. Se puntúa hacia adelante con la regla de "
                        "EVALUACION.md."),
    }, ensure_ascii=False, indent=2) + "\n")
    print(f"\nescrito {salida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
