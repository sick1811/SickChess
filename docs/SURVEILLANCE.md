# Surveillance en direct – SickChess

Le 23/10/2026 16:47 · 4 s de mesure · 2 cœurs logiques · carte graphique non mesurée

Fabriqué par `python outils/surveiller.py`. Détail seconde par seconde : `tests/surveillance.csv`.

| Mesure | Moyenne | Pic |
|---|---:|---:|
| Jeu (dessin, sons, logique), en % d'un cœur | 40.4 | 96.7 |
| Stockfish (tous), en % d'un cœur | 0.0 | 0.0 |
| Tout le PC, en % | 18.7 | 39.7 |
| Mémoire du jeu (Mo) | 34.8 | 48 |
| Mémoire de Stockfish (Mo) | 0 | 0 |

**Jeu seul quand Stockfish ne calcule pas** (repos, menus) : 40.4 % d'un cœur en moyenne — au-dessus de 10 %, le dessin travaille pour rien (skill performance-pygame).

Les 5 secondes les plus chargées :

- 2 s : jeu 96.7 %, Stockfish ×0 0.0 %, PC 39.7 %
- 3 s : jeu 37.9 %, Stockfish ×0 0.0 %, PC 13.2 %
- 4 s : jeu 25.0 %, Stockfish ×0 0.0 %, PC 20.1 %
- 1 s : jeu 2.0 %, Stockfish ×0 0.0 %, PC 1.9 %
