# tests/test_mes_erreurs.py - problemes tires de tes propres fautes (17/10).
#     python tests/test_mes_erreurs.py      (Stockfish necessaire)
# Tout se passe dans un dossier temporaire : parties/ et profil intacts.

import io
import json
import os
import sys
import tempfile
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import chess.pgn
import pygame

pygame.init()
ecran = pygame.display.set_mode((1024, 640))

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


sf = os.environ.get("SICKCHESS_STOCKFISH")
if not sf:
    with open("config.json", encoding="utf-8") as f:
        sf = json.load(f).get("stockfish_path", "moteur/stockfish.exe")
try:
    from engine import StockfishEngine
    StockfishEngine(sf).quit()
except Exception:
    print("Pas de Stockfish utilisable : test saute.")
    sys.exit(0)

TEMP = tempfile.mkdtemp()
import asset_manager
import historique_parties
asset_manager.dossier_ecriture = lambda: TEMP
historique_parties.dossier_parties = lambda: os.path.join(TEMP, "parties")
os.makedirs(os.path.join(TEMP, "parties"))

print("1. Une partie ou les Noirs (toi) font une gaffe")
COUPS = ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "g8f6", "h5f7"]   # 3...Cf6?? 4.Dxf7#
jeu = chess.pgn.Game()
jeu.headers.update({"White": "Ordinateur", "Black": "Julien", "Result": "1-0",
                    "Date": "2026.10.17", "Joueur": "noir"})
noeud = jeu
for uci in COUPS:
    noeud = noeud.add_variation(chess.Move.from_uci(uci))
chemin = os.path.join(TEMP, "parties", "2026-10-17_10h00_Ordinateur-Julien.pgn")
with open(chemin, "w", encoding="utf-8") as f:
    f.write(str(jeu))
partie = historique_parties.lister()[0]
verifier(partie["camp"] == "noir", "la partie est lue (camp %s)" % partie["camp"])

import mes_erreurs
verifier(mes_erreurs.problemes_d_une_partie(partie) == [],
         "sans analyse enregistree : pas encore de probleme")

from analyse_partie import AnalyseurPartie
a = AnalyseurPartie(None, COUPS, sf, "rapide",
                    fichier_cache=os.path.splitext(chemin)[0] + ".analyse.json")
a.demarrer()
fin = time.time() + 120
while a.en_cours and time.time() < fin:
    time.sleep(0.2)
verifier(a.terminee(), "analyse terminee et enregistree")

problemes = mes_erreurs.problemes_d_une_partie(partie)
verifier(len(problemes) == 1, "une seule faute des Noirs retenue (%d)" % len(problemes))
p = problemes[0]
verifier(p["coups"][0] == "f1c4", "le probleme commence par le coup d'avant (Fc4)")
verifier(p["fen"] == a.fens[4], "position : juste avant Fc4")
verifier(p["source"]["joue"] == "Nf6" and p["source"]["note"] == "gaffe",
         "source : tu as joue Cf6, gaffe")
print("   description :", mes_erreurs.description(p))
verifier("coup 3..." in mes_erreurs.description(p), "description lisible")

print("2. L'ecran des problemes, mode Mes erreurs")
from ecran_problemes import EcranProblemes
e = EcranProblemes(ecran, {"stockfish_path": sf})
e.draw()
verifier(e.nombre_erreurs == 1, "le bouton annonce 1 position")
pygame.image.save(ecran, os.path.join("tests", "capture_mes_erreurs_choix.png"))
e.commencer("erreurs")
verifier(e.puzzle and e.puzzle["id"] == p["id"], "le probleme est tire")
pl = e.plateau
verifier(pl.couleur_joueur == chess.BLACK and pl.flipped, "tu joues les Noirs, plateau retourne")
# l'adversaire joue Fc4
coup = chess.Move.from_uci(e.coup_en_attente)
e.coup_en_attente = None
from board import ChessBoard
ChessBoard.make_move(pl, coup)
e.chrono_debut = pygame.time.get_ticks()
meilleur = chess.Move.from_uci(p["coups"][1])
verifier(e.juger(meilleur), "le coup du moteur (%s) est accepte" % pl.board.san(meilleur))
autres = [m for m in (chess.Move.from_uci("d8e7"), chess.Move.from_uci("g7g6"),
                      chess.Move.from_uci("d8f6")) if m != meilleur and m in pl.board.legal_moves]
verifier(any(e.juger(m) for m in autres),
         "un autre coup qui defend f7 est accepte aussi")
verifier(not e.juger(chess.Move.from_uci("g8f6")), "refaire la gaffe Cf6 est refuse")
verifier(not e.juger(chess.Move.from_uci("a7a6")), "un coup quelconque est refuse")
e.draw()
pygame.image.save(ecran, os.path.join("tests", "capture_mes_erreurs.png"))

print("3. Suivi")
pl.make_move(meilleur)
verifier(e.fini and e.reussi, "probleme reussi")
suivi = mes_erreurs.charger_le_suivi()
verifier(suivi["reussis"].get(p["id"]) == 1, "reussite notee dans mes_erreurs.json")
verifier(not os.path.exists(os.path.join(RACINE, "puzzles_score.json.tmp")),
         "le classement des problemes n'est pas touche")

import moteurs
moteurs.tout_fermer()
print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
