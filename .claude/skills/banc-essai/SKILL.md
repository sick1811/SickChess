---
name: banc-essai
description: Lancer le banc d'essai complet de SickChess (bugs, vitesse, processeur, mémoire, Stockfish, ménage, conflits), lire les résultats, les comparer au passage précédent et tenir compte des décisions de Julien. À utiliser avant et après toute optimisation, avant chaque version, ou quand Julien demande « fais les tests de performance / de ménage / de conflits ».
---

# Banc d'essai SickChess

## Lancer
- **Claude Code (Windows, le PC de Julien) – les vraies mesures** :
  `python outils/banc_essai.py` (tout, 5–15 min avec Stockfish)
  ou `python outils/banc_essai.py --rapide` (2–3 min, sans Stockfish).
- Une partie seulement : `--sections vitesse,processeur` (sections : tests, vitesse,
  processeur, memoire, moteur, menage, conflits). Les autres sections du dernier passage
  sont gardées.
- **Cowork (Linux, sans carte graphique ni stockfish.exe)** : `python3 outils/banc_essai.py --rapide`.
  Chiffres de vitesse **indicatifs** (machine plus lente) : utiles pour comparer avant /
  après, pas comme valeur absolue. La section « moteur » y est grise.
- Outils nécessaires : `pip install -r requirements-dev.txt` (ruff, vulture, psutil…).
- **Dans Cowork, Git en lecture seulement et toujours avec `git --no-optional-locks`**
  (status, log, diff) : Cowork ne peut pas supprimer de fichiers, un `.git/index.lock`
  laissé derrière bloque ensuite les commits de Claude Code. Pas de commit depuis Cowork.
- **Jamais deux bancs (ou deux `lancer_tous.py`) en même temps** : le test multijoueur
  ouvre des ports réseau, deux passages simultanés se bloquent.
- **En direct sur le vrai PC** (Claude Code, Windows) : `python outils/surveiller.py` lance le
  jeu et note chaque seconde processeur du jeu et de Stockfish, mémoire, carte graphique,
  pendant que Julien joue ; résumé dans `docs/SURVEILLANCE.md`, détail dans
  `tests/surveillance.csv`. `--duree 120` pour s'arrêter seul, `--pid N` pour un jeu déjà lancé.

## Lire
- `docs/BANC_ESSAI.md` (lisible) et `tests/banc_essai.json` (complet : mesures + constats).
- `tests/banc_essai_historique.jsonl` : un passage par ligne → comparer avec le précédent
  **sur la même machine** (champ `machine`).
- Repères : une image doit coûter ≤ 5 ms (vert), ≤ 10 ms (orange) ; au repos, le jeu doit
  rester ≤ 10 % d'un cœur ; mémoire au menu < 250 Mo.
- Chaque constat a un `id` stable (même problème = même id d'un passage à l'autre).

## Décisions de Julien (page « SickChess – Banc d'essai »)
Page : voir l'adresse dans `CLAUDE.md`. Collections :
- `passages` (un document par passage, id = date `AAAA-MM-JJ_HHhMM`) : `date`, `machine`,
  `rapide`, `sections` (statut + résumé + mesures clés par section).
- `constats` (id = id du constat) : `section`, `titre`, `detail`, `gravite`, `vu_le`,
  `actif` (encore présent au dernier passage), et les champs de Julien : `decision`
  (`corriger` / `ok` / `ignorer`) et `commentaire`.
- `ressenti` : tests à la main (fluidité, ventilateur, Gestionnaire des tâches) avec
  `statut` (`ok` / `ko`) et `commentaire`.

Règles :
1. **Avant de travailler**, lire les constats `decision = corriger` et les commentaires :
   ce sont des demandes de Julien. `ignorer` = ne plus en parler.
2. **Après un passage dans Cowork** : lire les ids des constats déjà dans la page
   (ArtifactData `list` de `constats`), puis
   `python outils/banc_vers_page.py tests/banc_essai.json <dossier> "<machine>" --connus id1,id2…`
   prépare les écritures (lots de 50) : `set` pour les nouveaux, `update` pour les connus
   (jamais `decision` ni `commentaire` écrasés), `actif: false` pour ceux qui ont disparu.
   Ajouter à chaque `update` le `if_version` lu dans la liste, puis passer chaque lot à
   ArtifactData `batch`.
3. **Claude Code** ne peut pas écrire dans la page : il laisse `tests/banc_essai.json` à
   jour et l'écrit dans le journal ; Cowork le recopie à la séance suivante.

## Après une optimisation
Toujours mesurer **avant** et **après** (même machine, mêmes sections), garder le
changement seulement s'il fait gagner, et noter le gain dans `docs/JOURNAL.md`
(« Partie : 6,8 → 2,1 ms/image »). Les tests doivent rester verts.
