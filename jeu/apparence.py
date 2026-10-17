# apparence.py - V7 : NOUVEAU FICHIER
#
# Themes de plateau et jeux de pieces, comme la personnalisation de chess.com.
#
# POURQUOI :
# En V6 les couleurs des cases etaient ecrites en dur dans board_render, et les
# pieces venaient forcement du dossier assets (jeu Pokemon). Ici tout est
# regroupe : six themes de plateau, trois jeux de pieces, et les couleurs de
# surbrillance qui vont avec chaque theme. Le choix se fait dans l'ecran de
# personnalisation et se retient dans config.json.

import os

import pygame

import design
import pieces_vectorielles as vecto

# --------------------------------------------------------------- themes

THEMES = {
    "vert": {
        "nom": "Vert",
        "clair": (238, 238, 210), "sombre": (118, 150, 86),
        "bord": (58, 74, 44), "fond": (34, 38, 30), "panneau": (44, 50, 38),
        "texte": (233, 236, 226), "texte_discret": (150, 160, 140),
        "accent": (246, 246, 105),
        "dernier": (246, 246, 105, 130), "selection": (246, 246, 105, 175),
        "coup": (28, 34, 24, 110), "prise": (200, 60, 40, 160),
        "echec": (225, 60, 50, 180),
    },
    "marron": {
        "nom": "Marron",
        "clair": (240, 217, 181), "sombre": (181, 136, 99),
        "bord": (86, 62, 42), "fond": (36, 30, 24), "panneau": (52, 44, 35),
        "texte": (238, 231, 220), "texte_discret": (163, 152, 138),
        "accent": (255, 200, 90),
        "dernier": (255, 200, 70, 130), "selection": (255, 200, 70, 175),
        "coup": (40, 30, 18, 110), "prise": (200, 60, 40, 160),
        "echec": (225, 60, 50, 180),
    },
    "bleu": {
        "nom": "Bleu",
        "clair": (222, 227, 230), "sombre": (140, 162, 173),
        "bord": (70, 86, 96), "fond": (26, 32, 38), "panneau": (40, 48, 56),
        "texte": (231, 236, 240), "texte_discret": (146, 158, 168),
        "accent": (255, 214, 120),
        "dernier": (255, 214, 120, 130), "selection": (255, 214, 120, 175),
        "coup": (26, 36, 44, 110), "prise": (200, 70, 55, 160),
        "echec": (225, 70, 60, 180),
    },
    "gris": {
        "nom": "Gris",
        "clair": (220, 220, 220), "sombre": (150, 150, 150),
        "bord": (78, 78, 78), "fond": (28, 28, 30), "panneau": (44, 44, 47),
        "texte": (234, 234, 236), "texte_discret": (150, 150, 154),
        "accent": (255, 205, 100),
        "dernier": (255, 205, 100, 130), "selection": (255, 205, 100, 175),
        "coup": (34, 34, 36, 110), "prise": (200, 70, 55, 160),
        "echec": (225, 70, 60, 180),
    },
    "glace": {
        "nom": "Glace",
        "clair": (232, 238, 246), "sombre": (155, 175, 199),
        "bord": (84, 100, 122), "fond": (24, 30, 40), "panneau": (38, 46, 60),
        "texte": (232, 238, 246), "texte_discret": (145, 158, 176),
        "accent": (140, 210, 255),
        "dernier": (140, 210, 255, 130), "selection": (140, 210, 255, 175),
        "coup": (24, 40, 56, 110), "prise": (210, 80, 70, 160),
        "echec": (230, 80, 70, 180),
    },
    "nuit": {
        "nom": "Nuit",
        "clair": (124, 130, 145), "sombre": (72, 78, 92),
        "bord": (40, 44, 54), "fond": (18, 20, 26), "panneau": (30, 33, 42),
        "texte": (228, 231, 238), "texte_discret": (140, 146, 160),
        "accent": (170, 200, 255),
        "dernier": (170, 200, 255, 130), "selection": (170, 200, 255, 175),
        "coup": (18, 22, 30, 120), "prise": (215, 90, 80, 160),
        "echec": (235, 90, 80, 180),
    },
}
# ===========================================================================
# V8 : LES THEMES CONSTRUITS PAR LE SYSTEME DE DESIGN.
#
# Les six themes ci-dessus sont ceux de la v7 - ILS SONT CONSERVES, on peut
# toujours les choisir. Mais ils ont ete ecrits couleur par couleur, a la main,
# et ca se voit : chacun a son propre gris de fond, sa propre bordure, son
# propre gris de texte, sans rapport les uns avec les autres.
#
# Ceux de la V8 sont FABRIQUES : un damier + une couleur d'accent, poses sur le
# meme nuancier d'ardoise. Resultat, l'interface a exactement la meme tete quel
# que soit le plateau choisi - seul le damier et l'accent changent. C'est ce
# qu'on attend d'un logiciel qui a l'air fini.
#
# Le choix se fait maintenant en DEUX reglages independants (le plateau et
# l'accent), ce qui donne 6 x 6 = 36 combinaisons au lieu de 6 themes figes.
for _cle_plateau in design.ORDRE_PLATEAUX:
    THEMES[_cle_plateau] = design.construire_theme(design.ACCENT_PAR_DEFAUT,
                                                   _cle_plateau,
                                                   nom=design.PLATEAUX[
                                                       _cle_plateau]["nom"])

