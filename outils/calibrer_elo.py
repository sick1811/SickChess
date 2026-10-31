# outils/calibrer_elo.py - SickChess 31/10 (travail p34, « niveaux en vrai Elo »)
#
#     python outils/calibrer_elo.py                     # mesure complète (la nuit)
#     python outils/calibrer_elo.py --minutes 480       # s'arrête au bout de 8 h
#     python outils/calibrer_elo.py --niveaux 800,1600 --parties 6 --minutes 15
#     python outils/calibrer_elo.py --rapport           # refait le rapport sans jouer
#
# CE QUE ÇA FAIT
#   Fait jouer chaque niveau de l'ordinateur, AVEC LE VRAI CODE DU JEU (même
#   moteur « jeu » de moteurs.py, même set_custom_elo, même choix maison sous
#   1320 Elo, même livre d'ouvertures et même temps de calcul que
#   background_ai.BackgroundAI, dont on appelle le vrai _ai_worker), contre des
#   adversaires d'Elo connu :
#     - Stockfish bridé par UCI_LimitStrength + UCI_Elo (1320 à 3190). Stockfish
#       annonce cet Elo calibré à la cadence 120 s + 1 s par partie, ancré sur la
#       liste CCRL 40/4 : l'adversaire de référence joue donc avec SA pendule à
#       cette cadence (« go wtime btime winc binc »), réglable par --cadence-ref ;
#     - sous 1320, des niveaux du jeu déjà mesurés (échelle : 800 joue contre le
#       niveau 1200 une fois que celui-ci a son Elo mesuré).
#   Puis il calcule l'Elo de performance de chaque niveau (avec une marge à 95 %),
#   écrit docs/CALIBRAGE_ELO.md et propose la table à recopier dans
#   jeu/niveaux_elo.py.
#
# RÈGLES RESPECTÉES
#   - Jamais de Stockfish lancé à la main : tout passe par moteurs.py (rôle « jeu »
#     pour le niveau mesuré, rôle « calibrage » pour la référence), donc par
#     engine.StockfishEngine. Deux Stockfish au plus, en priorité basse.
#   - Fin de partie : python-chess (mat, pat, matériel insuffisant, 3 et 5
#     répétitions, 50 et 75 coups). Rien n'est changé aux règles du jeu.
#   - Reprise : chaque partie finie est écrite dans tests/calibrage_elo/parties.json ;
#     relancer la commande continue là où on s'était arrêté (--recommencer pour
#     tout effacer). Aucune donnée du joueur n'est lue ni écrite.

import argparse
import datetime
import json
import math
import os
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess  # noqa: E402

import niveaux_elo  # noqa: E402

FICHIER_PARTIES = os.path.join(RACINE, "tests", "calibrage_elo", "parties.json")
FICHIER_RAPPORT = os.path.join(RACINE, "docs", "CALIBRAGE_ELO.md")
REF_MIN, REF_MAX = 1320, 3190          # bornes de UCI_Elo (Stockfish 18)
ANCRE_PARTIES_MIN = 8                  # un niveau sert d'échelon dès 8 parties
LN10_400 = math.log(10.0) / 400.0


# =========================================================== calcul de l'Elo

def score_attendu(elo, elo_adversaire):
    """Score espéré (0..1) d'un joueur `elo` contre `elo_adversaire`."""
    return 1.0 / (1.0 + 10.0 ** ((elo_adversaire - elo) / 400.0))


