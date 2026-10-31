# pieces_vectorielles.py - V7 : NOUVEAU FICHIER
#
# Le jeu de pieces classique par defaut, dessine par le jeu lui-meme.
#
# POURQUOI :
# Jusqu'ici les pieces venaient de fichiers PNG (jeu Pokemon), et il n'y avait
# aucun jeu "normal". Ici les six pieces sont decrites par des contours
# vectoriels et dessinees a la volee par pygame, ce qui donne :
#   - un jeu classique lisible tout de suite, sans aucun fichier image,
#   - des pieces nettes a n'importe quelle taille de plateau (utile quand la
#     fenetre est agrandie ou passee en plein ecran),
#   - la possibilite de changer les couleurs (themes) sans refaire d'images.
#
# Aucune bibliotheque en plus : tout est fait avec pygame.draw, en dessinant
# quatre fois trop grand puis en reduisant, ce qui lisse les bords.


import pygame

VIEWBOX = 45.0          # les contours sont decrits dans un carre de 45x45
SUR_ECHANTILLON = 4     # facteur d'anticrenelage

# --------------------------------------------------------------------- contours

PION = [
    "M 22.5,9 C 20.29,9 18.5,10.79 18.5,13 C 18.5,13.89 18.79,14.71 19.28,15.38 "
    "C 17.33,16.5 16,18.59 16,21 C 16,23.03 16.94,24.84 18.41,26.03 "
    "C 15.41,27.09 11,31.58 11,39.5 L 34,39.5 C 34,31.58 29.59,27.09 26.59,26.03 "
    "C 28.06,24.84 29,23.03 29,21 C 29,18.59 27.67,16.5 25.72,15.38 "
    "C 26.21,14.71 26.5,13.89 26.5,13 C 26.5,10.79 24.71,9 22.5,9 z",
]

TOUR = [
    "M 9,39.5 L 36,39.5 L 36,36.5 L 33,36.5 L 33,32.5 L 32,32.5 L 31,29.5 "
    "L 31,17 L 34,14 L 34,9 L 30,9 L 30,11 L 25,11 L 25,9 L 20,9 L 20,11 "
    "L 15,11 L 15,9 L 11,9 L 11,14 L 14,17 L 14,29.5 L 13,32.5 L 12,32.5 "
    "L 12,36.5 L 9,36.5 z",
]

FOU = [
    "M 22.5,8 C 21.29,8 20.3,8.99 20.3,10.2 C 20.3,11 20.73,11.7 21.37,12.09 "
    "C 18.5,13.7 16,16.8 16,20.6 C 16,23.6 17.4,25.9 19.1,27.5 "
    "C 16.4,28.7 14,30.2 14,32 L 31,32 C 31,30.2 28.6,28.7 25.9,27.5 "
    "C 27.6,25.9 29,23.6 29,20.6 C 29,16.8 26.5,13.7 23.63,12.09 "
    "C 24.27,11.7 24.7,11 24.7,10.2 C 24.7,8.99 23.71,8 22.5,8 z",
    "M 11.5,36.5 C 11.5,33.6 13.6,32 15.5,32 L 29.5,32 C 31.4,32 33.5,33.6 33.5,36.5 z",
    "M 8.5,39.5 L 36.5,39.5 L 36.5,36.5 L 8.5,36.5 z",
]

# CAVALIER - REDESSINE LE 03/09.
#
# TA REMARQUE : "les move de cavalier, les dessins sont des L".
#
# Tu avais raison, et j'ai regarde avant de te croire sur parole : j'ai
# rasterise la piece en caracteres pour la VOIR. Le corps se lisait comme une
# botte - un mur vertical a droite, un trait horizontal en bas - et la tete ne
# ressortait pas du tout. Un L, exactement.
#
# LA CAUSE : mon deuxieme trace (la tete et le museau) etait une reconstitution
# de memoire, pas le vrai. Il ne collait pas au premier.
#
# LA CORRECTION : les traces AUTHENTIQUES de Cburnett, ceux dont tout le monde
# se sert (lichess, Wikipedia, chess.com...), recopies depuis le depot de
# lichess (public/piece/cburnett/wN.svg). Ils sont en coordonnees RELATIVES -
# le lecteur de chemins sait deja les lire.
#
# Verifie de la meme facon apres coup : on voit les deux oreilles, le chanfrein
# qui descend vers la gauche, le museau, et le socle a droite.
CAVALIER = [
    "M22 10c10.5 1 16.5 8 16 29H15c0-9 10-6.5 8-21",
    "M24 18c.38 2.91-5.55 7.37-8 9-3 2-2.82 4.34-5 4-1.042-.94 1.41-3.04 0-3"
    "-1 0 .19 1.23-1 2-1 0-4.003 1-4-4 0-2 6-12 6-12s1.89-1.9 2-3.5"
    "c-.73-.994-.5-2-.5-3 1-1 3 2.5 3 2.5h2s.78-1.992 2.5-3c1 0 1 3 1 3",
]
# L'oeil du cavalier : un point de la couleur du CONTOUR (noir sur un cavalier
# blanc, clair sur un cavalier noir), comme sur le dessin d'origine.
CAVALIER_OEIL = ((9.0, 25.5), 0.7)

