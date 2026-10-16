# ouvertures_fr.py - V7.2 : NOUVEAU FICHIER
#
# LES NOMS D'OUVERTURES EN FRANCAIS.
#
# TA DEMANDE : "trouve toutes les variantes d'ouverture connues, toutes".
#
# La base complete existe : lichess-org/chess-openings, 3 810 ouvertures avec
# leur code ECO. C'est LA reference, celle qu'utilisent lichess et beaucoup
# d'autres. Elle est en anglais.
#
# Le livre interne du jeu, lui, etait en francais (103 ouvertures). Passer aux
# 3 810 sans rien faire, c'etait remplacer "Defense sicilienne" par "Sicilian
# Defense" dans tout le logiciel. Ce fichier traduit.
#
# CE QU'IL TRADUIT, ET CE QU'IL NE TRADUIT PAS :
#
#   - LES NOMS DE FAMILLE ont un equivalent francais etabli, utilise dans toute
#     la litterature : "Ruy Lopez" se dit "Partie espagnole", "Queen's Gambit
#     Declined" se dit "Gambit dame refuse". Ce sont des traductions reelles,
#     pas des inventions.
#   - LE VOCABULAIRE DE STRUCTURE (Variation, Defense, Attack, Accepted...) se
#     traduit mot a mot, avec les accords qu'il faut : "Exchange Variation" ->
#     "Variante d'echange", pas "Variante Exchange".
#   - LES NOMS PROPRES NE SE TRADUISENT PAS. Najdorf reste Najdorf, Svenonius
#     reste Svenonius. C'est voulu : ce sont des noms de joueurs.
#
# QUAND ON NE SAIT PAS, ON LAISSE L'ANGLAIS plutot que d'inventer un nom
# francais qui n'existe pas. Un nom exact en anglais vaut mieux qu'un faux nom
# en francais.
#
# AUCUNE FONCTION SUPPRIMEE : ce fichier n'existait pas. ouvertures.py garde
# tout ce qu'il avait et l'appelle seulement si la traduction est demandee.

import re
import unicodedata

# ---------------------------------------------------------------- les familles
#
# La partie du nom AVANT les deux-points. C'est elle qu'on lit en premier, donc
# c'est elle qui doit etre juste.

