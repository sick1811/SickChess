# tests/test_cache_analyse.py - une analyse enregistree n'est jamais abimee
# (bug du 17/10 : « Mes erreurs » la reecrivait en profondeur 16, et la revue
# suivante refaisait toute l'analyse). Sans moteur.

import json
import os
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import chess

from analyse_partie import AnalyseurPartie

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


coups = ["e2e4", "e7e5", "g1f3", "b8c6"]
n = len(coups) + 1
cache = os.path.join(tempfile.mkdtemp(), "partie.analyse.json")
# 17/10 : format 2 (les trois meilleurs coups et la profondeur atteinte).
d = {"fen": chess.STARTING_FEN, "coups": coups, "profondeur": 22, "version": 2,
     "evaluations": [0.3, 0.3, 0.3, 0.3, 0.3], "mats": [None] * n,
     "meilleurs": ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
     "premiers": [0.3] * n, "seconds": [0.2] * n,
     "lignes": [[[m, 0.3, None, []]] for m in ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"]],
     "profondeurs": [22] * n}
with open(cache, "w", encoding="utf-8") as f:
    json.dump(d, f)
avant = open(cache, encoding="utf-8").read()
mtime = os.path.getmtime(cache)

a = AnalyseurPartie(None, coups, None, "rapide", fichier_cache=cache)
verifier(a.terminee(), "analyse de profondeur 22 relue par « rapide »")
verifier(open(cache, encoding="utf-8").read() == avant and os.path.getmtime(cache) == mtime,
         "le fichier n'est pas reecrit")
b = AnalyseurPartie(None, coups, None, "normale", fichier_cache=cache)
verifier(b.terminee(), "la revue (normale, profondeur 22) la reprend sans recalcul")
c = AnalyseurPartie(None, coups, None, "forte", fichier_cache=cache)
verifier(not c.terminee(), "« forte » (26) la juge trop faible : normal")
a._ecrire_cache()
verifier(json.load(open(cache))["profondeur"] == 22,
         "meme reecrite, elle garde sa profondeur d'origine")
verifier(a.meilleurs_coups(0) and a.meilleurs_coups(0)[0]["san"] == "e4",
         "les meilleurs coups sont relus avec l'analyse")
ancien = dict(d, version=1)
with open(cache, "w", encoding="utf-8") as f:
    json.dump(ancien, f)
e = AnalyseurPartie(None, coups, None, "normale", fichier_cache=cache)
verifier(not e.terminee(), "une analyse d'avant (format 1) est refaite une fois")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
