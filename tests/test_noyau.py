# tests/test_noyau.py - verifie le noyau sans ouvrir de fenetre.
#     python tests/test_noyau.py
# Teste : chargement des 19 sons, alerte des 30 secondes (son + clignotement),
# fin de partie a 00:00, et une partie a deux jusqu'au mat.

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import pygame

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
ecran = pygame.display.set_mode((1024, 640))

from board import ChessBoard
from ecran_fin import EcranFin

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


class Horloge:
    """Remplace pygame.time.get_ticks pour avancer le temps a volonte."""
    def __init__(self):
        self.ms = 1000

    def __call__(self):
        return self.ms


def nouvelle_partie(minutes=1):
    plateau = ChessBoard(ecran, {"minutes": minutes, "pendule_active": True,
                                 "increment": 0})
    plateau.timer.set_time(minutes, 0, True)
    plateau.end_screen = EcranFin(plateau, "hotseat")
    return plateau


print("1. Sons")
plateau = nouvelle_partie()
verifier(len(plateau.sounds.sounds) == 19, "19 bruitages charges (%d)" % len(plateau.sounds.sounds))
verifier(set(plateau.sounds.formats.values()) == {".wav"}, "tous en .wav")
joues = []
plateau.sounds.play = lambda nom, _o=plateau.sounds.play: joues.append(nom) or _o(nom)
plateau.timer.sons = plateau.sounds
plateau.make_move(chess.Move.from_uci("e2e4"))
verifier(bool(joues), "un son joue au premier coup (%s)" % joues)

print("2. Pendule : alerte sous 30 secondes")
horloge = Horloge()
pygame.time.get_ticks = horloge
plateau.timer.last_update = horloge.ms
plateau.timer.time_left[chess.BLACK] = 31.0
for _ in range(30):                       # 3 secondes par pas de 100 ms
    horloge.ms += 100
    plateau.update()
verifier(plateau.timer.en_alerte(chess.BLACK), "Noirs en alerte a ~28 s")
verifier("low_time" in joues, "son low_time joue")
couleurs = set()
for pas in range(4):
    horloge.ms += 250
    plateau.renderer.draw() if hasattr(plateau, "renderer") else None
    couleurs.add((horloge.ms // 500) % 2)
verifier(len(couleurs) == 2, "le clignotement alterne (periode 500 ms)")

print("3. Pendule : fin de partie a 00:00")
plateau.timer.time_left[chess.BLACK] = 0.5
for _ in range(10):
    horloge.ms += 100
    plateau.update()
verifier(plateau.game_over, "partie terminee au temps")
verifier(plateau.result == "1-0", "les Blancs gagnent au temps (%s)" % plateau.result)
verifier("TEMPS" in (plateau.game_over_reason or "").upper(), "raison : %s" % plateau.game_over_reason)
verifier(plateau.timer.get_time(chess.BLACK) == "0:00.0", "affiche 0:00.0")
verifier(plateau.timer.avec_pendule, "la pendule reste affichee apres la fin")
horloge.ms += 1000
plateau.update()
plateau.draw()
pygame.image.save(ecran, os.path.join(RACINE, "tests", "capture_fin_au_temps.png"))

print("4. Mat du berger")
horloge_mat = Horloge()
pygame.time.get_ticks = horloge_mat
plateau = nouvelle_partie(5)
for uci in ("e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"):
    plateau.make_move(chess.Move.from_uci(uci))
    horloge_mat.ms += 400
    plateau.update()
verifier(plateau.game_over and plateau.result == "1-0", "mat detecte (%s)" % plateau.game_over_reason)
verifier(plateau.end_screen.titre() == "Les Blancs gagnent", "carte de fin : %s" % plateau.end_screen.titre())
plateau.draw()
pygame.image.save(ecran, os.path.join(RACINE, "tests", "capture_mat.png"))

print("5. Menu")
from menu_principal import MainMenu
menu = MainMenu(ecran, "test")
menu.draw()
pygame.image.save(ecran, os.path.join(RACINE, "tests", "capture_menu.png"))

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
