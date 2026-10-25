# tests/test_moteur_decale.py - 25/10 : une recherche abandonnee ne decale plus Stockfish.
#     python tests/test_moteur_decale.py      (Stockfish necessaire)
#
# Le defaut (vu sur le PC de Julien, test_precision_moteur rouge une fois sur deux) :
# quand Stockfish tardait (PC charge, analyses en priorite basse), le jeu
# abandonnait la recherche, envoyait « stop »... sans lire le « bestmove » que
# Stockfish renvoie quand meme. La recherche SUIVANTE lisait ce vieux bestmove
# et le prenait pour le sien : chaque position recevait ensuite le resultat de
# la precedente (pastilles fausses ou absentes dans la revue, coup de
# l'ordinateur pour une autre position).
#
# Ici on simule le retard avec une fausse horloge : la premiere recherche
# « depasse le temps » ; la suivante, sur un mat en 1, doit donner LE coup du mat.

import json
import os
import sys
import time as vrai_time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


sf = os.environ.get("SICKCHESS_STOCKFISH")
if not sf:
    try:
        with open("config.json", encoding="utf-8") as f:
            sf = json.load(f).get("stockfish_path", "moteur/stockfish.exe")
    except (OSError, ValueError):
        sf = os.path.join("moteur", "stockfish.exe")

import engine
try:
    moteur = engine.StockfishEngine(sf)
    if not moteur.est_vivant():
        raise RuntimeError("mort")
except Exception:
    print("Pas de Stockfish utilisable : test saute.")
    sys.exit(0)


class Horloge:
    """time.time() qui saute de 1000 s quand on le demande (Stockfish « en retard »)."""
    def __init__(self):
        self.avance = 0.0

    def time(self):
        return vrai_time.time() + self.avance

    def sleep(self, s):
        vrai_time.sleep(s)


horloge = Horloge()
engine.time = horloge
vraie_lecture = moteur._lire_ligne


def en_retard():
    """La prochaine ligne lue arrive « 1000 s trop tard » : la recherche est abandonnee."""
    def lire():
        ligne = vraie_lecture()
        horloge.avance += 1000.0
        moteur._lire_ligne = vraie_lecture
        return ligne
    moteur._lire_ligne = lire


DEPART = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
MAT_EN_1 = "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1"        # Ra8#

print("1. Analyse (revue) : recherche abandonnee puis mat en 1")
moteur.configurer_pour_analyse(threads=1, hash_mb=16)
en_retard()
verifier(moteur.analyser_position(DEPART, 0, 3000) is None, "la recherche en retard est abandonnee")
r = moteur.analyser_position(MAT_EN_1, 0, 300)
verifier(r is not None and r.get("coup") == "a1a8" and r.get("mat") == 1,
         "la recherche suivante donne SON resultat : Ra8# mat en 1 (%s)" % r)
r = moteur.analyser_position(DEPART, 0, 200)
verifier(r is not None and r.get("coup") not in (None, "a1a8") and r.get("mat") is None,
         "et la suivante aussi (position de depart : %s)" % r)

print("2. Coup de l'ordinateur : recherche abandonnee puis mat en 1")
en_retard()
verifier(moteur.get_best_move(DEPART, 3000) is None, "le coup en retard est abandonne")
verifier(moteur.get_best_move(MAT_EN_1, 300) == "a1a8", "le coup suivant est le bon : Ra8#")

print("3. Le moteur reste utilisable")
verifier(moteur.est_vivant(), "Stockfish toujours vivant")
moteur.quit()
engine.time = vrai_time

print("4. Revue : le Stockfish d'analyse est ferme en pleine analyse")
# Avant : les positions analysees par un moteur ferme etaient notees « faites »
# sans evaluation (pastilles absentes). Maintenant un moteur neuf les refait.
import moteurs
from analyse_partie import AnalyseurPartie
coups = ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "f3g5", "d7d5"]
a = AnalyseurPartie(DEPART, coups, sf, "calcul_rapide")
a.demarrer()
debut = vrai_time.time()
while not moteurs.roles_vivants() and vrai_time.time() < debut + 20:
    vrai_time.sleep(0.05)
vrai_time.sleep(0.5)
fermes = [role for role in moteurs.roles_vivants() if role.startswith("analyse")]
for role in fermes:
    moteurs.liberer(role)
while not a.terminee() and not a.erreur and vrai_time.time() < debut + 120:
    vrai_time.sleep(0.1)
notes = [a.detail(i).get("note") for i in range(len(coups))]
verifier(fermes and a.terminee() and None not in notes,
         "analyse finie avec toutes ses pastilles malgre %d moteur(s) ferme(s) : %s"
         % (len(fermes), notes))
verifier(all(a.evaluations[k] is not None for k in range(len(coups) + 1)),
         "chaque position a son evaluation")
a.arreter()

print("5. Revue juste apres une revue sans calcul (mat, pat) : jamais bloquee")
# 25/10 : l'analyse d'un mat finit en 0,1 s ; la suivante demarrait pendant que
# ses moteurs se reglaient. Le reglage attendait « readyok » pendant qu'une
# recherche lisait le meme Stockfish : les deux attendaient pour toujours
# (1 fois sur 2 sur le PC de Julien, « dame_en_prise » sans pastille).
sys.path.insert(0, os.path.join(RACINE, "outils"))
import precision
banque = {p["id"]: p for p in precision.charger()}
bloquees = 0
for _ in range(3):
    for nom in ("pat_rate", "mat_en_un", "dame_en_prise"):
        p = banque[nom]
        a = AnalyseurPartie(p["fen"], p["coups"], sf, "calcul_rapide")
        a.demarrer()
        fin = vrai_time.time() + 40
        while not a.terminee() and not a.erreur and vrai_time.time() < fin:
            vrai_time.sleep(0.05)
        if not a.terminee() or None in [a.detail(i).get("note") for i in range(len(p["attendus"]))]:
            bloquees += 1
        a.arreter()
verifier(bloquees == 0, "9 revues a la suite, aucune bloquee ni sans pastille (%d)" % bloquees)
moteurs.tout_fermer()

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
