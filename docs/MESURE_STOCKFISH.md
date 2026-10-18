# Mesure de Stockfish sur ce PC

Fait par `outils/mesurer_stockfish.py` le 18/10/2026 03:53.
12 processeurs logiques ; partie 2026-10-17_23h31_SICK-1811-dragondu5-import.pgn, 20 positions ; 50 millions de noeuds par position (calcul fixe).

| Répartition | Toute la série | Par position | 1re position | Profondeur moyenne (min) | Millions de nœuds/s |
|---|---|---|---|---|---|
| 1 × 12 | 191 s | 9.6 s | 27.2 s | 50.0 (18) | 4.7 |
| 3 × 4 | 195 s | 9.8 s | 46.2 s | 52.6 (23) | 4.6 |
| 6 × 2 | 207 s | 10.3 s | 93.0 s | 54.6 (26) | 4.3 |
| 12 × 1 | 253 s | 12.7 s | 85.6 s | 57.2 (29) | 3.5 |

Plus rapide pour toute la série : **1 × 12**.

## Durée estimée d'une revue (partie de 40 coups = 80 positions)

Avec la répartition la plus rapide (4.7 millions de nœuds/s) :

- Calcul fixe – Rapide (10 M) : environ 3.4 min
- Calcul fixe – Forte (25 M) : environ 8.6 min
- Calcul fixe – Maximale (50 M) : environ 17.1 min