DAME = [
    "M 9,26.5 C 17.5,25 27.5,25 36,26.5 L 38.5,14 L 31,25.5 L 31,11 "
    "L 25.5,25 L 22.5,9.5 L 19.5,25 L 14,11 L 14,25.5 L 6.5,14 z",
    "M 9,26.5 C 9,28.5 10.5,28.5 10.5,30.5 C 10.5,32 10,32 10.5,33.5 "
    "C 9,35 9,36 9,36.5 C 6.5,38 11.5,39 11.5,39 C 15,40 30,40 33.5,39 "
    "C 33.5,39 38.5,38 36,36.5 C 36,36 36,35 34.5,33.5 "
    "C 35,32 34.5,32 34.5,30.5 C 34.5,28.5 36,28.5 36,26.5 z",
]
DAME_BOULES = [(6.5, 12.5), (14, 9.5), (22.5, 8), (31, 9.5), (38.5, 12.5)]
DAME_RAYON = 2.1

ROI = [
    "M 21.2,5 L 23.8,5 L 23.8,8 L 26.8,8 L 26.8,10.6 L 23.8,10.6 L 23.8,13.6 "
    "L 21.2,13.6 L 21.2,10.6 L 18.2,10.6 L 18.2,8 L 21.2,8 z",
    "M 22.5,13.8 C 26.2,16.4 27.8,19.1 27.8,21.8 C 27.8,24.4 25.7,26.4 22.5,27.6 "
    "C 19.3,26.4 17.2,24.4 17.2,21.8 C 17.2,19.1 18.8,16.4 22.5,13.8 z",
    "M 12.5,37 C 12.5,30.4 16.6,26.4 22.5,26.4 C 28.4,26.4 32.5,30.4 32.5,37 "
    "C 32.5,37 29.8,38.6 22.5,38.6 C 15.2,38.6 12.5,37 12.5,37 z",
    "M 12.6,31.2 C 12.1,28 9.2,27.6 9.2,30 C 9.2,32 11,32.8 12.6,33.2 z",
    "M 32.4,31.2 C 32.9,28 35.8,27.6 35.8,30 C 35.8,32 34,32.8 32.4,33.2 z",
]

CONTOURS = {"p": PION, "r": TOUR, "b": FOU, "n": CAVALIER, "q": DAME, "k": ROI}
CERCLES = {"q": (DAME_BOULES, DAME_RAYON)}

# Les petits details traces dans la couleur du CONTOUR, pas du remplissage.
YEUX = {"n": CAVALIER_OEIL}

# --------------------------------------------------------- lecture des contours

_COMMANDES = "MmLlHhVvCcSsQqTtZz"


def _decouper(d):
    """Transforme 'M 9,39 L 36,39 z' en une suite de lettres et de nombres."""
    elements = []
    i, n = 0, len(d)
    while i < n:
        c = d[i]
        if c in _COMMANDES:
            elements.append(c)
            i += 1
        elif c in " ,\t\r\n":
            i += 1
        else:
            j = i
            if d[j] in "+-":
                j += 1
            while j < n and (d[j].isdigit() or d[j] == "."):
                j += 1
            if j == i:
                i += 1
                continue
            elements.append(float(d[i:j]))
            i = j
    return elements


def _cubique(p0, p1, p2, p3, pas=20):
    points = []
    for k in range(1, pas + 1):
        t = k / float(pas)
        u = 1 - t
        points.append((
            u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
            u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1]))
    return points


def _quadratique(p0, p1, p2, pas=16):
    points = []
    for k in range(1, pas + 1):
        t = k / float(pas)
        u = 1 - t
        points.append((u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0],
                       u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1]))
    return points


