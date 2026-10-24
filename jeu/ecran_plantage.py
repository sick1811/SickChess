# ecran_plantage.py - SickChess 24/10 (travail p29) : au lancement qui suit un
# plantage, une carte propose d'envoyer le rapport (plantage.py) avec l'ecran
# « Signaler un probleme ». Envoyer le rapport / Non merci ; Echap = plus tard.

import pygame

import apparence
import design
import ui


class EcranPlantage:
    def __init__(self, screen, plantage):
        self.screen = screen
        self.plantage = plantage
        self.btn_envoyer = ui.Bouton((0, 0, 10, 10), "Envoyer le rapport", "envoyer", taille=18)
        self.btn_envoyer.selectionne = True
        self.btn_non = ui.Bouton((0, 0, 10, 10), "Non merci", "non", taille=17)
        self.boutons = [self.btn_envoyer, self.btn_non]
        self._placer()

    def _placer(self):
        largeur, hauteur = self.screen.get_size()
        ech = self.ech = ui.echelle(self.screen)
        self.carte = pygame.Rect(0, 0, min(int(600 * ech), largeur - 40), int(300 * ech))
        self.carte.center = (largeur // 2, hauteur // 2)
        hb = int(48 * ech)
        marge = int(24 * ech)
        lb = (self.carte.width - 3 * marge) // 2
        y = self.carte.bottom - marge - hb
        self.btn_non.placer((self.carte.x + marge, y, lb, hb))
        self.btn_envoyer.placer((self.carte.right - marge - lb, y, lb, hb))

    def handle_event(self, event):
        """'envoyer', 'non', 'plus_tard' (Echap) ou 'quitter'."""
        if event.type == pygame.QUIT:
            return "quitter"
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "plus_tard"
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return "envoyer"
        return ui.gerer_boutons(self.boutons, event)

    def draw(self):
        ecran, ech = self.screen, self.ech
        t = apparence.theme()
        cle = (ecran.get_size(), t["fond"])
        if getattr(self, "_fond", (None,))[0] != cle:          # degrade calcule une fois
            fond = pygame.Surface(ecran.get_size())
            design.degrade_vertical(fond, fond.get_rect(), design.eclaircir(t["fond"], 0.06),
                                    design.assombrir(t["fond"], 0.10))
            self._fond = (cle, fond)
        ecran.blit(self._fond[1], (0, 0))
        c = self.carte
        ui.cadre(ecran, c, t["panneau"], t["accent"], 2, 16, ombre=True)
        x, l = c.x + int(24 * ech), c.width - int(48 * ech)
        y = c.y + int(22 * ech)
        ui.texte(ecran, "La dernière fois, SickChess s'est fermé à cause d'une erreur",
                 c.centerx, y, ui.t(21, ech), t["texte"], gras=True, ancre="centre",
                 largeur_max=l, ajuster=True)
        y += ui.police(ui.t(21, ech), True).get_height() + int(14 * ech)
        ui.paragraphe(ecran, "Le %s (version %s). Envoie le rapport à Julien : il saura ce qui a "
                             "cassé et pourra le réparer. Tu verras le message avant de "
                             "l'envoyer ; rien ne part sans ton accord."
                      % (self.plantage.get("date", "?"), self.plantage.get("version", "?")),
                      pygame.Rect(x, y, l, int(80 * ech)), ui.t(15, ech), t["texte_discret"])
        y += int(84 * ech)
        ui.texte(ecran, self.plantage.get("erreur", ""), x, y, ui.t(13, ech), t["texte_faible"]
                 if "texte_faible" in t else t["texte_discret"], mono=True, largeur_max=l)
        souris = pygame.mouse.get_pos()
        for bouton in self.boutons:
            bouton.maj_survol(souris)
            bouton.dessiner(ecran, t, rayon=10)

    def run(self, clock, evenement_fenetre=None):
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
            self.draw()
            ui.afficher()
            clock.tick(30)