def performance(resultats):
    """Elo de performance par maximum de vraisemblance.

    resultats : [(elo_adversaire, score 0 / 0.5 / 1), ...]
    Renvoie {"elo", "marge" (95 %), "score", "parties", "borne"} ou None.
    borne = "min" si tout est gagné, "max" si tout est perdu (l'Elo n'est alors
    qu'une borne : on ajoute une nulle fictive contre l'adversaire moyen).
    """
    resultats = [(float(a), float(s)) for a, s in resultats]
    if not resultats:
        return None
    total = sum(s for _a, s in resultats)
    n = len(resultats)
    borne = None
    calcul = list(resultats)
    if total <= 0 or total >= n:
        borne = "min" if total >= n else "max"
        moyenne = sum(a for a, _s in resultats) / n
        calcul.append((moyenne, 0.5))

    def pente(x):
        return sum(s - score_attendu(x, a) for a, s in calcul)

    bas, haut = -2000.0, 6000.0
    for _ in range(80):
        milieu = (bas + haut) / 2.0
        if pente(milieu) > 0:
            bas = milieu
        else:
            haut = milieu
    elo = (bas + haut) / 2.0
    information = sum(score_attendu(elo, a) * (1.0 - score_attendu(elo, a))
                      for a, _s in calcul) * LN10_400 ** 2
    marge = 1.96 / math.sqrt(information) if information > 0 else 9999.0
    return {"elo": elo, "marge": marge, "score": total, "parties": n,
            "borne": borne}


def _monotone(points):
    """Points (consigne, mesuré) rendus croissants (moyenne des voisins qui se
    contredisent, méthode « pool adjacent violators »)."""
    blocs = []
    for x, y in sorted(points):
        blocs.append([[x], y, 1])
        while len(blocs) > 1 and blocs[-2][1] >= blocs[-1][1]:
            b = blocs.pop()
            a = blocs[-1]
            a[1] = (a[1] * a[2] + b[1] * b[2]) / (a[2] + b[2])
            a[0] += b[0]
            a[2] += b[2]
    sortie = []
    for xs, y, _n in blocs:
        sortie.append((sum(xs) / len(xs), y))
    return sortie


def proposer_table(mesures):
    """La table niveaux_elo.TABLE déduite des mesures.

    mesures : {consigne: {"elo", "marge", "borne"}, ...}
    Règle (demande de l'orchestre : ne rien changer sans preuve) : une consigne
    dont l'Elo mesuré tombe dans sa marge garde son Elo affiché = consigne. Les
    autres affichent l'Elo mesuré. Les bouts (100 et 3200) suivent le point
    mesuré le plus proche avec le même écart.
    Renvoie (table, changee) ; changee = False si la table reste l'identité.
    """
    points = []
    changee = False
    for x, m in sorted(mesures.items()):
        if m is None or m.get("borne"):
            continue                      # une borne n'est pas une mesure
        if abs(m["elo"] - x) <= m["marge"]:
            points.append((float(x), float(x)))
        else:
            points.append((float(x), float(m["elo"])))
            changee = True
    if not changee:
        # Rien de significatif : la table actuelle reste, on y note les mesures
        # des consignes qui y figurent déjà.
        table = []
        for affiche, consigne, mesure_, marge in niveaux_elo.TABLE:
            m = mesures.get(consigne)
            if m and not m.get("borne"):
                mesure_, marge = int(round(m["elo"])), int(round(m["marge"]))
            table.append((affiche, consigne, mesure_, marge))
        return table, False
    points = _monotone(points)
    lignes = []
    premier, dernier = points[0], points[-1]
    if premier[1] > niveaux_elo.ELO_MIN:
        ecart = premier[0] - premier[1]
        lignes.append((niveaux_elo.ELO_MIN, niveaux_elo.ELO_MIN + ecart))
    lignes.extend((y, x) for x, y in points)
    if dernier[1] < niveaux_elo.ELO_MAX:
        ecart = dernier[0] - dernier[1]
        lignes.append((niveaux_elo.ELO_MAX, niveaux_elo.ELO_MAX + ecart))
    table = []
    for affiche, consigne in lignes:
        affiche = int(round(affiche))
        consigne = int(round(max(100, min(3200, consigne))))
        if table and (affiche <= table[-1][0] or consigne <= table[-1][1]):
            continue                      # garde la table strictement croissante
        m = mesures.get(consigne)
        if m and not m.get("borne"):
            table.append((affiche, consigne, int(round(m["elo"])),
                          int(round(m["marge"]))))
        else:
            table.append((affiche, consigne, None, None))
    return table, changee


