# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
La firma de una corrida.

Es un sha256 de los datos que ya se publican, no un dato falso ni un texto
escondido. La diferencia importa y es la razon de que esto exista:

  * Un canario oculto -un caracter de ancho cero, un comentario con un
    identificador, un nombre de variable raro- no sobrevive a un minificador
    ni a que alguien pase el codigo por un modelo. Vive justo en la capa que
    cualquier reescritura automatica destruye.
  * Un dato falso plantado a proposito seria peor: este pronostico es una
    afirmacion sobre el mundo que la gente lee para decidir, y mentir un numero
    para cazar a un ladron corrompe la obra. Ademas romperia las identidades
    aritmeticas que gui/verificar.py comprueba.

Un hash de los datos verdaderos no tiene ninguno de los dos problemas. Si
alguien copia la corrida sin tocarla, la firma viaja con ella. Si la toca, deja
de ser esta corrida y el hash lo dice. Es portador de carga: borrarlo obliga a
cambiar los numeros.

Viaja por cuatro canales, para que baste con uno:
    - el campo "corrida" de web/datos.json
    - un trozo de texto dentro de web/og.png
    - la etiqueta de git de esa corrida
    - gui/verificar.py, que lo recalcula antes de publicar

Queda fuera del hash `data/archivo.json`: ver el comentario de FUERA, abajo.

    python3 gui/firma.py        imprime la firma de los datos de ahora
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# El dominio de la firma: dos corridas de proyectos distintos con los mismos
# datos no deberian dar el mismo hash.
SAL = b"placa|nerln|"


# Campos que se ignoran al firmar, por archivo. `archivo.json` se escribe
# DESPUES de construir la pagina y lleva la hora del congelamiento: si esa hora
# entrara en la firma, archivar cambiaria la corrida — y la corrida que la
# propia pagina archivada lleva adentro quedaria vieja en el momento mismo de
# archivarla. Es una dependencia circular, no una preferencia: corriendo
# `publicar.sh` justo en un cambio de minuto, `verificar.py` fallaba con un
# mensaje que no señalaba a la causa.
#
# Se ignora la HORA, no el archivo entero. Sacar `archivo.json` completo del
# hash abria el otro agujero, que este proyecto ya pago una vez: `datos.json`
# cambiaria de contenido sin cambiar de firma, y un navegador con el
# `datos.js?v=` viejo en cache lo emparejaria con el HTML nuevo. Archivar una
# gala NUEVA sigue moviendo la corrida, que es lo correcto; rehacer la misma no.
IGNORAR = {"archivo.json": ("congelado",)}


def _sin_volatiles(nombre, dato):
    campos = IGNORAR.get(nombre)
    if not campos:
        return dato
    def limpia(x):
        if isinstance(x, dict):
            return {k: limpia(v) for k, v in x.items() if k not in campos}
        if isinstance(x, list):
            return [limpia(v) for v in x]
        return x
    return limpia(dato)


def firma_corrida() -> str:
    """Hash de data/*.json, normalizado, ignorando los campos de IGNORAR.

    Se reserializa cada archivo con las claves ordenadas antes de digerirlo:
    asi la firma depende del contenido y no de como quedo indentado el JSON,
    que es lo que uno quiere -- reindentar un archivo no cambia la corrida.
    """
    h = hashlib.sha256()
    h.update(SAL)
    for p in sorted((ROOT / "data").glob("*.json")):
        h.update(p.name.encode())
        h.update(json.dumps(_sin_volatiles(p.name, json.loads(p.read_text())),
                            sort_keys=True, ensure_ascii=False,
                            separators=(",", ":")).encode())
    return h.hexdigest()[:16]


if __name__ == "__main__":
    print(firma_corrida())
