# Cómo se va a puntuar este pronóstico

Este archivo se escribe **antes** de que termine la temporada y no se toca
después. Declarar la predicción sin declarar cómo se la mide no sirve de nada:
al final se elige la métrica que conviene y se lee como excusa.

Lo que se fija acá: qué se mide, contra qué se compara, con qué datos, y qué
pasa si Telefe mueve la fecha de la final.

Firmado con la corrida del **10 de agosto de 2026**, hash `73cf007bb35633fc`.

Ese hash es el de los datos publicados el día en que se congeló esta regla, y sirve
para recuperar ese estado exacto del repositorio. Se mueve cada vez que se publica
cualquier dato nuevo, incluidas las novedades que no tocan el modelo. Lo que no se
mueve es lo escrito acá abajo.

---

## Las dos preguntas, que se puntúan por separado

El modelo contesta dos cosas distintas y las mezcla la mitad de la gente que lo
lee. Se puntúan aparte porque son de dificultad muy distinta, y porque una de
las dos ya se sabe que anda mal.

### Pregunta 1: quién se va en cada gala

Antes de cada gala de eliminación, el modelo publica una probabilidad de salida
para cada nominada. Se puntúa con **Brier multiclase**, sobre las nominadas de
esa gala:

    BS = Σ_i (p_i − y_i)²        y_i = 1 para quien salió, 0 para las demás

Más bajo es mejor. Se reporta gala por gala y el promedio.

**Baselines, fijadas ahora:**

1. **Uniforme sobre la placa.** p_i = 1/n para las n nominadas. Es la que hay que
   ganar para poder decir que el modelo aporta algo.
2. **Cuota de mercado**, si aparece un mercado de apuestas con volumen real
   antes de la final. Hoy no existe: el único hallado, en Manifold, tiene una
   sola operación y cotiza a alguien eliminado en marzo. Si no aparece, se
   declara que no hubo segunda baseline en vez de sustituirla por otra cosa.

**Lo que ya se sabe y queda registrado acá:** sobre las seis galas jugadas con
datos suficientes, el rasgo de rechazo proyectado una semana adelante puso al
eliminado en el puesto medio 5,00 de placas de cinco a siete, contra 3,50 del
azar, con p = 0,020 en un test de permutación. Cero aciertos de seis. Está en
`data/retro.json` y en la sección «La prueba hacia atrás» de la página. La
expectativa declarada para lo que queda de temporada es que esta pregunta siga
saliendo mal.

### Pregunta 2: quién gana la edición

Se puntúa con **log-loss** sobre la distribución del ganador publicada en cada
corrida:

    LL = −log p(ganadora real)

Se reporta para cada fecha de corrida guardada en
`data/historial_pronostico.json`, que es append-only. La serie completa muestra
si el modelo fue convergiendo hacia el resultado o dando bandazos.

**Baseline:** uniforme sobre quienes seguían en juego en esa fecha. Con nueve en
la casa son 2,197 nats.

### Calibración

Sobre todas las probabilidades publicadas de las dos preguntas, agrupadas en
tramos de diez puntos: de las veces que el modelo dijo «20%», ¿pasó una de cada
cinco? Se publica la curva y el error de calibración medio. Con una sola
temporada el número va a ser ruidoso, y se reporta con su intervalo en vez de
como punto.

---

## Qué cuenta como predicción

Solo lo que estaba publicado **antes** del hecho, con fecha, en
`data/historial_pronostico.json` o en un tag de git de esa fecha. Una predicción
recuperada después no entra, y las dos entradas del historial que se
reconstruyeron a mano de capturas están marcadas como tales y se excluyen del
puntaje.

## Si Telefe mueve la fecha de la final

La final está reportada para el 6 de septiembre de 2026 por una sola fuente
original y **no está confirmada por Telefe**. El puntaje no depende de esa
fecha: la pregunta 1 se puntúa gala por gala y la pregunta 2 en cada corrida
publicada. Si la temporada se alarga, hay más galas y más corridas, y el
promedio se calcula sobre todas. Si se acorta, sobre las que hubo. No se
descarta ninguna gala jugada.

