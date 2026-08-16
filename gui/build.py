# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
Inyecta los resultados del modelo en la plantilla HTML. Nada se transcribe a
mano: todo sale de data/. Correr despues de final_model.py y bootstrap.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
G = ROOT / "gui"
sys.path.insert(0, str(G))

from firma import firma_corrida                                    # noqa: E402
from marca import svg as marca_svg                                 # noqa: E402

ESCENARIOS = [
    ("base", "Caso base", "Todo el modelo tal como está especificado."),
    ("sin_encuesta", "Sin la encuesta", "La próxima gala se predice solo con preferencia revelada oficial."),
    ("psi_plano", "Sin apoyo positivo", "Se borra ψ: la final pasa a ser una lotería entre quienes lleguen."),
    ("kappa_0.4", "El rechazo resta en la final", "κ = +0,4: ser muy votado en contra penaliza también en el voto positivo."),
    ("kappa_-0.4", "El rechazo suma en la final", "κ = −0,4: el protagonismo conflictivo moviliza voto positivo."),
    ("4_finalistas", "Cuatro finalistas", "En vez de tres, como en 2024 y 2025."),
    ("beta_alto", "Final concentrada", "El voto de la final se reparte de forma muy desigual."),
    ("beta_bajo", "Final pareja", "El voto de la final se reparte de forma pareja."),
    ("deriva_alta", "Apoyo más volátil", "El apoyo positivo deriva más rápido de acá a la final."),
    ("base_rate_extranjeras", "Tasa base extranjera", "Ajuste por los dos campeones uruguayos consecutivos y el voto chileno recién habilitado."),
]

RANKING_1607 = ["Luana", "Juanicar", "Tamara", "Cinzia", "Charlotte", "Emanuel", "Pincoya",
                "Sol", "Yipio", "Zilli", "Campanita", "Cola", "Hanssen", "Mariela", "Majluf", "JC"]


NIVEL = {"bajo": 0, "medio": 1, "alto": 2}


def clasificar(valor, cortes):
    """Convierte un valor continuo en bajo/medio/alto segun dos cortes."""
    return "bajo" if valor < cortes[0] else ("alto" if valor > cortes[1] else "medio")


def analogos(res, casos):
    """
    Empareja a cada jugador con el caso historico mas parecido.

    Los ejes historicos estan documentados como bajo/medio/alto: nadie publico
    el reparto completo de las galas de 2024 y 2025, asi que no hay un mu ni un
    psi ajustado para esas temporadas. Se lleva entonces a los jugadores
    actuales a la misma escala ordinal, por terciles del plantel vigente.

    Dos cuidados:
      * Quien no tiene ninguna gala con reparto completo NO se clasifica por
        rechazo: su mu es el prior, no una medicion, y clasificarlo daria un
        "rechazo alto" que es puro artefacto de normalizacion. Se empareja solo
        por el eje de apoyo.
      * El eje de apoyo pesa mas (x1,5) porque es el discriminante que muestra
        la historia: bajo rechazo es necesario pero no suficiente.
      * Si hay empate, se devuelven los dos casos y la pagina dice "esta entre".
    """
    import statistics as st
    mu, psi, ngal = res["mu"], res["psi"], res["n_galas_negativas"]
    con_dato = [n for n in res["jugadores"] if ngal.get(n, 0) > 0]
    vm = sorted(mu[n] for n in con_dato)
    vp = sorted(psi.values())
    cm = tuple(st.quantiles(vm, n=3)) if len(vm) >= 3 else (0, 0)
    cp = tuple(st.quantiles(vp, n=3))

    out = {}
    for n in res["jugadores"]:
        sin_dato = ngal.get(n, 0) == 0
        r = None if sin_dato else clasificar(mu[n], cm)
        a = clasificar(psi[n], cp)
        puntuados = []
        for c in casos:
            d = 1.5 * abs(NIVEL[a] - NIVEL[c["apoyo"]])
            if r is not None:
                d += abs(NIVEL[r] - NIVEL[c["rechazo"]])
            puntuados.append((d, c))
        dmin = min(p[0] for p in puntuados)
        elegidos = [c for d, c in puntuados if d == dmin][:2]
        out[n] = {"rechazo": r, "apoyo": a, "casos": elegidos, "sin_dato_rechazo": sin_dato}
    return out


