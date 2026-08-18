# Qué hacer cuando termina una gala de eliminación

Esta es la rutina completa. La sigue una persona o la sigue un agente; está
escrita para que dé lo mismo. Vale para cualquier gala, no sólo para la próxima.

Antes de tocar nada, leé `EVALUACION.md`: fija cómo se puntúa lo que la página
prometió, y está escrito desde antes de que terminara la temporada.

---

## 1. Averiguar qué pasó

Necesitás tres cosas: **quién salió**, **el reparto de votos** si se publicó, y
**la placa nueva** si ya se armó.

La fuente original es `mitelefe.com`, que es el sitio de la emisora. Cruzala con
prensa argentina: Infobae, La Nación, A24/PrimiciasYa, Ciudad Magazine, El
Destape. Contar seis notas que replican a la misma fuente no son seis fuentes.

Telefe suele cantar los salvados en orden, cada uno con su cuota sobre el total
de la placa, y después el mano a mano final entre los dos últimos, renormalizado
sobre lo que queda. Esa estructura es la que espera `model/actualizar.py`.

**Tres reglas que no se negocian.**

- Si el nombre de quien salió **no está en la placa que el repositorio tenía
  cargada**, pará y no publiques. Algo se entendió mal, y publicar un resultado
  sobre otra placa es peor que no actualizar.
- Si una nota **no lleva fecha en el cuerpo**, no la uses para fechar nada.
  Deducir una fecha no es fecharla, y ya costó una corrección pública.
- Si conseguís **una sola fuente**, publicá igual pero decilo en el texto: «por
  ahora lo publica sólo Telefe».

## 2. Cargar la gala

```
python3 model/actualizar.py --gala <N> --fecha AAAA-MM-DD \
  --placa "Nombre,Nombre,…" \
  --salvados "Nombre:cuota,Nombre:cuota,…" \
  --versus "Nombre:pct,Nombre:pct" \
  --eliminado Nombre
```

Los nombres son los cortos que ya usa `data/`, no los completos. Mirá
`data/galas.json` para ver cuáles son.

Si la placa de la semana siguiente ya se conoce, agregá
`--nueva-placa "…" --nuevo-lider Nombre --fecha-proxima AAAA-MM-DD`. Si no se
conoce todavía, no la inventes: dejá esos tres afuera y el modelo simula la
próxima gala sin placa observada, que es lo correcto.

`actualizar.py` recalcula el modelo entero solo. No hace falta correr nada más
de `model/`.

## 3. Puntuar lo que se había prometido

```
python3 model/puntaje.py
```

Sin argumentos toma la última gala resuelta. Lee lo que quedó congelado en
`data/historial_pronostico.json` **antes** de la gala y puntúa por separado las
dos afirmaciones que la página hace sobre la misma pregunta: la del modelo y la
apuesta declarada. Escribe `data/puntaje.json`, y con eso la sección del
resultado se enciende sola arriba de la apuesta.

Se niega a puntuar si quien salió no estaba en la placa congelada. Si se niega,
no lo fuerces: leé el mensaje, que te está diciendo que algo no cuadra.

## 4. Escribir la novedad

Agregá una entrada al principio de `data/ultimo.json`. La forma está en las que
ya hay. Lo que tiene que decir:

- quién salió, con qué porcentaje, y **a qué visita se llevó** si la gala era en
  dupla;
- qué le pasó al pronóstico, en el campo `afecta`;
- `impacto`, que es uno de `recalculado`, `pendiente`, `parcial` o `sin_efecto`;
- `fuente`, con la URL.

Y revisá si alguna otra entrada quedó vieja con el resultado a la vista.

## 5. Publicar

```
bin/publicar.sh
```

Reconstruye, pasa las diez comprobaciones y empuja. **Si alguna comprobación
falla no publica y sale con error**: leé cuál falló y arreglá eso, no la
comprobación. Con `--sin-empujar` deja el commit hecho sin mandarlo.

Si el push falla por credenciales, dejá el commit y decilo claramente en el
informe final, con el hash.

## Cómo se escribe acá

La prosa de la página tiene reglas y conviene respetarlas.

- **Nunca una raya larga.** Si hace falta, partí la oración.
- Nada de «no es X, es Y» ni de contraposiciones puestas para dar ritmo.
- No cerrar párrafos con una sentencia.
- Los números en castellano rioplatense: coma decimal y punto de miles.
- Ningún número escrito a mano en la prosa si sale de `data/`: se lee de ahí.
- No inventes una cifra para redondear una frase. El fandom comprueba.

---

## Si esto lo corre un agente en la nube

Comprobado el 17 de agosto de 2026 en el entorno «Default» de las routines.

**Puede empujar a `main`.** Las credenciales viajan en el proxy del entorno y
`git push` anda. O sea que `bin/publicar.sh` funciona de punta a punta sin la
máquina de nadie.

**Pero no tiene salida a internet.** Todos los dominios probados dieron
`EGRESS_BLOCKED`, y no es cosa de `WebFetch`: `curl` devuelve código `000`
contra mitelefe, Infobae, La Nación y publish.twitter.com. Lo único abierto es
PyPI. Quiere decir que **no puede abrir ni una nota**.

Lo que sí funciona es **`WebSearch`**, que sale por el servicio de Anthropic y no
por la red de la caja. Devuelve títulos, enlaces y fragmentos. Alcanza para saber
un nombre, no para leer un reparto de votos.

Así que desde la nube la rutina se corre recortada, y se dice que está recortada:

- El nombre de quien salió se toma sólo si **dos medios distintos** coinciden en
  los resultados de la búsqueda. Un solo titular no alcanza, y un fragmento
  ambiguo tampoco.
- La gala se carga **sin `--salvados` ni `--versus`**, que es un caso que
  `actualizar.py` ya contempla: queda anotada como incompleta.
- En la novedad se escribe que el reparto de votos todavía no está cargado.
- El resto de la rutina es igual, y `model/puntaje.py` sólo necesita el nombre.

**Falta numpy y falta Pillow.** Empezá con `pip install numpy pillow`, que anda.
Sin Pillow, `verificar.py` se cae al comprobar la tarjeta. Node sí está.
`gh` no está instalado.
