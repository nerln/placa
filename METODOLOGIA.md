# Metodología

Cómo se construyó el pronóstico, con las decisiones discutibles a la vista y los
modelos que se descartaron en el camino.

---

## 0. Qué datos existen y cuáles no

Antes de modelar hubo una recolección de 21 agentes de investigación sobre 1.357
llamadas a herramientas, con verificación adversarial de los hechos que podían
dar vuelta el resultado. Lo que quedó:

| Fuente | Estado |
|---|---|
| Resultados oficiales de gala (Telefe / Mi Telefe) | **disponibles y completos** para 8 de 11 galas recientes |
| Instancias de voto positivo | 12, con orden de salvación pero casi sin porcentajes |
| Bases y condiciones de la votación (TELINFOR) | disponibles: el voto es **pago y sin tope** |
| Mercados de apuestas | **no existen** para esta edición |
| Encuestas | ninguna es probabilística; solo una tiene historial verificable |
| Fecha de la final | **no confirmada** por Telefe |
| Mecánica de la final | **no confirmada**; se infiere de 2024-25 |

Dos consecuencias que condicionan todo lo demás:

- **El voto es pago y sin límite por usuario.** Las bases dicen literalmente que
  se puede participar «sin límite alguno». Un SMS son 8 votos por $429,55; los
  paquetes web llegan a 140 votos. El resultado mide *gasto concentrado de
  fandom*, no cantidad de personas. Por eso el rating no sirve como proxy del
  volumen de votos y ninguna encuesta de intención puede capturarlo.
- **Votan cinco países**: Argentina, Uruguay, Chile, Brasil y Paraguay. Chile,
  Brasil y Paraguay entraron recién esta edición.

---

## 1. La firma aritmética que valida una gala

Telefe revela los salvados progresivamente, cada uno con su porcentaje **sobre
el total de la placa**, y renormaliza al 100% únicamente en el mano a mano
final. Eso deja una identidad comprobable:

```
suma de todos los porcentajes publicados − 100 = suma de los que no son del versus
```

Gala 27, 3 de agosto:

```
0,1 + 0,3 + 0,5 + 0,9 + 46,7 + 53,3 = 101,8
101,8 − 100 = 1,8    y    0,1+0,3+0,5+0,9 = 1,8    ✓
```

Cuando la identidad cierra, la lista de nominados publicada **está completa** y
la gala es una observación multinomial completa del voto. Se cumple exactamente
en las galas 18, 20, 21, 22, 23, 25, 26 y 27. En las otras tres hubo nominados
cuyo porcentaje nunca se publicó, y entran como observación parcial.

Esta comprobación la corre `model/actualizar.py` con cada gala nueva.

---

## 2. El rechazo deriva: mitad rasgo, mitad ruido

El primer modelo asignaba a cada persona un rechazo constante θ y estimaba un
logit condicional sobre las galas. Falla de forma sistemática:

| Persona | gala t | gala t+1 |
|---|---|---|
| Luana | 38,45% | 0,10% |
| Emanuel | 0,40% | 53,81% |
| Cola | 0,50% | 68,24% |
| Majluf | 20,16% | 0,90% |

Correlación de la cuota de una misma persona entre galas consecutivas: **−0,13**
(Spearman −0,27). No hay persistencia. Pero sí hay un efecto de piso: Hanssen
midió ≤2,5% seis galas seguidas. Hay una parte estable y una volátil, y hay que
separarlas.

Sobre la escala logit, centrando dentro de cada gala para eliminar el término de
normalización:

```
y(i,g) = log q(i,g) − media_j log q(j,g) = (μ_i − μ̄_g) + (ε_i,g − ε̄_g)
```

Es un modelo de efectos mixtos. Estimado por mínimos cuadrados con efectos fijos
de gala y corregido por ruido de muestreo (empirical Bayes):

- **var(μ) real = 3,31** → rasgo estable: **52%**
- **ω = 1,75 logits** → ruido semanal: **48%**

Un shock semanal de una desviación multiplica por 5,8 las chances de ser el
elegido de la noche. Ese ω es el que alimenta la incertidumbre de la simulación
hacia adelante.

**Comprobación que evitó una conclusión falsa:** la autocorrelación de los
residuos da −0,41, que parece reversión a la media. Pero los residuos de cada
persona suman cero por construcción, lo que induce una autocorrelación mecánica
de −1/(n−1); con n medio de 3,4 el valor esperado es −0,42. Coincide. El shock
semanal es ruido puro y no hay «turno» predecible.

---

## 3. La encuesta, calibrada contra resultados oficiales

Fefe Bongiorno (X) es el único agregador de la temporada con historial
verificable. Acertó el eliminado 4 de 4 veces con números publicados, y en tres
de esas veces **le ganó al modelo de rasgo**: cada vez que Sol Abraham estuvo en
placa, el modelo la daba eliminada y tanto la encuesta como la realidad dieron a otro.
No se la puede ignorar.

Pero tampoco tomar literal. Comparando cada encuesta con el resultado oficial de
la gala siguiente, en logits centrados dentro de la gala:

| Posición en la encuesta | Sesgo | Desvío | Peso relativo |
|---|---|---|---|
| 1.ª, a quién pone primero | −0,25 | **0,53** | 1,00× |
| 2.ª | +0,35 | 1,71 | 0,10× |
| 3.ª y siguientes | −0,10 | 1,60 | 0,11× |

La encuesta identifica bien al blanco de la noche y aplasta la concentración
real del voto en todo el resto. Entra como observación del estado de la próxima
gala, combinada con el prior por precisión inversa. Cuando no hay encuesta, el
modelo corre igual con preferencia revelada sola.

