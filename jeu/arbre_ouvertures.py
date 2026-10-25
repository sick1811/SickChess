# arbre_ouvertures.py - SickChess 25/10 : les ouvertures rangees en ARBRE,
# coup par coup (demande de Julien : « une suite logique : coup 1, puis 2,
# puis 3 »).
#
# Un noeud = un demi-coup : 1.e4 -> 1...e5 -> 2.Nf3 -> 2...Nc6 -> 3.Bb5 ...
# L'arbre est fait avec les 3 810 lignes du livre lichess (ouvertures.livre(),
# noms deja traduits) : chaque ligne se range sous le coup qui la fait naitre,
# et le noeud ou elle finit porte son nom et son code ECO. On ne nomme rien a
# la main.
#
# Tri fixe a chaque niveau : le coup qui a le plus de lignes en dessous
# d'abord (le livre lichess ne donne pas le nombre de parties jouees), puis
# l'ordre alphabetique. Jamais de hasard : l'arbre est le meme a chaque
# lancement.
#
# Construit une fois (premier appel de racine()), garde en memoire ensuite.
# Les lignes a reciter sont les FEUILLES (les lignes qui ne sont le debut
# d'aucune autre) : reciter « Partie espagnole » seule ne sert a rien quand
# la Morphy, l'Ouverte et la Fermee la contiennent deja.
#
# Ce module ne change rien au livre : nom de l'ouverture en partie, pastille
# « Theorique » de la revue et resume du coach lisent toujours ouvertures.py.

import chess

import ouvertures

SEPARATEUR = " › "


class Noeud:
    __slots__ = ("san", "parent", "enfants", "eco", "nom_lichess", "profondeur",
                 "nb_lignes", "_cle")

    def __init__(self, san, parent):
        self.san = san                  # en anglais (le livre), affiche via notation
        self.parent = parent
        self.enfants = []               # tries une fois l'arbre fini
        self.eco = ""
        self.nom_lichess = ""           # vide : simple coup de passage
        self.profondeur = 0 if parent is None else parent.profondeur + 1
        self.nb_lignes = 0              # feuilles en dessous (lui compris)
        self._cle = None

    # --- ce que l'ecran lit
    def est_une_ligne(self):
        """Une ligne lichess finit ici (le noeud a un nom)."""
        return bool(self.nom_lichess)

    def est_une_feuille(self):
        return not self.enfants

    def coups(self):
        """Les coups depuis le debut, en SAN anglaise."""
        suite, n = [], self
        while n.parent is not None:
            suite.append(n.san)
            n = n.parent
        suite.reverse()
        return suite

    def cle(self):
        """'e4 e5 Nf3' : la cle du livre (et de la progression)."""
        if self._cle is None:
            self._cle = " ".join(self.coups())
        return self._cle

    def chemin(self):
        """Les noeuds de la racine (exclue) jusqu'a lui."""
        suite, n = [], self
        while n.parent is not None:
            suite.append(n)
            n = n.parent
        suite.reverse()
        return suite

    def nommant(self):
        """Le noeud nomme le plus proche, lui compris (None avant le 1er nom)."""
        n = self
        while n is not None and not n.nom_lichess:
            n = n.parent
        return n

    def nom(self):
        """« Partie espagnole › Défense Morphy › Fermée » (celui du noeud
        nomme le plus proche au-dessus, s'il n'a pas de nom a lui)."""
        n = self.nommant()
        return nom_en_arbre(n.nom_lichess) if n is not None else ""

    def code_eco(self):
        n = self.nommant()
        return n.eco if n is not None else ""

    def famille(self):
        n = self.nommant()
        return n.nom_lichess.split(",")[0].split(":")[0].strip() if n is not None else ""

    def feuilles(self):
        """Les lignes a reciter sous ce noeud, dans l'ordre de l'arbre."""
        sortie, pile = [], [self]
        while pile:
            n = pile.pop()
            if not n.enfants:
                sortie.append(n)
            else:
                pile.extend(reversed(n.enfants))
        return sortie

    def position(self):
        """Le plateau apres ses coups (chess.Board : pas de Freestyle ici)."""
        plateau = chess.Board()
        for san in self.coups():
            plateau.push_san(san)
        return plateau

    def contient(self, autre):
        """'autre' est-il ce noeud ou en dessous ?"""
        n = autre
        while n is not None:
            if n is self:
                return True
            n = n.parent
        return False

    def __repr__(self):
        return "<Noeud %s>" % (self.cle() or "racine")


