# ecran_fin.py - SickChess : la carte de fin de partie.
#
# Version simple (V8_TURBO_3000 avait un ecran de fin avec analyse, profil,
# historique et revanche en ligne : ces morceaux reviendront avec la revue de
# partie). Ici : le resultat, la raison, et deux boutons REJOUER / MENU.
# board_render.py appelle draw() tout seul quand la partie est finie.

import chess
import pygame

import apparence
import ui


class EcranFin:
    def __init__(self, plateau, mode):
        self.plateau = plateau
        self.mode = mode                          # "stockfish" ou "hotseat"
        self.bouton_rejouer = ui.Bouton((0, 0, 10, 10), "Rejouer", "rejouer")
        self.bouton_menu = ui.Bouton((0, 0, 10, 10), "Menu", "menu")
        self.boutons = [self.bouton_rejouer, self.bouton_menu]
        self.rect = pygame.Rect(0, 0, 10, 10)

    # ------------------------------------------------------------------ texte

    def titre(self):
        resultat = getattr(self.plateau, "result", None)
        if resultat not in ("1-0", "0-1"):
            return "Partie nulle"
        gagnant = chess.WHITE if resultat == "1-0" else chess.BLACK
        if self.mode == "stockfish":
            couleur_ia = chess.WHITE if getattr(self.plateau, "ia_joue_blancs",
                                                False) else chess.BLACK
            return "Defaite" if gagnant == couleur_ia else "Victoire !"
        return "Les Blancs gagnent" if gagnant == chess.WHITE \
            else "Les Noirs gagnent"

    # ------------------------------------------------------------------ dessin

    def _placer(self, screen):
        largeur, hauteur = screen.get_size()
        carte_l, carte_h = min(420, largeur - 40), 210
        dispo = getattr(self.plateau, "disposition", None)
        if dispo is not None and hasattr(dispo, "rect_plateau"):
            zone = pygame.Rect(*dispo.rect_plateau())
        else:
            zone = screen.get_rect()
        self.rect = pygame.Rect(0, 0, carte_l, carte_h)
        self.rect.center = zone.center
        bl = (carte_l - 60) // 2
        y = self.rect.bottom - 70
        self.bouton_rejouer.placer((self.rect.x + 20, y, bl, 48))
        self.bouton_menu.placer((self.rect.x + 40 + bl, y, bl, 48))

    def draw(self, screen):
        if not self.plateau.game_over:
            return
        self._placer(screen)
        t = apparence.theme(getattr(self.plateau, "theme_plateau", None))
        ui.cadre(screen, self.rect, t["panneau"], t.get("accent"), 2, 16,
                 ombre=True)
        ui.texte(screen, self.titre(), self.rect.centerx, self.rect.y + 22, 34,
                 t["texte"], gras=True, ancre="centre",
                 largeur_max=self.rect.width - 30, ajuster=True)
        raison = getattr(self.plateau, "game_over_reason", "") or ""
        ui.texte(screen, raison, self.rect.centerx, self.rect.y + 76, 16,
                 t["texte_discret"], ancre="centre",
                 largeur_max=self.rect.width - 30, ajuster=True)
        for bouton in self.boutons:
            bouton.dessiner(screen, t, rayon=10)

    def handle_event(self, event):
        """Renvoie 'rejouer', 'menu' ou None."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "menu"
        return ui.gerer_boutons(self.boutons, event)
