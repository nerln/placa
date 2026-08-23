# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""Arma los videos verticales de TikTok y Reels con los números de la corrida.

QUÉ HACE CADA UNO. El fondo lo genera Omni y no dice nada: es un anillo de arcos
dorados sobre azul noche, sin ninguna marca del programa. Los números y el texto
se dibujan acá, con PIL, y se superponen. Esa división no es capricho: un modelo
de video escribe cifras que parecen cifras y no lo son, y acá una cifra
equivocada es lo único que no se puede publicar.

DE DÓNDE SALEN LOS NÚMEROS. De `web/datos.json` y `data/apuesta.json` de la
corrida vigente, leídos en el momento de armar. No hay ninguna cifra escrita a
mano en este archivo. Si la corrida cambia, los videos cambian solos, y si un
número que el guion espera no está, el guion se cae en vez de inventarlo.

    python3 social/video/montar.py           los ocho
    python3 social/video/montar.py 1 4       sólo esos

Salen en `social/video/salida/`, 1080x1920, listos para subir.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).parent
FONDO = AQUI / "anillo.mp4"
SALIDA = AQUI / "salida"
AUDIO = AQUI / "audio"
TIPO = AQUI / "tipos"

W, H = 1080, 1920
FPS = 30

AZUL = (4, 22, 43)
ORO = (226, 183, 90)
ORO_FUERTE = (246, 180, 14)
CREMA = (244, 242, 236)
GRIS = (143, 168, 196)

# Zonas que tapa la interfaz. En vertical, TikTok pone la descripción y los
# botones abajo a la derecha, y arriba el buscador. Nada importante va ahí.
SEGURO_ARRIBA = 330
SEGURO_ABAJO = 520



# Qué base musical lleva cada reel. Son dos, y se reparten a propósito.
#
# La idea es de Eugenio y es la correcta: no hace falta una base por video, hacen
# falta dos o tres y repartirlas de modo que, si una tanda funciona, se pueda
# saber si fue la música o fue el tema. Por eso el reparto está cruzado: cada
# base lleva cuatro videos, y dentro de cada base hay confesiones, predicciones y
# explicaciones. Si «tension» gana en los cuatro sin importar el tema, es la
# música. Si ganan las tres confesiones repartidas entre las dos bases, es el
# tema. Repartirlas al azar habría hecho imposible distinguir las dos cosas.
BASES = {
    1: "tension",   # predicción: le voy en contra al modelo
    2: "reloj",     # contradicción: Sol, 1 de cada 173
    3: "tension",   # explicación: los márgenes se pisan
    4: "reloj",     # confesión: el backtest, cero de siete
    5: "tension",   # confesión: la gala 29, puesto 3 de 5
    6: "reloj",     # explicación: quién va a placa
    7: "tension",   # explicación: la regla histórica
    8: "reloj",     # confesión: la campaña que se mide y no se usa
}

def datos():
    d = json.loads((RAIZ / "web" / "datos.json").read_text())
    a = json.loads((RAIZ / "data" / "apuesta.json").read_text())
    return d, a


def fuente(tam, negrita=True):
    from PIL import ImageFont
    for ruta in (
        TIPO / ("Inter-Bold.ttf" if negrita else "Inter-Regular.ttf"),
        Path.home() / "dev/MoneyPrinterTurbo/resource/fonts/BeVietnamPro-Bold.ttf",
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        Path("/System/Library/Fonts/Helvetica.ttc"),
    ):
        if ruta.exists():
            return ImageFont.truetype(str(ruta), tam)
    raise SystemExit("no encontré ninguna tipografía")


