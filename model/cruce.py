# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
EL CRUCE: el sentimiento y la campana, pesados por lo cerca que esta la gala.

POR QUE EXISTE. La pagina publica tres respuestas a «quien se va» y ninguna
mira lo que la gente escribe: el modelo lee repartos de votos viejos, y la
apuesta lee campanas y encuestas. Los comentarios se median y se mostraban al
costado, sin entrar a ninguna cuenta. En la gala 31 eso costo caro: las tres
predicciones pusieron a Pincoya SEGUNDA y salio Pincoya, mientras los
comentarios la ponian primera con el 91% en contra.

QUE CRUZA. Dos senales que se miden distinto y envejecen distinto:

  * la CAMPANA (y la encuesta cuando la hay), que es lo que se organiza: se
    mueve despacio, se arma con dias de anticipacion y aguanta.
  * el SENTIMIENTO de los comentarios, que es lo que se reacciona: se mueve en
    horas y responde a lo que acaba de pasar en la casa.

EL PESO SE MUEVE CON EL RELOJ, y esa es la idea entera. Faltando una semana,
lo que se organiza manda: una campana montada el lunes sigue en pie el viernes,
y un enojo del martes se apaga. Faltando horas, manda lo que se reacciona: el
voto que decide la gala se manda esa noche, despues del ultimo programa, y ahi
la conversacion de las ultimas horas dice mas que una encuesta de hace cuatro
dias. Por eso el peso del sentimiento CRECE cuando el reloj corre, y el de la
campana baja, pero baja menos: no se apaga, porque la campana es la que tiene
el unico acierto de la pagina.

    w_sentimiento = W0 + (W1 - W0) * r        r = 0 a una semana, 1 en la gala
    w_campana     = 1 - w_sentimiento

LA CORRECCION QUE HACE FALTA Y NO ES UN DETALLE. Una jugadora con dos
comentarios con signo no dice nada, y sin corregirlo el 100% de dos comentarios
pesaria como el 91% de quinientos. Se aplica un suavizado de Laplace: cada
proporcion se calcula como (en_contra + 1) / (total + 2), asi que con n chico
la proporcion se va sola al medio y la fila deja de gritar.

EL SIGNO LO PONE LA FASE, NUNCA EL TEXTO. En placa negativa se vota para echar
y la campana mas fuerte es la mas peligrosa; en placa positiva se vota para
salvar y la campana mas fuerte es la mas segura, y quien no tiene campana es
quien nadie esta pidiendo que se quede. La misma consigna dice lo contrario
segun el dia, y esta pagina ya publico una vez un pie de grafico con el signo
al reves.

QUE NO ES. No es el modelo ni lo usa. Es una cuarta prediccion, se congela
antes de cada gala como las otras tres y se puntua con EVALUACION.md, tambien
cuando falle. Se declara antes de la gala 32 y no tiene ni un acierto todavia.

    python3 model/cruce.py
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = dt.timezone(dt.timedelta(hours=-3))

# El horizonte del reloj: a partir de aca el sentimiento empieza a pesar mas.
# Una semana, que es lo que dura un ciclo de placa en esta edicion.
HORIZONTE_H = 168.0
W0 = 0.20     # peso del sentimiento a una semana de la gala
W1 = 0.65     # peso del sentimiento la noche de la gala
SUAVIZADO = 1.0   # Laplace: cuenta+1 sobre total+2


def _leer(n):
    return json.loads((ROOT / "data" / n).read_text())


def cercania(fecha_gala, ahora=None):
    """0 cuando falta una semana o mas, 1 cuando la gala ya empezo."""
    if not fecha_gala:
        return 0.0
    ahora = ahora or dt.datetime.now(ART)
    gala = dt.datetime.fromisoformat(f"{fecha_gala}T22:15:00-03:00")
    faltan = (gala - ahora).total_seconds() / 3600.0
    if faltan <= 0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - faltan / HORIZONTE_H))


def riesgo_sentimiento(por_jugadora, placa):
    """Proporcion en contra, suavizada, normalizada sobre la placa.

    «En contra» quiere decir lo mismo en las dos fases: que no la quieren
    adentro. En placa negativa es un voto para echarla y en positiva es un voto
    que no le llega, y las dos cosas la acercan a la puerta.
    """
    p = {}
    for n in placa:
        k = (por_jugadora or {}).get(n) or {}
        c, f = k.get("contra", 0), k.get("favor", 0)
        p[n] = (c + SUAVIZADO) / (c + f + 2 * SUAVIZADO)
    s = sum(p.values())
    return {n: v / s for n, v in p.items()} if s else {n: 1 / len(placa) for n in placa}


def riesgo_campana(campana, placa, fase, piso=0.35):
    """Riesgo segun lo que se pide afuera, con el signo de la fase.

    En positiva se invierte: la que mas campana junta es la mas segura. Quien
    no tiene consigna no vale cero — no haber sido medida no es lo mismo que
    haber medido cero — sino el piso, que es lo que vale una desconocida.
    """
    idx = (campana or {}).get("indice") or {}
    fuerza = {}
    for n in placa:
        v = (idx.get(n) or {}).get("icd")
        fuerza[n] = piso if v is None else abs(v)
    if fase == "positivo":
        # riesgo = falta de apoyo
        mx = max(fuerza.values()) if fuerza else 1.0
        crudo = {n: (mx - v) + piso for n, v in fuerza.items()}
    else:
        crudo = {n: v + piso for n, v in fuerza.items()}
    s = sum(crudo.values())
    return {n: v / s for n, v in crudo.items()} if s else {n: 1 / len(placa) for n in placa}


