# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
- **Règles d'échecs intouchables** (FIDE, dans TOUS les modes : ordinateur, à deux, en
  ligne, problèmes quand une partie se joue, Freestyle) : mat, pat, matériel insuffisant,
  position morte, 3 et 5 répétitions, 50 et 75 coups, chute au temps sans matériel de mat
  pour l'adversaire = nulle (6.9), roque (et roque Freestyle), prise en passant, promotion
  (dame, tour, fou, cavalier). **Interdit de les supprimer ou de les affaiblir.** Chacune a
  son contrôle dans `tests/test_regles.py` (et `tests/test_freestyle.py`) ; **un test de
  règle ne se supprime jamais**. Ordre : le mat l'emporte sur toute nulle.
- Freestyle (échecs 960) : `jeu/freestyle.py`. Toute position relue (revue, analyse, PGN,
  sauvegarde) passe par `freestyle.plateau(fen)`, jamais `chess.Board(fen)` tout court
  (sinon le roque Freestyle est perdu) ; Stockfish passe seul en `UCI_Chess960`
  (`engine.envoyer_position`).
- Multijoueur par Steam (relais Valve). `MODE_TEST = True` dans `jeu/salon_en_ligne.py`
  tant qu'on teste ; **le passer à False avant la sortie**.

## Organisation
- `SickChess.py` lanceur · `jeu/` code · `tests/` tests · `outils/` scripts (sons, logo,
  Blender) · `assets/`, `sounds/`, `polices/`, `ouvertures/` ressources · `moteur/stockfish.exe`.
- Hors GitHub (gros ou personnels) : `moteur/*.exe`, `puzzles/` (223 Mo), `syzygy/`,
  `steam_api64.dll`, `profil.json`, `parties/`, `puzzles_score.json`.
- Ne jamais écraser `profil.json`, `parties/`, `puzzles_score.json` : ce sont les données
  de Julien. Les tests travaillent dans des dossiers temporaires.

## Architecture (ce qu'il faut savoir avant de toucher au code)
- **Pas de paquet** : `SickChess.py` ajoute `jeu/` au chemin Python, puis les modules
  s'importent à plat (`import ui`, `from game_manager import GameManager`). Les tests font
  de même (`sys.path.insert(0, "jeu")`, `SDL_VIDEODRIVER=dummy`).
- **`game_manager.GameManager`** tient la fenêtre et la boucle : `run()` (menu) →
  `preparer_partie()` (crée `board.ChessBoard` + un mode : `mode_stockfish`, `mode_hotseat`,
  `mode_en_ligne`) → `boucle_de_partie()`. Chaque écran (`ecran_*.py`, `menu_*.py`) est une
  classe `handle_event` / `update` / `draw`, ouverte par une méthode `ouvrir_…()` qui fait
  tourner sa propre petite boucle puis rend la main.
- **Plateau** : `board.py` (état, coups, fin de partie `_verifier_fin`, pré-mouvement)
  délègue à `board_render`, `board_input`, `board_animation`, `board_highlights`, `timer`…
  Règles : python-chess (`rules.py`, `regles_nulle.py`).
