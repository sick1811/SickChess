# design.py - V8 : NOUVEAU FICHIER
#
# LE SYSTEME DE DESIGN DE LA VERSION 8 (ta demande : "refais une version 8 ultra
# propre avec tout, design surtout").
#
# POURQUOI UN FICHIER POUR CA, ET PAS DES COULEURS DANS CHAQUE ECRAN :
#
#   En v7.2, chaque ecran choisissait ses marges, ses rayons d'angle et ses
#   tailles de texte dans son coin. Le scan du 03/09 l'a montre noir sur blanc :
#   MARGE valait 18 dans layout.py et 16 dans replay_screen.py, FOND et TEXTE
#   avaient trois valeurs differentes selon le fichier. Rien ne plantait - c'est
#   pire : ca donnait une interface qui ne tombe jamais tout a fait juste, et
#   dont on ne sait pas dire pourquoi.
#
#   Ici il y a UN endroit ou sont ecrits : les couleurs, les espacements, les
#   tailles de texte, les rayons d'angle. Tout le reste s'y refere. Changer
#   l'accent de tout le logiciel, c'est changer une ligne.
#
# LES TROIS REGLES DU STYLE "SOMBRE MODERNE" (ton choix) :
#
#   1. UNE SEULE COULEUR VIVE. Le fond, les panneaux et les bordures sont des
#      gris ardoise ; l'accent ne sert qu'a ce qui compte (le titre, la valeur
#      qu'on regarde, le bouton principal). Une interface ou tout est colore est
#      une interface ou rien ne ressort.
#
#   2. LES ECARTS SE LISENT. Les gris sont espaces regulierement (chaque cran du
#      nuancier est un vrai pas visible), et les espacements suivent une echelle
#      de 4 en 4. Deux elements sont soit clairement colles, soit clairement
#      separes - jamais "presque".
#
#   3. PAS DE FAUX RELIEF. Ni biseaux, ni degrades, ni ombres portees lourdes.
#      La profondeur vient du fond : plus une surface est HAUTE dans la pile,
#      plus elle est CLAIRE. C'est tout, et ca suffit.
#
# AUCUNE FONCTION SUPPRIMEE : ce fichier n'existait pas. apparence.py garde ses
# six themes d'origine, wood_button garde son rendu en bois.

import pygame

# ---------------------------------------------------------------- le nuancier
#
# L'ARDOISE, du plus sombre au plus clair. Chaque cran est un pas visible : on
# peut poser deux surfaces voisines et voir la limite sans bordure.
ARDOISE = {
    # SickChess - direction artistique « Onyx & Or » (choix de Julien, 16/10) :
    # des noirs d'onyx a peine chauds au lieu des gris bleutes de la V8.
    950: (11, 11, 12),      # le fond de la fenetre
    900: (17, 17, 19),      # les grandes zones
    850: (24, 24, 27),      # les panneaux
    800: (33, 33, 37),      # les panneaux poses SUR un panneau
    700: (48, 47, 52),      # les bordures
    600: (72, 70, 74),      # les bordures qui doivent se voir
    500: (112, 108, 104),   # le texte secondaire sombre
    400: (152, 146, 138),   # le texte secondaire
    300: (192, 186, 176),   # le texte courant sur fond clair
    200: (222, 217, 208),   # les cases claires du plateau
    100: (243, 240, 232),   # le texte principal
}

# LES ACCENTS. Un seul est actif a la fois - c'est le point 1 des trois regles.
# Ils sont choisis pour rester lisibles sur ARDOISE[850] : un accent qu'il faut
# plisser les yeux pour lire n'est pas un accent, c'est une decoration.
ACCENTS = {
    "or":     {"nom": "Or",     "vif": (214, 176, 74),  "doux": (150, 120, 48)},
    "vert":   {"nom": "Vert",   "vif": (122, 178, 62),  "doux": (86, 128, 44)},
    "ambre":  {"nom": "Ambre",  "vif": (232, 176, 74),  "doux": (168, 124, 46)},
    "bleu":   {"nom": "Bleu",   "vif": (96, 165, 232),  "doux": (58, 112, 168)},
    "violet": {"nom": "Violet", "vif": (158, 138, 235), "doux": (108, 92, 176)},
    "rouge":  {"nom": "Rouge",  "vif": (226, 106, 96),  "doux": (162, 70, 62)},
    "menthe": {"nom": "Menthe", "vif": (86, 196, 168),  "doux": (52, 138, 118)},
}
ACCENT_PAR_DEFAUT = "or"
ORDRE_ACCENTS = ["or", "vert", "ambre", "bleu", "violet", "rouge", "menthe"]