def main():
    act = _leer("actualidad.json")
    G = act.get("proxima_gala") or {}
    placa = G.get("placa") or []
    if not placa:
        print("sin placa vigente: no hay cruce que calcular")
        return 0
    fase = ((act.get("tendencias") or {}).get("fase")
            or (G.get("fases") or [{}])[-1].get("signo"))
    if fase not in ("negativo", "positivo"):
        raise SystemExit("sin fase no se puede cruzar nada: el signo lo pone la placa")

    sen = _leer("sentimiento.json")
    camp = _leer("campana.json")
    r = cercania(G.get("fecha"))
    w_sen = W0 + (W1 - W0) * r
    w_camp = 1 - w_sen

    rs = riesgo_sentimiento(sen.get("por_jugadora"), placa)
    rc = riesgo_campana(camp, placa, fase)
    p = {n: w_sen * rs[n] + w_camp * rc[n] for n in placa}
    s = sum(p.values())
    p = {n: round(v / s, 4) for n, v in p.items()}
    orden = sorted(p, key=lambda n: -p[n])

    ahora = dt.datetime.now(ART)
    gala = dt.datetime.fromisoformat(f"{G['fecha']}T22:15:00-03:00")
    faltan = max(0.0, (gala - ahora).total_seconds() / 3600.0)

    salida = {
        "generado": ahora.strftime("%Y-%m-%dT%H:%M%z"),
        "gala": G.get("gala"), "fecha_gala": G.get("fecha"), "placa": placa, "fase": fase,
        "que_es": ("El cruce entre lo que la gente escribe y lo que se pide afuera, pesado por "
                   "lo cerca que está la gala: cuanto menos falta, más pesa el sentimiento."),
        "reloj": {"faltan_horas": round(faltan, 1), "cercania": round(r, 3),
                  "horizonte_horas": HORIZONTE_H},
        "pesos": {"sentimiento": round(w_sen, 3), "campana": round(w_camp, 3),
                  "_nota": (f"A una semana el sentimiento pesa {W0:.0%} y en la noche de la gala "
                            f"{W1:.0%}. La campaña baja de {1-W0:.0%} a {1-W1:.0%}: baja, pero "
                            "no se apaga.")},
        "entradas": {"sentimiento": {n: round(rs[n], 4) for n in orden},
                     "campana": {n: round(rc[n], 4) for n in orden}},
        "p_sale": p,
        "llama_a": orden[0],
        "coinciden": None,
        "aviso": ("Declarado antes de la gala 32 y sin ningún acierto todavía. Se puntúa como "
                  "las otras tres, también cuando falle."),
    }
    (ROOT / "data" / "cruce.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1))

    # Se congela como las otras tres. Sin esto no se puede puntuar despues.
    ph = ROOT / "data" / "historial_pronostico.json"
    H = json.loads(ph.read_text())
    reg = H.setdefault("cruces", [])
    entrada = {"gala": G.get("gala"), "fecha_gala": G.get("fecha"), "placa": placa,
               "p_sale": p, "escrita": salida["generado"], "llamada": orden[0],
               "pesos": salida["pesos"], "fase": fase}
    # Cuando esto corre solo cada hora, guardar cada version llenaria el
    # registro de veinticuatro renglones por gala que dicen casi lo mismo: el
    # peso del reloj se mueve un poco cada hora y el numero con el. Se guarda
    # cuando cambia algo que un lector notaria — a quien senala, o mas de un
    # punto en alguien — y se descarta el resto. Asi el registro sigue contando
    # como se movio la cuenta durante la semana, que es lo interesante, sin
    # convertirse en un log.
    previas = [e for e in reg if e.get("gala") == G.get("gala")]
    def vale_la_pena(ant):
        if ant.get("llamada") != orden[0]:
            return True
        vieja = ant.get("p_sale") or {}
        return any(abs(p.get(n, 0) - vieja.get(n, 0)) > 0.01 for n in set(p) | set(vieja))
    if not previas or vale_la_pena(previas[-1]):
        reg.append(entrada)
        H.setdefault("_nota_cruces", (
            "El cruce entre sentimiento y campaña, congelado antes de cada gala como las otras "
            "tres. Cada entrada lleva los pesos que tenía el reloj en ese momento."))
        ph.write_text(json.dumps(H, ensure_ascii=False, indent=1))
        print(f"cruce congelado para la gala {G.get('gala')}: {orden[0]}")

    print(f"faltan {faltan:.1f} h · sentimiento {w_sen:.0%} · campaña {w_camp:.0%} · "
          f"fase {fase}")
    print(f"\n{'quien se va':<12} {'cruce':>7} {'sentim.':>8} {'campaña':>8}")
    for n in orden:
        print(f"{n:<12} {100*p[n]:6.1f}% {100*rs[n]:7.1f}% {100*rc[n]:7.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
