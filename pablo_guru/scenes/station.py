"""PABLO GURU — A ESTACAO | cena V2 isolada.

Primeiro teste visual: enquadramento, ritmo, articulacao e expressoes.
Audio definitivo entra pela camada audio/ sem acelerar a timeline.
"""
from manim import *

config.frame_width = 8.0
config.frame_height = 14.222
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_rate = 30


class EstacaoV2(MovingCameraScene):
    def construct(self):
        # fundo em camadas para parallax visual
        sky = Rectangle(width=10, height=16, fill_color="#c9d5dd", fill_opacity=1, stroke_width=0)
        wall = Rectangle(width=10, height=7.0, fill_color="#6f7880", fill_opacity=1, stroke_width=0).shift(UP*1.0)
        floor = Polygon([-5,-7,0],[5,-7,0],[5,-1.5,0],[-5,-1.5,0], fill_color="#4d5054", fill_opacity=1, stroke_width=0)
        sign = VGroup(
            RoundedRectangle(width=4.7, height=0.8, corner_radius=0.12, fill_color="#25384b", fill_opacity=1, stroke_width=0),
            Text("ESTACAO", font="Poppins", weight=BOLD, font_size=38, color=WHITE)
        ).shift(UP*4.8)
        self.add(sky, wall, floor, sign)

        # silhuetas temporarias: o rig final substitui estes marcadores.
        pablo = VGroup(
            Circle(0.72, fill_color="#d7a27d", fill_opacity=1, stroke_color="#17191f", stroke_width=7),
            RoundedRectangle(width=1.7, height=2.6, corner_radius=0.35, fill_color="#8b704f", fill_opacity=1, stroke_color="#17191f", stroke_width=7).shift(DOWN*1.55),
        ).move_to([-1.45,-1.0,0])
        mulher = VGroup(
            Circle(0.68, fill_color="#d9a783", fill_opacity=1, stroke_color="#17191f", stroke_width=7),
            RoundedRectangle(width=1.55, height=2.45, corner_radius=0.35, fill_color="#526f85", fill_opacity=1, stroke_color="#17191f", stroke_width=7).shift(DOWN*1.48),
        ).move_to([1.35,-1.0,0])
        self.add(pablo, mulher)

        # entrada calma; nada de camera acelerada.
        self.camera.frame.save_state()
        self.play(self.camera.frame.animate.scale(0.95).move_to([0,-0.25,0]), run_time=3.2, rate_func=smooth)
        self.wait(1.2)
        self.play(mulher.animate.shift(LEFT*0.08), run_time=0.8, rate_func=there_and_back)
        self.wait(1.0)
        self.play(pablo.animate.shift(RIGHT*0.06), run_time=1.0, rate_func=there_and_back)
        self.wait(1.0)
        self.play(Restore(self.camera.frame), run_time=2.4, rate_func=smooth)
        self.wait(0.5)
