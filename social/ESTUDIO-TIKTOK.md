# Medir TikTok en Argentina, Paraguay y Uruguay: qué se puede y qué no

Estudio hecho el 19/08/2026 para decidir con qué herramientas se abre un canal de
TikTok e Instagram con los números de esta página.

Cada afirmación de acá abajo se comprobó abriendo la página, y después otro
revisor intentó tumbarla. **De treinta fichas, catorce sobrevivieron y dieciséis
se cayeron.** Las que se cayeron están al final, con el motivo, porque son las que
más tiempo ahorran.

---

## El resultado incómodo, primero

**Para Paraguay y Uruguay no existe ninguna fuente oficial, gratuita y sin
postulación.** No es que sea difícil: el selector de países del Creative Center
directamente no los tiene.

| | Argentina | Paraguay | Uruguay |
| --- | --- | --- | --- |
| Creative Center › Hashtags | **sí** | no | no |
| Creative Center › tab Video | no | no | no |
| Research API (region_code) | sí | sí | sí |
| Commercial Content Library | no | no | no |
| Cuenta publicitaria self-serve | sí | sí | **no** |

La lista de países del Creative Center se extrajo del DOM: veintiséis nombres,
con Argentina adentro. Escribiendo «Par» y «Uru» en el buscador el menú contesta
«No Data». El tab Video tiene sólo cinco países y Argentina no está entre ellos.

La Research API sí acepta `AR`, `PY` y `UY` como `region_code`, y es gratis. El
problema no son los países sino quién puede pedirla: hace falta afiliación a una
institución académica en Estados Unidos, EEE, Reino Unido, Suiza o Brasil, y su
propia FAQ contesta «No.» a creadores y a usuarios comerciales.

> **Esto puede cambiar en tu caso.** Estás haciendo un doctorado. Si la afiliación
> alcanza, la Research API es la única puerta oficial que cubre los tres países, y
> vale la semana que cuesta postularse. Si no alcanza, no existe puerta oficial y
> conviene saberlo antes de intentarlo.

Del lado de Meta la situación es peor: CrowdTangle está apagado desde el 14 de
agosto de 2024, y su reemplazo, Content Library, es gratuito pero también cerrado
a académicos.

---

## Lo que sí se puede hacer, gratis, desde mañana

**1. Creative Center para Argentina.** Hashtags en tendencia por país, con Posts y
Views, filtro por industria y ventanas de 7, 30 y 90 días. Enlace directo, sin
pasar por el selector:

    https://ads.tiktok.com/creative/creativeCenter/trends/hashtag?region=AR&period=7

Sin login se ven **sólo los tres primeros**. Después pide cuenta. Para «News &
Entertainment» a 7 días es el termómetro más barato que hay.

**2. Cuenta de TikTok for Business.** Se abre desde Argentina y desde Paraguay,
no desde Uruguay, según la lista oficial de noviembre de 2025. Con ese login el
Creative Center muestra la clasificación completa.

**3. TikTok Studio, cuando el canal tenga videos propios.** Es la única fuente que
va a decir qué porcentaje de tu público está en Argentina, en Paraguay y en
Uruguay. Nadie te lo puede dar desde afuera.

**4. Metricool en plan gratuito** para programar y leer los propios números. Ojo
con una limitación que no es obvia: su Hashtag Tracker cubre Twitter e Instagram,
**no TikTok**, y sus competidores tampoco incluyen TikTok. Sirve para publicar,
no para descubrir.

**5. Leer un video suelto, a mano.** Esto funciona y está comprobado: en la página
de un video, el script `__UNIVERSAL_DATA_FOR_REHYDRATION__` contiene
`itemInfo.itemStruct` con `video.duration`, `stats.playCount`,
`authorStats.followerCount` y `createTime`. Comprobado en un video real el
19/08/2026: 223 segundos, 214.300 reproducciones, 126.900 seguidores del autor,
publicado el 18/08 a las 20:21 UTC.

---

## Dónde está la línea

Todo lo demás que promete datos masivos de TikTok pasa por scraping: TikTokApi,
Apify, Bright Data, yt-dlp. Funcionan. Y la sección 5 de los Términos de TikTok
en la versión que aplica a estos tres países prohíbe «use automated scripts to
collect information from or otherwise interact with the Services». Bright Data
vende además resolución de CAPTCHA, que es exactamente lo que esa misma sección
prohíbe.

No es una nota al pie. Un canal que vive de tener razón con los números no puede
tener el flanco abierto por cómo consiguió los números.

Leer a mano la página de un video que estás mirando es otra cosa. Automatizar mil
es lo prohibido.

---

## Lo que se cayó, y por qué importa

Estas fichas parecían buenas y no lo eran. Van acá para que nadie las vuelva a
proponer.

**«Mediana de 52 segundos, y los 15 segundos son la peor franja, n=69».** El
método por video funciona, pero el marco de muestreo no existe. La página
`tiktok.com/tag/gh2026` devuelve HTTP 200 y 376 KB de HTML con **cero** ids de
video, cero `playCount` y ningún `itemList`: es una cáscara de JavaScript. Los 69
videos no se pueden sacar de ahí, así que la estadística de duración no es
reproducible. **No se usó para decidir la duración de los videos.**

**«La franja 18:00-01:00 rinde 4x la tarde».** Misma página, mismo problema:
`createTime` aparece cero veces y `playCount` cero veces. Las dos variables del
estudio no están en la fuente que el estudio cita.

**«Los picos de @granhermno_2026 son 391.100 views».** Su propia pestaña de
populares muestra 4,1 M, 3,2 M, 2,6 M. El pico real es diez veces más alto. Peor:
los ids de sus videos top decodifican a 2024 y 2025, y una miniatura dice
«GH2023». Los 3,9 millones de likes son herencia de ediciones anteriores, no de
las 107 clips de esta edición: la cuenta se renombró. Como modelo a imitar para
un canal que arranca hoy, es el peor posible.

**Exolyt, Pentos, Sprout, Hootsuite, HypeAuditor, Brandwatch, Talkwalker.**
Ninguno declara en su web que cubra los tres países. Exolyt es el único que vende
«Country analytics», a 250 € por mes, y su lista de países no es pública. Si
algún día se paga, se entra antes al plan Basic gratuito sólo para abrir el menú
de países y mirar. Trendpop directamente ya no existe.

---

## Sobre el lugar que queda libre

La palabra «analista» en esta nicha ya está ocupada, pero por opinión, no por
números. La palabra «predicción» está ocupada por el tarot. La franja
cuantitativa está vacía, y es la única en la que esta página puede competir sin
pelear por el mismo público que todos.

El vocabulario propio ya existe y es el de la placa: voto positivo, porcentajes,
mano a mano, quién sale. No hace falta inventar un tono. Hace falta no cambiarlo
cuando un video no funcione.
