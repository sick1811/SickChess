# PLAN DE SORTIE – SickChess (Steam + itch.io)

*Préparé le 16/10/2026. Règles Steam vérifiées sur partner.steamgames.com/steamdirect.*

## Les règles de Steam qui fixent le calendrier
- **100 $ par jeu** (non remboursables, mais rendus sur un versement une fois 1 000 $ de ventes atteints).
- **Vérification identité + banque + impôts : 15 à 30 jours.** C'est à lancer tôt : rien ne
  bouge avant. Le nom du titulaire du compte bancaire doit correspondre à la pièce d'identité.
- **30 jours d'attente** entre le paiement des 100 $ et le jour où on a le droit de sortir le jeu.
- **Page « Bientôt disponible » publique au moins 2 semaines** avant la sortie.
  En pratique, plus elle est en ligne tôt, plus on récolte de « listes de souhaits » (2 à 6 mois conseillés).
- **Relecture par Valve : 1 à 5 jours** pour la page, puis 1 à 5 jours pour le jeu lui-même.
- Steam garde 30 % de chaque vente.

## Phase A – Démarches (à lancer maintenant, en parallèle du code)
- [ ] Créer le compte Steamworks (partner.steamgames.com) avec le compte Steam de Julien.
- [ ] Remplir identité, coordonnées bancaires, questionnaire fiscal (en tant que particulier).
- [ ] Payer les 100 $ → le compteur de 30 jours démarre.
- [ ] Créer un compte itch.io (gratuit, pas de frais de publication).

## Phase B – Version 1.0 du jeu (ce qui doit être prêt pour vendre)
Proposition de périmètre (à valider) – le reste arrive en mises à jour gratuites après la sortie :
- [x] Noyau : plateau, règles, pendule, sons, Stockfish, partie à deux (v0.1.0).
- [ ] 1. Compilation en .exe (PyInstaller) qui marche sur un PC qui n'a pas Python.
- [ ] 2. Options / personnalisation.
- [ ] 3. Direction artistique : thème original complet, logo, icône.
- [ ] 4. Revue de partie.
- [ ] 5. Mes parties + profil.
- [ ] 6. Problèmes (base Lichess).
- [ ] Bugs connus réglés (son coupé, animation, Stockfish trop « robot »).
- **Après la sortie :** entraînement aux ouvertures, bouton « Signaler un problème »,
  multijoueur Steamworks (le plus gros morceau : il faut une passerelle Python ↔ Steamworks,
  à tester à part avant de le promettre sur la page).

## Phase C – Licences (obligatoire avant de vendre)
- [ ] **Stockfish (GPL v3)** : on a le droit de le livrer avec un jeu payant tant qu'il reste un
      programme séparé (c'est le cas : `moteur/stockfish.exe`, appelé en UCI). Il faut livrer
      sa licence (déjà là) **et son code source ou un lien vers la version exacte**, et le
      citer dans les crédits. Ne jamais modifier Stockfish sans publier les modifications.
- [ ] **Pièces « Classique » (contours Cburnett)** : vérifier la licence sur Wikimedia et
      mettre la mention d'auteur, ou dessiner nos propres pièces (plus simple pour un jeu vendu).
- [ ] Ouvertures Lichess et base de problèmes : confirmer la licence (CC0 annoncée).
- [ ] Polices : OK (OFL, fichiers de licence déjà fournis).
- [ ] Questionnaire Steam sur le contenu généré par IA : y répondre honnêtement
      (code écrit avec Claude ; sons synthétisés par un script).

## Phase D – Page Steam « Bientôt disponible »
- [ ] Images « capsule » aux formats imposés par Steam (logo SickChess lisible en petit).
- [ ] Au moins 5 captures d'écran du jeu **avec le nouveau thème** (donc après l'étape 3).
- [ ] Description courte + longue (FR et EN), étiquettes : Échecs, Stratégie, Plateau, Solo…
- [ ] Configuration minimale (Windows, petite config).
- [ ] Une bande-annonce de 30 à 60 s (conseillée, pas obligatoire).
- [ ] Prix : petit prix, à fixer en regardant 3 ou 4 jeux d'échecs vendus sur Steam.
- [ ] Envoyer en relecture → publier → la page reste en ligne au moins 2 semaines.

## Phase E – Mise en ligne
- [ ] Envoyer le .exe sur Steam (outil SteamPipe fourni par Valve) et le tester via Steam
      sur le PC de Julien, puis si possible sur un 2e PC.
- [ ] Envoyer le jeu en relecture (1 à 5 jours).
- [ ] Choisir le jour : plutôt un mardi, mercredi ou jeudi.
- [ ] Remise de lancement (facultative) la première semaine.
- [ ] Publier aussi sur itch.io le même jour.
- [ ] Facultatif : une démo gratuite pour le Steam Next Fest (dates sur partner.steamgames.com).

## Ordre conseillé
1. **Maintenant :** Phase A (démarches) – c'est elle qui prend le plus de temps d'attente.
2. **Code :** étapes 1 à 3 (exe, options, direction artistique).
3. **Dès que le jeu est joli :** Phase D, page « Bientôt disponible » en ligne.
4. **Pendant que la page récolte des souhaits :** étapes 4 à 6 + licences (Phase C).
5. **Sortie :** Phase E.