# ================================================================ cadences

def lire_cadence(texte):
    """« 120+1 » -> (120.0, 1.0). L'unité de la base dépend de l'option :
    SECONDES pour --cadence-ref, MINUTES pour --cadence-jeu ; l'incrément est
    toujours en secondes."""
    base, _, inc = str(texte).partition("+")
    return float(base.replace(",", ".")), float((inc or "0").replace(",", "."))


# ================================================================ joueurs

class _PenduleVue:
    """Ce que BackgroundAI lit de la pendule (comme timer.ChessTimer)."""

    def __init__(self, restant, increment_s):
        self.restant = restant           # {chess.WHITE: secondes, chess.BLACK: ...}
        self.increment = increment_s
        self.active = True

    def secondes_restantes(self, blancs):
        return max(0.1, self.restant[chess.WHITE if blancs else chess.BLACK])


class _PlateauVu:
    """Ce que BackgroundAI lit du plateau du jeu : .board et .timer."""

    def __init__(self, board, timer):
        self.board = board
        self.timer = timer


class JoueurNiveau:
    """Un niveau du jeu, joué par le VRAI fil de reflexion de BackgroundAI.

    Seule différence avec une partie : la pause « humaine » après le calcul
    n'est pas attendue (elle ne change rien à la force, seulement à l'heure).
    La pendule du niveau est une pendule de partie (--cadence-jeu) qui perd
    le budget « humain » tiré par BackgroundAI, comme à l'écran.
    """

    def __init__(self, moteur, consigne, minutes, increment_s, rythme_cle):
        import settings_screen
        from background_ai import BackgroundAI
        rythme = next((r for r in settings_screen.RYTHMES if r[1] == rythme_cle),
                      settings_screen.RYTHMES[1])
        self.moteur = moteur
        self.consigne = int(consigne)
        self.minutes = float(minutes)
        self.increment_s = float(increment_s)
        self.ia = BackgroundAI(None, moteur, temps_min_ms=rythme[2],
                               temps_max_ms=rythme[3], humain=rythme[1] != "rapide",
                               temps_moteur_max_ms=rythme[4])
        self.ia._attendre = lambda _secondes: True          # pas de pause
        tirer = self.ia._tirer_temps_de_reflexion

        def tirer_et_noter(board):
            self.dernier_budget_ms = tirer(board)
            return self.dernier_budget_ms
        self.ia._tirer_temps_de_reflexion = tirer_et_noter
        self.dernier_budget_ms = 0

    def nom(self):
        return "niveau %d" % self.consigne

    def preparer(self):
        self.moteur.nouvelle_partie()
        self.moteur.set_custom_elo(self.consigne, brut=True)
        self.ia.reprendre()
        secondes = self.minutes * 60.0
        self.pendule = {chess.WHITE: secondes, chess.BLACK: secondes}

    def jouer(self, board):
        couleur = board.turn
        timer = _PenduleVue(self.pendule, self.increment_s) if self.minutes > 0 else None
        self.ia.chessboard = _PlateauVu(board, timer)
        self.ia.pending_ai_move = None
        self.ia.is_thinking = True
        self.ia._ai_worker()
        coup = self.ia.pending_ai_move
        self.ia.pending_ai_move = None
        if self.minutes > 0:
            self.pendule[couleur] += self.increment_s - self.dernier_budget_ms / 1000.0
        return coup


