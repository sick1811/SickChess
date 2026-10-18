# tests/test_en_ligne_nulle.py - en ligne : nulle et parties enregistrees
# (17/10, travail p18). Deux joueurs relies sur ce PC (TransportLocal), sans
# Steam. Les parties sont ecrites dans un dossier temporaire.

import os
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

import asset_manager
TEMP = tempfile.mkdtemp(prefix="sickchess_ligne_")
asset_manager.dossier_ecriture = lambda: TEMP

import historique_parties
from board import ChessBoard
from mode_en_ligne import ModeEnLigne
from reseau_transport import TransportLocal

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


class Horloge:
    t = 1000.0
    def __call__(self):
        return self.t


h = Horloge()
PORT = 5950 + os.getpid() % 40
a = TransportLocal(True, "Julien", port=PORT, horloge=h)
b = TransportLocal(False, "Paul", port=PORT, horloge=h)
for _ in range(200):
    a.recevoir(); b.recevoir(); h.t += 0.05; time.sleep(0.002)
    if a.connecte() and b.connecte():
        break
verifier(a.connecte() and b.connecte(), "connexion")


def partie(numero):
    pa = ChessBoard(ecran, {"minutes": 5, "pendule_active": True})
    pb = ChessBoard(ecran, {"minutes": 5, "pendule_active": True})
    ma = ModeEnLigne(pa, a, "blanc", "Julien", horloge=h, numero=numero)
    mb = ModeEnLigne(pb, b, "noir", "Paul", horloge=h, numero=numero)
    pa.game_buttons.bouton_nulle()
    return pa, pb, ma, mb


def tourner(ma, mb, fois=25):
    for _ in range(fois):
        ma.update(); ma.board.update(); mb.update(); mb.board.update()
        h.t += 0.05; time.sleep(0.002)


def jouer(p, uci):
    return p.make_move(chess.Move.from_uci(uci))


print("1. Le bouton NULLE remplace MENU en ligne")
pa, pb, ma, mb = partie(1)
verifier(pa.game_buttons.menu_button.text == "NULLE"
         and pa.game_buttons.action_secondaire == "nulle", "bouton NULLE")

print("2. Proposer, accepter")
jouer(pa, "e2e4"); tourner(ma, mb)
verifier(ma.nulle() == "proposee", "les Blancs proposent la nulle")
tourner(ma, mb)
verifier(mb.nulle_recue and "propose la nulle" in (mb.message_actif() or ""),
         "les Noirs le voient : %s" % mb.message_actif())
verifier(ma.nulle() is None, "pas deux propositions de suite")
verifier(mb.nulle() == "acceptee", "les Noirs acceptent")
tourner(ma, mb)
verifier(pa.game_over and pb.game_over and pa.result == pb.result == "1/2-1/2",
         "nulle des deux cotes (%s / %s)" % (pa.result, pb.result))

print("3. La partie entre dans « Mes parties »")
tourner(ma, mb)
parties = historique_parties.lister()
verifier(len(parties) == 2, "chacun enregistre sa partie (%d fichiers)" % len(parties))
camps = sorted(p["camp"] for p in parties)
verifier(camps == ["blanc", "noir"], "avec son camp : %s" % camps)
verifier(all(p["verdict"] == "nulle" for p in parties), "verdict : nulle")
e = historique_parties.lire_entetes(parties[0]["chemin"])
verifier(e.get("Mode") == "en_ligne", "marquee « en ligne »")
tourner(ma, mb)
verifier(len(historique_parties.lister()) == 2, "une seule fois")

print("4. Un coup joue annule la proposition")
ma.arreter(); mb.arreter()
pa, pb, ma, mb = partie(2)
jouer(pa, "d2d4"); tourner(ma, mb)
ma.nulle(); tourner(ma, mb)
verifier(mb.nulle_recue, "proposition recue")
jouer(pb, "d7d5"); tourner(ma, mb)
jouer(pa, "c2c4"); tourner(ma, mb)
verifier(not mb.nulle_recue, "les Noirs ont joue au lieu d'accepter : proposition oubliee")
verifier(mb.nulle() == "proposee" and not pb.game_over,
         "le bouton NULLE propose alors une nouvelle nulle (pas d'acceptation fantome)")

a.fermer(); b.fermer()
print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
