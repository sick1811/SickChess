# tests/test_resume_coach.py - le resume du coach sur la carte de fin (24/10, travail p27).
#     python tests/test_resume_coach.py
# Sans Stockfish : une analyse inventee (coups, pastilles, precision) et de fausses
# parties precedentes. On verifie les trois lignes (ouverture, plus gros moment,
# precision comparee), la carte de fin qui les dessine, et l'anglais.

import os
import shutil
import sys
import tempfile
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

import langue
import resume_coach as C

# 31/10 : le test parle français, quelle que soit la langue du config.json de Julien.
langue.regler("fr")

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


class FausseAnalyse:
    """Ce que resume_coach lit d'un AnalyseurPartie."""

    def __init__(self, coups, notes, terminee=True, precisions=(84.4, 91.0), fen=chess.STARTING_FEN):
        b = chess.Board(fen)
        self.fens, self.sans, self.coups, self.erreur = [fen], [], list(coups), None
        self._details = []
        for i, uci in enumerate(coups):
            m = chess.Move.from_uci(uci)
            note = notes.get(i)
            self._details.append({"index": i, "pret": note is not None or terminee,
                                  "note": note, "san": b.san(m), "par_les_blancs": b.turn,
                                  "numero": b.fullmove_number, "meilleur_san": "Cf3",
                                  "perte": {"gaffe": 40, "erreur": 15, "imprecision": 7,
                                            "manque": 25}.get(note, 0.0)})
            self.sans.append(b.san(m))
            b.push(m)
            self.fens.append(b.fen())
        self._terminee, self._precisions = terminee, precisions

    def terminee(self):
        return self._terminee

    def nombre_de_coups(self):
        return len(self.coups)

    def detail(self, i):
        return self._details[i]

    def rapport(self):
        return {"blancs": {"precision": self._precisions[0]}, "noirs": {"precision": self._precisions[1]}}


ESPAGNOLE = ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6", "d2d3", "d7d6"]

print("1. L'ouverture")
o = C.ligne_ouverture(FausseAnalyse(ESPAGNOLE, {}).sans)
verifier(o.startswith("Ouverture : C") and "espagnol" in o.lower() and "coups de théorie" in o,
         "partie espagnole reconnue : %s" % o)
verifier(C.ligne_ouverture(FausseAnalyse(["a2a3", "h7h6"], {}).sans) in (
    "Ouverture : sortie du livre dès le premier coup",) or
    C.ligne_ouverture(FausseAnalyse(["a2a3", "h7h6"], {}).sans).startswith("Ouverture : A00"),
    "1.a3 : ouverture rare ou hors livre (%s)" % C.ligne_ouverture(FausseAnalyse(["a2a3", "h7h6"], {}).sans))
verifier(C.ligne_ouverture(["e4"], depuis_le_depart=False) == "",
         "partie commencee d'une position : pas d'ouverture")

print("2. Le plus gros moment (du joueur, pas de l'adversaire)")
a = FausseAnalyse(ESPAGNOLE, {4: "imprecision", 6: "gaffe", 5: "gaffe", 8: "erreur"})
m = C.ligne_moment([a.detail(i) for i in range(10)], True, True)
verifier(m == "Plus gros moment : 4. Ba4 ?? (gaffe), mieux : Cf3" or m.startswith("Plus gros moment : 4. B"),
         "Blancs : la gaffe du 4e coup, pas celle des Noirs : %s" % m)
m = C.ligne_moment([a.detail(i) for i in range(10)], False, True)
verifier(m.startswith("Plus gros moment : 3... a6 ??"), "Noirs : leur gaffe, notee 3... : %s" % m)
a = FausseAnalyse(ESPAGNOLE, {4: "brillant", 2: "tres_bon"})
m = C.ligne_moment([a.detail(i) for i in range(10)], True, True)
verifier(m.startswith("Plus beau coup : 3. ") and "!! (brillant)" in m, "sans faute : le plus beau coup : %s" % m)
a = FausseAnalyse(ESPAGNOLE, {})
verifier(C.ligne_moment([a.detail(i) for i in range(10)], True, True) == "Aucune faute : bravo !",
         "ni faute ni beau coup : « Aucune faute : bravo ! »")
a = FausseAnalyse(ESPAGNOLE, {}, terminee=False)
verifier(C.ligne_moment([a.detail(i) for i in range(10)], True, False) == "Plus gros moment : analyse en cours...",
         "analyse pas finie, rien de juge : « analyse en cours »")

print("3. La precision comparee")
verifier(C.ligne_precision(84.4, False, [70, 75]) == "Précision provisoire : 84 % (analyse en cours)",
         "provisoire tant que l'analyse tourne")
verifier(C.ligne_precision(84.4, True, None) == "Précision : 84 %", "premiere partie : sans comparaison")
verifier(C.ligne_precision(84.4, True, [70, 75, 80] + [60] * 7)
         == "Précision : 84 %, ta meilleure de tes 10 dernières parties", "meilleure des 10")
