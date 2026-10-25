# move_history.py - V6 : l'historique unique de la partie
#
# CE QUI CHANGE PAR RAPPORT A V5 (bugs C5 et m6 du rapport) :
#   1. DECALAGE D'UN CRAN CORRIGE. V5 faisait fens.append(board.fen()) AVANT de
#      jouer le coup : get_fen_at_move(3) renvoyait la position d'avant le
#      3e coup. Desormais fens[i] est la position APRES le coup i, et
#      fen_initiale garde la position de depart.
#   2. UN SEUL HISTORIQUE. V5 en avait trois qui ne se parlaient pas
#      (MoveHistory, ReplayManager, ReplayWindow) et aucun n'etait alimente
#      pour le replay. Celui-ci est desormais la seule source, remplie par
#      board.make_move pour TOUS les coups (humain, Stockfish et reseau).
#   3. La notation lisible (1. e4 e5 2. Cf3) est enregistree en meme temps.
#   4. detect_brilliant_blunder existe vraiment : pgn_exporter la cherchait
#      avec hasattr et ne la trouvait jamais.
#
# AUCUNE FONCTION SUPPRIMEE : add_move, get_move_count, get_fen_at_move,
# get_evaluation_at_move, export_pgn et clear sont conservees.

import chess
import freestyle

# Seuils en pions pour l'annotation automatique.
SEUIL_GAFFE = 1.5        # perte >= 1.5 pion  -> ?
SEUIL_ERREUR = 0.8       # perte >= 0.8 pion  -> ?!
SEUIL_BRILLANT = 1.0     # gain  >= 1.0 pion  -> !


