# annotations.py - V7.1 : NOUVEAU FICHIER
#
# Les pastilles de coup, comme sur chess.com : !!, !, meilleur coup, bon coup,
# imprecision (?!), erreur (?) et gaffe (??).
#
# POURQUOI CE FICHIER (ta remarque : "il devrait y avoir les logo a chaque coup
# avec ! !? ?? etc") :
#   - La V7 calculait bien une annotation dans move_history.detect_brilliant_blunder,
#     mais elle n'etait ecrite QUE dans le fichier PGN exporte. Rien n'apparaissait
#     a l'ecran.
#   - Le classement se faisait sur la difference brute d'evaluation en pions, ce
#     qui est trompeur : perdre 1 pion quand on a +8 n'est pas une gaffe, alors
#     que le perdre a egalite en est une. On raisonne maintenant en CHANCES DE
#     GAGNER, comme lichess et chess.com.
#
# LE DESSIN NE DEPEND D'AUCUNE POLICE SPECIALE : la coche et le rond sont traces
# au trait. Seuls "!!", "!", "?!", "?" et "??" sont du texte, et ces caracteres
# existent dans toutes les polices.
#
# AUCUNE FONCTION SUPPRIMEE : ce fichier n'existait pas avant.

import math

import chess
import pygame

import design

VALEUR_PIECE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

# Ordre du plus beau au plus vilain. Chaque entree :
#   cle : (libelle affiche, couleur de la pastille, glyphe)
# glyphe "coche" et "rond" sont traces au trait, le reste est du texte.
# V7.2 : "meilleur" et "excellent" avaient la MEME coche et deux verts qu'on ne
# distinguait pas a l'oeil. Le meilleur coup a maintenant son etoile, et les
# trois verts sont franchement differents. C'etait ton "les pastilles excellent,
# bon coup, etc. ne s'affichent pas correctement".
# V7.2 : TA LISTE DEFINITIVE, dix pastilles. Il en manquait deux :
#   THEORIQUE : le coup est dans le livre d'ouvertures. Il n'est ni bon ni
#       mauvais - le joueur n'a rien trouve, il a recite. Le noter "excellent"
#       n'aurait aucun sens. Icone : un livre. Voir ouvertures.py.
#   MANQUE : le coup laisse filer une position GAGNANTE. Ce n'est pas la meme
#       chose qu'une erreur ordinaire : la faute n'est pas d'avoir mal joue,
#       c'est de ne pas avoir vu ce qui gagnait.
PASTILLES = {
    "brillant":   ("Brillant",       (27, 172, 166), "!!"),
    "excellent":  ("Excellent",      (149, 191, 96), "coche"),
    "theorique":  ("Theorique",      (166, 138, 100), "livre"),
    "meilleur":   ("Meilleur",       (106, 173, 48), "etoile"),
    "tres_bon":   ("Très bien",      (92, 155, 214), "!"),
    "bon":        ("Bon",            (168, 173, 148), "rond"),
    "imprecision": ("Imprécision",   (247, 198, 49), "?!"),
    "erreur":     ("Erreur",         (229, 143, 42), "?"),
    "manque":     ("Manque",         (236, 96, 118), "X"),
    "gaffe":      ("Gaffe",          (214, 40, 40), "??"),
}
# 25/10 (t100, pastilles peu lisibles) : Gaffe d'un rouge plus franc, Manque
# plus rose et plus clair (signe sombre a 5,8 de contraste) : on ne les confond plus.

# L'ordre que tu m'as donne.
# V7.2 (03/09) - MEILLEUR PASSE DEVANT EXCELLENT.
#
# Ta demande du 31/08 disait l'inverse : "Excellent passe au-dessus de Meilleur,
# et si un coup est les deux, c'est Excellent qui s'affiche". Ta demande du
# 03/09 : "meilleur coup est au-dessus d'Excellent - meme reglage, juste
# inverse". Les deux places sont donc echangees, et RIEN D'AUTRE ne bouge :
# Brillant reste au-dessus des deux, Theorique reste ou il etait.
# V8 (04/09) : l'echelle officielle, du plus rare au plus grave. "Tres bien"
# (le grand coup, "il n'y avait que ca") remonte au-dessus de Meilleur, et
# Excellent redescend sous lui : c'est l'ordre de chess.com, et c'est ce qui
# empeche un coup du moteur de s'afficher "Excellent".
ORDRE = ["brillant", "tres_bon", "meilleur", "theorique", "excellent", "bon",
         "imprecision", "erreur", "manque", "gaffe"]