# LES COULEURS DE SENS. Elles ne changent JAMAIS avec l'accent : le rouge d'une
# gaffe doit vouloir dire "gaffe" quel que soit le reglage.
SUCCES = (122, 178, 62)
ATTENTION = (232, 176, 74)
DANGER = (222, 82, 74)
INFO = (96, 165, 232)

# ------------------------------------------------------------- les plateaux
#
# Les cases. Le contraste entre clair et sombre est volontairement MODERE : sur
# un fond d'ecran sombre, un damier tres contraste fatigue au bout d'une heure.
PLATEAUX = {
    # SickChess : les unis d'abord (le plus lisible en competition), puis les
    # matieres. Une matiere = une image 1024 x 1024 dans assets/plateaux/ ; ses
    # couleurs "clair"/"sombre" sont la teinte moyenne, utilisee pour les
    # coordonnees, les pastilles du menu Options, et si l'image manque.
    "tournoi": {"nom": "Tournoi", "clair": (236, 237, 209),
                "sombre": (120, 150, 90)},
    "marbre_uni": {"nom": "Marbre", "clair": (235, 232, 227),
                   "sombre": (159, 154, 146)},
    "ardoise": {"nom": "Ardoise", "clair": (214, 219, 227),
                "sombre": (114, 130, 150)},
    "foret":   {"nom": "Forêt",   "clair": (233, 237, 208),
                "sombre": (112, 146, 84)},
    "noyer":   {"nom": "Noyer",   "clair": (232, 214, 186),
                "sombre": (156, 118, 82)},
    "encre":   {"nom": "Encre",   "clair": (196, 204, 216),
                "sombre": (84, 96, 116)},
    "sable":   {"nom": "Sable",   "clair": (231, 223, 205),
                "sombre": (168, 152, 124)},
    "acier":   {"nom": "Acier",   "clair": (206, 214, 220),
                "sombre": (122, 140, 152)},
    "mat_marbre":  {"nom": "Marbre veiné", "clair": (226, 222, 214),
                    "sombre": (156, 150, 141), "texture": "plateau_marbre.png"},
    "mat_onyx_or": {"nom": "Onyx et or", "clair": (213, 205, 189),
                    "sombre": (36, 34, 33), "texture": "plateau_onyx_or.png"},
    "mat_noyer":   {"nom": "Noyer et érable", "clair": (222, 192, 150),
                    "sombre": (104, 68, 40), "texture": "plateau_noyer.png"},
}
PLATEAU_PAR_DEFAUT = "tournoi"
ORDRE_PLATEAUX = ["tournoi", "marbre_uni", "ardoise", "foret", "noyer", "encre",
                  "sable", "acier", "mat_marbre", "mat_onyx_or", "mat_noyer"]

# La duree du retournement de l'echiquier, en secondes. Ici parce que c'est un
# reglage d'apparence comme un autre, et que l'ecran d'apparence doit pouvoir la
# changer sans importer retournement.py.
DUREE_RETOURNEMENT = 0.32

# ------------------------------------------------------------- les mesures
#
# UNE SEULE ECHELLE D'ESPACEMENT, de 4 en 4. Toute marge du logiciel est l'une
# de ces valeurs - jamais 13, jamais 17.
ESPACE = {"xs": 4, "s": 8, "m": 12, "l": 16, "xl": 24, "xxl": 32, "xxxl": 48}

# LES RAYONS D'ANGLE. Trois valeurs, pas trente.
RAYON = {"petit": 6, "moyen": 10, "grand": 14, "rond": 999}

# LES TAILLES DE TEXTE. Une gamme qui monte d'environ 20 % a chaque cran : deux
# tailles voisines doivent se distinguer, sinon la hierarchie ne se lit pas.
TYPO = {
    "micro": 10, "petit": 12, "corps": 14, "moyen": 17,
    "grand": 21, "titre": 26, "affiche": 34, "geant": 44,
}

# L'EPAISSEUR DES TRAITS. Un seul pixel, sauf pour marquer ce qui est actif.
TRAIT = 1
TRAIT_ACTIF = 2


# ------------------------------------------------------------- les melanges

def melanger(couleur_a, couleur_b, part):
    """Entre deux couleurs. part=0 -> a, part=1 -> b."""
    part = max(0.0, min(1.0, float(part)))
    return tuple(int(round(a + (b - a) * part))
                 for a, b in zip(couleur_a[:3], couleur_b[:3]))


