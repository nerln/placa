# Ocho videos verticales, con los números de la corrida del 18/08

Para TikTok y Reels. Español rioplatense. Cada número sale de `web/datos.json`, de
`data/apuesta.json`, `data/retro.json`, `data/puntaje.json` o `data/campana.json` de
esta misma corrida, y está anotado al lado de dónde sale. Si se publican después de
la gala 30 hay que volver a sacar los números.

Regla que no se toca: **ningún número se redondea para que quede mejor**, y no se
nombra a nadie para burlarse. El modelo habla de números.

Los ocho no son ocho versiones de lo mismo. Son cuatro familias, y conviene
publicarlas alternadas para que la cuenta no quede como una sola idea repetida:

| Familia | Videos | Qué hace |
| --- | --- | --- |
| Predicción | 1 | dice qué va a pasar, con fecha |
| Contradicción | 2 | dos números verdaderos que parecen incompatibles |
| Explicación | 3, 6, 7, 8 | enseña a leer la placa sin que se note |
| Confesión | 4, 5 | el modelo se equivoca en público |

Las confesiones son las que más se comparten y las que menos copia la competencia.
No conviene guardarlas para el final.

---

## Video 1 · «Se va Sol»

El de la gala de hoy, y el primero que ve alguien que no sabe nada. Engancha con
el titular de la simulación y a los tres segundos lo da vuelta con las dos cosas
que la simulación no mira.

**No es el modelo contra su autor.** Son dos instrumentos distintos sobre la
misma pregunta, los dos publicados: la simulación mira los votos que ya se
cantaron, y las dos señales miran lo que se ve desde afuera antes de que cierre
la votación. Dicen cosas distintas y se muestran las dos.

**Duración:** 24 s. **Gancho:** un nombre en los primeros dos segundos.
**Base:** `tension`.

| t | En pantalla | Voz en off / texto |
| --- | --- | --- |
| 0,0 | `SE VA SOL` grande, `dice la simulación` debajo | Se va Sol. |
| 2,5 | `52,3%` / `de que salga esta noche` | Cincuenta y dos coma tres por ciento de que salga esta noche. |
| 6,0 | `PERO` / `hay dos cosas que la simulación no mira` | Pero hay dos cosas que la simulación no mira. |
| 9,5 | `«TAMARA AL 9009»` / `PUESTO 1` / `de las tendencias de Argentina` / `y 4 de la placa no tienen ninguna` | «Tamara al 9009» llegó al puesto uno de las tendencias de Argentina. Las otras cuatro de la placa no tienen ninguna campaña. |
| 14,5 | `la única encuesta con historial` / `ACERTÓ 5 DE 5` / `y a Tamara la deja última` / `imagen 15 sobre 100` | El único encuestador con historial, que va cinco de cinco, la deja última: quince de imagen sobre cien. |
| 19,0 | `las dos señales dicen` / `TAMARA` / url | Las dos señales dicen Tamara. |

Números: `data/apuesta.json` · `modelo_dice` (el titular), `entradas.campana` y
`entradas.imagen` (las dos señales) · `campana.indice` para el término exacto y
el puesto que alcanzó, con su ventana horaria · `imagen_historial` para el 5 de 5.

**Las dos frases que tienen que salir netas** son «puesto uno» y «cinco de
cinco». Son las únicas dos cosas que alguien que no sabe nada puede verificar
solo, en diez segundos.

---

## Video 2 · «Sol gana en un universo de cada 173»

Reducción al absurdo. Funciona porque el fandom la da por muerta y el número dice
que no es cero.

**Duración:** 20 s. **Base:** `reloj`.

