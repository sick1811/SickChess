# tests/test_analyse_de_fond.py - l'analyse des parties en tache de fond
# (25/10, travail p25). Avec le vrai Stockfish, dans un dossier temporaire.
#     python tests/test_analyse_de_fond.py

import inspect
import json
import os
import sys
import tempfile
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import asset_manager
_DOSSIER = tempfile.mkdtemp(prefix="sickchess_fond_")
asset_manager.dossier_ecriture = lambda: _DOSSIER       # jamais tes vraies parties

import analyse_de_fond
import historique_parties
from analyse_partie import AnalyseurPartie

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def chemin_stockfish():
    chemin = os.environ.get("SICKCHESS_STOCKFISH")
    if not chemin:
        try:
            with open("config.json", encoding="utf-8") as f:
                chemin = json.load(f).get("stockfish_path")
        except (OSError, ValueError):
            chemin = None
    return chemin if chemin and os.path.exists(chemin) else None


def ecrire_partie(nom, coups, age):
    chemin = os.path.join(historique_parties.dossier_parties(), nom + ".pgn")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write('[Event "Test"]\n[White "Toi"]\n[Black "Ordinateur"]\n[Result "*"]\n\n%s *\n\n' % coups)
    os.utime(chemin, (time.time() - age, time.time() - age))
    return chemin


def attendre(condition, secondes):
    fin = time.time() + secondes
    while time.time() < fin:
        if condition():
            return True
        time.sleep(0.2)
    return condition()


print("1. Reglage et ecrans")
import game_manager
verifier("_analyse_de_fond().reprendre()" in inspect.getsource(game_manager.GameManager.show_menu),
         "le menu relance l'analyse de fond")
verifier("puzzles" in game_manager.GameManager.ECRANS_AVEC_FOND
         and "analyse" not in game_manager.GameManager.ECRANS_AVEC_FOND,
         "elle continue pendant les Problemes, s'arrete pour l'analyse libre")
verifier("_analyse_de_fond().pause()" in inspect.getsource(game_manager.GameManager._une_partie),
         "elle s'arrete quand une partie commence")
coupee = analyse_de_fond.AnalyseDeFond("x", {"analyse_de_fond": False})
verifier(not coupee.reprendre(), "reglage « analyse_de_fond » a faux : rien ne demarre")

sf = chemin_stockfish()
if not sf:
    print("2. (pas de Stockfish : controles avec le vrai moteur sautes)")
else:
    print("2. Deux parties sans analyse : calculees toutes seules (%s)" % os.path.basename(sf))
    reglage = {"analyse_mode": "calcul", "analyse_niveau": "rapide"}
    courte = ecrire_partie("courte", "1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6", 100)
    berger = ecrire_partie("berger", "1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7#", 50)
    fond = analyse_de_fond.AnalyseDeFond(sf, reglage, threads=1)
    debut = time.time()
    verifier(fond.reprendre(), "l'analyse de fond demarre")
    verifier(attendre(lambda: analyse_de_fond.revue_prete(courte) and analyse_de_fond.revue_prete(berger), 240),
             "les deux revues sont pretes (%.0f s)" % (time.time() - debut))
    verifier(attendre(lambda: fond.terminees == 2, 5), "2 parties analysees (%d)" % fond.terminees)
    verifier(attendre(lambda: not (fond._fil and fond._fil.is_alive()), 10) and fond._moteur is None,
             "plus rien a faire : son Stockfish est ferme")
    donnees, _ = historique_parties.lire_partie(berger)
    revue = AnalyseurPartie(donnees["fen"], donnees["coups"], sf, "calcul_rapide",
                            fichier_cache=os.path.splitext(berger)[0] + ".analyse.json")
    verifier(revue.terminee(), "la revue relit l'analyse : rien a recalculer")

    print("3. Pause (une partie commence) puis reprise par la revue")
    longue = ecrire_partie("longue", "1. d4 d5 2. c4 e6 3. Nc3 Nf6 4. Bg5 Be7 5. e3 O-O 6. Nf3 Nbd7 "
                           "7. Rc1 c6 8. Bd3 dxc4 9. Bxc4 Nd5 10. Bxe7 Qxe7 11. O-O Nxc3 12. Rxc3 e5", 10)
    fond.nouvelle_partie()
    verifier(fond.reprendre(), "une nouvelle partie : l'analyse de fond repart")
    verifier(attendre(lambda: fond.en_cours == longue and fond._analyseurs.get(longue) is not None
                      and sum(1 for v in fond._analyseurs[longue].niveau if v) >= 3, 120),
             "elle travaille sur la nouvelle partie")
    debut = time.perf_counter()
    fond.pause()
    duree = time.perf_counter() - debut
    verifier(duree < 1.5 and fond._moteur is None, "pause : Stockfish ferme en %.2f s" % duree)
    partielle = fond._analyseurs.get(longue)
    faites = sum(1 for v in partielle.niveau if v) if partielle else 0
    verifier(partielle is not None and faites >= 3 and not partielle.terminee(),
             "le travail deja fait est garde (%d positions)" % faites)
    verifier(not analyse_de_fond.revue_prete(longue), "pas de fichier tant que ce n'est pas fini")
    donnees, _ = historique_parties.lire_partie(longue)
    revue = AnalyseurPartie(donnees["fen"], donnees["coups"], sf, "calcul_rapide",
                            fichier_cache=os.path.splitext(longue)[0] + ".analyse.json")
    reprises = revue.reprendre_de(fond.prendre(longue))
    verifier(reprises >= 3, "la revue reprend ce qui est deja calcule (%d positions)" % reprises)
    verifier(longue not in fond._analyseurs, "et l'analyse de fond la laisse a la revue")
    forte = AnalyseurPartie(donnees["fen"], donnees["coups"], sf, "calcul_maximale")
    verifier(forte.reprendre_de(revue) == 0, "une analyse plus faible n'est jamais reprise par une plus forte")
    fond.fermer()

    print("4. Mes parties : « Revue prête »")
    import pygame
    pygame.init()
    ecran = pygame.display.set_mode((1280, 720))
    from ecran_mes_parties import EcranMesParties
    e = EcranMesParties(ecran)
    verifier(courte in e.revues_pretes and berger in e.revues_pretes and longue not in e.revues_pretes,
             "les parties analysees ont « Revue prête », pas l'autre")
    e.draw()
    pygame.image.save(ecran, os.path.join(_DOSSIER, "mes_parties.png"))
    pygame.quit()

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
