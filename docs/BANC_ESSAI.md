# Banc d'essai – SickChess

Dernier passage : 2026-10-23 18:52 · Windows 11 · 12 cœurs · Python 3.13.7 · pygame 2.6.1 · complet

Fabriqué par `python outils/banc_essai.py` (ne pas modifier à la main).

## 🟢 Bugs (tests automatiques)

620 contrôles OK sur 27 séries, en 141 s


## 🔴 Vitesse d'affichage

Démarrage 1.08 s · écran le plus lent : Ouvertures (15.0 ms/image)

- **Écran « Partie » lent à dessiner** (moyen) – 6.7 ms par image (budget conseillé : 5 ms). Chaque image redessine tout : mettre en cache ce qui ne bouge pas (fond, textes, cases). ·  · Où passe le temps d'une image : · 'size' of 'pygame.font.Font' objects : 34 % (43 appels par image) · 'blit' of 'pygame.surface.Surface' objects : 25 % (92 appels par image) · 'render' of 'pygame.font.Font' objects : 11 % (44 appels par image) · pygame.draw.rect
- **Écran « Revue » lent à dessiner** (moyen) – 8.3 ms par image (budget conseillé : 5 ms). Chaque image redessine tout : mettre en cache ce qui ne bouge pas (fond, textes, cases). ·  · Où passe le temps d'une image : · 'blit' of 'pygame.surface.Surface' objects : 21 % (151 appels par image) · 'size' of 'pygame.font.Font' objects : 15 % (93 appels par image) · 'render' of 'pygame.font.Font' objects : 14 % (96 appels par image) · pygame.draw.rec
- **Écran « Options » lent à dessiner** (moyen) – 9.6 ms par image (budget conseillé : 5 ms). Chaque image redessine tout : mettre en cache ce qui ne bouge pas (fond, textes, cases). ·  · Où passe le temps d'une image : · 'render' of 'pygame.font.Font' objects : 35 % (68 appels par image) · 'size' of 'pygame.font.Font' objects : 20 % (83 appels par image) · 'blit' of 'pygame.surface.Surface' objects : 17 % (191 appels par image) · pygame.draw.rec
- **Écran « Mes parties » lent à dessiner** (grave) – 14.3 ms par image (budget conseillé : 5 ms). Chaque image redessine tout : mettre en cache ce qui ne bouge pas (fond, textes, cases). ·  · Où passe le temps d'une image : · 'render' of 'pygame.font.Font' objects : 36 % (55 appels par image) · 'size' of 'pygame.font.Font' objects : 27 % (71 appels par image) · 'blit' of 'pygame.surface.Surface' objects : 23 % (112 appels par image) · pygame.draw.re
- **« Ouvertures » relit des fichiers à chaque image** (grave) – Le disque est lu pendant le dessin, 60 fois par seconde : · entrainement.py:176 charger_progression (24 fois par image) · Lire une fois à l'ouverture de l'écran (ou après un changement), puis garder en mémoire.
- **Écran « Ouvertures » lent à dessiner** (grave) – 15.0 ms par image (budget conseillé : 5 ms). Chaque image redessine tout : mettre en cache ce qui ne bouge pas (fond, textes, cases). ·  · Où passe le temps d'une image : · 'render' of 'pygame.font.Font' objects : 34 % (56 appels par image) · 'size' of 'pygame.font.Font' objects : 19 % (59 appels par image) · _io.open : 13 % (24 appels par image) · 'read' of '_io.TextIOWrapper' objects : 5 % (24 a
- **« Problèmes » relit des fichiers à chaque image** (grave) – Le disque est lu pendant le dessin, 60 fois par seconde : · modes_problemes.py:42 charger (3 fois par image) · Lire une fois à l'ouverture de l'écran (ou après un changement), puis garder en mémoire.
- **Écran « Problèmes » lent à dessiner** (moyen) – 7.4 ms par image (budget conseillé : 5 ms). Chaque image redessine tout : mettre en cache ce qui ne bouge pas (fond, textes, cases). ·  · Où passe le temps d'une image : · 'size' of 'pygame.font.Font' objects : 36 % (61 appels par image) · 'render' of 'pygame.font.Font' objects : 31 % (34 appels par image) · 'blit' of 'pygame.surface.Surface' objects : 5 % (92 appels par image) · _io.open : 4 % (3

