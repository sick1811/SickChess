# board_highlights.py - V7 : affichage des coups possibles
#
# EN V5 : rien ne s'affichait. BoardInput remplissait board.legal_moves, mais le
# rendu dessinait board.highlights.legal_moves, une AUTRE liste que personne
# n'alimentait. Et pygame.draw.rect ignore la transparence : le "vert semi-
# transparent" aurait de toute facon masque la piece.
#
# EN V7 : les couleurs viennent du theme choisi (apparence.py), et la taille des
# pastilles suit la taille des cases, qui depend maintenant de la fenetre.
#
# AUCUNE FONCTION SUPPRIMEE : set_legal_moves, set_last_move, clear et draw
# sont conservees.

import chess
import pygame

import apparence
import board_geometry as geo


class Highlights:
    def __init__(self, chessboard):
        self.chessboard = chessboard
        self.legal_moves = []          # objets chess.Move
        self.cases_atteignables = []   # numeros de cases (compatibilite V5)
        self.selected_square = None
        self.last_move_from = None
        self.last_move_to = None
        self.case_echec = None
        self._calque = None

    # ------------------------------------------------------------------ etat

    def set_legal_moves(self, moves):
        """Coups a mettre en evidence. Accepte des Move ou des numeros de case."""
        objets, cases = [], []
        for m in moves or []:
            if isinstance(m, chess.Move):
                objets.append(m)
                cases.append(m.to_square)
            elif isinstance(m, int):
                cases.append(m)
        self.legal_moves = objets
        self.cases_atteignables = cases

    def set_selected_square(self, square):
        self.selected_square = square

    def set_last_move(self, from_square, to_square):
        self.last_move_from = from_square
        self.last_move_to = to_square

    def set_case_echec(self, square):
        self.case_echec = square

    def clear(self):
        self.legal_moves = []
        self.cases_atteignables = []
        self.selected_square = None
        self.last_move_from = None
        self.last_move_to = None
        self.case_echec = None

    def clear_legal_moves(self):
        self.legal_moves = []
        self.cases_atteignables = []
        self.selected_square = None

    # ------------------------------------------------------------------ dessin

    def _theme(self):
        return apparence.theme(getattr(self.chessboard, "theme_plateau", None))

    def _calque_pour(self, cote):
        if self._calque is None or self._calque.get_width() != cote:
            self._calque = pygame.Surface((cote, cote), pygame.SRCALPHA)
        self._calque.fill((0, 0, 0, 0))
        return self._calque

    def _rect_local(self, square, sq_size):
        colonne, ligne = geo.colonne_ligne_ecran(square, self.chessboard.flipped)
        return pygame.Rect(colonne * sq_size, ligne * sq_size, sq_size, sq_size)

    def draw(self, screen, sq_size=None):
        sq = geo.taille_case(sq_size or self.chessboard.SQ_SIZE)
        t = self._theme()
        calque = self._calque_pour(8 * sq)
        dessine = False

        montrer_dernier = apparence.reglage("surbrillance_dernier_coup", True)
        # 1. Dernier coup joue (sous tout le reste).
        for case in (self.last_move_from, self.last_move_to):
            if case is not None and montrer_dernier:
                pygame.draw.rect(calque, t["dernier"], self._rect_local(case, sq))
                dessine = True

        # 2. Case selectionnee.
        if self.selected_square is not None:
            pygame.draw.rect(calque, t["selection"],
                             self._rect_local(self.selected_square, sq))
            dessine = True

        # 3. Roi en echec.
        if self.case_echec is not None:
            rect = self._rect_local(self.case_echec, sq)
            pygame.draw.rect(calque, t["echec"], rect, max(3, sq // 16))
            dessine = True

        # 4. Coups possibles : pastille sur une case vide, anneau sur une prise.
        #    V8 : reglable aussi. Ceux qui jouent en club s'en passent, et
        #    c'est le seul moyen de voir l'echiquier exactement comme sur une
        #    vraie table.
        montrer_coups = apparence.reglage("points_coups_possibles", True)
        plateau = self.chessboard.board
        for coup in (self.legal_moves if montrer_coups else ()):
            rect = self._rect_local(coup.to_square, sq)
            prise = plateau.piece_at(coup.to_square) is not None
            try:
                prise = prise or plateau.is_en_passant(coup)
            except Exception:
                pass
            if prise:
                pygame.draw.circle(calque, t["prise"], rect.center,
                                   sq // 2 - 3, max(4, sq // 13))
            else:
                pygame.draw.circle(calque, t["coup"], rect.center, max(5, sq // 6))
            dessine = True

        # 5. Cases fournies en simple numero (ancien format).
        if montrer_coups and not self.legal_moves and self.cases_atteignables:
            for case in self.cases_atteignables:
                rect = self._rect_local(case, sq)
                pygame.draw.circle(calque, t["coup"], rect.center, max(5, sq // 6))
                dessine = True

        if dessine:
            screen.blit(calque, (geo.ORIGINE_X, geo.ORIGINE_Y))
