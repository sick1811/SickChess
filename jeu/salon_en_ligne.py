# salon_en_ligne.py - SickChess : l'ecran "Jouer en ligne".
#
# Trois moments :
#   1. ACCUEIL   : creer une partie, ou rejoindre avec un code.
#   2. SALON     : l'hote choisit la cadence et sa couleur, et invite un ami
#                  (liste d'amis Steam dans le jeu, fenetre d'invitation Steam,
#                  ou code a dicter). L'invite voit les reglages en direct.
#   3. DEPART    : quand l'ami est la, l'hote clique LANCER. Les deux recoivent
#                  les memes reglages et la partie commence.
#
# Accepter une invitation dans Steam (discussion ou liste d'amis) amene
# directement au salon de l'ami : voir partie_en_ligne.invitation_en_attente().
#
# MODE_TEST : deux boutons "Test sur ce PC" permettent de jouer contre
# soi-meme avec deux fenetres du jeu, sans Steam. A mettre a False avant la
# sortie sur Steam.

import random
import time

import pygame

import apparence
import design
import freestyle
import steam as module_steam
import ui
from reseau_transport import TransportLocal, TransportSteam

MODE_TEST = True

CADENCES = [(3, 2), (5, 3), (10, 5), (15, 10), (30, 0), (0, 0)]
COULEURS = [("blanc", "Blancs"), ("hasard", "Au hasard"), ("noir", "Noirs")]
# Deux modes, Normal (regles FIDE) et Freestyle ; « Tournoi » = Freestyle joue
# au reglement du championnat FIDE Freestyle.
VARIANTES = [("normal", "Normal"), ("freestyle", "Freestyle")]
FACONS_960 = [("freestyle", "Au hasard"), ("tournoi", "Tournoi")]
NOMS_VARIANTES = {"normal": "Normal", "freestyle": "Freestyle",
                  "tournoi": "Freestyle (tournoi)"}
DELAI_STEAM = 20.0

MESSAGES_ENTREE = {
    2: "Cette partie n'existe plus.",
    4: "Cette partie est déjà complète.",
    6: "Tu ne peux pas entrer dans cette partie.",
    7: "Ton compte Steam est limite : les salons lui sont fermes.",
}


def _numero_valide(numero):
    """Numero Freestyle recu par le reseau : 0 a 959, sinon partie normale."""
    try:
        numero = int(numero)
    except (TypeError, ValueError):
        return None
    return numero if 0 <= numero < freestyle.NOMBRE_DE_POSITIONS else None


def libelle_cadence(minutes, increment):
    if not minutes:
        return "Sans pendule"
    return "%d min + %d s" % (minutes, increment) if increment else "%d min" % minutes


