# tests/test_adversaire.py - un adversaire plus humain (17/10, travail p08).
#     python tests/test_adversaire.py
# Le temps de reflexion regarde la position : reprise evidente rapide, pieces
# menacees = plus long, jamais instantane, toujours dans le plafond en bullet.

import os
import random
import statistics
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess

import rythme
from background_ai import BackgroundAI

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


class Pendule:
    def __init__(self, secondes, increment=0):
        self.active = True
        self.s = secondes
        self.increment = increment

    def secondes_restantes(self, blancs):
        return self.s


class Plateau:
    def __init__(self, pendule=None):
        self.timer = pendule


def temps(board, pendule=None, n=300):
    random.seed(7)
    ia = BackgroundAI(Plateau(pendule), None)
    return [ia._tirer_temps_de_reflexion(board) for _ in range(n)]


print("1. Ce qu'un joueur voit")
reprise = chess.Board()
for san in ("e4", "d5", "exd5"):
    reprise.push_san(san)
verifier(rythme.est_une_reprise_evidente(reprise), "1.e4 d5 2.exd5 : reprise evidente pour les Noirs")
calme = chess.Board()
for san in ("e4", "e5", "Nf3"):
    calme.push_san(san)
verifier(not rythme.est_une_reprise_evidente(calme), "1.e4 e5 2.Nf3 : rien a reprendre")
menace = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 4 4")
verifier(rythme.facteur_de_complexite(menace) > rythme.facteur_de_complexite(chess.Board()),
         "pion f7 menace de mat : position plus complexe (%.2f > %.2f)"
         % (rythme.facteur_de_complexite(menace), rythme.facteur_de_complexite(chess.Board())))

print("2. Le temps de reflexion (partie de 10 minutes)")
milieu_calme = chess.Board("r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8")
for _ in range(10):
    milieu_calme.push(chess.Move.null()); milieu_calme.push(chess.Move.null())
milieu_tendu = chess.Board("r2q1rk1/pp2bppp/2n1bn2/3pp3/3PP3/2N1BN2/PP2BPPP/R2Q1RK1 w - - 0 10")
for _ in range(10):
    milieu_tendu.push(chess.Move.null()); milieu_tendu.push(chess.Move.null())
dix = Pendule(600, 0)
t_reprise = statistics.median(temps(reprise, dix))
t_calme = statistics.median(temps(milieu_calme, dix))
t_tendu = statistics.median(temps(milieu_tendu, dix))
print("      medianes : reprise %d ms, calme %d ms, tendu %d ms" % (t_reprise, t_calme, t_tendu))
verifier(t_reprise < t_calme, "la reprise evidente part plus vite qu'un coup calme")
verifier(t_tendu > t_calme, "une position tendue fait reflechir plus longtemps")
tous = temps(milieu_tendu, dix) + temps(reprise, dix) + temps(chess.Board(), dix)
verifier(min(tous) >= 350, "jamais moins de 0,35 s avec plus d'une minute (%d ms)" % min(tous))
verifier(max(tous) <= rythme.BUDGET_PLAFOND_MS, "jamais plus de 8 s")

print("3. Bullet : toujours rapide")
bullet = Pendule(20, 0)
t = temps(milieu_tendu, bullet)
verifier(max(t) <= 1500, "a 20 s de la fin : au plus 1,5 s (%d ms)" % max(t))
force = chess.Board("k7/8/8/8/8/8/1q6/K7 w - - 0 1")
verifier(force.legal_moves.count() == 1, "position test : un seul coup")
verifier(max(temps(force, dix)) <= 600, "un seul coup possible : moins de 0,6 s")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