FAMILLES = {
    "Sicilian Defense": "Defense sicilienne",
    "Ruy Lopez": "Partie espagnole",
    "French Defense": "Defense francaise",
    "Queen's Gambit Declined": "Gambit dame refuse",
    "Queen's Gambit Accepted": "Gambit dame accepte",
    "Queen's Gambit": "Gambit dame",
    "Italian Game": "Partie italienne",
    "English Opening": "Ouverture anglaise",
    "King's Gambit Accepted": "Gambit du roi accepte",
    "King's Gambit Declined": "Gambit du roi refuse",
    "King's Gambit": "Gambit du roi",
    "King's Indian Defense": "Defense est-indienne",
    "King's Indian Attack": "Attaque est-indienne",
    "Caro-Kann Defense": "Defense Caro-Kann",
    "Nimzo-Indian Defense": "Defense nimzo-indienne",
    "Queen's Pawn Game": "Partie du pion dame",
    "King's Pawn Game": "Partie du pion roi",
    "Semi-Slav Defense": "Defense semi-slave",
    "Slav Defense": "Defense slave",
    "Dutch Defense": "Defense hollandaise",
    "Benoni Defense": "Defense Benoni",
    "Modern Benoni": "Benoni moderne",
    "Old Benoni": "Ancienne Benoni",
    "Grunfeld Defense": "Defense Grunfeld",
    "Alekhine Defense": "Defense Alekhine",
    "Scotch Game": "Partie ecossaise",
    "Scotch Opening": "Ouverture ecossaise",
    "Queen's Indian Defense": "Defense ouest-indienne",
    "Indian Defense": "Defense indienne",
    "Old Indian Defense": "Ancienne defense indienne",
    "Petrov's Defense": "Defense russe",
    "Russian Game": "Partie russe",
    "Four Knights Game": "Partie des quatre cavaliers",
    "Three Knights Opening": "Ouverture des trois cavaliers",
    "Two Knights Defense": "Defense des deux cavaliers",
    "Zukertort Opening": "Ouverture Zukertort",
    "Scandinavian Defense": "Defense scandinave",
    "Philidor Defense": "Defense Philidor",
    "Reti Opening": "Ouverture Reti",
    "Nimzowitsch Defense": "Defense Nimzowitsch",
    "Vienna Game": "Partie viennoise",
    "Vienna Gambit": "Gambit viennois",
    "Bishop's Opening": "Ouverture du fou",
    "Modern Defense": "Defense moderne",
    "Van Geet Opening": "Ouverture Van Geet",
    "Catalan Opening": "Ouverture catalane",
    "Pirc Defense": "Defense Pirc",
    "Bird Opening": "Ouverture Bird",
    "Tarrasch Defense": "Defense Tarrasch",
    "Polish Opening": "Ouverture polonaise",
    "Bogo-Indian Defense": "Defense Bogo-indienne",
    "Hungarian Opening": "Ouverture hongroise",
    "Grob Opening": "Ouverture Grob",
    "Blackmar-Diemer Gambit Accepted": "Gambit Blackmar-Diemer accepte",
    "Blackmar-Diemer Gambit": "Gambit Blackmar-Diemer",
    "Pterodactyl Defense": "Defense pterodactyle",
    "Center Game": "Partie du centre",
    "Danish Gambit Accepted": "Gambit danois accepte",
    "Danish Gambit Declined": "Gambit danois refuse",
    "Danish Gambit": "Gambit danois",
    "Evans Gambit Accepted": "Gambit Evans accepte",
    "Evans Gambit Declined": "Gambit Evans refuse",
    "Evans Gambit": "Gambit Evans",
    "Giuoco Piano": "Giuoco Piano",
    "Ponziani Opening": "Ouverture Ponziani",
    "London System": "Systeme de Londres",
    "Colle System": "Systeme Colle",
    "Trompowsky Attack": "Attaque Trompowsky",
    "Torre Attack": "Attaque Torre",
    "Budapest Defense": "Defense budapestoise",
    "Latvian Gambit Accepted": "Gambit letton accepte",
    "Latvian Gambit": "Gambit letton",
    "Elephant Gambit": "Gambit elephant",
    "Englund Gambit Declined": "Gambit Englund refuse",
    "Englund Gambit Complex": "Complexe du gambit Englund",
    "Englund Gambit": "Gambit Englund",
    "Wing Gambit": "Gambit de l'aile",
    "Benko Gambit Accepted": "Gambit Benko accepte",
    "Benko Gambit Declined": "Gambit Benko refuse",
    "Benko Gambit": "Gambit Benko",
    "Albin Countergambit": "Contre-gambit Albin",
    "Halloween Gambit": "Gambit Halloween",
    "Sodium Attack": "Attaque du sodium",
    "Amar Opening": "Ouverture Amar",
    "Amar Gambit": "Gambit Amar",
    "Barnes Opening": "Ouverture Barnes",
    "Barnes Defense": "Defense Barnes",
    "Clemenz Opening": "Ouverture Clemenz",
    "Mieses Opening": "Ouverture Mieses",
    "Saragossa Opening": "Ouverture Saragosse",
    "Ware Opening": "Ouverture Ware",
    "Ware Defense": "Defense Ware",
    "Anderssen Opening": "Ouverture Anderssen",
    "Crab Opening": "Ouverture du crabe",
    "Global Opening": "Ouverture globale",
    "Kadas Opening": "Ouverture Kadas",
    "Lasker Simul Special": "Speciale simultanee Lasker",
    "Mikenas Defense": "Defense Mikenas",
    "Rat Defense": "Defense du rat",
    "Robatsch Defense": "Defense Robatsch",
    "St. George Defense": "Defense Saint-Georges",
    "Owen Defense": "Defense Owen",
    "Borg Defense": "Defense Borg",
    "Australian Defense": "Defense australienne",
    "Carr Defense": "Defense Carr",
    "Fried Fox Defense": "Defense du renard",
    "Goldsmith Defense": "Defense Goldsmith",
    "Guatemala Defense": "Defense guatemalteque",
    "Hippopotamus Defense": "Defense hippopotame",
    "Lemming Defense": "Defense du lemming",
    "Norwegian Defense": "Defense norvegienne",
    "Duras Gambit": "Gambit Duras",
    "Lion Defense": "Defense du lion",
    "Czech Defense": "Defense tcheque",
    "Semi-Benoni": "Semi-Benoni",
    "Neo-Grunfeld Defense": "Defense neo-Grunfeld",
    "Gruenfeld Defense": "Defense Grunfeld",
    "Richter-Veresov Attack": "Attaque Richter-Veresov",
    "Rapport-Jobava System": "Systeme Rapport-Jobava",
    "Queen's Pawn": "Pion dame",
    "King's Pawn": "Pion roi",
    "Horwitz Defense": "Defense Horwitz",
    "Kangaroo Defense": "Defense kangourou",
    "Marienbad System": "Systeme de Marienbad",
    "Yusupov-Rubinstein System": "Systeme Yusupov-Rubinstein",
    "Zaire Defense": "Defense zairoise",
    "Sicilian": "Sicilienne",
    "Alapin Opening": "Ouverture Alapin",
    "Portuguese Opening": "Ouverture portugaise",
    "Lopez Opening": "Ouverture Lopez",
    "Napoleon Attack": "Attaque Napoleon",
    "Gedult's Opening": "Ouverture Gedult",
    "System": "Systeme",
    "Formation": "Formation",
}

