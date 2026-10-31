# retournement.py - V7.2 (03/09) : NOUVEAU FICHIER
#
# L'ANIMATION DE RETOURNEMENT DE L'ECHIQUIER (ta demande : "quand on tourne
# l'echiquier il doit y avoir une animation, c'est trop brut et ca se teleporte,
# les pieces suivent l'echiquier et ne se teleportent pas - pour toutes les
# parties du logiciel").
#
# CE QUI SE PASSAIT : `plateau.flipped = not plateau.flipped` et c'est tout. A
# l'image suivante, les trente-deux pieces etaient ailleurs. Aucune animation
# n'existait pour ca - PieceAnimation ne sait glisser qu'UNE piece d'une case a
# une autre, quand un coup est joue.
#
# CE QUI REND L'ANIMATION SIMPLE, ET C'EST UNE PROPRIETE DE L'ECHIQUIER :
# retourner le plateau est une rotation de 180 degres, qui envoie la case
# (colonne, ligne) sur (7-colonne, 7-ligne). Or la somme (7-c)+(7-r) = 14-c-r a
# LA MEME PARITE que c+r : le damier est identique a lui-meme apres rotation.
# Les cases n'ont donc pas besoin de bouger - seules les PIECES traversent le
# plateau, chacune en ligne droite par le centre. C'est exactement ce qu'on voit
# quand on fait tourner un vrai echiquier.
#
# CE FICHIER NE DESSINE QUE LES PIECES EN VOL. Le reste du rendu continue
# normalement, et le rendu saute les cases dont la piece est en train de voler
# (cases_en_cours) pour ne pas la dessiner deux fois - le meme contrat que
# board_animation.py, pour que board_render n'ait presque rien a apprendre.
#
# AUCUNE FONCTION SUPPRIMEE : ce fichier n'existait pas. PieceAnimation est
# intacte et continue de servir aux coups joues.


import chess
import pygame

import board_geometry as geo

# Assez lent pour qu'on voie les pieces traverser, assez rapide pour ne pas
# attendre. Mesure a l'oeil sur les trois vitesses essayees : 0,45 s traine,
# 0,20 s se lit deja comme une teleportation.
DUREE = 0.32


def _adoucir(avancement):
    """Depart doux, arrivee douce. Sans ca le depart est un coup de fouet."""
    if avancement <= 0.5:
        return 2.0 * avancement * avancement
    return 1.0 - 2.0 * (1.0 - avancement) ** 2


