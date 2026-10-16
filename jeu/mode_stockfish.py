# mode_stockfish.py - V6 : Mode 1 - partie contre Stockfish
#
# CE QUI CHANGE PAR RAPPORT A V5 (bug M1 du rapport) :
#   1. set_custom_elo() est ENFIN APPELEE. En V5 elle existait dans engine.py et
#      n'etait invoquee nulle part dans tout le projet : Stockfish jouait donc
#      toujours a pleine puissance, quel que soit le reglage voulu.
#   2. Le temps de reflexion aleatoire est lu depuis config.json et transmis a
#      BackgroundAI (voir background_ai.py).
#   3. La reflexion s'arrete des que la partie est finie : plus de thread qui
#      continue de tourner dans le vide apres un mat ou un abandon.
#   4. Le moteur repart sur une table vide a chaque partie (ucinewgame).
#
# AUCUNE FONCTION SUPPRIMEE : __init__ et update sont conservees.

import json
import os
import random

import chess

from background_ai import BackgroundAI

# Reglages par defaut si config.json ne dit rien.
REGLAGES_PAR_DEFAUT = {
    "elo": 1500,
    "ia_temps_min_ms": 700,
    "ia_temps_max_ms": 5000,
    "ia_temps_humain": True,
    "ia_temps_moteur_max_ms": 1500,
}


def charger_reglages_ia():
    """Lit config.json et complete avec les valeurs par defaut."""
    reglages = dict(REGLAGES_PAR_DEFAUT)
    for dossier in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        chemin = os.path.join(dossier, "config.json")
        if os.path.exists(chemin):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    contenu = json.load(f)
                if not isinstance(contenu, dict):
                    # config.json abime : on garde les reglages par defaut.
                    print("[MODE STOCKFISH] config.json n'est pas un "
                          "dictionnaire, reglages par defaut")
                    contenu = {}
                for cle in REGLAGES_PAR_DEFAUT:
                    if cle in contenu:
                        reglages[cle] = contenu[cle]
                break
            except (ValueError, OSError) as e:
                print("[MODE STOCKFISH] config.json illisible (" + str(e)
                      + "), reglages par defaut")
    return reglages


class ModeStockfish:
    def __init__(self, board, engine, reglages=None):
        self.board = board
        self.engine = engine
        # Les reglages de l'ecran d'avant-partie sont prioritaires sur config.json.
        self.reglages = charger_reglages_ia()
        for cle in ("elo", "ia_temps_min_ms", "ia_temps_max_ms",
                    "ia_temps_humain", "ia_temps_moteur_max_ms"):
            if reglages and cle in reglages:
                self.reglages[cle] = reglages[cle]

        self.ia_joue_blancs = random.choice([True, False])
        self.board.ia_joue_blancs = self.ia_joue_blancs
        self.board.flipped = self.ia_joue_blancs
        self.board.hotseat_mode = False
        # Le plateau garde une reference au moteur : c'est ce qui permet
        # a la touche H de demander un indice sans passer par le mode.
        self.board.engine = engine

        # Niveau de jeu : c'est l'appel qui manquait en V5.
        if self.engine is not None:
            try:
                self.engine.nouvelle_partie()
            except AttributeError:
                pass
            try:
                self.engine.set_custom_elo(self.reglages["elo"])
            except Exception as e:
                print("[MODE STOCKFISH] reglage du niveau impossible : " + str(e))

        # IA completement separee du plateau.
        self.ai_manager = BackgroundAI(
            self.board,
            self.engine,
            temps_min_ms=self.reglages["ia_temps_min_ms"],
            temps_max_ms=self.reglages["ia_temps_max_ms"],
            humain=self.reglages["ia_temps_humain"],
            temps_moteur_max_ms=self.reglages["ia_temps_moteur_max_ms"],
        )
        self.board.ai_manager = self.ai_manager

        print("[INFO] Stockfish : elo %s, reflexion entre %s et %s ms%s"
              % (self.reglages["elo"],
                 self.reglages["ia_temps_min_ms"],
                 self.reglages["ia_temps_max_ms"],
                 "" if self.reglages["ia_temps_humain"] else " (rythme humain desactive)"))

        if self.ia_joue_blancs:
            print("[INFO] Stockfish joue les BLANCS et commence la partie.")
            self.ai_manager.start_thinking()
        else:
            print("[INFO] Stockfish joue les NOIRS. A toi de jouer !")

    def couleur_ia(self):
        return chess.WHITE if self.ia_joue_blancs else chess.BLACK

    def cest_le_tour_de_lia(self):
        return (not self.board.game_over) and self.board.board.turn == self.couleur_ia()

    def update(self):
        if self.ai_manager is None:
            return

        # Partie terminee : on coupe la reflexion au lieu de la laisser tourner.
        if self.board.game_over:
            if self.ai_manager.est_en_train_de_reflechir():
                self.ai_manager.stop()
            return

        # V7.2 - CORRECTION DU BLOCAGE DE L'IA ("stockfish ne reagit pas").
        #
        # CES DEUX LIGNES ETAIENT DANS LE MAUVAIS ORDRE, et c'est tout le bug.
        # Avant : on lancait une nouvelle reflexion, PUIS on jouait le coup
        # deja calcule. Donc a chaque coup :
        #   1. le fil de reflexion finit et depose son coup ;
        #   2. is_thinking repasse a False ;
        #   3. on relance AUSSITOT une reflexion - sur la position d'AVANT,
        #      puisque le coup depose n'a pas encore ete joue ;
        #   4. on joue le coup depose : la position change ;
        #   5. la reflexion lancee en 3 rend un coup pour l'ancienne position,
        #      qui est jete : "[BACKGROUND AI] position modifiee pendant le
        #      calcul, coup ignore" - les lignes de ton journal.
        # Un calcul sur deux etait perdu, et quand ca tombait mal l'IA
        # s'arretait franchement de jouer.
        #
        # On JOUE D'ABORD, on reflechit ENSUITE : la reflexion part toujours de
        # la position reelle.
        self.ai_manager.update()

        # L'IA ne reflechit que quand c'est son tour, et pas si un coup deja
        # calcule attend encore d'etre joue.
        if self.cest_le_tour_de_lia() \
                and not self.ai_manager.est_en_train_de_reflechir() \
                and not self.ai_manager.a_un_coup_en_attente():
            self.ai_manager.start_thinking()

    def arreter(self):
        """Appele au retour au menu pour ne laisser aucun thread derriere."""
        if self.ai_manager is not None:
            self.ai_manager.stop()
