# tests/test_sauvegarde_freestyle.py - reprendre une partie Freestyle (31/10, séance 50).
#     python tests/test_sauvegarde_freestyle.py
# Une partie Freestyle interrompue (partie_en_cours.json) doit rester Freestyle
# à la reprise : roque 960, numéro de position affiché, règlement de tournoi.
# Avant : seul est_freestyle_fen(fen) décidait, et les 18 positions qu'il ne
# reconnaît pas (roi en e1, tours en a1 / h1 : n° 414, 518...) repartaient en
# partie classique. La sauvegarde est écrite dans un dossier temporaire.

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
ecran = pygame.display.set_mode((1280, 720))

import freestyle
import sauvegarde
from board import ChessBoard

sauvegarde.FICHIER = os.path.join(tempfile.mkdtemp(), "partie_en_cours.json")

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


REGLAGES = {"son_de_depart": False, "pendule_active": True, "minutes": 5,
            "increment_secondes": 0}


def partie(variante, numero=None, coups=("e2e4", "e7e5", "g2g3")):
    """Une partie jouée puis sauvegardée, comme dans le jeu."""
    reglages = dict(REGLAGES, variante=variante, freestyle_hasard=False,
                    freestyle_numero=numero or 0)
    plateau = freestyle.reglages_de_partie(reglages)
    if numero is not None:
        plateau["freestyle"] = numero        # le tournoi tire au hasard : on fixe
    p = ChessBoard(ecran, plateau)
    for uci in coups:
        p.make_move(chess.Move.from_uci(uci))
    verifier(sauvegarde.enregistrer(p, "hotseat", reglages), "partie sauvegardée")
    return p, reglages


def reprendre(reglages, donnees=None):
    """La reprise, comme game_manager.preparer_partie."""
    donnees = donnees or sauvegarde.lire()
    p = ChessBoard(ecran, freestyle.reglages_de_partie(reglages,
                                                       donnees.get("fen_initiale")))
    sauvegarde.appliquer(p, donnees)
    return p


print("== Partie Freestyle reprise : elle reste Freestyle ==")
for numero in (77, 414, 518):
    avant, reglages = partie("freestyle", numero)
    apres = reprendre(reglages)
    verifier(apres.board.chess960 and apres.board.fen() == avant.board.fen(),
             "n° %d : roque Freestyle gardé, même position" % numero)
    verifier(apres.numero_freestyle == numero,
             "n° %d : le numéro de la position s'affiche encore (%s)"
             % (numero, apres.numero_freestyle))

avant, reglages = partie("tournoi", 518)
apres = reprendre(reglages)
verifier(apres.board.chess960 and apres.numero_freestyle == avant.numero_freestyle
         and apres.tournoi_fide,
         "tournoi Freestyle repris : toujours Freestyle, règlement de tournoi gardé")

print("== Partie classique reprise : elle reste classique ==")
avant, reglages = partie("normal")
apres = reprendre(reglages)
verifier(not apres.board.chess960 and apres.numero_freestyle is None
         and apres.board.fen() == avant.board.fen(),
         "partie classique : pas de Freestyle à la reprise")

print("== Ancienne sauvegarde (sans l'indicateur) : comme avant ==")
avant, reglages = partie("freestyle", 77)
donnees = sauvegarde.lire()
for cle in ("freestyle", "numero_freestyle", "tournoi_fide"):
    donnees.pop(cle, None)
apres = reprendre(reglages, donnees)
verifier(apres.board.chess960 and apres.numero_freestyle == 77
         and apres.board.fen() == avant.board.fen(),
         "ancienne sauvegarde n° 77 : reconnue à sa FEN, comme avant")
avant, reglages = partie("normal")
donnees = sauvegarde.lire()
donnees.pop("freestyle", None)
apres = reprendre(reglages, donnees)
verifier(not apres.board.chess960 and apres.board.fen() == avant.board.fen(),
         "ancienne sauvegarde classique : reste classique")

print("== Sauvegarde abîmée à la main : la reprise ne plante pas ==")
avant, reglages = partie("freestyle", 414)
donnees = sauvegarde.lire()
donnees["numero_freestyle"] = "abc"
try:
    apres = reprendre(reglages, donnees)
    verifier(apres.board.chess960 and apres.board.fen() == avant.board.fen(),
             "numéro illisible : la partie Freestyle reprend quand même")
except Exception as souci:
    verifier(False, "numéro illisible : la reprise plante (%r)" % souci)

sauvegarde.effacer()
print()
if echecs:
    print("%d ECHEC(S)" % len(echecs))
    sys.exit(1)
print("Tout est vert.")
