# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
Lo que se publica tiene que salir de lo que esta publicado.

Es la unica prueba que corre antes de desplegar, y contesta una sola pregunta:
la pagina que hay en web/ se puede reconstruir a partir de data/ tal como esta
en el repositorio? Si alguien edita un numero a mano en el HTML, o commitea
data/ nuevo sin volver a construir, esto falla y la pagina no sale.

Ademas comprueba lo que haria falso el resultado sin romper nada visible:

  * las probabilidades de ganar suman 1
  * las ramas ponderadas por su probabilidad devuelven el caso base (asi
    estan construidas: son el mismo Monte Carlo particionado, no una
    simulacion aparte, y si no cierran es que dejaron de serlo)
  * cada gala declarada completa cumple la identidad aritmetica de Telefe
  * la tarjeta de previsualizacion es de esta corrida y no de la anterior
  * la firma de la corrida coincide en todos los canales donde viaja
  * la prosa escrita a mano es de la gala que viene y no de la anterior
  * el guion de la pagina parsea
  * el <style> no tiene JavaScript dentro

Las dos ultimas no comprueban ningun dato: comprueban que la pagina no este
rota de una forma que no cambia ningun dato y por eso no la ve nadie mas.

    python3 gui/verificar.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
TOL_SUMA = 1e-9
TOL_RAMAS = 5e-4          # las ramas se guardan redondeadas al escribir el JSON
TOL_IDENTIDAD = 0.6       # Telefe publica con un decimal y a veces redondea feo


def fallo(msg):
    print("  FALLA · " + msg)
    return 1


def reconstruible():
    """Vuelve a construir la pagina y compara byte a byte con la publicada."""
    antes = {p.name: p.read_bytes() for p in WEB.glob("*")
             if p.suffix in (".html", ".json", ".js")}
    subprocess.run([sys.executable, str(ROOT / "gui" / "build.py")],
                   check=True, capture_output=True)
    malos = [n for n, b in antes.items() if (WEB / n).read_bytes() != b]
    if malos:
        return fallo("web/ no coincide con lo que produce gui/build.py: " +
                     ", ".join(sorted(malos)) + ". Correr gui/build.py y commitear.")
    print(f"  ok · web/ reconstruible ({len(antes)} archivos)")
    return 0


def probabilidades():
    res = json.loads((ROOT / "data" / "resultados.json").read_text())
    err = 0
    for nombre, esc in res["escenarios"].items():
        s = sum(esc["p_gana"].values())
        if abs(s - 1) > TOL_SUMA:
            err += fallo(f"p_gana del escenario {nombre} suma {s!r}")
    if not err:
        print(f"  ok · {len(res['escenarios'])} escenarios suman 1")
    return err


def ramas_cierran():
    p = ROOT / "data" / "ramas.json"
    if not p.exists():
        print("  (sin data/ramas.json: no hay nada que comprobar)")
        return 0
    R = json.loads(p.read_text())
    # La ley de probabilidad total solo se puede exigir si las ramas particionan
    # todas las salidas posibles. Cuando no hay placa, ramas.py publica solo las
    # salidas con probabilidad apreciable y la cobertura queda por debajo de 1:
    # ahi la suma no tiene por que dar el caso base, y exigirlo seria inventar
    # una identidad que no existe.
    cobertura = sum(r["p_sale"] for r in R["ramas"].values())
    if abs(cobertura - 1) > 1e-6:
        print(f"  (ramas parciales: cubren el {100*cobertura:.1f}% de las salidas, "
              f"no hay identidad que comprobar)")
        return 0
    err = 0
    peor = 0.0
    for quien in R["jugadores"]:
        recompuesto = sum(r["p_sale"] * r["p_gana"][quien] for r in R["ramas"].values())
        d = abs(recompuesto - R["base"]["p_gana"][quien])
        peor = max(peor, d)
        if d > TOL_RAMAS:
            err += fallo(f"la rama de {quien} no recompone el caso base (Δ={d:.5f})")
    if not err:
        print(f"  ok · {len(R['ramas'])} ramas recomponen el caso base (peor Δ={peor:.2e})")
    return err


