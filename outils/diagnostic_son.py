"""Diagnostic du son de SickChess.

Lance par TESTER_LE_SON.bat. Joue trois sons a la suite et ecrit ce qu'il a vu
dans diagnostic_son.txt, a la racine du jeu (Claude peut le lire ensuite).
"""
import os
import sys
import time
import traceback

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lignes = []


def note(texte):
    print(texte)
    lignes.append(str(texte))


try:
    import pygame
    note("Python %s - pygame %s - SDL %s" % (sys.version.split()[0], pygame.version.ver,
                                             ".".join(map(str, pygame.get_sdl_version()))))
    note("SDL_AUDIODRIVER = %r" % os.environ.get("SDL_AUDIODRIVER"))
    pygame.mixer.pre_init(44100, -16, 2, 1024)
    pygame.init()
    note("Lecteur audio apres pygame.init() : %s" % (pygame.mixer.get_init(),))
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init()
            note("Lecteur audio apres mixer.init() : %s" % (pygame.mixer.get_init(),))
        except Exception as e:
            note("mixer.init() impossible : %s" % e)
    try:
        from pygame._sdl2 import audio as sdl_audio
        note("Sorties audio vues par SDL : %s" % sdl_audio.get_audio_device_names(False))
    except Exception as e:
        note("Liste des sorties indisponible : %s" % e)
    try:
        note("Pilote audio SDL : %s" % pygame.mixer.get_driver())
    except Exception:
        pass
    for nom in ("game_start", "move", "capture"):
        chemin = os.path.join(RACINE, "sounds", nom + ".wav")
        try:
            son = pygame.mixer.Sound(chemin)
            son.set_volume(1.0)
            canal = son.play()
            note("Son %s : duree %.2f s, canal %s" % (nom, son.get_length(), canal))
            time.sleep(max(0.8, son.get_length() + 0.3))
        except Exception as e:
            note("Son %s : ERREUR %s" % (nom, e))
    pygame.quit()
except Exception:
    note("ERREUR GENERALE :\n" + traceback.format_exc())

with open(os.path.join(RACINE, "diagnostic_son.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lignes) + "\n")
print()
print("Rapport ecrit dans diagnostic_son.txt")
