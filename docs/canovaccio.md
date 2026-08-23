# El canovaccio: las cuatro pistas de cada gala

Cuatro cosas avanzan en paralelo toda la semana y no avanzan al mismo ritmo: las
**acciones**, el **sentimiento**, las **predicciones del modelo** y la
**validación** de esas predicciones. Este archivo dice qué le toca a cada una en
cada momento del ciclo, con qué comando, qué archivo queda escrito, y qué
comprobación lo protege.

Lo que ya está escrito en otro lado no se repite acá:

- **Qué hacer cuando termina una gala**, paso por paso, con las fuentes y las
  reglas para fecharlas: [`tras-la-gala.md`](tras-la-gala.md).
- **Cómo corre la actualización sola**, y los argumentos de `model/actualizar.py`
  para cada caso raro: [`../ACTUALIZACION.md`](../ACTUALIZACION.md).
- **Cómo se puntúa lo que la página prometió**, fijado antes de que terminara la
  temporada: [`../EVALUACION.md`](../EVALUACION.md).
- **De dónde salen μ y ψ**: [`../METODOLOGIA.md`](../METODOLOGIA.md).

## Cómo leer cada paso

Cada paso de este archivo termina en una de dos líneas, y la diferencia es todo:

- **Guarda:** hay algo que falla solo si el paso salió mal. Un comando que sale
  con error, una comprobación de [`../gui/verificar.py`](../gui/verificar.py),
  un guion que se niega a escribir.
- **Sin guarda:** no hay nada. Si se hace mal, se publica igual y no se entera
  nadie hasta que lo ve un lector.

Esta distinción existe porque ya falló la otra forma. `ACTUALIZACION.md` y
`tras-la-gala.md` tenían la rutina completa, con checklist, y la semana del 17
de agosto se publicaron cuatro textos de la gala 29 describiendo la placa de la
30. Una guía te acuerda; un check te obliga. Así que la lista de pasos **sin
guarda** de este archivo no es un descargo: es el pronóstico de por dónde va a
volver a romperse.

## Los cuatro estados

El ciclo parecía tener tres estados y tiene cuatro. El que faltaba es el que
trae más gente.

| | Estado | Cuándo | La pregunta que la página contesta |
|---|---|---|---|
| 1 | **Preparación** | martes de nominación → domingo | quién está en placa y qué se mide |
| 2 | **Predicción congelada** | domingo → lunes 22.15 | quién se va, y quedó escrito antes |
| 3 | **Resultado en caliente** | lunes 22.15 → carga del resultado | ya salió alguien y acá todavía no se sabe |
| 4 | **Validación** | martes | cuánto se equivocó cada una de las tres |

---

## Estado 1 · Preparación

Se arma la placa y se recogen señales. Es el estado más largo y el que más cosas
escritas a mano tiene, o sea el más frágil.

**Acciones.** La placa nueva entra con la gala anterior, si ya se conocía:

```
python3 model/actualizar.py --gala <N-1> … \
  --nueva-placa "Nombre,Nombre,…" --nuevo-lider Nombre --fecha-proxima AAAA-MM-DD
```

Eso escribe `data/galas.json → placa_vigente`. Lo que **no** escribe ningún
guion es `data/actualidad.json → proxima_gala`: la fase de la placa, el líder y
qué le dio el liderazgo, la regla de la dupla, los pesos de nominación. Todo eso
se edita a mano.

*Guarda:* `actualizar.py` comprueba la identidad aritmética de Telefe sobre la
gala que se está cargando, y la vuelve a comprobar `identidad_telefe()` en cada
publicación.
*Sin guarda:* que `actualidad.json → proxima_gala` y `galas.json →
placa_vigente` hablen de la misma gala, la misma fecha y la misma placa. Nadie
los compara. Y ese campo es el que usa `textos_al_dia()` para saber qué prosa
venció, así que un `proxima_gala.gala` que quedó atrás no rompe nada: apaga la
única guarda de la prosa sin decir una palabra.

