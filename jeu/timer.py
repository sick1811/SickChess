# timer.py - V6 : la pendule
#
# CE QUI CHANGE PAR RAPPORT A V5 (bug M4 du rapport, tes notes "timer bugg a
# 30sec ne clignote pas" et "la fin de partie n'est pas finie a 00:00") :
#   1. LA PARTIE SE TERMINE AU TEMPS. V5 plafonnait le temps a 0 et ne
#      prevenait personne : la pendule affichait 0:00 et la partie continuait.
#      update() renvoie maintenant la couleur qui a perdu au temps, et
#      board.update() termine la partie.
#   2. CLIGNOTEMENT SOUS 30 SECONDES, avec le son low_time.mp3 qui etait charge
#      depuis le debut et n'etait jamais joue.
#   3. La pendule ne tourne plus quand la partie est finie ni pendant le replay
#      (voir board.py), et pas non plus avant le tout premier coup.
#   4. Incrementation (Fischer) prise en charge : +N secondes par coup joue.
#   5. Les deux horloges sont affichees dans le panneau de droite. En V5 elles
#      etaient dessinees en (20,20) et (20,640), c'est-a-dire PAR-DESSUS
#      l'echiquier.
#   6. Duree et increment reglables dans config.json.
#
# AUCUNE FONCTION SUPPRIMEE : __init__(preset_id), update(is_white_turn),
# get_display_times(), get_time(is_white) et draw(screen) sont conservees.

import json
import os

import chess
import pygame

PRESETS = {1: 1, 2: 5, 3: 10, 4: 15}
SEUIL_ALERTE = 30.0          # secondes
PERIODE_CLIGNOTEMENT = 500   # millisecondes

FOND = (30, 27, 24)
FOND_ACTIF = (58, 52, 40)
BORDURE = (120, 108, 90)
TEXTE = (240, 236, 230)
TEXTE_INACTIF = (150, 145, 138)
ALERTE = (235, 70, 60)

# Position des deux horloges dans le panneau de droite.
BOITE_L, BOITE_H = 200, 62
X_HORLOGE = 1050
Y_HORLOGE_HAUT = 22
Y_HORLOGE_BAS = 636


def _reglages():
    defauts = {"minutes": None, "preset_pendule": 2, "increment_secondes": 0,
               "pendule_active": True}
    for dossier in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        chemin = os.path.join(dossier, "config.json")
        if os.path.exists(chemin):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    contenu = json.load(f)
                # JOURNEE DEBUG DU 04/09 : "null" ou "[]" dans config.json
                # faisait un TypeError sur le "in" et la pendule - donc TOUTE
                # partie - ne pouvait plus etre creee.
                if not isinstance(contenu, dict):
                    contenu = {}
                for cle in defauts:
                    if cle in contenu:
                        defauts[cle] = contenu[cle]
            except (ValueError, OSError):
                pass
            break
    return defauts


