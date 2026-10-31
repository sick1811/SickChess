# tests/test_freestyle_coup_illegal.py - Freestyle : Stockfish rend un roque illegal.
#     python tests/test_freestyle_coup_illegal.py
#
# Bug « 1 fois sur 2 » de test_freestyle_moteur (n° 77, 31/10).
# Dans une partie Freestyle dont le roi est en e1 / e8 et dont il ne reste que
# des droits de roque vers une tour de coin (h1/a1, h8/a8), la FEN ressemble a
# une FEN d'echecs classiques (« K », « Kk », « Qq »...). freestyle.est_freestyle_fen
# repond alors False, engine.envoyer_position remet Stockfish en UCI_Chess960
# false, et Stockfish note le roque e1g1 (classique) au lieu de e1h1 (roi prend
# tour) : le coup n'est pas dans legal_moves du plateau Freestyle. En partie,
# background_ai le jette (« coup devenu illegal, ignore ») et l'ordinateur
# recommence sans fin.
#
# Ici, le roque est l'UNIQUE coup qui mate : Stockfish le choisit toujours,
# le defaut se voit a chaque passage (pas une fois sur dix).

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
from background_ai import BackgroundAI
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

# Roi en e1, tour en h1, droit « K » seul : le petit roque (e1h1 en Freestyle)
# est le seul mat. Meme chose cote noir (position miroir, droit « k »).
# 31/10 : c'est la PARTIE qui dit « Freestyle » (board.chess960), comme dans
# le jeu (background_ai, indice) : la FEN seule a l'air classique.
blanc = chess.Board("4N3/2P5/8/3b1B2/5B2/5k2/8/2N1K2R w K - 0 1", chess960=True)
positions = [blanc, blanc.mirror()]


class PlateauDeJeu:
    """Le strict necessaire de board.ChessBoard pour BackgroundAI."""
    def __init__(self, board):
        self.board = board
        self.timer = None


moteur = StockfishEngine(sf)
try:
    print("1. Stockfish, plateau Freestyle a droits « classiques »")
    for b in positions:
        roque = [c.uci() for c in b.legal_moves if b.is_castling(c)]
        verifier(roque, "le plateau Freestyle connait le roque %s" % roque)
        rendus = [moteur.get_best_move(b.fen(), 50, **freestyle.options_moteur(b))
                  for _ in range(3)]
        faux = [u for u in rendus if not u or chess.Move.from_uci(u) not in b.legal_moves]
        verifier(not faux, "Freestyle %s : Stockfish rend %s, coups legaux du roque %s"
                 % (b.fen(), rendus, roque))
        # Le mat doit bien etre joue (le roque Freestyle, roi prend tour).
        verifier(rendus and rendus[0] in roque,
                 "Freestyle %s : Stockfish roque en notation roi-prend-tour (%s)"
                 % (b.fen(), rendus[0] if rendus else None))
        d = moteur.analyser_position(b.fen(), profondeur=10, lignes=1,
                                     **freestyle.options_moteur(b))
        verifier(d and d["coup"] in roque, "analyse Freestyle : meilleur coup %s"
                 % (d or {}).get("coup"))

    print("2. Partie classique : rien ne change (e1g1)")
    classique = chess.Board(blanc.fen())
    u = moteur.get_best_move(classique.fen(), 50, **freestyle.options_moteur(classique))
    verifier(u == "e1g1", "plateau classique : Stockfish roque e1g1 (%s)" % u)

    print("3. L'ordinateur en partie (background_ai) joue le roque Freestyle")
    ia = BackgroundAI(PlateauDeJeu(blanc.copy()), moteur, temps_min_ms=50,
                      temps_max_ms=60, humain=False, temps_moteur_max_ms=100)
    ia.suivre_la_pendule = False
    ia._ai_worker()
    coup = ia.pending_ai_move
    verifier(coup is not None and coup in blanc.legal_moves and blanc.is_castling(coup),
             "coup de l'ordinateur legal sur le plateau Freestyle (%s)" % coup)
finally:
    moteur.quit()

print("4. Lecture des coups (sans Stockfish)")
verifier(freestyle.lire_coup(blanc, "e1g1") == chess.Move.from_uci("e1h1"),
         "e1g1 se lit e1h1 sur le plateau Freestyle")
verifier(freestyle.lire_coup(chess.Board(blanc.fen()), "e1h1") == chess.Move.from_uci("e1g1"),
         "e1h1 se lit e1g1 sur un plateau classique")
verifier(freestyle.meme_coup(blanc, "e1g1", "e1h1") and not freestyle.meme_coup(blanc, "e1g1", "e1f1"),
         "meme roque, deux notations")


class MoteurFactice:
    """Rend toujours le roque note a la mode classique (e1g1)."""
    def __init__(self):
        self.options = []

    def analyser_position(self, fen, profondeur=0, temps_max_ms=0, lignes=1, **reste):
        self.options.append(reste.get("chess960"))
        p = freestyle.plateau(fen)
        roque = [c for c in p.legal_moves if p.is_castling(c)]
        coup = "e1g1" if roque and p.turn == chess.WHITE else next(iter(p.legal_moves)).uci()
        return {"coup": coup, "evaluation": 0.3, "mat": None,
                "lignes": [{"coup": coup, "cp": 30, "mat": None, "profondeur": 20}]}


print("5. La revue d'une partie Freestyle (n° 77) : le roque joue est le meilleur")
depart = freestyle.plateau_de_depart(77)
b = depart.copy()
coups = []
for san in ("h3", "h6", "Bh2", "Bh7", "g3", "g6", "Qg2", "Qg7", "c3", "c6", "Rc2", "Rc7", "O-O"):
    if san == "O-O":
        # Les tours c ont bouge : il ne reste que « Kk », d'allure classique.
        verifier(b.fen().split()[2] == "Kk" and not freestyle.est_freestyle_fen(b.fen()),
                 "n° 77 : FEN d'allure classique avant le roque (%s)" % b.fen())
    c = b.parse_san(san)
    coups.append(c.uci())
    b.push(c)
verifier(coups[-1] == "e1h1", "le roque Freestyle est note e1h1 (%s)" % coups[-1])
m = MoteurFactice()
a = AnalyseurPartie(depart.fen(), coups, moteur=m)
verifier(a.chess960, "la revue reconnait une partie Freestyle a son roque")
a.demarrer()
limite = time.time() + 60
while a.en_cours and time.time() < limite:
    time.sleep(0.05)
d = a.detail(len(coups) - 1)
verifier(d["pret"] and d["est_le_meilleur"],
         "roque e1h1 = meilleur coup e1g1 du moteur (%s, note %s)" % (d.get("meilleur_uci"), d.get("note")))
verifier(m.options and all(o is True for o in m.options),
         "la revue dit « Freestyle » au moteur (%s)" % sorted(set(map(str, m.options))))
c = AnalyseurPartie(None, ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "e1g1"],
                    moteur=MoteurFactice())
verifier(not c.chess960, "partie classique : pas de Freestyle pour la revue")

print()
if echecs:
    print("%d ECHEC(S)" % len(echecs))
    sys.exit(1)
print("Stockfish roque correctement en Freestyle, meme avec des droits « classiques ».")