def identidad_telefe():
    """suma publicada − 100 = suma de las cuotas que no son del versus.

    Es la firma que prueba que la lista de nominados de esa gala esta completa:
    Telefe renormaliza al 100% solo el mano a mano final, asi que el excedente
    tiene que ser exactamente lo que se llevaron los que salieron antes."""
    G = json.loads((ROOT / "data" / "galas.json").read_text())
    err = 0
    n = 0
    for g in G["galas"]:
        if not (g.get("completa") and g.get("versus")):
            continue
        n += 1
        publicado = sum(g["salvados_cuota"].values()) + sum(g["versus"].values())
        d = abs((publicado - 100) - sum(g["salvados_cuota"].values()))
        if d > TOL_IDENTIDAD:
            err += fallo(f"la gala {g['gala']} se declara completa y no cierra (Δ={d:.2f})")
    if not err:
        print(f"  ok · {n} galas completas cumplen la identidad de Telefe")
    return err


def tarjeta_al_dia():
    """La previsualizacion del enlace tiene que ser de esta corrida.

    build.py no la toca, asi que se puede reconstruir la pagina y olvidarse de
    tarjeta.py: la pagina diria una cosa y el enlace compartido otra, sin que
    nada se rompa. Por eso tarjeta.py deja la firma de la corrida dentro del
    PNG y aca se lee. Se compara la firma, no los pixeles: el rasterizado
    depende de la version de la libreria y compararlo daria falsos negativos.
    """
    png = WEB / "og.png"
    if not png.exists():
        return fallo("falta web/og.png: correr gui/tarjeta.py")
    from PIL import Image                                       # noqa: PLC0415
    sys.path.insert(0, str(ROOT / "gui"))
    from tarjeta import firma                                   # noqa: PLC0415

    res = json.loads((ROOT / "data" / "resultados.json").read_text())
    esperada = firma(res["escenarios"]["base"]["p_gana"], res["generado"])
    tiene = Image.open(png).text.get("corrida", "")
    if tiene != esperada:
        return fallo("web/og.png se dibujo con otra corrida.\n"
                     f"    tiene:   {tiene or '(sin firma)'}\n"
                     f"    espera:  {esperada}\n"
                     "    Correr gui/tarjeta.py.")
    print("  ok · web/og.png es de esta corrida")
    return 0


def apuesta_de_esta_placa():
    """La apuesta publicada tiene que ser sobre la placa vigente.

    El 29 de agosto de 2026 la pagina llego a decir «La apuesta dice Tamara»
    cinco dias despues de que Tamara saliera: data/apuesta.json era el de la
    placa anterior y nadie lo miraba, porque ninguna comprobacion cruzaba las
    dos listas. Un pronostico sobre gente que ya no esta no es un pronostico
    viejo, es un pronostico falso, y encima es el que la pagina muestra primero.
    """
    ap = ROOT / "data" / "apuesta.json"
    if not ap.exists():
        print("  (sin data/apuesta.json: no hay apuesta que comprobar)")
        return 0
    A = json.loads(ap.read_text())
    G = json.loads((ROOT / "data" / "galas.json").read_text())
    pv = G.get("placa_vigente") or {}
    vigente = set(pv.get("integrantes") or [])
    if not vigente:
        print("  (sin placa vigente: no se comprueba la apuesta)")
        return 0
    dentro = set(A.get("placa") or [])
    sobra = sorted(dentro - vigente)
    falta = sorted(vigente - dentro)
    if sobra or falta:
        return fallo(
            "data/apuesta.json es de otra placa. "
            + (f"Nombra a {', '.join(sobra)}, que no esta(n) en la placa vigente. " if sobra else "")
            + (f"No nombra a {', '.join(falta)}, que si esta(n). " if falta else "")
            + f"Placa vigente (gala {pv.get('gala')}): {', '.join(sorted(vigente))}. "
              "Correr model/apuesta.py, o borrar data/apuesta.json si esta placa no tiene apuesta.")
    if A.get("gala") is not None and pv.get("gala") is not None and A["gala"] != pv["gala"]:
        return fallo(f"data/apuesta.json dice gala {A['gala']} y la placa vigente es la "
                     f"{pv['gala']}. Correr model/apuesta.py.")
    print(f"  ok · la apuesta es de la placa vigente ({len(dentro)} nominadas)")
    return 0


