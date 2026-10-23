# puzzles.py - SickChess : la base des problemes et ton classement de problemes.
#
# Repris de V8_TURBO_3000 (857 lignes), nettoye : l'ancienne base d'un seul
# fichier (puzzles.tsv, 51 200 problemes) n'est plus lue, seules les 64
# tranches comptent. Ce fichier ne depend ni de pygame ni de l'ecran.
#
# LA BASE : celle de lichess (domaine public, CC0 - voir docs/CREDITS.md).
# 4 180 151 problemes tires de vraies parties ; les 644 356 dont lichess juge
# le classement peu fiable (deviation > 100 ou popularite < 50) ont ete ecartes.
# Ils sont ranges en 64 TRANCHES de classement (puzzles/p00 a p63.tsv.gz,
# decrites par puzzles/tranches.tsv) : tirer un probleme a 1300 n'ouvre que la
# tranche qui contient 1300, et seulement la plage utile en reste en memoire.
#
# LE PIEGE DU FORMAT LICHESS : la position est celle d'AVANT le coup de
# l'adversaire. coups[0] est SON coup, joue tout seul ; coups[1] est le tien,
# coups[2] sa reponse, coups[3] le tien, etc.
#
# LE CLASSEMENT DE PROBLEMES est separe du classement de partie (fichier
# puzzles_score.json). Deux modes :
#   CLASSE : ton vrai classement, enregistre ; pas de choix du niveau.
#   LIBRE  : tu choisis le niveau de depart, rien n'est enregistre.
# Le chrono compte : plus tu vas vite, plus le gain est gros (x1,6 -> x0,6).
# La perte, elle, n'est jamais reduite. L'indice coute 8 points tout de suite
# et le probleme ne rapporte plus rien.

import gzip
import json
import os
import random

DOSSIER = "puzzles"
MANIFESTE = "tranches.tsv"
FICHIER_SCORE = "puzzles_score.json"

FENETRE = 150               # on pioche a +/- 150 points de ton classement
FENETRE_MAXIMUM = 600       # et on elargit jusque-la si rien ne convient

FACTEUR_K = 32
CLASSEMENT_DEPART = 1000
CLASSEMENT_MINIMUM = 400
CLASSEMENT_MAXIMUM = 3200

MODE_CLASSE = "classe"
MODE_LIBRE = "libre"

SECONDES_DE_BASE = 6.0
SECONDES_PAR_COUP = 9.0
BONUS_VITESSE_MAXIMUM = 1.60
BONUS_VITESSE_MINIMUM = 0.60

PENALITE_INDICE = 8

PLAGES_EN_MEMOIRE = 3
ESSAIS_DE_TIRAGE = 60
BALAYAGE_MAXIMUM = 60000

_TRANCHES = None
_EN_MEMOIRE = {}
_ORDRE_MEMOIRE = []


# ------------------------------------------------------------------ dossiers

def _dossier_du_jeu():
    try:
        from asset_manager import dossier_ecriture
        return dossier_ecriture()
    except Exception:
        return os.getcwd()


def dossier_des_puzzles():
    """Un dossier puzzles/ pose a cote du jeu passe d'abord ; sinon celui que
    l'executable embarque (voir asset_manager.dossier_de_donnees)."""
    prefere = os.path.join(_dossier_du_jeu(), DOSSIER)
    if os.path.isdir(prefere):
        return prefere
    try:
        from asset_manager import dossier_de_donnees
        return dossier_de_donnees(DOSSIER)
    except Exception:
        return prefere


def chemin_du_manifeste():
    return os.path.join(dossier_des_puzzles(), MANIFESTE)


# ------------------------------------------------------------------ tranches

