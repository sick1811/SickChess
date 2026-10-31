# tests/test_premouvements.py - plusieurs coups prepares d'avance (31/10,
# demande de Julien : « on ne peut en faire qu'un seul, il faudrait pouvoir en
# faire a l'infini ; clic droit les annule tous »).
#     python tests/test_premouvements.py
# Sans Stockfish : on joue nous-memes les coups de l'adversaire.

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
import board_geometry as geo
import board_render
from board import ChessBoard

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


ecran = pygame.display.set_mode((1280, 720))


def partie(fen=None, couleur=chess.WHITE):
    """Plateau ou l'on joue `couleur` (comme en ligne), l'autre camp est joue a la main."""
    p = ChessBoard(ecran, {"son_de_depart": False, "pendule_active": False})
    p.couleur_joueur = couleur
    if fen:
        p.board.set_fen(fen)
    return p


def centre(p, case):
    x, y = geo.case_vers_pixel(case, p.SQ_SIZE, p.flipped)
    return (x + p.SQ_SIZE // 2, y + p.SQ_SIZE // 2)


def clic(p, case, bouton=1):
    pos = centre(p, case)
    p.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=bouton, pos=pos))
    p.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=bouton, pos=pos))


def preparer(p, uci):
    """Clic sur la piece puis sur sa case d'arrivee, a la souris."""
    coup = chess.Move.from_uci(uci)
    clic(p, coup.from_square)
    clic(p, coup.to_square)


def adversaire(p, uci):
    p.make_move(chess.Move.from_uci(uci))
    p.update()


def ucis(p):
    return [m.uci() for m in p.premoves]


print("1. Plusieurs coups d'avance, a la souris")
p = partie()
p.make_move(chess.Move.from_uci("e2e4"))          # a l'adversaire de jouer
for uci in ("d2d4", "g1f3", "f3g5", "f1c4"):
    preparer(p, uci)
verifier(ucis(p) == ["d2d4", "g1f3", "f3g5", "f1c4"],
         "quatre coups prepares a la suite (%s)" % ucis(p))
avance = p.plateau_premouvements()
verifier(avance.piece_at(chess.G5) == chess.Piece(chess.KNIGHT, chess.WHITE)
         and avance.piece_at(chess.G1) is None,
         "position d'avance : le cavalier est deja en g5")
verifier(p.board.piece_at(chess.G1) == chess.Piece(chess.KNIGHT, chess.WHITE),
         "la vraie position ne bouge pas tant que l'adversaire n'a pas joue")
preparer(p, "f3e5")
verifier(len(p.premoves) == 4, "on ne reprend pas une piece deja partie de sa case (f3 est vide d'avance)")

print("2. Un coup part a chaque tour, dans l'ordre")
adversaire(p, "e7e5")
verifier([m.uci() for m in p.board.move_stack] == ["e2e4", "e7e5", "d2d4"]
         and ucis(p) == ["g1f3", "f3g5", "f1c4"], "1er tour : d4 part, 3 en attente")
adversaire(p, "b8c6")
verifier(p.board.move_stack[-1].uci() == "g1f3" and len(p.premoves) == 2,
         "2e tour : Cf3 part, 2 en attente")
adversaire(p, "g8f6")
adversaire(p, "a7a6")
verifier([m.uci() for m in p.board.move_stack][-4:] == ["g8f6", "f3g5", "a7a6", "f1c4"]
         and not p.premoves, "3e et 4e tours : Cg5 puis Fc4, la file est vide")

print("3. Un coup devenu impossible efface toute la suite")
p = partie()
p.make_move(chess.Move.from_uci("e2e4"))
preparer(p, "e4e5")
preparer(p, "e5e6")
verifier(ucis(p) == ["e4e5", "e5e6"], "deux poussees du pion preparees")
adversaire(p, "e7e5")                              # le pion e4 est bloque
verifier(p.board.move_stack[-1].uci() == "e7e5" and not p.premoves,
         "e5 bloque : rien n'est joue, toute la file est oubliee")

print("4. Clic droit (et Echap) annule TOUS les coups prepares")
p = partie()
p.make_move(chess.Move.from_uci("e2e4"))
for uci in ("d2d4", "b1c3", "c1f4"):
    preparer(p, uci)
