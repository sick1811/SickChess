# pgn_exporter.py - V6 : export de la partie au format PGN
#
# CE QUI CHANGE PAR RAPPORT A V5 :
#   1. IL N'ETAIT APPELE NULLE PART. La classe existait, fonctionnait a peu
#      pres, et aucun bouton ne la declenchait. Elle est maintenant branchee
#      sur le bouton "EXPORTER EN PGN" de l'ecran de fin de partie.
#   2. detect_brilliant_blunder est cherchee avec hasattr() : en V5 elle
#      n'existait pas dans MoveHistory, donc l'annotation etait toujours vide.
#      Elle existe desormais (voir move_history.py) et les ?! et ?? apparaissent.
#   3. save_to_file range les parties dans un sous-dossier "parties" avec la
#      date et l'heure, au lieu d'ecraser partie.pgn a chaque fois.
#   4. Le PGN part de la position initiale reelle (utile si la partie ne
#      commence pas au debut).
#
# 31/10 (menage) : save_to_file, jamais appelee (l'export passe par
# export()), est retiree.

import datetime

import chess
import freestyle
import chess.pgn


class PGNExporter:
    """Exporte la partie au format PGN professionnel."""

    def __init__(self):
        pass

    def export(self, move_history, white_name="White", black_name="Black", result="*"):
        """Cree un PGN complet avec les evaluations et les annotations."""
        fen_initiale = getattr(move_history, "fen_initiale", chess.STARTING_FEN)

        game = chess.pgn.Game()
        game.headers["Event"] = "SickChess"
        game.headers["Site"] = "Local"
        game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
        game.headers["Round"] = "1"
        game.headers["White"] = white_name
        game.headers["Black"] = black_name
        game.headers["Result"] = result
        game.headers["Variant"] = ("Chess960" if freestyle.est_freestyle_fen(fen_initiale)
                                   else "Standard")
        if fen_initiale != chess.STARTING_FEN:
            game.headers["FEN"] = fen_initiale
            game.headers["SetUp"] = "1"

        node = game
        plateau = freestyle.plateau(fen_initiale)
        for i, uci in enumerate(move_history.moves):
            try:
                move = chess.Move.from_uci(uci)
            except ValueError:
                break
            if move not in plateau.legal_moves:
                print("[PGN EXPORTER] coup %s ignore (illegal a ce stade)" % uci)
                break
            node = node.add_variation(move)
            plateau.push(move)

            commentaires = []
            evaluations = getattr(move_history, "evaluations", [])
            if i < len(evaluations) and evaluations[i] is not None:
                commentaires.append("[%%eval %+.2f]" % evaluations[i])

            if hasattr(move_history, "detect_brilliant_blunder"):
                annotation = move_history.detect_brilliant_blunder(i)
                if annotation:
                    commentaires.append(annotation)

            if commentaires:
                node.comment = " ".join(commentaires)

        pgn_string = str(game)
        print("[PGN EXPORTER] Partie exportee (%d coups)" % len(move_history.moves))
        return pgn_string
