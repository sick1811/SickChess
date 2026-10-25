# rules.py
import chess

class ChessRules:
    """Toutes les règles du jeu (fin de partie + prise en passant)"""

    @staticmethod
    def check_game_over(board: chess.Board):
        """Détection complète de fin de partie.

        V7.2 - CORRECTION DU PAT ET DE LA RÉPÉTITION (ta remarque).

        Ce que faisait la V7.1, et pourquoi c'était faux :
            board.can_claim_threefold_repetition()
            board.can_claim_fifty_moves()
        Ces deux fonctions de python-chess ne disent PAS « la règle est
        atteinte ». Elles disent « le joueur au trait POURRAIT réclamer la
        nulle » — ce qui est vrai **dès qu'un de ses coups légaux permettrait
        d'y arriver**. Autrement dit elles répondent oui UN COUP TROP TÔT.

        Conséquence concrète : la partie s'arrêtait sur « RÉPÉTITION TRIPLE »
        alors que la position n'avait été vue que deux fois — et tout ce qui
        devait arriver ensuite (le pat que tu allais provoquer, le mat que tu
        allais donner) n'arrivait jamais. C'est ton « le pat n'est pas pris en
        compte ».

        Elles étaient aussi très lentes : pour répondre, elles jouent et
        annulent TOUS les coups légaux, à chaque image du jeu.

        Ici on regarde ce qui s'est VRAIMENT passé :
            is_repetition(3)   la position a été vue trois fois, point.
            is_fifty_moves()   cent demi-coups sans prise ni poussée de pion.
        Et on ajoute les deux règles qui, elles, s'appliquent d'office selon
        la FIDE, sans que personne n'ait à réclamer : cinq répétitions et
        soixante-quinze coups.

        L'ORDRE COMPTE : mat, puis pat, puis matériel, et seulement ensuite les
        règles de nulle par répétition. Un pat est un pat, même si la position
        s'était déjà répétée.
        """
        if board.is_checkmate():
            winner = "Noir" if board.turn == chess.WHITE else "Blanc"
            return True, f"ÉCHEC ET MAT ! {winner} gagne"

        if board.is_stalemate():
            return True, "PAT ! Match nul"

        if board.is_insufficient_material():
            return True, "MATÉRIEL INSUFFISANT - Match nul"

        # --- Règles automatiques de la FIDE : personne n'a à les réclamer.
        if ChessRules._compte_repetitions(board, 5):
            return True, "CINQ RÉPÉTITIONS - Match nul"

        if ChessRules._compte_coups_sans_prise(board, 150):
            return True, "RÈGLE DES 75 COUPS - Match nul"

        # --- Règles réclamables : ici le jeu réclame pour toi, mais seulement
        # une fois qu'elles sont RÉELLEMENT atteintes.
        if ChessRules._compte_coups_sans_prise(board, 100):
            return True, "RÈGLE DES 50 COUPS - Match nul"

        if ChessRules._compte_repetitions(board, 3):
            return True, "RÉPÉTITION TRIPLE - Match nul"

        return False, ""

    @staticmethod
    def fin_au_temps(board, perdant):
        """Le drapeau du camp `perdant` est tombe : (raison, resultat).

        Regle FIDE 6.9 : si l'adversaire ne peut mater par AUCUNE suite de
        coups legaux (roi seul, roi + fou, roi + cavalier...), c'est nulle.
        Roi + deux cavaliers peuvent mater : la defaite reste.
        """
        camp = "BLANCS" if perdant == chess.WHITE else "NOIRS"
        if board.has_insufficient_material(not perdant):
            return ("TEMPS ÉCOULÉ - mais l'adversaire ne peut plus mater : match nul",
                    "1/2-1/2")
        return ("TEMPS ÉCOULÉ - les %s perdent au temps" % camp,
                "0-1" if perdant == chess.WHITE else "1-0")

    @staticmethod
    def _compte_repetitions(board, combien):
        """La position a-t-elle DÉJÀ été vue `combien` fois ?

        On n'utilise surtout pas can_claim_threefold_repetition() : elle
        répond oui dès qu'un coup permettrait d'y arriver, donc un coup trop
        tôt. is_repetition() regarde ce qui s'est vraiment passé.
        """
        try:
            return bool(board.is_repetition(combien))
        except (AttributeError, TypeError):
            # Très vieux python-chess : on se rabat sur ce qui existe, en
            # acceptant l'approximation plutôt que de ne rien détecter.
            if combien <= 3:
                try:
                    return bool(board.can_claim_threefold_repetition())
                except AttributeError:
                    return False
            try:
                return bool(board.is_fivefold_repetition())
            except AttributeError:
                return False

    @staticmethod
    def _compte_coups_sans_prise(board, demi_coups):
        """`demi_coups` demi-coups sans prise ni poussée de pion, réellement."""
        try:
            return int(board.halfmove_clock) >= int(demi_coups)
        except (AttributeError, TypeError, ValueError):
            try:
                return bool(board.is_fifty_moves()) if demi_coups <= 100 \
                    else bool(board.is_seventyfive_moves())
            except AttributeError:
                return False

    @staticmethod
    def is_legal_move(board: chess.Board, from_square, to_square):
        """Vérifie si le coup est légal"""
        move = chess.Move(from_square, to_square)
        if move in board.legal_moves:
            return True, ""
        
        if board.is_check():
            return False, "Vous êtes en échec !"
        if board.piece_at(from_square) is None:
            return False, "Aucune pièce à cet endroit"
        if board.piece_at(from_square).color != board.turn:
            return False, "Ce n'est pas votre tour"
        
        return False, "Ce mouvement n'est pas autorisé"

    @staticmethod
    def is_en_passant(board: chess.Board, move: chess.Move):
        """Détecte si le coup est une prise en passant"""
        return board.is_en_passant(move)