# ---------------------------------------------------------------------------
# LES SEUILS OFFICIELS DE LICHESS (ta demande du 03/09 : "reglage officiel des
# pastilles de lichess ou chess.com").
#
# CHESS.COM NE PUBLIE PAS LES SIENS - leur systeme est proprietaire, et tout ce
# qu'on trouve en ligne est de la retro-ingenierie. LICHESS, LUI, EST OUVERT :
# les seuils sont dans son code, modules/tree/src/main/Advice.scala :
#
#       .3 -> Blunder        (30 points de chances de gagner perdus)
#       .2 -> Mistake        (20 points)
#       .1 -> Inaccuracy     (10 points)
#
# En dessous de 10 points, lichess ne met AUCUNE marque : le coup est bon, et
# c'est tout.
#
# CE QUE CA CHANGE POUR TOI : mes seuils etaient DEUX FOIS plus severes
# (5 / 10 / 20). Un coup qui perdait 12 points etait marque "erreur" ici et
# "imprecision" sur lichess. Tu vas donc voir nettement moins de fautes, et
# celles qui restent voudront dire quelque chose.
#
# LA FORMULE DES CHANCES DE GAGNER ET CELLE DE LA PRECISION etaient DEJA celles
# de lichess (constantes 0,00368208 et 103,1668 / 0,04354) : elles ne changent
# pas. Seuls les seuils bougent.
#
# 17/10 - CORRECTION (comparaison avec chess.com sur ta partie contre
# dragondu5) : la lecture ci-dessus etait FAUSSE. Les chances de lichess vont
# de -1 a +1 ; ici elles vont de 0 a 100 : 0,1 de lichess = 5 points ici, pas
# 10. Les vrais seuils de lichess sont donc 5 / 10 / 15, et ceux que chess.com
# publie (« points attendus » perdus : 0,05 / 0,10 / 0,20) sont 5 / 10 / 20.
# On prend ceux de chess.com, puisque c'est a lui que tu compares.
#   perte < 2   : Excellent (pas le coup du moteur, mais presque)
#   perte < 5   : Bon
#   perte < 10  : Imprecision
#   perte < 20  : Erreur
#   au-dela     : Gaffe
SEUIL_IMPRECISION = 5.0         # chess.com : Inaccuracy (0,05)
SEUIL_ERREUR = 10.0             # chess.com : Mistake (0,10)
SEUIL_GAFFE = 20.0              # chess.com : Blunder (0,20)

# Un coup MANQUE : on avait une position gagnante et on l'a laissee filer.
# C'est le "Miss" de chess.com, que lichess n'a pas. Il se declenche au niveau
# d'une ERREUR, pas d'une imprecision : laisser filer un gain en perdant dix
# points, ca arrive a tout le monde.
CHANCES_GAGNANTES = 70.0        # au-dela, la position est consideree gagnante
PERTE_MANQUE = SEUIL_ERREUR     # et il faut au moins perdre ca pour la gacher

# EXCELLENT PASSE AU-DESSUS DE MEILLEUR (ta regle du 31/08 : "Excellent passe
# au-dessus de Meilleur, oui mais Excellent peut etre Meilleur aussi. Si c'est
# le cas Excellent s'affiche").
#
# Ce qui distingue les deux, c'est la DIFFICULTE. Jouer le meilleur coup quand
# trois autres font aussi bien, c'est normal : c'est "Meilleur". Le jouer quand
# c'etait LE SEUL qui tenait, c'est une trouvaille : c'est "Excellent".
# On mesure ca avec l'ecart entre le meilleur coup et le DEUXIEME meilleur.
# Mesure corrigee (ta remarque : "il y a beaucoup d'Excellent quand meme").
# MON CRITERE MESURAIT L'ECART, PAS LA DIFFICULTE. Or l'ecart avec le deuxieme
# coup est ENORME sur des coups qui n'ont rien de brillant :
#   - reprendre une piece qu'on vient de te prendre : reprendre gagne 900
#     centiemes, ne pas reprendre les perd. Ecart maximal, coup evident.
#   - sortir d'un echec quand une seule case est libre : c'est force.
#   - une position ou il ne reste que deux coups legaux.
# Ces trois cas donnaient "Excellent" a des coups que n'importe qui trouve.
# On les exclut, et on releve le seuil.
ECART_SEUL_COUP = 25.0          # points de chances d'avance sur le deuxieme
PERTE_QUASI_MEILLEUR = 2.0      # un coup a moins de 2 points compte comme trouve
COUPS_LEGAUX_MINIMUM = 4        # sous ce nombre, le coup n'est pas une trouvaille

