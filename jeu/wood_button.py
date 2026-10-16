# wood_button.py - V7.1 : le bouton bois du menu
#
# CE QUI CHANGE :
#   1. L'image de bois n'etait mise a l'echelle qu'a la creation du bouton.
#      Des que la fenetre changeait de taille, le rectangle bougeait mais pas
#      l'image : le bois debordait ou laissait un trou. Elle est maintenant
#      remise a l'echelle des que la taille du bouton change.
#   2. Le libelle etait ecrit en taille 22 fixe : "CONTRE UN AMI, SUR CE PC"
#      depassait du bouton sur une petite fenetre. Il est maintenant mesure et
#      retreci pour tenir, toujours centre.
#   3. L'image est cherchee avec chemin_ressource : elle est donc trouvee aussi
#      dans l'executable compile.
#
# V7.2 - BOUTONS PLATS QUI S'ENFONCENT (ta demande : "enleve les png des
# boutons, utilise des boutons comme dans le menu en ligne, mais avec un
# surpassement qui s'enfonce").
#
# L'image wood_button.png n'est PLUS utilisee par defaut. Le bouton est
# maintenant dessine : un socle sombre, et par-dessus une plaque aux couleurs du
# theme - exactement les memes que les panneaux de l'ecran RESEAU.
#
# L'ENFONCEMENT : au survol, la plaque DESCEND dans son socle de quelques
# pixels, et le socle apparait en haut comme le bord d'un trou. Au clic, elle
# descend encore. C'est ce qui donne la sensation de presser un vrai bouton,
# la ou l'ancienne version faisait FLOTTER le bouton vers le haut.
#
# RIEN N'EST SUPPRIME : _image_bois() existe toujours, et il suffit de mettre
# UTILISER_LE_BOIS = True pour retrouver exactement l'ancien rendu.
#
# AUCUNE FONCTION SUPPRIMEE : __init__, update, handle_event et draw sont
# conservees, avec la meme signature.

import math
import os

import pygame

import design

import apparence
import ui

# Mets True pour revenir aux boutons en bois de la V7.1.
UTILISER_LE_BOIS = False

# De combien la plaque descend dans son socle.
ENFONCEMENT_SURVOL = 3
ENFONCEMENT_CLIC = 5

_IMAGE_SOURCE = None
_IMAGE_CHERCHEE = False


def _image_bois():
    """Charge l'image du bois une seule fois pour tous les boutons."""
    global _IMAGE_SOURCE, _IMAGE_CHERCHEE
    if _IMAGE_CHERCHEE:
        return _IMAGE_SOURCE
    _IMAGE_CHERCHEE = True
    chemins = [os.path.join("assets", "wood_button.png")]
    try:
        from asset_manager import chemin_ressource
        chemins.insert(0, chemin_ressource("assets", "wood_button.png"))
    except Exception:
        pass
    for chemin in chemins:
        if chemin and os.path.exists(chemin):
            try:
                _IMAGE_SOURCE = pygame.image.load(chemin).convert_alpha()
                return _IMAGE_SOURCE
            except Exception:
                continue
    return None


