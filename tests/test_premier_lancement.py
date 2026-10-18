# tests/test_premier_lancement.py - accueil guide (17/10, travail p11).
#     python tests/test_premier_lancement.py
# Profil et config.json dans un dossier temporaire.

import json
import os
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
ecran = pygame.display.set_mode((1024, 640))

import asset_manager
TEMP = tempfile.mkdtemp(prefix="sickchess_accueil_")
asset_manager.dossier_ecriture = lambda: TEMP
import settings_screen
import ecran_options
CONFIG = os.path.join(TEMP, "config.json")
settings_screen._chemin_config = lambda: CONFIG
ecran_options._chemin_config = lambda: CONFIG

import premier_lancement
from profil import Profil

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def clic(e, bouton):
    e._placer()
    return e.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                             pos=bouton.rect.center))


p = Profil()
verifier(premier_lancement.a_afficher({}, p), "profil neuf : l'accueil s'affiche")
verifier(not premier_lancement.a_afficher({"premier_lancement_fait": True}, p), "deja vu : non")
p2 = Profil(charger=False)
p2.parties = [{"x": 1}]
verifier(not premier_lancement.a_afficher({}, p2), "profil avec des parties (Julien) : jamais")

e = premier_lancement.EcranPremierLancement(ecran, p)
e.champ.contenu = ""
for car in "Lucas":
    e.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=car))
clic(e, e.btns_niveaux[2])
verifier(e.niveau == "club", "niveau « Je joue souvent » choisi")
e.draw()
pygame.image.save(ecran, "tests/capture_accueil_1.png")
clic(e, e.btn_suivant)
verifier(e.etape == 2, "Suivant : les trois choses a savoir")
e.draw()
pygame.image.save(ecran, "tests/capture_accueil_2.png")
verifier(clic(e, e.btn_go) == "fini", "C'est parti !")
verifier(p.nom == "Lucas" and p.elo == 1400, "nom et niveau dans le profil (%s, %d)" % (p.nom, p.elo))
c = json.load(open(CONFIG, encoding="utf-8"))
verifier(c.get("premier_lancement_fait") and c.get("elo") == 1400 and c.get("elo_suit_profil"),
         "config : deja vu, ordinateur a 1400 qui suit le profil")
verifier(not premier_lancement.a_afficher(c, p), "ne revient plus")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