**Sentimiento.** Se recoge a mano dentro de `data/actualidad.json`: la ventana
de tendencias de X (`tendencias`, con `ventana`, `desde`, `hasta` y `fase`), el
termómetro de placa (`termometro_placa.medido`) y las mediciones ajenas
(`medidas_sociales.fuentes`, cada una con su fecha y su aviso). Con eso corren
las dos lecturas:

```
python3 model/campana.py        ->  data/campana.json
python3 model/comentarios.py    ->  data/comentarios_crudos.json y data/sentimiento.json
```

`campana.py` es offline y lo corre `bin/publicar.sh`. `comentarios.py` sale a
YouTube y **no lo corre nadie**: se corre a mano o el sentimiento se queda en el
de la semana pasada.

*Guarda:* las dos reglas que sostienen la lectura están en el código y no en la
intención. `campana.py` deja en `null` a quien no tiene ninguna consigna con
signo, y `comentarios.py` deja sin clasificar a quien nombra sin marca de signo.
Ninguno de los dos codifica «no medido» como cero.
*Sin guarda:* que la ventana sea de esta semana. Los dos archivos copian su
campo `generado` de `actualidad.json`, que se edita a mano: hoy `campana.json`
dice `"generado": "2026-08-11"` sobre una ventana del 22 al 23 de agosto. El
número que la página muestra es correcto y la fecha que lo acompaña es de doce
días antes. Nada falla.
*Sin guarda, y menos visible:* `ULTIMA_MEDIDA()` en la plantilla lee
`tendencias.medido`, y `data/actualidad.json` no tiene ese campo bajo
`tendencias` (tiene `ventana`, `desde` y `hasta`). O sea que la ventana de
tendencias no cuenta para la fecha de «la última medida». La rama está muerta y
la página se dibuja igual.

**Predicción.** Se recalcula todo con un comando:

```
bin/publicar.sh
```

Corre `final_model`, `ramas`, `evolucion`, `bootstrap`, `camino`, `sendas`,
`campana`, `retro`, después `versus` y después `apuesta`, y recién entonces
`gui/build.py`. El orden no es libre y está explicado adentro del guion.

*Guarda:* `probabilidades()` exige que cada escenario sume 1, `ramas_cierran()`
que las ramas recompongan el caso base, y `riesgo_coherente()` que las dos
estimaciones del riesgo de salir no se separen más de 0,6 puntos.

**Validación.** Acá la validación no mira números: mira la prosa, que es la otra
fuente de verdad y la que no verifica nadie. Cada bloque escrito a mano en
`gui/plantilla.html` que hable de esta gala está inventariado en
`data/textos.json`, con el número de gala para el que se escribió.

*Guarda:* `textos_al_dia()` compara ese número con la gala vigente y no deja
publicar si alguno quedó atrás. Cuando falla hay dos salidas y sólo dos:
reescribir el bloque para la gala vigente y subirle el número en
`data/textos.json`, o derivarlo del campo que ya tiene el dato —está anotado en
`campo`— y borrarle el renglón de la lista para siempre. La segunda es la buena:
un bloque derivado no puede vencer. Subir el número sin tocar el texto es
mentirle a la comprobación.

---

## Estado 2 · Predicción congelada

Antes de la gala. Es el estado que le da sentido a todo lo demás: una predicción
que no quedó escrita antes no se puede puntuar después.

**Acciones.** Publicar:

```
bin/publicar.sh
```

*Guarda:* las once comprobaciones de `gui/verificar.py`, que son las mismas que
corre la CI, más la comprobación del render (`gui/mirar/comprobar.mjs`) si hay
Chrome en la máquina. Si alguna falla no publica y sale con error.

**Sentimiento.** La última ventana de tendencias antes de que cierre la
votación es la que vale, porque cae entera dentro de la fase de voto negativo.
`model/apuesta.py` la consume: la apuesta se arma con el índice de campaña y con
la imagen de Bongiorno, y los dos números que hay que suponer están escritos en
la cabecera de ese archivo.

*Guarda:* `apuesta.py → _congelar()` se niega a escribir una apuesta con fecha
posterior a la gala, y guarda cada versión con su hora en vez de pisar la
anterior. La apuesta se mueve durante la semana y esconder las versiones previas
sería elegir después cuál defender.

