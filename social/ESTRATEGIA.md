# La cuenta: con cara o sin cara, y con qué marca

Decidido el 24/08/2026, la tarde de la gala 30, con un consejo de cinco asesores
independientes, dos rondas de revisión cruzada y dos afirmaciones comprobadas
contra los datos antes de aceptarlas.

---

## La respuesta corta

**Con cara. Veinte segundos de cara, no un canal de alguien hablando.**

**La marca no es Gran Hermano y no es el modelo. Es el marcador.**

La cuenta va con tu nombre, el mismo en las dos plataformas, sin «GH», sin
«placa», sin «gran hermano». La serie que va adentro se llama **El Marcador**.
La línea de la biografía:

> Digo el número antes de que pase. Después muestro el marcador, incluidos los
> cero de siete.

Gran Hermano es la temporada uno. japepo ya demuestra que cambiás de tema. El año
que viene son elecciones, fútbol, o qué modelo gana un benchmark. La cuenta
sobrevive a que se termine el programa; una cuenta llamada «placa GH» no.

---

## Por qué la cara, cuando el instinto dice que no

Cuatro de los cinco asesores dijeron que sí, y todos por el mismo motivo, que no
es el que uno esperaría. **La cara no es alcance: es garantía.**

Una cuenta anónima que publica probabilidades es un horóscopo con mejor
tipografía. Cualquiera puede publicar un porcentaje con confianza. Lo que no
puede hacer cualquiera es poner una cara al lado de un número que puede salir
mal, con la hora de antes.

El asesor que nunca había visto el programa lo dijo mejor que nadie: de todo el
material, lo único que lo hizo frenar y volver a leer fue **cero de siete**. No
el 30,6% de Charlotte, no las 120.000 simulaciones. El cero de siete, publicado
por vos, con el test al lado que dice que es peor que el azar.

Eso es lo que se está vendiendo. No el pronóstico: el marcador.

---

## Cuánta cara, exactamente

Quince a veinte segundos, encima de los videos que ya se generan solos. Después
corta al gráfico.

El presupuesto es **quince minutos por día**. Un canal de cabeza parlante son
noventa minutos diarios y se abandona en tres semanas, en medio de un doctorado.
Ésa no es una advertencia poética: es la única cuenta que importa acá.

Los dieciséis reels ya hechos son inventario para los días muertos entre galas.
No son la apertura.

---

## El acento, que es la objeción real

Sos italiano, vivís en Valencia, y le vas a hablar en rioplatense al fandom más
territorial del TikTok en español, para pronosticar en contra de sus favoritas.

El único asesor que votó en contra se apoyó justo ahí, y tiene razón en el
diagnóstico. Pero la respuesta que ganó es más simple que su conclusión:
**el acento se declara en los primeros tres segundos**. Declarado, es blindaje.
Descubierto en el sexto video, es una avalancha.

---

## Lo que el consejo encontró y no le gustó a nadie

**Uno.** En el resumen que le pasé al consejo escribí que tu apuesta «le ganó al
azar» en la gala 29. Un asesor lo cazó y fue a mirar: la apuesta pierde con Brier
(0,8459 contra 0,8) y gana con log-verosimilitud (−1,5465 contra −1,6094).
Decirlo a secas es elegir la medida.

**El error era mío, no del sitio.** Fui a verificarlo: `web/index.html` usa sólo
Brier y escribe «no aportó sobre el azar» para las dos cajas, la del modelo y la
de la apuesta. La página está bien. La frase que hay que no decir nunca en un
video es «le gané al azar».

**Dos.** El 81,7% de Charlotte sale de un bootstrap de sesenta remuestreos, así
que su error estándar es de cinco puntos. **«Primera en 49 de 60»** dice lo mismo
y no esconde el ruido. En un video, además, se entiende mejor.

**Tres, y es la buena.** Un asesor de la ronda de revisión señaló algo que
ninguno de los cinco había visto: un modelo que anda *significativamente* peor
que el azar no está roto, está **anticorrelado**. Se probó.

    python3 model/signo.py

Leyendo el orden del modelo al revés, sobre las mismas siete galas: **2 aciertos
en vez de 0** (el azar espera 1,21) y el eliminado cae en el **puesto medio 2,14
en vez de 4,71** (el azar da 3,43).

Con la advertencia que va pegada al número y no se despega: el signo se eligió
**después** de ver los datos, sobre siete galas, y la prueba de permutación de la
versión invertida es la misma prueba leída de la otra cola. **No es un hallazgo,
es una hipótesis.** La única forma honesta de cobrarla es declararla ahora y
puntuarla hacia adelante en las galas que faltan, con la regla de
`EVALUACION.md`, sin tocar el modelo.

Declarada hoy, es exactamente el contenido que esta cuenta existe para producir.

---

## Los tres riesgos que quedan abiertos

**La temporada se termina antes que la cuenta.** Quedan ocho jugadoras, o sea
unas cuatro o cinco galas. El marcador tiene combustible para un mes. Por eso la
marca no puede ser el programa: japepo tiene que estar en la misma cuenta desde
el principio, no después.

**TikTok reparte por geografía.** Una cuenta que publica desde Valencia se prueba
primero con público español, no argentino. Esto no lo medí: es comportamiento
conocido de la plataforma, y por eso mismo entra acá como riesgo y no como dato.
La única fuente que lo va a contestar de verdad es la de siempre, y ya está
escrita en `ESTUDIO-TIKTOK.md`: **TikTok Studio, cuando la cuenta tenga videos
propios**, es lo único que dice qué porcentaje del público está en Argentina.
Mirarlo a los siete días. Si el público sale español, la conclusión no es
abandonar: es que el mismo aparato sirve para un formato de acá.

**La rama perdedora no está costeada, y no hace falta que lo esté.** Si esta
noche se va Sol, quedás equivocado en cámara el primer día con cero seguidores.
Ese es el producto, no el accidente. El guion de mañana ya tiene esa rama escrita
y es la mejor de las tres.

---

## El orden de esta noche

1. Registrar el usuario en las dos plataformas. Tu nombre, idéntico en las dos.
2. Grabar el video 1 **antes de que salga la gala**. Está en `canovaccio.md`.
3. Publicarlo con el pie que declara la hipótesis del signo. La hora de antes de
   la gala es el producto entero.
4. Mañana, el video 2. Las tres ramas ya están escritas.
