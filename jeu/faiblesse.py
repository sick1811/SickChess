# faiblesse.py - V7.2 : NOUVEAU FICHIER
#
# JOUER VRAIMENT FAIBLE (ta remarque : "le bot n'a pas 100 Elo, a 100 Elo il est
# 10x plus fort").
#
# TU AVAIS RAISON. Voila ce que le jeu faisait a 100 Elo, et pourquoi c'etait
# beaucoup trop fort :
#
#   1. Stockfish REFUSE UCI_Elo en dessous de 1320. En dessous, le jeu se
#      rabattait sur "Skill Level 0". Or Skill Level 0 n'est pas un debutant :
#      il vaut environ 1350 Elo. C'est le PLANCHER de Stockfish, pas le sol.
#
#   2. Il ajoutait "profondeur 1", en croyant que chercher a un seul coup rend
#      le moteur faible. C'est faux : meme a profondeur 1, Stockfish fait une
#      RECHERCHE DE QUIESCENCE, c'est-a-dire qu'il deroule toutes les prises
#      jusqu'a une position calme. Resultat : il ne laisse JAMAIS une piece en
#      prise, et il ramasse TOUJOURS le materiel gratuit. Un joueur a 100 Elo
#      fait exactement l'inverse, tout le temps.
#
# LA SOLUTION EST DE CHANGER DE PRINCIPE. On arrete de demander a Stockfish
# d'etre mauvais : on lui demande de CLASSER tous les coups, honnetement, puis
# c'est NOUS qui choisissons, plus ou moins mal selon le niveau vise.
#
#   - Stockfish tourne a pleine lucidite (Skill Level 20) mais a faible
#     profondeur : il ne voit pas les tactiques lointaines.
#   - Il renvoie les N meilleurs coups avec leur note (MultiPV).
#   - On tire au sort parmi eux, en donnant a chaque coup un poids
#     exp(-perte / sigma), ou "perte" est ce que le coup coute en centiemes de
#     pion par rapport au meilleur, et "sigma" est la largeur de l'erreur qu'on
#     s'autorise au niveau vise.
#
# LA GAFFE EST UN EVENEMENT A PART. C'est la correction de ta deuxieme
# remarque : "le bot a 1000 Elo n'a pas 1000 Elo, il blunder souvent."
#
# Ma version precedente melangeait tout dans une seule loi : plus le niveau
# baissait, plus la loi s'elargissait. Le probleme, c'est qu'une loi large lache
# la dame TRES souvent - a 1000 Elo elle produisait une vraie gaffe un coup sur
# sept. Un humain a 1000 Elo gaffe DEUX FOIS PAR PARTIE, pas tous les sept coups.
#
# Alors on separe franchement les deux choses, parce que ce sont deux choses
# differentes dans la tete d'un joueur :
#
#   LE COUP ORDINAIRE (la plupart du temps) : il choisit parmi les coups
#       CORRECTS seulement - ceux qui perdent moins de 250 centiemes de pion.
#       Il ne lache donc jamais une piece par distraction ordinaire. Plus le
#       niveau est bas, plus il prend un coup tiede plutot que le meilleur.
#
#   LA GAFFE (probabilite taux_de_gaffe(elo)) : la, il choisit expres parmi les
#       MAUVAIS coups. C'est le coup ou il laisse le cavalier en prise.
#
# On pilote donc deux choses observables, et rien d'autre : combien de fois il
# trouve le meilleur coup, et combien de gaffes par partie. La perte moyenne
# n'est plus une cible, elle en decoule.
#
# IL N'Y A PAS QUE LES GAFFES (ta troisieme remarque : "il y a des imprecisions,
# des erreurs et tout aussi"). Tu as raison, et c'etait le defaut de mon modele :
# il ne connaissait que deux etats, "coup correct" ou "gaffe". Or ton rapport de
# fin de partie, lui, compte QUATRE choses, avec les seuils de annotations.py,
# en POINTS DE CHANCES DE GAGNER et non en centiemes de pion :
#
#     moins de  5 points perdus  ->  bon coup (ou excellent, ou le meilleur)
#     moins de 10 points         ->  IMPRECISION  (?!)
#     moins de 20 points         ->  ERREUR       (?)
#     20 points et plus          ->  GAFFE        (??)
#
# Le bot vise donc maintenant les trois taux separement, dans la meme unite que
# le rapport. Tu peux le VERIFIER toi-meme : finis une partie, ouvre le rapport,
# et compte. C'est fait pour tomber juste.
#
#   elo    imprecisions   erreurs   gaffes    (par partie de 40 coups)
#   100        10,4         8,0       6,0
#   300         9,6         6,4       4,2
#   500         8,4         5,2       2,9
#   700         7,2         4,0       1,9
#   900         6,0         3,0       1,2
#   1000        5,4         2,6       1,0
#   1200        4,6         1,9       0,7
#   1320        3,8         1,6       0,5
#
# SI CA NE TE VA TOUJOURS PAS, tu n'as pas besoin de moi : mets
# "taux_de_gaffe" dans config.json. Il multiplie les TROIS taux a la fois :
# 1.0 = ce tableau, 0.5 = deux fois moins de fautes, 2.0 = deux fois plus.
#
# AUCUNE FONCTION SUPPRIMEE : engine.py garde _elo_vers_skill et
# _elo_vers_profondeur, qui servent toujours.

