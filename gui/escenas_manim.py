# SPDX-FileCopyrightText: 2026 nerln <https://github.com/nerln>
# SPDX-License-Identifier: Apache-2.0
"""
Tres animaciones que explican el modelo, hechas con Manim.

Cada una responde una pregunta que en texto plano cuesta seguir:
  1. Identidad   · por qué una resta prueba que la placa está completa
  2. DosEscalas  · por qué no alcanza con que nadie te quiera echar
  3. MonteCarlo  · qué quiere decir "22,4%" cuando faltan siete eliminaciones

Formato cuadrado, porque la página se lee sobre todo en el teléfono. Sin LaTeX:
todo el texto pasa por Pango, así no hace falta una instalación de TeX.

    python3 -m manim -qm --format=mp4 gui/escenas_manim.py Identidad DosEscalas MonteCarlo
"""

from manim import *

config.pixel_width = 720
config.pixel_height = 720
config.frame_width = 8.0
config.frame_height = 8.0
config.background_color = "#0E1119"

ORO = "#C9A227"
ORO_CLARO = "#F0D274"
TINTA = "#F4F2EC"
TINTA2 = "#C2C8D6"
TINTA3 = "#949BAD"
ROJO = "#D8476E"
FUENTE = "Helvetica Neue"


def t(txt, size=26, color=TINTA, weight=NORMAL):
    return Text(txt, font=FUENTE, font_size=size, color=color, weight=weight)


class Identidad(Scene):
    """La resta que prueba que en esa placa no faltaba nadie."""

    def construct(self):
        titulo = t("Gala 27 · 3 de agosto", 30, ORO_CLARO, BOLD).to_edge(UP, buff=0.6)
        self.play(FadeIn(titulo, shift=DOWN * 0.3))

        nombres = ["Luana", "Juanicar", "Hanssen", "Majluf", "Sol", "Campanita"]
        valores = [0.1, 0.3, 0.5, 0.9, 46.7, 53.3]

        filas = VGroup()
        for n, v in zip(nombres, valores):
            fila = VGroup(
                t(n, 24, TINTA2),
                t(f"{v}".replace(".", ",") + "%", 24, ORO if v < 40 else ROJO),
            ).arrange(RIGHT, buff=0.5)
            fila[1].align_to(fila[0], DOWN)
            filas.add(fila)
        filas.arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        for f in filas:
            f[1].shift(RIGHT * (2.0 - f[1].get_left()[0]))     # columna de cifras alineada
        filas.move_to(ORIGIN).next_to(titulo, DOWN, buff=0.7)

        self.play(LaggedStart(*[FadeIn(f, shift=RIGHT * 0.4) for f in filas], lag_ratio=0.16))
        self.wait(0.4)

        linea = Line(LEFT * 2.2, RIGHT * 2.2, color=TINTA3, stroke_width=1.5)
        linea.next_to(filas, DOWN, buff=0.32)
        suma = t("101,8 %", 34, TINTA, BOLD).next_to(linea, DOWN, buff=0.3)
        self.play(Create(linea), FadeIn(suma, shift=UP * 0.2))
        self.wait(0.5)

        pregunta = t("¿Por qué no da 100?", 26, TINTA3).next_to(suma, DOWN, buff=0.45)
        self.play(FadeIn(pregunta))
        self.wait(1.0)
        self.play(FadeOut(pregunta))

        # el versus se renormaliza: esos dos porcentajes se reparten el residuo
        caja = SurroundingRectangle(VGroup(filas[4], filas[5]), color=ROJO,
                                    stroke_width=2, buff=0.14, corner_radius=0.06)
        etq = t("el mano a mano se reparte\nsobre lo que quedaba", 20, ROJO)
        etq.next_to(caja, LEFT, buff=0.3).shift(LEFT * 0.2)
        self.play(Create(caja), FadeIn(etq, shift=RIGHT * 0.2))
        self.wait(1.4)
        self.play(FadeOut(etq), FadeOut(caja))

        # la identidad
        self.play(FadeOut(linea), FadeOut(suma), FadeOut(titulo),
                  filas.animate.scale(0.8).move_to(UP * 2.15))

        eq1 = t("101,8  −  100  =  1,8", 32, TINTA)
        eq1.next_to(filas, DOWN, buff=0.7)
        self.play(Write(eq1))
        self.wait(0.7)

        arriba = VGroup(*[f for f in filas[:4]])
        caja2 = SurroundingRectangle(arriba, color=ORO, stroke_width=2, buff=0.12, corner_radius=0.06)
        eq2 = t("0,1 + 0,3 + 0,5 + 0,9  =  1,8", 28, ORO_CLARO).next_to(eq1, DOWN, buff=0.42)
        self.play(Create(caja2))
        self.play(Write(eq2))
        self.wait(0.8)

        tic = t("✓  cuadra", 34, ORO_CLARO, BOLD).next_to(eq2, DOWN, buff=0.5)
        self.play(FadeIn(tic, scale=1.3))
        self.wait(0.5)

        cierre = t("Si cuadra, en esa placa no faltaba nadie:\nes el reparto completo de los votos de la noche.",
                   21, TINTA2).next_to(tic, DOWN, buff=0.42)
        self.play(FadeIn(cierre, shift=UP * 0.2))
        self.wait(2.6)


