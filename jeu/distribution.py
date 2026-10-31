# distribution.py - SickChess (31/10, demande de Julien) : quelle version du jeu
# tourne, et donc quel numero Steam utiliser. C'est le SEUL endroit qui le sait.
#
#   amis  : version entre amis (et dossier de developpement). Steam avec le
#           numero de test 480 (« Spacewar » de Valve). Comportement d'avant.
#   steam : version vendue sur Steam. Seul le numero change : APPID_STEAM_REEL.
#   itch  : version vendue sur itch.io. JAMAIS de Steam (l'acheteur ne l'a pas
#           forcement) : pas de jeu en ligne ni de classements mondiaux ; la
#           partie a deux sur le meme PC et les records personnels restent.
#
# Le choix est ecrit au moment de la compilation dans distribution.json, a cote
# du jeu (outils/publier_maj.py). Fichier absent ou illisible = « amis ».
# Pour essayer une autre version sans compiler : variable d'environnement
# SICKCHESS_DISTRIBUTION=itch (ou steam) avant de lancer python SickChess.py.

import json
import os
import sys

AMIS, STEAM, ITCH = "amis", "steam", "itch"
DISTRIBUTIONS = (AMIS, STEAM, ITCH)
FICHIER = "distribution.json"
VARIABLE = "SICKCHESS_DISTRIBUTION"

APPID_DE_TEST = 480        # « Spacewar » : le numero de test que Valve donne a tous
# Le vrai numero de SickChess sur Steam (compte Steamworks). Le jour venu : le
# seul chiffre a changer, ici. Tant qu'il vaut None, verifier_version.py --steam
# bloque la version Steam.
APPID_STEAM_REEL = None

_ACTUELLE = None


def dossier_du_jeu():
    """Le dossier du jeu (a cote de SickChess.exe, ou la racine du projet)."""
    if getattr(sys, "frozen", False):
        # Compile : a cote de l'exe, quel que soit le rangement de PyInstaller.
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lire(dossier=None):
    """La distribution ecrite dans distribution.json de `dossier` (amis si absent)."""
    try:
        with open(os.path.join(dossier or dossier_du_jeu(), FICHIER), "r",
                  encoding="utf-8") as f:
            nom = json.load(f).get("distribution")
    except (OSError, ValueError, AttributeError):
        return AMIS
    return nom if nom in DISTRIBUTIONS else AMIS


def actuelle():
    """La distribution du jeu qui tourne (lue une seule fois)."""
    global _ACTUELLE
    if _ACTUELLE is None:
        essai = (os.environ.get(VARIABLE) or "").strip().lower()
        _ACTUELLE = essai if essai in DISTRIBUTIONS else lire()
    return _ACTUELLE


def fixer(nom):
    """Pour les tests : impose une distribution (None = relire le fichier)."""
    global _ACTUELLE
    _ACTUELLE = nom if nom in DISTRIBUTIONS else None


def numero_steam(nom=None):
    """480 pour amis, APPID_STEAM_REEL pour steam (None tant qu'il n'est pas
    connu), None pour itch."""
    nom = nom or actuelle()
    if nom == AMIS:
        return APPID_DE_TEST
    if nom == STEAM:
        return APPID_STEAM_REEL
    return None


def steam_permis(nom=None):
    """False pour itch : Steam n'est jamais demarre, meme s'il est ouvert."""
    return (nom or actuelle()) != ITCH


def contenu_fichier(nom):
    """Le texte de distribution.json pour la distribution `nom` (compilation)."""
    if nom not in DISTRIBUTIONS:
        raise ValueError("distribution inconnue : %r" % (nom,))
    return json.dumps({"distribution": nom}, indent=2) + "\n"
