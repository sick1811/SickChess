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
        self.premove = None           # chess.Move joue d'avance
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

    def handle_event(self, event, engine=None):
        self.input.handle_event(event, engine or self.engine)

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

    def definir_premouvement(self, move):
        if not self.premouvement_actif:
            return False
        self.premove = move
        return True

    def annuler_premouvement(self):
        self.premove = None

    def jouer_premouvement(self):
        """Joue le coup prepare d'avance, s'il est devenu legal."""
        if self.premove is None or self.game_over or not self.cest_mon_tour():
            return False
        coup = self.premove
        self.premove = None
        if coup in self.board.legal_moves:
            self.make_move(coup, self.engine)
            return True
        # Coup devenu impossible : on l'oublie, comme sur chess.com.
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