**Predicción.** Las tres se congelan solas, cada una desde su guion, en
`data/historial_pronostico.json`:

| Predicción | La escribe | En la lista |
|---|---|---|
| MODELO | `model/ramas.py` | `predicciones_gala` |
| DOS TIEMPOS | `model/versus.py` | `predicciones_dos_tiempos` |
| APUESTA | `model/apuesta.py` | `apuestas` |

*Guarda:* el registro es append-only y ninguno de los tres reescribe una entrada
anterior. `ramas.py` no duplica una entrada idéntica, así que correr
`publicar.sh` cinco veces en la semana no ensucia el registro.
*Sin guarda:* que las tres estén congeladas antes de la gala. Si una falta, la
gala se publica igual y el martes `puntaje.py` dice «sin predicción congelada»
para esa. Ya pasó con la apuesta, que era justo la única de las tres que no sale
del modelo.

**Validación.** Se congela la página, no sólo los números:

```
python3 gui/archivar.py            archiva la gala vigente si falta
python3 gui/archivar.py --forzar   la rehace, antes de que se juegue
```

Deja `web/galas/NN.html` —una copia de `gui/pronostico.html`, que lleva los datos
adentro— y el renglón en `data/archivo.json`. Es lo único que un lector puede
auditar cuando ya se sabe el resultado, y es además el único lugar donde la
medición de sentimiento de esta semana sobrevive: `campana.json` y
`sentimiento.json` se sobrescriben con la ventana siguiente, y la copia
archivada no.

*Guarda:* `archivar.py` se niega si no hay ninguna predicción congelada para esa
gala, si `gui/pronostico.html` tiene alguna referencia externa (una copia que
referencia algo de afuera se actualiza sola y miente con fecha vieja), y si la
gala ya se jugó y ya estaba archivada.
*Sin guarda:* que la gala quede archivada. `publicar.sh` no corta cuando
`archivar.py` se niega, y es a propósito: el lunes a la noche no hay placa y esa
noche hay que publicar el resultado igual. El precio es que nada exige que la
gala vigente esté archivada antes de su fecha.

---

## Estado 3 · Resultado en caliente

Entre las 22.15 del lunes y el momento en que se carga el resultado. Ya se sabe
quién salió; la página todavía anuncia quién se va mañana. **Es el pico de
tráfico de la semana**: es cuando más se comparte el enlace, y era cuando peor
quedaba.

**Qué tiene que mostrar la página en esa ventana.** Cuatro cosas, y ninguna es
el resultado:

1. Que la gala ya empezó. El encabezado deja de decir «Gala de eliminación ·
   mañana a las 22.15» y dice «La gala ya empezó · el resultado todavía no está
   cargado».
2. Que la página se actualiza a mano y no se toca nada hasta que se confirme
   quién salió. No puede fingir que sabe.
3. El enlace a `web/galas/NN.html`, la página tal como se publicó antes de la
   gala. Es lo único que importa leer en ese momento.
4. Las tres predicciones, tal como estaban. No se esconden: esconderlas cuando
   el resultado ya se conoce afuera es exactamente lo que hace inauditable a un
   pronóstico.

*Guarda:* esta es la única de las cuatro que se protege sola. `CUANDO_GALA()`
en la plantilla calcula `caliente = empezó && !resuelta`, comparando el reloj de
Buenos Aires contra `proxima_gala.fecha` a las 22.15 y contra la existencia de
`data/puntaje.json` para esa gala. No hay que acordarse de encenderlo ni de
apagarlo, y por eso no puede vencer.
*Sin guarda:* nada obliga a que el resultado se cargue. Si el martes llega sin
`puntaje.json`, la página sigue diciendo la verdad, pero la sigue diciendo.

**Lo mínimo, si hay poco tiempo.** Cuatro pasos, en este orden, y todo lo demás
espera al martes:

```
# 1. quién salió, con dos fuentes distintas (ver tras-la-gala.md, §1)
python3 model/actualizar.py --gala <N> --fecha AAAA-MM-DD \
  --placa "Nombre,Nombre,…" --eliminado Nombre
python3 model/puntaje.py
bin/publicar.sh
```