# ------------------------------------------------------- expressions completes
#
# Traduites AVANT les mots isoles, sinon "Exchange Variation" donnerait
# "Variante Exchange". L'ordre du dictionnaire n'a pas d'importance : on essaie
# toujours la plus longue d'abord.

EXPRESSIONS = {
    "Exchange Variation": "Variante d'echange",
    "Advance Variation": "Variante d'avance",
    "Classical Variation": "Variante classique",
    "Modern Variation": "Variante moderne",
    "Closed Variation": "Variante fermee",
    "Open Variation": "Variante ouverte",
    "Normal Variation": "Variante normale",
    "Main Line": "Ligne principale",
    "Main line": "Ligne principale",
    "Old Variation": "Ancienne variante",
    "Neo-Classical Variation": "Variante neo-classique",
    "Modern Line": "Ligne moderne",
    "Classical Line": "Ligne classique",
    "Closed Line": "Ligne fermee",
    "Open Line": "Ligne ouverte",
    "Exchange Line": "Ligne d'echange",
    "Advance Line": "Ligne d'avance",
    "Modern Attack": "Attaque moderne",
    "Classical Attack": "Attaque classique",
    "Modern Defense": "Defense moderne",
    "Classical Defense": "Defense classique",
    "Modern System": "Systeme moderne",
    "Classical System": "Systeme classique",
    "Closed System": "Systeme ferme",
    "Modern Gambit": "Gambit moderne",
    "Delayed Exchange": "Echange differe",
    "Exchange Deferred": "Echange differe",
    "Deferred Exchange": "Echange differe",
    "Two Knights Defense": "Defense des deux cavaliers",
    "Three Knights Variation": "Variante des trois cavaliers",
    "Four Knights Variation": "Variante des quatre cavaliers",
    "Knight Variation": "Variante du cavalier",
    "Bishop Variation": "Variante du fou",
    "Queen Variation": "Variante de la dame",
    "King Variation": "Variante du roi",
    "Rook Variation": "Variante de la tour",
    "Pawn Variation": "Variante du pion",
    "Kingside Variation": "Variante de l'aile roi",
    "Queenside Variation": "Variante de l'aile dame",
    "Center Variation": "Variante du centre",
    "Fianchetto Variation": "Variante du fianchetto",
    "Fianchetto Attack": "Attaque du fianchetto",
    "Fianchetto Defense": "Defense du fianchetto",
    "Fianchetto System": "Systeme du fianchetto",
    "Gambit Accepted": "Gambit accepte",
    "Gambit Declined": "Gambit refuse",
    "Gambit Line": "Ligne de gambit",
    "Counter-Attack": "Contre-attaque",
    "Anti-Sicilian": "Anti-sicilienne",
    "Traditional Line": "Ligne traditionnelle",
    "Delayed Variation": "Variante differee",
    "Early Deviations": "Deviations precoces",
    "Other variations": "Autres variantes",
    "Miscellaneous": "Divers",
    "Copycat Variation": "Variante du miroir",
    "Symmetrical Variation": "Variante symetrique",
    "Symmetrical Defense": "Defense symetrique",
    "Reversed": "inversee",
}

