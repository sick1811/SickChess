---
name: version-amis
description: Fabriquer, vérifier et publier la version amis de SickChess (installeur SickChess_Installation.exe, zip, mise à jour automatique) et vérifier le jeu en ligne. À utiliser quand Julien demande une version pour ses amis, un installeur, de publier, ou de vérifier le multijoueur ; et en fin de séance quand le jeu a changé.
---

# Version amis : fabriquer, vérifier, publier

Sur le PC de Julien (Windows) uniquement. Mode d'emploi pour Julien : `docs/VERSION_AMIS.md`.

## Une fois
- Inno Setup (fabrique l'installeur) : `winget install JRSoftware.InnoSetup`
- GitHub CLI (publie) : `winget install GitHub.cli` puis `gh auth login` (Julien se connecte).
- Dépôt `sick1811/SickChess-amis` (public) : le script le crée s'il manque.

## Règle de Julien (23/10) : « il se met à jour à chaque nouvelle modification »
**En fin de chaque séance où le jeu a changé** (code, sons, images) et où tout est vert
(`python tests/lancer_tous.py`, banc `--rapide` sans rouge), publier une version amis :
`py outils/publier_maj.py --notes "<ce qui change pour le joueur, séparé par ;>"`.
Les amis la reçoivent seuls (mise à jour automatique dans le menu). Ne pas publier une
séance rouge ni une séance qui ne touche qu'aux outils / à la doc.
Le numéro de version amis augmente seul ; changer `VERSION` dans SickChess.py seulement pour
une grosse nouveauté.

## Ce que fabrique publier_maj.py
1. Exe PyInstaller (`outils/sickchess_amis.spec`, refait seulement si nécessaire), avec sa fiche
   d'identité (éditeur, produit, version), sans UPX, en dossier.
2. Paquets qui ont changé (programme, jeu, moteur, puzzles, syzygy) + `maj.json`.
3. `SickChess_amis.zip` et **`SickChess_Installation.exe`** (Inno Setup,
   `outils/installeur_amis.iss` : programme + jeu + Stockfish, installation par utilisateur
   sans administrateur dans `%LOCALAPPDATA%\Programs\SickChess`, icône Bureau).
4. Signature si `"signature"` est réglé dans `outils/maj_config.json` (certificat de Julien).
5. Release GitHub avec tous les fichiers.

## Installeur sous 1 Go (31/10, demande de Julien)
L'installeur contient programme, jeu et Stockfish (~100 Mo) ; il TÉLÉCHARGE problèmes et
finales (~1,2 Go) pendant l'installation (lignes `[Files]` « external download
extractarchive » écrites par `lignes_telechargement`, SHA-256 vérifié). Jamais plus de
1 Go (`LIMITE_INSTALLEUR`, l'envoi est refusé au-delà).
`SICKCHESS_INSTALLEUR_LEGER=1` pour un installeur qui ne télécharge rien.
Si seul l'installeur a changé (pas le jeu) : `py outils/publier_maj.py --installeur-seul`
refait l'installeur de la dernière version et le remplace dans sa release.

## Vérifier avant d'annoncer (à faire à chaque nouvel installeur)
1. Installer en silence dans un dossier d'essai (et `set SICKCHESS_SANS_PARE_FEU=1` avant de lancer le jeu d'essai) :
   `publier\<etiquette>\SickChess_Installation.exe /VERYSILENT /CURRENTUSER /DIR="%TEMP%\SickChessEssai" /TASKS=""`
2. Lancer `"%TEMP%\SickChessEssai\SickChess.exe"` 20 s puis le fermer : `journal_du_jeu.txt` du
   dossier d'essai sans erreur, menu atteint.
3. `python outils/verifier_en_ligne.py --dossier "%TEMP%\SickChessEssai"` (Steam ouvert) :
   tout en ✅ dans `docs/VERIFICATION_EN_LIGNE.md`.
   Vérifier aussi que `puzzles/` et `syzygy/` sont dans le dossier d'essai et que le menu
   propose « Problèmes » (pas « base absente »).
4. Désinstaller l'essai : `"%TEMP%\SickChessEssai\unins000.exe" /VERYSILENT`.

## Mises à jour une par une et pare-feu (25/10, règles de Julien)
- Chaque `maj.json` porte la liste `versions` : un ami à la n° 3 reçoit 4, 5 puis 6 et ne
  redémarre qu'une fois. **Ne jamais supprimer une ancienne release** de `SickChess-amis`.
- Essais automatiques du `.exe` ou de l'installeur : mettre `SICKCHESS_SANS_PARE_FEU=1`
  (sinon le jeu demande l'accord de Windows pour le pare-feu). L'installation en
  `/VERYSILENT` ne demande rien.
- Vérifier une fois à la main (R-118) : installation normale → une demande Windows → règles
  « SickChess » entrée et sortie, profil « Tous » (`netsh advfirewall firewall show rule name=SickChess`).

## Ne jamais
- Chercher à cacher le programme aux antivirus (obfuscation, packers, exe qui se déguise,
  désactiver Defender). On rend le jeu identifiable et on le signe ; un faux positif se
  signale à Microsoft (https://www.microsoft.com/wdsi/filesubmission).
- Mettre `config.json`, `profil.json`, `parties/` de Julien dans un paquet.

## Jeu en ligne : ce qui reste à faire à deux
Une vraie partie entre deux comptes Steam amis, deux PC (liste dans
`docs/VERIFICATION_EN_LIGNE.md`). Avec le numéro de test 480, l'ami ouvre SickChess AVANT
d'accepter l'invitation (sinon Steam lance « Spacewar »).
