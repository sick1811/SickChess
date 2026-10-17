# game_manager.py - SickChess : le chef d'orchestre.
#
# Version allegee de celui de V8_TURBO_3000 (877 lignes). Il ne garde que le
# noyau : menu -> reglages -> partie (contre Stockfish ou a deux sur ce PC) ->
# fin de partie -> menu. Les autres ecrans (problemes, historique, revue,
# en ligne...) seront rebranches ici un par un, chacun dans sa propre methode.
# Deja rebranches : Options, Mes parties et profil, reprise de partie,
# revue de partie, problemes.

import json
import os
import sys

import pygame

import apparence
import sauvegarde
import partie_en_ligne
import ui
from board import ChessBoard
from ecran_options import EcranOptions
from ecran_fin import EcranFin
from enregistrement import enregistrer_la_partie, texte_classement
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
        # Tampon de 1024 (et non 512) : sur certaines cartes son Windows, un
        # tampon trop petit donne un jeu muet sans aucune erreur.
        pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.init()
        self._verifier_le_son()
        self.version = version

        self.plein_ecran = False
        ui.memoriser_taille(LARGEUR, HAUTEUR, False)
        self.screen = pygame.display.set_mode((LARGEUR, HAUTEUR), pygame.RESIZABLE)
        pygame.display.set_caption("SickChess")
        self._poser_icone()

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
        self.reprise = None                   # partie sauvegardee a reprendre
        self.sauvegardeur = sauvegarde.Sauvegardeur()
        self.menu.annoncer_reprise(sauvegarde.lire() is not None,
                                   sauvegarde.resume(sauvegarde.lire()))

        if self.config.get("plein_ecran"):       # reglage de l'ecran Options
            self.screen = ui.basculer_plein_ecran()
            self.plein_ecran = True
            self._appliquer_taille(*self.screen.get_size())

    def _verifier_le_son(self):
        """Si le lecteur audio n'a pas demarre avec pygame.init(), on reessaie
        avec les reglages par defaut de la carte son, et on l'ecrit au journal."""
        if not pygame.mixer.get_init():
            for essai in ({"frequency": 48000, "size": -16, "channels": 2, "buffer": 2048}, {}):
                try:
                    pygame.mixer.init(**essai)
                    break
                except pygame.error as e:
                    print("[SONS] demarrage audio rate (%s) : %s" % (essai or "defaut", e))
        print("[SONS] lecteur audio : %s" % (pygame.mixer.get_init(),))
        try:
            from pygame._sdl2 import audio as sdl_audio
            print("[SONS] sorties audio : %s" % sdl_audio.get_audio_device_names(False))
        except Exception:
            pass

    def _poser_icone(self):
        """L'icone Onyx & Or (assets/icone.png, fabriquee par outils/generer_logo.py)."""
        try:
            from asset_manager import chemin_ressource
            chemin = chemin_ressource("assets", "icone.png")
            if os.path.exists(chemin):
                pygame.display.set_icon(pygame.image.load(chemin))
        except Exception as e:
            print("[ICONE] %s" % e)

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
            # Invitation Steam acceptee (ou jeu lance par une invitation) :
            # on file directement au salon de l'ami.
            if partie_en_ligne.invitation_en_attente():
                self.ouvrir_en_ligne()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quitter()
                if self.evenement_fenetre(event):
                    continue
                choix = self.menu.handle_event(event)
                if choix == "quitter":
                    self.quitter()
                if choix == "en_ligne":
                    self.ouvrir_en_ligne()
                    continue
                if choix == "options":
                    self.ouvrir_options()
                    continue
                if choix == "historique":
                    self.ouvrir_mes_parties()
                    continue
                if choix == "puzzles":
                    self.ouvrir_problemes()
                    continue
                if choix == "reprendre":
                    donnees = sauvegarde.lire()
                    if donnees is None:
                        self.menu.annoncer_reprise(False)
                        continue
                    self.reprise = donnees
                    self.game_mode = donnees["mode"]
                    return choix
                if choix in ("stockfish", "hotseat"):
                    self.game_mode = choix
                    return choix
            self.menu.draw()
            self.aide.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)

    def ouvrir_options(self):
        """Ecran Options. Au retour : config relue, fenetre remise a jour."""
        if EcranOptions(self.screen).run(self.clock) == "quitter":
            self.quitter()
        self.config = self._charger_config()
        self.screen = pygame.display.get_surface()
        self.plein_ecran = ui.est_plein_ecran()
        self._appliquer_taille(*self.screen.get_size())
        self.menu.redimensionner(*self.screen.get_size())

    # ------------------------------------------------------------------ problemes

    def ouvrir_problemes(self):
        """Ecran des problemes (ecran_problemes.py)."""
        from ecran_problemes import EcranProblemes
        try:
            ecran = EcranProblemes(self.screen, self.config)
        except Exception as e:
            print("[PROBLEMES] ouverture impossible : %s" % e)
            self.afficher_erreur("Les problèmes n'ont pas pu s'ouvrir.", str(e)[:80])
            return
        if ecran.run(self.clock, self.evenement_fenetre, self._dessiner_aide) == "quitter":
            self.quitter()
        self.screen = pygame.display.get_surface()
        self._appliquer_taille(*self.screen.get_size())

    # ------------------------------------------------------------------ mes parties

    def ouvrir_mes_parties(self):
        """Ecran "Mes parties et profil", et la relecture d'une partie."""
        from ecran_mes_parties import EcranMesParties
        from ecran_revoir import EcranRevoir
        theme = self.config.get("theme_plateau")
        while True:
            ecran = EcranMesParties(self.screen, theme)
            reponse = ecran.run(self.clock, self.evenement_fenetre, self._dessiner_aide)
            if reponse == "quitter":
                self.quitter()
            if not isinstance(reponse, dict):
                break
            relecture = self._revue_d_une_partie_enregistree(reponse["partie"]) \
                or EcranRevoir(self.screen, reponse["partie"],
                               self.disposition, self.config)
            reponse = relecture.run(self.clock, self.evenement_fenetre,
                                    self._dessiner_aide)
            if getattr(relecture, "analyseur", None) is not None:
                relecture.analyseur.arreter()      # inutile de continuer
            if reponse == "quitter":
                self.quitter()
        self.menu.redimensionner(*self.screen.get_size())

    def _revue_d_une_partie_enregistree(self, partie):
        """La revue (avec analyse) d'une partie de "Mes parties".

        None si le fichier ne se relit pas : la relecture simple (ecran_revoir)
        prend alors le relais et affiche l'erreur.
        """
        import historique_parties
        from analyse_partie import AnalyseurPartie
        from ecran_revue import EcranRevue
        donnees, erreur = historique_parties.lire_partie(partie.get("chemin", ""))
        if erreur or not donnees:
            return None
        analyseur = AnalyseurPartie(donnees["fen"], donnees["coups"],
                                    self.stockfish_path,
                                    self.config.get("analyse_puissance"))
        resultat = " ".join(m for m in (partie.get("resultat", ""),
                                        partie.get("date", "")) if m)
        return EcranRevue(self.screen, analyseur, self.config,
                          (partie.get("blancs", "Blancs"), partie.get("noirs", "Noirs")),
                          resultat, partie.get("raison", ""),
                          partie.get("camp") == "noir")

    def _dessiner_aide(self, ecran):
        self.aide.draw(ecran)

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
        self.partie_enregistree = False

        reprise, self.reprise = self.reprise, None
        if reprise is not None:
            sauvegarde.appliquer(self.board, reprise)

        if self.game_mode == "stockfish":
            self.engine = self.demarrer_moteur()
            if self.engine is None:
                return False
            reglages = dict(self.reglages)
            if reprise is not None:
                reglages["ia_joue_blancs"] = bool(reprise.get("ia_joue_blancs"))
            self.current_mode = ModeStockfish(self.board, self.engine, reglages)
        else:
            self.current_mode = ModeHotseat(self.board,
                                            self.reglages.get("retourner_plateau"))
        if reprise is not None:
            self.board.flipped = bool(reprise.get("flipped"))
        return True

    def demarrer_moteur(self):
        try:
            import moteurs
            moteur = moteurs.moteur_de_jeu(self.stockfish_path)
            if moteur is not None:
                return moteur
            raise RuntimeError("le processus ne répond pas")
        except Exception as e:
            print("[ERREUR] Stockfish n'a pas pu demarrer : %s" % e)
            self.afficher_erreur("Stockfish n'a pas pu demarrer.",
                                 "Le moteur doit être dans le dossier moteur/",
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

    def ouvrir_en_ligne(self):
        """Jouer en ligne par Steam : salon, partie, revanche.
        Tout le parcours vit dans partie_en_ligne.py."""
        partie_en_ligne.lancer(self)
        self.board = None
        self._appliquer_taille(*self.screen.get_size())

    def run(self):
        while True:
            if self.show_menu() == "reprendre":
                self.reglages = dict(self.reprise.get("reglages") or {})
            elif not self.demander_reglages():
                continue
            rejouer = True
            while rejouer:
                rejouer = False
                if self.preparer_partie():
                    rejouer = self.boucle_de_partie() == "rejouer"
                self.cleanup_game()
            self.menu.annoncer_reprise(sauvegarde.lire() is not None,
                                       sauvegarde.resume(sauvegarde.lire()))

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
                    if action == "revue":
                        self.ouvrir_revue()
                        continue
                action = self.board.game_buttons.handle_event(event)
                if action == "return_to_menu":
                    # Partie pas finie : on la garde, le menu proposera de la
                    # reprendre.
                    sauvegarde.enregistrer(self.board, self.game_mode, self.reglages)
                    return "menu"
                self.board.handle_event(event, self.engine)

            if self.current_mode is not None:
                self.current_mode.update()
            self.board.update()

            if self.board.game_over:
                self._partie_terminee()
            else:
                self.sauvegardeur.peut_etre(self.board, self.game_mode, self.reglages)
                self._suivre_analyse()

            self.board.draw()
            self.aide.draw(self.screen, self.board.theme_plateau)
            pygame.display.flip()
            self.clock.tick(60)

    def _partie_terminee(self):
        """Une seule fois par partie : profil, PGN, et plus rien a reprendre."""
        if self.partie_enregistree:
            return
        self.partie_enregistree = True
        sauvegarde.effacer()
        try:
            infos = enregistrer_la_partie(self.board, self.game_mode)
        except Exception as e:
            print("[PROFIL] partie non enregistree : %s" % e)
            infos = None
        self.board.end_screen.ligne_classement = texte_classement(infos)
        # La revue de partie : l'analyse faite PENDANT la partie est reprise
        # telle quelle (rien a recalculer) ; sinon elle demarre maintenant.
        direct = getattr(self, "analyse_en_direct", None)
        if direct is not None and getattr(direct, "plateau_id", None) == id(self.board):
            self._suivre_analyse(force=True)
            direct.finir_le_suivi()
            self.board.end_screen.analyseur = direct
            self.analyse_en_direct = None
        try:
            self.board.end_screen.lancer_analyse(
                self.stockfish_path, self.config.get("analyse_puissance"))
        except Exception as e:
            print("[ANALYSE] non lancee : %s" % e)

    # ---------------------------------------------------- analyse en direct

    def _suivre_analyse(self, force=False):
        """SickChess 17/10 (demande de Julien) : Stockfish analyse la partie
        PENDANT qu'on joue, sans rien afficher. A la fin, la precision et la
        revue sont pretes tout de suite. Moitie des coeurs seulement, pour ne
        pas ralentir l'adversaire. "analyse_pendant_partie": false la coupe."""
        if self.game_mode not in ("stockfish", "hotseat"):
            return
        if not self.config.get("analyse_pendant_partie", True):
            return
        historique = getattr(self.board, "move_history", None)
        if historique is None:
            return
        maintenant = pygame.time.get_ticks()
        if not force and maintenant < getattr(self, "_prochain_suivi", 0):
            return
        self._prochain_suivi = maintenant + 250
        coups = list(historique.moves)
        a = getattr(self, "analyse_en_direct", None)
        if a is not None and (getattr(a, "plateau_id", None) != id(self.board)
                              or a.nombre_de_coups() > len(coups)):
            a.arreter()
            a = None
        if a is None:
            if not coups:
                return
            from analyse_partie import AnalyseurPartie
            try:
                coeurs = os.cpu_count() or 2
            except Exception:
                coeurs = 2
            a = AnalyseurPartie(historique.fen_initiale, coups, self.stockfish_path,
                                self.config.get("analyse_puissance"), suivi=True,
                                threads=max(1, coeurs // 2))
            a.plateau_id = id(self.board)
            a.demarrer()
            self.analyse_en_direct = a
        elif len(coups) > a.nombre_de_coups():
            a.ajouter_coups(coups[a.nombre_de_coups():])

    # ------------------------------------------------------------------ revue

    def ouvrir_revue(self):
        """Revue de la partie qui vient de finir (ecran_revue.py)."""
        from ecran_revue import EcranRevue
        fin = self.board.end_screen
        analyseur = fin.lancer_analyse(self.stockfish_path,
                                       self.config.get("analyse_puissance"))
        if analyseur is None:
            return
        cote_noir = False
        noms = ("Blancs", "Noirs")
        if self.game_mode == "stockfish":
            cote_noir = bool(getattr(self.board, "ia_joue_blancs", False))
            ia = "Ordinateur (%s)" % self.reglages.get("elo", "?")
            noms = (ia, "Toi") if cote_noir else ("Toi", ia)
        revue = EcranRevue(self.screen, analyseur, self.config, noms,
                           getattr(self.board, "result", "") or "",
                           getattr(self.board, "game_over_reason", "") or "",
                           cote_noir)
        if revue.run(self.clock, self.evenement_fenetre,
                     self._dessiner_aide) == "quitter":
            self.quitter()
        # On rend a la partie sa geometrie (la revue a la sienne).
        self.screen = pygame.display.get_surface()
        self._appliquer_taille(*self.screen.get_size())

    # ------------------------------------------------------------------ arret

    def cleanup_game(self):
        direct = getattr(self, "analyse_en_direct", None)
        if direct is not None:
            direct.arreter()
            self.analyse_en_direct = None
        fin = getattr(self.board, "end_screen", None) if self.board else None
        if fin is not None and getattr(fin, "analyseur", None) is not None:
            fin.analyseur.arreter()
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
        if self.board is not None and not self.board.game_over:
            sauvegarde.enregistrer(self.board, self.game_mode, self.reglages)
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
            partie_en_ligne.arreter()
        except Exception:
            pass
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        pygame.quit()
