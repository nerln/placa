#!/bin/sh
# Rehace, comprueba y publica. Sin preguntar nada.
#
# Es el camino entero en un comando: recalcular el pronóstico con los datos que
# haya en data/, rearmar la apuesta, reconstruir web/, pasar las diez
# comprobaciones y empujar. Si alguna comprobación falla NO publica y sale con
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
