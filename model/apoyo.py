# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
EL APOYO, AGREGADO DE VARIAS FUENTES Y CORREGIDO POR EXPOSICION.

EL PROBLEMA QUE RESUELVE. Hasta ahora el «apoyo» se leia de dos sitios y los dos
median mal:

  * Las consignas en tendencias estan CENSURADAS POR UMBRAL: trends24 publica el
    top-50 argentino, asi que quien no llega al puesto 50 no aparece. No vale
    cero: no se midio. Con cinco nombres, esta semana tres quedaron con una raya
    y de esas tres la campana no dice absolutamente nada. Un lector lo leyo y
    pregunto si jugaban solo dos.
  * Los comentarios cuentan bien el SIGNO pero su VOLUMEN no se puede comparar
    entre personas, porque depende de cuanto habla de cada una el canal. La
    pagina lo decia con estas palabras: «los volumenes NO se comparan entre
    jugadoras». Era honesto y era una renuncia.

QUE SE PROBO Y NO SIRVE, para que no se vuelva a probar:

  * Google Trends, endpoint comparativo (el que usa pytrends): devuelve 429 sin
    credenciales, y desde un runner de CI con IP compartida peor. Era la fuente
    obvia para tener un numero por persona sin umbral.
  * Google Trends, RSS de tendencias diarias: responde, pero publica solo lo que
    YA es tendencia. Es la misma censura por umbral con otro nombre.
  * Vistas de Wikipedia: la API es abierta y funciona, pero de las cinco de esta
    semana solo tres tienen articulo. Y las dos que faltan faltan PORQUE son
    menos conocidas, o sea que el hueco esta correlacionado con lo que se quiere
    medir: usarla castigaria justo a quien no logra medir. Peor que no tenerla.

LA IDEA. La exposicion es el denominador que faltaba. Cuantos videos publica el
canal sobre cada una, y cuantas visualizaciones juntan, es una medida SIN UMBRAL
y que cubre a todas. No mide apoyo — mide de quien decidio hablar la produccion —
pero es exactamente lo que hay que dividir para que el signo de los comentarios
se pueda comparar entre personas.

    apoyo = (a favor - en contra) / (a favor + en contra)      el signo, limpio
    peso  = comentarios con signo / exposicion                 cuanto se habla
                                                               de ella por video

REGLA QUE NO SE ROMPE: ninguna fuente se imputa. Si una no cubre a alguien, esa
persona no recibe un valor inventado: la fuente declara su cobertura y el
agregado dice con cuantas fuentes se calculo cada fila. Una media de tres
fuentes y una media de una no son el mismo numero y no se dibujan igual.

    python3 model/apoyo.py