---

## 4. El apoyo positivo, estimado con Plackett-Luce

La final se decide con voto **positivo**, y las dos escalas son casi
ortogonales. Evidencia dura de 2024-25:

- **Nicolás Grosman**: rechazo tan bajo como el del campeón (0,2%, 0,2%, 3,4%) y
  **2%** en la final.
- **Darío Martínez Corti**: rechazo bajísimo toda la temporada, **0,5%** en la
  única placa positiva medida, y fulminado 77,3% en el mano a mano.
- **Juliana «Furia»**: la más rechazada de la temporada (37-47% semanal) y a la
  vez la **más votada** en positivo (30,5%).
- **Luz Tito**: la más rechazada de 2025 y aun así 25,5% positivo entre tres.
- **Tato Algorta**: bajo rechazo **y** primero en las fases positivas (32,4% y
  29,8%) → ganó con 62,8%.

La regla que sale de ahí: bajo rechazo es **necesario pero no suficiente**. El
discriminante es la evidencia de voto positivo. Y el perfil de mayor riesgo en
una final es *salvarse siempre primero con 0,1-0,5% y no aparecer nunca arriba
en las fases positivas*.

Telefe casi nunca publica porcentajes en las fases positivas, pero **anuncia los
salvados en orden de más a menos votado**. Un ranking parcial es exactamente el
dato de un modelo Plackett-Luce:

```
P(i₁ ≻ i₂ ≻ … ≻ i_k | conjunto S) = ∏ⱼ  e^ψ(iⱼ) ⁄ Σ_{m aún en juego} e^ψ(m)
```

Doce instancias, con la gala del 16 de julio como ancla: una placa positiva pura
con los 16 de la casa ordenados de punta a punta. Tres tipos de observación:
orden (Plackett-Luce secuencial), porcentaje (multinomial; solo el repechaje) y
conjunto sin orden interno (comparaciones pareadas, con la información
normalizada por número de pares para que una fase con 84 pares no aplaste a un
ranking completo de 15 puestos).

El modelo reproduce el ranking del 16/07 con **correlación de rangos 0,87** y
acierta exactamente el fondo: Hanssen 13.º, Mariela 14.ª, Majluf 15.ª, JC 16.º.

Correlación medida entre μ y ψ en esta edición: **+0,52**. Quien molesta también
moviliza. Por eso el caso base **no resta** el rechazo del voto de la final
(κ = 0), y κ = ±0,4 queda como escenario de sensibilidad.

---

## 5. Simulación Monte Carlo

Cada corrida sortea los parámetros dentro de su incertidumbre (μ con su error
estándar, ψ con el suyo más la deriva estimada hasta la final, la temperatura del
voto final y el número de finalistas) y después juega el tramo que falta:

1. **Liderazgo** con inmunidad, uniforme entre quienes siguen.
2. **Armado de placa** con propensión de nominación estimada de la frecuencia de
   placas desde junio y de los puntos de nominación interna recibidos en las
   últimas cuatro galas, más un canal aparte para el fulminante.
3. **Eliminación** por softmax de μ + ε con el ruido semanal medido.
4. **Final** de tres, o de cuatro, resuelta con softmax de ψ, eliminando al menos
   votado hasta que queda uno.

La primera gala usa la placa real y el estado posterior calculado con la
encuesta; lo observado ahí también actualiza el rasgo de largo plazo de quienes
están en placa. Es la única información de rechazo que llegan a tener Charlotte
y Pincoya, que no aparecen en ninguna gala con reparto completo.

---

## 6. Bootstrap: la respuesta a «¿a quién elijo?»

El caso base deja a las dos primeras separadas por 1,3 puntos, menos que la
incertidumbre de los datos. La pregunta no se contesta mirando el punto
estimado. Se remuestrean con reposición las 8 galas completas y las 12 fases de
voto positivo, se reestiman las dos escalas y se vuelve a simular, 60 veces.

| | media | rango 90% | veces favorita |
|---|---|---|---|
| Tamara | 22,6% | 11,0 – 38,2 | **47%** |
| Zilli | 22,4% | 9,2 – 61,0 | 20% |
| Pincoya | 19,4% | 7,6 – 25,1 | 27% |

El intervalo enorme de Zilli no es volatilidad: su rechazo se estima con una
sola gala, así que el remuestreo la deja sin evidencia buena parte de las veces.

---

## Modelos que se descartaron

- **Logit condicional estático** (`model/fit_theta.py`): predicciones
  comprimidas hacia la uniforme; error de 138× en casos como el de Luana.
- **State-space con random walk** (`model/dynamic_fit.py`): la validación
  cruzada resulta monótona y casi plana en σ, y con σ grande el modelo se limita
  a reproducir la encuesta. Diagnóstico decisivo: la predicción un paso adelante
  daba *peor* que uniforme, y acertaba el eliminado 1 de 7. Se reemplazó por la
  descomposición de varianza, que dice lo mismo con honestidad.

---

## Lo que el modelo no sabe

- Fecha de la final, número de finalistas y mecánica de la final: no confirmados.
- Abandonos, expulsiones y evacuaciones médicas: **no se simulan**. Van 13 en
  esta edición, incluido Juanicar el 6 de agosto estando en placa. Es la vía más
  probable por la que el pronóstico se rompe.
- La tasa base de campeones uruguayos (2 de 2 finalistas uruguayos ganaron,
  ambos de Montevideo, sobre 11 campeones argentinos previos) entra como
  **escenario etiquetado**, no como parte del caso base: n = 2 y los dos casos
  comparten el arquetipo «outsider simpático», así que la nacionalidad puede ser
  un proxy y no la causa.
