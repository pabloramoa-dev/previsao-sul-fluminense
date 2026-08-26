"""Movimentos de camera discretos para storytelling vertical."""
from manim import *


def slow_push(scene, target, scale=0.94, run_time=3.0):
    frame = scene.camera.frame
    scene.play(frame.animate.scale(scale).move_to(target), run_time=run_time,
               rate_func=smooth)


def reframe(scene, target, width=None, run_time=1.8):
    frame = scene.camera.frame
    anim = frame.animate.move_to(target)
    if width is not None:
        anim = anim.set(width=width)
    scene.play(anim, run_time=run_time, rate_func=smooth)


def micro_drift(frame, amplitude=0.035, period=6.0):
    """Deriva quase imperceptivel; evita quadro morto sem parecer camera nervosa."""
    import numpy as np
    state = {"t": 0.0, "last": 0.0}
    def upd(mob, dt):
        state["t"] += dt
        now = amplitude * np.sin(TAU * state["t"] / period)
        mob.shift(RIGHT * (now - state["last"]))
        state["last"] = now
    frame.add_updater(upd)
    return upd
