"""Animação suave do braço ESQUERDO, sem conflitar com bengala, microfone,
copo ou ações existentes na mão direita. Aplica deltas reversíveis a cada frame.
"""
from manim import VMobject
import numpy as np
import direcao_previsao as D


def anexar(scene, personagem, grupo, plano, escala=1.0):
    braco = personagem.get("bracoE")
    mao = personagem.get("maoE")
    if braco is None or mao is None or not plano:
        return
    state = {"dx": 0., "dy": 0.}
    relogio = VMobject()
    def mover(_obj, _dt):
        t = scene.renderer.time
        item = next((p for p in plano if p["inicio"] <= t < p["fim"]), None)
        dx, dy = (D.deslocamento(item["gesto"],t,item["inicio"],item["fim"],item["energia"])
                  if item else (0., 0.))
        delta = np.array([(dx-state["dx"])*escala,(dy-state["dy"])*escala,0.])
        if abs(delta[0])+abs(delta[1]) > 1.e-7:
            # Só a extremidade livre do braço se move; o ombro segue G.
            braco.put_start_and_end_on(braco.get_start(), braco.get_end()+delta)
            mao.shift(delta)
        state["dx"],state["dy"] = dx,dy
    relogio.add_updater(mover)
    scene.add(relogio)