# --------------------------------------------------------------- mots isoles

MOTS = {
    "Variation": "Variante",
    "Defense": "Defense",
    "Defence": "Defense",
    "Attack": "Attaque",
    "Opening": "Ouverture",
    "Line": "Ligne",
    "System": "Systeme",
    "Game": "Partie",
    "Accepted": "accepte",
    "Declined": "refuse",
    "Deferred": "differe",
    "Delayed": "differe",
    "Closed": "fermee",
    "Open": "ouverte",
    "Modern": "moderne",
    "Classical": "classique",
    "Traditional": "traditionnelle",
    "Normal": "normale",
    "Old": "ancienne",
    "Exchange": "Echange",
    "Advance": "Avance",
    "Center": "Centre",
    "Kingside": "aile roi",
    "Queenside": "aile dame",
    "Knight": "cavalier",
    "Bishop": "fou",
    "Rook": "tour",
    "Queen": "dame",
    "King": "roi",
    "Pawn": "pion",
    "Double": "double",
    "Doubled": "double",
    "Quiet": "calme",
    "Wing": "aile",
    "Push": "poussee",
    "Trap": "piege",
    "Swap": "echange",
    "Hunt": "chasse",
    "Mate": "mat",
    "Endgame": "finale",
    "Setup": "dispositif",
}


# ------------------------------------------------- l'ordre des mots en francais
#
# CE QUI M'A FAIT REECRIRE CE FICHIER. Traduire mot a mot donnait :
#     "Najdorf Variation"  ->  "Najdorf Variante"
#     "Breyer Defense"     ->  "Breyer Defense"
#     "English Attack"     ->  "English Attaque"
# En francais le nom passe DEVANT : "Variante Najdorf", "Defense Breyer",
# "Attaque anglaise". C'est la regle la plus importante du fichier, et la
# traduction mot a mot ne peut pas la voir.
#
# Chaque nom de structure porte son genre, parce que l'adjectif s'accorde :
# "Variante anglaise" mais "Gambit anglais".

STRUCTURES = {
    "Variation": ("Variante", "f"),
    "Variations": ("Variantes", "f"),
    "Defense": ("Defense", "f"),
    "Defence": ("Defense", "f"),
    "Attack": ("Attaque", "f"),
    "Gambit": ("Gambit", "m"),
    "Countergambit": ("Contre-gambit", "m"),
    "Counterattack": ("Contre-attaque", "f"),
    "System": ("Systeme", "m"),
    "Line": ("Ligne", "f"),
    "Lines": ("Lignes", "f"),
    "Opening": ("Ouverture", "f"),
    "Game": ("Partie", "f"),
    "Formation": ("Formation", "f"),
    "Trap": ("Piege", "m"),
    "Endgame": ("Finale", "f"),
}

