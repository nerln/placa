# Mirar la página de verdad

Tres guiones para ver lo que se va a publicar en un navegador real, no en una
previsualización. Viven acá y no en un directorio temporal porque el temporal se
limpia solo y ya se perdieron dos veces.

Todos hablan con un Chrome sin ventana por el protocolo de depuración. Se
levanta una vez:

    gui/mirar/arrancar.sh

Y después:

    node gui/mirar/foto.mjs  http://localhost:8899/ '#placa' /tmp/a.png 1280 900
    node gui/mirar/ev.mjs    http://localhost:8899/ 'document.title'
    node gui/mirar/noche.mjs http://localhost:8899/ '#placa' /tmp/b.png

**Los tres apagan la caché.** Sin eso Chrome sirve un `datos.js` viejo, la
página se ve sin lo que uno acaba de escribir y uno se pone a buscar el fallo en
el código, que está bien. Pasó, y costó veinte minutos.
