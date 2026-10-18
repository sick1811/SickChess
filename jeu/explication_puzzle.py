# explication_puzzle.py - SickChess : pourquoi ton coup n'etait pas le bon.
#
# Repris de V8_TURBO_3000 (622 lignes) SANS LA VOIX : la synthese vocale de
# Windows sonnait robotique et ne tenait pas le niveau d'un jeu vendu. Il ne
# reste que l'explication ecrite.
#
# Pas de moteur ici : on REGARDE LA POSITION avec python-chess, comme un joueur
# qui explique une faute, et on dit ce qui cloche SANS DONNER LA SOLUTION
# (regle de Julien : "le cavalier est en prise", pas "il fallait Ra4+") :
#   1. il y avait mat et tu l'as laisse passer ;
#   2. ton coup permet le mat ;
#   3. ton coup laisse une piece en prise ;
#   4. une piece adverse etait mal defendue ;
#   5. sinon : "la position demandait mieux" ; et le theme du probleme.

import chess


# La valeur des pieces, en centiemes de pion. Les memes que partout ailleurs
# dans le jeu : une explication qui compterait autrement que les pastilles
# serait une deuxieme verite.
VALEURS = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
           chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}

NOMS = {chess.PAWN: "pion", chess.KNIGHT: "cavalier", chess.BISHOP: "fou",
        chess.ROOK: "tour", chess.QUEEN: "dame", chess.KING: "roi"}

# La tour et la dame sont feminines. Une explication qui dit "prendre le tour"
# s'entend, et une voix qui le prononce s'entend encore plus.
FEMININ = (chess.ROOK, chess.QUEEN)

# Au-dela de cet ecart, une prise vaut la peine d'etre nommee. Un pion perdu
# dans un echange a peu pres egal n'est pas une explication.
SEUIL_MATERIEL = 150


def nom_de_piece(piece):
    """'cavalier' pour un cavalier. '' si on ne sait pas."""
    if piece is None:
        return ""
    genre = getattr(piece, "piece_type", piece)
    return NOMS.get(genre, "")


def avec_article(piece, possessif=False):
    """'la tour', 'le cavalier' - ou 'ta tour', 'ton cavalier'."""
    nom = nom_de_piece(piece)
    if not nom:
        return ""
    genre = getattr(piece, "piece_type", piece)
    if genre in FEMININ:
        return ("ta " if possessif else "la ") + nom
    return ("ton " if possessif else "le ") + nom


def _san(plateau, coup):
    """La notation courte d'un coup, sans jamais lever d'exception."""
    try:
        import notation
        return notation.afficher(plateau.san(coup))
    except Exception:
        try:
            return coup.uci()
        except Exception:
            return "?"


def _valeur(piece):
    if piece is None:
        return 0
    return VALEURS.get(piece.piece_type, 0)


def mat_en_un(plateau):
    """Le coup qui mate tout de suite, ou None. Aucun moteur : 30 coups a tester."""
    for coup in plateau.legal_moves:
        plateau.push(coup)
        mat = plateau.is_checkmate()
        plateau.pop()
        if mat:
            return coup
    return None


def prise_gratuite(plateau, couleur):
    """La meilleure piece de 'couleur' qu'on peut prendre pour rien.

    Renvoie (case, piece, gain) ou (None, None, 0). "Pour rien" veut dire : le
    camp adverse peut la prendre et, meme si on reprend, il reste gagnant.
    C'est volontairement grossier - c'est ce qu'un joueur voit d'un coup d'oeil,
    et c'est exactement ce qu'on veut expliquer.
    """
    attaquant = not couleur
    meilleure = (None, None, 0)
    hypothese = plateau.copy()
    hypothese.turn = attaquant
    for coup in hypothese.legal_moves:
        cible = hypothese.piece_at(coup.to_square)
        if cible is None or cible.color != couleur:
            continue
        gain = _valeur(cible)
        # Si la case est defendue, on reprend : le gain retombe de la valeur
        # de la piece qui vient de prendre.
        if hypothese.is_attacked_by(couleur, coup.to_square):
            gain -= _valeur(hypothese.piece_at(coup.from_square))
        if gain > meilleure[2]:
            meilleure = (coup.to_square, cible, gain)
    return meilleure


