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
# 25/10 (petites fenetres, demande de Julien) : LE calcul commun des ecrans
# avec echiquier (partie, revue, analyse libre, problemes, revoir) :
#   - une seule echelle : celle des textes (ui.echelle, donc avec le reglage
#     « Taille des textes »), reduite si le panneau ne tient pas ;
#   - deux dispositions : « cote » (panneau a droite) et « hauteur » (fenetre
#     plus haute que large : panneau SOUS l'echiquier) ;
#   - l'echiquier et le panneau sont centres ensemble (plus de grand vide entre
#     les deux en 1920x1080).
#
# 31/10 (menage) : dans_le_plateau, jamais appelee, est retiree.

import board_geometry as geo
import mise_en_page as mep
import ui

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

    # Hauteur minimum du panneau quand il passe sous l'echiquier (a l'echelle 1).
    # La revue et l'analyse libre, plus chargees, demandent davantage.
    PANNEAU_HAUTEUR_MIN = 520

    def __init__(self, largeur=1024, hauteur=640):
        self.recalculer(largeur, hauteur)

    def reserve_gauche(self):
        """Pixels a garder a gauche de l'echiquier (la barre d'avantage de la revue)."""
        return 0

    def recalculer(self, largeur, hauteur):
        self.largeur = max(LARGEUR_MINI, int(largeur))
        self.hauteur = max(HAUTEUR_MINI, int(hauteur))
        brute = max(0.86, min(ECHELLE_MAX, min(self.largeur / 1024.0,
                                               self.hauteur / 640.0)))
        # Grand ecran : les bornes en pixels grandissent avec l'echelle.
        self.grand = max(1.0, brute / ECHELLE_NORMALE_MAX)
        self.echelle = ui.echelle((self.largeur, self.hauteur))
        g, marge = self.grand, int(MARGE * self.grand)
        self.echelle_fenetre = brute
        reserve = int(self.reserve_gauche())

        # 24/10 (plantage trouve par Cowork en 1920x1080) : des pixels entiers,
        # sinon plateau_x etait 211.0 et les cases calculees au clic des flottants.
        largeur_panneau = int(_borne(self.largeur * 0.32, PANNEAU_MIN * g, PANNEAU_MAX * g))

        # Les deux dispositions possibles : on garde celle qui donne le plus
        # grand echiquier (l'echiquier passe toujours en premier).
        cote_a_droite = min(self.hauteur - 2 * marge,
                            self.largeur - largeur_panneau - 3 * marge - reserve)
        h_panneau_min = int(self.PANNEAU_HAUTEUR_MIN * min(brute, ECHELLE_NORMALE_MAX) * g)
        cote_dessous = min(self.largeur - 2 * marge - reserve,
                           self.hauteur - h_panneau_min - 3 * marge)
        self.mode = "hauteur" if cote_dessous > cote_a_droite * 1.05 else "cote"

        if self.mode == "cote":
            cote = max(240, cote_a_droite)
            self.taille_case = int(cote // 8)
            self.cote_plateau = self.taille_case * 8
            # La place en trop va d'abord au panneau (jusqu'a sa largeur
            # maximum), puis l'ensemble est centre.
            libre = self.largeur - 3 * marge - reserve - self.cote_plateau - largeur_panneau
            plus = max(0, min(libre, int(PANNEAU_MAX * g) - largeur_panneau))
            largeur_panneau += plus
            libre -= plus
            self.plateau_x = marge + max(0, libre) // 2 + reserve
            self.plateau_y = marge + (self.hauteur - 2 * marge - self.cote_plateau) // 2
            self.panneau_x = self.plateau_x + self.cote_plateau + marge
            self.panneau_y = marge
            self.panneau_l = largeur_panneau
            self.panneau_h = self.hauteur - 2 * marge
        else:
            cote = max(240, cote_dessous)
            self.taille_case = int(cote // 8)
            self.cote_plateau = self.taille_case * 8
            groupe = reserve + self.cote_plateau
            self.plateau_x = (self.largeur - groupe) // 2 + reserve
            self.plateau_y = marge
            self.panneau_x = self.plateau_x - reserve
            self.panneau_y = self.plateau_y + self.cote_plateau + marge
            self.panneau_l = groupe
            self.panneau_h = self.hauteur - self.panneau_y - marge

        self._repartir_le_panneau()

        # On previent la geometrie du plateau : tout le reste du jeu en depend.
        geo.configurer(self.plateau_x, self.plateau_y, self.taille_case)
        return self

    # ------------------------------------------------------------------ panneau

    def _hauteurs(self, ech):
        g = self.grand
        return {"horloge": _borne(56 * ech, 44, 74 * g),
                "captures": _borne(40 * ech, 30, 56 * g),
                "infos": _borne(44 * ech, 34, 60 * g),
                "boutons": _borne(44 * ech, 36, 58 * g),
                "espace": _borne(8 * ech, 6, 14 * g)}

    def _besoin_du_panneau(self, ech):
        h = self._hauteurs(ech)
        return (2 * h["horloge"] + 2 * h["captures"] + h["infos"] + h["boutons"]
                + 9 * h["espace"] + int(90 * ech))

    def _repartir_le_panneau(self):
        """Empile les zones du panneau de haut en bas, sans chevauchement.

        Les horloges, les prises et les boutons prennent une hauteur bornee ;
        la liste des coups (ou le chat) recoit tout le reste.
        """
        # 25/10 : si le panneau ne tient pas (petite fenetre, grands textes),
        # c'est l'echelle qui baisse, pas les zones qui se chevauchent.
        self.echelle = mep.echelle_qui_tient(self._besoin_du_panneau, self.panneau_h,
                                             self.echelle, mini=0.75)
        ech = self.echelle
        marge = int(14 * ech)
        x = self.panneau_x + marge
        interieur = self.panneau_l - 2 * marge

        h = self._hauteurs(ech)
        h_horloge, h_captures, h_infos = h["horloge"], h["captures"], h["infos"]
        h_boutons, espace = h["boutons"], h["espace"]

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
        bas = self.panneau_y - 6 if self.mode == "hauteur" else self.hauteur - 6
        hauteur = min(int(hauteur), max(0, bas - y))
        return (self.plateau_x, y, self.cote_plateau, hauteur)

    def __repr__(self):
        return ("Disposition(fenetre %dx%d, case %d, plateau en %d,%d, %s)"
                % (self.largeur, self.hauteur, self.taille_case,
                   self.plateau_x, self.plateau_y, self.mode))
