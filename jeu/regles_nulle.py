# regles_nulle.py - V7.2 : NOUVEAU FICHIER
#
# PREVENIR AVANT LA NULLE (ta remarque : "la regle de repetition et des 50 coups
# manque aussi").
#
# Elles ne manquaient pas : je l'ai verifie sur ta machine, la triple repetition
# tombe au bon demi-coup et les 50 coups a 100 pile. Ce qui manquait, c'est
# qu'ON NE TE DISAIT RIEN. La partie s'arretait d'un coup, sans que rien ne
# t'ait prevenu que tu approchais. C'est ca qu'on repare ici.
#
# CE QU'ON SURVEILLE :
#
#   LES 50 COUPS : le compteur repart a zero a chaque prise et a chaque coup de
#       pion. On l'affiche a partir de 30 coups sans rien, et il devient rouge
#       dans les cinq derniers. En finale, savoir qu'il reste huit coups pour
#       mater change completement la facon de jouer.
#
#   LA REPETITION : des que la position en cours a DEJA ete vue deux fois, on
#       previent - la prochaine fois qu'elle revient, c'est nulle. C'est le
#       moment ou il faut choisir : prendre la nulle, ou changer de plan.
#
# CE FICHIER NE DECIDE RIEN. C'est rules.py qui arrete la partie, et il n'a pas
# ete touche. Ici on ne fait que REGARDER et prevenir.
#
# AUCUNE FONCTION SUPPRIMEE : ce fichier n'existait pas.

# Les seuils d'affichage.
SEUIL_50 = 60           # demi-coups sans prise ni pion avant d'en parler (30 coups)
ALERTE_50 = 90          # a partir de la, c'est urgent (5 coups avant la nulle)
LIMITE_50 = 100         # la nulle tombe ici (rules.py)
LIMITE_75 = 150         # et la elle est automatique, sans rien demander


def coups_sans_prise(board):
    """Demi-coups depuis la derniere prise ou le dernier coup de pion."""
    try:
        return int(board.halfmove_clock)
    except Exception:
        # Ce code tourne A CHAQUE IMAGE : il ne doit JAMAIS faire tomber la
        # partie, quel que soit l'etat du plateau.
        return 0


def repetitions(board, maximum=5):
    """Combien de fois la position en cours a deja ete vue. 1 = premiere fois.

    On n'utilise SURTOUT PAS can_claim_threefold_repetition() : elle repond oui
    quand le joueur POURRAIT atteindre la repetition avec un coup, donc un coup
    trop tot - c'etait le bug d'origine. is_repetition(n) regarde ce qui s'est
    vraiment passe sur l'echiquier.
    """
    try:
        for combien in range(maximum, 1, -1):
            if board.is_repetition(combien):
                return combien
    except Exception:
        return 1
    return 1


def etat(board):
    """Ce qu'il faut savoir pour prevenir. Ne decide jamais rien.

    {"demi_coups": 84, "restants": 16, "coups_restants": 8,
     "repetitions": 2, "alerte_50": True, "alerte_repetition": True,
     "urgent": False}
    """
    if board is None:
        return {"demi_coups": 0, "restants": LIMITE_50, "coups_restants": 50,
                "repetitions": 1, "alerte_50": False,
                "alerte_repetition": False, "urgent": False}
    demi = coups_sans_prise(board)
    vues = repetitions(board)
    restants = max(0, LIMITE_50 - demi)
    return {
        "demi_coups": demi,
        "restants": restants,
        "coups_restants": restants // 2,
        "repetitions": vues,
        "alerte_50": demi >= SEUIL_50,
        "alerte_repetition": vues >= 2,
        "urgent": demi >= ALERTE_50 or vues >= 2,
    }


def lignes(board):
    """Les phrases a afficher, avec leur niveau. [] quand il n'y a rien a dire.

    [(texte, "info" | "attention"), ...]
    """
    infos = etat(board)
    sortie = []

    if infos["alerte_repetition"]:
        vues = infos["repetitions"]
        if vues >= 3:
            sortie.append(("Position vue 3 fois - nulle par repetition",
                           "attention"))
        else:
            sortie.append(("Position deja vue 2 fois - au prochain retour, "
                           "c'est nulle", "attention"))

    if infos["alerte_50"]:
        niveau = "attention" if infos["demi_coups"] >= ALERTE_50 else "info"
        sortie.append(("Regle des 50 coups : %d / %d   (encore %d coups)"
                       % (infos["demi_coups"], LIMITE_50,
                          infos["coups_restants"]), niveau))
    return sortie


def resume(board):
    """Une seule ligne, la plus urgente. '' quand il n'y a rien a dire."""
    toutes = lignes(board)
    if not toutes:
        return ""
    for texte, niveau in toutes:
        if niveau == "attention":
            return texte
    return toutes[0][0]


def couleur(niveau, theme=None):
    """La couleur d'une ligne. Rouge quand ca presse, discret sinon."""
    if niveau == "attention":
        return (232, 150, 120)
    if theme:
        return theme.get("texte_discret", (150, 150, 150))
    return (150, 150, 150)
