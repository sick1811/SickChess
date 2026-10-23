# board_last_move_highlight.py - V7
#
# EN V5 : la position ne tenait pas compte du retournement du plateau (seules
# les lignes etaient inversees), et pygame.draw.rect ignorant la transparence,
# le cadre orange etait opaque.
# EN V7 : couleurs du theme choisi et taille de case dynamique.
#
# AUCUNE FONCTION SUPPRIMEE : set_last_move et draw(screen, sq_size).

import pygame

import apparence
import board_geometry as geo


class LastMoveHighlight:
    def __init__(self, chessboard):
        self.chessboard = chessboard
        self.from_square = None
        self.to_square = None
        self._calque = None
        self._cle = None

    def set_last_move(self, from_square, to_square):
        self.from_square = from_square
        self.to_square = to_square

    def clear(self):
        self.from_square = None
        self.to_square = None

    def draw(self, screen, sq_size=None):
        if self.from_square is None or self.to_square is None:
            return
        # V8 : reglable. Certains veulent un echiquier nu ; d'autres ne
        # retrouvent pas le dernier coup sans le voile. C'est un gout, donc
        # c'est un reglage.
        if not apparence.reglage("surbrillance_dernier_coup", True):
            return
        sq = geo.taille_case(sq_size or self.chessboard.SQ_SIZE)
        t = apparence.theme(getattr(self.chessboard, "theme_plateau", None))
        # 23/10 (banc d'essai) : une seule case transparente, gardee en memoire,
        # posee sur les deux cases (au lieu d'un calque grand comme le plateau
        # repeint et recopie a chaque image).
        cle = (sq, tuple(t["dernier"]))
        if self._calque is None or self._cle != cle:
            self._cle = cle
            self._calque = pygame.Surface((sq, sq), pygame.SRCALPHA)
            cadre = t["dernier"][:3] + (min(255, t["dernier"][3] + 70),)
            pygame.draw.rect(self._calque, t["dernier"], self._calque.get_rect())
            pygame.draw.rect(self._calque, cadre, self._calque.get_rect(), max(3, sq // 20))
        for case in (self.from_square, self.to_square):
            colonne, ligne = geo.colonne_ligne_ecran(case, self.chessboard.flipped)
            screen.blit(self._calque, (geo.ORIGINE_X + colonne * sq, geo.ORIGINE_Y + ligne * sq))