def tranches():
    """[(fichier, classement_min, classement_max, nombre)] ; [] sans base."""
    global _TRANCHES
    if _TRANCHES is not None:
        return _TRANCHES
    _TRANCHES = []
    try:
        with open(chemin_du_manifeste(), "r", encoding="utf-8") as f:
            for ligne in f:
                if ligne.startswith("#") or not ligne.strip():
                    continue
                morceaux = ligne.rstrip("\n").split("\t")
                if len(morceaux) < 4:
                    continue
                try:
                    _TRANCHES.append((morceaux[0], int(morceaux[1]),
                                      int(morceaux[2]), int(morceaux[3])))
                except ValueError:
                    continue
    except OSError:
        _TRANCHES = []
    if _TRANCHES:
        print("[PROBLEMES] %d tranches, %d problemes"
              % (len(_TRANCHES), sum(t[3] for t in _TRANCHES)))
    return _TRANCHES


def disponible():
    """Y a-t-il des problemes ? (ne lit que le petit manifeste)"""
    return bool(tranches())


def combien():
    return sum(t[3] for t in tranches())


def oublier_les_tranches():
    """Vide la memoire (tests)."""
    global _TRANCHES
    _TRANCHES = None
    _EN_MEMOIRE.clear()
    del _ORDRE_MEMOIRE[:]


def _note_de_ligne(ligne):
    try:
        return int(ligne.split("\t", 5)[3])
    except (IndexError, ValueError):
        return -1


def _plage_de_tranche(nom, bas, haut):
    """Les lignes d'une tranche (triee) dont le classement est entre bas et
    haut. Lue en flux, gardee en memoire pour les tirages suivants."""
    cle = (nom, int(bas), int(haut))
    if cle in _EN_MEMOIRE:
        return _EN_MEMOIRE[cle]
    chemin = os.path.join(dossier_des_puzzles(), nom)
    gardees = []
    try:
        ouvrir = gzip.open if chemin.endswith(".gz") else open
        with ouvrir(chemin, "rt", encoding="utf-8") as f:
            for ligne in f:
                note = _note_de_ligne(ligne)
                if note < bas:
                    continue
                if note > haut:
                    break
                gardees.append(ligne)
    except (OSError, EOFError, ValueError) as souci:
        print("[PROBLEMES] tranche %s illisible : %s" % (nom, souci))
        gardees = []
    _EN_MEMOIRE[cle] = gardees
    _ORDRE_MEMOIRE.append(cle)
    while len(_ORDRE_MEMOIRE) > PLAGES_EN_MEMOIRE:
        _EN_MEMOIRE.pop(_ORDRE_MEMOIRE.pop(0), None)
    return gardees


def _lire_une_ligne(ligne):
    """Une ligne de la base -> un probleme (dict). None si inutilisable."""
    morceaux = ligne.rstrip("\n").split("\t")
    if len(morceaux) < 5 or morceaux[0] == "id":
        return None
    try:
        classement = int(morceaux[3])
    except (TypeError, ValueError):
        return None
    coups = morceaux[2].split()
    if len(coups) < 2:
        return None
    return {"id": morceaux[0], "fen": morceaux[1], "coups": coups,
            "classement": classement, "themes": morceaux[4].split(),
            "partie": morceaux[5] if len(morceaux) > 5 else ""}


def _poids_de_tranche(tranche, bas, haut):
    _nom, mini, maxi, nombre = tranche
    largeur = max(1, maxi - mini + 1)
    commun = max(0, min(maxi, haut) - max(mini, bas) + 1)
    return max(1, int(nombre * commun / float(largeur)))


def _ordre_pondere(concernees, bas, haut, tirage):
    restantes = list(concernees)
    sortie = []
    while restantes:
        poids = [_poids_de_tranche(t, bas, haut) for t in restantes]
        tire = tirage.randrange(sum(poids))
        for indice, part in enumerate(poids):
            if tire < part:
                sortie.append(restantes.pop(indice))
                break
            tire -= part
    return sortie


