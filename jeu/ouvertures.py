# ouvertures.py - V7.2 : NOUVEAU FICHIER
#
# LE LIVRE D'OUVERTURES (ta demande : "pour les ouvertures c'est une icone de
# livre un peu").
#
# Tant que les deux joueurs suivent une ouverture connue, le coup n'est ni bon
# ni mauvais : c'est de la THEORIE. Le marquer "excellent" n'a pas de sens - le
# joueur n'a rien trouve, il a recite. Chess.com le marque d'un livre ; on fait
# pareil, avec en plus le NOM de l'ouverture ("Defense sicilienne, Najdorf").
#
# D'OU VIENNENT LES DONNEES, ET CE QUE JE NE POUVAIS PAS FAIRE :
#
#   1. La liste ci-dessous est ecrite a la main. Elle couvre les ouvertures que
#      tu rencontreras vraiment - environ 200 lignes, jusqu'au 6e coup.
#
#   2. LE FICHIER OFFICIEL EST MAINTENANT LA (03/09, ta demande : "trouve
#      toutes les variantes d'ouverture connues, toutes"). J'avais ecrit ici
#      que je n'avais pas pu le telecharger. C'etait vrai avec les outils de
#      l'epoque ; en clonant le depot lichess-org/chess-openings, je l'ai eu.
#      Les cinq fichiers a.tsv a e.tsv sont dans "ouvertures/" a cote du jeu :
#      3 810 ouvertures avec leur code ECO, jusqu'a 36 demi-coups de theorie.
#      Ils remplacent la liste ci-dessous des qu'ils sont presents ; si on les
#      enleve, le jeu retombe sur les 103 ecrites a la main et continue de
#      marcher.
#      Les noms de lichess sont en anglais : ouvertures_fr.py les traduit.
#
# COMMENT ON RECONNAIT UN COUP DE LIVRE : on garde la suite des coups joues
# depuis le debut, en notation UCI, et on regarde si elle est le debut d'une
# ouverture connue. Des qu'on sort du livre, on n'y revient pas - c'est ce que
# fait chess.com, et c'est ce qui evite de retagger "livre" un coup joue par
# hasard au 30e coup.
#
# AUCUNE FONCTION SUPPRIMEE : ce fichier n'existait pas.

import json
import os