def cuotas_absolutas(g):
    """Reparto del voto en cuota sobre el total de la placa."""
    if not (g.get("completa") and g.get("versus")):
        return None
    resto = 1 - sum(g["salvados_cuota"].values()) / 100
    q = {k: v for k, v in g["salvados_cuota"].items()}
    for k, v in g["versus"].items():
        q[k] = round(v * resto, 2)
    return sorted(q.items(), key=lambda z: -z[1])


SITIO = "https://nerln.github.io/placa/"

# GoatCounter: codigo abierto, alojado en la UE, y guarda agregados por pagina y
# hora en vez de eventos por persona. No escribe ni lee nada en el equipo de
# quien visita, asi que no hace falta banner de consentimiento; el aviso va en
# la propia pagina, en la seccion "Como se mide esta pagina".
def analitica():
    """El script del contador, solo si el codigo esta registrado.

    Un codigo sin registrar devuelve 400, asi que emitirlo igual significaria
    una peticion fallida a un tercero en cada visita y un error en la consola de
    cada persona. El interruptor vive en data/analitica.json.
    """
    p = ROOT / "data" / "analitica.json"
    if not p.exists():
        return ""
    a = json.loads(p.read_text())
    if not a.get("registrado") or not a.get("codigo"):
        return ""
    return (f'<script data-goatcounter="https://{a["codigo"]}.goatcounter.com/count" '
            'async src="https://gc.zgo.at/count.js"></script>')


def meta(datos):
    """La cabecera del sitio: lo que se ve cuando alguien pega el enlace.

    Solo va en la version de GitHub Pages. La descripcion y la imagen se
    escriben con los numeros de la corrida, asi que despues de cada gala el
    enlace compartido dice el pronostico nuevo sin tocar nada a mano. El
    parametro ?v= de la imagen es la fecha de la ultima gala: obliga a X y a
    WhatsApp a volver a pedirla en vez de servir la cache de la semana pasada.
    """
    base = datos["escenarios"]["base"]["p_gana"]
    orden = sorted(base, key=lambda n: -base[n])[:3]
    lista = " · ".join(f"{n} {100*base[n]:.1f}%".replace(".", ",") for n in orden)
    titulo = "¿Quién gana Gran Hermano: Generación Dorada?"
    sims = (datos.get("ramas") or {}).get("n_sims", 0)
    desc = ((f"Pronóstico con {sims:,} simulaciones ".replace(",", ".") if sims else "Pronóstico ") +
            f"sobre {len(datos['galas'])} galas con el reparto de votos publicado. "
            f"Hoy: {lista}. Método, datos y código, abiertos.")
    og = SITIO + "og.png?v=" + datos["generado"]
    et = [
        ('<link rel="canonical" href="%s">' % SITIO),
        ('<meta name="description" content="%s">' % desc),
        ('<meta name="author" content="nerln">'),
        ('<meta property="og:type" content="article">'),
        ('<meta property="og:site_name" content="nerln">'),
        ('<meta property="og:locale" content="es_AR">'),
        ('<meta property="og:url" content="%s">' % SITIO),
        ('<meta property="og:title" content="%s">' % titulo),
        ('<meta property="og:description" content="%s">' % desc),
        ('<meta property="og:image" content="%s">' % og),
        ('<meta property="og:image:width" content="1200">'),
        ('<meta property="og:image:height" content="630">'),
        ('<meta name="twitter:card" content="summary_large_image">'),
        ('<meta name="twitter:creator" content="@nerellone">'),
        ('<meta name="twitter:title" content="%s">' % titulo),
        ('<meta name="twitter:description" content="%s">' % desc),
        ('<meta name="twitter:image" content="%s">' % og),
        ('<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">'),
        ('<meta name="theme-color" content="#EEF0F3" media="(prefers-color-scheme: light)">'),
        ('<meta name="theme-color" content="#05182F" media="(prefers-color-scheme: dark)">'),
        # No es un descargo legal, es un hecho que conviene que viaje con la
        # pagina: quien la indexe o la cite tiene que saber que no es oficial.
        ('<meta name="disclaimer" content="Analisis independiente. Sin relacion con Telefe, '
         'Kuarzo ni Banijay. Las marcas nombradas son de sus titulares.">'),
        ('<link rel="icon" href="ojo.svg" type="image/svg+xml">'),
        ('<link rel="apple-touch-icon" href="og.png">'),
        ('<link rel="license" href="https://creativecommons.org/licenses/by/4.0/">'),
        ('<script type="application/ld+json">%s</script>' % jsonld(datos, desc)),
    ]
    return "\n".join(et)