class WoodButton:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False
        self.pressed = False
        # V8 : le bouton principal est rempli a la couleur
        # d'accent. Un seul par ecran, sinon plus rien ne ressort.
        self.principal = False
        self.float_offset = 0.0
        self.font = None                 # conserve pour compatibilite
        self.source = _image_bois()
        self.image = None
        self._taille_image = None

    def _preparer_image(self):
        taille = (max(1, self.rect.width), max(1, self.rect.height))
        if self.source is None:
            self.image = None
            return
        if self._taille_image != taille:
            self.image = pygame.transform.smoothscale(self.source, taille)
            self._taille_image = taille

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        # float_offset servait a faire FLOTTER le bouton vers le haut au survol.
        # En V7.2 le bouton s'enfonce (voir _dessiner_plat), donc il reste a
        # zero - mais on le calcule quand meme pour le rendu en bois, qui est
        # conserve et que UTILISER_LE_BOIS peut rallumer.
        if self.hovered and UTILISER_LE_BOIS:
            self.float_offset = math.sin(pygame.time.get_ticks() / 300.0) * 4
        else:
            self.float_offset = 0.0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pressed = False
        return False

    def draw(self, screen):
        if UTILISER_LE_BOIS and self.source is not None:
            return self._dessiner_en_bois(screen)
        return self._dessiner_plat(screen)

    # ------------------------------------------------------------ V7.2 : plat

    def profondeur(self):
        """De combien la plaque est enfoncee dans son socle, en pixels."""
        if self.pressed:
            return ENFONCEMENT_CLIC
        if self.hovered:
            return ENFONCEMENT_SURVOL
        return 0

    def _dessiner_plat(self, screen):
        """LE BOUTON DE LA V8.

        Ce qui a change par rapport a la v7.2, et pourquoi :

          LE SOCLE A DISPARU. La v7.2 dessinait un trou sombre et une plaque qui
          descendait dedans. C'est du faux relief, et le faux relief est
          exactement ce qui date une interface. La profondeur vient maintenant
          de la LUMIERE : degrade plus clair en haut, liset d'un pixel sur
          l'arete, ombre portee large et faible.

          LE SURVOL FAIT MONTER DE DEUX PIXELS. Pas dix : deux. C'est assez pour
          que le bouton semble reel, trop peu pour qu'on voie l'animation.

          IL Y A DEUX BOUTONS, PAS UN. Le bouton PRINCIPAL est rempli a la
          couleur d'accent : c'est celui qu'on veut que tu cliques. Les autres
          sont sombres. Une interface ou tous les boutons crient est une
          interface ou on ne sait pas ou aller. Mets .principal = True pour le
          premier de la pile.
        """
        t = apparence.theme()
        ech = ui.echelle(screen)
        socle = self.rect
        if socle.width <= 2 or socle.height <= 2:
            return
        rayon = max(6, int(design.RAYON["moyen"] * ech))
        montee = 0 if self.pressed else (-2 if self.hovered else 0)
        zone = pygame.Rect(socle.x, socle.y + montee, socle.width, socle.height)

        if self.principal:
            base = t.get("accent", (122, 178, 62))
            if self.pressed:
                base = design.assombrir(base, 0.16)
            elif self.hovered:
                base = design.eclaircir(base, 0.10)
            design.ombre_douce(screen, zone, rayon,
                               force=120 if self.hovered else 92,
                               etalement=18, decalage=6)
            if self.hovered:
                design.lueur(screen, zone, t.get("accent"), rayon, force=64)
            design.degrade_vertical(screen, zone, design.eclaircir(base, 0.12),
                                    design.assombrir(base, 0.30), rayon)
            design.liset(screen, zone, (255, 255, 255), rayon, 110)
            couleur_texte = design.lisible_sur(base)
        else:
            base = t.get("panneau", (30, 34, 42))
            if self.pressed:
                base = design.assombrir(base, 0.14)
            elif self.hovered:
                base = design.eclaircir(base, 0.10)
            design.ombre_douce(screen, zone, rayon,
                               force=88 if self.hovered else 58,
                               etalement=16, decalage=5)
            design.degrade_vertical(screen, zone, design.eclaircir(base, 0.07),
                                    design.assombrir(base, 0.06), rayon)
            design.liset(screen, zone, (255, 255, 255), rayon,
                         52 if self.hovered else 34)
            bordure = t.get("accent") if self.hovered else t.get("trait",
                                                                 t.get("bord"))
            pygame.draw.rect(screen, bordure, zone,
                             design.TRAIT_ACTIF if self.hovered
                             else design.TRAIT, border_radius=rayon)
            couleur_texte = t.get("accent") if self.hovered else t.get("texte")

        taille = max(11, min(22, int(zone.height * 0.38)))
        ui.texte_centre_dans(screen, self.text, zone, taille, couleur_texte,
                             gras=True, marge=14)

    @staticmethod
    def _assombrir(couleur, facteur):
        return tuple(max(0, min(255, int(c * facteur))) for c in couleur[:3])

    @staticmethod
    def _eclaircir(couleur, facteur):
        return tuple(max(0, min(255, int(c * facteur))) for c in couleur[:3])

    # ------------------------------------------------------ V7.1 : le bois

    def _dessiner_en_bois(self, screen):
        """L'ancien rendu, garde entier. Voir UTILISER_LE_BOIS en haut."""
        draw_y = int(self.rect.y + self.float_offset)
        if self.pressed:
            draw_y += 4
        zone = pygame.Rect(self.rect.x, draw_y, self.rect.width, self.rect.height)

        self._preparer_image()
        if self.image is not None:
            screen.blit(self.image, zone.topleft)
        else:
            couleur = (139, 69, 19) if self.hovered else (160, 82, 45)
            pygame.draw.rect(screen, couleur, zone, border_radius=8)
            pygame.draw.rect(screen, (96, 52, 18), zone, 2, border_radius=8)

        taille = max(11, min(23, int(zone.height * 0.42)))
        ui.texte_centre_dans(screen, self.text, zone, taille, (18, 12, 6),
                             gras=True, marge=12)