# BRILLANT : tu le veux rare, "entre 0,5 et 1 % des coups". L'ancien critere
# etait trop large - "le meilleur coup, et c'est un sacrifice" arrive souvent
# quand on est deja en train de gagner et qu'on echange bien. Trois conditions
# de plus, qui correspondent a ce qu'on appelle vraiment un coup brillant :
#   - la partie n'etait PAS deja pliee (sinon tout sacrifice gagne) ;
#   - le sacrifice ne perd pas la partie (on reste au moins jouable) ;
#   - c'est bien LE coup a jouer, pas un parmi d'autres.
BRILLANT_DEJA_GAGNE = 92.0      # au-dela, la partie etait pliee : rien de brillant
BRILLANT_MINIMUM = 45.0         # en dessous, le sacrifice ne tient pas debout


# ---------------------------------------------------------------- classement

def chances_de_gagner(evaluation):
    """Evaluation en pions -> chances de gagner des Blancs, de 0 a 100.

    Meme formule que lichess. C'est elle qui rend le classement juste : entre
    +8 et +7 il ne se passe presque rien, entre +0.2 et -0.8 il se passe tout.
    """
    if evaluation is None:
        return None
    # 17/10 : bornee a +/- 10 pions, exactement comme lichess.
    centipions = max(-1000.0, min(1000.0, float(evaluation) * 100.0))
    return 50.0 + 50.0 * (2.0 / (1.0 + math.exp(-0.00368208 * centipions)) - 1.0)


def est_un_sacrifice(plateau_avant, coup):
    """Le coup abandonne-t-il vraiment du materiel ? (coups brillants)

    SickChess : la piece doit etre REELLEMENT en prise apres le coup - soit
    elle n'est pas defendue, soit l'adversaire peut la prendre avec une piece
    nettement moins chere. Avant, une piece simplement attaquee comptait comme
    un sacrifice, meme defendue par un pion (Cc3 dans le Fegatello etait note
    "Brillant").
    """
    if plateau_avant is None or coup is None:
        return False
    try:
        deplacee = plateau_avant.piece_at(coup.from_square)
        if deplacee is None:
            return False
        prise = plateau_avant.piece_at(coup.to_square)
        gain = VALEUR_PIECE.get(prise.piece_type, 0) if prise else 0
        risque = VALEUR_PIECE.get(deplacee.piece_type, 0)
        if coup.promotion:
            risque = VALEUR_PIECE.get(coup.promotion, 0)
        if risque - gain < 2:
            return False
        apres = plateau_avant.copy(stack=False)
        apres.push(coup)
        attaquants = apres.attackers(not deplacee.color, coup.to_square)
        if not attaquants:
            return False
        if not apres.attackers(deplacee.color, coup.to_square):
            return True                     # en prise, et personne ne defend
        moins_chere = min(VALEUR_PIECE.get(apres.piece_at(case).piece_type, 0)
                          or 100 for case in attaquants)   # le roi : 100
        return risque - moins_chere >= 2
    except Exception:
        return False


def _vraiment_brillant(chances_avant, chances_apres):
    """Un sacrifice merite-t-il vraiment l'etoile ? Voir les seuils plus haut.

    Sans les chances (analyse incomplete), on garde l'ancien comportement :
    mieux vaut une pastille de trop qu'une pastille perdue.
    """
    if chances_avant is None or chances_apres is None:
        return True
    if chances_avant >= BRILLANT_DEJA_GAGNE:
        return False            # la partie etait deja gagnee
    return chances_apres >= BRILLANT_MINIMUM


