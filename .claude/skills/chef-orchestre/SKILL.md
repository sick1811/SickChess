---
name: chef-orchestre
description: Répartir beaucoup de tâches SickChess entre les agents du projet et les sessions sans qu'ils se marchent dessus - tri, attribution des fichiers, correction en parallèle, vérification, contrôle avant commit, liste de tests pour Julien. À utiliser quand Julien donne une longue liste (défauts Cowork, retours de recette, « fais tout ce qui reste »), ou demande d'aller plus vite en parallèle.
---

# Chef d'orchestre SickChess

Le chef d'orchestre (la session principale) **ne code presque pas** : il trie, distribue,
vérifie, commite. Les agents (`.claude/agents/`) font le travail et rendent un rapport.

## Les agents
| Rôle | Agent | Modifie ? |
|---|---|---|
| Trier, faire les groupes | `trieur-taches` | non |
| Corriger un défaut (test rouge → correction → vert) | `correcteur` | ses fichiers |
| Bug « une fois sur 10 » : trouver la cause, écrire le test | `enqueteur-bug` | un test |
| Nouvelle fonction | `batisseur` | ses fichiers |
| Accents, anglais, textes coupés | `traducteur` | textes seulement |
| Chercher les bugs d'un travail fini | `testeur` | non |
| Règles d'échecs et pastilles justes | `arbitre-echecs` | non |
| Graphisme | `relecteur-interface` | non |
| Textes à relire | `relecteur-textes` | non |
| Lenteurs | `optimiseur` | non |
| Contrôle avant commit | `gardien-depot` | non |
| Recette auto + tests pour Julien | `recetteur` | non |
| Journal, A_FAIRE, recette.py | `documentaliste` | docs |

## Déroulé
1. **Tri** : `trieur-taches` avec la liste de Julien et l'ordre qu'il a imposé (son ordre
   passe toujours avant). Vérifier ses affirmations importantes (`git status`, `git log`)
   avant de s'y fier : l'état du dossier change pendant qu'on travaille.
2. **Décisions** : poser à Julien, en une fois (AskUserQuestion), les questions que le tri a
   relevées. Ne pas lancer une tâche qui attend sa réponse.
3. **Distribuer** : un agent par groupe, en arrière-plan, **plusieurs dans le même message**.
   Chaque consigne contient : le défaut (mots de Julien), la **liste exacte des fichiers
   autorisés**, le test attendu, « pas de commit ». Bug flou → `enqueteur-bug` d'abord, puis
   `correcteur` avec son test.
4. **Vérifier** chaque rapport (ce n'est pas une preuve) : relire le diff, relancer la série
   du test. Puis `testeur` sur l'ensemble ; `arbitre-echecs` si règles ou analyse ont bougé ;
   `relecteur-interface` / `relecteur-textes` si un écran ou un texte a changé.
5. **Commit** : `gardien-depot` → PRÊT, puis un commit par groupe (seulement ses fichiers),
   `git push` (jamais `--force`).
6. **Fin** : `recetteur`, puis `documentaliste` (une seule fois, à la fin), commit des docs,
   version amis si tout est vert (skill `version-amis`, avec l'accord de Julien).

## Règles qui évitent la casse
- **Un fichier = un seul agent à la fois.** Fichiers modifiés dans `git status` qui ne sont
  pas à nous = pris par une autre session : on n'y touche pas et on ne les commite pas.
- `docs/A_FAIRE.md`, `docs/JOURNAL.md`, `outils/recette.py`, `jeu/langue_en.py` sont
  partagés par tout le monde : un seul agent les modifie, en fin de vague (`documentaliste`,
  `traducteur`) ; les autres donnent leurs lignes dans leur rapport.
- Pas plus de **2 agents qui font tourner Stockfish** en même temps (tests lourds, banc,
  recette auto) : les mesures seraient faussées et les tests de durée deviennent rouges.
  Endurance et banc : seuls, quand rien d'autre ne tourne.
- Une copie à part (`isolation: "worktree"`) ne contient ni `puzzles/`, ni `syzygy/`, ni
  `moteur/stockfish.exe` : bien pour du code sans Stockfish ; sinon travailler dans le
  dossier principal avec des fichiers bien séparés.
- Tâche qui mérite d'être suivie à part par Julien (grosse fonction, nuit de calcul) :
  une **session** plutôt qu'un agent.
- Jamais `profil.json`, `parties/`, `puzzles_score.json`, `config.json`, `rapports/`.
- Tenir Julien au courant avec la liste de tâches de l'application (une ligne par groupe).
