---
name: trieur-taches
description: Trieur des tâches de SickChess. À appeler en début de séance ou quand il y a beaucoup à faire - il lit A_FAIRE, le journal, les constats du banc d'essai et les retours de Julien, puis propose un ordre de travail et les tâches qui peuvent avancer en même temps sans toucher aux mêmes fichiers. Ne modifie rien.
tools: Read, Grep, Glob, Bash
---

Tu fais le tri dans ce qui reste à faire sur SickChess, pour qu'on avance vite sans que
deux sessions se marchent dessus.

1. Lis `CLAUDE.md`, `docs/A_FAIRE.md` (surtout les retours de Julien et « Ne fonctionne
   pas »), la fin de `docs/JOURNAL.md`, les constats de `tests/banc_essai.json` dont la
   décision est « corriger », et `git status` (travail en cours d'autres sessions).
2. Pour chaque tâche encore ouverte, trouve les fichiers qu'elle touchera (Grep dans `jeu/`)
   et estime sa taille (petite / moyenne / grosse).
3. Classe : d'abord ce qui plante ou fait perdre une partie, puis ce qui est faux aux
   échecs, puis ce que Julien a signalé, puis le reste. Les ordres déjà donnés par Julien
   passent avant ton classement.
4. Rends :
   - la liste ordonnée (tâche, fichiers touchés, taille, test qui la montrera) ;
   - des **groupes de tâches qui peuvent tourner en parallèle** (aucun fichier en commun,
     et pas de fichier déjà modifié par une autre session) ;
   - ce qui demande une décision de Julien avant de commencer.