class JoueurReference:
    """Stockfish bridé par UCI_Elo, qui gère sa pendule lui-même."""

    def __init__(self, moteur, elo, base_s, increment_s):
        self.moteur = moteur
        self.elo = int(max(REF_MIN, min(REF_MAX, elo)))
        self.base_s = float(base_s)
        self.increment_s = float(increment_s)

    def nom(self):
        return "Stockfish %d" % self.elo

    def preparer(self):
        self.moteur.nouvelle_partie()
        self.moteur.regler_threads(1)
        self.moteur.set_custom_elo(self.elo, brut=True)     # >= 1320 : UCI_Elo
        self.restant_ms = self.base_s * 1000.0

    def jouer(self, board):
        inc = self.increment_s * 1000.0
        debut = time.perf_counter()
        details = self.moteur.coup_a_la_pendule(board.fen(), self.restant_ms,
                                                self.restant_ms, inc, inc,
                                                chess960=False)
        self.restant_ms += inc - (time.perf_counter() - debut) * 1000.0
        self.restant_ms = max(100.0, self.restant_ms)        # pas de chute au temps
        if not details:
            return None
        try:
            return chess.Move.from_uci(details["coup"])
        except ValueError:
            return None


# ================================================================ une partie

def jouer_une_partie(blancs, noirs, demi_coups_max=400):
    """Joue une partie. Renvoie (score des Blancs ou None, fin, coups uci)."""
    board = chess.Board()
    blancs.preparer()
    noirs.preparer()
    while True:
        fin = board.outcome(claim_draw=True)
        if fin is not None:
            score = {True: 1.0, False: 0.0, None: 0.5}[fin.winner]
            return score, fin.termination.name.lower(), [c.uci() for c in board.move_stack]
        if len(board.move_stack) >= demi_coups_max:
            return 0.5, "limite_de_coups", [c.uci() for c in board.move_stack]
        joueur = blancs if board.turn == chess.WHITE else noirs
        coup = joueur.jouer(board)
        if coup is None or coup not in board.legal_moves:
            print("  ! %s n'a pas rendu de coup légal (%s) : partie annulée"
                  % (joueur.nom(), coup))
            return None, "annulee", [c.uci() for c in board.move_stack]
        board.push(coup)


# ================================================================ état

def charger_etat(chemin):
    try:
        with open(chemin, encoding="utf-8") as f:
            etat = json.load(f)
        if isinstance(etat, dict) and isinstance(etat.get("parties"), list):
            return etat
    except (OSError, ValueError):
        pass
    return {"parties": []}


def enregistrer_etat(chemin, etat):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    provisoire = chemin + ".tmp"
    with open(provisoire, "w", encoding="utf-8") as f:
        json.dump(etat, f, ensure_ascii=False, indent=1)
    os.replace(provisoire, chemin)


def mesurer(parties, tours=6):
    """{consigne: performance} à partir de toutes les parties enregistrées.

    Les parties contre un niveau-échelon utilisent l'Elo mesuré de cet échelon
    (recalculé en boucle jusqu'à stabilité)."""
    consignes = sorted({p["niveau"] for p in parties})
    elos = {}
    resultat = {}
    for _ in range(tours):
        resultat = {}
        for x in consignes:
            liste = []
            for p in parties:
                if p["niveau"] != x:
                    continue
                adv = p["adversaire"]
                if adv["type"] == "stockfish":
                    liste.append((adv["elo"], p["score"]))
                elif adv["consigne"] in elos:
                    liste.append((elos[adv["consigne"]], p["score"]))
                else:
                    liste.append((adv.get("elo", adv["consigne"]), p["score"]))
            resultat[x] = performance(liste)
        elos = {x: r["elo"] for x, r in resultat.items() if r and not r["borne"]}
    return resultat


