# tests/test_precision.py - la banque de positions (24/10, travail p30), partie rapide.
#     python tests/test_precision.py
# Sans Stockfish : la banque est bien formee, et les defauts qu'elle a trouves
# restent corriges. La verification complete (avec Stockfish) :
# tests/test_precision_moteur.py et la section « precision » du banc d'essai.

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
sys.path.insert(0, os.path.join(RACINE, "outils"))

import chess

import annotations
import precision
from analyse_partie import AnalyseurPartie

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


print("1. La banque est bien formee")
positions = precision.charger()
verifier(50 <= len(positions) <= 100, "%d positions (50 a 100)" % len(positions))
ids = [p["id"] for p in positions]
verifier(len(ids) == len(set(ids)), "identifiants uniques")
for p in positions:
    plateau = chess.Board(p["fen"])
    ok = plateau.is_valid() and len(p["coups"]) == len(p["attendus"]) and p["pourquoi"]
    for u in p["coups"]:
        coup = chess.Move.from_uci(u)
        ok = ok and coup in plateau.legal_moves
        if not ok:
            break
        plateau.push(coup)
    ok = ok and all(set(a) <= set(annotations.ORDRE) for a in p["attendus"])
    if not ok:
        verifier(False, "position %s : coups legaux, pastilles connues" % p["id"])
verifier(not echecs, "toutes les positions sont legales, avec une explication")
verifier(any(p["id"] == "mat_etouffe" for p in positions)
         and sum(1 for p in positions if "sacrifice" in p.get("themes", [])) >= 15,
         "des sacrifices corrects (au moins 15) et le mat etouffe")

print("2. Defaut trouve par la banque : une gaffe notee « Theorique »")
# Une partie qui ne part PAS de la position initiale (partie importee avec une
# position de depart, Mes erreurs, analyse libre) : son 1er coup « e3 » n'est pas
# le 1.e3 d'une ouverture. Avant le 24/10, le livre d'ouvertures le reconnaissait.
milieu = AnalyseurPartie("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
                         ["d2d3"])
verifier(not milieu.coup_de_livre(0), "partie partie d'une autre position : 1er coup pas « theorique »")
depart = AnalyseurPartie(None, ["e2e4", "e7e5", "g1f3"])
verifier(depart.coup_de_livre(0) and depart.coup_de_livre(2),
         "partie depuis la position initiale : 1.e4 e5 2.Cf3 restent « theoriques »")
verifier(annotations.classer(30.0, theorique=True, chances_avant=50, chances_apres=20) == "gaffe",
         "un coup du livre qui perd 30 points de chances reste une gaffe")
verifier(annotations.classer(1.0, theorique=True, chances_avant=50, chances_apres=49) == "theorique",
         "un coup du livre qui ne perd rien reste « theorique »")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
