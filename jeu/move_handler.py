# move_handler.py - V7 : toute la logique de saisie des coups
#
# CE QUI CHANGE PAR RAPPORT A LA V6 :
#   1. CLIC DROIT = ANNULER LE COUP EN COURS. Si une piece est selectionnee ou
#      en train d'etre deplacee, le clic droit la repose a sa place. Ce n'est
#      que si rien n'est en cours que le clic droit sert a tracer des fleches.
#   2. PREMOUVEMENT : on peut preparer son coup pendant que l'adversaire
#      reflechit. Il part tout seul des que c'est notre tour, et il est oublie
#      s'il est devenu impossible, comme sur chess.com.
#   3. Touche H : Stockfish montre le meilleur coup avec une fleche verte.
#   4. Touche F : retourner le plateau a la main.
#
# AUCUNE FONCTION SUPPRIMEE : handle_move_input et get_square_from_mouse
# gardent leur nom et leur signature.

import chess
import pygame

import board_geometry as geo
import freestyle
import retournement


class MoveHandler:
    def __init__(self, chessboard):
        self.chessboard = chessboard
        self.selection_premouvement = False

    # ------------------------------------------------------------------ droits

    def couleur_du_joueur(self):
        """La couleur que le joueur humain controle, ou None si les deux."""
        plateau = self.chessboard
        couleur = getattr(plateau, "couleur_joueur", None)
        if couleur is not None:
            return couleur
        if getattr(plateau, "hotseat_mode", False):
            return None
        if getattr(plateau, "ia_joue_blancs", False):
            return chess.BLACK
        if getattr(plateau, "ai_manager", None) is not None:
            return chess.WHITE
        return None

    def piece_a_nous(self, piece):
        """La piece appartient-elle au joueur humain ?"""
        if piece is None:
            return False
        # V7.2 - SPECTATEUR : on regarde la partie de quelqu'un d'autre, aucune
        # piece n'est a nous. Le relais refuse deja nos coups, mais sans ce
        # garde-fou l'echiquier AFFICHE partait dans une position fausse.
        if getattr(self.chessboard, "spectateur", False):
            return False
        couleur = self.couleur_du_joueur()
        return True if couleur is None else piece.color == couleur

    def piece_jouable(self, piece):
        """Peut-on la bouger MAINTENANT (c'est-a-dire a notre tour) ?"""
        if piece is None or piece.color != self.chessboard.board.turn:
            return False
        return self.piece_a_nous(piece)

    # ------------------------------------------------------------------ saisie

    def handle_move_input(self, event, engine=None):
        plateau = self.chessboard

        # 1. Le panneau de promotion capte tout tant qu'il est ouvert.
        promotion = getattr(plateau, "promotion", None)
        if promotion is not None and promotion.est_actif():
            reponse = promotion.handle_event(event)
            if reponse == "annule":
                promotion.fermer()
                self._annuler_selection()
            elif reponse is not None:
                depart, arrivee = promotion.from_square, promotion.to_square
                promotion.fermer()
                self._jouer(depart, arrivee, engine, piece_promotion=reponse)
            return

        # 2. Clavier.
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                # V7.2 (03/09) : le retournement GLISSE. C'etait un simple
                # `not plateau.flipped`, donc les trente-deux pieces
                # changeaient de place a l'image suivante.
                retournement.retourner(plateau)
                return
            if event.key == pygame.K_h:
                plateau.demander_indice(engine)
                return
            if event.key == pygame.K_ESCAPE:
                if plateau.selected_square is not None or plateau.dragging:
                    self._annuler_selection()
                elif getattr(plateau, "premove", None):
                    plateau.annuler_premouvement()
                return

        # 3. CLIC DROIT : d'abord annuler le coup en cours, sinon les fleches.
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if plateau.selected_square is not None or plateau.dragging:
                self._annuler_selection()
                return
            if getattr(plateau, "premove", None):
                plateau.annuler_premouvement()
                return
        gestionnaire = getattr(plateau, "right_click_manager", None)
        if gestionnaire is not None:
            gestionnaire.handle_event(event)

        if plateau.game_over:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._clic_gauche(event, engine)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._relachement(event, engine)
        elif event.type == pygame.MOUSEMOTION:
            if plateau.dragging:
                plateau.drag_pos = event.pos

    # ------------------------------------------------------------------ details

    def _clic_gauche(self, event, engine):
        plateau = self.chessboard

        if plateau.ui_manager and plateau.ui_manager.handle_click(event.pos):
            return

        square = self.get_square_from_mouse(event.pos)
        if square is None:
            self._annuler_selection()
            return

        plateau.indice = None

        # a) Une piece est deja selectionnee et on clique sur une case jouable.
        if plateau.selected_square is not None and square in plateau.legal_moves:
            if self.selection_premouvement:
                self._preparer_premouvement(plateau.selected_square, square)
            else:
                self._jouer(plateau.selected_square, square, engine)
            return

        piece = plateau.board.piece_at(square)

        # b) On clique sur une de ses pieces : selection normale ou premouvement.
        if self.piece_jouable(piece):
            self._selectionner(square, piece, event.pos, premouvement=False)
            return
        if (plateau.premouvement_actif and self.piece_a_nous(piece)
                and not plateau.cest_mon_tour()):
            self._selectionner(square, piece, event.pos, premouvement=True)
            return

        # c) Clic dans le vide : on annule.
        self._annuler_selection()

    def _relachement(self, event, engine):
        plateau = self.chessboard
        if not plateau.dragging:
            return
        depart = plateau.selected_square
        square = self.get_square_from_mouse(event.pos)
        plateau.dragging = False
        plateau.drag_piece = None
        if square is None or depart is None or square == depart:
            return                      # simple clic : la selection reste
        if square in plateau.legal_moves:
            if self.selection_premouvement:
                self._preparer_premouvement(depart, square)
            else:
                self._jouer(depart, square, engine)
        else:
            plateau.sounds.play("illegal")
            self._annuler_selection()

    def _coups_depuis(self, square, premouvement):
        """Coups possibles depuis une case. Pour un premouvement, on regarde la
        position comme si c'etait deja notre tour."""
        plateau = self.chessboard
        if not premouvement:
            return [m for m in plateau.board.legal_moves if m.from_square == square]
        hypothese = plateau.board.copy()
        hypothese.turn = not hypothese.turn
        try:
            return [m for m in hypothese.legal_moves if m.from_square == square]
        except Exception:
            return []

    def _selectionner(self, square, piece, pos, premouvement=False):
        plateau = self.chessboard
        coups = self._coups_depuis(square, premouvement)
        self.selection_premouvement = premouvement
        plateau.selected_square = square
        plateau.legal_moves = []
        for m in coups:
            if m.to_square not in plateau.legal_moves:
                plateau.legal_moves.append(m.to_square)
        if freestyle.est_freestyle(plateau.board):
            # Freestyle : le roque se joue aussi en posant le roi sur g / c.
            for m in [m for m in coups if plateau.board.is_castling(m)]:
                roi = freestyle.arrivee_du_roi(plateau.board, m)
                if roi not in plateau.legal_moves:
                    plateau.legal_moves.append(roi)
                    coups.append(chess.Move(square, roi))
        plateau.dragging = True
        plateau.drag_piece = piece
        plateau.drag_pos = pos
        plateau.highlights.set_legal_moves(coups)
        plateau.highlights.set_selected_square(square)

    def _annuler_selection(self):
        """Repose la piece a sa place et efface les indications."""
        plateau = self.chessboard
        plateau.selected_square = None
        plateau.legal_moves = []
        plateau.dragging = False
        plateau.drag_piece = None
        plateau.drag_pos = None
        self.selection_premouvement = False
        plateau.highlights.clear_legal_moves()

    def _preparer_premouvement(self, depart, arrivee):
        plateau = self.chessboard
        coups = freestyle.coups_vers(plateau.board, self._coups_depuis(depart, True),
                                     depart, arrivee)
        if not coups:
            self._annuler_selection()
            return False
        coup = next((m for m in coups if m.promotion == chess.QUEEN), coups[0])
        self._annuler_selection()
        plateau.definir_premouvement(coup)
        print("[PREMOUVEMENT] %s prepare" % coup.uci())
        return True

    def _jouer(self, from_square, to_square, engine, piece_promotion=None):
        plateau = self.chessboard
        candidats = freestyle.coups_vers(plateau.board, list(plateau.board.legal_moves),
                                         from_square, to_square)
        if not candidats:
            plateau.sounds.play("illegal")
            self._annuler_selection()
            return False

        promotions = [m for m in candidats if m.promotion]
        if promotions:
            if piece_promotion is None:
                promotion = getattr(plateau, "promotion", None)
                if promotion is not None:
                    piece = plateau.board.piece_at(from_square)
                    couleur = piece.color if piece else plateau.board.turn
                    promotion.ouvrir(from_square, to_square, couleur)
                    return False
                piece_promotion = chess.QUEEN
            coup = next((m for m in promotions if m.promotion == piece_promotion),
                        promotions[0])
        else:
            coup = candidats[0]

        self._annuler_selection()
        plateau.make_move(coup, engine)
        return True

    # ------------------------------------------------------------------ souris

    def get_square_from_mouse(self, pos):
        return geo.pixel_vers_case(pos, self.chessboard.SQ_SIZE,
                                   self.chessboard.flipped)