class SalonEnLigne:
    def __init__(self, screen, clock, evenement_fenetre=None, nom_local="Joueur",
                 steam=None, salon_a_rejoindre=0, config=None):
        self.screen = screen
        self.clock = clock
        self.evenement_fenetre = evenement_fenetre
        self.nom_local = nom_local
        self.steam = steam or module_steam.instance()
        self.config = config or {}

        self.etape = "accueil"         # accueil | attente_steam | salon
        self.attente_depuis = 0.0
        self.attente_quoi = ""
        self.erreur = ""
        self.info = ""
        self.transport = None
        self.salon = 0
        self.resultat = None

        minutes = int(self.config.get("minutes", 10) or 0)
        increment = int(self.config.get("increment_secondes", 5) or 0)
        self.cadence = (minutes, increment) if (minutes, increment) in CADENCES \
            else (10, 5)
        self.couleur = "hasard"
        self.variante = self.config.get("variante", "normal")
        if self.variante not in NOMS_VARIANTES:
            self.variante = "normal"
        self.reglages_hote = None       # vus par l'invite
        self._dernier_envoi_salon = 0.0

        self.champ_code = ui.ChampTexte(20)
        self.amis = []
        self._amis_le = -999.0
        self.invites = set()
        self.defilement_amis = 0
        self.zone_amis = pygame.Rect(0, 0, 0, 0)
        self._rect_code = pygame.Rect(0, 0, 0, 0)

        self._boutons = {}
        self._visibles = []

        if not self.steam.actif:
            self.steam.demarrer()
        if salon_a_rejoindre:
            self.rejoindre(salon_a_rejoindre)

    # ------------------------------------------------------------ actions

    def creer(self):
        self.erreur = ""
        if not self.steam.demarrer():
            self.erreur = self.steam.erreur
            return
        self.steam.evenements("salon_cree", "salon_entre")
        self.steam.creer_salon(2)
        self._attendre("creation", "Creation de la partie sur Steam...")

    def rejoindre(self, salon):
        self.erreur = ""
        if not salon:
            self.erreur = "Ce code n'est pas valide."
            return
        if not self.steam.demarrer():
            self.erreur = self.steam.erreur
            return
        self.steam.evenements("salon_entre")
        self.steam.rejoindre_salon(salon)
        self.salon = int(salon)
        self._attendre("entree", "Connexion à la partie de ton ami...")

    def test_local(self, hote):
        self.erreur = ""
        self.transport = TransportLocal(hote, self.nom_local + (" (hôte)" if hote
                                                                else " (invite)"))
        if self.transport.erreur:
            self.erreur = self.transport.erreur
            self.transport = None
            return
        self.salon = 0
        self.etape = "salon"

    def _attendre(self, quoi, info):
        self.etape = "attente_steam"
        self.attente_quoi = quoi
        self.attente_depuis = time.monotonic()
        self.info = info

    def _retour_accueil(self, erreur=""):
        if self.transport is not None:
            self.transport.fermer()
        elif self.salon:
            self.steam.quitter_salon(self.salon)
        self.transport = None
        self.salon = 0
        self.reglages_hote = None
        self.invites = set()
        self.etape = "accueil"
        self.erreur = erreur

    def _suivre_steam(self):
        """Evenements Steam pendant l'attente (creation / entree)."""
        self.steam.pomper()
        for ev in self.steam.evenements("invitation_acceptee"):
            if self.transport is None or not self.transport.connecte():
                self._retour_accueil()
                self.rejoindre(ev["salon"])
                return
        if self.etape != "attente_steam":
            return
        if time.monotonic() - self.attente_depuis > DELAI_STEAM:
            self._retour_accueil("Steam ne répond pas. Réessaie dans un moment.")
            return
        if self.attente_quoi == "creation":
            for ev in self.steam.evenements("salon_cree"):
                if not ev["ok"]:
                    self._retour_accueil("Steam n'a pas pu créer la partie.")
                    return
                self.salon = ev["salon"]
                self.steam.ecrire_info(self.salon, "jeu", module_steam.NOM_DU_JEU)
                self.steam.ecrire_info(self.salon, "hote", self.steam.mon_nom())
                self._ouvrir_transport()
                return
        else:
            for ev in self.steam.evenements("salon_entre"):
                if ev["salon"] != self.salon:
                    continue
                if not ev["ok"]:
                    self.salon = 0
                    self._retour_accueil(MESSAGES_ENTREE.get(
                        ev["reponse"], "Impossible d'entrer dans cette partie."))
                    return
                if self.steam.lire_info(self.salon, "jeu") != module_steam.NOM_DU_JEU:
                    self._retour_accueil("Ce code ne correspond a aucune partie "
                                         "SickChess.")
                    return
                self._ouvrir_transport()
                return

    def _ouvrir_transport(self):
        self.transport = TransportSteam(self.steam, self.salon)
        self.etape = "salon"
        self.info = ""

    def _envoyer_reglages(self, force=False):
        maintenant = time.monotonic()
        if not force and maintenant - self._dernier_envoi_salon < 2.0:
            return
        self._dernier_envoi_salon = maintenant
        self.transport.envoyer({"type": "salon", "minutes": self.cadence[0],
                                "increment": self.cadence[1],
                                "couleur_hote": self.couleur,
                                "variante": self.variante})

    def lancer(self):
        """L'hote lance la partie."""
        if self.transport is None or not self.transport.connecte():
            return
        couleur = self.couleur
        if couleur == "hasard":
            couleur = random.choice(["blanc", "noir"])
        # Freestyle : l'hote tire la position, les deux jouent la meme.
        reglages = freestyle.reglages_de_partie({"variante": self.variante})
        message = {"type": "debut", "minutes": self.cadence[0],
                   "increment": self.cadence[1], "couleur_hote": couleur,
                   "variante": self.variante, "freestyle": reglages["freestyle"]}
        self.transport.envoyer(message)
        if self.salon:
            self.steam.fermer_salon(self.salon)
        self._terminer(message, couleur)

    def _terminer(self, message, couleur_locale):
        minutes = int(message.get("minutes", 10) or 0)
        self.resultat = (self.transport, {
            "minutes": minutes,
            "increment": int(message.get("increment", 0) or 0),
            "pendule_active": minutes > 0,
            "couleur_locale": couleur_locale,
            "variante": message.get("variante", "normal"),
            "freestyle": _numero_valide(message.get("freestyle")),
            "tournoi_fide": message.get("variante") == "tournoi",
            "joueurs_preparation": 2,
        })

    def _suivre_salon(self):
        t = self.transport
        messages = t.recevoir()
        if t.erreur:
            self._retour_accueil(t.erreur)
            return
        if t.parti:
            if t.hote:
                self.info = "%s est reparti. La partie reste ouverte." % (
                    t.nom_adverse or "Ton ami")
                # On garde le salon : un autre ami peut entrer.
                t.oublier_adversaire()
            else:
                self._retour_accueil("L'hôte a fermé la partie.")
            return
        if t.hote:
            if t.connecte():
                self._envoyer_reglages()
            return
        for index, message in enumerate(messages):
            if message.get("type") == "salon":
                self.reglages_hote = message
            elif message.get("type") == "debut":
                hote = message.get("couleur_hote")
                self._terminer(message, "noir" if hote == "blanc" else "blanc")
                t.remettre(messages[index + 1:])
                return

    # ------------------------------------------------------------ boucle

    def run(self):
        """Renvoie (transport, reglages) quand la partie commence, None pour
        revenir au menu, ou 'quitter'."""
        while self.resultat is None:
            for event in ui.evenements():
                if event.type == pygame.QUIT:
                    self._retour_accueil()
                    return "quitter"
                if self.evenement_fenetre is not None and self.evenement_fenetre(event):
                    self.screen = pygame.display.get_surface()
                    continue
                if self.handle_event(event) == "retour":
                    self._retour_accueil()
                    self.champ_code.activer(False)
                    return None
            self.update()
            self.draw()
            ui.afficher()
            self.clock.tick(60)
        self.champ_code.activer(False)
        return self.resultat

    def update(self):
        if self.etape in ("accueil", "attente_steam") or self.salon:
            self._suivre_steam()
        if self.etape == "salon" and self.transport is not None:
            self._suivre_salon()
            if self.salon and self.transport is not None and self.transport.hote:
                maintenant = time.monotonic()
                if maintenant - self._amis_le > 5.0:
                    self._amis_le = maintenant
                    self.amis = self.steam.amis()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE \
                and not self.champ_code.actif:
            return "retour" if self.etape == "accueil" else self._retour_accueil()
        if self.etape == "accueil" and self.champ_code.actif:
            action = self.champ_code.handle_event(event)
            if action == "valider":
                self.rejoindre(module_steam.salon_depuis_code(self.champ_code.contenu))
                return None
            if action == "annuler":
                self.champ_code.activer(False)
                return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5) \
                and self.zone_amis.collidepoint(event.pos):
            self.defilement_amis = max(0, self.defilement_amis
                                       + (-1 if event.button == 4 else 1))
            return None
        cle = ui.gerer_boutons(self._visibles, event)
        if cle is None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                    and self.etape == "accueil":
                self.champ_code.activer(self._rect_code.collidepoint(event.pos))
            return None
        return self._clic(cle)

    def _clic(self, cle):
        if cle == "retour":
            if self.etape == "accueil":
                return "retour"
            self._retour_accueil()
        elif cle == "creer":
            self.creer()
        elif cle == "rejoindre":
            self.rejoindre(module_steam.salon_depuis_code(self.champ_code.contenu))
        elif cle == "coller":
            self.champ_code.coller_le_presse_papiers()
            self.champ_code.activer(True)
        elif cle == "reessayer":
            self.steam.demarrer()
            self.erreur = "" if self.steam.actif else self.steam.erreur
        elif cle == "test_hote":
            self.test_local(True)
        elif cle == "test_invite":
            self.test_local(False)
        elif cle == "test_invitation":
            import invitations
            invitations.ajouter(module_steam.salon_depuis_code("TEST"), "Ami de test")
            self.info = "Invitation de test : reviens au menu pour voir le bandeau."
        elif cle == "lancer":
            self.lancer()
        elif cle == "copier":
            ui.copier(module_steam.code_depuis_salon(self.salon))
            self.info = "Code copié : envoie-le à ton ami."
        elif cle == "fenetre_steam":
            self.steam.ouvrir_fenetre_invitation(self.salon)
            self.info = ("Fenêtre Steam ouverte. Si rien ne s'affiche, "
                         "utilise la liste d'amis ci-contre.")
        elif cle.startswith("cadence:"):
            m, i = cle.split(":")[1].split("+")
            self.cadence = (int(m), int(i))
            self._envoyer_reglages(force=True)
        elif cle.startswith("couleur:"):
            self.couleur = cle.split(":")[1]
            self._envoyer_reglages(force=True)
        elif cle.startswith("variante:") or cle.startswith("facon:"):
            self.variante = cle.split(":")[1]
            if self.variante == "tournoi":
                self.cadence = (10, 5)      # cadence de poule FIDE Freestyle 2026
            self._envoyer_reglages(force=True)
        elif cle.startswith("invitation:"):
            import invitations
            salon = int(cle.split(":")[1])
            invitations.oublier(salon)
            self.rejoindre(salon)
        elif cle.startswith("inviter:"):
            ami = int(cle.split(":")[1])
            if self.steam.inviter(self.salon, ami):
                self.invites.add(ami)
                self.info = "Invitation envoyée dans la discussion Steam."
        return None

    # ------------------------------------------------------------ dessin

    def _b(self, cle, libelle, rect, actif=True, selectionne=False, taille=17):
        bouton = self._boutons.get(cle)
        if bouton is None:
            bouton = ui.Bouton(rect, libelle, cle, taille=taille)
            self._boutons[cle] = bouton
        bouton.libelle = libelle
        bouton.placer(rect)
        bouton.actif = actif
        bouton.selectionne = selectionne
        bouton.taille = taille
        self._visibles.append(bouton)
        return bouton

    def draw(self):
        ecran = self.screen
        largeur, hauteur = ecran.get_size()
        t = apparence.theme(self.config.get("theme_plateau"))
        design.degrade_vertical(ecran, ecran.get_rect(),
                                design.eclaircir(t["fond"], 0.06),
                                design.assombrir(t["fond"], 0.10))
        self._visibles = []
        ui.texte(ecran, "Jouer en ligne", largeur // 2, 26, 40, t["texte"],
                 gras=True, ancre="centre")

        if self.etape == "accueil":
            self._dessiner_accueil(t, largeur, hauteur)
        elif self.etape == "attente_steam":
            ui.texte(ecran, self.info, largeur // 2, hauteur // 2 - 20, 20,
                     t["texte"], ancre="centre", largeur_max=largeur - 40)
            points = "." * (1 + int(time.monotonic() * 2) % 3)
            ui.texte(ecran, points, largeur // 2, hauteur // 2 + 14, 24,
                     t["accent"], ancre="centre")
        else:
            self._dessiner_salon(t, largeur, hauteur)

        self._b("retour", "Retour" if self.etape == "accueil" else "Quitter le salon",
                (20, hauteur - 64, 200, 44))
        for bouton in self._visibles:
            bouton.dessiner(ecran, t, rayon=10)
        if self.etape == "accueil":
            self.champ_code.dessiner(ecran, self._rect_code, t, 18,
                                     "Code de la partie (ex. 2K7F-9QXA-31BZ)")

    def _dessiner_accueil(self, t, largeur, hauteur):
        ecran = self.screen
        colonne = min(460, largeur - 40)
        x = (largeur - colonne) // 2
        y = 100
        # 25/10 (Cowork, 24/10 : phrase coupée « ou entre... ») : les 50 px ne
        # laissaient qu'une ligne ; jusqu'à 3 lignes, toute la phrase (FR et EN).
        hauteur_phrase = ui.paragraphe(ecran, "Joue contre un ami Steam. Crée une partie et "
                                       "invite-le, ou entre le code qu'il t'a donné.",
                                       (x, y, colonne, 0), 16, t["texte_discret"],
                                       max_lignes=3)
        y += max(60, hauteur_phrase + 12)
        actif = self.steam.actif
        self._b("creer", "Créer une partie", (x, y, colonne, 54), actif, taille=20)
        y += 80
        self._rect_code = pygame.Rect(x, y, colonne - 110, 46)
        self._b("coller", "Coller", (x + colonne - 100, y, 100, 46), actif, taille=15)
        y += 56
        self._b("rejoindre", "Rejoindre avec ce code", (x, y, colonne, 46),
                actif and bool(self.champ_code.contenu.strip()))
        y += 66
        y = self._dessiner_invitations(t, x, y, colonne)

        if not actif:
            message = self.steam.erreur or "Steam n'est pas disponible."
            ui.cadre(ecran, (x, y, colonne, 96), t["panneau"], (200, 90, 80), 2, 10)
            ui.texte(ecran, message, x + 14, y + 10, 17, (240, 140, 120), gras=True,
                     largeur_max=colonne - 28, ajuster=True)
            ui.paragraphe(ecran, self.steam.conseil or "", (x + 14, y + 36,
                                                             colonne - 150, 52),
                          14, t["texte_discret"])
            self._b("reessayer", "Réessayer", (x + colonne - 128, y + 46, 114, 38),
                    taille=15)
            y += 110
        if self.erreur and self.erreur != self.steam.erreur:
            ui.texte(ecran, self.erreur, largeur // 2, y, 17, (240, 140, 120),
                     ancre="centre", largeur_max=largeur - 40, ajuster=True)
            y += 34
        elif self.info:
            ui.texte(ecran, self.info, largeur // 2, y, 16, t["accent"],
                     ancre="centre", largeur_max=largeur - 40, ajuster=True)
            y += 34

        if MODE_TEST:
            y = max(y, hauteur - 130)
            ui.texte(ecran, "Test sans Steam : deux fenêtres du jeu sur ce PC",
                     largeur // 2, y, 14, t["texte_discret"], ancre="centre")
            tiers = (colonne - 20) // 3
            self._b("test_hote", "Test : héberger", (x, y + 22, tiers, 38), taille=14)
            self._b("test_invite", "Test : rejoindre", (x + tiers + 10, y + 22, tiers, 38),
                    taille=14)
            # 24/10 (p36) : voir le bandeau d'invitation sans ami (retour au menu).
            self._b("test_invitation", "Test : invitation",
                    (x + 2 * (tiers + 10), y + 22, colonne - 2 * (tiers + 10), 38), taille=14)

    def _dessiner_invitations(self, t, x, y, colonne):
        """24/10 (p36) : les invitations recues ces 10 dernieres minutes
        (« Plus tard » sur le bandeau, ou arrivees pendant une partie)."""
        import invitations
        recues = invitations.en_attente()[:3]
        if not recues:
            return y
        ui.texte(self.screen, "INVITATIONS REÇUES", x, y, 13, t["texte_discret"], gras=True)
        y += 22
        for invitation in recues:
            rect = pygame.Rect(x, y, colonne, 46)
            ui.cadre(self.screen, rect, t["panneau"], t["bord"], 1, 10)
            l_bouton = 120
            ui.texte(self.screen, "%s t'invite" % invitation["nom"], x + 14, y + 6, 16,
                     t["texte"], gras=True, largeur_max=colonne - l_bouton - 30)
            ui.texte(self.screen, invitations.depuis_quand(invitation), x + 14, y + 26, 12,
                     t["texte_discret"], largeur_max=colonne - l_bouton - 30)
            self._b("invitation:%d" % invitation["salon"], "Rejoindre",
                    (rect.right - l_bouton - 6, y + 6, l_bouton, 34), self.steam.actif,
                    selectionne=True, taille=15)
            y += 54
        return y + 12

    def _dessiner_salon(self, t, largeur, hauteur):
        ecran = self.screen
        tr = self.transport
        hote = tr.hote
        avec_amis = hote and bool(self.salon)
        total = min(980, largeur - 40)
        x0 = (largeur - total) // 2
        gauche = total if not avec_amis else int(total * 0.52)
        y = 90

        # Etat de la connexion
        couleur_etat = t["accent"] if tr.connecte() else t["texte_discret"]
        ui.texte(ecran, tr.etat(), x0, y, 19, couleur_etat, gras=True,
                 largeur_max=gauche - 10, ajuster=True)
        y += 34

        if hote:
            ui.texte(ecran, "CADENCE", x0, y, 13, t["texte_discret"], gras=True)
            y += 22
            par_ligne = 3
            l_puce = (gauche - 10 - (par_ligne - 1) * 8) // par_ligne
            for i, (m, inc) in enumerate(CADENCES):
                rx = x0 + (i % par_ligne) * (l_puce + 8)
                ry = y + (i // par_ligne) * 46
                self._b("cadence:%d+%d" % (m, inc), libelle_cadence(m, inc),
                        (rx, ry, l_puce, 38), selectionne=(m, inc) == self.cadence,
                        taille=15)
            y += 2 * 46 + 10
            ui.texte(ecran, "TA COULEUR", x0, y, 13, t["texte_discret"], gras=True)
            y += 22
            for i, (cle, libelle) in enumerate(COULEURS):
                self._b("couleur:" + cle, libelle,
                        (x0 + i * (l_puce + 8), y, l_puce, 38),
                        selectionne=cle == self.couleur, taille=15)
            y += 58
            ui.texte(ecran, "VARIANTE", x0, y, 13, t["texte_discret"], gras=True)
            y += 22
            for i, (cle, libelle) in enumerate(VARIANTES):
                self._b("variante:" + cle, libelle,
                        (x0 + i * (l_puce + 8), y, l_puce, 38),
                        selectionne=cle == ("normal" if self.variante == "normal"
                                            else "freestyle"), taille=15)
            if self.variante != "normal":
                for i, (cle, libelle) in enumerate(FACONS_960):
                    self._b("facon:" + cle, libelle,
                            (x0 + i * (l_puce + 8), y + 46, l_puce, 38),
                            selectionne=cle == self.variante, taille=15)
                y += 46
            y += 58
            self._b("lancer", "Lancer la partie" if tr.connecte()
                    else "En attente de ton ami...",
                    (x0, y, gauche - 10, 54), tr.connecte(), taille=20)
            y += 70
            if self.salon:
                code = module_steam.code_depuis_salon(self.salon)
                ui.texte(ecran, "Code à donner :", x0, y + 12, 15, t["texte_discret"])
                ui.texte(ecran, code, x0 + 130, y + 8, 22, t["texte"], gras=True,
                         mono=True)
                self._b("copier", "Copier", (x0 + gauche - 110, y, 100, 40), taille=15)
            else:
                ui.texte(ecran, "Mode test : lance une 2e fenêtre et clique "
                         "\"Test : rejoindre\".", x0, y + 10, 15,
                         t["texte_discret"], largeur_max=gauche - 10, ajuster=True)
        else:
            r = self.reglages_hote
            if r is None:
                ui.texte(ecran, "On attend les réglages de l'hôte...", x0, y, 17,
                         t["texte_discret"])
            else:
                couleur = {"blanc": "Noirs", "noir": "Blancs"}.get(
                    r.get("couleur_hote"), "tiree au hasard")
                lignes = ["Cadence : %s" % libelle_cadence(int(r.get("minutes", 0)),
                                                          int(r.get("increment", 0))),
                          "Ta couleur : %s" % couleur,
                          "Variante : %s" % NOMS_VARIANTES.get(r.get("variante"), "Normal"),
                          "",
                          "%s va lancer la partie." % (tr.nom_adverse or "L'hôte")]
                for ligne in lignes:
                    ui.texte(ecran, ligne, x0, y, 19, t["texte"],
                             largeur_max=total - 10)
                    y += 32

        if self.info:
            ui.texte(ecran, self.info, largeur // 2, hauteur - 108, 15,
                     t["texte_discret"], ancre="centre", largeur_max=largeur - 40,
                     ajuster=True)

        if avec_amis:
            self._dessiner_amis(t, x0 + gauche + 10, 90, total - gauche - 10,
                                hauteur - 90 - 130)

    def _dessiner_amis(self, t, x, y, largeur, hauteur):
        ecran = self.screen
        self._b("fenetre_steam", "Inviter avec Steam (Maj+Tab)", (x, y, largeur, 40),
                taille=15)
        y += 52
        ui.texte(ecran, "TES AMIS STEAM", x, y, 13, t["texte_discret"], gras=True)
        y += 22
        self.zone_amis = pygame.Rect(x, y, largeur, max(0, hauteur - 74))
        ui.cadre(ecran, self.zone_amis, t["panneau"], t.get("bord"), 1, 10)
        if not self.amis:
            ui.texte(ecran, "Aucun ami trouve.", x + 12, y + 12, 15,
                     t["texte_discret"])
            return
        ligne = 44
        visibles = max(1, (self.zone_amis.height - 8) // ligne)
        self.defilement_amis = min(self.defilement_amis,
                                   max(0, len(self.amis) - visibles))
        for i, ami in enumerate(self.amis[self.defilement_amis:
                                          self.defilement_amis + visibles]):
            ry = y + 4 + i * ligne
            pastille = (110, 200, 120) if ami["sur_sickchess"] else \
                (120, 170, 220) if ami["en_ligne"] else (110, 110, 110)
            pygame.draw.circle(ecran, pastille, (x + 16, ry + ligne // 2), 5)
            ui.texte(ecran, ami["nom"], x + 30, ry + 12, 16,
                     t["texte"] if ami["en_ligne"] else t["texte_discret"],
                     largeur_max=largeur - 150)
            deja = ami["id"] in self.invites
            self._b("inviter:%d" % ami["id"], "Invite" if deja else "Inviter",
                    (x + largeur - 112, ry + 5, 100, ligne - 10), not deja, taille=14)
