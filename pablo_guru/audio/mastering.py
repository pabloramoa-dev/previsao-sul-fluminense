"""Pos-processamento de dialogo sem alterar artificialmente o ritmo da fala."""
from pydub import AudioSegment, effects


def master_dialogue(src, dst, headroom_db=1.5):
    audio = AudioSegment.from_file(src)
    audio = effects.normalize(audio, headroom=headroom_db)
    audio.export(dst, format="wav")
    return dst


def mix_ambience(dialogue_path, ambience_path, dst, ambience_gain_db=-24):
    voice = AudioSegment.from_file(dialogue_path)
    amb = AudioSegment.from_file(ambience_path) + ambience_gain_db
    if len(amb) < len(voice):
        times = len(voice) // max(1, len(amb)) + 1
        amb = amb * times
    amb = amb[:len(voice)]
    voice.overlay(amb).export(dst, format="wav")
    return dst
