# Banc d'essai – SickChess

Dernier passage : 2026-10-23 19:28 · Windows 11 · 12 cœurs · Python 3.13.7 · pygame 2.6.1 · complet

Fabriqué par `python outils/banc_essai.py` (ne pas modifier à la main).

## 🟢 Bugs (tests automatiques)

634 contrôles OK sur 27 séries, en 151 s


## 🟢 Vitesse d'affichage

Démarrage 1.09 s · écran le plus lent : Mes parties (4.2 ms/image)


## 🟢 Charge du processeur au repos

Menu : 5 % d'un cœur (61 img/s) · Partie : 9 % d'un cœur (40 img/s) · 12 cœurs logiques


## 🟢 Mémoire

Jeu au menu : 73.2 Mo


## 🟢 Moteur d'analyse (Stockfish)

6 174 878 nœuds/s avec 10 fils de calcul (sur 12)


## 🟠 Ménage (code et fichiers inutiles)

26341 lignes de jeu · 0 imports/variables inutiles · 94 éléments peut-être morts · 1 fichier(s) jamais importé(s) · 8 Mo de restes

- **Fonctions et méthodes peut-être jamais utilisées** (moyen) – 94 élément(s) dans 37 fichier(s), à vérifier un par un avant de retirer (skill menage-code) : · jeu/design.py : bandeau (l.260), filet (l.273), jauge (l.280), puce (l.297), mesure (l.331), vignette (l.516), cadre_du_plateau (l.544) · jeu/faiblesse.py : SIGMA_ATTENTIF (l.142), lucidite (l.220), oublier_le_reglage (l.253), profondeur_ancienne (l.314), gaffes_par_partie (l.520), separer (l.525), pert
- **Fichier jamais importé : jeu/fond_anime.py** (moyen) – Aucun autre fichier ne l'utilise. Probablement un reste de V8.
- **Fichiers en double** (faible) – 4 fichier(s) identiques (0.6 Mo) : · sounds/fifty_moves.wav = sounds/repetition.wav · sounds/fifty_moves.wav = sounds/stalemate.wav · sounds/feutre/repetition.wav = sounds/feutre/stalemate.wav · assets_src/steam/header_capsule_920x430.png = assets_src/steam/library_header_920x430.png

## 🟢 Conflits et santé du projet

0 conflit(s) Git · 0 erreur(s) de syntaxe · dépendances OK · 8 fichier(s) non enregistré(s)

- **Commits pas encore envoyés sur GitHub** (info) – 4 commit(s) d'avance : penser au push.
