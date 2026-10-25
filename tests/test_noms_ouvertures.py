# tests/test_noms_ouvertures.py - les noms d'ouvertures en francais, sans reste
# d'anglais (25/10, defaut Cowork : « Ouverture King's du cavalier, Variante
# normale » dans l'entrainement aux ouvertures).
#     python tests/test_noms_ouvertures.py

import glob
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))

import ouvertures_fr as o

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


print("1. Les noms signales par Cowork et leurs cousins")
ATTENDUS = {
    "King's Knight Opening: Normal Variation": "Partie du cavalier roi, Variante normale",
    "King's Knight Opening": "Partie du cavalier roi",
    "Petrov's Defense": "Défense russe",
    "Bishop's Opening: Berlin Defense": "Ouverture du fou, Défense Berlin",
    "English Opening: King's English Variation": "Ouverture anglaise, Variante anglaise du roi",
    "Benoni Defense: King's Indian System": "Défense Benoni, Système est-indien",
    "King's Gambit Declined: Queen's Knight Defense": "Gambit du roi refusé, Défense du cavalier dame",
    "Benoni Defense: King's Pawn Line": "Défense Benoni, Ligne du pion roi",
}
for anglais, francais in ATTENDUS.items():
    obtenu = o.traduire(anglais)
    verifier(obtenu == francais, "%s -> « %s »" % (anglais, obtenu))

print("2. Tout le livre d'ouvertures : plus aucun « 's » anglais")
noms = set()
for fichier in glob.glob(os.path.join("ouvertures", "*.tsv")):
    with open(fichier, encoding="utf-8") as f:
        for ligne in f:
            morceaux = ligne.rstrip("\n").split("\t")
            if len(morceaux) >= 2 and morceaux[0] != "eco":
                noms.add(morceaux[1])
restes = sorted((n, o.traduire(n)) for n in noms if re.search(r"\w's\b", o.traduire(n)))
verifier(len(noms) > 3000, "%d noms lus" % len(noms))
verifier(not restes, "%d nom(s) avec un possessif anglais%s" % (
    len(restes), " ; ex. : %s -> %s" % restes[0] if restes else ""))
for n, t in restes[:15]:
    print("      %s -> %s" % (n, t))

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