# Les adjectifs, au masculin et au feminin. Sans ca on ecrirait "Variante
# anglais".
ADJECTIFS = {
    "English": ("anglais", "anglaise"),
    "Spanish": ("espagnol", "espagnole"),
    "Italian": ("italien", "italienne"),
    "French": ("francais", "francaise"),
    "German": ("allemand", "allemande"),
    "Russian": ("russe", "russe"),
    "Polish": ("polonais", "polonaise"),
    "Dutch": ("hollandais", "hollandaise"),
    "Danish": ("danois", "danoise"),
    "Swedish": ("suedois", "suedoise"),
    "Norwegian": ("norvegien", "norvegienne"),
    "Czech": ("tcheque", "tcheque"),
    "Hungarian": ("hongrois", "hongroise"),
    "Austrian": ("autrichien", "autrichienne"),
    "Yugoslav": ("yougoslave", "yougoslave"),
    "Scandinavian": ("scandinave", "scandinave"),
    "Portuguese": ("portugais", "portugaise"),
    "Romanian": ("roumain", "roumaine"),
    "Bulgarian": ("bulgare", "bulgare"),
    "Greek": ("grec", "grecque"),
    "Belgian": ("belge", "belge"),
    "Icelandic": ("islandais", "islandaise"),
    "Latvian": ("letton", "lettone"),
    "Finnish": ("finlandais", "finlandaise"),
    "Argentine": ("argentin", "argentine"),
    "Chinese": ("chinois", "chinoise"),
    "Indian": ("indien", "indienne"),
    "Mexican": ("mexicain", "mexicaine"),
    "Canadian": ("canadien", "canadienne"),
    "American": ("americain", "americaine"),
    "Classical": ("classique", "classique"),
    "Modern": ("moderne", "moderne"),
    "Neo-Classical": ("neo-classique", "neo-classique"),
    "Closed": ("ferme", "fermee"),
    "Open": ("ouvert", "ouverte"),
    "Normal": ("normal", "normale"),
    "Old": ("ancien", "ancienne"),
    "Traditional": ("traditionnel", "traditionnelle"),
    "Symmetrical": ("symetrique", "symetrique"),
    "Delayed": ("differe", "differee"),
    "Deferred": ("differe", "differee"),
    "Accelerated": ("accelere", "acceleree"),
    "Quiet": ("calme", "calme"),
    "Double": ("double", "double"),
    "Doubled": ("double", "double"),
    "Improved": ("ameliore", "amelioree"),
    "Irregular": ("irregulier", "irreguliere"),
    "General": ("general", "generale"),
    "Main": ("principal", "principale"),
    "Early": ("precoce", "precoce"),
    "Late": ("tardif", "tardive"),
    "Reversed": ("inverse", "inversee"),
    "Anti-Sicilian": ("anti-sicilien", "anti-sicilienne"),
}

# Les complements introduits par "du/de la" plutot que par un adjectif.
COMPLEMENTS = {
    "Knight": "du cavalier",
    "Knights": "des cavaliers",
    "Bishop": "du fou",
    "Bishops": "des fous",
    "Rook": "de la tour",
    "Rooks": "des tours",
    "Queen": "de la dame",
    "King": "du roi",
    "Pawn": "du pion",
    "Pawns": "des pions",
    "Center": "du centre",
    "Centre": "du centre",
    "Kingside": "de l'aile roi",
    "Queenside": "de l'aile dame",
    "Wing": "de l'aile",
    "Exchange": "d'echange",
    "Advance": "d'avance",
    "Fianchetto": "du fianchetto",
    "Mate": "de mat",
}


# Les nombres : "Two Knights Line" doit donner "Ligne des deux cavaliers",
# pas "Ligne Two des cavaliers".
NOMBRES = {"Two": "deux", "Three": "trois", "Four": "quatre", "Five": "cinq",
           "Six": "six", "Double": "double", "Triple": "triple"}


