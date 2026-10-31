# tests/test_finales_dtz.py - tables de finale DTZ (.rtbz) a cote des WDL (31/10).
#     python tests/test_finales_dtz.py      (Stockfish + dossier syzygy/ necessaires)
#
# 1. Stockfish annonce les tables trouvees (145 WDL et 145 DTZ chez Julien).
# 2. Roi + dame contre roi : le moteur d'analyse va au mat, sans repetition.
# 3. Regle des 50 coups : roi + fou + cavalier gagne avec le compteur a 0,
#    nulle avec le compteur a 60 (le mat demande plus de 40 coups).
# 4. Sans .rtbz (ami sans le paquet) : WDL seuls, tout marche comme avant ;
#    sans dossier du tout : rien, et l'analyse marche.

import json
import os
import shutil
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import chess

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


sf = os.environ.get("SICKCHESS_STOCKFISH")
if not sf:
    try:
        with open("config.json", encoding="utf-8") as f:
            sf = json.load(f).get("stockfish_path", "moteur/stockfish.exe")
    except (OSError, ValueError):
        sf = os.path.join("moteur", "stockfish.exe")
try:
    from engine import StockfishEngine
    StockfishEngine(sf).quit()
except Exception:
    print("Pas de Stockfish utilisable : test saute.")
    sys.exit(0)

import analyse_continue

SYZYGY = os.path.join(RACINE, "syzygy")
noms = os.listdir(SYZYGY) if os.path.isdir(SYZYGY) else []
WDL = sorted(n for n in noms if n.endswith(".rtbw"))
DTZ = sorted(n for n in noms if n.endswith(".rtbz"))
if not WDL:
    print("Pas de dossier syzygy/ (cloud, ami sans le paquet) : test saute.")
    sys.exit(0)

TEMP = tempfile.mkdtemp(prefix="sickchess_dtz_")
SEULS_WDL = os.path.join(TEMP, "syzygy_wdl")
os.makedirs(SEULS_WDL)
for n in WDL:                    # liens : pas 380 Mo de copie
    try:
        os.link(os.path.join(SYZYGY, n), os.path.join(SEULS_WDL, n))
    except OSError:
        shutil.copy2(os.path.join(SYZYGY, n), os.path.join(SEULS_WDL, n))


def moteur(dossier):
    """Moteur d'analyse branche sur ce dossier de tables (None = aucun)."""
    StockfishEngine.DOSSIER_TABLES = dossier or os.path.join(TEMP, "absent")
    m = StockfishEngine(sf)
    m.configurer_pour_analyse(threads=2, hash_mb=64)
    return m


def jouer_jusqu_au_bout(m, fen, demi_coups=80, noeuds=200000):
    """Le moteur joue les deux camps ; rend le plateau a la fin."""
    b = chess.Board(fen)
    while not b.is_game_over(claim_draw=True) and len(b.move_stack) < demi_coups:
        r = m.analyser_position(b.fen(), noeuds=noeuds, temps_max_ms=5000)
        if not r:
            break
        b.push_uci(r["coup"])
    return b


def score(m, fen):
    r = m.analyser_position(fen, noeuds=500000, temps_max_ms=8000)
    return r["evaluation"], r["mat"]


KBN = "8/8/8/4k3/8/8/8/1BN1K3 w - - %d 1"

