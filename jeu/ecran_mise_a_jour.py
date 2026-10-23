# ecran_mise_a_jour.py - SickChess : l'ecran du bouton "Mise a jour".
#
#   Verification...  ->  "Tu as la derniere version"           [Menu]
#                    ->  "Version 0.3.0 (n°8) disponible"       [Installer] [Plus tard]
#                         notes de version, taille a telecharger
#   Telechargement   ->  barre de progression                   [Annuler]
#   Pret             ->  "SickChess va redemarrer"              [Redemarrer]
#
# La logique (reseau, fichiers) est dans mise_a_jour.py : cet ecran ne fait
# que l'afficher et transmettre les clics.

import pygame

import apparence
import design
import mise_a_jour
import ui


class EcranMiseAJour:
    def __init__(self, screen, maj=None, config=None):
        self.screen = screen
        self.config = config or {}
        self.maj = maj or mise_a_jour.MiseAJour()
        if self.maj.etat in ("rien", "erreur", "annule", "a_jour"):
            self.maj.verifier()
        self._boutons = {}
        self._visibles = []

    # ------------------------------------------------------------ boucle

    def run(self, clock, evenement_fenetre=None):
        """Renvoie 'menu', 'redemarrer' ou 'quitter'."""
        while True:
            for event in ui.evenements():
                if event.type == pygame.QUIT:
                    if self.maj.etat == "telechargement":
                        self.maj.annuler()
                    return "quitter"
                if evenement_fenetre is not None and evenement_fenetre(event):
                    self.screen = pygame.display.get_surface()
                    continue
                action = self.handle_event(event)
                if action:
                    return action
            self.draw()
            ui.afficher()
            clock.tick(30)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.maj.etat == "telechargement":
                self.maj.annuler()
                return None
            return "menu"
        cle = ui.gerer_boutons(self._visibles, event)
        if cle == "menu":
            if self.maj.etat == "telechargement":
                self.maj.annuler()
                return None
            return "menu"
        if cle == "installer":
            self.maj.telecharger()
        elif cle == "reessayer":
            self.maj.verifier()
        elif cle == "redemarrer":
            if self.maj.lancer_installation():
                return "redemarrer"
        return None

    # ------------------------------------------------------------ dessin

    def _b(self, cle, libelle, rect, actif=True, selectionne=False):
        bouton = self._boutons.get(cle) or ui.Bouton(rect, libelle, cle, taille=19)
        self._boutons[cle] = bouton
        bouton.libelle = libelle
        bouton.placer(rect)
        bouton.actif = actif
        bouton.selectionne = selectionne
        self._visibles.append(bouton)

    def draw(self):
        ecran = self.screen
        largeur, hauteur = ecran.get_size()
        t = apparence.theme(self.config.get("theme_plateau"))
        design.degrade_vertical(ecran, ecran.get_rect(),
                                design.eclaircir(t["fond"], 0.06),
                                design.assombrir(t["fond"], 0.10))
        self._visibles = []
        ui.texte(ecran, "Mise à jour", largeur // 2, 30, 40, t["texte"], gras=True,
                 ancre="centre")

        carte = pygame.Rect(0, 0, min(620, largeur - 40), min(420, hauteur - 150))
        carte.center = (largeur // 2, hauteur // 2 + 20)
        ui.cadre(ecran, carte, t["panneau"], t.get("bord"), 2, 16, ombre=True)
        x, y, l = carte.x + 28, carte.y + 24, carte.width - 56
        m = self.maj
        etat = m.etat

        ui.texte(ecran, "Version installée : %s" % m.version_installee(), x, y, 16,
                 t["texte_discret"], largeur_max=l)
        y += 40
        bas = carte.bottom - 74
        demi = (l - 16) // 2

        if etat == "verification" or etat == "rien":
            self._titre("Recherche d'une nouvelle version…", x, y, l, t)
            self._points(carte.centerx, y + 60, t)
            self._b("menu", "Retour", (x, bas, l, 50))

        elif etat == "a_jour":
            self._titre("Tu as la dernière version.", x, y, l, t)
            ui.paragraphe(ecran, "Rien à télécharger. Reviens quand Julien annonce "
                          "une nouvelle version.", (x, y + 46, l, 60), 16,
                          t["texte_discret"])
            self._b("menu", "Retour au menu", (x, bas, l, 50))

        elif etat == "disponible":
            self._titre("Nouvelle version : %s" % m.version_disponible(), x, y, l, t,
                        t["accent"])
            y += 42
            noms = ", ".join(mise_a_jour.NOMS_LISIBLES.get(n, n) for n in m.a_telecharger)
            ui.paragraphe(ecran, "À télécharger : %s  –  %s"
                          % (mise_a_jour.taille_lisible(m.octets_total), noms),
                          (x, y, l, 44), 15, t["texte_discret"])
            y += 50
            notes = m.notes()
            if notes:
                ui.texte(ecran, "CE QUI CHANGE", x, y, 13, t["texte_discret"], gras=True)
                y += 22
                for note in notes:
                    if y > bas - 30:
                        break
                    y += ui.paragraphe(ecran, "-  " + note, (x, y, l, bas - 12 - y), 15,
                                       t["texte"], max_lignes=2) + 2
            self._b("installer", "Installer", (x, bas, demi, 50), selectionne=True)
            self._b("menu", "Plus tard", (x + demi + 16, bas, demi, 50))

        elif etat == "telechargement":
            self._titre("Téléchargement : %s" % m.paquet_en_cours, x, y, l, t)
            y += 56
            barre = pygame.Rect(x, y, l, 26)
            ui.cadre(ecran, barre, t["fond"], t.get("bord"), 1, 13, plat=True)
            plein = barre.inflate(-6, -6)
            plein.width = int(plein.width * m.progression())
            if plein.width > 0:
                pygame.draw.rect(ecran, t["accent"], plein, border_radius=10)
            ui.texte(ecran, "%d %%  –  %s sur %s" % (
                int(m.progression() * 100), mise_a_jour.taille_lisible(m.octets_recus),
                mise_a_jour.taille_lisible(m.octets_total)),
                carte.centerx, y + 40, 16, t["texte_discret"], ancre="centre")
            self._b("menu", "Annuler", (x, bas, l, 50))

        elif etat == "pret":
            self._titre("Mise à jour prête.", x, y, l, t, t["accent"])
            ui.paragraphe(ecran, "SickChess va se fermer, installer la nouvelle "
                          "version (quelques secondes) puis se relancer tout seul. "
                          "Tes parties, ton profil et tes réglages sont gardés.",
                          (x, y + 46, l, 90), 16, t["texte"])
            self._b("redemarrer", "Redémarrer maintenant", (x, bas, l, 50),
                    selectionne=True)

        else:                                   # erreur / annule
            titre = "Téléchargement annulé." if etat == "annule" else "Oups."
            self._titre(titre, x, y, l, t)
            if m.erreur:
                ui.paragraphe(ecran, m.erreur, (x, y + 46, l, 110), 16, (240, 150, 130))
            self._b("reessayer", "Réessayer", (x, bas, demi, 50),
                    actif=m.geree())
            self._b("menu", "Retour au menu", (x + demi + 16, bas, demi, 50))

        for bouton in self._visibles:
            bouton.dessiner(ecran, t, rayon=12)

    def _titre(self, texte, x, y, largeur, t, couleur=None):
        ui.texte(self.screen, texte, x, y, 24, couleur or t["texte"], gras=True,
                 largeur_max=largeur, ajuster=True)

    def _points(self, cx, y, t):
        n = 1 + (pygame.time.get_ticks() // 400) % 3
        ui.texte(self.screen, "." * n, cx, y, 30, t["accent"], ancre="centre")
