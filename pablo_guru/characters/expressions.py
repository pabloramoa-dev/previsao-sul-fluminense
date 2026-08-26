"""Microexpressoes reutilizaveis para personagens V2."""
from manim import *


def blink_pair(left_eye, right_eye, amount=0.12):
    return AnimationGroup(
        left_eye.animate.stretch(amount, 1),
        right_eye.animate.stretch(amount, 1),
        lag_ratio=0,
    )


def listening_brows(left_brow, right_brow):
    """Expressao de escuta: leve assimetria, sem caricatura excessiva."""
    return AnimationGroup(
        left_brow.animate.shift(UP * 0.035).rotate(0.05),
        right_brow.animate.shift(DOWN * 0.015).rotate(-0.025),
        lag_ratio=0,
    )


def concerned_brows(left_brow, right_brow):
    return AnimationGroup(
        left_brow.animate.rotate(-0.10).shift(DOWN * 0.025),
        right_brow.animate.rotate(0.10).shift(DOWN * 0.025),
        lag_ratio=0,
    )