import math
import random

# Sous ce classement, Stockfish refuse UCI_Elo : c'est nous qui prenons la main.
SEUIL_MOTEUR = 1320

# (elo, sigma des coups ORDINAIRES, probabilite de gaffe par coup)
#
# Les sigma ont ete calcules par dichotomie pour atteindre le taux de "meilleur
# coup" du tableau ci-dessus, sur un profil de position realiste. Ils ne portent
# QUE sur les coups corrects : les gaffes ont leur propre tirage.
# (elo, largeur du choix parmi les BONS coups, imprecisions, erreurs, gaffes)
#
# La colonne des gaffes est celle que tu as validee le 31/08 ("divise les gaffes
# par deux et c'est bien"). Les deux autres colonnes ont ete ajoutees ensuite,
# a ta remarque suivante : il manquait les imprecisions et les erreurs.
_COURBE = [
    (100, 3.5, 0.260, 0.200, 0.1500),
    (300, 3.0, 0.240, 0.160, 0.1050),
    (500, 2.5, 0.210, 0.130, 0.0725),
    (700, 2.1, 0.180, 0.100, 0.0475),
    (900, 1.7, 0.150, 0.075, 0.0310),
    (1100, 1.4, 0.120, 0.055, 0.0210),
    (1320, 1.1, 0.095, 0.040, 0.0135),
]

# LES MEMES SEUILS QUE annotations.py, en points de chances de gagner. C'est ce
# qui fait que le bot produit exactement ce que le rapport annonce.
#
# V7.2 (03/09) : passes aux seuils OFFICIELS DE LICHESS (10 / 20 / 30) en meme
# temps que annotations.py. Les deux DOIVENT bouger ensemble : si le bot visait
# encore 5/10/20 pendant que le rapport compte en 10/20/30, ses "gaffes"
# s'afficheraient comme de simples erreurs et le tableau que tu as valide ne
# voudrait plus rien dire. Un test verifie que les deux echelles coincident.
#
# CE QUE CA CHANGE POUR LE BOT : il ne se trompe pas plus souvent, mais quand
# il gaffe, la gaffe est plus franche - il faut maintenant perdre 30 points de
# chances de gagner pour que ca en soit une. C'est la definition de lichess.
#
# Ces valeurs sont recopiees plutot qu'importees parce que annotations.py a
# besoin de pygame, et que le moteur ne doit dependre de rien d'affichable.
SEUIL_IMPRECISION = 10.0
SEUIL_ERREUR = 20.0
SEUIL_GAFFE_POINTS = 30.0

# Dans une categorie, il prefere le haut du panier : une erreur a 11 points
# plutot qu'a 19, une gaffe de cavalier plutot que de dame.
SIGMA_DANS_LA_CATEGORIE = 4.0

# Conserve pour separer() : l'ancien seuil, en centiemes de pion.
SEUIL_GAFFE = 250
SIGMA_GAFFE = 600.0

