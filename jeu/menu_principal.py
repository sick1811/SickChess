# menu_principal.py - SickChess : le menu d'accueil.
#
# Cinq entrees claires, comme prevu dans le plan Steam :
#   Jouer contre l'ordinateur / Jouer a deux / Problemes / Mes parties / Options
# Les fonctions pas encore integrees dans SickChess sont affichees grisees avec
# la mention "bientot" : elles reviendront une par une depuis V8_TURBO_3000.

import os

import pygame

import apparence
import design
import ui

ENTREES = [
    # (cle, libelle, disponible)
    ("stockfish", "Jouer contre l'ordinateur", True),
    ("hotseat", "Jouer à deux sur ce PC", True),
    ("en_ligne", "Jouer en ligne (Steam)", True),
    ("puzzles", "Problèmes", True),
    ("historique", "Mes parties et profil", True),
    ("options", "Options", True),
    ("quitter", "Quitter", True),
]


def _problemes_disponibles():
    try:
        import puzzles
        return puzzles.disponible()
    except Exception:
        return False


class MainMenu:
    def __init__(self, screen, version=""):
        self.screen = screen
        self.version = version
        self.boutons = [ui.Bouton((0, 0, 10, 10), libelle, cle, taille=19,
                                  actif=dispo)
                        for cle, libelle, dispo in ENTREES]
        # Les problemes ne sont proposes que si la base est la (puzzles/,
        # 223 Mo, livree a part : elle n'est pas sur GitHub).
        for bouton in self.boutons:
            if bouton.cle == "puzzles":
                bouton.actif = _problemes_disponibles()
                if not bouton.actif:
                    bouton.libelle = "Problèmes  (base absente)"
        self.detail_reprise = ""
        self.redimensionner(*screen.get_size())

    def annoncer_reprise(self, presente, detail=""):
        """Ajoute (ou retire) le bouton "Reprendre la partie" en tete du menu."""
        self.boutons = [b for b in self.boutons if b.cle != "reprendre"]
        self.detail_reprise = detail if presente else ""
        if presente:
            bouton = ui.Bouton((0, 0, 10, 10), "Reprendre la partie en cours",
                               "reprendre", taille=19)
            bouton.selectionne = True          # en couleur d'accent
            self.boutons.insert(0, bouton)
        self.redimensionner(*self.screen.get_size())

    def redimensionner(self, largeur, hauteur):
        """Menu « Vitrine » : colonne a gauche, rendu 3D du plateau a droite."""
        n = len(self.boutons)
        x = max(28, int(largeur * 0.065))
        largeur_bouton = max(240, min(400, int(largeur * 0.32)))
        ecart = max(4, int(hauteur * 0.008))
        y_mini = int(hauteur * 0.34)
        bas = hauteur - max(40, int(hauteur * 0.08))
        hauteur_bouton = max(30, min(50, (bas - y_mini - (n - 1) * ecart) // max(1, n)))
        y = y_mini
        for bouton in self.boutons:
            bouton.placer((x, y, largeur_bouton, hauteur_bouton))
            y += hauteur_bouton + ecart
        self._fond_cache = None

    def handle_event(self, event):
        """Renvoie la cle de l'entree choisie, ou None."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quitter"
        return ui.gerer_boutons(self.boutons, event)

    # ------------------------------------------------------------ dessin

    def _fond(self, largeur, hauteur, t):
        """Le rendu 3D (assets/menu/fond_menu.jpg) cadre pour remplir la
        fenetre, avec un voile sombre a gauche pour lire le menu. Calcule une
        fois par taille de fenetre : le menu reste fluide."""
        cle = (largeur, hauteur, t["fond"])
        if getattr(self, "_fond_cache", None) and self._fond_cache[0] == cle:
            return self._fond_cache[1]
        surface = pygame.Surface((largeur, hauteur))
        design.degrade_vertical(surface, surface.get_rect(),
                                design.eclaircir(t["fond"], 0.05),
                                design.assombrir(t["fond"], 0.10))
        image = _image_fond()
        if image is not None:
            iw, ih = image.get_size()
            echelle = max(largeur / iw, hauteur / ih)
            w, h = int(iw * echelle) + 1, int(ih * echelle) + 1
            cadree = pygame.transform.smoothscale(image, (w, h))
            # on cale l'image a droite : le plateau reste visible, la gauche
            # (vide dans le rendu) accueille le menu
            surface.blit(cadree, (largeur - w, (hauteur - h) // 2))
        voile = pygame.Surface((largeur, 1), pygame.SRCALPHA)
        r, g, b = t["fond"]
        for x in range(largeur):
            part = x / max(1, largeur)
            alpha = 236 if part < 0.30 else max(0, int(236 * (1 - (part - 0.30) / 0.30)))
            voile.set_at((x, 0), (r, g, b, alpha))
        surface.blit(pygame.transform.scale(voile, (largeur, hauteur)), (0, 0))
        self._fond_cache = (cle, surface)
        return surface

    def _entree(self, ecran, bouton, t):
        rect = bouton.rect
        if not bouton.actif:
            couleur = t.get("texte_faible", t["texte_discret"])
        elif bouton.selectionne:
            couleur = t["accent"]
        elif bouton.survol:
            couleur = t["texte"]
        else:
            couleur = t["texte_discret"]
        if bouton.actif and (bouton.survol or bouton.selectionne):
            voile = pygame.Surface(rect.size, pygame.SRCALPHA)
            voile.fill(design.avec_alpha(t["panneau_haut"] if "panneau_haut" in t
                                         else t["panneau"], 170))
            ecran.blit(voile, rect.topleft)
            pygame.draw.rect(ecran, t["accent"],
                             pygame.Rect(rect.x, rect.y + 6, 3, rect.height - 12))
        decalage = 18 if (bouton.survol or bouton.selectionne) and bouton.actif else 10
        taille = max(15, min(22, int(rect.height * 0.46)))
        y = rect.centery - ui.police(taille, True).get_height() // 2
        ui.texte(ecran, bouton.libelle.upper(), rect.x + decalage, y,
                 taille, couleur, gras=True, largeur_max=rect.width - decalage - 6)

    def draw(self):
        ecran = self.screen
        largeur, hauteur = ecran.get_size()
        t = apparence.theme()
        ecran.blit(self._fond(largeur, hauteur, t), (0, 0))

        # Titre : SICK en clair, CHESS en or
        x = self.boutons[0].rect.x if self.boutons else 40
        taille_titre = max(46, min(104, int(hauteur * 0.13)))
        y_titre = int(hauteur * 0.09)
        police = ui.police(taille_titre, True)
        sick = police.render("SICK", True, t["texte"])
        chess_ = police.render("CHESS", True, t["accent"])
        # Logo officiel (17/10) : l'icone cavalier sur damier, puis SICKCHESS
        icone = _icone(int(sick.get_height() * 1.05))
        if icone is not None:
            ecran.blit(icone, (x, y_titre + (sick.get_height() - icone.get_height()) // 2 + 2))
            x += icone.get_width() + int(sick.get_height() * 0.22)
        ecran.blit(sick, (x, y_titre))
        ecran.blit(chess_, (x + sick.get_width(), y_titre))
        ui.texte(ecran, "ENTRA\u00ceNE  \u00b7  ANALYSE  \u00b7  GAGNE", x + 4,
                 y_titre + sick.get_height() + 2, max(12, int(hauteur * 0.02)),
                 t["texte_discret"], mono=True)

        for bouton in self.boutons:
            self._entree(ecran, bouton, t)
        if self.detail_reprise and self.boutons and self.boutons[0].cle == "reprendre":
            haut = self.boutons[0].rect
            ui.texte(ecran, self.detail_reprise, haut.x + 10, haut.y - 20, 13,
                     t["texte_discret"], largeur_max=max(200, largeur // 2))

        if self.version:
            ui.texte(ecran, "version %s" % self.version, largeur - 14,
                     hauteur - 26, 13, t["texte_discret"], ancre="droite")


_IMAGE_FOND = []
_ICONE = {}


def _icone(cote):
    """L'icone du jeu (assets/icone.png) a la taille demandee ; None si absente."""
    if "source" not in _ICONE:
        try:
            from asset_manager import dossier_ressources
            racine = dossier_ressources()
        except Exception:
            racine = os.getcwd()
        try:
            _ICONE["source"] = pygame.image.load(
                os.path.join(racine, "assets", "icone.png")).convert_alpha()
        except Exception:
            _ICONE["source"] = None
    if _ICONE["source"] is None or cote < 8:
        return None
    if cote not in _ICONE:
        _ICONE[cote] = pygame.transform.smoothscale(_ICONE["source"], (cote, cote))
    return _ICONE[cote]


def _image_fond():
    """Charge une seule fois le rendu du menu ; None s'il manque."""
    if not _IMAGE_FOND:
        image = None
        try:
            from asset_manager import dossier_ressources
            racine = dossier_ressources()
        except Exception:
            racine = os.getcwd()
        chemin = os.path.join(racine, "assets", "menu", "fond_menu.jpg")
        try:
            image = pygame.image.load(chemin).convert()
        except Exception as e:
            print("[MENU] fond %s absent (%s)" % (chemin, e))
        _IMAGE_FOND.append(image)
    return _IMAGE_FOND[0]
