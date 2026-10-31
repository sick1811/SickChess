# board_right_click.py - V6 : fleches et cases colorees au clic droit
#
# CE QUI CHANGE PAR RAPPORT A V5 (bug M6 du rapport) :
#   1. LE FICHIER PLANTAIT. draw() utilisait math.atan2, math.cos et math.sin
#      sans que "import math" soit present : NameError des le premier appel.
#      Le bug ne s'etait jamais vu parce que...
#   2. ...LA CLASSE N'ETAIT JAMAIS CREEE. ChessBoard ne construisait aucun
#      right_click_manager, donc le hasattr() de board_input.py etait toujours
#      faux et board_render ne dessinait jamais rien. C'etait du code mort.
#      Elle est maintenant instanciee dans board.py et dessinee par le rendu.
#   3. Un clic droit simple colorie la case, un glisser trace une fleche : en
#      V5 les deux se declenchaient en meme temps sur un glisser.
#   4. Couleurs a la Lichess : vert par defaut, rouge avec Maj, bleu avec Ctrl.
#   5. Les annotations s'effacent quand un coup est joue, comme sur les sites.
#
# 31/10 (menage) : get_center, jamais appelee, est retiree.

import math

import pygame

import board_geometry as geo

VERT = (21, 128, 61, 160)
ROUGE = (190, 40, 40, 160)
BLEU = (40, 90, 190, 160)