def placa_texto(lineas, dest):
    """Un PNG transparente con las líneas centradas, del tamaño del video.

    Se dibuja entero y no por línea: así el interlineado se controla acá y no
    con la posición de cada superposición, que era donde se desalineaba.
    """
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    alto = sum(t + esp for _txt, t, _col, esp in lineas)
    y = (H - alto) / 2 + 60
    for txt, tam, col, esp in lineas:
        f = fuente(tam)
        d.text((W / 2, y + tam / 2), txt, font=f, anchor="mm", fill=col + (255,),
               stroke_width=max(2, tam // 22), stroke_fill=(4, 12, 24, 220))
        y += tam + esp
    img.save(dest)


def barras(dest, filas):
    """Dos barras con su intervalo, para el video de la incertidumbre.

    La barra es la probabilidad y la línea clara arriba es el intervalo del 90%.
    Se ven pisándose, que es todo el argumento del video.
    """
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, ancho = 150, W - 300
    tope = max(hi for _n, _p, _lo, hi in filas) * 1.15
    y = H / 2 - 150
    for nombre, p, lo, hi in filas:
        f = fuente(52)
        d.text((x0, y - 70), f"{nombre}  {p*100:.1f}%".replace(".", ","), font=f,
               fill=CREMA + (255,), stroke_width=3, stroke_fill=(4, 12, 24, 220))
        d.rounded_rectangle([x0, y, x0 + ancho * (p / tope), y + 46], 23, fill=ORO + (255,))
        d.line([x0 + ancho * (lo / tope), y + 23, x0 + ancho * (hi / tope), y + 23],
               fill=CREMA + (200,), width=7)
        for x in (lo, hi):
            px = x0 + ancho * (x / tope)
            d.line([px, y + 2, px, y + 44], fill=CREMA + (220,), width=7)
        y += 230
    img.save(dest)


def montar(n, capas, segundos, base=None):
    """Superpone las capas sobre el fondo y saca el mp4.

    El fondo dura diez segundos y el video dura más: se repite en bucle. No se
    nota porque el fondo no cuenta nada, y ésa es exactamente la razón por la que
    el fondo no cuenta nada.
    """
    SALIDA.mkdir(exist_ok=True)
    dest = SALIDA / f"video{n}.mp4"
    entradas = ["-stream_loop", "-1", "-i", str(FONDO)]
    audio = AUDIO / f"{base}.mp3" if base else None
    for png, _a, _b in capas:
        entradas += ["-i", str(png)]
    filtros = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
               f"crop={W}:{H},setsar=1,trim=0:{segundos},setpts=PTS-STARTPTS[base]"]
    actual = "[base]"
    for i, (_png, desde, hasta) in enumerate(capas, start=1):
        sig = f"[c{i}]" if i < len(capas) else "[v]"
        filtros.append(f"{actual}[{i}:v]overlay=0:0:enable='between(t,{desde},{hasta})'{sig}")
        actual = sig
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *entradas]
    if audio and audio.exists():
        cmd += ["-i", str(audio)]
        # Medio segundo de fundido al final: cortar una base en seco se escucha.
        filtros.append(f"[{len(capas) + 1}:a]atrim=0:{segundos},asetpts=PTS-STARTPTS,"
                       f"afade=t=out:st={max(segundos - 0.5, 0):.2f}:d=0.5[a]")
    cmd += ["-filter_complex", ";".join(filtros), "-map", "[v]"]
    if audio and audio.exists():
        cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "160k", "-ar", "44100"]
    # Los hilos van atados a mano. Con los de fábrica cada hilo de x264 se queda
    # con su juego de cuadros a 1080x1920 y el pico se va arriba de 500MB, que en
    # esta máquina significa no arrancar nunca. Con dos hilos tarda un poco más y
    # entra.
    cmd += ["-t", str(segundos), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-threads", "2", "-filter_complex_threads", "1",
            "-pix_fmt", "yuv420p", "-r", str(FPS), str(dest)]
    subprocess.run(cmd, check=True)
    print(f"  video{n}.mp4  {segundos}s  base {base or 'sin audio'}")
    return dest