def coup_evident(plateau_avant, coup, dernier_coup=None):
    """Ce coup se trouve-t-il tout seul ? Alors ce n'est pas une trouvaille.

    Trois cas, et ce sont EXACTEMENT ceux qui donnaient trop d'"Excellent" :
      - il ne reste presque aucun coup legal : le choix se fait tout seul ;
      - on est en echec : sortir d'un echec n'a rien d'une decouverte ;
      - on reprend sur la case ou l'adversaire vient de prendre : tout joueur
        reprend, c'est le reflexe le plus repandu du jeu.
    """
    if plateau_avant is None or coup is None:
        return False
    try:
        if plateau_avant.is_check():
            return True
        legaux = 0
        for _ in plateau_avant.legal_moves:
            legaux += 1
            if legaux >= COUPS_LEGAUX_MINIMUM:
                break
        if legaux < COUPS_LEGAUX_MINIMUM:
            return True
        if dernier_coup is not None \
                and getattr(dernier_coup, "to_square", None) == coup.to_square \
                and plateau_avant.piece_at(coup.to_square) is not None:
            return True            # simple reprise
    except Exception:
        return False
    return False


# ---------------------------------------------------------------------------
# SICKCHESS 17/10 - LE MATERIEL COMPTE AUSSI (remarque de Julien : "le bot a
# donne une dame, ca a compte comme une imprecision").
#
# Les chances de gagner (methode lichess) ecrasent les fautes quand la position
# est deja tres desequilibree : de 15 % a 3 %, donner sa dame ne "coute" que
# 12 points, donc une imprecision. Pour un jeu de competition, ce n'est pas ce
# qu'on attend. On regarde donc AUSSI la perte en pions (evaluation bornee a
# 15) : la pastille prend la plus severe des deux lectures.
#   perte >= 1 pion  -> au moins Imprecision
#   perte >= 2 pions -> au moins Erreur
#   perte >= 4 pions -> Gaffe
# Exception : si la position reste ECRASANTE apres le coup (+5 ou plus pour le
# joueur), on ne monte pas au-dela d'Imprecision : rendre un peu de son
# avance quand on gagne largement n'est pas une gaffe.
#
# 17/10 - CORRECTION : cette regle faisait des GAFFES la ou chess.com voit des
# erreurs (10. h3 contre dragondu5 : la partie etait deja perdue, chess.com dit
# « Erreur », SickChess disait « Gaffe »). Le materiel ne fait donc plus monter
# qu'a Erreur au maximum ; seule une vraie chute des chances fait une Gaffe.
PIONS_IMPRECISION = 1.0
PIONS_ERREUR = 3.0
PIONS_GAFFE = 999.0             # jamais : la gaffe vient des chances seulement
TOUJOURS_ECRASANT = 5.0
GRAVITE = {"imprecision": 1, "erreur": 2, "manque": 3, "gaffe": 4}


def classer(perte, est_le_meilleur=False, sacrifice=False,
            theorique=False, chances_avant=None, chances_apres=None,
            ecart_second=None, evident=False, meilleur_connu=None,
            perte_pions=None, apres_pions=None):
    """Pastille d'un coup : chances de gagner ET materiel (voir plus haut)."""
    note = _classer_chances(perte, est_le_meilleur, sacrifice, theorique,
                            chances_avant, chances_apres, ecart_second,
                            evident, meilleur_connu)
    if note is None or perte_pions is None or note == "theorique" \
            or est_le_meilleur:
        return note
    if perte_pions >= PIONS_GAFFE:
        selon_pions = "gaffe"
    elif perte_pions >= PIONS_ERREUR:
        selon_pions = "erreur"
    elif perte_pions >= PIONS_IMPRECISION:
        selon_pions = "imprecision"
    else:
        return note
    if apres_pions is not None and apres_pions >= TOUJOURS_ECRASANT:
        selon_pions = "imprecision"
    if GRAVITE.get(selon_pions, 0) > GRAVITE.get(note, 0):
        return selon_pions
    return note


