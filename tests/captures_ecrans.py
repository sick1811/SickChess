# tests/captures_ecrans.py - photographie les ecrans du jeu dans tests/ecrans/.
#     python tests/captures_ecrans.py
# Sert a verifier la direction artistique d'un coup d'oeil (rien n'est enregistre
# dans le profil ni dans config.json). Avec la variable SICKCHESS_STOCKFISH, la
# revue est aussi photographiee avec une vraie analyse.

import os
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import pygame

SORTIE = os.path.join(RACINE, "tests", "ecrans")
os.makedirs(SORTIE, exist_ok=True)
TAILLE = tuple(int(v) for v in os.environ.get("SICKCHESS_TAILLE", "1280x720").split("x"))

PARTIE = ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "f3g5", "d7d5", "e4d5",
          "c6a5", "c4b5", "c7c6", "d5c6", "b7c6", "b5e2", "h7h6", "g5f3", "e5e4",
          "f3e5", "f8d6", "d2d4", "e8g8"]


def photo(ecran, nom):
    pygame.image.save(ecran, os.path.join(SORTIE, nom + ".png"))
    print("  ", nom)


from game_manager import GameManager
gm = GameManager("0.x")
gm.screen = pygame.display.set_mode(TAILLE)
gm._appliquer_taille(*TAILLE)

# 1. menu
gm.menu.draw(); photo(gm.screen, "01_menu")

# 2. reglages avant partie
from settings_screen import SettingsScreen
for mode in ("stockfish", "hotseat"):
    SettingsScreen(gm.screen, mode).draw()
    photo(gm.screen, "02_reglages_" + mode)

# 3. partie en cours (a deux, 5 min + 3 s)
gm.game_mode = "hotseat"
gm.reglages = {"minutes": 5, "increment": 3, "pendule_active": True,
               "retourner_plateau": False}
gm.preparer_partie()
p = gm.board
for uci in PARTIE:
    p.make_move(chess.Move.from_uci(uci))
fin = time.time() + 1.0
while time.time() < fin:
    p.update(); time.sleep(0.02)
p.draw(); photo(gm.screen, "03_partie")

# 4. aide F1 par-dessus la partie
gm.aide.basculer()
gm.aide.draw(gm.screen, p.theme_plateau); photo(gm.screen, "04_aide")
gm.aide.basculer()

# 5. promotion
gm.cleanup_game()
gm.preparer_partie()
p = gm.board
p.board.set_fen("8/5P1k/8/8/8/8/8/K7 w - - 0 1")
p.draw()
try:
    p.promotion.ouvrir(chess.F7, chess.F8, chess.WHITE)
except Exception as e:
    print("   (promotion non photographiee : %s)" % e)
p.draw(); photo(gm.screen, "05_promotion")
gm.cleanup_game()

# 6. revue (si un Stockfish utilisable est donne)
sf = os.environ.get("SICKCHESS_STOCKFISH")
if sf:
    from analyse_partie import AnalyseurPartie
    from ecran_revue import EcranRevue
    a = AnalyseurPartie(None, PARTIE, sf, "rapide")
    revue = EcranRevue(gm.screen, a, gm.config, noms=("Toi", "Ordinateur (1200)"),
                       resultat="*")
    fin = time.time() + 90
    while a.en_cours and time.time() < fin:
        time.sleep(0.2)
    revue.aller_a(10, son=False)
    fin = time.time() + 0.6
    while time.time() < fin:
        revue.plateau.update(); time.sleep(0.02)
    revue.draw(); photo(gm.screen, "06_revue")
    a.arreter() if hasattr(a, "arreter") else None

print("captures dans", SORTIE)
pygame.quit()
