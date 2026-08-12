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
