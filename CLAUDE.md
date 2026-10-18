# SickChess – consignes pour Claude

Jeu d'échecs PC (Windows) en **Python + Pygame**, moteur **Stockfish**, vendu à petit
prix sur **Steam** et **itch.io**. Auteur : Julien (pas développeur : explications
simples, en français, sans jargon). Positionnement : jeu d'exercice et d'analyse pour
progresser, **ultra compétitif** – joli, facile, professionnel.

## À lire au début de chaque séance
1. `docs/A_FAIRE.md` – ce qui reste à faire et les retours de Julien.
2. `docs/JOURNAL.md` – décisions et historique (la fin du fichier = le plus récent).
3. `docs/SORTIE.md` (Steam / itch.io) et `docs/CREDITS.md` (licences) si la tâche y touche.

## Décisions à respecter
- On garde Python/Pygame (pas de Godot). PC Windows uniquement, pas de mobile.
- **On repart propre** : `../V8_TURBO_3000` est l'archive de référence. Une fonction
  est reprise **une par une**, nettoyée, testée ; le jeu reste jouable après chaque étape.
- **Aucune ressource sans licence vérifiée** (noter dans `docs/CREDITS.md`).
  Stockfish = GPL v3 : livrer `moteur/COPYING-Stockfish.txt` avec le jeu.
- Direction artistique « Onyx & Or » (`jeu/design.py`) ; pièces par défaut « Tournoi plat ».
  Police Barlow Semi Condensed. **Tous les textes affichés avec accents.**
- Notation des coups au choix dans Options, **anglaise par défaut**.
- Tables Syzygy gardées (évaluation, finales, apprentissage).
- Analyse : doit être **puissante, rapide et surtout juste**. Un sacrifice correct n'est
  pas une gaffe : on juge le coup sur l'évaluation du moteur, pas sur le matériel donné.
- Multijoueur par Steam (relais Valve). `MODE_TEST = True` dans `jeu/salon_en_ligne.py`
  tant qu'on teste ; **le passer à False avant la sortie**.

## Organisation
- `SickChess.py` lanceur · `jeu/` code · `tests/` tests · `outils/` scripts (sons, logo,
  Blender) · `assets/`, `sounds/`, `polices/`, `ouvertures/` ressources · `moteur/stockfish.exe`.
- Hors GitHub (gros ou personnels) : `moteur/*.exe`, `puzzles/` (223 Mo), `syzygy/`,
  `steam_api64.dll`, `profil.json`, `parties/`, `puzzles_score.json`.
- Ne jamais écraser `profil.json`, `parties/`, `puzzles_score.json` : ce sont les données
  de Julien. Les tests travaillent dans des dossiers temporaires.

## Commandes
- Lancer le jeu : `python SickChess.py` (ou double-clic `LANCER.bat`).
- **Tous les tests : `python tests/lancer_tous.py`** (`--rapide` = sans Stockfish).
  Une série seule : `python tests/test_revue.py`. Tout doit être vert avant un commit.
- Captures des écrans (pour juger le graphisme) : `python tests/captures_ecrans.py`
  → `tests/ecrans/`.
- Version amis (exe + bouton « Mise à jour ») : `CONSTRUIRE_VERSION_AMIS.bat`
  → `outils/publier_maj.py` ; voir `docs/VERSION_AMIS.md`.
- Sons : `python outils/generer_sons.py`. Logo/icône : `python outils/generer_logo.py`.

## Façon de travailler
- Petites étapes. Après chaque étape : tests verts, une ligne dans `docs/JOURNAL.md`
  (section datée « Fait / À vérifier par Julien »), commit Git clair en français.
- **À chaque séance de code, donner à Julien une liste de tests à faire** sur son PC
  (« Fonctionne / Ne fonctionne pas + commentaire »). Les écrire dans `docs/A_FAIRE.md`,
  section « À tester par Julien ». (Dans Cowork, Claude les recopie aussi dans la page
  « SickChess – À faire » : https://claude.ai/artifact/PzJkQy7b8DKRs9wgksP9T5.)
- Pour un bug : le reproduire dans un test avant de le corriger.
- **Recette complète (`docs/RECETTE.md`)** : la liste de TOUS les tests à la main du jeu
  (R-001…). Elle est fabriquée par `python outils/recette.py` : on modifie la liste
  `RECETTE` dans `outils/recette.py`, jamais RECETTE.md à la main. **Chaque fonction
  ajoutée, modifiée ou retirée = ses lignes de recette mises à jour dans la même séance**
  (nouvel id libre dans la section, on ne réutilise pas un ancien id). Avant chaque
  version amis / Steam : `python tests/lancer_tous.py` tout vert, puis Julien repasse la
  recette (page « À faire », groupe « Recette complète », bouton « Nouvelle passe »).
  Un test « Ne fonctionne pas » devient un contrôle automatique dans `tests/` avant d'être corrigé.
- Ne pas pousser sur GitHub (`git push`) sans que Julien l'ait demandé.

## Deux Claude, un seul dossier
- **Cowork** (application Claude, onglet discussion) : idées, graphisme, Blender, page Steam,
  textes, page « À faire ». Il voit ce dossier, mais sous Linux : il ne lance pas le vrai jeu.
- **Claude Code** (onglet Code, sur ce PC Windows) : lancer le jeu, Stockfish.exe, Steam,
  compiler le .exe, commits Git.
- Le lien entre les deux = **ce fichier + `docs/A_FAIRE.md` + `docs/JOURNAL.md`** :
  toujours les tenir à jour en fin de séance.

## Skills du projet (`.claude/skills/`)
`seance-sickchess` (déroulé d'une séance) · `compiler-exe` (PyInstaller) ·
`verifier-echecs` (règles et analyse justes) · `captures-steam` (images de la page Steam).
Agents (`.claude/agents/`) : `testeur` (cherche les bugs), `relecteur-interface` (graphisme).