THEME_PAR_DEFAUT = design.PLATEAU_PAR_DEFAUT
# SickChess : seuls les damiers du systeme de design sont proposes. Les six de
# la v7 restent dans THEMES (un ancien config.json qui en nomme un marche
# toujours) mais ne sont plus listes : trop de choix voisins, et ils ne
# suivaient pas la direction artistique.
ORDRE_THEMES = list(design.ORDRE_PLATEAUX)
# Les anciens themes restent accessibles par leur nom ; les nouveaux sont en
# tete parce que ce sont eux qu'on propose d'abord.
ACCENT_ACTUEL = design.ACCENT_PAR_DEFAUT


def regler_accent(cle):
    """Change la couleur d'accent de TOUT le logiciel, d'un coup.

    Les six themes de la V8 sont refabriques avec le nouvel accent ; les six
    anciens n'en dependent pas et ne bougent pas.
    """
    global ACCENT_ACTUEL
    if cle not in design.ACCENTS:
        return ACCENT_ACTUEL
    ACCENT_ACTUEL = cle
    for cle_plateau in design.ORDRE_PLATEAUX:
        THEMES[cle_plateau] = design.construire_theme(
            cle, cle_plateau, nom=design.PLATEAUX[cle_plateau]["nom"])
    design.vider_le_cache()
    return ACCENT_ACTUEL


def accents_disponibles():
    return [(cle, design.ACCENTS[cle]["nom"]) for cle in design.ORDRE_ACCENTS]

# ------------------------------------------------------------ jeux de pieces

FICHIERS = {
    "P": "p", "N": "n", "B": "b", "R": "r", "Q": "q", "K": "k",
    "p": "pb", "n": "nb", "b": "bb", "r": "rb", "q": "qb", "k": "kb",
}

JEUX = {
    # SickChess : pieces originales, modelisees pour le jeu (outils/blender/).
    # "Relief" = modeles 3D rendus dans Blender ; "plat" = silhouettes 2D tirees
    # des memes profils. Douze PNG par jeu, meme cadrage pour toutes les pieces.
    "relief_prisme": {"nom": "Relief Prisme", "type": "image",
                      "dossier": ("assets", "pieces", "relief_prisme"), "extension": ".png"},
    "relief_arene": {"nom": "Relief Arène", "type": "image",
                     "dossier": ("assets", "pieces", "relief_arene"), "extension": ".png"},
    "relief_tournoi": {"nom": "Relief Tournoi", "type": "image",
                       "dossier": ("assets", "pieces", "relief_tournoi"), "extension": ".png"},
    "plat_arene": {"nom": "Arène", "type": "image",
                   "dossier": ("assets", "pieces", "plat_arene"), "extension": ".png"},
    "plat_tournoi": {"nom": "Tournoi", "type": "image",
                     "dossier": ("assets", "pieces", "plat_tournoi"), "extension": ".png"},
    "classique": {"nom": "Classique", "type": "vectoriel"},
    # Les jeux "bois" et "pokemon" de V8_TURBO_3000 sont retires (droits
    # d'auteur / origine inconnue).
}
JEU_PAR_DEFAUT = "plat_tournoi"      # choix de Julien (17/10) : "la version E est incroyable"
ORDRE_JEUX = ["plat_tournoi", "plat_arene", "relief_prisme", "relief_arene",
              "relief_tournoi", "classique"]


