# tests/test_regles.py - les regles officielles des echecs (FIDE), une par une.
#     python tests/test_regles.py
# Sans Stockfish. REGLES INTOUCHABLES (voir CLAUDE.md) : un controle de cette
# serie ne se supprime jamais ; s'il devient rouge, c'est le jeu qu'on corrige.

import os
import sys
import tempfile

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
from rules import ChessRules

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def jouer(fen, coups):
    b = chess.Board(fen) if fen else chess.Board()
    for c in coups.split():
        b.push_uci(c)
    return b


def legal(fen, uci):
    return chess.Move.from_uci(uci) in chess.Board(fen).legal_moves


def fin(b):
    return ChessRules.check_game_over(b)


print("== Coups ==")
# Le roi ne reste jamais en echec ; les rois ne se touchent jamais.
verifier(not legal("k3r3/8/8/8/8/8/4B3/4K3 w - - 0 1", "e2d3")
         and not legal("4k3/8/8/8/8/8/3r4/4K3 w - - 0 1", "e1e2"),
         "un coup qui laisse son roi en echec est interdit")
verifier(not legal("8/8/8/3k4/8/3K4/8/8 w - - 0 1", "d3d4"),
         "les deux rois ne sont jamais cote a cote")
# Une piece clouee attaque quand meme : le roi adverse ne peut pas y aller.
verifier(not legal("3r4/2k5/8/8/3N4/8/8/3K4 b - - 0 1", "c7c6"),
         "un cavalier cloue controle encore ses cases (le roi noir ne va pas en c6)")
verifier(not legal("3r4/2k5/8/8/3N4/8/8/3K4 w - - 0 1", "d4c6"),
         "une piece clouee ne bouge pas")

print("== Roque ==")
verifier(legal("1r2k3/8/8/8/8/8/8/R3K3 w Q - 0 1", "e1c1"),
         "grand roque permis quand b1 est attaquee (seule la tour y passe)")
verifier(not legal("3rk3/8/8/8/8/8/8/R3K3 w Q - 0 1", "e1c1"),
         "grand roque interdit si le roi traverse d1 attaquee")
verifier(not legal("2r1k3/8/8/8/8/8/8/R3K3 w Q - 0 1", "e1c1"),
         "grand roque interdit si le roi arrive sur c1 attaquee")
verifier(not legal("4r1k1/8/8/8/8/8/8/4K2R w K - 0 1", "e1g1"),
         "pas de roque quand le roi est en echec")
verifier(not legal("4k3/8/8/8/8/8/8/R2QK3 w Q - 0 1", "e1c1"),
         "pas de roque si une piece est entre le roi et la tour")
verifier(not legal("4k3/8/8/8/8/8/8/R3K3 w - - 0 1", "e1c1"),
         "pas de roque si le roi ou la tour a deja bouge (droit perdu)")
b = jouer(None, "e2e4 e7e5 g1f3 b8c6 f1c4 g8f6")
verifier(b.is_castling(chess.Move.from_uci("e1g1")) and chess.Move.from_uci("e1g1") in b.legal_moves,
         "petit roque normal possible")
b.push_uci("e1g1")
verifier(b.piece_at(chess.G1) == chess.Piece(chess.KING, chess.WHITE)
         and b.piece_at(chess.F1) == chess.Piece(chess.ROOK, chess.WHITE),
         "apres O-O : roi en g1, tour en f1")

print("== Prise en passant ==")
b = jouer(None, "e2e4 a7a6 e4e5 d7d5")
verifier(chess.Move.from_uci("e5d6") in b.legal_moves,
         "prise en passant juste apres l'avance de deux cases")
b = jouer(None, "e2e4 a7a6 e4e5 d7d5 h2h3 h7h6")
verifier(chess.Move.from_uci("e5d6") not in b.legal_moves,
         "prise en passant interdite un coup trop tard")
verifier(not legal("8/8/8/K2pP2r/8/8/8/7k w - d6 0 1", "e5d6"),
         "prise en passant interdite si elle met son roi en echec")

print("== Promotion ==")
fen = "8/P7/8/8/8/8/8/k6K w - - 0 1"
promos = {m.promotion for m in chess.Board(fen).legal_moves if m.from_square == chess.A7}
verifier(promos == {chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT},
         "promotion : dame, tour, fou, cavalier (jamais roi ni pion)")
verifier(chess.Move.from_uci("a7a8") not in chess.Board(fen).legal_moves,
         "la promotion est obligatoire (pas de pion en 8e rangee)")
verifier(legal("8/P7/8/8/8/8/8/k2Q3K w - - 0 1", "a7a8q"),
         "deuxieme dame permise")

