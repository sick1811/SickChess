# ui_manager.py - V6 : bouton "abandonner" en haut a droite
#
# CE QUI CHANGE PAR RAPPORT A V5 :
# En V5 la classe existait, board.ui_manager restait a None, donc le bouton
# n'etait jamais dessine ni cliquable : du code mort.
# Elle est maintenant reellement instanciee par ChessBoard, donc handle_click
# est appele a chaque clic. Mais son bouton est MASQUE par defaut (visible =
# False), parce que GameButtons affiche deja un bouton "ABANDONNER" en bas a
# gauche et que deux boutons d'abandon a l'ecran preteraient a confusion.
#
# Pour utiliser celui-ci a la place, mets dans config.json :
#     "bouton_abandon_haut_droite": true
# GameButtons masquera alors le sien automatiquement.
#
# AUCUNE FONCTION SUPPRIMEE : __init__(chessboard), draw(surface) et
# handle_click(pos) sont conservees.

import json
import os

import chess
import pygame

import ui


def _visible_par_defaut():
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
                    return False
                return bool(contenu.get("bouton_abandon_haut_droite", False))
            except (ValueError, OSError):
                return False
    return False


class UIManager:
    def __init__(self, chessboard, visible=None):
        self.chessboard = chessboard
        # V7.1 : le rectangle etait fixe en (680, 660) - hors de l'ecran sur une
        # fenetre de 640 de haut. Il suit maintenant la zone que la disposition
        # reserve aux boutons, comme l'autre bouton d'abandon.
        self.resign_rect = pygame.Rect(680, 560, 340, 48)
        self.text = "ABANDONNER LA PARTIE"
        self.font = ui.police(18, True)
        self.color = (150, 30, 30)
        self.hover_color = (225, 60, 55)
        self.visible = _visible_par_defaut() if visible is None else bool(visible)

    def _placer(self):
        dispo = getattr(self.chessboard, "disposition", None)
        zone = getattr(dispo, "boutons", None) if dispo is not None else None
        if zone:
            self.resign_rect = pygame.Rect(*zone)
        return self.resign_rect

    def draw(self, surface):
        if not self.visible or self.chessboard.game_over:
            return
        self._placer()
        souris = pygame.mouse.get_pos()
        couleur = self.hover_color if self.resign_rect.collidepoint(souris) else self.color
        ui.cadre(surface, self.resign_rect, couleur, (250, 250, 250), 2, 8)
        ui.texte_centre_dans(surface, self.text, self.resign_rect,
                             max(12, min(19, int(self.resign_rect.height * 0.42))),
                             (255, 255, 255), gras=True, marge=10)

    def handle_click(self, pos):
        """Renvoie True si le clic a ete consomme par l'interface."""
        if not self.visible or self.chessboard.game_over:
            return False
        self._placer()
        if not self.resign_rect.collidepoint(pos):
            return False
        self.abandonner()
        return True

    def abandonner(self):
        plateau = self.chessboard
        # Celui qui abandonne est le joueur humain : on determine sa couleur.
        couleur = getattr(plateau, "couleur_joueur", None)
        if couleur is None:
            if getattr(plateau, "ia_joue_blancs", False):
                couleur = chess.BLACK
            elif getattr(plateau, "hotseat_mode", False):
                couleur = plateau.board.turn
            else:
                couleur = chess.WHITE
        resultat = "0-1" if couleur == chess.WHITE else "1-0"
        plateau.terminer_partie("Abandon", resultat)
        print("[UI MANAGER] Partie abandonnee par le joueur humain")
