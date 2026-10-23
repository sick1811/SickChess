# Banc d'essai – SickChess

Dernier passage : 2026-10-23 19:15 · Windows 11 · 12 cœurs · Python 3.13.7 · pygame 2.6.1 · complet

Fabriqué par `python outils/banc_essai.py` (ne pas modifier à la main).

## 🟢 Bugs (tests automatiques)

634 contrôles OK sur 27 séries, en 162 s


## 🟠 Vitesse d'affichage

Démarrage 1.11 s · écran le plus lent : Revue (5.3 ms/image)

- **Écran « Revue » lent à dessiner** (moyen) – 5.3 ms par image (budget conseillé : 5 ms). Chaque image redessine tout : mettre en cache ce qui ne bouge pas (fond, textes, cases). ·  · Où passe le temps d'une image : · 'blit' of 'pygame.surface.Surface' objects : 30 % (151 appels par image) · pygame.draw.rect : 7 % (88 appels par image) · board_render.py:139 _fleche : 4 % (1 appels par image) · 'render' of 'pygame.font.Font' objects : 4 % (17 

## 🟠 Charge du processeur au repos

Menu : 4 % d'un cœur (60 img/s) · Partie : 17 % d'un cœur (40 img/s) · 12 cœurs logiques

- **« Partie » occupe le processeur sans rien faire** (moyen) – 17 % d'un cœur à 40 images/s alors que rien ne bouge. Pistes : ne redessiner que si quelque chose change, descendre à 30 images/s au repos, mettre en cache le fond et les textes (skill performance-pygame).

## 🟢 Mémoire

Jeu au menu : 73.4 Mo


## 🟢 Moteur d'analyse (Stockfish)

6 798 148 nœuds/s avec 10 fils de calcul (sur 12)


## 🟠 Ménage (code et fichiers inutiles)

26264 lignes de jeu · 0 imports/variables inutiles · 94 éléments peut-être morts · 1 fichier(s) jamais importé(s) · 779 Mo de restes

- **Fonctions et méthodes peut-être jamais utilisées** (moyen) – 94 élément(s) dans 37 fichier(s), à vérifier un par un avant de retirer (skill menage-code) : · jeu/design.py : bandeau (l.260), filet (l.273), jauge (l.280), puce (l.297), mesure (l.331), vignette (l.516), cadre_du_plateau (l.544) · jeu/faiblesse.py : SIGMA_ATTENTIF (l.142), lucidite (l.220), oublier_le_reglage (l.253), profondeur_ancienne (l.314), gaffes_par_partie (l.520), separer (l.525), pert
- **Fichier jamais importé : jeu/fond_anime.py** (moyen) – Aucun autre fichier ne l'utilise. Probablement un reste de V8.
- **Fichiers en double** (faible) – 4 fichier(s) identiques (0.6 Mo) : · sounds/fifty_moves.wav = sounds/repetition.wav · sounds/fifty_moves.wav = sounds/stalemate.wav · sounds/feutre/repetition.wav = sounds/feutre/stalemate.wav · assets_src/steam/header_capsule_920x430.png = assets_src/steam/library_header_920x430.png
- **Restes de fabrication et de tests sur le disque** (info) – 779 Mo au total (rien de tout ça n'est sur GitHub) : · build_amis : 52 Mo · publier : 720 Mo · tests/ecrans : 1 Mo · tests/ecrans_en : 2 Mo · tests/ecrans_revue : 0 Mo · __pycache__ (tous) : 3 Mo · tests/capture_*.png : 3 Mo · « publier » et « build_amis » se refont à chaque version amis.

## 🟠 Conflits et santé du projet

0 conflit(s) Git · 0 erreur(s) de syntaxe · dépendances OK · 30 fichier(s) non enregistré(s)

- **Beaucoup de changements pas encore enregistrés dans Git** (moyen) – 30 fichiers modifiés depuis le dernier commit. Si Cowork et Claude Code travaillent en même temps, demander à Claude Code un commit avant la séance suivante.
- **Commits pas encore envoyés sur GitHub** (info) – 3 commit(s) d'avance : penser au push.
