# fond_anime.py - V7.2 : NOUVEAU FICHIER
#
# LA POUSSIERE DOREE DE FOND (ta demande : "tu vois les particules dans le menu ?
# fais un truc stylé dans ce genre mais sur toute la fenetre").
#
# Les particules du menu (particle_system.py) sortent d'UN point, au-dessus d'un
# bouton : c'est un feu. Ici c'est autre chose - une poussiere doree qui flotte
# dans TOUTE la fenetre, derriere le contenu, en permanence.
#
# particle_system.py n'est pas supprime et n'est pas modifie : il continue de
# faire son feu. Les deux peuvent tourner ensemble.
#
# CE QUI COMPTE POUR QUE CA NE RAME PAS :
#
#   - Un nombre FIXE de grains. Ils ne naissent ni ne meurent : quand un grain
#     sort d'un cote, il rentre par l'autre. Aucune allocation pendant le jeu,
#     contrairement au systeme de feu qui cree et detruit sans arret.
#   - Les ronds flous sont dessines UNE FOIS au demarrage, dans quelques tailles,
#     puis recopies. Dessiner un cercle avec transparence a chaque image pour
#     chaque grain, c'est ce qui coute cher.
#   - L'animation suit le TEMPS, pas les images : a 30 ou a 120 images par
#     seconde, la poussiere derive a la meme vitesse.
#   - Rien n'est dessine par-dessus le contenu : on appelle dessiner() en
#     PREMIER, juste apres avoir efface l'ecran.
#
# Elle ne tourne QUE dans les menus (ton choix) : jamais par-dessus l'echiquier
# pendant une partie, ou elle generait la lecture des pieces.

import math
import random

import pygame

# Combien de grains pour une fenetre de 1024x640. On en met proportionnellement
# autant sur une grande fenetre, sans jamais depasser le plafond.
DENSITE = 90
PLAFOND = 220
TAILLES = (1, 2, 3, 4)          # rayons, en pixels a l'echelle 1
BORDURE_FONDU = 26              # sur cette bande, les grains s'eteignent


class Grain:
    """Un grain de poussiere. Il ne meurt jamais : il fait le tour."""

    __slots__ = ("x", "y", "vx", "vy", "taille", "phase", "vitesse_scintil",
                 "eclat")

    def __init__(self, largeur, hauteur, hasard):
        self.x = hasard.uniform(0, largeur)
        self.y = hasard.uniform(0, hauteur)
        self._nouvelle_derive(hasard)
        self.taille = hasard.choice(TAILLES)
        self.phase = hasard.uniform(0, math.tau)
        self.vitesse_scintil = hasard.uniform(0.6, 1.8)
        self.eclat = hasard.uniform(0.45, 1.0)

    def _nouvelle_derive(self, hasard):
        # Une derive lente, plutot vers le haut : la poussiere ne tombe pas,
        # elle flotte. En pixels par seconde.
        angle = hasard.uniform(-math.pi * 0.85, -math.pi * 0.15)
        vitesse = hasard.uniform(4.0, 16.0)
        self.vx = math.cos(angle) * vitesse
        self.vy = math.sin(angle) * vitesse