# Conserve : c'etait la largeur du mode "attentif" de la version precedente.
# Elle n'est plus utilisee par choisir(), mais rien n'est supprime.
SIGMA_ATTENTIF = 25.0

# Combien de coups on demande a Stockfish de classer. Plus on joue faible, plus
# il en faut : c'est parmi eux qu'on ira chercher la betise.
#
# PREMIERE VERSION TROP TIMIDE (mesuree) : avec 12 coups classes, la perte
# moyenne a 100 Elo plafonnait a 62 centiemes de pion - parce que les 12
# MEILLEURS coups d'une position sont tous corrects. Les vraies gaffes, celles
# qui laissent une piece en prise, sont classees 20e ou 30e. Il faut donc
# demander PRESQUE TOUS les coups legaux au niveau debutant (une position de
# milieu de partie en compte 30 a 40).
_MULTIPV = [
    (300, 48),
    (600, 40),
    (900, 26),
    (1100, 16),
    (1320, 8),
]

# Ce que "mat" vaut, en centiemes de pion, pour pouvoir comparer les coups.
VALEUR_MAT = 10000


def doit_brider(elo):
    """Vrai si c'est a nous de choisir le coup (Stockfish ne sait pas si bas)."""
    try:
        return int(elo) < SEUIL_MOTEUR
    except (TypeError, ValueError):
        return False


def _interpoler(elo, colonne):
    """Lit la courbe a ce classement, en interpolant entre deux paliers."""
    try:
        elo = float(elo)
    except (TypeError, ValueError):
        return float(_COURBE[-1][colonne])
    if elo <= _COURBE[0][0]:
        return float(_COURBE[0][colonne])
    if elo >= _COURBE[-1][0]:
        return float(_COURBE[-1][colonne])
    for gauche, droite in zip(_COURBE, _COURBE[1:]):
        if gauche[0] <= elo <= droite[0]:
            part = (elo - gauche[0]) / float(droite[0] - gauche[0])
            return gauche[colonne] + part * (droite[colonne] - gauche[colonne])
    return float(_COURBE[-1][colonne])


def sigma(elo):
    """Largeur de l'erreur quand il est DISTRAIT, en centiemes de pion."""
    return _interpoler(elo, 1)


def taux_imprecision(elo):
    """Probabilite que ce coup-ci soit une IMPRECISION (?!)."""
    return max(0.0, min(0.5, _interpoler(elo, 2) * _reglage_du_joueur()))


def taux_erreur(elo):
    """Probabilite que ce coup-ci soit une ERREUR (?)."""
    return max(0.0, min(0.4, _interpoler(elo, 3) * _reglage_du_joueur()))


def taux_de_gaffe(elo):
    """Probabilite que ce coup-ci soit une GAFFE (??).

    Multipliee par "taux_de_gaffe" de config.json : c'est le bouton a tourner
    si le bot te parait trop (ou pas assez) etourdi, sans toucher au code.
    """
    return max(0.0, min(0.3, _interpoler(elo, 4) * _reglage_du_joueur()))


def taux_de_bon_coup(elo):
    """Probabilite qu'il joue simplement un bon coup. Le reste, forcement."""
    return max(0.0, 1.0 - taux_imprecision(elo) - taux_erreur(elo)
               - taux_de_gaffe(elo))


def lucidite(elo):
    """Probabilite qu'il ne fasse AUCUNE faute a ce coup-ci."""
    return taux_de_bon_coup(elo)


def fautes_par_partie(elo, coups=40):
    """(imprecisions, erreurs, gaffes) attendues sur une partie. Pour le journal."""
    return (taux_imprecision(elo) * coups, taux_erreur(elo) * coups,
            taux_de_gaffe(elo) * coups)


_REGLAGE = None


def _reglage_du_joueur():
    """Lit "taux_de_gaffe" dans config.json. 1.0 par defaut."""
    global _REGLAGE
    if _REGLAGE is not None:
        return _REGLAGE
    _REGLAGE = 1.0
    try:
        import json
        import os
        from asset_manager import dossier_ecriture
        with open(os.path.join(dossier_ecriture(), "config.json"),
                  encoding="utf-8") as f:
            valeur = json.load(f).get("taux_de_gaffe", 1.0)
        _REGLAGE = max(0.0, min(4.0, float(valeur)))
    except Exception:
        _REGLAGE = 1.0
    return _REGLAGE