## Si el modelo acierta la ganadora

Acertar una vez sobre nueve candidatas no demuestra nada por sí solo, y la
página no lo va a presentar como validación. Lo que se va a publicar es el
puntaje completo definido acá, con las dos baselines al lado, incluida la
pregunta 1 que ya se sabe que sale mal.

## Cuándo se publica el resultado

Dentro de los siete días de la final, en este mismo repositorio, con los datos
para recalcularlo. Si el resultado es peor que las baselines, se publica igual y
con el mismo tamaño de letra.

---

# Apéndice del 23 de agosto de 2026: las tres series

Nada de lo que está arriba se toca. Esto agrega.

Escrito con las tres predicciones de la gala 30 ya congeladas, sobre la corrida
del **18 de agosto de 2026**. No se anota acá el hash de la corrida: cambia con
cualquier edición de datos, incluso una que no toque ningún número de este
apéndice, y un hash que envejece solo es peor que ninguno. La fecha de este texto
es la de su commit, que es lo que un tercero puede comprobar.

## Por qué hay un apéndice

Arriba dice «el modelo publica una probabilidad de salida para cada nominada», en
singular. La página publica **tres** probabilidades para esa misma pregunta:
el modelo, la variante de dos tiempos y la apuesta declarada. Para la gala 30 son
Sol 52,3%, Sol 26,0% y Tamara 37,0%.

Publicar tres y no declarar cuál se puntúa es cubrirse: el martes se señala la que
acertó. Pero declarar hoy una canónica, con siete resultados ya a la vista, es
cambiar la regla a mitad de temporada, que es justo lo que este archivo existe
para impedir.

La salida es aditiva y no selectiva. Se puntúan **las tres, siempre**, hacia atrás
también, en tres series de Brier separadas y públicas, con las reconstruidas
marcadas como reconstruidas. Un apéndice que agrega series no elige ganador.

## A. Las tres series

Cada serie tiene dos partes que **no se mezclan nunca en el mismo promedio**: lo
reconstruido y lo congelado. La diferencia no es de precisión, es de qué clase de
afirmación es cada cosa. Una predicción reconstruida es una **prueba**: se rehace
hoy el cálculo con los datos que había antes de esa gala, y muestra qué hace el
procedimiento. Una predicción congelada es una **promesa cumplida**: estaba
publicada, con fecha, antes de que pasara nada. La regla «Qué cuenta como
predicción» sigue valiendo tal cual: al puntaje de la temporada entra sólo lo
congelado. Lo reconstruido se publica al lado, rotulado, y no cuenta como promesa.

### Serie M — el modelo

Es el ranking de rechazo, μ, ajustado sobre el reparto de votos de las galas
jugadas. Es la predicción de la que habla todo lo escrito arriba.

**Parte reconstruida: 7 galas — 22, 23, 25, 26, 27, 28 y 29.** Está en
`data/retro.json`, la produce `model/retro.py` y se rehace entera cada vez que se
corre, reajustando cada gala con las anteriores solamente. Empieza en la 22 porque
antes de eso hay menos de tres galas previas y el ajuste no dice nada. Resultado:
cero aciertos de siete, puesto medio 4,71 contra 3,43 del azar, Brier medio 1,2994
contra 0,8272 del uniforme. Es peor que el azar en las dos métricas.

**Parte congelada: 2 galas — la 29 y la 30.** Está en `predicciones_gala` de
`data/historial_pronostico.json`, que es append-only. Sólo la 29 tiene resultado:
salió Majluf, el modelo le daba 15,66%, puesto 3 de 5, Brier 0,9059 contra 0,8000
del uniforme. La 30 se juega mañana.

