# mode_hotseat.py - V6 : Mode 2 - deux joueurs sur le meme PC
#
# CE QUI CHANGE PAR RAPPORT A V5 :
# Le mode fonctionnait deja (c'etait le seul mode a deux joueurs operationnel).
# Deux ajouts :
#   - Option "plateau qui tourne" : a chaque coup, le plateau se retourne pour
#     que le joueur au trait soit toujours en bas. Reglable dans config.json
#     avec "hotseat_retourner_plateau" (false par defaut : on garde le
#     comportement de la V5 tant que tu n'y touches pas).
#   - couleur_joueur remis a None explicitement, sinon une partie en ligne
#     precedente pouvait laisser une couleur imposee.
#
# AUCUNE FONCTION SUPPRIMEE : __init__(board) et update() sont conservees.

import json
import os

import chess
import retournement


def _retourner_configure():
    for dossier in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        chemin = os.path.join(dossier, "config.json")
        if os.path.exists(chemin):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    contenu = json.load(f)
            # JOURNEE DEBUG DU 04/09 : un config.json coupe en plein
            # milieu (coupure de courant, disque plein) contient
            # "null" ou "[]". json.load() ne bronche pas, et le .get()
            # qui suit levait un AttributeError QUE PERSONNE N'ATTRAPAIT :
            # le jeu ne demarrait plus. Un fichier qui n'est pas un
            # dictionnaire vaut desormais un fichier absent.
                if not isinstance(contenu, dict):
                    return True
                return bool(contenu.get("hotseat_retourner_plateau", True))
            except (ValueError, OSError):
                return True
    return True


class ModeHotseat:
    def __init__(self, board, retourner=None):
        print("[INFO] Mode Ami Local - 2 joueurs sur le meme PC")
        self.board = board
        self.board.ia_joue_blancs = False
        self.board.ai_manager = None
        self.board.hotseat_mode = True     # Active le mode libre
        self.board.couleur_joueur = None
        self.board.flipped = False
        self.retourner = _retourner_configure() if retourner is None else bool(retourner)
        self._dernier_trait = self.board.board.turn

    def update(self):
        # Pas d'IA : juste les deux joueurs.
        if not self.retourner:
            return
        trait = self.board.board.turn
        if trait != self._dernier_trait:
            self._dernier_trait = trait
            # Le joueur au trait se retrouve toujours en bas de l'ecran.
            # V7.2 (03/09) : en glissant, pas d'un coup - c'est ici que le
            # saut se voyait le plus, puisque le plateau tourne a CHAQUE coup.
            retournement.orienter(self.board, trait == chess.BLACK)

    def arreter(self):
        pass
