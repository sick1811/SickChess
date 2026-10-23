# Surveillance en direct – SickChess

Le 23/10/2026 19:47 · 832 s de mesure · 12 cœurs logiques · carte graphique mesurée

Fabriqué par `python outils/surveiller.py`. Détail seconde par seconde : `tests/surveillance.csv`.

| Mesure | Moyenne | Pic |
|---|---:|---:|
| Jeu (dessin, sons, logique), en % d'un cœur | 27.6 | 90.1 |
| Stockfish (tous), en % d'un cœur | 668.1 | 1088.0 |
| Tout le PC, en % | 69.0 | 100.0 |
| Mémoire du jeu (Mo) | 140.4 | 227 |
| Mémoire de Stockfish (Mo) | 4166.3 | 6786 |
| Carte graphique, en % | 29.5 | 44.0 |

**Jeu seul quand Stockfish ne calcule pas** (repos, menus) : 30.5 % d'un cœur en moyenne — au-dessus de 10 %, le dessin travaille pour rien (skill performance-pygame).

Les 5 secondes les plus chargées :

- 567 s : jeu 51.0 %, Stockfish ×5 1066.1 %, PC 100.0 %
- 612 s : jeu 28.0 %, Stockfish ×5 1088.0 %, PC 100.0 %
- 618 s : jeu 28.5 %, Stockfish ×5 1083.9 %, PC 100.0 %
- 572 s : jeu 49.1 %, Stockfish ×5 1062.8 %, PC 100.0 %
- 577 s : jeu 48.0 %, Stockfish ×5 1063.2 %, PC 100.0 %