class FondAnime:
    """La poussiere doree, sur toute la fenetre, derriere le contenu."""

    def __init__(self, largeur=1024, hauteur=640, couleur=None, densite=None,
                 hasard=None):
        self.hasard = hasard or random.Random()
        self.largeur = max(1, int(largeur))
        self.hauteur = max(1, int(hauteur))
        self.densite = int(densite or DENSITE)
        self.couleur = tuple(couleur or (255, 214, 120))
        self.actif = True
        self._dernier_temps = None
        self._ronds = {}
        self.grains = []
        self._peupler()

    # ------------------------------------------------------------- reglages

    def _combien(self):
        surface = self.largeur * self.hauteur
        reference = 1024.0 * 640.0
        return max(20, min(PLAFOND, int(self.densite * surface / reference)))

    def _peupler(self):
        voulu = self._combien()
        while len(self.grains) > voulu:
            self.grains.pop()
        while len(self.grains) < voulu:
            self.grains.append(Grain(self.largeur, self.hauteur, self.hasard))

    def redimensionner(self, largeur, hauteur):
        """La fenetre a change de taille : on garde les grains, on les replace."""
        largeur = max(1, int(largeur))
        hauteur = max(1, int(hauteur))
        if (largeur, hauteur) == (self.largeur, self.hauteur):
            return False
        ancienne_l, ancienne_h = self.largeur, self.hauteur
        self.largeur, self.hauteur = largeur, hauteur
        for grain in self.grains:
            grain.x = grain.x * largeur / float(ancienne_l)
            grain.y = grain.y * hauteur / float(ancienne_h)
        self._peupler()
        self._ronds.clear()
        return True

    def changer_couleur(self, couleur):
        """Suit le theme : la poussiere prend la couleur d'accent du plateau."""
        couleur = tuple(couleur)[:3]
        if couleur == self.couleur:
            return False
        self.couleur = couleur
        self._ronds.clear()
        return True

    # ------------------------------------------------------------- animation

    def _rond(self, taille, alpha):
        """Un rond flou pret a coller. Fabrique une fois, recopie ensuite."""
        cle = (taille, alpha)
        rond = self._ronds.get(cle)
        if rond is not None:
            return rond
        cote = taille * 4
        surface = pygame.Surface((cote, cote), pygame.SRCALPHA)
        centre = cote // 2
        # Trois cercles concentriques : un halo, puis le grain net au milieu.
        for rayon, part in ((taille * 2, 0.18), (taille, 0.55),
                            (max(1, taille // 2), 1.0)):
            couleur = (self.couleur[0], self.couleur[1], self.couleur[2],
                       max(0, min(255, int(alpha * part))))
            pygame.draw.circle(surface, couleur, (centre, centre), rayon)
        self._ronds[cle] = surface
        return surface

    def avancer(self, secondes):
        """Fait deriver les grains. 'secondes' depuis la derniere image."""
        if secondes <= 0:
            return
        secondes = min(secondes, 0.1)      # apres une pause, pas de saut brutal
        marge = 2
        for grain in self.grains:
            grain.x += grain.vx * secondes
            grain.y += grain.vy * secondes
            grain.phase += grain.vitesse_scintil * secondes
            # Il sort d'un cote, il revient par l'autre.
            if grain.y < -marge:
                grain.y = self.hauteur + marge
                grain.x = self.hasard.uniform(0, self.largeur)
                grain._nouvelle_derive(self.hasard)
            elif grain.y > self.hauteur + marge:
                grain.y = -marge
            if grain.x < -marge:
                grain.x = self.largeur + marge
            elif grain.x > self.largeur + marge:
                grain.x = -marge

    def dessiner(self, screen, temps_ms=None):
        """A appeler EN PREMIER, juste apres avoir efface l'ecran."""
        if not self.actif:
            return 0
        largeur, hauteur = screen.get_size()
        self.redimensionner(largeur, hauteur)

        maintenant = (pygame.time.get_ticks() if temps_ms is None
                      else temps_ms) / 1000.0
        if self._dernier_temps is None:
            self._dernier_temps = maintenant
        self.avancer(maintenant - self._dernier_temps)
        self._dernier_temps = maintenant

        dessines = 0
        for grain in self.grains:
            # Le scintillement : chaque grain respire a son rythme.
            brillance = 0.5 + 0.5 * math.sin(grain.phase)
            alpha = int(28 + 92 * brillance * grain.eclat)
            # Fondu sur les bords : un grain ne doit jamais apparaitre ou
            # disparaitre d'un coup au ras du cadre, ni deborder de la fenetre.
            alpha = int(alpha * self._fondu_du_bord(grain))
            if alpha <= 4:
                continue
            # On arrondit l'alpha : sinon on fabriquerait 255 ronds par taille.
            rond = self._rond(grain.taille, (alpha // 12) * 12)
            x = int(grain.x) - rond.get_width() // 2
            y = int(grain.y) - rond.get_height() // 2
            # RIEN NE SORT DU CADRE : un grain a cheval sur le bord n'est pas
            # dessine du tout. Le fondu ci-dessus l'a deja rendu invisible, donc
            # ca ne se voit pas - et l'ecran reste propre.
            if x < 0 or y < 0 or x + rond.get_width() > largeur \
                    or y + rond.get_height() > hauteur:
                continue
            screen.blit(rond, (x, y))
            dessines += 1
        return dessines

    def _fondu_du_bord(self, grain):
        """De 0 au ras du cadre a 1 des qu'on est rentre dans la fenetre."""
        distance = min(grain.x, self.largeur - grain.x,
                       grain.y, self.hauteur - grain.y)
        if distance >= BORDURE_FONDU:
            return 1.0
        if distance <= 0:
            return 0.0
        return distance / float(BORDURE_FONDU)


_PARTAGE = None


def fond(largeur=1024, hauteur=640, couleur=None):
    """Le fond commun a tous les menus : un seul objet, une seule poussiere.

    Le partager evite que chaque ecran reparte d'une poussiere neuve : en
    passant du menu aux reglages, les grains continuent leur derive au lieu de
    se replacer au hasard.
    """
    global _PARTAGE
    if _PARTAGE is None:
        _PARTAGE = FondAnime(largeur, hauteur, couleur)
    elif couleur is not None:
        _PARTAGE.changer_couleur(couleur)
    return _PARTAGE


def dessiner_le_fond(screen, couleur=None):
    """Raccourci : une ligne a mettre en haut de chaque draw() de menu.

    V8 : la densite est un reglage ("poussiere_fond", de 0 a 2). A zero on ne
    dessine rien du tout - certains preferent un fond parfaitement calme, et
    sur une vieille machine c'est aussi quelques images par seconde de gagnees.
    """
    try:
        import apparence
        part = float(apparence.reglage("poussiere_fond", 1.0))
    except Exception:
        part = 1.0
    if part <= 0.0:
        return None
    largeur, hauteur = screen.get_size()
    poussiere = fond(largeur, hauteur, couleur)
    voulu = int(DENSITE * part)
    if poussiere.densite != voulu:
        poussiere.densite = voulu
        poussiere._peupler()
    return poussiere.dessiner(screen)
