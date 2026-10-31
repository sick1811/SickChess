# tests/test_nulles.py - le pat et la repetition arretent bien la partie, dans
# tous les modes (25/10, retour de Julien : « le pat / la repetition marche une
# fois sur 10 » - pas reproduit ici ; ces controles le surveillent).
#     python tests/test_nulles.py
# Sans Stockfish : a deux sur ce PC et apres une reprise. Avec Stockfish
# (config.json ou SICKCHESS_STOCKFISH) : aussi contre l'ordinateur, 5 fois.

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

import asset_manager
_DOSSIER = tempfile.mkdtemp()
asset_manager.dossier_ecriture = lambda: _DOSSIER       # jamais les vraies donnees

import chess
import pygame
pygame.init()
import regles_nulle
from game_manager import GameManager

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


gm = GameManager("test")
gm.screen = pygame.display.set_mode((1280, 720))
gm._appliquer_taille(1280, 720)
ALLER_RETOUR = "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8".split()
PAT = ("7k/8/5K2/6Q1/8/8/8/8 w - - 0 1", "g5g6")


def partie(mode="hotseat", fen=None):
    gm.game_mode = mode
    gm.reglages = {"minutes": 5, "increment": 0, "pendule_active": False,
                   "elo": 1500, "ia_joue_blancs": False}
    assert gm.preparer_partie()
    if fen:
        gm.board.board.set_fen(fen)
    return gm.board


def jouer(b, ucis, attendre_ia=False):
    for uci in ucis:
        if b.game_over:
            break
        b.make_move(chess.Move.from_uci(uci))
        for _ in range(40 if attendre_ia else 3):
            if gm.current_mode is not None:
                gm.current_mode.update()
            b.update()
            if b.game_over or not attendre_ia:
                break
            time.sleep(0.05)
    return b


print("1. A deux sur ce PC")
b = jouer(partie(), ALLER_RETOUR[:4])
verifier(not b.game_over and regles_nulle.repetitions(b.board) == 2,
         "2e fois la meme position : la partie continue, l'encart previent")
verifier("2 fois" in regles_nulle.resume(b.board), "annonce : « %s »" % regles_nulle.resume(b.board))
jouer(b, ALLER_RETOUR[4:])
verifier(b.game_over and "RÉPÉTITION" in (b.game_over_reason or "") and b.result == "1/2-1/2",
         "3e fois : nulle par repetition (%s, %s)" % (b.game_over_reason, b.result))
gm.cleanup_game()
b = jouer(partie(fen=PAT[0]), [PAT[1]])
verifier(b.game_over and "PAT" in (b.game_over_reason or "") and b.result == "1/2-1/2",
         "pat : la partie s'arrete (%s)" % b.game_over_reason)
gm.cleanup_game()
# une repetition non consecutive (la position revient apres d'autres coups)
b = jouer(partie(), "g1f3 g8f6 f3g1 f6g8 b1c3 b8c6 c3b1 c6b8 g1f3 g8f6 f3g1 f6g8".split())
verifier(b.game_over and "RÉPÉTITION" in (b.game_over_reason or ""),
         "position de depart vue 3 fois, pas a la suite : nulle (%s)" % b.game_over_reason)
gm.cleanup_game()

print("1 bis. Un coup prepare d'avance attend (cas de l'ami de Julien, 25/10)")
# L'adversaire ramene la position une 3e fois alors qu'un pre-mouvement attend :
# avant le 25/10, le pre-mouvement partait avant qu'on regarde la fin de partie,
# la repetition passait a la trappe et l'avertissement jaune s'effacait.
b = jouer(partie(), ALLER_RETOUR[:7])
b.premove = chess.Move.from_uci("b1c3")
jouer(b, ALLER_RETOUR[7:])
verifier(b.game_over and "RÉPÉTITION" in (b.game_over_reason or ""),
         "3e retour joue par l'adversaire, pre-mouvement en attente : nulle (%s)" % b.game_over_reason)
verifier(len(b.board.move_stack) == 8, "le pre-mouvement n'est pas joue apres la nulle (%d coups)"
         % len(b.board.move_stack))
gm.cleanup_game()
# Meme chose pour la regle des 50 coups : le 100e demi-coup vient de l'adversaire.
b = partie(fen="4k3/8/8/8/8/8/8/R3K3 b - - 99 80")
b.premove = chess.Move.from_uci("a1a2")
jouer(b, ["e8d8"])
verifier(b.game_over and "50 COUPS" in (b.game_over_reason or ""),
         "50 coups atteints par l'adversaire, pre-mouvement en attente : nulle (%s)" % b.game_over_reason)
gm.cleanup_game()
for _essai in range(20):
    b = jouer(partie(), ALLER_RETOUR[:7])
    b.premove = chess.Move.from_uci("b1c3")
    jouer(b, ALLER_RETOUR[7:])
    if not (b.game_over and "RÉPÉTITION" in (b.game_over_reason or "")):
        break
    gm.cleanup_game()
else:
    essai = 20
verifier(essai == 20, "repetition avec pre-mouvement : nulle %d fois sur 20" % essai)

print("2. Apres « Reprendre » (la partie sauvegardee est rejouee)")
b = jouer(partie(), ALLER_RETOUR[:4])
donnees = {"mode": "hotseat", "coups": [m.uci() for m in b.board.move_stack],
           "fen_initiale": chess.STARTING_FEN, "reglages": gm.reglages}
gm.cleanup_game()
gm.reprise = donnees
b = partie()
verifier(len(b.board.move_stack) == 4 and regles_nulle.repetitions(b.board) == 2,
         "la reprise garde l'historique : position deja vue 2 fois")
jouer(b, ALLER_RETOUR[4:])
verifier(b.game_over and "RÉPÉTITION" in (b.game_over_reason or ""),
         "apres la reprise : nulle par repetition (%s)" % b.game_over_reason)
gm.cleanup_game()


def chemin_stockfish():
    chemin = os.environ.get("SICKCHESS_STOCKFISH")
    if not chemin:
        try:
            with open("config.json", encoding="utf-8") as f:
                chemin = json.load(f).get("stockfish_path")
        except (OSError, ValueError):
            chemin = None
    return chemin if chemin and os.path.exists(chemin) else None


if chemin_stockfish():
    print("3. Contre l'ordinateur (vrai Stockfish), 5 fois")
    gm.stockfish_path = chemin_stockfish()    # 25/10 : celui trouve (cloud : SICKCHESS_STOCKFISH)
    vus = 0
    for _ in range(5):
        b = jouer(partie("stockfish", PAT[0]), [PAT[1]], attendre_ia=True)
        vus += b.game_over and "PAT" in (b.game_over_reason or "")
        gm.cleanup_game()
    verifier(vus == 5, "pat donne a l'ordinateur : partie arretee %d fois sur 5" % vus)
else:
    print("3. (pas de Stockfish : contre l'ordinateur saute)")

gm.cleanup()
print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