def _choisir_une_ligne(lignes, themes, tirage, deja_vus):
    if not lignes:
        return None
    for _essai in range(ESSAIS_DE_TIRAGE):
        puzzle = _lire_une_ligne(lignes[tirage.randrange(len(lignes))])
        if puzzle is None or puzzle["id"] in deja_vus:
            continue
        if themes and not themes.intersection(puzzle["themes"]):
            continue
        return puzzle
    if not themes:
        return None
    choix = []
    for ligne in lignes[:BALAYAGE_MAXIMUM]:
        puzzle = _lire_une_ligne(ligne)
        if puzzle and puzzle["id"] not in deja_vus \
                and themes.intersection(puzzle["themes"]):
            choix.append(puzzle)
    return tirage.choice(choix) if choix else None


def tirer(classement=CLASSEMENT_DEPART, themes=None, hasard=None, deja_vus=None):
    """Un probleme proche de ce classement. None si la base est absente."""
    tirage = hasard or random
    deja_vus = deja_vus or set()
    themes = set(themes or ())
    liste = tranches()
    if not liste:
        return None
    fenetre = FENETRE
    while fenetre <= FENETRE_MAXIMUM:
        bas, haut = classement - fenetre, classement + fenetre
        concernees = [t for t in liste if t[2] >= bas and t[1] <= haut]
        for tranche in _ordre_pondere(concernees, bas, haut, tirage):
            trouve = _choisir_une_ligne(_plage_de_tranche(tranche[0], bas, haut),
                                        themes, tirage, deja_vus)
            if trouve is not None:
                return trouve
        fenetre *= 2
    # Classement hors de la base : la tranche la plus proche fera l'affaire.
    proche = min(liste, key=lambda t: abs((t[1] + t[2]) // 2 - classement))
    lignes = _plage_de_tranche(proche[0], proche[1], proche[2])
    return _choisir_une_ligne(lignes, themes, tirage, set())


# ------------------------------------------------------------------ themes

THEMES_FRANCAIS = {
    "mate": "Mat", "mateIn1": "Mat en 1", "mateIn2": "Mat en 2",
    "mateIn3": "Mat en 3", "fork": "Fourchette", "pin": "Clouage",
    "skewer": "Enfilade", "discoveredAttack": "Découverte",
    "doubleCheck": "Échec double", "sacrifice": "Sacrifice",
    "deflection": "Déviation", "attraction": "Attraction",
    "clearance": "Degagement", "interference": "Interception",
    "xRayAttack": "Attaque aux rayons X", "hangingPiece": "Pièce en prise",
    "trappedPiece": "Pièce piégée", "backRankMate": "Mat du couloir",
    "smotheredMate": "Mat etouffe", "promotion": "Promotion",
    "endgame": "Finale", "middlegame": "Milieu de partie",
    "opening": "Ouverture", "advancedPawn": "Pion passe",
    "defensiveMove": "Coup défensif", "quietMove": "Coup calme",
    "zugzwang": "Zugzwang", "crushing": "Ecrasant", "advantage": "Avantage",
    "equality": "Égalité", "short": "Court", "long": "Long",
    "veryLong": "Très long", "oneMove": "Un seul coup",
    "master": "Partie de maitre",
}

# Les themes proposes dans le filtre de l'ecran (dans cet ordre).
THEMES_PROPOSES = ["mateIn1", "mateIn2", "mateIn3", "fork", "pin", "skewer",
                   "discoveredAttack", "sacrifice", "deflection",
                   "hangingPiece", "backRankMate", "endgame"]


def nom_du_theme(theme):
    return THEMES_FRANCAIS.get(theme, theme)


def description(puzzle):
    """'Fourchette, Finale' pour l'ecran ('Tactique' si rien de parlant)."""
    if not puzzle:
        return ""
    noms = [nom_du_theme(t) for t in puzzle.get("themes", [])
            if t in THEMES_FRANCAIS and t not in ("short", "long", "veryLong",
                                                  "oneMove", "crushing",
                                                  "advantage", "equality")]
    return ", ".join(noms[:3]) if noms else "Tactique"


def lien_lichess(puzzle):
    identifiant = (puzzle or {}).get("id")
    return "https://lichess.org/training/%s" % identifiant if identifiant else ""


# ------------------------------------------------------------------ le probleme

def coup_d_ouverture(puzzle):
    coups = (puzzle or {}).get("coups") or []
    return coups[0] if coups else None


def coups_a_trouver(puzzle):
    return ((puzzle or {}).get("coups") or [])[1::2]


def reponses_adverses(puzzle):
    return ((puzzle or {}).get("coups") or [])[2::2]


def coup_attendu(puzzle, avance):
    a_trouver = coups_a_trouver(puzzle)
    return a_trouver[avance] if 0 <= avance < len(a_trouver) else None


def reponse_apres(puzzle, avance):
    reponses = reponses_adverses(puzzle)
    return reponses[avance] if 0 <= avance < len(reponses) else None


def nombre_de_coups(puzzle):
    return len(coups_a_trouver(puzzle))


# ------------------------------------------------------------------ classement

def temps_de_reference(puzzle):
    return SECONDES_DE_BASE + SECONDES_PAR_COUP * max(1, nombre_de_coups(puzzle))


def bonus_de_vitesse(secondes, puzzle):
    """x1,60 trouve tout de suite, x0,60 au-dela de 2 fois le temps de
    reference, en ligne droite entre les deux. 1,0 sans chrono."""
    if secondes is None:
        return 1.0
    try:
        secondes = max(0.0, float(secondes))
    except (TypeError, ValueError):
        return 1.0
    limite = 2.0 * temps_de_reference(puzzle)
    part = min(1.0, secondes / limite) if limite > 0 else 1.0
    return BONUS_VITESSE_MAXIMUM - (BONUS_VITESSE_MAXIMUM
                                    - BONUS_VITESSE_MINIMUM) * part


def nouveau_classement(le_tien, celui_du_puzzle, reussi, facteur=1.0):
    """Calcul Elo. Le bonus de vitesse ne s'applique qu'aux gains."""
    try:
        le_tien = float(le_tien)
        celui_du_puzzle = float(celui_du_puzzle)
    except (TypeError, ValueError):
        return int(CLASSEMENT_DEPART)
    attendu = 1.0 / (1.0 + 10.0 ** ((celui_du_puzzle - le_tien) / 400.0))
    variation = FACTEUR_K * ((1.0 if reussi else 0.0) - attendu)
    if variation > 0:
        variation *= max(0.0, float(facteur))
    return int(round(max(float(CLASSEMENT_MINIMUM),
                         min(float(CLASSEMENT_MAXIMUM), le_tien + variation))))


def chemin_du_score():
    return os.path.join(_dossier_du_jeu(), FICHIER_SCORE)


def score_neuf(classement=None):
    depart = int(classement or CLASSEMENT_DEPART)
    return {"classement": depart, "reussis": 0, "rates": 0, "aides": 0,
            "serie": 0, "meilleure_serie": 0, "meilleur_classement": depart,
            "vus": []}


def charger_le_score():
    defaut = score_neuf()
    try:
        with open(chemin_du_score(), "r", encoding="utf-8") as f:
            score = json.load(f)
    except (OSError, ValueError):
        return defaut
    if not isinstance(score, dict):
        return defaut
    for cle, valeur in defaut.items():
        score.setdefault(cle, valeur)
    return score


def enregistrer_le_score(score):
    """Ecrit le score (500 derniers problemes vus gardes). False si echec."""
    try:
        score = dict(score)
        score["vus"] = list(score.get("vus", []))[-500:]
        with open(chemin_du_score(), "w", encoding="utf-8") as f:
            json.dump(score, f, indent=2, ensure_ascii=False, sort_keys=True)
        return True
    except OSError as souci:
        print("[PROBLEMES] score non enregistre : %s" % souci)
        return False


def noter(score, puzzle, reussi, secondes=None, indice=False):
    """Met le score a jour. Renvoie (score, variation du classement)."""
    avant = int(score.get("classement", CLASSEMENT_DEPART))
    if reussi and indice:
        # Resolu avec l'indice : aucun gain, compte comme rate, serie perdue.
        apres = avant
        score["aides"] = int(score.get("aides", 0)) + 1
        score["rates"] = int(score.get("rates", 0)) + 1
        score["serie"] = 0
    else:
        apres = nouveau_classement(avant, puzzle.get("classement", avant),
                                   reussi, bonus_de_vitesse(secondes, puzzle))
        cle = "reussis" if reussi else "rates"
        score[cle] = int(score.get(cle, 0)) + 1
        if reussi:
            score["serie"] = int(score.get("serie", 0)) + 1
            score["meilleure_serie"] = max(int(score.get("meilleure_serie", 0)),
                                           score["serie"])
        else:
            score["serie"] = 0
    score["classement"] = apres
    score["meilleur_classement"] = max(int(score.get("meilleur_classement",
                                                     apres)), apres)
    if puzzle.get("id"):
        score["vus"] = list(score.get("vus", [])) + [puzzle["id"]]
    return score, apres - avant


def penaliser_pour_l_indice(score):
    avant = int(score.get("classement", CLASSEMENT_DEPART))
    apres = max(CLASSEMENT_MINIMUM, avant - PENALITE_INDICE)
    score["classement"] = apres
    return score, apres - avant


def pourcentage(score):
    reussis = int(score.get("reussis", 0))
    total = reussis + int(score.get("rates", 0))
    return 100.0 * reussis / total if total else 0.0


# ------------------------------------------------------------------ session

class Session:
    """Le mode, le classement et les compteurs d'une seance de problemes.
    C'est elle qui sait si l'on enregistre (CLASSE) ou non (LIBRE)."""

    def __init__(self, mode=MODE_CLASSE, depart=None):
        self.mode = MODE_LIBRE if mode == MODE_LIBRE else MODE_CLASSE
        self.classe = self.mode == MODE_CLASSE
        enregistre = charger_le_score()
        if self.classe:
            self.score = enregistre
        else:
            self.score = score_neuf(depart)
            self.score["vus"] = list(enregistre.get("vus", []))
        self.classement_de_depart = self.classement()
        self.gain = 0

    def classement(self):
        return int(self.score.get("classement", CLASSEMENT_DEPART))

    def serie(self):
        return int(self.score.get("serie", 0))

    def meilleure_serie(self):
        return int(self.score.get("meilleure_serie", 0))

    def reussis(self):
        return int(self.score.get("reussis", 0))

    def rates(self):
        return int(self.score.get("rates", 0))

    def pourcentage(self):
        return pourcentage(self.score)

    def deja_vus(self):
        return set(self.score.get("vus", []))

    def variation(self):
        return self.classement() - self.classement_de_depart

    def nom_du_mode(self):
        return "Classé" if self.classe else "Libre"

    def tirer_un_puzzle(self, themes=None, hasard=None):
        return tirer(self.classement(), themes=themes, hasard=hasard,
                     deja_vus=self.deja_vus())

    def noter_un_puzzle(self, puzzle, reussi, secondes=None, indice=False):
        if not puzzle:
            self.gain = 0
            return 0
        self.score, self.gain = noter(self.score, puzzle, reussi,
                                      secondes=secondes, indice=indice)
        if self.classe:
            enregistrer_le_score(self.score)
            import classements                 # 24/10 (p37) : classement Steam
            classements.envoyer("problemes", self.classement())
            try:
                import succes
                succes.verifier({"serie_10": self.serie() >= 10,
                                 "problemes_100": self.reussis() >= 100,
                                 "classement_1500": self.classement() >= 1500})
            except Exception as e:
                print("[SUCCES] %s" % e)
        return self.gain

    def payer_l_indice(self):
        self.score, perte = penaliser_pour_l_indice(self.score)
        if self.classe:
            enregistrer_le_score(self.score)
        return perte
