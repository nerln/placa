# Licencias de terceros

## Tipografías

La página incrusta dos familias, ambas bajo **SIL Open Font License 1.1**, que
permite el uso, la modificación y la redistribución incluso incrustadas en un
documento, siempre que el aviso de licencia viaje con ellas.

- **Archivo** — Omnibus-Type (Héctor Gatti). Es la que pone los títulos y los
  números. https://github.com/Omnibus-Type/Archivo
  En la página viajan dos instancias estáticas con el juego de caracteres
  recortado; en `gui/tipos/Archivo.ttf` está la variable completa, que es la que
  dibuja la tarjeta de previsualización.

- **Atkinson Hyperlegible** — Braille Institute of America. Es la del texto
  corrido. https://www.brailleinstitute.org/freefont
  Diseñada para maximizar la distinción entre caracteres parecidos.

El texto completo de la SIL OFL 1.1 está en https://openfontlicense.org

## Las publicaciones de X

La sección «Las pruebas» muestra dos posts incrustados con el código que entrega
la propia plataforma a través de su API pública de oEmbed
(`publish.twitter.com/oembed`), que es el mecanismo previsto para republicarlos.
No hay capturas ni transcripciones: el contenido lo sirve X y lo firma su autor.
Si el post se borra o la cuenta se cierra, la incrustación se cae y acá no queda
ninguna copia. El guion de X se pide recién cuando alguien llega a esa sección,
con `dnt=1`.

Lo que sí está guardado en `data/actualidad.json` son las **cifras leídas** de
cada encuesta —los porcentajes y el N—, que son datos y no obra ajena, junto con
el enlace al original.

## Imágenes

No se publica ninguna fotografía.

Hubo un intento de usar retratos de Wikimedia Commons con licencia libre, del
que salió una sola imagen aprovechable de diez. La página nunca llegó a
mostrarla —la función de retrato dibuja la bandera y nada más—, pero el archivo
seguía en el repositorio: `data/fotos.json` guardaba un retrato de Charlotte
Caniggia con licencia **CC BY-SA 3.0** (autor «Char fan», Wikimedia Commons)
incrustado en base64, y la atribución que esa licencia exige no aparecía en
ningún sitio, porque la imagen no se veía. Redistribuir una obra CC BY-SA sin su
aviso de atribución incumple la licencia aunque nadie la mire. Se quitaron el
archivo y su recolector. A cada participante lo identifica la bandera de
su país, dibujada en la página. Los únicos archivos de imagen del repositorio son propios: `web/og.png`, la
previsualización del enlace, y `web/ojo.svg`, la marca, generados por
`gui/tarjeta.py` y `gui/marca.py` con los números de la corrida.
