# tests/test_analyse_directe.py - seance du 17/10.
#     python tests/test_analyse_directe.py
# Avec SICKCHESS_STOCKFISH (ou moteur/stockfish.exe sous Windows) pour la partie
# "analyse en direct". Rien n'est ecrit dans le profil ni dans config.json.

import os
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import json
import chess
import pygame

pygame.init()
pygame.display.set_mode((1024, 640))

import annotations
import apparence
import notation

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


print("1. Le materiel compte (une dame donnee n'est pas une imprecision)")
base = dict(chances_avant=15.0, chances_apres=3.0, meilleur_connu=True)
verifier(annotations.classer(12.0, **base) == "imprecision",
         "sans le materiel : 12 points de chances = imprecision")
verifier(annotations.classer(12.0, perte_pions=9.0, apres_pions=-14.0, **base) == "gaffe",
         "dame donnee dans une position perdue : gaffe")
verifier(annotations.classer(3.0, perte_pions=2.5, apres_pions=-1.0, **base) == "erreur",
         "2,5 pions perdus : au moins erreur")
verifier(annotations.classer(1.0, perte_pions=6.0, apres_pions=8.0, chances_avant=99.5,
                             chances_apres=98.5, meilleur_connu=True) == "imprecision",
         "position toujours ecrasante (+8) : pas plus qu'une imprecision")
verifier(annotations.classer(0.0, est_le_meilleur=True, perte_pions=5.0, apres_pions=-10.0,
                             **base) == "meilleur",
         "le coup du moteur n'est jamais puni")
verifier(annotations.classer(4.0, perte_pions=0.4, apres_pions=0.0, **base) == "bon",
         "petite perte : reste bon")

print("2. Notation au choix")
# (comme l'ecran Options : on modifie les preferences en memoire)
prefs = apparence.preferences()
origine = prefs.get("notation")
prefs["notation"] = "anglaise"
verifier(notation.afficher("Nxf7+") == "Nxf7+", "anglaise par defaut : Nxf7+")
prefs["notation"] = "francaise"
verifier(notation.afficher("Nxf7+") == "Cxf7+", "francaise : Cxf7+")
verifier(notation.afficher("e8=Q#") == "e8=D#", "francaise : e8=D#")
verifier(notation.afficher("Kxe2") == "Rxe2" and notation.afficher("Rxe2") == "Txe2",
         "francaise : roi = R, tour = T (sans confusion)")
verifier(notation.afficher("O-O-O") == "O-O-O", "le roque ne change pas")
verifier(notation.afficher_ligne("Qxh7+ Kxh7 Rh3#") == "Dxh7+ Rxh7 Th3#", "une ligne entiere")
if origine is None:
    prefs.pop("notation", None)
else:
    prefs["notation"] = origine
verifier(notation.choix() == "anglaise", "retour au reglage d'origine (anglaise)")

print("3. Analyse en direct pendant la partie")
sf = os.environ.get("SICKCHESS_STOCKFISH")
if not sf:
    with open("config.json", encoding="utf-8") as f:
        sf = json.load(f).get("stockfish_path", "moteur/stockfish.exe")
try:
    from engine import StockfishEngine
    StockfishEngine(sf).quit()
except Exception:
    sf = None
if not sf:
    print("  (pas de Stockfish utilisable ici : partie 3 sautee)")
else:
    import game_manager
    from game_manager import GameManager
    game_manager.enregistrer_la_partie = lambda plateau, mode: None   # profil intact
    import sauvegarde
    sauvegarde.effacer = lambda: None
    sauvegarde.enregistrer = lambda *a, **k: None
    gm = GameManager("test")
    gm.stockfish_path = sf
    gm.config["analyse_puissance"] = "rapide"
    gm.config["analyse_pendant_partie"] = True
    gm.game_mode = "hotseat"
    gm.reglages = {"pendule_active": False}
    gm.preparer_partie()
    BERGER = ["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"]
    for uci in BERGER[:4]:
        gm.board.make_move(chess.Move.from_uci(uci))
    gm._suivre_analyse(force=True)
    direct = gm.analyse_en_direct
    verifier(direct is not None and direct.suivi, "l'analyse demarre des les premiers coups")
    attente = time.time() + 15
    while direct.niveau[1] < 1 and time.time() < attente and not direct.erreur:
        time.sleep(0.2)
    print("   (premiere position analysee en %.1f s, erreur=%s)" % (15 - (attente - time.time()), direct.erreur))
    verifier(direct.niveau[1] >= 1, "les premieres positions sont deja analysees pendant la partie")
    for uci in BERGER[4:]:
        gm.board.make_move(chess.Move.from_uci(uci))
        gm._suivre_analyse(force=True)
    verifier(direct.nombre_de_coups() == len(BERGER), "les coups suivants s'ajoutent (%d)" % direct.nombre_de_coups())
    fin_attente = time.time() + 3
    while not gm.board.game_over and time.time() < fin_attente:
        gm.board.update(); time.sleep(0.02)
    gm._partie_terminee()
    fin = gm.board.end_screen
    verifier(fin.analyseur is direct, "la carte de fin reprend l'analyse faite pendant la partie")
    verifier(not direct.suivi, "le suivi est termine")
    attente = time.time() + 90
    while direct.en_cours and time.time() < attente:
        time.sleep(0.2)
    verifier(direct.terminee(), "analyse terminee")
    verifier(direct.detail(5)["note"] in ("gaffe", "erreur", "manque"),
             "6...Cf6?? (laisse le mat) est une faute : %s" % direct.detail(5)["note"])
    verifier(fin.ligne_analyse().startswith("Précision"), "precision affichee : %s" % fin.ligne_analyse())
    gm.cleanup_game()
    verifier(getattr(gm, "analyse_en_direct", None) is None, "rien ne tourne apres la partie")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
