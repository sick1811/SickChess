# tests/test_analyse_libre_moteur.py - l'analyse libre avec le vrai Stockfish
# (24/10, travail p35).
#     python tests/test_analyse_libre_moteur.py      (Stockfish necessaire)

import json
import os
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import pygame

pygame.init()
ecran = pygame.display.set_mode((1024, 640))
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
import moteurs
from ecran_analyse_libre import EcranAnalyseLibre


def attendre(condition, secondes=30):
    fin = time.time() + secondes
    while time.time() < fin:
        e.draw()
        if condition():
            return True
        time.sleep(0.05)
    return False


print("1. Stockfish reflechit sur la position, 3 lignes")
e = EcranAnalyseLibre(ecran, {}, stockfish_path=sf, threads=2)
verifier(attendre(lambda: len(e.lignes()) == 3), "3 lignes au depart (%s)"
         % [(l["san"], l["texte"]) for l in e.lignes()])
verifier(attendre(lambda: e.analyse.resultat()["profondeur"] >= 14),
         "la profondeur monte (%d)" % e.analyse.resultat()["profondeur"])
verifier(abs(e.lignes()[0]["evaluation"]) < 1.0, "position de depart : a peu pres egale (%s)"
         % e.lignes()[0]["texte"])
verifier(moteurs.roles_vivants() == [analyse_continue.ROLE],
         "un seul Stockfish pour l'analyse libre (%s)" % moteurs.roles_vivants())

print("2. Juste : le mat en 1 et la piece en prise")
e.coller_texte("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1")
debut = time.time()
verifier(attendre(lambda: e.lignes() and e.lignes()[0]["texte"] == "M1", 10),
         "mat en 1 trouve : %s (%s)" % (e.lignes()[0]["san"] if e.lignes() else "-",
                                       e.lignes()[0]["texte"] if e.lignes() else "-"))
verifier(time.time() - debut < 3, "en moins de 3 s apres le changement (%.1f s)" % (time.time() - debut))
verifier(e.texte_d_une_ligne(e.lignes()[0]) == "1. Ra8#", "ligne lisible : %s"
         % e.texte_d_une_ligne(e.lignes()[0]))
e.draw()
verifier(e.plateau.fleches_conseil and e.plateau.fleches_conseil[0][:2] == (chess.A1, chess.A8),
         "fleche bleue a1 -> a8")
# La dame noire en prise : les Blancs la prennent.
e.coller_texte("rnb1kbnr/pppp1ppp/8/4p3/4P2q/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3")
verifier(attendre(lambda: e.lignes() and e.analyse.resultat()["profondeur"] >= 12, 15)
         and e.lignes()[0]["san"] == "Nxh4", "la dame en prise est prise : %s (%s)"
         % (e.lignes()[0]["san"], e.lignes()[0]["texte"]))
verifier(e.lignes()[0]["evaluation"] > 5, "et les Blancs sont nettement mieux (%s)"
         % e.lignes()[0]["texte"])

print("3. Les deux camps : Stockfish suit chaque coup")
e.coller_texte("1. e4 e5 *")
e.aller_a(2)
e.plateau.make_move(chess.Move.from_uci("g1f3"))
verifier(attendre(lambda: e.lignes() and e.plateau.board.turn == chess.BLACK
                  and chess.Move.from_uci(e.lignes()[0]["uci"]) in e.plateau.board.legal_moves, 10),
         "apres Cf3, les lignes sont des coups noirs (%s)" % (e.lignes()[0]["san"] if e.lignes() else "-"))

print("4. Arret tout seul (pas de chauffe inutile)")
analyse_continue.DUREE_MAX_S = 2
e.coller_texte("8/8/8/4k3/8/8/4P3/4K3 w - - 0 1")
verifier(attendre(lambda: e.analyse.resultat()["fini"], 15),
         "analyse terminee : %s" % e.etat_du_moteur())
verifier("terminée" in e.etat_du_moteur(), "la ligne d'etat le dit")
analyse_continue.DUREE_MAX_S = 60

print("5. En sortant, Stockfish est ferme")
e.analyse.arreter()
fin = time.time() + 5
while time.time() < fin and moteurs.roles_vivants():
    time.sleep(0.1)
verifier(moteurs.roles_vivants() == [], "plus aucun Stockfish (%s)" % moteurs.roles_vivants())

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