De la gala 29 hay dos entradas congeladas. La que cuenta es la última escrita antes
de la gala sobre la placa que efectivamente se votó, la de la corrida del 16 de
agosto sobre placa de cinco. La otra, de la corrida del 12, es sobre la placa de
siete que todavía figuraba a las 18.44 del 17, y no se puede puntuar contra otra
placa. Se conserva publicada porque el cambio tiene que verse.

### Serie D — dos tiempos

Es el modelo más una fuerza de mano a mano por persona, tipo Bradley-Terry,
ajustada sobre los once versus publicados y usada sólo en el segundo tiempo de la
placa. Existe desde el 18 de agosto de 2026, y no antes.

**Parte reconstruida: las mismas 7 galas.** Está en el bloque `backtest` de
`data/versus.json`. Cero aciertos de siete, puesto medio 4,86 contra 3,43 del azar.

**Parte congelada: 1 gala — la 30, y nada más.** Está en
`predicciones_dos_tiempos`. **Ninguna predicción congelada de esta serie tiene
resultado todavía.** Cualquier cosa que se diga hoy sobre si dos tiempos anda mejor
o peor que el modelo sale de la parte reconstruida, y por lo tanto es una prueba
del procedimiento y no un antecedente.

### Serie A — la apuesta declarada

No es el modelo y nunca lo fue: es el índice de campaña por la imagen invertida,
con cuatro supuestos escritos a mano en `model/apuesta.py`.

**Parte reconstruida: no hay, y no va a haber.** El índice de campaña se mide sobre
una ventana de tendencias de X de las últimas 24 horas —la de hoy va del 22/08
12:20 al 23/08 07:21 UTC— y no existe archivo de esas tendencias para las semanas
de las galas 22 a 28. El ranking de imagen se publicó el 12 de agosto. Reconstruir
esta serie hacia atrás con los datos de hoy sería inventarle un pasado a una señal
que no lo tiene. Se declara que no hay serie reconstruida en vez de fabricarla.

**Parte congelada: 2 galas — la 29 y la 30.** Está en `apuestas`. Sólo la 29 tiene
resultado: le daba 21,30% a Majluf, puesto 3 de 5, Brier 0,8459 contra 0,8000. De
la 29 hay dos entradas, de las 19.10 y de las 20.05; la que cuenta es la de las
20.05, la última antes de que cerrara la votación. La anterior queda publicada con
el motivo del cambio.

### La convención del cero, que hay que fijar antes de que sirva de excusa

El mismo modelo, sobre la misma serie reconstruida de siete galas, publicaba dos
log-verosimilitudes medias distintas: **−3,776** en `data/retro.json` y **−4,434**
en `data/versus.json`. No se contradecían ni había un error de cuenta: en la gala
23 el modelo le dio probabilidad **cero** al que salió, y `model/retro.py` pisaba
ese cero en 10⁻⁴ mientras que `model/versus.py` lo pisaba en 10⁻⁶. Dos pisos, dos
números.

Con una serie eso es una nota al pie. Con tres es la puerta abierta a citar el
piso que conviene. **Arreglado el 23 de agosto de 2026**: las dos constantes se
llaman ahora `PISO_CERO`, valen 10⁻⁴ en los dos archivos, y `data/versus.json`
reporta −3,776 para el modelo, el mismo número que `data/retro.json`. Queda
fijado:

* La métrica declarada de la pregunta 1 sigue siendo el **Brier**, que no tiene el
  problema: un cero es un cero y aporta 1 al puntaje, sin ningún piso.
* La log-verosimilitud se sigue reportando como color, con **un solo piso, 10⁻⁴**,
  y diciendo cuántas galas lo tocaron. Hoy es una: la 23.

Falta una cosa para que las tres series de Brier estén completas, y se anota como
deuda en vez de taparla: el `backtest` de `data/versus.json` guarda sólo la
probabilidad del eliminado, no la distribución entera de la placa, y con eso el
Brier reconstruido de la serie D no se puede calcular. Hay que guardar la
distribución completa por gala, como ya hace `data/retro.json`.

## B. Qué significa hoy el p = 0,0266, y qué no

