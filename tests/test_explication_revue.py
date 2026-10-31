# tests/test_explication_revue.py - fautes expliquees dans la revue (17/10, p03).
#     python tests/test_explication_revue.py
# Sans moteur : on donne la position, le coup joue et le meilleur coup.

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess

import explication_revue as er

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def fen_apres(*sans):
    b = chess.Board()
    for s in sans:
        b.push_san(s)
    return b.fen()


cas = [
    ("le coup permet le mat", fen_apres("e4", "e5", "Bc4", "Nc6", "Qh5"), "g8f6", "g7g6",
     ["permet le mat"]),
    ("mat en 1 manque", fen_apres("e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6"), "d2d3", "h5f7",
     ["mat en un coup"]),
    ("fourchette manquee", "r3k3/8/8/1N6/8/8/8/4K3 w - - 0 1", "e1d2", "b5c7",
     ["fourchette sur", "le roi", "la tour"]),
    ("piece sur une case prise", "4k3/8/7p/8/8/5N2/8/4K3 w - - 0 1", "f3g5", "e1d2",
     ["ton cavalier est perdu"]),
    ("piece laissee sans defense", "4k3/8/8/8/2b5/8/3N4/4K3 w - - 0 1", "e1f2", "d2c4",
     ["Le fou adverse était à prendre"]),
    ("prise manquee", "4k3/8/8/3q4/8/8/3R4/4K3 w - - 0 1", "e1e2", "d2d5",
     ["La dame adverse était à prendre"]),
    ("le coup permet une fourchette", "4k3/8/8/8/1n6/8/7P/R3K3 w - - 0 1", "h2h3", "a1a4",
     ["permet une fourchette sur", "ton roi", "ta tour"]),
]
for nom, fen, joue, meilleur, attendus in cas:
    texte = er.expliquer(fen, joue, meilleur)
    verifier(all(a in texte for a in attendus), "%s : « %s »" % (nom, texte))

# Regle de Julien : jamais le coup dans l'explication.
import re
for nom, fen, joue, meilleur, _attendus in cas:
    texte = er.expliquer(fen, joue, meilleur)
    verifier(not re.search(r"[KQRBN]?[a-h]?x?[a-h][1-8]|O-O", texte),
             "%s : aucun coup ecrit" % nom)
verifier(er.expliquer(chess.STARTING_FEN, "e2e4", "d2d4") == "",
         "rien de clair : pas de phrase inventee")
verifier(er.expliquer(chess.STARTING_FEN, "e2e5", None) == "", "coup illegal : ''")
verifier(er.expliquer("pas une fen", "e2e4", None) == "", "position illisible : ''")


print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
