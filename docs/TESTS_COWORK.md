# Tests de la page « À faire » : qui fait quoi (24/10/2026)

Chaque test ouvert de la page « SickChess – À faire »
(https://claude.ai/artifact/PzJkQy7b8DKRs9wgksP9T5, groupe « Tester sur ton PC ») porte
maintenant une étiquette **Qui** (champ `qui` de la base de la page) :

| Qui | Tests | Pourquoi |
|---|---|---|
| **Cowork (robot)** | m04, r01, r02, t01, t12, t50–t52, t54–t57, t61–t65, t68, t71, t95 | Un programme peut piloter le vrai jeu (fenêtre invisible, vrai Stockfish) et juger le résultat. |
| **Cowork, puis ton avis (Toi)** | t60, t99, t100 | Cowork vérifie (rien ne chevauche, captures) ; Julien juge si c'est joli / utile. |
| **Claude Code (PC)** | t67, t70, t88, t92–t94, t97, t98, u02–u04 | Windows, Steam ouvert, stockfish.exe, l'installeur, des mesures sur le vrai PC. |
| **Claude Code (PC), puis Toi** | t96, t101 | Claude Code prépare / mesure ; Julien regarde la carte ou le ressenti. |
| **Toi** | q01, t53, t58, t66 | Des oreilles (sons, musique), un ressenti, ton compte chess.com. |
| **Toi (coup d'œil)** | t82–t87 | Déjà vérifiés par le robot dans le cloud ; reste ce que voient tes yeux sous Windows. |
| **Toi + un ami** | t13, t59, t89–t91 | Il faut un vrai ami Steam. |

Le filtre **« Seulement pour moi »** de la page ne montre que les tests de Julien.

## Consignes pour Cowork
1. Avant : le dossier doit contenir le travail du 24/10 (branche `main-phsero` fusionnée dans `main`
   par Claude Code sur le PC). Vérifier que `tests/test_sortie_rapide.py` existe.
2. Outils sous Linux : `bash outils/cloud/configuration.sh` (pygame, python-chess, psutil, Stockfish
   Linux). Puis `SICKCHESS_STOCKFISH=/usr/local/bin/stockfish python tests/lancer_tous.py`.
3. Pour chaque test « Cowork (robot) » : piloter le vrai jeu comme `outils/recette_auto.py` (clics,
   touches, fenêtre invisible, dossier temporaire : **jamais** les données de Julien). Ajouter les
   contrôles réutilisables dans `outils/recette_auto.py` (clé = id du test, ex. `note("t50", …)`).
4. Résultat dans la page (base `taches`, champ `commentaire`) : commencer par
   « Vérifié par Cowork (robot, Linux) : ✓ … ✗ … ». Tout vert et rien à juger à l'œil →
   `statut: "ok"`, `fait: true`. Un défaut → ne pas cocher, le décrire, l'écrire dans `docs/A_FAIRE.md`
   (un test « Ne fonctionne pas » devient d'abord un contrôle automatique dans `tests/`).
5. Ne pas toucher aux commentaires déjà écrits par Julien : ajouter à la suite.
6. Fin : `docs/JOURNAL.md` (une section datée), `docs/A_FAIRE.md` à jour.
