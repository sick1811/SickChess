---
name: compiler-exe
description: Fabriquer l'exécutable Windows de SickChess avec PyInstaller et le paquet à envoyer sur itch.io / Steam. À utiliser quand Julien demande de compiler, de faire le .exe ou de préparer une version à distribuer. Uniquement sous Windows (Claude Code).
---

# Compiler SickChess en .exe

Référence : `../V8_TURBO_3000/COMPILER.bat` et `Echec.spec` (à adapter, ne pas copier
tels quels : plus de bore.exe / ngrok, nouvelle structure `jeu/`).

## Fichiers à créer / tenir à jour
- `SickChess.spec` : mode **dossier** (onedir, démarrage rapide), `console=False` pour
  la version à donner (variable d'environnement pour garder la console en diagnostic),
  icône `assets/icone.ico`, `version_info.txt` (éditeur, produit, version : limite
  les alertes de Windows Defender), `pathex=["jeu"]`.
- `COMPILER.bat` : trouve Python (`py` puis `python`), installe pygame / chess /
  pyinstaller si besoin, vérifie que les ressources existent, lance PyInstaller,
  puis fait le zip.

## Ce qui doit être embarqué (datas)
`assets/`, `sounds/`, `polices/`, `ouvertures/`, `config.json` (réglages par défaut,
pas celui de Julien), `moteur/stockfish.exe` + `moteur/COPYING-Stockfish.txt`,
`docs/CREDITS.md`, `steam_appid.txt` et `steam_api64.dll` pour la version Steam.
Optionnels selon la version : `puzzles/` (223 Mo) et `syzygy/` (379 Mo).

## Points à vérifier dans le code avant de compiler
- Les chemins doivent partir du dossier de l'exe (`sys._MEIPASS` / `sys.executable`)
  et non du dossier courant.
- Les données du joueur (`profil.json`, `parties/`, `config.json` modifié, sauvegarde)
  doivent aller dans un dossier inscriptible : `%APPDATA%\SickChess` dans la version
  compilée (Steam peut installer dans Program Files, non inscriptible).
- `MODE_TEST = False` dans `jeu/salon_en_ligne.py` pour une version publique.

## Contrôle du résultat
1. Lancer `dist\SickChess\SickChess.exe` : menu, une partie contre l'ordinateur
   (Stockfish répond), son, Options, Problèmes, revue.
2. Copier le dossier ailleurs (ex. Bureau) et relancer : rien ne doit dépendre du
   dossier source.
3. Taille du dossier, et zip `SickChess_<version>_windows.zip` pour itch.io.
4. Noter dans `docs/JOURNAL.md` la version, la taille et ce que Julien doit tester
   (idéalement sur un autre PC sans Python).
