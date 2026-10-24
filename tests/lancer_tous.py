# tests/lancer_tous.py - lance toutes les series de tests d'un coup.
#     python tests/lancer_tous.py            -> tout (avec Stockfish si present)
#     python tests/lancer_tous.py --rapide   -> sans les tests qui font tourner Stockfish
# Chaque serie tourne dans son propre Python (pas de fenetre, pas de son).
# Rien n'est ecrit dans profil.json, config.json ni parties/ (chaque test s'en charge).
# Code de sortie : 0 si tout est vert, 1 sinon.

import os
import subprocess
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERIES = [
    ("test_noyau.py", False),
    ("test_options.py", False),
    ("test_mes_parties.py", False),
    ("test_problemes.py", False),
    ("test_multijoueur.py", False),
    ("test_mise_a_jour.py", False),
    ("test_maj_auto.py", False),
    ("test_pause.py", False),
    ("test_explication_revue.py", False),
    ("test_modes_problemes.py", False),
    ("test_adversaire.py", False),
    ("test_signaler.py", False),
    ("test_import_pgn.py", False),
    ("test_en_ligne_nulle.py", False),
    ("test_en_ligne_revue.py", False),
    ("test_invitations.py", False),
    ("test_classements.py", False),
    ("test_precision.py", False),
    ("test_plantage.py", False),
    ("test_endurance.py", False),
    ("test_verifier_version.py", False),
    ("test_petit_pc.py", False),
    ("test_cache_analyse.py", False),
    ("test_statistiques.py", False),
    ("test_entrainement.py", False),
    ("test_premier_lancement.py", False),
    ("test_sons_musique.py", False),
    ("test_effets.py", False),
    ("test_succes.py", False),
    ("test_anglais.py", False),
    ("test_analyse_profonde.py", False),
    ("test_modes_analyse.py", False),
    ("test_analyse_libre.py", False),
    ("test_revue.py", True),            # True = utilise Stockfish
    ("test_analyse_directe.py", True),
    ("test_mes_erreurs.py", True),
    ("test_variantes.py", True),
    ("test_analyse_libre_moteur.py", True),
    ("test_precision_moteur.py", True),
]


def main():
    rapide = "--rapide" in sys.argv
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
               PYTHONIOENCODING="utf-8")
    resultats = []
    for nom, lourd in SERIES:
        if rapide and lourd:
            continue
        chemin = os.path.join(RACINE, "tests", nom)
        if not os.path.exists(chemin):
            continue
        debut = time.time()
        try:
            p = subprocess.run([sys.executable, chemin], cwd=RACINE, env=env,
                               capture_output=True, text=True, timeout=600,
                               encoding="utf-8", errors="replace")
            ok, sortie = p.returncode == 0, p.stdout + p.stderr
        except subprocess.TimeoutExpired:
            ok, sortie = False, "trop long (plus de 10 minutes)"
        duree = time.time() - debut
        nb_ok = sortie.count("  OK   ")
        nb_ko = sortie.count("  ECHEC ")
        resultats.append((nom, ok, nb_ok, nb_ko, duree))
        print("%-26s %s  %3d OK  %2d echec(s)  %5.1f s"
              % (nom, "VERT " if ok else "ROUGE", nb_ok, nb_ko, duree))
        if not ok:
            lignes = [l for l in sortie.splitlines()
                      if "ECHEC" in l or "Error" in l or "Traceback" in l]
            for l in (lignes or sortie.splitlines())[-15:]:
                print("    " + l)
    total_ok = sum(r[2] for r in resultats)
    rouges = [r[0] for r in resultats if not r[1]]
    print("-" * 60)
    print("%d controles OK. %s" % (total_ok, "Tout est vert." if not rouges
                                   else "En rouge : " + ", ".join(rouges)))
    return 1 if rouges else 0


if __name__ == "__main__":
    sys.exit(main())
