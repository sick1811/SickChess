# tests/test_analyse_profonde.py - analyse « maximale » (17/10).
#     python tests/test_analyse_profonde.py      (sans Stockfish : moteur factice)
# Demande de Julien : analyse a la profondeur 30, aussi juste que possible,
# precision comparable a lichess, et Stockfish qui propose les coups aussi bons.

import math
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import chess
import analyse_partie as A

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


class Factice:
    """Repond selon la profondeur : a 30, un autre meilleur coup qu'a 22."""
    def __init__(self):
        self.appels = []

    def analyser_position(self, fen, profondeur, temps, lignes=1):
        self.appels.append((profondeur, lignes))
        plateau = chess.Board(fen)
        coups = [c.uci() for c in list(plateau.legal_moves)[:3]]
        if profondeur >= 30:
            lignes_moteur = [{"coup": coups[-1], "cp": 40, "mat": None,
                              "profondeur": profondeur, "suite": []}]
        else:
            lignes_moteur = [{"coup": u, "cp": 30 - 5 * n, "mat": None,
                              "profondeur": profondeur, "suite": []}
                             for n, u in enumerate(coups[:lignes])]
        return {"coup": lignes_moteur[0]["coup"], "evaluation": lignes_moteur[0]["cp"] / 100.0,
                "mat": None, "profondeur": profondeur, "lignes": lignes_moteur,
                "second_evaluation": (lignes_moteur[1]["cp"] / 100.0 if len(lignes_moteur) > 1 else None),
                "second_mat": None}


print("1. Formule de lichess")
verifier(A.precision_du_coup(0) == 100.0, "aucune perte : 100")
attendu = min(100, 103.1668100711649 * math.exp(-0.04354415386753951 * 10) - 3.166924740191411 + 1)
verifier(abs(A.precision_du_coup(10) - attendu) < 1e-9, "10 points perdus : %.2f" % attendu)
verifier(abs(A.chances_lichess(20.0) - A.chances_lichess(10.0)) < 1e-9,
         "evaluation bornee a 10 pions, comme lichess")
verifier(A.poids_lichess([50, 52, 48, 60, 30, 35]) == [1.0, 2.0, 6.0, 12.0, 2.5],
         "poids de la fenetre glissante")

print("2. Profondeur 30 : trois coups a 22, puis le meilleur a 30")
m = Factice()
a = A.AnalyseurPartie(None, ["e2e4", "e7e5", "g1f3"], None, "maximale", moteur=m)
verifier(a.profondeur == 30 and a.niveau_final == 3, "reglage par defaut : profondeur 30")
verifier(A.PUISSANCE_PAR_DEFAUT == "calcul_maximale",
         "18/10 : le calcul fixe maximal est le reglage par defaut")
a._travailler()
verifier(a.terminee(), "analyse terminee")
verifier((10, 1) in m.appels and (22, 3) in m.appels and (30, 1) in m.appels,
         "survol, trois coups a 22, meilleur coup a 30 : %s" % sorted(set(m.appels)))
verifier(a.lignes[0][0][0] == a.meilleurs[0] and a.lignes[0][0][1] == 0.4,
         "le meilleur coup de la passe profonde passe en tete")
verifier(len(a.meilleurs_coups(0)) >= 1, "meilleurs coups proposes : %s"
         % [c["san"] for c in a.meilleurs_coups(0)])
verifier(a.profondeur_atteinte() == 30, "profondeur atteinte : %d" % a.profondeur_atteinte())

print("3. Les pastilles attendent la passe profonde")
b = A.AnalyseurPartie(None, ["e2e4", "e7e5"], None, "maximale", moteur=Factice())
b._analyser(b._moteur_fourni, 0, 1)
b._analyser(b._moteur_fourni, 1, 1)
b._analyser(b._moteur_fourni, 0, 2)
b._analyser(b._moteur_fourni, 1, 2)
verifier(not b.detail(0)["pret"], "a 22 seulement : pas encore de pastille")
b._analyser(b._moteur_fourni, 0, 3)
b._analyser(b._moteur_fourni, 1, 3)
verifier(b.detail(0)["pret"], "a 30 : pastille posee (%s)" % b.detail(0)["note"])

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
