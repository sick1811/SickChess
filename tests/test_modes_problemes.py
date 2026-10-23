# tests/test_modes_problemes.py - defis de problemes (17/10, travail p07) :
# contre la montre, survie, probleme du jour.
#     python tests/test_modes_problemes.py
# Records et scores dans un dossier temporaire ; le classement n'est pas touche.

import datetime
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
import tempfile as _tf
_DOSSIER = _tf.mkdtemp(prefix="sickchess_pb_ecriture_")
asset_manager.dossier_ecriture = lambda: _DOSSIER     # jamais tes vraies parties
import puzzles
import modes_problemes as mp

TEMP = tempfile.mkdtemp(prefix="sickchess_defis_")
puzzles.chemin_du_score = lambda: os.path.join(TEMP, "puzzles_score.json")
mp._chemin = lambda: os.path.join(TEMP, "modes_problemes.json")

from ecran_problemes import EcranProblemes

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


if not puzzles.disponible():
    print("Base de problemes absente : test saute.")
    sys.exit(0)


def avancer(e):
    e.attente_jusqu_a = 0
    e.update()


def bon_coup(e):
    return chess.Move.from_uci(puzzles.coup_attendu(e.puzzle, e.avance))


def mauvais_coup(e):
    attendu = puzzles.coup_attendu(e.puzzle, e.avance)
    for m in e.plateau.board.legal_moves:
        essai = e.plateau.board.copy()
        essai.push(m)
        if m.uci() != attendu and not essai.is_checkmate():
            return m


def resoudre(e):
    avancer(e)
    while not e.fini:
        e.plateau.make_move(bon_coup(e))
        avancer(e)


print("1. Contre la montre (horloge simulee)")
heure = [1000.0]
s = mp.SessionDefi(mp.CHRONO, maintenant=lambda: heure[0])
verifier(s.temps_restant() == 180, "3:00 avant de commencer")
p1 = s.tirer_un_puzzle()
verifier(p1 is not None and abs(p1["classement"] - 600) <= 600, "1er probleme facile (%d)" % p1["classement"])
s.noter_un_puzzle(p1, True)
verifier(s.niveau == 670 and s.classement() == 1, "reussi : score 1, niveau monte a 670")
heure[0] += 60
verifier(abs(s.temps_restant() - 120) < 0.01, "2:00 restantes apres une minute")
p2 = s.tirer_un_puzzle()
verifier(p2 and p2["id"] != p1["id"], "jamais deux fois le meme probleme")
s.noter_un_puzzle(p2, False)
verifier(s.rates() == 1 and s.niveau == 670, "faute : comptee, le niveau ne monte pas")
heure[0] += 200
verifier(s.terminee() and s.tirer_un_puzzle() is None, "temps ecoule : plus de probleme")
verifier(s.nouveau_record and mp.record(mp.CHRONO) == 1, "record enregistre (1)")
verifier("Temps écoulé" in s.resume() and "record" in s.resume().lower(), s.resume())

print("2. Survie")
s = mp.SessionDefi(mp.SURVIE)
for i in range(3):
    pb = s.tirer_un_puzzle()
    s.noter_un_puzzle(pb, i == 0)
verifier(not s.terminee() and s.vies_restantes == 1, "1 reussi, 2 fautes : encore une vie")
s.noter_un_puzzle(s.tirer_un_puzzle(), False)
verifier(s.terminee() and s.tirer_un_puzzle() is None, "3e faute : fini")
verifier("Trois fautes" in s.resume(), s.resume())

