"""La banque de positions : les pastilles de la revue sont-elles justes ? (24/10, travail p30)

    python outils/precision.py               verifie la banque (Stockfish necessaire)
    python outils/precision.py --fabriquer   refait tests/positions_revue.json

LA BANQUE (tests/positions_revue.json) : de petites « parties » de 1 ou 2 coups,
avec, pour chaque coup, les pastilles acceptees. Elle ne vient PAS de notre propre
analyse (ce serait se verifier soi-meme) :
  - des problemes lichess (base deja livree avec le jeu, domaine public) : chacun
    nait d'une VRAIE GAFFE d'un joueur, suivie du bon coup - souvent un sacrifice -
    verifie par lichess avec Stockfish en profondeur. La gaffe doit etre jugee
    mauvaise (Erreur, Manque ou Gaffe) ; le bon coup, bon (jamais une faute : un
    sacrifice correct n'est pas une gaffe) ;
  - quelques positions classiques choisies a la main (mat etouffe, piege de Legal,
    pat rate, dame en prise, coup d'ouverture).
Les retours de Julien (« coup 12 faux ») s'ajoutent dans A_LA_MAIN.

LA VERIFICATION : chaque petite partie passe par l'analyse de la revue
(analyse_partie.AnalyseurPartie, la meme que dans le jeu), a la puissance choisie
(par defaut celle du jeu : calcul, forte). Sert au banc d'essai (section
« precision ») et a tests/test_precision.py.
"""
import gzip
import json
import os
import random
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "jeu"))
BANQUE = os.path.join(RACINE, "tests", "positions_revue.json")

BONS = ["brillant", "tres_bon", "meilleur", "theorique", "excellent", "bon"]
FAUTES = ["erreur", "manque", "gaffe"]

# Positions choisies a la main : (id, fen, coups uci, [pastilles acceptees par coup], explication)
A_LA_MAIN = [
    ("mat_etouffe", "5r1k/6pp/7N/3Q4/8/8/8/6K1 w - - 0 1", ["d5g8", "f8g8", "h6f7"],
     [BONS, BONS, BONS],
     "Sacrifice de dame Dg8+ ! Txg8 Cf7# (mat etouffe) : sacrifice correct = bonne pastille."),
    ("piege_de_legal", "rn1qkbnr/ppp2p1p/3p2p1/4p3/2B1P1b1/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 5",
     ["f3e5", "g4d1"], [BONS, FAUTES],
     "Piege de Legal : 5.Cxe5 ! (la dame est donnee) puis 5...Fxd1 ?? permet Fxf7+ Re7 Cd5#."),
    ("pat_rate", "7k/5K2/8/6Q1/8/8/8/8 w - - 0 1", ["g5g6"], [FAUTES],
     "Dg6 ?? pat : la partie gagnee devient nulle (Dg7# etait mat)."),
    ("mat_en_un", "7k/5K2/8/6Q1/8/8/8/8 w - - 0 1", ["g5g7"], [BONS],
     "Dg7# : le mat."),
    ("dame_en_prise", "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
     ["d8g5", "f3g5"], [FAUTES, BONS],
     "2...Dg5 ?? : la dame est prise par le cavalier pour rien."),
    ("ouverture", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", ["e2e4"],
     [BONS], "1.e4 : coup d'ouverture, jamais une faute."),
]

# Tirage des problemes lichess : (theme, combien, classement mini, maxi)
TIRAGE = [("sacrifice", 22, 1000, 2300), ("mate", 10, 800, 2000), ("endgame", 10, 1000, 2200),
          ("crushing", 10, 1000, 2300)]
GRAINE = 20261024


