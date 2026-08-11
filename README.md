# Pronóstico: Gran Hermano Argentina, Generación Dorada (2026)

Quién gana la 13.ª edición. Corrida del 10 de agosto de 2026, gala 28.

> **Charlotte Caniggia, 22,2%.** Tamara 19,2%, Pincoya 18,5%.
>
> La diferencia entre las dos primeras es más chica que la incertidumbre, así que
> el número de arriba no alcanza para elegir. Remuestreando toda la cadena
> sesenta veces, Charlotte queda primera en el 53% de los casos y Tamara en el
> 42%. Esa frecuencia es la que decide, no los tres puntos.

**La página: https://nerln.github.io/placa/** · los datos, sin la página:
[`web/datos.json`](web/datos.json)

Se recalcula **solo** después de cada gala, y el despliegue no sale si la página
no se puede reconstruir desde los datos del repositorio. Ver
[ACTUALIZACION.md](ACTUALIZACION.md) y [`gui/verificar.py`](gui/verificar.py).

> **Esta página no es de Gran Hermano.** Es un análisis independiente, sin
> relación con Telefe, Kuarzo, Banijay ni con la producción del programa, y
> nadie de ahí lo revisó ni lo respalda. «Gran Hermano» y «Big Brother» son
> marcas de sus titulares y se nombran acá para identificar el programa del que
> trata este análisis. Los porcentajes de gala son hechos publicados por Telefe
> y no se reclama ningún derecho sobre ellos. La marca de la página no es el
> logotipo del programa: es un gráfico de este pronóstico con forma de ojo
> ([`gui/marca.py`](gui/marca.py)), y se redibuja después de cada gala.

## Por qué acá y no en un artefacto

Vivió un tiempo como artefacto de Claude, que corre bajo una política de
seguridad que prohíbe toda petición a un servidor ajeno. Sirve para publicar
rápido y tiene un techo: las mediciones de X se podían citar, no mostrar; el
enlace compartido no tenía previsualización; los datos no eran un archivo que
alguien pudiera bajar. Servida desde acá, esas tres cosas existen:

- **Las encuestas se incrustan desde X**, con el código que da la propia
  plataforma vía su API de oEmbed. No es una captura ni una transcripción: si el
  autor borra el post, desaparece de acá también. El guion de X se pide recién
  cuando alguien baja hasta esa sección.
- **La tarjeta de previsualización se dibuja con los números de la corrida**
  ([`gui/tarjeta.py`](gui/tarjeta.py)), así que el enlace pegado en cualquier
  lado muestra el pronóstico del día sin que nadie lo abra.
- **`datos.json` es un archivo público.** Todo lo que dibuja la página está ahí
  y se puede leer con una línea de código, sin pasar por el HTML.

## La idea

Los porcentajes que canta Telefe cada gala no son una encuesta. Son el censo del
electorado que efectivamente paga por votar, que es el único que decide. Acá no
entran opiniones de panelistas ni cuotas de casas de apuestas, entre otras cosas
porque para esta edición no existe ningún mercado real.

Lo que ordena todo es esto: durante la temporada el público paga para sacar
gente, y en la final paga para coronar a alguien. Suena parecido y no lo es.
Mirando 2024 y 2025 las dos escalas casi no correlacionan. Nicolás Grosman llegó
a la final con el mismo rechazo nulo que el campeón y sacó 2%. Juliana «Furia»,
la más odiada de su temporada, era a la vez la más votada cuando se votaba para
salvar. Por eso hacen falta dos parámetros por persona y no uno.

| | qué mide | cómo se estima | qué decide |
|---|---|---|---|
| **μ** | rechazo | logit condicional sobre 8 galas de voto negativo | quién sobrevive cada semana |
| **ψ** | apoyo positivo | Plackett-Luce sobre 12 instancias de voto positivo | quién gana la final |

## Los cinco hallazgos que cambiaron el modelo

1. **Ocho galas son observaciones completas.** Telefe anuncia los salvados con
   su cuota sobre el total de la placa y renormaliza al 100% recién en el mano a
   mano final. Eso deja una firma aritmética verificable:
   `suma publicada − 100 = suma de las cuotas que no son del versus`.
   La identidad se cumple exactamente en 8 de 11 galas, lo que prueba que la
   lista de nominados está completa. Es también la comprobación que corre el
   actualizador automático con cada gala nueva.

2. **El rechazo no es un rasgo fijo.** Luana pasó del 38,45% al 0,10% en tres
   semanas; Emanuel del 0,4% al 53,8%. Correlación entre galas consecutivas:
   −0,13. La descomposición de varianza da 52% rasgo estable y 48% ruido semanal
   (ω = 1,75 logits). El primer modelo, con θ constante, se descartó.

3. **La deriva aparente en los residuos es un artefacto.** La autocorrelación de
   −0,41 coincide con el −1/(n−1) mecánico esperado: el shock semanal es ruido
   puro, no reversión a la media.

4. **La encuesta de Bongiorno vale, pero solo en el puesto 1.** Calibrada contra
   resultados oficiales: su primero tiene sesgo −0,25 y desvío 0,53 logits (4 de
   4 aciertos); sus puestos 2 y siguientes tienen desvío 1,6 y sesgo al alza.
   Entra ponderada por precisión inversa, no a ojo.

