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

No se publica ninguna fotografía. A cada participante lo identifica la bandera de
su país, dibujada en la página. El único archivo de imagen del repositorio es
`web/og.png`, la previsualización del enlace, generada por `gui/tarjeta.py` con
los números de la corrida.
