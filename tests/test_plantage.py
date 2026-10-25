# tests/test_plantage.py - le rapport de plantage (24/10, travail p29).
#     python tests/test_plantage.py
# Un vrai plantage du lanceur (SickChess.py copie dans un dossier temporaire, avec
# un faux jeu qui plante expres), puis le lancement suivant : carte, « Signaler »
# deja rempli, envoi, oubli. Dossier temporaire : tes donnees ne sont pas touchees.

import os as _os_envoi
_os_envoi.environ["SICKCHESS_SANS_ENVOI"] = "1"   # 25/10 : jamais de faux message dans le vrai salon Discord
import os
import shutil
import subprocess
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
ecran = pygame.display.set_mode((1024, 640))

import asset_manager
TEMP = tempfile.mkdtemp(prefix="sickchess_plantage_")
asset_manager.dossier_ecriture = lambda: TEMP

import plantage
import signalement
import ui

signalement.ouvrir_le_dossier = lambda chemin: True     # pas d'explorateur pendant les tests
ui.copier = lambda texte: True

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


print("1. Un vrai plantage du lanceur")
essai = tempfile.mkdtemp(prefix="sickchess_lanceur_")
os.makedirs(os.path.join(essai, "jeu"))
shutil.copy(os.path.join(RACINE, "SickChess.py"), essai)
for nom in ("plantage.py", "signalement.py", "asset_manager.py"):
    shutil.copy(os.path.join(RACINE, "jeu", nom), os.path.join(essai, "jeu"))
with open(os.path.join(essai, "jeu", "game_manager.py"), "w", encoding="utf-8") as f:
    f.write("class GameManager:\n"
            "    def __init__(self, version):\n"
            "        print('[TEST] le jeu demarre')\n"
            "    def run(self):\n"
            "        raise RuntimeError('plantage de test')\n"
            "    def cleanup(self):\n"
            "        pass\n")
env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYTHONIOENCODING="utf-8")
p = subprocess.run([sys.executable, os.path.join(essai, "SickChess.py")], cwd=essai, env=env,
                   capture_output=True, text=True, timeout=60)
verifier(p.returncode == 1, "le lanceur rend 1 (plantage)")
asset_manager.dossier_ecriture = lambda: essai
d = plantage.en_attente()
verifier(d is not None and d["erreur"] == "RuntimeError: plantage de test",
         "plantage.json garde l'erreur : %s" % (d or {}).get("erreur"))
verifier(d and "raise RuntimeError" in d["trace"] and "game_manager.py" in d["trace"],
         "avec le detail technique (fichier et ligne)")
verifier(d and "[TEST] le jeu demarre" in d["journal"] and "[SICKCHESS] Demarrage" in d["journal"],
         "et la fin du journal de CE lancement")
verifier(d and d["version"] not in ("", "?") and d["systeme"], "version et systeme notes")
os.remove(os.path.join(essai, "plantage.json"))
p = subprocess.run([sys.executable, os.path.join(essai, "SickChess.py"), "--plantage-test"], cwd=essai,
                   env=env, capture_output=True, text=True, timeout=60)
verifier((plantage.en_attente() or {}).get("erreur") == "RuntimeError: Plantage de test (--plantage-test)",
         "python SickChess.py --plantage-test : plantage volontaire note (recette R-124)")
asset_manager.dossier_ecriture = lambda: TEMP
shutil.rmtree(essai, ignore_errors=True)

print("2. noter() ne plante jamais")
try:
    zero = 0
    print(1 / zero)
except ZeroDivisionError as e:
    d = plantage.noter(e, "9.9")
verifier(d and d["erreur"] == "ZeroDivisionError: division by zero" and plantage.en_attente(),
         "erreur Python ordinaire notee")
asset_manager.dossier_ecriture = lambda: os.path.join(TEMP, "n_existe_pas", "ni_ici")
verifier(plantage.noter(ValueError("x"), "1") is None, "dossier impossible : pas de plantage en plus")
asset_manager.dossier_ecriture = lambda: TEMP

print("3. Plus tard (3 fois au plus), Non merci")
for _ in range(plantage.PROPOSITIONS_MAX - 1):
    plantage.propose_une_fois_de_plus()
verifier(plantage.en_attente() is not None, "propose encore apres 2 « plus tard »")
plantage.propose_une_fois_de_plus()
verifier(plantage.en_attente() is None, "au 3e « plus tard », le rapport est oublie")
plantage.noter(ValueError("y"), "1")
plantage.oublier()
verifier(plantage.en_attente() is None, "Non merci : efface")

print("4. Le lancement suivant : carte, puis « Signaler » deja rempli")
from game_manager import GameManager
gm = GameManager("test")
try:
    raise KeyError("piece")
except KeyError as e:
    plantage.noter(e, "0.2.0")
# Echap sur la carte : plus tard
pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode=""))
gm._proposer_le_rapport_de_plantage()
verifier((plantage.en_attente() or {}).get("propose") == 1, "Echap : on reproposera")
# Non merci
from ecran_plantage import EcranPlantage
carte = EcranPlantage(gm.screen, plantage.en_attente())
carte.draw()
pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=carte.btn_non.rect.center))
gm._proposer_le_rapport_de_plantage()
verifier(plantage.en_attente() is None, "Non merci : le rapport est efface")
# Envoyer le rapport : la carte, puis l'ecran Signaler deja rempli, puis Envoyer
try:
    raise KeyError("piece")
except KeyError as e:
    plantage.noter(e, "0.2.0")
from ecran_signaler import EcranSignaler
vus = []
_init = EcranSignaler.__init__


def espion(self, *a, **k):
    _init(self, *a, **k)
    vus.append(self)
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                         pos=self.btn_envoyer.rect.center))
    pygame.time.set_timer(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0,
                                             unicode=""), 600, 8)


EcranSignaler.__init__ = espion
pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))
gm._proposer_le_rapport_de_plantage()
EcranSignaler.__init__ = _init
pygame.time.set_timer(pygame.KEYDOWN, 0)
s = vus[0] if vus else None
verifier(s is not None and s.champ.contenu.startswith("Le jeu s'est fermé tout seul")
         and "KeyError" in s.champ.contenu, "« Signaler » s'ouvre avec le message deja ecrit")
rapports = os.listdir(os.path.join(TEMP, "rapports")) if os.path.isdir(os.path.join(TEMP, "rapports")) else []
texte = open(os.path.join(TEMP, "rapports", rapports[0]), encoding="utf-8").read() if rapports else ""
verifier("KeyError: 'piece'" in texte and "Journal du lancement qui a plante" in texte
         and "Traceback" in texte, "le rapport contient l'erreur et le journal du lancement qui a plante")
verifier(plantage.en_attente() is None, "une fois le rapport range ou envoye, il n'est plus propose")
verifier(s is not None and s.etat == "fini", "l'envoi s'est termine (%s)" % (s.message if s else ""))

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
ui.retirer_crochet(gm.bandeau)
pygame.quit()
sys.exit(1 if echecs else 0)
