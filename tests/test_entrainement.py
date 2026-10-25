# tests/test_entrainement.py - entraineur d'ouvertures (17/10, travail p06).
#     python tests/test_entrainement.py
# Progression dans un dossier temporaire.

import os
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random

import chess
import pygame

pygame.init()
ecran = pygame.display.set_mode((1024, 640))

import asset_manager
TEMP = tempfile.mkdtemp(prefix="sickchess_ouv_")
asset_manager.dossier_ecriture = lambda: TEMP
import langue
langue.regler("fr")   # la machine de test peut etre en anglais

import entrainement

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


print("1. Les ouvertures proposees (25/10 : en arbre, voir test_arbre_ouvertures.py)")
import arbre_ouvertures
r = arbre_ouvertures.racine()
verifier(len(r.enfants) >= 15 and r.nb_lignes > 2000,
         "%d premiers coups, %d lignes a reciter" % (len(r.enfants), r.nb_lignes))
sic = arbre_ouvertures.noeud("e4 c5")
verifier(sic.famille() == "Défense sicilienne" and sic.nb_lignes > 20,
         "sicilienne : %d lignes differentes (les deviations)" % sic.nb_lignes)

print("2. Reciter une ligne")
ligne = (["e4", "c5", "Nf3", "d6", "d4", "cxd4"], "B50", "Défense sicilienne")
e = entrainement.Entrainement(ligne, chess.WHITE)
verifier(e.a_moi_de_jouer() and e.coup_attendu() == "e4", "les Blancs commencent : e4 attendu")
verifier(not e.proposer(chess.Move.from_uci("d2d4")), "d4 refuse")
verifier(e.avance == 0 and e.fautes == 1, "la ligne n'avance pas, une faute")
e.proposer(chess.Move.from_uci("g1f3"))
verifier(e.fautes == 1, "deux fautes sur le meme coup ne comptent qu'une fois")
verifier(e.proposer(chess.Move.from_uci("e2e4")), "e4 accepte")
verifier(e.jouer_le_coup_de_theorie().uci() == "c7c5", "l'adversaire joue c5")
verifier(e.proposer(chess.Move.from_uci("g1f3")), "Nf3 accepte")
e.jouer_le_coup_de_theorie(); e.proposer(chess.Move.from_uci("d2d4")); e.jouer_le_coup_de_theorie()
verifier(e.termine() and e.trouves == 2 and e.fautes == 1, "fin : 2 trouves, 1 rate")

print("3. Progression enregistree")
entrainement.noter_une_ligne("Défense sicilienne", chess.WHITE, 100.0)
entrainement.noter_une_ligne("Défense sicilienne", chess.WHITE, 50.0)
p = entrainement.progression("Défense sicilienne", chess.WHITE)
verifier(p["lignes"] == 2 and p["parfaites"] == 1 and abs(p["moyenne"] - 75) < 0.01,
         "2 lignes, 1 parfaite, moyenne 75 %%")
verifier(entrainement.progression("Défense sicilienne", chess.BLACK) is None,
         "Blancs et Noirs comptent a part")

print("4. L'ecran")
from ecran_entrainement import EcranEntrainement
ecr = EcranEntrainement(ecran, {})
ecr.draw()
pygame.image.save(ecran, "tests/capture_ouvertures_choix.png")
verifier(ecr.rect_arbre.bottom <= 640 and ecr.btn_retour_choix.rect.bottom <= 640,
         "l'arbre des ouvertures et le bouton Retour tiennent dans 640 px")
ecr.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=ecr.btn_noirs.rect.center))
verifier(ecr.couleur == chess.BLACK, "choix des Noirs")
random.seed(3)
ecr.commencer("Partie italienne")
verifier(ecr.etape == "jeu" and ecr.plateau.flipped, "Noirs : plateau retourne, l'adversaire commence")
ecr.adverse_a = 1
ecr.update()
verifier(len(ecr.plateau.board.move_stack) == 1, "le coup des Blancs est joue tout seul")
attendu = chess.Move.from_uci(ecr.entr.coup_attendu_uci())
faux = next(m for m in ecr.plateau.board.legal_moves if m != attendu)
verifier(ecr.plateau.make_move(faux) is False and ecr.flash and ecr.flash[0] == (232, 118, 108),
         "coup faux refuse, plateau rouge")
verifier(ecr.demander_un_indice() and ecr.plateau.indice == (attendu.from_square, attendu.to_square),
         "Montrer le coup : fleche du coup de theorie")