class Retournement:
    """Le vol des pieces pendant que le plateau se retourne.

    'proprietaire' est l'objet qui porte .flipped et .board (ChessBoard ou
    PlateauSimple) ; on ne lui demande rien d'autre.
    """

    def __init__(self, proprietaire=None, duree=DUREE):
        self.proprietaire = proprietaire
        self.duree = duree
        self.active = True          # False = retournement instantane
        self.vols = []              # [(case, piece, (x1,y1), (x2,y2))]
        self.debut = 0
        self.avancement = 0.0

    # ---------------------------------------------------------------- pilotage

    def lancer(self, plateau, avant, apres, taille_case):
        """Prepare le vol de chaque piece, de l'orientation 'avant' a 'apres'.

        'plateau' est un chess.Board. On photographie les positions de depart
        et d'arrivee TOUT DE SUITE : si le joueur redimensionne la fenetre
        pendant l'animation, les pieces finissent leur vol sur l'ancienne
        grille plutot que de sauter - c'est le moindre mal, et ca dure 0,32 s.
        """
        self.vols = []
        self.avancement = 0.0
        # V8 : la duree vient du reglage d'apparence. A zero, on ne lance
        # rien - c'est le "retournement instantane" de la v7.2, redevenu un
        # choix au lieu d'un defaut.
        try:
            import apparence
            self.duree = float(apparence.reglage("duree_retournement",
                                                 self.duree))
        except Exception:
            pass
        if not self.active or self.duree <= 0.0 or plateau is None \
                or avant == apres:
            return False
        for case in chess.SQUARES:
            piece = plateau.piece_at(case)
            if piece is None:
                continue
            depart = geo.case_vers_pixel(case, taille_case, avant)
            arrivee = geo.case_vers_pixel(case, taille_case, apres)
            if depart == arrivee:
                continue
            self.vols.append((case, piece, depart, arrivee))
        if not self.vols:
            return False
        self.debut = pygame.time.get_ticks()
        return True

    def arreter(self):
        self.vols = []
        self.avancement = 0.0

    # Meme nom que dans board_animation.py : le rendu n'a qu'une chose a savoir.
    def clear(self):
        self.arreter()

    def en_cours(self):
        return bool(self.vols)

    def cases_en_cours(self):
        """Les cases dont la piece vole : le rendu ne doit pas les dessiner."""
        return {vol[0] for vol in self.vols}

    def update(self):
        if not self.vols:
            return
        duree_ms = max(1.0, self.duree * 1000.0)
        self.avancement = (pygame.time.get_ticks() - self.debut) / duree_ms
        if self.avancement >= 1.0:
            self.arreter()

    # ------------------------------------------------------------------ dessin

    def draw(self, screen, images=None, taille_case=None):
        if not self.vols:
            return
        images = images if images is not None else self._images()
        taille = int(taille_case or getattr(self.proprietaire, "SQ_SIZE", 0)
                     or geo.TAILLE_CASE)
        eased = _adoucir(max(0.0, min(1.0, self.avancement)))
        for _case, piece, (x1, y1), (x2, y2) in self.vols:
            image = images.get(piece.symbol())
            if image is None:
                continue
            x = x1 + (x2 - x1) * eased
            y = y1 + (y2 - y1) * eased
            decalage_x = (taille - image.get_width()) // 2
            decalage_y = (taille - image.get_height()) // 2
            screen.blit(image, (int(x) + decalage_x, int(y) + decalage_y))

    def _images(self):
        proprietaire = self.proprietaire
        for nom in ("piece_images", "images"):
            images = getattr(proprietaire, nom, None)
            if images:
                return images
        return {}


# --------------------------------------------------------------------- service

def retourner(proprietaire, plateau=None, taille_case=None):
    """Retourne l'echiquier de cet objet, EN L'ANIMANT si c'est possible.

    C'est le seul point d'entree : partout ou le code faisait
    `plateau.flipped = not plateau.flipped`, il appelle ceci a la place, et
    l'animation vient avec. Si l'objet n'a pas de Retournement (vieux code,
    test sans fenetre), on retombe sur le basculement instantane d'avant -
    donc rien ne peut casser.
    """
    return orienter(proprietaire, not bool(getattr(proprietaire, "flipped",
                                                   False)),
                    plateau=plateau, taille_case=taille_case)


def orienter(proprietaire, flipped, plateau=None, taille_case=None):
    """Met l'echiquier dans CETTE orientation, en animant s'il change.

    Sert la ou le code choisit une orientation absolue plutot que de basculer :
    le tour a jouer en hotseat, la couleur recue en ligne.
    """
    if proprietaire is None:
        return False
    avant = bool(getattr(proprietaire, "flipped", False))
    apres = bool(flipped)
    proprietaire.flipped = apres
    if avant == apres:
        return False
    animation = getattr(proprietaire, "retournement", None)
    if animation is None:
        return False
    echiquier = plateau if plateau is not None else getattr(proprietaire,
                                                            "board", None)
    taille = taille_case or getattr(proprietaire, "SQ_SIZE", None) \
        or getattr(proprietaire, "taille_case", None)
    try:
        return animation.lancer(echiquier, avant, apres, int(taille or 0)
                                or geo.TAILLE_CASE)
    except Exception:
        # Une animation ratee ne doit jamais empecher le retournement.
        animation.arreter()
        return False