5. **Existe un ranking de voto positivo completo.** La gala del 16/07 fue una
   placa positiva pura con los 16 de la casa, anunciados de más a menos votado.
   El modelo lo reproduce con una correlación de rangos de 0,87 y clava exacto
   el fondo de la tabla.

## Estructura

```
data/   plantel.json          quiénes están en juego, sus atributos y sus perfiles verificados
        galas.json            galas de voto negativo con las cuotas reconstruidas
        encuestas.json        historial calibrable + la encuesta de la próxima gala
        voto_positivo.json    12 instancias de voto positivo (rankings parciales)
        resultados.json       salida del modelo, 10 escenarios
        bootstrap.json        60 remuestreos de la cadena completa
        ramas.json            el pronóstico condicionado a cada salida de la próxima gala
        evolucion.json        el mismo modelo con y sin las cifras de la última gala
        camino.json           qué tendría que pasar para que gane la última del cuadro
        actualidad.json       tendencias de X, publicaciones incrustadas, zodíaco
        historial_pronostico.json   append-only: cada corrida publicada, con su fecha
        dataset_sintesis.json · crudo.json · verificacion*.json   recolección cruda

model/  variance_components.py   μ y ω, descomposición de varianza
        calibrar_encuesta.py     sesgo y desvío de la encuesta por posición
        fit_psi.py               Plackett-Luce sobre el voto positivo
        final_model.py           estado de la próxima gala + Monte Carlo + escenarios
        ramas.py                 la conjunta (quién sale hoy, quién gana la edición)
        evolucion.py             qué aportó la última gala más allá de quién salió
        camino.py                abre las simulaciones que gana la última y las describe
        bootstrap.py             remuestreo de toda la cadena
        actualizar.py            incorpora una gala nueva y recalcula todo
        fit_theta.py             primer modelo estático (descartado, queda como rastro)
        dynamic_fit.py           modelo state-space (descartado: la CV es plana en σ)

gui/    plantilla.html           la página, con huecos para los datos y el motor
        animaciones.js           el motor de las animaciones de la página
        build.py                 -> web/ (el sitio) y gui/pronostico.html (autocontenido)
        marca.py                 el ojo cuyo iris es el pronóstico -> la marca y el favicon
        tarjeta.py               -> web/og.png, la previsualización del enlace
        firma.py                 el hash de la corrida, que viaja por cuatro canales
        verificar.py             lo que corre antes de publicar
        escenas_manim.py         las mismas animaciones en Manim (descartadas: la página
                                 las dibuja sola y a la resolución de cada pantalla)

web/    index.html · datos.json · datos.js · og.png · ojo.svg · llms.txt
```

## Contador de visitas

Está preparado y apagado. Se enciende registrando el código `placa` en
[goatcounter.com/signup](https://www.goatcounter.com/signup) y poniendo
`"registrado": true` en [`data/analitica.json`](data/analitica.json). Hasta
entonces la página no emite el script ni el aviso, porque un código sin
registrar devuelve 400 y haría una petición fallida a un tercero en cada visita.

GoatCounter es de código abierto (EUPL-1.2), está alojado en la Unión Europea y
guarda agregados por página y hora en vez de eventos por persona. No escribe ni
lee nada en el equipo de quien visita, así que no activa el artículo 5(3) de la
directiva ePrivacy: no hace falta banner de consentimiento, y poner uno
empeoraría la situación, porque un banner necesita guardar la elección en el
dispositivo. Lo que corresponde es informar, y eso es el párrafo «Cómo se mide
esta página» que aparece al pie cuando el contador está encendido.

## Correr

```bash
python3 model/final_model.py && python3 model/ramas.py && \
  python3 model/evolucion.py && python3 model/bootstrap.py && \
  python3 model/camino.py && python3 gui/build.py && python3 gui/tarjeta.py
```

Y antes de subir, lo mismo que corre en CI:

```bash
python3 gui/verificar.py
```

## Sobre los retratos: no hay

La página identifica a cada participante con la **bandera de su país**, que en
una edición de ex participantes de cinco países dice más que una cara. No se
publica ninguna fotografía.

Hubo un intento anterior de usar retratos de Wikimedia Commons con licencia
libre, del que solo salió uno útil en diez. La página nunca llegó a mostrarlo
(la función de retrato dibuja la bandera y nada más), así que la imagen viajaba
incrustada en el artefacto sin verse y el pie explicaba una política de
licencias que no se aplicaba a nada visible. Se quitaron las dos cosas.

## Límites declarados

- La fecha de la final **no está confirmada** por Telefe (6 de septiembre o 31 de agosto). El
  modelo simula por cantidad de eliminaciones, no por calendario.
- El número de finalistas y la mecánica de la final son inferencia de 2024-25.
- Charlotte y Pincoya no tienen ninguna gala con reparto completo: su μ es casi
  solo prior. El gráfico las marca con contorno punteado.
- El μ de Tamara y el de Zilli salen de una sola gala cada uno.
- El modelo **no simula abandonos ni expulsiones**, que en esta edición ya
  fueron 13. Es la vía más probable por la que el pronóstico se rompe.
