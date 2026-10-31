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
| syzygy | tables de finales (WDL + DTZ depuis le 31/10) | ~940 Mo | une fois (ajout des DTZ, 31/10) |

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

## Pour un nouvel ami : l'installeur (23/10)
Envoie-lui une fois ce lien (il donne toujours la dernière version) :
`https://github.com/sick1811/SickChess-amis/releases/latest/download/SickChess_Installation.exe`
- Double-clic : **aucune demande d'administrateur**, le jeu s'installe dans ses programmes
  (`%LOCALAPPDATA%\Programs\SickChess`, un dossier où la mise à jour peut écrire) avec une
  **icône sur le Bureau** et dans le menu Démarrer. Désinstallation par Windows (Paramètres →
  Applications) ; ses parties et son profil ne sont pas effacés.
- **Installeur sous 1 Go (31/10, demande de Julien)** : il contient programme, jeu et
  Stockfish (~100 Mo). Les problèmes (~220 Mo) et les tables de finales (~940 Mo) sont
  **téléchargés par l'installeur** pendant l'installation, depuis la release GitHub, avec
  leur somme SHA-256 vérifiée (fichier abîmé = installation refusée) : tout marche dès la
  fin de l'installation. Il faut Internet pour installer. `publier_maj.py` refuse
  d'envoyer un installeur de plus de 1 Go. (Sans téléchargement :
  `SICKCHESS_INSTALLEUR_LEGER=1`, problèmes et finales arrivent alors par la mise à jour.)
- Fabriqué par `CONSTRUIRE_VERSION_AMIS.bat` si **Inno Setup** est installé
  (une fois : `winget install JRSoftware.InnoSetup`). Recette : `outils/installeur_amis.iss`.

## Mise à jour automatique (23/10)
Dès qu'une nouvelle version est publiée, le jeu de l'ami, **quand il est dans le menu**,
la télécharge tout seul (« Mise à jour : 42 % »), puis redémarre dessus. Jamais en pleine
partie. S'il reste ouvert au menu, il revérifie toutes les 3 minutes (20 avant le 25/10). Pour couper :
`"maj_auto": false` dans son config.json.
→ Chaque fois que tu publies (`CONSTRUIRE_VERSION_AMIS.bat`), tous tes amis l'ont dans
l'heure, sans rien faire.

## Les mises à jour s'installent une par une (25/10, règle de Julien)
- Un ami resté à la **n° 3** reçoit la **n° 4, puis la n° 5, puis la n° 6** : les paquets de
  chaque version sont téléchargés et posés dans l'ordre, et le jeu **ne redémarre qu'une fois**,
  à la fin. Un ami à la **n° 5** ne reçoit que la **n° 6**.
- Le bouton du menu affiche « Mise à jour n° 4 à 6 : 42 % » ; l'écran « Mise à jour » montre
  les notes de chaque version.
- Comment : chaque `maj.json` contient la liste `versions` (numéro + adresse du `maj.json` de
  chaque version), écrite par `publier_maj.py`. La n° 7 retrouve seule les n° 1 à 6 en ligne.
- **Ne jamais effacer une ancienne version (release) sur GitHub** : un ami en retard en a besoin.
- Les jeux à la n° 6 ou avant ont encore l'ancien programme : leur première mise à jour les
  amène directement à la dernière version (n° 7 ou plus) ; ensuite, c'est une par une.

## Sans rien demander à l'ami (25/10)
- **Le jeu insiste tout seul** : chaque téléchargement est réessayé 3 fois ; au menu, le jeu
  revérifie toutes les **3 minutes**, aussi après un échec.
- **DNS de secours** : si le réseau de l'ami (box, Wi-Fi public, école) ne trouve pas GitHub,
  le jeu demande l'adresse à un DNS public sécurisé (Cloudflare, Google, en HTTPS). Le
  certificat de GitHub reste vérifié : rien n'est contourné. Seulement pour les sites de la
  mise à jour.
- **Pare-feu de Windows, réseau privé ET public** : à l'installation (et au premier lancement
  si ce n'est pas fait), Windows demande **une fois** « Autoriser cette application à apporter
  des modifications ? ». Avec « Oui », SickChess.exe est autorisé en entrée et en sortie sur
  tous les réseaux (mises à jour et parties en ligne par Steam), et les anciennes règles de
  blocage du jeu (créées quand on a cliqué « Annuler » sur le message du pare-feu) sont
  retirées. Personne ne peut changer le pare-feu sans cet accord : c'est la règle de Windows.
  « Non » : le jeu marche quand même et redemandera à la version suivante. Code :
  `jeu/pare_feu.py` et la fin de `outils/installeur_amis.iss`. Pour les essais automatiques :
  `SICKCHESS_SANS_PARE_FEU=1`.
