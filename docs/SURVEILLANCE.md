# Surveillance en direct – SickChess

Le 23/10/2026 20:15 · 1216 s de mesure · 12 cœurs logiques · carte graphique mesurée

Fabriqué par `python outils/surveiller.py`. Détail seconde par seconde : `tests/surveillance.csv`.

| Mesure | Moyenne | Pic |
|---|---:|---:|
| Jeu (dessin, sons, logique), en % d'un cœur | 31.6 | 99.2 |
| Stockfish (tous), en % d'un cœur | 793.9 | 1151.5 |
| Tout le PC, en % | 81.0 | 100.0 |
| Mémoire du jeu (Mo) | 161.5 | 195 |
| Mémoire de Stockfish (Mo) | 4579.3 | 6592 |
| Carte graphique, en % | 23.7 | 55.0 |

**Jeu seul quand Stockfish ne calcule pas** (repos, menus) : 25.0 % d'un cœur en moyenne — au-dessus de 10 %, le dessin travaille pour rien (skill performance-pygame).

Les 5 secondes les plus chargées :

- 630 s : jeu 22.4 %, Stockfish ×3 1151.5 %, PC 100.0 %
- 615 s : jeu 19.5 %, Stockfish ×3 1148.0 %, PC 100.0 %
- 611 s : jeu 18.1 %, Stockfish ×3 1149.2 %, PC 100.0 %
- 619 s : jeu 19.6 %, Stockfish ×3 1147.7 %, PC 100.0 %
- 601 s : jeu 18.1 %, Stockfish ×3 1145.4 %, PC 100.0 %