def jsonld(datos, desc):
    """Los metadatos de la pagina en el formato que leen los buscadores.

    Es lo que hace que, cuando un sistema use estos numeros para contestar algo,
    tenga a mano de quien son y bajo que licencia. Vale mas que cualquier aviso
    escondido: es un estandar que se lee de verdad, y va a la vista.
    """
    autor = {
        "@type": "Person", "@id": SITIO + "#nerln", "name": "nerln",
        "url": "https://github.com/nerln",
        "sameAs": ["https://github.com/nerln", "https://x.com/nerellone",
                   "https://nerln.pages.dev"],
    }
    articulo = {
        "@type": "Article",
        "@id": SITIO + "#articulo",
        "headline": "¿Quién gana Gran Hermano: Generación Dorada? Pronóstico y probabilidades",
        "description": desc,
        "inLanguage": "es-AR",
        "datePublished": "2026-08-08",
        "dateModified": datos["generado"] + "T23:00:00-03:00",
        "author": {"@id": SITIO + "#nerln"},
        "publisher": {"@id": SITIO + "#nerln"},
        "isBasedOn": {"@id": SITIO + "#datos"},
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "mainEntityOfPage": SITIO,
        "image": SITIO + "og.png",
        "about": [
            {"@type": "TVSeries", "name": "Gran Hermano Argentina"},
            {"@type": "TVSeason", "name": "Generación Dorada", "seasonNumber": 13},
        ],
        "citation": ("Resultados de votación publicados por Telefe en cada gala de "
                     "eliminación de la 13.ª edición"),
    }
    return json.dumps({
        "@context": "https://schema.org",
        "@graph": [autor, articulo, _dataset(datos, desc)],
    }, ensure_ascii=False, separators=(",", ":"))


def _dataset(datos, desc):
    return {
        "@type": "Dataset",
        "@id": SITIO + "#datos",
        "name": "Pronóstico de Gran Hermano Argentina — Generación Dorada (2026)",
        "description": desc,
        "url": SITIO,
        "sameAs": "https://github.com/nerln/placa",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "isAccessibleForFree": True,
        "dateModified": datos["generado"],
        "version": datos["corrida"],
        "inLanguage": "es-AR",
        "creator": {"@id": SITIO + "#nerln"},
        "citation": ("nerln, «placa: pronóstico de Gran Hermano Argentina» (2026), "
                     "https://github.com/nerln/placa"),
        "distribution": [{
            "@type": "DataDownload",
            "encodingFormat": "application/json",
            "contentUrl": SITIO + "datos.json",
        }],
    }


