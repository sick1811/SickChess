# invitations.py - SickChess 24/10 (travail p36) : l'invitation d'un ami Steam
# affichee DANS le jeu.
#
# Quand un ami t'invite (depuis son salon SickChess ou la fenetre Steam) pendant
# que SickChess est ouvert, Steam previent le jeu (steam.py, « invitation_recue »).
# On affiche alors, sur N'IMPORTE QUEL ecran, un bandeau en haut :
#
#       Paul t'invite à jouer        [Rejoindre]  [Plus tard]
#
#   - Rejoindre, depuis le menu : on file au salon de l'ami ;
#   - depuis un autre ecran (problemes, revue, options...) : l'ecran se ferme et
#     on file au salon (exception RetourAuMenu, rattrapee par game_manager) ;
#   - pendant une partie : on demande d'abord confirmation ; la partie est
#     gardee, « Reprendre la partie » la retrouve dans le menu ;
#   - Plus tard : le bandeau s'en va ; l'invitation reste 10 minutes dans
#     « Jouer en ligne », liste « Invitations reçues ».
# Pendant le jeu en ligne lui-meme, pas de bandeau (le salon a sa liste).
#
# Le bandeau est un « crochet » d'ui.py : il se dessine juste avant l'affichage
# de chaque image et prend ses propres clics (ui.evenements / ui.afficher).

import time

import pygame

import apparence
import ui

DUREE_DE_VIE_S = 600          # une invitation reste proposee 10 minutes
BANDEAU_S = 45                # le bandeau se range tout seul apres 45 s
POMPE_S = 0.25                # Steam lu 4 fois par seconde hors du menu

_RECUES = []                  # [{salon, ami, nom, recue, vue}], la plus recente en dernier


class RetourAuMenu(BaseException):
    """Ferme l'ecran en cours et revient au menu (pour rejoindre un ami).
    BaseException : les « except Exception » des ecrans ne l'arretent pas."""


# ------------------------------------------------------------------ la liste

def recevoir(steam, maintenant=None):
    """Range les invitations arrivees de Steam. Renvoie les nouvelles."""
    maintenant = time.monotonic() if maintenant is None else maintenant
    nouvelles = []
    for ev in steam.evenements("invitation_recue"):
        salon = int(ev.get("salon") or 0)
        if not salon:
            continue
        oublier(salon)                    # une nouvelle invitation remplace l'ancienne
        try:
            nom = steam.nom_de(ev.get("ami")) or "Un ami"
        except Exception:
            nom = "Un ami"
        invitation = {"salon": salon, "ami": int(ev.get("ami") or 0), "nom": nom[:24],
                      "recue": maintenant, "vue": False}
        _RECUES.append(invitation)
        nouvelles.append(invitation)
    return nouvelles


def ajouter(salon, nom, ami=0, maintenant=None):
    """Pour les tests et le mode test : comme si Steam l'avait apportee."""
    oublier(salon)
    invitation = {"salon": int(salon), "ami": int(ami), "nom": nom,
                  "recue": time.monotonic() if maintenant is None else maintenant,
                  "vue": False}
    _RECUES.append(invitation)
    return invitation


def en_attente(maintenant=None):
    """Les invitations encore valables, la plus recente d'abord."""
    maintenant = time.monotonic() if maintenant is None else maintenant
    _RECUES[:] = [i for i in _RECUES if maintenant - i["recue"] < DUREE_DE_VIE_S]
    return sorted(reversed(_RECUES), key=lambda i: -i["recue"])   # a egalite : la derniere arrivee


def oublier(salon):
    _RECUES[:] = [i for i in _RECUES if i["salon"] != int(salon)]


def vider():
    del _RECUES[:]