def _classer_chances(perte, est_le_meilleur=False, sacrifice=False,
                     theorique=False, chances_avant=None, chances_apres=None,
                     ecart_second=None, evident=False, meilleur_connu=None):
    """Nom de la pastille pour un coup. perte = points de chances perdus.

    V7.2 : deux entrees de plus, toutes optionnelles, donc les anciens appels
    continuent de marcher a l'identique.
      theorique       le coup est dans le livre d'ouvertures (ouvertures.py)
      chances_avant   chances de gagner AVANT le coup, de 0 a 100
      chances_apres   chances de gagner APRES le coup
      ecart_second    de combien le meilleur coup devancait le deuxieme, en
                      points de chances. Grand ecart = il n'y avait qu'un coup.
      evident         le coup se trouvait tout seul (reprise, echec, position
                      forcee) : il ne peut alors pas etre un "grand coup".
      meilleur_connu  sait-on quel etait le coup du moteur ? Sans lui, pas
                      d'Excellent : "presque aussi bien que le meilleur" n'a
                      aucun sens quand on ignore le meilleur. Laisse a None,
                      on le deduit de est_le_meilleur pour ne casser aucun
                      appel ecrit avant ce parametre.
    Les deux dernieres servent a reperer un coup MANQUE : on etait en train de
    gagner, et on a laisse filer.
    """
    if perte is None:
        return None
    if meilleur_connu is None:
        # Compatibilite : les appels ecrits avant ce parametre passaient deja
        # est_le_meilleur, qui suppose qu'on connait le coup du moteur.
        meilleur_connu = bool(est_le_meilleur) or ecart_second is not None
    # LE LIVRE PASSE AVANT TOUT. Reciter la Najdorf n'est ni un exploit ni une
    # faute : c'est de la theorie, et ca se dit comme ca.
    # 24/10 (p30, banque de positions) : SAUF si le coup perd vraiment (une
    # Erreur ou pire) : le livre de lichess contient aussi des pieges ou un
    # camp se trompe ; l'analyse doit rester juste.
    if theorique and perte < SEUIL_ERREUR:
        return "theorique"
    # BRILLANT, exactement comme EXCELLENT (ta regle : "pareil pour brillant") :
    # il ne faut pas que ce soit le coup exact du moteur. Un sacrifice trouve a
    # deux points pres reste un sacrifice trouve - et si c'EST le meilleur coup,
    # c'est Brillant qui s'affiche, pas Meilleur.
    if sacrifice and (est_le_meilleur or perte <= PERTE_QUASI_MEILLEUR) \
            and _vraiment_brillant(chances_avant, chances_apres):
        return "brillant"
    # TRES BIEN (le "!") : IL N'Y AVAIT QU'UN COUP, et il a ete trouve.
    #
    # V8 (04/09) - TA DEMANDE : "mets les reglages officiels des tags, il y a
    # des Excellent qui devraient etre Meilleur coup".
    # Ce critere - le meilleur coup devancait largement le deuxieme - etait
    # accroche a EXCELLENT, et c'est ce qui volait la pastille Meilleur : un
    # coup pouvait etre exactement celui du moteur et s'afficher "Excellent".
    # Dans le systeme officiel, "il n'y avait que ce coup" n'est pas Excellent,
    # c'est le GRAND COUP - le "!" de chess.com. Le critere est donc remonte
    # ici, AU-DESSUS de Meilleur, et Excellent redevient ce qu'il est partout
    # ailleurs : un coup qui n'est pas celui du moteur mais qui vaut presque
    # autant. Un coup du moteur ne peut donc plus etre etiquete Excellent.
    if (ecart_second is not None and ecart_second >= ECART_SEUL_COUP
            and not evident
            and (est_le_meilleur or perte <= PERTE_QUASI_MEILLEUR)):
        return "tres_bon"
    # MEILLEUR : le coup joue est EXACTEMENT celui du moteur. C'est le "Best"
    # de chess.com, et rien ne passe devant sauf le livre, le brillant et le
    # grand coup ci-dessus.
    if est_le_meilleur:
        return "meilleur"
    # EXCELLENT : ce n'est PAS le coup du moteur, mais il n'en coute presque
    # rien. C'est la definition officielle, et elle demande de connaitre le
    # coup du moteur : sans lui, on ne peut pas dire "presque aussi bien que",
    # et on ne va pas distribuer des Excellent au hasard d'une analyse qui n'a
    # pas abouti.
    if perte <= PERTE_QUASI_MEILLEUR and meilleur_connu:
        return "excellent"
    if sacrifice and perte < 4.0:
        return "tres_bon"
    if perte < 2.0:
        return "tres_bon"
    # SOUS LE SEUIL D'IMPRECISION DE LICHESS (10 points), le coup est bon et on
    # n'en dit pas plus. C'est la que se trouvent la plupart des coups.
    if perte < SEUIL_IMPRECISION:
        return "bon"
    if perte < SEUIL_ERREUR:
        return "imprecision"
    # MANQUE : la position etait gagnante et ne l'est plus. Ce n'est pas une
    # erreur ordinaire - c'est une occasion laissee passer.
    if (chances_avant is not None and chances_apres is not None
            and perte >= PERTE_MANQUE
            and chances_avant >= CHANCES_GAGNANTES
            and chances_apres < CHANCES_GAGNANTES):
        return "manque"
    if perte < SEUIL_GAFFE:
        return "erreur"
    return "gaffe"


