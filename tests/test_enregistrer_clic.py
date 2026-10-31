# tests/test_enregistrer_clic.py - t68 : « Enregistrer n'a pas réagi une fois ».
#     python tests/test_enregistrer_clic.py
#
# Enquête du 31/10 (agent enqueteur-bug). Le seul bouton « Enregistrer » du jeu
# est celui de l'écran Options (ecran_options.py). Ce fichier vérifie :
#   1. (CAUSE PROBABLE) Sous Windows, SDL 2 JETTE le clic qui sert à remettre la
#      fenêtre du jeu au premier plan (réglage SDL_MOUSE_FOCUS_CLICKTHROUGH,
#      « 0 » par défaut). Le jeu agit au MOUSEBUTTONDOWN : si on revient au jeu
#      en cliquant directement sur « Enregistrer » (après être passé par une
#      autre fenêtre : page « À faire », Cowork, navigateur...), le clic ne
#      ressort jamais de pygame -> rien ne se passe ; le 2e clic marche.
#      Le lanceur doit donc régler SDL_MOUSE_FOCUS_CLICKTHROUGH=1 avant pygame.
#   2. (DÉFAUT VOISIN) config.json impossible à écrire : l'écran se fermait
#      quand même comme si tout était enregistré (le choix était perdu en silence).
#   3. (GARDE, vert) des centaines de clics simulés sur le bouton tel qu'il est
#      dessiné (tailles, onglets, Taille des textes, anglais, molette,
#      redimensionnement) : tous doivent donner « enregistre ».
# Rien de Julien n'est touché : tout se passe dans un dossier temporaire.

import os
import random
import re
import shutil
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

TEMP = tempfile.mkdtemp(prefix="sickchess_enregistrer_")
import asset_manager  # noqa: E402
asset_manager.dossier_ecriture = lambda: TEMP
with open(os.path.join(TEMP, "config.json"), "w", encoding="utf-8") as f:
    f.write("{}")

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1024, 640), pygame.RESIZABLE)

import ui  # noqa: E402
from ecran_options import EcranOptions  # noqa: E402
from settings_screen import _chemin_config  # noqa: E402

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def ev(type_, **k):
    return pygame.event.Event(type_, **k)


def clic(pos):
    return [ev(pygame.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(0, 0, 0)),
            ev(pygame.MOUSEBUTTONDOWN, pos=pos, button=1),
            ev(pygame.MOUSEBUTTONUP, pos=pos, button=1)]


class _Horloge:
    def tick(self, *_a):
        return 16


def lancer(script, taille=(1024, 640), images_max=30):
    """Fait tourner la VRAIE boucle EcranOptions.run() ; script(ecran, n) donne
    les evenements de l'image n. Renvoie la reponse de run() (None = rien)."""
    pygame.display.set_mode(taille, pygame.RESIZABLE)
    ui._etat_fenetre["taille"] = taille
    ecran = EcranOptions(pygame.display.get_surface())
    compteur = [0]
    vrai = ui.evenements

    class _Fin(Exception):
        pass

    def faux():
        pygame.event.get()
        n = compteur[0]
        compteur[0] += 1
        if n >= images_max:
            raise _Fin()
        return script(ecran, n)

    ui.evenements = faux
    try:
        return ecran.run(_Horloge())
    except _Fin:
        return None
    finally:
        ui.evenements = vrai


try:
    print("1. Le clic qui ramène la fenêtre au premier plan n'est pas jeté (Windows)")
    textes = []
    for chemin in [os.path.join(RACINE, "SickChess.py")] + [
            os.path.join(RACINE, "jeu", n) for n in os.listdir(os.path.join(RACINE, "jeu"))
            if n.endswith(".py")]:
        with open(chemin, encoding="utf-8", errors="replace") as f:
            textes.append(f.read())
    regle = any(re.search(r"""SDL_MOUSE_FOCUS_CLICKTHROUGH["']\s*[,\]=]\s*["']1["']""", t)
                for t in textes)
    verifier(regle, "SDL_MOUSE_FOCUS_CLICKTHROUGH = \"1\" réglé par le jeu (sinon SDL jette "
                    "le 1er clic quand la fenêtre n'avait pas la main : « Enregistrer » ne réagit pas)")

    print("2. config.json impossible à écrire : pas de « enregistré » en silence")
    chemin = _chemin_config()
    verifier(chemin.startswith(TEMP), "config.json de test dans le dossier temporaire")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write('{"analyse_niveau": "rapide"}')
    os.chmod(chemin, 0o444)
    try:
        def script_bloque(ecran, n):
            if n == 0:
                ecran.valeurs["analyse_niveau"] = "forte"
            if n == 2:
                return clic(ecran.btn_ok.rect.center)
            return []
        reponse = lancer(script_bloque, images_max=6)
    finally:
        os.chmod(chemin, 0o666)
    with open(chemin, encoding="utf-8") as f:
        ecrit = f.read()
    verifier(not (reponse == "enregistre" and "forte" not in ecrit),
             "écriture ratée : l'écran ne dit pas « enregistré » (réponse %r, fichier %s)"
             % (reponse, ecrit.strip()))
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("{}")

    print("3. Garde : clics sur le bouton tel qu'il est dessiné")
    hasard = random.Random(68)
    tailles = [(1024, 640), (1280, 720), (1366, 768), (1920, 1080), (800, 600), (2560, 1440)]
    rates = 0
    essais = 0

    def script_garde(variante):
        def script(ecran, n):
            if n == 0:
                ecran.onglet = hasard.randrange(len(ecran.onglets))
                if variante == "echelle":
                    ecran.valeurs["echelle_interface"] = hasard.choice([0.88, 1.0, 1.15, 1.30])
                    ecran._appliquer_en_direct("echelle_interface")
                elif variante == "anglais":
                    ecran.valeurs["langue"] = "en"
                    ecran._appliquer_en_direct("langue")
                return []
            if n == 1 and variante == "molette":
                return [ev(pygame.MOUSEWHEEL, x=0, y=-hasard.randrange(1, 8), flipped=False)]
            if n == 1 and variante == "taille":
                w, h = hasard.choice(tailles)
                return [ev(pygame.VIDEORESIZE, w=w, h=h, size=(w, h))]
            if n == 3:
                r = ecran.btn_ok.rect
                return clic((hasard.randrange(r.left, r.right), hasard.randrange(r.top, r.bottom)))
            return []
        return script

    for variante in ("simple", "echelle", "anglais", "molette", "taille", "image0"):
        for _ in range(20):
            essais += 1
            if variante == "image0":       # clic avant le 1er dessin (pendant le fondu)
                reponse = lancer(lambda e, n: clic(e.btn_ok.rect.center) if n == 0 else [],
                                 taille=hasard.choice(tailles))
            else:
                reponse = lancer(script_garde(variante), taille=hasard.choice(tailles))
            if reponse != "enregistre":
                rates += 1
        import langue
        langue.regler("fr")
    verifier(rates == 0, "%d clics simulés sur « Enregistrer » : %d sans réponse" % (essais, rates))
finally:
    try:
        import langue
        langue.regler("fr")
    except Exception:
        pass
    pygame.quit()
    shutil.rmtree(TEMP, ignore_errors=True)

print()
if echecs:
    print("%d ECHEC(S) :" % len(echecs))
    for m in echecs:
        print("  - " + m)
    sys.exit(1)
print("Tout est bon.")
sys.exit(0)