def textos_al_dia():
    """La prosa escrita a mano tiene que ser de la gala que viene.

    Es el unico agujero que reconstruible() no puede ver, y no lo ve por como
    esta hecha: compara la pagina contra lo que produce build.py, o sea contra
    si misma, asi que un parrafo de la gala anterior se reproduce byte a byte
    con total fidelidad. La semana del 17 de agosto salieron cuatro textos de la
    gala 29 describiendo la placa de la 30 -«la placa de esta noche es de 6»
    arriba de seis nominadas nuevas, «las cinco salidas» arriba de una lista de
    seis- y las diez comprobaciones de este archivo dijeron que todo cerraba.

    data/textos.json anota para que gala se escribio cada bloque a mano. Aca se
    compara con la gala vigente y nada mas. No prohibe prosa, que rechazaria la
    plantilla entera: prohibe prosa vencida.
    """
    p = ROOT / "data" / "textos.json"
    if not p.exists():
        print("  (sin data/textos.json: no hay prosa inventariada)")
        return 0
    bloques = json.loads(p.read_text())["bloques"]
    act = json.loads((ROOT / "data" / "actualidad.json").read_text())
    vigente = (act.get("proxima_gala") or {}).get("gala")
    if not vigente:
        # De respaldo galas.json, que es de donde sale la placa que se dibuja.
        # Entre una gala y la nominacion siguiente, actualidad.json puede
        # quedarse sin proxima_gala y la lista no se puede comprobar contra nada.
        G = json.loads((ROOT / "data" / "galas.json").read_text())
        vigente = (G.get("placa_vigente") or {}).get("gala")
    if not vigente:
        return fallo("no hay gala vigente en actualidad.json ni en galas.json: "
                     "sin ella no se puede saber que prosa vencio.")
    a_mano = [b for b in bloques if b.get("estado") == "a mano"]
    viejos = sorted((b for b in a_mano if b.get("gala", 0) < vigente),
                    key=lambda b: (b["gala"], b["id"]))
    if viejos:
        det = "".join(f"\n    · {b['id']} · escrito para la gala {b['gala']} · {b['donde']}"
                      f"\n      «{b['recorte']}»" for b in viejos)
        return fallo(f"{len(viejos)} bloque(s) de prosa quedaron en una gala anterior "
                     f"a la {vigente}:" + det +
                     "\n    Para cada uno, una de dos: reescribirlo para la gala "
                     f"{vigente} y subirle «gala» en data/textos.json, o derivarlo del "
                     "campo que ya tiene el dato y borrarle el renglon de la lista. "
                     "Subir el numero sin tocar el texto no arregla nada.")
    print(f"  ok · {len(a_mano)} bloques de prosa a mano, todos de la gala {vigente}")
    return 0


def javascript_valido():
    """El guion de la pagina tiene que parsear.

    Esta comprobacion existe porque ya paso: una edicion dejo una llave de mas,
    el HTML se construyo sin quejarse, la pagina se veia bien -todo lo que se
    dibuja del lado del servidor seguia ahi- y el guion entero estaba muerto.
    Ninguna otra comprobacion lo veia: web/ era reconstruible, los numeros
    cerraban, la firma coincidia. Un error de sintaxis no cambia ningun dato.
    """
    html = (WEB / "index.html").read_text()
    i = html.rindex("<script>") + len("<script>")
    j = html.rindex("</script>")
    tmp = ROOT / "web" / ".guion.js"
    tmp.write_text(html[i:j])
    try:
        r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    except FileNotFoundError:
        tmp.unlink(missing_ok=True)
        print("  (sin node: no se comprueba la sintaxis del guion)")
        return 0
    tmp.unlink(missing_ok=True)
    if r.returncode:
        return fallo("el guion de web/index.html no parsea:\n    " +
                     r.stderr.strip().splitlines()[-1][:160])
    print(f"  ok · el guion parsea ({(j - i)/1024:.0f} KB)")
    return 0


def css_sin_javascript():
    """La hoja de estilos no puede tener JavaScript dentro.

    Pasó tres veces en la misma tanda y siempre igual: los bloques del archivo
    se separan con comentarios del tipo /* ---------- nombre ---------- */, y
    varios de esos nombres existen dos veces, una en el CSS y otra en el JS.
    Insertar código buscando el marcador acierta el equivocado, el navegador se
    traga cincuenta líneas de JavaScript como CSS inválido sin decir una
    palabra, y la funcionalidad simplemente no aparece. Ninguna otra
    comprobación lo ve: el HTML es válido, los datos están, la firma coincide.

    Se buscan formas que no existen en CSS y sí en este guion.
    """
    html = (WEB / "index.html").read_text()
    css = html[html.index("<style>"):html.index("</style>")]
    sospechas = ['$("#', "function ", "=> {", "addEventListener", "innerHTML"]
    hallados = [x for x in sospechas if x in css]
    if hallados:
        i = css.index(hallados[0])
        return fallo("hay JavaScript dentro del <style>: " + ", ".join(hallados) +
                     "\n    …" + css[max(0, i-90):i+90].replace("\n", " ") + "…")
    print(f"  ok · el <style> es solo CSS ({len(css)/1024:.0f} KB)")
    return 0


