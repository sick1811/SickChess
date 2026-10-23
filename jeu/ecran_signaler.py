# ecran_signaler.py - SickChess 17/10 (travail p16) : l'ecran « Signaler un
# problème / Proposer une idée ». Le travail (rapport, envoi) est dans
# signalement.py ; ici, seulement la saisie et l'affichage.

import threading

import pygame

import apparence
import signalement
import ui

VERT = (120, 200, 130)
ROUGE = (232, 118, 108)


class EcranSignaler:
    def __init__(self, screen, version=""):
        self.screen = screen
        self.version = version
        self.type = "probleme"
        self.champ = ui.ChampTexte(longueur_max=1500).activer(True)
        self.etat = "saisie"           # saisie -> envoi -> fini
        self.message = ""
        self.couleur = None
        self.chemin = None
        self._fil = None
        self._resultat = None
        self.btn_probleme = ui.Bouton((0, 0, 10, 10), "Un problème", "probleme", taille=17)
        self.btn_idee = ui.Bouton((0, 0, 10, 10), "Une idée", "idee", taille=17)
        self.btn_envoyer = ui.Bouton((0, 0, 10, 10), "Envoyer", "envoyer", taille=18)
        self.btn_annuler = ui.Bouton((0, 0, 10, 10), "Annuler", "annuler", taille=18)
        self.btn_coller = ui.Bouton((0, 0, 10, 10), "Coller", "coller", taille=14)
        self.boutons = [self.btn_probleme, self.btn_idee, self.btn_coller,
                        self.btn_envoyer, self.btn_annuler]
        self._placer()

    def _placer(self):
        largeur, hauteur = self.screen.get_size()
        ech = ui.echelle(self.screen)
        self.ech = ech
        l = min(int(720 * ech), largeur - 60)
        x = (largeur - l) // 2
        y = int(hauteur * 0.22)
        h = int(44 * ech)
        moitie = (l - int(10 * ech)) // 2
        self.btn_probleme.placer((x, y, moitie, h))
        self.btn_idee.placer((x + l - moitie, y, moitie, h))
        y += h + int(18 * ech)
        self.zone = pygame.Rect(x, y, l, int(hauteur * 0.36))
        y = self.zone.bottom + int(8 * ech)
        self.btn_coller.placer((x, y, int(110 * ech), int(32 * ech)))
        self.y_note = y + int(6 * ech)
        y += int(32 * ech) + int(40 * ech)
        self.btn_envoyer.placer((x, y, moitie, int(50 * ech)))
        self.btn_annuler.placer((x + l - moitie, y, moitie, int(50 * ech)))
        self.y_message = y + int(50 * ech) + int(14 * ech)
        self.colonne = (x, l)

    # --- envoi
    def envoyer(self, adresse=None, ouvrir=None):
        """Construit, range et (si une adresse est reglee) envoie le rapport."""
        texte = signalement.construire(self.type, self.champ.contenu, self.version)
        self.chemin = signalement.enregistrer(texte, self.type)
        adresse = signalement.adresse_d_envoi() if adresse is None else adresse
        if not adresse:
            ui.copier(texte)
            if self.chemin:
                signalement.ouvrir_le_dossier(self.chemin)
            self._resultat = (True, "Message enregistré dans le dossier rapports et "
                                    "copié : envoie-le à Julien (Discord ou e-mail).")
            return self._resultat
        self._resultat = signalement.envoyer(adresse, self.type, self.champ.contenu,
                                             texte, ouvrir=ouvrir)
        return self._resultat

    def _lancer_l_envoi(self):
        if not self.champ.contenu.strip():
            self.message, self.couleur = "Écris d'abord ton message.", ROUGE
            return
        self.etat = "envoi"
        self.message, self.couleur = "Envoi...", None
        self._fil = threading.Thread(target=self.envoyer, daemon=True)
        self._fil.start()

    def update(self):
        if self.etat == "envoi" and self._resultat is not None:
            ok, texte = self._resultat
            self.etat = "fini"
            self.message, self.couleur = texte, VERT if ok else ROUGE
            self.btn_annuler.libelle = "Fermer"
            self.btn_envoyer.actif = False

    # --- evenements
    def handle_event(self, event):
        """Renvoie 'retour' pour fermer l'ecran."""
        if event.type == pygame.QUIT:
            return "quitter"
        if self.etat == "saisie":
            reponse = self.champ.handle_event(event)
            if event.type == getattr(pygame, "TEXTINPUT", -1) and self.couleur == ROUGE:
                self.message = ""
            if reponse == "annuler":
                return "retour"
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            return "retour" if self.etat == "fini" else None
        cle = ui.gerer_boutons([b for b in self.boutons if b.actif], event)
        if cle in ("probleme", "idee") and self.etat == "saisie":
            self.type = cle
        elif cle == "coller" and self.etat == "saisie":
            self.champ.coller_le_presse_papiers(remplacer=False)
        elif cle == "envoyer" and self.etat == "saisie":
            self._lancer_l_envoi()
        elif cle == "annuler":
            return "retour"
        return None

    # --- dessin
    def draw(self):
        ecran, ech = self.screen, self.ech
        t = apparence.theme()
        ecran.fill(t["fond"])
        largeur = ecran.get_width()
        x, l = self.colonne
        ui.texte(ecran, "Signaler un problème ou proposer une idée", largeur // 2,
                 int(ecran.get_height() * 0.08), ui.t(30, ech), t["texte"], gras=True,
                 ancre="centre", largeur_max=largeur - 40, ajuster=True)
        ui.texte(ecran, "Ton message aide à améliorer SickChess. Merci !", largeur // 2,
                 int(ecran.get_height() * 0.08) + ui.t(40, ech), ui.t(14, ech),
                 t["texte_discret"], ancre="centre")
        self.btn_probleme.selectionne = self.type == "probleme"
        self.btn_idee.selectionne = self.type == "idee"
        souris = pygame.mouse.get_pos()
        for b in self.boutons:
            b.maj_survol(souris)
            b.dessiner(ecran, t)
        ui.cadre(ecran, self.zone, t["fond"], t["accent"] if self.etat == "saisie"
                 else t["bord"], 2, 10)
        interieur = self.zone.inflate(-int(24 * ech), -int(20 * ech))
        invite = ("Décris ce qui s'est passé : ce que tu faisais, ce que tu as vu..."
                  if self.type == "probleme" else "Ton idée pour améliorer le jeu...")
        contenu = self.champ.contenu
        if contenu:
            curseur = "|" if self.etat == "saisie" and (pygame.time.get_ticks() // 500) % 2 == 0 else ""
            ui.paragraphe(ecran, contenu + curseur, interieur, ui.t(16, ech), t["texte"])
        else:
            ui.paragraphe(ecran, invite, interieur, ui.t(16, ech), t["texte_discret"])
        note = ("Le jeu ajoute tout seul la version et la fin du journal du jeu."
                if self.type == "probleme" else "Le jeu ajoute tout seul la version.")
        ui.texte(ecran, note, self.btn_coller.rect.right + int(12 * ech), self.y_note,
                 ui.t(13, ech), t["texte_discret"],
                 largeur_max=l - self.btn_coller.rect.width - int(110 * ech))
        ui.texte(ecran, "%d / 1500" % len(contenu), x + l, self.y_note, ui.t(12, ech),
                 t["texte_discret"], ancre="droite")
        if self.message:
            ui.paragraphe(ecran, self.message, (x, self.y_message, l, ui.t(50, ech)),
                          ui.t(15, ech), self.couleur or t["texte"], gras=True)

    def run(self, clock, evenement_fenetre=None):
        try:
            cadence = ui.Cadence()       # 23/10 : 30 images/s au repos
            while True:
                evenements = ui.evenements()
                for event in evenements:
                    if evenement_fenetre is not None and evenement_fenetre(event):
                        self.screen = pygame.display.get_surface()
                        self._placer()
                        continue
                    reponse = self.handle_event(event)
                    if reponse:
                        return reponse
                self.update()
                self.draw()
                ui.afficher()
                clock.tick(cadence.suivante(evenements))
        finally:
            self.champ.activer(False)
