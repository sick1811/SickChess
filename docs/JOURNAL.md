# JOURNAL – SickChess

## Décisions
- **Nom du jeu : SickChess.** Dépôt GitHub : github.com/sick1811/SickChess
- **PC uniquement** (Windows) : Steam et itch.io. Plus de version mobile ni de Play Store.
- **On garde Python + Pygame** (pas de passage à Godot).
- **Méthode : on repart propre.** V8_TURBO_3000 reste l'archive de référence ; chaque
  fonction est réintégrée une par une dans SickChess, nettoyée et testée, le jeu
  restant jouable après chaque étape.
- **Aucune ressource sans licence vérifiée** (voir docs/CREDITS.md).

## 16/10/2026 – Étape 1 : le noyau (version 0.1.0)
Fait :
- Nouveau dossier propre : `SickChess.py` (lanceur), `jeu/` (code), ressources à la racine.
- 44 fichiers repris de V8_TURBO_3000 (plateau, règles, pendule, sons, Stockfish,
  partie à deux, écran de réglages) sur 90 ; 4 nouveaux fichiers plus simples :
  `game_manager.py` (250 lignes au lieu de 877), `menu_principal.py` (menu à 5 entrées),
  `ecran_fin.py` (carte de fin : Rejouer / Menu), `SickChess.py`.
- Renommage « Pokemon Chess » → SickChess. Pièces Pokémon et bois retirées.
- 19 bruitages originaux, synthétisés par `outils/generer_sons.py` (aucun droit à payer).
- **Bug corrigé : la pendule affichait « --:-- » à la fin de la partie** au lieu du
  temps final (0:00.0). Cause : l'affichage confondait « pendule en pause » et
  « partie sans pendule » (jeu/timer.py).
- Vérifié par `tests/test_noyau.py` : 19 sons chargés, son joué à chaque coup,
  alerte et clignotement sous 30 s, partie perdue au temps à 0:00, mat détecté.

À vérifier par Julien sur son PC :
- [ ] Lancer `LANCER.bat`, jouer une partie contre l'ordinateur et une à deux.
- [ ] Écouter les nouveaux sons : à garder, à retoucher ?
- [ ] Faire le premier « Push » vers GitHub (GitHub Desktop).

## 16/10/2026 – Étape 2 : Options et personnalisation
Fait :
- Nouvel écran `jeu/ecran_options.py` (remplace `personnalisation_screen.py`, 700 lignes) :
  4 onglets – **Échiquier** (12 damiers, 6 couleurs d'accent, coordonnées, dernier coup,
  coups possibles, flèche du cavalier), **Partie** (vitesse des pièces, retournement,
  pré-mouvement, plateau qui tourne à deux), **Son** (volume, on entend le son en
  cliquant), **Affichage** (fenêtre / plein écran, taille des textes, police).
- Aperçu de l'échiquier qui change en direct ; Annuler remet tout comme avant ;
  Entrée = enregistrer, Échap = annuler, Tab = onglet suivant.
- Seuls les réglages qui ont un effet sont proposés (voix des puzzles, poussière du
  fond… reviendront avec leurs écrans). Le choix « Pièces » apparaîtra dès qu'il y
  aura un 2e jeu de pièces.
- Entrée « Options » du menu activée ; le plein écran est retenu au démarrage.
- Vérifié par `tests/test_options.py` (19 contrôles, config.json remis tel quel).