def video1(d, a):
    q = a["llamada"]["quien"]
    p = a["p_sale"][q] * 100
    seg = sorted(((k, v) for k, v in a["p_sale"].items() if k != q), key=lambda x: -x[1])[:2]
    m = max(a["modelo_dice"], key=a["modelo_dice"].get)
    pm = a["modelo_dice"][m] * 100
    tmp = AQUI / "_tmp"; tmp.mkdir(exist_ok=True)
    capas = []
    def añadir(nombre, lineas, desde, hasta):
        png = tmp / f"v1-{nombre}.png"; placa_texto(lineas, png); capas.append((png, desde, hasta))
    añadir("a", [(f"ESTA NOCHE", 96, CREMA, 24), ("SE VA", 96, CREMA, 24), (q.upper(), 150, ORO_FUERTE, 0)], 0, 2.5)
    añadir("b", [(f"{p:.1f}%".replace(".", ","), 210, ORO_FUERTE, 40),
                 (f"{seg[0][0]} {seg[0][1]*100:.1f}".replace(".", ",") + f"   {seg[1][0]} {seg[1][1]*100:.1f}".replace(".", ","), 56, GRIS, 0)], 2.5, 6)
    añadir("c", [("MI MODELO", 100, CREMA, 24), ("DICE OTRA COSA", 100, CREMA, 0)], 6, 9)
    añadir("d", [(m.upper(), 150, ORO, 30), (f"{pm:.1f}%".replace(".", ","), 190, ORO_FUERTE, 0)], 9, 12)
    añadir("e", [("NO LE HAGO CASO", 110, CREMA, 0)], 12, 14.5)
    añadir("f", [("en esa pregunta", 72, GRIS, 20), ("anda peor", 88, CREMA, 20), ("que el azar", 88, CREMA, 0)], 14.5, 18)
    añadir("g", [("si falla,", 76, GRIS, 20), ("queda escrito", 96, CREMA, 40), ("nerln.github.io/placa", 52, ORO, 0)], 18, 22)
    return montar(1, capas, 22, BASES[1])


def video2(d, a):
    p = d["escenarios"]["base"]["p_gana"]["Sol"] * 100
    c = json.loads((RAIZ / "data" / "camino.json").read_text())
    v = json.loads((RAIZ / "data" / "versus.json").read_text())
    g, pierde = v["registro"]["Sol"]
    tmp = AQUI / "_tmp"; tmp.mkdir(exist_ok=True)
    capas = []
    def añadir(nombre, lineas, desde, hasta):
        png = tmp / f"v2-{nombre}.png"; placa_texto(lineas, png); capas.append((png, desde, hasta))
    añadir("a", [("SOL GANA EN", 92, CREMA, 24), ("1 UNIVERSO", 120, ORO_FUERTE, 16), (f"DE CADA {c['una_de_cada']}", 120, ORO_FUERTE, 0)], 0, 3)
    añadir("b", [(f"{p:.2f}%".replace(".", ","), 210, ORO_FUERTE, 0)], 3, 5.5)
    añadir("c", [("tiene que zafar de", 68, GRIS, 20), (f"{c['eliminaciones_que_sobrevive']:.1f}".replace(".", ","), 180, CREMA, 10), ("eliminaciones", 76, CREMA, 0)], 5.5, 9)
    añadir("d", [("MANO A MANO", 92, CREMA, 30), (f"{g} DE {g + pierde}", 190, ORO_FUERTE, 0)], 9, 13)
    añadir("e", [("la mejor", 84, ORO, 16), ("en el mano a mano", 64, GRIS, 46), ("la peor", 84, ORO, 16), ("para ganar", 64, GRIS, 0)], 13, 16.5)
    añadir("f", [("las dos cosas", 92, CREMA, 20), ("son verdad", 92, CREMA, 0)], 16.5, 20)
    return montar(2, capas, 20, BASES[2])


def video3(d, a):
    p = d["escenarios"]["base"]["p_gana"]; ic = d["bootstrap"]["ic90"]
    uno, dos = "Charlotte", "Tamara"
    tmp = AQUI / "_tmp"; tmp.mkdir(exist_ok=True)
    capas = []
    def añadir(nombre, lineas, desde, hasta):
        png = tmp / f"v3-{nombre}.png"; placa_texto(lineas, png); capas.append((png, desde, hasta))
    añadir("a", [(f"{uno.upper()} {p[uno]*100:.1f}".replace(".", ","), 96, ORO_FUERTE, 26),
                 (f"{dos.upper()} {p[dos]*100:.1f}".replace(".", ","), 96, CREMA, 0)], 0, 3)
    añadir("b", [("parece resuelto", 96, GRIS, 0)], 3, 5)
    png = tmp / "v3-barras.png"
    barras(png, [(uno, p[uno], ic[uno][0], ic[uno][1]), (dos, p[dos], ic[dos][0], ic[dos][1])])
    capas.append((png, 5, 12.5))
    añadir("d", [("se pisan", 130, ORO_FUERTE, 0)], 12.5, 14.5)
    dif = (p[uno] - p[dos]) * 100
    err = (ic[uno][1] - ic[uno][0]) * 100
    añadir("e", [(f"{dif:.0f} puntos de diferencia", 72, CREMA, 24),
                 (f"{err:.0f} de incertidumbre", 72, ORO, 0)], 14.5, 18)
    return montar(3, capas, 18, BASES[3])