clic(p, chess.H5, bouton=3)
verifier(not p.premoves, "clic droit : les trois coups sont annules")
fleches = getattr(p.right_click_manager, "fleches", None)
verifier(not fleches, "ce clic droit n'a pas trace de fleche ni colorie de case")
preparer(p, "d2d4")
clic(p, chess.G1)                                  # cavalier en main
clic(p, chess.A8, bouton=3)
verifier(not p.premoves and p.selected_square is None,
         "clic droit avec une piece en main : piece reposee et file vide")
preparer(p, "d2d4")
preparer(p, "c1f4")
p.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode=""))
verifier(not p.premoves, "Echap : tous les coups prepares sont annules")

print("5. Coups possibles d'avance (clouage, prise, promotion)")
# Le fou e2 est cloue par la tour e8, mais l'adversaire peut la bouger : on a
# le droit de le preparer, le vrai controle se fait quand le coup part.
p = partie("4r1k1/8/8/8/8/8/4B3/4K3 b - - 0 1")
preparer(p, "e2b5")
verifier(ucis(p) == ["e2b5"], "piece clouee : le coup se prepare quand meme")
adversaire(p, "e8f8")
verifier(p.board.move_stack[-1].uci() == "e2b5", "la tour est partie : le coup passe")
p = partie("4r1k1/8/8/8/8/8/4B3/4K3 b - - 0 1")
preparer(p, "e2b5")
adversaire(p, "g8h8")
verifier(p.board.move_stack[-1].uci() == "g8h8" and not p.premoves,
         "toujours cloue : le coup n'est pas joue (regle respectee)")
p = partie("1k6/4P3/8/8/8/8/8/4K3 b - - 0 1")
preparer(p, "e7e8")
preparer(p, "e8e4")
verifier(ucis(p) == ["e7e8q", "e8e4"], "promotion en dame d'avance, puis la dame rejoue")
p = partie("1k6/8/8/8/8/8/8/R3K2R b KQ - 0 1")
preparer(p, "e1g1")
verifier(ucis(p) == ["e1g1"], "roque prepare d'avance")
adversaire(p, "b8b7")
verifier(p.board.move_stack[-1].uci() == "e1g1" and p.board.piece_at(chess.F1)
         == chess.Piece(chess.ROOK, chess.WHITE), "le roque part : roi g1, tour f1")

print("6. Fin de partie : la file est videe et rien ne part")
p = partie("6k1/5ppp/8/8/8/8/r4PPP/6K1 b - - 0 1")
preparer(p, "h2h3")
preparer(p, "h3h4")
adversaire(p, "a2a1")                              # mat du couloir
verifier(p.game_over and not p.premoves and p.board.move_stack[-1].uci() == "a2a1",
         "mat : aucun coup prepare ne part, la file est vide (%s)" % p.game_over_reason)

print("7. Dessin : coup prevu presque transparent, vraie piece un peu plus visible")
p = partie()
p.make_move(chess.Move.from_uci("e2e4"))
preparer(p, "g1f3")
preparer(p, "f3g5")
poses = []
original = board_render.BoardRender._poser_piece


def espion(self, image, square, opacite=None):
    poses.append((square, opacite))
    return original(self, image, square, opacite)


board_render.BoardRender._poser_piece = espion
p.draw()
board_render.BoardRender._poser_piece = original
verifier((chess.G1, board_render.OPACITE_PIECE_QUI_PART) in poses,
         "le cavalier reste visible en g1, un peu transparent")
verifier((chess.G5, board_render.OPACITE_FANTOME) in poses,
         "le cavalier prevu en g5 est presque transparent")
verifier(not any(s == chess.F3 for s, _ in poses), "pas de fantome sur la case de passage f3")
verifier(board_render.OPACITE_FANTOME < board_render.OPACITE_PIECE_QUI_PART < 255,
         "fantome plus transparent que la vraie piece")
verifier(all(o is None for s, o in poses if s not in (chess.G1, chess.G5)),
         "les autres pieces sont dessinees normalement")
p.premove = None
verifier(p.premoves == [] and p.premove is None, "premove = None vide la file (ecrans problemes)")

print("8. Option coupee : rien ne se prepare")
p = partie()
p.premouvement_actif = False
p.make_move(chess.Move.from_uci("e2e4"))
preparer(p, "d2d4")
verifier(not p.premoves, "pre-mouvement desactive dans Options : aucun coup prepare")

print()
if echecs:
    print("%d ECHEC(S)" % len(echecs))
    sys.exit(1)
print("Tout est bon.")