Sin `--salvados` ni `--versus`: es un caso previsto y la gala queda anotada como
incompleta. Sin `--nueva-placa`, que el lunes a la noche todavía no existe. El
reparto de votos, la novedad de `data/ultimo.json` y la placa nueva son del
martes.

**Lo que no se hace para ganar tiempo.** No se toca `actualidad.json →
proxima_gala` para apuntar a la gala siguiente antes de cargar el resultado. Eso
saca a la página del estado en caliente —que es honesto— y la deja hablando de
una gala futura como si la de anoche no hubiera existido: el resultado
desaparece sin que falle nada.

**Sentimiento.** La ventana se cierra a las 22.15 y no se vuelve a abrir para
esta gala. Lo que se mide después de la gala es reacción, no campaña, y mezclar
las dos cosas rompe el signo: en la fase negativa «X AL 9009» pide que la echen,
y una hora después el mismo término significa otra cosa.
*Sin guarda:* nada impide sobrescribir `tendencias` con una ventana posterior a
la gala. Lo que evita perder la medición buena es haber archivado en el estado 2.

**Predicción.** Nada. Ya está congelada y no se toca. Volver a correr
`bin/publicar.sh` en esta ventana no reescribe ninguna predicción —el registro
es append-only y `apuesta.py` se niega a escribir con fecha posterior a la
gala—, así que es seguro.

**Validación.** Todavía no hay nada que puntuar. La prueba está en
`web/galas/NN.html` y en `data/historial_pronostico.json`, las dos escritas
antes, y en el historial de commits de ese archivo, que lo puede leer cualquiera
sin creerle a nadie.

---

## Estado 4 · Validación

El martes. La rutina completa está en [`tras-la-gala.md`](tras-la-gala.md); acá
va sólo qué le toca a cada pista.

**Acciones.** La carga completa de la gala, con el reparto de votos y la placa
nueva si ya se conoce:

```
python3 model/actualizar.py --gala <N> --fecha AAAA-MM-DD \
  --placa "…" --salvados "Nombre:cuota,…" --versus "Nombre:pct,Nombre:pct" \
  --eliminado Nombre \
  --nueva-placa "…" --nuevo-lider Nombre --fecha-proxima AAAA-MM-DD
```

Y la novedad al principio de `data/ultimo.json`, con `afecta`, `impacto` y
`fuente`.

*Guarda:* la identidad aritmética. Si cierra, la gala entra como observación
multinomial completa y pesa en la estimación de μ; si no cierra, entra marcada
como parcial en vez de entrar como si estuviera completa.
*Sin guarda:* la novedad. Es prosa escrita a mano y no está en
`data/textos.json`, porque el inventario cubre la plantilla y no los datos. Lo
único que la mira es la comprobación del render, y sólo ve una frase rota, no
una frase vieja.

**Sentimiento.** Se abre la ventana de la gala siguiente. `campana.py` corre
solo dentro de `publicar.sh`; `comentarios.py` hay que acordarse.
*Sin guarda:* la misma de siempre, y con un agravante en este estado: si la
placa nueva todavía no está cargada, `comentarios.py` clasifica contra la placa
vieja, porque lee `galas.json → placa_vigente`. Corre sin quejarse y cuenta
nombres que ya no están en juego.

**Predicción.** Entre la gala del lunes y la nominación del martes no hay placa,
y eso no es un fallo: `ramas.py` publica sólo las salidas con probabilidad
apreciable, `ramas_cierran()` ve que la cobertura no llega a 1 y lo dice en vez
de exigir una identidad que no existe, y `archivar.py` se niega porque archivar
una página sin predicción congelada es archivar nada.

**Validación.** El puntaje de las tres:

```
python3 model/puntaje.py                        toma la última gala resuelta
python3 model/puntaje.py --gala 30 --eliminado Sol
```

Escribe `data/puntaje.json` y agrega una entrada a `historial_pronostico.json →
puntajes`. Con eso la sección del resultado se enciende sola arriba de la
apuesta y la tarjeta de la apuesta de esa gala se retira, para que no haya dos
respuestas a la misma pregunta en la misma pantalla. Y `model/retro.py` rehace
la prueba hacia atrás con la gala nueva adentro.