def eclaircir(couleur, part=0.12):
    return melanger(couleur, (255, 255, 255), part)


def assombrir(couleur, part=0.12):
    return melanger(couleur, (0, 0, 0), part)


def avec_alpha(couleur, alpha):
    return tuple(couleur[:3]) + (max(0, min(255, int(alpha))),)


def lisible_sur(fond, clair=None, sombre=None):
    """Le texte qui se lit sur ce fond : clair sur sombre, sombre sur clair.

    Luminance perceptuelle (les yeux voient le vert bien plus que le bleu) -
    c'est ce qui evite du texte gris sur du jaune.
    """
    r, v, b = fond[:3]
    luminance = (0.299 * r + 0.587 * v + 0.114 * b) / 255.0
    return (sombre or ARDOISE[950]) if luminance > 0.55 else (clair or ARDOISE[100])


# ------------------------------------------------------------- le theme

def construire_theme(accent=ACCENT_PAR_DEFAUT, plateau=PLATEAU_PAR_DEFAUT,
                     nom=None):
    """Un theme complet, aux memes cles que ceux d'apparence.py.

    C'EST VOLONTAIRE QUE LES CLES SOIENT LES MEMES : tous les ecrans lisent
    deja t["fond"], t["panneau"], t["accent"]... Construire un theme neuf avec
    d'autres noms aurait oblige a reecrire quatre-vingts fichiers pour changer
    trois couleurs. Les cles ajoutees (panneau_haut, succes, danger...) sont
    optionnelles : un ecran qui ne les connait pas continue de marcher.
    """
    couleurs = ACCENTS.get(accent, ACCENTS[ACCENT_PAR_DEFAUT])
    cases = PLATEAUX.get(plateau, PLATEAUX[PLATEAU_PAR_DEFAUT])
    vif = couleurs["vif"]
    return {
        "nom": nom or "%s %s" % (cases["nom"], couleurs["nom"].lower()),
        "accent_cle": accent,
        "plateau_cle": plateau,

        # Le damier.
        "clair": cases["clair"],
        "sombre": cases["sombre"],
        "texture": cases.get("texture"),
        "bord": ARDOISE[700],

        # Les surfaces, de la plus basse a la plus haute.
        "fond": ARDOISE[950],
        "fond_haut": ARDOISE[900],
        "panneau": ARDOISE[850],
        "panneau_haut": ARDOISE[800],
        "trait": ARDOISE[700],
        "trait_fort": ARDOISE[600],

        # Le texte.
        "texte": ARDOISE[100],
        "texte_discret": ARDOISE[400],
        "texte_faible": ARDOISE[500],

        # L'accent, et lui seul.
        "accent": vif,
        "accent_doux": couleurs["doux"],
        "accent_voile": avec_alpha(vif, 38),

        # Le sens.
        "succes": SUCCES, "attention": ATTENTION, "danger": DANGER,
        "info": INFO,

        # Les voiles du plateau. Ils sont TRANSLUCIDES : poses sur une case
        # claire ou sombre, ils doivent rester lisibles dans les deux cas.
        "dernier": avec_alpha(vif, 92),
        "selection": avec_alpha(vif, 130),
        "coup": avec_alpha(ARDOISE[950], 96),
        "prise": avec_alpha(DANGER, 120),
        "echec": avec_alpha(DANGER, 165),
    }


# -------------------------------------------------------------- les briques
#
# Les quelques dessins qu'on refait partout. Les avoir ici, c'est la garantie
# qu'une carte a la meme tete dans le menu, dans les puzzles et dans le replay.

def carte(surface, rect, theme, haute=False, bordure=True, rayon=None,
          survol=False):
    """Une surface posee sur le fond. La brique de base de toute l'interface.

    'haute' : la carte est posee SUR une autre carte, donc plus claire.
    'survol' : la souris est dessus - le trait s'eclaire, rien ne bouge.
    """
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return rect
    rayon = RAYON["moyen"] if rayon is None else rayon
    fond = theme.get("panneau_haut" if haute else "panneau", ARDOISE[850])
    pygame.draw.rect(surface, fond, rect, border_radius=rayon)
    if bordure:
        trait = theme.get("accent") if survol else theme.get("trait",
                                                             ARDOISE[700])
        pygame.draw.rect(surface, trait, rect,
                         TRAIT_ACTIF if survol else TRAIT, border_radius=rayon)
    return rect


