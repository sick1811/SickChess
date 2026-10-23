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
        # Revue de partie : l'analyse demarre des la fin (game_manager).
        self.bouton_revue = ui.Bouton((0, 0, 10, 10), "Revue de la partie", "revue")
        self.boutons = [self.bouton_revue, self.bouton_rejouer, self.bouton_menu]
        self.analyseur = None          # AnalyseurPartie, voir lancer_analyse()
        self.rect = pygame.Rect(0, 0, 10, 10)
        self.ligne_classement = ""    # "Classement : 1200 -> 1214 (+14)"

    # ------------------------------------------------------------------ texte

    def titre(self):
        resultat = getattr(self.plateau, "result", None)
        if resultat not in ("1-0", "0-1"):
            return "Partie nulle"
        gagnant = chess.WHITE if resultat == "1-0" else chess.BLACK
        if self.mode == "stockfish":
            couleur_ia = chess.WHITE if getattr(self.plateau, "ia_joue_blancs",
                                                False) else chess.BLACK
            return "Défaite" if gagnant == couleur_ia else "Victoire !"
        return "Les Blancs gagnent" if gagnant == chess.WHITE \
            else "Les Noirs gagnent"

    # ------------------------------------------------------------------ analyse

    def lancer_analyse(self, chemin_stockfish=None, puissance=None):
        """Demarre l'analyse de la partie en tache de fond (une seule fois)."""
        if self.analyseur is not None:
            return self.analyseur
        historique = getattr(self.plateau, "move_history", None)
        if historique is None or not historique.moves:
            return None
        from analyse_partie import AnalyseurPartie
        self.analyseur = AnalyseurPartie(historique.fen_initiale,
                                         list(historique.moves),
                                         chemin_stockfish, puissance)
        self.analyseur.demarrer()
        return self.analyseur

    def ligne_analyse(self):
        """'Precision : Toi 84.2 %  -  Ordinateur 91.0 %', ou l'avancement."""
        a = self.analyseur
        if a is None:
            return ""
        if a.erreur or not a.terminee():
            return a.texte_avancement()
        rapport = a.rapport()
        blancs, noirs = rapport["blancs"]["precision"], rapport["noirs"]["precision"]
        if blancs is None or noirs is None:
            return ""
        if self.mode == "stockfish":
            ia_blancs = getattr(self.plateau, "ia_joue_blancs", False)
            moi = noirs if ia_blancs else blancs
            ia = blancs if ia_blancs else noirs
            self._succes_precision_90(moi)
            return "Précision : toi %.1f %%   -   ordinateur %.1f %%" % (moi, ia)
        return "Précision : Blancs %.1f %%   -   Noirs %.1f %%" % (blancs, noirs)

    def _succes_precision_90(self, precision):
        if precision >= 90 and not getattr(self, "_succes_precision", False):
            self._succes_precision = True
            try:
                import succes
                succes.debloquer("precision_90")
            except Exception as e:
                print("[SUCCES] %s" % e)

    # ------------------------------------------------------------------ dessin

    def _placer(self, screen):
        largeur, hauteur = screen.get_size()
        carte_l, carte_h = min(420, largeur - 40), 300
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
        self.bouton_revue.placer((self.rect.x + 20, y - 58, carte_l - 40, 48))

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
        if self.ligne_classement:
            ui.texte(screen, self.ligne_classement, self.rect.centerx,
                     self.rect.y + 104, 16, t["accent"], gras=True, ancre="centre",
                     largeur_max=self.rect.width - 30, ajuster=True)
        ligne = self.ligne_analyse()
        if ligne:
            ui.texte(screen, ligne, self.rect.centerx, self.rect.y + 132, 15,
                     t["texte"], ancre="centre",
                     largeur_max=self.rect.width - 30, ajuster=True)
        for bouton in self.boutons:
            bouton.dessiner(screen, t, rayon=10)

    def handle_event(self, event):
        """Renvoie 'revue', 'rejouer', 'menu' ou None."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "menu"
        return ui.gerer_boutons(self.boutons, event)
