# mise_en_page.py - V7.2 : NOUVEAU FICHIER
#
# LA GRILLE COMMUNE A TOUS LES ECRANS (ta demande : "revois les dispositions").
#
# CE QUI N'ALLAIT PAS, MESURE ET NON SUPPOSE :
#
#   1. UN QUART DE LA FENETRE ETAIT VIDE. Sur l'ecran de reglages en 1024x671,
#      les panneaux s'arretaient a y=399 et les cases a cocher commencaient a
#      y=565 : 166 pixels de vide, 25 % de la hauteur. En 1280x720, 208 pixels,
#      29 %. Les panneaux se dessinaient a leur hauteur naturelle et flottaient
#      en haut ; personne ne remplissait le reste.
#
#   2. LA BANDE DU BAS AVAIT DEUX ALIGNEMENTS. Les cases a cocher commencaient
#      a x=30, les boutons a x=244 : rien ne retombait sur rien.
#
#   3. SOIXANTE VALEURS D'ESPACEMENT DIFFERENTES etaient melangees dans les
#      ecrans : 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 17, 18, 20, 22,
#      24, 26, 28, 30... C'est ca qui fait qu'un ecran a l'air bricole meme
#      quand chaque element pris isolement est correct : l'oeil sent que rien
#      ne s'aligne sur rien.
#
#   4. LE TITRE MANGEAIT TROIS LIGNES POUR DEUX MOTS : le titre, puis la ligne
#      des raccourcis en dessous. Sur la meme ligne, ca rend ~40 pixels au
#      contenu, sur chaque ecran.
#
# LA GRILLE : une seule unite, 8 pixels, et ses multiples. Rien d'autre.
# Toutes les valeurs passent par ces fonctions, donc elles suivent l'echelle de
# la fenetre sans qu'on ait a y penser.
#
# AUCUNE FONCTION SUPPRIMEE : ce fichier n'existait pas. Les ecrans qui ne
# l'utilisent pas encore continuent de marcher exactement comme avant.

import pygame


# L'unite. Tout le reste en est un multiple.
UNITE = 8


def pas(nombre, ech=1.0):
    """n pas de grille, a l'echelle de la fenetre. pas(2) = 16 px."""
    return max(1, int(round(nombre * UNITE * ech)))


def s(ech=1.0):
    """8 px : entre deux elements d'un meme bloc."""
    return pas(1, ech)


def m(ech=1.0):
    """16 px : entre deux blocs."""
    return pas(2, ech)


def l(ech=1.0):
    """24 px : la marge des bords de fenetre."""
    return pas(3, ech)


def xl(ech=1.0):
    """32 px : entre deux zones qui n'ont rien a voir."""
    return pas(4, ech)


def colonnes(zone, parts=(1, 1), ech=1.0):
    """Coupe une zone en colonnes, dans les proportions demandees.

    colonnes(zone, (2, 3)) donne 40 % / 60 %. C'est ce qui permet de donner
    plus de place a la colonne qui a plus a dire, au lieu de couper en deux
    par habitude.
    """
    parts = [max(0.01, float(p)) for p in (parts or (1, 1))]
    ecart = m(ech)
    utile = zone.width - ecart * (len(parts) - 1)
    if utile <= 0:
        # Fenetre trop etroite pour l'ecart demande. On rend quand meme UNE
        # colonne PAR PART : l'appelant ecrit "col_g, col_d = colonnes(...)"
        # et une liste d'un seul element le faisait planter (ValueError) au
        # lieu de simplement serrer la mise en page.
        largeur = max(1, zone.width // len(parts))
        return [pygame.Rect(zone.x + index * largeur, zone.y, largeur,
                            zone.height)
                for index in range(len(parts))]
    total = sum(parts)
    sortie = []
    x = zone.x
    for index, part in enumerate(parts):
        largeur = (utile - sum(int(utile * p / total) for p in parts[:index])
                   if index == len(parts) - 1
                   else int(utile * part / total))
        sortie.append(pygame.Rect(x, zone.y, max(1, largeur), zone.height))
        x += largeur + ecart
    return sortie


# 25/10 (petites fenetres) : quand la place manque, on reduit l'echelle d'un
# ecran jusqu'a ce que tout tienne - mais jamais en dessous de ceci (les textes
# passent de toute facon par ui.t, qui ne descend pas sous ui.TEXTE_MINI).
ECHELLE_MINI = 0.7


def echelle_qui_tient(besoin, place, ech, mini=ECHELLE_MINI):
    """La plus grande echelle (au plus 'ech') pour laquelle tout tient.

    besoin : fonction echelle -> pixels demandes ; place : pixels disponibles.
    C'est LA regle commune des ecrans : on rapetisse au lieu de cacher un
    panneau ou de laisser un bloc deborder. Si meme 'mini' ne tient pas, on
    rend 'mini' : l'appelant rogne alors ce qui peut l'etre (liste des coups).
    """
    mini = min(mini, ech)
    if besoin(ech) <= place:
        return ech
    if besoin(mini) > place:
        return mini
    bas, haut = mini, ech
    for _ in range(12):
        milieu = (bas + haut) / 2.0
        if besoin(milieu) <= place:
            bas = milieu
        else:
            haut = milieu
    return bas


def bande_du_bas(largeur, hauteur_fenetre, ech=1.0, avec_cases=True):
    """La bande du bas : cases a cocher A GAUCHE, boutons A DROITE, meme ligne.

    Renvoie (zone des cases, zone des boutons, y du haut de la bande).
    Un seul bord de reference : la marge, des deux cotes.
    """
    marge = l(ech)
    h_bouton = pas(6, ech)                   # 48 px : la hauteur d'un bouton
    y_bouton = hauteur_fenetre - marge - h_bouton
    largeur_boutons = min(pas(64, ech), (largeur - 2 * marge) * 2 // 3)
    zone_boutons = pygame.Rect(largeur - marge - largeur_boutons, y_bouton,
                               largeur_boutons, h_bouton)
    zone_cases = pygame.Rect(marge, y_bouton,
                             max(1, zone_boutons.x - marge - m(ech)), h_bouton)
    if not avec_cases:
        zone_cases = pygame.Rect(marge, y_bouton, 0, h_bouton)
    return zone_cases, zone_boutons, y_bouton - m(ech)


def etirer(blocs, bas):
    """Etire le DERNIER bloc jusqu'en bas. C'est le correctif du grand vide.

    'blocs' : la liste des rectangles d'une colonne, dans l'ordre. On ne touche
    qu'au dernier : les autres gardent la hauteur qu'il leur faut.
    """
    reels = [b for b in blocs if b is not None]
    if not reels:
        return blocs
    dernier = reels[-1]
    if bas > dernier.bottom:
        dernier.height = bas - dernier.y
    return blocs