def _accorder(mot, genre, pluriel=False):
    """L'adjectif au bon genre ET au bon nombre. None si adjectif inconnu.

    Sans le nombre, "Closed Variations" donnait "Variantes fermee".
    """
    paire = ADJECTIFS.get(mot)
    if paire is None:
        return None
    forme = paire[1] if genre == "f" else paire[0]
    if not pluriel or forme.endswith(("s", "x")):
        return forme
    return forme + "s"


def _inverser(morceau):
    """'Najdorf Variation' -> 'Variante Najdorf'. None si la regle ne s'applique pas.

    C'est la regle du francais : le nom d'abord, ce qui le qualifie ensuite.
    """
    mots = morceau.split()
    if len(mots) < 2:
        return None
    dernier = mots[-1]
    structure = STRUCTURES.get(dernier)
    if structure is None:
        return None
    nom, genre = structure
    pluriel = nom.endswith("s")
    tete = " ".join(mots[:-1]).strip()
    if not tete:
        return nom
    # "Accepted"/"Declined" restent APRES le nom : "Gambit dame accepte".
    if tete in ("Accepted", "Declined"):
        return "%s %s" % (nom, "accepte" if tete == "Accepted" else "refuse")
    complement = COMPLEMENTS.get(tete)
    if complement:
        return "%s %s" % (nom, complement)
    adjectif = _accorder(tete, genre, pluriel)
    if adjectif:
        return "%s %s" % (nom, adjectif)
    # "Two Knights", "Four Knights"... : un nombre suivi d'un complement.
    if len(mots) == 3 and mots[0] in NOMBRES and mots[1] in COMPLEMENTS:
        complement = COMPLEMENTS[mots[1]]
        # "des cavaliers" -> "des deux cavaliers"
        morceaux_c = complement.split(" ", 1)
        if len(morceaux_c) == 2:
            return "%s %s %s %s" % (nom, morceaux_c[0], NOMBRES[mots[0]],
                                    morceaux_c[1])
    # Tete inconnue : c'est un nom propre (Najdorf, Breyer, Svenonius...).
    # On le garde tel quel, derriere le nom francais.
    if len(mots) == 2:
        return "%s %s" % (nom, tete)
    # Plusieurs mots devant : on traduit ce qu'on connait, sans casser l'ordre.
    morceaux = []
    for mot in mots[:-1]:
        morceaux.append(_accorder(mot, genre, pluriel)
                        or COMPLEMENTS.get(mot) or NOMBRES.get(mot) or mot)
    return "%s %s" % (nom, " ".join(morceaux))


def _adjectif_en_tete(morceau):
    """'Classical Fianchetto' -> 'Fianchetto classique'. None si ca ne colle pas.

    Meme regle que _inverser, pour les morceaux qui ne finissent pas par un
    nom de structure : en francais l'adjectif passe DERRIERE.
    """
    mots = morceau.split()
    if len(mots) != 2 or mots[0] not in ADJECTIFS:
        return None
    if mots[1] in STRUCTURES or mots[1] in ADJECTIFS:
        return None
    complement = COMPLEMENTS.get(mots[1])
    nom = complement.split(" ", 1)[-1] if complement else mots[1]
    # On ne connait pas le genre du nom propre : masculin par defaut, qui est
    # la forme neutre en francais.
    return "%s %s" % (nom, ADJECTIFS[mots[0]][0])


_CACHE = {}


