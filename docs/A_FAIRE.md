# SickChess – À faire

Fichier partagé entre Cowork et Claude Code. **À relire au début de chaque séance,
à mettre à jour à la fin.** La page « SickChess – À faire »
(https://claude.ai/artifact/PzJkQy7b8DKRs9wgksP9T5) en est la version à cocher pour Julien.
Mis à jour le 24/10/2026.

## Retours de Julien à traiter (priorité)
- [x] Analyses gardées (fichier `.analyse.json` à côté du PGN), pastilles stables, analyse
      pendant la partie, revue au coup 1, sacrifices non punis – faits et validés le 17/10.
- [x] Sons des pièces : chocs de bois enregistrés (Kenney CC0) – validés.
- [ ] Son de réussite des problèmes « pas ouf » → refait le 17/10 (marimba), à valider.
- [ ] Version amis : « pourquoi j'ai 5 zip ? » → normal (voir réponse du 17/10 dans le journal).
- [ ] 17/10 soir : « Stockfish joue à ma place dans la revue, stats pas fiables face à chess.com,
      analyse plus précise (profondeur 30) et plus rapide » → revue refaite le 18/10 (journal (11)) :
      à valider sur son PC, surtout le TEMPS d'analyse à profondeur 30.
- [ ] 18/10 : « analyse à la profondeur ou au temps ? » → choix de Julien : plusieurs modes, calcul fixe
      par défaut (journal (13)). À valider : t67, t68 ; mesure t69 par Claude Code.

## Recette complète (stabilité)
- `docs/RECETTE.md` : 71 tests à la main sur tout le jeu (R-001 à R-131), source dans
  `outils/recette.py`. Recopiés dans la page, groupe « Recette complète »
  (Fonctionne / Ne fonctionne pas + commentaire, bouton « Nouvelle passe »).
- Tenue à jour à chaque séance ; passe complète avant chaque version amis / Steam.
- [ ] Première passe complète par Julien.

## Travaux proposés (Julien choisit dans la page « À faire », groupe « Travaux proposés »)
22 propositions (p01 à p22) : variantes dans la revue, rejouer d'ici, fautes expliquées,
problèmes tirés de ses gaffes, statistiques, ouvertures, modes de problèmes, adversaire
humain, partie classée / entraînement, menu pause, premier lancement, anglais, finitions,
musique, packs de sons, bouton « Signaler », test sur PC neuf, en ligne, succès Steam,
page Steam, démarches Steamworks, licence des pièces Classique.
→ Lire les choix (`statut` = `veux` / `non` + commentaire) avant de choisir la séance suivante.
→ p04 (Mes erreurs) et p01 (variantes) faits le 17/10.

→ 18/10 (16) : 5 nouvelles propositions pour garder les joueurs sans attente (p23 à p27 : moments clés
  d'abord, « Trouve mieux », analyse en tâche de fond, objectif pour la partie suivante, résumé du coach).

## Performance et ménage (banc d'essai du 23/10, page « SickChess – Banc d'essai »)
Mesures faites dans Cowork (machine Linux plus lente) : à refaire sur le PC de Julien
(`python outils/banc_essai.py`, puis `python outils/surveiller.py` en jouant).
- [x] (23/10, journal 17) **Fichiers relus à chaque image** (le plus rentable) : `entrainement.charger_progression`
      (24 lectures par image dans Ouvertures, 44–51 ms par image), `modes_problemes.charger`
      (Problèmes), `succes.obtenus` (Statistiques). Lire une fois, garder en mémoire.
- [x] (23/10, journal 17-18) **Cache des textes** dans `ui.py` (`texte` / `rogner`) : `font.size` + `font.render` =
      40 à 60 % du temps d'une image sur Partie, Revue, Options, Mes parties.
- [x] (23/10, journal 17-19 : 30 images/s au repos, partie 9 % d'un cœur) **Ne pas redessiner au repos** : une partie arrêtée prend ~50 % d'un cœur (machine
      Cowork) ; redessiner seulement si quelque chose change, 30 images/s au repos.
- [x] (23/10, journal 19) Stockfish d'analyse en priorité basse (le jeu reste fluide pendant une revue).
- [ ] Ménage : ~~8 imports/variables inutiles~~ faits le 23/10 ; `jeu/fond_anime.py` jamais
      importé, ~100 fonctions peut-être mortes à vérifier une par une (skill `menage-code`).
- [x] (23/10, retiré) Réglage `ia_suivre_la_pendule` de config.json lu nulle part : le reprendre ou l'enlever.
- [x] (23/10) Commit : 34 fichiers modifiés non enregistrés + 1 commit pas encore envoyé sur GitHub.
→ Avant de commencer, lire les décisions de Julien dans la page (Corriger / OK / Ignorer).

→ 23/10 (soir) : banc d'essai tout vert sur le PC de Julien (sauf ménage). 7 nouvelles propositions
  qualité (p28 à p34) : test d'endurance de 2 h, rapport de plantage, banque de positions pour la
  précision des pastilles, mode « petit PC », vérification avant chaque version, lisibilité
  (daltoniens, petits écrans), niveaux de l'ordinateur calibrés en vrai Elo. Julien choisit.

## Demandes de Julien du 24/10 (testé avec l'installeur) – EN PREMIER
0. [x] (24/10, publié en n° 3) **Installeur complet** (fait côté code le 24/10 dans Cowork : problèmes + finales dans
       l'installeur, ~700 Mo). Claude Code : `py outils/publier_maj.py --installeur-seul` (refait
       l'installeur de la n° 2 et le remplace en ligne), puis essai silencieux comme d'habitude
       (skill `version-amis`) : Problèmes et finales disponibles dès le premier lancement.
1. [ ] **p35 – Analyse libre** (nouvelle entrée du menu, recette + tests) :
       - un échiquier où l'on joue librement les deux camps (glisser, clic-clic, retour arrière,
         flèches ← →, retournement F), avec une **feuille de coups à variantes** ;
       - **éditeur de position** : palette des 12 pièces, gomme, « position de départ »,
         « vider », trait aux Blancs / Noirs, roques et prise en passant déduits ou cochés,
         position illégale refusée avec la raison (python-chess `is_valid`) ;
       - **coller un FEN ou un PGN** (presse-papiers), et « Analyser cette position » depuis la
         revue, Mes erreurs et les problèmes ;
       - **moteur en continu** : barre d'avantage, évaluation, 3 meilleures lignes (MultiPV)
         avec profondeur qui monte, flèche du meilleur coup, tables Syzygy en finale ;
         marche / arrêt (touche Espace), puissance des Options ; Stockfish en priorité basse,
         arrêté en quittant l'écran (banc d'essai : processeur à l'arrêt quand le moteur est coupé) ;
       - reprendre ce qui existe : plateau de la partie, `ecran_revue` (barre, flèches),
         `analyse_partie` / `moteurs.py`, `charger_position.py` de V8 pour le FEN ;
       - enregistrer la ligne dans Mes parties (PGN) et copier le FEN.
2. [ ] **p36 – Invitation d'un ami visible dans le jeu** : quand un ami Steam t'invite pendant
       que SickChess est ouvert (menu, partie, problèmes…), un bandeau en jeu « <nom> t'invite à
       une partie – Rejoindre / Plus tard » (son discret). Steam : rappel `LobbyInvite_t` (n° 503 :
       ami, salon, jeu ; 24 octets) à ajouter dans `jeu/steam.py` (`_lire`) → évènement
       « invitation_recue ». Rejoindre en pleine partie contre l'ordinateur = demander
       confirmation (la partie est sauvegardée). Plus tard = rappel dans l'écran « Jouer en
       ligne » (liste des invitations reçues). Ne marche qu'avec Steam ouvert ; testable seul avec
       un 2e compte sur un autre PC, sinon test automatique avec un faux Steam.
3. [ ] **p37 – Classements et succès Steam** :
       - **classements** (classement des problèmes, meilleur score Contre la montre et Survie) via
         `ISteamUserStats` FindOrCreateLeaderboard / UploadLeaderboardScore /
         DownloadLeaderboardEntries (Global, Amis, Autour de moi) ; écran « Classements » dans
         Problèmes avec les noms Steam ; ces appels marchent déjà avec le numéro de test 480,
         donc testables dès maintenant ;
       - **succès** : les 14 de `docs/SUCCES_STEAM.md` sont déjà gérés dans le jeu (écran Succès) ;
         pour qu'ils s'affichent DANS Steam, il faut le vrai numéro du jeu et les déclarer dans
         Steamworks (p21 : compte + 100 $). Préparer le fichier de déclaration
         (noms, descriptions, icônes 64×64 dorées) pour que ce soit 10 minutes de travail ce jour-là.

## Version amis et jeu en ligne (23/10 soir) – AVANT les travaux p30…
1. [x] Claude Code : `winget install JRSoftware.InnoSetup` et `winget install GitHub.cli` + `gh auth login`.
2. [x] Claude Code : `python outils/verifier_en_ligne.py` (Steam ouvert) → tout ✅.
3. [x] (23/10, n° 1 publiée) Claude Code : version amis avec installeur (skill `version-amis`) : essai silencieux, lancement,
       vérification en ligne sur le dossier d'essai, puis publication ; donner le lien à Julien.
4. [ ] Julien + un ami : vraie partie en ligne sur deux PC (R-102 à R-107).
5. [ ] Plus tard (avant la vente) : certificat de signature de code → `"signature"` dans maj_config.json.

## Travaux choisis par Julien le 23/10 (statut « veux ») – ORDRE DES SÉANCES
Une séance = un travail (skill `seance-sickchess`), tests + banc d'essai avant/après, recette mise
à jour, tests pour Julien dans la page « À faire ». Phrase à Claude Code : « fais le travail pXX ».
1. [x] (24/10, séance 26) **p30 – Banque de positions** (`tests/positions_revue.json`, 50–100 positions : vrais
       sacrifices, vraies gaffes, mats, finales Syzygy, + m04 « bon sacrifice ») ; 8e contrôle
       « precision » du banc d'essai. À faire en premier : protège tout le reste.
2. [x] (24/10, séances 27 et 28) **p29 – Rapport de plantage** (erreur + fin du journal gardées, proposées au lancement
       suivant via « Signaler »), puis **p28 – Test d'endurance** (`outils/endurance.py` : robot
       2 h, mémoire, plantages, ralentissements ; section « endurance » du banc, hors --rapide).
3. [x] (24/10, séance 29) **p32 – Vérification avant chaque version** (`outils/verifier_version.py`, appelé par
       CONSTRUIRE_VERSION_AMIS.bat : tests, banc, MODE_TEST, appid, licences, version, .exe neuf).
4. [x] (24/10, séance 30) **p31 – Mode « petit PC »** (détection cœurs / mémoire au 1er lancement → puissance
       d'analyse, hachage, animations ; modifiable dans Options).
5. [ ] **p34 – Niveaux en vrai Elo** (matchs automatiques contre des références, à lancer la nuit
       sur le PC de Julien ; table de calibrage dans le code, test qui la vérifie).
6. [x] **p27 – Résumé du coach immédiat** (**fait le 24/10, séance (31)**) (carte de fin : ouverture, plus gros moment, précision
       provisoire, comparaison avec les 10 dernières parties).
7. [x] **p33 – Lisibilité pour tous** (**fait le 24/10, séance (32)**) (pastilles reconnaissables sans couleur, contrastes,
       1366×768 et 4K ; relecteur-interface).
→ 24/10 : nouvelles demandes de Julien (page « À faire », statut « veux ») : p35 Analyse libre (**faite le
  24/10, séance (23)**), p36 invitation d'un ami affichée dans le jeu
  (**faite le 24/10, séance (24)**), p37 classements et succès Steam (**faite le 24/10, séance (25)**).
Toujours en attente de décision : p21 Steamworks (le délai de 30 jours ne démarre qu'au paiement),
p20 page Steam (icônes des succès prêtes : `docs/steam_succes/`), p22 licence des pièces Classique, p02, p09, p17, p23–p26.

## Prochaines étapes (dans l'ordre)
1. **Compilation en .exe** (PyInstaller, skill `compiler-exe`) – à faire dans Claude Code
   sur Windows.
2. Revue : jouer des variantes ; statistiques par tranche d'Elo (`statistiques.py` de V8).
3. Options accessibles en pleine partie.
4. Entraînement aux ouvertures et aux faiblesses (`ecran_entrainement`, `faiblesse`).
5. Bouton « Signaler un problème / Proposer une idée ».
6. Multijoueur : proposer la nulle, parties en ligne dans « Mes parties », spectateurs.
7. Problèmes : classement en ligne (Steam), classement dans « Mes parties et profil ».
8. Page Steam : captures et capsules (skill `captures-steam`).

## À tester par Julien (sur son PC)
- [ ] t101 (28) : **quitter et lancer vite** : pendant que l'ordinateur réfléchit (niveau Maximum, longue cadence),
      clique Quitter la partie → le menu revient aussitôt ; dans le Gestionnaire des tâches, stockfish.exe redescend
      à 0 % ; relance une partie contre l'ordinateur → elle démarre tout de suite. Même chose pendant une revue, puis
      bouton Quitter du jeu (et la croix) : le jeu se ferme en moins d'une seconde, sans « ne répond pas ».
- [ ] t78 (26) : couper Internet, cliquer Mise à jour → le message dit « pas d'Internet, ou adresse du site … introuvable » (et plus « pas de connexion » quand Internet marche) ; rétablir Internet → la mise à jour marche.
- [ ] t100 (32) : la revue sur ton écran : les symboles des pastilles (surtout Imprécision jaune, Excellent vert
      clair) ont un fin contour sombre : plus lisibles ? toujours jolis ? Si tu as un écran 2560×1440 ou une télé
      4K : plein écran (F11), tout est-il à la bonne taille ?
- [ ] t99 (31) : finis une partie contre l'ordinateur : sur la carte de fin, trois lignes du coach (ouverture, ton
      plus gros moment avec le coup qu'il fallait jouer, précision « provisoire » puis comparée à tes 10 dernières
      parties). Utile ? Lisible ? Rien ne chevauche les boutons ?
- [ ] t98 (30) : Options → Affichage → « Puissance du PC » : la ligne dit « Ce PC : 12 cœurs, … → PC normal » ;
      choisis Petit PC, ouvre une revue : un seul stockfish.exe (Gestionnaire des tâches), jeu fluide ; reviens à
      Automatique. Si un ami a un petit portable : le jeu est-il plus fluide chez lui ?
- [ ] t97 (29) : double-clic sur CONSTRUIRE_VERSION_AMIS.bat : la vérification passe d'abord (OK / A REVOIR /
      BLOQUANT) ; la version ne se fabrique que sans BLOQUANT ; le .exe est essayé avant l'envoi. Clair ?
- [ ] Claude Code (PC) : `python outils/endurance.py` (2 h, la nuit) → docs/ENDURANCE.md ; dire à Julien le verdict.
- [ ] t96 (27) : dans un terminal, dossier du jeu : `python SickChess.py --plantage-test` (le jeu se ferme), puis
      relance le jeu : carte « La dernière fois, SickChess s'est fermé… » ; « Envoyer le rapport » ouvre Signaler
      déjà rempli ; envoie (ou Non merci) : la carte ne revient plus.
- [ ] t95 (26) : importe (Mes parties → Importer) une partie qui commence à une autre position (PGN avec
      [FEN "…"]) dont le 1er coup est une gaffe : sa revue le note Gaffe, pas « Théorique » (R-06I).
- [ ] Claude Code (PC) : `python outils/recette_auto.py` et `python outils/banc_essai.py --sections precision`
      (relance programmée à 4 h 20), puis version amis.
- [ ] t92 (25, Steam ouvert) : Problèmes → « Classements Steam » : les trois classements et les trois vues se
      chargent ; ta ligne « Toi » en or (après un premier score). Lisible ? Rapide ?
- [ ] t93 (25) : fais un contre la montre puis rouvre les classements : ton score y est (Actualiser si besoin) ;
      même chose avec une survie et un problème classé.
- [ ] t94 (25) : Steam fermé : l'écran le dit et montre tes scores ; joue un contre la montre ; relance le jeu
      Steam ouvert : ton record apparaît dans le classement sans rien refaire.
- [ ] Regarder `docs/steam_succes/apercu.png` : les icônes des succès te plaisent ? (à refaire avec Cowork sinon)
- [ ] t88 (24, sans ami) : Jouer en ligne → « Test : invitation », puis Retour : dans le menu, « Ami de test
      t'invite à jouer » avec un petit son ; « Plus tard » le range ; Jouer en ligne le montre dans
      « INVITATIONS REÇUES ».
- [ ] t89 (24, avec un ami) : SickChess ouvert au menu, ton ami t'invite depuis son salon : bandeau en haut ;
      « Rejoindre » → tu arrives dans son salon et la partie se lance normalement.
- [ ] t90 (24, avec un ami) : même chose pendant les Problèmes (ou une revue) : l'écran se ferme, salon de l'ami.
- [ ] t91 (24, avec un ami) : même chose pendant une partie contre l'ordinateur : « Rejoindre <ami> ? »,
      pendule arrêtée ; Rester continue ; Rejoindre → salon, et ensuite « Reprendre la partie » dans le menu.
- [ ] t82 (23) : Menu → Analyse libre : en quelques secondes, 3 lignes de Stockfish, « profondeur » qui monte,
      flèche bleue ; joue des coups des deux camps : Stockfish suit chaque coup aussitôt ; le jeu reste fluide.
- [ ] t83 (23) : clique sur une des 3 lignes (son premier coup est joué) ; Espace : « Relancer » en or et le
      processeur redescend (Gestionnaire des tâches) ; Espace : ça repart.
- [ ] t84 (23) : copie un FEN sur lichess (Partager) puis Ctrl+V ; copie une partie PGN puis Ctrl+V ; C copie
      le FEN et lichess.org/analysis affiche la même position.
- [ ] t85 (23) : Éditer (E) : vide le plateau, pose rois / tours / pions, essaie une position impossible
      (message), coche un roque, « Analyser ». L'éditeur est-il facile à utiliser ?
- [ ] t86 (23) : revue d'une partie → un coup → « Analyser (A) » : même position ; Retour : la revue revient
      au même coup. Les 4 boutons du bas de la revue tiennent bien sur ton écran ?
- [ ] t87 (23) : avec le dossier syzygy/ : colle `8/8/8/4k3/8/8/4P3/4K3 w - - 0 1` → « Tables de finale :
      les Blancs gagnent » ; laisse 2 min sur une position : « analyse terminée », plus de stockfish.exe
      d'analyse libre après Retour.
- [ ] Claude Code (PC) : commit / envoi de la séance (23) si pas fait dans le cloud, puis version amis.
- [ ] t78 (21, à deux) : finir une partie en ligne : la carte montre « Analyse en cours… » puis
      « Précision : toi … – <ami> … », et les boutons Revue de la partie / Revanche / Menu (R-108).
- [ ] t79 (21, à deux) : cliquer « Revue de la partie » : revue dans ton sens, noms « Toi » et ton ami,
      pastilles, flèches, variantes ; l'ami, lui, reste sur sa carte de fin.
- [ ] t80 (21, à deux) : pendant ta revue, l'ami demande la revanche et écrit dans le chat : bandeau en haut ;
      au retour « Accepter la revanche » marche, couleurs inversées (R-109).
- [ ] t81 (21) : après une partie en ligne analysée : elle compte dans Statistiques ; ses fautes arrivent dans
      Problèmes → « Mes erreurs ».
- [ ] t77 (19) : surveillance en direct, une partie puis sa revue : jeu fluide pendant l'analyse ; après la
      revue, mémoire de Stockfish ≈ 2 Go (5,8 avant) ; menus moins gourmands.
- [ ] t75 (18) : revue : flèches des meilleurs coups, surlignages et pastilles comme avant ; défilement fluide.
- [ ] t76 (18) : partie : coups possibles d'une pièce, dernier coup surligné, plateau retourné (F) correct.
- [ ] t72 (17) : partie contre l'ordinateur : tout reste fluide (pièces, flèches, pendule, coups de l'ordinateur).
- [ ] t73 (17) : Gestionnaire des tâches → SickChess, partie où personne ne joue : processeur bien plus bas qu'avant.
- [ ] t74 (17) : Ouvertures et Problèmes : progression et records s'affichent et se mettent à jour.
- [ ] Page « Banc d'essai » : passer « Fichiers en double » en OK (voulu) ; dire si on pousse sur GitHub
      (publier/ et build_amis/ supprimés le 23/10).
- [ ] t64-t66 : revue – Stockfish ne joue plus, flèches bleues/vertes, export et comparaison chess.com.
- [ ] t67 : temps réel d'une revue complète (Calcul fixe, **Forte**, par défaut depuis le 18/10 (14)) ;
      la mesure prévoit environ 9 min pour 40 coups. « environ X min » juste ?
- [ ] t68 : Options → Partie → Façon d'analyser / Puissance ; « Forte » est sélectionné ; partie déjà
      analysée pas refaite.
- [x] t69 : mesure faite le 18/10 (`docs/MESURE_STOCKFISH.md`) ; décision de Julien : Forte et 3 × 4.
- [ ] t71 (16) : revue d'une longue partie importée (Forte) : ≈ 5 min pour 70 coups ? Ronds creux qui se
      remplissent, pastilles qui ne changent plus. Commit de la séance (16) par Claude Code.
- [ ] t70 : hachage 6 Go – les stockfish.exe prennent ~6 Go pendant une revue, le PC reste fluide ;
      noter la mémoire du PC (Gestionnaire des tâches → Performance → Mémoire).
- [x] Commit Git de la séance du 18/10 (13) par Claude Code (fusionné sur GitHub, PR n° 1).
- [ ] Problèmes → « Mes erreurs » : tes gaffes deviennent des problèmes (parties dont la revue a été ouverte).
- [ ] Revue : jouer une variante sur l'échiquier, Stockfish répond ; Échap pour revenir.
- [ ] Commit Git des séances du 17/10 (3) et (4) par Claude Code.
- [ ] Problèmes : nouveaux sons de réussite / d'erreur (marimba).
- [ ] Commit Git de la séance du 17/10 (3) par Claude Code (sons des problèmes, A_FAIRE, JOURNAL).
- [ ] Version amis : créer le dépôt GitHub `SickChess-amis` (public) + GitHub CLI
      (`winget install GitHub.cli` puis `gh auth login`). Voir `docs/VERSION_AMIS.md`.
- [ ] Double-clic CONSTRUIRE_VERSION_AMIS.bat → release n°1 sur GitHub ?
- [ ] SickChess_amis.zip dézippé sur le Bureau : SickChess.exe démarre ? « Mise à jour »
      télécharge moteur + problèmes + finales, puis le jeu redémarre ?
- [ ] Petite modif + nouveau .bat : le bouton s'allume « Mise à jour disponible ! »,
      ne télécharge que le paquet « jeu », profil et réglages gardés ?
- [ ] Multijoueur sur un seul PC : lancer le jeu deux fois, « Test : héberger » /
      « Test : rejoindre ». (Pas encore fait : pas d'adversaire humain.)
- [ ] Multijoueur Steam avec un ami (deux PC) ; l'overlay Maj+Tab s'ouvre-t-il ?

## Démarches (plus tard)
- [ ] Compte Steamworks (partner.steamgames.com) ; identité, banque, fiscal (15–30 jours).
- [ ] Payer les 100 $ Steam (lance le délai de 30 jours avant sortie).
- [ ] Compte itch.io (gratuit).
- [ ] Avant la sortie : `MODE_TEST = False` dans `jeu/salon_en_ligne.py` ; vrai
      `steam_appid.txt` (480 = numéro de test de Valve).

## Fait récemment
- 24/10 (30) : mode « petit PC » (p31) : détection, Options → Puissance du PC, analyse et effets allégés.
- 24/10 (29) : vérification avant chaque version (p32), lancée par CONSTRUIRE_VERSION_AMIS.bat.
- 24/10 (28) : test d'endurance (p28) : robot de 2 h, section « endurance » du banc ; essais cloud verts.
- 24/10 (27) : rapport de plantage (p29) : erreur + journal gardés, proposés au lancement suivant via Signaler.
- 24/10 (26) : banque de positions (p30) : 114 coups jugés justes ; défaut « gaffe notée Théorique » corrigé ;
  recette automatique (`outils/recette_auto.py`).
- 24/10 (25) : classements Steam (problèmes, contre la montre, survie ; mondial, amis, autour de moi) et
  succès préparés pour le vrai numéro Steam (rattrapage, icônes, notice) (p37).
- 24/10 (24) : invitation d'un ami Steam affichée dans le jeu (p36) : bandeau sur tous les écrans,
  confirmation en partie (partie gardée), liste « Invitations reçues » dans Jouer en ligne.
- 24/10 (23) : analyse libre (p35) : les deux camps, Stockfish en continu (3 lignes), éditeur de position,
  FEN / PGN, tables de finale, « Analyser » depuis la revue.
- 18/10 (13) : analyse en calcul fixe par défaut (comme lichess), profondeur et temps au choix,
  temps restant affiché, outil de mesure de Stockfish.
- 17/10 : son réparé chez Julien, analyse en tâche de fond (précision immédiate),
  notation au choix (anglaise par défaut), promotion dans les problèmes, logo et icône.
