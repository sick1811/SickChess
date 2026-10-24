# JOURNAL – SickChess

## Décisions
- **Nom du jeu : SickChess.** Dépôt GitHub : github.com/sick1811/SickChess
- **PC uniquement** (Windows) : Steam et itch.io. Plus de version mobile ni de Play Store.
- **On garde Python + Pygame** (pas de passage à Godot).
- **Méthode : on repart propre.** V8_TURBO_3000 reste l'archive de référence ; chaque
  fonction est réintégrée une par une dans SickChess, nettoyée et testée, le jeu
  restant jouable après chaque étape.
- **Aucune ressource sans licence vérifiée** (voir docs/CREDITS.md).
- **Les vérifications de Julien se cochent dans la page « SickChess – À faire »**
  (https://claude.ai/artifact/PzJkQy7b8DKRs9wgksP9T5, collection `taches`) : y ajouter les
  nouvelles tâches à tester au lieu de cases `- [ ]` ici, et la relire pour savoir ce qui est fait.
- **Règle de Julien (17/10) : à CHAQUE séance de code, ajouter dans cette page les tests de la
  séance** (statut Fonctionne / Ne fonctionne pas + commentaire, champ `etape` = date · sujet).
  Le jeu écrit `journal_du_jeu.txt` à chaque lancement : le lire après ses tests.

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
- 17/10 – **Bug corrigé : promotion impossible dans les problèmes.** Le choix de la pièce
  (Dame / Tour / Fou / Cavalier) s'ouvrait mais n'était pas dessiné sur cet écran, et le
  clic suivant l'annulait. Testé (glisser et clic-clic) dans `tests/test_problemes.py`.

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
- 17/10 : **logo officiel** choisi par Julien parmi 5 propositions + 3 mélanges : cavalier or
  (pièces Tournoi plat) sur un damier gris et noir, nom SICK**CHESS**, devise
  « ENTRAÎNE · ANALYSE · GAGNE ». Fichiers : `assets/icone.png`, `assets/icone.ico`
  (16 à 256 px, pour la fenêtre et le futur .exe), `assets/logo.png`, `assets/logo_fond.png`.
  Source : `outils/blender/gen_logo.py` ; `outils/generer_logo.py` (ancienne icône) ne doit
  plus être lancé. L'icône est aussi dessinée devant le titre du menu.
- 17/10 : **images de la page Steam** dans `assets_src/steam/` (voir son LISEZ-MOI) : les 4
  capsules obligatoires, les 4 images de bibliothèque, le fond de page, l'icône communauté
  et 6 captures 1920×1080 (menu, partie, revue, problème, options, réglages) faites avec
  les réglages par défaut. Illustrations : `outils/blender/rendu_steam.py`.
  Menu : entrées plus grandes en plein écran 1920×1080.
  Les pièces Relief vues de face (choix du 17/10) ont été remises dans `assets/pieces/` et
  `assets_src/pieces_relief_origine/` (une retouche les avait remplacées par les anciennes).
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

## 17/10/2026 (4) – « Mes erreurs » et variantes dans la revue (Cowork)
Julien n'ayant rien choisi dans « Travaux proposés », Claude a pris sa recommandation (p04, p01).
Fait :
- **Problèmes tirés de tes gaffes** (`jeu/mes_erreurs.py`, nouveau) : chaque gaffe, erreur ou coup
  manqué de Julien dans une partie dont l'analyse est enregistrée devient un problème au format
  lichess (`fen` = avant le coup adverse précédent, `coups` = [coup adverse, meilleur coup]).
  Bouton « Mes erreurs – N positions de tes parties » dans l'écran des problèmes ; description
  « Ta partie du … – coup 3… : tu as joué Cf6 (gaffe) » ; un autre coup accepté s'il ne perd pas
  plus de 0,3 pion (Stockfish profondeur 14) ; suivi dans `mes_erreurs.json` (hors GitHub) ; le
  classement des problèmes n'est pas touché ; le gros chiffre du panneau = « 3/12 ».
  Test : `tests/test_mes_erreurs.py`.
- **Variantes dans la revue** (`jeu/ecran_revue.py`) : on joue sur l'échiquier de la revue ; le coup
  de la partie fait avancer, un autre ouvre une variante, Stockfish répond (2e moteur d'analyse,
  profondeur 18, verrou : un calcul à la fois) ; l'évaluation et la barre d'avantage suivent la
  variante ; Échap / flèche gauche / clic sur la feuille = retour à la partie ; pas de pastille
  dans une variante. Test : `tests/test_variantes.py`.
- Le PC s'est déconnecté en cours de séance ; reprise à 20 h : tous les tests au vert
  (307 contrôles, 11 séries).
- Pas de commit depuis Cowork : à faire par Claude Code.

À vérifier par Julien : tests « 17/10 (4) » de la page (Mes erreurs, variantes).

## 17/10/2026 (3) – Sons des problèmes, travaux proposés (Cowork)
Retours de la page : sons des pièces validés, pastilles stables et analyse gardée validées.
Fait :
- Son de réussite des problèmes refait (« pas ouf ») : arpège de marimba sol-si-ré-sol avec une
  petite réverbération ; « pas le bon coup » = deux notes graves descendantes, sans buzzer
  (`outils/generer_sons.py` : `marimba()`, `reverb()`).
- Réponse à « pourquoi j'ai 5 zip ? » (version amis) : c'est voulu. `SickChess_amis.zip`
  (24 Mo) est le seul à donner à un ami ; les 5 autres sont les paquets que le bouton
  « Mise à jour » télécharge séparément (programme, jeu, moteur, problèmes, finales), pour
  qu'une correction ne fasse retélécharger que le petit paquet « jeu » (5 Mo).
- Page « À faire » : nouveau groupe **« Travaux proposés »** avec boutons « ★ Je veux » /
  « Pas maintenant » (statut `veux` / `non`, hors du compteur de tests). 22 propositions.
- Pas de commit depuis Cowork (consigne du skill) : à faire par Claude Code.

À vérifier par Julien : sons des problèmes ; choisir dans « Travaux proposés ».

## 17/10/2026 (2) – Pastilles stables, analyse enregistrée, vrais sons de bois
Retours de Julien sur la séance précédente : le son marche (tampon audio 1024), la précision
arrive tout de suite, la notation et la revue au début fonctionnent. Traité ensuite :
- **« Les analyses ne sont pas enregistrées, une nouvelle évaluation commence à chaque revue »** :
  l'analyse terminée est écrite à côté du PGN (`parties/<partie>.analyse.json`) et relue à
  l'ouverture (`AnalyseurPartie(fichier_cache=...)`) : plus aucun recalcul, mêmes pastilles. Le
  fichier est ignoré s'il ne correspond pas exactement à la partie ou s'il a été fait moins
  profond. Le ménage des vieilles parties efface aussi leur analyse.
- **« Les pastilles doivent être justes et pas modifiées »** : une pastille ne s'affiche qu'une fois
  les deux positions analysées en profondeur (rond d'attente avant). Le survol rapide ne sert plus
  qu'à la courbe et à la barre. La carte de fin attend l'analyse complète pour la précision.
- **« Un sacrifice n'est pas forcément un mauvais coup »** : c'était déjà le cas, le jugement compte
  la perte d'ÉVALUATION de Stockfish, pas les pièces données ; deux contrôles le prouvent
  maintenant (sacrifice juste = bon coup, sacrifice du moteur = Brillant).
- **« Les sons ne sont pas super »** : coups, prises, roque et coup illégal utilisent de vrais chocs
  de bois enregistrés (pack « Impact Sounds » de Kenney, CC0, sources et licence dans
  `assets_src/sons_kenney/`), assemblés par `outils/generer_sons.py`. Les carillons restent
  synthétisés. CREDITS.md à jour.
- Tests : `test_analyse_directe.py` passe à 28 contrôles ; tout au vert (247 contrôles).

## 17/10/2026 – Retours de Julien (page de test) : son, revue, notation
Retours lus dans la page « SickChess – À faire » et traités :
- **Son (aucun son chez Julien)** : le code charge bien les sons (déjà vrai en V8 : « 19/19
  bruitages chargés ») mais rien ne sort, donc la cause est probablement côté Windows (sortie
  audio, mélangeur de volume). Ajouts : `TESTER_LE_SON.bat` + `outils/diagnostic_son.py`
  (joue 3 sons, écrit `diagnostic_son.txt`) ; tampon audio 1024 au lieu de 512 et nouvel essai
  si le lecteur audio ne démarre pas (`game_manager._verifier_le_son`) ; **journal automatique**
  `journal_du_jeu.txt` (tout ce que le jeu affiche, remis à zéro à chaque lancement).
- **Revue « trop imprécise » (une dame donnée comptée comme imprécision)** :
  - le jugement tient compte du **matériel** en plus des chances de gagner
    (`annotations.classer`) : ≥ 1 pion perdu = au moins imprécision, ≥ 2 = erreur, ≥ 4 = gaffe,
    sauf si la position reste écrasante (+5) ; le coup du moteur n'est jamais puni ;
  - **moteur plus fort** : profondeurs 16 / 20 / 24 (normale = 20 par défaut), survol à 12,
    table de hachage 1 Go ;
  - **tables de finales Syzygy** copiées dans `syzygy/` (379 Mo, hors GitHub) : le moteur
    d'analyse les branche tout seul ;
  - **analyse pendant la partie** (demande de Julien) : Stockfish analyse en tâche de fond, sur la
    moitié des cœurs, sans rien afficher ; la carte de fin et la revue reprennent ce travail
    (`game_manager._suivre_analyse`, `AnalyseurPartie(suivi=True).ajouter_coups`).
    `"analyse_pendant_partie": false` dans config.json la coupe.
- **Revue et relecture s'ouvrent sur la position de départ** (et non plus sur le dernier coup).
- **Notation des coups au choix** : Options → Partie → Notation des coups, **anglaise par défaut**,
  française (Cf3, Fc4, Dh5) en option. Nouveau `jeu/notation.py`, appliqué à la liste des coups,
  la revue, la relecture, les problèmes et les explications. PGN et analyse restent en anglais.
- **Problèmes – promotion** : pas reproduit. Nouveau test avec les Noirs qui promeuvent (plateau
  retourné), en glissant et en cliquant : ça fonctionne. Julien précisera s'il revoit le bug.
- Décisions notées : garder Syzygy ; jeu « ultra compétitif » → analyse puissante et précise.
- Tests : nouveau `tests/test_analyse_directe.py` (22 contrôles, avec un vrai Stockfish) ;
  `test_problemes.py` + promotion des Noirs ; 234 contrôles au vert au total.

Tests ajoutés pour Julien dans la page (étapes « 17/10 · … ») : test du son, son en partie,
précision immédiate en fin de partie, gaffes justes, revue au début, notation, vitesse de
l'adversaire, promotion.

## 17/10/2026 – Outils pour travailler avec Cowork et Claude Code
Fait :
- `CLAUDE.md` à la racine : les règles du projet, lues automatiquement par Claude Code.
- `docs/A_FAIRE.md` : la liste partagée (retours de Julien, prochaines étapes, tests,
  démarches), reprise de la page « SickChess – À faire ».
- `docs/TRAVAILLER_AVEC_CLAUDE.md` : qui fait quoi entre Cowork et Claude Code.
- `tests/lancer_tous.py` : toutes les séries de tests d'un coup (`--rapide` sans Stockfish).
  180 contrôles verts en rapide.
- `.claude/` : 4 skills (`seance-sickchess`, `compiler-exe`, `verifier-echecs`,
  `captures-steam`), 2 agents (`testeur`, `relecteur-interface`), un crochet qui vérifie la
  syntaxe de chaque fichier Python modifié, et les autorisations courantes (tests, git).

À vérifier par Julien :
- [ ] Ouvrir Claude Code (onglet Code de l'application, dossier SickChess) et lui dire :
  « Lis CLAUDE.md et dis-moi la prochaine tâche ».
- [ ] Lui demander de faire le commit de cette séance.

## 17/10/2026 – Version amis + bouton « Mise à jour »
Fait :
- **CONSTRUIRE_VERSION_AMIS.bat** (→ `outils/publier_maj.py`) : fabrique l'exe avec
  PyInstaller (`outils/sickchess_amis.spec`, mode dossier, sans console), découpe le jeu en
  5 paquets (programme, jeu, moteur, puzzles, syzygy), ne garde que ceux qui ont changé,
  écrit `maj.json` et `SickChess_amis.zip` (pour un nouvel ami), et les envoie dans une
  « release » GitHub du dépôt `sick1811/SickChess-amis` (avec GitHub CLI ; sinon il dit
  quoi glisser où). Le numéro de version amis (n°1, n°2…) augmente tout seul.
- Le code (`jeu/*.py`) reste en fichiers à côté de l'exe : une correction = ~0,3 Mo à
  télécharger pour les amis, sans refaire l'exe (vérifié par une vraie compilation).
- Dans le jeu (version amis seulement) : entrée **« Mise à jour »** avant Quitter, qui
  s'allume « Mise à jour disponible ! » ; écran avec notes de version, taille, barre de
  progression, annulation. Fichiers vérifiés (SHA-256). L'installation se fait après la
  fermeture du jeu (`_maj.bat` + robocopy), puis le jeu se relance. Jamais touchés :
  config.json, profil.json, parties/, scores des problèmes, sauvegardes.
- Nouveaux fichiers : `jeu/mise_a_jour.py`, `jeu/ecran_mise_a_jour.py`,
  `docs/VERSION_AMIS.md`, `LISEZ-MOI_AMIS.txt`. `game_manager.py` : quelques lignes.
- Vérifié par `tests/test_mise_a_jour.py` (36 contrôles, faux serveur web) et une
  compilation PyInstaller d'essai (sous Linux : l'exe lit bien le code depuis le disque).

À vérifier par Julien :
- [ ] Créer le dépôt GitHub `SickChess-amis` (public) ; installer GitHub CLI
  (`winget install GitHub.cli`, puis `gh auth login`).
- [ ] Double-clic sur CONSTRUIRE_VERSION_AMIS.bat → la release n°1 apparaît sur GitHub.
- [ ] Télécharger SickChess_amis.zip, dézipper sur le Bureau, lancer SickChess.exe,
  cliquer « Mise à jour » (moteur + problèmes + finales).
- [ ] Changer une petite chose, relancer le .bat → dans le jeu dézippé, le bouton
  s'allume, la mise à jour s'installe et le jeu redémarre.

## 23/10/2026 – Boîte à outils : banc d'essai, surveillance en direct, ménage (Cowork)
Fait :
- `outils/banc_essai.py` : 7 contrôles d'un coup – bugs (tous les tests), vitesse (ms par
  image de 8 écrans + où passe le temps), processeur au repos, mémoire, Stockfish (bench),
  ménage (ruff, vulture, fichiers orphelins, ressources non citées, doublons, restes), conflits
  (marques Git, syntaxe, dépendances, travail non enregistré, verrous, réglages inconnus).
  Rapport `docs/BANC_ESSAI.md` + `tests/banc_essai.json` + historique.
- `outils/surveiller.py` : lance le jeu et mesure en direct (Windows) processeur du jeu et de
  Stockfish, mémoire, carte graphique, chaque seconde → `docs/SURVEILLANCE.md`.
- Page « SickChess – Banc d'essai » (https://claude.ai/artifact/ARYw19umG9WeUbQDVJrXe9) :
  résultats, constats à décider (Corriger / OK / Ignorer + commentaire), 8 tests de ressenti,
  historique. `outils/banc_vers_page.py` prépare la recopie.
- Outils : `requirements-dev.txt` (ruff, vulture, psutil, pyinstaller, py-spy),
  `pyproject.toml`, `outils/vulture_liste_blanche.py`.
- Skills `banc-essai`, `performance-pygame`, `menage-code` ; agent `optimiseur` ;
  `CLAUDE.md`, `seance-sickchess` et `docs/TRAVAILLER_AVEC_CLAUDE.md` mis à jour (outils,
  connecteurs, crédits).
- Premier passage (Cowork, indicatif) : 514 contrôles verts ; trouvé que Ouvertures,
  Problèmes et Statistiques relisent des fichiers à chaque image, et que les textes
  coûtent 40–60 % de chaque image (voir A_FAIRE, « Performance et ménage »).

À vérifier par Julien :
- [ ] Claude Code : « installe les outils de développement », puis « lance le banc d'essai
  complet » et « lance la surveillance en direct pendant que je joue ».
- [ ] Page Banc d'essai : décider chaque constat, remplir les 8 tests de ressenti.
- [ ] Activer les crédits d'utilisation (claude.ai → Réglages → Utilisation).
- 18h57 : `.git/index.lock` bloquait les commits. Cause : le `git status` du banc lancé depuis
  Cowork (qui ne peut pas supprimer de fichiers). Verrou supprimé par Claude Code ; le banc
  utilise maintenant `git --no-optional-locks` et la skill `banc-essai` l'impose dans Cowork.
- Vrais chiffres du PC (banc complet Windows, 18h52) recopiés dans la page : 620 contrôles
  verts ; Stockfish 6,35 M nœuds/s sur 10 fils ; partie au repos 38 % d'un cœur ;
  Ouvertures 15 ms/image. Décisions de Julien : 18 constats « corriger », 2 « ignorer »
  (fonctions peut-être mortes, `fond_anime.py`).

## 23/10/2026 (soir) – Installeur amis, mise à jour automatique, vérification en ligne (Cowork)
Demande de Julien : « un installeur .exe pour les amis qui évite les détections Windows, sur le
Bureau, et qu'on puisse jouer ensemble ; le mode en ligne est important, vérifie qu'il
fonctionne » ; puis « il se met à jour à chaque nouvelle modification ».
Fait :
- **Installeur** `SickChess_Installation.exe` (Inno Setup, `outils/installeur_amis.iss`) fabriqué et
  publié par `outils/publier_maj.py` : programme + jeu + Stockfish, installation pour l'utilisateur
  sans administrateur dans `%LOCALAPPDATA%\Programs\SickChess` (dossier où la mise à jour peut
  écrire), icône Bureau + menu Démarrer, désinstallation Windows (parties gardées).
- **Windows / antivirus, sans rien cacher** : fiche d'identité de SickChess.exe (éditeur, produit,
  version) dans `outils/sickchess_amis.spec` (sans risque : si elle échoue, l'exe se fait sans),
  installeur renseigné, exe en dossier sans UPX, signature automatique si un certificat est
  réglé (`"signature"` dans `outils/maj_config.json`). Sans certificat, « éditeur inconnu »
  reste affiché une fois (Informations complémentaires → Exécuter quand même).
- **Mise à jour automatique** : dans le menu, une version publiée se télécharge seule
  (« Mise à jour : 42 % ») puis le jeu redémarre dessus ; jamais en pleine partie ; revérifie
  toutes les 20 min ; `"maj_auto": false` pour couper. `mise_a_jour.pas_automatique` +
  `game_manager._badge_maj` ; `tests/test_maj_auto.py` (13 contrôles).
  Règle ajoutée (CLAUDE.md, skills) : Claude Code publie une version amis à la fin de chaque séance
  où le jeu a changé et où tout est vert.
- **En ligne vérifié autant que possible ici** : relecture de `jeu/steam.py` (relais de Valve,
  sessions acceptées, salons réservés aux amis) ; tests réseau verts (multijoueur 41, nulle 15).
  **Piège trouvé** : avec le numéro de test 480, accepter une invitation quand SickChess est fermé
  fait lancer « Spacewar » par Steam → l'ami ouvre SickChess d'abord (ou tape le code). Doc et
  LISEZ-MOI_AMIS corrigés. Nouveau `outils/verifier_en_ligne.py` (fichiers, Steam, salon + code,
  tests réseau) à lancer sur Windows → `docs/VERIFICATION_EN_LIGNE.md`.
- Skill `version-amis` (fabriquer, installer l'essai en silence, vérifier, publier). Recette :
  R-106, R-107, R-113, R-114 (106 tests). 550 contrôles rapides verts (Cowork).

À vérifier par Julien (page « À faire », v01 à v04) :
- [ ] Claude Code : installer Inno Setup + GitHub CLI ; « Vérifie le jeu en ligne » ;
  « Fais la version amis avec l'installeur, vérifie-la, puis publie ».
- [ ] Une vraie partie en ligne avec un ami sur deux PC.

## 24/10/2026 (25) – Installeur complet ; analyse libre, invitations, classements à faire (Cowork)
Retour de Julien sur la version installée : « il reste beaucoup d'éléments manquants : les problèmes,
l'analyse en partie, Steam ». Précisé : installeur → tout dedans ; analyse = **analyse libre** ;
Steam = **succès et classements** + **notification en jeu de l'invitation d'un ami**.
Cause pour les problèmes : l'installeur n° 2 n'avait que programme + jeu + Stockfish, problèmes et
finales (~600 Mo) arrivaient ensuite par la mise à jour automatique.
Fait :
- `outils/publier_maj.py` : installeur **complet** (programme, jeu, Stockfish, problèmes, finales,
  ~700 Mo ; `SICKCHESS_INSTALLEUR_LEGER=1` pour l'ancien) ; option **`--installeur-seul`** (refait
  l'installeur de la dernière version publiée et le remplace dans sa release, refuse si le jeu a
  changé). Essayé avec un faux Inno Setup : contenu et `paquets_installes.json` justes.
- `outils/installeur_amis.iss` : compression normale non solide (données déjà compressées).
- Docs (VERSION_AMIS, LISEZ-MOI_AMIS, skill version-amis) mises à jour.
- Nouveaux travaux dans A_FAIRE (en premier) et la page : p35 analyse libre, p36 invitation
  affichée dans le jeu (rappel Steam LobbyInvite_t), p37 classements Steam (testables avec 480) +
  succès Steam préparés (affichage dans Steam seulement avec le vrai numéro, p21).
À faire par Julien (page « À faire ») :
- [ ] v05 : Claude Code refait l'installeur complet ; réinstaller et vérifier Problèmes / finales.
- [ ] Puis « fais le travail p35 », p36, p37.

## Bugs connus (repris de « a debug.txt »)
- [x] Pendule ne clignote pas à 30 s → fonctionne (testé).
- [x] Fin de partie à 00:00 → corrigé (affichage du temps final).
- [x] Son : réglé le 17/10 (tampon audio) ; sons de bois enregistrés à juger.
- [ ] Animation lente (réglable : `vitesse_animation` dans config.json, 0.18 s).
- [ ] Temps de réflexion de Stockfish pas assez humain.
- [x] Organisation de la fenêtre de jeu : disposition « Classique » retenue (plateau à gauche, panneau à droite).

## Fonctions de V8_TURBO_3000 à réintégrer (dans cet ordre)
1. Compilation en .exe : version amis faite (CONSTRUIRE_VERSION_AMIS.bat). Reste : version
   Steam / itch.io (données du joueur dans %APPDATA%, version_info pour Windows Defender).
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

## 17/10/2026 (5) – Recette complète
Fait :
- `docs/RECETTE.md` : la liste de tous les tests à faire à la main pour vérifier le jeu
  entier (71 tests, 14 parties : lancement, partie, règles, pendule, fin et revue, mes
  parties, problèmes, options, en ligne, version amis, solidité, graphisme).
- Une seule source : `outils/recette.py` fabrique RECETTE.md et `outils/recette.json`.
- Page « À faire » : nouveau groupe « Recette complète » (Fonctionne / Ne fonctionne pas
  + commentaire), compté à part, avec un bouton « Nouvelle passe » qui remet tout à tester.
- Règle ajoutée dans CLAUDE.md et dans la skill `seance-sickchess` : chaque fonction
  touchée met à jour sa recette ; passe complète avant chaque version.
- `tests/lancer_tous.py` : les séries `test_mes_erreurs` et `test_variantes` y sont déclarées.

À vérifier par Julien :
- [ ] Ouvrir la page « À faire » : le groupe « Recette complète » s'affiche en bas avec ses 14 parties.
- [ ] Faire une première passe complète de la recette.

## 17/10/2026 (6) – Première passe de la recette par Claude
- Tous les tests automatiques passent (216 contrôles rapides + revue, analyse, Mes erreurs,
  variantes avec Stockfish). 28 lignes de la recette cochées « Vérifié par Claude » dans la page.
- Défaut trouvé sur les captures (R-130) : le chiffre de la barre d'avantage de la revue
  était coupé (« -0… »). Barre élargie (18 px minimum), chiffre sans signe et à une décimale
  (« 0.3 », « M3 ») : le côté de la barre dit déjà qui est mieux. `jeu/ecran_revue.py`.
- Reste pour Julien : 43 lignes (sons, sensations, F11, Steam réel, version amis, solidité).

## 17/10/2026 (7) – Recette passée par Claude sur le PC de Julien (contrôle de l'ordinateur)
Lignes vérifiées en jouant pour de vrai : lancement, F11, fenêtre, F1, réglages, partie contre
l'ordinateur avec les Noirs, partie à deux, glisser / clic-clic, coup illégal, petit roque, prise
en passant, promotion en cavalier, échec, répétition triple, clic droit, incrément, sans limite,
Rejouer, reprise, revue d'une vraie partie, Options, Mes parties, Ouvrir le dossier, un problème
classé, Stockfish absent. 51 lignes de la recette validées en tout.
Bugs trouvés et corrigés :
- **Plein écran** : le jeu se réduisait et revenait tout noir dès qu'une autre fenêtre passait
  devant → `SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS=0` dans `SickChess.py` (revérifié sur le PC).
- **Aucun moyen de revenir au menu en pleine partie** (seulement Abandonner) → bouton MENU à côté
  d'Abandonner (`game_buttons.py`), la partie est gardée et se reprend. Contrôle ajouté dans
  `tests/test_noyau.py` (4 bis).
- « 1 minutes par joueur » → « 1 minute » (`settings_screen.py`) ; « SUR ? » → « SÛR ? » ;
  « n'a pas pu demarrer » → « démarrer » ; « Stockfish 400 Elo » → « Ordinateur 400 Elo »
  dans le panneau (`board_render.py`).
- Courbe Elo de « Mes parties » : le chiffre du bas était caché par le dernier point.
Remarques pour Julien (pas changées) : pièces prises minuscules en grand écran ; l'ordinateur
répond très vite même en « Humain » ; fond de l'aide F1 trop transparent.
Recette : R-051 renommé (« Bouton MENU »).

## 17/10/2026 (8) – Travaux choisis par Julien : pause, fautes expliquées, défis, adversaire, signaler
- **Menu pause** (p10, `jeu/menu_pause.py`) : Échap en partie → Reprendre, Options (sans quitter
  la partie), Proposer la nulle (à deux : acceptée ; contre l'ordinateur : refusée avant le 15e
  coup ou s'il est mieux, acceptée si c'est égal ou s'il est moins bien), Abandonner (deux clics),
  Retour au menu (partie gardée). La pendule s'arrête. Test : `tests/test_pause.py`.
- **Fautes expliquées dans la revue** (p03, `jeu/explication_revue.py`) : une phrase sous la
  pastille (« Ce coup laisse ton cavalier sans défense », « Tu avais un mat en un coup »,
  « Il y avait une fourchette sur le roi et la tour »…). **Règle de Julien : jamais le coup.**
  Test : `tests/test_explication_revue.py` (vérifie aussi qu'aucun coup n'est écrit).
- **Défis de problèmes** (p07, `jeu/modes_problemes.py`) : Contre la montre (3 min, difficulté
  qui monte), Survie (3 vies), Problème du jour (même problème toute la journée, série de jours).
  Records dans `modes_problemes.json` (hors GitHub). Test : `tests/test_modes_problemes.py`.
- **Adversaire plus humain** (p08, `rythme.py`, `background_ai.py`) : reprise évidente rapide,
  plus long quand des pièces sont menacées ou qu'il y a beaucoup de prises / échecs, jamais
  sous 0,35 s avec plus d'une minute. Test : `tests/test_adversaire.py`. Styles : pas encore.
- **Signaler un problème / une idée** (p16, `jeu/signalement.py`, `jeu/ecran_signaler.py`) :
  entrée du menu ; rapport avec version, système et fin du journal ; envoi direct sur Discord si
  une adresse webhook est réglée (`signalement.json`, hors GitHub), sinon rangé dans `rapports/`,
  dossier ouvert et texte copié. Test : `tests/test_signaler.py`.
- Recette : R-015, R-055 à R-057, R-06A, R-087 à R-089, R-095, R-096. 290 contrôles rapides verts.

## 17/10/2026 (9) – Import PGN, nulle en ligne, statistiques, ouvertures, accueil, sons et musique
- **Import de parties** (p18, `historique_parties.importer`) : Mes parties → « Importer (PGN) »
  lit le presse-papiers (texte PGN ou lien lichess, téléchargé) ; un fichier .pgn glissé sur la
  fenêtre marche aussi ; la revue s'ouvre ; pastille PGN ; l'Elo ne bouge pas. Test : `test_import_pgn.py`.
- **En ligne** (p18) : le bouton MENU devient **NULLE** (proposer / accepter ; un coup joué
  oublie la proposition) ; chaque partie en ligne finie entre dans Mes parties (avec revue).
  Test : `test_en_ligne_nulle.py`. Spectateurs : pas encore.
- **Statistiques** (p05, `statistiques.py`, `ecran_statistiques.py`) : Mes parties → Statistiques.
  Test : `test_statistiques.py`.
- **Entraînement aux ouvertures** (p06, `entrainement.py`, `ecran_entrainement.py`, entrée du menu) :
  83 ouvertures, lignes tirées au hasard dans la famille (les déviations), progression dans
  `entrainement.json`. Test : `test_entrainement.py`.
- **Premier lancement guidé** (p11, `premier_lancement.py`) : nom, niveau, trois choses à savoir ;
  jamais chez un profil qui a déjà des parties. Test : `test_premier_lancement.py`.
- **Sons** (p15) : packs Bois / Feutre (`sounds/feutre/`, généré) / Muet sauf alertes. **Musique** (p14) :
  `music/calme.wav` synthétisée (32 s en boucle), menu / problèmes / entraînement, jamais en partie,
  touche M. `outils/generer_sons.py --feutre --musique`. Test : `test_sons_musique.py`.
- **Bugs trouvés en route** :
  - le bouton « Mes erreurs » réécrivait les analyses enregistrées en « profondeur 16 » : la revue
    suivante refaisait toute l'analyse. Corrigé (`analyse_partie.py`), test `test_cache_analyse.py`.
    Tes analyses existantes sont marquées 16 : elles seront refaites une fois, puis gardées.
  - `test_multijoueur.py`, `test_problemes.py` et `test_modes_problemes.py` écrivaient dans tes
    vraies parties : ils travaillent maintenant dans un dossier temporaire (4 parties « Julien-Paul »
    de test retirées de parties/).
- Recette : ordre par section (ajouter un test ne décale plus toute la liste). 418 contrôles rapides verts.

## 17/10/2026 (10) – Effets, succès, le jeu en anglais
- **Effets** (p13, `effets.py`) : onde sur la case d'une prise, halo et confettis au mat, fondu doux
  entre les écrans (coupé sans écran, pour les captures des tests). Test : `test_effets.py`.
- **Succès** (p19, `succes.py`) : 14 succès dans `succes.json`, message à l'écran quand on en débloque un,
  vue Statistiques → Succès ; `steam.debloquer_succes` prêt (identifiants dans `docs/SUCCES_STEAM.md`).
  Manquent les icônes Steam (64×64, couleur + gris). Test : `test_succes.py`.
- **Anglais** (p12, `langue.py` + `langue_en.py`, ~670 textes) : traduction au moment de dessiner
  (`ui.texte`, `texte_centre_dans`, `paragraphe`), gabarits avec nombres, majuscules du menu ;
  noms d'ouvertures lichess en anglais. Options → Affichage → Langue. Sans réglage, le jeu suit la
  langue de Windows (français si Windows est en français). Test : `test_anglais.py` ;
  `test_entrainement.py` force le français (la machine de test est en anglais).
- **Bug** : les boutons Importer et Statistiques de Mes parties n'étaient pas dessinés. Corrigé.
- Recette : R-078, R-132, R-09C. 443 contrôles rapides verts.
- Reste à faire : styles de jeu de l'ordinateur (p08), spectateurs en ligne (p18), classements et
  icônes de succès Steam, adresse du webhook Discord pour Signaler.

## 17-18/10/2026 (11) – Revue refaite : Stockfish ne joue plus, analyse à la profondeur 30
Retour de Julien : « dans la revue Stockfish joue les coups au lieu de proposer les meilleurs avec des
flèches ; les stats ne sont pas fiables (comparées à chess.com) ; il faut une analyse très précise et
beaucoup plus rapide ; profondeur 30 ».
- **Revue** (`ecran_revue.py`) : Stockfish ne joue JAMAIS. Flèches bleues = meilleur coup de la position
  affichée et coups aussi bons (moins de 2 points de chances d'écart, ~0,1 pion) ; flèche verte = ce qu'il
  fallait jouer après une faute (gardée). Variante : on joue les deux camps, flèche gauche annule un coup,
  Échap revient. « Meilleur ici : … » + suite prévue. Feuille : évaluation après chaque coup, colorée.
  Touche B : flèches ; bouton/touche E : Exporter. La précision ne s'affiche qu'une fois l'analyse finie.
- **Export** (`export_revue.py`) : PGN avec [%eval], NAG (!!, !, ?!, ?, ??), meilleur coup en variante pour
  les fautes, WhiteAccuracy/BlackAccuracy ; dans exports/ + presse-papiers.
- **Analyse** (`analyse_partie.py`) :
  - profondeur 30 par défaut (« maximale ») : survol (10), trois meilleurs coups à 22, puis passe profonde
    à 30 (meilleur coup seul : 3 fois moins cher). Pastilles et précision attendent la passe à 30.
    Option : Options → Partie → Profondeur de l'analyse (18 / 22 / 26 / 30) ;
  - profondeur réellement atteinte enregistrée ; position refaite une fois avec 2× plus de temps si
    elle manque de 2 ; la revue affiche la plus petite profondeur atteinte ;
  - jusqu'à 3 moteurs en parallèle après la partie (1 pendant la partie) ;
  - analyse enregistrée format 2 (3 meilleurs coups + profondeurs) ; les anciennes sont refaites à la
    revue (les statistiques les acceptent encore).
- **Précision** : exactement la méthode lichess (évaluations bornées à 10 pions, bonus +1, poids par
  fenêtre glissante, moyenne pondérée + harmonique). chess.com a sa formule secrète (CAPS2) : on ne peut
  pas l'égaler au chiffre près.
- **Pastilles** (`annotations.py`) : seuils corrigés à ceux publiés par chess.com (5 / 10 / 20 points de
  chances) — l'ancienne lecture de lichess était fausse d'un facteur 2 ; le matériel perdu ne fait plus
  monter qu'à Erreur (h3 contre dragondu5 : chess.com « Erreur », nous « Gaffe » avant). Comparaison sur
  cette partie : gaffes 1 (chess.com 1, avant 3), 7.Qe2 ??, 10.h3 ?, 15.Qb3 ?, 7...Bxa1 ! identiques.
- **Stockfish** (`engine.py`) : une borne (lowerbound/upperbound) ne remplace plus un score exact ; toutes
  les lignes MultiPV et leur suite sont rendues. Tables Syzygy : déjà branchées (dossier syzygy/).
- Tests : `test_variantes.py` réécrit, `test_analyse_profonde.py` (nouveau), `test_cache_analyse.py`,
  `test_analyse_directe.py` mis à jour. 458 contrôles rapides verts + revue, variantes, mes erreurs.
- Recette : R-067 modifié, R-06B à R-06E, R-09D.
- **À vérifier par Julien** : temps de la revue à profondeur 30 sur son PC (sur 2 cœurs : 7 à 23 s par
  position) ; si c'est trop long, régler 26 dans Options.

## 18/10/2026 (12) – Vitesse maximale, Stockfish 19 testé
- PC de Julien : i7-8700K (6 cœurs, 12 processeurs logiques, AVX2 + BMI2). Le stockfish.exe installé
  (17.1, version « bmi2 ») est déjà la compilation la plus rapide pour ce processeur.
- Après la partie : 3 moteurs × 4 threads = les 12 processeurs logiques ; table de hachage 2 Go
  partagée (`analyse_partie.py`).
- **Stockfish 19** (05/09/2026, +44 Elo sur la 18) testé avec le jeu (version Linux, même options UCI) :
  revue, variantes, analyse directe et adversaire de 400 à 3190 Elo fonctionnent. MAIS pour atteindre
  la même profondeur il lui faut 4,5 fois plus de temps (9 positions de la partie contre dragondu5, profondeur
  24 : 17 s pour la 17.1, 79 s pour la 19). Avec une analyse « à profondeur 30 », la 19 serait donc
  beaucoup plus lente. **Décision : on garde la 17.1** ; la version Windows de la 19 n'a pas été téléchargée.
  À reconsidérer si on passe un jour à une analyse au temps (et non à la profondeur).

## 18/10/2026 (13) – Analyse : calcul fixe par défaut, profondeur et temps au choix (Cowork)
Question de Julien : analyse à la profondeur (30) ou au temps ? Mesure faite d'abord sur sa partie contre
dragondu5 (Stockfish 17.1, ordinateur de test Linux à 2 processeurs) :
- la profondeur 30 coûte de **3 à 78 millions de nœuds** selon la position (25 fois d'écart, moyenne
  ≈ 28 millions) : c'est pour ça que la durée d'une revue « à la profondeur » est imprévisible ;
- entre la profondeur 22 et la 30, l'évaluation bouge de **0,05 pion** en position équilibrée, moins de
  0,3 pion quand la partie est jouée : les pastilles ne changent presque jamais ;
- lichess n'analyse ni à la profondeur ni au temps, mais avec un **nombre de nœuds fixe** par position
  (exemple de son protocole fishnet : profondeur 18, 1,7 million de nœuds).

**Décision de Julien : plusieurs modes, le calcul fixe par défaut.**
- `analyse_partie.py` : `REGLAGES` = 3 modes × 3 puissances (config `analyse_mode` + `analyse_niveau`,
  lus par `puissance_de(config)` ; l'ancien `analyse_puissance` donne le niveau) :
  - **Calcul fixe** (défaut) : 10 / 25 / **50 millions** de nœuds par position (passe des trois meilleurs
    coups : un cinquième). Même analyse sur tous les PC, durée prévisible, une version plus récente de
    Stockfish compte pour ce qu'elle vaut. 50 millions = profondeur 28 à 33 ; c'est environ 2 fois le
    calcul moyen de l'ancienne profondeur 30, réparti également (aucune position bâclée).
  - **Profondeur** : 22 / 26 / 30 (comme avant ; Maximale = l'ancienne profondeur 30).
  - **Temps** : 3 / 7 / 15 s par position, refaite une fois avec le double si la profondeur minimale
    (22 / 26 / 26) n'est pas atteinte.
  - Les anciens noms (« rapide », « maximale »…) restent acceptés (Mes erreurs, statistiques).
- **Analyses enregistrées** : comparées par un « effort » de 1 à 5 (enregistré avec le réglage), plus par
  la profondeur. Une analyse à la profondeur 30 vaut le calcul fixe maximal : **changer de mode ne refait
  pas les parties déjà analysées**. Une ancienne analyse à 26 est refaite en Maximale.
- **Temps restant** affiché dans la revue et sur la carte de fin : « Analyse fine… 40 % · environ 3 min »
  (vitesse réelle de Stockfish mesurée pendant l'analyse) ; à la fin « Analyse terminée (profondeur X à Y) ».
- `engine.py` : `go nodes`, et chaque recherche rend les nœuds et le temps vraiment utilisés.
- Variante dans la revue : réglage de la passe des meilleurs coups (rapide) ; une fois l'analyse de la
  partie finie, tous les processeurs sauf un (le « 1 × 12 » du tableur de Julien) au lieu de 2.
- Options → Partie : « Façon d'analyser » (Calcul fixe / Profondeur / Temps) et « Puissance de l'analyse »
  (Rapide / Forte / Maximale), en français et en anglais. Export : l'en-tête dit le réglage et les profondeurs.
- **Outil de mesure** `outils/mesurer_stockfish.py` (à lancer par Claude Code sur Windows, 10-15 min) :
  1 × 12, 3 × 4, 6 × 2, 12 × 1 sur la partie contre dragondu5 au même budget → temps total, temps de la
  première position, profondeur atteinte, nœuds/s, durée d'une revue par réglage → `docs/MESURE_STOCKFISH.md`.
- **Hachage : 6 Go** (demande de Julien : « JE VEUX 6 GO DE HACHAGE ») – total de l'analyse, partagé
  entre les moteurs prévus après la partie (3 × 2 Go sur son PC), y compris pendant la partie (2 Go pour
  le seul moteur, pour ne jamais dépasser 6 Go quand les deux autres arrivent). Garde-fou pour les PC des
  acheteurs : au plus la moitié de (mémoire − 4 Go) → 16 Go de mémoire = 6 Go, 8 Go = 2 Go. Stockfish
  reçoit la taille exacte (plus d'arrondi à la puissance de 2). Avant : 2 Go (512 Mo par moteur).
- Remarques sur le tableur de Julien : (1) le code était à 2 Go, pas 6 Go (corrigé ci-dessus) ; (2) les chiffres « 6,3 » et « 9,4 » venaient de commentaires de V8, jamais mesurés
  sur son PC, et 9,4 dépasse le plafond théorique de 7,5 calculé dans le tableur : à remplacer par la mesure.
- Tests : `tests/test_modes_analyse.py` (nouveau, 47 contrôles dont le hachage dont `go nodes` avec un vrai Stockfish),
  `test_analyse_profonde.py` et `test_analyse_directe.py` mis à jour. 505 contrôles rapides verts +
  revue, variantes, analyse directe, mes erreurs (Stockfish 17.1 Linux).
- Recette : R-06E modifié, R-06F, R-06G, R-09E nouveaux, R-09D retiré (101 tests).

À vérifier par Julien :
- [ ] t64 à t66 (revue, flèches, comparaison chess.com) – toujours à faire.
- [ ] t67 : temps réel d'une revue complète en Calcul fixe Maximale (estimation : 6 à 10 min pour 40 coups
  analysés de zéro sur l'i7-8700K ; moins si l'analyse a tourné pendant la partie). Trop long → Forte.
- [ ] t68 : Options → Façon d'analyser / Puissance ; une partie déjà analysée n'est pas refaite.
- [ ] t69 : Claude Code lance `python outils/mesurer_stockfish.py`. Selon le résultat, on règlera la
  répartition (aujourd'hui 3 × 4) et, si besoin, la puissance par défaut.
- Claude Code : commit de la séance (13) après `python tests/lancer_tous.py`.

Mesure faite par Claude Code sur le PC de Julien (i7-8700K, `docs/MESURE_STOCKFISH.md`, 20 positions,
50 millions de nœuds) : 1 × 12 = 191 s, 3 × 4 = 195 s, 6 × 2 = 207 s, 12 × 1 = 253 s ; 4,7 millions de
nœuds/s au mieux. 1 × 12 et 3 × 4 sont à égalité (2 % d'écart), mais la première position sort bien plus
vite en 1 × 12 (27 s contre 46 s). Revue estimée pour 80 positions : Rapide 3,4 min, Forte 8,6 min,
Maximale 17,1 min (plus que les 6 à 10 min prévues). À décider : réglage par défaut Forte, ou 1 × 12.
Tests : `python tests/lancer_tous.py` → 611 contrôles verts. Commit de la séance (13) fait.

## 18/10/2026 (14) – Analyse « Forte » par défaut (Claude Code)
Fait :
- Décision de Julien après la mesure : **puissance Forte par défaut** (25 millions de nœuds par
  position, revue d'environ 9 min au lieu de 17 pour 40 coups) et **répartition 3 × 4 gardée**.
- `analyse_partie.py` (`PUISSANCE_PAR_DEFAUT`, `puissance_de`) et `ecran_options.py` : Forte par défaut.
  L'ancien réglage seul (`analyse_puissance` « maximale », mis par défaut le 17/10) donne maintenant Forte.
- `config.json` de Julien : `analyse_mode` calcul, `analyse_niveau` forte ajoutés.
- Tests : `test_modes_analyse.py`, `test_analyse_profonde.py` mis à jour. Recette : R-09E modifié.

À vérifier par Julien :
- [ ] t67 : durée réelle d'une revue en Forte (environ 9 min prévues pour 40 coups).
- [ ] t68 : Options → Partie → Puissance de l'analyse affiche « Forte ».


## 18/10/2026 (15) – Hachage 4 Go (Cowork)
- Julien, après explication (au-delà de 4 Go, aucun gain visible pour ces analyses ; 8 Go demanderait
  32 Go de mémoire vive) : **« OK 4 »**. `HASH_ANALYSE_MB` = 4096 (au lieu de 6144) : 3 × 1,3 Go sur
  l'i7-8700K. Le garde-fou reste : jamais plus de la moitié de (mémoire − 4 Go) sur un petit PC.
- `tests/test_modes_analyse.py` et `outils/mesurer_stockfish.py` alignés. 506 contrôles rapides verts.
- Claude Code : commit de la séance (15).

## 18/10/2026 (16) – Revue : bug des threads, vérification ciblée (Cowork)
Retour de Julien : « 35 MIN POUR 70 COUPS ?? », puis « plus précise que maintenant et quasiment
instantanée ». Question : « peut-on utiliser le moteur de lichess pour la rapidité ? »
- **Bug corrigé (journal du jeu de Julien)** : les trois Stockfish d'analyse avaient 11, 6 et 4 threads
  (21 pour 12 processeurs) : le nombre dépendait de l'ordre de démarrage. Maintenant on partage selon le
  nombre de moteurs PRÉVUS (3 × 4 = 12), et un moteur qui finit la partie avec 6 threads repasse à 4.
- **Vérification ciblée** (mode Calcul fixe) : toutes les positions reçoivent une analyse rapide (trois
  meilleurs coups, 2 / 3 / 5 millions de nœuds), puis SEULS les coups dont la pastille hésite sont vérifiés
  en profondeur (15 / 25 / 50 millions) : perte à moins de 3 points d'un seuil (5 / 10 / 20), à moins de
  0,3 pion des seuils en pions, candidat Très bien / Brillant / Manque (`_coup_sur`). Ailleurs, la
  pastille est déjà sûre. Plus de passe profonde non plus pour les mats et la théorie (pas pour une
  partie qui ne commence pas à la position de départ).
- Mesure sur la partie contre dragondu5 (Stockfish 17.1, Forte) : **11 positions vérifiées sur 39** ;
  comparé à l'analyse complète Forte de la nuit (25 millions partout) : aucune pastille de faute ne
  change (Imprécision / Erreur / Gaffe identiques) ; 5 nuances Meilleur / Excellent / Bon sur des coups
  presque équivalents (Stockfish lui-même varie d'une analyse à l'autre là-dessus) ; précision
  65,0 / 63,9 (Blancs) et 93,7 / 92,4 (Noirs). Le raccourci « partie jouée à 8 pions » essayé d'abord a
  été retiré : il faisait passer 12...d4 d'Imprécision à Excellent (règle du matériel perdu).
- Durée estimée sur l'i7-8700K (4,7 millions de nœuds/s mesurés) pour 70 coups : Forte ≈ **5 min**
  (avant : ≈ 15 min, plus le bug) ; la courbe, les flèches et ~70 % des pastilles après ≈ 1,5 min.
  Une partie jouée dans SickChess est analysée pendant qu'on joue : la revue est prête à la fin.
- Temps restant : compte seulement les positions à vérifier ; vitesse mesurée sur les vraies recherches
  (≥ 1 million de nœuds) ; recalculé une fois par seconde.
- **Moteur de lichess** : c'est Stockfish, le même. Sa rapidité vient de milliers d'ordinateurs bénévoles
  et d'un budget plus petit (~2 millions de nœuds par position). Son API « cloud-eval » ne rend que des
  positions déjà analysées sur le site (surtout des ouvertures, déjà « Théorique » chez nous), demande
  Internet et est faite pour « quelques positions ici et là » : pas de gain pour la revue.
- Tests : `test_modes_analyse.py` (56 contrôles : vérification ciblée, threads, théorie), `test_analyse_profonde.py`
  adapté. Séries rapides vertes + revue (32), variantes (19), mes erreurs (18), analyse directe (34).
- Recette : R-06F, R-09E modifiés ; R-06H nouveau (102 tests).

À vérifier par Julien :
- [ ] t67 : revue d'une longue partie importée en Forte : temps réel (≈ 5 min prévues pour 70 coups) ?
- [ ] t71 : pendant la revue, les ronds creux se remplissent ; une pastille posée ne change plus.
- Claude Code : commit de la séance (16) après `python tests/lancer_tous.py`.


## 23/10/2026 (17) – Banc d'essai : constats « Corriger » (Claude Code)
Fait (mesuré sur le PC de Julien, i7-8700K, avant → après) :
- **Fichiers relus à chaque image** : la progression des ouvertures (`entrainement.py`, 24 lectures par
  image) et les records des défis (`modes_problemes.py`, 3 par image) sont lus une fois puis gardés en
  mémoire, mis à jour à chaque enregistrement. Ouvertures 14,9 → 11,0 ms/image, Problèmes 7,6 → 6,6.
- **Textes gardés en mémoire** (`ui.py`) : mesures, textes rognés et textes dessinés ne sont plus refaits à
  chaque image (vidés quand la police change). Toutes les images sous 5 ms sauf la Revue :
  Partie 6,6 → 3,5 · Revue 9,1 → 5,3 · Options 9,8 → 3,4 · Mes parties 14,3 → 4,2 · Ouvertures → 1,8 ·
  Problèmes → 1,1 ms.
- **Partie au repos** (`game_manager.cadence_de_partie`) : 60 images/s pendant 1,5 s après un geste, un coup,
  une animation ou la pause ; 30 sinon. Processeur au repos : 42 → 17 % d'un cœur (menu 8 → 4 %).
  Le banc mesure maintenant avec la vraie cadence du jeu.
- **Ménage** : 4 imports et 4 variables inutiles retirés ; 43 valeurs rangées mais jamais relues retirées
  (13 fichiers) ; 4 fausses alertes (champs Windows, commentaires PGN, position d'un rectangle) ajoutées à
  `outils/vulture_liste_blanche.py`. `ia_suivre_la_pendule` retiré de config.json (le jeu suit toujours
  la pendule).
- `outils/banc_essai.py` : Stockfish trouvé sous Windows (chemin complet).
- Pas corrigés, volontairement : **fichiers en double** (le même son de nulle sous trois noms, voulu par
  `generer_sons.py` ; deux images Steam de même taille, exigées séparément par Steam) → à passer en « OK ».
  **Restes sur le disque** (`publier/` 720 Mo, `build_amis/` 52 Mo) et **push** : attendent l'accord de Julien.
- Tests : `test_entrainement.py`, `test_modes_problemes.py` (fichier lu une seule fois), `test_pause.py`
  (cadence). `python tests/lancer_tous.py` → 634 contrôles verts. Banc complet : rien en rouge.

À vérifier par Julien :
- [ ] t72 : partie contre l'ordinateur : tout reste fluide (pièces, flèches, pendule, coups de l'ordinateur).
- [ ] t73 : Gestionnaire des tâches → SickChess pendant une partie où personne ne joue : bien moins qu'avant.
- [ ] t74 : Ouvertures et Problèmes : la progression et les records s'affichent et se mettent à jour.

## 23/10/2026 (18) – Banc d'essai : derniers constats « Corriger » (Claude Code)
Fait (PC de Julien, banc complet avant → après) :
- **Revue** 5,3 → 2,5 ms/image : meilleurs coups gardés en mémoire (`analyse_partie.meilleurs_depuis_lignes`,
  calculés deux fois par image avant) ; flèches gardées en mémoire, rognées à leur taille (`board_render._fleche`).
- **Partie** 3,5 → 1,9 ms/image, **processeur au repos 17 → 9 % d'un cœur** : damier uni dessiné une fois ;
  coordonnées par la mémoire des textes (`ui.rendu_texte`) ; surlignages (dernier coup, sélection, coups
  possibles) repeints seulement quand ils changent, et seules les cases concernées recopiées.
- Captures vérifiées : plateau, surlignages et coordonnées identiques à avant (a1 sombre, h1 clair).
- `publier/` et `build_amis/` supprimés (770 Mo, accord de Julien) ; `publier/maj.json` gardé (numéro de la
  version amis suivante).
- Banc complet : **tout vert** sauf Ménage (orange, rien de marqué « Corriger » hormis les fichiers en double,
  voulus). 634 contrôles verts.
- Reste à Julien : passer « Fichiers en double » en OK ; dire quand pousser (4 commits d'avance).

À vérifier par Julien :
- [ ] t75 : revue : flèches des meilleurs coups, surlignages et pastilles comme avant ; défilement fluide.
- [ ] t76 : partie : cliquer une pièce montre ses coups possibles ; le dernier coup reste surligné ;
  plateau retourné (F) correct.

## 23/10/2026 (19) – Surveillance en direct : trois corrections (Claude Code)
Première surveillance sur le PC de Julien (`docs/SURVEILLANCE.md`, 14 min : une partie puis sa revue) :
pendant la revue, 4 Stockfish d'analyse + le moteur de jeu, PC à 100 %, 6,8 Go de mémoire pour Stockfish ;
après la revue, 5,8 Go gardés jusqu'à la fermeture du jeu ; le jeu seul à ~30 % d'un cœur dans les menus.
Fait :
- **Stockfish d'analyse en priorité basse** (`moteurs._priorite_basse`, Windows : BELOW_NORMAL) : l'analyse prend
  tout ce qui est libre, mais le jeu passe avant et reste fluide. Moteur des variantes de la revue : 1 thread
  tant que l'analyse tourne (2 avant), les 12 processeurs étant déjà pris par 3 × 4.
- **Moteurs fermés** : à la fin de l'analyse, les moteurs de renfort (analyse-2, analyse-3, ~1,3 Go chacun) sont
  fermés (`moteurs.liberer_les_renforts`) ; en quittant la revue, le moteur des variantes aussi. Le premier
  moteur d'analyse et le moteur de jeu restent (revanche, deuxième analyse rapide).
- **Menus et écrans à 30 images/s au repos** (`ui.Cadence`) : menu, revue, options, mes parties, problèmes,
  revoir, statistiques, ouvertures, signaler ; 60 pendant 1,5 s après un geste ou pendant une animation.
- Tests : `test_modes_analyse.py` (moteurs fermés, priorité basse vérifiée sur un vrai Stockfish),
  `test_pause.py` (cadence). 644 contrôles verts.

À vérifier par Julien :
- [ ] t77 : relancer la surveillance (« lance la surveillance en direct »), jouer une partie puis sa revue :
  jeu fluide pendant l'analyse ; après la revue, la mémoire de Stockfish redescend (≈ 2 Go au lieu de 5,8).

## 23/10/2026 (20) – Version amis n° 1 publiée (Claude Code)
Fait :
- Inno Setup 6.7.3 et GitHub CLI 2.103.0 installés (winget) ; Julien connecté à GitHub (`gh auth login`).
- Vérification en ligne (Steam ouvert, compte Sick) : fichiers, connexion, salon, réseau → tout ✅,
  depuis les sources puis sur la version installée.
- Le dépôt `sick1811/SickChess-amis` n'existait pas : l'ancienne « n° 1 » du 17/10 n'avait jamais été
  publiée (son `publier/maj.json` mis de côté). Dépôt créé (public, avec un README), version **n° 1**
  publiée : programme, jeu, moteur, problèmes, finales, zip et installeur (90,5 Mo).
- Installeur vérifié avant l'envoi : installation silencieuse dans un dossier d'essai, jeu lancé 25 s sans
  erreur (Steam connecté, Stockfish prêt), vérification en ligne ✅, désinstallation propre.
- Aucun fichier personnel dans les paquets (config.json, profil.json, parties…).
- Lien pour un ami : https://github.com/sick1811/SickChess-amis/releases/latest/download/SickChess_Installation.exe

À vérifier par Julien :
- [ ] R-102 à R-107 : vraie partie en ligne avec un ami (il installe, ouvre SickChess AVANT d'accepter
  l'invitation).

## 23/10/2026 (21) – En ligne : fin de partie et revue comme contre l'ordinateur (Claude Code)
Demande de Julien : « rajoute toutes les fonctionnalités pour les fins de partie et de revue pour le mode
Steam online, comme contre le bot ».
Fait :
- **Carte de fin en ligne** (`partie_en_ligne.EcranFinEnLigne`, reprend `ecran_fin.EcranFin`) : résultat,
  raison, **précision « toi / ton ami »**, boutons **Revue de la partie**, Revanche, Menu.
- **Analyse pendant la partie** en ligne aussi (en silence, moitié des cœurs, réglage « analyse pendant la
  partie » respecté) ; à la fin, elle est reprise et rangée à côté du PGN (`<partie>.analyse.json`) :
  la partie compte dans les **Statistiques** et ses fautes dans **« Mes erreurs »**.
  (`game_manager.brancher_analyse`, partagé avec les parties contre l'ordinateur.)
- **Revue** : locale à chaque joueur, plateau dans son sens, noms « Toi » et l'ami. Pendant la revue, le
  réseau continue (chat, demande de revanche, départ de l'ami) avec un bandeau en haut.
- **Succès** en ligne : « Chirurgien » (90 % de précision) et « Échec et mat » comptent aussi.
- Pas d'Elo en ligne (l'ami n'a pas de classement) : inchangé.
- Tests : nouvelle série `tests/test_en_ligne_revue.py` (deux joueurs simulés, fausse analyse) ;
  recette : R-108 et R-109 ajoutés.

À vérifier par Julien (à deux) :
- [ ] t78 à t81 (voir A_FAIRE), R-108, R-109.

## 23/10/2026 (21) – Claude Code dans le cloud (Claude Code)
Fait :
- `outils/cloud/configuration.sh` (script à coller dans l'environnement claude.ai/code) : bibliothèques
  Python, Stockfish 17.1 Linux (repli : Stockfish d'Ubuntu), base des problèmes prise dans la version amis.
- `outils/cloud/demarrage_session.sh` + crochet SessionStart dans `.claude/settings.json` : dans le cloud,
  complète les installations et rappelle à Claude ce qui est impossible là-bas ; sur le PC, ne fait rien.
- `.gitattributes` : scripts `.sh` toujours en fins de ligne Linux. `requirements-dev.txt` : numpy (tests des sons).
- `test_problemes.py` et `test_anglais.py` : sautent la partie « problèmes » si `puzzles/` manque (au lieu
  d'être rouges dans une copie neuve du dépôt).
- Essai dans WSL (Ubuntu 24.04, comme le cloud), copie neuve du dépôt : 587 contrôles verts sans les
  problèmes, 686 avec. Mode d'emploi : `docs/CLAUDE_CLOUD.md`.
- Les « prebuilds » Codespaces activés sur GitHub le 23/10 ne servent pas : à supprimer par Julien.

À faire par Julien :
- [ ] Régler l'environnement sur claude.ai/code (`docs/CLAUDE_CLOUD.md`, 5 étapes) puis lancer une session
  cloud : « lance python tests/lancer_tous.py » → tout vert.
- [ ] Supprimer les prebuilds Codespaces (github.com/sick1811/SickChess/settings/codespaces).

## 23/10/2026 (22) – Première vraie session cloud : deux corrections (Claude Code)
Session cloud de test (environnement « SickChess » déjà réglé par Julien : script, variable, accès Complet) :
pygame et python-chess ne s'étaient PAS installés (pip 24.0 + Python 3.13 du cloud : python-chess demande
`--use-pep517`) ; une fois installés à la main : 685 contrôles verts, 1 rouge passager dans
`test_mes_erreurs.py` (« un autre coup qui défend f7 », vert relancé seul : sans doute Stockfish trop lent
quand toute la suite tourne). Stockfish 17.1 et puzzles/ bien présents.
Fait :
- `outils/cloud/configuration.sh` : `--use-pep517` ; `demarrage_session.sh` : réinstalle pygame / python-chess
  s'ils manquent et le dit à Claude au début de la session.
- `.gitignore` : `/puzzles` (le raccourci créé dans le cloud n'était pas ignoré).
À faire par Julien :
- [ ] Recoller `outils/cloud/configuration.sh` (100 lignes) dans l'environnement claude.ai/code.
- [ ] Plus tard : rendre fiable le contrôle « autre coup qui défend f7 » de `test_mes_erreurs.py`.

## 23/10/2026 (23) – Cloud prêt (Claude Code)
- Environnement claude.ai/code « SickChess » mis à jour avec le script corrigé (100 lignes).
- 2e session cloud de test : pygame 2.6.1, python-chess 1.11.2 (Python 3.13), Stockfish 17.1, puzzles/
  présents ; `python tests/lancer_tous.py` → **686 contrôles verts** en 1 min 50.
- `tests/ecrans_en/` n'est plus suivi par Git (`.gitignore`) : `test_anglais.py` refait ces 20 captures à
  chaque passage, elles apparaissaient toujours « modifiées » (PC et cloud). Les images restent sur le disque.

## 24/10/2026 (24) – Version amis n° 2 publiée (Claude Code)
Fait :
- Avant : `python tests/lancer_tous.py` → 687 contrôles verts ; banc d'essai rapide : rien en rouge.
- Version **n° 2** (`v0.1.0-n2` sur `sick1811/SickChess-amis`) : seul le paquet « jeu » change (fin de partie et
  revue en ligne comme contre l'ordinateur, jeu plus fluide, analyse en priorité basse qui libère la mémoire) ;
  programme, moteur, problèmes et finales reprennent ceux de la n° 1. Aucun fichier personnel dans les paquets.
- Installeur vérifié avant l'envoi : installation silencieuse dans un dossier d'essai, jeu lancé 25 s sans erreur
  (Steam connecté), `outils/verifier_en_ligne.py` sur la version installée → tout ✅, désinstallation propre.
- En ligne : `maj.json` « latest » = n° 2, les 5 paquets et l'installeur répondent. Les amis la reçoivent par la
  mise à jour automatique du menu.
- `docs/A_FAIRE.md` : section performance et ménage cochée (faite le 23/10).

À vérifier par Julien :
- [ ] R-102 à R-107 : vraie partie en ligne avec un ami (il ouvre SickChess AVANT d'accepter l'invitation),
  puis la fin de partie : précision, bouton Revue, revue complète.

## 24/10/2026 (24) – GitHub toujours à jour (Claude Code)
Demande de Julien : « redépose toutes les fonctionnalités travaillées en Cowork et avec Claude Code ; ça doit être
mis en ligne dans le cloud à chaque modification acceptée localement ».
- Vérifié : tout le travail (Cowork + Claude Code) était déjà sur GitHub (PC et GitHub au même commit) ;
  hors GitHub, seulement ce qui doit y rester (parties, profil, sauvegardes, stockfish.exe, puzzles/,
  syzygy/, fabrications, captures de tests).
- **Envoi automatique** : `outils/git/post-commit` (crochet Git : après chaque commit, envoie la branche sur
  GitHub, sans forcer, sans jamais bloquer ; journal `.git/envoi_github.log` ; `SICKCHESS_SANS_ENVOI=1`
  pour un commit qui reste local) et `outils/git/installer_envoi_auto.py`. Essayé dans un dépôt jetable :
  envoi réussi, envoi raté (commit gardé + message), envoi coupé.
- Règle changée dans CLAUDE.md, le skill seance-sickchess, TRAVAILLER_AVEC_CLAUDE.md et CLAUDE_CLOUD.md.
- Branche `seance-13-analyse-calcul-fixe` supprimée (fusionnée dans main le 18/10).
À faire par Julien (une fois, la sécurité de Claude Code refuse qu'un crochet s'installe sans lui) :
- [ ] `python outils/git/installer_envoi_auto.py` dans le dossier SickChess.

## 24/10/2026 (25) – Installeur complet, version amis n° 3 (Claude Code)
Fait :
- Installeur complet préparé par Cowork (`publier_maj.py`, `installeur_amis.iss`, `LISEZ-MOI_AMIS.txt`) :
  programme, jeu, Stockfish, problèmes ET tables de finales dans `SickChess_Installation.exe` (664 Mo).
- `--installeur-seul` a refusé de remplacer l'installeur de la n° 2 : `LISEZ-MOI_AMIS.txt` (dans le paquet
  « jeu ») avait changé. Publié donc en **version n° 3** (seul le paquet « jeu » change ; le lien
  `releases/latest/download/SickChess_Installation.exe` donne le nouvel installeur).
- Vérifié avant l'envoi : installation silencieuse en ~1 min, problèmes (65 fichiers) et finales (145) présents,
  jeu lancé sans erreur (Steam connecté, 4 180 151 problèmes chargés au démarrage), vérification en ligne de la
  version installée toute verte, désinstallation propre. Aucun fichier personnel dans les paquets.
- En ligne : `maj.json` « latest » = n° 3 ; paquets et installeur répondent.

## 24/10/2026 (23) – Travail p35 : l'analyse libre (Claude Code dans le cloud)
Demande de Julien (page « À faire », « Demandes du 24/10 ») : « fais le travail p35 ».
Fait :
- **Nouvelle entrée du menu « Analyse libre »** (`jeu/ecran_analyse_libre.py`) : un échiquier où tu joues
  **les deux camps** ; flèches, Début/Fin et clic sur la feuille pour naviguer ; un autre coup joué au
  milieu remplace la suite.
- **Stockfish en continu** (`jeu/analyse_continue.py`), comme sur lichess : les **3 meilleures lignes**
  s'affinent en direct (profondeur qui monte), **flèche bleue** du meilleur coup (plus fines : les coups
  presque aussi bons), **barre d'avantage** (la même que la revue). Un clic sur une ligne joue son premier
  coup. Changement de position : Stockfish repart aussitôt (0,1 s). Espace = pause / relance.
  Pour ne pas chauffer : arrêt tout seul après 1 minute (ou profondeur 40) sur une même position ; un seul
  Stockfish à lui, en priorité basse, fermé en quittant l'écran.
- **Éditeur de position** (E) : palette de pièces, Déplacer, Gomme, clic droit pour enlever, trait, roques
  (cochables seulement si roi et tour sont en place), Vider / Départ. Une position impossible est refusée
  avec la raison (« Il manque le roi noir », « pion sur la première rangée »…).
- **Coller un FEN ou une partie PGN** (Ctrl+V) ; **copier le FEN** (C).
- **Tables de finale Syzygy** : si le dossier `syzygy/` est là, « Tables de finale : les Blancs gagnent /
  nulle » sous les lignes (5 pièces ou moins). Sans le dossier : rien ne s'affiche.
- **Revue → « Analyser (A) »** : la position regardée (variante comprise) s'ouvre dans l'analyse libre ;
  Retour revient à la revue au même coup. Les boutons du bas de la revue passent sur deux rangées.
- Anglais : tous les nouveaux textes traduits (« Analysis board »).
- Tests : `tests/test_analyse_libre.py` (64 contrôles, faux Stockfish) et `tests/test_analyse_libre_moteur.py`
  (14, vrai Stockfish : mat en 1 trouvé en 0,1 s, dame en prise prise, arrêt tout seul, moteur fermé en
  sortant). Suite complète : 766 contrôles verts (686 avant).
- Banc (mesure à part, dans le cloud, même machine avant / après ; `tests/banc_essai.json` du PC de Julien
  pas touché) : revue 3,29 → 3,31 ms/image et menu 0,90 → 0,86 ms (inchangés) ; analyse libre 4,24 →
  **2,44 ms/image** après mise en cache (−42 %), 16 % → 11 % d'un cœur au repos, Stockfish à l'arrêt.
  « Analyse libre » ajoutée aux écrans mesurés par `outils/banc_essai.py`.
- Recette : R-140 à R-149 ajoutés (section « Analyse libre »).
- Vu en passant (pas corrigé) : dans le cloud, un Stockfish met ~4,5 s à démarrer (réservation de sa
  mémoire, 512 Mo) ; à mesurer sur le PC de Julien.
- Pas de version amis : impossible dans le cloud (Windows seulement) ; à publier par Claude Code sur le PC.

À vérifier par Julien :
- [ ] t82 à t87 (voir A_FAIRE), R-140 à R-149.

## 24/10/2026 (24) – Travail p36 : l'invitation d'un ami affichée dans le jeu (Claude Code dans le cloud)
Demande de Julien : « fais le travail p36 ».
Fait :
- Le jeu écoute maintenant l'**invitation reçue** de Steam (`LobbyInvite_t`, `steam.py`) : avant, il ne
  savait réagir qu'à une invitation **acceptée** dans Steam.
- **Bandeau en haut, sur tous les écrans** (`jeu/invitations.py`) : « Paul t'invite à jouer – Rejoindre /
  Plus tard », avec un petit son (celui du début de partie, déjà dans le jeu).
  - au menu : Rejoindre → salon de l'ami ;
  - dans un autre écran (problèmes, revue, options, analyse libre…) : l'écran se ferme, puis salon de l'ami ;
  - **pendant une partie** contre l'ordinateur ou à deux : fenêtre « Rejoindre Paul ? » (Rester / Rejoindre),
    pendule arrêtée pendant la question ; si Rejoindre : la partie est **gardée** (« Reprendre la partie »
    dans le menu) ;
  - Plus tard (ou 45 s sans réponse) : le bandeau s'en va.
- **« Jouer en ligne » : liste « INVITATIONS REÇUES »** (10 minutes), avec « il y a N min » et Rejoindre.
  Pas de bandeau pendant le jeu en ligne lui-même (le salon a sa liste).
- Mode test : bouton **« Test : invitation »** dans Jouer en ligne (fausse invitation, pour voir le bandeau
  sans ami). Disparaît avec `MODE_TEST = False`.
- Comment : tous les écrans lisent maintenant la souris / le clavier par `ui.evenements()` et affichent par
  `ui.afficher()` (au lieu de `pygame.event.get()` / `pygame.display.flip()`, 17 endroits). Sans invitation
  c'est exactement pareil ; le bandeau coûte 1,7 microseconde par image (négligeable).
- Anglais : textes traduits. Tests : nouvelle série `tests/test_invitations.py` (31 contrôles : Steam,
  bandeau au menu / dans un écran / en partie, Plus tard, en ligne, liste du salon, retour au menu).
  Suite complète : 797 contrôles verts.
- Recette : R-10A à R-10E ajoutés (section « En ligne (Steam) »).
- Vu en passant (pas corrigé) : l'accueil de « Jouer en ligne » a deux textes sans accents (« Cree une
  partie et invite-le… ») ; corrigé seulement pour « Test : héberger » et « fenêtres ».
- Pas de version amis (impossible dans le cloud).

À vérifier par Julien :
- [ ] t88 à t91 (voir A_FAIRE), R-10A à R-10E — il faut un ami Steam (ou deux comptes Steam).

## 24/10/2026 (25) – Travail p37 : classements Steam, succès préparés (Claude Code dans le cloud)
Demande de Julien : « fais le travail p37 », puis pousser sur GitHub.
Fait :
- **Classements Steam** (`jeu/classements.py`, `jeu/ecran_classements.py`) : Problèmes → « Classements
  Steam ». Trois classements (Problèmes = ton classement du jour ; Contre la montre et Survie = ton
  record, Steam garde le meilleur), trois vues (Mondial = 10 premiers, Amis, Autour de moi), ta ligne en
  or, Actualiser. Ils marchent **dès maintenant** avec le numéro de test 480 (Steam les crée à la
  première demande).
- Les scores partent tout seuls : après chaque problème classé, à la fin de chaque contre la montre /
  survie. Sans Steam, ils restent dans le jeu et partent à la connexion suivante (rattrapage). Rien
  n'attend jamais Steam (réponses lues à chaque image ; message si Steam ne répond pas en 15 s).
- **Succès préparés pour le vrai numéro Steam** : à chaque connexion, le jeu renvoie à Steam tous les
  succès déjà gagnés (personne ne perd ses succès d'avant) ; avec 480, rien n'est envoyé (Steam ne les
  connaît pas). **28 icônes** (débloqué + grisé, 256 px, Onyx & Or) dans `docs/steam_succes/`, faites par
  `outils/generer_icones_succes.py` avec les pièces « Tournoi plat » et Barlow (noté dans CREDITS).
  `docs/SUCCES_STEAM.md` réécrit : les 4 étapes du jour J dans Steamworks, les 14 succès, les 3 classements.
- `steam.py` : appels Steam des classements (FindOrCreateLeaderboard, UploadLeaderboardScore,
  DownloadLeaderboardEntries…), tailles des structures vérifiées au chargement.
- Anglais : textes traduits. Tests : nouvelle série `tests/test_classements.py` (32 contrôles, faux Steam qui
  répond comme le vrai). Suite complète : 829 contrôles verts.
- Recette : R-08A à R-08C ajoutés (section « Problèmes »).
- Pas de version amis (impossible dans le cloud).

À vérifier par Julien :
- [ ] t92 à t94 (voir A_FAIRE), R-08A à R-08C — Steam ouvert, avec steam_api64.dll et steam_appid.txt (480).

## 24/10/2026 (26) – Recette automatique, page « À faire », travail p30 : banque de positions (Claude Code dans le cloud)
Demande de Julien : publier une version amis, mettre les tests dans la page « À faire », les faire sur son PC
(« tu dois passer par mon PC obligatoirement »), puis passer au travail suivant.
Fait :
- **`outils/recette_auto.py`** : la recette faite par Claude. Pilote le VRAI jeu (clics souris sur les cases et
  les boutons, clavier, vrai Stockfish, fenêtre invisible) et vérifie 13 lignes de recette (R-140 à R-149,
  R-10E…). Dans le cloud : tout vert (ex. Stockfish 297 % → 0 % de processeur avec Espace ; arrêt tout seul à
  60 s ; plus aucun Stockfish après Retour ; Analyser depuis la revue au même coup).
- **Page « À faire »** : ajout de t82 à t94 et de 20 lignes de recette manquantes (R-08A–C, R-108–109, R-10A–E,
  R-140–149), avec en commentaire ce que Claude a déjà vérifié et ce qui reste pour Julien. « Fonctionne » pas
  encore coché : en attente de la même vérification sur le PC Windows.
- **PC de Julien** : la session Claude Code du PC (« Mesure Stockfish ») a reçu la consigne (fusion de la
  branche, tests, recette automatique, Steam, version amis), mais elle avait atteint sa limite d'utilisation
  (jusqu'à 4 h 10) ; une relance automatique est programmée à 4 h 20. **Version amis pas encore publiée.**
- **p30 – Banque de positions** (`tests/positions_revue.json`, `outils/precision.py`) : 58 petites parties,
  114 coups jugés : 52 problèmes lichess (22 sacrifices, 10 mats, 10 finales, 10 avantages décisifs) – la gaffe
  qui crée le problème doit être notée Erreur / Manque / Gaffe, le bon coup (souvent un sacrifice) une bonne
  pastille – plus 6 positions à la main (mat étouffé, piège de Légal, pat raté, dame en prise, 1.e4). Chaque
  problème est revérifié à la fabrication par Stockfish en profondeur 20 (gaffe nette : ≥ 40 % de chances avant,
  ≤ 15 % après ; bon coup : ≥ 75 %) : la banque ne vient pas de notre propre analyse.
- **Défaut trouvé par la banque et corrigé** : une partie qui commence à une autre position (PGN importé avec
  [FEN], « Mes erreurs », analyse libre) voyait son 1er coup comparé au livre d'ouvertures comme si elle partait
  de la position initiale : « e3 », « d3 », « a4 », « h4 », de vraies gaffes, étaient notées **Théorique**. Le
  livre ne sert plus que pour les parties parties de la position initiale ; et un coup du livre qui perd
  vraiment (Erreur ou pire) reçoit sa vraie pastille. Avant : 108 justes sur 114 ; après : **114 sur 114** (Forte,
  686 s dans le cloud ; Rapide : 114 sur 114 en 408 s).
- Banc d'essai : 8e section **« precision »** (toute la banque, Forte ; --rapide : Rapide). Tests :
  `tests/test_precision.py` (8 contrôles, sans Stockfish) et `tests/test_precision_moteur.py` (échantillon de 19
  parties, Rapide, ~2 min). Suite complète : 874 contrôles verts. Recette : R-06I ajouté.

À vérifier par Julien :
- [ ] t95 (voir A_FAIRE).

## 24/10/2026 (27) – Travail p29 : rapport de plantage (Claude Code dans le cloud)
Demande de Julien : « FAIS p29 ».
Fait :
- **Au plantage** (`SickChess.py` → `jeu/plantage.py`) : l'erreur, son détail technique (fichier, ligne), la fin du
  journal de CE lancement, la version et le système sont gardés dans `plantage.json` (à côté du jeu, hors GitHub,
  hors paquets amis). Avant, `journal_du_jeu.txt` était remis à zéro au lancement suivant : l'erreur était perdue.
- **Au lancement suivant** (`jeu/ecran_plantage.py`) : carte « La dernière fois, SickChess s'est fermé à cause
  d'une erreur » : **Envoyer le rapport** ouvre « Signaler un problème » déjà rempli (message + erreur + journal
  du lancement qui a planté ; on peut compléter) ; **Non merci** l'efface ; Échap = plus tard (3 fois au plus).
  Rien ne part sans clic du joueur. Une fois envoyé (ou rangé dans rapports/), il n'est plus proposé.
- `python SickChess.py --plantage-test` : plantage volontaire pour essayer (recette R-124).
- Tests : `tests/test_plantage.py` (18 contrôles, dont un VRAI plantage du lanceur copié dans un dossier
  temporaire avec un faux jeu qui plante). Suite complète : 891 contrôles verts. Anglais traduit.

À vérifier par Julien :
- [ ] t96 (voir A_FAIRE), R-124.

## 24/10/2026 (28) – Travail p28 : test d'endurance (Claude Code dans le cloud)
Demande de Julien : « p28 ».
Fait :
- **`outils/endurance.py`** : un robot joue au VRAI jeu (fenêtre invisible, dossier temporaire, vrai Stockfish, 60
  images/s) pendant 2 h, en boucle : menu → partie contre l'ordinateur (coups au hasard, niveau 800 / 1400 / 2000) →
  sa revue → partie à deux quittée en cours → problèmes (15 % de mauvais coups) → analyse libre → Options, Mes
  parties, Statistiques. Après chaque scénario : mémoire du jeu et des Stockfish, nombre de Stockfish, fils, temps
  d'image, erreurs. Jugement : fuite (pente de la mémoire au menu, seconde moitié du test), Stockfish qui
  s'accumulent, ralentissement (fin / début), plantages (erreur ou « Traceback » dans le journal).
  → `tests/endurance/rapport.json`, `journal.txt` et, pour 1 h ou plus, `docs/ENDURANCE.md`.
- Banc d'essai : 9e section **« endurance »** (hors --rapide ; SICKCHESS_ENDURANCE_MINUTES change la durée).
- Essais dans le cloud (18 min, 2 fois) : **0 plantage, 0 Traceback, au plus 3 Stockfish (2 au menu, toujours),
  pas de ralentissement (x1,05 à x1,13)**. Mémoire du jeu au menu : 182 → 199 Mo en 8 min puis plafond (réserves
  des textes et des tranches de problèmes, bornées) → +19 Mo/h, vert. Le 1er essai avait vu une fausse fuite : le
  robot gardait lui-même le temps de chaque image (corrigé : 600 au plus par écran).
- Tests : `tests/test_endurance.py` (10 contrôles du jugement sur des mesures inventées). Suite : 900 contrôles verts.
- Le vrai passage de 2 h est à faire sur le PC de Julien (demandé à Claude Code du PC, la nuit).

## 24/10/2026 (29) – Travail p32 : vérification avant chaque version (Claude Code dans le cloud)
Demande de Julien : « P32 ».
Fait :
- **`outils/verifier_version.py`** (`--amis` ou `--steam`) : une ligne OK / A REVOIR / BLOQUANT par point :
  MODE_TEST (permis pour les amis, bloquant pour Steam), steam_appid.txt (480 pour les amis, le vrai numéro pour
  Steam, avec le rappel de ne pas l'envoyer à Steam), licences (fichiers présents ; lignes « à vérifier » de
  docs/CREDITS.md : à revoir pour les amis, bloquantes pour Steam), VERSION jamais plus petite que la version déjà
  publiée (lue en ligne), Git (tout enregistré, hors données de Julien), tests/lancer_tous.py tout vert, banc
  d'essai sans rouge (vitesse, processeur, mémoire, conflits, précision), et le .exe (`--exe`) qui démarre depuis
  une COPIE neuve et tourne 25 s sans erreur.
- **CONSTRUIRE_VERSION_AMIS.bat** lance d'abord la vérification : s'il y a un BLOQUANT, rien n'est fabriqué.
  **publier_maj.py** essaie le .exe dans un dossier neuf AVANT tout envoi sur GitHub (Windows).
- Essai dans le cloud (`--amis --sans-banc`, 3 min 40) : rien de bloquant ; à revoir : licences des pièces
  « Classique » et des ouvertures encore « à vérifier » (bloquant pour Steam), fichiers pas encore enregistrés.
- Tests : `tests/test_verifier_version.py` (33 contrôles, faux projets). Suite : 931 contrôles verts. Recette : R-115.

À vérifier par Julien / Claude Code (PC) :
- [ ] t97 (voir A_FAIRE), R-115.

## 24/10/2026 (30) – Travail p31 : mode « petit PC » (Claude Code dans le cloud)
Demande de Julien : « P31 ».
Fait :
- **`jeu/petit_pc.py`** : au lancement, le jeu regarde le PC (cœurs, mémoire). **Petit PC** = 4 cœurs ou moins, ou
  ~8 Go ou moins. Écrit au journal (« [PC] 4 coeurs, 7.9 Go : PETIT PC »).
- Sur un petit PC : analyse avec **un seul Stockfish** (au lieu de 2 ou 3), **1 Go** de mémoire au plus (au lieu de
  4), **un seul cœur pendant la partie** (l'ordinateur adverse reste fluide), puissance **Rapide par défaut** (un
  choix fait dans Options est toujours respecté) ; **30 confettis** au lieu de 90 ; **24 images/s au repos** au lieu
  de 30.
- **Options → Affichage → « Puissance du PC »** : Automatique (par défaut, avec « Ce PC : 12 cœurs, 16 Go → PC
  normal »), Petit PC, PC normal. Le PC de Julien (i7, 12 cœurs) reste en « PC normal » : rien ne change pour lui.
- Le cloud (4 cœurs) est un petit PC : toute la suite d'analyse y a tourné avec un seul Stockfish, verte.
  Les séries qui contrôlent les réglages d'un PC normal le forcent (`petit_pc.forcer`).
- Tests : `tests/test_petit_pc.py` (20 contrôles). Anglais traduit. Recette : R-09F.
- En passant : le contrôle instable de `test_mes_erreurs.py` (« un autre coup qui défend f7 », noté le 23/10 (22))
  a de nouveau été rouge pendant la suite complète, vert 3 fois sur 3 seul. Cause : Stockfish n'avait que 1,5 s
  pour la profondeur 14 ; PC occupé = profondeur pas atteinte = un BON coup de « Mes erreurs » pouvait être refusé
  (vrai défaut pour un joueur pendant une analyse en tâche de fond). Garde-fou porté à 5 s
  (`jeu/mes_erreurs.py`). Suite complète : 950 contrôles verts.

À vérifier par Julien :
- [ ] t98 (voir A_FAIRE), R-09F.