# Chaque entree : (code ECO, nom, coups en notation algebrique courte)
# Ecrites a la main. Le fichier officiel de lichess, s'il est depose, prend le
# relais et couvre 3 500 lignes au lieu de 200.
_THEORIE = [
    # ---------------------------------------------------------------- 1.e4 e5
    ("C20", "Ouverture du pion roi", "e4 e5"),
    ("C40", "Partie du cavalier roi", "e4 e5 Nf3"),
    ("C44", "Partie écossaise", "e4 e5 Nf3 Nc6 d4"),
    ("C45", "Partie écossaise, variante classique", "e4 e5 Nf3 Nc6 d4 exd4 Nxd4"),
    ("C46", "Partie des trois cavaliers", "e4 e5 Nf3 Nc6 Nc3"),
    ("C47", "Partie des quatre cavaliers", "e4 e5 Nf3 Nc6 Nc3 Nf6"),
    ("C50", "Partie italienne", "e4 e5 Nf3 Nc6 Bc4"),
    ("C50", "Partie italienne, giuoco piano", "e4 e5 Nf3 Nc6 Bc4 Bc5"),
    ("C53", "Partie italienne, variante classique", "e4 e5 Nf3 Nc6 Bc4 Bc5 c3"),
    ("C55", "Partie des deux cavaliers", "e4 e5 Nf3 Nc6 Bc4 Nf6"),
    ("C57", "Deux cavaliers, attaque Fried Liver", "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5 d5 exd5 Nxd5 Nxf7"),
    ("C60", "Partie espagnole", "e4 e5 Nf3 Nc6 Bb5"),
    ("C64", "Espagnole, défense classique", "e4 e5 Nf3 Nc6 Bb5 Bc5"),
    ("C65", "Espagnole, défense berlinoise", "e4 e5 Nf3 Nc6 Bb5 Nf6"),
    ("C68", "Espagnole, variante d'echange", "e4 e5 Nf3 Nc6 Bb5 a6 Bxc6"),
    ("C70", "Espagnole, système fermé", "e4 e5 Nf3 Nc6 Bb5 a6 Ba4"),
    ("C78", "Espagnole, défense Archangelsk", "e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O b5"),
    ("C84", "Espagnole, variante fermee", "e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7"),
    ("C88", "Espagnole, système Marshall", "e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7 Re1 b5 Bb3 O-O c3 d5"),
    ("C30", "Gambit du roi", "e4 e5 f4"),
    ("C33", "Gambit du roi accepte", "e4 e5 f4 exf4"),
    ("C30", "Gambit du roi refuse", "e4 e5 f4 Bc5"),
    ("C21", "Gambit danois", "e4 e5 d4 exd4 c3"),
    ("C23", "Partie du fou", "e4 e5 Bc4"),
    ("C25", "Partie viennoise", "e4 e5 Nc3"),
    ("C42", "Défense russe (Petroff)", "e4 e5 Nf3 Nf6"),
    ("C41", "Défense Philidor", "e4 e5 Nf3 d6"),
    ("C44", "Gambit Ponziani", "e4 e5 Nf3 Nc6 c3"),

    # ------------------------------------------------------------- 1.e4 autres
    ("B20", "Défense sicilienne", "e4 c5"),
    ("B21", "Sicilienne, gambit Smith-Morra", "e4 c5 d4 cxd4 c3"),
    ("B22", "Sicilienne, variante Alapine", "e4 c5 c3"),
    ("B23", "Sicilienne fermee", "e4 c5 Nc3"),
    ("B27", "Sicilienne, système Hyperaccéléré", "e4 c5 Nf3 g6"),
    ("B30", "Sicilienne, variante Rossolimo", "e4 c5 Nf3 Nc6 Bb5"),
    ("B33", "Sicilienne, variante Sveshnikov", "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 Nf6 Nc3 e5"),
    ("B40", "Sicilienne, variante Kan", "e4 c5 Nf3 e6"),
    ("B44", "Sicilienne, variante Taimanov", "e4 c5 Nf3 e6 d4 cxd4 Nxd4 Nc6"),
    ("B50", "Sicilienne, système avec d6", "e4 c5 Nf3 d6"),
    ("B54", "Sicilienne ouverte", "e4 c5 Nf3 d6 d4 cxd4 Nxd4"),
    ("B70", "Sicilienne, variante du dragon", "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 g6"),
    ("B76", "Dragon, attaque yougoslave", "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 g6 Be3 Bg7 f3"),
    ("B80", "Sicilienne, variante Scheveningue", "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 e6"),
    ("B90", "Sicilienne, variante Najdorf", "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6"),
    ("B01", "Défense scandinave", "e4 d5"),
    ("B01", "Scandinave, variante principale", "e4 d5 exd5 Qxd5 Nc3 Qa5"),
    ("B02", "Défense Alekhine", "e4 Nf6"),
    ("B07", "Défense Pirc", "e4 d6 d4 Nf6 Nc3"),
    ("B06", "Défense moderne", "e4 g6"),
    ("B10", "Défense Caro-Kann", "e4 c6"),
    ("B12", "Caro-Kann, variante d'avance", "e4 c6 d4 d5 e5"),
    ("B13", "Caro-Kann, variante d'echange", "e4 c6 d4 d5 exd5 cxd5"),
    ("B18", "Caro-Kann, variante classique", "e4 c6 d4 d5 Nc3 dxe4 Nxe4 Bf5"),
    ("C00", "Défense française", "e4 e6"),
    ("C02", "Française, variante d'avance", "e4 e6 d4 d5 e5"),
    ("C03", "Française, variante Tarrasch", "e4 e6 d4 d5 Nd2"),
    ("C11", "Française, variante classique", "e4 e6 d4 d5 Nc3 Nf6"),
    ("C15", "Française, variante Winawer", "e4 e6 d4 d5 Nc3 Bb4"),
    ("B00", "Défense Nimzowitsch", "e4 Nc6"),
    ("B00", "Défense Owen", "e4 b6"),

    # ---------------------------------------------------------------- 1.d4 d5
    ("D00", "Ouverture du pion dame", "d4 d5"),
    ("D06", "Gambit dame", "d4 d5 c4"),
    ("D20", "Gambit dame accepte", "d4 d5 c4 dxc4"),
    ("D30", "Gambit dame refuse", "d4 d5 c4 e6"),
    ("D35", "Gambit dame refuse, variante d'echange", "d4 d5 c4 e6 Nc3 Nf6 cxd5 exd5"),
    ("D37", "Gambit dame refuse, variante principale", "d4 d5 c4 e6 Nc3 Nf6 Nf3 Be7"),
    ("D10", "Défense slave", "d4 d5 c4 c6"),
    ("D15", "Slave, variante principale", "d4 d5 c4 c6 Nf3 Nf6 Nc3"),
    ("D43", "Défense semi-slave", "d4 d5 c4 c6 Nf3 Nf6 Nc3 e6"),
    ("D02", "Système de Londres", "d4 d5 Nf3 Nf6 Bf4"),
    ("D00", "Attaque Torre", "d4 Nf6 Nf3 e6 Bg5"),
    ("A45", "Attaque Trompowsky", "d4 Nf6 Bg5"),
    ("D01", "Attaque Richter-Veresov", "d4 d5 Nc3 Nf6 Bg5"),
    ("D07", "Défense Tchigorine", "d4 d5 c4 Nc6"),
    ("D08", "Contre-gambit Albin", "d4 d5 c4 e5"),
    ("A40", "Défense Englund", "d4 e5"),

    # ------------------------------------------------------------- 1.d4 Nf6
    ("E60", "Défense est-indienne", "d4 Nf6 c4 g6 Nc3 Bg7"),
    ("E90", "Est-indienne, variante classique", "d4 Nf6 c4 g6 Nc3 Bg7 e4 d6 Nf3"),
    ("E97", "Est-indienne, variante Mar del Plata", "d4 Nf6 c4 g6 Nc3 Bg7 e4 d6 Nf3 O-O Be2 e5"),
    ("E20", "Défense nimzo-indienne", "d4 Nf6 c4 e6 Nc3 Bb4"),
    ("E32", "Nimzo-indienne, variante classique", "d4 Nf6 c4 e6 Nc3 Bb4 Qc2"),
    ("E12", "Défense ouest-indienne", "d4 Nf6 c4 e6 Nf3 b6"),
    ("E60", "Défense Gruenfeld", "d4 Nf6 c4 g6 Nc3 d5"),
    ("D85", "Gruenfeld, variante d'echange", "d4 Nf6 c4 g6 Nc3 d5 cxd5 Nxd5 e4"),
    ("A56", "Défense Benoni", "d4 Nf6 c4 c5"),
    ("A57", "Gambit Benko", "d4 Nf6 c4 c5 d5 b5"),
    ("A80", "Défense hollandaise", "d4 f5"),
    ("A87", "Hollandaise, variante Leningrad", "d4 f5 g3 Nf6 Bg2 g6"),
    ("A90", "Hollandaise, variante Stonewall", "d4 f5 g3 Nf6 Bg2 e6 Nf3 d5"),
    ("E00", "Défense catalane", "d4 Nf6 c4 e6 g3"),
    ("A46", "Défense indienne", "d4 Nf6 Nf3"),

    # --------------------------------------------------------------- flancs
    ("A10", "Ouverture anglaise", "c4"),
    ("A20", "Anglaise, système du pion roi", "c4 e5"),
    ("A30", "Anglaise symetrique", "c4 c5"),
    ("A15", "Anglaise, défense indienne", "c4 Nf6"),
    ("A04", "Ouverture Reti", "Nf3"),
    ("A05", "Reti, système est-indien", "Nf3 Nf6"),
    ("A07", "Attaque indienne du roi", "Nf3 d5 g3"),
    ("A01", "Ouverture Larsen", "b3"),
    ("A02", "Ouverture Bird", "f4"),
    ("A00", "Ouverture Sokolsky", "b4"),
    ("A00", "Ouverture Grob", "g4"),
    ("A00", "Ouverture Van't Kruijs", "e3"),
    ("A00", "Ouverture Anderssen", "a3"),
]