def oublier_le_reglage():
    """Relit config.json au prochain coup (sert aux tests)."""
    global _REGLAGE
    _REGLAGE = None


# PROFONDEUR DU CLASSEMENT - CORRIGE LE 01/09, ET C'ETAIT MA FAUTE.
#
# TA REMARQUE : "l'IA en jeu est bridee en fonction de l'Elo, mais les bots a
# 1000 Elo ont peut-etre 400 la".
#
# TU AVAIS RAISON, ET VOILA L'ERREUR. Ce fichier repose sur UN principe, ecrit
# tout en haut : "on arrete de demander a Stockfish d'etre mauvais ; il CLASSE
# les coups honnetement, et c'est NOUS qui choisissons plus ou moins mal."
#
# Sauf que j'ai garde la profondeur basse de l'ANCIENNE methode, celle que je
# venais justement de declarer cassee. Resultat : DEUX affaiblissements empiles
# au lieu d'un.
#
#   A 941 Elo (ton reglage), cette fonction renvoyait 3.
#   A profondeur 3, Stockfish ne voit AUCUNE tactique en deux coups.
#   Donc quand mon modele decide "ce coup-ci, il joue bien" - ce qui arrive
#   77 % du temps a 941 - le coup qu'il prend est bon SELON UNE RECHERCHE A
#   PROFONDEUR 3. Il peut laisser une tour en prise en croyant bien jouer.
#
# Autrement dit : les taux de gaffes que tu as valides etaient respectes, mais
# les 77 % de "bons coups" n'etaient pas bons du tout. D'ou 400 joue pour 1000
# regle.
#
# LA REGLE MAINTENANT : le classement doit etre VRAI. La faiblesse ne vient que
# du tirage de categorie, qui est mesurable et que tu peux verifier dans ton
# rapport de fin de partie. Un seul bouton, pas deux qui se marchent dessus.
#
# POURQUOI PAS 22 PARTOUT : parce qu'il reste un peu d'aveuglement humain a
# garder. Un joueur a 300 Elo ne rate pas seulement les coups qu'on lui fait
# rater : il a aussi un horizon court. Mais entre 10 et 13 le classement est
# deja juste a plus de 2400 Elo - largement assez pour que "le 3e meilleur
# coup" soit vraiment le 3e meilleur. En dessous de 10, il ne l'est plus.
PROFONDEUR_MINIMALE = 10


def profondeur(elo):
    """Jusqu'ou Stockfish cherche pour CLASSER les coups.

    Ce n'est PAS le bouton de la force : le bouton de la force, c'est le tirage
    de categorie (imprecision / erreur / gaffe). Ici on veut seulement que le
    classement soit fiable, sinon on ne sait plus ce qu'on choisit.
    """
    try:
        elo = int(elo)
    except (TypeError, ValueError):
        return 12
    if elo <= 600:
        return PROFONDEUR_MINIMALE          # 10
    if elo <= 900:
        return 11
    if elo <= 1100:
        return 12
    return 13


def profondeur_ancienne(elo):
    """L'ancienne profondeur (1 a 6). CONSERVEE, RIEN N'EST SUPPRIME.

    Elle n'est plus utilisee par le jeu : elle rendait le classement faux (voir
    le commentaire ci-dessus). Elle reste ici pour les tests de non-regression
    et pour pouvoir comparer les deux comportements.
    """
    try:
        elo = int(elo)
    except (TypeError, ValueError):
        return 6
    if elo <= 300:
        return 1
    if elo <= 600:
        return 2
    if elo <= 900:
        return 3
    if elo <= 1100:
        return 4
    return 6


def multipv(elo):
    """Combien de coups on demande a classer."""
    try:
        elo = int(elo)
    except (TypeError, ValueError):
        return 6
    for seuil, combien in _MULTIPV:
        if elo <= seuil:
            return combien
    return _MULTIPV[-1][1]


