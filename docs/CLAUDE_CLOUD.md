# SickChess avec Claude dans le cloud

Claude Code peut travailler sur SickChess **dans le cloud** (claude.ai/code, l'application
Claude, ou « Cloud » au lieu de « Local » dans l'application de bureau) : la session continue
même PC éteint. Elle tourne sur un ordinateur Linux (Ubuntu 24.04) qui récupère le dépôt
`sick1811/SickChess` sur GitHub.

> Ce n'est **pas** GitHub Codespaces. Les « prebuilds » Codespaces ne servent à rien ici :
> les supprimer dans https://github.com/sick1811/SickChess/settings/codespaces.

## À faire une fois

1. Ouvrir https://claude.ai/code → environnement (en haut, le nom de l'environnement →
   **Ajouter** ou **Modifier**).
2. **Accès réseau** : **Trusted** (par défaut). Il laisse passer PyPI, GitHub et Ubuntu.
3. **Variables d'environnement** — ajouter :
   ```
   SICKCHESS_STOCKFISH=/usr/local/bin/stockfish
   ```
4. **Setup script** : **Choose file** → `outils/cloud/configuration.sh` (ou copier-coller son
   contenu). Il installe pygame, python-chess, ruff, vulture, psutil, numpy, Stockfish 17.1
   pour Linux et la base des problèmes (prise dans la version amis publiée). Environ 1 à 3 min
   la première fois ; ensuite le résultat est gardé et les sessions démarrent tout de suite.
5. Enregistrer. Sur GitHub, le dépôt doit être accessible à Claude (application GitHub
   « Claude » installée, ou `/web-setup` depuis un terminal).

Au début de chaque session, `.claude/settings.json` lance `outils/cloud/demarrage_session.sh` :
dans le cloud il complète les installations si `requirements.txt` a changé et rappelle à
Claude ce qu'il peut faire ; **sur le PC de Julien il ne fait rien**.

## Ce que Claude peut faire dans le cloud

- Lire et modifier le code, écrire des tests, lancer `python tests/lancer_tous.py`
  (vérifié le 23/10 sur Ubuntu 24.04 : 686 contrôles verts avec Stockfish et les problèmes),
  le banc d'essai `python outils/banc_essai.py --rapide`, ruff et vulture.
- Pousser une branche et ouvrir une demande de fusion (PR) sur GitHub.

## Ce qui reste sur le PC de Julien (Claude Code « Local », Windows)

- Lancer le vrai jeu à l'écran, Steam et le jeu en ligne (`outils/verifier_en_ligne.py`).
- `stockfish.exe`, la mesure Stockfish, la surveillance en direct, le banc d'essai complet.
- Le `.exe`, l'installeur et la version amis (`outils/publier_maj.py`).
- Les tables de finales `syzygy/` (trop grosses) : l'analyse marche sans.

## Bon à savoir

- Le cloud part de ce qui est **sur GitHub** : pousser d'abord les commits du PC.
- Le travail du cloud arrive sur une **branche** ; on la récupère sur le PC par une PR fusionnée
  (puis `git pull`) ou avec `claude --teleport`.
- Les sessions cloud comptent dans la même limite d'usage que le reste de Claude.