try:
    if DTZ:
        print("1. Stockfish annonce les tables DTZ")
        m = moteur("syzygy")
        verifier(m.tables_trouvees == (len(WDL), len(DTZ)),
                 "annonce : %s (attendu %d WDL et %d DTZ)"
                 % (m.tables_trouvees, len(WDL), len(DTZ)))
        verifier(len(DTZ) == len(WDL), "un .rtbz pour chaque .rtbw (%d / %d)"
                 % (len(DTZ), len(WDL)))

        print("2. Roi + dame contre roi : droit au mat, sans tourner en rond")
        b = jouer_jusqu_au_bout(m, "8/8/8/4k3/8/8/8/3QK3 w - - 0 1")
        verifier(b.is_checkmate() and b.turn == chess.BLACK,
                 "mat des Blancs (%s)" % b.fen())
        coups = (len(b.move_stack) + 1) // 2
        verifier(coups <= 12, "mat en %d coups blancs (au plus 12)" % coups)
        rejoue, vues = chess.Board("8/8/8/4k3/8/8/8/3QK3 w - - 0 1"), set()
        repetee = False
        for coup in b.move_stack:
            cle = rejoue.board_fen() + (" w" if rejoue.turn else " b")
            repetee = repetee or cle in vues
            vues.add(cle)
            rejoue.push(coup)
        verifier(not repetee, "aucune position repetee")

        print("3. Regle des 50 coups (roi + fou + cavalier)")
        ev0, mat0 = score(m, KBN % 0)
        verifier(mat0 is not None and mat0 > 0 or (ev0 or 0) > 50,
                 "compteur a 0 : les Blancs gagnent (eval %s, mat %s)" % (ev0, mat0))
        ev60, mat60 = score(m, KBN % 60)
        verifier(mat60 is None and ev60 is not None and abs(ev60) < 1.0,
                 "compteur a 60 : nulle par la regle des 50 coups (eval %s, mat %s)"
                 % (ev60, mat60))
        verifier(analyse_continue.finale_des_tables(chess.Board(KBN % 0), SYZYGY)
                 == "Tables de finale : les Blancs gagnent",
                 "verdict affiche, compteur a 0 : les Blancs gagnent")
        verifier(analyse_continue.finale_des_tables(chess.Board(KBN % 60), SYZYGY)
                 == "Tables de finale : nulle",
                 "verdict affiche, compteur a 60 : nulle (50 coups)")
        m.quit()
    else:
        print("1-3. Pas de .rtbz dans syzygy/ : parties DTZ sautees")

    print("4. Sans .rtbz : WDL seuls, comme avant")
    m = moteur(SEULS_WDL)
    verifier(m.tables_trouvees == (len(WDL), 0),
             "annonce : %s (attendu %d WDL et 0 DTZ)" % (m.tables_trouvees, len(WDL)))
    r = m.analyser_position("8/8/8/4k3/8/8/4P3/4K3 w - - 0 1", noeuds=200000)
    verifier(r is not None and r["mat"] is None and abs(r["evaluation"]) < 1.0,
             "roi + pion contre roi bloque : nulle (%s)" % (r and r["evaluation"]))
    b = jouer_jusqu_au_bout(m, "8/8/8/4k3/8/8/8/3QK3 w - - 0 1")
    verifier(b.is_checkmate(), "roi + dame contre roi : mat quand meme (%d demi-coups)"
             % len(b.move_stack))
    verifier(analyse_continue.finale_des_tables(chess.Board(KBN % 60), SEULS_WDL)
             == "Tables de finale : les Blancs gagnent",
             "verdict affiche sans DTZ : WDL seul, comme avant")
    m.quit()

    print("5. Sans dossier syzygy/ : rien, et l'analyse marche")
    m = moteur(None)
    verifier(m.tables_trouvees is None, "aucune table annoncee")
    r = m.analyser_position(chess.STARTING_FEN, noeuds=100000)
    verifier(r is not None and r.get("coup"), "analyse de la position de depart")
    verifier(analyse_continue.finale_des_tables(chess.Board(KBN % 0),
                                                os.path.join(TEMP, "absent")) is None,
             "aucun verdict de tables")
    m.quit()
finally:
    StockfishEngine.DOSSIER_TABLES = "syzygy"
    for tables in analyse_continue._TABLES.values():
        tables.close()
    analyse_continue._TABLES.clear()
    shutil.rmtree(TEMP, ignore_errors=True)

print()
if echecs:
    print("%d ECHEC(S)" % len(echecs))
    sys.exit(1)
print("Tout est bon.")
