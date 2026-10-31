# tests/test_freestyle_moteur.py - le Freestyle avec le vrai Stockfish (UCI_Chess960).
#     python tests/test_freestyle_moteur.py
# Stockfish joue des coups legaux (roques Freestyle compris) et la revue
# analyse une partie Freestyle jusqu'au bout, roque compris.

import os
import sys
import tempfile
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import asset_manager
_DOSSIER = tempfile.mkdtemp()
asset_manager.dossier_ecriture = lambda: _DOSSIER       # jamais les vraies donnees

import chess
import freestyle
from analyse_partie import AnalyseurPartie
from engine import StockfishEngine

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


sf = os.environ.get("SICKCHESS_STOCKFISH") or os.path.join(RACINE, "moteur", "stockfish.exe")
if not os.path.exists(sf):
    print("Stockfish introuvable : serie sautee.")
    sys.exit(0)

moteur = StockfishEngine(sf)
roques = 0
for numero in (0, 77, 254):
    b = freestyle.plateau_de_depart(numero)
    illegal = None
    fautif = ""
    for _ in range(40):
        if b.is_game_over():
            break
        # 31/10 : comme le jeu (background_ai), on dit au moteur que la partie
        # est Freestyle ; sans ca, n° 77 ressemblait a une partie classique.
        uci = moteur.get_best_move(b.fen(), 50, **freestyle.options_moteur(b))
        coup = chess.Move.from_uci(uci) if uci else None
        if coup not in b.legal_moves:
            illegal = uci or "None"
            fautif = " ; coup rendu %s, FEN %s, roques legaux %s" % (
                illegal, b.fen(), [c.uci() for c in b.legal_moves if b.is_castling(c)])
            break
        roques += b.is_castling(coup)
        b.push(coup)
    verifier(illegal is None, "n° %d : Stockfish joue %d coups legaux%s"
             % (numero, len(b.move_stack), fautif))
verifier(roques > 0, "Stockfish a roque a la mode Freestyle (%d roque(s))" % roques)

# Petit roque ou seul le roi bouge vers g1 : Stockfish doit le connaitre.
fen = "1k6/8/8/8/8/8/PPP5/1K1R3R w H - 0 1"
b = chess.Board(fen, chess960=True)
details = moteur.analyser_position(b.fen(), profondeur=8)
verifier(details is not None, "analyse d'une position Freestyle avec droit de roque")
moteur.quit()

# La revue : une partie Freestyle avec deux roques.
depart = freestyle.plateau("rk5r/pppppppp/8/8/8/8/PPPPPPPP/RK5R w KQkq - 0 1")
b = depart.copy()
coups = []
for san in ("d4", "d5", "O-O-O", "O-O-O", "e4", "e6"):
    coup = b.parse_san(san)
    coups.append(coup.uci())
    b.push(coup)
a = AnalyseurPartie(depart.fen(), coups, sf, "rapide")
a.demarrer()
limite = time.time() + 120
while a.en_cours and time.time() < limite:
    time.sleep(0.2)
verifier(a.terminee(), "revue d'une partie Freestyle terminee (%d coups)" % len(coups))
verifier(all(a.detail(i)["pret"] for i in range(len(coups))),
         "chaque coup a sa pastille, roques compris")
verifier(a.detail(2)["san"] == "O-O-O", "le roque s'affiche O-O-O dans la revue (%s)"
         % a.detail(2)["san"])

print()
if echecs:
    print("%d ECHEC(S)" % len(echecs))
    sys.exit(1)
print("Stockfish et la revue suivent le Freestyle.")