El número que circula sale del test de permutación de `model/retro.py`. Hay que
decir de entrada sobre qué se calculó, porque tal como se viene citando afirma más
de lo que se midió:

* Sobre **una sola variante**, la serie M, cuando era la única que existía.
* Sobre la parte **reconstruida** de esa serie, siete galas. Ninguna de las siete
  estaba publicada antes de su gala.
* El estadístico es el **puesto medio** del eliminado dentro de su propia placa:
  4,71 observado contra 3,43 del azar. No es el Brier.
* La hipótesis nula es que el eliminado ocupa un puesto uniforme dentro de su
  placa, independiente entre galas. 200 000 permutaciones, semilla 7.
* Es de **una sola cola**, y en la dirección **«peor que el azar»**. No mide que el
  modelo acierte: mide que se equivoque de un modo demasiado sistemático para
  leerlo como ruido.

Además se mueve. El cuerpo de este documento cita la versión de seis galas —puesto
medio 5,00 contra 3,50, p = 0,020— y con la gala 29 adentro es 4,71 contra 3,43,
p = 0,0266. Mismo test, una gala más. Y `data/retro.json` se rehace entero en cada
corrida, no es append-only: **toda cita de este p tiene que llevar la fecha de la
corrida que lo produjo.** El 0,0266 es el del 17 de agosto de 2026.

**Lo que sigue siendo citable:** que en la serie M reconstruida el ranking de μ
pone al eliminado más abajo de lo que lo pondría el azar, con p = 0,0266 a una cola
sobre siete galas al 17 de agosto de 2026. Eso es una afirmación sobre el
procedimiento de ajuste, no sobre predicciones publicadas.

**Lo que no es:** no es un p-valor de la familia de tres. Si alguien mira las tres
series, elige la más extrema y cita ese número, el p correcto no es éste. La cota
perezosa es Bonferroni: 3 × 0,0266 = 0,0798, que deja de ser significativo a 0,05.
La cota perezosa además sobra, porque las tres series comparten galas, eliminados y
buena parte del orden, y Bonferroni supone independencia. El recálculo que
corresponde es una **permutación conjunta** que preserve esa correlación —permutar
el puesto del eliminado una vez por gala y arrastrarlo a las tres series—, tomando
como estadístico la más extrema de las tres. El resultado va a caer entre 0,0266 y
0,0798, y ése es el número a publicar el día que se quiera afirmar algo sobre las
tres juntas.

Con una salvedad que corresponde decir en las dos direcciones: la serie M no se
eligió entre tres mirando cuál daba mejor. Cuando ese test se corrió, el 17 de
agosto, era la única serie que existía; dos tiempos apareció el 18. Así que la
corrección de multiplicidad **no se aplica hacia atrás** a este p. Se aplica a
cualquier afirmación futura de la forma «una de las tres le gana al azar» o «una de
las tres pierde con el azar». El 0,0266 vale para M y para nada más.

## C. La regla de multiplicidad

1. **Las tres se puntúan siempre.** Todas las galas, las tres, con la misma métrica
   y contra la misma baseline uniforme.
2. **Las tres se publican juntas**, en el mismo lugar, con el mismo tamaño de letra
   y las mismas columnas. Si una gala no tiene predicción congelada de alguna de
   las tres, se publica la fila igual y dice «sin predicción congelada». El hueco
   tiene que verse; omitir la fila lo esconde.
3. **Ninguna se retira después de un resultado malo.** Una serie sólo se cierra si
   deja de publicarse lo que la produce, y eso se declara **antes** de una gala,
   nunca después de una.
4. **Se pueden agregar series**, siempre de forma aditiva, siempre antes de una
   gala. Una serie nueva **empieza en cero**: no hereda crédito hacia atrás, salvo
   que se publique su reconstrucción entera y rotulada, y aun así la reconstrucción
   no entra al puntaje de la temporada.
