# Actualización automática

El pronóstico se recalcula solo después de cada gala de eliminación y se vuelve
a publicar **en la misma URL**:

https://nerln.github.io/placa/

## Cómo funciona

Una página publicada no puede recalcularse a sí misma: no ejecuta el modelo ni
sale a buscar datos. Lo que se actualiza solo es el **proceso que la genera**.

Hay una tarea programada (`gh-dorada-actualizar`, en `~/.claude/scheduled-tasks/`) que corre los **martes y viernes a las 09:47**
y hace esto:

1. Lee la última gala registrada en `data/galas.json`.
2. Busca en la prensa si hubo alguna gala posterior a esa fecha.
3. **Si no hubo, no hace nada.** Es idempotente: correrla de más no rompe nada.
4. Si hubo, extrae el reparto oficial de votos, la nueva placa, el líder y la
   encuesta de la semana, y llama a `model/actualizar.py`.
5. Ese script comprueba la identidad aritmética, incorpora la gala, saca al
   eliminado del plantel, pasa la encuesta vieja al historial de calibración, y
   vuelve a correr `final_model.py`, `ramas.py`, `evolucion.py`, `bootstrap.py`,
   `camino.py`, `gui/build.py` y `gui/tarjeta.py`.
6. Commitea y empuja a `main`. GitHub Actions vuelve a construir la página desde
   los datos recién subidos, comprueba que coincida con la commiteada
   (`gui/verificar.py`) y recién entonces la publica.

Los martes cubren la gala del lunes. Los viernes cubren las de mitad de semana,
que en esta edición pasaron varias veces, como la del jueves 16 de julio.

> Las tareas programadas corren mientras la aplicación esté abierta. Si estaba
> cerrada cuando tocaba, se ejecuta en el siguiente arranque.

## Actualizar a mano

Si querés adelantarte o corregir algo:

```bash
cd gh_dorada_predictor

python3 model/actualizar.py \
  --gala 28 --fecha 2026-08-10 \
  --placa "Charlotte,Majluf,Sol,Hanssen,Pincoya,Zilli" \
  --salvados "Zilli:0.8,Pincoya:1.1,Majluf:2.4,Charlotte:5.2" \
  --versus "Sol:47.9,Hanssen:52.1" \
  --eliminado Hanssen \
  --nueva-placa "Sol,Majluf,Mariela,Luana,Tamara" \
  --nuevo-lider Pincoya --fecha-proxima 2026-08-17
```

Agregá `--dry-run` para ver qué haría sin escribir nada.

### Otras situaciones

**Alguien se va sin votación** (abandono, expulsión, evacuación médica):

```bash
python3 model/actualizar.py --abandono Juanicar --fecha 2026-08-06 \
  --modo abandono --motivo "problema de salud de su madre" \
  --nueva-placa "Charlotte,Majluf,Sol,Hanssen,Pincoya,Zilli"
```

**La gala tuvo fase de voto positivo** (placa mixta «Generación Dorada»):

```bash
  --positivo-candidatos "Sol,Majluf,Mariela,Luana,Tamara,Pincoya,Yipio" \
  --positivo-orden "Pincoya,Tamara,Yipio"
```

Los rankings positivos son el dato más valioso del modelo: son lo único que mide
directamente la escala que decide la final. Cargalos siempre que existan.

**Hay encuesta para la próxima gala:**

```bash
  --encuesta "Sol:48.2,Majluf:24.1,Luana:12.0" \
  --encuesta-fecha 2026-08-14 --encuesta-n 22000 --encuesta-resto 3.5
```

Si no hay, el script deja la encuesta vacía y el modelo corre solo con
preferencia revelada. Es un modo previsto, no un fallo.

### Después de actualizar, publicar

El script deja `web/` listo. Publicar es empujar:

```bash
python3 gui/verificar.py && git add -A && \
  git commit -m "gala NN: <eliminado> con NN,N%" && git push
```

`verificar.py` es la misma comprobación que corre en CI, así que si pasa acá el
despliegue no se va a caer allá. Lo que hace es reconstruir `web/` desde `data/`
y comparar: si la página publicada dejó de ser reproducible a partir de los
datos del repositorio, no sale.

Queda además `gui/pronostico.html`, la versión autocontenida de un solo archivo,
por si hace falta pasarla por un canal donde no se pueda enlazar el sitio.

## Qué revisar de vez en cuando

Estas cosas la automatización **no** las resuelve sola y conviene mirarlas cada
tanto:

- **Cambia el signo del voto.** Si una gala pasa a ser de voto positivo puro, no
  entra en `galas.json` como negativa: cargala como fase positiva.
- **Se confirma la fecha de la final** o el número de finalistas. Están como
  supuesto en `model/final_model.py` (`p3 = 0.70`).
- **Quedan pocos jugadores.** Con 4 o 5 en la casa, la propensión de nominación
  deja de importar porque cae en placa casi todo el mundo, y el pronóstico pasa
  a depender casi solo de ψ.
- **Aparece un mercado de apuestas real.** Hoy no existe; si apareciera con
  volumen, sería la señal más informativa disponible y habría que incorporarla.
