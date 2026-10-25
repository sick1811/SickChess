# Recette complète – SickChess

Tous les tests à faire à la main pour vérifier le jeu entier. Version : 24/10/2026.

**Règles**
- Fichier fabriqué par `python outils/recette.py` : modifier `outils/recette.py`, pas ce fichier.
- Chaque fonction ajoutée ou modifiée = ses lignes ajoutées ou corrigées ici, dans la même séance.
- Avant chaque version (amis, Steam) : Claude Code lance `python tests/lancer_tous.py`, puis
  Julien repasse toute la recette dans la page « SickChess – À faire » (bouton « Nouvelle passe »).
- Un test « Ne fonctionne pas » = d'abord un contrôle automatique qui montre le bug, puis la correction.

## Lancement et fenêtre

- [ ] **R-001** – Double-clic sur LANCER.bat (ou SickChess.exe)  
  → Le menu s'ouvre en quelques secondes, fond 3D, titre SICKCHESS, icône dorée dans la barre des tâches.
- [ ] **R-002** – F11 dans le menu puis en partie  
  → Plein écran puis retour en fenêtre, rien ne déborde ni ne se chevauche.
- [ ] **R-003** – Agrandir / rétrécir la fenêtre à la souris pendant une partie  
  → L'échiquier et le panneau se recalent, les textes restent lisibles.
- [ ] **R-004** – F1 dans une partie  
  → L'aide des raccourcis s'affiche par-dessus ; F1 ou Échap la ferme.
- [ ] **R-006** – Premier lancement (dézipper la version amis dans un dossier neuf, ou renommer profil.json)  
  → Accueil : ton nom, ton niveau (4 choix), puis « Trois choses à savoir » ; ensuite le menu ; il ne revient plus. (Remettre profil.json.)
- [ ] **R-005** – Quitter par le bouton Quitter puis par la croix de la fenêtre  
  → Le jeu se ferme tout de suite (moins d'une seconde, même pendant une revue ou quand l'ordinateur réfléchit), sans message d'erreur ; journal_du_jeu.txt finit par « Fin normale ».

## Partie contre l'ordinateur

- [ ] **R-010** – Menu → Jouer contre l'ordinateur : changer niveau (Débutant → Maximum), rythme, cadence, incrément  
  → Les pastilles se sélectionnent en doré, le résumé « X minutes par joueur, +Y s » suit.
- [ ] **R-011** – Cocher « Retenir ces réglages », lancer, revenir au menu, rouvrir l'écran  
  → Les réglages choisis sont retrouvés.
- [ ] **R-012** – Jouer une partie complète jusqu'au mat ou à l'abandon  
  → L'ordinateur joue à son tour sans bloquer, à une vitesse humaine.