def _traduire_morceau(texte):
    """Traduit UN morceau de nom (entre deux virgules)."""
    reste = texte.strip()
    if not reste:
        return ""
    # 1. les expressions completes, les plus longues d'abord.
    #    SUR DES MOTS ENTIERS : sans \b, "Closed Variation" se declenchait a
    #    l'interieur de "Closed VariationS" et donnait "Variante fermees", avec
    #    le nom au singulier et l'adjectif au pluriel.
    for anglais in sorted(EXPRESSIONS, key=len, reverse=True):
        motif_exact = r"\b%s\b" % re.escape(anglais)
        if re.search(motif_exact, reste):
            reste = re.sub(motif_exact, EXPRESSIONS[anglais].replace("\\", "\\\\"), reste)
    # 2. LA REGLE DE L'ORDRE FRANCAIS : "Najdorf Variation" -> "Variante
    #    Najdorf". Elle passe avant le mot a mot, qui ne sait pas inverser.
    inverse = _inverser(reste)
    if inverse is not None:
        return inverse
    inverse = _adjectif_en_tete(reste)
    if inverse is not None:
        return inverse
    # 3. a defaut, les mots isoles, en respectant les limites de mot pour ne
    #    pas massacrer un nom propre qui contiendrait la sequence.
    def remplacer(correspondance):
        return MOTS.get(correspondance.group(0), correspondance.group(0))
    motif = r"\b(%s)\b" % "|".join(re.escape(m) for m in
                                  sorted(MOTS, key=len, reverse=True))
    reste = re.sub(motif, remplacer, reste)
    return reste.strip()


def sans_accents(texte):
    """'Grunfeld' pour 'Grünfeld', 'Samisch' pour 'Sämisch'.

    POURQUOI : tout le reste du logiciel est ecrit sans accents, et pour une
    bonne raison - une console Windows en cp1252 s'etrangle sur un caractere
    qu'elle ne connait pas, et le jeu s'arrete au milieu d'un print. Les noms
    de lichess, eux, en contiennent (Grünfeld, Sämisch, Réti). On les ramene
    donc au meme alphabet que le reste, une fois pour toutes.
    """
    # NFKD ne sait pas defaire ces lettres-la : elles n'ont pas de forme
    # "lettre + accent", c'est un caractere entier. Trois noms du livre en
    # contiennent (Hjorring, Sorensen, Moller).
    ENTIERES = {"\u00f8": "o", "\u00d8": "O", "\u00e6": "ae", "\u00c6": "AE",
                "\u00df": "ss", "\u0142": "l", "\u0141": "L",
                "\u0111": "d", "\u0110": "D", "\u00fe": "th", "\u00de": "Th"}
    try:
        texte = "".join(ENTIERES.get(c, c) for c in str(texte or ""))
        decompose = unicodedata.normalize("NFKD", texte)
        return "".join(c for c in decompose if not unicodedata.combining(c))
    except Exception:
        return str(texte or "")


def traduire(nom):
    """'French Defense: Exchange Variation' -> 'Defense francaise, Variante d'echange'.

    Ce qu'on ne sait pas traduire reste tel quel : un nom exact en anglais vaut
    mieux qu'un faux nom en francais.
    """
    nom = str(nom or "").strip()
    if not nom:
        return ""
    if nom in _CACHE:
        return _CACHE[nom]

    famille, _, suite = nom.partition(":")
    famille = famille.strip()
    traduite = FAMILLES.get(famille)
    if traduite is None:
        # Pas dans la table : on traduit quand meme le vocabulaire de structure
        # ("Xyz Defense" -> "Defense Xyz" serait risque, on garde l'ordre).
        traduite = _traduire_morceau(famille)

    morceaux = [traduite]
    for bout in suite.split(","):
        bout = _traduire_morceau(bout)
        if bout:
            morceaux.append(bout)
    sortie = sans_accents(", ".join(m for m in morceaux if m))
    _CACHE[nom] = sortie
    return sortie


def reste_en_anglais(nom):
    """Les mots anglais de structure qu'on n'a PAS su traduire. Pour mesurer.

    Sert au test : il compte ce qui reste, et on sait exactement ou on en est
    au lieu de croire que "c'est traduit".
    """
    traduit = traduire(nom)
    restants = []
    for mot in MOTS:
        if re.search(r"\b%s\b" % re.escape(mot), traduit) \
                and MOTS[mot].lower() != mot.lower():
            restants.append(mot)
    return sorted(set(restants))


def oublier():
    """Vide le cache (sert aux tests)."""
    _CACHE.clear()
