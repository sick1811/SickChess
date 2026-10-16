# SickChess

Jeu d'échecs pour PC (Windows), destiné à Steam et itch.io.
Python + Pygame, moteur Stockfish.

## Lancer le jeu
1. Installer Python 3 (cocher « Add Python to PATH »).
2. Placer `stockfish.exe` dans `moteur/` (voir `moteur/LISEZ-MOI.txt`).
3. Double-cliquer sur `LANCER.bat`.

## Organisation
- `SickChess.py` – le lanceur
- `jeu/` – le code
- `sounds/`, `polices/`, `ouvertures/`, `assets/` – les ressources
- `moteur/` – Stockfish
- `outils/` – scripts (génération des sons…)
- `tests/` – `python tests/test_noyau.py`
- `docs/` – `JOURNAL.md` (avancement), `CREDITS.md` (licences)

Commandes : F11 plein écran, F1 aide des raccourcis.
