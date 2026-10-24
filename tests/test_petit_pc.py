# tests/test_petit_pc.py - le mode « petit PC » (24/10, travail p31).
#     python tests/test_petit_pc.py
# La detection (coeurs, memoire), le choix d'Options, et ce qui change sur un petit
# PC : analyse (1 Stockfish, 1 Go, 1 coeur en partie, Rapide par defaut), confettis,
# images au repos. Tout est force (petit_pc.forcer) : le resultat ne depend pas du PC.

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((1024, 640))

import analyse_partie as A
import petit_pc
import ui

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


print("1. La detection")
for coeurs, memoire, attendu in ((12, 16384, "normal"), (4, 16384, "petit"), (8, 8192, "petit"),
                                 (8, 7900, "petit"), (6, 16000, "normal"), (12, None, "normal"),
                                 (2, None, "petit")):
    verifier(petit_pc.detecter(coeurs, memoire) == attendu,
             "%d coeurs, %s Mo : %s" % (coeurs, memoire, attendu))
verifier(petit_pc.mode("petit") == "petit" and petit_pc.mode("normal") == "normal",
         "Options : Petit PC / PC normal imposent le mode")
verifier(petit_pc.mode("auto") == petit_pc.detecter(), "Options : Automatique = ce qui est detecte")
verifier(petit_pc.description().startswith("Ce PC : %d cœurs" % (os.cpu_count() or 2)),
         "description dans Options : %s" % petit_pc.description())

print("2. L'analyse sur un petit PC")
ancien_cpu = os.cpu_count
os.cpu_count = lambda: 12
petit_pc.forcer("normal")
z = A.AnalyseurPartie(None, ["e2e4"], "x")
s = A.AnalyseurPartie(None, ["e2e4"], "x", suivi=True)
normal = (z._moteurs_prevus(), z._nombre_de_moteurs(), z._threads_par_moteur(), s._threads_par_moteur(),
          A.hachage_total_mo(16384), A.puissance_de({}))
petit_pc.forcer("petit")
petit = (z._moteurs_prevus(), z._nombre_de_moteurs(), z._threads_par_moteur(), s._threads_par_moteur(),
         A.hachage_total_mo(16384), A.puissance_de({}))
os.cpu_count = ancien_cpu
verifier(normal == (3, 3, 4, 6, 4096, "calcul_forte"),
         "PC normal (12 coeurs, 16 Go) : 3 Stockfish x 4 coeurs, 6 en partie, 4 Go, Forte %s" % (normal,))
verifier(petit == (1, 1, 11, 1, petit_pc.HACHAGE_PETIT_MO, "calcul_rapide"),
         "petit PC : 1 Stockfish (11 coeurs apres la partie), 1 coeur en partie, 1 Go, Rapide %s" % (petit,))
verifier(A.puissance_de({"analyse_niveau": "maximale"}) == "calcul_maximale",
         "un choix du joueur (Maximale) est respecte, meme sur un petit PC")

print("3. Affichage")
import effets
e = effets.Effets()
e.mat(4)
verifier(len(e.liste[-1]["particules"]) == petit_pc.CONFETTIS_PETIT, "petit PC : 30 confettis")
verifier(ui.images_au_repos() == 24, "petit PC : 24 images/s au repos")
petit_pc.forcer("normal")
e.mat(4)
verifier(len(e.liste[-1]["particules"]) == 90 and ui.images_au_repos() == 30,
         "PC normal : 90 confettis, 30 images/s au repos")

print("4. Options")
import ecran_options
reglages = {r.cle: r for _cle, _nom, liste in ecran_options._onglets() for r in liste}
r = reglages.get("mode_pc")
verifier(r is not None and [v for _n, v in r.valeurs] == ["auto", "petit", "normal"],
         "Options → Affichage → « Puissance du PC » : Automatique / Petit PC / PC normal")
verifier(r is not None and r.explication.startswith("Ce PC :"), "avec ce que le jeu a detecte")
import apparence
verifier(apparence.DEFAUTS.get("mode_pc") == "auto", "Automatique par defaut")
petit_pc.forcer(None)

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