def _capas(pref, tmp):
    """Fabriquita para no repetir el mismo bloque en cada video."""
    capas = []
    def añadir(nombre, lineas, desde, hasta):
        png = tmp / f"{pref}-{nombre}.png"
        placa_texto(lineas, png)
        capas.append((png, desde, hasta))
    return capas, añadir


def video4(d, a):
    """La confesión. El más fuerte que tiene esta cuenta y el que nadie copia."""
    r = json.loads((RAIZ / "data" / "retro.json").read_text())
    tmp = AQUI / "_tmp"; tmp.mkdir(exist_ok=True)
    capas, añadir = _capas("v4", tmp)
    añadir("a", [("PROBÉ MI MODELO", 92, CREMA, 24), ("CONTRA LAS GALAS", 92, CREMA, 24),
                 ("YA JUGADAS", 92, CREMA, 0)], 0, 3)
    añadir("b", [(f"{r['aciertos']} DE {r['n']}", 230, ORO_FUERTE, 30), ("aciertos", 68, GRIS, 0)], 3, 6.5)
    añadir("c", [("el azar habría", 68, GRIS, 20), (f"acertado {r['aciertos_esperados_azar']:.2f}".replace(".", ","), 96, CREMA, 0)], 6.5, 10)
    añadir("d", [("puso al eliminado", 68, GRIS, 20),
                 (f"en el puesto {r['puesto_medio']:.2f}".replace(".", ","), 88, CREMA, 20),
                 (f"el azar lo pone en {r['puesto_medio_azar']:.2f}".replace(".", ","), 60, GRIS, 0)], 10, 14)
    añadir("e", [("anda peor", 110, ORO_FUERTE, 20), ("que una moneda", 96, CREMA, 0)], 14, 17.5)
    añadir("f", [("está publicado", 76, GRIS, 24), ("con el test al lado", 76, CREMA, 40),
                 ("nerln.github.io/placa", 52, ORO, 0)], 17.5, 21)
    return montar(4, capas, 21, BASES[4])


def video5(d, a):
    """La última gala, con la nota que se puso solo."""
    p = json.loads((RAIZ / "data" / "puntaje.json").read_text())
    m = p["modelo"]
    tmp = AQUI / "_tmp"; tmp.mkdir(exist_ok=True)
    capas, añadir = _capas("v5", tmp)
    añadir("a", [(f"GALA {p['gala']}", 96, CREMA, 24), ("SE FUE", 88, GRIS, 20),
                 (p["eliminado"].upper(), 140, ORO_FUERTE, 0)], 0, 3)
    añadir("b", [("mi modelo lo tenía", 68, GRIS, 24),
                 (f"{m['puesto']}º DE {m['de']}", 200, CREMA, 0)], 3, 6.5)
    añadir("c", [("le había dado", 68, GRIS, 20),
                 (f"{m['p_del_eliminado']*100:.1f}%".replace(".", ","), 190, ORO_FUERTE, 0)], 6.5, 10)
    añadir("d", [("Brier", 76, GRIS, 16), (f"{m['brier']:.3f}".replace(".", ","), 150, CREMA, 24),
                 (f"tirar al azar da {m['brier_uniforme']:.1f}".replace(".", ","), 60, GRIS, 0)], 10, 14)
    añadir("e", [("peor que el azar,", 84, CREMA, 20), ("otra vez", 100, ORO_FUERTE, 0)], 14, 17)
    añadir("f", [("la regla estaba escrita", 64, GRIS, 20), ("antes de la gala", 76, CREMA, 0)], 17, 20)
    return montar(5, capas, 20, BASES[5])