def _dossier_ressources():
    try:
        from asset_manager import dossier_ressources
        return dossier_ressources()
    except Exception:
        return os.getcwd()


_COMPLETS = {}


def _completer(base):
    """Ajoute a un ANCIEN theme les cles que la V8 attend.

    LES SIX THEMES DE LA V7 SONT CONSERVES, et ils n'avaient ni panneau_haut,
    ni trait, ni succes/danger : le code de la V8 aurait plante en les
    demandant. Plutot que d'aller les reecrire un par un - et de figer pour
    toujours des couleurs choisies a la main - on les COMPLETE ici, en
    derivant les cles manquantes de celles qui existent. Un theme de la V7
    reste donc utilisable, et il herite au passage de la profondeur de la V8.
    """
    if base.get("panneau_haut"):
        return base
    cle = (id(base), ACCENT_ACTUEL)
    if cle in _COMPLETS:
        return _COMPLETS[cle]
    complet = dict(base)
    # L'ACCENT EST UN REGLAGE GLOBAL, LE DAMIER N'EN DECIDE PAS.
    #
    # Les six themes de la v7 portaient chacun sa couleur vive : jaune pour le
    # vert, or pour le marron, bleu ciel pour la glace. Resultat, choisir
    # "damier marron" changeait aussi la couleur des titres et des boutons de
    # tout le logiciel - deux decisions dans un seul reglage. En V8 le damier
    # decide des CASES, l'accent decide du reste, et les douze damiers marchent
    # avec les six accents. C'est ce qui fait 72 combinaisons au lieu de 12.
    vif = design.ACCENTS.get(ACCENT_ACTUEL,
                             design.ACCENTS[design.ACCENT_PAR_DEFAUT])["vif"]
    complet["accent"] = vif
    complet["dernier"] = design.avec_alpha(vif, 92)
    complet["selection"] = design.avec_alpha(vif, 130)
    complet.setdefault("fond_haut", design.eclaircir(base["fond"], 0.05))
    complet.setdefault("panneau_haut", design.eclaircir(base["panneau"], 0.12))
    complet.setdefault("trait", base.get("bord", design.ARDOISE[700]))
    complet.setdefault("trait_fort", design.eclaircir(
        base.get("bord", design.ARDOISE[700]), 0.18))
    complet.setdefault("texte_faible", design.melanger(
        base.get("texte_discret", design.ARDOISE[400]), base["panneau"], 0.45))
    complet.setdefault("accent_doux", design.assombrir(base["accent"], 0.30))
    complet.setdefault("accent_voile", design.avec_alpha(base["accent"], 38))
    complet.setdefault("succes", design.SUCCES)
    complet.setdefault("attention", design.ATTENTION)
    complet.setdefault("danger", design.DANGER)
    complet.setdefault("info", design.INFO)
    _COMPLETS[cle] = complet
    return complet


def theme(cle=None):
    """Renvoie le dictionnaire de couleurs d'un theme, complet pour la V8."""
    return _completer(THEMES.get(cle or THEME_PAR_DEFAUT,
                                 THEMES[THEME_PAR_DEFAUT]))


def nom_theme(cle):
    return theme(cle)["nom"]


def nom_jeu(cle):
    return JEUX.get(cle, JEUX[JEU_PAR_DEFAUT])["nom"]


