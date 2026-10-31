# musique.py - SickChess 17/10 (travail p14, demande de Julien) : une musique
# d'ambiance dans le menu, les problemes et l'entrainement. Jamais pendant une
# partie. Options -> Son : Musique Oui / Non et son volume.
# 31/10 : nouvelle piste choisie par Julien parmi 5 essais : « Zugzwang »
# (music/zugzwang.ogg, 85 s en boucle, synthetisee par outils/musique/pistes.py,
# aucun droit a payer). L'ancienne music/calme.wav n'est plus utilisee par le jeu.

import os

import pygame

FICHIER = os.path.join("music", "zugzwang.ogg")
_etat = {"joue": False}


def _chemin():
    for base in (os.getcwd(), os.path.dirname(os.path.dirname(os.path.abspath(__file__)))):
        chemin = os.path.join(base, FICHIER)
        if os.path.exists(chemin):
            return chemin
    return None


def jouer(config):
    """Lance la musique (ou regle son volume) selon config.json."""
    config = config or {}
    if not config.get("musique", True) or float(config.get("volume_musique", 0.3)) <= 0:
        arreter(0)
        return False
    if not pygame.mixer.get_init():
        return False
    volume = max(0.0, min(1.0, float(config.get("volume_musique", 0.3))))
    try:
        if not _etat["joue"] or not pygame.mixer.music.get_busy():
            chemin = _chemin()
            if chemin is None:
                return False
            pygame.mixer.music.load(chemin)
            pygame.mixer.music.play(-1, fade_ms=1500)
            _etat["joue"] = True
        pygame.mixer.music.set_volume(volume * 0.6)
        return True
    except Exception as e:
        print("[MUSIQUE] %s" % e)
        return False


def arreter(fondu_ms=800):
    if not _etat["joue"]:
        return
    _etat["joue"] = False
    try:
        if fondu_ms:
            pygame.mixer.music.fadeout(int(fondu_ms))
        else:
            pygame.mixer.music.stop()
    except Exception:
        pass


def en_cours():
    return _etat["joue"]
