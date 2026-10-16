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

## Bugs connus (repris de « a debug.txt »)
- [x] Pendule ne clignote pas à 30 s → fonctionne (testé).
- [x] Fin de partie à 00:00 → corrigé (affichage du temps final).
- [ ] Son « coupé » : à confirmer à l'oreille avec les nouveaux sons.
- [ ] Animation lente (réglable : `vitesse_animation` dans config.json, 0.18 s).
- [ ] Temps de réflexion de Stockfish pas assez humain.
- [ ] Organisation de la fenêtre de jeu à revoir (chantier direction artistique).

## Fonctions de V8_TURBO_3000 à réintégrer (dans cet ordre)
1. Compilation en .exe (PyInstaller) – adapter COMPILER.bat à la nouvelle structure.
2. Options / personnalisation (`personnalisation_screen.py`, thèmes, accents).
3. Direction artistique : un thème complet original (plateau + pièces + sons) ;
   logo et icône originaux.
4. Revue de partie (`analyse_partie`, `annotations`, `courbe_eval`, `replay_screen`,
   `rapport_analyse`, écran de fin complet).
5. Mes parties + profil (`historique_parties`, `ecran_historique`, `profil_screen`,
   `statistiques`, `sauvegarde` / reprise de partie).
6. Problèmes (`puzzles`, `ecran_puzzles`, `explication_puzzle`, `classement_puzzles`)
   + base Lichess (230 Mo, hors GitHub).
7. Entraînement aux ouvertures et faiblesses (`ecran_entrainement`, `faiblesse`).
8. Bouton « Signaler un problème / Proposer une idée ».
9. Multijoueur : remplacer le relais bore.pub par Steamworks (salons, invitations).
10. Tables de finales Syzygy (379 Mo) : utiles ? à décider.
