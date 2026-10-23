# Travailler avec Cowork et Claude Code

## Qui fait quoi
| Cowork (discussion Claude, projet « Échecs – Version Steam ») | Claude Code (onglet Code, sur ton PC) |
|---|---|
| Idées, plan, décisions | Lancer le vrai jeu, Stockfish.exe |
| Graphisme, Blender, logo, sons | Compiler le .exe (PyInstaller) |
| Page Steam, textes, captures (Canva) | Tester Steam (steam_api64.dll, overlay) |
| Page « À faire » à cocher | Commits Git (et push quand tu le demandes) |

Les deux lisent le même dossier SickChess. Ils se passent le relais par trois fichiers :
`CLAUDE.md` (les règles), `docs/A_FAIRE.md` (la liste), `docs/JOURNAL.md` (l'historique).

## Installer Claude Code (une fois)
- Le plus simple : l'application Claude sur ton PC → onglet **Code** → choisir le dossier
  `C:\Users\mesck\Desktop\echequier\echequier\SickChess`.
- Ou dans PowerShell : `irm https://claude.ai/install.ps1 | iex`, puis dans le dossier du jeu :
  `claude`. Installer aussi Git for Windows (recommandé).
- Python doit être dans le PATH (commande `python`) : c'est déjà le cas si `LANCER.bat` marche.

## Phrases à dire à Claude Code
- « Fais la prochaine tâche de A_FAIRE » → il suit la skill `seance-sickchess`.
- « Compile le jeu » → skill `compiler-exe`.
- « Vérifie que les pastilles sont justes » → skill `verifier-echecs`.
- « Fais les captures pour Steam » → skill `captures-steam`.
- « Demande au testeur de chercher des bugs dans la revue » → agent `testeur`.
- « Lance le banc d'essai complet » → skill `banc-essai` (vitesse, processeur, mémoire,
  Stockfish, ménage, conflits, bugs).
- « Corrige les points marqués Corriger dans le banc d'essai » → il lit tes décisions.
- « Rends l'écran X plus léger » / « le jeu chauffe » → skill `performance-pygame`
  (+ agent `optimiseur` pour chiffrer les gains).
- « Fais le ménage dans le code » → skill `menage-code` (un lot à la fois, tests à l'appui).

## Ce qui est automatique
- À chaque fichier Python modifié, Claude Code vérifie qu'il n'y a pas de faute de syntaxe
  (`.claude/hooks/verifier_syntaxe.py`).
- `python tests/lancer_tous.py` lance toutes les séries de tests d'un coup.

## La boîte à outils complète (23/10/2026)

### Déjà en place
- **GitHub** relié (dépôt sick1811/SickChess).
- **Pages à cocher** : « SickChess – À faire » (tâches, recette, propositions) et
  « SickChess – Banc d'essai » (résultats automatiques + tes décisions Corriger / OK / Ignorer
  + ton ressenti).
- **Skills** dans `.claude/skills/` (lues par Claude Code) : séance, compiler, vérifier les
  échecs, captures Steam, banc d'essai, performance, ménage. Côté Cowork : `sickchess-cowork`.
- **Agents** : testeur, relecteur-interface, optimiseur.
- **Garde-fous** : vérification de syntaxe automatique, `git push --force` et
  `git reset --hard` interdits.

### À installer une fois (dans Claude Code, dis : « installe les outils de développement »)
`pip install -r requirements-dev.txt` installe :
| Outil | À quoi il sert | Quand |
|---|---|---|
| ruff | erreurs, imports et variables inutiles, pièges classiques | à chaque séance (rapide) |
| vulture | fonctions et classes jamais utilisées | ménage |
| psutil | mesure mémoire et processeur | banc d'essai |
| PyInstaller | fabrique le .exe | version amis / Steam |
| py-spy | montre en direct où le vrai jeu passe son temps | « ça rame » |

### Facultatif
- **GitHub CLI** (`winget install GitHub.cli`, puis `gh auth login`) : nécessaire pour publier
  la version amis automatiquement ; Claude Code peut aussi ouvrir des « pull requests ».
- **Connecteur Discord** (réglages de Claude → Connecteurs) : seulement si des amis testent et
  écrivent leurs retours sur un serveur Discord.
- **Canva** (déjà connecté) : capsules et images de la page Steam.
- **Blender** (déjà sur ton PC) : rendus 3D du menu et des pièces (scripts dans `outils/blender/`).
- Pas besoin d'autre connecteur pour la vitesse ou la stabilité : ce sont les outils ci-dessus
  et le banc d'essai qui font ce travail, sur ton PC.

### Continuer quand ton forfait est épuisé (crédits)
- Les **crédits d'utilisation** (« usage credits ») prennent le relais quand tu atteins une
  limite de ton abonnement, **dans les discussions comme dans Claude Code**.
- À activer sur claude.ai (sur le web, pas dans l'application mobile) : **Réglages → Utilisation
  (Usage)** → section « Usage credits » → **Enable**. Tu choisis un plafond de dépense mensuel ;
  le solde et les dates d'expiration s'affichent sur cette même page.
- Ton crédit offert de 100 $ expire le **5 novembre** : vérifie sur cette page qu'il apparaît
  bien dans le solde, et garde un plafond pour ne rien payer au-delà.
- Pour l'économiser : utiliser Claude Code pour les grosses séances de code (il travaille
  directement sur ton PC), demander le banc `--rapide` en cours de séance et le complet avant
  une version.
