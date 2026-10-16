# menu_principal.py - SickChess : le menu d'accueil.
#
# Cinq entrees claires, comme prevu dans le plan Steam :
#   Jouer contre l'ordinateur / Jouer a deux / Problemes / Mes parties / Options
# Les fonctions pas encore integrees dans SickChess sont affichees grisees avec
# la mention "bientot" : elles reviendront une par une depuis V8_TURBO_3000.

import pygame

import apparence
import design
import ui

ENTREES = [
    # (cle, libelle, disponible)
    ("stockfish", "Jouer contre l'ordinateur", True),
    ("hotseat", "Jouer a deux sur ce PC", True),
    ("puzzles", "Problemes  (bientot)", False),
    ("historique", "Mes parties  (bientot)", False),
    ("options", "Options  (bientot)", False),
    ("quitter", "Quitter", True),
]


class MainMenu:
    def __init__(self, screen, version=""):
        self.screen = screen
        self.version = version
        self.boutons = [ui.Bouton((0, 0, 10, 10), libelle, cle, taille=19,
                                  actif=dispo)
                        for cle, libelle, dispo in ENTREES]
        self.redimensionner(*screen.get_size())

    def redimensionner(self, largeur, hauteur):
        largeur_bouton = min(420, largeur - 80)
        hauteur_bouton = 50
        ecart = 12
        total = len(self.boutons) * (hauteur_bouton + ecart) - ecart
        y = max(int(hauteur * 0.36), (hauteur - total) // 2 + 60)
        x = (largeur - largeur_bouton) // 2
        for bouton in self.boutons:
            bouton.placer((x, y, largeur_bouton, hauteur_bouton))
            y += hauteur_bouton + ecart

    def handle_event(self, event):
        """Renvoie la cle de l'entree choisie, ou None."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quitter"
        return ui.gerer_boutons(self.boutons, event)

    def draw(self):
        ecran = self.screen
        largeur, hauteur = ecran.get_size()
        t = apparence.theme()
        design.degrade_vertical(ecran, ecran.get_rect(),
                                design.eclaircir(t["fond"], 0.06),
                                design.assombrir(t["fond"], 0.10))

        # Titre
        taille_titre = max(48, min(84, hauteur // 8))
        y_titre = int(hauteur * 0.10)
        ui.texte(ecran, "SickChess", largeur // 2, y_titre, taille_titre,
                 t["texte"], gras=True, ancre="centre")
        ui.texte(ecran, "Les echecs, simplement.", largeur // 2,
                 y_titre + taille_titre + 10, 18, t["texte_discret"],
                 ancre="centre")

        for bouton in self.boutons:
            bouton.dessiner(ecran, t, rayon=12)

        if self.version:
            ui.texte(ecran, "version %s" % self.version, largeur - 14,
                     hauteur - 26, 13, t["texte_discret"], ancre="droite")
