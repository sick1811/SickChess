# board_input.py - V6
#
# CE QUI CHANGE PAR RAPPORT A V5 :
# En V5, board_input.py et move_handler.py contenaient DEUX FOIS la meme
# logique de saisie, avec des differences (move_handler jouait le son "coup
# interdit", board_input non), et move_handler n'etait jamais importe.
# BoardInput reste la porte d'entree utilisee par ChessBoard - rien n'est
# supprime - mais il delegue desormais a MoveHandler. Une seule logique, plus
# de risque que les deux divergent.
#
# AUCUNE FONCTION SUPPRIMEE : handle_event(event, engine),
# get_square_from_mouse(pos) et update() sont conservees.

import board_geometry as geo
from move_handler import MoveHandler


class BoardInput:
    def __init__(self, chessboard):
        self.chessboard = chessboard
        # Un seul MoveHandler pour tout le plateau : ChessBoard peut aussi
        # utiliser chessboard.move_handler directement.
        handler = getattr(chessboard, "move_handler", None)
        if handler is None:
            handler = MoveHandler(chessboard)
            chessboard.move_handler = handler
        self.handler = handler

    def handle_event(self, event, engine):
        self.handler.handle_move_input(event, engine)

    def get_square_from_mouse(self, pos):
        return geo.pixel_vers_case(pos, self.chessboard.SQ_SIZE,
                                   self.chessboard.flipped)

    def update(self):
        pass
