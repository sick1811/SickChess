# game_manager.py - SickChess : le chef d'orchestre.
#
# Version allegee de celui de V8_TURBO_3000 (877 lignes). Il ne garde que le
# noyau : menu -> reglages -> partie (contre Stockfish ou a deux sur ce PC) ->
# fin de partie -> menu. Les autres ecrans (problemes, historique, revue,
# en ligne...) seront rebranches ici un par un, chacun dans sa propre methode.

import json
import os
import sys

import pygame

import apparence
import ui
from board import ChessBoard
from ecran_fin import EcranFin
from layout import Disposition
from menu_principal import MainMenu
from mode_hotseat import ModeHotseat
from mode_stockfish import ModeStockfish
from raccourcis import AideRaccourcis
from settings_screen import SettingsScreen

LARGEUR, HAUTEUR = ui.TAILLE_PAR_DEFAUT
TAILLE_MINI = ui.TAILLE_MINI


class GameManager:
    def __init__(self, version=""):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.version = version

        self.plein_ecran = False
        ui.memoriser_taille(LARGEUR, HAUTEUR, False)
        self.screen = pygame.display.set_mode((LARGEUR, HAUTEUR), pygame.RESIZABLE)
        pygame.display.set_caption("SickChess")

        self.clock = pygame.time.Clock()
        self.disposition = Disposition(LARGEUR, HAUTEUR)
        self.aide = AideRaccourcis(self.screen)
        self.menu = MainMenu(self.screen, version)

        self.config = self._charger_config()
        self.stockfish_path = self.config.get("stockfish_path",
                                              os.path.join("moteur", "stockfish.exe"))
        self.game_mode = None
        self.current_mode = None
        self.board = None
        self.engine = None
        self.reglages = {}

    # ------------------------------------------------------------------ config

    def _charger_config(self):
        chemin = os.path.join(os.getcwd(), "config.json")
        if os.path.exists(chemin):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    contenu = json.load(f)
                if isinstance(contenu, dict):
                    return contenu
                print("[CONFIG] config.json n'est pas un dictionnaire")
            except (ValueError, OSError) as e:
                print("[CONFIG] config.json illisible : %s" % e)
        return {}

    # ------------------------------------------------------------------ fenetre

    def _appliquer_taille(self, largeur, hauteur):
        largeur = max(TAILLE_MINI[0], largeur)
        hauteur = max(TAILLE_MINI[1], hauteur)
        if not self.plein_ecran:
            ui.memoriser_taille(largeur, hauteur)
        self.disposition.recalculer(largeur, hauteur)
        self.menu.screen = self.screen
        self.menu.redimensionner(largeur, hauteur)
        self.aide.screen = self.screen
        if self.board is not None:
            self.board.screen = self.screen
            self.board.appliquer_disposition(self.disposition)

    def evenement_fenetre(self, event):
        """Redimensionnement, plein ecran (F11) et aide (F1). True si consomme."""
        nouvelle = ui.evenement_fenetre(event)
        if nouvelle is not None:
            self.screen = nouvelle
            self.plein_ecran = ui.est_plein_ecran()
            self._appliquer_taille(*self.screen.get_size())
            return True
        return bool(self.aide.handle_event(event))

    # ------------------------------------------------------------------ menu

    def show_menu(self):
        """Boucle du menu. Renvoie 'stockfish' ou 'hotseat'."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quitter()
                if self.evenement_fenetre(event):
                    continue
                choix = self.menu.handle_event(event)
                if choix == "quitter":
                    self.quitter()
                if choix in ("stockfish", "hotseat"):
                    self.game_mode = choix
                    return choix
            self.menu.draw()
            self.aide.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)

    # ------------------------------------------------------------------ partie

    def _appliquer_preferences(self, board):
        board.changer_apparence(self.config.get("theme_plateau"),
                                self.config.get("jeu_pieces"))
        board.renderer.afficher_coordonnees = bool(
            self.config.get("afficher_coordonnees", True))
        vitesse = float(self.config.get("vitesse_animation", 0.18))
        board.animation.duree = max(0.01, vitesse)
        board.animation.active = vitesse > 0
        board.sounds.set_volume(float(self.config.get("volume_sons", 0.6)))
        board.sounds.actif = bool(self.config.get("sons_actifs", True))
        board.premouvement_actif = bool(self.config.get("premouvement", True))

    def demander_reglages(self):
        """Ecran de reglages avant partie. False = retour au menu."""
        reglages = SettingsScreen(self.screen, self.game_mode).run(self.clock)
        if reglages == "quitter":
            self.quitter()
        if not reglages:
            return False
        self.reglages = dict(reglages)
        for cle in ("theme_plateau", "jeu_pieces", "premouvement"):
            if cle in self.config:
                self.reglages.setdefault(cle, self.config[cle])
        return True

    def preparer_partie(self):
        """Cree le plateau et le mode avec self.reglages. False = echec."""
        self.board = ChessBoard(self.screen, self.reglages, self.disposition)
        self._appliquer_preferences(self.board)
        self.board.competitive = False
        self.board.end_screen = EcranFin(self.board, self.game_mode)

        if self.game_mode == "stockfish":
            self.engine = self.demarrer_moteur()
            if self.engine is None:
                return False
            self.current_mode = ModeStockfish(self.board, self.engine, self.reglages)
        else:
            self.current_mode = ModeHotseat(self.board,
                                            self.reglages.get("retourner_plateau"))
        return True

    def demarrer_moteur(self):
        try:
            import moteurs
            moteur = moteurs.moteur_de_jeu(self.stockfish_path)
            if moteur is not None:
                return moteur
            raise RuntimeError("le processus ne repond pas")
        except Exception as e:
            print("[ERREUR] Stockfish n'a pas pu demarrer : %s" % e)
            self.afficher_erreur("Stockfish n'a pas pu demarrer.",
                                 "Le moteur doit etre dans le dossier moteur/",
                                 "(voir moteur/LISEZ-MOI.txt).")
            return None

    def afficher_erreur(self, *lignes):
        t = apparence.theme(self.config.get("theme_plateau"))
        fin = pygame.time.get_ticks() + 8000
        while pygame.time.get_ticks() < fin:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quitter()
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    return
            largeur, hauteur = self.screen.get_size()
            self.screen.fill(t["fond"])
            for i, ligne in enumerate(lignes):
                ui.texte(self.screen, ligne, largeur // 2, hauteur // 2 - 60 + i * 40,
                         26 if i == 0 else 19,
                         (240, 120, 110) if i == 0 else t["texte_discret"],
                         gras=(i == 0), ancre="centre")
            ui.texte(self.screen, "Clique pour revenir au menu", largeur // 2,
                     hauteur // 2 + 90, 17, t["texte_discret"], ancre="centre")
            pygame.display.flip()
            self.clock.tick(60)

    # ------------------------------------------------------------------ boucles

    def run(self):
        while True:
            self.show_menu()
            if not self.demander_reglages():
                continue
            rejouer = True
            while rejouer:
                rejouer = False
                if self.preparer_partie():
                    rejouer = self.boucle_de_partie() == "rejouer"
                self.cleanup_game()

    def boucle_de_partie(self):
        """Joue la partie. Renvoie 'menu' ou 'rejouer'."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quitter()
                if self.evenement_fenetre(event):
                    continue
                if self.board.game_over:
                    action = self.board.end_screen.handle_event(event)
                    if action in ("menu", "rejouer"):
                        return action
                action = self.board.game_buttons.handle_event(event)
                if action == "return_to_menu":
                    return "menu"
                self.board.handle_event(event, self.engine)

            if self.current_mode is not None:
                self.current_mode.update()
            self.board.update()

            self.board.draw()
            self.aide.draw(self.screen, self.board.theme_plateau)
            pygame.display.flip()
            self.clock.tick(60)

    # ------------------------------------------------------------------ arret

    def cleanup_game(self):
        if self.current_mode is not None and hasattr(self.current_mode, "arreter"):
            try:
                self.current_mode.arreter()
            except Exception:
                pass
        try:
            import moteurs
            moteurs.liberer("jeu")
        except Exception:
            if self.engine:
                self.engine.quit()
        self.engine = None
        self.board = None
        self.current_mode = None

    def quitter(self):
        self.cleanup_game()
        self.cleanup()
        sys.exit()

    def cleanup(self):
        try:
            import moteurs
            moteurs.tout_fermer()
        except Exception:
            pass
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        pygame.quit()