5. **Cuál se muestra arriba es una decisión de presentación, no de puntuación**, y
   se declara antes del resultado, que es lo único que la hace legítima. Para la
   gala 30 se declara hoy, 23 de agosto, antes de la gala: arriba va el **modelo**
   (Sol 52,3%), con dos tiempos y la apuesta al lado. Esto no cambia el puntaje de
   ninguna de las tres.

## D. Qué evidencia obligaría a cambiar el modelo

El modelo invertido no se toca hoy. Lo que faltaba escrito, y se escribe acá antes
de verlo, es qué haría falta para tocarlo.

**Qué quiere decir «cambiarlo»:** que el ranking de rechazo μ deje de ser la
respuesta que la página publica arriba para la pregunta 1. No quiere decir
retirarlo: por la regla C.3 la serie M se sigue puntuando y publicando igual.

**Sobre qué se evalúa.** Sobre la parte **congelada** de la serie M, de la gala 29
en adelante. No sobre la reconstruida. La reconstruida es de donde salió la
sospecha, y probar una hipótesis con los datos que la generaron no es una prueba.

**El estadístico: el puesto medio del eliminado dentro de su placa.** No el Brier,
y el motivo es concreto. El nulo del puesto depende sólo del orden, así que no se
puede mover aflojando las probabilidades: un modelo que se cubre poniendo 1/n a
todas cae exactamente en el azar y nunca dispara, mientras que ese mismo modelo
mejoraría su Brier sin haber mejorado nada de lo que afirma. Y una sola gala
degenerada domina un Brier medio de siete: en la gala 23 el ajuste le dio 1,0 a Sol
y 0 a todo el resto, Brier 2,0000, el máximo posible. Esa gala pesa como cualquier
otra en el puesto medio. El Brier sigue siendo el puntaje publicado, que es lo que
fija este documento arriba; el disparador usa el puesto porque lo que se
reemplazaría es el orden.

**El nulo.** El eliminado ocupa un puesto uniforme dentro de su propia placa,
independiente entre galas. Permutación de 200 000 tiradas, semilla 7, el mismo
código que ya está en `model/retro.py`. Una cola, dirección «peor que el azar».

**La barra.** Después de cada gala resuelta se evalúa, y dispara si:

  * **(A)** hay **n ≥ 10** galas congeladas y **p ≤ 0,05**; o
  * **(B)** hay **n ≥ 5** galas congeladas y **p ≤ 0,01**.

Acá no se escribe un puesto medio crítico porque depende de los tamaños de placa,
que todavía no se saben; el test se corre con los tamaños reales del momento. Para
que se entienda qué exige: con cinco placas de 6, 6, 5, 5 y 5, la barra (B) es un
puesto medio de 4,8 sobre un máximo posible de 5,4, o sea el eliminado casi último
casi todas las veces. Con diez placas de 6, 6, 5, 5, 5, 4, 4, 3, 3 y 3, la barra
(A) es 3,40 contra 2,70 del azar.

**Lo que cuesta, declarado ahora y no descubierto después.** Mirar después de cada
gala infla la tasa de falsa alarma, y hay que decir cuánto. Simulando esa regla
sobre un horizonte de doce galas con esos tamaños, con un modelo exactamente tan
bueno como el azar, dispara sola en el **4,7% de las temporadas**, cerca de una de
cada veintiuna. Ése es el precio.

**Lo que rinde, que es la parte incómoda.** Si la serie congelada mantiene
exactamente el patrón relativo de la reconstruida —el eliminado a 0,80 del largo de
la placa, en promedio—, la regla dispara en el 64% de las temporadas simuladas y
suele necesitar unas diez galas congeladas. Esta temporada no hay diez: la 29 ya
está puntuada, la 30 se juega mañana, quedan ocho en la casa y la final está
reportada para el 6 de septiembre. **Lo más probable es que esta preinscripción no
dispare esta temporada y el modelo no cambie.** Es a propósito. Una barra que se
puede alcanzar esta semana es una barra puesta después de mirar. Si la temporada
termina sin llegar a n = 10, la serie congelada sigue abierta y la regla se evalúa
igual en la temporada siguiente, sin reiniciarse.

