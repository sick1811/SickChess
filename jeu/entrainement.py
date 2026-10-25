# entrainement.py - SickChess 17/10 (travail p06) : l'entraineur d'ouvertures.
#
# Repris de V8_TURBO_3000 (entrainement.py), nettoye : tu choisis une
# ouverture et ta couleur, le jeu joue les coups adverses de la theorie, et
# c'est a toi de trouver les tiens. Un coup faux ne fait pas avancer : on
# reessaie, ou on demande a voir le coup.
#
# Les donnees : les 3 810 lignes du livre lichess (ouvertures.py), deja
# traduites. Le livre donne les coups et les noms, pas les idees : on entraine
# la memoire des coups. La progression par ouverture est gardee dans
# entrainement.json (hors GitHub).
#
# 25/10 (arbre des ouvertures) : l'ecran ne tire plus au hasard dans une
# famille. Il montre l'arbre coup par coup (arbre_ouvertures.py) ;
# « S'entrainer ici » recite les lignes SOUS le noeud choisi, dans l'ordre de
# l'arbre, puis les lignes ratees repassent (Seance). La progression est
# gardee ligne par ligne (format 2) ; l'ancien fichier est converti (.bak).

import copy
import json
import os
import shutil

import chess

FICHIER = "entrainement.json"


class Entrainement:
    """Une ligne a reciter. 'couleur' : le camp que TU joues."""

    def __init__(self, ligne, couleur=chess.WHITE):
        coups, eco, nom = ligne
        self.coups = list(coups)
        self.eco, self.nom = eco, nom
        self.couleur = couleur
        self.plateau = chess.Board()
        self.avance = 0
        self.fautes = 0
        self.trouves = 0
        self.faute_sur_ce_coup = False

    def termine(self):
        return self.avance >= len(self.coups)

    def a_moi_de_jouer(self):
        return not self.termine() and self.plateau.turn == self.couleur

    def coup_attendu(self):
        return None if self.termine() else self.coups[self.avance]

    def coup_attendu_uci(self):
        san = self.coup_attendu()
        try:
            return self.plateau.parse_san(san).uci() if san else None
        except Exception:
            return None

    def jouer_le_coup_de_theorie(self):
        """Le coup suivant du livre (l'adversaire, ou la correction)."""
        san = self.coup_attendu()
        if not san:
            return None
        try:
            coup = self.plateau.parse_san(san)
        except Exception:
            self.avance = len(self.coups)
            return None
        self.plateau.push(coup)
        self.avance += 1
        self.faute_sur_ce_coup = False
        return coup

    def proposer(self, coup):
        """True si c'est le coup de theorie (il est alors joue)."""
        if not self.a_moi_de_jouer():
            return False
        try:
            bon = self.plateau.san(coup) == self.coup_attendu()
        except Exception:
            bon = False
        if not bon:
            if not self.faute_sur_ce_coup:
                self.fautes += 1
            self.faute_sur_ce_coup = True
            return False
        if not self.faute_sur_ce_coup:
            self.trouves += 1
        self.faute_sur_ce_coup = False
        self.plateau.push(coup)
        self.avance += 1
        return True

    def note(self):
        total = self.trouves + self.fautes
        return 100.0 * self.trouves / total if total else 100.0

    def resume(self):
        return "%s - %s" % (self.eco, self.nom)


# --- progression gardee
#
# Format 2 (25/10) :
#   {"version": 2,
#    "lignes":   {"blancs|e4 e5 Nf3 Nc6 Bb5 a6": {essais, reussie, meilleure, derniere}},
#    "familles": {"Partie espagnole|blancs": {lignes, parfaites, moyenne}}}
# "familles" est l'ancien contenu du fichier, repris tel quel : rien de perdu.
VERSION_PROGRESSION = 2
PARFAIT = 99.9


def _chemin():
    try:
        from asset_manager import dossier_ecriture
        return os.path.join(dossier_ecriture(), FICHIER)
    except Exception:
        return os.path.join(os.getcwd(), FICHIER)


def _camp(couleur):
    return "blancs" if couleur == chess.WHITE else "noirs"


def convertir(d):
    """Un contenu lu (ancien ou nouveau) -> format 2. Rien n'est jete."""
    if not isinstance(d, dict):
        return {"version": VERSION_PROGRESSION, "lignes": {}, "familles": {}}
    if d.get("version") == VERSION_PROGRESSION:
        d.setdefault("lignes", {})
        d.setdefault("familles", {})
        return d
    anciennes = {cle: v for cle, v in d.items() if isinstance(v, dict) and "|" in cle}
    return {"version": VERSION_PROGRESSION, "lignes": {}, "familles": anciennes}


def _ecrire(chemin, d):
    try:
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    except OSError as e:
        print("[ENTRAINEMENT] progression non enregistree : %s" % e)


# 23/10 (banc d'essai) : l'ecran Ouvertures demandait la progression 24 fois
# par image. On lit le fichier une fois, puis on garde une copie en memoire,
# mise a jour a chaque enregistrement (par chemin : les tests en changent).
_EN_MEMOIRE = {}
# 25/10 : les lignes reussies par chemin et par camp (l'arbre les lit a chaque image)
_REUSSIES = {}


