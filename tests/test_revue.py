# tests/test_revue.py - verifie la revue de partie sans ouvrir de fenetre.
#     python tests/test_revue.py
# Stockfish : celui de config.json (moteur/stockfish.exe sous Windows), ou
# celui indique par la variable SICKCHESS_STOCKFISH. Sans Stockfish, seule la
# partie "sans moteur" est testee.
# Teste : l'analyse (pastilles, gaffe reperee, precision, mat), la priorite au
# coup regarde, l'ecran de revue (navigation, dessin a plusieurs tailles), la
# carte de fin (bouton Revue, ligne de precision) et le passage
# fin de partie -> revue -> retour dans le vrai game_manager.

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

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
ecran = pygame.display.set_mode((1024, 640))

import annotations
from analyse_partie import AnalyseurPartie
from ecran_revue import EcranRevue

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def chemin_stockfish():
    chemin = os.environ.get("SICKCHESS_STOCKFISH")
    if not chemin:
        with open("config.json", encoding="utf-8") as f:
            chemin = json.load(f).get("stockfish_path", "moteur/stockfish.exe")
    if not os.path.exists(chemin):
        return None
    try:
        from engine import StockfishEngine
        StockfishEngine(chemin).quit()
        return chemin
    except Exception:
        return None


def attendre(analyseur, secondes=120):
    fin = time.time() + secondes
    while analyseur.en_cours and time.time() < fin:
        time.sleep(0.2)


# Une partie de club : le Fegatello, puis 10...Cd3+?? qui perd une piece.
PARTIE = ("e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 f3g5 d7d5 e4d5 f6d5 g5f7 e8f7 d1f3 "
          "f7e6 b1c3 c6b4 f3e4 c7c6 d2d4 b4d3").split()
MAT_DU_BERGER = "e2e4 e7e5 f1c4 b8c6 d1h5 g8f6 h5f7".split()


class MoteurFactice:
    """Toujours +0.20 et le premier coup legal : pour tester sans Stockfish."""
    def analyser_position(self, fen, profondeur=0, temps_max_ms=0, lignes=1):
        coup = next(iter(chess.Board(fen).legal_moves))
        return {"coup": coup.uci(), "evaluation": 0.2, "mat": None,
                "second_evaluation": 0.1, "second_mat": None}


print("1. Analyse sans moteur (moteur factice)")
a = AnalyseurPartie(None, PARTIE, moteur=MoteurFactice())
a.demarrer(); attendre(a)
verifier(a.terminee() and a.erreur is None, "analyse terminee sans erreur")
verifier(all(n is not None for n in a.notes()), "une pastille pour chaque coup")
verifier(a.rapport()["blancs"]["precision"] is not None, "precision calculee")
verifier(a.nombre_de_coups() == len(PARTIE), "%d coups relus" % len(PARTIE))

print("2. Coups refuses et partie vide")
b = AnalyseurPartie(None, ["e2e4", "e2e4", "d7d5"], moteur=MoteurFactice())
verifier(b.nombre_de_coups() == 1, "lecture arretee au premier coup illegal")
vide = AnalyseurPartie(None, [], moteur=MoteurFactice())
verifier(vide.rapport()["blancs"]["precision"] is None, "partie vide : pas de precision")

print("3. Sacrifices (pastille Brillant)")
p = chess.Board()
for san in "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5 d5 exd5 Nxd5 Nxf7 Kxf7 Qf3+ Ke6".split():
    p.push_san(san)
verifier(not annotations.est_un_sacrifice(p, p.parse_san("Nc3")),
         "Cc3 defendu par un pion n'est PAS un sacrifice")
p2 = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 2 3")
verifier(annotations.est_un_sacrifice(p2, p2.parse_san("Bxf7+")),
         "Fxf7+ (piece donnee contre un pion) est un sacrifice")

print("4. Ecran de revue")
r = EcranRevue(ecran, a, {"theme_plateau": "marron"}, ("Toi", "Ordinateur"), "0-1")
verifier(r.index == 0, "s'ouvre sur la position de depart")
for touche in (pygame.K_HOME, pygame.K_RIGHT, pygame.K_RIGHT, pygame.K_LEFT):
    r.handle_event(pygame.event.Event(pygame.KEYDOWN, key=touche))
verifier(r.index == 1, "fleches et Debut : coup 1 (%d)" % r.index)
verifier(r.plateau.board.fen() == a.fens[1], "l'echiquier montre la bonne position")
plantages = 0
for taille in ((1024, 640), (900, 560), (1600, 900), (1920, 1080)):
    ecran = pygame.display.set_mode(taille)
    r._placer(ecran)
    for i in range(len(PARTIE) + 1):
        r.aller_a(i, son=False)
        try:
            r.draw()
        except Exception as e:
            plantages += 1
            print("    %s coup %d : %s" % (taille, i, e))
verifier(plantages == 0, "dessin de chaque coup a 4 tailles de fenetre")
verifier(r.disposition.barre.right < r.disposition.plateau_x,
         "la barre d'avantage ne mord pas sur l'echiquier")
