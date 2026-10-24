# layout.py - V7.1 : disposition de l'ecran de jeu
#
# CE QUI CHANGE PAR RAPPORT A LA V7 :
#   Les hauteurs des zones du panneau etaient ecrites en dur (58, 70, 46, 214,
#   218...). Sur une fenetre courte elles se chevauchaient, sur une grande il
#   restait un trou. Tout est maintenant reparti proportionnellement, avec des
#   bornes : chaque zone recoit une hauteur minimum, la liste des coups prend ce
#   qui reste, et rien ne peut plus mordre sur la zone voisine.
#
#   La taille par defaut de la fenetre est 1024x640.
#
# AUCUNE FONCTION SUPPRIMEE : recalculer, rect_plateau, rect_panneau et
# dans_le_plateau existent toujours, avec les memes noms d'attributs.

import board_geometry as geo

MARGE = 18
PANNEAU_MIN = 290
PANNEAU_MAX = 430
LARGEUR_MINI = 900
HAUTEUR_MINI = 560
# 24/10 (p33) : au-dela de 1,65 (plus grand qu'environ 1700x1050 : 1440p, 4K),
# tout grandit encore, proportionnellement. En dessous, rien ne change.
ECHELLE_NORMALE_MAX = 1.65
ECHELLE_MAX = 3.4


def _borne(valeur, mini, maxi):
    return max(mini, min(maxi, int(valeur)))


class Disposition:
    """Calcule les zones de l'ecran de jeu pour une taille de fenetre donnee."""

    def __init__(self, largeur=1024, hauteur=640):
        self.recalculer(largeur, hauteur)

    def recalculer(self, largeur, hauteur):
        self.largeur = max(LARGEUR_MINI, int(largeur))
        self.hauteur = max(HAUTEUR_MINI, int(hauteur))
        self.echelle = max(0.86, min(ECHELLE_MAX, min(self.largeur / 1024.0,
                                                      self.hauteur / 640.0)))
        # Grand ecran : les bornes en pixels grandissent avec l'echelle.
        self.grand = max(1.0, self.echelle / ECHELLE_NORMALE_MAX)
        g, marge = self.grand, int(MARGE * self.grand)

        # 24/10 (defaut Cowork) : un nombre a virgule ici rendait plateau_x et
        # panneau_x a virgule, et le numero de case de l'editeur aussi (plantage
        # en plein ecran). Toujours des pixels entiers.
        largeur_panneau = int(_borne(self.largeur * 0.32, PANNEAU_MIN * g, PANNEAU_MAX * g))

        hauteur_dispo = self.hauteur - 2 * marge
        largeur_dispo = self.largeur - largeur_panneau - 3 * marge
        cote = max(240, min(hauteur_dispo, largeur_dispo))

        self.taille_case = int(cote // 8)
        self.cote_plateau = self.taille_case * 8
        self.plateau_x = marge + (largeur_dispo - self.cote_plateau) // 2
        self.plateau_y = marge + (hauteur_dispo - self.cote_plateau) // 2

        self.panneau_x = self.largeur - largeur_panneau - marge
        self.panneau_y = marge
        self.panneau_l = largeur_panneau
        self.panneau_h = hauteur_dispo

        self._repartir_le_panneau()

        # On previent la geometrie du plateau : tout le reste du jeu en depend.
        geo.configurer(self.plateau_x, self.plateau_y, self.taille_case)
        return self

    # ------------------------------------------------------------------ panneau

    def _repartir_le_panneau(self):
        """Empile les zones du panneau de haut en bas, sans chevauchement.

        Les horloges, les prises et les boutons prennent une hauteur bornee ;
        la liste des coups (ou le chat) recoit tout le reste.
        """
        ech, g = self.echelle, self.grand
        marge = int(14 * ech)
        x = self.panneau_x + marge
        interieur = self.panneau_l - 2 * marge

        h_horloge = _borne(56 * ech, 44, 74 * g)
        h_captures = _borne(40 * ech, 30, 56 * g)
        h_infos = _borne(44 * ech, 34, 60 * g)
        h_boutons = _borne(44 * ech, 36, 58 * g)
        espace = _borne(8 * ech, 6, 14 * g)

        fixes = 2 * h_horloge + 2 * h_captures + h_infos + h_boutons + 7 * espace
        reste = self.panneau_h - fixes - 2 * espace

        # Si la fenetre est vraiment courte, on rogne les zones secondaires
        # AVANT de laisser quoi que ce soit deborder.
        if reste < 90:
            manque = 90 - reste
            retrait = min(manque, (h_captures - 24) * 2)
            h_captures -= int(retrait // 2)
            reste += retrait
        if reste < 70:
            manque = 70 - reste
            retrait = min(manque, h_infos - 26)
            h_infos -= int(retrait)
            reste += retrait
        reste = max(60, reste)

        y = self.panneau_y + espace
        self.horloge_haut = (x, y, interieur, h_horloge); y += h_horloge + espace
        self.captures_haut = (x, y, interieur, h_captures); y += h_captures + espace
        self.infos = (x, y, interieur, h_infos); y += h_infos + espace
        self.coups = (x, y, interieur, reste); y += reste + espace
        self.captures_bas = (x, y, interieur, h_captures); y += h_captures + espace
        self.horloge_bas = (x, y, interieur, h_horloge); y += h_horloge + espace
        self.boutons = (x, y, interieur, h_boutons)

        # Filet de securite : le dernier bloc ne sort jamais du panneau.
        bas_panneau = self.panneau_y + self.panneau_h - espace
        if self.boutons[1] + self.boutons[3] > bas_panneau:
            self.boutons = (x, bas_panneau - h_boutons, interieur, h_boutons)

    # ------------------------------------------------------------------ aides

    def rect_plateau(self):
        return (self.plateau_x, self.plateau_y, self.cote_plateau, self.cote_plateau)

    def rect_panneau(self):
        return (self.panneau_x, self.panneau_y, self.panneau_l, self.panneau_h)

    def zone_sous_le_plateau(self, hauteur=44):
        """Bande libre sous l'echiquier (bulles de chat, messages du mode)."""
        y = self.plateau_y + self.cote_plateau + 6
        hauteur = min(int(hauteur), max(0, self.hauteur - y - 6))
        return (self.plateau_x, y, self.cote_plateau, hauteur)

    def dans_le_plateau(self, position):
        x, y = position
        return (self.plateau_x <= x < self.plateau_x + self.cote_plateau
                and self.plateau_y <= y < self.plateau_y + self.cote_plateau)

    def __repr__(self):
        return ("Disposition(fenetre %dx%d, case %d, plateau en %d,%d)"
                % (self.largeur, self.hauteur, self.taille_case,
                   self.plateau_x, self.plateau_y))