def _memoire():
    chemin = _chemin()
    if chemin not in _EN_MEMOIRE:
        try:
            with open(chemin, "r", encoding="utf-8") as f:
                lu = json.load(f)
        except (OSError, ValueError):
            lu = None
        neuf = convertir(lu)
        if isinstance(lu, dict) and lu.get("version") != VERSION_PROGRESSION:
            try:                        # l'ancien fichier est garde a cote
                shutil.copyfile(chemin, chemin + ".bak")
            except OSError as e:
                print("[ENTRAINEMENT] copie .bak impossible : %s" % e)
            _ecrire(chemin, neuf)
            print("[ENTRAINEMENT] progression convertie au format %d" % VERSION_PROGRESSION)
        _EN_MEMOIRE[chemin] = neuf
    return _EN_MEMOIRE[chemin]


def charger_progression():
    return copy.deepcopy(_memoire())


def noter_une_ligne(famille, couleur, note, cle_ligne=None):
    """Ajoute le resultat d'une ligne finie ; renvoie l'entree de la famille.
    cle_ligne ('e4 e5 Nf3 ...') : la ligne de l'arbre, notee a part."""
    d = copy.deepcopy(_memoire())
    cle = "%s|%s" % (famille, _camp(couleur))
    e = d["familles"].setdefault(cle, {"lignes": 0, "parfaites": 0, "moyenne": 0.0})
    e["moyenne"] = (e["moyenne"] * e["lignes"] + note) / (e["lignes"] + 1)
    e["lignes"] += 1
    if note >= PARFAIT:
        e["parfaites"] += 1
        try:
            import succes
            succes.debloquer("ouverture_parfaite")
        except Exception as e3:
            print("[SUCCES] %s" % e3)
    if cle_ligne:
        lg = d["lignes"].setdefault("%s|%s" % (_camp(couleur), cle_ligne), {
            "essais": 0, "reussie": False, "meilleure": 0.0, "derniere": 0.0})
        lg["essais"] += 1
        lg["derniere"] = round(float(note), 1)
        lg["meilleure"] = max(lg["meilleure"], lg["derniere"])
        lg["reussie"] = bool(lg["reussie"] or note >= PARFAIT)
    chemin = _chemin()
    _EN_MEMOIRE[chemin] = d
    _REUSSIES.pop(chemin, None)
    _ecrire(chemin, d)
    return dict(e)


def progression(famille, couleur):
    e = _memoire()["familles"].get("%s|%s" % (famille, _camp(couleur)))
    return dict(e) if e is not None else None


def ligne(cle_ligne, couleur):
    """Ce qu'on sait d'une ligne de l'arbre, ou None si jamais jouee."""
    e = _memoire()["lignes"].get("%s|%s" % (_camp(couleur), cle_ligne))
    return dict(e) if e is not None else None


def lignes_reussies(couleur):
    """frozenset des cles de lignes reussies sans faute (gardees en memoire)."""
    par_camp = _REUSSIES.setdefault(_chemin(), {})
    camp = _camp(couleur)
    if camp not in par_camp:
        debut = camp + "|"
        par_camp[camp] = frozenset(c[len(debut):] for c, v in _memoire()["lignes"].items()
                                   if c.startswith(debut) and v.get("reussie"))
    return par_camp[camp]


def reussies_sous(noeud, couleur):
    """Combien de lignes reussies sous ce noeud de l'arbre."""
    reussies = lignes_reussies(couleur)
    cle = noeud.cle()
    if not reussies or not cle:
        return len(reussies)
    debut = cle + " "
    return sum(1 for c in reussies if c == cle or c.startswith(debut))


# --- s'entrainer sous un noeud de l'arbre
class Seance:
    """Les lignes sous un noeud, dans l'ordre de l'arbre (la plus jouee
    d'abord), celles deja reussies en dernier ; une ligne ratee repasse une
    fois le tour fini. 'hasard' (random.Random) : le groupe est melange."""

    def __init__(self, noeud, couleur=chess.WHITE, hasard=None):
        self.noeud = noeud
        self.couleur = couleur
        self.hasard = hasard
        self.a_revoir = []
        self.courante = None
        self.tour = 0
        self.numero = self.taille_tour = 0
        self.file = []
        self._remplir()

    def _remplir(self):
        feuilles = self.noeud.feuilles()
        faites = lignes_reussies(self.couleur)
        a_faire = [f for f in feuilles if f.cle() not in faites]
        deja = [f for f in feuilles if f.cle() in faites]
        if self.hasard is not None:
            self.hasard.shuffle(a_faire)
            self.hasard.shuffle(deja)
        self.file = a_faire + deja
        self._nouveau_tour()

    def _nouveau_tour(self):
        self.tour += 1
        self.numero = 0                   # la ligne en cours dans ce tour
        self.taille_tour = len(self.file)

    def total(self):
        return self.noeud.nb_lignes

    def suivante(self):
        """La prochaine ligne (un noeud feuille de l'arbre)."""
        if not self.file and self.a_revoir:
            self.file, self.a_revoir = self.a_revoir, []
            self._nouveau_tour()
        if not self.file:
            self._remplir()               # tout le groupe est passe : on recommence
        self.courante = self.file.pop(0) if self.file else None
        if self.courante is not None:
            self.numero += 1
        return self.courante

    def resultat(self, note):
        """La ligne courante est finie : ratee, elle repasse a la fin du tour."""
        if self.courante is not None and note < PARFAIT \
                and self.courante not in self.a_revoir:
            self.a_revoir.append(self.courante)

    def entrainement(self):
        """L'Entrainement de la ligne courante, ou None."""
        n = self.courante
        if n is None:
            return None
        nommant = n.nommant()
        return Entrainement((n.coups(), n.code_eco(),
                             nommant.nom_lichess if nommant is not None else ""), self.couleur)

