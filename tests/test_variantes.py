# tests/test_variantes.py - jouer des variantes dans la revue (17/10).
#     python tests/test_variantes.py      (Stockfish necessaire)

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
    with open("config.json", encoding="utf-8") as f:
        sf = json.load(f).get("stockfish_path", "moteur/stockfish.exe")
try:
    from engine import StockfishEngine
    StockfishEngine(sf).quit()
except Exception:
    print("Pas de Stockfish utilisable : test saute.")
    sys.exit(0)

from analyse_partie import AnalyseurPartie
from ecran_revue import EcranRevue
import board_geometry as geo

BERGER = ["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"]
a = AnalyseurPartie(None, BERGER, sf, "rapide")
r = EcranRevue(ecran, a, {"theme_plateau": "tournoi"}, ("Toi", "Ordinateur"), "1-0")
p = r.plateau


def attendre(condition, secondes=40):
    fin = time.time() + secondes
    while time.time() < fin:
        r.draw()
        if condition():
            return True
        time.sleep(0.05)
    return False


# 17/10 (Julien : « Stockfish joue a ma place dans la revue, il ne doit
# jamais jouer, seulement proposer le meilleur coup »).
print("1. Le coup de la partie fait avancer la revue")
verifier(p.make_move(chess.Move.from_uci("e2e4")) and r.index == 1 and r.variante is None,
         "e4 joue sur l'echiquier : coup 1 de la partie")

print("2. Fleches bleues : le meilleur coup de la position affichee")
r.aller_a(4, son=False)                 # apres 2...Nc6, les Blancs au trait
verifier(attendre(lambda: bool(p.fleches_conseil)),
         "fleche du meilleur coup (%s)" % [c["san"] for c in r.coups_conseilles()])
r.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b, mod=0, unicode=""))
r.draw()
verifier(not p.fleches_conseil, "touche B : fleches cachees")
r.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b, mod=0, unicode=""))

print("3. Une variante : on joue les deux camps, Stockfish NE JOUE PAS")
r.aller_a(5, son=False)                 # apres 3. Dh5, les Noirs au trait
verifier(p.make_move(chess.Move.from_uci("g7g6")) and r.variante == [chess.Move.from_uci("g7g6")],
         "3...g6 au lieu de 3...Cf6 : variante ouverte")
verifier(attendre(lambda: r.texte_eval_variante not in ("", "...")
                  and bool(r.coups_conseilles())),
         "evaluation (%s) et meilleurs coups (%s)" % (
             r.texte_eval_variante, [c["san"] for c in r.coups_conseilles()]))
time.sleep(1.0)
r.draw()
verifier(r.variante == [chess.Move.from_uci("g7g6")],
         "Stockfish n'a joue aucun coup a ta place")
verifier(p.board.turn == chess.WHITE, "c'est toujours aux Blancs de jouer")
verifier(bool(p.fleches_conseil), "fleches des meilleurs coups dans la variante")
verifier(p.make_move(chess.Move.from_uci("h5f3")) and len(r.variante) == 2,
         "tu joues aussi le coup des Blancs")
verifier(r.texte_de_la_variante().startswith("3... g6 4."), "texte : %s" % r.texte_de_la_variante())
verifier(p.pastille_coup is None and p.indice is None, "pas de pastille dans une variante")
r.draw()
pygame.image.save(ecran, os.path.join("tests", "capture_variante.png"))
r.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT, mod=0, unicode=""))
verifier(r.variante == [chess.Move.from_uci("g7g6")], "fleche gauche : un coup annule")

print("4. Echap ramene a la partie")
r.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode=""))
verifier(r.variante is None and r.index == 5 and p.board.fen() == a.fens[5],
         "retour a la position de la partie")

print("4 bis. Clic sur un coup de la feuille (Cowork, t65 : « ne fait rien » sur le PC)")
r.aller_a(0, son=False)
r.draw()
bons = 0
for rect, index in list(r.rects_coups):
    for genre in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        r.handle_event(pygame.event.Event(genre, button=1, pos=rect.center))
    bons += r.index == index + 1
    r.draw()
verifier(r.rects_coups and bons == len(r.rects_coups),
         "chaque coup clique dans la feuille s'affiche (%d / %d)" % (bons, len(r.rects_coups)))
d = r.disposition
case_g1 = (d.plateau_x + 6 * d.taille_case + d.taille_case // 2, d.plateau_y + 7 * d.taille_case + d.taille_case // 2)
if p.flipped:
    case_g1 = (d.plateau_x + d.taille_case + d.taille_case // 2, d.plateau_y + d.taille_case // 2)
r.aller_a(2, son=False)
r.draw()
for genre in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
    r.handle_event(pygame.event.Event(genre, button=1, pos=case_g1))
rect, index = r.rects_coups[5]
for genre in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
    r.handle_event(pygame.event.Event(genre, button=1, pos=rect.center))
verifier(r.index == index + 1 and p.selected_square is None,
         "une piece selectionnee : le 1er clic sur un coup marche quand meme (%d, voulu %d)" % (r.index, index + 1))
r.aller_a(0, son=False)

print("5. Exporter la revue (PGN annote)")
import tempfile
import chess.pgn
import io
verifier(attendre(a.terminee, 120), "analyse terminee")
dossier = tempfile.mkdtemp()
chemin = r.exporter(dossier)
verifier(chemin is not None and os.path.exists(chemin), "fichier ecrit : %s" % chemin)
if chemin:
    texte = open(chemin, encoding="utf-8").read()
    jeu = chess.pgn.read_game(io.StringIO(texte))
    verifier(jeu is not None and len(list(jeu.mainline_moves())) == len(BERGER),
             "le PGN se relit (python-chess)")
    verifier("[%eval" in texte, "evaluations au format [%eval]")
    verifier("WhiteAccuracy" in jeu.headers, "precision dans l'en-tete")
    print(texte[:400])
verifier(r.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0,
                                           unicode="")) == "retour",
         "Echap quitte la revue")

a.arreter()
import moteurs
moteurs.tout_fermer()
print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
