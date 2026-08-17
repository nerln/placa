# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
LA APUESTA: la prediccion declarada para la gala de esta noche.

Esto NO es el modelo de la pagina, y se publica aparte a proposito. El modelo
contesta "quien se va" con el rasgo de rechazo ajustado sobre el reparto de
votos de las galas jugadas, y la prueba hacia atras dice que en esa pregunta
anda PEOR QUE EL AZAR: cero aciertos de seis, puesto medio 5,00 contra 3,50 del
azar, p = 0,020 en un test de permutacion. Eso esta publicado en la pagina desde
antes de esta gala. Apostar siguiendo ese ranking seria seguir una senal que ya
se midio y salio mal.

Asi que la apuesta se arma con las dos cosas que si se pueden observar desde
afuera antes de que cierre la votacion:

    1. EL INDICE DE CAMPANA. Cuenta consignas con signo en las tendencias de X:
       "LUANA AL 9009" pide que la echen y lleva el signo escrito adentro. Es
       una medicion propia, de la ventana de las ultimas 24 horas, y cae entera
       dentro de la fase de voto negativo.
    2. LA IMAGEN DE FEFE BONGIORNO. Es el unico agregador de la temporada con
       historial: acerto el eliminado en 5 de 5 galas documentadas. Mide si
       alguien cae bien, no intencion de voto, y se publico el 12 de agosto.

Se multiplican. Ninguna de las dos es el voto: el voto es pago, sin tope, y mide
gasto y no personas. Por eso esto es una apuesta declarada y no un pronostico, y
por eso los cuatro numeros que hay que suponer estan escritos aca arriba y no
escondidos en el codigo. Abajo se reporta que pasaria con cada senal sola.

Una nota sobre la fase positiva: hasta la emision del domingo esta placa se
votaba al reves, para salvar, y de ahi bajaron dos. Eso ya no hay que estimarlo
porque se anuncio al aire: bajaron Sol y Yipio. Si alguna vez hay que correr
esto con la fase positiva todavia abierta, hay que volver a simular quien baja.

    python3 model/apuesta.py        ->  data/apuesta.json
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# LO QUE HAY QUE SUPONER. Cuatro numeros que no salen de ningun dato.
# ---------------------------------------------------------------------------

# Cuanto pesa cada senal. 1 y 1 es creerles lo mismo a las dos. Poner una en 0
# equivale a ignorarla, y eso es justo lo que se reporta como sensibilidad.
PESO_CAMPANA = 1.0
PESO_IMAGEN = 1.0

# Quien no tiene consigna NO es quien no tiene votos en contra: es quien no fue
# medida. Codificarlo como cero afirmaria que nadie pide que se vaya, que es
# justo lo que no se sabe. Se le da el peso de una consigna que hubiera llegado
# al puesto 25, o sea media campana.
PISO_SIN_CONSIGNA = 0.52

# Lo mismo para quien no aparece en el ranking de imagen: se le da la mitad.
PISO_SIN_IMAGEN = 0.50


def _leer(nombre):
    return json.loads((ROOT / "data" / nombre).read_text())