DOSSIER = "ouvertures"
FICHIERS = ("a.tsv", "b.tsv", "c.tsv", "d.tsv", "e.tsv")

# Un coup n'est plus "de livre" au-dela de ce demi-coup, meme s'il colle encore.
#
# V7.2 (03/09) : 24 -> 36. La base complete de lichess descend jusqu'a 36
# demi-coups (30 lignes le depassent). A 24 on coupait ces lignes-la au milieu,
# alors qu'un joueur qui suit vraiment la theorie jusqu'au 18e coup EST dans le
# livre - c'est meme le cas le plus interessant a signaler. La regle "on sort
# une fois pour toutes" (coups_de_livre) empeche toujours qu'un coup joue par
# hasard au 30e coup se retrouve marque "theorique".
PROFONDEUR_MAX = 36

_LIVRE = None
_SOURCE = "interne"
_FRANCAIS = None


def _en_francais():
    """config.json : "ouvertures_en_francais". Vrai par defaut."""
    global _FRANCAIS
    if _FRANCAIS is not None:
        return _FRANCAIS
    _FRANCAIS = True
    try:
        for dossier in (os.getcwd(),
                        os.path.dirname(os.path.abspath(__file__))):
            chemin = os.path.join(dossier, "config.json")
            if os.path.exists(chemin):
                with open(chemin, "r", encoding="utf-8") as f:
                    _FRANCAIS = bool(json.load(f).get("ouvertures_en_francais",
                                                      True))
                break
    except Exception:
        _FRANCAIS = True
    return _FRANCAIS