def choisir_adversaire(consigne, parties, mesures):
    """L'adversaire le plus instructif : celui dont l'Elo est le plus proche de
    l'Elo estimé du niveau (au départ : sa consigne)."""
    m = mesures.get(consigne)
    estime = float(consigne)
    if m:
        # Les premières parties sont très bruitées : l'estimation est tirée
        # vers la consigne tant qu'il y a peu de parties (poids de 4 parties).
        n = m.get("parties", 0)
        estime = (m["elo"] * n + float(consigne) * 4) / (n + 4)
    cible = max(REF_MIN, min(REF_MAX, estime))
    meilleur = {"type": "stockfish", "elo": int(round(cible / 10.0) * 10)}
    ecart = abs(cible - estime)
    if estime < REF_MIN:
        for autre, r in mesures.items():
            if autre == consigne or not r or r["borne"]:
                continue
            nombre = sum(1 for p in parties if p["niveau"] == autre)
            if nombre >= ANCRE_PARTIES_MIN and abs(r["elo"] - estime) < ecart:
                ecart = abs(r["elo"] - estime)
                meilleur = {"type": "niveau", "consigne": autre,
                            "elo": int(round(r["elo"]))}
    return meilleur


# ================================================================ rapport

def ecrire_rapport(etat, chemin, reglages):
    parties = etat["parties"]
    mesures = mesurer(parties)
    table, changee = proposer_table(mesures)
    noms = {elo: nom for nom, elo in niveaux_elo.NIVEAUX}
    lignes = [
        "# Calibrage des niveaux de l'ordinateur (Elo mesuré)",
        "",
        "Fabriqué par `python outils/calibrer_elo.py` le %s. Ne pas modifier à la main."
        % datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "",
        "## Comment c'est mesuré",
        "",
        "- Chaque niveau joue avec **le vrai code du jeu** (moteur « jeu », `set_custom_elo`, "
        "choix maison sous 1320, livre d'ouvertures, temps de calcul de `BackgroundAI`), "
        "pendule de partie **%s** (rythme « %s »)." % (reglages["cadence_jeu"], reglages["rythme"]),
        "- Adversaires : **Stockfish bridé (`UCI_LimitStrength` + `UCI_Elo`, de 1320 à 3190)**, "
        "qui gère sa pendule à **%s** (Stockfish annonce son `UCI_Elo` calibré à 120 s + 1 s, "
        "ancré sur la liste CCRL 40/4), et, sous 1320, des niveaux du jeu déjà mesurés "
        "(échelons)." % reglages["cadence_ref"],
        "- Elo de performance par maximum de vraisemblance ; marge à 95 %. "
        "**Attention : c'est un Elo de moteurs (CCRL), pas un Elo FIDE ou Lichess humain.**",
        "- Parties enregistrées : %d (fichier `%s`)." % (len(parties), reglages["fichier"]),
        "",
        "## Résultat par niveau",
        "",
        "| Niveau | Consigne | Parties | Score | Adversaires | Elo mesuré | Écart | Verdict |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for x in sorted(mesures):
        m = mesures[x]
        if not m:
            continue
        adv = [p["adversaire"] for p in parties if p["niveau"] == x]
        elos_adv = [a.get("elo", 0) for a in adv]
        if m["borne"] == "min":
            texte_elo, verdict = "au moins %d" % m["elo"], "toutes gagnées : borne seulement"
        elif m["borne"] == "max":
            texte_elo, verdict = "au plus %d" % m["elo"], "toutes perdues : borne seulement"
        else:
            texte_elo = "%d ± %d" % (m["elo"], m["marge"])
            ecart = m["elo"] - x
            if abs(ecart) <= m["marge"]:
                verdict = "juste (dans la marge)"
            elif ecart > 0:
                verdict = "plus fort que sa consigne"
            else:
                verdict = "plus faible que sa consigne"
        lignes.append("| %s | %d | %d | %.1f / %d (%d %%) | %d – %d | %s | %+d | %s |" % (
            noms.get(x, "-"), x, m["parties"], m["score"], m["parties"],
            round(100.0 * m["score"] / m["parties"]), min(elos_adv), max(elos_adv),
            texte_elo, round(m["elo"] - x), verdict))
    lignes += [
        "",
        "## Table proposée pour `jeu/niveaux_elo.py`",
        "",
    ]
    if not changee:
        lignes += ["Aucun niveau ne s'écarte de sa consigne plus que la marge de mesure : "
                   "**on garde la table actuelle** (rien ne change pour le joueur).", ""]
    else:
        lignes += ["Au moins un niveau s'écarte de sa consigne : table à recopier "
                   "(Elo affiché, consigne envoyée au moteur, Elo mesuré, marge). "
                   "Puis `python tests/test_niveaux_elo.py`.", ""]
    lignes += ["```python",
               "ETALON = %r" % ("Stockfish UCI_Elo, cadence %s" % reglages["cadence_ref"]),
               "DATE_MESURE = %r" % datetime.date.today().isoformat(),
               "TABLE = ["]
    lignes += ["    %r," % (ligne,) for ligne in table]
    lignes += ["]", "```", ""]
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes))
    return mesures, table, changee


