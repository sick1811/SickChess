# SickChess – À faire

Fichier partagé entre Cowork et Claude Code. **À relire au début de chaque séance,
à mettre à jour à la fin.** La page « SickChess – À faire »
(https://claude.ai/artifact/PzJkQy7b8DKRs9wgksP9T5) en est la version à cocher pour Julien.
Mis à jour le 18/10/2026.

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
- [ ] **Fichiers relus à chaque image** (le plus rentable) : `entrainement.charger_progression`
      (24 lectures par image dans Ouvertures, 44–51 ms par image), `modes_problemes.charger`
      (Problèmes), `succes.obtenus` (Statistiques). Lire une fois, garder en mémoire.
- [ ] **Cache des textes** dans `ui.py` (`texte` / `rogner`) : `font.size` + `font.render` =
      40 à 60 % du temps d'une image sur Partie, Revue, Options, Mes parties.
- [ ] **Ne pas redessiner au repos** : une partie arrêtée prend ~50 % d'un cœur (machine
      Cowork) ; redessiner seulement si quelque chose change, 30 images/s au repos.
- [ ] Stockfish d'analyse en priorité basse (le jeu reste fluide pendant une revue).
- [ ] Ménage : 8 imports/variables inutiles (correction automatique), `jeu/fond_anime.py` jamais
      importé, ~100 fonctions peut-être mortes à vérifier une par une (skill `menage-code`).
- [ ] Réglage `ia_suivre_la_pendule` de config.json lu nulle part : le reprendre ou l'enlever.
- [ ] Commit : 34 fichiers modifiés non enregistrés + 1 commit pas encore envoyé sur GitHub.
→ Avant de commencer, lire les décisions de Julien dans la page (Corriger / OK / Ignorer).

→ 23/10 (soir) : banc d'essai tout vert sur le PC de Julien (sauf ménage). 7 nouvelles propositions
  qualité (p28 à p34) : test d'endurance de 2 h, rapport de plantage, banque de positions pour la
  précision des pastilles, mode « petit PC », vérification avant chaque version, lisibilité
  (daltoniens, petits écrans), niveaux de l'ordinateur calibrés en vrai Elo. Julien choisit.

## Version amis et jeu en ligne (23/10 soir) – AVANT les travaux p30…
1. [ ] Claude Code : `winget install JRSoftware.InnoSetup` et `winget install GitHub.cli` + `gh auth login`.
2. [ ] Claude Code : `python outils/verifier_en_ligne.py` (Steam ouvert) → tout ✅.
3. [ ] Claude Code : version amis avec installeur (skill `version-amis`) : essai silencieux, lancement,
       vérification en ligne sur le dossier d'essai, puis publication ; donner le lien à Julien.
4. [ ] Julien + un ami : vraie partie en ligne sur deux PC (R-102 à R-107).
5. [ ] Plus tard (avant la vente) : certificat de signature de code → `"signature"` dans maj_config.json.

## Travaux choisis par Julien le 23/10 (statut « veux ») – ORDRE DES SÉANCES
Une séance = un travail (skill `seance-sickchess`), tests + banc d'essai avant/après, recette mise
à jour, tests pour Julien dans la page « À faire ». Phrase à Claude Code : « fais le travail pXX ».
1. [ ] **p30 – Banque de positions** (`tests/positions_revue.json`, 50–100 positions : vrais
       sacrifices, vraies gaffes, mats, finales Syzygy, + m04 « bon sacrifice ») ; 8e contrôle
       « precision » du banc d'essai. À faire en premier : protège tout le reste.
2. [ ] **p29 – Rapport de plantage** (erreur + fin du journal gardées, proposées au lancement
       suivant via « Signaler »), puis **p28 – Test d'endurance** (`outils/endurance.py` : robot
       2 h, mémoire, plantages, ralentissements ; section « endurance » du banc, hors --rapide).
3. [ ] **p32 – Vérification avant chaque version** (`outils/verifier_version.py`, appelé par
       CONSTRUIRE_VERSION_AMIS.bat : tests, banc, MODE_TEST, appid, licences, version, .exe neuf).
4. [ ] **p31 – Mode « petit PC »** (détection cœurs / mémoire au 1er lancement → puissance
       d'analyse, hachage, animations ; modifiable dans Options).
5. [ ] **p34 – Niveaux en vrai Elo** (matchs automatiques contre des références, à lancer la nuit
       sur le PC de Julien ; table de calibrage dans le code, test qui la vérifie).
6. [ ] **p27 – Résumé du coach immédiat** (carte de fin : ouverture, plus gros moment, précision
       provisoire, comparaison avec les 10 dernières parties).
7. [ ] **p33 – Lisibilité pour tous** (pastilles reconnaissables sans couleur, contrastes,
       1366×768 et 4K ; relecteur-interface).
Toujours en attente de décision : p21 Steamworks (le délai de 30 jours ne démarre qu'au paiement),
p20 page Steam, p22 licence des pièces Classique, p02, p09, p17, p23–p26.

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
- 18/10 (13) : analyse en calcul fixe par défaut (comme lichess), profondeur et temps au choix,
  temps restant affiché, outil de mesure de Stockfish.
- 17/10 : son réparé chez Julien, analyse en tâche de fond (précision immédiate),
  notation au choix (anglaise par défaut), promotion dans les problèmes, logo et icône.
