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

import chess

import pygame

import analyse_partie
import apparence
import invitations
import sauvegarde
import mise_a_jour
import partie_en_ligne
import ui
from board import ChessBoard
from ecran_options import EcranOptions
import menu_pause
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
        # Version amis : "0.2.0 (n°7)", lue dans paquets_installes.json.
        version = mise_a_jour.version_affichee(version)
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
        self.maj = None
        self._ajouter_bouton_maj()

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
        # 24/10 (p36) : le bandeau « X t'invite » sur tous les ecrans.
        self.au_menu = False          # le menu lui-meme est a l'ecran
        self.en_partie = False        # une partie contre l'ordinateur / a deux
        self.en_ligne = False         # le parcours en ligne (salon, partie)
        self.bandeau = invitations.BandeauInvitation(self)
        ui.installer_crochet(self.bandeau)

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

    # ------------------------------------------------------------------ mises a jour

    def _ajouter_bouton_maj(self):
        """Version amis seulement : entree "Mise a jour" juste avant Quitter, et
        verification discrete en tache de fond. Voir mise_a_jour.py."""
        mise_a_jour.nettoyer_restes()
        self.maj = mise_a_jour.verifier_en_arriere_plan()
        if self.maj is None:
            return
        bouton = ui.Bouton((0, 0, 10, 10), "Mise à jour", "mise_a_jour", taille=19)
        place = next((i for i, b in enumerate(self.menu.boutons) if b.cle == "quitter"),
                     len(self.menu.boutons))
        self.menu.boutons.insert(place, bouton)
        self.menu.redimensionner(*self.screen.get_size())

    def _badge_maj(self):
        """Le bouton s'allume quand une nouvelle version est en ligne. En mise a
        jour automatique (par defaut), le menu telecharge et installe tout seul."""
        if self.maj is None:
            return
        import time as _time
        if not hasattr(self, "_maj_auto"):
            self._maj_auto = {}
        action, libelle_auto = mise_a_jour.pas_automatique(
            self.maj, self.config, _time.time(), self._maj_auto)
        if action == "telecharger":
            self.maj.telecharger()
        elif action == "verifier":
            self.maj.verifier()
        elif action == "installer":
            if self.maj.lancer_installation():
                self.quitter()          # _maj.bat installe puis relance le jeu
        for bouton in self.menu.boutons:
            if bouton.cle == "mise_a_jour":
                dispo = self.maj.etat in ("disponible", "telechargement", "pret")
                if libelle_auto:
                    bouton.libelle = libelle_auto
                else:
                    bouton.libelle = "Mise à jour disponible !" if dispo else "Mise à jour"
                bouton.selectionne = dispo

    def ouvrir_mise_a_jour(self):
        from ecran_mise_a_jour import EcranMiseAJour
        resultat = EcranMiseAJour(self.screen, self.maj, self.config).run(
            self.clock, self.evenement_fenetre)
        if resultat in ("quitter", "redemarrer"):
            # "redemarrer" : _maj.bat attend que le jeu soit ferme pour
            # installer la nouvelle version, puis le relance.
            self.quitter()
        self._appliquer_taille(*self.screen.get_size())

    def show_menu(self):
        """Boucle du menu. Renvoie 'stockfish', 'hotseat' ou 'reprendre'."""
        import musique
        musique.jouer(self.config)          # 17/10, travail p14
        cadence = ui.Cadence()       # 23/10 : 30 images/s au repos
        while True:
            # Invitation Steam acceptee (ou jeu lance par une invitation) :
            # on file directement au salon de l'ami.
            if partie_en_ligne.invitation_en_attente():
                self.au_menu = False
                self.ouvrir_en_ligne()
            self._badge_maj()
            self.au_menu = True
            evenements = ui.evenements()
            try:
                self._evenements_du_menu(evenements)
            except invitations.RetourAuMenu:
                # « Rejoindre » d'une invitation dans un ecran ouvert depuis le
                # menu : l'ecran est ferme, on file au salon de l'ami.
                self._retour_force_au_menu()
                continue
            if self.game_mode_choisi is not None:
                return self.game_mode_choisi
            self.menu.draw()
            self.aide.draw(self.screen)
            ui.afficher()
            self.clock.tick(cadence.suivante(evenements))

    def _retour_force_au_menu(self):
        self.screen = pygame.display.get_surface()
        self._appliquer_taille(*self.screen.get_size())
        self.menu.annoncer_reprise(sauvegarde.lire() is not None,
                                   sauvegarde.resume(sauvegarde.lire()))

    def _evenements_du_menu(self, evenements):
        """Les evenements du menu. Range dans self.game_mode_choisi le choix
        qui lance une partie ('stockfish', 'hotseat' ou 'reprendre')."""
        import musique
        self.game_mode_choisi = None
        ecrans = {"en_ligne": self.ouvrir_en_ligne, "mise_a_jour": self.ouvrir_mise_a_jour,
                  "signaler": self.ouvrir_signaler, "historique": self.ouvrir_mes_parties,
                  "puzzles": self.ouvrir_problemes, "ouvertures": self.ouvrir_entrainement,
                  "analyse": self.ouvrir_analyse_libre}
        for event in evenements:
            if event.type == pygame.QUIT:
                self.quitter()
            if self.evenement_fenetre(event):
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                # M : couper / remettre la musique (aide F1)
                self.config["musique"] = not self.config.get("musique", True)
                try:
                    import ecran_options
                    ecran_options.enregistrer({"musique": self.config["musique"],
                                               "volume_sons": self.config.get("volume_sons", 0.6)})
                except Exception:
                    pass
                musique.jouer(self.config)
                continue
            choix = self.menu.handle_event(event)
            if choix == "quitter":
                self.quitter()
            if choix in ecrans or choix == "options":
                self.au_menu = False          # un autre ecran s'ouvre par-dessus
                if choix == "options":
                    self.ouvrir_options()
                    musique.jouer(self.config)
                else:
                    ecrans[choix]()
                self.au_menu = True
                continue
            if choix == "reprendre":
                donnees = sauvegarde.lire()
                if donnees is None:
                    self.menu.annoncer_reprise(False)
                    continue
                self.reprise = donnees
                self.game_mode = donnees["mode"]
                self.game_mode_choisi = choix
                return
            if choix in ("stockfish", "hotseat"):
                self.game_mode = choix
                self.game_mode_choisi = choix
                return

    def ouvrir_signaler(self):
        """« Signaler un problème / une idée » (17/10, travail p16)."""
        from ecran_signaler import EcranSignaler
        if EcranSignaler(self.screen, self.version).run(
                self.clock, self.evenement_fenetre) == "quitter":
            self.quitter()
        self.screen = pygame.display.get_surface()
        self._appliquer_taille(*self.screen.get_size())

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

    def ouvrir_entrainement(self):
        """Entraineur d'ouvertures (17/10, travail p06)."""
        from ecran_entrainement import EcranEntrainement
        if EcranEntrainement(self.screen, self.config).run(
                self.clock, self.evenement_fenetre) == "quitter":
            self.quitter()
        self.screen = pygame.display.get_surface()
        self._appliquer_taille(*self.screen.get_size())

    def ouvrir_analyse_libre(self):
        """Analyse libre : les deux camps, editeur, FEN / PGN (24/10, travail p35)."""
        from ecran_analyse_libre import EcranAnalyseLibre
        if EcranAnalyseLibre(self.screen, self.config,
                             stockfish_path=self.stockfish_path).run(
                self.clock, self.evenement_fenetre, self._dessiner_aide) == "quitter":
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
            if reponse.get("action") == "statistiques":
                from ecran_statistiques import EcranStatistiques
                if EcranStatistiques(self.screen, theme).run(
                        self.clock, self.evenement_fenetre) == "quitter":
                    self.quitter()
                continue
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
        chemin_pgn = partie.get("chemin", "")
        analyseur = AnalyseurPartie(donnees["fen"], donnees["coups"],
                                    self.stockfish_path,
                                    analyse_partie.puissance_de(self.config),
                                    fichier_cache=os.path.splitext(chemin_pgn)[0]
                                    + ".analyse.json" if chemin_pgn else None)
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
        board.sounds.changer_de_pack(self.config.get("pack_sons", "bois"))
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
        import musique
        musique.arreter()                   # jamais de musique en partie
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
            self.afficher_erreur("Stockfish n'a pas pu démarrer.",
                                 "Le moteur doit être dans le dossier moteur/",
                                 "(voir moteur/LISEZ-MOI.txt).")
            return None

    def afficher_erreur(self, *lignes):
        t = apparence.theme(self.config.get("theme_plateau"))
        fin = pygame.time.get_ticks() + 8000
        while pygame.time.get_ticks() < fin:
            for event in ui.evenements():
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
            ui.afficher()
            self.clock.tick(60)

    # ------------------------------------------------------------------ boucles

    def ouvrir_en_ligne(self):
        """Jouer en ligne par Steam : salon, partie, revanche.
        Tout le parcours vit dans partie_en_ligne.py."""
        import musique
        musique.arreter()
        self.en_ligne = True          # p36 : le salon a sa liste, pas de bandeau
        try:
            partie_en_ligne.lancer(self)
        finally:
            self.en_ligne = False
        self.board = None
        self._appliquer_taille(*self.screen.get_size())

    def _premier_lancement(self):
        """Accueil guide, une seule fois (17/10, travail p11)."""
        try:
            import premier_lancement
            from profil import get_profil
            profil = get_profil()
            if not premier_lancement.a_afficher(self.config, profil):
                return
            if premier_lancement.EcranPremierLancement(self.screen, profil).run(
                    self.clock, self.evenement_fenetre) == "quitter":
                self.quitter()
            self.config = self._charger_config()
            self.screen = pygame.display.get_surface()
            self._appliquer_taille(*self.screen.get_size())
        except Exception as e:
            print("[ACCUEIL] %s" % e)

    def _proposer_le_rapport_de_plantage(self):
        """24/10 (p29) : le lancement precedent a plante (plantage.py) : on propose
        d'envoyer le rapport avec « Signaler », deja rempli."""
        try:
            import plantage
            d = plantage.en_attente()
            if d is None:
                return
            from ecran_plantage import EcranPlantage
            reponse = EcranPlantage(self.screen, d).run(self.clock, self.evenement_fenetre)
            if reponse == "quitter":
                self.quitter()
            if reponse == "non":
                plantage.oublier()
            elif reponse == "plus_tard":
                plantage.propose_une_fois_de_plus()
            elif reponse == "envoyer":
                from ecran_signaler import EcranSignaler
                if EcranSignaler(self.screen, self.version, plantage.message(d),
                                 plantage.journal(d), apres_envoi=plantage.oublier).run(
                        self.clock, self.evenement_fenetre) == "quitter":
                    self.quitter()
                if plantage.en_attente() is not None:     # Annuler : on reproposera
                    plantage.propose_une_fois_de_plus()
            self.screen = pygame.display.get_surface()
            self._appliquer_taille(*self.screen.get_size())
        except Exception as e:
            print("[PLANTAGE] %s" % e)

    def _preparer_l_adversaire(self):
        """24/10 (« lancer une partie est long ») : le Stockfish adversaire
        demarre en tache de fond pendant qu'on est au menu (~0,6 s) ; la
        premiere partie contre l'ordinateur se lance alors tout de suite."""
        import threading

        def demarrer():
            try:
                import moteurs
                moteurs.moteur_de_jeu(self.stockfish_path)
            except Exception as e:
                print("[MOTEURS] adversaire pas prepare a l'avance : %s" % e)
        threading.Thread(target=demarrer, daemon=True, name="adversaire").start()

    def run(self):
        self._premier_lancement()
        self._proposer_le_rapport_de_plantage()
        self._preparer_l_adversaire()
        while True:
            try:
                self._une_partie()
            except invitations.RetourAuMenu:
                # p36 : « Rejoindre » une invitation pendant les reglages, la
                # partie (deja gardee par le bandeau) ou sa revue : retour au
                # menu, qui file au salon de l'ami.
                self.en_partie = False
                self.cleanup_game()
                self._retour_force_au_menu()
            self.menu.annoncer_reprise(sauvegarde.lire() is not None,
                                       sauvegarde.resume(sauvegarde.lire()))

    def _une_partie(self):
        """Menu -> reglages -> partie(s). Revient au menu."""
        if self.show_menu() == "reprendre":
            self.reglages = dict(self.reprise.get("reglages") or {})
        elif not self.demander_reglages():
            return
        rejouer = True
        while rejouer:
            rejouer = False
            if self.preparer_partie():
                self.en_partie = True
                try:
                    rejouer = self.boucle_de_partie() == "rejouer"
                finally:
                    self.en_partie = False
            self.cleanup_game()

    # ------------------------------------------------------------------ pause

    def _peut_ouvrir_la_pause(self, event):
        """Echap sans rien de selectionne, partie en cours (17/10, travail p10)."""
        if event.type != pygame.KEYDOWN or event.key != pygame.K_ESCAPE:
            return False
        b = self.board
        if b.game_over or b.selected_square is not None or b.dragging:
            return False
        if getattr(b, "premove", None):
            return False
        promotion = getattr(b, "promotion", None)
        if promotion is not None and getattr(promotion, "actif", False):
            return False
        return True

    def _ouvrir_la_pause(self):
        self._pendule_tournait = bool(self.board.timer.active and self.board.timer.demarree)
        self.board.timer.pause()
        self.pause.theme_plateau = self.board.theme_plateau
        self.pause.screen = self.screen
        self.pause.ouvrir()

    def _fermer_la_pause(self):
        self.pause.fermer()
        if getattr(self, "_pendule_tournait", False) and not self.board.game_over:
            self.board.timer.reprendre()

    def _evaluation_en_direct(self):
        a = getattr(self, "analyse_en_direct", None)
        if a is None or getattr(a, "plateau_id", None) != id(self.board):
            return None
        try:
            return a.evaluation_connue(a.nombre_de_coups())
        except Exception:
            return None

    def _action_de_pause(self, action):
        """Renvoie 'menu' pour quitter la partie, sinon None."""
        if action == "reprendre":
            self._fermer_la_pause()
        elif action == "options":
            self.ouvrir_options()
            import musique
            musique.arreter(0)              # Options a pu la relancer : pas en partie
            self._appliquer_preferences(self.board)
            self.pause.screen = self.screen
            self.pause.theme_plateau = self.board.theme_plateau
        elif action == "nulle":
            if self.game_mode == "hotseat":
                self.pause.fermer()
                self.board.terminer_partie("Nulle d'un commun accord", "1/2-1/2")
            else:
                couleur_ia = chess.WHITE if getattr(self.board, "ia_joue_blancs", False) \
                    else chess.BLACK
                accepte, raison = menu_pause.ordinateur_accepte_la_nulle(
                    self.board.board, couleur_ia, self._evaluation_en_direct())
                print("[PAUSE] nulle proposee : %s" % raison)
                if accepte:
                    self.pause.fermer()
                    self.board.terminer_partie("Nulle acceptée par l'ordinateur",
                                               "1/2-1/2")
                else:
                    self.pause.message = raison
        elif action == "abandon":
            self.pause.fermer()
            self.board.game_buttons._abandonner()
        elif action == "menu":
            self.pause.fermer()
            sauvegarde.enregistrer(self.board, self.game_mode, self.reglages)
            return "menu"
        return None

    def boucle_de_partie(self):
        """Joue la partie. Renvoie 'menu' ou 'rejouer'."""
        self.pause = menu_pause.MenuPause(
            self.screen, self.board.theme_plateau,
            nulle_possible=self.game_mode in ("stockfish", "hotseat"))
        self._activite_ms, self._coups_vus = pygame.time.get_ticks(), -1
        while True:
            evenements = ui.evenements()
            for event in evenements:
                if event.type == pygame.QUIT:
                    self.quitter()
                if self.evenement_fenetre(event):
                    continue
                if self.pause.ouvert:
                    if self._action_de_pause(self.pause.handle_event(event)) == "menu":
                        return "menu"
                    continue
                if self._peut_ouvrir_la_pause(event):
                    self._ouvrir_la_pause()
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

            if not self.pause.ouvert:          # en pause, tout est fige
                if self.current_mode is not None:
                    self.current_mode.update()
                self.board.update()

            if self.board.game_over:
                self._partie_terminee()
            elif not self.pause.ouvert:
                self.sauvegardeur.peut_etre(self.board, self.game_mode, self.reglages)
                self._suivre_analyse()

            self.board.draw()
            self.pause.draw()
            self.aide.draw(self.screen, self.board.theme_plateau)
            ui.afficher()
            self.clock.tick(self.cadence_de_partie(evenements))

    # 23/10 (banc d'essai) : au repos, la partie prenait ~40 % d'un coeur en
    # dessinant 60 images/s d'une position immobile. 60 images/s pendant
    # 1,5 s apres un geste, un coup ou pendant une animation ; 30 sinon.
    REPOS_APRES_MS = 1500

    def cadence_de_partie(self, evenements=()):
        maintenant = pygame.time.get_ticks()
        coups = len(self.board.board.move_stack)
        anime = (getattr(self.board.animation, "animations", None)
                 or getattr(self.board.retournement, "vols", None))
        if evenements or anime or coups != getattr(self, "_coups_vus", coups) \
                or self.board.game_over or getattr(getattr(self, "pause", None), "ouvert", False):
            self._activite_ms = maintenant
        self._coups_vus = coups
        if maintenant - getattr(self, "_activite_ms", maintenant) < self.REPOS_APRES_MS:
            return 60
        return ui.images_au_repos()

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
        self.brancher_analyse(infos.get("pgn") if infos else "")

    def brancher_analyse(self, chemin_pgn=""):
        """L'analyse de la partie qui vient de finir, rangee a cote de son PGN
        (<partie>.analyse.json : revue, statistiques, « Mes erreurs »).
        Sert aussi a la fin d'une partie en ligne (partie_en_ligne.py)."""
        self._fichier_analyse = None
        if chemin_pgn:
            self._fichier_analyse = os.path.splitext(chemin_pgn)[0] + ".analyse.json"
        try:
            self.board.end_screen.preparer_le_coach(chemin_pgn)     # 24/10 (p27)
        except Exception as e:
            print("[COACH] %s" % e)
        # La revue de partie : l'analyse faite PENDANT la partie est reprise
        # telle quelle (rien a recalculer) ; sinon elle demarre maintenant.
        direct = getattr(self, "analyse_en_direct", None)
        if direct is not None and getattr(direct, "plateau_id", None) == id(self.board):
            self._suivre_analyse(force=True, en_ligne=True)
            direct.finir_le_suivi()
            self.board.end_screen.analyseur = direct
            self.analyse_en_direct = None
        try:
            analyseur = self.board.end_screen.lancer_analyse(
                self.stockfish_path, analyse_partie.puissance_de(self.config))
            if analyseur is not None and self._fichier_analyse:
                analyseur.definir_fichier_cache(self._fichier_analyse)
        except Exception as e:
            print("[ANALYSE] non lancee : %s" % e)

    # ---------------------------------------------------- analyse en direct

    def _suivre_analyse(self, force=False, en_ligne=False):
        """SickChess 17/10 (demande de Julien) : Stockfish analyse la partie
        PENDANT qu'on joue, sans rien afficher. A la fin, la precision et la
        revue sont pretes tout de suite. Moitie des coeurs seulement, pour ne
        pas ralentir l'adversaire. "analyse_pendant_partie": false la coupe."""
        if self.game_mode not in ("stockfish", "hotseat") and not en_ligne:
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
                                analyse_partie.puissance_de(self.config), suivi=True,
                                threads=max(1, coeurs // 2))
            a.plateau_id = id(self.board)
            a.demarrer()
            self.analyse_en_direct = a
        elif len(coups) > a.nombre_de_coups():
            a.ajouter_coups(coups[a.nombre_de_coups():])

    # ------------------------------------------------------------------ revue

    def ouvrir_revue(self, noms=None, cote_noir=False, apres_dessin=None):
        """Revue de la partie qui vient de finir (ecran_revue.py). En ligne,
        partie_en_ligne.py donne les noms, le camp du joueur, et apres_dessin
        garde la connexion en vie pendant la revue."""
        from ecran_revue import EcranRevue
        fin = self.board.end_screen
        analyseur = fin.lancer_analyse(self.stockfish_path,
                                       analyse_partie.puissance_de(self.config))
        if analyseur is None:
            return
        if noms is None and self.game_mode == "stockfish":
            cote_noir = bool(getattr(self.board, "ia_joue_blancs", False))
            ia = "Ordinateur (%s)" % self.reglages.get("elo", "?")
            noms = (ia, "Toi") if cote_noir else ("Toi", ia)
        revue = EcranRevue(self.screen, analyseur, self.config,
                           noms or ("Blancs", "Noirs"),
                           getattr(self.board, "result", "") or "",
                           getattr(self.board, "game_over_reason", "") or "",
                           cote_noir)
        if revue.run(self.clock, self.evenement_fenetre,
                     apres_dessin or self._dessiner_aide) == "quitter":
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
        # 24/10 (« lancer une partie est long ») : le Stockfish adversaire
        # n'est plus ferme en quittant une partie (le relancer prenait ~0,6 s
        # sur les 0,7 s d'un lancement). Il reste pret pour la partie suivante
        # et la revanche ; il est ferme en quittant le jeu (cleanup).
        # Sauf sur un petit PC (p31 : un seul Stockfish a la fois, la revue
        # qui suit lance le sien) : la on le ferme comme avant.
        if self._petit_pc():
            try:
                import moteurs
                moteurs.liberer("jeu")
            except Exception:
                if self.engine:
                    self.engine.quit()
        self.engine = None
        self.board = None
        self.current_mode = None

    @staticmethod
    def _petit_pc():
        try:
            import petit_pc
            return petit_pc.est_petit()
        except Exception:
            return False

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