def _dossier_du_jeu():
    try:
        from asset_manager import dossier_ecriture
        return dossier_ecriture()
    except Exception:
        return os.getcwd()


def dossier_des_ouvertures():
    """Ou sont les cinq .tsv de lichess. Voir asset_manager.dossier_de_donnees.

    Une fois le jeu compile, ils sont dans _internal/ouvertures et non a cote
    de l'executable : les chercher au mauvais endroit faisait silencieusement
    retomber le jeu sur les 103 ouvertures ecrites a la main.
    """
    # UN DOSSIER POSE A LA MAIN A COTE DU JEU PASSE D'ABORD : c'est ce qui
    # permet de mettre les donnees a jour sans recompiler, et c'est aussi ce
    # que le banc de test detourne pour verifier la lecture.
    prefere = os.path.join(_dossier_du_jeu(), DOSSIER)
    if os.path.isdir(prefere):
        return prefere
    try:
        from asset_manager import dossier_de_donnees
        return dossier_de_donnees(DOSSIER)
    except Exception:
        return prefere


def _lire_le_fichier_officiel():
    """Lit les .tsv de lichess-org/chess-openings s'ils sont deposes.

    Renvoie [(eco, nom, "e4 e5 Nf3"), ...] ou [] si le dossier n'existe pas.
    Format d'une ligne : eco <tab> nom <tab> "1. e4 e5 2. Nf3".
    """
    dossier = dossier_des_ouvertures()
    if not os.path.isdir(dossier):
        return []
    lignes = []
    for nom_fichier in FICHIERS:
        chemin = os.path.join(dossier, nom_fichier)
        if not os.path.exists(chemin):
            continue
        try:
            with open(chemin, "r", encoding="utf-8") as f:
                for ligne in f:
                    morceaux = ligne.rstrip("\n").split("\t")
                    if len(morceaux) < 3:
                        continue
                    eco, nom, pgn = morceaux[0], morceaux[1], morceaux[2]
                    if eco.lower() == "eco":
                        continue          # l'en-tete du fichier
                    coups = _sans_numeros(pgn)
                    if coups:
                        lignes.append((eco, nom, coups))
        except OSError:
            continue
    return lignes


def _sans_numeros(pgn):
    """'1. e4 e5 2. Nf3' -> 'e4 e5 Nf3'."""
    jetons = []
    for jeton in str(pgn or "").replace(".", ". ").split():
        if not jeton or jeton[0].isdigit() or jeton in ("*", "1-0", "0-1"):
            continue
        jetons.append(jeton)
    return " ".join(jetons)


def livre():
    """Le livre, charge une seule fois. {suite en SAN: (eco, nom)}."""
    global _LIVRE, _SOURCE
    if _LIVRE is not None:
        return _LIVRE
    officiel = _lire_le_fichier_officiel()
    if officiel:
        source, lignes = "lichess (%d ouvertures)" % len(officiel), officiel
    else:
        source, lignes = "interne (%d ouvertures)" % len(_THEORIE), _THEORIE
    _SOURCE = source
    # V7.2 (03/09) - TA DEMANDE : "trouve toutes les variantes d'ouverture
    # connues, toutes". La base de lichess les a toutes (3 810 avec leur code
    # ECO), mais elle est en anglais. On la traduit, sinon le logiciel passerait
    # de "Defense sicilienne" a "Sicilian Defense" partout.
    # Se coupe par "ouvertures_en_francais": false dans config.json, pour qui
    # prefere les noms officiels anglais (ceux de lichess et chess.com).
    traduire = None
    if _en_francais():
        try:
            from ouvertures_fr import traduire
        except Exception as souci:
            print("[OUVERTURES] traduction indisponible : %s" % souci)
    _LIVRE = {}
    for eco, nom, coups in lignes:
        if traduire is not None:
            nom = traduire(nom) or nom
        cle = coups.strip()
        if cle:
            # La ligne la plus PRECISE gagne : "Najdorf" plutot que "Sicilienne".
            ancien = _LIVRE.get(cle)
            if ancien is None or len(nom) > len(ancien[1]):
                _LIVRE[cle] = (eco, nom)
    print("[OUVERTURES] livre %s" % source)
    return _LIVRE


