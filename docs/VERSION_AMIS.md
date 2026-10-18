# Version amis + bouton « Mise à jour »

## Le principe
Tu publies chaque nouvelle version **à un seul endroit** : les « releases » d'un dépôt
GitHub (`sick1811/SickChess-amis`, gratuit). Le jeu de tes amis y lit un petit fichier
(`maj.json`) et ne télécharge **que ce qui a changé** :

| Paquet | Contenu | Taille | Change… |
|---|---|---|---|
| programme | SickChess.exe + Python + pygame | ~30 Mo | rarement (nouvelle bibliothèque) |
| jeu | code, images, sons, polices, ouvertures | ~10 Mo | à chaque correction |
| moteur | Stockfish | ~110 Mo | rarement |
| puzzles | base de problèmes | ~220 Mo | rarement |
| syzygy | tables de finales | ~380 Mo | jamais |

Une correction de bug = quelques Mo à télécharger pour tes amis.
Le code (`jeu/*.py`) reste en fichiers à côté de l'exe : pas besoin de refaire l'exe
pour une correction. Tes amis gardent leurs parties, profil et réglages.

## Une seule fois
1. Sur github.com, crée le dépôt **SickChess-amis** (Public, vide). Il ne contiendra que
   les versions du jeu, pas ton code. (Le script peut aussi le créer tout seul, voir 2.)
2. Conseillé : installe GitHub CLI pour que l'envoi soit automatique.
   Dans un terminal : `winget install GitHub.cli` puis `gh auth login`.
   Sans lui, le script t'ouvre le dossier et tu glisses les fichiers sur la page GitHub.

## À chaque nouvelle version
1. Double-clic sur **CONSTRUIRE_VERSION_AMIS.bat**.
2. Écris ce qui change (séparé par des `;`) → Entrée.
3. Le script fabrique, compare avec la version d'avant, et envoie seulement le nécessaire.
   La première fois, PyInstaller fabrique l'exe (2 à 5 min). Ensuite, l'exe n'est refait
   que si `SickChess.py`, la recette ou les bibliothèques changent.

## Pour un nouvel ami
Envoie-lui une fois ce lien (il donne toujours la dernière version) :
`https://github.com/sick1811/SickChess-amis/releases/latest/download/SickChess_amis.zip`
Il dézippe, lance SickChess.exe, clique **Mise à jour** : le moteur, les problèmes et les
tables de finales se téléchargent (~700 Mo, une fois). Mode d'emploi : `LISEZ-MOI_AMIS.txt`.

## À savoir
- **Dépôt public** = quelqu'un qui a le lien peut télécharger le jeu. Pour des versions de
  test entre amis, c'est le plus simple. Avant la vente, on pourra passer sur un
  hébergement privé : il suffit de changer l'adresse dans `outils/maj_config.json`.
- **Windows SmartScreen** affichera « Windows a protégé votre ordinateur » (jeu non signé) :
  « Informations complémentaires » → « Exécuter quand même ».
- Le bouton « Mise à jour » n'apparaît **que** dans la version amis (là où il y a
  `paquets_installes.json`), jamais quand tu lances le jeu depuis les sources.
- La version Steam n'en aura pas besoin : Steam fait les mises à jour lui-même.

## Fichiers
- `jeu/mise_a_jour.py` – vérification, téléchargement vérifié (SHA-256), installation.
- `jeu/ecran_mise_a_jour.py` – l'écran du bouton.
- `outils/publier_maj.py` + `outils/sickchess_amis.spec` – fabrication et publication.
- `tests/test_mise_a_jour.py` – tout le circuit avec un faux serveur (36 contrôles).