**La otra cola, declarada al mismo tiempo para que la regla no sea cómoda en una
sola dirección.** Con el mismo test, los mismos umbrales de n y p, en la dirección
«mejor que el azar»: si dispara, se retira la frase escrita arriba de que se espera
que esta pregunta siga saliendo mal. No cambia el modelo, cambia lo que la página
afirma sobre él. Con las dos colas, la falsa alarma del aparato entero es del orden
del 9% por temporada.

**Lo que NO dispara nada**, listado ahora para que después no se discuta: una gala
mala; una racha de galas malas que no llegue a la barra; que el modelo falle la
ganadora; que la apuesta le gane; que dos tiempos le gane; que alguien lo diga. Y
que la barra se cumpla sobre la serie **reconstruida** tampoco dispara: sólo cuenta
la congelada.

**Qué pasa si dispara.** Tres cosas, en este orden:

1. El ranking de μ deja de ser la respuesta publicada arriba para la pregunta 1, y
   sigue publicándose y puntuándose como serie M.
2. Lo que lo reemplace se declara **antes** de usarlo por primera vez, con sus
   supuestos escritos, y abre su propia serie **en cero**, sin crédito hacia atrás.
3. El test que disparó se publica con sus datos y su código, para que cualquiera lo
   recalcule.

**Y una sola serie.** El disparador mira la serie M y nada más, elegida hoy, antes
de los datos. Eso es lo que lo hace un test y no una pesca entre tres. Si alguna
vez hace falta un disparador para D o para A, cada uno se declara por separado,
antes de sus datos y con su propia barra.

---

# Apéndice del 2 de septiembre de 2026: la cuarta serie

## Serie C — el cruce

Se estrena en la gala 32 y **no tiene ni una gala jugada**. Mezcla dos señales que
ya se median y que no entraban en ninguna predicción de la misma forma: el
sentimiento de los comentarios y la campaña en tendencias. La mezcla no es fija:
el peso del sentimiento **crece a medida que se acerca la gala**, de 20% a una
semana hasta 65% la noche misma, y el de la campaña baja de 80% a 35%.

El motivo está medido, no supuesto. La campaña se organiza con días de
anticipación y aguanta; el sentimiento se mueve en horas y responde a lo último
que pasó en la casa. Y el voto que decide la gala se manda esa noche.

**Por qué existe.** En la gala 31 las tres predicciones publicadas pusieron a
Pincoya **segunda de cuatro** —modelo 29,3%, dos tiempos 28,6%, apuesta 33,6%— y
salió Pincoya. Los comentarios la ponían **primera, con el 91% en contra**, y esa
señal se mostraba al costado sin comprometerse con ningún número. El cruce existe
para obligarla a comprometerse y a poder fallar en público.

**Parte reconstruida: no hay.** Se podría calcular hacia atrás para las galas 30 y
31, pero el peso depende de cuántas horas faltaban en el momento de la medición, y
esas mediciones se tomaron en momentos distintos de la semana. Reconstruirlo
obligaría a elegir hoy qué reloj usar para cada una, y elegir un parámetro después
de ver el resultado es exactamente lo que este documento existe para impedir. Se
declara que no hay serie reconstruida en vez de fabricarla.

## La apuesta, en placa positiva

La serie A (la apuesta declarada) **no se publica para la gala 32**, y la razón es
de definición y no de conveniencia: se arma leyendo la campaña y la imagen como
**riesgo** —más consigna, más peligro— y desde el 31 de agosto la placa es
positiva, o sea que la misma cuenta sale al revés. Una versión invertida
improvisada la tarde de una gala no es la misma predicción, y publicarla bajo el
mismo nombre rompería la serie.

Queda anotado que la serie A se interrumpe con **1 acierto de 3**, que es el único
acierto de toda la página, y que la interrupción es por cambio de reglas del
programa y no por su resultado.