print("3. Probleme du jour")
jour = datetime.date(2026, 10, 17)
a, b = mp.probleme_du_jour(jour), mp.probleme_du_jour(jour)
verifier(a and a["id"] == b["id"], "le meme probleme toute la journee")
verifier(mp.probleme_du_jour(datetime.date(2026, 10, 18))["id"] != a["id"], "un autre le lendemain")
s = mp.SessionDefi(mp.DU_JOUR, date=jour)
pb = s.tirer_un_puzzle()
s.noter_un_puzzle(pb, True)
e = mp.etat_du_jour(jour)
verifier(e["fait"] and e["reussi"] and e["serie"] == 1, "reussi : serie 1")
verifier(mp.SessionDefi(mp.DU_JOUR, date=jour).tirer_un_puzzle() is None, "un seul essai par jour")
s = mp.SessionDefi(mp.DU_JOUR, date=jour + datetime.timedelta(days=1))
s.noter_un_puzzle(s.tirer_un_puzzle(), True)
verifier(mp.etat_du_jour(jour + datetime.timedelta(days=1))["serie"] == 2, "le lendemain : serie 2")

print("4. Dans l'ecran des problemes")
ecr = EcranProblemes(ecran, {})
ecr.draw()
pygame.image.save(ecran, "tests/capture_problemes_choix.png")
verifier(all(b.rect.bottom <= ecr.btn_erreurs.rect.top for b in ecr.btns_defis),
         "les boutons des defis tiennent au-dessus de « Mes erreurs »")
verifier(ecr.btn_retour_choix.rect.bottom <= 640, "tout tient en 1024x640")
ecr.commencer("chrono")
verifier(ecr.session.mode == "chrono" and ecr.puzzle is not None, "contre la montre lance")
classement_avant = puzzles.charger_le_score()["classement"]
avancer(ecr)
verifier(not ecr.demander_un_indice(), "pas d'indice pendant un defi")
ecr.plateau.make_move(mauvais_coup(ecr))
verifier(ecr.fini and ecr.enchainer_a > 0 and ecr.session.rates() == 1,
         "une faute : probleme termine, le suivant arrive tout seul")
ancien = ecr.puzzle["id"]
ecr.enchainer_a = 1
ecr.update()
verifier(ecr.puzzle["id"] != ancien and not ecr.fini, "probleme suivant")
resoudre(ecr)
verifier(ecr.session.reussis() == 1, "un probleme trouve compte")
ecr.draw()
pygame.image.save(ecran, "tests/capture_contre_la_montre.png")
ecr.session.debut -= 500
ecr.update()
verifier(ecr.fini and "Temps écoulé" in ecr.message, "temps ecoule : %s" % ecr.message)
ecr.draw()
verifier(ecr.btn_suivant.libelle == "Rejouer le défi", "bouton « Rejouer le défi »")
verifier(puzzles.charger_le_score()["classement"] == classement_avant,
         "le classement des problemes n'est pas touche")
ecr.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                    pos=ecr.btn_suivant.rect.center))
verifier(ecr.session.reussis() == 0 and ecr.puzzle is not None, "le defi recommence a zero")

ecr.commencer("survie")
for i in range(3):
    avancer(ecr)
    ecr.plateau.make_move(mauvais_coup(ecr))
    if i < 2:
        ecr.enchainer_a = 1
        ecr.update()
verifier(ecr.session.terminee() and "Trois fautes" in ecr.message, "survie : %s" % ecr.message)
ecr.draw()
pygame.image.save(ecran, "tests/capture_survie.png")

print("Records gardes en memoire (banc d'essai 23/10)")
import builtins
import json
lectures = []
def _open_compte(*a, **k):
    if "r" in (a[1] if len(a) > 1 else k.get("mode", "r")):
        lectures.append(a[0])
    return builtins.open(*a, **k)
mp.open = _open_compte
mp.charger()
for _ in range(3):
    ecr.draw()
verifier(not lectures, "dessin de l'ecran : aucune lecture du fichier (%d)" % len(lectures))
d = mp.charger()
d["record_survie"] = 4242
mp.enregistrer(d)
verifier(mp.record("survie") == 4242, "un record enregistre se voit tout de suite")
with builtins.open(mp._chemin(), encoding="utf-8") as f:
    verifier(json.load(f)["record_survie"] == 4242, "et il est bien ecrit sur le disque")
d["record_survie"] = 1
verifier(mp.record("survie") == 4242, "modifier ce qu'on a recu ne change pas la memoire")
del mp.open

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
