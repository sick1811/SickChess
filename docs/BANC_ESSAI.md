# Banc d'essai – SickChess

Dernier passage : 2026-10-24 20:46 · Windows 11 · 12 cœurs · Python 3.13.7 · pygame 2.6.1 · complet

Fabriqué par `python outils/banc_essai.py` (ne pas modifier à la main).

## 🟢 Bugs (tests automatiques)

871 contrôles OK sur 35 séries (sans Stockfish), en 76 s


## 🟢 Vitesse d'affichage

Démarrage 0.68 s · écran le plus lent : Mes parties (4.1 ms/image)


## 🟢 Charge du processeur au repos

Menu : 5 % d'un cœur (60 img/s) · Partie : 10 % d'un cœur (40 img/s) · 12 cœurs logiques


## 🟢 Mémoire

Jeu au menu : 73.1 Mo


## 🟢 Moteur d'analyse (Stockfish)

6 514 586 nœuds/s avec 10 fils de calcul (sur 12)


## 🟠 Ménage (code et fichiers inutiles)

29830 lignes de jeu · 0 imports/variables inutiles · 101 éléments peut-être morts · 1 fichier(s) jamais importé(s) · 1698 Mo de restes

- **Fonctions et méthodes peut-être jamais utilisées** (moyen) – 98 élément(s) dans 37 fichier(s), à vérifier un par un avant de retirer (skill menage-code) : · jeu/steam.py : SALON_PRIVE (l.40), SALON_PUBLIC (l.42), CB_SALON_INFOS (l.57), SCORE_REMPLACER (l.71), DEMANDE_MONDIAL (l.72), DEMANDE_AUTOUR_DE_MOI (l.73), DEMANDE_AMIS (l.74), presence (l.671) · jeu/design.py : contraste (l.161), filet (l.285), jauge (l.292), puce (l.309), mesure (l.343), vignette (l.
- **Valeurs rangées mais jamais relues (attributs)** (faible) – 3 élément(s) dans 2 fichier(s), à vérifier un par un avant de retirer (skill menage-code) : · jeu/ecran_revue.py : analyse_libre (l.572), analyse_libre (l.578) · jeu/ecran_analyse_libre.py : ep_square (l.52)
- **Fichier jamais importé : jeu/fond_anime.py** (moyen) – Aucun autre fichier ne l'utilise. Probablement un reste de V8.
- **Fichiers en double** (faible) – 4 fichier(s) identiques (0.6 Mo) : · sounds/fifty_moves.wav = sounds/repetition.wav · sounds/fifty_moves.wav = sounds/stalemate.wav · sounds/feutre/repetition.wav = sounds/feutre/stalemate.wav · assets_src/steam/header_capsule_920x430.png = assets_src/steam/library_header_920x430.png
- **Restes de fabrication et de tests sur le disque** (info) – 1698 Mo au total (rien de tout ça n'est sur GitHub) : · build_amis : 52 Mo · publier : 1637 Mo · tests/ecrans : 2 Mo · tests/ecrans_en : 2 Mo · tests/ecrans_revue : 0 Mo · __pycache__ (tous) : 3 Mo · tests/capture_*.png : 3 Mo · « publier » et « build_amis » se refont à chaque version amis.

## 🟢 Conflits et santé du projet

0 conflit(s) Git · 0 erreur(s) de syntaxe · dépendances OK · 2 fichier(s) non enregistré(s)


## 🟢 Précision des pastilles (banque de positions)

114 coups justes sur 114 (calcul_forte, 626 s)


## ⚪ Endurance (un robot joue 2 heures)

Pas en mode rapide (2 heures) : python outils/endurance.py

