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
# AUCUNE FONCTION SUPPRIMEE : export() et save_to_file() sont conservees,
# memes noms, memes signatures.

import datetime
import os

import chess
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
        game.headers["Variant"] = "Standard"
        if fen_initiale != chess.STARTING_FEN:
            game.headers["FEN"] = fen_initiale
            game.headers["SetUp"] = "1"

        node = game
        plateau = chess.Board(fen_initiale)
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

    def save_to_file(self, move_history, filename=None,
                     white_name="White", black_name="Black", result="*"):
        """Sauvegarde le PGN. Renvoie le chemin du fichier ecrit."""
        pgn = self.export(move_history, white_name, black_name, result)

        if filename is None:
            dossier = os.path.join(os.getcwd(), "parties")
            try:
                os.makedirs(dossier, exist_ok=True)
            except OSError:
                dossier = os.getcwd()
            horodatage = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%M%S")
            filename = os.path.join(dossier, "partie_%s.pgn" % horodatage)

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(pgn)
            print("[PGN EXPORTER] Fichier sauvegarde : %s" % filename)
            return filename
        except OSError as e:
            print("[PGN EXPORTER] Sauvegarde impossible : %s" % e)
            return None
