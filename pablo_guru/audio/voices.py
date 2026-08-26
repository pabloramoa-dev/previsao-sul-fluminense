"""Perfis de voz do Pablo Guru V2.
Mantem fala deliberadamente mais lenta que o pipeline meteorologico.
"""
VOICE_PROFILES = {
    "pablo": {
        "voice": "pm_santa",
        "speed": 0.84,
        "pause_sentence": 0.34,
        "pause_comma": 0.16,
        "role": "grave_calmo",
    },
    "perguntadora": {
        "voice": "pf_dora",
        "speed": 0.90,
        "pause_sentence": 0.28,
        "pause_comma": 0.13,
        "role": "suave_natural",
    },
}


def profile(name):
    if name not in VOICE_PROFILES:
        raise KeyError(f"perfil de voz desconhecido: {name}")
    return dict(VOICE_PROFILES[name])