| t | En pantalla | Voz en off / texto |
| --- | --- | --- |
| 0,0 | `SOL GANA EN 1 DE CADA 173` | Sol gana en un universo de cada 173. |
| 3,0 | `0,58%` | Cero coma cincuenta y ocho por ciento. |
| 5,5 | `tiene que zafar de 4,6 eliminaciones` | Para eso tiene que zafar de casi cinco eliminaciones seguidas. |
| 9,0 | `MANO A MANO: 4 de 4` | Y acá está la parte incómoda. En el mano a mano ganó los cuatro que jugó. |
| 13,0 | `la mejor del mano a mano` + `la peor para ganar` | Es la mejor de la casa en el mano a mano y la peor candidata a ganar. |
| 16,5 | `las dos cosas son verdad` | Las dos cosas son verdad al mismo tiempo. |

Números: `escenarios.base.p_gana.Sol` = 0,0058 · `data/camino.json` `una_de_cada` = 173,
`eliminaciones_que_sobrevive` = 4,6 · `data/versus.json` `registro.Sol` = [4, 0].

---

## Video 3 · «La diferencia es más chica que el error»

El que educa sin que se note. Sirve para cuando alguien grite que Charlotte ya ganó.

**Duración:** 18 s. **Base:** `tension`.

| t | En pantalla | Voz en off / texto |
| --- | --- | --- |
| 0,0 | `CHARLOTTE 30,6 · TAMARA 22,0` | Charlotte 30,6. Tamara 22,0. |
| 3,0 | `parece resuelto` | Parece resuelto. |
| 5,0 | dos barras con los intervalos superpuestos | Estos son los márgenes de las dos. |
| 8,5 | `Charlotte 22,8 a 38,2` / `Tamara 11,6 a 30,7` | Charlotte va de 22,8 a 38,2. Tamara de 11,6 a 30,7. |
| 12,5 | `se pisan` | Se pisan. |
| 14,5 | `8 puntos de diferencia, 15 de error` | Ocho puntos de diferencia y quince de incertidumbre. |

Números: `escenarios.base.p_gana` · `bootstrap.ic90` (B = 60 remuestreos).

---

## Video 4 · «Cero de siete»

La confesión grande. El modelo probado contra las galas que ya se jugaron, con el
resultado que a nadie le gusta publicar.

**Duración:** 21 s. **Base:** `reloj`.

| t | En pantalla | Voz en off / texto |
| --- | --- | --- |
| 0,0 | `PROBÉ MI MODELO CONTRA LAS GALAS YA JUGADAS` | Probé mi modelo contra las galas que ya se jugaron. |
| 3,0 | `0 DE 7` + `aciertos` | Cero de siete. |
| 6,5 | `el azar habría acertado 1,21` | Tirando al azar habría acertado 1,21. |
| 10,0 | `puso al eliminado en el puesto 4,71` / `el azar lo pone en 3,43` | Puso al que se iba en el puesto 4,71 de su lista. El azar lo pone en 3,43. |
| 14,0 | `anda peor que una moneda` | Anda peor que una moneda. |
| 17,5 | `está publicado con el test al lado` + url | Está publicado, con el test al lado. |

Números: `data/retro.json` · `aciertos` = 0, `n` = 7, `aciertos_esperados_azar` = 1,21,
`puesto_medio` = 4,71 contra `puesto_medio_azar` = 3,43, `p_valor` = 0,0266.

**Lo que no se dice y hay que saber:** ese p de 0,0266 es de una prueba de
permutación a dos colas. Dicho corto: es difícil andar tan mal por casualidad. Eso
no entra en el video porque no entra en veintiún segundos, y está entero en la
página.

---

## Video 5 · «La gala 29, con la nota puesta»

La confesión chica, y la que demuestra que la de arriba no fue una vez.

**Duración:** 20 s. **Base:** `tension`.

| t | En pantalla | Voz en off / texto |
| --- | --- | --- |
| 0,0 | `GALA 29 · SE FUE MAJLUF` | Gala 29. Se fue Majluf. |
| 3,0 | `3º DE 5` | Mi modelo lo tenía tercero de cinco. |
| 6,5 | `15,7%` | Le había dado 15,7 por ciento. |
| 10,0 | `Brier 0,906` / `tirar al azar da 0,8` | Brier de 0,906. Tirando al azar da 0,8. |
| 14,0 | `peor que el azar, otra vez` | Peor que el azar, otra vez. |
| 17,0 | `la regla estaba escrita antes de la gala` | La regla con la que se calcula estaba escrita antes de la gala. |

