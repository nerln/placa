#!/bin/sh
# Chrome sin ventana en el puerto 9333. Si ya hay uno, no hace nada.
if curl -s --max-time 3 http://127.0.0.1:9333/json/version >/dev/null 2>&1; then
  echo "ya estaba andando"; exit 0
fi
PERFIL="${TMPDIR:-/tmp}/placa-chrome"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --remote-debugging-port=9333 --disable-gpu --no-first-run \
  --user-data-dir="$PERFIL" >/dev/null 2>&1 &
for i in 1 2 3 4 5 6 7 8; do
  sleep 1
  curl -s --max-time 2 http://127.0.0.1:9333/json/version >/dev/null 2>&1 && { echo "listo"; exit 0; }
done
echo "no arrancó" >&2; exit 1