def source():
    """D'ou vient le livre : 'interne' ou 'lichess'. Pour le journal."""
    livre()
    return _SOURCE


def recharger():
    """Oublie le livre : il sera relu au prochain appel (sert aux tests)."""
    global _LIVRE, _SOURCE, _FRANCAIS
    _LIVRE = None
    _SOURCE = "interne"
    _FRANCAIS = None
    try:
        import ouvertures_fr
        ouvertures_fr.oublier()
    except Exception:
        pass


def _suites(sans):
    """Toutes les suites du debut : 'e4', 'e4 e5', 'e4 e5 Nf3'...

    JOURNEE DEBUG DU 04/09 : la liste de coups vient parfois d'un PGN relu ou
    d'une partie reprise, ou une case peut etre vide. " ".join levait alors un
    TypeError en plein milieu de l'analyse. On convertit ce qu'on recoit au
    lieu de faire confiance a l'appelant.
    """
    coups = [str(coup) for coup in sans if coup]
    for taille in range(1, len(coups) + 1):
        yield taille, " ".join(coups[:taille])


def reconnaitre(sans):
    """La derniere ouverture reconnue dans cette suite de coups.

    'sans' : la liste des coups depuis le debut, en notation courte
    ("e4", "c5", "Nf3"...). Renvoie (eco, nom, nombre de coups de livre) ou
    None si on n'est jamais entre dans le livre.
    """
    if not sans:
        return None
    table = livre()
    trouve = None
    for taille, suite in _suites(list(sans)[:PROFONDEUR_MAX]):
        entree = table.get(suite)
        if entree is not None:
            trouve = (entree[0], entree[1], taille)
    return trouve


def coups_de_livre(sans):
    """Combien de demi-coups du debut sont de la theorie connue.

    ON S'ARRETE A LA PREMIERE SORTIE : une fois hors du livre, on n'y rentre
    plus. Sans cette regle, un coup joue par hasard au 30e coup se retrouvait
    marque "livre".
    """
    reconnu = reconnaitre(sans)
    return reconnu[2] if reconnu else 0


def est_un_coup_de_livre(sans, indice):
    """Le coup numero 'indice' (0 = premier demi-coup) est-il de la theorie ?"""
    if indice < 0:
        return False
    return indice < coups_de_livre(sans)


def nom_de_l_ouverture(sans):
    """'Defense sicilienne, variante Najdorf', ou '' si rien de connu."""
    reconnu = reconnaitre(sans)
    return reconnu[1] if reconnu else ""


def code_eco(sans):
    """'B90', ou '' si l'ouverture n'est pas reconnue."""
    reconnu = reconnaitre(sans)
    return reconnu[0] if reconnu else ""


# --------------------------------------------------------------- V7.2, 03/09
#
# TA DEMANDE : "ajoute aussi les ouvertures dans le logiciel".
#
# Elles etaient DEJA reconnues - c'est ce qui allume la pastille "Theorique",
# l'icone de livre. Mais leur NOM n'etait affiche nulle part : nom_de_l_ouverture
# et code_eco existaient et n'etaient appelees par aucun ecran. Le travail
# etait fait, il ne sortait pas.
#
# Ces trois fonctions sont ce que les ecrans appellent maintenant.

def etiquette(sans):
    """'C60 - Partie espagnole' pour l'ecran. '' si on n'est jamais entre
    dans le livre."""
    reconnu = reconnaitre(sans)
    if not reconnu:
        return ""
    eco, nom, _ = reconnu
    return "%s - %s" % (eco, nom) if eco else nom


