# SickChess – À faire

Fichier partagé entre Cowork et Claude Code. **À relire au début de chaque séance,
à mettre à jour à la fin.** La page « SickChess – À faire »
(https://claude.ai/artifact/PzJkQy7b8DKRs9wgksP9T5) en est la version à cocher pour Julien.
Mis à jour le 31/10/2026 (séance (48) – installeur sous 1 Go, version amis n° 11, 0.6.0).

## Demande de Julien du 31/10 – itch.io : jeu en ligne et classements sans le n° 480 (Claude Code) – EN PREMIER
Constat (Cowork, 31/10) : tout le jeu en ligne et les classements passent par Steam avec le numéro de
test **480** (« Spacewar » de Valve). C'est bien pour les tests entre amis, **pas pour un jeu vendu** :
classements partagés avec tous les développeurs qui testent sur 480 (scores mélangés, peuvent être
effacés), invitation qui ouvre « Spacewar », profil Steam qui affiche « joue à Spacewar ». Et un
acheteur itch.io n'a pas forcément Steam. Le vrai numéro Steam arrivera avec le compte Steamworks
(démarche de Julien, 100 $) : ce travail-ci prépare tout pour que ce jour-là il n'y ait qu'un chiffre à changer.

Travail (petites étapes, jeu jouable après chacune, tests verts, journal, commit) :
1. [ ] **Audit d'abord, sans rien changer** : lister tout ce qui dépend de Steam / 480 /
       `steam_appid.txt` / `steam_api64.dll` (`jeu/steam.py`, `partie_en_ligne.py` qui démarre Steam
       dès que le jeu est compilé, `classements.py`, succès, `salon_en_ligne.py`, `outils/publier_maj.py`,
       `outils/verifier_version.py`, skill `compiler-exe`). Résumer à Julien en 5 lignes simples.
2. [ ] **Un seul réglage « distribution »** : `amis` / `steam` / `itch`, à un seul endroit, écrit au
       moment de la compilation. Le numéro Steam lu à un seul endroit (480 pour `amis`, le vrai numéro
       pour `steam`, aucun pour `itch`).
3. [ ] **Version itch** : ni `steam_api64.dll` ni `steam_appid.txt` dans le paquet ; Steam jamais démarré,
       même si Steam est ouvert sur le PC. « Jouer en ligne » et « Classements » : un message clair
       et joli (pas d'erreur), partie à deux sur le même PC toujours là. Records et classement
       personnels gardés dans le jeu et visibles. Ne pas supprimer le code Steam.
4. [ ] **Version amis** : rien ne change (480, comme aujourd'hui). **Version Steam** : rien ne change
       sauf le numéro ; `verifier_version.py --steam` bloque toujours 480 et `MODE_TEST = True`.
5. [ ] `outils/verifier_version.py --itch` : bloquant si un fichier Steam est dans le paquet ou si
       `MODE_TEST = True`. Compilation : zip `SickChess_<version>_itch.zip` à part.
6. [ ] Tests (faux Steam) : `tests/test_distribution.py` dans `SERIES` : en `itch`, Steam n'est jamais
       démarré, les écrans en ligne / classements s'ouvrent et se ferment sans planter ; en `amis` et
       `steam`, tout comme avant. `python tests/lancer_tous.py` tout vert.
7. [ ] Textes : accents, clés dans `langue_en.py`. Docs : `SORTIE.md`, `MULTIJOUEUR_STEAM.md`,
       `SUCCES_STEAM.md`, recette (`outils/recette.py`), `CREDITS` si un import change, journal,
       tests pour Julien dans « À tester par Julien ».
Ne PAS faire sans l'accord de Julien : créer un serveur à nous (coût, entretien, triche), toucher aux
règles, passer `MODE_TEST` à False pour les amis, `git push --force`.
**Question à poser à Julien à la fin** (expliquer simplement) : pour que les acheteurs itch.io jouent
aussi en ligne, soit on leur donne **une clé Steam** avec leur achat (itch.io sait le faire, une fois
le vrai numéro Steam obtenu ; rien à coder de plus), soit on fait **notre propre serveur** (plus long,
payant, à surveiller). Conseil : la clé Steam.

## Retours de Julien à traiter (priorité)
- [ ] **25/10 – mise à jour chez l'ami de Julien** (version n° 4 ou 5) : « vérifie ta connexion / site
      introuvable ». Le site marche (vérifié par Cowork le 25/10 : latest → v0.2.0-n6, maj.json téléchargé). Donc
      blocage sur le PC de l'ami (antivirus, pare-feu, DNS, VPN). Attendre son journal_du_jeu.txt (ligne [MAJ]).
      **Règle de Julien (25/10) : l'ami ne doit JAMAIS aller sur GitHub ; le jeu se met à jour et s'installe
      seul. Pas de bouton « Télécharger à la main ».** Fait par Cowork le 25/10 et **publié dans la n° 7**
      (25/10, JOURNAL (41)) : mises à jour une par une avec un seul redémarrage, réessais, DNS de secours,
      revérification toutes les 3 min, autorisation pare-feu (privé + public). Reste : t105 chez l'ami.
- [x] (25/10, Claude Code, JOURNAL (41) : relu, 1213 contrôles verts, commit 5406d04, n° 7 publiée avec la liste
      n° 1 à 7 ; reste l'essai réel du pare-feu = t106) **Claude Code (PC) – mises à jour une par une + pare-feu** : relire `jeu/mise_a_jour.py`,
      `jeu/pare_feu.py`, `SickChess.py`, `jeu/ecran_mise_a_jour.py`, `outils/publier_maj.py`,
      `outils/installeur_amis.iss`, `tests/test_maj_une_par_une.py` ; tous les tests (vrai Stockfish) ; sur le
      PC : lancer l'exe d'essai SANS `SICKCHESS_SANS_PARE_FEU` → une demande Windows → `netsh advfirewall
      firewall show rule name=SickChess` (entrée + sortie, profil Tous) ; commit ; puis version amis n° 7
      (sa liste `versions` doit contenir les n° 1 à 7). Ne jamais supprimer une ancienne release.
- [x] (25/10, Cowork, à vérifier par Claude Code + commit) **« la répétition ne compte pas »** (ami de Julien
      contre l'ordinateur, version n° 4 ou 5) : cause = le pré-mouvement partait avant la vérification de fin de
      partie (jeu/board.py `update`). Corrigé (`_verifier_fin` avant le pré-mouvement), tests/test_nulles.py
      partie 1 bis. Plan du jour dans la page « À faire », groupe « Aujourd'hui · 25/10 » (j01 à j08) :
      Julien précise le cas (j01), Cowork reproduit sur le PC (j02), Claude Code corrige avec un test qui joue
      chaque cas 20 fois (j03, `tests/test_nulles.py`). **Relu et commité le 25/10 (5406d04), dans la n° 7.**
- [ ] **25/10 – Recette, points rouges** :
      - [x] R-095 / R-096 « Signaler » arrive dans le salon Discord (séance 39) : bugs en **rouge**, idées en
            **vert**, plantages en **bleu** (choix de Julien), version + rapport en pièce jointe ; 3 messages de
            test envoyés et acceptés par Discord le 25/10. **L'adresse (webhook) n'est PAS dans Git** : sur le PC,
            Claude Code crée `signalement.json` à la racine du jeu (`{"signalement_webhook": "<adresse>"}`, adresse
            donnée par Julien dans la discussion cloud du 25/10) ; il part dans le paquet « jeu » de la version amis.
            **Fait le 25/10 sur le PC (adresse redonnée par Julien) : présent dans la n° 7.**
      - [x] R-114 « ne fonctionne pas en version 4 » (l'ami au menu ne reçoit pas la nouvelle version) : le jeu ne
            revérifiait que toutes les 20 min → 3 min (séance 37). À revérifier maintenant que la n° 7 est publiée.
      - [ ] Bugs et idées postés dans le salon Discord : Claude n'a pas accès à Discord → Julien les recopie.
- [ ] **24/10 – Défauts trouvés par Cowork sur le PC de Julien** (page « À faire », commentaires « Vérifié par Cowork ») :
      - [x] PLANTAGE t85 : éditeur de l'analyse libre en 1920×1080 (cases en nombres à virgule) → corrigé (séance 30).
      - [x] PLANTAGE t52 : rouvrir le Problème du jour déjà fait → corrigé (séance 30).
      - [x] Textes coupés (séance 36) : t51 explication des gaffes (cadre plus haut, 3 lignes), t52 / r01 messages
            et « tu as joué… » sur plusieurs lignes, t62 « BLA… » (mesure du texte traduit), aide F1 de la revue.
      - [x] t65 (séance 36) : « Nf3, Nf3 » en double et ordre des meilleurs coups ; clic sur un coup de la feuille :
            une pièce sélectionnée « mangeait » le clic → corrigé. ⚠ Le cas exact de Cowork n'est pas reproduit :
            à revérifier sur le PC.
      - [x] t57 (séance 36) : noms d'ouvertures (King's / Queen's / « Keene's » → français). « Ligne suivante » :
            **non reproduit** (marche en 1920×1080 et dans les tests) → à revérifier par Cowork.
      - [x] t54 (séance 36) : Ctrl+V ajoute au message (remplace toujours dans un champ court : code de salon) ;
            accents gardés (presse-papiers Windows en cp1252).
      - [x] r01 (séance 36) : une partie importée sans ton nom ne donne plus de « Mes erreurs ».
      - [x] t62 (séance 36) : « 55 %10olved » corrigé (« %% » mal lu), restes en français (reprise, haut de la revue).
      - [x] t52 (séance 36) : contre la montre / survie : après une faute, le bon coup est joué sous tes yeux
            (« Raté ! Il fallait Qxh2#… ») pendant 2,2 s.
      - [x] t98 (séance 36) : « → » remplacé par « : » (la police n'a pas ce signe).
      - [x] t71 / t99 : revue lente (17 coups : 7 min) et temps annoncé faux ; précision définitive ~2 min 30.
            (25/10, JOURNAL (43)) Temps annoncé : **fait** (écart < 25 % dès 20 % de l'analyse). Lenteur : **mesurée**
            (Forte, 17 coups = 1 min 30 à 3 min ; les 7 min venaient très probablement du réglage « Maximale » du
            dossier de dev) ; ~12 s + ~11 s gagnés. Reste : retest de Julien avec la version installée (test (43) n° 4).
      - [x] t100 : petites pastilles « ?! » / « ! » peu lisibles dans la feuille de coups. (25/10, JOURNAL (43) :
            plus grosses et contrastées, validées par Julien sur captures.)
      - [x] t56 : une partie à deux compte dans « Tes ouvertures » (voulu ?) → **pas un bug** (25/10, JOURNAL (43)) :
            en ligne contre soi-même sur un seul PC, la partie compte deux fois ; surveillé par `test_stats_a_deux`.
      - [ ] t68 : Enregistrer pas réagi une fois (pas reproduit, reste ouvert).
      - [x] Accents manquants (séance 36) : « Aucun coup joué », « … l'adversaire réfléchit », « %d problèmes
            joués », « Crée une partie » → corrigés, surveillés par `tests/test_textes_affiches.py`.
      - [x] Texte coupé : « Joue contre un ami Steam. Cree une partie et invite-le, ou entre… » (Jouer en ligne).
            (25/10, JOURNAL (43) : phrase entière en français et en anglais.)
      - [x] (25/10, JOURNAL (43), fait) Au menu principal, Échap ferme le jeu sans demander (deux fois par accident pendant les tests).
            **Décision de Julien (25/10)** : Échap ouvre « Quitter SickChess ? Oui / Non » (Non ou Échap = on reste).
      - **Autres décisions de Julien (25/10)** :
        - t71 revue lente : **accélérer sans baisser** « Forte » par défaut (mesure avant / après) ; si on
          n'atteint pas ~2 min 30, lui redemander.
        - t100 pastilles : **plus grosses et plus contrastées**, capture montrée à Julien avant de valider.
        - t56 : pas un bug (test en ligne contre soi-même sur un seul PC = la partie compte deux fois) ;
          surveillé par `tests/test_stats_a_deux.py`.
        - p34 (niveaux en vrai Elo) et grand ménage : **après la version amis n° 7**.
        - `_sauvegarde_cowork_2026-10-24/` : **gardée** pour l'instant (hors GitHub).
      - [x] Ne pas mettre dans Git : `_sauvegarde_cowork_2026-10-24/` et `rapports/` → dans `.gitignore` (25/10),
            aucun fichier suivi. Reste à Julien : garder ou supprimer la sauvegarde de Cowork.
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
- `docs/RECETTE.md` : 161 tests à la main sur tout le jeu (version du 25/10/2026), source dans
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
Séance du 31/10 (49) · promotion en pré-mouvement – **Fonctionne / Ne fonctionne pas + commentaire** (version amis 0.6.1).
- [ ] t139 (49) : **choisir la pièce d'une promotion préparée d'avance** : contre l'ordinateur, pendant qu'il réfléchit,
      amène ton pion sur la dernière rangée : le panneau **Dame / Tour / Fou / Cavalier** s'ouvre (avant : dame d'office).
      Choisis le cavalier (clic ou touche C) : quand c'est ton tour, c'est bien un **cavalier** qui apparaît.
- [ ] t140 (49) : sur ce panneau, **Échap** (ou clic à côté) : aucun coup n'est préparé ; tu peux en préparer un autre.

Séance du 31/10 (48) · installeur sous 1 Go – **Fonctionne / Ne fonctionne pas + commentaire** (version amis n° 11, 0.6.0).
- [ ] t136 (48) : **taille de l'installeur** : après CONSTRUIRE_VERSION_AMIS.bat, `SickChess_Installation.exe` fait
      **moins de 1 Go** (environ 100 Mo) ; la fenêtre noire dit « telecharges a l'installation : puzzles, syzygy ».
- [ ] t137 (48) : **installation chez un ami (Internet branché)** : double-clic sur l'installeur : une page montre le
      **téléchargement** des problèmes et des tables de finales (~1,2 Go, quelques minutes) ; à la fin, le jeu démarre,
      les **Problèmes** s'ouvrent et l'analyse d'une finale (ex. `8/8/8/4k3/8/8/8/1BN1K3 w - - 0 1`) dit « Tables de finale »,
      **sans passer par Mise à jour**.
- [ ] t138 (48) : **sans Internet** : coupe Internet, lance l'installeur : il dit qu'il n'arrive pas à télécharger et
      propose de réessayer ; rien de cassé (Annuler ne laisse pas de jeu à moitié installé).

Séance du 31/10 (46) · tables de finales DTZ – **Fonctionne / Ne fonctionne pas + commentaire** (version amis n° 11, 0.6.0).
- [ ] t129 (46) : **Stockfish voit les DTZ** : lance le jeu, ouvre l'analyse libre, quitte ; dans `journal_du_jeu.txt`
      (dossier SickChess) : « tables de finale Syzygy branchees … : 145 WDL et 145 DTZ ».
- [ ] t130 (46) : **règle des 50 coups** : analyse libre, colle `8/8/8/4k3/8/8/8/1BN1K3 w - - 0 1` → « Tables de finale :
      les Blancs gagnent », évaluation très haute ; colle `8/8/8/4k3/8/8/8/1BN1K3 w - - 60 1` → « Tables de finale :
      nulle », évaluation proche de 0 (le mat arriverait trop tard pour la règle des 50 coups).
- [ ] t131 (46) : **droit au mat** : colle `8/8/8/4k3/8/8/8/3QK3 w - - 0 1` et joue chaque fois le premier coup proposé
      par Stockfish (pour les deux camps) : mat en 10 coups environ, sans revenir en arrière ni tourner en rond.
- [ ] t132 (46) : **revue d'une partie qui finit en finale** (tour + pion contre tour, roi + pions…) : la revue va aussi
      vite qu'avant et les pastilles de la finale te semblent justes.

Séance du 31/10 (47) · pré-mouvements à la suite – **Fonctionne / Ne fonctionne pas + commentaire** (version amis n° 11, 0.6.0).
- [ ] t133 (47) : **plusieurs coups d'avance** : contre l'ordinateur (niveau fort, il réfléchit un peu), pendant son
      tour prépare 3 ou 4 coups à la suite (ex. d4, Cf3, Fc4, petit roque). Chaque coup prévu se voit **presque
      transparent** avec son numéro, la vraie pièce reste à sa place **un peu plus visible**. Un coup part à chaque
      tour, dans l'ordre.
- [ ] t134 (47) : **tout annuler** : prépare plusieurs coups puis **clic droit** n'importe où : tout disparaît d'un coup
      (pas de flèche tracée). Même chose avec Échap. Un clic droit sans coup prévu trace toujours les flèches.
- [ ] t135 (47) : **coup devenu impossible** : prépare un coup que l'ordinateur peut bloquer ou prendre : quand il
      devient impossible, rien n'est joué, petit son, et les coups suivants sont oubliés aussi. Essaie aussi en ligne.

Séance du 26/10 (45) · petites fenêtres – **Fonctionne / Ne fonctionne pas + commentaire** (version amis n° 10, 0.5.1).
- [ ] t124 (45) : **réglages en petite fenêtre** : réduis la fenêtre au plus petit (elle s'arrête à 900×560), Options →
      Affichage → Taille des textes « Très grande », puis Jouer contre l'ordinateur : NIVEAU, RYTHME, DURÉE et
      **VARIANTE (Normal / Freestyle)** sont tous visibles et cliquables. Même chose dans Jouer à deux.
- [ ] t125 (45) : **revue en petite fenêtre** : même fenêtre, ouvre la revue d'une partie avec les 4 tailles de textes :
      les deux **pourcentages** se lisent (en « Très grande », sur une seule ligne), les boutons ◀ ▶ ne recouvrent plus
      la courbe ni la liste des coups.
- [ ] t126 (45) : **redimensionner en cours de partie** : pendant une partie, puis une revue, agrandis / rétrécis la
      fenêtre à la souris : tout se recale aussitôt, l'échiquier reste carré. En plein écran (F11), l'échiquier et le
      panneau sont centrés ensemble (plus de grand vide entre les deux).
- [ ] t127 (45) : **fenêtre en hauteur** : rends la fenêtre plus haute que large : le panneau passe **sous**
      l'échiquier (partie, revue, analyse libre) ; en la rélargissant, il revient à droite.
- [ ] t128 (45) : **autres écrans** en petite fenêtre + « Très grande » : Problèmes (« Classements Steam » et
      « Retour » dans la fenêtre), Options, Mes parties, Jouer en ligne, Mise à jour : rien ne sort de l'écran, aucun
      texte minuscule.

Séance du 25/10 (44) · arbre des ouvertures – **Fonctionne / Ne fonctionne pas + commentaire** (version amis n° 9, 0.5.0).
- [ ] t118 (44) : **l'arbre** : Menu → Entraînement aux ouvertures. À gauche les premiers coups (1.e4, 1.d4, 1.c4…)
      toujours dans le même ordre ; clic sur « + » (ou flèche →) déplie coup par coup : 1.e4 › 1...e5 › 2.Nf3 ›
      2...Nc6 › 3.Bb5 « Partie espagnole » › 3...a6 « Partie espagnole › Défense Morphy ». Chaque ligne montre le
      code ECO et « réussies / total ». Des coups sans nom sont regroupés sur une ligne (ex. « 5...b5 6.Bb3 »).
- [ ] t119 (44) : **naviguer** : flèches ↑ ↓ → ←, + / −, molette, clic ; l'échiquier à droite montre la position du coup
      choisi ; le fil d'Ariane en haut (« Début › 1.e4 › … ») suit, et un clic sur un de ses morceaux y remonte.
- [ ] t120 (44) : **S'entraîner ici** : choisis 3...a6, Blancs, « S'entraîner ici » (ou Entrée) : toutes les lignes sont
      des suites de 3...a6, la plus jouée d'abord (« Ligne 1 / N »). Fais une faute sur une ligne : elle revient à la
      fin du tour (« à revoir 1 »). « Changer de groupe » ou Échap : retour à l'arbre, au même coup, et le compteur
      « réussies / total » a augmenté pour les lignes sans faute.
- [ ] t121 (44) : **au hasard dans ce groupe** : coche la case puis « S'entraîner ici » : ordre mélangé, mais jamais une
      ligne d'une autre ouverture.
- [ ] t122 (44) : **notation, langue, tailles** : Options → notation française : « 2.Cf3 Cc6 3.Fb5 » dans l'arbre et le
      fil d'Ariane ; en anglais : textes et noms anglais ; en plein écran (et en 4K si tu peux) rien n'est coupé.
- [ ] t123 (44) : **ta progression d'avant** : ton ancien % par ouverture n'est pas perdu (gardé dans le fichier) ;
      un fichier `entrainement.json.bak` (l'ancien) apparaît dans le dossier du jeu. Le nom d'ouverture pendant une
      partie, la pastille « Théorique » de la revue et le résumé du coach sont inchangés.

Séance du 25/10 (43) – pour chaque point : **Fonctionne / Ne fonctionne pas + commentaire**.
Les points 3 à 6 ne seront dans la version installée qu'après la prochaine version amis (n° 8) ; le point 4
(durée de la revue) peut se faire dès maintenant avec la n° 7.
- [ ] t112 (43) : **Échap au menu** : au menu principal, appuie sur Échap → une fenêtre « Quitter SickChess ? »
      avec Oui / Non. Essaie Non, puis Échap, puis un clic à côté : la fenêtre se ferme et tu restes au menu.
      Enfin Échap puis Oui (ou Entrée) : le jeu se ferme.
- [ ] t113 (43) : **bouton Quitter du menu** : un clic ferme le jeu tout de suite, sans question.
- [ ] t114 (43) : **pastilles plus lisibles** : ouvre une revue ; dans la feuille de coups, sur l'échiquier et dans le
      résumé de fin, les pastilles sont plus grosses, le signe se lit bien même sur le jaune et le vert clair, Gaffe
      en rouge franc, Manque en rose ; rien ne chevauche le texte des coups.
- [ ] t115 (43) : **retest de la durée de la revue (t71)** avec la **VERSION INSTALLÉE** (pas le dossier de dev, qui est
      réglé en « Maximale ») : Options → Partie : Calcul fixe + Forte ; ouvre la revue d'une partie d'environ
      17 coups jamais analysée et chronomètre. On doit voir : le temps restant baisse sans remonter, la revue finit
      en 1 min 30 à 3 min, et un clic sur un coup au milieu ne retarde pas la fin. **Note le temps réel.**
- [ ] t116 (43) : **« Théorique » dès la 1re revue** : lance le jeu et ouvre tout de suite la revue d'une partie jamais
      analysée qui commence par une ouverture connue : les premiers coups ont la pastille « Théorique ».
- [ ] t117 (43) : **phrase du salon en ligne** : Menu → Jouer en ligne : la phrase sous le titre (« Joue contre un ami
      Steam. Crée une partie… ») est entière, rien de coupé ; pareil en anglais (Options → Langue → English).
- [ ] t110 (42) : **Freestyle** (Fonctionne / Ne fonctionne pas + commentaire) :
      a) Partie contre l'ordinateur → panneau VARIANTE : Normal / Freestyle ; Freestyle → Au hasard : pièces
         mélangées, « Freestyle n° … » au-dessus des coups ; b) roquer en posant le roi SUR sa tour, puis en le
         posant sur g1 / c1 ; c) Choisir le n° → 518 = position normale ; d) Freestyle → Tournoi : 10 min + 5 s,
         « Préparation : 10:00 », « Je suis prêt » ; Échap → nulle refusée avant le 40e coup des Noirs ;
         e) revue de la partie (roques rejoués) et Mes parties ; f) en ligne avec un ami : Freestyle, même position
         chez les deux, revanche = même position couleurs inversées ; g) à deux sur ce PC en Freestyle.
- [ ] t111 (42) : **chute au temps sans matériel de mat** : partie à deux 1 min, prends tout sauf le roi adverse,
      laisse TON temps tomber : « TEMPS ÉCOULÉ - mais l'adversaire ne peut plus mater : match nul ».
- [ ] t109 (41) : **Signaler dans la n° 7** : Menu → Signaler → un bug, puis une idée : ils arrivent dans ton salon
      Discord en rouge / vert, avec la version 0.3.0.
- [ ] t108 (41) : **revue plus fiable** : fais deux revues à la suite (dont une partie finie par un mat rapide), et une
      revue pendant que le PC travaille (une vidéo, un autre programme lourd) : toutes les pastilles arrivent, la revue
      ne reste jamais bloquée sur un coup ; aide F1 dans la revue : les touches listées marchent.
- [ ] t107 (39) : regarde ton salon Discord : 3 messages de test (rouge, vert, bleu) de Claude, à supprimer.
      Après la prochaine version : Menu → Signaler → un bug puis une idée : ils arrivent en rouge / vert.
- [ ] t106 (39) : installer la n° 7 : Windows demande une fois l'accord (pare-feu) ; « Oui » ; relancer : plus de
      demande ; jouer en ligne avec un ami sur un Wi-Fi public (R-118).
      **Sur ton PC (25/10)** : deux règles « SickChess » existaient déjà (créées avant, sans description) : avec elles,
      Windows ne demande rien. **Fait le 25/10** (installation normale de la n° 7 sur le PC de Julien) : une demande
      Windows, « Oui », les 2 règles refaites par l'installeur (entrée + sortie, profil Tous, autoriser), aucune
      règle de blocage ; au lancement « [PARE-FEU] ok », plus aucune demande. Reste : jouer en ligne sur un Wi-Fi public.
- [ ] t105 (39) : après la n° 7, ton ami (n° 4 ou 5) : le jeu se met à jour seul au menu, sans aller sur GitHub.
      À partir de la n° 8 : un ami en retard de plusieurs versions les reçoit toutes, un seul redémarrage (R-117).
- [ ] t104 (38) : **analyse de fond (p25)** : importe une partie (ou joues-en une à deux), reste au menu
      quelques minutes, puis Mes parties : « Revue prête » ; sa revue s'ouvre avec toutes les pastilles.
      Pendant une partie contre l'ordinateur : pas de stockfish.exe en plus. Le jeu reste fluide au menu ?
- [ ] t103 (36) : **corrections des défauts trouvés par Cowork** (à confier à Cowork sur ton PC) :
      revue : clic sur un coup de la feuille (même après avoir cliqué une pièce), plus de « Nf3, Nf3 », explication
      d'une gaffe en entier ; Problèmes : messages et record lisibles, Mes erreurs sans les parties de Morphy,
      contre la montre : le bon coup montré après une faute ; Ouvertures : noms en français, « Ligne suivante » ;
      Signaler : Ctrl+V ajoute au texte avec les accents ; anglais : plus de « %10olved », pendule « BLACK » entière,
      aide F1 de la revue à jour ; Options : « Ce PC : 12 cœurs, 16 Go : PC normal ».
- [ ] t102 (32) : fais une revue, reviens au menu et ne touche à rien 3 minutes, Gestionnaire des tâches ouvert :
      au bout de 2 min les stockfish.exe d'analyse disparaissent (il en reste 1, l'adversaire), la mémoire
      redescend de plusieurs Go ; rouvre la même revue : pastilles et précision sont toujours là.
→ 24/10 : chaque test de la page porte une étiquette « Qui » (Cowork / Claude Code PC / Toi) ;
  répartition et consignes pour Cowork : `docs/TESTS_COWORK.md`. Filtre « Seulement pour moi » dans la page.
- [x] (✓ Cowork 24/10) t101 (28) : **quitter et lancer vite** : pendant que l'ordinateur réfléchit (niveau Maximum, longue cadence),
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
- [x] (✓ Cowork 24/10) t96 (27) : dans un terminal, dossier du jeu : `python SickChess.py --plantage-test` (le jeu se ferme), puis
      relance le jeu : carte « La dernière fois, SickChess s'est fermé… » ; « Envoyer le rapport » ouvre Signaler
      déjà rempli ; envoie (ou Non merci) : la carte ne revient plus.
- [x] (✓ Cowork 24/10) t95 (26) : importe (Mes parties → Importer) une partie qui commence à une autre position (PGN avec
      [FEN "…"]) dont le 1er coup est une gaffe : sa revue le note Gaffe, pas « Théorique » (R-06I).
- [ ] Claude Code (PC) : `python outils/recette_auto.py` et `python outils/banc_essai.py --sections precision`
      (relance programmée à 4 h 20), puis version amis.
- [x] (✓ Cowork 24/10) t92 (25, Steam ouvert) : Problèmes → « Classements Steam » : les trois classements et les trois vues se
      chargent ; ta ligne « Toi » en or (après un premier score). Lisible ? Rapide ?
- [x] (✓ Cowork 24/10) t93 (25) : fais un contre la montre puis rouvre les classements : ton score y est (Actualiser si besoin) ;
      même chose avec une survie et un problème classé.
- [ ] t94 (25) : Steam fermé : l'écran le dit et montre tes scores ; joue un contre la montre ; relance le jeu
      Steam ouvert : ton record apparaît dans le classement sans rien refaire.
- [ ] Regarder `docs/steam_succes/apercu.png` : les icônes des succès te plaisent ? (à refaire avec Cowork sinon)
- [x] (✓ Cowork 24/10) t88 (24, sans ami) : Jouer en ligne → « Test : invitation », puis Retour : dans le menu, « Ami de test
      t'invite à jouer » avec un petit son ; « Plus tard » le range ; Jouer en ligne le montre dans
      « INVITATIONS REÇUES ».
- [ ] t89 (24, avec un ami) : SickChess ouvert au menu, ton ami t'invite depuis son salon : bandeau en haut ;
      « Rejoindre » → tu arrives dans son salon et la partie se lance normalement.
- [ ] t90 (24, avec un ami) : même chose pendant les Problèmes (ou une revue) : l'écran se ferme, salon de l'ami.
- [ ] t91 (24, avec un ami) : même chose pendant une partie contre l'ordinateur : « Rejoindre <ami> ? »,
      pendule arrêtée ; Rester continue ; Rejoindre → salon, et ensuite « Reprendre la partie » dans le menu.
- [x] (✓ Cowork 24/10) t82 (23) : Menu → Analyse libre : en quelques secondes, 3 lignes de Stockfish, « profondeur » qui monte,
      flèche bleue ; joue des coups des deux camps : Stockfish suit chaque coup aussitôt ; le jeu reste fluide.
- [x] (✓ Cowork 24/10) t83 (23) : clique sur une des 3 lignes (son premier coup est joué) ; Espace : « Relancer » en or et le
      processeur redescend (Gestionnaire des tâches) ; Espace : ça repart.
- [x] (✓ Cowork 24/10) t84 (23) : copie un FEN sur lichess (Partager) puis Ctrl+V ; copie une partie PGN puis Ctrl+V ; C copie
      le FEN et lichess.org/analysis affiche la même position.
- [ ] t85 (23) : Éditer (E) : vide le plateau, pose rois / tours / pions, essaie une position impossible
      (message), coche un roque, « Analyser ». L'éditeur est-il facile à utiliser ?
- [x] (✓ Cowork 24/10) t86 (23) : revue d'une partie → un coup → « Analyser (A) » : même position ; Retour : la revue revient
      au même coup. Les 4 boutons du bas de la revue tiennent bien sur ton écran ?
- [x] t87 (23) : avec le dossier syzygy/ : colle `8/8/8/4k3/8/8/4P3/4K3 w - - 0 1` → « Tables de finale :
      nulle » (24/10 : vérifié par Cowork ; c'est bien nulle, l'ancien texte « les Blancs gagnent » était faux) ; laisse 2 min sur une position : « analyse terminée », plus de stockfish.exe
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
- [x] (✓ Cowork 24/10) t68 : Options → Partie → Façon d'analyser / Puissance ; « Forte » est sélectionné ; partie déjà
      analysée pas refaite.
- [x] t69 : mesure faite le 18/10 (`docs/MESURE_STOCKFISH.md`) ; décision de Julien : Forte et 3 × 4.
- [ ] t71 (16) : revue d'une longue partie importée (Forte) : ≈ 5 min pour 70 coups ? Ronds creux qui se
      remplissent, pastilles qui ne changent plus. Commit de la séance (16) par Claude Code.
- [ ] t70 : hachage 6 Go – les stockfish.exe prennent ~6 Go pendant une revue, le PC reste fluide ;
      noter la mémoire du PC (Gestionnaire des tâches → Performance → Mémoire).
- [x] Commit Git de la séance du 18/10 (13) par Claude Code (fusionné sur GitHub, PR n° 1).
- [ ] Problèmes → « Mes erreurs » : tes gaffes deviennent des problèmes (parties dont la revue a été ouverte).
- [x] (✓ Cowork 24/10) Revue : jouer une variante sur l'échiquier, Stockfish répond ; Échap pour revenir.
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
- [x] (✓ Cowork 24/10) Multijoueur sur un seul PC : lancer le jeu deux fois, « Test : héberger » /
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