- **Stockfish** : ne jamais lancer un moteur à la main, passer par `moteurs.py` (un moteur
  par rôle : « jeu », « analyse », renforts ; priorité basse pour l'analyse). `engine.py`
  garde un verrou pendant toute une recherche : arrêter / quitter ne doit pas le prendre
  (`interrompre()`). Analyse d'une partie : `analyse_partie.py`, pastilles `annotations.py`.
- **Textes affichés** : écrits en français dans le code ; `ui.texte` les passe par
  `langue.traduire`, qui cherche la phrase dans `langue_en.EN` (les `%s` / `%d` sont des
  modèles). Un texte modifié = sa clé dans `langue_en.py` modifiée aussi.
  Dessin : `ui.py` (cache des textes, `ui.Cadence` 30/60 images/s), mise en page `layout.py`.
- **Données du joueur** : toujours via `asset_manager.dossier_ecriture()` ; les tests le
  remplacent par un dossier temporaire (`asset_manager.dossier_ecriture = lambda: TEMP`).
- **Tests** : scripts simples (pas de pytest) avec `verifier(condition, message)`, sortie
  1 si un échec. Nouvelle série = l'ajouter à `SERIES` dans `tests/lancer_tous.py`
  (`True` = utilise Stockfish, sautée par `--rapide`). Vérif. de style : `ruff check jeu tests`.

## Commandes
- Lancer le jeu : `python SickChess.py` (ou double-clic `LANCER.bat`).
- **Tous les tests : `python tests/lancer_tous.py`** (`--rapide` = sans Stockfish).
  Une série seule : `python tests/test_revue.py`. Tout doit être vert avant un commit.
- Captures des écrans (pour juger le graphisme) : `python tests/captures_ecrans.py`
  → `tests/ecrans/`.
- Version amis : `CONSTRUIRE_VERSION_AMIS.bat` → `outils/publier_maj.py` : exe, paquets,
  zip et **installeur `SickChess_Installation.exe`** (Inno Setup), publiés sur GitHub ; le jeu
  des amis se met à jour **tout seul** dans le menu. Voir `docs/VERSION_AMIS.md` et la skill
  `version-amis`. **Demande de Julien : publier une version amis à la fin de chaque séance
  où le jeu a changé et où tout est vert.**
  **Numéro de version** (`VERSION` dans `SickChess.py`) : nouveautés → 0.x+1.0, corrections seules →
  0.x.y+1, 1.0.0 = sortie Steam (règle dans `docs/VERSION_AMIS.md`).
- Jeu en ligne : `python outils/verifier_en_ligne.py` (Steam ouvert) → `docs/VERIFICATION_EN_LIGNE.md`.
- **Banc d'essai : `python outils/banc_essai.py`** (bugs, vitesse, processeur, mémoire,
  Stockfish, ménage, conflits ; `--rapide`, `--sections vitesse,menage`) → `docs/BANC_ESSAI.md`
  et `tests/banc_essai.json`. Page à cocher : « SickChess – Banc d'essai »
  https://claude.ai/artifact/ARYw19umG9WeUbQDVJrXe9 (collections `passages`, `constats`,
  `ressenti`). **Avant de travailler, lire les constats marqués « corriger » et leurs
  commentaires.** Outils : `pip install -r requirements-dev.txt` (ruff, vulture, psutil,
  pyinstaller, py-spy) ; réglages dans `pyproject.toml`.
- **Performances en direct (Windows seulement)** : `python outils/surveiller.py` lance le jeu
  et mesure chaque seconde processeur (jeu + Stockfish), mémoire, carte graphique pendant que
  Julien joue → `docs/SURVEILLANCE.md`. Cowork ne voit pas le vrai Windows : c'est Claude Code
  qui le lance.
- Sons : `python outils/generer_sons.py`. Logo/icône : `python outils/generer_logo.py`.

## Façon de travailler
- Petites étapes. Après chaque étape : tests verts, une ligne dans `docs/JOURNAL.md`
  (section datée « Fait / À vérifier par Julien »), commit Git clair en français.
- **À chaque séance de code, donner à Julien une liste de tests à faire** sur son PC
  (« Fonctionne / Ne fonctionne pas + commentaire »). Les écrire dans `docs/A_FAIRE.md`,
  section « À tester par Julien ». (Dans Cowork, Claude les recopie aussi dans la page
  « SickChess – À faire » : https://claude.ai/artifact/PzJkQy7b8DKRs9wgksP9T5.)
- Pour un bug : le reproduire dans un test avant de le corriger.
- **Avant chaque version** : `python outils/verifier_version.py --amis` (ou `--steam`) : tests, banc, MODE_TEST,
  numéro Steam, licences, version, Git, `.exe` (`--exe`). Lancé tout seul par CONSTRUIRE_VERSION_AMIS.bat.
- **Test d'endurance (2 h, PC Windows)** : `python outils/endurance.py` (un robot joue au vrai jeu, fenêtre
  invisible ; `--minutes 15` pour un essai) → fuite de mémoire, Stockfish qui s'accumulent, ralentissement,
  plantages ; `tests/endurance/rapport.json` et `docs/ENDURANCE.md`. Section « endurance » du banc (hors --rapide).
- **Précision des pastilles** : `python outils/precision.py` (banque `tests/positions_revue.json`, section
  « precision » du banc). Un « coup N faux » signalé par Julien s'ajoute dans `A_LA_MAIN`.
- **Recette automatique** : `python outils/recette_auto.py` pilote le vrai jeu (souris, clavier, vrai
  Stockfish, fenêtre invisible) et vérifie les lignes de recette qu'un programme peut juger →
  `tests/recette_auto/resultats.json`. À lancer sur le PC avant de demander une passe à Julien.
