# board.py - V7 : le plateau et l'etat de la partie
#
# CE QUI CHANGE PAR RAPPORT A LA V6 :
#   1. Le plateau connait sa DISPOSITION : position et taille des cases suivent
#      la fenetre (plein ecran, redimensionnement).
#   2. THEME et JEU DE PIECES : les couleurs et les pieces viennent de
#      apparence.py. Le jeu classique est dessine par le programme lui-meme,
#      donc il n'y a plus besoin d'aucun fichier image pour jouer.
#   3. PREMOUVEMENT : on peut jouer son coup pendant que l'adversaire reflechit.
#   4. INDICE : Stockfish peut montrer le meilleur coup avec une fleche verte.
#   5. annuler_selection() est accessible de l'exterieur : c'est ce qui permet
#      au clic droit d'annuler un deplacement en cours.
#
# AUCUNE FONCTION SUPPRIMEE : __init__, load_piece_images, update, draw,
# handle_event, make_move et terminer_partie sont conservees.

import chess

import apparence
import freestyle
from layout import Disposition
from board_render import BoardRender
from board_input import BoardInput
from board_animation import PieceAnimation
from retournement import Retournement
from board_highlights import Highlights
from board_last_move_highlight import LastMoveHighlight
from timer import ChessTimer
from sounds import SoundManager
from rules import ChessRules
from captured_pieces import CapturedPieces
from game_buttons import GameButtons
from move_history import MoveHistory
from board_right_click import RightClickManager
from move_handler import MoveHandler
from promotion_choice import PromotionChoice
from ui_manager import UIManager


