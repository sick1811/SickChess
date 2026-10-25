# tests/test_livre_fils.py - le livre d'ouvertures lu par plusieurs fils a la fois
# (25/10, defaut de l'optimiseur, revue lente t71 : livre() publiait une table
# vide puis la remplissait ; un autre fil d'analyse croyait alors 1...e5 hors du
# livre, le verifiait 33 s avec Stockfish et pouvait perdre la pastille
# « Théorique »).
#     python tests/test_livre_fils.py

import os
import sys
import threading
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))

import ouvertures

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


FILS = 4
TOURS = 20
COUPS = ["e4", "e5"]

print("1. %d fils lisent 1.e4 e5 juste apres recharger(), %d fois" % (FILS, TOURS))
rates = []
for tour in range(TOURS):
    ouvertures.recharger()
    depart = threading.Barrier(FILS)
    reponses = []

    def lire(numero, depart=depart, reponses=reponses):
        depart.wait()
        # Le fil 0 lance le chargement ; les autres arrivent PENDANT, des que
        # le livre est publie (c'est le moment ou l'analyse de fond le lit).
        if numero:
            for _ in range(20000):
                if ouvertures._LIVRE is not None:
                    break
                time.sleep(0.0005)
        # La moitie des fils demande le coup, l'autre le nombre de coups de livre.
        if numero % 2:
            reponses.append(ouvertures.est_un_coup_de_livre(COUPS, 1))
        else:
            reponses.append(ouvertures.coups_de_livre(COUPS) == 2)

    fils = [threading.Thread(target=lire, args=(n,)) for n in range(FILS)]
    for f in fils:
        f.start()
    for f in fils:
        f.join()
    if len(reponses) != FILS or not all(reponses):
        rates.append((tour, reponses))
verifier(not rates, "tous les fils voient 1...e5 dans le livre (%d tour(s) rate(s) sur %d%s)"
         % (len(rates), TOURS, " ; ex. : tour %d -> %s" % rates[0] if rates else ""))

print("2. Apres le chargement, la source et le nom restent coherents")
verifier("ouvertures" in ouvertures.source(), "source : %s" % ouvertures.source())
verifier(ouvertures.nom_de_l_ouverture(COUPS) != "",
         "nom de 1.e4 e5 : « %s »" % ouvertures.nom_de_l_ouverture(COUPS))

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
