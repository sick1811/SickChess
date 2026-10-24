# tests/test_precision_moteur.py - la banque de positions avec le vrai Stockfish
# (24/10, travail p30).
#     python tests/test_precision_moteur.py      (Stockfish necessaire)
# Chaque petite partie de tests/positions_revue.json passe par l'analyse de la revue ;
# chaque coup doit recevoir une pastille acceptee (sacrifice correct = bonne
# pastille, gaffe nette = Erreur / Manque / Gaffe). Ici : puissance Rapide et un
# echantillon fixe (les positions faites a la main + 1 probleme sur 4) pour que la
# suite de tests reste courte. Toute la banque, en Forte : banc d'essai, section
# « precision » (ou SICKCHESS_PRECISION_COMPLETE=1).

import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
sys.path.insert(0, os.path.join(RACINE, "outils"))

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
try:
    from engine import StockfishEngine
    StockfishEngine(sf).quit()
except Exception:
    print("Pas de Stockfish utilisable : test saute.")
    sys.exit(0)

import precision

positions = precision.charger()
if not os.environ.get("SICKCHESS_PRECISION_COMPLETE"):
    a_la_main = [p for p in positions if not p["id"].startswith("lichess")]
    lichess = [p for p in positions if p["id"].startswith("lichess")]
    positions = a_la_main + lichess[::4]
print("La banque de positions : %d petites parties (puissance Rapide)" % len(positions))
resultats = precision.verifier(sf, "calcul_rapide", positions)
for r in resultats:
    verifier(r["ok"], "%s, coup %d (%s) : %s" % (r["id"], r["coup"], r["san"], r["note"]))
sacrifices = [r for r in resultats if r["coup"] == 2 and r["id"].startswith("lichess")
              and r["ok"]]
verifier(len(sacrifices) >= len([p for p in positions if p["id"].startswith("lichess")]),
         "%d bons coups de problemes (souvent des sacrifices) bien notes" % len(sacrifices))

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