- [ ] **R-013** – Jouer avec les Noirs (relancer jusqu'à les avoir)  
  → Plateau retourné, l'ordinateur commence, ta pendule est en bas.
- [ ] **R-015** – Regarder le rythme de l'ordinateur pendant une partie de 10 minutes  
  → Il reprend vite une pièce qu'on vient de lui prendre, réfléchit plus longtemps quand ses pièces sont menacées, ne joue jamais en un éclair (sauf coup forcé).
- [ ] **R-014** – Niveau Débutant puis Maximum  
  → Débutant laisse des pièces en prise ; Maximum ne laisse rien passer.

## Partie à deux sur ce PC

- [ ] **R-020** – Menu → Jouer à deux, plateau « Il tourne à chaque coup »  
  → Le plateau se retourne vers le joueur qui a le trait.
- [ ] **R-021** – Même chose avec « Plateau fixe »  
  → Les Blancs restent en bas toute la partie.

## Échiquier et règles

- [ ] **R-030** – Déplacer une pièce en la glissant, puis par clic-clic  
  → Les deux manières marchent ; points sur les coups possibles ; dernier coup surligné.
- [ ] **R-031** – Tenter un coup illégal  
  → La pièce revient à sa place avec un petit son, rien n'est joué.
- [ ] **R-032** – Petit roque et grand roque  
  → Roi et tour se déplacent ensemble, son du roque.
- [ ] **R-033** – Prise en passant  
  → Le pion pris disparaît bien de sa case.
- [ ] **R-034** – Promotion : amener un pion sur la dernière rangée, choisir dame puis une autre fois cavalier  
  → Le choix de la pièce s'affiche, la pièce choisie apparaît (aussi avec les Noirs).
- [ ] **R-035** – Mettre le roi adverse en échec  
  → Case du roi en rouge, son d'échec.
- [ ] **R-036** – Faire mat  
  → Carte de fin « Victoire ! » ou « Les Blancs gagnent », son de mat.
- [ ] **R-037** – Pat, répétition 3 fois, règle des 50 coups (partie à deux pour le provoquer)  
  → Partie nulle annoncée avec la bonne raison.
- [ ] **R-038** – Clic droit sur des cases / glisser au clic droit  
  → Cases colorées et flèches ; clic gauche les efface.
- [ ] **R-039** – Pré-mouvement : jouer pendant que l'ordinateur réfléchit  
  → Le coup part tout seul dès que c'est ton tour ; Échap l'annule.

## Pendule

- [ ] **R-040** – Partie 1 min, laisser descendre sous 30 s  
  → Le chrono clignote en rouge, un bip d'alerte.
- [ ] **R-041** – Laisser le temps tomber à 0  
  → Partie perdue au temps, pendule affichée à 0:00.0.
- [ ] **R-042** – Partie avec incrément (+3 s)  
  → Le temps augmente de 3 s après chaque coup joué.
- [ ] **R-043** – Partie « Sans limite »  
  → Les pendules affichent « --:-- » et ne bougent pas.

## Pendant la partie

- [ ] **R-050** – Bouton Abandonner (cliquer deux fois)  
  → Confirmation « SÛR ? », puis la partie est perdue pour toi.
- [ ] **R-051** – Bouton MENU (à côté d'Abandonner) en pleine partie  
  → Le menu propose « Reprendre la partie en cours ».
- [ ] **R-052** – Fermer le jeu en pleine partie, le relancer, Reprendre  
  → Position, pendules, couleur et orientation retrouvées.
- [ ] **R-053** – Écouter : coup, prise, roque, échec, mat, promotion, coup illégal  
  → Chaque situation a son son ; pas de son coupé ni en double.
- [ ] **R-055** – Échap en pleine partie (rien de sélectionné)  
  → Menu Pause : la pendule s'arrête ; Reprendre la relance ; Options change le plateau sans quitter la partie.
- [ ] **R-056** – Pause → Proposer la nulle : à deux, puis contre l'ordinateur au début et vers le coup 25  
  → À deux : nulle tout de suite. Ordinateur : refuse au début (« trop tôt »), accepte si la partie est égale.
- [ ] **R-057** – Pause → Abandonner (deux clics) et Pause → Retour au menu  
  → Abandon demandé deux fois ; Retour au menu garde la partie (« Reprendre la partie en cours »).
- [ ] **R-054** – Panneau de droite pendant la partie  
  → Nom de l'ouverture (avec accents), coups joués, matériel pris, pendules.

## Fin de partie et revue

- [ ] **R-060** – Finir une partie contre l'ordinateur  
  → Carte de fin : résultat, raison, Elo « 1200 -> 1215 (+15) », précision des deux joueurs presque tout de suite.
- [ ] **R-06J** – Finir une partie contre l'ordinateur : lire le résumé du coach sur la carte de fin  
  → Trois lignes tout de suite : l'ouverture (« Ouverture : C60 - Partie espagnole (4 coups de théorie) »), ton plus gros moment (ta pire faute et le coup qu'il fallait jouer, ou ton plus beau coup), ta précision « provisoire » qui devient définitive, comparée à tes 10 dernières parties (« ta meilleure… », « au-dessus de ta moyenne… »). Rien ne chevauche les boutons.
- [ ] **R-061** – Carte de fin → Rejouer, puis → Menu  
  → Rejouer relance avec les mêmes réglages ; Menu revient au menu.
- [ ] **R-062** – Carte de fin → Revue de la partie  
  → La revue s'ouvre sur la position de départ.
- [ ] **R-063** – Revue : flèches gauche/droite, Début/Fin, molette, clic sur un coup, clic sur la courbe  
  → On se déplace dans la partie, l'échiquier suit, son à chaque coup en avant.
- [ ] **R-064** – Revue : pastilles des coups  
  → Une pastille par coup (rond d'attente avant) ; elle ne change plus une fois affichée.
- [ ] **R-065** – Revue : un coup marqué Erreur ou Gaffe  
  → Flèche verte vers le coup qu'il fallait jouer ; « Il fallait jouer … » dans le détail.
- [ ] **R-06A** – Revue : un coup marqué Gaffe / Erreur / Imprécision (ex. laisser une pièce en prise)  
  → Sous la pastille, une phrase explique la faute (« Ce coup laisse ton cavalier sans défense », « Tu avais un mat en un coup »…) sans jamais écrire le coup.
- [ ] **R-066** – Revue : un bon sacrifice  
  → Garde une bonne pastille (Brillant, Meilleur, Excellent…).
- [ ] **R-067** – Revue : jouer un autre coup sur l'échiquier, puis le coup de l'autre camp  
  → Variante : TU joues les deux camps, Stockfish ne joue JAMAIS ; flèches bleues de ses meilleurs coups, évaluation et barre suivent ; flèche gauche annule un coup, Échap ramène à la partie.
- [ ] **R-06B** – Revue : regarder n'importe quelle position ; touche B  
  → Flèche bleue = meilleur coup de Stockfish ici (plus claire : les coups aussi bons) ; « Meilleur ici : … » et la suite prévue dans le détail ; B cache / remet les flèches.
- [ ] **R-06C** – Revue : la feuille de coups  
  → L'évaluation après chaque coup à droite, en couleur quand le coup a coûté (orange, rouge).
- [ ] **R-06D** – Revue : Exporter (ou touche E) une fois l'analyse terminée ; coller sur lichess.org/paste ou chess.com/analysis  
  → PGN copié et enregistré dans exports/ ; lichess / chess.com relisent les évaluations et les pastilles. Précision : identique à la méthode lichess (chess.com a sa propre formule, secrète : écart de quelques points normal).
- [ ] **R-06E** – Revue d'une partie importée de chess.com (ex. contre dragondu5)  
  → Mêmes moments forts que chess.com : 7.Qe2 gaffe, 10.h3 erreur, 15.Qb3 erreur, 7...Bxa1 Très bien.
- [ ] **R-06F** – Revue juste après une partie, pendant que l'analyse calcule (Options : Calcul fixe, Forte)  
  → En haut : « Analyse fine… 40 % · environ 3 min » ; le temps restant baisse régulièrement ; à la fin « Analyse terminée (profondeur X à Y) ».
- [ ] **R-06H** – Mes parties → Importer une longue partie (60 coups et plus), ouvrir la revue (Calcul fixe, Forte)  
  → Courbe, flèches et la plupart des pastilles en 1 à 2 minutes ; quelques coups gardent un rond creux (« en vérification ») puis reçoivent leur pastille ; une pastille posée ne change plus ; revue complète en environ 5 minutes pour 70 coups.
- [ ] **R-06I** – Importer une partie qui commence à une autre position (PGN avec [FEN "…"]) dont le 1er coup est une gaffe, puis sa revue  
  → Le 1er coup n'est pas « Théorique » : il reçoit sa vraie pastille (Gaffe). Une partie normale garde ses coups « Théorique » au début.
- [ ] **R-06G** – Changer Options → Partie → Façon d'analyser, puis rouvrir la revue d'une partie déjà analysée  
  → La revue s'affiche tout de suite, sans tout refaire (une analyse assez forte est gardée, quel que soit le mode).
- [ ] **R-068** – Revue : touche F  
  → L'échiquier se retourne.
- [ ] **R-069** – Ressortir de la revue, la rouvrir  
  → Tout s'affiche tout de suite, sans nouvelle analyse.

## Mes parties et profil

- [ ] **R-070** – Menu → Mes parties et profil  
  → Profil (nom, Elo, victoires/nulles/défaites, courbe) et liste des parties, la plus récente en haut.
- [ ] **R-071** – Changer de nom, valider avec Entrée  
  → Le nouveau nom s'affiche ici et dans les nouvelles parties.
- [ ] **R-072** – Revoir une partie de la liste  
  → La revue s'ouvre au début ; si elle a déjà été analysée, pas de nouvelle analyse.
- [ ] **R-075** – Copier un PGN (lichess / chess.com) puis Mes parties → Importer (PGN)  
  → La revue de la partie s'ouvre ; elle apparaît dans la liste avec la pastille PGN (ou V/N/D si ton nom y est) ; l'Elo ne bouge pas.
- [ ] **R-076** – Copier un lien de partie lichess puis Importer ; glisser un fichier .pgn sur la fenêtre  
  → La partie est téléchargée / importée et la revue s'ouvre.
- [ ] **R-077** – Mes parties → Statistiques  
  → Parties et score (Blancs / Noirs), précision moyenne et tendance, tes ouvertures avec leur score, tes fautes par phase, courbe de précision.
- [ ] **R-078** – Battre l'ordinateur, puis Mes parties → Statistiques → Succès  
  → Bandeau « Succès débloqué : Premier sang » en haut de l'écran ; la liste montre les 14 succès, ceux obtenus en couleur avec la date.
- [ ] **R-073** – Bouton Ouvrir le dossier  
  → L'explorateur Windows s'ouvre sur le dossier parties.
- [ ] **R-074** – Partie à deux puis Mes parties  
  → La partie apparaît avec la pastille « 2J » et ne change pas l'Elo.

## Problèmes

- [ ] **R-080** – Menu → Problèmes → Mode classé : faire 10 problèmes  
  → Coup adverse joué tout seul, chrono, classement qui monte ou descend, son de réussite.
- [ ] **R-081** – Jouer un mauvais coup  
  → Plateau rouge, explication écrite sans donner la solution, on peut réessayer.
- [ ] **R-082** – Indice (H) puis Solution  
  → L'indice montre la pièce à jouer ; la solution se rejoue avec les flèches.
- [ ] **R-083** – Passer un problème  
  → Il compte comme raté, le suivant arrive.
- [ ] **R-084** – Mode libre avec un niveau (600 → 2500) et un thème (ex. Mat en 2)  
  → Les problèmes sont du niveau et du thème choisis ; le classement n'est pas touché.
- [ ] **R-085** – Problème avec promotion (thème Promotion)  
  → Le choix de la pièce s'affiche et la bonne pièce est acceptée.
- [ ] **R-087** – Problèmes → Contre la montre  
  → 3:00 qui descend ; les problèmes deviennent plus durs ; une faute = solution puis problème suivant ; à 0:00 « Temps écoulé ! », score et record ; « Rejouer le défi ».
- [ ] **R-088** – Problèmes → Survie  
  → Vies 3/3 ; chaque faute en retire une ; à 0 : « Trois fautes : fini ! » et le record.
- [ ] **R-089** – Problèmes → Problème du jour, puis le rouvrir  
  → Un seul essai ; ensuite « Tu as déjà fait le problème du jour. Reviens demain ! » ; le bouton affiche « fait ».
- [ ] **R-086** – Problèmes → Mes erreurs  
  → Tes gaffes de parties analysées reviennent en problèmes ; « Ta partie du … » ; un autre très bon coup est accepté.
- [ ] **R-08A** – Steam ouvert : Problèmes → « Classements Steam » ; Problèmes / Contre la montre / Survie ; Mondial / Amis / Autour de moi  
  → Les listes se chargent (rang, joueur, score) ; ta ligne « Toi » est en or ; flèches gauche/droite changent de classement ; Échap revient aux Problèmes.
- [ ] **R-08B** – Faire un contre la montre (ou une survie, ou un problème classé), puis rouvrir les classements  
  → Ton nouveau score y est (Actualiser si besoin) ; un moins bon record ne remplace pas le meilleur ; le classement des problèmes suit ta valeur du jour.
- [ ] **R-08C** – Steam fermé : Problèmes → « Classements Steam » ; jouer un contre la montre ; puis relancer le jeu avec Steam ouvert  
  → Sans Steam : message clair et tes scores du jeu ; une fois Steam ouvert, ton record apparaît dans le classement sans rien refaire.

## Entraînement aux ouvertures

- [ ] **R-097** – Menu → Entraînement aux ouvertures : choisir Blancs ou Noirs puis une ouverture  
  → Le jeu joue les coups adverses de la théorie ; à toi de trouver les tiens ; un coup faux = rouge, on réessaie.
- [ ] **R-098** – « Montrer le coup (H) », finir la ligne, « Ligne suivante »  
  → Flèche du bon coup ; à la fin : score et nom exact de la variante ; la suivante est une autre variante ; le % s'affiche sur l'ouverture dans la liste.

## Analyse libre

- [ ] **R-140** – Menu → Analyse libre  
  → Position de départ ; en quelques secondes, 3 lignes de Stockfish à droite (évaluation + coups), « profondeur » qui monte, flèche bleue du meilleur coup, barre d'avantage à gauche.
- [ ] **R-141** – Jouer des coups des deux camps (glisser ou clic-clic), puis flèches gauche/droite, Début/Fin, clic sur un coup de la feuille  
  → Les deux camps se jouent ; Stockfish repart aussitôt sur chaque nouvelle position ; on navigue dans les coups ; un autre coup joué au milieu remplace la suite.
- [ ] **R-142** – Cliquer sur une des 3 lignes de Stockfish  
  → Son premier coup est joué sur l'échiquier.
- [ ] **R-143** – Espace (ou bouton Pause), attendre, puis Espace encore  
  → « Stockfish à l'arrêt », bouton « Relancer » en or, le processeur redescend (Gestionnaire des tâches) ; Espace : l'analyse reprend.
- [ ] **R-144** – Copier un FEN (ex. lichess → Partager → FEN) puis Ctrl+V ; puis copier une partie PGN et Ctrl+V  
  → « Position collée » : la position s'affiche et s'analyse ; « Partie collée : N coups » : la partie s'affiche depuis le début, flèches pour avancer. Un texte quelconque : message clair, rien ne casse.
- [ ] **R-145** – Éditer (E) : Vider, poser rois, tours, pions ; Déplacer ; Gomme ; clic droit ; trait ; roques ; Analyser  
  → Les pièces se posent / s'enlèvent ; les roques ne se cochent que si roi et tour sont à leur place ; une position impossible (pas de roi, pion sur la 1re rangée…) est refusée avec la raison ; « Analyser » lance Stockfish dessus ; Échap annule.
- [ ] **R-146** – Copier le FEN (C), le coller dans lichess.org/analysis  
  → « FEN copié » ; lichess affiche la même position.
- [ ] **R-147** – Revue d'une partie → aller à un coup → « Analyser (A) » ; puis Retour  
  → L'analyse libre s'ouvre sur la même position (variante comprise), avec la partie dans la feuille ; Retour revient à la revue au même coup.
- [ ] **R-148** – Finale à 5 pièces ou moins (ex. coller 8/8/8/4k3/8/8/4P3/4K3 w - - 0 1 : nulle, roi noir devant le pion ; puis 8/8/8/4k3/8/8/8/3QK3 w - - 0 1 : les Blancs gagnent), dossier syzygy/ présent  
  → Sous les lignes : « Tables de finale : nulle » pour la première, « les Blancs gagnent » pour la seconde ; sans le dossier syzygy/, rien ne s'affiche et tout marche.
- [ ] **R-149** – Laisser l'analyse libre ouverte 2 minutes sur la même position, puis Retour  
  → Au bout d'une minute « analyse terminée » et le processeur redescend ; après Retour, plus de stockfish.exe d'analyse libre dans le Gestionnaire des tâches.

## Signaler un problème

- [ ] **R-095** – Menu → Signaler un problème / une idée : écrire un message, Envoyer  
  → Sans adresse d'envoi réglée : « Message enregistré dans le dossier rapports et copié », le dossier rapports s'ouvre avec le fichier.
- [ ] **R-096** – Ouvrir le fichier du rapport  
  → Ton message, la version, le système et (pour un problème) la fin du journal du jeu.

## Options

- [ ] **R-090** – Options → Échiquier : changer damier, accent, pièces, coordonnées  
  → L'aperçu change tout de suite ; Enregistrer garde, Annuler remet comme avant.
- [ ] **R-091** – Options → Partie : vitesse des pièces, retournement, pré-mouvement, notation française  
  → Les coups s'écrivent Cf3/Fc4 partout ; retour en anglais possible.
- [ ] **R-092** – Options → Son : volume (cliquer pour entendre), Muet  
  → Le volume change vraiment ; Muet coupe tout.
- [ ] **R-09A** – Options → Son : Sons des pièces Bois / Feutre / Muet sauf alertes (cliquer pour entendre)  
  → Feutre est plus doux ; « Muet sauf alertes » : plus de bruit de pièce, mais l'échec, le temps et la fin sonnent.
- [ ] **R-09B** – Menu : la musique d'ambiance ; Options → Son → Musique Non ; touche M dans le menu  
  → Musique douce dans le menu, les problèmes et l'entraînement, coupée en partie ; Non ou M la coupent ; le volume change.
- [ ] **R-09E** – Options → Partie → Façon d'analyser (Calcul fixe / Profondeur / Temps) et Puissance (Rapide / Forte / Maximale)  
  → Calcul fixe et Forte par défaut (analyse rapide de toutes les positions, puis vérification à 15 / 25 / 50 millions des seuls coups dont la pastille hésite) ; Profondeur Maximale = l'ancienne profondeur 30 ; Temps : chaque position prend le temps choisi (3 / 7 / 15 s).
- [ ] **R-093** – Options → Affichage : taille des textes, police, plein écran  
  → Tous les écrans suivent, rien ne déborde.
- [ ] **R-09C** – Options → Affichage → Langue → English, puis Enregistrer ; parcourir menu, partie, revue, problèmes, aide F1  
  → Tout est en anglais (boutons, explications, noms d'ouvertures), rien ne déborde ; revenir à Français remet tout.
- [ ] **R-09G** – Plein écran (F11) sur un grand écran (2560×1440 ou 4K) ; puis fenêtre réduite au minimum  
  → En 4K, panneau, boutons, pendules et textes grandissent avec l'écran (rien de minuscule) ; en petite fenêtre et en 1366×768 rien ne déborde.
- [ ] **R-09H** – Revue : regarder les pastilles (ou une capture en noir et blanc)  
  → Chaque pastille se reconnaît à son symbole, même sans les couleurs (!!, !, étoile, livre, coche, rond, ?!, ?, X, ??) ; le symbole se lit aussi sur le jaune et le vert clair (contour sombre).
- [ ] **R-094** – Valeurs par défaut  
  → Tout revient aux réglages d'origine (plateau Tournoi, accent Or).
- [ ] **R-09F** – Options → Affichage → « Puissance du PC » : lire la ligne « Ce PC : … » ; essayer Petit PC puis une revue ; revenir à Automatique  
  → La ligne dit tes cœurs, ta mémoire et « PC normal » (ton i7) ; en Petit PC, la revue n'ouvre qu'un seul stockfish.exe (Gestionnaire des tâches) et reste fluide ; un choix de puissance d'analyse fait à la main est gardé.

## En ligne (Steam)

- [ ] **R-100** – Jouer en ligne sans Steam lancé  
  → Message clair « Ouvre Steam… », le jeu ne plante pas.
- [ ] **R-101** – Lancer le jeu deux fois : Test : héberger / Test : rejoindre  
  → Les deux fenêtres se connectent, la partie démarre.
- [ ] **R-102** – Avec un ami (deux PC) : inviter, choisir cadence et couleur, jouer  
  → Coups, pendules et chat synchronisés ; overlay Maj+Tab.
- [ ] **R-104** – En ligne : bouton NULLE (à la place de MENU), l'ami accepte avec son bouton NULLE  
  → Partie nulle des deux côtés ; si l'ami joue un coup au lieu d'accepter, la proposition est oubliée.
- [ ] **R-105** – Après une partie en ligne : Mes parties  
  → La partie y est (avec ton camp et le résultat) et se revoit avec l'analyse ; l'Elo ne bouge pas.
- [ ] **R-103** – Revanche, abandon, un joueur qui ferme le jeu  
  → Revanche couleurs inversées ; abandon et départ donnent le bon résultat.
- [ ] **R-106** – Ton ami (SickChess déjà OUVERT) accepte ton invitation Steam, ou tape le code  
  → Il arrive dans ton salon en quelques secondes ; avec le numéro de test 480, accepter quand SickChess est fermé ouvrirait « Spacewar » : c'est normal.
- [ ] **R-107** – Claude Code : python outils/verifier_en_ligne.py (Steam ouvert)  
  → Fichiers, connexion Steam, salon créé avec son code, tests réseau : tout en ✅ dans docs/VERIFICATION_EN_LIGNE.md.
- [ ] **R-108** – Fin d'une partie en ligne : regarder la carte de fin, puis cliquer « Revue de la partie »  
  → Carte : résultat, raison, « Précision : toi … – <ami> … » (après « Analyse en cours… »), boutons Revue, Revanche, Menu ; la revue s'ouvre de ton côté (plateau dans ton sens, noms « Toi » et ton ami), pastilles, flèches et variantes comme contre l'ordinateur ; l'ami ne voit pas ta revue.
- [ ] **R-109** – Pendant ta revue, l'ami demande une revanche ou écrit dans le chat ; puis Retour  
  → Un bandeau en haut de la revue annonce la revanche ; au retour, la carte propose « Accepter la revanche » et le chat contient son message ; la partie compte dans Statistiques et ses fautes dans « Mes erreurs » une fois l'analyse finie.
- [ ] **R-10A** – SickChess ouvert au menu : un ami Steam t'invite (depuis son salon SickChess ou Maj+Tab)  
  → Un petit son, et en haut « <ami> t'invite à jouer » avec Rejoindre / Plus tard ; Rejoindre : tu arrives dans son salon.
- [ ] **R-10B** – Même chose pendant les Problèmes, une revue ou l'analyse libre ; cliquer Rejoindre  
  → L'écran se ferme et tu arrives dans le salon de l'ami.
- [ ] **R-10C** – Même chose pendant une partie contre l'ordinateur ; Rejoindre, puis « Rester » ; recommencer et confirmer « Rejoindre »  
  → Une fenêtre demande « Rejoindre <ami> ? », la pendule s'arrête ; Rester : la partie continue ; Rejoindre : salon de l'ami, et plus tard « Reprendre la partie » dans le menu la retrouve.
- [ ] **R-10D** – « Plus tard » sur le bandeau (ou ne rien faire 45 s), puis Menu → Jouer en ligne  
  → Le bandeau disparaît ; « INVITATIONS REÇUES » liste l'invitation (« il y a N min ») avec Rejoindre, pendant 10 minutes.
- [ ] **R-10E** – Sans ami : Jouer en ligne → « Test : invitation », puis Retour au menu  
  → « Ami de test t'invite à jouer » apparaît dans le menu (Rejoindre mène à un salon qui n'existe pas : message clair).

## Version amis et mises à jour

- [ ] **R-110** – CONSTRUIRE_VERSION_AMIS.bat  
  → Une version est fabriquée ; SickChess_Installation.exe (ou SickChess_amis.zip) est le fichier à donner à un nouvel ami.
- [ ] **R-111** – Sur un PC sans Python : dézipper, lancer SickChess.exe  
  → Le jeu démarre ; Windows ne le bloque pas (ou propose « Exécuter quand même »).
- [ ] **R-112** – Bouton Mise à jour après une nouvelle version  
  → Il s'allume, ne télécharge que ce qui a changé, garde profil et réglages.
- [ ] **R-113** – Chez un ami : double-clic sur SickChess_Installation.exe  
  → Aucune demande d'administrateur ; installation dans ses programmes, icône sur le Bureau ; le jeu démarre et on peut jouer contre l'ordinateur tout de suite. (Si Windows prévient « éditeur inconnu » : Informations complémentaires → Exécuter quand même.)
- [ ] **R-114** – Publier une nouvelle version, l'ami ouvre le jeu et reste dans le menu  
  → Le bouton affiche « Mise à jour : X % », puis « Nouvelle version prête », le jeu redémarre tout seul sur la nouvelle version ; profil et parties gardés ; jamais de redémarrage en pleine partie.
- [ ] **R-115** – Double-clic sur CONSTRUIRE_VERSION_AMIS.bat  
  → D'abord « Vérification avant une version pour les amis » : une ligne OK / A REVOIR / BLOQUANT par point (mode test, numéro Steam, licences, version, Git, tests, banc d'essai) ; s'il y a un BLOQUANT, rien n'est fabriqué ; sinon la version se fabrique, et le .exe est essayé dans un dossier neuf avant l'envoi.
- [ ] **R-116** – Mise à jour qui échoue : cliquer Mise à jour avec Internet coupé, puis Internet rétabli pendant qu'une version se publie  
  → Le message dit la vraie cause : « pas d'Internet, ou adresse du site … introuvable » (Internet coupé), « fichier de mise à jour introuvable sur le site (erreur 404) … réessaie dans quelques minutes » (publication en cours) ; plus jamais « pas de connexion » quand Internet marche.
- [ ] **R-117** – Un PC d'essai à la n° 7 ; publier la n° 8 puis la n° 9 ; ouvrir le jeu et rester au menu  
  → Le bouton affiche « Mise à jour n° 8 à 9 : X % » ; « Ce qui change » montre les notes de la n° 8 puis de la n° 9 ; les deux versions se téléchargent l'une après l'autre ; le jeu ne redémarre qu'une fois et affiche la n° 9 ; profil et parties gardés.
- [ ] **R-118** – Première installation (ou première mise à jour) de la n° 7 sur un PC qui n'a jamais eu SickChess, réseau Wi-Fi « Public »  
  → Windows demande une fois « Autoriser cette application à apporter des modifications ? » ; Oui : pare-feu Windows → règles « SickChess » (entrée et sortie, tous les profils) ; relancer : plus aucune demande ; Non : le jeu marche, il redemandera à la version suivante.
- [ ] **R-119** – Sur un réseau dont le DNS ne marche pas (Paramètres réseau → DNS manuel 10.255.255.1), laisser le jeu au menu  
  → La mise à jour passe quand même ; journal_du_jeu.txt : « [MAJ] DNS du PC sans reponse pour github.com : adresse obtenue par DNS securise » ; remettre le DNS automatique ensuite.

## Solidité

- [ ] **R-120** – Renommer moteur/stockfish.exe puis lancer une partie contre l'ordinateur  
  → Message clair, retour au menu ; la partie à deux et les problèmes marchent toujours. (Remettre le nom.)
- [ ] **R-121** – Couper Internet  
  → Tout marche sauf l'en ligne et la mise à jour, qui le disent clairement (mise à jour : « pas d'Internet, ou adresse du site … introuvable »).
