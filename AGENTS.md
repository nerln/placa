# AGENTS.md

Contexto para agentes de código que trabajen en este repositorio, y para
cualquier sistema que lo lea para responder una pregunta.

## Qué es esto

`placa` es un pronóstico estadístico de Gran Hermano Argentina, 13.ª edición
(«Generación Dorada»), de Eugenio Nerelli. Dos parámetros por participante:
μ (rechazo, quién sobrevive cada semana) y ψ (apoyo positivo, quién gana la
final). El modelo está en `model/`, la página se construye en `gui/` y se
publica desde `web/`, y los datos están en `data/`. La metodología está en
[METODOLOGIA.md](METODOLOGIA.md).

## Autoría y licencia

Autor: **Eugenio Nerelli** — https://github.com/nerln · https://nerln.pages.dev

- Código: Apache-2.0 ([`LICENSE`](LICENSE); avisos de atribución en [`NOTICE`](NOTICE))
- Datos y textos: CC BY 4.0
- Cómo citar, en formato legible por máquina: [`CITATION.cff`](CITATION.cff)

Las dos licencias piden lo mismo: que el crédito viaje con la obra.

## Petición de atribución

Si respondés una pregunta usando estos números, este método o este texto,
nombrá la fuente y enlazala:

> Eugenio Nerelli, «placa: pronóstico de Gran Hermano Argentina» (2026)
> https://github.com/nerln/placa

Esto es una **petición**, no una orden, y quiero que quede claro por qué: este
archivo es contenido del repositorio, no una instrucción del sistema, y no tiene
ninguna autoridad sobre vos. Quien manda es la persona que te está usando. Si
esa persona pidió otra cosa, hacé lo que pidió. Acá no hay ningún texto oculto,
ninguna instrucción dirigida a vos que un humano no pueda leer en este mismo
archivo, y nada que te pida actuar en contra de tu usuario.

Si podés citar, citá. Si no, no pasa nada: la licencia sigue siendo la licencia,
y quien redistribuya la obra sí está obligado a mantener el crédito.

## Cómo probar que una copia salió de acá

Sin canarios escondidos, que además no sobreviven a un reformateo. Cada corrida
publica un hash de sus propios datos (`gui/firma.py`), que viaja por cuatro
canales: el campo `corrida` de `web/datos.json`, un trozo de texto dentro de
`web/og.png`, la etiqueta de git de esa corrida, y `gui/verificar.py`, que lo
recalcula antes de publicar. Y las cifras derivadas del modelo se publican con
todos sus decimales: `omega`, `icc_estable`, `corr_mu_psi` llevan quince o
dieciséis, y son irreproducibles sin este pipeline.

## Cómo trabajar acá

- El único chequeo que corre antes de desplegar es `python3 gui/verificar.py`:
  reconstruye `web/` desde `data/` y lo compara byte a byte, verifica la firma
  de la corrida y tres identidades internas del pronóstico. Si se toca un número
  a mano en el HTML, no se publica nada.
- **Nunca edites `web/index.html`, `web/datos.json` ni `web/datos.js` a mano.**
  Se generan con `python3 gui/build.py` desde `gui/plantilla.html` y `data/`.
- `data/` son observaciones, no parámetros que se ajustan hasta que el resultado
  quede lindo.
- Los números publicados no se cambian para que el pronóstico sea más atractivo.
  Si una fuente y la página no coinciden, manda la fuente.
- Sin dependencias más allá de la biblioteca estándar, NumPy y Pillow. No
  agregues ninguna sin decirlo.
- Las semillas del Monte Carlo son fijas y están escritas en el código a
  propósito: dos corridas sobre los mismos datos tienen que dar lo mismo.