def firma_coherente():
    """La firma de la corrida tiene que ser la misma en los cuatro canales.

    Es lo que permite demostrar que una copia salio de aca sin recurrir a
    canarios escondidos, que no sobreviven a un reformateo. Se recalcula desde
    data/ y se compara con lo que quedo publicado: si no coincide, alguien
    edito los datos sin reconstruir, o al reves.
    """
    sys.path.insert(0, str(ROOT / "gui"))
    from firma import firma_corrida                              # noqa: PLC0415

    esperada = firma_corrida()
    err = 0
    en_datos = json.loads((WEB / "datos.json").read_text()).get("corrida")
    if en_datos != esperada:
        err += fallo(f"web/datos.json dice corrida={en_datos!r} y los datos dan {esperada!r}")

    png = WEB / "og.png"
    if png.exists():
        from PIL import Image                                    # noqa: PLC0415
        if esperada not in Image.open(png).text.get("corrida", ""):
            err += fallo(f"web/og.png no lleva la firma {esperada!r}")
    if not err:
        print(f"  ok · firma de la corrida {esperada} en datos.json y og.png")
    return err


def riesgo_coherente():
    """El riesgo de salir se estima dos veces y las dos alimentan la pagina.

    El caso base lo saca de su corrida y las ramas de la suya, que tiene mas
    simulaciones. Son dos estimaciones del mismo numero, asi que difieren en
    decimas y la pagina muestra una sola. Si alguna vez se separan de mas es que
    dejaron de estimar lo mismo, y eso hay que verlo antes de publicar y no
    despues de que alguien encuentre dos cifras distintas para lo mismo.
    """
    pd = ROOT / "data" / "resultados.json"
    pr = ROOT / "data" / "ramas.json"
    if not (pd.exists() and pr.exists()):
        print("  (sin ramas o sin resultados: no hay nada que cotejar)")
        return 0
    base = (json.loads(pd.read_text()).get("escenarios") or {}).get("base", {}).get("p_sale28")
    ramas = json.loads(pr.read_text()).get("ramas") or {}
    if not base or not ramas:
        print("  (sin riesgo por rama: no hay nada que cotejar)")
        return 0
    d, quien = max((abs(base.get(n, 0.0) - r["p_sale"]), n) for n, r in ramas.items())
    # 0,6 puntos: bastante mas que el error de muestreo de dos corridas de este
    # tamano, y bastante menos que cualquier discrepancia real de modelo.
    if d > 0.006:
        print(f"  FALLA · el caso base y las ramas discrepan en {100*d:.2f} puntos "
              f"para {quien}: dejaron de estimar lo mismo.")
        return 1
    print(f"  ok · las dos estimaciones del riesgo coinciden "
          f"(peor {quien}, {100*d:.2f} puntos)")
    return 0


def datos_sin_cache():
    """El HTML tiene que pedir los datos de esta corrida y no «los datos».

    GitHub Pages sirve con cache-control de diez minutos. Sin firma en la
    direccion, un navegador puede pegar un datos.js viejo a un HTML nuevo: la
    pagina se dibuja entera, sin un solo error en la consola, con los numeros de
    la semana pasada. Es el peor fallo posible de esta pagina, porque no se ve.
    """
    idx = ROOT / "web" / "index.html"
    dj = ROOT / "web" / "datos.json"
    if not (idx.exists() and dj.exists()):
        print("  (sin web/: no hay nada que comprobar)")
        return 0
    corrida = json.loads(dj.read_text()).get("corrida", "")
    html = idx.read_text()
    esperado = f'src="datos.js?v={corrida}"'
    if esperado not in html:
        m = re.search(r'src="datos\.js[^"]*"', html)
        print(f"  FALLA · el HTML pide {m.group(0) if m else 'datos.js de otra forma'} "
              f"y esta corrida es {corrida}: una cache puede servir datos viejos.")
        return 1
    print(f"  ok · el HTML pide los datos de esta corrida ({corrida})")
    return 0


def main():
    print("verificando lo que se va a publicar")
    err = (reconstruible() + probabilidades() + ramas_cierran() +
           identidad_telefe() + tarjeta_al_dia() + firma_coherente() +
           riesgo_coherente() + datos_sin_cache() + apuesta_de_esta_placa() +
           textos_al_dia() +
           javascript_valido() + css_sin_javascript())
    if err:
        print(f"\n{err} comprobacion(es) fallaron: no se publica")
        sys.exit(1)
    print("\ntodo cierra")


if __name__ == "__main__":
    main()