print("== Fins de partie ==")
b = jouer(None, "f2f3 e7e5 g2g4 d8h4")
f, r = fin(b)
verifier(f and "MAT" in r and "Noir" in r, "mat du berger inverse : les Noirs gagnent")
f, r = fin(chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"))
verifier(f and "PAT" in r, "pat = nulle")
for fen, nom in (("8/8/8/4k3/8/8/8/4K3 w - - 0 1", "R contre R"),
                 ("8/8/8/4k3/8/8/8/3BK3 w - - 0 1", "R+F contre R"),
                 ("8/8/8/4k3/8/8/8/3NK3 w - - 0 1", "R+C contre R"),
                 ("8/8/1b6/4k3/8/8/8/2B1K3 w - - 0 1", "fous de meme couleur")):
    f, r = fin(chess.Board(fen))
    verifier(f and "INSUFFISANT" in r, "materiel insuffisant : %s" % nom)
f, r = fin(chess.Board("8/8/8/4k3/8/8/8/2NNK3 w - - 0 1"))
verifier(not f, "R+2C contre R n'est PAS nul d'office")
f, r = fin(chess.Board("8/8/2b5/4k3/8/8/8/2B1K3 w - - 0 1"))
verifier(not f, "fous de couleurs differentes : pas nul d'office")

aller = "g1f3 g8f6 f3g1 f6g8 "
b = jouer(None, aller)
verifier(not fin(b)[0], "position vue 2 fois : la partie continue (pas un coup trop tot)")
b = jouer(None, aller * 2)
f, r = fin(b)
verifier(f and "TRIPLE" in r, "3 repetitions = nulle")
b = jouer(None, aller * 4)
f, r = fin(b)
verifier(f and "CINQ" in r, "5 repetitions = nulle automatique")

verifier(not fin(chess.Board("4k3/8/8/8/8/8/8/R3K3 w - - 99 80"))[0],
         "99 demi-coups sans prise : la partie continue")
f, r = fin(chess.Board("4k3/8/8/8/8/8/8/R3K3 w - - 100 80"))
verifier(f and "50" in r, "50 coups sans prise ni pion = nulle")
f, r = fin(chess.Board("4k3/8/8/8/8/8/8/R3K3 w - - 150 80"))
verifier(f and "75" in r, "75 coups = nulle automatique")
b = jouer("7k/8/6K1/8/8/8/8/R7 w - - 149 80", "a1a8")
f, r = fin(b)
verifier(b.halfmove_clock == 150 and f and "MAT" in r,
         "mat au 75e coup : le MAT l'emporte sur la nulle")
b = jouer("7k/8/8/8/8/8/R7/1R4K1 w - - 0 1", "")
verifier(not fin(b)[0], "position normale : la partie continue")

print("== Chute au temps (FIDE 6.9) ==")
raison, res = ChessRules.fin_au_temps(chess.Board("8/8/8/4k3/8/8/8/R3K3 w - - 0 1"),
                                      chess.BLACK)
verifier(res == "1-0", "les Noirs tombent, les Blancs ont une tour : 1-0")
raison, res = ChessRules.fin_au_temps(chess.Board("8/8/8/4k3/8/8/8/R3K3 w - - 0 1"),
                                      chess.WHITE)
verifier(res == "1/2-1/2" and "nul" in raison,
         "les Blancs tombent, les Noirs n'ont que le roi : NULLE (%s)" % raison)
raison, res = ChessRules.fin_au_temps(chess.Board("8/8/8/4k3/8/8/2n5/R3K3 w - - 0 1"),
                                      chess.WHITE)
verifier(res == "0-1", "roi + cavalier contre roi + tour : un mat aide reste possible -> 0-1")
raison, res = ChessRules.fin_au_temps(chess.Board("8/8/8/4k3/8/8/8/1n2K3 w - - 0 1"),
                                      chess.WHITE)
verifier(res == "1/2-1/2", "roi + cavalier contre roi seul : nulle")
raison, res = ChessRules.fin_au_temps(chess.Board("8/8/8/4k3/8/8/1nn5/4K3 w - - 0 1"),
                                      chess.WHITE)
verifier(res == "0-1", "roi + 2 cavaliers peuvent mater : les Blancs perdent")

# Le vrai plateau du jeu (hors ligne) applique la regle.
from board import ChessBoard
ecran = pygame.display.set_mode((1280, 720))
plateau = ChessBoard(ecran, {"son_de_depart": False, "minutes": 5, "increment": 0,
                             "pendule_active": True})
plateau.board = chess.Board("8/8/8/4k3/8/8/8/R3K3 w - - 0 1")
plateau.timer.update = lambda trait: chess.WHITE
plateau.update()
verifier(plateau.game_over and plateau.result == "1/2-1/2",
         "plateau : les Blancs tombent contre un roi seul -> nulle (%s)"
         % plateau.game_over_reason)
plateau = ChessBoard(ecran, {"son_de_depart": False, "minutes": 5, "increment": 0,
                             "pendule_active": True})
plateau.timer.update = lambda trait: chess.WHITE
plateau.update()
verifier(plateau.game_over and plateau.result == "0-1",
         "plateau : les Blancs tombent au debut de partie -> 0-1")

print()
if echecs:
    print("%d ECHEC(S)" % len(echecs))
    sys.exit(1)
print("Toutes les regles sont respectees.")