def main():
    res = json.loads((ROOT / "data" / "resultados.json").read_text())
    boot = json.loads((ROOT / "data" / "bootstrap.json").read_text())
    plantel = json.loads((ROOT / "data" / "plantel.json").read_text())
    galas = json.loads((ROOT / "data" / "galas.json").read_text())
    encuestas = json.loads((ROOT / "data" / "encuestas.json").read_text())
    hist = json.loads((ROOT / "data" / "analogos_historicos.json").read_text())
    ramas_p = ROOT / "data" / "ramas.json"
    ramas = json.loads(ramas_p.read_text()) if ramas_p.exists() else None
    evo_p = ROOT / "data" / "evolucion.json"
    evo = json.loads(evo_p.read_text()) if evo_p.exists() else None
    ult_p = ROOT / "data" / "ultimo.json"
    ultimo = json.loads(ult_p.read_text()) if ult_p.exists() else None
    ret_p = ROOT / "data" / "retro.json"
    retro = json.loads(ret_p.read_text()) if ret_p.exists() else None
    cmp_p = ROOT / "data" / "campana.json"
    campana = json.loads(cmp_p.read_text()) if cmp_p.exists() else None
    rei_p = ROOT / "data" / "reingresos.json"
    reingresos = json.loads(rei_p.read_text()) if rei_p.exists() else None
    sen_p = ROOT / "data" / "sendas.json"
    sendas = json.loads(sen_p.read_text()) if sen_p.exists() else None
    cam_p = ROOT / "data" / "camino.json"
    camino = json.loads(cam_p.read_text()) if cam_p.exists() else None
    act_p = ROOT / "data" / "actualidad.json"
    act = json.loads(act_p.read_text()) if act_p.exists() else None
    hp_p = ROOT / "data" / "historial_pronostico.json"
    corridas = json.loads(hp_p.read_text())["corridas"] if hp_p.exists() else []

    perfil = {j["apodo"]: j for j in plantel["jugadores"]}
    galas_completas = [
        {"gala": g["gala"], "fecha": g["fecha"], "eliminado": g["eliminado"],
         "reparto": cuotas_absolutas(g),
         # numeros TAL COMO LOS PUBLICA TELEFE, sin renormalizar: son los que
         # hacen visible la identidad aritmetica que valida la gala
         "publicado": {"salvados": g["salvados_cuota"], "versus": g["versus"]}}
        for g in galas["galas"] if cuotas_absolutas(g)]

    datos = {
        "generado": res["generado"],
        "corrida": firma_corrida(),
        "autor": "nerln · https://github.com/nerln/placa",
        "licencia": "CC-BY-4.0 · https://creativecommons.org/licenses/by/4.0/",
        "meta": res["meta"],
        "jugadores": res["jugadores"],
        "perfil": perfil,
        "ramas": ramas,
        "evolucion": evo,
        "camino": camino,
        "sendas": sendas,
        "reingresos": reingresos,
        "campana": campana,
        "retro": retro,
        "ultimo": ultimo,
        "actualidad": act,
        "historial_pronostico": corridas,
        "edicion": {k: plantel[k] for k in ("edicion", "temporada", "estreno", "premio")},
        "eliminados": plantel["eliminados_recientes"],
        "mu": res["mu"], "se_mu": res["se_mu"], "psi": res["psi"], "se_psi": res["se_psi"],
        "n_galas": res["n_galas_negativas"], "fases_psi": res["fases_psi"],
        "propension": res["propension_nominacion"],
        "placa28": res["placa28"], "estado28": res["estado28"],
        "placa_vigente": galas["placa_vigente"],
        "encuesta": encuestas["proxima"],
        "escenarios": res["escenarios"],
        "orden_escenarios": ESCENARIOS,
        "bootstrap": boot,
        "galas": galas_completas,
        # cuantas se miraron en total, para poder decir "9 de 11" sin escribirlo
        "galas_totales": len(galas["galas"]),
        "ranking1607": RANKING_1607,
        "analogos": analogos(res, hist["casos"]),
        "regla_historica": hist["_regla"],
        "ejes_historicos": hist["_ejes"],
    }
    tpl = (G / "plantilla.html").read_text()
    motor = (G / "animaciones.js").read_text()
    fuentes = (G / "fuentes.css").read_text()
    crudo = json.dumps(datos, ensure_ascii=False)
    # La marca se dibuja con los numeros de esta corrida, asi que despues de
    # cada gala el ojo de la cabecera tiene otro iris. Ver gui/marca.py.
    marca = marca_svg(res["escenarios"]["base"]["p_gana"], fondo=False, animar=True)

    # --- el sitio, para GitHub Pages -------------------------------------
    # Los datos salen a un archivo aparte en vez de ir incrustados. Sirve para
    # tres cosas: actualizar despues de una gala es reemplazar un archivo y no
    # reconstruir la pagina entera, el navegador puede cachear la pagina y
    # pedir solo los datos, y datos.json queda como un archivo publico que
    # cualquiera puede leer sin pasar por el HTML.
    #
    # Y trae un peligro que costo dos mananas: GitHub Pages sirve todo con
    # cache-control de diez minutos, asi que el navegador puede quedarse con un
    # datos.js viejo y pegarlo a un HTML nuevo. La pagina se dibuja entera y sin
    # un solo error, con los numeros de la semana pasada. Por eso el enlace
    # lleva la firma de la corrida: si los datos cambian, cambia la direccion, y
    # ninguna cache puede servir los de antes.
    WEB = ROOT / "web"
    WEB.mkdir(exist_ok=True)
    (WEB / "datos.json").write_text(crudo)
    (WEB / "datos.js").write_text("window.__DATOS = " + crudo + ";\n")
    cuerpo = (tpl.replace("/*__DATOS__*/null", "window.__DATOS")
                 .replace("/*__ANIMACIONES__*/", motor)
                 .replace("/*__FUENTES__*/", fuentes)
                 .replace("<!--__META__-->", meta(datos))
                 .replace("<!--__MARCA__-->", marca)
                 .replace("<!--__DATOS_SRC__-->",
                          f'<script src="datos.js?v={datos["corrida"]}"></script>')
                 # GSAP, servido desde web/vendor y no desde un CDN: la pagina
                 # publicada tampoco pide nada a terceros. Va con defer y lo
                 # unico que anima es el reordenamiento de "que movio la gala";
                 # si no carga, esa tabla se queda quieta y correcta. Solo el
                 # core: nada de ScrollTrigger ni de Flip, que esto se abre con
                 # datos moviles.
                 .replace("<!--__GSAP__-->",
                          '<script src="vendor/gsap.min.js" defer></script>')
                 # El contador solo vive en la pagina publicada. El artefacto
                 # autocontenido se queda sin ninguna llamada a terceros.
                 .replace("<!--__ANALITICA__-->", analitica()))
    # La plantilla nacio para un artefacto, donde el <head> lo pone el que
    # publica. Sirviendola nosotros hay que armar el documento entero: se corta
    # donde termina la hoja de estilos, y lo de arriba es cabeza y lo de abajo
    # cuerpo. Sin charset declarado el navegador adivina, y adivina mal con los
    # acentos; sin viewport el telefono renderiza a 980px y encoge todo.
    corte = cuerpo.index("</style>") + len("</style>")
    sitio = ('<!doctype html>\n<html lang="es">\n<head>\n'
             '<meta charset="utf-8">\n'
             '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
             + cuerpo[:corte] +
             '\n</head>\n<body>\n' + cuerpo[corte:] + '\n</body>\n</html>\n')
    (WEB / "index.html").write_text(sitio)

    # El sitemap de una sola pagina no sirve para que la encuentren: sirve de
    # reloj. lastmod sale de la fecha de la ultima gala, asi que es
    # comprobable contra la propia pagina, que es la condicion que pone Google
    # para hacerle caso.
    (WEB / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url>\n    <loc>{SITIO}</loc>\n'
        f'    <lastmod>{datos["generado"]}T23:00:00-03:00</lastmod>\n'
        '  </url>\n</urlset>\n')

    # --- el artefacto autocontenido, por si hace falta --------------------
    out = (tpl.replace("/*__DATOS__*/null", crudo)
              .replace("/*__ANIMACIONES__*/", motor)
              .replace("/*__FUENTES__*/", fuentes)
              .replace("<!--__META__-->", "")
              .replace("<!--__MARCA__-->", marca)
              .replace("<!--__DATOS_SRC__-->", "")
              .replace("<!--__GSAP__-->", "")
              .replace("<!--__ANALITICA__-->", ""))
    (G / "pronostico.html").write_text(out)

    nr = len(ramas["ramas"]) if ramas else 0
    print(f"escrito web/index.html ({len(sitio)/1024:.0f} KB) + web/datos.json "
          f"({len(crudo)/1024:.0f} KB) · gui/pronostico.html ({len(out)/1024:.0f} KB)")
    print(f"  {len(perfil)} en juego · {nr} ramas de la gala {datos['placa_vigente']['gala']}")


if __name__ == "__main__":
    main()
