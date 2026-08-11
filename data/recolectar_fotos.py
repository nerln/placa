# SPDX-FileCopyrightText: 2026 Eugenio Nerelli <kira_and_light@hotmail.it>
# SPDX-License-Identifier: Apache-2.0
"""
Recolector de retratos de los participantes.

REGLA INNEGOCIABLE: solo se incorporan imagenes con licencia libre verificada
(dominio publico, CC0, CC BY o CC BY-SA) alojadas en Wikimedia Commons, y
siempre con su atribucion. Las fotos de prensa de Telefe, Infobae o cualquier
medio estan protegidas por derechos de autor y NO se descargan ni se publican,
aunque aparezcan primero en cualquier buscador.

Para quien no tenga una foto libre se genera un retrato tipografico en el estilo
de la pagina. No es un relleno: deja explicito que de esa persona no existe
imagen reutilizable, que es informacion honesta sobre la disponibilidad del dato.

Salida: data/fotos.json con {apodo: {b64, licencia, autor, fuente}}.
"""

from __future__ import annotations

import base64
import io
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://commons.wikimedia.org/w/api.php"
UA = "gh-dorada-predictor/1.0 (proyecto personal de analisis estadistico)"

LIBRES = re.compile(
    r"^(cc[ -]?by([ -]sa)?([ -][0-9.]+)?|cc0|public domain|pd|cc[ -]?pd|"
    r"attribution|gfdl|no restrictions)", re.I)

# Nombre de busqueda y apellido obligatorio en el nombre del archivo, para no
# traer a un homonimo o una foto de otra persona.
BUSQUEDAS = {
    "Charlotte": [("Charlotte Caniggia", "caniggia")],
    "Tamara":    [("Tamara Paganini", "paganini")],
    "Sol":       [("Solange Abraham", "abraham"), ("Sol Abraham", "abraham")],
    "Pincoya":   [("Jennifer Galvarini", "galvarini"), ("Pincoya Gran Hermano", "pincoya")],
    "Yipio":     [("Yisela Pintos", "pintos"), ("Yipio", "yipio")],
    "Zilli":     [("Yanina Zilli", "zilli")],
    "Majluf":    [("Alejandra Majluf", "majluf")],
    "Mariela":   [("Mariela Prieto", "prieto")],
    "Luana":     [("Luana Fernandez Combate", "fern")],
    "Hanssen":   [("Matias Hanssen", "hanssen")],
}


def pedir(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def buscar(nombre, apellido):
    try:
        d = pedir({"action": "query", "format": "json", "prop": "imageinfo",
                   "generator": "search", "gsrsearch": nombre, "gsrnamespace": 6,
                   "gsrlimit": 12, "iiprop": "url|extmetadata", "iiurlwidth": 640})
    except Exception as e:
        print(f"   ! error de red: {e}")
        return None
    # Exigir TODOS los tokens del nombre en el archivo. Con solo el apellido, la
    # busqueda de "Solange Abraham" devolvia "Der Schoss Abrahams", una miniatura
    # medieval del seno de Abraham. Un apellido suelto no identifica a nadie.
    tokens = [t.lower() for t in re.findall(r"\w+", nombre) if len(t) > 3]
    if len(tokens) < 2:
        # Un solo token no identifica a una persona: "Sol Abraham" reducido a
        # "abraham" traia mapas hidrograficos de Saint-Abraham, Quebec.
        return None
    for p in (d.get("query", {}).get("pages") or {}).values():
        titulo = p["title"]
        tl = titulo.lower()
        if apellido.lower() not in tl:
            continue
        if not all(re.search(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", tl) for t in tokens):
            print(f"   - descartada, el archivo no confirma la identidad: {titulo}")
            continue
        if not re.search(r"\.(jpe?g|png|webp)$", titulo, re.I):
            continue
        ii = p["imageinfo"][0]
        em = ii.get("extmetadata", {})
        lic = (em.get("LicenseShortName", {}).get("value") or "").strip()
        if not LIBRES.match(lic):
            print(f"   - descartada por licencia «{lic}»: {titulo}")
            continue
        autor = re.sub(r"<[^>]+>", "", em.get("Artist", {}).get("value", "") or "").strip()
        return {"titulo": titulo, "thumb": ii["thumburl"].split("?")[0],
                "licencia": lic, "autor": autor or "desconocido",
                "fuente": ii["descriptionurl"]}
    return None


def descargar_cuadrado(url, lado=320):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        crudo = r.read()
    try:
        from PIL import Image
    except ImportError:
        return base64.b64encode(crudo).decode(), "image/jpeg"
    im = Image.open(io.BytesIO(crudo)).convert("RGB")
    w, h = im.size
    # recorte cuadrado desplazado hacia arriba: en un retrato la cara esta en el
    # tercio superior, un recorte centrado suele cortar la frente
    if w > h:
        izq = (w - h) // 2
        im = im.crop((izq, 0, izq + h, h))
    else:
        arr = int((h - w) * 0.18)
        im = im.crop((0, arr, w, arr + w))
    im = im.resize((lado, lado), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
    return base64.b64encode(buf.getvalue()).decode(), "image/jpeg"


def local(apodo):
    """
    Retrato puesto a mano por el usuario en data/fotos_locales/<Apodo>.jpg.
    Tiene prioridad sobre Commons. Es la via prevista para incorporar imagenes
    cuya licencia el usuario tenga o haya conseguido: el script no decide por el,
    solo se abstiene de redistribuir material ajeno por su cuenta.
    """
    carpeta = ROOT / "data" / "fotos_locales"
    for ext in ("jpg", "jpeg", "png", "webp", "JPG", "PNG"):
        f = carpeta / f"{apodo}.{ext}"
        if f.exists():
            return f
    return None


def main():
    (ROOT / "data" / "fotos_locales").mkdir(exist_ok=True)
    out = {}
    for apodo, intentos in BUSQUEDAS.items():
        print(f"· {apodo}")
        f = local(apodo)
        if f:
            try:
                b64, mime = descargar_cuadrado(f.as_uri())
                out[apodo] = {"b64": b64, "mime": mime, "licencia": "aportada por el usuario",
                              "autor": "", "fuente": "", "archivo": f.name}
                print(f"   OK archivo local {f.name} · {len(b64)//1024} KB")
                continue
            except Exception as e:
                print(f"   ! archivo local ilegible: {e}")
        hallado = None
        for nombre, apellido in intentos:
            hallado = buscar(nombre, apellido)
            time.sleep(9)          # cortesia con la API: evita el 429
            if hallado:
                break
        if not hallado:
            print("   sin imagen de licencia libre")
            out[apodo] = None
            continue
        try:
            b64, mime = descargar_cuadrado(hallado["thumb"])
        except Exception as e:
            print(f"   ! no se pudo descargar: {e}")
            out[apodo] = None
            continue
        out[apodo] = {"b64": b64, "mime": mime, "licencia": hallado["licencia"],
                      "autor": hallado["autor"], "fuente": hallado["fuente"],
                      "archivo": hallado["titulo"]}
        print(f"   OK {hallado['titulo']} · {hallado['licencia']} · {len(b64)//1024} KB")

    (ROOT / "data" / "fotos.json").write_text(json.dumps(out, ensure_ascii=False))
    con = sum(1 for v in out.values() if v)
    print(f"\n{con}/{len(out)} con retrato de licencia libre verificada")


if __name__ == "__main__":
    main()