def _problemes(dossier):
    """Lit la base de problemes (puzzles/pXX.tsv.gz) : id, fen, coups, classement, themes."""
    for nom in sorted(os.listdir(dossier)):
        if not nom.endswith(".tsv.gz"):
            continue
        with gzip.open(os.path.join(dossier, nom), "rt", encoding="utf-8") as f:
            for ligne in f:
                m = ligne.rstrip("\n").split("\t")
                if len(m) >= 5:
                    yield m[0], m[1], m[2].split(), int(m[3]), set(m[4].split())


PROFONDEUR_VERITE = 20     # Stockfish en profondeur, a la fabrication seulement
GAFFE_AVANT_MINI = 40.0    # avant la gaffe, le joueur avait au moins 40 % de chances...
GAFFE_APRES_MAXI = 15.0    # ... et apres, 15 % au plus : une gaffe nette
BON_APRES_MINI = 75.0      # apres le bon coup, au moins 75 % : il garde le gain


def _chances(moteur, fen, du_camp):
    """Chances de gagner du camp 'du_camp' dans la position (Stockfish en profondeur)."""
    import annotations
    import chess
    plateau = chess.Board(fen)
    if plateau.is_checkmate():
        return 0.0 if plateau.turn == du_camp else 100.0
    if plateau.is_game_over():
        return 50.0
    d = moteur.analyser_position(fen, PROFONDEUR_VERITE, 20000, lignes=1)
    if not d:
        return None
    v = 100.0 if d["mat"] is not None and d["mat"] > 0 else -100.0 if d["mat"] is not None \
        else d["evaluation"]
    if v is None:
        return None
    blancs = v if plateau.turn == chess.WHITE else -v
    c = annotations.chances_de_gagner(blancs)
    return c if du_camp == chess.WHITE else 100.0 - c


def _verite(moteur, fen, coups):
    """(chances avant la gaffe, apres la gaffe, apres le bon coup), chacune du point
    de vue de celui qui joue ce coup ; None si Stockfish ne repond pas."""
    import chess
    plateau = chess.Board(fen)
    fautif = plateau.turn
    avant = _chances(moteur, plateau.fen(), fautif)
    plateau.push_uci(coups[0])
    apres = _chances(moteur, plateau.fen(), fautif)
    solveur = plateau.turn
    plateau.push_uci(coups[1])
    bon = _chances(moteur, plateau.fen(), solveur)
    if None in (avant, apres, bon):
        return None
    return round(avant, 1), round(apres, 1), round(bon, 1)


def fabriquer(dossier=None, chemin_stockfish=None):
    """Refait la banque : positions a la main + problemes lichess tires au sort
    (toujours les memes : graine fixe), gardes seulement si Stockfish en profondeur
    confirme une gaffe NETTE suivie d'un bon coup qui garde le gain."""
    import chess
    from engine import StockfishEngine
    dossier = dossier or os.path.join(RACINE, "puzzles")
    moteur = StockfishEngine(chemin_stockfish or _stockfish())
    moteur.configurer_pour_analyse(None, 512)
    hasard = random.Random(GRAINE)
    candidats = {theme: [] for theme, *_ in TIRAGE}
    deja = set()
    for pid, fen, coups, classement, themes in _problemes(dossier):
        for theme, _n, mini, maxi in TIRAGE:
            if theme in themes and mini <= classement <= maxi and len(coups) >= 2 \
                    and hasard.random() < 0.004:
                candidats[theme].append((pid, fen, coups[:2], classement, sorted(themes)))
    positions = []
    for ident, fen, coups, attendus, pourquoi in A_LA_MAIN:
        positions.append({"id": ident, "source": "a la main", "fen": fen, "coups": coups,
                          "attendus": attendus, "pourquoi": pourquoi})
    for theme, nombre, _mini, _maxi in TIRAGE:
        liste = candidats[theme]
        hasard.shuffle(liste)
        pris = 0
        for pid, fen, coups, classement, themes in liste:
            if pid in deja or pris >= nombre:
                continue
            plateau = chess.Board(fen)
            try:
                sans = []
                for u in coups:
                    sans.append(plateau.san(chess.Move.from_uci(u)))
                    plateau.push_uci(u)
            except ValueError:
                continue
            verite = _verite(moteur, fen, coups)
            if verite is None or verite[0] < GAFFE_AVANT_MINI or verite[1] > GAFFE_APRES_MAXI \
                    or verite[2] < BON_APRES_MINI:
                continue
            deja.add(pid)
            pris += 1
            print("  %s %-10s %s puis %s : chances %s" % (theme, pid, sans[0], sans[1], verite))
            positions.append({
                "id": "lichess_" + pid, "source": "https://lichess.org/training/" + pid,
                "fen": fen, "coups": coups, "attendus": [FAUTES, BONS],
                "pourquoi": "Probleme lichess %s (%d, %s) : %s est la gaffe qui cree le probleme "
                            "(chances %.0f %% -> %.0f %%), %s le bon coup (%.0f %%)." % (
                                pid, classement, theme, sans[0], verite[0], verite[1], sans[1],
                                verite[2]),
                "themes": themes, "chances_stockfish_p20": list(verite)})
    moteur.quit()
    with open(BANQUE, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "fabrique_le": time.strftime("%d/%m/%Y"),
                   "explication": "Voir outils/precision.py.", "positions": positions},
                  f, ensure_ascii=False, indent=1)
    return positions