- Un antivirus qui bloque le jeu, lui, ne se règle pas de l'extérieur (et on ne cherche pas à
  le contourner) : signature de l'exe ou signalement de faux positif à Microsoft (voir plus bas).

## Pour un nouvel ami : le zip (ancienne façon, toujours valable)
Lien :
`https://github.com/sick1811/SickChess-amis/releases/latest/download/SickChess_amis.zip`
Il dézippe, lance SickChess.exe, clique **Mise à jour** : le moteur, les problèmes et les
tables de finales se téléchargent (~1,2 Go, une fois). Mode d'emploi : `LISEZ-MOI_AMIS.txt`.

## À savoir
- **Dépôt public** = quelqu'un qui a le lien peut télécharger le jeu. Pour des versions de
  test entre amis, c'est le plus simple. Avant la vente, on pourra passer sur un
  hébergement privé : il suffit de changer l'adresse dans `outils/maj_config.json`.
- **Windows SmartScreen et les antivirus** : on ne « contourne » pas la sécurité de Windows,
  on fait en sorte que le jeu soit reconnu comme un vrai programme :
  - déjà fait : exe en dossier (pas d'exe « tout-en-un » qui se décompresse, souvent pris pour
    un virus), pas de compression UPX, nom / éditeur / version renseignés dans SickChess.exe
    et dans l'installeur, installation sans droits d'administrateur ;
  - ce qui reste sans signature : « Windows a protégé votre ordinateur » → « Informations
    complémentaires » → « Exécuter quand même ». L'avertissement disparaît peu à peu quand
    assez de gens ont installé le même fichier ;
  - pour le supprimer vraiment : **signer** l'exe et l'installeur avec un certificat de
    signature de code (payant, quelques dizaines à quelques centaines d'euros par an), puis
    régler `"signature"` dans `outils/maj_config.json` ; `publier_maj.py` signe alors tout seul ;
  - un antivirus bloque à tort ? Envoyer le fichier à Microsoft comme « faux positif » :
    https://www.microsoft.com/wdsi/filesubmission ;
  - sur **Steam**, rien de tout ça : Steam installe le jeu lui-même.
- Le bouton « Mise à jour » n'apparaît **que** dans la version amis (là où il y a
  `paquets_installes.json`), jamais quand tu lances le jeu depuis les sources.
- La version Steam n'en aura pas besoin : Steam fait les mises à jour lui-même.

## Fichiers
- `jeu/mise_a_jour.py` – vérification, téléchargement vérifié (SHA-256), installation.
- `jeu/ecran_mise_a_jour.py` – l'écran du bouton.
- `outils/publier_maj.py` + `outils/sickchess_amis.spec` – fabrication et publication.
- `tests/test_mise_a_jour.py` – tout le circuit avec un faux serveur (36 contrôles).
- `tests/test_maj_une_par_une.py` – une par une, réessais, DNS de secours, pare-feu (37 contrôles).
- `jeu/pare_feu.py` – l'autorisation dans le pare-feu de Windows.

## Le numéro de version (24/10/2026)
Deux numéros, comme les vraies applications :
- **La version** (`VERSION` dans `SickChess.py`, affichée dans le menu) : `MAJEUR.MINEUR.CORRECTIF`.
  - `0.x.y` tant que le jeu n'est pas sorti sur Steam ; **1.0.0 = la sortie sur Steam**.
  - **MINEUR** +1 (0.2.0 → 0.3.0) quand la version apporte des **nouveautés** (un écran, un mode, une fonction).
  - **CORRECTIF** +1 (0.2.0 → 0.2.1) quand elle ne fait que **corriger** des défauts.
  - C'est Claude qui l'augmente, dans la séance où il change le jeu, et l'écrit dans le journal.
- **Le n° amis** (n° 1, 2, 3…) : il augmente **tout seul** à chaque publication (`publier_maj.py`) ; c'est lui
  que le jeu des amis compare pour proposer « Mise à jour disponible ». Il sert de compteur, pas de nom.

Historique : 0.1.0 = n° 1 à n° 5. **0.2.0** = depuis le 24/10 (analyse libre, invitations, classements Steam,
quitter / lancer vite, plantages corrigés) – à publier en n° 6.
