"""Rig 2D articulado do Pablo Guru V2.

Braco, antebraco e mao sao objetos independentes. Isso evita o efeito de
"braco de borracha" e permite gestos por articulacao sem deformar o tronco.
"""
from manim import *

INK = "#17191f"
SKIN = "#d7a27d"


def limb_segment(a, b, width=18, color=SKIN):
    return Line(a, b, stroke_color=color, stroke_width=width).set_stroke(cap_style=CapStyleType.ROUND)


def articulated_arm(shoulder, elbow, wrist, hand_radius=0.12):
    upper = limb_segment(shoulder, elbow)
    fore = limb_segment(elbow, wrist)
    hand = Circle(radius=hand_radius, fill_color=SKIN, fill_opacity=1,
                  stroke_color=INK, stroke_width=4).move_to(wrist)
    return {"upper": upper, "fore": fore, "hand": hand,
            "group": VGroup(upper, fore, hand)}


def attach_arm_updater(arm, shoulder_fn, elbow_fn, wrist_fn):
    """Reconstroi segmentos a cada frame mantendo juntas coerentes."""
    def update(_mob, _dt):
        s, e, w = shoulder_fn(), elbow_fn(), wrist_fn()
        arm["upper"].put_start_and_end_on(s, e)
        arm["fore"].put_start_and_end_on(e, w)
        arm["hand"].move_to(w)
    arm["group"].add_updater(update)
    return update
