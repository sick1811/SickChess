# niveaux_elo.py - SickChess 31/10 (travail p34, « niveaux en vrai Elo »)
#
# LA TABLE DE CALIBRAGE DES NIVEAUX DE L'ORDINATEUR.
#
# Le joueur choisit un Elo AFFICHE (bouton « Club 1600 », curseur, « Se caler
# sur mon classement »). Cet Elo est celui qu'on montre partout : Options,
# écran de partie, sauvegarde, résumé, calcul du classement du profil.
#
# Ce n'est pas forcément la CONSIGNE envoyée au moteur. Si les matchs de
# calibrage (outils/calibrer_elo.py) montrent que la consigne 1600 joue en vrai
# comme un 1450, il faut envoyer une consigne plus haute pour que « 1600 »
# soit vrai. Cette table fait la conversion :
#
#     Elo affiché  ->  consigne envoyée à engine.set_custom_elo
#
# Entre deux lignes, on interpole en ligne droite.
#
# TANT QU'IL N'Y A PAS DE MESURE, LA TABLE EST L'IDENTITE (consigne = Elo
# affiché) : le jeu se comporte exactement comme avant. Pour l'appliquer :
# lancer la mesure de nuit, lire docs/CALIBRAGE_ELO.md, recopier la table
# proposée ici (colonnes « mesuré » et « marge » comprises), relancer
# tests/test_niveaux_elo.py.

# Les boutons du panneau « NIVEAU DE L'ORDINATEUR » (settings_screen.py).
NIVEAUX = [
    ("Débutant", 400), ("Facile", 800), ("Moyen", 1200), ("Club", 1600),
    ("Fort", 2000), ("Très fort", 2400), ("Maximum", 3000),
]

# Bornes du curseur Elo des Options (settings_screen.Slider).
ELO_MIN = 100
ELO_MAX = 3200

# Contre quoi la mesure a été faite (recopié du rapport de calibrage).
ETALON = None          # ex. "Stockfish 18, UCI_Elo, cadence 120 s + 1 s"
DATE_MESURE = None     # ex. "2026-11-02"

# (Elo affiché, consigne envoyée au moteur, Elo mesuré ou None, marge ± ou None)
# - colonnes 1 et 2 strictement croissantes (test_niveaux_elo le vérifie) ;
# - « mesuré » = la performance de la consigne dans les matchs de calibrage.
TABLE = [
    (100, 100, None, None),
    (400, 400, None, None),
    (800, 800, None, None),
    (1200, 1200, None, None),
    (1600, 1600, None, None),
    (2000, 2000, None, None),
    (2400, 2400, None, None),
    (3000, 3000, None, None),
    (3200, 3200, None, None),
]


def _borner(elo):
    try:
        elo = float(elo)
    except (TypeError, ValueError):
        elo = float(TABLE[0][0])
    return max(float(ELO_MIN), min(float(ELO_MAX), elo))


def _interpoler(valeur, source, cible):
    """Lit la colonne `cible` à la position `valeur` de la colonne `source`."""
    if valeur <= TABLE[0][source]:
        return float(TABLE[0][cible])
    if valeur >= TABLE[-1][source]:
        return float(TABLE[-1][cible])
    for gauche, droite in zip(TABLE, TABLE[1:]):
        if gauche[source] <= valeur <= droite[source]:
            part = (valeur - gauche[source]) / float(droite[source] - gauche[source])
            return gauche[cible] + part * (droite[cible] - gauche[cible])
    return float(TABLE[-1][cible])


def consigne(elo_affiche):
    """La consigne à envoyer au moteur pour jouer à `elo_affiche`."""
    return int(round(_interpoler(_borner(elo_affiche), 0, 1)))


def elo_affiche(consigne_moteur):
    """L'inverse : quel Elo affiché correspond à cette consigne."""
    try:
        valeur = float(consigne_moteur)
    except (TypeError, ValueError):
        valeur = float(TABLE[0][1])
    return int(round(_interpoler(valeur, 1, 0)))


def mesure(elo_affiche_voulu):
    """(Elo mesuré, marge) d'une ligne de la table, ou None si pas mesurée."""
    for affiche, _consigne, mesure_, marge in TABLE:
        if affiche == elo_affiche_voulu and mesure_ is not None:
            return mesure_, marge
    return None


def est_calibree():
    """Vrai si au moins une ligne de la table vient d'une vraie mesure."""
    return any(ligne[2] is not None for ligne in TABLE)
