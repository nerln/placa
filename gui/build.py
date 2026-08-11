# SPDX-FileCopyrightText: 2026 Eugenio Nerelli <kira_and_light@hotmail.it>
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
        ('<meta name="author" content="Eugenio Nerelli">'),
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
        ('<meta name="theme-color" content="#141a1e">'),
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
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Pronóstico de Gran Hermano Argentina — Generación Dorada (2026)",
        "description": desc,
        "url": SITIO,
        "sameAs": "https://github.com/nerln/placa",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "isAccessibleForFree": True,
        "dateModified": datos["generado"],
        "version": datos["corrida"],
        "inLanguage": "es-AR",
        "creator": {
            "@type": "Person",
            "name": "Eugenio Nerelli",
            "url": "https://nerln.pages.dev",
            "sameAs": ["https://github.com/nerln", "https://x.com/nerellone"],
        },
        "citation": ("Eugenio Nerelli, «placa: pronóstico de Gran Hermano Argentina» "
                     "(2026), https://github.com/nerln/placa"),
        "distribution": [{
            "@type": "DataDownload",
            "encodingFormat": "application/json",
            "contentUrl": SITIO + "datos.json",
        }],
    }, ensure_ascii=False, separators=(",", ":"))


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
        "autor": "Eugenio Nerelli · https://github.com/nerln/placa",
        "licencia": "CC-BY-4.0 · https://creativecommons.org/licenses/by/4.0/",
        "meta": res["meta"],
        "jugadores": res["jugadores"],
        "perfil": perfil,
        "ramas": ramas,
        "evolucion": evo,
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
        "ranking1607": RANKING_1607,
        "analogos": analogos(res, hist["casos"]),
        "regla_historica": hist["_regla"],
        "ejes_historicos": hist["_ejes"],
    }
    tpl = (G / "plantilla.html").read_text()
    motor = (G / "animaciones.js").read_text()
    fuentes = (G / "fuentes.css").read_text()
    crudo = json.dumps(datos, ensure_ascii=False)

    # --- el sitio, para GitHub Pages -------------------------------------
    # Los datos salen a un archivo aparte en vez de ir incrustados. Sirve para
    # tres cosas: actualizar despues de una gala es reemplazar un archivo y no
    # reconstruir la pagina entera, el navegador puede cachear la pagina y
    # pedir solo los datos, y datos.json queda como un archivo publico que
    # cualquiera puede leer sin pasar por el HTML.
    WEB = ROOT / "web"
    WEB.mkdir(exist_ok=True)
    (WEB / "datos.json").write_text(crudo)
    (WEB / "datos.js").write_text("window.__DATOS = " + crudo + ";\n")
    cuerpo = (tpl.replace("/*__DATOS__*/null", "window.__DATOS")
                 .replace("/*__ANIMACIONES__*/", motor)
                 .replace("/*__FUENTES__*/", fuentes)
                 .replace("<!--__META__-->", meta(datos))
                 .replace("<!--__DATOS_SRC__-->", '<script src="datos.js"></script>'))
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

    # --- el artefacto autocontenido, por si hace falta --------------------
    out = (tpl.replace("/*__DATOS__*/null", crudo)
              .replace("/*__ANIMACIONES__*/", motor)
              .replace("/*__FUENTES__*/", fuentes)
              .replace("<!--__META__-->", "")
              .replace("<!--__DATOS_SRC__-->", ""))
    (G / "pronostico.html").write_text(out)

    nr = len(ramas["ramas"]) if ramas else 0
    print(f"escrito web/index.html ({len(sitio)/1024:.0f} KB) + web/datos.json "
          f"({len(crudo)/1024:.0f} KB) · gui/pronostico.html ({len(out)/1024:.0f} KB)")
    print(f"  {len(perfil)} en juego · {nr} ramas de la gala {datos['placa_vigente']['gala']}")


if __name__ == "__main__":
    main()
