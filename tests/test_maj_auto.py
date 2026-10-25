# tests/test_maj_auto.py - mise a jour automatique du menu (23/10, demande de Julien).
#     python tests/test_maj_auto.py
# Verifie mise_a_jour.pas_automatique : telechargement tout seul, redemarrage apres
# 3 s une seule fois, reverification toutes les 3 min (25/10 ; avant 20), reglage "maj_auto" a False.

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))

import mise_a_jour as m

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


class Faux:
    def __init__(self, etat, prog=0.0):
        self.etat = etat
        self._p = prog

    def progression(self):
        return self._p


print("Mise a jour automatique")
verifier(m.pas_automatique(None, {}, 0, {}) == (None, None), "version de developpement : rien")
verifier(m.pas_automatique(Faux("disponible"), {"maj_auto": False}, 0, {}) == (None, None),
         "maj_auto = False : rien d'automatique")
a, lib = m.pas_automatique(Faux("disponible"), {}, 0, {})
verifier(a == "telecharger" and "téléchargement" in lib, "nouvelle version : telechargement lance")
a, lib = m.pas_automatique(Faux("telechargement", 0.42), {}, 0, {})
verifier(a is None and lib.endswith("42 %"), "progression affichee sur le bouton (%s)" % lib)
etat = {}
a, lib = m.pas_automatique(Faux("pret"), {}, 100.0, etat)
verifier(a is None and "prête" in lib, "pret : on previent d'abord")
a, _ = m.pas_automatique(Faux("pret"), {}, 101.0, etat)
verifier(a is None, "pas de redemarrage avant 3 s")
a, _ = m.pas_automatique(Faux("pret"), {}, 103.5, etat)
verifier(a == "installer", "apres 3 s : installation et redemarrage")
a, _ = m.pas_automatique(Faux("pret"), {}, 104.0, etat)
verifier(a is None, "une seule tentative d'installation (pas une par image)")
etat = {}
verifier(m.pas_automatique(Faux("a_jour"), {}, 0, etat)[0] is None, "a jour : rien tout de suite")
verifier(m.pas_automatique(Faux("a_jour"), {}, 2 * 60, etat)[0] is None, "rien avant 3 min")
verifier(m.pas_automatique(Faux("a_jour"), {}, 3 * 60 + 1, etat)[0] == "verifier",
         "jeu reste ouvert : reverification apres 3 min")
verifier(m.pas_automatique(Faux("a_jour"), {}, 3 * 60 + 2, etat)[0] is None,
         "puis attend de nouveau 3 min")
etat = {}
m.pas_automatique(Faux("erreur"), {}, 0, etat)
verifier(m.pas_automatique(Faux("erreur"), {}, 3 * 60 + 1, etat)[0] == "verifier",
         "apres un echec reseau : le jeu reessaie tout seul 3 min plus tard")
verifier(m.pas_automatique(Faux("erreur"), {}, 0, {})[0] is None, "erreur reseau : on ne boucle pas")

print("%d controle(s) en echec" % len(echecs) if echecs else "Tout est bon.")
sys.exit(1 if echecs else 0)