class ChessBoard:
    def __init__(self, screen, reglages=None, disposition=None):
        self.reglages = reglages or {}
        self.screen = screen
        self.disposition = disposition or Disposition(*screen.get_size())
        self.SQ_SIZE = self.disposition.taille_case

        self.theme_plateau = self.reglages.get("theme_plateau",
                                               apparence.THEME_PAR_DEFAUT)
        self.jeu_pieces = self.reglages.get("jeu_pieces", apparence.JEU_PAR_DEFAUT)

        # Freestyle (echecs 960) : reglages["freestyle"] = numero de la position
        # de depart (0 a 959), None pour une partie normale.
        self.numero_freestyle = self.reglages.get("freestyle")
        if self.numero_freestyle is not None:
            self.board = freestyle.plateau_de_depart(self.numero_freestyle)
        else:
            self.board = chess.Board()
        # Freestyle, reglement de tournoi : pas de nulle avant le 40e coup des Noirs
        # et quelques minutes pour regarder la position avant de jouer.
        self.tournoi_fide = bool(self.reglages.get("tournoi_fide"))             and self.numero_freestyle is not None
        self.preparation = None
        duree = self.reglages.get("preparation_s", freestyle.PREPARATION_TOURNOI_S)
        if self.tournoi_fide and duree:
            self.preparation = freestyle.Preparation(
                duree, self.reglages.get("joueurs_preparation", 1))
        self.bouton_pret = None
        from effets import Effets
        self.effets = Effets()           # 17/10 (p13) : onde de prise, mat
        self.selected_square = None
        self.dragging = False
        self.drag_piece = None
        self.drag_pos = None
        self.legal_moves = []
        self.flipped = False
        self.ia_joue_blancs = False
        self.hotseat_mode = False
        self.couleur_joueur = None
        self.ai_manager = None
        # V7.2 : vrai quand on REGARDE la partie de quelqu'un d'autre. Aucune
        # piece n'est alors jouable, meme si personne ne "possede" le plateau.
        self.spectateur = False
        # V7.2 : partie COMPETITIVE (ton choix) - le classement bouge, l'indice
        # et l'annulation sont coupes, et la partie compte dans les statistiques.
        # Faux = partie amicale : rien de tout ca.
        self.competitive = False

        # Nouveautes V7
        self.indice = None            # (case_depart, case_arrivee) ou None
        # 31/10 (ta demande) : autant de coups d'avance qu'on veut, joues dans
        # l'ordre. `premove` reste le premier de la file (les ecrans s'en servent).
        self.premoves = []
        self._cache_premoves = (None, None)
        self.premouvement_actif = bool(self.reglages.get("premouvement", True))
        self.indices_utilises = 0
        self.engine = None            # renseigne par le mode Stockfish

        # Nouveautes V7.1
        self.chat = None              # Chat du mode en ligne (onglet du panneau)
        self.coup_fantome = None      # coup montre en transparence (replay)
        self.pastille_coup = None     # "gaffe", "meilleur"... (replay)
        self.pastille_case = None     # case ou poser la pastille

        self.sounds = SoundManager()
        self.last_move_highlight = LastMoveHighlight(self)
        self.highlights = Highlights(self)
        self.animation = PieceAnimation(self)
        # V7.2 (03/09) - LE RETOURNEMENT ANIME (ta demande : "ca se
        # teleporte, les pieces suivent l'echiquier"). Voir retournement.py.
        self.retournement = Retournement(self)

        self.timer = ChessTimer(
            minutes=self.reglages.get("minutes"),
            increment=self.reglages.get("increment"),
            active=self.reglages.get("pendule_active"),
        )
        self.timer.sons = self.sounds

        self.move_handler = MoveHandler(self)
        self.input = BoardInput(self)
        self.right_click_manager = RightClickManager(self)
        self.promotion = PromotionChoice(self)

        self.renderer = BoardRender(self)
        self.game_over = False
        self.result = None
        self.game_over_reason = None
        self.ui_manager = UIManager(self)
        self.captured_pieces = CapturedPieces(self)
        self.game_buttons = GameButtons(self)
        self.move_history = MoveHistory(self.board.fen())

        self.piece_images = {}
        self.load_piece_images()
        # La relecture d'une partie (ecran_revoir.py) cree un plateau muet.
        if self.reglages.get("son_de_depart", True):
            self.sounds.play("game_start")

    # ------------------------------------------------------------------ visuel

    def appliquer_disposition(self, disposition):
        """Recalcule tout quand la fenetre change de taille."""
        self.disposition = disposition
        if disposition.taille_case != self.SQ_SIZE:
            self.SQ_SIZE = disposition.taille_case
            self.load_piece_images()
            self.captured_pieces._cache.clear()
        return self

    def changer_apparence(self, theme=None, jeu=None):
        """Change le theme du plateau et/ou le jeu de pieces, en pleine partie."""
        if theme:
            self.theme_plateau = theme
        if jeu and jeu != self.jeu_pieces:
            self.jeu_pieces = jeu
            self.load_piece_images()
            self.captured_pieces._cache.clear()
        return self

    def load_piece_images(self):
        """Charge les douze pieces du jeu choisi, a la taille des cases."""
        self.piece_images = apparence.charger_jeu(self.jeu_pieces, self.SQ_SIZE)
        if len(self.piece_images) < 12:
            print("[PIECES] jeu incomplet (%d/12)" % len(self.piece_images))

    # ------------------------------------------------------------------ boucle

    def update(self):
        self.input.update()
        self.animation.update()
        self.retournement.update()

        if not self.game_over:
            perdant = self.timer.update(self.board.turn)
            if perdant is not None:
                # V7.2 - TA REMARQUE : "j'ai deja perdu au temps alors que mon
                # ami etait encore en train de jouer".
                #
                # En partie en ligne, les deux machines comptaient chacune de
                # leur cote et terminaient la partie chacune de leur cote. Avec
                # la derive du reseau, l'une pouvait declarer la fin pendant que
                # l'autre laissait encore jouer.
                #
                # Maintenant, quand un arbitre de pendule est branche (et il ne
                # l'est QUE en ligne), on lui demande la permission : notre
                # propre pendule, on l'annonce tout de suite ; celle d'en face,
                # on attend son message - ou la marge reseau s'il ne dit rien.
                # Hors ligne, arbitre_pendule vaut None et rien ne change.
                arbitre = getattr(self, "arbitre_pendule", None)
                if arbitre is not None and not arbitre.peut_declarer(perdant):
                    # Ce n'est pas a nous de le dire : on remet le drapeau et on
                    # attend. La pendule reste a 0:00 a l'ecran, ce qui est la
                    # verite.
                    self.timer.perdant_au_temps = None
                else:
                    if arbitre is not None \
                            and perdant == getattr(arbitre, "couleur_locale", None):
                        arbitre.annoncer_notre_defaite()
                    # Regle FIDE 6.9 : nulle si l'adversaire ne peut plus mater.
                    self.terminer_partie(*ChessRules.fin_au_temps(self.board, perdant))
                    return

        if not self.game_over and self.board.is_check():
            self.highlights.set_case_echec(self.board.king(self.board.turn))
        else:
            self.highlights.set_case_echec(None)

        # 25/10 - TA REMARQUE (ton ami contre l'ordinateur) : « repetition 2 fois
        # en jaune, puis le dernier coup, le message s'efface et la nulle ne
        # compte pas ». Le coup prepare d'avance partait AVANT qu'on regarde si
        # la partie etait finie : quand l'ordinateur ramenait la position une
        # 3e fois, ton pre-mouvement etait joue aussitot, la position changeait
        # et la repetition passait a la trappe. On regarde d'abord si la partie
        # est finie, et seulement ensuite on joue le coup prepare.
        if self._verifier_fin():
            return

        # Le coup prepare d'avance part des que c'est notre tour.
        if self.jouer_premouvement():
            self._verifier_fin()

    def _verifier_fin(self):
        """Termine la partie si une regle l'arrete (mat, pat, nulles). True si finie."""
        if self.game_over:
            return True
        fini, raison = ChessRules.check_game_over(self.board)
        if fini:
            self.terminer_partie(raison)
        return fini

    def draw(self):
        self.renderer.draw()
        if self.en_preparation():
            self._dessiner_preparation()

    def handle_event(self, event, engine=None):
        if self.en_preparation():
            self._evenement_preparation(event)
            return
        self.input.handle_event(event, engine or self.engine)

    # ------------------------------------------------------ preparation (FIDE)

    def en_preparation(self):
        return self.preparation is not None and not self.game_over             and self.preparation.en_cours()

    def _evenement_preparation(self, event):
        """Pendant la preparation, on ne joue pas : seul « Je suis prêt »
        (clic, Entree ou Espace) compte."""
        import pygame
        touche = event.type == pygame.KEYDOWN and event.key in (
            pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER)
        clic = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.bouton_pret is not None
                and self.bouton_pret.contient(event.pos))
        if self.bouton_pret is not None and event.type == pygame.MOUSEMOTION:
            self.bouton_pret.maj_survol(event.pos)
        if (touche or clic) and "local" not in self.preparation.prets:
            self.preparation.pret("local")
            rappel = getattr(self, "quand_pret", None)
            if rappel is not None:
                rappel()

    def _dessiner_preparation(self):
        import ui
        d = self.disposition
        ech = ui.echelle(self.screen)
        t = apparence.theme(self.theme_plateau)
        zone = (d.plateau_x, d.plateau_y, d.cote_plateau, d.cote_plateau)
        hauteur = int(150 * ech)
        bandeau = (zone[0] + int(20 * ech), zone[1] + (zone[3] - hauteur) // 2,
                   zone[2] - int(40 * ech), hauteur)
        ui.cadre(self.screen, bandeau, t.get("fond"), t.get("accent"), 2, 12)
        x, y, largeur, _ = bandeau
        ui.texte(self.screen, self.preparation.texte(), x + largeur // 2,
                 y + int(14 * ech), ui.t(26, ech), t.get("texte"), gras=True,
                 ancre="centre", mono=True, largeur_max=largeur - 20)
        attente = "local" in self.preparation.prets
        ui.texte(self.screen, "Prêt : on attend ton adversaire..." if attente
                 else "Regarde la position. La pendule part au premier coup.",
                 x + largeur // 2, y + int(52 * ech), ui.t(15, ech),
                 t.get("texte_discret"), ancre="centre", largeur_max=largeur - 20)
        if self.bouton_pret is None:
            self.bouton_pret = ui.Bouton((0, 0, 10, 10), "Je suis prêt", "pret")
        l_bouton = min(largeur - 40, int(240 * ech))
        self.bouton_pret.placer((x + (largeur - l_bouton) // 2,
                                 y + hauteur - int(58 * ech), l_bouton, int(44 * ech)))
        self.bouton_pret.taille = ui.t(18, ech)
        self.bouton_pret.actif = not attente
        self.bouton_pret.dessiner(self.screen, t)

    # ------------------------------------------------------ premouvement / indice

    def cest_mon_tour(self):
        """Le joueur humain a-t-il le trait ?"""
        # V7.2 : en spectateur, ce n'est jamais notre tour - on regarde.
        if getattr(self, "spectateur", False):
            return False
        if self.couleur_joueur is not None:
            return self.board.turn == self.couleur_joueur
        if self.hotseat_mode:
            return True
        if self.ai_manager is not None:
            return self.board.turn != (chess.WHITE if self.ia_joue_blancs else chess.BLACK)
        return True

    @property
    def premove(self):
        """Le prochain coup prepare d'avance (le premier de la file), ou None."""
        return self.premoves[0] if self.premoves else None

    @premove.setter
    def premove(self, move):
        self.premoves = [] if move is None else [move]

    def couleur_premouvement(self):
        """La couleur qui prepare ses coups : la notre, l'adversaire a le trait."""
        couleur = self.move_handler.couleur_du_joueur()
        return (not self.board.turn) if couleur is None else couleur

    def plateau_premouvements(self):
        """La position si tous les coups prepares passent, notre camp au trait.

        On ne sait pas ce que l'adversaire jouera entre deux : chaque coup
        prepare est joue a la suite, comme si c'etait encore a nous. Gardee en
        memoire tant que la position et la file ne changent pas (le dessin la
        demande a chaque image)."""
        cle = (self.board.fen(), tuple(self.premoves))
        if self._cache_premoves[0] == cle:
            return self._cache_premoves[1]
        couleur = self.couleur_premouvement()
        hypothese = self.board.copy(stack=False)
        for coup in self.premoves:
            hypothese.turn = couleur
            hypothese.ep_square = None
            hypothese.push(coup)
        hypothese.turn = couleur
        hypothese.ep_square = None
        self._cache_premoves = (cle, hypothese)
        return hypothese

    def coups_premouvement(self, case):
        """Coups qu'on peut preparer depuis une case de la position d'avance.

        Coups « possibles » et non « legaux » : un clouage ou un echec peut
        disparaitre avec le coup adverse. Le vrai controle se fait quand le coup
        part (jouer_premouvement)."""
        hypothese = self.plateau_premouvements()
        return [m for m in hypothese.generate_pseudo_legal_moves(
                    from_mask=chess.BB_SQUARES[case])
                if hypothese.piece_type_at(m.to_square) != chess.KING]

    def definir_premouvement(self, move):
        """Ajoute un coup au bout de la file des coups prepares d'avance."""
        if not self.premouvement_actif:
            return False
        self.premoves.append(move)
        return True

    def annuler_premouvement(self):
        """Oublie TOUS les coups prepares d'avance (clic droit, Echap)."""
        self.premoves = []

    def jouer_premouvement(self):
        """Joue le premier coup prepare d'avance, s'il est devenu legal.

        Les suivants attendent nos prochains tours. Si le coup est devenu
        impossible, toute la file est oubliee : la suite reposait dessus."""
        if not self.premoves or self.game_over or not self.cest_mon_tour():
            return False
        coup = self.premoves.pop(0)
        if coup in self.board.legal_moves:
            self.make_move(coup, self.engine)
            return True
        self.premoves = []
        self.sounds.play("illegal")
        return False

    def demander_indice(self, engine=None, temps_ms=400):
        """Fait chercher le meilleur coup par Stockfish et l'affiche en fleche."""
        # V7.2 - PARTIE COMPETITIVE : pas d'indice. C'est ton choix, et il vaut
        # pour les deux joueurs : une partie qui compte au classement ne se
        # joue pas avec le moteur qui souffle les coups.
        if getattr(self, "competitive", False):
            self.indice = None
            print("[INDICE] refuse : partie competitive")
            return None
        moteur = engine or self.engine
        if moteur is None or self.game_over:
            self.indice = None
            return None
        try:
            # V7.2 : a bas classement, le moteur de JEU choisit expres un coup
            # de debutant (faiblesse.py). L'indice, lui, doit donner le MEILLEUR
            # coup - sinon il souffle une betise. On le lui demande explicitement.
            uci = None
            if hasattr(moteur, "meilleur_coup_honnete"):
                honnete = moteur.meilleur_coup_honnete(self.board.fen(),
                                                       temps_ms)
                if honnete:
                    uci = honnete.get("coup")
            if not uci:
                uci = moteur.get_best_move(self.board.fen(), temps_ms)
        except Exception as e:
            print("[INDICE] impossible : %s" % e)
            return None
        if not uci:
            return None
        coup = chess.Move.from_uci(uci)
        self.indice = (coup.from_square, coup.to_square)
        self.indices_utilises += 1
        print("[INDICE] meilleur coup : %s (%d indices utilises)"
              % (uci, self.indices_utilises))
        return coup

    def effacer_indice(self):
        self.indice = None

    def annuler_selection(self):
        """Annule le deplacement en cours et remet la piece a sa place."""
        self.move_handler._annuler_selection()

    # ------------------------------------------------------------------ fin

    def terminer_partie(self, reason, result=None):
        if self.game_over:
            return
        self.game_over = True
        self.game_over_reason = reason
        if result is not None:
            self.result = result
        elif self.board.is_checkmate() or self._raison_est_un_mat(reason):
            self.result = "1-0" if self.board.turn == chess.BLACK else "0-1"
        else:
            self.result = "1/2-1/2"

        self.timer.pause()
        if self.board.is_checkmate():
            gagnant = not self.board.turn
            moi = getattr(self, "couleur_joueur", None)
            if getattr(self, "ai_manager", None) is not None and moi is None:
                moi = chess.BLACK if getattr(self, "ia_joue_blancs", False) else chess.WHITE
            self.effets.mat(self.board.king(self.board.turn),
                            confettis=moi is None or moi == gagnant)
        self.highlights.clear_legal_moves()
        self.promotion.fermer()
        self.premove = None
        self.indice = None
        if self.ai_manager is not None and hasattr(self.ai_manager, "stop"):
            self.ai_manager.stop()

        raison_majuscule = (reason or "").upper().replace("É", "E")
        if "PAT" in raison_majuscule and "MAT" not in raison_majuscule:
            self.sounds.play("stalemate")
        elif "50" in raison_majuscule:
            self.sounds.play("fifty_moves")
        elif "REPETITION" in raison_majuscule:
            self.sounds.play("repetition")
        else:
            self.sounds.play("game_end")
        print("[GAME OVER] %s (%s)" % (reason, self.result))

    @staticmethod
    def _raison_est_un_mat(reason):
        if not reason:
            return False
        texte = reason.upper().replace("É", "E").replace("È", "E")
        return "ECHEC ET MAT" in texte

    # ------------------------------------------------------------------ coups

    def make_move(self, move, engine=None):
        """Joue un coup. Utilise pour le joueur, pour Stockfish et pour le reseau."""
        if move not in self.board.legal_moves:
            self.sounds.play("illegal")
            return False

        piece_deplacee = self.board.piece_at(move.from_square)
        capturee = self.board.piece_at(move.to_square)
        est_en_passant = self.board.is_en_passant(move)
        est_roque = self.board.is_castling(move)
        couleur_joueuse = self.board.turn
        fen_avant = self.board.fen()

        # Roque : le roi « prend » sa propre tour (notation Freestyle) - ce
        # n'est pas une prise. Le roi arrive en g / c, la tour en f / d.
        roque = freestyle.cases_du_roque(self.board, move) if est_roque else None
        if roque is not None:
            capturee = None

        if est_en_passant and capturee is None:
            direction = -8 if piece_deplacee.color == chess.WHITE else 8
            capturee = self.board.piece_at(move.to_square + direction)

        self.board.push(move)

        self.timer.demarrer()
        self.timer.ajouter_increment(couleur_joueuse)
        self.move_history.add_move(move.uci(), fen_avant=fen_avant)

        if capturee:
            self.captured_pieces.add_captured(capturee)
            self.effets.prise(move.to_square)

        arrivee = roque[0] if roque is not None else move.to_square
        self.last_move_highlight.set_last_move(move.from_square, arrivee)
        self.highlights.set_last_move(move.from_square, arrivee)
        self.highlights.clear_legal_moves()
        self.indice = None

        if self.right_click_manager is not None:
            self.right_click_manager.clear()

        piece_arrivee = self.board.piece_at(arrivee)
        self.animation.start_animation(move.from_square, arrivee,
                                       piece_arrivee, self.SQ_SIZE)
        if roque is not None and roque[1] != roque[2]:
            self.animation.start_animation(roque[1], roque[2],
                                           self.board.piece_at(roque[2]),
                                           self.SQ_SIZE)

        self._jouer_son_du_coup(move, piece_deplacee, capturee,
                                est_roque, est_en_passant)
        return True

    def _jouer_son_du_coup(self, move, piece_deplacee, capturee,
                           est_roque, est_en_passant):
        """UN SEUL son par coup, du plus important au plus anodin."""
        if self.board.is_checkmate():
            self.sounds.play("checkmate")
            return
        if self.board.is_check():
            self.sounds.play("check")
            return
        if move.promotion:
            self.sounds.play("promotion")
            return
        if est_roque:
            self.sounds.play("castling")
            return
        if est_en_passant:
            self.sounds.play("en_passant")
            return
        if capturee:
            self.sounds.play("capture")
            return

        sons_par_piece = {
            chess.KNIGHT: "knight_move", chess.BISHOP: "bishop_move",
            chess.ROOK: "rook_move", chess.QUEEN: "queen_move",
            chess.KING: "king_move",
        }
        if piece_deplacee is not None:
            self.sounds.play(sons_par_piece.get(piece_deplacee.piece_type, "move"))
        else:
            self.sounds.play("move")