- [ ] **R-122** – Jouer 5 parties à la suite sans relancer le jeu  
  → Pas de ralentissement, pas de son qui disparaît, l'ordinateur reste rapide.
- [ ] **R-123** – Après chaque test : ouvrir journal_du_jeu.txt  
  → Aucune ligne « Traceback » ni « ERREUR ».
- [ ] **R-124** – Dans un terminal, dans le dossier du jeu : python SickChess.py --plantage-test (le jeu se ferme tout de suite), puis relancer le jeu normalement  
  → Au lancement : « La dernière fois, SickChess s'est fermé à cause d'une erreur » ; « Envoyer le rapport » ouvre Signaler déjà rempli (message + journal du plantage) ; « Non merci » efface ; Échap : reproposé (3 fois au plus).
- [ ] **R-126** – Faire une revue, revenir au menu et ne rien toucher pendant 3 minutes (Gestionnaire des tâches ouvert)  
  → Au bout de 2 minutes, les stockfish.exe d'analyse disparaissent (il en reste un : l'adversaire) et la mémoire redescend de plusieurs Go ; rouvrir la même revue : tout est là (pastilles, précision) ; une nouvelle revue démarre normalement.
- [ ] **R-125** – Quitter une partie pendant que l'ordinateur réfléchit ou que l'analyse tourne, puis relancer une partie contre l'ordinateur  
  → Retour au menu aussitôt (pas de fenêtre figée) ; Stockfish redescend à 0 % dans le Gestionnaire des tâches ; la nouvelle partie se lance tout de suite et l'ordinateur joue normalement.

## Graphisme et textes

- [ ] **R-130** – Passer sur tous les écrans (menu, réglages, partie, fin, revue, mes parties, problèmes, options, en ligne)  
  → Style Onyx & Or partout, accents corrects, aucun texte coupé ou qui dépasse.
- [ ] **R-132** – Prendre une pièce ; faire mat ; se faire mater ; ouvrir les écrans  
  → Petite onde blanche sur la case de la prise ; au mat : halo rouge sur le roi maté et confettis si tu gagnes (pas si tu perds) ; chaque écran arrive en fondu.
- [ ] **R-131** – Essayer les 6 jeux de pièces sur les damiers clairs et sombres  
  → Toutes les pièces se lisent bien, blanches comme noires.
