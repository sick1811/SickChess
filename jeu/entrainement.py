# entrainement.py - SickChess 17/10 (travail p06) : l'entraineur d'ouvertures.
#
# Repris de V8_TURBO_3000 (entrainement.py), nettoye : tu choisis une
# ouverture et ta couleur, le jeu joue les coups adverses de la theorie, et
# c'est a toi de trouver les tiens. Chaque nouvelle ligne est tiree au hasard
# dans la famille : c'est ainsi que les DEVIATIONS courantes arrivent
# (Najdorf, puis Dragon, puis Scheveningue...). Un coup faux ne fait pas
# avancer : on reessaie, ou on demande a voir le coup.
#
# Les donnees : les 3 810 lignes du livre lichess (ouvertures.py), deja
# traduites. Le livre donne les coups et les noms, pas les idees : on entraine
# la memoire des coups. La progression par ouverture est gardee dans
# entrainement.json (hors GitHub).

import json
import os
import random

import chess

import ouvertures

FAMILLES_MISES_EN_AVANT = [
    "Défense sicilienne", "Partie espagnole", "Partie italienne",
    "Défense française", "Défense Caro-Kann", "Gambit dame refusé",
    "Gambit dame accepté", "Défense slave", "Défense est-indienne",
    "Défense nimzo-indienne", "Ouverture anglaise", "Défense scandinave",
    "Partie écossaise", "Défense Pirc", "Défense hollandaise",
    "Partie viennoise", "Défense Alekhine", "Défense Grünfeld",
    "Défense Benoni", "Défense russe", "Gambit du roi accepté", "Ouverture catalane",
]
COUPS_MINIMUM = 6          # demi-coups
COUPS_MAXIMUM = 20
FICHIER = "entrainement.json"


def famille_de(nom):
    return nom.split(",")[0].split(":")[0].strip()


def lignes_de(famille, minimum=COUPS_MINIMUM, maximum=COUPS_MAXIMUM):
    """Les lignes de theorie de la famille [(coups SAN, eco, nom)], sans les
    lignes qui ne sont que le debut d'une autre."""
    famille = str(famille or "").strip()
    trouvees = []
    for cle, (eco, nom) in ouvertures.livre().items():
        if famille_de(nom) != famille:
            continue
        coups = cle.split()
        if minimum <= len(coups) <= maximum:
            trouvees.append((coups, eco, nom))
    trouvees.sort(key=lambda l: -len(l[0]))
    gardees = []
    for coups, eco, nom in trouvees:
        prefixe = " ".join(coups) + " "
        if any(" ".join(c).startswith(prefixe) for c, _e, _n in gardees):
            continue
        gardees.append((coups, eco, nom))
    gardees.sort(key=lambda l: (l[1], l[2]))
    return gardees


_FAMILLES = []


def familles(minimum=4):
    """[(famille, nombre de lignes)] : les mises en avant d'abord."""
    if _FAMILLES:
        return list(_FAMILLES)
    comptes = {}
    for _cle, (_eco, nom) in ouvertures.livre().items():
        f = famille_de(nom)
        comptes[f] = comptes.get(f, 0) + 1
    utiles = {}
    for nom, combien in comptes.items():
        if combien >= minimum:
            n = len(lignes_de(nom))
            if n:
                utiles[nom] = n
    en_avant = [(n, utiles[n]) for n in FAMILLES_MISES_EN_AVANT if n in utiles]
    reste = sorted(((n, c) for n, c in utiles.items() if n not in FAMILLES_MISES_EN_AVANT),
                   key=lambda x: (-x[1], x[0]))
    _FAMILLES.extend(en_avant + reste)
    return list(_FAMILLES)


def tirer_une_ligne(famille, hasard=None, sauf=None):
    lignes = lignes_de(famille)
    if sauf and len(lignes) > 1:
        lignes = [l for l in lignes if l[0] != sauf] or lignes
    return (hasard or random).choice(lignes) if lignes else None


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
def _chemin():
    try:
        from asset_manager import dossier_ecriture
        return os.path.join(dossier_ecriture(), FICHIER)
    except Exception:
        return os.path.join(os.getcwd(), FICHIER)


def charger_progression():
    try:
        with open(_chemin(), "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def noter_une_ligne(famille, couleur, note):
    """Ajoute le resultat d'une ligne finie ; renvoie l'entree de la famille."""
    d = charger_progression()
    cle = "%s|%s" % (famille, "blancs" if couleur == chess.WHITE else "noirs")
    e = d.setdefault(cle, {"lignes": 0, "parfaites": 0, "moyenne": 0.0})
    e["moyenne"] = (e["moyenne"] * e["lignes"] + note) / (e["lignes"] + 1)
    e["lignes"] += 1
    if note >= 99.9:
        e["parfaites"] += 1
        try:
            import succes
            succes.debloquer("ouverture_parfaite")
        except Exception as e3:
            print("[SUCCES] %s" % e3)
    try:
        with open(_chemin(), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    except OSError as e2:
        print("[ENTRAINEMENT] progression non enregistree : %s" % e2)
    return e


def progression(famille, couleur):
    cle = "%s|%s" % (famille, "blancs" if couleur == chess.WHITE else "noirs")
    return charger_progression().get(cle)
