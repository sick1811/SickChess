---
name: verifier-echecs
description: Vérifier que SickChess est juste aux échecs - règles (roque, prise en passant, promotion, nulles), pastilles de la revue (gaffe, brillant, sacrifice), précision et évaluation. À utiliser après une modification des règles, de l'analyse ou des annotations, ou quand Julien signale une pastille fausse.
---

# Vérifier la justesse (jeu ultra compétitif)

## 1. Règles du jeu
- Comparer `jeu/rules.py` / `move_handler.py` avec **python-chess** (la référence) :
  sur des milliers de positions aléatoires et de parties de la base `puzzles/`,
  la liste des coups légaux du jeu doit être identique à `board.legal_moves`.
- Cas à couvrir : roque des deux côtés (et interdit sous échec / à travers une case
  attaquée), prise en passant (y compris celle qui découvre un échec), promotion en
  dame / tour / fou / cavalier pour les deux couleurs, pat, triple répétition,
  50 coups, matériel insuffisant, fin au temps avec matériel insuffisant adverse (= nulle).
- Écrire ces contrôles dans une série `tests/test_regles.py` (déclarée dans
  `tests/lancer_tous.py`).

## 2. Pastilles de la revue
- Principe : **on juge le coup sur l'évaluation du moteur avant / après**, pas sur le
  matériel. Un sacrifice qui garde l'évaluation = bon coup, voire « Brillant ».
  Donner une pièce sans compensation = gaffe.
- Évaluation assez profonde pour ne pas se tromper (Syzygy en finale ≤ 7 pièces).
- Banque de positions de contrôle (FEN + coup + pastille attendue) dans
  `tests/positions_revue.json`, enrichie à chaque retour de Julien
  (« coup n°, ce que j'attendais ») : sacrifices célèbres (ex. Fxh7+, Txf7),
  vraies gaffes (dame en prise), mats, finales.
- Vérifier les seuils de `jeu/annotations.py` sur cette banque ; tout écart = test rouge.

## 3. Précision
- La précision (méthode lichess) doit être stable d'une analyse à l'autre de la même
  partie (même puissance) et cohérente avec le compte des pastilles.

Lancer : `python tests/lancer_tous.py` (Stockfish requis pour les parties 2 et 3).
