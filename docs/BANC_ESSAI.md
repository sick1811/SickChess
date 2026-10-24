# Banc d'essai – SickChess

Dernier passage : 2026-10-24 00:02 · Windows 11 · 12 cœurs · Python 3.13.7 · pygame 2.6.1 · rapide

Fabriqué par `python outils/banc_essai.py` (ne pas modifier à la main).

## 🟢 Bugs (tests automatiques)

584 contrôles OK sur 25 séries (sans Stockfish), en 61 s


## 🟢 Vitesse d'affichage

Démarrage 1.19 s · écran le plus lent : Mes parties (4.6 ms/image)


## 🟠 Charge du processeur au repos

Menu : 9 % d'un cœur (60 img/s) · Partie : 16 % d'un cœur (55 img/s) · 12 cœurs logiques

- **« Partie » occupe le processeur sans rien faire** (moyen) – 16 % d'un cœur à 55 images/s alors que rien ne bouge. Pistes : ne redessiner que si quelque chose change, descendre à 30 images/s au repos, mettre en cache le fond et les textes (skill performance-pygame).

## 🟢 Mémoire

Jeu au menu : 72.8 Mo


## 🟢 Moteur d'analyse (Stockfish)

6 033 588 nœuds/s avec 10 fils de calcul (sur 12)


## 🟠 Ménage (code et fichiers inutiles)

26617 lignes de jeu · 0 imports/variables inutiles · 94 éléments peut-être morts · 1 fichier(s) jamais importé(s) · 876 Mo de restes

- **Fonctions et méthodes peut-être jamais utilisées** (moyen) – 94 élément(s) dans 37 fichier(s), à vérifier un par un avant de retirer (skill menage-code) : · jeu/design.py : bandeau (l.260), filet (l.273), jauge (l.280), puce (l.297), mesure (l.331), vignette (l.516), cadre_du_plateau (l.544) · jeu/faiblesse.py : SIGMA_ATTENTIF (l.142), lucidite (l.220), oublier_le_reglage (l.253), profondeur_ancienne (l.314), gaffes_par_partie (l.520), separer (l.525), pert
- **Fichier jamais importé : jeu/fond_anime.py** (moyen) – Aucun autre fichier ne l'utilise. Probablement un reste de V8.
- **Fichiers en double** (faible) – 4 fichier(s) identiques (0.6 Mo) : · sounds/fifty_moves.wav = sounds/repetition.wav · sounds/fifty_moves.wav = sounds/stalemate.wav · sounds/feutre/repetition.wav = sounds/feutre/stalemate.wav · assets_src/steam/header_capsule_920x430.png = assets_src/steam/library_header_920x430.png
- **Restes de fabrication et de tests sur le disque** (info) – 876 Mo au total (rien de tout ça n'est sur GitHub) : · build_amis : 52 Mo · publier : 816 Mo · tests/ecrans : 1 Mo · tests/ecrans_en : 2 Mo · tests/ecrans_revue : 0 Mo · __pycache__ (tous) : 3 Mo · tests/capture_*.png : 3 Mo · « publier » et « build_amis » se refont à chaque version amis.

## 🟢 Conflits et santé du projet

0 conflit(s) Git · 0 erreur(s) de syntaxe · dépendances OK · 1 fichier(s) non enregistré(s)