def bandeau(surface, rect, theme, couleur=None, alpha=38, rayon=None):
    """Un aplat translucide : la ligne selectionnee, la zone mise en avant."""
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return rect
    rayon = RAYON["petit"] if rayon is None else rayon
    calque = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(calque, avec_alpha(couleur or theme.get("accent"), alpha),
                     calque.get_rect(), border_radius=rayon)
    surface.blit(calque, rect.topleft)
    return rect


def filet(surface, x, y, largeur, theme, epaisseur=TRAIT):
    """Un trait de separation. Discret : il separe, il ne decore pas."""
    pygame.draw.rect(surface, theme.get("trait", ARDOISE[700]),
                     pygame.Rect(int(x), int(y), int(largeur),
                                 int(epaisseur)))


def jauge(surface, rect, part, theme, couleur=None, rayon=None):
    """Une barre de progression. part va de 0 a 1."""
    rect = pygame.Rect(rect)
    rayon = RAYON["rond"] if rayon is None else rayon
    rayon = min(rayon, rect.height // 2)
    pygame.draw.rect(surface, theme.get("trait", ARDOISE[700]), rect,
                     border_radius=rayon)
    part = max(0.0, min(1.0, float(part)))
    if part <= 0:
        return rect
    plein = pygame.Rect(rect.x, rect.y, max(rect.height, int(rect.width * part)),
                        rect.height)
    pygame.draw.rect(surface, couleur or theme.get("accent"), plein,
                     border_radius=rayon)
    return rect


def puce(surface, centre, rayon, couleur):
    """Un rond plein. Etat, indicateur, point de liste."""
    pygame.draw.circle(surface, couleur, (int(centre[0]), int(centre[1])),
                       int(rayon))


def etiquette(surface, rect, theme, couleur=None, rayon=None):
    """Le fond d'une petite etiquette de texte (un mode, un statut)."""
    rect = pygame.Rect(rect)
    rayon = RAYON["rond"] if rayon is None else rayon
    rayon = min(rayon, rect.height // 2)
    couleur = couleur or theme.get("accent")
    calque = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(calque, avec_alpha(couleur, 46), calque.get_rect(),
                     border_radius=rayon)
    pygame.draw.rect(calque, avec_alpha(couleur, 150), calque.get_rect(),
                     TRAIT, border_radius=rayon)
    surface.blit(calque, rect.topleft)
    return rect


def echelle(surface_ou_taille, reference=1280.0):
    """Combien il faut multiplier les mesures pour cette fenetre.

    Bornee : sous 0,8 le texte devient illisible, au-dela de 1,6 l'interface
    devient un jouet.
    """
    try:
        largeur = surface_ou_taille.get_size()[0]
    except AttributeError:
        largeur = float(surface_ou_taille)
    return max(0.8, min(1.6, largeur / reference))


def mesure(cle, ech=1.0):
    """Un espacement de l'echelle, ajuste a la taille de la fenetre."""
    return max(1, int(round(ESPACE.get(cle, cle if isinstance(cle, int) else 8)
                            * ech)))


def taille_texte(cle, ech=1.0):
    """Une taille de texte de la gamme, ajustee a la fenetre."""
    return max(9, int(round(TYPO.get(cle, cle if isinstance(cle, int) else 14)
                            * ech)))


# ===========================================================================
# LA COUCHE "JEU DU COMMERCE" (ta demande : "vraiment un truc joli, un design
# digne d'un jeu a 50 euros").
#
# CE QUI SEPARE UNE INTERFACE PLATE D'UNE INTERFACE CHERE, ET CE N'EST PAS LA
# COULEUR :
#
#   1. LA LUMIERE VIENT D'EN HAUT. Toute surface est un degre plus claire en
#      haut qu'en bas, et porte un liset clair d'un pixel sur son arete
#      superieure. C'est ce qui donne la matiere - pas les biseaux.
#
#   2. LES OMBRES SONT LARGES ET FAIBLES. Une ombre nette et noire fait
#      "annees 2000". Une ombre etalee sur vingt pixels a douze pour cent
#      d'opacite fait "objet pose sur une table".
#
#   3. RIEN NE SAUTE. Le survol eclaire et fait monter de deux pixels, en
#      douceur. Ce sont ces deux pixels qui font qu'un bouton semble reel.
#
#   4. UNE LUEUR, PAS UN CONTOUR. L'element actif diffuse sa couleur autour de
#      lui au lieu d'etre cercle d'un trait epais.
#
# TOUT EST MIS EN CACHE. Une ombre, c'est une vingtaine de rectangles empiles :
# la recalculer soixante fois par seconde couterait plus cher que le jeu. Elles
# sont fabriquees une fois par taille et gardees.
# ===========================================================================

_CACHE_OMBRES = {}
_CACHE_DEGRADES = {}
_CACHE_LUEURS = {}
_CACHE_VIGNETTES = {}
CACHE_MAXIMUM = 160


def _ranger(cache, cle, surface):
    if len(cache) > CACHE_MAXIMUM:
        cache.clear()
    cache[cle] = surface
    return surface


def ombre_douce(surface, rect, rayon=None, force=64, etalement=14,
                decalage=5):
    """L'ombre portee d'une carte : large, faible, decalee vers le bas.

    Fabriquee en empilant des rectangles arrondis de plus en plus opaques.
    C'est l'approximation d'un flou gaussien qu'on peut se permettre sans
    bibliotheque d'images - et a l'oeil, sur un fond sombre, la difference ne
    se voit pas.
    """
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return rect
    rayon = RAYON["moyen"] if rayon is None else rayon
    cle = (rect.width, rect.height, rayon, force, etalement)
    calque = _CACHE_OMBRES.get(cle)
    if calque is None:
        calque = pygame.Surface((rect.width + 2 * etalement,
                                 rect.height + 2 * etalement), pygame.SRCALPHA)
        couches = max(3, etalement)
        for i in range(couches, 0, -1):
            part = i / float(couches)
            marge = int(etalement * part)
            alpha = int(force * (1.0 - part) ** 2 / couches * 3.0)
            if alpha <= 0:
                continue
            pygame.draw.rect(
                calque, (0, 0, 0, alpha),
                pygame.Rect(etalement - marge, etalement - marge,
                            rect.width + 2 * marge, rect.height + 2 * marge),
                border_radius=rayon + marge)
        calque = _ranger(_CACHE_OMBRES, cle, calque)
    surface.blit(calque, (rect.x - etalement, rect.y - etalement + decalage))
    return rect


def degrade_vertical(surface, rect, haut, bas, rayon=None):
    """Un aplat qui s'assombrit vers le bas : la lumiere vient d'en haut."""
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return rect
    rayon = RAYON["moyen"] if rayon is None else rayon
    cle = (rect.width, rect.height, tuple(haut[:3]), tuple(bas[:3]), rayon)
    calque = _CACHE_DEGRADES.get(cle)
    if calque is None:
        # UNE LIGNE PAR RANGEE, puis un masque arrondi. Premiere version : un
        # ruban d'un pixel de large peint au pixel pres puis etire. Ca marchait,
        # mais ca demandait set_at() et smoothscale() - deux choses de plus a
        # supporter, et le banc de test s'y est casse les dents. Des lignes
        # horizontales font le meme degrade avec la seule primitive que tout le
        # monde a.
        calque = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        derniere = max(1.0, rect.height - 1.0)
        for y in range(rect.height):
            pygame.draw.line(calque, melanger(haut, bas, y / derniere),
                             (0, y), (rect.width - 1, y))
        masque = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(masque, (255, 255, 255, 255), masque.get_rect(),
                         border_radius=rayon)
        calque.blit(masque, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        calque = _ranger(_CACHE_DEGRADES, cle, calque)
    surface.blit(calque, rect.topleft)
    return rect


def lueur(surface, rect, couleur, rayon=None, force=70, etalement=16):
    """Le halo colore d'un element actif. Remplace le gros contour."""
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return rect
    rayon = RAYON["moyen"] if rayon is None else rayon
    cle = (rect.width, rect.height, tuple(couleur[:3]), rayon, force, etalement)
    calque = _CACHE_LUEURS.get(cle)
    if calque is None:
        calque = pygame.Surface((rect.width + 2 * etalement,
                                 rect.height + 2 * etalement), pygame.SRCALPHA)
        couches = max(3, etalement // 2)
        for i in range(couches, 0, -1):
            part = i / float(couches)
            marge = int(etalement * part)
            alpha = int(force * (1.0 - part) / couches * 2.2)
            if alpha <= 0:
                continue
            pygame.draw.rect(
                calque, avec_alpha(couleur, alpha),
                pygame.Rect(etalement - marge, etalement - marge,
                            rect.width + 2 * marge, rect.height + 2 * marge),
                border_radius=rayon + marge)
        calque = _ranger(_CACHE_LUEURS, cle, calque)
    surface.blit(calque, (rect.x - etalement, rect.y - etalement))
    return rect


def liset(surface, rect, couleur, rayon=None, alpha=44):
    """Le trait clair d'un pixel sur l'arete du haut. Regle numero 1."""
    rect = pygame.Rect(rect)
    rayon = RAYON["moyen"] if rayon is None else rayon
    if rect.width <= 2 * rayon or rect.height < 3:
        return rect
    calque = pygame.Surface((rect.width - 2 * rayon, 1), pygame.SRCALPHA)
    calque.fill(avec_alpha(couleur, alpha))
    surface.blit(calque, (rect.x + rayon, rect.y + 1))
    return rect


def panneau(surface, rect, theme, haute=False, rayon=None, ombre=True,
            survol=False, actif=False, bordure=True):
    """LA carte de la version 8 : degrade, liset, bordure fine, ombre portee.

    C'est la brique qu'on voit partout - menu, panneaux de jeu, puzzles. Elle
    remplace le simple rectangle plat de la v7.2, et c'est elle qui fait la
    difference entre "une fenetre" et "un jeu".
    """
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return rect
    rayon = RAYON["grand"] if rayon is None else rayon
    base = theme.get("panneau_haut" if haute else "panneau", ARDOISE[850])
    if ombre:
        ombre_douce(surface, rect, rayon)
    if actif:
        lueur(surface, rect, theme.get("accent"), rayon, force=58)
    degrade_vertical(surface, rect, eclaircir(base, 0.06), assombrir(base, 0.05),
                     rayon)
    liset(surface, rect, (255, 255, 255), rayon, 40 if not survol else 60)
    if bordure:
        trait = theme.get("accent") if (survol or actif) \
            else theme.get("trait", ARDOISE[700])
        pygame.draw.rect(surface, trait, rect,
                         TRAIT_ACTIF if (survol or actif) else TRAIT,
                         border_radius=rayon)
    return rect


def vignette(surface, force=110):
    """Les coins de l'ecran assombris. Le regard va au centre tout seul.

    Un demi-pourcent de travail pour un effet que tout jeu du commerce a, et
    dont personne ne remarque la presence - seulement l'absence.
    """
    taille = surface.get_size()
    calque = _CACHE_VIGNETTES.get((taille, force))
    if calque is None:
        largeur, hauteur = taille
        calque = pygame.Surface(taille, pygame.SRCALPHA)
        couches = 22
        for i in range(couches):
            part = i / float(couches)
            marge_x = int(largeur * 0.5 * part)
            marge_y = int(hauteur * 0.5 * part)
            alpha = int(force * part ** 3 / couches * 6.0)
            if alpha <= 0:
                continue
            pygame.draw.rect(
                calque, (0, 0, 0, alpha),
                pygame.Rect(marge_x, marge_y, largeur - 2 * marge_x,
                            hauteur - 2 * marge_y),
                max(1, int(min(largeur, hauteur) * 0.5 / couches) + 1))
        calque = _ranger(_CACHE_VIGNETTES, (taille, force), calque)
    surface.blit(calque, (0, 0))


def cadre_du_plateau(surface, rect, theme, epaisseur=None):
    """Le cadre de l'echiquier : un liser sombre, un filet clair, une ombre.

    Sans lui, le damier est un carre pose sur un fond. Avec, c'est un objet.
    """
    rect = pygame.Rect(rect)
    epaisseur = max(3, int(epaisseur or 6))
    exterieur = rect.inflate(epaisseur * 2, epaisseur * 2)
    ombre_douce(surface, exterieur, RAYON["petit"], force=90, etalement=18,
                decalage=7)
    degrade_vertical(surface, exterieur, eclaircir(theme.get("trait_fort",
                                                            ARDOISE[600]), 0.10),
                     assombrir(theme.get("trait", ARDOISE[700]), 0.25),
                     RAYON["petit"])
    pygame.draw.rect(surface, assombrir(theme.get("fond", ARDOISE[950]), 0.35),
                     exterieur, 1, border_radius=RAYON["petit"])
    pygame.draw.rect(surface, avec_alpha(ARDOISE[950], 200), rect, 1)
    return exterieur


def vider_le_cache():
    """A appeler quand le theme change : les couleurs en cache sont perimees."""
    for cache in (_CACHE_OMBRES, _CACHE_DEGRADES, _CACHE_LUEURS,
                  _CACHE_VIGNETTES):
        cache.clear()
