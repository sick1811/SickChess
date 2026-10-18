# menu_pause.py - SickChess 17/10 (travail p10, demande de Julien).
#
# Touche Echap pendant une partie (quand rien n'est selectionne) : la partie
# se met en pause par-dessus l'echiquier.
#   Reprendre - Options - Proposer la nulle - Abandonner - Retour au menu
# Contre l'ordinateur et a deux, la pendule s'arrete pendant la pause.
# La nulle :
#   - a deux : acceptee tout de suite (les deux joueurs sont devant l'ecran) ;
#   - contre l'ordinateur : il accepte si la partie est equilibree (ou s'il est
#     moins bien) apres le 15e coup, sinon il refuse et on le dit.

import chess
import pygame

import apparence
import ui

ACTIONS = [("reprendre", "Reprendre"), ("options", "Options"),
           ("nulle", "Proposer la nulle"), ("abandon", "Abandonner"),
           ("menu", "Retour au menu")]

COUP_MINIMUM_NULLE = 15        # avant, l'ordinateur refuse toujours
SEUIL_NULLE = 0.5              # en pions, du point de vue de l'ordinateur


def valeur_materiel(board, couleur):
    valeurs = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5,
               chess.QUEEN: 9}
    return sum(v * len(board.pieces(p, couleur)) for p, v in valeurs.items())


def ordinateur_accepte_la_nulle(board, couleur_ordinateur, evaluation_blancs=None):
    """(accepte, raison). evaluation_blancs : en pions, du point de vue des
    Blancs (analyse en direct) ; sinon on compte le materiel."""
    if board.fullmove_number < COUP_MINIMUM_NULLE:
        return False, "L'ordinateur refuse : il est trop tôt pour une nulle."
    if evaluation_blancs is None:
        evaluation_blancs = (valeur_materiel(board, chess.WHITE)
                             - valeur_materiel(board, chess.BLACK))
    pour_lui = evaluation_blancs if couleur_ordinateur == chess.WHITE else -evaluation_blancs
    if pour_lui <= SEUIL_NULLE:
        return True, "L'ordinateur accepte la nulle."
    return False, "L'ordinateur refuse : il pense être mieux."


class MenuPause:
    def __init__(self, screen, theme_plateau=None, nulle_possible=True):
        self.screen = screen
        self.theme_plateau = theme_plateau
        self.ouvert = False
        self.message = ""
        self.confirmer_abandon = False
        self.boutons = [ui.Bouton((0, 0, 10, 10), libelle, cle, taille=20)
                        for cle, libelle in ACTIONS]
        self.bouton("nulle").actif = nulle_possible

    def bouton(self, cle):
        return next(b for b in self.boutons if b.cle == cle)

    def ouvrir(self):
        self.ouvert = True
        self.message = ""
        self.confirmer_abandon = False
        self.bouton("abandon").libelle = "Abandonner"

    def fermer(self):
        self.ouvert = False

    def _placer(self):
        ech = ui.echelle(self.screen)
        largeur = int(340 * ech)
        hauteur = int(52 * ech)
        ecart = int(12 * ech)
        total = len(self.boutons) * hauteur + (len(self.boutons) - 1) * ecart
        x = (self.screen.get_width() - largeur) // 2
        y = (self.screen.get_height() - total) // 2 + int(20 * ech)
        for b in self.boutons:
            b.taille = ui.t(19, ech)
            b.placer((x, y, largeur, hauteur))
            y += hauteur + ecart
        return ech

    def handle_event(self, event):
        """Renvoie 'reprendre', 'options', 'nulle', 'abandon', 'menu' ou None."""
        if not self.ouvert:
            return None
        self._placer()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "reprendre"
        cle = ui.gerer_boutons(self.boutons, event)
        if cle == "abandon" and not self.confirmer_abandon:
            self.confirmer_abandon = True
            self.bouton("abandon").libelle = "Sûr ? Clique encore"
            return None
        return cle

    def draw(self):
        if not self.ouvert:
            return
        ech = self._placer()
        t = apparence.theme(self.theme_plateau)
        ui.voile(self.screen, opacite=190)
        premier = self.boutons[0].rect
        dernier = self.boutons[-1].rect
        cadre = pygame.Rect(premier.x - int(28 * ech), premier.y - int(90 * ech),
                            premier.width + int(56 * ech),
                            dernier.bottom - premier.y + int(90 * ech) + int(60 * ech))
        ui.cadre(self.screen, cadre, t["panneau"], t["bord"], 1, 16, ombre=True)
        ui.texte(self.screen, "Pause", cadre.centerx, cadre.y + int(22 * ech),
                 ui.t(30, ech), t["texte"], gras=True, ancre="centre")
        ui.texte(self.screen, "La pendule est arrêtée", cadre.centerx,
                 cadre.y + int(60 * ech), ui.t(13, ech), t["texte_discret"],
                 ancre="centre")
        for b in self.boutons:
            b.dessiner(self.screen, t)
        texte = self.message or "Échap : reprendre la partie"
        couleur = t["accent"] if self.message else t["texte_discret"]
        ui.texte(self.screen, texte, cadre.centerx, dernier.bottom + int(20 * ech),
                 ui.t(14, ech), couleur, ancre="centre",
                 largeur_max=cadre.width - int(20 * ech), ajuster=True)