Números: `data/puntaje.json` · `gala` = 29, `eliminado` = Majluf, `modelo.puesto` = 3
de 5, `p_del_eliminado` = 0,1566, `brier` = 0,9059 contra `brier_uniforme` = 0,8.

---

## Video 6 · «Quién termina en placa»

Las dos preguntas que el fandom mezcla todo el tiempo. Sirve de base para responder
discusiones durante semanas.

**Duración:** 19 s. **Base:** `reloj`.

| t | En pantalla | Voz en off / texto |
| --- | --- | --- |
| 0,0 | `QUIÉN TERMINA EN PLACA` | Quién termina en placa. |
| 2,5 | `no es lo mismo que quién se va` | No es lo mismo que quién se va. |
| 5,5 | la lista entera con el signo | Sol más 1,89. Yipio más 0,69. Mariela más 0,19. Tamara más 0,08. Zilli menos 0,01. Luana menos 0,51. Charlotte menos 0,76. Pincoya menos 0,81. |
| 13,0 | `SOL` + `la nominan siempre` | A Sol la nominan siempre. |
| 16,0 | `PINCOYA` + `casi nunca` | A Pincoya casi nunca. |

Números: `web/datos.json` · `propension`, tal cual, sin reordenar ni redondear a un
decimal distinto del que sale.

---

## Video 7 · «Caer bien no alcanza»

La regla histórica. El que se puede volver a publicar en cualquier edición porque no
depende de esta.

**Duración:** 17,5 s. **Base:** `tension`.

| t | En pantalla | Voz en off / texto |
| --- | --- | --- |
| 0,0 | `CAER BIEN NO ALCANZA` | Caer bien no alcanza. |
| 3,0 | `seis casos con rechazo bajo` | Hay seis casos documentados con rechazo bajo. |
| 6,0 | `2` + `ganaron` | Dos ganaron. |
| 9,0 | `4` + `terminaron entre 0,5% y 15,7%` | Cuatro terminaron entre 0,5 y 15,7 por ciento. |
| 13,0 | `no te salva que no te odien` / `te salva que te voten` | No te salva que no te odien. Te salva que te voten. |

Números: `web/datos.json` · `regla_historica`. El discriminante entre los dos grupos
es el apoyo positivo, no la ausencia de rechazo.

---

## Video 8 · «Mido las campañas de X y no las uso»

El más raro de los ocho y el que más confianza construye: explica una decisión de
no usar un dato que sí se tiene.

**Duración:** 17,5 s. **Base:** `reloj`.

| t | En pantalla | Voz en off / texto |
| --- | --- | --- |
| 0,0 | `MIDO LAS CAMPAÑAS DE X` | Mido las campañas de X. |
| 3,0 | `posiciones del top 50 de tendencias en Argentina` | Posiciones en el top 50 de tendencias de Argentina. |
| 6,5 | `y NO las meto en el modelo` | Y no las meto en el modelo. |
| 10,0 | `con una sola ventana no hay con qué estimar cuánto pesan` | Con una sola ventana de medición no hay con qué estimar cuánto pesan. |
| 14,0 | `meterla sin medirla sería inventar` | Meterla sin medirla sería inventar. |

Números: `data/campana.json` · `entra_al_modelo`, `por_que_no`, `null_no_es_cero`.

---

## Video 9 · «Mi modelo no está roto, está al revés»

El mejor material que dio esta corrida, y el que no puede publicar nadie más
porque hace falta tener un backtest perdedor publicado para tenerlo.

**Duración:** 25 s. **Base:** `tension`.

