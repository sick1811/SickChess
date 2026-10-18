# tests/test_statistiques.py - statistiques de progression (17/10, travail p05).
#     python tests/test_statistiques.py
# Des parties et des analyses fabriquees dans un dossier temporaire.

import json
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
TEMP = tempfile.mkdtemp(prefix="sickchess_stats_")
asset_manager.dossier_ecriture = lambda: TEMP

import historique_parties
import statistiques

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def partie(nom, blancs, noirs, resultat, camp, coups_san, ouverture, evals=None, mats=None):
    b = chess.Board()
    ucis = []
    for san in coups_san.split():
        m = b.push_san(san)
        ucis.append(m.uci())
    chemin = os.path.join(historique_parties.dossier_parties(), nom + ".pgn")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write('[White "%s"]\n[Black "%s"]\n[Result "%s"]\n[Joueur "%s"]\n[Opening "%s"]\n\n%s %s\n'
                % (blancs, noirs, resultat, camp, ouverture, coups_san, resultat))
    if evals is not None:
        n = len(ucis) + 1
        b = chess.Board()
        meilleurs = []
        for u in ucis:
            meilleurs.append(u)
            b.push_uci(u)
        meilleurs.append(None)
        meilleurs[5] = "g7g6" if len(meilleurs) > 5 else meilleurs[5]
        d = {"fen": chess.STARTING_FEN, "coups": ucis, "profondeur": 20, "version": 1,
             "evaluations": evals, "mats": mats or [None] * n, "meilleurs": meilleurs,
             "premiers": evals, "seconds": [e - 0.2 if e is not None else None for e in evals]}
        with open(chemin[:-4] + ".analyse.json", "w", encoding="utf-8") as f:
            json.dump(d, f)
    return chemin


print("1. Bilan, ouvertures")
BERGER = "e4 e5 Bc4 Nc6 Qh5 Nf6 Qxf7#"
partie("p1", "Ordinateur", "sick1811", "1-0", "noir", BERGER, "Partie du pion roi",
       evals=[0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 20.0, 20.0],
       mats=[None, None, None, None, None, None, 1, 0])
partie("p2", "sick1811", "Ordinateur", "1-0", "blanc", "e4 c5 Nf3 d6", "Défense sicilienne : variante Najdorf")
partie("p3", "sick1811", "Ordinateur", "1/2-1/2", "blanc", "e4 c5 Nc3 Nc6", "Défense sicilienne, fermée")
partie("p4", "Blancs", "Noirs", "1-0", "", "d4 d5", "Partie du pion dame")     # a deux : ignoree
s = statistiques.calculer()
b = s["bilan"]
verifier(b["parties"] == 3, "3 parties comptees (la partie a deux est ignoree)")
verifier((b["victoires"], b["nulles"], b["defaites"]) == (1, 1, 1), "1 V, 1 N, 1 D")
verifier(abs(s["score"] - 50.0) < 0.01, "score 50 %%")
verifier(abs(s["score_blanc"] - 75.0) < 0.01 and s["score_noir"] == 0.0, "Blancs 75 %%, Noirs 0 %%")
o = dict((nom, (n, sc)) for nom, n, sc in s["ouvertures"])
verifier(o.get("Défense sicilienne") == (2, 75.0), "variantes regroupees : sicilienne 2 parties, 75 %%")
verifier(s["ouvertures"][0][0] == "Défense sicilienne", "la plus jouee en tete")

print("2. Precision et fautes par phase (partie analysee)")
verifier(s["parties_analysees"] == 1 and s["precision_moyenne"] is not None,
         "precision moyenne : %s" % s["precision_moyenne"])
verifier(s["fautes"]["ouverture"] >= 1, "la gaffe 3...Cf6 comptee dans l'ouverture (%s)" % s["fautes"])
verifier(statistiques.phase(chess.STARTING_FEN, 30) == "milieu", "coup 15 avec toutes les pieces : milieu")
verifier(statistiques.phase("4k3/8/8/8/8/8/4P3/R3K3 w - - 0 40", 80) == "finale", "tour contre rien : finale")
verifier(statistiques.famille_d_ouverture("Gambit dame : accepté") == "Gambit dame", "famille d'ouverture")

print("3. L'ecran")
from ecran_statistiques import EcranStatistiques
e = EcranStatistiques(ecran)
verifier(e.attendre() is not None, "calcul en tache de fond termine")
e.draw()
pygame.image.save(ecran, "tests/capture_statistiques.png")
verifier(e.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode="")) == "retour",
         "Echap = retour")
from ecran_mes_parties import EcranMesParties
m = EcranMesParties(ecran)
action = m.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=m.btn_stats.rect.center))
verifier(action == {"action": "statistiques"}, "bouton Statistiques dans Mes parties")
import time as _t
for _i in range(8):                      # apres le fondu d arrivee
    m.draw(); _t.sleep(0.05)
fond = ecran.get_at((m.btn_stats.rect.x - 3, m.btn_stats.rect.centery))
dessus = [ecran.get_at((m.btn_stats.rect.x + 4, m.btn_stats.rect.centery)),
          ecran.get_at((m.btn_importer.rect.x + 4, m.btn_importer.rect.centery))]
print("      couleurs", fond, dessus)
verifier(all(d != fond for d in dessus), "les boutons Statistiques et Importer sont bien dessines")
verifier(m.btn_stats.rect.right < m.btn_importer.rect.left and m.btn_retour.rect.right < m.btn_stats.rect.left,
         "les boutons du bas ne se chevauchent pas")
vide = tempfile.mkdtemp()
asset_manager.dossier_ecriture = lambda: vide
e2 = EcranStatistiques(ecran)
e2.attendre()
e2.draw()
verifier(e2.stats["bilan"]["parties"] == 0, "sans partie : message, pas de plantage")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