- **Recette complète (`docs/RECETTE.md`)** : la liste de TOUS les tests à la main du jeu
  (R-001…). Elle est fabriquée par `python outils/recette.py` : on modifie la liste
  `RECETTE` dans `outils/recette.py`, jamais RECETTE.md à la main. **Chaque fonction
  ajoutée, modifiée ou retirée = ses lignes de recette mises à jour dans la même séance**
  (nouvel id libre dans la section, on ne réutilise pas un ancien id). Avant chaque
  version amis / Steam : `python tests/lancer_tous.py` tout vert, puis Julien repasse la
  recette (page « À faire », groupe « Recette complète », bouton « Nouvelle passe »).
  Un test « Ne fonctionne pas » devient un contrôle automatique dans `tests/` avant d'être corrigé.
- **GitHub toujours à jour (demande de Julien, 24/10)** : chaque commit est envoyé sur GitHub
  tout seul par le crochet `post-commit` (`outils/git/post-commit`, installé avec
  `python outils/git/installer_envoi_auto.py` ; journal `.git/envoi_github.log`). Donc : ne
  commiter que du travail accepté (tests verts). Sans le crochet (nouveau PC, nouveau clone),
  faire `git push` après chaque commit. Jamais `git push --force`.

## Deux Claude, un seul dossier
- **Cowork** (application Claude, onglet discussion) : idées, graphisme, Blender, page Steam,
  textes, page « À faire ». Il voit ce dossier, mais sous Linux : il ne lance pas le vrai jeu.
- **Claude Code** (onglet Code, sur ce PC Windows) : lancer le jeu, Stockfish.exe, Steam,
  compiler le .exe, commits Git.
- **Claude Code dans le cloud** (claude.ai/code, Linux, depuis GitHub) : code et tests, sans
  écran ni Steam ni .exe. Réglage : `docs/CLAUDE_CLOUD.md` (`outils/cloud/configuration.sh`).
- Le lien entre les deux = **ce fichier + `docs/A_FAIRE.md` + `docs/JOURNAL.md`** :
  toujours les tenir à jour en fin de séance.

## Documentation des bibliothèques (Context7)
- Serveur MCP **Context7** déclaré dans `.mcp.json` (https://github.com/upstash/context7) : il donne
  la documentation à jour de Pygame, python-chess, PyInstaller, Steamworks, Inno Setup, etc.
- Avant d'utiliser une fonction de bibliothèque dont on n'est pas sûr (nom, paramètres, version),
  la chercher avec Context7 (`resolve-library-id` puis `query-docs` / `get-library-docs`) au lieu
  de deviner. Pas de clé nécessaire (limite gratuite suffisante).

## Performance (le jeu doit rester léger)
- Rien ne se lit sur le disque dans un `draw()` ; textes et fonds fixes gardés en cache ;
  ne pas tout redessiner 60 fois par seconde quand rien ne bouge (skill `performance-pygame`).
- Toute optimisation : banc avant / après sur la même machine, gain noté dans le journal.

## Skills du projet (`.claude/skills/`)
`seance-sickchess` (déroulé d'une séance) · `chef-orchestre` (répartir beaucoup de tâches
entre agents et sessions) · `compiler-exe` (PyInstaller) ·
`verifier-echecs` (règles et analyse justes) · `captures-steam` (images de la page Steam) ·
`banc-essai` (mesures et décisions de Julien) · `performance-pygame` (processeur, carte
graphique, Stockfish) · `menage-code` (code et fichiers inutiles, sans rien casser) · `version-amis` (installeur,
publication, mise à jour automatique, vérification en ligne).
Agents (`.claude/agents/`) : `testeur` (cherche les bugs), `relecteur-interface` (graphisme),
`optimiseur` (cherche les lenteurs et chiffre les gains), `arbitre-echecs` (règles et pastilles
justes, erreurs avec FEN), `relecteur-textes` (accents, anglais, textes coupés, aide F1),
`recetteur` (recette auto + liste « À tester par Julien »), `gardien-depot` (avant un commit :
rien de personnel, tests verts, journal à jour), `trieur-taches` (ordre de travail et tâches
parallèles sans fichier commun) : ils lisent et rendent un rapport. Ceux qui modifient
(seulement les fichiers qu'on leur confie, jamais de commit) : `correcteur` (un défaut :
test rouge → correction → vert), `enqueteur-bug` (bugs « une fois sur 10 » : cause + test),
`batisseur` (nouvelle fonction), `traducteur` (textes et anglais), `documentaliste`
(journal, A_FAIRE, recette). **Beaucoup de tâches à la fois : skill `chef-orchestre`**
(qui fait quoi, un fichier = un seul agent, contrôle avant commit).