class RightClickManager:
    def __init__(self, chessboard):
        self.chessboard = chessboard
        self.arrows = []           # (case_depart, case_arrivee, couleur)
        self.colored_squares = {}  # case -> couleur
        self.dragging_arrow = False
        self.arrow_start = None
        self._calque = None

    # ------------------------------------------------------------------ souris

    def _couleur_active(self):
        try:
            touches = pygame.key.get_mods()
        except Exception:
            return VERT
        if touches & getattr(pygame, "KMOD_SHIFT", 0):
            return ROUGE
        if touches & getattr(pygame, "KMOD_CTRL", 0):
            return BLEU
        return VERT

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            square = self.get_square_from_mouse(event.pos)
            if square is None:
                return
            # On memorise seulement le depart : on saura au relachement s'il
            # s'agissait d'un clic simple (case coloree) ou d'un glisser (fleche).
            self.dragging_arrow = True
            self.arrow_start = square

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
            if not self.dragging_arrow or self.arrow_start is None:
                return
            square = self.get_square_from_mouse(event.pos)
            couleur = self._couleur_active()
            if square is not None and square != self.arrow_start:
                self.basculer_fleche(self.arrow_start, square, couleur)
            elif square is not None:
                self.basculer_case(square, couleur)
            self.dragging_arrow = False
            self.arrow_start = None

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Un clic gauche efface les annotations, comme sur Lichess.
            self.clear()

    def basculer_case(self, square, couleur=VERT):
        if self.colored_squares.get(square) == couleur:
            del self.colored_squares[square]
        else:
            self.colored_squares[square] = couleur

    def basculer_fleche(self, depart, arrivee, couleur=VERT):
        for fleche in list(self.arrows):
            if fleche[0] == depart and fleche[1] == arrivee:
                self.arrows.remove(fleche)
                if fleche[2] != couleur:
                    self.arrows.append((depart, arrivee, couleur))
                return
        self.arrows.append((depart, arrivee, couleur))

    def clear(self):
        self.arrows = []
        self.colored_squares = {}
        self.dragging_arrow = False
        self.arrow_start = None

    def get_square_from_mouse(self, pos):
        return geo.pixel_vers_case(pos, self.chessboard.SQ_SIZE,
                                   self.chessboard.flipped)

    # ------------------------------------------------------------------ dessin

    def _preparer_calque(self, sq):
        cote = 8 * sq
        if self._calque is None or self._calque.get_width() != cote:
            self._calque = pygame.Surface((cote, cote), pygame.SRCALPHA)
        self._calque.fill((0, 0, 0, 0))
        return self._calque

    def draw_cases(self, screen):
        """Cases coloriees : dessinees SOUS les pieces."""
        if not self.colored_squares:
            return
        sq = self.chessboard.SQ_SIZE
        calque = self._preparer_calque(sq)
        for square, couleur in self.colored_squares.items():
            colonne, ligne = geo.colonne_ligne_ecran(square, self.chessboard.flipped)
            pygame.draw.rect(calque, couleur,
                             pygame.Rect(colonne * sq, ligne * sq, sq, sq))
        screen.blit(calque, (geo.ORIGINE_X, geo.ORIGINE_Y))

    def draw_fleches(self, screen):
        """Fleches : dessinees AU-DESSUS des pieces, comme sur Lichess."""
        if not self.arrows:
            return
        sq = self.chessboard.SQ_SIZE
        calque = self._preparer_calque(sq)
        for depart, arrivee, couleur in self.arrows:
            self._dessiner_fleche(calque, depart, arrivee, couleur, sq)
        screen.blit(calque, (geo.ORIGINE_X, geo.ORIGINE_Y))

    def draw(self, screen):
        """Dessine tout d'un coup (compatibilite avec l'ancien appel V5)."""
        self.draw_cases(screen)
        self.draw_fleches(screen)

    @staticmethod
    def est_un_saut_de_cavalier(col_d, lig_d, col_a, lig_a):
        """Ce deplacement a-t-il la forme d'un saut de cavalier ?

        On regarde la GEOMETRIE, pas la piece : une fleche tracee au clic droit
        n'a pas forcement de cavalier au depart - on peut montrer une case ou un
        cavalier POURRAIT aller. C'est la forme du deplacement qui compte.
        """
        dx, dy = abs(col_a - col_d), abs(lig_a - lig_d)
        return (dx, dy) in ((1, 2), (2, 1))

    def _dessiner_fleche(self, surface, depart, arrivee, couleur, sq):
        flip = self.chessboard.flipped
        col_d, lig_d = geo.colonne_ligne_ecran(depart, flip)
        col_a, lig_a = geo.colonne_ligne_ecran(arrivee, flip)
        x1 = col_d * sq + sq // 2
        y1 = lig_d * sq + sq // 2
        x2 = col_a * sq + sq // 2
        y2 = lig_a * sq + sq // 2

        # V7.2 (03/09) - LA FLECHE DE CAVALIER SE PLIE EN L (ta demande).
        #
        # Une fleche droite entre deux cases d'un saut de cavalier passe en
        # diagonale au milieu de deux autres cases : on ne lit pas le
        # deplacement, on lit un trait de travers. Pliee en L - le grand cote
        # d'abord, puis le petit - elle montre exactement le chemin du cavalier.
        # C'est ce que fait lichess, et c'est plus clair.
        if self.est_un_saut_de_cavalier(col_d, lig_d, col_a, lig_a) \
                and self._coude_voulu():
            self._fleche_en_L(surface, (x1, y1), (x2, y2), couleur, sq,
                              horizontal_d_abord=abs(col_a - col_d) == 2)
            return

        angle = math.atan2(y2 - y1, x2 - x1)
        pointe = max(10, sq // 4)
        # On raccourcit le trait pour qu'il s'arrete au debut de la pointe.
        xt = x2 - pointe * 0.8 * math.cos(angle)
        yt = y2 - pointe * 0.8 * math.sin(angle)

        pygame.draw.line(surface, couleur, (x1, y1), (xt, yt), max(5, sq // 11))
        pygame.draw.polygon(surface, couleur, [
            (x2, y2),
            (x2 - pointe * math.cos(angle - 0.5), y2 - pointe * math.sin(angle - 0.5)),
            (x2 - pointe * math.cos(angle + 0.5), y2 - pointe * math.sin(angle + 0.5)),
        ])

    @staticmethod
    def _coude_voulu():
        """Le reglage "fleche en L pour le cavalier". Vrai par defaut."""
        try:
            import apparence
            return bool(apparence.reglage("fleche_cavalier_en_L", True))
        except Exception:
            return True

    def _fleche_en_L(self, surface, depart, arrivee, couleur, sq,
                     horizontal_d_abord=True):
        """La fleche coudee du cavalier : le grand cote, puis le petit.

        On part TOUJOURS par le grand cote (deux cases), comme sur lichess :
        c'est le chemin qu'on se represente quand on bouge un cavalier.
        """
        x1, y1 = depart
        x2, y2 = arrivee
        coude = (x2, y1) if horizontal_d_abord else (x1, y2)
        epaisseur = max(5, sq // 11)
        pointe = max(10, sq // 4)

        # Le dernier segment donne la direction de la pointe.
        angle = math.atan2(y2 - coude[1], x2 - coude[0])
        xt = x2 - pointe * 0.8 * math.cos(angle)
        yt = y2 - pointe * 0.8 * math.sin(angle)

        pygame.draw.line(surface, couleur, (x1, y1), coude, epaisseur)
        pygame.draw.line(surface, couleur, coude, (xt, yt), epaisseur)
        # Un disque au coude : sans lui, l'angle droit laisse une encoche.
        pygame.draw.circle(surface, couleur, (int(coude[0]), int(coude[1])),
                           epaisseur // 2)
        pygame.draw.polygon(surface, couleur, [
            (x2, y2),
            (x2 - pointe * math.cos(angle - 0.5),
             y2 - pointe * math.sin(angle - 0.5)),
            (x2 - pointe * math.cos(angle + 0.5),
             y2 - pointe * math.sin(angle + 0.5)),
        ])