def nom_en_arbre(nom):
    """'Partie espagnole, Défense Morphy, Fermée' -> avec des › (le livre
    traduit separe deja famille, variante et sous-variante par des virgules ;
    les noms anglais de lichess par « : » puis des virgules)."""
    nom = str(nom or "").replace(": ", ", ")
    morceaux = [m.strip() for m in nom.split(", ") if m.strip()]
    # « Partie espagnole, fermée » : chaque morceau commence par une majuscule
    return SEPARATEUR.join(m[0].upper() + m[1:] for m in morceaux)


def etiquette_coup(noeud, avec_numero=True, afficher=None):
    """'1.e4', '1...e5' (afficher : la fonction de notation, ex. Cf3)."""
    san = afficher(noeud.san) if afficher else noeud.san
    numero = (noeud.profondeur + 1) // 2
    if noeud.profondeur % 2 == 1:
        return "%d.%s" % (numero, san)
    return ("%d...%s" % (numero, san)) if avec_numero else san


def etiquette_chaine(noeuds, afficher=None):
    """'2.Nf3 Nc6 3.Bb5' : une suite de demi-coups sur une seule ligne."""
    morceaux = []
    for i, n in enumerate(noeuds):
        blanc = n.profondeur % 2 == 1
        morceaux.append(etiquette_coup(n, avec_numero=blanc or i == 0, afficher=afficher))
    return " ".join(morceaux)


def chaine_depuis(noeud):
    """Le noeud et ses coups de passage replies avec lui : on avance tant que
    le noeud n'a pas de nom et un seul suivant. Le dernier est celui qu'on
    deplie (pas de niveaux vides a l'ecran)."""
    suite = [noeud]
    while not noeud.nom_lichess and len(noeud.enfants) == 1:
        noeud = noeud.enfants[0]
        suite.append(noeud)
    return suite


# ------------------------------------------------------------ construction
_RACINE = None
_INDEX = {}


def construire(livre=None):
    """Un arbre neuf a partir du livre {suite SAN: (eco, nom)}."""
    livre = ouvertures.livre() if livre is None else livre
    racine = Noeud("", None)
    index = {"": racine}
    # ordre des cles trie : la construction ne depend pas de l'ordre du fichier
    for cle in sorted(livre):
        eco, nom = livre[cle]
        n = racine
        prefixe = []
        for san in cle.split():
            prefixe.append(san)
            suivant = None
            for e in n.enfants:
                if e.san == san:
                    suivant = e
                    break
            if suivant is None:
                suivant = Noeud(san, n)
                n.enfants.append(suivant)
                index[" ".join(prefixe)] = suivant
            n = suivant
        n.eco, n.nom_lichess = eco, nom
    # nombre de lignes en dessous (de bas en haut), puis tri fixe
    def compter(n):
        if not n.enfants:
            n.nb_lignes = 1
            return 1
        n.nb_lignes = sum(compter(e) for e in n.enfants)
        return n.nb_lignes
    compter(racine)                     # 36 demi-coups au plus : pas de souci de pile
    pile = [racine]
    while pile:
        n = pile.pop()
        n.enfants.sort(key=lambda e: (-e.nb_lignes, e.san))
        pile.extend(n.enfants)
    return racine, index


def racine():
    """L'arbre du livre, construit une seule fois."""
    global _RACINE, _INDEX
    if _RACINE is None:
        _RACINE, _INDEX = construire()
    return _RACINE


def noeud(cle):
    """Le noeud de la suite 'e4 e5 Nf3' (ou une liste de SAN), None sinon."""
    racine()
    if isinstance(cle, (list, tuple)):
        cle = " ".join(cle)
    return _INDEX.get(str(cle or "").strip())


def oublier():
    """Le livre a change (langue des noms) : l'arbre sera refait."""
    global _RACINE, _INDEX
    _RACINE, _INDEX = None, {}