class DosEscalas(Scene):
    """Bajo rechazo no es cariño. El caso Grosman."""

    def construct(self):
        titulo = t("Dos votaciones distintas", 32, ORO_CLARO, BOLD).to_edge(UP, buff=0.55)
        self.play(FadeIn(titulo, shift=DOWN * 0.3))

        # include_numbers usa LaTeX para las cifras y acá no hay una instalación
        # de TeX; las marcas se ponen a mano con Text, que pasa por Pango.
        eje1 = NumberLine(x_range=[0, 60, 20], length=6, color=TINTA3).shift(UP * 1.2)
        marcas1 = VGroup(*[t(f"{v}%", 17, TINTA3).next_to(eje1.n2p(v), DOWN, buff=0.14)
                           for v in (0, 20, 40, 60)])
        rot1 = t("votos para ELIMINARTE  →", 19, TINTA3).next_to(marcas1, DOWN, buff=0.18)
        self.play(Create(eje1), FadeIn(marcas1), FadeIn(rot1))

        def punto(x, nombre, color, eje, arriba=True):
            d = Dot(eje.n2p(x), color=color, radius=0.11)
            l = t(nombre, 19, color).next_to(d, UP if arriba else DOWN, buff=0.16)
            return VGroup(d, l)

        campeon = punto(2, "Tato (campeón)", ORO_CLARO, eje1)
        gros = punto(3, "Grosman", TINTA, eje1, arriba=False)
        self.play(FadeIn(campeon, scale=0.6), FadeIn(gros, scale=0.6))
        self.wait(0.6)

        obs = t("Los dos casi no reciben votos en contra.\nEn esta escala son la misma persona.",
                21, TINTA2).next_to(eje1, DOWN, buff=1.0)
        self.play(FadeIn(obs))
        self.wait(2.0)
        self.play(FadeOut(obs))

        # segunda escala
        eje2 = NumberLine(x_range=[0, 60, 20], length=6, color=TINTA3).shift(DOWN * 1.4)
        marcas2 = VGroup(*[t(f"{v}%", 17, TINTA3).next_to(eje2.n2p(v), DOWN, buff=0.14)
                           for v in (0, 20, 40, 60)])
        rot2 = t("votos para que GANES  →", 19, ORO).next_to(marcas2, DOWN, buff=0.18)
        self.play(Create(eje2), FadeIn(marcas2), FadeIn(rot2))

        c2 = punto(56.2, "Tato  56,2%", ORO_CLARO, eje2)
        g2 = punto(2, "Grosman  2%", ROJO, eje2, arriba=False)
        self.play(FadeIn(c2, scale=0.6))
        self.wait(0.4)
        self.play(FadeIn(g2, scale=0.6))
        self.wait(1.2)

        flecha = CurvedArrow(gros[0].get_center() + DOWN * 0.1, g2[0].get_center() + UP * 0.1,
                             color=ROJO, stroke_width=2.5, angle=-1.1)
        self.play(Create(flecha))
        self.wait(0.8)

        cierre = t("Que nadie te quiera echar\nno significa que alguien te quiera adentro.",
                   23, TINTA, BOLD).next_to(rot2, DOWN, buff=0.5)
        self.play(FadeIn(cierre, shift=UP * 0.25))
        self.wait(2.8)


class MonteCarlo(Scene):
    """Qué quiere decir un 22,4% cuando faltan siete eliminaciones."""

    def construct(self):
        titulo = t("Faltan 7 eliminaciones", 30, ORO_CLARO, BOLD).to_edge(UP, buff=0.55)
        sub = t("cada corrida juega una temporada entera", 20, TINTA3).next_to(titulo, DOWN, buff=0.18)
        self.play(FadeIn(titulo, shift=DOWN * 0.25), FadeIn(sub))

        import random
        random.seed(7)

        # un árbol que se abre: cada rama es una temporada posible
        origen = UP * 2.2
        niveles = [[origen]]
        ramas = VGroup()
        for nivel in range(6):
            nuevo = []
            for p in niveles[-1]:
                n_hijos = 2 if nivel < 5 else 1
                for k in range(n_hijos):
                    dx = (k - (n_hijos - 1) / 2) * (3.4 / (nivel + 1.15) ** 1.05)
                    q = p + DOWN * 0.48 + RIGHT * dx
                    ramas.add(Line(p, q, stroke_width=1.4,
                                   color=interpolate_color(ManimColor(ORO), ManimColor(TINTA3), nivel / 5)))
                    nuevo.append(q)
            niveles.append(nuevo)

        raiz = Dot(origen, color=ORO_CLARO, radius=0.09)
        self.play(FadeIn(raiz, scale=0.5))
        self.play(LaggedStart(*[Create(r) for r in ramas], lag_ratio=0.008, run_time=2.6))
        self.wait(0.5)

        hojas = VGroup(*[Dot(p, color=TINTA3, radius=0.036) for p in niveles[-1]])
        self.play(FadeIn(hojas, lag_ratio=0.02, run_time=0.9))

        # las hojas donde gana Tamara se encienden
        ganan = random.sample(range(len(hojas)), max(1, round(len(hojas) * 0.224)))
        self.play(*[hojas[i].animate.set_color(ORO_CLARO).scale(2.2) for i in ganan], run_time=1.0)
        self.wait(0.6)

        cuenta = t("22,4 %", 44, ORO_CLARO, BOLD)
        pie = t("de las temporadas simuladas\nlas gana Tamara", 20, TINTA2)
        grupo = VGroup(cuenta, pie).arrange(DOWN, buff=0.2).next_to(hojas, DOWN, buff=0.4)
        self.play(FadeIn(cuenta, scale=1.25), FadeIn(pie, shift=UP * 0.2))
        self.wait(1.2)

        aclara = t("No es que vaya a ganar.\nEs que gana más veces que cualquier otra.",
                   19, TINTA3).next_to(grupo, DOWN, buff=0.3)
        self.play(FadeIn(aclara))
        self.wait(2.6)
