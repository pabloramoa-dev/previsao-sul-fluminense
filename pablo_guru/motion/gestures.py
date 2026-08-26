"""Gestos e reacoes discretas para evitar poses rigidas."""
from manim import *


def nod(scene, head, angle=4*DEGREES, run_time=0.55):
    scene.play(Rotate(head, angle=angle), run_time=run_time/2, rate_func=smooth)
    scene.play(Rotate(head, angle=-angle), run_time=run_time/2, rate_func=smooth)


def listening_shift(scene, character, amount=0.06, run_time=0.65):
    scene.play(character.animate.shift(DOWN*amount + RIGHT*(amount*0.25)),
               run_time=run_time, rate_func=smooth)
    scene.play(character.animate.shift(UP*amount + LEFT*(amount*0.25)),
               run_time=run_time, rate_func=smooth)


def arm_emphasis(scene, arm, pivot, angle=10*DEGREES, run_time=0.7):
    scene.play(Rotate(arm, angle=angle, about_point=pivot), run_time=run_time/2,
               rate_func=rate_functions.ease_out_sine)
    scene.play(Rotate(arm, angle=-angle, about_point=pivot), run_time=run_time/2,
               rate_func=rate_functions.ease_in_sine)


def reaction_pause(scene, seconds=0.35):
    scene.wait(seconds)
