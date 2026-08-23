#!/bin/sh
# Rehace, comprueba y publica. Sin preguntar nada.
#
# Es el camino entero en un comando: recalcular el pronóstico con los datos que
# haya en data/, rearmar la apuesta, reconstruir web/, pasar las diez
# comprobaciones, archivar la gala y empujar. Si alguna comprobación falla NO publica y sale con
# error, que es la única forma de que esto pueda correr solo sin vigilancia.
#
#   bin/publicar.sh                      recalcula todo y publica
#   bin/publicar.sh --solo-web           no recalcula el modelo, sólo rearma la página
#   bin/publicar.sh --sin-empujar        deja el commit hecho y no lo manda
#
# Correr desde la raíz del repositorio.

set -eu

cd "$(dirname "$0")/.."

SOLO_WEB=0
EMPUJAR=1
for a in "$@"; do
  case "$a" in
    --solo-web)    SOLO_WEB=1 ;;
    --sin-empujar) EMPUJAR=0 ;;
    *) echo "no conozco la opción $a" >&2; exit 2 ;;
  esac
done

corre() { echo ">>> $*"; "$@"; }

if [ "$SOLO_WEB" -eq 0 ]; then
  for m in final_model ramas evolucion bootstrap camino sendas campana retro; do
    corre python3 "model/$m.py" >/dev/null
  done
fi

# El mano a mano se reajusta con cada versus nuevo, así que va después de que
# la gala esté cargada. No depende de la placa vigente: es historia.
corre python3 model/versus.py >/dev/null

# La apuesta va después de ramas y de campana: usa las dos.
[ -f data/campana.json ] && corre python3 model/apuesta.py >/dev/null

corre python3 gui/build.py   >/dev/null
corre python3 gui/tarjeta.py >/dev/null

# El portero. Si esto falla no se publica, y el guion termina en error para que
# quien lo haya lanzado se entere aunque nadie esté mirando.
if ! python3 gui/verificar.py; then
  echo "no se publica: alguna comprobación falló" >&2
  exit 1
fi

# La comprobación del RENDER: la página armada, mirada en un Chrome sin
# ventana. Es la única que ve un texto mal ensamblado o un desborde en el
# teléfono, porque en esos fallos ningún dato está mal. Sin Chrome se salta y
# se dice, igual que verificar.py salta la sintaxis cuando no hay node.
if sh gui/mirar/arrancar.sh >/dev/null 2>&1; then
  if ! node gui/mirar/comprobar.mjs; then
    echo "no se publica: el render está roto" >&2
    exit 1
  fi
else
  echo "(sin Chrome: no se comprueba el render)"
fi

# El archivo de la gala: la copia congelada de gui/pronostico.html, que es lo
# unico que un lector puede auditar cuando ya se sabe el resultado.
#
# Va DESPUES de las dos puertas y no antes. archivar.py se niega a reescribir
# una gala ya archivada, asi que congelar antes de que la pagina pase las
# comprobaciones dejaria congelada para siempre una pagina que el portero
# rechazo: el arreglo se publicaria el mismo dia con el archivo roto al lado, y
# nadie lo volveria a mirar.
#
# Y hay que RECONSTRUIR despues, porque gui/build.py mete data/archivo.json
# adentro de datos.json (la tabla del archivo sale de ahi). Sin este segundo
# build, verificar.py falla en la CI con «web/ no coincide con lo que produce
# gui/build.py: datos.js, datos.json», que es un mensaje que no senala a la
# causa. web/index.html no cambia -los datos viajan aparte, en datos.js- asi
# que lo que miraron las dos puertas se commitea byte a byte.
#
# No corta la publicacion si se niega, y eso es deliberado. El lunes a la
# noche, entre la gala y la nominacion del miercoles, no hay placa:
# model/ramas.py no congela ninguna prediccion y archivar.py sale con error
# porque archivar una pagina sin prediccion congelada es archivar nada. Esa
# noche hay que publicar el resultado igual. Cuando se niega no escribe nada,
# asi que lo peor que pasa es que esa semana no haya archivo, nunca que haya
# uno que miente.
if corre python3 gui/archivar.py; then
  corre python3 gui/build.py >/dev/null
else
  echo "(no se archivó esta gala: se publica igual, el motivo está arriba)"
fi

if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
  echo "nada que publicar: el árbol está limpio"
  exit 0
fi

CORRIDA=$(python3 -c 'import sys;sys.path.insert(0,"gui");from firma import firma_corrida;print(firma_corrida())')
git add -A
git commit -q -m "corrida $CORRIDA" -m "Publicado por bin/publicar.sh tras pasar las comprobaciones." \
  -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
echo "commit de la corrida $CORRIDA"

if [ "$EMPUJAR" -eq 1 ]; then
  git push
  echo "empujado. el despliegue tarda un par de minutos: gh run list --limit 1"
else
  echo "sin empujar, como se pidió"
fi
