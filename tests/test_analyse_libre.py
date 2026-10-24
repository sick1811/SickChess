# tests/test_analyse_libre.py - l'analyse libre (24/10, travail p35).
#     python tests/test_analyse_libre.py
# Sans fenetre, avec un moteur factice (et un vrai Stockfish si
# SICKCHESS_STOCKFISH est donne). Rien n'est ecrit dans tes donnees.

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
ecran = pygame.display.set_mode((1280, 720))

import ecran_analyse_libre as al

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


class FauxMoteur:
    """Trois lignes : les trois premiers coups legaux, profondeur qui monte."""
    def __init__(self):
        self.appels = 0
        self.interruptions = 0

    def analyser_position(self, fen, profondeur=0, temps_max_ms=0, lignes=1):
        self.appels += 1
        time.sleep(0.01)
        b = chess.Board(fen)
        coups = list(b.legal_moves)[:lignes]
        return {"lignes": [{"coup": c.uci(), "cp": 30 - 10 * i, "mat": None,
                            "suite": [c.uci()]} for i, c in enumerate(coups)],
                "profondeur": min(40, 10 + self.appels)}

    def interrompre(self):
        self.interruptions += 1


def attendre(e, secondes=3):
    fin = time.time() + secondes
    while time.time() < fin and e.moteur.info(e.fen()) is None:
        time.sleep(0.02)
    return e.moteur.info(e.fen())


print("1. Menu et ouverture")
import menu_principal
verifier(any(c == "analyse" for c, _, _ in menu_principal.ENTREES), "entrée « Analyse libre » au menu")
import game_manager
verifier(hasattr(game_manager.GameManager, "ouvrir_analyse_libre"), "le menu sait ouvrir l'écran")
faux = FauxMoteur()
e = al.EcranAnalyseLibre(ecran, {}, None, moteur=faux)
verifier(e.fen() == chess.STARTING_FEN, "s'ouvre sur la position de départ")
info = attendre(e)
verifier(info is not None and len(info["lignes"]) == 3, "le moteur donne 3 lignes")
e.draw()
verifier(len(e.plateau.fleches_conseil) == 3, "3 flèches bleues sur l'échiquier")

print("2. Jouer les deux camps")
verifier(e._coup_joue(chess.Move.from_uci("e2e4")), "1. e4 joué")
verifier(e._coup_joue(chess.Move.from_uci("e7e5")), "1... e5 joué (les Noirs aussi)")
verifier(e.index == 2 and len(e.coups) == 2, "feuille : 2 coups")
verifier(not e._coup_joue(chess.Move.from_uci("e1e3")), "coup illégal refusé")
e.executer("precedent")
verifier(e.index == 1 and e.plateau.board.turn == chess.BLACK, "← revient d'un coup")
verifier(e._coup_joue(chess.Move.from_uci("c7c5")), "autre coup : nouvelle suite")
verifier([c.uci() for c in e.coups] == ["e2e4", "c7c5"], "la suite est remplacée")
verifier("remplacé" in e.message, "message « coup(s) remplacé(s) »")
e.executer("debut")
verifier(e.index == 0, "Début")
e.executer("suivant")
verifier(e.index == 1, "→ rejoue le coup suivant")
e.executer("fin")
verifier(e.index == 2, "Fin")

print("3. Coller un FEN ou un PGN")
fen = "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1"
verifier(e.coller(fen) and e.fen().split()[0] == fen.split()[0], "FEN collé")
pgn = '[Event "?"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 *'
verifier(e.coller(pgn) and len(e.coups) == 6 and e.index == 6, "PGN collé : 6 coups, à la fin")
verifier(not e.coller("bonjour"), "texte illisible refusé")
verifier(al.position_depuis_texte("") is None, "presse-papiers vide refusé")