verifier(C.ligne_precision(84.4, True, [70]) == "Précision : 84 %, mieux que ta partie précédente",
         "une seule partie avant")
verifier(C.ligne_precision(80.0, True, [70, 72, 90]) == "Précision : 80 %, au-dessus de ta moyenne (77 %)",
         "au-dessus de la moyenne")
verifier(C.ligne_precision(60.0, True, [70, 72, 90]) == "Précision : 60 %, sous ta moyenne (77 %)",
         "sous la moyenne")
verifier(C.ligne_precision(77.0, True, [70, 72, 90]) == "Précision : 77 %, comme ta moyenne (77 %)",
         "comme la moyenne")
verifier(C.ligne_precision(None, True, [70]) == "", "pas encore de precision : rien")

print("4. Les trois lignes")
a = FausseAnalyse(ESPAGNOLE, {6: "erreur"}, precisions=(84.4, 91.0))
l = C.lignes(a, True, [70, 75])
verifier(len(l) == 3 and l[0].startswith("Ouverture") and l[1].startswith("Plus gros moment : 4. ")
         and l[2].startswith("Précision : 84 %, ta meilleure"), "contre l'ordinateur : %s" % l)
l = C.lignes(a, False, [95])
verifier(l[2] == "Précision : 91 %, sous ta moyenne (95 %)", "avec les Noirs : leur precision (%s)" % l[2])
verifier(len(C.lignes(a, None)) == 2, "partie a deux : ouverture et plus gros moment, pas de precision")
verifier(C.lignes(None, True) == [], "pas d'analyse : rien")

print("5. Les parties precedentes (fausses, dossier temporaire)")
import statistiques
dossier = tempfile.mkdtemp(prefix="sickchess_coach_")
parties = [{"chemin": os.path.join(dossier, "p%d.pgn" % i), "fichier": "p%d.pgn" % i,
            "camp": "blanc" if i != 3 else ""} for i in range(14)]
ancien = statistiques._analyse
statistiques._analyse = lambda p: None if p["fichier"] == "p5.pgn" else {"precision": 50.0 + int(p["fichier"][1:-4])}
v = C.precisions_passees(exclure=parties[0]["chemin"], parties=parties)
statistiques._analyse = ancien
verifier(v == [51, 52, 54, 56, 57, 58, 59, 60, 61, 62],
         "les 10 dernieres analysees, sans la partie jouee ni celles a deux ni les non analysees : %s" % v)
p = C.PrecisionsPassees("x", lire=lambda exclure: (time.sleep(0.2), [70.0])[1])
verifier(p.valeurs is None, "lues dans un fil : la carte ne bloque pas")
verifier(p.attendre(5) == [70.0], "puis disponibles")
shutil.rmtree(dossier, ignore_errors=True)

print("6. La carte de fin")
from board import ChessBoard                  # noqa: E402
import ecran_fin                               # noqa: E402
b = ChessBoard(ecran, {})
b.game_over, b.result, b.game_over_reason = True, "1-0", "Échec et mat"
b.ia_joue_blancs = False
fin = ecran_fin.EcranFin(b, "stockfish")
fin.analyseur = FausseAnalyse(ESPAGNOLE, {6: "gaffe"})
fin.passees = p
verifier(fin.camp_du_joueur() is True, "contre l'ordinateur avec les Blancs : camp = Blancs")
vus = []
ancien_texte = ecran_fin.ui.texte
ecran_fin.ui.texte = lambda s, t, *a, **k: (vus.append(t), ancien_texte(s, t, *a, **k))[1]
fin.draw(ecran)
ecran_fin.ui.texte = ancien_texte
coach = [t for t in vus if t.startswith(("Ouverture", "Plus gros", "Précision : 84"))]
verifier(len(coach) == 3, "la carte dessine les trois lignes : %s" % coach)
bas = max(fin.rect.y + 132 + 24 * 3, 0)
verifier(bas < fin.bouton_revue.rect.y, "les lignes ne touchent pas le bouton « Revue de la partie »")
verifier(fin.rect.height <= 390 and fin.rect.width <= 460, "taille de la carte : %s" % (fin.rect.size,))
deux = ecran_fin.EcranFin(b, "hotseat")
verifier(deux.camp_du_joueur() is None, "partie a deux : pas de camp")
deux.preparer_le_coach("x")
verifier(deux.passees is None, "partie a deux : on ne lit pas les parties precedentes")

print("7. En anglais")
langue.regler("en")
for phrase in C.lignes(FausseAnalyse(ESPAGNOLE, {6: "gaffe"}), True, [70, 75]) + [
        C.ligne_precision(84.4, False, []), C.ligne_precision(60, True, [70, 80]),
        "Plus beau coup : 3. Bb5 ! (très bien)", "Aucune faute : bravo !"]:
    en = langue.traduire(phrase)
    verifier(en != phrase and not any(m in en for m in ("Précision", "Ouverture", "moment :", "mieux")),
             "%s -> %s" % (phrase, en))
langue.regler("fr")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
