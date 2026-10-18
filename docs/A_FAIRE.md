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
- [ ] t64-t66 : revue – Stockfish ne joue plus, flèches bleues/vertes, export et comparaison chess.com.
- [ ] t67 : temps réel d'une revue complète (Calcul fixe, Maximale) ; « environ X min » juste ?
- [ ] t68 : Options → Partie → Façon d'analyser / Puissance ; partie déjà analysée pas refaite.
- [ ] t69 (Claude Code, Windows) : `python outils/mesurer_stockfish.py` → `docs/MESURE_STOCKFISH.md`,
      puis choisir la répartition (1 × 12, 3 × 4, 6 × 2, 12 × 1) d'après la mesure.
- [ ] t70 : hachage 6 Go – les stockfish.exe prennent ~6 Go pendant une revue, le PC reste fluide ;
      noter la mémoire du PC (Gestionnaire des tâches → Performance → Mémoire).
- [ ] Commit Git de la séance du 18/10 (13) par Claude Code.
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
