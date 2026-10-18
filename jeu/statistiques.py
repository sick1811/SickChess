# statistiques.py - SickChess 17/10 (travail p05, demande de Julien).
#
# Les statistiques de progression, calculees a partir de TES parties
# (dossier parties/) et de leurs analyses enregistrees (.analyse.json) :
#   - bilan : parties, victoires / nulles / defaites, score, par couleur ;
#   - precision moyenne, et son evolution (les 10 dernieres contre avant) ;
#   - tes ouvertures : nombre de parties et score de chacune ;
#   - tes fautes (imprecisions, erreurs, gaffes) selon la phase de jeu :
#     ouverture, milieu de partie, finale.
# Seules les parties ou l'on sait quel camp tu jouais comptent (contre
# l'ordinateur, en ligne, ou importees avec ton nom). Aucun moteur ici.
# (La « base par tranche d'Elo » de V8 n'est pas reprise : elle ne servait
# qu'a regler le bot.)

import os

import chess

FAUTES = ("imprecision", "erreur", "gaffe", "manque")
DEMI_COUPS_OUVERTURE = 20
MATERIEL_FINALE = 26        # pieces (sans pions ni rois), les deux camps, en points
VALEURS = {chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


def phase(fen, demi_coup):
    """'ouverture', 'milieu' ou 'finale' pour la position avant le coup."""
    if demi_coup < DEMI_COUPS_OUVERTURE:
        return "ouverture"
    plateau = chess.Board(fen)
    materiel = sum(v * len(plateau.pieces(p, c)) for p, v in VALEURS.items()
                   for c in (chess.WHITE, chess.BLACK))
    return "finale" if materiel <= MATERIEL_FINALE else "milieu"


def famille_d_ouverture(nom):
    """« Défense sicilienne : variante Najdorf » -> « Défense sicilienne »."""
    nom = (nom or "").strip()
    for separateur in (":", ","):
        if separateur in nom:
            nom = nom.split(separateur)[0].strip()
    return nom or "Inconnue"


def _score(resultat, camp):
    if resultat == "1/2-1/2":
        return 0.5
    if resultat in ("1-0", "0-1"):
        return 1.0 if (resultat == "1-0") == (camp == "blanc") else 0.0
    return None


def _analyse(partie):
    """Precision et fautes par phase du joueur dans cette partie, ou None."""
    import historique_parties
    from analyse_partie import AnalyseurPartie
    chemin = partie.get("chemin", "")
    cache = os.path.splitext(chemin)[0] + ".analyse.json"
    if not os.path.exists(cache):
        return None
    donnees, erreur = historique_parties.lire_partie(chemin)
    if erreur or not donnees:
        return None
    a = AnalyseurPartie(donnees["fen"], donnees["coups"], None, "rapide",
                        fichier_cache=cache, version_min=1)
    if not a.terminee():
        return None
    blancs = partie["camp"] == "blanc"
    rapport = a.rapport()
    fautes = {"ouverture": 0, "milieu": 0, "finale": 0}
    coups = {"ouverture": 0, "milieu": 0, "finale": 0}
    for i in range(a.nombre_de_coups()):
        if a.trait[i] != blancs:
            continue
        ph = phase(a.fens[i], i)
        coups[ph] += 1
        if a.detail(i).get("note") in FAUTES:
            fautes[ph] += 1
    return {"precision": rapport["blancs" if blancs else "noirs"]["precision"],
            "fautes": fautes, "coups": coups}


def calculer(parties=None):
    """Toutes les statistiques, en un dictionnaire (voir l'en-tete)."""
    import historique_parties
    if parties is None:
        parties = historique_parties.lister(400)
    miennes = [p for p in parties if p.get("camp") in ("blanc", "noir")
               and _score(p.get("resultat"), p["camp"]) is not None]
    miennes.sort(key=lambda p: os.path.getmtime(p["chemin"]) if os.path.exists(p["chemin"]) else 0)

    bilan = {"parties": len(miennes), "victoires": 0, "nulles": 0, "defaites": 0,
             "blanc": [0, 0.0], "noir": [0, 0.0]}
    ouvertures = {}
    precisions = []
    fautes = {"ouverture": 0, "milieu": 0, "finale": 0}
    coups = {"ouverture": 0, "milieu": 0, "finale": 0}
    parties_analysees = 0
    for p in miennes:
        s = _score(p["resultat"], p["camp"])
        bilan["victoires" if s == 1 else "nulles" if s == 0.5 else "defaites"] += 1
        bilan[p["camp"]][0] += 1
        bilan[p["camp"]][1] += s
        o = ouvertures.setdefault(famille_d_ouverture(p.get("ouverture")), [0, 0.0])
        o[0] += 1
        o[1] += s
        try:
            a = _analyse(p)
        except Exception as e:
            print("[STATS] %s : %s" % (p.get("fichier"), e))
            a = None
        if a:
            parties_analysees += 1
            if a["precision"] is not None:
                precisions.append(round(float(a["precision"]), 1))
            for ph in fautes:
                fautes[ph] += a["fautes"][ph]
                coups[ph] += a["coups"][ph]

    def pourcent(n, total):
        return 100.0 * n / total if total else None

    recents, anciens = precisions[-10:], precisions[:-10]
    return {
        "bilan": bilan,
        "score": pourcent(bilan["victoires"] + 0.5 * bilan["nulles"], bilan["parties"]),
        "score_blanc": pourcent(bilan["blanc"][1], bilan["blanc"][0]),
        "score_noir": pourcent(bilan["noir"][1], bilan["noir"][0]),
        "precisions": precisions,
        "precision_moyenne": sum(precisions) / len(precisions) if precisions else None,
        "precision_recente": sum(recents) / len(recents) if recents else None,
        "precision_avant": sum(anciens) / len(anciens) if anciens else None,
        "ouvertures": sorted(((nom, n, pourcent(s, n)) for nom, (n, s) in ouvertures.items()),
                             key=lambda x: (-x[1], x[0])),
        "fautes": fautes,
        "fautes_pour_100": {ph: pourcent(fautes[ph], coups[ph]) for ph in fautes},
        "parties_analysees": parties_analysees,
    }
