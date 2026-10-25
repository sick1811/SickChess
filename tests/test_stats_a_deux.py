# tests/test_stats_a_deux.py - une partie a deux sur ce PC ne compte pas dans
# les statistiques (retour t56 de Cowork, 25/10).
#     python tests/test_stats_a_deux.py
# Vraies parties jouees sur un plateau (comme le jeu), enregistrees dans un
# dossier temporaire, puis statistiques.calculer() comme l'ecran Statistiques.
# Aucun moteur.

import os
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import pygame

pygame.init()
ecran = pygame.display.set_mode((1024, 640))

import asset_manager
TEMP = tempfile.mkdtemp(prefix="sickchess_stats_a_deux_")
asset_manager.dossier_ecriture = lambda: TEMP

import enregistrement
import historique_parties
import sauvegarde
import statistiques
from board import ChessBoard
from ecran_fin import EcranFin
from mode_hotseat import ModeHotseat

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def jouer(plateau, coups):
    for uci in coups:
        plateau.make_move(chess.Move.from_uci(uci))
        plateau.update()


def plateau_a_deux():
    p = ChessBoard(ecran, {"pendule_active": False})
    p.end_screen = EcranFin(p, "hotseat")
    ModeHotseat(p, False)
    return p


BERGER = ["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"]   # ouverture du fou
LEGAL = ["f2f3", "e7e5", "g2g4", "d8h4"]                              # ouverture Barnes
ANGLAISE = ["c2c4", "e7e5", "b1c3", "g8f6", "g2g4", "f8c5", "g4g5", "f6g4",
            "e2e3", "g4f2"]                                           # partie anglaise

print("1. Une partie contre l'ordinateur (temoin) -> comptee")
p = ChessBoard(ecran, {"elo": 1400, "pendule_active": False})
p.end_screen = EcranFin(p, "stockfish")
p.ia_joue_blancs = False
jouer(p, BERGER)
infos = enregistrement.enregistrer_la_partie(p, "stockfish")
verifier(infos and os.path.exists(infos["pgn"]), "PGN de la partie contre l'ordinateur")

print("2. Une vraie partie a deux, jusqu'au mat")
p2 = plateau_a_deux()
jouer(p2, LEGAL)
verifier(p2.game_over and p2.result == "0-1", "mat du lion, 0-1")
infos2 = enregistrement.enregistrer_la_partie(p2, "hotseat")
verifier(infos2 and os.path.exists(infos2["pgn"]), "PGN de la partie a deux ecrit")
e = historique_parties.lire_entetes(infos2["pgn"])
verifier("Joueur" not in e and e.get("Mode") == "à deux",
         "partie a deux : pas de camp du joueur (Mode %s)" % e.get("Mode"))

print("3. Une partie a deux interrompue, reprise depuis le menu, puis finie")
p3 = plateau_a_deux()
jouer(p3, ANGLAISE[:4])
verifier(sauvegarde.enregistrer(p3, "hotseat", {"pendule_active": False}),
         "partie a deux gardee pour plus tard")
donnees = sauvegarde.lire()
verifier(donnees is not None and donnees.get("mode") == "hotseat", "reprise : mode hotseat")
p3b = plateau_a_deux()
sauvegarde.appliquer(p3b, donnees)
jouer(p3b, ANGLAISE[4:])
p3b.terminer_partie("Abandon", "1-0")
infos3 = enregistrement.enregistrer_la_partie(p3b, donnees["mode"])
verifier(infos3 and os.path.exists(infos3["pgn"]), "PGN de la partie reprise ecrit")
sauvegarde.effacer()

print("4. Statistiques (comme l'ecran Statistiques)")
s = statistiques.calculer()
noms = [nom for nom, _, _ in s["ouvertures"]]
print("      ouvertures :", s["ouvertures"])
verifier(s["bilan"]["parties"] == 1,
         "une seule partie comptee (%d)" % s["bilan"]["parties"])
temoin = statistiques.famille_d_ouverture(historique_parties.lire_entetes(infos["pgn"]).get("Opening"))
verifier(noms == [temoin],
         "« Tes ouvertures » sans les parties a deux (%s)" % noms)

if echecs:
    print("\n%d ECHEC(S)" % len(echecs))
    sys.exit(1)
print("\nTout est bon.")
