# Banc d'essai – SickChess

Dernier passage : 2026-10-31 21:46 · Windows 11 · 12 cœurs · Python 3.13.7 · pygame 2.6.1 · complet

Fabriqué par `python outils/banc_essai.py` (ne pas modifier à la main).

## 🟢 Bugs (tests automatiques)

1021 contrôles OK sur 39 séries (sans Stockfish), en 137 s


## 🟢 Vitesse d'affichage

Démarrage 1.17 s · écran le plus lent : Mes parties (4.4 ms/image)


## 🟠 Charge du processeur au repos

Menu : 7 % d'un cœur (60 img/s) · Partie : 10 % d'un cœur (40 img/s) · 12 cœurs logiques

- **« Partie » occupe le processeur sans rien faire** (moyen) – 10 % d'un cœur à 40 images/s alors que rien ne bouge. Pistes : ne redessiner que si quelque chose change, descendre à 30 images/s au repos, mettre en cache le fond et les textes (skill performance-pygame).

## 🟢 Mémoire

Jeu au menu : 75.2 Mo

- **Gros fichier chargé par le jeu : music/essais/1_Horloge.mp3** (info) – 2.3 Mo. Vérifier s'il peut être plus petit (taille d'image utile, son en .ogg).
- **Gros fichier chargé par le jeu : music/essais/2_Profondeur.mp3** (info) – 2.2 Mo. Vérifier s'il peut être plus petit (taille d'image utile, son en .ogg).
- **Gros fichier chargé par le jeu : music/essais/3_Tournoi.mp3** (info) – 1.7 Mo. Vérifier s'il peut être plus petit (taille d'image utile, son en .ogg).
- **Gros fichier chargé par le jeu : music/essais/4_Blitz_de_nuit.mp3** (info) – 2.2 Mo. Vérifier s'il peut être plus petit (taille d'image utile, son en .ogg).
- **Gros fichier chargé par le jeu : music/essais/5_Zugzwang.mp3** (info) – 2.0 Mo. Vérifier s'il peut être plus petit (taille d'image utile, son en .ogg).

## 🟢 Moteur d'analyse (Stockfish)

4 863 276 nœuds/s avec 10 fils de calcul (sur 12)


## 🟠 Ménage (code et fichiers inutiles)

32288 lignes de jeu · 6 imports/variables inutiles · 18 éléments peut-être morts · 0 fichier(s) jamais importé(s) · 7299 Mo de restes

- **Imports et variables inutiles** (faible) – 6 ligne(s) dans 1 fichier(s). Correction sûre et automatique : · python -m ruff check --select F401,F841 --fix jeu outils SickChess.py ·  · outils/video_bande_annonce.py : F841 Local variable `cx` is assigned to but never used ; F841 Local variable `cy` is assigned to but never used ; F841 Local variable `cx_plateau` is assigned to but never used
- **Fonctions et méthodes peut-être jamais utilisées** (moyen) – 18 élément(s) dans 9 fichier(s), à vérifier un par un avant de retirer (skill menage-code) : · jeu/steam.py : SALON_PRIVE (l.44), SALON_PUBLIC (l.46), CB_SALON_INFOS (l.61), SCORE_REMPLACER (l.75), DEMANDE_MONDIAL (l.76), DEMANDE_AUTOUR_DE_MOI (l.77), DEMANDE_AMIS (l.78), presence (l.683) · jeu/arbre_ouvertures.py : est_une_ligne (l.46), est_une_feuille (l.50) · SickChess.py : isatty (l.23), isatt
- **Fichiers en double** (faible) – 5 fichier(s) identiques (1.6 Mo) : · sounds/fifty_moves.wav = sounds/repetition.wav · sounds/fifty_moves.wav = sounds/stalemate.wav · sounds/feutre/repetition.wav = sounds/feutre/stalemate.wav · music/zugzwang.ogg = music/essais/5_Zugzwang.ogg · assets_src/steam/header_capsule_920x430.png = assets_src/steam/library_header_920x430.png
- **Restes de fabrication et de tests sur le disque** (info) – 7299 Mo au total (rien de tout ça n'est sur GitHub) : · build_amis : 52 Mo · publier : 7234 Mo · tests/ecrans : 3 Mo · tests/ecrans_en : 2 Mo · tests/ecrans_revue : 0 Mo · __pycache__ (tous) : 4 Mo · tests/capture_*.png : 3 Mo · « publier » et « build_amis » se refont à chaque version amis.

## 🟢 Conflits et santé du projet

0 conflit(s) Git · 0 erreur(s) de syntaxe · dépendances OK · 7 fichier(s) non enregistré(s)


## 🟢 Précision des pastilles (banque de positions)

114 coups justes sur 114 (calcul_forte, 307 s)


## ⚪ Endurance (un robot joue 2 heures)

Pas en mode rapide (2 heures) : python outils/endurance.py

