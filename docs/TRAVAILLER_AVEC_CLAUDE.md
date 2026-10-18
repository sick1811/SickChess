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

## Ce qui est automatique
- À chaque fichier Python modifié, Claude Code vérifie qu'il n'y a pas de faute de syntaxe
  (`.claude/hooks/verifier_syntaxe.py`).
- `python tests/lancer_tous.py` lance toutes les séries de tests d'un coup.
