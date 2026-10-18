# export_revue.py - SickChess : exporter la revue en PGN annote (17/10).
#
# Demande de Julien : « on peut exporter le replayer pour analyser ailleurs et
# comparer les statistiques avec lichess ou chess.com ». Le PGN contient :
#   - chaque coup avec son evaluation au format standard [%eval 0.35] / [%eval #3]
#     (lichess et chess.com le relisent) ;
#   - la pastille en symbole PGN (!!, !, ?!, ?, ??) ;
#   - pour les fautes, le meilleur coup de Stockfish en variante ;
#   - en tete : la precision de chaque camp (calcul de lichess) et la
#     profondeur d'analyse vraiment atteinte.
# Le fichier va dans exports/ et le texte est copie dans le presse-papiers.

import datetime
import os
import re

import chess
import chess.pgn

# pastille -> symbole PGN (NAG)
NAGS = {"brillant": 3, "tres_bon": 1, "imprecision": 6, "erreur": 2,
        "manque": 2, "gaffe": 4}
LIBELLES = {"brillant": "Brillant", "tres_bon": "Très bon coup", "meilleur": "Meilleur",
            "excellent": "Excellent", "bon": "Bon", "theorique": "Théorie",
            "imprecision": "Imprécision", "erreur": "Erreur", "manque": "Occasion manquée",
            "gaffe": "Gaffe"}


def _eval_pgn(evaluation, mat):
    if mat is not None:
        if mat == 0:
            return None
        return "#%d" % mat
    if evaluation is None:
        return None
    return "%.2f" % evaluation


def construire_pgn(analyseur, blancs="Blancs", noirs="Noirs", resultat="*",
                   date=None):
    """Le PGN annote de la partie analysee (texte)."""
    a = analyseur
    jeu = chess.pgn.Game()
    jeu.headers["Event"] = "SickChess"
    jeu.headers["Site"] = "SickChess"
    jeu.headers["Date"] = (date or datetime.date.today()).strftime("%Y.%m.%d")
    jeu.headers["White"] = blancs
    jeu.headers["Black"] = noirs
    jeu.headers["Result"] = resultat if resultat in ("1-0", "0-1", "1/2-1/2") else "*"
    if a.fen_initiale != chess.STARTING_FEN:
        jeu.setup(chess.Board(a.fen_initiale))
    rapport = a.rapport()
    pb, pn = rapport["blancs"]["precision"], rapport["noirs"]["precision"]
    jeu.headers["Annotator"] = "SickChess / Stockfish (%s)" % a.description()
    if pb is not None:
        jeu.headers["WhiteAccuracy"] = "%.1f" % pb
    if pn is not None:
        jeu.headers["BlackAccuracy"] = "%.1f" % pn
    jeu.comment = ("Précision (calcul de lichess) : Blancs %s, Noirs %s."
                   % ("%.1f %%" % pb if pb is not None else "?",
                      "%.1f %%" % pn if pn is not None else "?"))
    noeud = jeu
    for i, uci in enumerate(a.coups):
        coup = chess.Move.from_uci(uci)
        infos = a.detail(i)
        avant = noeud
        noeud = noeud.add_variation(coup)
        morceaux = []
        ev = _eval_pgn(a.evaluations[i + 1], a.mats[i + 1])
        if ev is not None:
            morceaux.append("[%%eval %s]" % ev)
        note = infos.get("note") if infos.get("pret") else None
        if note in NAGS:
            noeud.nags.add(NAGS[note])
        if note:
            texte = LIBELLES.get(note, note)
            if infos.get("precision") is not None:
                texte += " (précision %.0f)" % infos["precision"]
            morceaux.append(texte)
        noeud.comment = " ".join(morceaux)
        # Pour une faute : le meilleur coup de Stockfish, en variante.
        if note in ("imprecision", "erreur", "manque", "gaffe"):
            meilleurs = a.meilleurs_coups(i, maximum=1)
            if meilleurs and meilleurs[0]["uci"] != uci:
                try:
                    variante = avant.add_variation(chess.Move.from_uci(meilleurs[0]["uci"]))
                    variante.comment = "Meilleur coup de Stockfish [%%eval %s]" % (
                        _eval_pgn(meilleurs[0]["evaluation"], meilleurs[0]["mat"]) or "0.00")
                except Exception:
                    pass
    exporteur = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
    return jeu.accept(exporteur) + "\n"


def nom_de_fichier(blancs, noirs):
    propre = lambda t: re.sub(r"[^A-Za-z0-9_-]+", "_", str(t))[:24].strip("_") or "joueur"
    return "%s_%s_contre_%s.pgn" % (datetime.datetime.now().strftime("%Y-%m-%d_%H%M"),
                                   propre(blancs), propre(noirs))


def exporter(analyseur, blancs="Blancs", noirs="Noirs", resultat="*", dossier=None):
    """Ecrit le PGN dans exports/ et le copie. Renvoie (chemin, copie_ok)."""
    texte = construire_pgn(analyseur, blancs, noirs, resultat)
    if dossier is None:
        import asset_manager
        dossier = os.path.join(asset_manager.dossier_ecriture(), "exports")
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, nom_de_fichier(blancs, noirs))
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte)
    copie = False
    try:
        import ui
        copie = ui.copier(texte)
    except Exception:
        copie = False
    return chemin, copie