def depuis_quand(invitation, maintenant=None):
    """« à l'instant », « il y a 3 min »."""
    maintenant = time.monotonic() if maintenant is None else maintenant
    minutes = int((maintenant - invitation["recue"]) // 60)
    return "à l'instant" if minutes < 1 else "il y a %d min" % minutes


def rejoindre(invitation):
    """Demande au jeu d'aller au salon de l'ami (lu par le menu)."""
    import partie_en_ligne
    oublier(invitation["salon"])
    partie_en_ligne.demander_a_rejoindre(invitation["salon"])


# ------------------------------------------------------------------ le bandeau

class BandeauInvitation:
    """Le crochet d'ui.py. manager : le GameManager (ecran courant, partie en
    cours, configuration) ; il dit aussi s'il est au menu (au_menu) ou dans
    le jeu en ligne (en_ligne)."""

    def __init__(self, manager, steam=None):
        self.manager = manager
        self.steam = steam
        self.confirmation = None          # invitation a confirmer (partie en cours)
        self._pompe_le = 0.0
        self._boutons = {}
        self._rect = None
        self._sonne = set()

    # --------------------------------------------------------- etat

    def _steam(self):
        if self.steam is None:
            import steam as module_steam
            self.steam = module_steam.instance()
        return self.steam

    def actif(self):
        """Pas de bandeau dans le jeu en ligne (le salon a sa propre liste)."""
        return not getattr(self.manager, "en_ligne", False)

    def affichee(self, maintenant=None):
        """L'invitation montree dans le bandeau (ou None)."""
        if self.confirmation is not None:
            return self.confirmation
        maintenant = time.monotonic() if maintenant is None else maintenant
        for invitation in en_attente(maintenant):
            if not invitation["vue"]:
                if maintenant - invitation["recue"] > BANDEAU_S:
                    invitation["vue"] = True      # rangee dans la liste
                    continue
                return invitation
        return None

    def partie_en_cours(self):
        """Une partie (ordinateur ou a deux) pas finie : on demande avant de la quitter."""
        m = self.manager
        board = getattr(m, "board", None)
        return bool(getattr(m, "en_partie", False) and board is not None
                    and not board.game_over
                    and getattr(m, "game_mode", None) in ("stockfish", "hotseat"))

    # --------------------------------------------------------- crochet

    def filtrer(self, evenements):
        self._pomper()
        if not self.actif():
            return evenements
        invitation = self.affichee()
        if invitation is None:
            return evenements
        return [event for event in evenements if not self._prendre(event, invitation)]

    def _pomper(self):
        """Lit Steam (au menu, partie_en_ligne le fait deja)."""
        maintenant = time.monotonic()
        if maintenant - self._pompe_le < POMPE_S:
            return
        self._pompe_le = maintenant
        s = self._steam()
        if not getattr(s, "actif", False):
            return
        if not getattr(self.manager, "au_menu", False) and not getattr(self.manager, "en_ligne", False):
            s.pomper()
        for invitation in recevoir(s):
            print("[INVITATION] %s t'invite (salon %d)" % (invitation["nom"], invitation["salon"]))
        try:                                   # 24/10 (p37) : scores en attente
            import classements
            classements.instance().suivre()
        except Exception as e:
            print("[CLASSEMENTS] %s" % e)

    def _prendre(self, event, invitation):
        """True si l'evenement est pour le bandeau (il ne va pas a l'ecran)."""
        if event.type == pygame.MOUSEMOTION:
            for bouton in self._boutons.values():
                bouton.maj_survol(event.pos)
            return False
        if self.confirmation is not None:
            # Fenetre de confirmation : elle prend tout le clavier et la souris.
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._rester()
                return True
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._quitter_la_partie(invitation)
                return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                cle = self._cle_sous(event.pos)
                if cle == "confirmer":
                    self._quitter_la_partie(invitation)
                elif cle == "rester":
                    self._rester()
                return True
            return event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL,
                                  getattr(pygame, "TEXTINPUT", -1))
        if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return False
        if self._rect is None or not self._rect.collidepoint(event.pos):
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cle = self._cle_sous(event.pos)
            if cle == "rejoindre":
                self.cliquer_rejoindre(invitation)
            elif cle == "plus_tard":
                invitation["vue"] = True
        return True

    def _cle_sous(self, pos):
        for cle, bouton in self._boutons.items():
            if bouton.contient(pos):
                return cle
        return None

    # --------------------------------------------------------- actions

    def cliquer_rejoindre(self, invitation):
        if getattr(self.manager, "au_menu", False):
            rejoindre(invitation)             # le menu file au salon tout seul
            return
        if self.partie_en_cours():
            self.confirmation = invitation
            timer = getattr(self.manager.board, "timer", None)
            self._pendule = bool(timer is not None and timer.active and timer.demarree)
            if timer is not None:
                timer.pause()
            return
        rejoindre(invitation)
        raise RetourAuMenu()

    def _rester(self):
        invitation, self.confirmation = self.confirmation, None
        if invitation is not None:
            invitation["vue"] = True
        timer = getattr(getattr(self.manager, "board", None), "timer", None)
        if timer is not None and getattr(self, "_pendule", False):
            timer.reprendre()

    def _quitter_la_partie(self, invitation):
        self.confirmation = None
        m = self.manager
        try:
            import sauvegarde
            sauvegarde.enregistrer(m.board, m.game_mode, m.reglages)
        except Exception as e:
            print("[INVITATION] partie non gardee : %s" % e)
        rejoindre(invitation)
        raise RetourAuMenu()

    # --------------------------------------------------------- dessin

    def _bouton(self, cle, libelle, rect, principal=False, taille=15):
        bouton = self._boutons.get(cle)
        if bouton is None:
            bouton = self._boutons[cle] = ui.Bouton(rect, libelle, cle, taille=taille)
        bouton.libelle = libelle
        bouton.placer(rect)
        bouton.selectionne = principal
        return bouton

    def dessiner(self, ecran):
        self._rect = None
        if not self.actif():
            return
        invitation = self.affichee()
        if invitation is None:
            return
        if invitation["salon"] not in self._sonne:
            self._sonne.add(invitation["salon"])
            self._sonner()
        t = apparence.theme(getattr(self.manager, "config", {}).get("theme_plateau"))
        ech = ui.echelle(ecran)
        self._boutons = {}
        if self.confirmation is not None:
            self._dessiner_confirmation(ecran, t, ech, invitation)
            return
        largeur, _ = ecran.get_size()
        h = int(52 * ech)
        texte = "%s t'invite à jouer" % invitation["nom"]
        l_bouton = int(118 * ech)
        l_texte = ui.mesurer(texte, ui.t(17, ech), gras=True)[0]
        l = min(largeur - 20, l_texte + 2 * l_bouton + int(64 * ech))
        rect = pygame.Rect(0, 0, l, h)
        rect.midtop = (largeur // 2, int(10 * ech))
        self._rect = rect
        ui.cadre(ecran, rect, t["panneau"], t["accent"], 2, 14, ombre=True)
        marge = int(10 * ech)
        hb = h - 2 * marge
        plus_tard = self._bouton("plus_tard", "Plus tard",
                                 (rect.right - marge - l_bouton, rect.y + marge, l_bouton, hb))
        rejoindre_ = self._bouton("rejoindre", "Rejoindre",
                                  (plus_tard.rect.x - marge - l_bouton, rect.y + marge, l_bouton, hb),
                                  principal=True)
        ui.texte(ecran, texte, rect.x + int(16 * ech),
                 rect.centery - ui.police(ui.t(17, ech), True).get_height() // 2,
                 ui.t(17, ech), t["texte"], gras=True,
                 largeur_max=rejoindre_.rect.x - rect.x - int(24 * ech), ajuster=True)
        souris = pygame.mouse.get_pos()
        for bouton in self._boutons.values():
            bouton.maj_survol(souris)
            bouton.dessiner(ecran, t, rayon=10)

    def _dessiner_confirmation(self, ecran, t, ech, invitation):
        largeur, hauteur = ecran.get_size()
        ui.voile(ecran, opacite=150)
        rect = pygame.Rect(0, 0, min(largeur - 40, int(480 * ech)), int(200 * ech))
        rect.center = (largeur // 2, hauteur // 2)
        self._rect = rect
        ui.cadre(ecran, rect, t["panneau"], t["accent"], 2, 16, ombre=True)
        x, l = rect.x + int(20 * ech), rect.width - int(40 * ech)
        ui.texte(ecran, "Rejoindre %s ?" % invitation["nom"], rect.centerx, rect.y + int(20 * ech),
                 ui.t(24, ech), t["texte"], gras=True, ancre="centre", largeur_max=l, ajuster=True)
        ui.paragraphe(ecran, "Ta partie en cours est gardée : « Reprendre la partie » "
                             "la retrouvera dans le menu.",
                      pygame.Rect(x, rect.y + int(64 * ech), l, int(60 * ech)),
                      ui.t(15, ech), t["texte_discret"])
        hb = int(44 * ech)
        lb = (l - int(12 * ech)) // 2
        y = rect.bottom - int(20 * ech) - hb
        self._bouton("rester", "Rester", (x, y, lb, hb))
        self._bouton("confirmer", "Rejoindre", (x + lb + int(12 * ech), y, l - lb - int(12 * ech), hb),
                     principal=True, taille=17)
        souris = pygame.mouse.get_pos()
        for bouton in self._boutons.values():
            bouton.maj_survol(souris)
            bouton.dessiner(ecran, t, rayon=10)

    def _sonner(self):
        """Un petit son, une fois par invitation (si les sons sont actifs)."""
        config = getattr(self.manager, "config", {}) or {}
        if not config.get("sons_actifs", True):
            return
        try:
            if getattr(self, "_son", None) is None:
                from sounds import SoundManager
                self._son = SoundManager()
                self._son.set_volume(float(config.get("volume_sons", 0.6)))
            self._son.play("game_start")
        except Exception as e:
            print("[INVITATION] son : %s" % e)