def jeu_disponible(cle):
    """Un jeu d'images n'est proposable que si ses douze fichiers existent."""
    infos = JEUX.get(cle)
    if not infos:
        return False
    if infos["type"] == "vectoriel":
        return True
    base = os.path.join(_dossier_ressources(), *infos["dossier"])
    return all(os.path.exists(os.path.join(base, nom + infos["extension"]))
               for nom in FICHIERS.values())


def jeux_disponibles():
    return [c for c in ORDRE_JEUX if jeu_disponible(c)]


def _detourer(surface):
    """Rend transparent le fond uni d'une image JPEG (pieces 'Bois')."""
    try:
        couleur_fond = surface.get_at((0, 0))[:3]
        tableau = pygame.PixelArray(surface)
        tableau.replace(couleur_fond, (255, 0, 255), 0.10)
        del tableau
        surface.set_colorkey((255, 0, 255))
        return surface.convert_alpha()
    except Exception as e:
        print("[APPARENCE] detourage impossible : %s" % e)
        return surface


def charger_jeu(cle, taille_case, epaisseur_contour=1.4):
    """Renvoie les douze images de pieces a la taille demandee.

    Retombe sur le jeu classique si les fichiers demandes sont absents.
    """
    taille = max(16, int(taille_case * 0.88))
    infos = JEUX.get(cle, JEUX[JEU_PAR_DEFAUT])
    if not jeu_disponible(cle) and jeu_disponible(JEU_PAR_DEFAUT):
        cle, infos = JEU_PAR_DEFAUT, JEUX[JEU_PAR_DEFAUT]

    if infos["type"] == "vectoriel" or not jeu_disponible(cle):
        if infos["type"] != "vectoriel":
            print("[APPARENCE] jeu '%s' incomplet, retour au jeu classique" % cle)
        return vecto.jeu_complet(taille, epaisseur=epaisseur_contour)

    base = os.path.join(_dossier_ressources(), *infos["dossier"])
    images = {}
    for symbole, nom in FICHIERS.items():
        chemin = os.path.join(base, nom + infos["extension"])
        try:
            image = pygame.image.load(chemin)
            image = image.convert_alpha() if not infos.get("detourer") else image.convert()
            if infos.get("detourer"):
                image = _detourer(image)
            images[symbole] = pygame.transform.smoothscale(image, (taille, taille))
        except Exception as e:
            print("[APPARENCE] %s illisible (%s)" % (chemin, e))
    if len(images) < 12:
        print("[APPARENCE] jeu '%s' incomplet, retour au jeu classique" % cle)
        return vecto.jeu_complet(taille, epaisseur=epaisseur_contour)
    return images


# ------------------------------------------------------- plateaux en matiere

_TEXTURES = {}


def damier_texture(theme_ou_cle, cote):
    """L'image d'un plateau en matiere (marbre, bois...) a la taille demandee.

    Renvoie None pour un damier uni, ou si l'image manque : l'appelant dessine
    alors les cases avec theme["clair"] / theme["sombre"], comme avant.
    La case en haut a gauche de l'image est claire, comme a8 vu des Blancs
    et h1 vu des Noirs : l'image sert telle quelle dans les deux sens.
    """
    t = theme(theme_ou_cle) if isinstance(theme_ou_cle, str) or theme_ou_cle is None \
        else theme_ou_cle
    nom = t.get("texture")
    if not nom or cote < 8:
        return None
    cle = (nom, int(cote))
    if cle in _TEXTURES:
        return _TEXTURES[cle]
    image = None
    chemin = os.path.join(_dossier_ressources(), "assets", "plateaux", nom)
    try:
        source = _TEXTURES.get((nom, "source"))
        if source is None:
            source = pygame.image.load(chemin)
            try:
                source = source.convert()
            except pygame.error:
                pass
            _TEXTURES[(nom, "source")] = source
        image = pygame.transform.smoothscale(source, (int(cote), int(cote)))
    except Exception as e:
        print("[APPARENCE] plateau %s illisible (%s)" % (chemin, e))
    _TEXTURES[cle] = image
    return image