def charger():
    with open(BANQUE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def verifier(chemin_stockfish, puissance="calcul_forte", positions=None, delai=120,
             afficher=False):
    """Analyse chaque petite partie comme la revue. Renvoie la liste des coups jugés :
    {id, coup, san, note, attendus, ok, pourquoi}."""
    from analyse_partie import AnalyseurPartie
    positions = positions if positions is not None else charger()
    resultats = []
    for p in positions:
        a = AnalyseurPartie(p["fen"], p["coups"], chemin_stockfish, puissance)
        a.demarrer()
        fin = time.time() + delai
        while not a.terminee() and time.time() < fin and not a.erreur:
            time.sleep(0.05)
        for i, attendus in enumerate(p["attendus"]):
            infos = a.detail(i)
            note = infos.get("note") if infos.get("pret") else None
            r = {"id": p["id"], "coup": i + 1, "san": infos.get("san"), "note": note,
                 "attendus": attendus, "ok": note in attendus, "pourquoi": p["pourquoi"],
                 "evaluations": (infos.get("evaluation_avant"), infos.get("evaluation_apres"))}
            resultats.append(r)
            if afficher:
                print("  %s %-26s %d. %-8s %-11s (attendu : %s)" % (
                    "OK  " if r["ok"] else "FAUX", p["id"], i + 1, r["san"], note,
                    "bon" if attendus == BONS else "faute" if attendus == FAUTES else attendus))
        a.arreter()
    return resultats


def _stockfish():
    sf = os.environ.get("SICKCHESS_STOCKFISH")
    if sf:
        return sf
    try:
        with open(os.path.join(RACINE, "config.json"), encoding="utf-8") as f:
            sf = json.load(f).get("stockfish_path")
    except (OSError, ValueError):
        sf = None
    return sf or os.path.join(RACINE, "moteur", "stockfish.exe")


def main():
    os.chdir(RACINE)
    if "--fabriquer" in sys.argv:
        positions = fabriquer(chemin_stockfish=_stockfish())
        print("%d positions ecrites dans %s" % (len(positions), BANQUE))
        return 0
    puissance = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--puissance=")),
                     "calcul_forte")
    debut = time.time()
    resultats = verifier(_stockfish(), puissance, afficher=True)
    faux = [r for r in resultats if not r["ok"]]
    print()
    print("%d coups juges, %d justes, %d faux (%s, %.0f s)" % (
        len(resultats), len(resultats) - len(faux), len(faux), puissance, time.time() - debut))
    return 1 if faux else 0


if __name__ == "__main__":
    sys.exit(main())
