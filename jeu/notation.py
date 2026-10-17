# notation.py - SickChess : la notation des coups a l'ecran.
#
# Choix de Julien (17/10) : au choix dans Options, ANGLAISE par defaut.
#   anglaise  : Nf3, Bxc4, Qh5, O-O, e8=Q   (K Q R B N)
#   francaise : Cf3, Fxc4, Dh5, O-O, e8=D   (R D T F C)
# Le jeu calcule et enregistre TOUJOURS en anglais (PGN, analyse, base de
# problemes) : seule la traduction affichee change. Une seule fonction a
# appeler partout ou un coup est montre : afficher(san).

import apparence

NOTATIONS = {
    "anglaise": None,
    "francaise": str.maketrans("KQRBN", "RDTFC"),
}
PAR_DEFAUT = "anglaise"


def choix():
    nom = str(apparence.reglage("notation", PAR_DEFAUT) or PAR_DEFAUT).lower()
    return nom if nom in NOTATIONS else PAR_DEFAUT


def afficher(san):
    """'Nf3' -> 'Cf3' en notation francaise ; inchange en anglaise."""
    if not san:
        return san
    table = NOTATIONS.get(choix())
    return str(san).translate(table) if table else str(san)


def afficher_ligne(texte):
    """Une suite de coups separes par des espaces ('Qxh7+ Kxh7 Rh3#')."""
    return " ".join(afficher(m) for m in str(texte or "").split(" "))
