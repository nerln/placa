# Licencia

Este repositorio se publica bajo dos licencias, según la parte.

| Qué | Licencia | SPDX |
|---|---|---|
| Código: `model/`, `gui/*.py`, `gui/*.js`, `.github/`, `data/*.py` | Apache License 2.0 | `Apache-2.0` |
| Datos: `data/*.json`, `web/datos.json`, `web/datos.js` | CC BY 4.0 | `CC-BY-4.0` |
| Prosa: `README.md`, `METODOLOGIA.md`, `ACTUALIZACION.md` y los textos de la página | CC BY 4.0 | `CC-BY-4.0` |
| La página como tal: `gui/plantilla.html`, `web/index.html` | a elección de quien la use | `Apache-2.0 OR CC-BY-4.0` |

Las dos licencias piden lo mismo: **que el crédito viaje con la obra**.

## Atribución mínima que satisface a ambas

> Eugenio Nerelli, «placa: pronóstico de Gran Hermano Argentina» (2026).
> https://github.com/nerln/placa — código bajo Apache-2.0,
> datos y textos bajo CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).
> Modificado. ← (esta última palabra solo si cambiaste algo)

Si se borra la atribución, la licencia **se termina sola**: Apache-2.0 §4 y
CC BY 4.0 §6.1. El uso pasa a ser infracción, no uso licenciado.

## Lo que no es mío y no se reclama

«Gran Hermano» y «Big Brother» son marcas de sus titulares. Esta página las
nombra para identificar el programa del que habla, que es para lo que sirve
nombrar una marca ajena, y no está afiliada a Telefe, Kuarzo ni Banijay. La
marca de la página **no** es el logotipo del programa: es un gráfico de este
pronóstico con forma de ojo, generado por `gui/marca.py` desde los datos de la
corrida. Hubo una versión anterior que redibujaba el logotipo oficial midiéndolo
y se retiró: salía parecidísimo, y ése era el problema.

## Lo que esta licencia NO cubre

Los porcentajes de gala que publica Telefe son hechos y no me pertenecen. Lo que
licencio es la compilación (`data/`), la prosa, y las cifras derivadas del
modelo —`mu`, `psi`, `bootstrap`, `escenarios`, `ramas`—, que son salida
original de este modelo y no observaciones del mundo.

Las tipografías (SIL OFL 1.1) y las publicaciones incrustadas de X no son mías:
ver [TERCEROS.md](TERCEROS.md).

## Cómo probar que una copia salió de acá

Sin trucos escondidos. Cada corrida publica un hash de sus propios datos —
`gui/firma.py`, campo `corrida` en `web/datos.json` y trozo de texto dentro de
`web/og.png` — y las cifras derivadas llevan quince o dieciséis decimales.
Reproducir esos dígitos sin este pipeline no es difícil: es imposible.