class ChessTimer:
    def __init__(self, preset_id=None, minutes=None, increment=None, active=None):
        reglages = _reglages()
        if preset_id is None:
            preset_id = reglages.get("preset_pendule", 2)
        if minutes is None:
            minutes = reglages.get("minutes")
        if minutes is None:
            minutes = PRESETS.get(preset_id, 5)
        if increment is None:
            increment = reglages.get("increment_secondes", 0)
        if active is None:
            active = bool(reglages.get("pendule_active", True))

        # 0 minute choisi dans l'ecran de reglages = partie sans limite de temps.
        if float(minutes) <= 0:
            active = False
            minutes = 60

        self.initial_time = float(minutes) * 60.0
        self.time_left = {chess.WHITE: self.initial_time,
                          chess.BLACK: self.initial_time}
        self.last_update = pygame.time.get_ticks()
        self.active = bool(active)
        # V8 (03/09) - TON BUG "l'historique ne montre que des parties sans le
        # temps". `active` voulait dire DEUX choses a la fois : "cette partie a
        # une pendule" et "la pendule tourne en ce moment". Or terminer_partie()
        # appelle pause(), qui met active a False - et c'est PILE a ce
        # moment-la que end_screen ecrit le PGN. Resultat : toutes tes parties,
        # meme jouees en 15 min + 3 s, portaient [TimeControl "Sans limite de
        # temps"]. Les deux idees sont maintenant separees : `active` reste la
        # pendule qui tourne, `avec_pendule` dit s'il y a une cadence du tout.
        self.avec_pendule = bool(active)
        self.increment = float(increment)

        self.demarree = False          # ne compte qu'apres le premier coup
        self.perdant_au_temps = None
        self.alerte_jouee = {chess.WHITE: False, chess.BLACK: False}
        self.sons = None               # SoundManager, branche par ChessBoard

        self.font = None
        self.font_petit = None
        # Zones fixees par la disposition (layout.py). En V6 les horloges
        # etaient dessinees a des coordonnees fixes, donc par-dessus
        # l'echiquier des que la fenetre changeait de taille.
        self.zone_haut = (X_HORLOGE, Y_HORLOGE_HAUT, BOITE_L, BOITE_H)
        self.zone_bas = (X_HORLOGE, Y_HORLOGE_BAS, BOITE_L, BOITE_H)
        self.theme = None
        # V7.1 - CORRECTION DE TON BUG "des fois l'horloge noire est chez les
        # blancs" : les horloges etaient toujours dessinees Noirs en haut,
        # Blancs en bas, meme quand le plateau etait retourne (partie a deux sur
        # ce PC, ou partie en ligne dans laquelle tu joues les Noirs). L'horloge
        # du bas doit etre celle du joueur affiche en bas.
        self.flipped = False

    # ------------------------------------------------------------------ pilotage

    def demarrer(self):
        """Lance le decompte (appele au premier coup joue)."""
        if not self.demarree:
            self.demarree = True
            self.last_update = pygame.time.get_ticks()

    def pause(self):
        self.active = False

    def reprendre(self):
        self.active = True
        self.last_update = pygame.time.get_ticks()

    def ajouter_increment(self, couleur):
        """Bonus Fischer apres le coup joue."""
        if self.increment > 0:
            self.time_left[couleur] += self.increment

    @staticmethod
    def _nombre(valeur, defaut):
        """Un nombre, quoi qu'on nous donne.

        JOURNEE DEBUG DU 04/09. En ligne, la cadence arrive PAR LE RESEAU
        (message "reglages" de l'hote). Un client d'une autre version, un
        message abime ou un plaisantin envoyaient une chaine, float() levait
        une ValueError, et comme game_manager.boucle_de_partie n'entoure pas
        current_mode.update(), LE JEU SE FERMAIT EN PLEINE PARTIE. On ne fait
        plus confiance a ce qui vient d'en face : on retombe sur la valeur
        par defaut et on le dit dans le journal.
        """
        try:
            return float(valeur)
        except (TypeError, ValueError):
            print("[PENDULE] cadence illisible (%r), on garde %s"
                  % (valeur, defaut))
            return float(defaut)

    def set_time(self, minutes, increment=None, active=None):
        """Change la cadence en cours de route (ecran de reglages, mode en ligne)."""
        minutes = self._nombre(minutes, 5)
        if minutes <= 0:
            active = False
            minutes = 60
        elif active is None:
            active = True
        self.initial_time = float(minutes) * 60.0
        self.time_left = {chess.WHITE: self.initial_time,
                          chess.BLACK: self.initial_time}
        if increment is not None:
            self.increment = max(0.0, self._nombre(increment, self.increment))
        self.active = bool(active)
        self.avec_pendule = bool(active)
        self.perdant_au_temps = None
        self.alerte_jouee = {chess.WHITE: False, chess.BLACK: False}
        self.demarree = False

    def appliquer_reglages(self, reglages):
        """Applique un dictionnaire venu de l'ecran de reglages."""
        if not reglages:
            return
        self.set_time(reglages.get("minutes", 5),
                      reglages.get("increment", 0),
                      reglages.get("pendule_active"))

    def description_cadence(self):
        # On lit avec_pendule et NON active : une partie finie a sa pendule en
        # pause, ce qui ne change rien a la cadence a laquelle elle a ete jouee.
        if not getattr(self, "avec_pendule", self.active):
            return "Sans limite de temps"
        minutes = int(self.initial_time // 60)
        if self.increment:
            return "%d min + %d s" % (minutes, int(self.increment))
        return "%d min" % minutes

    # ------------------------------------------------------------------ decompte

    def update(self, is_white_turn):
        """Fait tourner la pendule. Renvoie la couleur qui vient de perdre au
        temps, sinon None. (En V5 cette methode ne renvoyait jamais rien : la
        partie ne pouvait pas se terminer a 0:00.)"""
        maintenant = pygame.time.get_ticks()
        if not self.active or not self.demarree or self.perdant_au_temps is not None:
            self.last_update = maintenant
            return None

        delta = (maintenant - self.last_update) / 1000.0
        self.last_update = maintenant
        if delta <= 0:
            return None

        couleur = chess.WHITE if is_white_turn else chess.BLACK
        self.time_left[couleur] -= delta

        # Alerte sous 30 secondes : un seul bip par joueur.
        if 0 < self.time_left[couleur] <= SEUIL_ALERTE and not self.alerte_jouee[couleur]:
            self.alerte_jouee[couleur] = True
            if self.sons is not None:
                self.sons.play("low_time")

        if self.time_left[couleur] <= 0:
            self.time_left[couleur] = 0.0
            self.perdant_au_temps = couleur
            return couleur
        return None

    def temps_ecoule(self):
        return self.perdant_au_temps

    def en_alerte(self, couleur):
        return 0 < self.time_left[couleur] <= SEUIL_ALERTE

    # ------------------------------------------------------------------ lecture

    def get_display_times(self):
        return self.get_time(chess.WHITE), self.get_time(chess.BLACK)

    def secondes_restantes(self, is_white):
        """Le temps restant EN SECONDES, pas en texte.

        V7.2 : get_time renvoie une chaine prete a afficher ("2:07"). Pour
        calculer le rythme de Stockfish il faut le nombre lui-meme - c'est ce
        que rend cette methode. get_time n'est pas touchee : tout ce qui
        l'utilise continue de marcher exactement pareil.
        """
        return max(0.0, float(self.time_left[bool(is_white)]))

    def cadence_en_secondes(self):
        """(temps initial, increment) en secondes. (None, 0) sans pendule."""
        if not getattr(self, "avec_pendule", self.active):
            return None, 0.0
        return float(self.initial_time), float(self.increment)

    def get_time(self, is_white):
        temps = max(0.0, self.time_left[is_white])
        minutes = int(temps // 60)
        secondes = int(temps % 60)
        if temps < 60:
            # Sous une minute on affiche les dixiemes, comme sur Lichess.
            dixiemes = int((temps % 1) * 10)
            return "%d:%02d.%d" % (minutes, secondes, dixiemes)
        return "%d:%02d" % (minutes, secondes)

    # ------------------------------------------------------------------ dessin

    def camp_en_bas(self):
        """Couleur affichee en bas de l'ecran, selon l'orientation du plateau."""
        return chess.BLACK if self.flipped else chess.WHITE

    def zone_de(self, couleur):
        """Zone de l'horloge d'un camp : celui du bas est en bas, toujours."""
        return self.zone_bas if couleur == self.camp_en_bas() else self.zone_haut

    def draw(self, screen, trait=None):
        import ui

        bas = self.camp_en_bas()
        zones = {bas: self.zone_bas, not bas: self.zone_haut}

        t = self.theme or {}
        fond = t.get("fond", FOND)
        fond_actif = t.get("panneau", FOND_ACTIF)
        bordure = t.get("bord", BORDURE)
        texte_actif = t.get("texte", TEXTE)
        texte_inactif = t.get("texte_discret", TEXTE_INACTIF)

        clignote = (pygame.time.get_ticks() // PERIODE_CLIGNOTEMENT) % 2 == 0
        for couleur, nom in ((chess.BLACK, "NOIRS"), (chess.WHITE, "BLANCS")):
            rect = pygame.Rect(*zones[couleur])
            if rect.height < 20 or rect.width < 80:
                continue
            actif = (trait == couleur) if trait is not None else False
            ui.cadre(screen, rect, fond_actif if actif else fond,
                     t.get("accent", bordure) if actif else bordure, 2, 8)

            # Pastille de couleur : on voit d'un coup d'oeil a qui est l'horloge,
            # meme quand le plateau est retourne.
            rayon = max(6, rect.height // 6)
            centre = (rect.x + 10 + rayon, rect.centery)
            pygame.draw.circle(screen, (245, 243, 238) if couleur == chess.WHITE
                               else (40, 38, 36), centre, rayon)
            pygame.draw.circle(screen, bordure, centre, rayon, 1)

            taille_nom = max(11, min(15, rect.height // 4))
            largeur_nom = ui.mesurer(nom, taille_nom, gras=True)[0]
            ui.texte(screen, nom, centre[0] + rayon + 8,
                     rect.centery - taille_nom // 2 - 1, taille_nom,
                     texte_inactif, gras=True, largeur_max=largeur_nom + 2)

            # Le chrono prend toute la place restante, sans jamais toucher le nom.
            x_texte = centre[0] + rayon + 12 + largeur_nom
            place = max(40, rect.right - 12 - x_texte)
            taille_chiffres = max(16, min(38, int(rect.height * 0.55)))

            # SickChess - BUG "la fin de partie n'est pas finie a 00:00" :
            # on testait self.active, qui passe a False des que la partie se
            # termine (pause). Les deux pendules affichaient alors "--:--" au
            # lieu du temps final (0:00.0 pour celui qui a perdu au temps).
            # avec_pendule dit s'il y a une cadence ; active, si elle tourne.
            if not getattr(self, "avec_pendule", self.active):
                # Partie sans limite de temps : on n'affiche pas de faux chrono.
                ui.texte(screen, "--:--", rect.right - 12,
                         rect.centery - taille_chiffres // 2 - 2, taille_chiffres,
                         texte_inactif, gras=True, mono=True,
                         largeur_max=place, ancre="droite", ajuster=True)
                continue

            if self.en_alerte(couleur):
                couleur_texte = ALERTE if clignote else (255, 190, 185)
            elif self.time_left[couleur] <= 0:
                couleur_texte = ALERTE
            else:
                couleur_texte = texte_actif if actif else texte_inactif

            ui.texte(screen, self.get_time(couleur), rect.right - 12,
                     rect.centery - taille_chiffres // 2 - 2, taille_chiffres,
                     couleur_texte, gras=True, mono=True,
                     largeur_max=place, ancre="droite", ajuster=True)
