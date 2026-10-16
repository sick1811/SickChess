# game_buttons.py - V6 : boutons pendant la partie
#
# CE QUI CHANGE PAR RAPPORT A V5 :
#   1. L'ABANDON DONNAIT TOUJOURS "0-1". V5 ecrivait result = "0-1" en dur :
#      si tu abandonnais en jouant les Noirs, le jeu annoncait quand meme que
#      les Noirs avaient gagne. La couleur de celui qui abandonne est
#      maintenant determinee correctement.
#   2. L'abandon passe par board.terminer_partie(), donc l'ecran de fin,
#      l'arret de l'IA et le son se declenchent comme pour un mat.
#   3. Le survol fonctionne aussi quand la souris bouge, pas seulement au clic.
#   4. Le bouton se masque tout seul si tu as choisi celui d'ui_manager
#      (config.json : "bouton_abandon_haut_droite": true) : jamais deux boutons
#      d'abandon a l'ecran.
#   5. Une confirmation en deux temps evite l'abandon par megarde.
#
# AUCUNE FONCTION SUPPRIMEE : __init__(chessboard), draw(screen) et
# handle_event(event) sont conservees.

import chess
import pygame

import ui

from wood_button import WoodButton

DELAI_CONFIRMATION = 3000   # millisecondes


class GameButtons:
    def __init__(self, chessboard):
        self.chessboard = chessboard
        self.font = ui.police(18, True)

        # Bouton Abandon pendant la partie (sous l'echiquier, a gauche).
        self.abandon_button = WoodButton(20, 656, 280, 50, "ABANDONNER")
        # Bouton Retour au menu, visible seulement a la fin.
        self.retour_button = WoodButton(980, 656, 280, 50, "RETOUR AU MENU")

        self.confirmation = False
        self.confirmation_jusqu_a = 0
        # Zone fixee par la disposition (layout.py) : les boutons suivent la
        # taille de la fenetre au lieu d'etre a des coordonnees fixes.
        self.zone = None

    def _placer(self):
        if not self.zone:
            return
        x, y, largeur, hauteur = self.zone
        for bouton in (self.abandon_button, self.retour_button):
            bouton.rect = pygame.Rect(x, y, largeur, hauteur)

    # ------------------------------------------------------------------ etat

    def _abandon_visible(self):
        gestionnaire = getattr(self.chessboard, "ui_manager", None)
        if gestionnaire is not None and getattr(gestionnaire, "visible", False):
            return False       # c'est l'autre bouton qui s'en charge
        return True

    def _expirer_confirmation(self):
        if self.confirmation and pygame.time.get_ticks() > self.confirmation_jusqu_a:
            self.confirmation = False
            self.abandon_button.text = "ABANDONNER"

    # ------------------------------------------------------------------ dessin

    def draw(self, screen):
        self._expirer_confirmation()
        self._placer()
        if self.chessboard.game_over:
            self.retour_button.draw(screen)
        elif self._abandon_visible():
            self.abandon_button.draw(screen)

    # ------------------------------------------------------------------ souris

    def handle_event(self, event):
        self._expirer_confirmation()
        self._placer()
        souris = pygame.mouse.get_pos()

        if self.chessboard.game_over:
            self.retour_button.update(souris)
            if self.retour_button.handle_event(event):
                return "return_to_menu"
            return None

        if not self._abandon_visible():
            return None

        self.abandon_button.update(souris)
        if self.abandon_button.handle_event(event):
            if not self.confirmation:
                # Premier clic : on demande confirmation.
                self.confirmation = True
                self.confirmation_jusqu_a = pygame.time.get_ticks() + DELAI_CONFIRMATION
                self.abandon_button.text = "SUR ? RECLIQUE"
                return None
            self.confirmation = False
            self.abandon_button.text = "ABANDONNER"
            self._abandonner()
            return "abandon"
        return None

    def _abandonner(self):
        plateau = self.chessboard
        couleur = getattr(plateau, "couleur_joueur", None)
        if couleur is None:
            if getattr(plateau, "ia_joue_blancs", False):
                couleur = chess.BLACK          # l'humain joue les Noirs
            elif getattr(plateau, "hotseat_mode", False):
                couleur = plateau.board.turn   # celui qui a le trait abandonne
            else:
                couleur = chess.WHITE
        resultat = "0-1" if couleur == chess.WHITE else "1-0"
        plateau.terminer_partie("Abandon", resultat)
        print("[GAME BUTTONS] Partie abandonnee (%s)" % resultat)
