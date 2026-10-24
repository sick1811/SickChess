# ecran_analyse_libre.py - SickChess 24/10 (travail p35) : l'analyse libre.
#
# Un echiquier ou l'on joue LES DEUX CAMPS, et Stockfish qui reflechit sans
# arret sur la position affichee (analyse_continue.py), comme sur lichess :
#   - a gauche : l'echiquier et la barre d'avantage (la meme que la revue) ;
#     fleche bleue = le meilleur coup, plus fines = les coups presque aussi bons ;
#   - a droite : les 3 meilleures lignes (un clic joue le premier coup), le
#     verdict des tables de finale Syzygy quand elles connaissent la position,
#     la feuille des coups joues, et les boutons.
# On y arrive par le menu (« Analyse libre »), ou depuis la revue (« Analyser »)
# avec la position regardee. On peut aussi coller un FEN ou une partie PGN
# (Ctrl+V), ou fabriquer une position avec l'editeur (E).
#
# Commandes : fleches = coup precedent / suivant, Debut / Fin, F = retourner,
# Espace = moteur en marche / a l'arret, E = editeur, C = copier le FEN,
# Ctrl+V = coller, Echap = retour.

import os

import chess
import pygame

import analyse_continue
import annotations
import apparence
import notation
import retournement
import ui
from board import ChessBoard
from ecran_revue import (BLEU_AUSSI_BON, BLEU_MEILLEUR, DispositionRevue,
                         dessiner_barre_avantage)

ORDRE_PALETTE = "KQRBNP"
OUTIL_GOMME = "gomme"


