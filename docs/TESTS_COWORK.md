# Tests de la page « À faire » : qui fait quoi (24/10/2026)

Chaque test ouvert de la page « SickChess – À faire »
(https://claude.ai/artifact/PzJkQy7b8DKRs9wgksP9T5, groupe « Tester sur ton PC ») porte une
étiquette **Qui** (champ `qui` de la base de la page). Le filtre « Seulement pour moi » ne montre
que les tests de Julien.

**Cowork travaille sur le PC Windows de Julien** (il prend la main sur l'écran, la souris et le
clavier : vrai jeu, vrai Steam, Gestionnaire des tâches). Pendant ce temps, Julien n'utilise pas le PC.

| Qui | Tests | Pourquoi |
|---|---|---|
| **Cowork (sur ton PC)** | m04, r01, r02, t01, t12, t50–t52, t54–t57, t61–t65, t68, t71, t82–t88, t92–t96, t98, t101 | Cowork joue au vrai jeu à la place de Julien et juge le résultat (Steam ouvert pour t88, t92–t94). |
| **Cowork, puis ton avis (Toi)** | t60, t99, t100 | Cowork vérifie (rien ne chevauche, captures) ; Julien dit si c'est joli / utile. |
| **Claude Code (PC)** | t67, t70, t97, u02–u04 | Mesures longues dans un terminal, fabrication et publication de la version amis. |
| **Toi** | q01, t53, t58, t66 | Des oreilles (sons, musique), un ressenti, ton compte chess.com. |
| **Toi + un ami** | t13, t59, t89–t91 | Il faut un vrai ami Steam. |

## Consignes pour Cowork (sur le PC de Julien)
1. **Avant** : le dossier `C:\Users\mesck\Desktop\echequier\echequier\SickChess` doit contenir le
   travail du 24/10 (branche `main-phsero` fusionnée dans `main` par Claude Code). Vérifier que
   `tests\test_sortie_rapide.py` et `docs\TESTS_COWORK.md` existent ; sinon, s'arrêter et le dire.
2. Lancer le jeu avec `LANCER.bat` (ou `python SickChess.py`). Steam ouvert pour t88, t92–t94.
3. Faire les tests « Cowork » de la page dans l'ordre, comme un joueur. Ne jamais effacer
   `profil.json`, `parties\`, `puzzles_score.json` (données de Julien) ; une partie de test ajoutée
   dans Mes parties peut rester, la signaler.
4. Résultat dans la page (base `taches`) : ajouter au `commentaire` (après celui de Julien, sans
   l'effacer) « Vérifié par Cowork sur ton PC (date) : ✓ … ✗ … ». Tout bon et rien à juger à
   l'œil → `statut: "ok"`, `fait: true`. « Cowork, puis ton avis » : ne pas cocher, laisser à Julien.
   Un défaut → ne pas cocher, le décrire précisément (étapes, ce qui s'affiche, capture) et
   l'ajouter dans `docs\A_FAIRE.md`.
5. **Fin** : une section datée dans `docs\JOURNAL.md`, la liste de ce qui reste à Julien.