def chances_de_gagner(centipions):
    """Centiemes de pion -> chances de gagner, de 0 a 100.

    LA MEME FORMULE QUE annotations.py (celle de lichess). Elle est recopiee
    plutot qu'importee parce que annotations.py a besoin de pygame, et que le
    moteur ne doit pas dependre de l'affichage. Un test verifie que les deux
    donnent exactement le meme resultat.
    """
    valeur = max(-2000.0, min(2000.0, float(centipions)))
    return 50.0 + 50.0 * (2.0 / (1.0 + math.exp(-0.00368208 * valeur)) - 1.0)


def perte_en_points(meilleure_note, note_du_coup):
    """Ce que le coup coute, EN POINTS DE CHANCES DE GAGNER.

    C'est l'unite du rapport de fin de partie. Un pion perdu quand on est deja
    a +8 ne coute presque rien ; le meme pion a l'egalite coute enormement.
    """
    return max(0.0, chances_de_gagner(meilleure_note)
               - chances_de_gagner(note_du_coup))


def categorie(perte):
    """'bon', 'imprecision', 'erreur' ou 'gaffe' - seuils de annotations.py."""
    if perte < SEUIL_IMPRECISION:
        return "bon"
    if perte < SEUIL_ERREUR:
        return "imprecision"
    if perte < SEUIL_GAFFE_POINTS:
        return "erreur"
    return "gaffe"


ORDRE = ("bon", "imprecision", "erreur", "gaffe")


def repartir(coups):
    """Range les coups par categorie : {'bon': [...], 'gaffe': [...], ...}.

    Chaque coup recoit aussi sa perte en points, sous la cle 'perte'.
    """
    paniers = dict((nom, []) for nom in ORDRE)
    if not coups:
        return paniers
    meilleure = max(note(c) for c in coups)
    for coup in coups:
        perte = perte_en_points(meilleure, note(coup))
        panier = dict(coup)
        panier["perte"] = perte
        paniers[categorie(perte)].append(panier)
    return paniers


