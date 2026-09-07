# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
LA CADENCIA SIGUE AL RELOJ DE LA GALA, NO AL RELOJ DE LA MAQUINA.

POR QUE EXISTE. Una corrida por hora alcanza casi siempre, pero no en las
horas antes de una gala de eliminacion a las 22:15 hora argentina: ahi el
sentimiento de los comentarios y la campana de tendencias se mueven en
minutos, y es tambien cuando mas gente mira la pagina. Y despues de la gala,
al reves: seguir refrescando cada hora no suma nada hasta que una persona
carga el resultado con model/actualizar.py, porque hasta entonces
proxima_gala en data/actualidad.json sigue apuntando a la gala que ya se jugo
y no hay nada nuevo que leer.

EL CRON DE GITHUB ES FIJO Y NO SABE LEER data/actualidad.json ANTES DE
ARRANCAR. No se le puede pedir "una hora antes de la proxima gala", porque la
proxima gala cambia de fecha cada semana. La solucion de .github/workflows/
refrescar.yml es disparar seguido, TODOS LOS DIAS, en una franja horaria ancha
que alcanza para cualquier gala futura sin importar el dia -y este guion
decide en cada disparo si corresponde hacer algo o cortar en seco. Cortar
temprano es barato: en un repositorio publico los minutos de Actions son
gratis, y lo caro de verdad -un commit, un despliegue- ni siquiera llega a
intentarse si este guion dice que no.

LOS CUATRO MODOS.

  * manual:   alguien lo disparo a mano (workflow_dispatch). Corre siempre:
              si un humano lo pide es porque lo quiere YA, sin que el reloj
              de la gala se meta a decidir por el.
  * sin_gala: data/actualidad.json no tiene proxima_gala.fecha (por ejemplo,
              entre que se resuelve una placa y se arma la siguiente). Sin
              fecha no hay ventana que activar, asi que se preserva el
              comportamiento de siempre: corre el disparo normal de cada
              hora y el disparo extra corta, por las dudas.
  * posgala:  la hora de la gala (22:15 ART) ya paso segun el reloj de la
              maquina Y proxima_gala.fecha todavia apunta a esa misma fecha:
              es la senal de que nadie cargo el resultado todavia. Cortan
              los dos disparos, el normal y el extra, hasta que una persona
              actualice la gala y la fecha salte a la siguiente.
  * alta:     faltan HORAS_ALTA horas o menos para la gala y todavia no paso.
              Corren los dos disparos: el normal, porque nunca deja de
              correr, y el extra, que es la razon de que exista este modo.
  * normal:   ninguno de los anteriores: falta mas de HORAS_ALTA para la
              proxima gala. Corre el disparo de siempre; el extra corta,
              porque en esta franja no aporta nada que el disparo de cada
              hora no vaya a traer.

QUE DISPARO ES CUAL. .github/workflows/refrescar.yml declara dos formas de
cron: la de siempre (una vez por hora, todos los dias) y una extra (cada
pocos minutos, pero solo en una franja horaria angosta pensada para cubrir
las horas antes de una gala). GitHub expone cual de las dos disparo esta
corrida puntual en el contexto `github.event.schedule`, y el workflow lo pasa
aca en la variable de entorno CRON_DISPARADOR: si coincide con el cron de
siempre, ESTE guion nunca lo corta salvo en modo posgala. El otro cron, el
extra, solo corre en modo alta.

LA HORA DE LA GALA, 22:15 ART, ESTA REPETIDA A PROPOSITO. model/cruce.py ya
tiene esta misma cuenta en su funcion cercania(), porque su peso tambien
depende del reloj. No se importa de aca para no atar dos guiones pensados
para correr solos a que el mismo modulo este siempre disponible, pero si
alguna vez la gala deja de ser a las 22:15, hay que tocar los dos archivos:
este y model/cruce.py.

    python3 model/reloj_gala.py            imprime el modo y el motivo
    python3 model/reloj_gala.py --ver      lo mismo, sin escribir GITHUB_OUTPUT
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = dt.timezone(dt.timedelta(hours=-3))
HORA_GALA = "22:15"