class MoveHistory:
    """Gestion complete de l'historique des coups (replay, PGN, evaluations)."""

    def __init__(self, fen_initiale=None):
        self.fen_initiale = fen_initiale or chess.STARTING_FEN
        self.moves = []          # coups en UCI ("e2e4", "e7e8q")
        self.sans = []           # meme chose en notation lisible ("e4", "Cf3")
        self.fens = []           # FEN APRES chaque coup
        self.evaluations = []    # evaluation Stockfish apres chaque coup
        self.best_moves = []     # meilleur coup suggere par Stockfish
        self.horodatage = []     # temps de reflexion en millisecondes
        self.board = freestyle.plateau(self.fen_initiale)   # plateau interne

    # ------------------------------------------------------------------ ecriture

    def set_fen_initiale(self, fen):
        """Change la position de depart et vide l'historique."""
        self.fen_initiale = fen
        self.clear()

    def _resynchroniser(self, fen_avant):
        """Recale le plateau interne sur la vraie position.

        Utile quand la partie ne commence pas au debut (position chargee,
        board.set_fen appele a la main). Sans cela, tous les coups suivants
        seraient refuses comme "illegaux".
        """
        if fen_avant is None or fen_avant == self.board.fen():
            return
        if not self.moves:
            # Aucun coup encore joue : c'est simplement une autre position
            # de depart, on l'adopte sans rien perdre.
            self.fen_initiale = fen_avant
            self.board = freestyle.plateau(fen_avant)
        else:
            print("[HISTORIQUE] position modifiee en cours de partie, recalage")
            self.board = freestyle.plateau(fen_avant)

    def add_move(self, uci_move, evaluation=None, best_move=None, temps_ms=None,
                 fen_avant=None):
        """Ajoute un coup a l'historique (appele par board.make_move)."""
        try:
            move = chess.Move.from_uci(uci_move)
        except ValueError:
            print("[HISTORIQUE] coup illisible ignore : %r" % uci_move)
            return False
        self._resynchroniser(fen_avant)
        if move not in self.board.legal_moves:
            print("[HISTORIQUE] coup illegal ignore : %s" % uci_move)
            return False

        # La notation lisible doit etre calculee AVANT de jouer le coup.
        try:
            notation = self.board.san(move)
        except Exception:
            notation = uci_move

        self.board.push(move)

        self.moves.append(uci_move)
        self.sans.append(notation)
        self.fens.append(self.board.fen())      # position APRES le coup (bug m6)
        self.evaluations.append(evaluation)
        self.best_moves.append(best_move)
        self.horodatage.append(temps_ms)
        return True

    def set_evaluation(self, index, evaluation, best_move=None):
        """Renseigne l'evaluation d'un coup deja joue (analyse differee)."""
        if 0 <= index < len(self.evaluations):
            self.evaluations[index] = evaluation
            if best_move is not None:
                self.best_moves[index] = best_move

    def undo(self):
        """Retire le dernier coup (annulation)."""
        if not self.moves:
            return None
        self.board.pop()
        self.sans.pop()
        self.fens.pop()
        self.evaluations.pop()
        self.best_moves.pop()
        self.horodatage.pop()
        return self.moves.pop()

    def clear(self):
        """Vide l'historique (nouvelle partie)."""
        self.moves.clear()
        self.sans.clear()
        self.fens.clear()
        self.evaluations.clear()
        self.best_moves.clear()
        self.horodatage.clear()
        self.board = freestyle.plateau(self.fen_initiale)

    # ------------------------------------------------------------------ lecture

    def get_move_count(self):
        """Nombre total de demi-coups joues."""
        return len(self.moves)

    def get_move(self, index):
        if 0 <= index < len(self.moves):
            return self.moves[index]
        return None

    def get_fen_at_move(self, move_index):
        """FEN APRES le coup demande. -1 = position de depart."""
        if move_index < 0:
            return self.fen_initiale
        if move_index < len(self.fens):
            return self.fens[move_index]
        return self.fens[-1] if self.fens else self.fen_initiale

    def get_evaluation_at_move(self, move_index):
        """Evaluation apres le coup demande."""
        if 0 <= move_index < len(self.evaluations):
            return self.evaluations[move_index]
        return None

    def get_san_at_move(self, move_index):
        if 0 <= move_index < len(self.sans):
            return self.sans[move_index]
        return None

    def lignes_lisibles(self):
        """[(numero, coup blanc, coup noir), ...] pour l'affichage du replay."""
        lignes = []
        depart = freestyle.plateau(self.fen_initiale)
        numero = depart.fullmove_number
        blancs_commencent = depart.turn == chess.WHITE
        i = 0
        if not blancs_commencent and self.sans:
            lignes.append((numero, "...", self.sans[0]))
            numero += 1
            i = 1
        while i < len(self.sans):
            blanc = self.sans[i]
            noir = self.sans[i + 1] if i + 1 < len(self.sans) else ""
            lignes.append((numero, blanc, noir))
            numero += 1
            i += 2
        return lignes

    # ------------------------------------------------------------------ analyse

    def detect_brilliant_blunder(self, index):
        """Annotation automatique d'un coup a partir des evaluations.

        Cette methode etait appelee par pgn_exporter.py via hasattr() en V5,
        mais elle n'existait pas : l'annotation etait donc toujours vide.
        """
        if not (0 <= index < len(self.evaluations)):
            return ""
        apres = self.evaluations[index]
        avant = self.evaluations[index - 1] if index > 0 else 0.0
        if apres is None or avant is None:
            return ""

        # On se place du point de vue du camp qui vient de jouer.
        joue_par_les_blancs = (index % 2 == 0)
        variation = (apres - avant) if joue_par_les_blancs else (avant - apres)

        if variation <= -SEUIL_GAFFE:
            return "??"
        if variation <= -SEUIL_ERREUR:
            return "?!"
        if variation >= SEUIL_BRILLANT:
            return "!"
        return ""

    def resume_annotations(self):
        """Compte les gaffes et les bons coups des deux camps."""
        resume = {"blancs": {"!": 0, "?!": 0, "??": 0},
                  "noirs": {"!": 0, "?!": 0, "??": 0}}
        for i in range(len(self.moves)):
            note = self.detect_brilliant_blunder(i)
            if note:
                camp = "blancs" if i % 2 == 0 else "noirs"
                resume[camp][note] += 1
        return resume

    # ------------------------------------------------------------------ export

    def export_pgn(self, player_white="White", player_black="Black", result="*"):
        """Exporte la partie au format PGN (Chess.com, Lichess, SCID...)."""
        from pgn_exporter import PGNExporter
        return PGNExporter().export(self, player_white, player_black, result)
