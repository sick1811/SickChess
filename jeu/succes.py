# succes.py - SickChess 17/10 (travail p19, demande de Julien) : les succes.
#
# Des badges qui donnent envie de revenir et qui se voient sur la page Steam.
# Ils sont gardes dans succes.json (meme sans Steam) et envoyes a Steam quand
# il est branche (steam.debloquer_succes). Pour qu'ils apparaissent dans
# Steam, il faudra les declarer dans Steamworks avec les memes noms API
# (colonne API ci-dessous) : voir docs/SUCCES_STEAM.md.
# Un succes debloque s'annonce dans un bandeau en haut de l'ecran (4 s).

import json
import os
import time

import pygame

# (cle, nom API Steam, titre, description)
SUCCES = [
    ("premiere_victoire", "PREMIERE_VICTOIRE", "Premier sang", "Battre l'ordinateur pour la première fois."),
    ("victoire_1500", "VICTOIRE_1500", "Joueur de club", "Battre l'ordinateur réglé à 1500 Elo ou plus."),
    ("victoire_2000", "VICTOIRE_2000", "Expert", "Battre l'ordinateur réglé à 2000 Elo ou plus."),
    ("victoire_mat", "VICTOIRE_MAT", "Échec et mat", "Gagner une partie par mat."),
    ("precision_90", "PRECISION_90", "Chirurgien", "Finir une partie avec 90 % de précision ou plus."),
    ("serie_10", "SERIE_10", "Dix d'affilée", "Réussir 10 problèmes classés d'affilée."),
    ("problemes_100", "PROBLEMES_100", "Centurion", "Réussir 100 problèmes classés."),
    ("classement_1500", "CLASSEMENT_1500", "Tacticien", "Atteindre 1500 au classement des problèmes."),
    ("chrono_15", "CHRONO_15", "Éclair", "Trouver 15 problèmes en contre la montre."),
    ("survie_10", "SURVIE_10", "Survivant", "Trouver 10 problèmes en survie."),
    ("jour_7", "JOUR_7", "Fidèle", "Réussir le problème du jour 7 jours de suite."),
    ("ouverture_parfaite", "OUVERTURE_PARFAITE", "Théoricien", "Réciter une ligne d'ouverture sans faute."),
    ("en_ligne", "EN_LIGNE", "Entre amis", "Finir une partie en ligne."),
    ("importer", "IMPORTER", "Archiviste", "Importer une partie jouée ailleurs."),
]
FICHIER = "succes.json"
DUREE_ANNONCE = 4.0

_annonces = []          # [(titre, description, heure)]


def _chemin():
    try:
        from asset_manager import dossier_ecriture
        return os.path.join(dossier_ecriture(), FICHIER)
    except Exception:
        return os.path.join(os.getcwd(), FICHIER)


def obtenus():
    """{cle: date} des succes deja debloques."""
    try:
        with open(_chemin(), "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def debloquer(cle, steam=None):
    """Debloque le succes 'cle'. True s'il est nouveau (et l'annonce)."""
    definition = next((s for s in SUCCES if s[0] == cle), None)
    if definition is None:
        return False
    d = obtenus()
    if cle in d:
        return False
    d[cle] = time.strftime("%Y-%m-%d")
    try:
        with open(_chemin(), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    except OSError as e:
        print("[SUCCES] non enregistre : %s" % e)
    _annonces.append((definition[2], definition[3], time.time()))
    print("[SUCCES] debloque : %s" % definition[2])
    try:
        if steam is None:
            import steam as module_steam
            steam = module_steam.instance()
        steam.debloquer_succes(definition[1])
    except Exception as e:
        print("[SUCCES] Steam : %s" % e)
    return True


def verifier(conditions):
    """{cle: bool} -> debloque toutes les cles vraies. Renvoie les nouvelles."""
    return [cle for cle, vrai in conditions.items() if vrai and debloquer(cle)]


def annonce_en_cours():
    while _annonces and time.time() - _annonces[0][2] > DUREE_ANNONCE:
        _annonces.pop(0)
    return _annonces[0] if _annonces else None


def dessiner_annonce(ecran):
    """Le bandeau « Succès débloqué » en haut de l'ecran (a appeler en dernier)."""
    a = annonce_en_cours()
    if a is None:
        return
    import apparence
    import ui
    titre, description, debut = a
    t = apparence.theme()
    ech = ui.echelle(ecran)
    age = time.time() - debut
    entree = min(1.0, age / 0.25, (DUREE_ANNONCE - age) / 0.25)
    largeur = min(int(460 * ech), ecran.get_width() - 40)
    hauteur = int(64 * ech)
    rect = pygame.Rect((ecran.get_width() - largeur) // 2,
                       int(-hauteur + (hauteur + 16 * ech) * max(0.0, entree)),
                       largeur, hauteur)
    ui.cadre(ecran, rect, t["panneau"], t["accent"], 2, 12, ombre=True)
    ui.texte(ecran, "Succès débloqué : %s" % titre, rect.x + int(16 * ech),
             rect.y + int(10 * ech), ui.t(17, ech), t["accent"], gras=True,
             largeur_max=rect.width - int(32 * ech))
    ui.texte(ecran, description, rect.x + int(16 * ech), rect.y + int(36 * ech),
             ui.t(13, ech), t["texte"], largeur_max=rect.width - int(32 * ech))
