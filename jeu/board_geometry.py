# board_geometry.py - V7 : la seule conversion case <-> pixel du projet
#
# EN V5 : cette conversion etait recopiee dans quatre fichiers, avec des
# versions qui n'etaient pas d'accord entre elles, et aucune n'inversait les
# colonnes quand le plateau etait retourne (miroir au lieu de rotation).
#
# EN V6 : tout est passe par ce fichier, mais le plateau etait toujours colle
# en haut a gauche, avec des cases de 80 pixels fixes.
#
# EN V7 : l'origine et la taille des cases sont reglables. C'est layout.py qui
# les fixe en fonction de la taille de la fenetre, ce qui permet le plein ecran,
# le redimensionnement, et un vrai decor autour de l'echiquier.

import chess

# Position du coin haut-gauche du plateau et taille d'une case.
# Valeurs par defaut = comportement de la V6 ; layout.py les remplace.
ORIGINE_X = 0
ORIGINE_Y = 0
TAILLE_CASE_PAR_DEFAUT = 80
TAILLE_CASE = 80


def configurer(origine_x, origine_y, taille_case):
    """Fixe la position et l'echelle du plateau (appele par layout.py)."""
    global ORIGINE_X, ORIGINE_Y, TAILLE_CASE
    ORIGINE_X = int(origine_x)
    ORIGINE_Y = int(origine_y)
    TAILLE_CASE = max(8, int(taille_case))
    return ORIGINE_X, ORIGINE_Y, TAILLE_CASE


def taille_case(sq_size=None):
    """Taille de case a utiliser : celle fournie, sinon celle de la disposition."""
    return int(sq_size) if sq_size else TAILLE_CASE


def colonne_ligne_ecran(square, flipped):
    """Case d'echiquier -> (colonne, ligne) a l'ecran, 0 = haut/gauche.

    Retourner le plateau, c'est une rotation de 180 degres : il faut inverser
    les colonnes ET les lignes.
    """
    colonne = chess.square_file(square)
    ligne = chess.square_rank(square)
    if flipped:
        return 7 - colonne, ligne
    return colonne, 7 - ligne


def case_vers_pixel(square, sq_size=None, flipped=False):
    """Coin haut-gauche de la case, en pixels dans la fenetre."""
    taille = taille_case(sq_size)
    colonne, ligne = colonne_ligne_ecran(square, flipped)
    return ORIGINE_X + colonne * taille, ORIGINE_Y + ligne * taille


def case_vers_pixel_local(square, sq_size=None, flipped=False):
    """Coin haut-gauche de la case, en pixels DANS le calque du plateau."""
    taille = taille_case(sq_size)
    colonne, ligne = colonne_ligne_ecran(square, flipped)
    return colonne * taille, ligne * taille


def centre_case(square, sq_size=None, flipped=False):
    taille = taille_case(sq_size)
    x, y = case_vers_pixel(square, taille, flipped)
    return x + taille // 2, y + taille // 2


def pixel_vers_case(pos, sq_size=None, flipped=False):
    """Position souris -> case d'echiquier, ou None en dehors du plateau."""
    taille = taille_case(sq_size)
    try:
        x, y = pos[0] - ORIGINE_X, pos[1] - ORIGINE_Y
    except (TypeError, IndexError):
        return None
    cote = 8 * taille
    if x < 0 or y < 0 or x >= cote or y >= cote:
        return None
    colonne = int(x // taille)
    ligne = int(y // taille)
    if flipped:
        return chess.square(7 - colonne, ligne)
    return chess.square(colonne, 7 - ligne)


def est_sur_le_plateau(pos, sq_size=None):
    return pixel_vers_case(pos, sq_size, False) is not None


def case_claire(square):
    """True si la case est claire. a1 (colonne 0, ligne 0) est sombre."""
    return (chess.square_file(square) + chess.square_rank(square)) % 2 == 1


def rectangle_case(square, sq_size=None, flipped=False):
    taille = taille_case(sq_size)
    x, y = case_vers_pixel(square, taille, flipped)
    return (x, y, taille, taille)
