# tests/test_succes.py - succes (17/10, travail p19). Dossier temporaire,
# faux Steam.

import os
import sys
import tempfile

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
TEMP = tempfile.mkdtemp(prefix="sickchess_succes_")
asset_manager.dossier_ecriture = lambda: TEMP

import succes

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


class FauxSteam:
    def __init__(self):
        self.recus = []

    def debloquer_succes(self, nom):
        self.recus.append(nom)
        return True


import steam as module_steam
faux = FauxSteam()
module_steam._INSTANCE = faux

print("1. Debloquer")
verifier(len(succes.SUCCES) == 14 and len({s[1] for s in succes.SUCCES}) == 14, "14 succes, noms API uniques")
verifier(succes.debloquer("premiere_victoire"), "premier sang : nouveau")
verifier(not succes.debloquer("premiere_victoire"), "une seule fois")
verifier(faux.recus == ["PREMIERE_VICTOIRE"], "envoye a Steam : %s" % faux.recus)
verifier("premiere_victoire" in succes.obtenus(), "garde dans succes.json")
verifier(succes.annonce_en_cours()[0] == "Premier sang", "annonce affichee")
succes.dessiner_annonce(ecran)
verifier(not succes.debloquer("inconnu"), "cle inconnue : rien")

print("2. Branche sur le jeu")
import enregistrement
from board import ChessBoard
b = ChessBoard(ecran, {"pendule_active": False, "elo": 2100})
b.ai_manager = object()
for uci in ("e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"):
    b.make_move(chess.Move.from_uci(uci))
b.terminer_partie("ÉCHEC ET MAT !", "1-0")
enregistrement.enregistrer_la_partie(b, "stockfish")
o = succes.obtenus()
verifier(all(k in o for k in ("victoire_1500", "victoire_2000", "victoire_mat")),
         "battre l'ordinateur a 2100 par mat : 3 succes")
import entrainement
import chess as _c
entrainement.noter_une_ligne("Défense sicilienne", _c.WHITE, 100.0)
verifier("ouverture_parfaite" in succes.obtenus(), "ligne d'ouverture parfaite")
import historique_parties
historique_parties.importer("1. e4 e5 2. Nf3 Nc6")
verifier("importer" in succes.obtenus(), "partie importee")

print("3. L'ecran")
from ecran_statistiques import EcranStatistiques
e = EcranStatistiques(ecran)
e.attendre()
e.draw()
e.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=e.btn_succes.rect.center))
verifier(e.vue == "succes", "bouton Succès : la liste")
e.draw()
pygame.image.save(ecran, "tests/capture_succes.png")
e.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=e.btn_retour.rect.center))
verifier(e.vue == "stats", "Retour : revient aux statistiques")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
