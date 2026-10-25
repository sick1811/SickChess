# freestyle.py - SickChess : le mode Freestyle (échecs 960, « Fischer Random »).
#
# Les pièces de la dernière rangée sont mélangées au départ (960 positions
# possibles), les pions restent à leur place. Les Noirs ont la même position
# que les Blancs, en miroir. Le roi est toujours entre ses deux tours et les
# fous sur deux cases de couleurs différentes.
#
# LE ROQUE : comme aux échecs normaux, le roi arrive en g1 (petit roque) ou
# c1 (grand roque), la tour juste à côté (f1 ou d1), quelle que soit leur place
# de départ. python-chess note ce coup « roi qui prend sa propre tour »
# (ex. b1a1) : c'est aussi ce qu'attend Stockfish quand UCI_Chess960 est actif.
#
# POURQUOI CE FICHIER : une position Freestyle écrite en FEN (« KQkq ») perd
# ses droits de roque si on la relit avec chess.Board(fen) tout court
# (python-chess y exige le roi en e1 et les tours en a1 / h1). Toute partie
# relue (revue, analyse, sauvegarde, PGN) doit donc passer par plateau(fen).

import random

import chess

NOMBRE_DE_POSITIONS = 960
POSITION_CLASSIQUE = 518     # la position normale des échecs


def tirer_numero():
    """Une position Freestyle au hasard, jamais la position classique."""
    numero = random.randrange(NOMBRE_DE_POSITIONS - 1)
    return numero + 1 if numero >= POSITION_CLASSIQUE else numero


def plateau_de_depart(numero):
    return chess.Board.from_chess960_pos(int(numero) % NOMBRE_DE_POSITIONS)


def est_freestyle_fen(fen):
    """Vrai si cette FEN a des droits de roque que seules les règles
    Freestyle comprennent (roi hors de e1 / e8, ou tour hors des coins)."""
    if not fen:
        return False
    morceaux = str(fen).split()
    if len(morceaux) < 3 or morceaux[2] == "-":
        return False
    try:
        classique = chess.Board(fen)
        libre = chess.Board(fen, chess960=True)
    except ValueError:
        return False
    return libre.castling_rights != classique.castling_rights


def plateau(fen=None):
    """chess.Board(fen), mais qui garde le roque d'une partie Freestyle."""
    if fen is None:
        return chess.Board()
    return chess.Board(fen, chess960=est_freestyle_fen(fen))


def est_freestyle(board):
    """Le plateau joue-t-il une partie Freestyle (roque à la mode 960) ?"""
    return bool(getattr(board, "chess960", False))


def cases_du_roque(board, coup):
    """(arrivée du roi, départ de la tour, arrivée de la tour) d'un roque."""
    rangee = chess.square_rank(coup.from_square)
    if board.is_kingside_castling(coup):
        return (chess.square(6, rangee), coup.to_square, chess.square(5, rangee))
    return (chess.square(2, rangee), coup.to_square, chess.square(3, rangee))


def arrivee_du_roi(board, coup):
    """Case où le joueur pose son roi pour ce coup (g1 / c1 pour un roque)."""
    if board.is_castling(coup):
        return cases_du_roque(board, coup)[0]
    return coup.to_square


def coups_vers(board, coups, depart, arrivee):
    """Les coups de `coups` qui vont de `depart` à `arrivee`.

    En Freestyle on roque en posant le roi sur sa tour OU sur sa case
    d'arrivée (g1 / c1). Si un coup normal du roi va déjà sur cette case, il
    passe d'abord : pour roquer, on pose alors le roi sur la tour.
    """
    directs = [m for m in coups if m.from_square == depart and m.to_square == arrivee]
    if directs or not est_freestyle(board):
        return directs
    return [m for m in coups if m.from_square == depart and board.is_castling(m)
            and arrivee_du_roi(board, m) == arrivee]