def video6(d, a):
    """Quién termina en placa. No es lo mismo que quién se va."""
    pr = d["propension"]
    orden = sorted(pr.items(), key=lambda x: -x[1])
    top, ultimo = orden[0], orden[-1]
    tmp = AQUI / "_tmp"; tmp.mkdir(exist_ok=True)
    capas, añadir = _capas("v6", tmp)
    añadir("a", [("QUIÉN TERMINA", 96, CREMA, 24), ("EN PLACA", 120, ORO_FUERTE, 0)], 0, 2.5)
    añadir("b", [("no es lo mismo", 72, GRIS, 20), ("que quién se va", 88, CREMA, 0)], 2.5, 5.5)
    lineas = [(f"{k}   {v:+.2f}".replace(".", ","), 62, ORO if i == 0 else CREMA, 18)
              for i, (k, v) in enumerate(orden)]
    añadir("c", lineas, 5.5, 13)
    añadir("d", [(top[0].upper(), 130, ORO_FUERTE, 24), ("la nominan siempre", 68, GRIS, 0)], 13, 16)
    añadir("e", [(ultimo[0].upper(), 130, CREMA, 24), ("casi nunca", 68, GRIS, 0)], 16, 19)
    return montar(6, capas, 19, BASES[6])


def video7(d, a):
    """La regla histórica: por qué caer bien no alcanza."""
    tmp = AQUI / "_tmp"; tmp.mkdir(exist_ok=True)
    capas, añadir = _capas("v7", tmp)
    añadir("a", [("CAER BIEN", 120, CREMA, 24), ("NO ALCANZA", 120, ORO_FUERTE, 0)], 0, 3)
    añadir("b", [("seis casos con", 68, GRIS, 20), ("rechazo bajo", 96, CREMA, 0)], 3, 6)
    añadir("c", [("2", 210, ORO_FUERTE, 16), ("ganaron", 72, CREMA, 0)], 6, 9)
    añadir("d", [("4", 210, CREMA, 16), ("terminaron entre", 60, GRIS, 16),
                 ("0,5% y 15,7%", 96, ORO, 0)], 9, 13)
    añadir("e", [("no te salva", 84, GRIS, 20), ("que no te odien", 96, CREMA, 20),
                 ("te salva que te voten", 84, ORO_FUERTE, 0)], 13, 17.5)
    return montar(7, capas, 17.5, BASES[7])


def video8(d, a):
    """La campaña de X: medida, publicada, y deliberadamente fuera del modelo."""
    c = json.loads((RAIZ / "data" / "campana.json").read_text())
    tmp = AQUI / "_tmp"; tmp.mkdir(exist_ok=True)
    capas, añadir = _capas("v8", tmp)
    añadir("a", [("MIDO LAS CAMPAÑAS", 88, CREMA, 24), ("DE X", 130, ORO_FUERTE, 0)], 0, 3)
    añadir("b", [("posiciones del top 50", 64, GRIS, 20), ("de tendencias", 64, GRIS, 20),
                 ("en Argentina", 76, CREMA, 0)], 3, 6.5)
    añadir("c", [("y NO las meto", 100, ORO_FUERTE, 24), ("en el modelo", 96, CREMA, 0)], 6.5, 10)
    añadir("d", [("con una sola ventana", 64, GRIS, 20), ("no hay con qué", 88, CREMA, 20),
                 ("estimar cuánto pesan", 64, GRIS, 0)], 10, 14)
    añadir("e", [("meterla sin medirla", 76, CREMA, 20), ("sería inventar", 92, ORO_FUERTE, 0)], 14, 17.5)
    return montar(8, capas, 17.5, BASES[8])


def main():
    if not FONDO.exists():
        raise SystemExit(f"falta el fondo: {FONDO}")
    todos = [str(i) for i in range(1, 9)]
    quiere = [a for a in sys.argv[1:] if a in todos] or todos
    d, a = datos()
    print(f"corrida {d['generado']} · gala {a['gala']} del {a['fecha_gala']}")
    for n in quiere:
        {"1": video1, "2": video2, "3": video3, "4": video4,
         "5": video5, "6": video6, "7": video7, "8": video8}[n](d, a)


if __name__ == "__main__":
    main()