À vérifier par Julien :
- [ ] Menu → Options : essayer damiers, accents, taille des textes, plein écran.
- [ ] Le fichier `config.json.test_bak` (reste d'un test) peut être supprimé.
- Noté pour la direction artistique : fous et rois du jeu « classique » trop
  ressemblants aux pions en petite taille ; textes sans accents à corriger partout.

## 16/10/2026 – Étape 5 : Mes parties et profil
Fait :
- Menu : entrée **« Mes parties et profil »** activée. Un seul écran
  (`jeu/ecran_mes_parties.py`, remplace `profil_screen.py` + `ecran_historique.py`) :
  à gauche le profil (nom modifiable, Elo estimé, meilleur Elo, victoires / nulles /
  défaites, courbe de progression) ; à droite toutes les parties, la plus récente en
  haut, avec une pastille V / N / D (ou « 2J » pour une partie à deux), la date,
  la cadence et l'ouverture. Bouton « Ouvrir le dossier ».
- **Relecture coup par coup** (`jeu/ecran_revoir.py`) : clic sur une partie → échiquier
  + feuille de partie ; flèches ← →, Début/Fin, molette, clic sur un coup, F pour
  retourner. Sans analyse pour l'instant : la revue (étape 4) viendra s'y brancher.
- **Fin de partie** (`jeu/enregistrement.py`) : contre l'ordinateur, la partie entre
  dans le profil et l'Elo bouge (affiché sur la carte de fin : « 1200 -> 1230 (+30) ») ;
  avec un indice demandé, elle compte dans les stats mais pas dans l'Elo. Toute
  partie (y compris à deux) est écrite en PGN dans `parties/` (`historique_parties.py`).
  Une partie à deux ne touche pas au profil (on ne sait pas qui tu étais).
- **Reprise de partie** (`jeu/sauvegarde.py`) : la partie en cours est sauvée toutes
  les 5 s, en revenant au menu et en fermant le jeu ; le menu affiche alors
  « Reprendre la partie en cours » (pendules, couleurs et orientation retrouvées).
- Petites retouches : `mode_stockfish.py` (couleur imposée à la reprise ; l'IA ne
  réfléchit au départ que si elle a le trait), `board.py` (plateau muet pour la
  relecture), `ecran_fin.py` (ligne de classement), `menu_principal.py` (bouton
  Reprendre, boutons qui se resserrent pour tenir en 640 px).
- `statistiques.py` (qualité des coups par tranche d'Elo) **pas repris ici** : il
  dépend de l'analyse, il reviendra avec la revue de partie (étape 4).
- Vérifié par `tests/test_mes_parties.py` (41 contrôles, dans un dossier temporaire :
  profil.json et parties/ ne sont pas touchés) + `tests/test_noyau.py` toujours bon.

À vérifier par Julien :
- [ ] Jouer une partie contre l'ordinateur jusqu'au bout → regarder l'Elo sur la carte
  de fin, puis Menu → Mes parties et profil → Revoir.
- [ ] Changer son nom dans le profil.
- [ ] Fermer le jeu en pleine partie, le relancer → « Reprendre la partie en cours ».

## 16/10/2026 – Étape 4 : Revue de partie
Fait :
- **Analyse** (`jeu/analyse_partie.py`, 395 lignes au lieu de 1016 + `rapport_analyse.py`) :
  un seul Stockfish d'analyse (sans bride, séparé de l'adversaire), d'abord un survol
  rapide de toute la partie (pastilles et précision en quelques secondes), puis une
  passe fine. Le coup que tu regardes passe toujours en premier (jugé en ~0,5 s).
  Puissance réglable dans config.json : `"analyse_puissance"` = `"rapide"` (prof. 14),
  `"normale"` (18, par défaut) ou `"forte"` (22).
- **Écran de revue** (`jeu/ecran_revue.py`, remplace `replay_screen.py` 1269 lignes,
  `replay_manager`, `replay_window`, `courbe_eval`) : barre d'avantage le long de
  l'échiquier ; pastille du coup sur sa case (!!, !, ★, ✓, ?!, ?, ??…) ; **flèche verte
  vers le coup qu'il fallait jouer** quand le coup est une imprécision, une erreur ou
  une gaffe ; précision de chaque joueur (méthode lichess) avec le compte des
  pastilles ; détail du coup (« Gaffe. Il fallait jouer Rf7 », évaluation, meilleur
  coup maintenant) ; courbe de la partie avec les fautes en points rouges (cliquable) ;
  feuille de partie avec une pastille par coup. Flèches, molette, Début/Fin, F, Échap.
- **Carte de fin** : l'analyse démarre dès la fin de la partie ; la carte affiche
  « Précision : toi 84 % – ordinateur 91 % » puis un bouton **« Revue de la partie »**.
- **Mes parties** : ouvrir une partie enregistrée lance maintenant la revue (avec
  analyse) ; la relecture simple (`ecran_revoir.py`) ne sert plus que si le PGN est
  illisible.
- **Bug corrigé – faux « Brillant »** : une pièce simplement attaquée comptait comme un
  sacrifice, même défendue par un pion (4…d5 5.exd5 Cxd5 … 8.Cc3 dans le Fegatello
  était « Brillant »). Il faut maintenant qu'elle soit vraiment en prise
  (`annotations.est_un_sacrifice`).
- **Bug corrigé – mats** : un mat annoncé par Stockfish n'avait pas d'évaluation, le
  coup restait sans pastille. Un mat compte maintenant pour ±20 pions (affiché « M3 »).
- Vérifié par `tests/test_revue.py` (32 contrôles, avec un vrai Stockfish) : gaffe
  10…Cd3+ repérée et meilleur coup proposé, mat du berger, précision, écran dessiné
  à 4 tailles de fenêtre, fin de partie → revue → retour, revue d'un PGN.
  Les autres tests (noyau, options, mes parties) sont toujours bons.

À vérifier par Julien :
- [ ] Finir une partie contre l'ordinateur → regarder la précision sur la carte de fin
  → « Revue de la partie » → naviguer avec les flèches.
- [ ] Dire si la vitesse d'analyse te convient sur ton i7 (sinon `"forte"` ou `"rapide"`).
- Pas encore repris : jouer des variantes dans la revue, l'indice (touche H), les
  statistiques par tranche d'Elo (`statistiques.py`).

## 16/10/2026 – Étape 9 : multijoueur Steam
Fait :
- Menu « Jouer en ligne (Steam) ». Créer une partie = salon Steam réservé aux amis ;
  inviter depuis la liste d'amis affichée dans le jeu, l'overlay Steam, ou un code
  (ex. `U0W2-PIQO-3K1`). Accepter une invitation Steam ouvre directement le salon,
  même si le jeu était fermé (`+connect_lobby`).
- L'hôte choisit cadence et couleur (Blancs / Noirs / hasard), l'ami les voit en direct.
- Partie : coups, pendules arbitrées (`pendule_reseau.py` de V8), chat, abandon,
  revanche couleurs inversées. Un message perdu se rattrape tout seul. Adversaire
  qui quitte = victoire ; connexion muette 60 s = partie interrompue (nulle).
- Le relais bore.pub n'est pas repris : tout passe par le relais de Valve.
- Nouveaux fichiers : `steam.py`, `reseau_transport.py`, `salon_en_ligne.py`,
  `mode_en_ligne.py`, `partie_en_ligne.py` (+ `pendule_reseau.py`, `revanche.py`
  repris de V8). `game_manager.py` / `menu_principal.py` : quelques lignes.
- `steam_appid.txt` = 480 (numéro de test de Valve) ; `steam_api64.dll` à côté du jeu
  (hors GitHub). Mode d'emploi : `docs/MULTIJOUEUR_STEAM.md`.
- Vérifié par `tests/test_multijoueur.py` (44 contrôles, avec un faux Steam).
  Pas encore testé avec le vrai Steam : il faut deux PC et deux comptes amis.

À vérifier par Julien :
- [ ] Test sur un PC : lancer le jeu deux fois, « Test : héberger » / « Test : rejoindre ».
- [ ] Test Steam avec un ami (deux PC) : inviter, jouer, revanche.
- [ ] Dire si l'overlay Steam (Maj+Tab) s'ouvre dans le jeu (pygame ne le garantit pas).
- Pas encore fait : proposer la nulle, enregistrer les parties en ligne dans
  « Mes parties », spectateurs. Avant la sortie : `MODE_TEST = False`.

## 16/10/2026 – Étape 6 : Problèmes
Fait :
- Menu « Problèmes » activé (grisé « base absente » si le dossier `puzzles/` manque).
- **Base lichess** copiée de V8 dans `puzzles/` (64 tranches, 223 Mo, 4 180 151
  problèmes, hors GitHub). Licence CC0 ajoutée à CREDITS.md.
- `jeu/puzzles.py` (base, tirage à ton niveau, classement Elo, modes Classé / Libre,
  bonus de vitesse ×1,6 → ×0,6, indice −8) : repris de V8, nettoyé (l'ancienne base
  d'un seul fichier n'est plus lue).
- `jeu/ecran_problemes.py` (≈770 lignes au lieu de 1377 + `plateau_simple.py`) : il
  utilise **le vrai plateau de la partie**, donc glisser-déposer, flèches au clic droit,
  pré-mouvement, promotion, animations et sons identiques à une partie.
  Écran de choix (Classé / Libre + niveau de départ + filtre de 12 thèmes) ; coup
  adverse joué tout seul ; chrono ; coup faux = plateau rouge + explication sans
  donner la solution, on peut réessayer mais c'est compté raté ; réussi du premier
  coup = vert puis problème suivant automatique ; « Passer » un problème commencé
  = raté ; solution navigable (flèches, Début/Fin, clic sur un coup) ; un mat par
  un autre chemin que celui de la base est accepté.
- `jeu/explication_puzzle.py` : l'explication écrite de V8, **sans la voix**
  (trop robotique pour un jeu vendu).
- 2 nouveaux sons synthétisés : `puzzle_reussi`, `puzzle_faux` (21 sons en tout).
- Ton classement de problèmes de V8 (1306) est repris (`puzzles_score.json`).
- Pas repris : le classement en ligne par bore.pub (→ classements Steam plus tard).
- Vérifié par `tests/test_problemes.py` (53 contrôles, score dans un dossier
  temporaire) ; noyau, options et mes parties toujours bons.

À vérifier par Julien :
- [ ] Menu → Problèmes → Mode classé : en faire une dizaine (glisser, clic-clic, H).
- [ ] Écouter les deux nouveaux sons (trouvé / pas le bon coup).
- [ ] Dire si l'enchaînement automatique après une réussite (0,9 s) est trop rapide.

## 16/10/2026 – Étape 3 : direction artistique « Onyx & Or » (conversation graphisme)
Choix de Julien dans les deux pages « Atelier SickChess » (voir `assets_src/atelier/`) :
- **Interface** : noirs d'onyx (`design.ARDOISE` refait) et accent **Or** par défaut (le choix
  d'accent reste libre dans Options). Police **Barlow Semi Condensed** (OFL) à la place
  d'Outfit, agrandie de 10 % pour garder les mises en page.
- **Pièces** : 5 nouveaux jeux originaux, défaut **Relief Prisme** – Relief Prisme / Arène /
  Tournoi (modèles 3D rendus dans Blender) et Arène / Tournoi plats. Même cadrage pour toutes
  les pièces d'un jeu, contour de lisibilité, tour affinée. « Classique » reste proposé.
  Remarque de Julien « la 3D sur du 2D, c'est pas top » : les pièces Relief sont maintenant
  rendues **de face** (sans perspective ni ombre au sol), elles se posent comme des pièces 2D.
  Commande : `ELEVATION=0 OMBRE=0 ROT_CAVALIER=0 python rendu_sprites.py prisme <dossier>`
  puis `python finir_sprites.py <dossier> assets/pieces/relief_prisme`.
- 17/10 : Julien choisit les pièces **Tournoi plat** comme jeu par défaut (en tête de la
  liste dans Options) ; les Relief restent au choix.
- **Plateaux** : défaut **Tournoi** (uni crème et vert, le plus lisible) ; 8 unis + 3 matières
  (marbre veiné, onyx et or, noyer et érable : images dans `assets/plateaux/`). Les 6 damiers
  de la v7 ne sont plus listés (toujours lus si un vieux config.json les nomme).
- **Menu** : « Vitrine » – rendu 3D du plateau en fond (`assets/menu/fond_menu.jpg`), titre
  SICK**CHESS**, entrées en colonne à gauche, barre dorée au survol.
- Code touché : `design.py`, `apparence.py` (jeux d'images, `damier_texture()`),
  `board_render.py` et `ecran_options.py` (plateaux en matière), `ui.py` (police),
  `menu_principal.py` (dessin du menu ; les entrées et leurs clés ne changent pas).
- `config.json` de Julien réglé sur ses choix : plateau tournoi, accent or, pièces relief_prisme.
- Sources de tout le graphisme : `outils/blender/` (régénérable, voir `assets_src/atelier/LISEZ-MOI.md`).

À vérifier par Julien :
- [ ] Lancer le jeu : menu, une partie, Options → Échiquier (pièces et plateaux).
- [ ] Dire si les pièces Relief blanches se lisent assez sur les cases claires.

## 17/10/2026 – Assemblage de la direction artistique
Le travail des conversations parallèles (étapes 2 à 6 et 9) n'avait jamais été enregistré dans
Git ni vérifié ensemble. Fait dans cette séance :
- **Tout tient ensemble** : les 6 séries de tests passent (199 contrôles, la revue avec un vrai
  Stockfish). Nouveau `tests/captures_ecrans.py` : photographie menu, réglages, partie, aide F1,
  promotion et revue dans `tests/ecrans/` pour juger la DA d'un coup d'œil.
- **Pièces Relief lisibles** (`outils/retoucher_pieces.py`, originaux gardés dans
  `assets_src/pieces_relief_origine/`) : l'ombre portée cuite dans l'image (tache grise à droite,
  pièce décentrée) est retirée et remplacée par une petite ombre de contact centrée ; contour
  régulier, sombre autour des blancs, clair autour des noirs ; blancs un peu plus modelés.
  → réponse à « les Relief blanches se lisent-elles sur les cases claires ? » : non, c'est corrigé.
- **Bug corrigé – fou blanc sans contour** : son fichier s'appelle `b.png` et la règle « finit par
  b = pièce noire » le prenait pour un noir (aussi corrigé dans `outils/blender/finir_sprites.py`).
- **Accents partout** : environ 280 textes affichés corrigés dans 40 fichiers (Échiquier, Pièces,
  Problèmes, Précision, Défaite, COUPS JOUÉS, À toi…), plus 84 noms d'ouvertures (« Défense des
  deux cavaliers », « Gambit dame accepté »…). Les messages du journal technique, les clés de
  réglages et les textes comparés dans le code n'ont pas été touchés. Les noms d'ouvertures
  n'ont plus leurs accents retirés : le lanceur rend la console Windows tolérante
  (`reconfigure(errors="replace")`), ce qui supprime la raison de cette précaution de V8.
- **Écran de réglages avant partie** mis au style Onyx & Or : il avait gardé les couleurs de V8
  (titres jaune vif, sélection cuivre, fond violet à poussière). Couleurs tirées du thème (suit
  l'accent choisi), même fond et mêmes boutons qu'Options, « ordinateur » au lieu de « Stockfish ».
  La case « Partir d'une position chargée » est cachée : elle ne faisait plus rien.
- **Icône et logo** (`outils/generer_logo.py`) : cavalier doré (pièce « Tournoi plat » du projet)
  sur tuile onyx à filet or ; `assets/icone.ico` (16 à 256 px, pour le futur .exe),
  `assets/icone.png` (posée sur la fenêtre du jeu), `assets/logo.png` et `logo_fond.png`.

À vérifier par Julien :
- [ ] Lancer le jeu : icône dans la barre des tâches, réglages avant partie, pièces Relief.
- [ ] Décider la notation des coups (voir question ci-dessous).

Question ouverte : les coups sont écrits en notation anglaise (Nf3, Bc4, Qh5) alors que tout le jeu
est en français. Trois choix : notation française (Cf3, Fc4, Dh5), notation par figurines
(petite icône de pièce + case, lisible dans toutes les langues, comme chess.com), ou garder l'anglais.

## Bugs connus (repris de « a debug.txt »)
- [x] Pendule ne clignote pas à 30 s → fonctionne (testé).
- [x] Fin de partie à 00:00 → corrigé (affichage du temps final).
- [ ] Son « coupé » : à confirmer à l'oreille avec les nouveaux sons.
- [ ] Animation lente (réglable : `vitesse_animation` dans config.json, 0.18 s).
- [ ] Temps de réflexion de Stockfish pas assez humain.
- [x] Organisation de la fenêtre de jeu : disposition « Classique » retenue (plateau à gauche, panneau à droite).

## Fonctions de V8_TURBO_3000 à réintégrer (dans cet ordre)
1. Compilation en .exe (PyInstaller) – adapter COMPILER.bat à la nouvelle structure.
2. ~~Options / personnalisation~~ → fait (étape 2). Reste : options accessibles en pleine partie.
3. ~~Direction artistique~~ → fait (étape 3 + assemblage du 17/10). Reste : captures et
   capsules pour la page Steam, notation des coups.
4. ~~Revue de partie~~ → fait (étape 4). Reste : variantes dans la revue, `statistiques`.
5. ~~Mes parties + profil~~ → fait (étape 5). Reste : `statistiques` (avec la revue).
6. ~~Problèmes~~ → fait (étape 6). Reste : classement des problèmes en ligne (Steam),
   classement des problèmes dans « Mes parties et profil ».
7. Entraînement aux ouvertures et faiblesses (`ecran_entrainement`, `faiblesse`).
8. Bouton « Signaler un problème / Proposer une idée ».
9. ~~Multijoueur Steam~~ → fait (étape 9). Reste : test réel à deux PC, nulle, parties en ligne dans « Mes parties ».
10. Tables de finales Syzygy (379 Mo) : utiles ? à décider.
