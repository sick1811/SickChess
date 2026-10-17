# raccourcis.py - V7 : NOUVEAU FICHIER
#
# La liste des raccourcis clavier, affichee par-dessus le jeu avec F1.
# Elle sert aussi de rappel de tout ce que le jeu sait faire.

import pygame

import apparence
import ui

RACCOURCIS = [
    ("PENDANT LA PARTIE", None),
    ("Clic gauche", "Sélectionner une pièce, puis sa case d'arrivée"),
    ("Glisser-deposer", "Déplacer une pièce directement"),
    ("Clic droit sur une pièce prise", "Annuler le déplacement en cours"),
    ("Clic droit", "Colorier une case ; en glissant, tracer une flèche"),
    ("Maj + clic droit", "Flèche rouge      Ctrl + clic droit : flèche bleue"),
    ("H", "Indice : Stockfish montre le meilleur coup"),
    ("F", "Retourner le plateau"),
    ("Échap", "Annuler la sélection ou le prémouvement"),
    ("", None),
    ("PRÉMOUVEMENT", None),
    ("Jouer pendant le tour adverse", "Le coup part dès que c'est à toi"),
    ("Clic droit", "Annuler le prémouvement préparé"),
    ("", None),
    ("PARTIE EN RESEAU", None),
    ("Tab", "Ouvrir ou fermer le chat (onglet CHAT du panneau)"),
    ("Windows + .", "Clavier d'emoji de Windows, dans le chat"),
    ("Entrée", "Envoyer le message"),
    ("", None),
    ("MENU PRINCIPAL", None),
    ("M", "Couper ou remettre la musique du menu"),
    ("Case en haut à droite", "Même chose à la souris ; le choix est retenu"),
    ("", None),
    ("FENÊTRE", None),
    ("F11", "Plein écran / fenêtre"),
    ("F1", "Afficher ou cacher cette aide"),
    ("Coin de la fenêtre", "Redimensionner : le plateau s'adapte"),
    ("", None),
    ("REPLAY (après la partie)", None),
    ("Flèches gauche / droite", "Coup par coup"),
    ("Flèches haut / bas", "Cinq coups d'un coup"),
    ("Espace", "Lecture automatique"),
    ("Debut / Fin", "Aller au premier ou au dernier coup"),
    ("F", "Retourner le plateau"),
    ("A", "Relancer ou interrompre l'analyse Stockfish"),
    ("Clic sur un coup", "Aller directement a ce coup"),
    ("Échap", "Revenir à l'écran de fin"),
]


class AideRaccourcis:
    """Panneau d'aide affiche par-dessus l'ecran de jeu."""

    def __init__(self, screen):
        self.screen = screen
        self.visible = False
        # Polices conservees pour compatibilite ; l'affichage passe par ui.py.
        self.f_titre = ui.police(26, True)
        self.f_section = ui.police(15, True)
        self.f_touche = ui.police(15, True, True)
        self.f_texte = ui.police(15)

    def basculer(self):
        self.visible = not self.visible
        return self.visible

    def handle_event(self, event):
        """Renvoie True si l'evenement a ete consomme par l'aide."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                self.basculer()
                return True
            if self.visible and event.key == pygame.K_ESCAPE:
                self.visible = False
                return True
        if self.visible and event.type == pygame.MOUSEBUTTONDOWN:
            self.visible = False
            return True
        return False

    def draw(self, screen=None, theme_cle=None):
        """V7.1 : la liste s'adapte a la fenetre.

        Avant, 26 lignes de 24 pixels a partir de y=84 : sur une fenetre de 640
        de haut, le dernier tiers de l'aide etait hors de l'ecran, et la
        description commencait a x+210 quelle que soit la largeur de colonne.
        """
        if not self.visible:
            return
        ecran = screen or self.screen
        t = apparence.theme(theme_cle)
        largeur, hauteur = ecran.get_size()
        ech = ui.echelle(ecran)

        voile = pygame.Surface((largeur, hauteur), pygame.SRCALPHA)
        voile.fill((0, 0, 0, 210))
        ecran.blit(voile, (0, 0))

        marge = int(30 * ech)
        ui.texte(ecran, "RACCOURCIS", largeur // 2, int(18 * ech), ui.t(26, ech),
                 t["accent"], gras=True, ancre="centre", largeur_max=largeur - 60)

        taille = ui.t(14, ech)
        hauteur_ligne = ui.police(taille).get_height() + int(5 * ech)
        haut = int(18 * ech) + ui.police(ui.t(26, ech), True).get_height() + int(14 * ech)
        bas = hauteur - int(16 * ech) - ui.police(ui.t(14, ech)).get_height()
        place = max(1, (bas - haut) // hauteur_ligne)

        # Autant de colonnes qu'il en faut pour que tout tienne.
        colonnes = max(1, (len(RACCOURCIS) + place - 1) // place)
        colonnes = min(colonnes, max(1, (largeur - 2 * marge) // int(320 * ech)))
        colonnes = max(1, colonnes)
        par_colonne = (len(RACCOURCIS) + colonnes - 1) // colonnes
        largeur_colonne = (largeur - 2 * marge - (colonnes - 1) * int(24 * ech)) \
            // colonnes
        largeur_touche = min(int(190 * ech), largeur_colonne // 2)

        for index, (touche, description) in enumerate(RACCOURCIS):
            colonne = index // par_colonne
            ligne = index % par_colonne
            if colonne >= colonnes or ligne >= place:
                continue
            x = marge + colonne * (largeur_colonne + int(24 * ech))
            y = haut + ligne * hauteur_ligne
            if not touche:
                continue
            if description is None:
                ui.texte(ecran, touche, x, y, taille, t["accent"], gras=True,
                         largeur_max=largeur_colonne)
                continue
            ui.texte(ecran, touche, x, y, taille, t["texte"], gras=True, mono=True,
                     largeur_max=largeur_touche - 8)
            ui.texte(ecran, description, x + largeur_touche, y, taille,
                     t["texte_discret"], largeur_max=largeur_colonne - largeur_touche)

        ui.texte(ecran, "F1 ou un clic pour fermer", largeur // 2,
                 hauteur - int(14 * ech) - ui.police(taille).get_height(),
                 taille, t["texte_discret"], ancre="centre", largeur_max=largeur - 60)