def note(coup):
    """La note d'un coup, en centiemes de pion, du point de vue du joueur.

    Un coup porte soit "cp" (centiemes de pion), soit "mat" (nombre de coups).
    On ramene les deux a la meme echelle pour pouvoir les comparer.
    """
    mat = coup.get("mat")
    if mat is not None:
        try:
            mat = int(mat)
        except (TypeError, ValueError):
            mat = 0
        if mat > 0:
            return VALEUR_MAT - min(abs(mat), 50) * 10
        if mat < 0:
            return -VALEUR_MAT + min(abs(mat), 50) * 10
        return VALEUR_MAT
    try:
        return float(coup.get("cp") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def poids(coups, elo, attentif=True):
    """Le poids de chaque coup dans le tirage au sort. Meme ordre que 'coups'.

    Le meilleur coup a toujours le poids le plus fort ; les autres decroissent
    selon ce qu'ils coutent. 'attentif=False' est le tirage de la GAFFE : il
    prefere alors les betises les moins couteuses.
    """
    if not coups:
        return []
    notes = [note(c) for c in coups]
    meilleure = max(notes)
    largeur = max(1.0, float(sigma(elo))) if attentif else SIGMA_GAFFE
    resultat = []
    for valeur in notes:
        perte = max(0.0, meilleure - valeur)
        # exp(-700) deborde en zero tout seul : pas de garde-fou necessaire,
        # mais on borne pour rester lisible dans les journaux.
        resultat.append(math.exp(-min(perte / largeur, 60.0)))
    return resultat


def choisir(coups, elo, hasard=None):
    """Choisit un coup parmi ceux classes par Stockfish. Renvoie le dictionnaire.

    LE PRINCIPE : on tire d'abord la QUALITE du coup - bon, imprecision, erreur
    ou gaffe - avec les taux du niveau vise, puis on choisit un coup dans cette
    categorie. C'est ce qui fait que le rapport de fin de partie annonce bien ce
    que le niveau promet.

    'coups' : [{"coup": "e2e4", "cp": 34, "mat": None}, ...].
    Renvoie None si la liste est vide.
    """
    coups = [c for c in (coups or []) if c and c.get("coup")]
    if not coups:
        return None
    if len(coups) == 1:
        return coups[0]
    tirage = hasard or random

    paniers = repartir(coups)
    voulue = _tirer_la_categorie(elo, tirage)
    candidats = _panier_le_plus_proche(paniers, voulue)
    if not candidats:
        return coups[0]

    # Dans la categorie, il prefere le haut du panier : une erreur a 11 points
    # plutot qu'a 19. Parmi les bons coups, la largeur depend du niveau.
    largeur = (max(0.2, float(_interpoler(elo, 1))) if voulue == "bon"
               else SIGMA_DANS_LA_CATEGORIE)
    meilleure = min(c["perte"] for c in candidats)
    valeurs = [math.exp(-min((c["perte"] - meilleure) / largeur, 60.0))
               for c in candidats]
    total = sum(valeurs)
    if total <= 0:
        return candidats[0]
    seuil = tirage.random() * total
    cumul = 0.0
    for coup, valeur in zip(candidats, valeurs):
        cumul += valeur
        if cumul >= seuil:
            return coup
    return candidats[-1]


def _tirer_la_categorie(elo, tirage):
    """Quelle qualite de coup va-t-il jouer ? Tire une fois, par coup."""
    de = tirage.random()
    seuil = taux_de_gaffe(elo)
    if de < seuil:
        return "gaffe"
    seuil += taux_erreur(elo)
    if de < seuil:
        return "erreur"
    seuil += taux_imprecision(elo)
    if de < seuil:
        return "imprecision"
    return "bon"


def _panier_le_plus_proche(paniers, voulue):
    """Le panier demande, ou le plus proche s'il est vide.

    ON DESCEND D'ABORD VERS LES BONS COUPS : dans une position calme, aucune
    gaffe n'est possible, et il vaut mieux jouer mieux que prevu que d'aller
    chercher une betise qui n'existe pas.
    """
    if paniers.get(voulue):
        return paniers[voulue]
    depart = ORDRE.index(voulue)
    for pas in range(1, len(ORDRE)):
        for indice in (depart - pas, depart + pas):
            if 0 <= indice < len(ORDRE) and paniers.get(ORDRE[indice]):
                return paniers[ORDRE[indice]]
    return []


def gaffes_par_partie(elo, coups_par_partie=40):
    """Combien de fois il lachera une piece sur une partie. Pour le journal."""
    return taux_de_gaffe(elo) * coups_par_partie


def separer(coups):
    """(coups corrects, gaffes) : au-dela de SEUIL_GAFFE c'est une piece lachee."""
    if not coups:
        return [], []
    meilleure = max(note(c) for c in coups)
    corrects, mauvais = [], []
    for coup in coups:
        if meilleure - note(coup) >= SEUIL_GAFFE:
            mauvais.append(coup)
        else:
            corrects.append(coup)
    return corrects, mauvais


def perte_moyenne(coups, elo, tirages=400, hasard=None):
    """Ce que ce niveau perd en moyenne sur cette position, en centiemes de pion.

    Sert aux tests et au reglage : c'est la mesure qui dit si le bot joue
    vraiment au niveau demande.
    """
    coups = [c for c in (coups or []) if c and c.get("coup")]
    if not coups:
        return 0.0
    tirage = hasard or random
    meilleure = max(note(c) for c in coups)
    total = 0.0
    for _ in range(max(1, tirages)):
        choix = choisir(coups, elo, tirage)
        total += max(0.0, meilleure - note(choix))
    return total / float(max(1, tirages))


def description(elo):
    """Une phrase pour le journal : ce que le bot va faire a ce niveau."""
    if not doit_brider(elo):
        return "Stockfish se bride lui-même (UCI_Elo %d)" % int(elo)
    impr, err, gaf = fautes_par_partie(elo)
    return ("choix maison : profondeur %d, %d coups classes, par partie "
            "environ %.1f imprécision(s), %.1f erreur(s), %.1f gaffe(s)"
            % (profondeur(elo), multipv(elo), impr, err, gaf))