r.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f))
verifier(r.plateau.flipped, "F retourne l'echiquier")
verifier(r.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
         == "retour", "Echap = retour")
ecran = pygame.display.set_mode((1024, 640))

sf = chemin_stockfish()
print("5. Analyse avec Stockfish : %s" % (sf or "INTROUVABLE, partie sautee"))
if sf:
    debut = time.time()
    a = AnalyseurPartie(None, PARTIE, sf, "rapide")
    a.prioriser(19)
    a.demarrer()
    while a.en_cours and not a.detail(19)["pret"] and time.time() - debut < 30:
        time.sleep(0.05)
    delai = time.time() - debut
    verifier(a.detail(19)["pret"], "coup regarde juge en %.1f s (priorite)" % delai)
    attendre(a)
    verifier(a.terminee() and not a.erreur, "analyse terminee en %.1f s"
             % (time.time() - debut))
    d = a.detail(19)
    verifier(d["note"] == "gaffe", "10...Cd3+ est une gaffe (%s)" % d["note"])
    verifier(d["meilleur_san"] is not None and d["meilleur_san"] != "Nd3+",
             "un meilleur coup est propose (%s)" % d["meilleur_san"])
    verifier(a.detail(0)["note"] == "theorique", "1.e4 est un coup de theorie")
    rapport = a.rapport()
    verifier(rapport["blancs"]["precision"] > rapport["noirs"]["precision"],
             "precision Blancs %.1f > Noirs %.1f" % (rapport["blancs"]["precision"],
                                                     rapport["noirs"]["precision"]))
    verifier(any(m["index"] == 19 for m in rapport["moments_cles"]),
             "la gaffe figure dans les moments cles")
    m = AnalyseurPartie(None, MAT_DU_BERGER, sf, "rapide")
    m.demarrer(); attendre(m)
    verifier(m.texte_evaluation(len(MAT_DU_BERGER)) == "Mat",
             "mat du berger : position finale = Mat")
    verifier(m.detail(5)["note"] in ("gaffe", "erreur", "manque"),
             "6...Cf6?? (laisse le mat) est une faute (%s)" % m.detail(5)["note"])

print("6. Fin de partie -> revue -> retour (game_manager)")
from game_manager import GameManager
gm = GameManager("test")
if sf:
    gm.stockfish_path = sf
gm.game_mode = "hotseat"
gm.reglages = {"pendule_active": False}
gm.preparer_partie()
for uci in MAT_DU_BERGER:
    gm.board.make_move(chess.Move.from_uci(uci))
fin_attente = time.time() + 2
while not gm.board.game_over and time.time() < fin_attente:
    gm.board.update()          # la fin est constatee apres l'animation
    time.sleep(0.02)
verifier(gm.board.game_over, "la partie se termine par le mat")
fin = gm.board.end_screen
fin.lancer_analyse(gm.stockfish_path, "rapide")
verifier(fin.analyseur is not None, "analyse lancee a la fin de la partie")
gm.board.draw()
verifier(any(b.cle == "revue" for b in fin.boutons), "bouton Revue sur la carte de fin")
if sf:
    attendre(fin.analyseur)
    verifier(fin.ligne_analyse().startswith("Précision"),
             "carte de fin : %s" % fin.ligne_analyse())
    gm.board.draw()
    pygame.image.save(gm.screen, os.path.join("tests", "capture_fin_avec_revue.png"))
pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
gm.ouvrir_revue()
verifier(gm.board.SQ_SIZE == gm.disposition.taille_case,
         "au retour, l'echiquier de la partie retrouve sa taille")

print("7. Revue d'une partie de \"Mes parties\" (fichier PGN)")
import tempfile
dossier = tempfile.mkdtemp()
chemin_pgn = os.path.join(dossier, "partie.pgn")
with open(chemin_pgn, "w", encoding="utf-8") as f:
    f.write('[White "Julien"]\n[Black "Ordinateur"]\n[Result "0-1"]\n\n'
            "1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6 4. Ng5 d5 5. exd5 Nxd5 0-1\n")
partie = {"chemin": chemin_pgn, "blancs": "Julien", "noirs": "Ordinateur",
          "resultat": "0-1", "date": "16/10/2026", "camp": "blanc"}
revue = gm._revue_d_une_partie_enregistree(partie)
verifier(revue is not None and revue.analyseur.nombre_de_coups() == 10,
         "partie relue depuis le PGN (10 demi-coups)")
pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
verifier(revue.run(gm.clock) == "retour", "revue ouverte puis refermee")
revue.analyseur.arreter()
verifier(gm._revue_d_une_partie_enregistree({"chemin": "absent.pgn"}) is None,
         "fichier absent : la relecture simple prend le relais")

gm.cleanup_game()
gm.cleanup()

print()
if echecs:
    print("%d ECHEC(S)" % len(echecs))
    sys.exit(1)
print("Tout est bon.")