def lire_contour(d):
    """Renvoie la liste des sous-contours (listes de points) d'un chemin."""
    elements = _decouper(d)
    contours, courant = [], []
    position = depart = (0.0, 0.0)
    controle = None
    commande = None
    i = 0
    while i < len(elements):
        if isinstance(elements[i], str):
            commande = elements[i]
            i += 1
            if commande in "Zz":
                if courant:
                    contours.append(courant)
                    courant = []
                position = depart
                controle = None
                continue
        if commande is None:
            i += 1
            continue
        relatif = commande.islower()
        lettre = commande.upper()

        def suivant():
            nonlocal i
            valeur = elements[i]
            i += 1
            return valeur

        if lettre == "M":
            x, y = suivant(), suivant()
            if relatif:
                x, y = position[0] + x, position[1] + y
            if courant:
                contours.append(courant)
            position = depart = (x, y)
            courant = [position]
            controle = None
            commande = "l" if relatif else "L"
        elif lettre == "L":
            x, y = suivant(), suivant()
            if relatif:
                x, y = position[0] + x, position[1] + y
            position = (x, y)
            courant.append(position)
            controle = None
        elif lettre == "H":
            x = suivant()
            if relatif:
                x += position[0]
            position = (x, position[1])
            courant.append(position)
            controle = None
        elif lettre == "V":
            y = suivant()
            if relatif:
                y += position[1]
            position = (position[0], y)
            courant.append(position)
            controle = None
        elif lettre == "C":
            x1, y1, x2, y2, x, y = (suivant() for _ in range(6))
            if relatif:
                x1, y1 = position[0] + x1, position[1] + y1
                x2, y2 = position[0] + x2, position[1] + y2
                x, y = position[0] + x, position[1] + y
            courant += _cubique(position, (x1, y1), (x2, y2), (x, y))
            controle = (x2, y2)
            position = (x, y)
        elif lettre == "S":
            x2, y2, x, y = (suivant() for _ in range(4))
            if relatif:
                x2, y2 = position[0] + x2, position[1] + y2
                x, y = position[0] + x, position[1] + y
            if controle:
                x1, y1 = 2 * position[0] - controle[0], 2 * position[1] - controle[1]
            else:
                x1, y1 = position
            courant += _cubique(position, (x1, y1), (x2, y2), (x, y))
            controle = (x2, y2)
            position = (x, y)
        elif lettre == "Q":
            x1, y1, x, y = (suivant() for _ in range(4))
            if relatif:
                x1, y1 = position[0] + x1, position[1] + y1
                x, y = position[0] + x, position[1] + y
            courant += _quadratique(position, (x1, y1), (x, y))
            controle = (x1, y1)
            position = (x, y)
        else:
            i += 1
    if courant:
        contours.append(courant)
    return contours


# ------------------------------------------------------------------ rendu

_cache = {}


def rendre_piece(symbole, taille, couleur_remplissage, couleur_contour,
                 epaisseur=1.4):
    """Dessine une piece et renvoie une Surface transparente carree.

    symbole : 'P' 'N' 'B' 'R' 'Q' 'K' pour les Blancs, minuscules pour les Noirs.
    Le resultat est mis en cache : le dessin n'est fait qu'une fois par taille.
    """
    cle = (symbole, int(taille), tuple(couleur_remplissage),
           tuple(couleur_contour), round(epaisseur, 2))
    if cle in _cache:
        return _cache[cle]

    lettre = symbole.lower()
    if lettre not in CONTOURS:
        return None

    taille = max(8, int(taille))
    grand = taille * SUR_ECHANTILLON
    echelle = grand / VIEWBOX
    surface = pygame.Surface((grand, grand), pygame.SRCALPHA)

    formes = []
    for chemin in CONTOURS[lettre]:
        formes.extend([(x * echelle, y * echelle) for x, y in contour]
                      for contour in lire_contour(chemin))
    cercles = []
    if lettre in CERCLES:
        centres, rayon = CERCLES[lettre]
        cercles = [((cx * echelle, cy * echelle), rayon * echelle)
                   for cx, cy in centres]

    trait = max(1, int(epaisseur * echelle))

    # 1. remplissage
    for forme in formes:
        if len(forme) > 2:
            pygame.draw.polygon(surface, couleur_remplissage, forme)
    for centre, rayon in cercles:
        pygame.draw.circle(surface, couleur_remplissage,
                           (int(centre[0]), int(centre[1])), int(rayon))
    # 2. contour
    for forme in formes:
        if len(forme) > 1:
            pygame.draw.lines(surface, couleur_contour, True, forme, trait)
    for centre, rayon in cercles:
        pygame.draw.circle(surface, couleur_contour,
                           (int(centre[0]), int(centre[1])), int(rayon), trait)
    # 3. les details du contour (l'oeil du cavalier)
    if lettre in YEUX:
        (ox, oy), rayon_oeil = YEUX[lettre]
        pygame.draw.circle(surface, couleur_contour,
                           (int(ox * echelle), int(oy * echelle)),
                           max(1, int(rayon_oeil * echelle)))

    try:
        rendu = pygame.transform.smoothscale(surface, (taille, taille))
    except (ValueError, pygame.error):
        rendu = pygame.transform.scale(surface, (taille, taille))
    _cache[cle] = rendu
    return rendu


def jeu_complet(taille, blanc_remplissage=(250, 250, 248),
                blanc_contour=(26, 24, 22), noir_remplissage=(44, 42, 40),
                noir_contour=(238, 236, 232), epaisseur=1.4):
    """Renvoie les douze pieces : {'P': Surface, ..., 'k': Surface}."""
    images = {}
    for lettre in "pnbrqk":
        images[lettre.upper()] = rendre_piece(lettre, taille, blanc_remplissage,
                                              blanc_contour, epaisseur)
        images[lettre] = rendre_piece(lettre, taille, noir_remplissage,
                                      noir_contour, epaisseur)
    return {k: v for k, v in images.items() if v is not None}


def vider_cache():
    _cache.clear()