# ================================================================ programme

def main(arguments=None):
    aide = argparse.ArgumentParser(description="Mesure l'Elo réel des niveaux de l'ordinateur.")
    aide.add_argument("--parties", type=int, default=30,
                      help="parties par niveau (30 par défaut, toujours par paires blancs/noirs)")
    aide.add_argument("--niveaux", default="",
                      help="consignes à mesurer, ex. 400,800 (défaut : les 7 niveaux du menu)")
    aide.add_argument("--minutes", type=float, default=0,
                      help="budget en minutes ; 0 = jusqu'au bout (on reprend à la prochaine fois)")
    aide.add_argument("--cadence-ref", default="120+1",
                      help="pendule de Stockfish de référence, en SECONDES (défaut 120+1)")
    aide.add_argument("--cadence-jeu", default="5+0",
                      help="pendule du niveau mesuré, en MINUTES + secondes (défaut 5+0, "
                           "celle des Options)")
    aide.add_argument("--rythme", default="humain", choices=("rapide", "humain", "pose"))
    aide.add_argument("--demi-coups-max", type=int, default=400)
    aide.add_argument("--recommencer", action="store_true",
                      help="efface les parties déjà jouées")
    aide.add_argument("--rapport", action="store_true",
                      help="refait seulement docs/CALIBRAGE_ELO.md")
    aide.add_argument("--fichier", default=FICHIER_PARTIES)
    aide.add_argument("--sortie", default=FICHIER_RAPPORT)
    aide.add_argument("--stockfish", default=os.path.join(RACINE, "moteur", "stockfish.exe"))
    args = aide.parse_args(arguments)
    try:
        # Une ligne par partie, tout de suite, même redirigé dans un fichier.
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass

    reglages = {"cadence_ref": args.cadence_ref + " (s)", "cadence_jeu": args.cadence_jeu + " (min+s)",
                "rythme": args.rythme,
                "fichier": os.path.relpath(args.fichier, RACINE).replace(os.sep, "/")
                if os.path.splitdrive(args.fichier)[0].lower()
                == os.path.splitdrive(RACINE)[0].lower() else args.fichier}
    etat = {"parties": []} if args.recommencer else charger_etat(args.fichier)
    if args.rapport:
        ecrire_rapport(etat, args.sortie, reglages)
        print("Rapport : %s" % args.sortie)
        return 0

    if args.niveaux.strip():
        consignes = [int(v) for v in args.niveaux.replace(";", ",").split(",") if v.strip()]
    else:
        consignes = [niveaux_elo.consigne(elo) for _nom, elo in niveaux_elo.NIVEAUX]
    consignes = sorted(set(consignes), reverse=True)    # du plus fort au plus faible
    ref_base, ref_inc = lire_cadence(args.cadence_ref)
    jeu_min, jeu_inc = lire_cadence(args.cadence_jeu)

    # Le réglage personnel « taux_de_gaffe » et l'arrêt du livre (config.json)
    # ne doivent pas fausser la mesure : on mesure le jeu tel qu'il est livré.
    import faiblesse
    import moteurs
    from background_ai import BackgroundAI
    faiblesse._REGLAGE = 1.0
    BackgroundAI._LIVRE_DEMANDE = True

    debut = time.time()
    limite = debut + args.minutes * 60.0 if args.minutes > 0 else None
    moteur_jeu = moteurs.moteur_de_jeu(args.stockfish)
    moteur_ref, _neuf = moteurs._obtenir("calibrage", args.stockfish, True,
                                         apres_creation=moteurs._priorite_basse)
    if moteur_jeu is None or moteur_ref is None:
        print("Stockfish introuvable : %s" % args.stockfish)
        return 2
    moteurs._priorite_basse(moteur_jeu)
    threads_jeu = getattr(moteur_jeu, "threads_courant", None) or 1
    print("Calibrage : niveaux %s, %d parties chacun, référence %s s, jeu %s min"
          % (consignes, args.parties, args.cadence_ref, args.cadence_jeu))

    jouees = 0
    try:
        while True:
            restants = [x for x in consignes
                        if sum(1 for p in etat["parties"] if p["niveau"] == x) < args.parties]
            if not restants:
                break
            arret = False
            for x in restants:
                # Une paire = le même adversaire avec les deux couleurs.
                adv = choisir_adversaire(x, etat["parties"], mesurer(etat["parties"]))
                for couleur in ("blancs", "noirs"):
                    if limite is not None and time.time() >= limite:
                        arret = True
                        break
                    niveau = JoueurNiveau(moteur_jeu, x, jeu_min, jeu_inc, args.rythme)
                    if adv["type"] == "stockfish":
                        autre = JoueurReference(moteur_ref, adv["elo"], ref_base, ref_inc)
                    else:
                        moteur_ref.regler_threads(threads_jeu)
                        autre = JoueurNiveau(moteur_ref, adv["consigne"], jeu_min,
                                             jeu_inc, args.rythme)
                    blancs, noirs = (niveau, autre) if couleur == "blancs" else (autre, niveau)
                    t0 = time.time()
                    score_blancs, fin, coups = jouer_une_partie(blancs, noirs,
                                                                args.demi_coups_max)
                    if score_blancs is None:
                        continue
                    score = score_blancs if couleur == "blancs" else 1.0 - score_blancs
                    etat["parties"].append({
                        "niveau": x, "adversaire": adv, "couleur": couleur,
                        "score": score, "fin": fin, "demi_coups": len(coups),
                        "duree_s": round(time.time() - t0, 1),
                        "date": datetime.datetime.now().isoformat(timespec="seconds"),
                        "cadence_ref": args.cadence_ref, "cadence_jeu": args.cadence_jeu,
                        "rythme": args.rythme, "coups": " ".join(coups)})
                    enregistrer_etat(args.fichier, etat)
                    jouees += 1
                    print("  %-10s (%s) contre %-14s : %s  [%s, %d demi-coups, %.0f s]"
                          % ("niveau %d" % x, couleur, autre.nom(),
                             {1.0: "gagne", 0.5: "nulle", 0.0: "perd"}[score], fin,
                             len(coups), time.time() - t0))
                if arret:
                    break
            if arret:
                print("Budget de %.0f min atteint : on reprendra ici." % args.minutes)
                break
    except KeyboardInterrupt:
        print("Arrêté (Ctrl+C) : les parties finies sont gardées.")
    finally:
        moteurs.liberer("calibrage")
        moteurs.liberer("jeu")

    mesures, table, changee = ecrire_rapport(etat, args.sortie, reglages)
    print()
    print("%d partie(s) jouée(s) en %.1f min. Rapport : %s"
          % (jouees, (time.time() - debut) / 60.0, args.sortie))
    for x in sorted(mesures):
        m = mesures[x]
        if m:
            print("  consigne %4d : %s%d ± %d  (%d parties, %.1f pts)"
                  % (x, {"min": ">= ", "max": "<= "}.get(m["borne"], ""), m["elo"],
                     m["marge"], m["parties"], m["score"]))
    print("Table %s." % ("à changer (voir le rapport)" if changee else "inchangée"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