# El cron de SIEMPRE en refrescar.yml (una vez por hora), no el extra. Si ese
# archivo cambia el minuto o la hora de este cron, hay que actualizar tambien
# esta constante: son el mismo texto, uno en YAML y otro aca, y no hay forma
# de que un guion de Python lea el YAML del workflow que lo esta corriendo.
CRON_NORMAL = "7 * * * *"

# Cuantas horas antes de la gala se considera "ya falta poco". Tres horas:
# es la ventana en la que trends24 y los comentarios del canal reaccionan a
# lo que acaba de pasar en el programa de esa misma noche, y coincide con la
# franja horaria ancha que cubre el cron extra de refrescar.yml (documentado
# ahi mismo, con la cuenta de UTC a ART).
HORAS_ALTA = 3.0


def horas_para_la_gala(fecha_gala, ahora=None):
    """Horas que faltan para la gala; negativo si ya paso. None sin fecha."""
    if not fecha_gala:
        return None
    ahora = ahora or dt.datetime.now(ART)
    gala = dt.datetime.fromisoformat(f"{fecha_gala}T{HORA_GALA}:00-03:00")
    return (gala - ahora).total_seconds() / 3600.0


def decidir(evento, cron, faltan):
    """(modo, correr, motivo).

    `evento` es github.event_name ('schedule' o 'workflow_dispatch').
    `cron` es github.event.schedule: el texto del cron que disparo esta
    corrida puntual, vacio si no fue un disparo por cron.
    `faltan` son las horas hasta la gala, o None sin proxima_gala.fecha.
    """
    if evento != "schedule":
        return "manual", True, "disparo manual (workflow_dispatch): corre siempre"

    es_normal = (cron == CRON_NORMAL)

    if faltan is None:
        motivo = "sin proxima_gala.fecha en data/actualidad.json"
        return ("sin_gala", True, motivo + ": corre el disparo normal") if es_normal else \
               ("sin_gala", False, motivo + ": el disparo extra corta por las dudas")

    if faltan <= 0:
        motivo = (f"la gala era hace {-faltan:.1f} h y proxima_gala.fecha sigue "
                  "apuntando a esa fecha: nadie cargo el resultado todavia")
        return "posgala", False, motivo

    if faltan <= HORAS_ALTA:
        return "alta", True, f"faltan {faltan:.1f} h para la gala: ventana de alta frecuencia"

    motivo = f"faltan {faltan:.1f} h para la gala: cadencia normal"
    return ("normal", True, motivo) if es_normal else \
           ("normal", False, motivo + ", el disparo extra no suma nada aca")


def main():
    ap = argparse.ArgumentParser(
        description="Decide si esta corrida de refrescar.yml corresponde")
    ap.add_argument("--ver", action="store_true",
                    help="no escribe en GITHUB_OUTPUT, solo imprime")
    a = ap.parse_args()

    act = json.loads((ROOT / "data" / "actualidad.json").read_text())
    fecha_gala = (act.get("proxima_gala") or {}).get("fecha")
    faltan = horas_para_la_gala(fecha_gala)

    evento = os.environ.get("GITHUB_EVENT_NAME", "")
    cron = os.environ.get("CRON_DISPARADOR", "")
    modo, correr, motivo = decidir(evento, cron, faltan)

    print(f"modo: {modo} · corre: {'si' if correr else 'no'}")
    print(f"  {motivo}")
    if fecha_gala:
        print(f"  proxima_gala.fecha = {fecha_gala} {HORA_GALA} ART")

    salida = os.environ.get("GITHUB_OUTPUT")
    if salida and not a.ver:
        with open(salida, "a") as f:
            f.write(f"correr={'si' if correr else 'no'}\n")
            f.write(f"modo={modo}\n")

    # Sale siempre con 0: decidir que no corresponde correr no es un error
    # del guion, es el resultado correcto. Un exit distinto de 0 aca pintaria
    # de rojo una corrida que hizo exactamente lo que tenia que hacer.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
