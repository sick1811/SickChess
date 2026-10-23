# Multijoueur Steam – mode d'emploi

## Ce que ça fait
- **Créer une partie** : Steam ouvre un salon (réservé aux amis). Tu choisis la
  cadence et ta couleur, puis tu invites un ami :
  - depuis la **liste de tes amis Steam** affichée dans le jeu (bouton *Inviter*) ;
  - avec la **fenêtre d'invitation Steam** (overlay, Maj+Tab) ;
  - ou en lui donnant le **code** de la partie (bouton *Copier*).
- **Ton ami accepte l'invitation** dans Steam **avec SickChess déjà ouvert** : le jeu passe
  tout seul au salon. Il peut aussi taper le code.
  ⚠️ Tant que le jeu utilise le numéro de test 480, accepter une invitation quand SickChess
  est **fermé** fait lancer « Spacewar » par Steam (le jeu de test de Valve), pas SickChess.
  Avec le vrai numéro Steam du jeu, l'invitation ouvrira SickChess directement.
- Quand il est là, tu cliques **Lancer la partie**.
- Pendant la partie : chat (onglet CHAT), pendules synchronisées, abandon.
- À la fin : **Revanche** (couleurs inversées) ou **Menu**.
- Les messages passent par le relais de Valve : rien à ouvrir sur la box,
  aucun serveur à payer, les adresses IP ne sont jamais montrées.

## Ce qu'il faut à côté de SickChess.py
| Fichier | D'où il vient | Sur GitHub ? |
|---|---|---|
| `steam_api64.dll` | Steamworks SDK, dossier `redistributable_bin/win64` | non (`.gitignore`) |
| `steam_appid.txt` | contient `480` (numéro de test de Valve, « Spacewar ») | oui |

Et le **client Steam ouvert et connecté**.

> Quand SickChess aura son propre numéro Steam (après les 100 $ de Steam Direct),
> remplacer `480` par ce numéro dans `steam_appid.txt`. Ce fichier ne doit **pas**
> être envoyé sur Steam avec le jeu final.

## Tester
1. **Sans Steam, sur un seul PC** : lance le jeu deux fois (deux `LANCER.bat`).
   Fenêtre 1 : *Jouer en ligne* → *Test : héberger*. Fenêtre 2 : *Test : rejoindre*.
2. **Avec Steam** : il faut **deux PC et deux comptes Steam amis** (un même PC ne
   peut pas faire tourner deux comptes Steam). Avec le numéro 480, Steam affiche
   que vous jouez à « Spacewar » : c'est normal.
3. Tests automatiques : `python tests/test_multijoueur.py`.
4. **Vérification complète sur ce PC** (Claude Code, Steam ouvert) :
   `python outils/verifier_en_ligne.py` (ou `--dossier "<dossier installé>"` pour la version
   amis) → fichiers, connexion Steam, salon et code, tests réseau ; résultat dans
   `docs/VERIFICATION_EN_LIGNE.md`.

## Avant la sortie
- `MODE_TEST = False` dans `jeu/salon_en_ligne.py` (cache les boutons de test).
- Mettre le vrai numéro du jeu, retirer `steam_appid.txt` du paquet.
- Prendre `steam_api64.dll` dans **son propre** Steamworks SDK.

## Fichiers
- `jeu/steam.py` – le lien avec `steam_api64.dll` (ctypes) : salons, amis, messages.
- `jeu/reseau_transport.py` – le « tuyau » : Steam, ou TCP local pour les tests.
- `jeu/salon_en_ligne.py` – l'écran *Jouer en ligne* (créer, rejoindre, inviter).
- `jeu/mode_en_ligne.py` – la partie en ligne (coups, pendules, chat, revanche).
- `jeu/partie_en_ligne.py` – le parcours complet + la carte de fin en ligne.
- `jeu/pendule_reseau.py`, `jeu/revanche.py` – repris tels quels de V8_TURBO_3000.
