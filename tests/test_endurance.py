# tests/test_endurance.py - le jugement du test d'endurance (24/10, travail p28).
#     python tests/test_endurance.py
# Sans lancer le robot (2 heures) : des mesures inventees, et ce que le robot doit en
# conclure (fuite, Stockfish qui s'accumulent, ralentissement, plantage). Le robot
# lui-meme : python outils/endurance.py (section « endurance » du banc d'essai).

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "outils"))

import endurance

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def mesures(tours=8, minutes_par_tour=15.0, memoire=lambda t: 150.0, stockfish=lambda t: 2,
            image=lambda t: 2.0):
    """Une serie de mesures : menu, partie, revue... a chaque tour."""
    sortie = []
    for tour in range(1, tours + 1):
        for k, scenario in enumerate(("menu", "partie", "problemes", "analyse_libre")):
            t = (tour - 1) * minutes_par_tour + k * minutes_par_tour / 4
            sortie.append({"t_min": t, "scenario": scenario, "tour": tour,
                           "memoire_jeu_mo": memoire(t) + (40 if scenario == "partie" else 0),
                           "stockfish": stockfish(t), "memoire_stockfish_mo": 500.0,
                           "fils": 2, "objets_python": 1000, "image_ms": image(t)})
    return sortie


print("1. Un jeu sain")
j = endurance.juger(mesures(), [], [], 120)
verifier(j["statut"] == "vert" and abs(j["fuite_mo_par_heure"]) < 1, "tout vert : %s" % j["resume"])
# Le premier tour charge tout (memoire qui monte) : ce n'est pas une fuite.
j = endurance.juger(mesures(memoire=lambda t: 80.0 if t < 15 else 160.0), [], [], 120)
verifier(j["statut"] == "vert", "la memoire qui monte au 1er tour n'est pas une fuite (%+.0f Mo/h)"
         % j["fuite_mo_par_heure"])

print("2. Une fuite de memoire")
j = endurance.juger(mesures(memoire=lambda t: 150.0 + t), [], [], 120)       # +60 Mo/h
verifier(j["statut"] == "orange" and 50 < j["fuite_mo_par_heure"] < 70,
         "+60 Mo/h : orange (%+.0f Mo/h)" % j["fuite_mo_par_heure"])
j = endurance.juger(mesures(memoire=lambda t: 150.0 + 4 * t), [], [], 120)   # +240 Mo/h
verifier(j["statut"] == "rouge" and any("mémoire" in c["titre"] for c in j["constats"]),
         "+240 Mo/h : rouge, « La mémoire du jeu monte »")

print("3. Des Stockfish qui restent ouverts")
j = endurance.juger(mesures(stockfish=lambda t: 2 + int(t // 15)), [], [], 120)
verifier(j["statut"] == "rouge" and any("Stockfish" in c["titre"] for c in j["constats"]),
         "un Stockfish de plus a chaque tour : rouge")

print("4. Un jeu qui ralentit")
j = endurance.juger(mesures(image=lambda t: 2.0 + t / 20.0), [], [], 120)
verifier(j["statut"] in ("orange", "rouge") and any("ralentit" in c["titre"] for c in j["constats"]),
         "images de plus en plus lentes : %s (x%.1f)" % (j["statut"], max(j["lenteurs"].values())))

print("5. Plantages")
j = endurance.juger(mesures(), [{"t_min": 12.0, "scenario": "revue", "erreur": "KeyError: 'x'",
                                 "trace": "Traceback ..."}], [], 120)
verifier(j["statut"] == "rouge" and j["plantages"] == 1, "un plantage dans un scenario : rouge")
j = endurance.juger(mesures(), [], ["10:02:03"], 120)
verifier(j["statut"] == "rouge", "un « Traceback » dans le journal : rouge")

print("6. Trop court")
j = endurance.juger(mesures(tours=2), [], [], 5)
verifier(any("Trop court" in c["titre"] for c in j["constats"]), "moins de 4 tours : « trop court pour juger »")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
