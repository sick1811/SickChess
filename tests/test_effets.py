# tests/test_effets.py - finitions visuelles (17/10, travail p13) : onde de
# prise, halo et confettis au mat, fondu d'arrivee.

import os
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import pygame

pygame.init()
ecran = pygame.display.set_mode((1024, 640))

import effets
from board import ChessBoard

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


b = ChessBoard(ecran, {"pendule_active": False})
for uci in ("e2e4", "d7d5", "e4d5"):
    b.make_move(chess.Move.from_uci(uci))
verifier(any(e["type"] == "onde" for e in b.effets.actifs()), "une prise lance une onde")
b.draw()
time.sleep(effets.DUREE_ONDE + 0.05)
verifier(not b.effets.actifs(), "l'onde s'eteint toute seule")

b = ChessBoard(ecran, {"pendule_active": False})
b.hotseat_mode = True
for uci in ("e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"):
    b.make_move(chess.Move.from_uci(uci))
b.terminer_partie("ÉCHEC ET MAT !")
mats = [e for e in b.effets.actifs() if e["type"] == "mat"]
verifier(mats and mats[0]["case"] == chess.E8, "au mat : halo sur le roi mate (e8)")
verifier(mats and len(mats[0]["particules"]) > 0, "a deux : confettis")
time.sleep(0.4)
b.draw()
pygame.image.save(ecran, "tests/capture_mat_confettis.png")

b2 = ChessBoard(ecran, {"pendule_active": False})
b2.couleur_joueur = chess.BLACK                 # tu joues les Noirs et tu te fais mater
for uci in ("e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"):
    b2.make_move(chess.Move.from_uci(uci))
b2.terminer_partie("ÉCHEC ET MAT !")
m2 = [e for e in b2.effets.actifs() if e["type"] == "mat"][0]
verifier(not m2["particules"], "tu perds : pas de confettis, seulement le halo")

effets.FONDU_ACTIF = True
s = pygame.Surface((100, 100))
s.fill((200, 200, 200))
effets.fondu(s, "essai", (0, 0, 0))
verifier(s.get_at((50, 50))[0] < 60, "fondu : l'ecran arrive dans le noir")
time.sleep(effets.DUREE_FONDU + 0.02)
s.fill((200, 200, 200))
effets.fondu(s, "essai", (0, 0, 0))
verifier(s.get_at((50, 50))[0] == 200, "puis plus rien")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