print("4. Éditeur de position")
e.executer("debut")
e.ouvrir_edition()
verifier(e.edition is not None, "éditeur ouvert (E)")
e.draw()
e.edition["board"].remove_piece_at(chess.H1)
verifier(e.valider_edition(), "position de départ sans la tour h1 acceptée")
verifier(e.plateau.board.castling_xfen() == "Qkq", "roques déduits : plus de petit roque blanc")
e.ouvrir_edition()
e.edition["board"].clear_board()
e.poser(chess.E1, "K")
verifier(not e.valider_edition(), "sans roi noir : refusé")
verifier("roi noir" in e.message, "la raison est donnée (%s)" % e.message)
e.poser(chess.E8, "k")
e.poser(chess.D7, "Q")
e.poser(chess.D7, "Q")
verifier(e.edition["board"].piece_at(chess.D7) is None, "cliquer deux fois enlève la pièce")
e.poser(chess.A1, "R")
e.poser(chess.A1, None)
verifier(e.edition["board"].piece_at(chess.A1) is None, "clic droit / gomme enlève")
e.edition["board"].turn = chess.BLACK
e.poser(chess.H4, "q")          # la dame noire met le roi blanc en echec
verifier(not e.valider_edition() and "trait" in e.message,
         "le camp sans le trait ne peut pas être en échec")
e.edition["board"].turn = chess.WHITE
e.btn_trait.libelle = ""
e._maj_trait()
verifier(e.btn_trait.libelle == "Trait : Blancs", "bouton du trait à jour")
verifier(e.valider_edition() and e.edition is None, "position valable chargée (Blancs en échec, à eux de jouer)")
verifier(e.index == 0 and not e.coups, "feuille vide après l'édition")
e.ouvrir_edition()
e._evenement_edition(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
verifier(e.edition is None, "Échap quitte l'éditeur sans rien changer")

print("5. Moteur, mat et pat")
verifier(not e.moteur.basculer() and not e.moteur.actif, "Espace : moteur arrêté")
e.draw()
verifier(e.plateau.fleches_conseil == [], "moteur arrêté : plus de flèches")
e.moteur.basculer()
mat = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
e.coller(mat)
avant = faux.appels
time.sleep(0.2)
verifier(faux.appels == avant, "position de mat : le moteur ne calcule pas")
e.draw()
verifier(e.plateau.board.is_checkmate(), "le mat est affiché (Échec et mat)")
for taille in ((1024, 640), (1366, 768), (1920, 1080), (900, 560)):
    s = pygame.display.set_mode(taille)
    e._placer(s)
    e.draw()
    e.ouvrir_edition()
    e.draw()
    e.edition = None
verifier(True, "écran dessiné à 4 tailles (analyse et éditeur)")
pygame.image.save(e.screen, os.path.join(RACINE, "tests", "capture_analyse_libre.png"))

print("6. Depuis la revue (touche A)")
import analyse_partie
from ecran_revue import EcranRevue


class FauxAnalyse:
    def analyser_position(self, fen, profondeur=0, temps_max_ms=0, lignes=1):
        c = next(iter(chess.Board(fen).legal_moves))
        return {"coup": c.uci(), "evaluation": 0.2, "mat": None,
                "second_evaluation": 0.1, "second_mat": None}


a = analyse_partie.AnalyseurPartie(None, ["e2e4", "e7e5", "g1f3"], moteur=FauxAnalyse())
s = pygame.display.set_mode((1280, 720))
r = EcranRevue(s, a, {})
r.aller_a(2, son=False)
r.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, mod=0, unicode="a"))
demande = getattr(r, "_demande_analyse", None)
verifier(demande is not None and [m.uci() for m in demande[1]] == ["e2e4", "e7e5"],
         "A dans la revue : la position affichée part dans l'analyse libre")

e.moteur.arreter()
verifier(e.moteur._fini, "en sortant, le moteur s'arrête")

sf = os.environ.get("SICKCHESS_STOCKFISH")
if sf and os.path.exists(sf):
    print("7. Vrai Stockfish")
    vrai = al.EcranAnalyseLibre(s, {}, sf)
    fin = time.time() + 20
    prof = 0
    while time.time() < fin:
        i = vrai.moteur.info(vrai.fen())
        if i:
            prof = i["profondeur"]
            if prof >= 18:
                break
        time.sleep(0.2)
    verifier(prof >= 14, "la profondeur monte toute seule (%d)" % prof)
    vrai._coup_joue(chess.Move.from_uci("d2d4"))
    t0 = time.time()
    while time.time() - t0 < 5 and vrai.moteur.info(vrai.fen()) is None:
        time.sleep(0.05)
    verifier(vrai.moteur.info(vrai.fen()) is not None and time.time() - t0 < 3,
             "nouvelle position analysée en moins de 3 s (%.1f s)" % (time.time() - t0))
    vrai.moteur.arreter()

print("%d controle(s) en echec" % len(echecs) if echecs else "Tout est bon.")
sys.exit(1 if echecs else 0)
