# board_animation.py - V6 : glissement des pieces
#
# CE QUI CHANGE PAR RAPPORT A V5 (bug M2 du rapport) :
#   1. LA FORMULE ETAIT FAUSSE. V5 ligne 47 :
#         curr_y = from_y + (to_y - from_y) * SQ_SIZE * eased
#      from_y et to_y sont deja en pixels : multiplier encore par SQ_SIZE (80)
#      envoyait la piece a y = -12 320 sur un ecran de 720 px. La piece
#      disparaissait vers le haut. Mesure : e2->e4 donnait 480, puis -10 720,
#      puis -12 320.
#   2. LA DUREE EST ENFIN UTILISEE. V5 stockait 'duration': 0.5 et ne la lisait
#      jamais : la vitesse venait de progress += 0.03 par image, donc elle
#      dependait du nombre d'images par seconde. L'animation est maintenant
#      calee sur l'horloge : 0,18 s quel que soit le framerate (c'etait ta note
#      "animation lente").
#   3. Le plateau retourne est gere via board_geometry (bug M3).
#   4. La piece n'est plus dessinee deux fois. En V5 le rendu affichait la
#      piece deja arrivee a destination ET la copie animee par-dessus.
#      cases_en_cours() permet au rendu de sauter la case d'arrivee.
#
# AUCUNE FONCTION SUPPRIMEE : start_animation(from, to, piece, sq_size),
# update() et draw(screen) sont conservees avec la meme signature.

import math

import pygame

import board_geometry as geo

DUREE_PAR_DEFAUT = 0.18   # secondes


class PieceAnimation:
    def __init__(self, chessboard, duree=DUREE_PAR_DEFAUT):
        self.chessboard = chessboard
        self.animations = []
        self.SQ_SIZE = chessboard.SQ_SIZE
        self.duree = duree
        self.active = True        # mettre a False pour couper les animations

    # ------------------------------------------------------------------ pilotage

    def start_animation(self, from_square, to_square, piece, sq_size=None):
        if not self.active or piece is None:
            return
        if sq_size:
            self.SQ_SIZE = sq_size
        self.animations.append({
            'from_square': from_square,
            'to_square': to_square,
            'piece': piece,
            'progress': 0.0,
            'duration': self.duree,
            'debut': pygame.time.get_ticks(),
            'start_pos': geo.case_vers_pixel(from_square, self.SQ_SIZE,
                                             self.chessboard.flipped),
            'end_pos': geo.case_vers_pixel(to_square, self.SQ_SIZE,
                                           self.chessboard.flipped),
        })

    def clear(self):
        self.animations = []

    def cases_en_cours(self):
        """Cases d'arrivee actuellement animees : le rendu ne doit pas y
        dessiner la piece, sinon elle apparait en double."""
        return {a['to_square'] for a in self.animations}

    def en_cours(self):
        return bool(self.animations)

    # ------------------------------------------------------------------ update

    def update(self):
        maintenant = pygame.time.get_ticks()
        for anim in self.animations[:]:
            duree_ms = max(1.0, anim['duration'] * 1000.0)
            anim['progress'] = (maintenant - anim['debut']) / duree_ms
            if anim['progress'] >= 1.0:
                self.animations.remove(anim)

    # ------------------------------------------------------------------ dessin

    def draw(self, screen):
        for anim in self.animations:
            progress = max(0.0, min(anim['progress'], 1.0))
            eased = 1 - math.pow(1 - progress, 3)   # decelere en arrivant

            from_x, from_y = anim['start_pos']
            to_x, to_y = anim['end_pos']

            # CORRECTION M2 : interpolation simple entre deux points en pixels.
            curr_x = from_x + (to_x - from_x) * eased
            curr_y = from_y + (to_y - from_y) * eased

            piece = anim['piece']
            images = getattr(self.chessboard, 'piece_images', {})
            symbole = piece.symbol() if piece else None
            if symbole in images:
                image = images[symbole]
                decalage = (self.SQ_SIZE - image.get_width()) // 2
                screen.blit(image, (curr_x + decalage, curr_y + decalage))