def main():
    ramas = _leer("ramas.json")
    campana = _leer("campana.json")
    act = _leer("actualidad.json")
    galas = _leer("galas.json")

    placa = list(ramas["placa"])
    if not placa:
        print("sin placa vigente: no hay apuesta que declarar")
        return

    # --- senal 1: la campana, con signo y con el momento en que esta ---------
    # El indice de campana pesa por el PICO de la consigna en 24 horas. Para una
    # votacion que cierra esta noche importa mas donde esta AHORA: una consigna
    # que encabezo el pais a la madrugada y a la tarde cayo al puesto 40 ya no
    # esta juntando votos. Cuando hay medicion reciente se usa esa, y el pico
    # queda como variante en la sensibilidad.
    idx = campana["indice"]
    terminos = {t["txt"]: t for t in (act.get("tendencias") or {}).get("terminos", [])}

    def peso_puesto(p):
        return max(0.02, (51 - min(float(p), 50.0)) / 50.0)

    camp_pico, camp_ahora = {}, {}
    for n in placa:
        v = idx.get(n, {}).get("icd")
        camp_pico[n] = PISO_SIN_CONSIGNA if v is None or v >= 0 else -v
        t = terminos.get(f"{n.upper()} AL 9009")
        rec = (t or {}).get("reciente")
        camp_ahora[n] = peso_puesto(rec) if rec is not None else PISO_SIN_CONSIGNA
    camp = camp_ahora

    # --- senal 2: la imagen, dada vuelta ------------------------------------
    fuentes = (act.get("medidas_sociales") or {}).get("fuentes", [])
    img_f = next((f for f in fuentes if f.get("mide") == "imagen positiva"), None)
    img = {}
    for n in placa:
        v = (img_f or {}).get("valores", {}).get(n)
        # Caer mal es lo que hace que a uno lo voten para afuera, asi que la
        # imagen entra invertida: 100 menos el porcentaje, sobre 100.
        img[n] = PISO_SIN_IMAGEN if v is None else max(0.02, (100.0 - float(v)) / 100.0)

    def repartir(pc, pi, cual=None):
        c = cual or camp
        w = {n: (c[n] ** pc) * (img[n] ** pi) for n in placa}
        t = sum(w.values())
        return {n: w[n] / t for n in placa}

    p = repartir(PESO_CAMPANA, PESO_IMAGEN)
    orden = sorted(placa, key=lambda n: -p[n])

    sens = {
        "las_dos": {n: round(p[n], 4) for n in orden},
        "solo_campana": {n: round(v, 4) for n, v in
                         sorted(repartir(1.0, 0.0).items(), key=lambda kv: -kv[1])},
        "solo_imagen": {n: round(v, 4) for n, v in
                        sorted(repartir(0.0, 1.0).items(), key=lambda kv: -kv[1])},
        "con_el_pico": {n: round(v, 4) for n, v in
                        sorted(repartir(PESO_CAMPANA, PESO_IMAGEN, camp_pico).items(),
                               key=lambda kv: -kv[1])},
    }

    pv = galas.get("placa_vigente") or {}
    salida = {
        "generado": ramas["generado"],
        "gala": pv.get("gala"),
        "fecha_gala": pv.get("fecha"),
        "placa": placa,
        "bajaron_de_placa": {
            "quienes": ["Sol", "Yipio"],
            "cuando": "2026-08-16",
            "como": ("Los sacó la fase de voto positivo. Del Moro lo anunció al aire el domingo, "
                     "para afuera: a las jugadoras no se les dijo."),
            "fuente": ("https://www.mitelefe.com/gran-hermano/noticias/"
                       "cruces-en-la-cena-de-nominadas-y-dos-jugadoras-salvadas-de-la-"
                       "eliminacion-pid2562969"),
        },
        "es_del_modelo": False,
        "que_es": ("Predicción declarada para esta gala. No sale del modelo de la página: el "
                   "modelo contesta la misma pregunta, y su prueba hacia atrás dice que en esa "
                   "pregunta anda peor que el azar. Ésta se arma con las dos señales que se "
                   "pueden observar desde afuera antes de que cierre la votación."),
        "supuestos": {
            "peso_campana": PESO_CAMPANA,
            "peso_imagen": PESO_IMAGEN,
            "piso_sin_consigna": PISO_SIN_CONSIGNA,
            "piso_sin_imagen": PISO_SIN_IMAGEN,
        },
        "entradas": {
            "campana": {n: round(camp[n], 3) for n in orden},
            "campana_medida": {n: idx.get(n, {}).get("icd") for n in placa},
            "campana_ahora": {n: ((terminos.get(f"{n.upper()} AL 9009") or {}).get("reciente"))
                              for n in orden},
            "campana_tendencia": {n: ((terminos.get(f"{n.upper()} AL 9009") or {}).get("tendencia"))
                                  for n in orden},
            "momento_nota": (act.get("tendencias") or {}).get("_nota_momento"),
            "ventana_campana": (act.get("tendencias") or {}).get("ventana"),
            "imagen": {n: (img_f or {}).get("valores", {}).get(n) for n in orden},
            "imagen_quien": (img_f or {}).get("quien"),
            "imagen_fecha": (img_f or {}).get("fecha"),
            "imagen_historial": (img_f or {}).get("historial"),
        },
        "p_sale": {n: round(p[n], 4) for n in orden},
        "sensibilidad": sens,
        "modelo_dice": {k: round(v["p_sale"], 4)
                        for k, v in sorted(ramas["ramas"].items(),
                                           key=lambda kv: -kv[1]["p_sale"])},
        "coinciden": orden[0] == max(ramas["ramas"], key=lambda k: ramas["ramas"][k]["p_sale"]),
    }
    (ROOT / "data" / "apuesta.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1))

    print(f"placa de {len(placa)} · gala {pv.get('gala')} del {pv.get('fecha')}")
    print(f"\n{'quien se va':<12} {'apuesta':>8} {'campana':>9} {'imagen':>8}   "
          f"{'el modelo':>10}")
    for n in orden:
        iv = (img_f or {}).get("valores", {}).get(n)
        print(f"{n:<12} {100*p[n]:7.1f}% {camp[n]:9.2f} "
              f"{(str(iv) + '%') if iv is not None else '—':>8}   "
              f"{100*ramas['ramas'][n]['p_sale']:9.1f}%")
    print("\ncon una sola senal, o con el pico en vez del momento:")
    for k in ("solo_campana", "solo_imagen", "con_el_pico"):
        top = list(sens[k].items())[:3]
        print(f"  {k:14} " + " · ".join(f"{n} {100*v:.0f}%" for n, v in top))
    print(f"\nla apuesta y el modelo {'COINCIDEN' if salida['coinciden'] else 'no coinciden'}")


if __name__ == "__main__":
    main()