*Guarda:* `puntaje.py` se niega a puntuar si quien salió no estaba en la placa
congelada, y el registro es append-only: una gala ya puntuada no se repuntúa. La
regla con la que se puntúa está en `EVALUACION.md`, escrita antes de que
terminara la temporada y firmada con el hash de su corrida.
*Sin guarda:* que se corra. `publicar.sh` no lo llama y `verificar.py` no exige
que una gala ya jugada tenga puntaje. Se puede publicar una página de una gala
resuelta sin el resultado, y las once comprobaciones dicen que todo cierra.

---

## Los pasos que hoy no tienen guarda

La lista completa, junta, porque es la lista de lo que va a fallar:

1. **`actualidad.json → proxima_gala` no lo escribe ningún guion** y nadie lo
   compara con `galas.json → placa_vigente`. Es el peor de todos, porque es el
   campo del que depende `textos_al_dia()`: si queda atrás, apaga la guarda de
   la prosa sin fallar. Una comprobación que compare los dos campos —gala, fecha
   e integrantes— es la que más rinde de las que faltan.
2. **La ventana de sentimiento no se comprueba contra la fecha de la gala.**
   `campana.json` y `sentimiento.json` copian un `generado` escrito a mano, y hoy
   ese campo va doce días atrasado respecto del dato que acompaña.
3. **`model/comentarios.py` no lo corre nadie.** No está en `publicar.sh`
   porque necesita salir a internet, así que el sentimiento de los comentarios
   se queda quieto salvo que alguien se acuerde.
4. **Nada exige que la gala vigente quede archivada antes de su fecha.**
   `publicar.sh` no corta cuando `archivar.py` se niega, y esa decisión es
   correcta por otra razón.
5. **Nada exige correr `model/puntaje.py`.** Una gala jugada puede publicarse
   sin resultado y ninguna comprobación se queja.
6. **`data/ultimo.json` es prosa a mano fuera del inventario.** El único que la
   mira es el render, y sólo ve frases rotas.
7. **Fechar por fuente es responsabilidad humana entera.** Ninguna comprobación
   puede saber si una fecha salió del cuerpo de una nota o de una deducción.

---

## Qué NO se hace nunca

- **No se fecha por deducción.** Si una nota no lleva fecha en el cuerpo, no
  sirve para fechar nada. Deducir una fecha no es fecharla, y ya costó una
  corrección pública: un episodio del 10 de junio se publicó como del 16 de
  agosto.
- **No se publica un resultado sobre una placa que no es la cargada.** Si quien
  salió no está en la placa que el repositorio tenía cargada, se para. Publicar
  un resultado sobre otra placa es peor que no actualizar, y `puntaje.py` se
  niega solo. Cuando se niega, se lee el mensaje: está diciendo que algo no
  cuadra.
- **No se escribe a mano un número ni una fecha que exista en un campo.** Se lee
  del campo. Un número escrito a mano en la prosa es un número que va a vencer,
  y la comprobación que lo atrapa sólo existe para los bloques que están
  inventariados en `data/textos.json`. Cuando se puede derivar, se deriva y se
  borra el renglón del inventario: un bloque derivado no puede vencer.
- **No se archiva copiando `web/index.html`.** Parece el mismo archivo y no lo
  es: carga los datos aparte, con `src="datos.js?v=<corrida>"`, y `datos.js` se
  sobrescribe después de cada gala. Esa copia se reescribiría sola el martes
  siguiente y mostraría los números de la semana que viene con la fecha de ésta.
  Se archiva con `gui/archivar.py`, que copia `gui/pronostico.html`, que lleva
  los datos adentro.
- **No se rehace un archivo después de la gala.** Antes de la gala, `--forzar`
  es legítimo; después, un archivo que se puede acomodar al resultado no prueba
  nada. `archivar.py` lo impide.
- **No se arregla la comprobación en vez del dato.** Si `verificar.py` falla, lo
  que está mal es lo que se iba a publicar.