def expliquer(position, coup_joue, coup_attendu, puzzle=None,
              donner_la_solution=False):
    """Ce qu'il faut DIRE quand on se trompe. Toujours une chaine, jamais None.

    TA REGLE DU 04/09, ET C'EST LA BONNE :
    "il ne doit pas donner la reponse, il doit dire le cavalier est en prise,
     et ne pas dire 'tu aurais du faire Ra4+'"

    Un puzzle rate se rejoue : annoncer le coup, c'est le finir a la place du
    joueur. On decrit donc CE QUI CLOCHE - la piece en prise, le mat concede,
    l'occasion laissee - et on se tait sur la solution. Le coup exact reste
    disponible par l'indice (touche H) et par VOIR LA SOLUTION : la, c'est
    demande.

    donner_la_solution=True rend l'ancien comportement, pour le jour ou on
    voudra expliquer une position DEJA finie.
    """
    if position is None or coup_joue is None:
        return ""
    plateau = position.copy()
    nous = plateau.turn
    morceaux = []

    attendu_san = ""
    if coup_attendu is not None:
        attendu_san = _san(plateau, coup_attendu)

    # 1. Y AVAIT-IL MAT ? On le dit - c'est un indice sur la NATURE de la
    #    position, pas le coup - mais on ne nomme le coup que si on nous le
    #    demande expressement.
    mat = False
    if coup_attendu is not None:
        essai = plateau.copy()
        try:
            essai.push(coup_attendu)
            mat = essai.is_checkmate()
        except Exception:
            mat = False

    joue_san = _san(plateau, coup_joue)
    piece_jouee = plateau.piece_at(coup_joue.from_square)

    apres = plateau.copy()
    try:
        apres.push(coup_joue)
    except Exception:
        return "Ce coup n'était pas jouable ici."

    if mat:
        if donner_la_solution and attendu_san:
            morceaux.append("Il y avait mat avec %s." % attendu_san)
        else:
            morceaux.append("Il y avait mat, et tu l'as laisse passer.")
    else:
        # 2. TON COUP PERMET-IL LE MAT ? La faute la plus chere. On dit qu'il y
        #    a mat, pas lequel : la position est encore a jouer.
        riposte = mat_en_un(apres)
        if riposte is not None:
            if donner_la_solution:
                morceaux.append("Après ce coup, l'adversaire mate par %s."
                                % _san(apres, riposte))
            else:
                morceaux.append("Ce coup permet le mat à l'adversaire.")
        else:
            # 3. LAISSE-T-IL UNE PIECE EN PRISE ? C'est TON exemple : "le
            #    cavalier est en prise". On nomme la piece et rien d'autre.
            _case, perdue, gain = prise_gratuite(apres, nous)
            avant_case, _avant_piece, gain_avant = prise_gratuite(plateau, nous)
            if perdue is not None and gain >= SEUIL_MATERIEL \
                    and gain > gain_avant:
                if coup_joue.to_square == _case:
                    morceaux.append("%s est en prise."
                                    % avec_article(perdue, possessif=True)
                                    .capitalize())
                else:
                    morceaux.append("Tu laisses %s en prise."
                                    % avec_article(perdue, possessif=True))
            elif gain_avant >= SEUIL_MATERIEL and avant_case is not None:
                morceaux.append("%s était déjà en prise, et l'est toujours."
                                % avec_article(_avant_piece, possessif=True)
                                .capitalize())
            else:
                # 4. RIEN DE VISIBLE A L'OEIL NU : on oriente le regard vers ce
                #    qu'il y avait a prendre, sans dire par quoi.
                _c, a_prendre, gain_adverse = prise_gratuite(apres, not nous)
                if a_prendre is not None and gain_adverse >= SEUIL_MATERIEL:
                    # On NE NOMME PAS la piece adverse : sur un echiquier de
                    # huit cases de cote, dire "le fou" revient souvent a
                    # designer le coup. On dit qu'il y a a prendre, et on rend
                    # la main.
                    morceaux.append("Il y a une pièce adverse mal défendue : "
                                    "regarde ce qui n'est pas protege.")
                else:
                    morceaux.append("Ce n'est pas le coup : la position "
                                    "demandait mieux.")

        # 5. LE BON COUP - SEULEMENT SI ON LE DEMANDE.
        if donner_la_solution and attendu_san:
            gagne = plateau.piece_at(coup_attendu.to_square)
            if gagne is not None and _valeur(gagne) >= 300:
                morceaux.append("Il fallait jouer %s et prendre %s."
                                % (attendu_san, avec_article(gagne)))
            else:
                morceaux.append("Il fallait jouer %s." % attendu_san)

    # 6. LE THEME DU PUZZLE : le motif a chercher, jamais le coup.
    theme = _theme_lisible(puzzle)
    if theme:
        morceaux.append("Theme : %s." % theme)
    return " ".join(morceaux)


def _theme_lisible(puzzle):
    """Le premier theme du puzzle, en francais. '' s'il n'y en a pas."""
    if not puzzle:
        return ""
    themes = puzzle.get("themes") or []
    # Les themes de longueur ("mateIn2", "short", "oneMove"...) n'apprennent
    # rien sur le coup : on prefere celui qui nomme un motif.
    sans_interet = ("short", "long", "veryLong", "oneMove", "crushing",
                    "advantage", "equality", "master", "masterVsMaster",
                    "superGM", "opening", "middlegame", "endgame")
    try:
        import puzzles
        traduire = puzzles.nom_du_theme
    except Exception:
        def traduire(nom):
            return nom
    for theme in themes:
        if theme in sans_interet:
            continue
        nom = traduire(theme)
        if nom and nom != theme:
            return nom
    for theme in themes:
        if theme not in sans_interet:
            return theme
    return ""