"""

from __future__ import annotations

import datetime as dt
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = dt.timezone(dt.timedelta(hours=-3))


def _leer(n):
    p = ROOT / "data" / n
    return json.loads(p.read_text()) if p.exists() else {}


def _plano(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).upper())
                   if unicodedata.category(c) != "Mn")


CANAL = "https://www.youtube.com/channel/UCFAiSCNaJnizLNIF1aSkQAQ/videos"
UA = {"User-Agent": "Mozilla/5.0 (compatible; placa/1.0; +https://github.com/nerln/placa)"}


def _texto(o, out):
    """Junta todos los strings de una rama, sin saber su forma exacta.

    YouTube cambia la forma de este JSON cada tanto — hoy es lockupViewModel,
    antes era videoRenderer — y un lector que dependa de la ruta exacta se
    rompe en silencio la semana que la cambien. Se junta el texto y se busca el
    nombre adentro: menos preciso, mucho mas duradero.
    """
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("content", "simpleText", "text") and isinstance(v, str):
                out.append(v)
            else:
                _texto(v, out)
    elif isinstance(o, list):
        for v in o:
            _texto(v, out)
    return out


def bajar_canal():
    """Titulos y vistas de los videos recientes del canal, o [] si no se pudo.

    Es la unica fuente que cubre a TODAS sin umbral, y por eso se intenta; pero
    si YouTube cambia de forma o no responde, se devuelve vacio y el agregado
    declara que no hubo exposicion. Nunca se inventa.
    """
    import urllib.request
    try:
        h = urllib.request.urlopen(
            urllib.request.Request(CANAL, headers=UA), timeout=40).read().decode("utf-8", "replace")
        d = json.loads(re.search(r"var ytInitialData = (\{.*?\});</script>", h, re.S).group(1))
    except Exception:
        return []
    items, pila = [], [d]
    while pila:
        x = pila.pop()
        if isinstance(x, dict):
            if "richItemRenderer" in x:
                items.append(x["richItemRenderer"])
            pila.extend(x.values())
        elif isinstance(x, list):
            pila.extend(x)
    out = []
    for it in items:
        t = _texto(it, [])
        if not t:
            continue
        titulo = max(t, key=len)
        vistas = 0
        for s2 in t:
            m = re.match(r"^([\d.,]+)\s*(mil|M)?\s+(vistas|visualizaciones|views)", s2, re.I)
            if m:
                n = float(m.group(1).replace(".", "").replace(",", "."))
                vistas = int(n * (1000 if (m.group(2) or "").lower() == "mil"
                                  else 1_000_000 if m.group(2) == "M" else 1))
                break
        out.append({"titulo": titulo, "vistas": vistas})
    return out


def exposicion(videos, placa, alias):
    """De quien habla el canal, y cuanto se ve. Sin umbral: cubre a todas.

    NO es apoyo. Que el canal publique veintiun videos sobre alguien puede
    querer decir que es el centro del conflicto, no que la quieran. Se usa como
    DENOMINADOR, para que el signo de los comentarios deje de depender de cuanto
    se hablo de cada una.
    """
    out = {n: {"titulos": 0, "vistas": 0} for n in placa}
    for v in videos:
        t = _plano(v.get("titulo") or v.get("que") or "")
        vistas = int(v.get("vistas") or 0)
        # Sin `break`: un video que nombra a dos cuenta para las dos. Con el
        # break, «Charla intima entre Luana y Charlotte» se le atribuia solo a
        # la primera del orden de la placa, y Charlotte aparecia con CERO
        # exposicion teniendo videos suyos en la lista. La exposicion es «de
        # quien se habla», no «de quien se habla primero».
        for n in placa:
            if any(re.search(r"\b" + re.escape(_plano(a)) + r"\b", t)
                   for a in ([n] + alias.get(n, []))):
                out[n]["titulos"] += 1
                out[n]["vistas"] += vistas
    return out


def main():
    act = _leer("actualidad.json")
    G = act.get("proxima_gala") or {}
    placa = G.get("placa") or []
    if not placa:
        print("sin placa vigente: no hay a quien medirle el apoyo")
        return 0
    fase = ((act.get("tendencias") or {}).get("fase")
            or (G.get("fases") or [{}])[-1].get("signo") or "")

    sen = _leer("sentimiento.json")
    por = sen.get("por_jugadora") or {}
    camp = (_leer("campana.json").get("indice")) or {}
    # La exposicion se lee del canal entero, no del punado de videos del que se
    # bajaron comentarios: si el denominador saliera del mismo sitio que el
    # numerador, dividir no corregiria nada.
    vids = bajar_canal()
    del_canal = bool(vids)
    if not vids:
        vids = (_leer("videos.json").get("videos")) or []
    alias = _leer("alias.json") or {}

    exp = exposicion(vids, placa, alias)
    max_tit = max([e["titulos"] for e in exp.values()] or [0])

    filas = {}
    for n in placa:
        k = por.get(n) or {}
        con, fav = k.get("contra", 0), k.get("favor", 0)
        firmados = con + fav
        # El signo, entre -1 y +1, suavizado para que dos comentarios no griten
        # como doscientos.
        signo = ((fav + 1) - (con + 1)) / (fav + con + 2)
        e = exp[n]
        # Cuanto se habla de ella EN RELACION a cuanto el canal la muestra.
        # Sin exposicion no se divide: se declara que no se puede.
        por_video = round(firmados / e["titulos"], 2) if e["titulos"] else None
        fuentes = []
        if firmados >= 6:
            fuentes.append("comentarios")
        if e["titulos"]:
            fuentes.append("exposicion")
        if (camp.get(n) or {}).get("icd") is not None:
            fuentes.append("campaña")
        filas[n] = {
            "signo": round(signo, 3),
            "a_favor": fav, "en_contra": con, "con_signo": firmados,
            "titulos": e["titulos"], "vistas": e["vistas"],
            "comentarios_por_video": por_video,
            "campana": (camp.get(n) or {}).get("icd"),
            "fuentes": fuentes, "n_fuentes": len(fuentes),
        }

    orden = sorted(placa, key=lambda n: -filas[n]["signo"])
    salida = {
        "generado": dt.datetime.now(ART).strftime("%Y-%m-%dT%H:%M%z"),
        "gala": G.get("gala"), "fase": fase, "placa": placa, "orden": orden,
        "que_es": ("El apoyo, juntando lo que se escribe con cuánto habla de cada una el canal. "
                   "El signo sale de los comentarios; la exposición es el denominador que hace "
                   "que ese signo se pueda comparar entre personas."),
        "que_no_es": ("La exposición NO es apoyo: que el canal publique veintiún videos sobre "
                      "alguien puede querer decir que es el centro del conflicto, no que la "
                      "quieran. Por eso entra como denominador y nunca como puntaje."),
        "cobertura": {
            "comentarios": [n for n in placa if "comentarios" in filas[n]["fuentes"]],
            "exposicion": [n for n in placa if "exposicion" in filas[n]["fuentes"]],
            "campaña": [n for n in placa if "campaña" in filas[n]["fuentes"]],
        },
        "descartadas": [
            {"fuente": "Google Trends (endpoint comparativo)",
             "por_que": "devuelve 429 sin credenciales, y peor desde un runner de CI"},
            {"fuente": "Google Trends (RSS de tendencias)",
             "por_que": "publica sólo lo que ya es tendencia: la misma censura por umbral"},
            {"fuente": "Vistas de Wikipedia",
             "por_que": ("de las cinco de esta semana sólo tres tienen artículo, y las dos que "
                         "faltan faltan porque son menos conocidas: el hueco está correlacionado "
                         "con lo que se quiere medir")},
        ],
        "filas": filas,
        "max_titulos": max_tit,
    }
    (ROOT / "data" / "apoyo.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1))

    salida["exposicion_del_canal"] = del_canal
    salida["_nota_exposicion"] = (
        "Leída del canal entero" if del_canal
        else "NO se pudo leer el canal: la exposición sale sólo de los videos del corpus de "
             "comentarios, que es el mismo sitio del que sale el signo. Dividir por eso corrige "
             "menos de lo que parece, y por eso queda declarado.")
    (ROOT / "data" / "apoyo.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1))
    print(f"fase {fase} · {len(vids)} videos de exposición" +
          ("" if del_canal else "  (del corpus, NO del canal)"))
    print(f"\n{'quien':<12} {'signo':>7} {'a favor':>8} {'contra':>7} {'videos':>7} "
          f"{'com/video':>10}  fuentes")
    for n in orden:
        f = filas[n]
        pv = "—" if f["comentarios_por_video"] is None else f"{f['comentarios_por_video']:.2f}"
        print(f"{n:<12} {f['signo']:+7.2f} {f['a_favor']:8} {f['en_contra']:7} "
              f"{f['titulos']:7} {pv:>10}  {f['n_fuentes']} ({', '.join(f['fuentes'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
