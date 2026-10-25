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
# 18/10 (16) : hors theorie (les positions de theorie ne sont plus creusees).
a = A.AnalyseurPartie(None, ["h2h3", "a7a6", "h1h2"], None, "maximale", moteur=m)
verifier(a.profondeur == 30 and a.niveau_final == 3, "reglage par defaut : profondeur 30")
verifier(A.PUISSANCE_PAR_DEFAUT == "calcul_forte",
         "18/10 (14) : le calcul fixe fort est le reglage par defaut")
a._travailler()
verifier(a.terminee(), "analyse terminee")
verifier((10, 1) in m.appels and (22, 3) in m.appels and (30, 1) in m.appels,
         "survol, trois coups a 22, meilleur coup a 30 : %s" % sorted(set(m.appels)))
verifier(a.lignes[1][0][0] == a.meilleurs[1] and a.lignes[1][0][1] == -0.4,
         "le meilleur coup de la passe profonde passe en tete")
verifier(len(a.meilleurs_coups(1)) >= 1, "meilleurs coups proposes : %s"
         % [c["san"] for c in a.meilleurs_coups(1)])
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

print("4. Un saut au coup p ne fait pas verifier de position en plus (25/10, t71)")


class Calme:
    """Partie calme (meme evaluation partout) : note chaque passe profonde
    (25 millions de noeuds) et si les deux voisines avaient leur passe des
    trois coups a ce moment-la."""
    def __init__(self):
        self.a = None
        self.profondes = []
        self.trop_tot = []

    def analyser_position(self, fen, profondeur, temps, lignes=1, noeuds=0):
        a = self.a
        k = a.fens.index(fen)
        if noeuds == a.noeuds:
            self.profondes.append(k)
            if any(0 <= j < len(a.fens) and a.niveau[j] < 2 and not a.finie[j]
                   for j in (k - 1, k + 1)):
                self.trop_tot.append(k)
        plateau = chess.Board(fen)
        signe = 1 if plateau.turn == chess.WHITE else -1    # +0,2 pour les Blancs
        coups = [c.uci() for c in list(plateau.legal_moves)[:3]]
        lignes_moteur = [{"coup": u, "cp": signe * 20 - 2 * n, "mat": None,
                          "profondeur": 22, "suite": []}
                         for n, u in enumerate(coups[:lignes])]
        return {"coup": coups[0], "evaluation": signe * 0.2, "mat": None,
                "profondeur": 22, "lignes": lignes_moteur, "second_mat": None,
                "second_evaluation": signe * 0.2 - 0.02 if lignes > 1 else None}


# Coups tranquilles hors theorie, sans prise ni position repetee.
PARTIE_CALME = ["h2h3", "h7h6", "a2a3", "a7a6", "g2g3", "g7g6", "b2b3", "b7b6",
                "f1g2", "f8g7", "c1b2", "c8b7", "g1f3", "g8f6", "b1c3", "b8c6",
                "e1g1", "e8g8", "d2d3", "d7d6", "e2e3", "e7e6", "d1e2", "d8e7",
                "f1e1", "f8e8", "a1d1", "a8d8"]


def revue_calme(saut=None):
    m = Calme()
    a = A.AnalyseurPartie(None, PARTIE_CALME, None, "calcul_forte", moteur=m)
    m.a = a
    verifier(len(set(a.fens)) == len(a.fens), "partie calme : %d positions toutes "
             "differentes" % len(a.fens))
    if saut is not None:
        a.prioriser(saut)
    a._travailler()
    verifier(a.terminee(), "revue terminee (saut : %s)" % saut)
    return m, a


m_sans, a_sans = revue_calme()
m_saut, a_saut = revue_calme(saut=15)
verifier(not m_saut.trop_tot, "apres un saut au coup 15 : aucune position verifiee "
         "avant la passe des 3 coups de ses voisines (%s)" % m_saut.trop_tot)
verifier(sorted(m_saut.profondes) == sorted(m_sans.profondes),
         "meme nombre de positions verifiees qu'une revue sans saut (%d / %d)"
         % (len(m_saut.profondes), len(m_sans.profondes)))
verifier([a_saut.detail(i)["note"] for i in range(len(PARTIE_CALME))]
         == [a_sans.detail(i)["note"] for i in range(len(PARTIE_CALME))],
         "memes pastilles avec ou sans saut")

print("5. Un moteur de renfort attend la voisine prise par un autre moteur (25/10)")
import threading
import time
m5 = Calme()
a5 = A.AnalyseurPartie(None, PARTIE_CALME[:6], None, "calcul_forte", moteur=m5)
m5.a = a5
# Tout est fait sauf la position 3 (passe des 3 coups faite, a verifier) et
# sa voisine 4, que « l'autre moteur » est en train de passer aux 3 coups.
a5.niveau = [a5.niveau_final] * len(a5.fens)
a5.niveau[3], a5.niveau[4] = 2, 1
a5._en_travail.add(4)
a5._ouvriers = 2
renfort = threading.Thread(target=a5._travailler, args=(1,), daemon=True)
renfort.start()
time.sleep(0.4)
verifier(renfort.is_alive(), "le renfort attend au lieu de quitter la revue")
with a5._verrou_choix:                 # l'autre moteur a fini la position 4
    a5.niveau[4] = 2
    a5._en_travail.discard(4)
renfort.join(5)
verifier(not renfort.is_alive() and a5.niveau[3] == a5.niveau_final,
         "puis il fait la position 3 et s'arrete (niveau %d)" % a5.niveau[3])
a5._stop = True

print("6. Analyse en direct : coup ajoute a moitie (25/10)")
a6 = A.AnalyseurPartie(None, ["h2h3", "h7h6"], None, "calcul_forte", moteur=Calme(),
                       suivi=True)
a6.niveau = [3, 3, 2]
a6.niveau.append(0)                    # ajouter_coups : la case niveau d'abord
try:
    choix6 = a6._prochaine()
    a6.finie.append(False)
    choix6 = a6._prochaine()
except IndexError as e:
    choix6 = "plante : %s" % e
verifier(choix6 == (2, 3), "la position pas encore construite est ignoree (%s)" % (choix6,))

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
