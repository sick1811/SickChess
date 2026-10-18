# explication_revue.py - SickChess 17/10 (travail p03, demande de Julien).
#
# Dans la revue, une faute (imprecision, erreur, gaffe, occasion manquee) est
# expliquee AVEC DES MOTS, comme un entraineur :
#   « Ce coup laisse ton cavalier sans défense. »
#   « Tu avais un mat en un coup. »
#   « Il y avait une fourchette sur le roi et la tour. »
# REGLE DE JULIEN (17/10) : « ne jamais dire le coup ». On dit ce qui cloche
# (la piece en prise, le mat concede, la fourchette ratee), jamais le coup
# lui-meme, comme dans les problemes (explication_puzzle.py).
# Aucun moteur ici : python-chess regarde la position (meme methode que
# explication_puzzle.py) ; le meilleur coup vient de l'analyse Stockfish.

import chess

import explication_puzzle as ep

SEUIL = ep.SEUIL_MATERIEL


def _san(plateau, coup):
    return ep._san(plateau, coup)


def cibles_d_une_fourchette(plateau, case):
    """Pieces adverses de valeur (cavalier ou plus, ou le roi) attaquees par la
    piece en 'case', et pas mieux defendues que ce qu'elle vaut. [] si moins de 2."""
    piece = plateau.piece_at(case)
    if piece is None:
        return []
    valeur = ep._valeur(piece)
    cibles = []
    for c in plateau.attacks(case):
        cible = plateau.piece_at(c)
        if cible is None or cible.color == piece.color:
            continue
        if cible.piece_type == chess.KING:
            cibles.append(cible)
        elif ep._valeur(cible) >= 300 and (ep._valeur(cible) > valeur
                                           or not plateau.is_attacked_by(cible.color, c)):
            cibles.append(cible)
    return cibles if len(cibles) >= 2 else []


def _liste_possessif(pieces, nous):
    noms = [ep.avec_article(p, possessif=(p.color == nous)) for p in pieces]
    return noms[0] if len(noms) == 1 else ", ".join(noms[:-1]) + " et " + noms[-1]


def _liste(pieces):
    noms = [ep.avec_article(p) for p in pieces]
    if len(noms) <= 1:
        return "".join(noms)
    return ", ".join(noms[:-1]) + " et " + noms[-1]


def _ce_que_le_bon_coup_faisait(plateau, meilleur):
    """Une phrase sur ce qu'apportait le meilleur coup, ou ''."""
    if meilleur is None or meilleur not in plateau.legal_moves:
        return ""
    prise = plateau.piece_at(meilleur.to_square)
    essai = plateau.copy()
    essai.push(meilleur)
    if essai.is_checkmate():
        return "Tu avais un mat en un coup."
    if ep.mat_en_un(essai) is None:
        # mat en 2 force ? (echec, et toute reponse permet un mat en 1)
        if essai.is_check() and all(ep.mat_en_un(_apres(essai, r)) is not None
                                    for r in essai.legal_moves):
            return "Tu avais un mat en deux coups."
    fourchette = cibles_d_une_fourchette(essai, meilleur.to_square)
    if fourchette:
        return "Il y avait une fourchette sur %s." % _liste(fourchette)
    if prise is not None and ep._valeur(prise) >= 300:
        defendue = essai.is_attacked_by(not plateau.turn, meilleur.to_square)
        if not defendue or ep._valeur(prise) > ep._valeur(plateau.piece_at(meilleur.from_square)):
            return "%s adverse était à prendre." % ep.avec_article(prise).capitalize()
    return ""


def _apres(plateau, coup):
    p = plateau.copy()
    p.push(coup)
    return p


def _ce_que_ton_coup_permet(plateau, joue):
    """Une phrase sur ce que le coup joue concede, ou ''."""
    nous = plateau.turn
    apres = _apres(plateau, joue)
    riposte = ep.mat_en_un(apres)
    if riposte is not None:
        return "Ce coup permet le mat à l'adversaire."
    case, perdue, gain = ep.prise_gratuite(apres, nous)
    _c0, _p0, gain_avant = ep.prise_gratuite(plateau, nous)
    if perdue is not None and gain >= SEUIL and gain > gain_avant:
        if joue.to_square == case:
            return "Ta pièce va sur une case où elle se fait prendre : %s est perdu%s." % (
                ep.avec_article(perdue, possessif=True),
                "e" if perdue.piece_type in ep.FEMININ else "")
        return "Ce coup laisse %s sans défense." % ep.avec_article(perdue, possessif=True)
    for r in apres.legal_moves:
        essai = _apres(apres, r)
        cibles = cibles_d_une_fourchette(essai, r.to_square)
        if cibles and any(c.color == nous for c in cibles):
            if not essai.is_attacked_by(nous, r.to_square) or \
                    any(c.piece_type == chess.KING for c in cibles):
                return "Ce coup permet une fourchette sur %s." % _liste_possessif(cibles, nous)
    return ""


def expliquer(fen_avant, joue_uci, meilleur_uci=None):
    """Une ou deux phrases. '' si on ne voit rien de clair (la pastille et
    « Il fallait jouer ... » suffisent alors)."""
    try:
        plateau = chess.Board(fen_avant)
        joue = chess.Move.from_uci(joue_uci)
        if joue not in plateau.legal_moves:
            return ""
        meilleur = chess.Move.from_uci(meilleur_uci) if meilleur_uci else None
    except Exception:
        return ""
    phrases = []
    concede = _ce_que_ton_coup_permet(plateau, joue)
    if concede:
        phrases.append(concede)
    if meilleur is not None and meilleur != joue:
        rate = _ce_que_le_bon_coup_faisait(plateau, meilleur)
        if rate:
            phrases.append(rate)
    return " ".join(phrases[:2])