def resume(sans):
    """'C60 - Partie espagnole  (5 coups de theorie)'.

    Le nombre de coups compte : savoir qu'on est sorti du livre au 5e coup
    explique souvent tout le reste de la partie.
    """
    reconnu = reconnaitre(sans)
    if not reconnu:
        return ""
    eco, nom, combien = reconnu
    coups = (combien + 1) // 2
    return "%s  (%d coup%s de théorie)" % (etiquette(sans), coups,
                                           "s" if coups > 1 else "")


def entetes_pgn(sans):
    """Les deux etiquettes normalisees du PGN : {'ECO': 'C60', 'Opening': '...'}.

    C'est le format que lisent lichess, chess.com et SCID : une partie exportee
    d'ici garde donc son ouverture partout ailleurs.
    """
    reconnu = reconnaitre(sans)
    if not reconnu:
        return {}
    eco, nom, _ = reconnu
    sortie = {}
    if eco:
        sortie["ECO"] = eco
    if nom:
        sortie["Opening"] = nom
    return sortie


# ---------------------------------------------------------- V7.2, 03/09 (2)
#
# LE LIVRE POUR LE BOT.
#
# TA DEMANDE : "donne le livre au bot". Jusqu'ici il choisissait TOUS ses coups
# dans le classement de Stockfish, y compris les trois premiers - et a
# profondeur fixe, le classement des trois premiers coups ne change jamais.
# Resultat : il jouait a peu de choses pres toujours les memes debuts.
#
# Un vrai joueur a un repertoire, et il en sort tot ou tard. On reproduit les
# deux : le bot pioche dans les 3 810 ouvertures, avec un tirage pondere, et il
# sort du livre d'autant plus tot qu'il est faible - un joueur a 300 Elo ne
# connait pas dix coups de theorie.

# Jusqu'ou le bot suit la theorie, selon son classement. En DEMI-COUPS.
_PROFONDEUR_DU_BOT = [
    (300, 2), (600, 4), (900, 6), (1200, 8), (1600, 10), (4000, 14),
]


def profondeur_du_bot(elo):
    """Combien de demi-coups de theorie ce niveau est cense connaitre."""
    try:
        elo = int(elo)
    except (TypeError, ValueError):
        return 6
    for seuil, combien in _PROFONDEUR_DU_BOT:
        if elo <= seuil:
            return combien
    return _PROFONDEUR_DU_BOT[-1][1]


def coups_de_suite(sans):
    """Les coups de livre jouables ICI, avec leur poids. {} si on est sorti.

    Le poids, c'est le nombre de lignes du livre qui passent par ce coup :
    une suite tres ramifiee est une suite tres jouee. C'est une approximation
    de la popularite, et elle vaut ce qu'elle vaut - mais elle a le merite de
    ne demander aucune donnee de plus.
    """
    prefixe = " ".join(sans) if sans else ""
    debut = (prefixe + " ") if prefixe else ""
    suivants = {}
    for cle in livre():
        if prefixe and not cle.startswith(debut):
            continue
        reste = cle[len(debut):] if debut else cle
        if not reste:
            continue
        coup = reste.split(" ", 1)[0]
        if coup:
            suivants[coup] = suivants.get(coup, 0) + 1
    return suivants


def coup_du_livre(sans, elo=1200, hasard=None):
    """Un coup de theorie pour le bot, ou None quand il doit se debrouiller.

    'hasard' : un random.Random, pour que les tests soient reproductibles.
    """
    sans = list(sans or [])
    if len(sans) >= profondeur_du_bot(elo):
        return None                       # il est sorti de son repertoire
    suivants = coups_de_suite(sans)
    if not suivants:
        return None
    import random as _random
    tirage = hasard or _random
    coups = sorted(suivants)
    # PLUS LE NIVEAU EST BAS, PLUS LE TIRAGE EST PLAT : un joueur fort suit les
    # grandes lignes, un debutant joue n'importe quelle ouverture connue.
    try:
        force = max(0.0, min(1.0, (int(elo) - 200) / 1200.0))
    except (TypeError, ValueError):
        force = 0.5
    poids = [suivants[c] ** (0.2 + 1.3 * force) for c in coups]
    total = sum(poids)
    if total <= 0:
        return tirage.choice(coups)
    seuil = tirage.random() * total
    cumul = 0.0
    for coup, poid in zip(coups, poids):
        cumul += poid
        if cumul >= seuil:
            return coup
    return coups[-1]