| t | En pantalla | Voz en off / texto |
| --- | --- | --- |
| 0,0 | `MI MODELO NO ESTÁ ROTO` / `ESTÁ AL REVÉS` | Mi modelo no está roto. Está al revés. |
| 3,0 | `un modelo roto da el azar` / `el mío da 0 de 7` | Un modelo roto da el azar. El mío da cero de siete. |
| 7,0 | `2 DE 7` / `el azar esperaba 1,21` | Leído al revés habría acertado dos. El azar esperaba 1,21. |
| 11,5 | `en el puesto 2,14` / `antes 4,71 · el azar 3,43` | Y el eliminado le cae en el puesto 2,14 en vez de 4,71. |
| 16,0 | `elegí el signo DESPUÉS de ver los datos` | Elegí el signo después de ver los datos, así que no vale como resultado. |
| 20,5 | `vale como apuesta` / `y no toco el modelo` | Vale como apuesta. La puntúo hacia adelante y no toco el modelo. |

Números: `data/signo.json`, que produce `model/signo.py` a partir de
`data/retro.json`. Nada escrito a mano.

**El renglón que no se saca nunca.** «Elegí el signo después de ver los datos.»
Sin eso el video es un truco: la permutación de la versión invertida es la misma
prueba que condena al modelo al derecho, leída de la otra cola, así que no es
evidencia nueva. Con ese renglón el video es una apuesta declarada, que es
exactamente lo que esta cuenta vende.

---

## Cómo se arman

El fondo se dibuja acá, con `fondo.py`: un anillo de arcos dorados sobre azul
noche, el mismo lenguaje del ojo de la página, sin ninguna marca del programa.

    python3 social/video/fondo.py

Sale un bucle de doce segundos sin costura, porque todo lo que se mueve tiene por
período la duración del bucle. `montar()` lo repite con `-stream_loop -1`.

**Antes venía de Omni y por eso se cambió.** Esa versión, que quedó guardada como
`anillo-omni.mp4`, traía la estrellita de Gemini abajo a la derecha, encima justo
de donde TikTok pone su propia interfaz, y además una marca de agua invisible que
no es nuestra. Un anillo de arcos es geometría: dibujarlo cuesta menos que
discutir de quién es.

Los números y el texto también se dibujan acá, con PIL, y se superponen, porque
tienen que ser exactos y porque un modelo de video no sabe escribir cifras.

    python3 social/video/montar.py          # los ocho
    python3 social/video/montar.py 4 5      # sólo las confesiones

Salen en `social/video/salida/`. A 1080x1920, con audio a 44,1 kHz.

**Los hilos de ffmpeg están atados a mano en `montar()`.** Con los de fábrica el pico
de memoria se va arriba de 500 MB y en esta máquina eso significa no arrancar. Con
dos hilos el pico medido es de 364 MiB y tarda apenas más.

## El sonido

Dos bases, hechas con Lyria, las dos originales:

| Archivo | Qué es | Dura |
| --- | --- | --- |
| `audio/tension.mp3` | orquestal en suspenso, resuelve al final | 29,7 s |
| `audio/reloj.mp3` | segundero frío, no resuelve | 30,8 s |

Se cortan a la duración del video con medio segundo de fundido, porque cortar una
base en seco se escucha.

**Por qué no se usa un sonido en tendencia de la app.** Se buscó. El Creative Center
de TikTok tenía una pestaña de canciones y hoy redirige a la de hashtags: quedan
Hashtag, Creator («Coming soon») y Video. No hay lista pública de sonidos en
tendencia para Argentina, así que no hay a qué agarrarse. Con dos bases propias se
puede hacer otra cosa que no permite un sonido prestado: repetirlas.

**Cómo se reparten, y por qué.** Cada base toca las cuatro familias, así que si una
funciona no va a ser porque le tocaron los videos fáciles:

| | Predicción | Contradicción | Explicación | Confesión |
| --- | --- | --- | --- | --- |
| `tension` | 1 | | 3, 7 | 5 |
| `reloj` | | 2 | 6, 8 | 4 |

La idea es que el que llega por el segundo video reconozca el sonido del primero.
Eso con un audio prestado no pasa, porque lo comparte con miles de cuentas.

El texto en pantalla está pensado para que el video se entienda **sin sonido**,
porque así se mira la mayoría.
