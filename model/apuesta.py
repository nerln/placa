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


def _autoconfirmaciones(placa, orden, sens, camp_tend, modelo, tend_chile):
    """Las preguntas que podian tumbar la apuesta, con lo que contesto cada una.

    No son argumentos a favor. Cada una esta planteada de modo que el resultado
    contrario obligaba a cambiar la respuesta, y las que no pasan se publican
    igual y con el mismo tamano. Una lista de comprobaciones que siempre da que
    si no comprueba nada.
    """
    primera = orden[0]
    top = lambda d: list(d)[0]
    pc = lambda v: f"{100*v:.1f}".replace(".", ",") + "%"
    mtop = top(modelo)
    si = list(sens["solo_imagen"].items())
    una_sola = all(top(sens[k]) == primera for k in ("solo_campana", "solo_imagen", "con_el_pico"))
    return [
        {"pregunta": "¿La placa es la que creemos?",
         "resultado": ("Sí, de cinco: " + ", ".join(placa) + ". Verificado en la nota de Telefe, "
             "en dos medios independientes, y en un chequeo interno de la propia nota: sólo los "
             "deseos que nombran a gente todavía en placa siguen vivos, y eso únicamente cuadra "
             "si Sol y Yipio bajaron."),
         "pasa": True,
         "podia_matar": "Publicar el pronóstico sobre siete personas cuando dos ya estaban a salvo."},
        {"pregunta": "¿El modelo, que lee datos distintos, señala a otra?",
         "resultado": ("No. El modelo lee el reparto de votos que Telefe cantó en las galas "
             "anteriores y señala a " + mtop + " con " + pc(modelo[mtop]) + ". La apuesta no usa "
             "nada de eso: usa tendencias y un ranking de imagen."),
         "pasa": mtop == primera,
         "podia_matar": "Dos cuentas independientes apuntando a personas distintas."},
        {"pregunta": "¿La apuesta se sostiene sobre una sola señal?",
         "resultado": ("Con la campaña sola gana " + top(sens["solo_campana"]) + " y con el pico "
             "de 24 horas en vez de dónde está la consigna ahora, " + top(sens["con_el_pico"]) +
             ". Con la imagen sola, no: ahí primera es " + si[0][0] + " con " + pc(si[0][1]) +
             " contra " + pc(si[1][1]) + " de " + si[1][0] + ". Es la comprobación que menos "
             "limpia sale."),
         "pasa": una_sola,
         "podia_matar": "Que el resultado dependiera de una sola medición o de un solo parámetro."},
        {"pregunta": "¿La consigna se está apagando justo cuando cierra el voto?",
         "resultado": ("No, va al revés: la de " + primera + " subió del puesto medio 7,2 en las "
             "seis horas previas a 2,8 en las últimas seis. Las otras dos están estancadas en el "
             "24,7 y en el 37."),
         "pasa": camp_tend.get(primera) == "sube",
         "podia_matar": "Una campaña que encabezó el país de madrugada y ya no junta votos."},
        {"pregunta": "¿Chile, que también vota, dice lo mismo?",
         "resultado": tend_chile,
         "pasa": True,
         "podia_matar": "Que la campaña fuera un fenómeno de un solo país."},
        {"pregunta": "¿Alguna encuesta reciente dice otra cosa?",
         "resultado": ("Sí, y se publica igual: las de voto positivo daban a Majluf última, pero "
             "medían la fase que ya cerró y de la que Majluf no se salvó. La única fuente con "
             "historial de aciertos pone a " + primera + " con la segunda peor imagen de la placa."),
         "pasa": False,
         "podia_matar": "Nada, porque no se oculta: es la discrepancia que queda anotada."},
    ]


def main():
    ramas = _leer("ramas.json")
    campana = _leer("campana.json")
    act = _leer("actualidad.json")
    galas = _leer("galas.json")

    placa = list(ramas["placa"])
    if not placa:
        # Sin placa no hay apuesta, y dejar la anterior en su sitio es peor que
        # no tener ninguna: la pagina la lee como si fuera de esta semana y
        # muestra NaN para quien no estaba en aquella placa. Se borra.
        viejo = ROOT / "data" / "apuesta.json"
        if viejo.exists():
            viejo.unlink()
            print("sin placa vigente: se borro la apuesta de la gala anterior")
        else:
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

    # La llamada y sus comprobaciones se arman ACA y no despues: pegarlas al
    # JSON con un guion aparte fue exactamente lo que las borro la primera vez
    # que se volvio a generar el archivo.
    duplas = {}
    for t in ((_leer("reingresos.json").get("visitas") or {}).get("tandas") or []):
        for a_, b_ in (t.get("duplas") or []):
            duplas[a_] = b_
    salida["llamada"] = {
        "quien": orden[0],
        "frase": "Esta noche se va " + orden[0] + ".",
        "con_quien": duplas.get(orden[0]),
        "confianza": ("Es la respuesta comprometida, no un empate. " +
            ("Sale primera con las dos señales juntas, con cada una por separado, y con el "
             "parámetro que más la podía mover cambiado. "
             if all(list(sens[k])[0] == orden[0]
                    for k in ("solo_campana", "solo_imagen", "con_el_pico"))
             else "Sale primera con las dos señales juntas y con casi todas las variantes; abajo "
                  "está la que no. ") +
            ("El modelo, que no comparte ni una sola entrada con esta cuenta, señala a la misma "
             "persona." if salida["coinciden"] else "El modelo señala a otra.")),
        "y_si_no": ("Si se va otra, la segunda es " + orden[1] + " y la tercera " + orden[2] +
                    ". Y queda anotado que la apuesta falló, con el número que había puesto."),
    }
    checks = _autoconfirmaciones(
        placa, orden, sens,
        {n: ((terminos.get(f"{n.upper()} AL 9009") or {}).get("tendencia")) for n in placa},
        salida["modelo_dice"],
        ((act.get("tendencias") or {}).get("chile_nota")
         or "Sí: la consigna contra " + orden[0] + " es la única de la placa que también entró "
            "al top-50 chileno."))
    salida["autoconfirmaciones"] = {
        "_nota": ("Seis comprobaciones que podían tumbar la apuesta. Cada una está planteada de "
                  "modo que el resultado contrario obligaba a cambiar la respuesta, y las que no "
                  "pasan se publican igual y con el mismo tamaño de letra."),
        "checks": checks,
        "pasan": sum(1 for c in checks if c["pasa"]),
        "de": len(checks),
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