def vider_cache():
    vecto.vider_cache()
    for cle in [c for c in _TEXTURES if c[1] != "source"]:
        del _TEXTURES[cle]


# ===========================================================================
# V8 : LES PREFERENCES D'APPARENCE, EN UN SEUL ENDROIT.
#
# POURQUOI CETTE COUCHE : chaque reglage etait lu par le fichier qui s'en
# servait, avec son propre defaut ecrit en dur. Resultat, "afficher les
# coordonnees" avait un defaut dans board_render et un autre dans
# plateau_simple, et ajouter un reglage voulait dire aller le brancher a la
# main partout. Ici il y a UNE table de defauts, UNE lecture du fichier, et
# tout le monde demande a la meme fonction.
#
# TOUT EST OPTIONNEL : un config.json sans aucune de ces cles donne exactement
# le comportement d'avant.
DEFAUTS = {
    "theme_plateau": THEME_PAR_DEFAUT,
    "accent": design.ACCENT_PAR_DEFAUT,
    "jeu_pieces": JEU_PAR_DEFAUT,
    "afficher_coordonnees": True,
    "surbrillance_dernier_coup": True,
    "points_coups_possibles": True,
    "vitesse_animation": 0.18,
    "duree_retournement": design.DUREE_RETOURNEMENT,
    "poussiere_fond": 1.0,          # 0 = aucune
    "coins_assombris": True,        # la vignette
    "police_livree": True,
    "echelle_interface": 1.0,
    "fleche_cavalier_en_L": True,
    "voix_puzzles": True,           # l'erreur expliquee a voix haute
    "timbre_voix": "naturelle",     # dix timbres, voir explication_puzzle.py
    "premouvement": True,
    "volume_sons": 0.6,
    "notation": "anglaise",         # ou "francaise" (Cf3, Fc4...) : notation.py
}

_PREFERENCES = None


def _lire_config():
    for dossier in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        chemin = os.path.join(dossier, "config.json")
        if os.path.exists(chemin):
            try:
                import json
                with open(chemin, "r", encoding="utf-8") as f:
                    contenu = json.load(f)
                # 04/09 : voir settings_screen.charger_config()
                return contenu if isinstance(contenu, dict) else {}
            except (ValueError, OSError):
                return {}
    return {}


def preferences(recharger=False):
    """Les reglages d'apparence, lus une fois puis gardes.

    'recharger' relit le fichier : c'est ce que fait l'ecran d'apparence quand
    on valide, pour que le changement se voie tout de suite sans redemarrer.
    """
    global _PREFERENCES
    if _PREFERENCES is None or recharger:
        config = _lire_config()
        _PREFERENCES = dict(DEFAUTS)
        for cle, defaut in DEFAUTS.items():
            if cle in config and config[cle] is not None:
                valeur = config[cle]
                try:
                    if isinstance(defaut, bool):
                        valeur = bool(valeur)
                    elif isinstance(defaut, float):
                        valeur = float(valeur)
                except (TypeError, ValueError):
                    continue
                _PREFERENCES[cle] = valeur
        appliquer(_PREFERENCES)
    return _PREFERENCES


def appliquer(reglages=None):
    """Met en oeuvre ce qui doit l'etre au moment ou on change de reglage.

    L'accent refabrique les six themes de la V8 ; les caches de dessin sont
    vides parce qu'ils contiennent des degrades aux anciennes couleurs.
    """
    reglages = reglages or preferences()
    regler_accent(reglages.get("accent", design.ACCENT_PAR_DEFAUT))
    design.DUREE_RETOURNEMENT = float(reglages.get("duree_retournement",
                                                   design.DUREE_RETOURNEMENT))
    try:
        import retournement
        retournement.DUREE = design.DUREE_RETOURNEMENT
    except Exception:
        pass
    vider_cache()
    return reglages


def reglage(cle, defaut=None):
    """Un reglage d'apparence, avec son defaut. Le raccourci de tout le jeu."""
    valeurs = preferences()
    return valeurs.get(cle, DEFAUTS.get(cle, defaut))