def threads_conseilles(analyse_de_partie_en_cours=False):
    """Tous les coeurs sauf un ; la moitie si la revue analyse encore la partie
    (les deux en priorite basse : le jeu reste fluide)."""
    coeurs = os.cpu_count() or 2
    if analyse_de_partie_en_cours:
        return max(1, coeurs // 2)
    return max(1, coeurs - 1)


class EditeurPosition:
    """L'editeur de position : on pose et on enleve les pieces, on choisit le
    trait et les roques, puis on valide."""

    def __init__(self, fen):
        self.plateau = chess.Board(fen)
        self.plateau.ep_square = None
        self.outil = None            # symbole de piece ("Q", "n"...), gomme, ou None
        self.prise = None            # case de la piece qu'on deplace (sans outil)
        self.message = ""

    def clic(self, case, bouton=1):
        """Un clic sur l'echiquier. Clic droit = enlever la piece."""
        b = self.plateau
        self.message = ""
        if bouton == 3 or self.outil == OUTIL_GOMME:
            b.remove_piece_at(case)
            self.prise = None
        elif self.outil:
            piece = chess.Piece.from_symbol(self.outil)
            # Reposer la meme piece au meme endroit l'enleve (comme lichess).
            if b.piece_at(case) == piece:
                b.remove_piece_at(case)
            else:
                b.set_piece_at(case, piece)
        elif self.prise is None:
            self.prise = case if b.piece_at(case) else None
        else:
            if case != self.prise:
                b.set_piece_at(case, b.piece_at(self.prise))
                b.remove_piece_at(self.prise)
            self.prise = None
        self._garder_les_roques_possibles()

    def choisir_outil(self, outil):
        """Une piece, la gomme, ou None (« Deplacer »). Elle reste choisie."""
        self.outil = outil
        self.prise = None

    def changer_trait(self, couleur):
        self.plateau.turn = couleur

    def basculer_roque(self, masque):
        if not masque & analyse_continue.roques_possibles(self.plateau):
            return
        self.plateau.castling_rights ^= masque

    def vider(self):
        self.plateau.clear_board()
        self.plateau.castling_rights = 0

    def position_de_depart(self):
        self.plateau.reset()

    def _garder_les_roques_possibles(self):
        self.plateau.castling_rights &= analyse_continue.roques_possibles(self.plateau)

    def valider(self):
        """La position, prete a analyser (fen), ou None et self.message dit pourquoi."""
        b = self.plateau.copy()
        b.halfmove_clock, b.fullmove_number = 0, 1
        self.message = analyse_continue.probleme_de_position(b)
        return None if self.message else b.fen()


class EcranAnalyseLibre:
    def __init__(self, screen, preferences=None, fen=None, coups=(), index=None,
                 stockfish_path=None, threads=None, moteur=None, retourne=False):
        """fen : la position de depart (la position initiale par defaut) ;
        coups : coups (uci ou chess.Move) deja joues depuis fen ; index : la
        position affichee (apres index coups ; la derniere par defaut)."""
        self.screen = screen
        prefs = dict(preferences or {})
        self.disposition = DispositionRevue(*screen.get_size())
        self.plateau = ChessBoard(screen, {"pendule_active": False,
                                           "son_de_depart": False,
                                           "theme_plateau": prefs.get("theme_plateau"),
                                           "jeu_pieces": prefs.get("jeu_pieces")},
                                  self.disposition)
        p = self.plateau
        p.changer_apparence(prefs.get("theme_plateau"), prefs.get("jeu_pieces"))
        p.renderer.afficher_coordonnees = bool(prefs.get("afficher_coordonnees", True))
        p.sounds.set_volume(float(prefs.get("volume_sons", 0.6)))
        p.sounds.actif = bool(prefs.get("sons_actifs", True))
        vitesse = float(prefs.get("vitesse_animation", 0.18))
        p.animation.duree = max(0.01, vitesse)
        p.animation.active = vitesse > 0
        p.flipped = bool(retourne)
        p.hotseat_mode = True            # on joue les deux camps
        p.premouvement_actif = False
        p.make_move = self._coup_sur_l_echiquier

        self.analyse = analyse_continue.AnalyseContinue(
            stockfish_path if moteur is None else None,
            threads or threads_conseilles(), moteur=moteur)
        self.edition = None              # EditeurPosition pendant l'edition
        self.message = ""
        self.message_fin = 0
        self.rects_lignes = []
        self.rects_coups = []
        self.rects_palette = []
        self.rects_roques = []
        self.premiere_ligne = 0

        b = ui.Bouton
        self.boutons_nav = [b((0, 0, 10, 10), s, c, taille=18)
                            for s, c in (("|<", "debut"), ("<", "precedent"),
                                         (">", "suivant"), (">|", "fin"))]
        self.btn_editer = b((0, 0, 10, 10), "Éditer (E)", "editer", taille=15, gras=False)
        self.btn_coller = b((0, 0, 10, 10), "Coller (Ctrl+V)", "coller", taille=15, gras=False)
        self.btn_copier = b((0, 0, 10, 10), "Copier le FEN", "copier", taille=15, gras=False)
        self.btn_moteur = b((0, 0, 10, 10), "Pause (Espace)", "moteur", taille=15, gras=False)
        self.btn_retourner = b((0, 0, 10, 10), "Retourner (F)", "retourner", taille=15, gras=False)
        self.btn_retour = b((0, 0, 10, 10), "Retour", "retour", taille=16)
        self.boutons_analyse = self.boutons_nav + [
            self.btn_editer, self.btn_coller, self.btn_copier,
            self.btn_moteur, self.btn_retourner, self.btn_retour]
        # L'editeur
        self.btn_blancs = b((0, 0, 10, 10), "Trait aux Blancs", "trait_blancs", taille=14, gras=False)
        self.btn_noirs = b((0, 0, 10, 10), "Trait aux Noirs", "trait_noirs", taille=14, gras=False)
        self.btn_vider = b((0, 0, 10, 10), "Vider", "vider", taille=15, gras=False)
        self.btn_depart = b((0, 0, 10, 10), "Départ", "depart", taille=15, gras=False)
        self.btn_annuler = b((0, 0, 10, 10), "Annuler", "annuler", taille=15, gras=False)
        self.btn_valider = b((0, 0, 10, 10), "Analyser", "valider", taille=16)
        self.btn_valider.selectionne = True
        self.boutons_edition = [self.btn_blancs, self.btn_noirs, self.btn_vider,
                                self.btn_depart, self.btn_annuler, self.btn_valider]

        self.charger(fen or chess.STARTING_FEN, coups, index)
        self._placer()

    # ------------------------------------------------------------- position

    def charger(self, fen, coups=(), index=None):
        """Nouvelle position de depart (collage, editeur, revue)."""
        self.fen_depart = chess.Board(fen).fen()
        self.coups = [c if isinstance(c, chess.Move) else chess.Move.from_uci(c)
                      for c in coups]
        self.index = -1
        self.aller_a(len(self.coups) if index is None else index)

    def aller_a(self, index, son=False):
        index = max(0, min(len(self.coups), int(index)))
        p = self.plateau
        avant = chess.Board(self.fen_depart)
        for coup in self.coups[:max(0, index - 1)]:
            avant.push(coup)
        p.board = avant.copy()
        if index:
            p.board.push(self.coups[index - 1])
        avance_d_un = index == self.index + 1
        self.index = index
        p.animation.clear()
        p.selected_square = None
        p.highlights.clear_legal_moves()
        if index:
            dernier = self.coups[index - 1]
            p.last_move_highlight.set_last_move(dernier.from_square, dernier.to_square)
            p.highlights.set_last_move(dernier.from_square, dernier.to_square)
            if avance_d_un and son:
                p.animation.start_animation(dernier.from_square, dernier.to_square,
                                            p.board.piece_at(dernier.to_square), p.SQ_SIZE)
                prise = avant.piece_at(dernier.to_square)
                if avant.is_en_passant(dernier):
                    prise = chess.Piece(chess.PAWN, not avant.turn)
                p._jouer_son_du_coup(dernier, avant.piece_at(dernier.from_square), prise,
                                     avant.is_castling(dernier), avant.is_en_passant(dernier))
        else:
            p.last_move_highlight.clear()
            p.highlights.clear()
        p.highlights.set_case_echec(p.board.king(p.board.turn)
                                    if p.board.is_check() else None)
        self._suivre_le_coup()

    def _coup_sur_l_echiquier(self, move, engine=None):
        """Un coup joue a la souris : la suite prevue continue si c'est le meme
        coup ; sinon la suite est remplacee par ce coup."""
        p = self.plateau
        if move not in p.board.legal_moves:
            p.sounds.play("illegal")
            return False
        if self.index < len(self.coups) and self.coups[self.index] == move:
            self.aller_a(self.index + 1, son=True)
            return True
        if not ChessBoard.make_move(p, move, engine):
            return False
        del self.coups[self.index:]
        self.coups.append(move)
        self.index += 1
        self._suivre_le_coup()
        return True

    def jouer_ligne(self, rang):
        """Clic sur une des lignes du moteur : on joue son premier coup."""
        lignes = self.lignes()
        if 0 <= rang < len(lignes):
            coup = chess.Move.from_uci(lignes[rang]["uci"])
            if coup in self.plateau.board.legal_moves:
                self._coup_sur_l_echiquier(coup)

    def position(self):
        """{fen, finie, mat, pat} de la position affichee. Calcule une fois par
        position (pas a chaque image : le FEN et la fin de partie coutent cher)."""
        b = self.plateau.board
        cle = (b._transposition_key(), len(b.move_stack), b.halfmove_clock)
        if getattr(self, "_position", (None,))[0] != cle:
            self._position = (cle, {"fen": b.fen(), "finie": b.is_game_over(),
                                    "mat": b.is_checkmate(), "pat": b.is_stalemate()})
        return self._position[1]

    def lignes(self):
        """Les meilleures lignes de la position affichee (vide si non calculee)."""
        if self.edition is not None:
            return []
        pos = self.position()
        if pos["finie"]:
            return []
        return self.analyse.resultat(pos["fen"])["lignes"]

    def evaluation(self):
        """(evaluation en pions pour les Blancs, texte) de la position affichee."""
        b, pos = self.plateau.board, self.position()
        if pos["mat"]:
            return (-20.0 if b.turn == chess.WHITE else 20.0), "Mat"
        if pos["finie"]:
            return 0.0, "Nulle"
        lignes = self.lignes()
        if not lignes:
            return None, ""
        return lignes[0]["evaluation"], lignes[0]["texte"]

    # ------------------------------------------------------------- collage

    def coller_texte(self, texte):
        """Un FEN ou un PGN : la position (ou la partie) remplace l'analyse."""
        fen, coups, erreur = analyse_continue.lire_fen_ou_pgn(texte)
        if erreur:
            self._afficher_message(erreur)
            return False
        self.edition = None
        self.charger(fen, coups, 0 if coups else None)
        self._afficher_message("Partie collée : %d coups" % len(coups) if coups
                               else "Position collée")
        return True

    def copier_fen(self):
        fen = self.plateau.board.fen()
        self._afficher_message("FEN copié" if ui.copier(fen) else fen, 6)
        return fen

    # ------------------------------------------------------------- editeur

    def ouvrir_l_editeur(self):
        self.edition = EditeurPosition(self.plateau.board.fen())
        self.plateau.selected_square = None
        self.plateau.highlights.clear()
        self.plateau.last_move_highlight.clear()
        self.plateau.fleches_conseil = []
        self.plateau.board = self.edition.plateau

    def fermer_l_editeur(self, valider):
        if valider:
            fen = self.edition.valider()
            if fen is None:
                return False
            self.edition = None
            self.charger(fen)
            self._afficher_message("Position prête : Stockfish l'analyse")
            return True
        self.edition = None
        self.aller_a(self.index)
        return True

    # ------------------------------------------------------------- placement

    def _placer(self, screen=None):
        if screen is not None:
            self.screen = screen
            self.plateau.screen = screen
        self.disposition.recalculer(*self.screen.get_size())
        p = self.plateau
        if p.SQ_SIZE != self.disposition.taille_case:
            p.SQ_SIZE = self.disposition.taille_case
            p.load_piece_images()
        p.disposition = self.disposition
        ech = self.ech = ui.echelle(self.screen)
        self.panneau = panneau = pygame.Rect(*self.disposition.rect_panneau())
        x = panneau.x + int(14 * ech)
        l = panneau.width - int(28 * ech)
        self.x, self.l = x, l
        espace = int(8 * ech)
        h36 = int(36 * ech)
        h_nav = int(40 * ech)
        bas = panneau.bottom - int(12 * ech)

        def rangee(boutons, y, h):
            n = len(boutons)
            largeur = (l - (n - 1) * espace) // n
            for i, bouton in enumerate(boutons):
                fin = x + l if i == n - 1 else x + i * (largeur + espace) + largeur
                bouton.placer((x + i * (largeur + espace), y, fin - x - i * (largeur + espace), h))

        # --- analyse : 3 rangees de boutons en bas
        rangee([self.btn_moteur, self.btn_retourner, self.btn_retour], bas - h36, h36)
        rangee([self.btn_editer, self.btn_coller, self.btn_copier], bas - 2 * h36 - espace, h36)
        y_nav = bas - 2 * h36 - 2 * espace - h_nav
        rangee(self.boutons_nav, y_nav, h_nav)

        y = panneau.y + int(12 * ech)
        h_titre = ui.police(ui.t(17, ech), True).get_height() \
            + ui.police(ui.t(12, ech)).get_height() + int(6 * ech)
        self.zone_titre = pygame.Rect(x, y, l, h_titre)
        y += h_titre + espace
        self.h_ligne_moteur = int(30 * ech)
        h_lignes = 3 * self.h_ligne_moteur + ui.police(ui.t(12, ech)).get_height() + int(18 * ech)
        self.zone_lignes = pygame.Rect(x, y, l, h_lignes)
        y += h_lignes + espace
        self.zone_coups = pygame.Rect(x, y, l, max(int(40 * ech), y_nav - espace - y))
        self.taille_coup = ui.t(14, ech)
        self.hauteur_ligne = ui.police(self.taille_coup, mono=True).get_height() + int(5 * ech)
        self.lignes_visibles = max(1, (self.zone_coups.height - int(10 * ech))
                                   // self.hauteur_ligne)

        # --- editeur
        y = panneau.y + int(12 * ech) + h_titre + espace
        self.zone_palette = pygame.Rect(x, y, l, int(2 * 52 * ech + espace))
        y = self.zone_palette.bottom + espace
        rangee([self.btn_blancs, self.btn_noirs], y, h36)
        y += h36 + espace
        self.zone_roques = pygame.Rect(x, y, l, int(2 * 26 * ech))
        y = self.zone_roques.bottom + espace
        self.zone_message_edition = pygame.Rect(x, y, l, int(40 * ech))
        rangee([self.btn_annuler, self.btn_valider], bas - h36, h36)
        rangee([self.btn_vider, self.btn_depart], bas - 2 * h36 - espace, h36)
        self._suivre_le_coup()

    def _ligne_du_coup(self, index):
        noirs = chess.Board(self.fen_depart).turn == chess.BLACK
        return (index + (1 if noirs else 0)) // 2

    def _suivre_le_coup(self):
        if not hasattr(self, "lignes_visibles"):
            return
        total = self._ligne_du_coup(len(self.coups) - 1) + 1 if self.coups else 0
        if self.index == 0:
            self.premiere_ligne = 0
            return
        ligne = self._ligne_du_coup(self.index - 1)
        if ligne < self.premiere_ligne:
            self.premiere_ligne = ligne
        elif ligne >= self.premiere_ligne + self.lignes_visibles:
            self.premiere_ligne = ligne - self.lignes_visibles + 1
        self.premiere_ligne = max(0, min(self.premiere_ligne, total - self.lignes_visibles))

    # ------------------------------------------------------------- evenements

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return "quitter"
        if self.edition is not None:
            return self._evenement_edition(event)
        p = self.plateau
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            sur_le_plateau = pygame.Rect(self.disposition.rect_plateau()).collidepoint(event.pos)
            if sur_le_plateau or p.dragging or p.selected_square is not None \
                    or p.promotion.est_actif():
                p.handle_event(event)
                if event.type != pygame.MOUSEMOTION:
                    return None
        action = None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_v and event.mod & pygame.KMOD_CTRL:
                action = "coller"
            elif event.key == pygame.K_ESCAPE and (p.selected_square is not None or p.dragging):
                p.handle_event(event)
                return None
            else:
                action = {pygame.K_LEFT: "precedent", pygame.K_RIGHT: "suivant",
                          pygame.K_HOME: "debut", pygame.K_END: "fin",
                          pygame.K_UP: "debut", pygame.K_DOWN: "fin",
                          pygame.K_f: "retourner", pygame.K_SPACE: "moteur",
                          pygame.K_e: "editer", pygame.K_c: "copier",
                          pygame.K_ESCAPE: "retour"}.get(event.key)
        elif event.type == pygame.MOUSEWHEEL:
            action = "precedent" if getattr(event, "y", 0) > 0 else "suivant"
        else:
            action = ui.gerer_boutons(self.boutons_analyse, event)
            if action is None and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, rang in self.rects_lignes:
                    if rect.collidepoint(event.pos):
                        self.jouer_ligne(rang)
                        return None
                for rect, index in self.rects_coups:
                    if rect.collidepoint(event.pos):
                        self.aller_a(index + 1)
                        return None
        return self._action(action)

    def _action(self, action):
        if action == "retour":
            return "retour"
        if action == "precedent":
            self.aller_a(self.index - 1)
        elif action == "suivant":
            self.aller_a(self.index + 1, son=True)
        elif action == "debut":
            self.aller_a(0)
        elif action == "fin":
            self.aller_a(len(self.coups))
        elif action == "retourner":
            retournement.retourner(self.plateau, self.plateau.board, self.plateau.SQ_SIZE)
        elif action == "moteur":
            self.analyse.mettre_en_pause(self.analyse.actif)
            self._afficher_message("Stockfish en marche" if self.analyse.actif
                                   else "Stockfish à l'arrêt (Espace pour le relancer)")
        elif action == "editer":
            self.ouvrir_l_editeur()
        elif action == "coller":
            self.coller_texte(ui.coller())
        elif action == "copier":
            self.copier_fen()
        return None

    def _evenement_edition(self, event):
        e = self.edition
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.fermer_l_editeur(False)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.fermer_l_editeur(True)
            elif event.key == pygame.K_v and event.mod & pygame.KMOD_CTRL:
                self.coller_texte(ui.coller())
            return None
        action = ui.gerer_boutons(self.boutons_edition, event)
        if event.type != pygame.MOUSEBUTTONDOWN or event.button not in (1, 3):
            return None
        if action is None:
            case = self._case_sous(event.pos)
            if case is not None:
                e.clic(case, event.button)
                return None
            if event.button == 1:
                for rect, outil in self.rects_palette:
                    if rect.collidepoint(event.pos):
                        e.choisir_outil(outil)
                        return None
                for rect, masque in self.rects_roques:
                    if rect.collidepoint(event.pos):
                        e.basculer_roque(masque)
                        return None
            return None
        if action == "trait_blancs":
            e.changer_trait(chess.WHITE)
        elif action == "trait_noirs":
            e.changer_trait(chess.BLACK)
        elif action == "vider":
            e.vider()
        elif action == "depart":
            e.position_de_depart()
        elif action == "annuler":
            self.fermer_l_editeur(False)
        elif action == "valider":
            self.fermer_l_editeur(True)
        return None

    def _case_sous(self, pos):
        d = self.disposition
        if not pygame.Rect(d.rect_plateau()).collidepoint(pos):
            return None
        colonne = int((pos[0] - d.plateau_x) // d.taille_case)   # 24/10 : entier
        rangee = int((pos[1] - d.plateau_y) // d.taille_case)
        if self.plateau.flipped:
            return chess.square(7 - colonne, rangee)
        return chess.square(colonne, 7 - rangee)

    def _afficher_message(self, texte, secondes=5):
        self.message = texte
        self.message_fin = pygame.time.get_ticks() + int(secondes * 1000)

    # ------------------------------------------------------------- dessin

    def _marquer(self):
        """Fleches du moteur sur l'echiquier, recalculees a chaque image."""
        p = self.plateau
        p.fleches_conseil = []
        p.pastille_coup = p.pastille_case = p.indice = None
        lignes = self.lignes()
        if not lignes:
            return
        blancs = p.board.turn == chess.WHITE

        def du_trait(v):
            c = annotations.chances_de_gagner(v)
            return c if blancs else 100.0 - c

        import analyse_partie
        reference = du_trait(lignes[0]["evaluation"])
        for n, ligne in enumerate(lignes):
            if n and reference - du_trait(ligne["evaluation"]) > analyse_partie.SEUIL_EQUIVALENT:
                break
            coup = chess.Move.from_uci(ligne["uci"])
            p.fleches_conseil.append((coup.from_square, coup.to_square,
                                      BLEU_MEILLEUR if n == 0 else BLEU_AUSSI_BON,
                                      0.12 if n == 0 else 0.08))

    def draw(self):
        ecran = self.screen
        p = self.plateau
        t = apparence.theme(p.theme_plateau)
        ech = self.ech
        p.animation.update()
        p.retournement.update()
        if self.edition is None:
            self.analyse.regarder(self.position()["fen"])
            self._marquer()
        else:
            p.fleches_conseil = []
        ecran.blit(self._fond(t), (0, 0))
        p.renderer.dessiner_plateau(avec_interaction=self.edition is None)
        if self.edition is not None:
            self._dessiner_prise(ecran, t)
        evaluation, texte = self.evaluation() if self.edition is None else (None, "")
        dessiner_barre_avantage(ecran, self.disposition.barre, evaluation, texte,
                                p.flipped, t, ech)
        souris = pygame.mouse.get_pos()
        if self.edition is None:
            self._dessiner_titre(ecran, t, ech)
            self._dessiner_lignes(ecran, t, ech)
            self._dessiner_feuille(ecran, t, ech)
            self.boutons_nav[0].actif = self.boutons_nav[1].actif = self.index > 0
            self.boutons_nav[2].actif = self.boutons_nav[3].actif = self.index < len(self.coups)
            # A l'arret, le bouton s'allume en or : on voit tout de suite qu'il faut le relancer.
            self.btn_moteur.selectionne = not self.analyse.actif
            self.btn_moteur.libelle = "Pause (Espace)" if self.analyse.actif else "Relancer"
            boutons = self.boutons_analyse
        else:
            self._dessiner_editeur(ecran, t, ech)
            boutons = self.boutons_edition
        for bouton in boutons:
            bouton.maj_survol(souris)
            bouton.dessiner(ecran, t, rayon=10)
        import effets
        effets.fondu(ecran, "analyse_libre", t["fond"])

    def _fond(self, t):
        """Le fond, le panneau et ses cadres : ils ne bougent pas, on les dessine
        une fois par taille de fenetre et par ecran (analyse ou editeur)."""
        cle = (self.screen.get_size(), self.plateau.theme_plateau, t["panneau"], t["fond"],
               self.edition is None)
        if getattr(self, "_cache_fond", (None,))[0] != cle:
            fond = pygame.Surface(self.screen.get_size())
            fond.fill(t["fond"])
            ui.cadre(fond, self.panneau, t["panneau"], t["bord"], 1, 14)
            zones = (self.zone_lignes, self.zone_coups) if self.edition is None \
                else (self.zone_palette,)
            for zone in zones:
                ui.cadre(fond, zone, t["fond"], t["bord"], 1, 10)
            self._cache_fond = (cle, fond)
        return self._cache_fond[1]

    def _dessiner_titre(self, ecran, t, ech):
        zone = self.zone_titre
        ui.texte(ecran, "Analyse libre", zone.x, zone.y, ui.t(17, ech), t["texte"],
                 gras=True, largeur_max=zone.width)
        y = zone.y + ui.police(ui.t(17, ech), True).get_height() + int(4 * ech)
        if self.message and pygame.time.get_ticks() < self.message_fin:
            texte, couleur = self.message, t["accent"]
        else:
            texte, couleur = self.etat_du_moteur(), t["texte_discret"]
        ui.texte(ecran, texte, zone.x, y, ui.t(12, ech), couleur, largeur_max=zone.width)

    def etat_du_moteur(self):
        """La ligne d'etat sous le titre (phrases entieres : traduites en anglais)."""
        b, pos = self.plateau.board, self.position()
        trait = "Trait aux Blancs" if b.turn == chess.WHITE else "Trait aux Noirs"
        if pos["mat"]:
            return "Échec et mat"
        if pos["pat"]:
            return "Pat : partie nulle"
        if pos["finie"]:
            return "Partie nulle"
        if self.analyse.erreur:
            return self.analyse.erreur
        if not self.analyse.actif:
            return trait + "  ·  Stockfish à l'arrêt (Espace)"
        r = self.analyse.resultat(pos["fen"])
        if not r["profondeur"]:
            return trait + "  ·  Stockfish réfléchit..."
        if r["fini"]:
            return trait + "  ·  profondeur %d (analyse terminée)" % r["profondeur"]
        return trait + "  ·  profondeur %d" % r["profondeur"]

    def texte_d_une_ligne(self, ligne):
        """'12. Nf3 Nc6 13. Bb5' : la ligne du moteur, numerotee."""
        b = self.plateau.board
        numero, blancs = b.fullmove_number, b.turn == chess.WHITE
        morceaux = []
        for i, san in enumerate(ligne["suite_san"]):
            san = notation.afficher(san)
            if blancs:
                morceaux.append("%d. %s" % (numero, san))
            elif i == 0:
                morceaux.append("%d... %s" % (numero, san))
            else:
                morceaux.append(san)
            if not blancs:
                numero += 1
            blancs = not blancs
        return " ".join(morceaux)

    def _dessiner_lignes(self, ecran, t, ech):
        zone = self.zone_lignes
        self.rects_lignes = []
        x = zone.x + int(8 * ech)
        l = zone.width - int(16 * ech)
        y = zone.y + int(8 * ech)
        lignes = self.lignes()
        petite = ui.t(12, ech)
        souris = pygame.mouse.get_pos()
        for rang in range(analyse_continue.LIGNES):
            rect = pygame.Rect(x, y, l, self.h_ligne_moteur - int(4 * ech))
            if rang < len(lignes):
                ligne = lignes[rang]
                if rect.collidepoint(souris):
                    ui.cadre(ecran, rect, t["panneau"], t["accent"], 1, 6)
                case = pygame.Rect(rect.x, rect.y, int(64 * ech), rect.height)
                blancs_mieux = (ligne["evaluation"] or 0) >= 0
                ui.cadre(ecran, case, (232, 229, 220) if blancs_mieux else (58, 56, 52),
                         t["bord"], 1, 6)
                ui.texte_centre_dans(ecran, ligne["texte"], case, ui.t(13, ech),
                                     (40, 38, 34) if blancs_mieux else (232, 229, 220),
                                     gras=True, marge=4)
                ui.texte(ecran, self.texte_d_une_ligne(ligne), case.right + int(8 * ech),
                         rect.centery - ui.police(ui.t(13, ech)).get_height() // 2,
                         ui.t(13, ech), t["texte"] if rang == 0 else t["texte_discret"],
                         gras=rang == 0, largeur_max=rect.right - case.right - int(12 * ech))
                self.rects_lignes.append((rect, rang))
            elif rang == 0:
                texte = ("Plus de coup possible : la partie est finie." if self.position()["finie"]
                         else "Stockfish à l'arrêt : Espace pour le relancer."
                         if not self.analyse.actif else "Stockfish réfléchit...")
                ui.texte(ecran, texte, x, rect.centery - ui.police(petite).get_height() // 2,
                         petite, t["texte_discret"], largeur_max=l)
            y += self.h_ligne_moteur
        tables = analyse_continue.finale_des_tables(self.plateau.board)
        texte = tables or "Clique sur une ligne pour jouer son premier coup."
        ui.texte(ecran, texte, x, y + int(2 * ech), petite,
                 t["accent"] if tables else t["texte_discret"], largeur_max=l)

    def _dessiner_feuille(self, ecran, t, ech):
        zone = self.zone_coups
        self.rects_coups = []
        taille = self.taille_coup
        x0 = zone.x + int(8 * ech)
        y = zone.y + int(5 * ech)
        if not self.coups:
            ui.paragraphe(ecran, "Joue les coups des deux camps sur l'échiquier, colle un "
                                 "FEN ou une partie PGN (Ctrl+V), ou fabrique une position "
                                 "(Éditer).",
                          pygame.Rect(x0, y + int(4 * ech), zone.width - int(16 * ech),
                                      zone.height - int(10 * ech)),
                          ui.t(13, ech), t["texte_discret"])
            return
        depart = chess.Board(self.fen_depart)
        noirs = depart.turn == chess.BLACK
        sans = self._sans()
        larg_num = ui.mesurer("999.", taille, mono=True)[0] + int(4 * ech)
        colonne = max(40, (zone.width - larg_num - int(16 * ech)) // 2)
        total = self._ligne_du_coup(len(self.coups) - 1) + 1
        for ligne in range(self.premiere_ligne, min(total, self.premiere_ligne + self.lignes_visibles)):
            ui.texte(ecran, "%d." % (depart.fullmove_number + ligne), x0, y, taille,
                     t["texte_discret"], mono=True, largeur_max=larg_num)
            for demi in (0, 1):
                index = ligne * 2 + demi - (1 if noirs else 0)
                if index < 0 or index >= len(sans):
                    continue
                rect = pygame.Rect(x0 + larg_num + demi * colonne - int(3 * ech),
                                   y - int(2 * ech), colonne - int(4 * ech), self.hauteur_ligne)
                courant = index == self.index - 1
                if courant:
                    pygame.draw.rect(ecran, t["accent"], rect, border_radius=int(6 * ech))
                ui.texte(ecran, notation.afficher(sans[index]), rect.x + int(6 * ech), y, taille,
                         t["fond"] if courant else t["texte"], gras=courant,
                         largeur_max=rect.width - int(8 * ech))
                self.rects_coups.append((rect, index))
            y += self.hauteur_ligne

    def _sans(self):
        """La notation des coups joues, gardee tant que les coups ne changent pas."""
        cle = (self.fen_depart, tuple(self.coups))
        if getattr(self, "_cache_sans", (None,))[0] != cle:
            b, sans = chess.Board(self.fen_depart), []
            for coup in self.coups:
                sans.append(b.san(coup))
                b.push(coup)
            self._cache_sans = (cle, sans)
        return self._cache_sans[1]

    # --- l'editeur

    def _dessiner_prise(self, ecran, t):
        """La piece prise en main dans l'editeur (sans outil) : case surlignee."""
        case = self.edition.prise
        if case is None:
            return
        import board_geometry as geo
        rect = pygame.Rect(geo.rectangle_case(case, self.plateau.SQ_SIZE, self.plateau.flipped))
        pygame.draw.rect(ecran, t["accent"], rect, max(2, rect.width // 18))

    def _dessiner_editeur(self, ecran, t, ech):
        e = self.edition
        zone = self.zone_titre
        ui.texte(ecran, "Éditer la position", zone.x, zone.y, ui.t(17, ech), t["texte"],
                 gras=True, largeur_max=zone.width)
        aide = ("Choisis une pièce puis clique sur les cases. Clic droit : enlever."
                if e.outil else "Déplacer : clique une pièce puis sa nouvelle case.")
        ui.texte(ecran, aide, zone.x, zone.y + ui.police(ui.t(17, ech), True).get_height()
                 + int(4 * ech), ui.t(12, ech), t["texte_discret"], largeur_max=zone.width)
        # Palette : pieces blanches, pieces noires, et la gomme.
        palette = self.zone_palette
        self.rects_palette = []
        cote = min((palette.width - int(16 * ech)) // 7, (palette.height - int(16 * ech)) // 2)
        images = self._images_palette(cote)
        for r, couleur in enumerate((True, False)):
            for c, lettre in enumerate(ORDRE_PALETTE):
                symbole = lettre if couleur else lettre.lower()
                rect = pygame.Rect(palette.x + int(8 * ech) + c * cote,
                                   palette.y + int(8 * ech) + r * cote, cote, cote)
                self._case_palette(ecran, t, rect, e.outil == symbole)
                image = images.get(symbole)
                if image is not None:
                    ecran.blit(image, image.get_rect(center=rect.center))
                self.rects_palette.append((rect, symbole))
        # Derniere colonne : « Deplacer » (sans piece choisie) et la gomme.
        x7 = palette.x + int(8 * ech) + 6 * cote
        l7 = palette.right - int(8 * ech) - x7
        for r, (outil, libelle) in enumerate(((None, "Déplacer"), (OUTIL_GOMME, "Gomme"))):
            rect = pygame.Rect(x7, palette.y + int(8 * ech) + r * cote, l7, cote)
            choisi = e.outil == outil
            self._case_palette(ecran, t, rect, choisi, piece=False)
            ui.texte_centre_dans(ecran, libelle, rect.inflate(-4, -4), ui.t(12, ech),
                                 t["fond"] if choisi else t["texte"], marge=3)
            self.rects_palette.append((rect, outil))
        # Trait et roques
        self.btn_blancs.selectionne = e.plateau.turn == chess.WHITE
        self.btn_noirs.selectionne = e.plateau.turn == chess.BLACK
        self.rects_roques = []
        possibles = analyse_continue.roques_possibles(e.plateau)
        zone = self.zone_roques
        h = zone.height // 2
        for i, (masque, libelle) in enumerate((
                (chess.BB_H1, "Blancs : petit roque"), (chess.BB_A1, "Blancs : grand roque"),
                (chess.BB_H8, "Noirs : petit roque"), (chess.BB_A8, "Noirs : grand roque"))):
            x = zone.x + (i % 2) * (zone.width // 2)
            y = zone.y + (i // 2) * h
            case = pygame.Rect(x, y + (h - int(18 * ech)) // 2, int(18 * ech), int(18 * ech))
            dispo = bool(masque & possibles)
            theme = t if dispo else dict(t, texte=t["texte_discret"])
            rect = ui.case_a_cocher(ecran, case, bool(e.plateau.castling_rights & masque),
                                    libelle, theme, ui.t(12, ech),
                                    largeur_max=zone.width // 2 - int(30 * ech))
            if dispo:
                self.rects_roques.append((rect, masque))
        if e.message:
            ui.paragraphe(ecran, e.message, self.zone_message_edition, ui.t(13, ech),
                          (240, 120, 110))
        elif self.message and pygame.time.get_ticks() < self.message_fin:
            ui.paragraphe(ecran, self.message, self.zone_message_edition, ui.t(13, ech),
                          t["accent"])

    def _case_palette(self, ecran, t, rect, choisie, piece=True):
        """Les pieces sur une case claire du damier (les noires restent lisibles) ;
        l'outil choisi est entoure d'or."""
        fond = t["clair"] if piece else (t["accent"] if choisie else t["panneau"])
        ui.cadre(ecran, rect.inflate(-4, -4), fond, t["accent"] if choisie else t["bord"],
                 3 if choisie and piece else 1, 6)

    def _images_palette(self, cote):
        """Les pieces de la palette, a la taille voulue (calculees une fois)."""
        cle = (self.plateau.jeu_pieces, cote)
        if getattr(self, "_palette", (None,))[0] != cle:
            taille = max(8, int(cote * 0.82))
            images = {s: pygame.transform.smoothscale(i, (taille, taille))
                      for s, i in self.plateau.piece_images.items()}
            self._palette = (cle, images)
        return self._palette[1]

    # ------------------------------------------------------------- boucle

    def run(self, clock, evenement_fenetre=None, apres_dessin=None):
        """Renvoie 'retour' ou 'quitter'. Le moteur est ferme en sortant."""
        try:
            cadence = ui.Cadence()
            profondeur_vue = None
            while True:
                evenements = ui.evenements()
                for event in evenements:
                    if evenement_fenetre is not None and evenement_fenetre(event):
                        self._placer(pygame.display.get_surface())
                        continue
                    reponse = self.handle_event(event)
                    if reponse is not None:
                        return reponse
                self.draw()
                if apres_dessin is not None:
                    apres_dessin(self.screen)
                ui.afficher()
                # Une nouvelle profondeur compte comme du mouvement : l'ecran
                # suit le moteur sans dessiner 60 images/s pour rien.
                r = self.analyse.resultat()
                nouveau = (r["profondeur"], len(r["lignes"])) != profondeur_vue
                profondeur_vue = (r["profondeur"], len(r["lignes"]))
                anime = bool(getattr(self.plateau.animation, "animations", None))
                clock.tick(cadence.suivante(evenements, anime or nouveau))
        finally:
            self.analyse.arreter()