verifier(ecr.plateau.make_move(attendu), "le bon coup est joue")
fin = 0
while not ecr.entr.termine() and fin < 40:
    fin += 1
    if ecr.adverse_a:
        ecr.adverse_a = 1
        ecr.update()
    elif ecr.entr.a_moi_de_jouer():
        ecr.plateau.make_move(chess.Move.from_uci(ecr.entr.coup_attendu_uci()))
verifier(ecr.entr.termine() and "Ligne terminée" in ecr.message, "ligne finie : %s" % ecr.message)
ecr.draw()
pygame.image.save(ecran, "tests/capture_ouvertures_ligne.png")
verifier(entrainement.progression("Partie italienne", chess.BLACK)["lignes"] == 1, "progression notee")
ancienne = ecr.entr.coups
ecr.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=ecr.btn_suivante.rect.center))
verifier(ecr.entr.coups != ancienne and not ecr.entr.termine(), "ligne suivante : une autre variante")

print("4 bis. Noms des ouvertures en francais (Cowork, t57 : « Ouverture King's du cavalier »)")
import ouvertures
import ouvertures_fr
import re as _re
restes = sorted({ouvertures_fr.traduire(nom) for _eco, nom in ouvertures.livre().values()
                 if _re.search(r"\b(King's|Queen's|roi's|dame's)", ouvertures_fr.traduire(nom))})
verifier(not restes, "plus de King's / Queen's dans les noms traduits (%d : %s)" % (len(restes), restes[:3]))
verifier(ouvertures_fr.traduire("King's Knight Opening") == "Partie du cavalier roi",
         "King's Knight Opening : %s" % ouvertures_fr.traduire("King's Knight Opening"))
verifier(ouvertures_fr.traduire("King's Gambit Declined: Keene's Defense") == "Gambit du roi refusé, Défense Keene",
         "le « 's » anglais d'un nom propre disparait : %s" % ouvertures_fr.traduire("King's Gambit Declined: Keene's Defense"))

print("4 ter. « Ligne suivante » en plein ecran, 3 fois de suite (defaut Cowork 24/10, non reproduit)")
ecran_grand = pygame.display.set_mode((1920, 1080))
grand = EcranEntrainement(ecran_grand, {})
grand.commencer()
for essai in range(3):
    n = 0
    while not grand.entr.termine() and n < 60:
        n += 1
        if grand.adverse_a:
            grand.adverse_a = 1
            grand.update()
        elif grand.entr.a_moi_de_jouer():
            grand.plateau.make_move(chess.Move.from_uci(grand.entr.coup_attendu_uci()))
            grand.update()
    grand.draw()
    avant = list(grand.entr.coups)
    centre = grand.btn_suivante.rect.center
    for type_ in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        grand.handle_event(pygame.event.Event(type_, button=1, pos=centre))
    verifier(grand.entr.coups != avant and not grand.entr.termine(),
             "1920x1080, ligne finie, clic %d sur « Ligne suivante » : une autre ligne" % (essai + 1))
ecran = pygame.display.set_mode((1024, 640))

print("5. Le menu")
from menu_principal import MainMenu
m = MainMenu(ecran)
m.annoncer_reprise(True, "x")
verifier(any(b.cle == "ouvertures" for b in m.boutons), "entree « Entraînement aux ouvertures »")
verifier(max(b.rect.bottom for b in m.boutons) <= 640, "les 10 entrees tiennent en 640 px")

print("6. La progression n'est plus relue sur le disque a chaque image (banc d'essai 23/10)")
import builtins
import json
lectures = []
def _open_compte(*a, **k):
    if "r" in (a[1] if len(a) > 1 else k.get("mode", "r")):
        lectures.append(a[0])
    return builtins.open(*a, **k)
entrainement.open = _open_compte
entrainement.charger_progression()
for _ in range(24):
    entrainement.progression("Partie italienne", chess.BLACK)
verifier(not lectures, "24 demandes : aucune lecture du fichier (%d)" % len(lectures))
avant = entrainement.progression("Partie italienne", chess.BLACK)["lignes"]
entrainement.noter_une_ligne("Partie italienne", chess.BLACK, 50.0)
verifier(entrainement.progression("Partie italienne", chess.BLACK)["lignes"] == avant + 1,
         "une ligne notee se voit tout de suite")
with builtins.open(entrainement._chemin(), encoding="utf-8") as f:
    verifier(json.load(f)["familles"]["Partie italienne|noirs"]["lignes"] == avant + 1,
             "et elle est bien ecrite sur le disque")
p = entrainement.progression("Partie italienne", chess.BLACK)
p["lignes"] = 999
verifier(entrainement.progression("Partie italienne", chess.BLACK)["lignes"] == avant + 1,
         "modifier ce qu'on a recu ne change pas la memoire")
del entrainement.open

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
