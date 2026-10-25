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
    return libre.clean_castling_rights() != classique.clean_castling_rights()


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


# ------------------------------------------------------------ tournoi FIDE
#
# Règlement du championnat du monde FIDE Freestyle 2026 : position tirée au
# hasard, la 518 exclue, une position tirée ne revient pas ; position montrée
# 10 minutes avant la partie ; pas de nulle avant le 40e coup des Noirs.

PREPARATION_TOURNOI_S = 600
COUP_MINI_POUR_NULLE = 40
FICHIER_TIRAGES = "freestyle_tirages.json"


def _chemin_tirages():
    import os
    import asset_manager
    return os.path.join(asset_manager.dossier_ecriture(), FICHIER_TIRAGES)


def positions_deja_tirees():
    import json
    try:
        with open(_chemin_tirages(), "r", encoding="utf-8") as f:
            deja = json.load(f)
        return {int(n) for n in deja if 0 <= int(n) < NOMBRE_DE_POSITIONS}
    except (OSError, ValueError, TypeError):
        return set()


def tirer_numero_tournoi():
    """Comme tirer_numero(), sans jamais redonner une position déjà jouée en
    tournoi. Quand les 959 y sont passées, on recommence à zéro."""
    import json
    deja = positions_deja_tirees()
    libres = [n for n in range(NOMBRE_DE_POSITIONS)
              if n != POSITION_CLASSIQUE and n not in deja]
    if not libres:
        deja, libres = set(), [n for n in range(NOMBRE_DE_POSITIONS)
                               if n != POSITION_CLASSIQUE]
    numero = random.choice(libres)
    try:
        with open(_chemin_tirages(), "w", encoding="utf-8") as f:
            json.dump(sorted(deja | {numero}), f)
    except OSError as souci:
        print("[FREESTYLE] tirage non retenu : %s" % souci)
    return numero


def nulle_refusee(board, tournoi):
    """Message si le règlement du tournoi interdit encore la nulle, sinon None."""
    if tournoi and board.fullmove_number <= COUP_MINI_POUR_NULLE:
        return "Tournoi Freestyle : pas de nulle avant le 40e coup des Noirs."
    return None


def libelle(numero, tournoi=False):
    """« Freestyle n° 412 » (+ « - Tournoi Freestyle »), affiché pendant la partie."""
    texte = "Freestyle n° %d" % int(numero)
    return texte + "  -  Tournoi" if tournoi else texte


class Preparation:
    """Les minutes où l'on regarde la position avant de jouer (tournoi FIDE).

    Personne ne joue tant qu'elle dure ; la pendule ne part qu'au premier coup.
    Elle finit au bout du temps, ou quand chacun s'est dit prêt (`joueurs` =
    nombre d'accords attendus : 1 contre l'ordinateur ou à deux sur ce PC,
    2 en ligne).
    """

    def __init__(self, duree_s=PREPARATION_TOURNOI_S, joueurs=1, horloge=None):
        import time
        self._horloge = horloge or time.monotonic
        self.fin = self._horloge() + float(duree_s)
        self.joueurs = int(joueurs)
        self.prets = set()

    def reste_s(self):
        return max(0.0, self.fin - self._horloge())

    def en_cours(self):
        return self.reste_s() > 0 and len(self.prets) < self.joueurs

    def pret(self, qui="local"):
        self.prets.add(qui)

    def texte(self):
        reste = int(self.reste_s() + 0.999)
        return "Préparation : %s" % ("%d:%02d" % (reste // 60, reste % 60))


def numero_de_depart(fen):
    """Le numero (0-959) d'une position de depart Freestyle, sinon None."""
    if not fen or not est_freestyle_fen(fen):
        return None
    try:
        return plateau(fen).chess960_pos()
    except ValueError:
        return None


def reglages_de_partie(reglages, fen_reprise=None):
    """Les reglages du plateau pour UNE partie : tire la position Freestyle.

    variante « normal » / « freestyle » (au hasard ou n° choisi) / « tournoi ».
    Une partie reprise garde sa position (et ne refait pas la preparation).
    """
    reglages = dict(reglages or {})
    variante = reglages.get("variante", "normal")
    reglages["tournoi_fide"] = variante == "tournoi"
    if fen_reprise:
        reglages["freestyle"] = numero_de_depart(fen_reprise)
        reglages["preparation_s"] = 0
    elif variante == "tournoi":
        reglages["freestyle"] = tirer_numero_tournoi()
    elif variante == "freestyle":
        reglages["freestyle"] = tirer_numero() if reglages.get("freestyle_hasard", True) \
            else int(reglages.get("freestyle_numero", 0)) % NOMBRE_DE_POSITIONS
    else:
        reglages["freestyle"] = None
    return reglages