def libelle(cle):
    return PASTILLES[cle][0] if cle in PASTILLES else ""


def couleur(cle):
    return PASTILLES[cle][1] if cle in PASTILLES else (150, 150, 150)


# ---------------------------------------------------------------- dessin

# La couleur du coup PAS ENCORE JUGE. Volontairement terne : on doit voir d'un
# coup d'oeil que c'est une attente, pas un verdict.
COULEUR_EN_ATTENTE = (92, 92, 92)


def dessiner_pastille_en_attente(surface, centre, rayon):
    """Le rond creux d'un coup que l'analyse n'a pas encore atteint.

    V7.2 (03/09) - TA REMARQUE : "pas tous les coups dans l'historique sont
    affiches avec la pastille". C'etait vrai, et c'etait normal SANS ETRE
    LISIBLE : tant que l'analyse n'a pas fini de passer sur les deux positions
    qui encadrent un coup, on ne peut rien dire de ce coup - alors on
    n'affichait rien du tout. A l'ecran, "pas encore juge" et "rien a dire" se
    ressemblaient exactement.
    Maintenant chaque coup a sa marque : un rond creux gris tant qu'il attend,
    sa vraie pastille des que l'analyse l'a atteint.
    """
    import pygame as _pg
    rayon = max(3, int(rayon))
    _pg.draw.circle(surface, COULEUR_EN_ATTENTE,
                    (int(centre[0]), int(centre[1])), rayon, max(1, rayon // 4))


def dessiner_pastille(surface, centre, rayon, cle, police=None, fond=None):
    """Pastille ronde coloree, comme celle qui apparait sur la case d'arrivee.

    Le glyphe est trace au trait pour la coche et le rond : aucune police
    speciale n'est necessaire, donc rien ne peut manquer sur un autre PC.
    fond : la couleur derriere la pastille ; le contour prend alors la teinte
    (claire ou sombre) qui s'en detache le mieux. Sans fond : contour blanc.
    """
    if cle not in PASTILLES:
        return
    _, coul, glyphe = PASTILLES[cle]
    cx, cy = int(centre[0]), int(centre[1])
    rayon = max(7, int(rayon))

    # 25/10 (t100) : contour de 2 px au moins (1 px avant, il disparaissait).
    contour = (255, 255, 255) if fond is None else couleur_contour(fond)
    pygame.draw.circle(surface, contour, (cx, cy), rayon)
    pygame.draw.circle(surface, coul, (cx, cy), rayon - max(2, rayon // 6))

    # 24/10 (p33, lisibilite) : le symbole a un contour sombre.
    # 25/10 (t100) : il ne suffisait pas (blanc sur jaune : 1,6) et, en petit, le
    # contour empatait le signe. Le symbole est maintenant onyx sur les couleurs
    # claires, blanc sur le rouge, sans contour : 4,5 de contraste au moins
    # partout (tests/test_pastilles.py).
    _dessiner_glyphe(surface, glyphe, cx, cy, rayon, couleur_signe(cle), police)


CONTOUR_GLYPHE = (28, 26, 24)
SIGNE_SOMBRE = (20, 18, 16)        # l'onyx de design.py, a peine chaud
CONTOUR_CLAIR = design.ARDOISE[100]  # le texte principal, blanc chaud


def couleur_signe(cle):
    """Blanc ou onyx : celui qui se lit le mieux sur la couleur de la pastille."""
    coul = couleur(cle)
    return max(((255, 255, 255), SIGNE_SOMBRE), key=lambda s: design.contraste(s, coul))


def couleur_contour(fond):
    """Le contour de la pastille : clair sur fond sombre, sombre sur l'accent."""
    return max((CONTOUR_CLAIR, CONTOUR_GLYPHE), key=lambda c: design.contraste(c, fond))


def _dessiner_glyphe(surface, glyphe, cx, cy, rayon, blanc, police=None, contour=False):
    """Le symbole d'une pastille (trace au trait, ou texte) ; contour=True le
    trace un peu plus epais, en dessous, pour faire le contour sombre."""
    plus = max(1, rayon // 9) if contour else 0
    if glyphe == "coche":
        e = max(2, rayon // 4) + 2 * plus
        pygame.draw.lines(surface, blanc, False, [
            (cx - rayon * 0.45, cy),
            (cx - rayon * 0.10, cy + rayon * 0.38),
            (cx + rayon * 0.50, cy - rayon * 0.40),
        ], e)
    elif glyphe == "rond":
        pygame.draw.circle(surface, blanc, (cx, cy), max(3, int(rayon * 0.42)) + plus,
                           max(2, rayon // 5) + 2 * plus)
    elif glyphe == "livre":
        # Un petit livre ouvert : deux pages et la reliure au milieu.
        largeur = rayon * 0.62
        hauteur = rayon * 0.46
        pygame.draw.line(surface, blanc, (cx, cy - hauteur),
                         (cx, cy + hauteur), max(2, rayon // 6) + 2 * plus)
        for sens in (-1, 1):
            pygame.draw.lines(surface, blanc, False, [
                (cx + sens * largeur, cy - hauteur * 0.78),
                (cx + sens * largeur, cy + hauteur * 0.62),
                (cx, cy + hauteur),
            ], max(2, rayon // 7) + 2 * plus)
            pygame.draw.line(surface, blanc,
                             (cx + sens * largeur, cy - hauteur * 0.78),
                             (cx, cy - hauteur * 0.35), max(2, rayon // 7) + 2 * plus)
    elif glyphe == "etoile":
        # Etoile a cinq branches, tracee au trait : aucune police speciale.
        points = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            r = rayon * (0.62 if i % 2 == 0 else 0.27)
            points.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
        pygame.draw.polygon(surface, blanc, points)
        if plus:
            pygame.draw.polygon(surface, blanc, points, 2 * plus + 1)
    else:
        if police is None:
            police = _police_glyphe(max(10, int(rayon * 1.25)))
        rendu = police.render(glyphe, True, blanc)
        x, y = cx - rendu.get_width() // 2, cy - rendu.get_height() // 2
        if plus:
            for dx, dy in ((-plus, 0), (plus, 0), (0, -plus), (0, plus)):
                surface.blit(rendu, (x + dx, y + dy))
        else:
            surface.blit(rendu, (x, y))


_POLICES_GLYPHE = {}


def _police_glyphe(taille):
    """Gardee en memoire : SysFont est lent (jamais a chaque image)."""
    if taille not in _POLICES_GLYPHE:
        _POLICES_GLYPHE[taille] = pygame.font.SysFont("Arial", taille, bold=True)
    return _POLICES_GLYPHE[taille]


def dessiner_pastille_sur_case(surface, rect_case, cle, police=None,
                               rect_plateau=None):
    """Pastille posee en haut a droite de la case d'arrivee, comme chess.com.

    V7.2 : elle debordait de la case de 6 % vers la droite et vers le haut. Sur
    la colonne h et sur la rangee 8, elle sortait donc DU PLATEAU et se
    dessinait a moitie dans le decor. On la ramene a l'interieur quand on sait
    ou est le plateau (rect_plateau), sinon on la garde dans sa case.
    """
    if cle not in PASTILLES:
        return
    x, y, largeur, hauteur = rect_case
    rayon = max(8, int(largeur * 0.19))
    cx = x + largeur - rayon + rayon // 3
    cy = y + rayon - rayon // 3

    if rect_plateau is not None:
        px, py, plargeur, phauteur = rect_plateau
        cx = min(cx, px + plargeur - rayon - 1)
        cy = max(cy, py + rayon + 1)
        cx = max(cx, px + rayon + 1)
        cy = min(cy, py + phauteur - rayon - 1)
    dessiner_pastille(surface, (cx, cy), rayon, cle, police)