## 🔴 Charge du processeur au repos

Menu : 9 % d'un cœur (61 img/s) · Partie : 38 % d'un cœur (61 img/s) · 12 cœurs logiques

- **« Partie » occupe le processeur sans rien faire** (grave) – 38 % d'un cœur à 61 images/s alors que rien ne bouge. Pistes : ne redessiner que si quelque chose change, descendre à 30 images/s au repos, mettre en cache le fond et les textes (skill performance-pygame).

## 🟢 Mémoire

Jeu au menu : 75.2 Mo


## 🟢 Moteur d'analyse (Stockfish)

6 353 232 nœuds/s avec 10 fils de calcul (sur 12)


## 🟠 Ménage (code et fichiers inutiles)

26224 lignes de jeu · 8 imports/variables inutiles · 147 éléments peut-être morts · 1 fichier(s) jamais importé(s) · 779 Mo de restes

- **Imports et variables inutiles** (faible) – 8 ligne(s) dans 7 fichier(s). Correction sûre et automatique : · python -m ruff check --select F401,F841 --fix jeu outils SickChess.py ·  · jeu/explication_puzzle.py : F841 Local variable `joue_san` is assigned to but never used ; F841 Local variable `piece_jouee` is assigned to but never used · jeu/analyse_partie.py : F841 Local variable `profondeur` is assigned to but never used · jeu/board.py :
- **Fonctions et méthodes peut-être jamais utilisées** (moyen) – 96 élément(s) dans 38 fichier(s), à vérifier un par un avant de retirer (skill menage-code) : · jeu/design.py : bandeau (l.260), filet (l.273), jauge (l.280), puce (l.297), mesure (l.331), vignette (l.516), cadre_du_plateau (l.544) · jeu/faiblesse.py : SIGMA_ATTENTIF (l.142), lucidite (l.220), oublier_le_reglage (l.253), profondeur_ancienne (l.314), gaffes_par_partie (l.520), separer (l.525), pert
- **Valeurs rangées mais jamais relues (attributs)** (faible) – 51 élément(s) dans 17 fichier(s), à vérifier un par un avant de retirer (skill menage-code) : · jeu/settings_screen.py : f_titre (l.292), f_section (l.293), f_texte (l.294), f_chip (l.295), f_valeur (l.296), f_petit (l.297), case_position (l.359), zone_position (l.362) … · jeu/revanche.py : j_ai_demande (l.37), il_a_demande (l.38), j_ai_demande (l.93), il_a_demande (l.107), il_a_demande (l.128), j
- **Fichier jamais importé : jeu/fond_anime.py** (moyen) – Aucun autre fichier ne l'utilise. Probablement un reste de V8.
- **Fichiers en double** (faible) – 4 fichier(s) identiques (0.6 Mo) : · sounds/fifty_moves.wav = sounds/repetition.wav · sounds/fifty_moves.wav = sounds/stalemate.wav · sounds/feutre/repetition.wav = sounds/feutre/stalemate.wav · assets_src/steam/header_capsule_920x430.png = assets_src/steam/library_header_920x430.png
- **Restes de fabrication et de tests sur le disque** (info) – 779 Mo au total (rien de tout ça n'est sur GitHub) : · build_amis : 52 Mo · publier : 720 Mo · tests/ecrans : 1 Mo · tests/ecrans_en : 2 Mo · tests/ecrans_revue : 0 Mo · __pycache__ (tous) : 3 Mo · tests/capture_*.png : 3 Mo · « publier » et « build_amis » se refont à chaque version amis.

## 🟠 Conflits et santé du projet

0 conflit(s) Git · 0 erreur(s) de syntaxe · dépendances OK · 29 fichier(s) non enregistré(s)

- **Beaucoup de changements pas encore enregistrés dans Git** (moyen) – 29 fichiers modifiés depuis le dernier commit. Si Cowork et Claude Code travaillent en même temps, demander à Claude Code un commit avant la séance suivante.
- **Commits pas encore envoyés sur GitHub** (info) – 2 commit(s) d'avance : penser au push.
- **Verrou Git oublié : .git/index.lock** (moyen) – Une opération Git a été coupée. Si aucun Git ne tourne, le supprimer (Claude Code peut le faire).
- **Réglages de config.json que le jeu ne lit plus** (faible) – ia_suivre_la_pendule
