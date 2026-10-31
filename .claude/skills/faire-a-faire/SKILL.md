---
name: faire-a-faire
description: Faire tout ce qui reste dans docs/A_FAIRE.md avec tous les agents du projet, puis vérifier le VRAI jeu sur le PC de Julien avec l'utilisation de l'ordinateur (captures d'écran, clics, frappe) et passer soi-même les tests « À tester par Julien ». À utiliser quand Julien dit « fais les à faire », « fais tout ce qui reste » ou tape /faire-a-faire.
---

# Faire les « À faire » de SickChess (agents + utilisation du PC)

Tu es le **chef d'orchestre** : tu suis la skill `chef-orchestre` (tri, distribution, vérification,
commit) et la skill `seance-sickchess` (règles d'une séance). Cette skill ajoute deux choses :
l'ordre exact de la journée et **le contrôle du vrai jeu à l'écran**.

## 0. Démarrage (seul, avant tout agent)
1. Lire `CLAUDE.md`, `docs/A_FAIRE.md`, la fin de `docs/JOURNAL.md`, les constats « corriger »
   de `tests/banc_essai.json`.
2. `git status` : les fichiers modifiés qui ne sont pas à toi appartiennent à une autre session
   (Cowork) → n'y touche pas, ne les commite pas. `git log -5`.
3. `python tests/lancer_tous.py --rapide` : partir d'un état vert. Sinon, la première tâche
   devient « remettre au vert ».
4. Vérifier l'utilisation de l'ordinateur : chercher les outils de captures d'écran / clic / frappe
   (computer use). S'ils manquent, le dire à Julien en une phrase, puis continuer avec
   `python tests/captures_ecrans.py` à la place (étape 4 en mode « sans écran »).

## 1. Tri
Agent `trieur-taches` sur tout `docs/A_FAIRE.md`. Ordre imposé :
1. sections marquées « EN PREMIER » (de la plus récente à la plus ancienne) ;
2. « Retours de Julien à traiter » non cochés ;
3. constats « corriger » du banc d'essai ;
4. « Travaux choisis par Julien » puis « Prochaines étapes ».
Ne PAS faire : « Démarches (plus tard) », les « Travaux proposés » que Julien n'a pas choisis,
tout ce qui touche Steam en vrai (paiement, mise en ligne de la page) ou `MODE_TEST = False`.
Poser à Julien **en une seule fois** les questions relevées par le tri ; ne pas lancer ce qui
attend sa réponse, avancer sur le reste.

## 2. Travail en parallèle (vagues)
Plusieurs agents dans le même message, en arrière-plan, chacun avec : les mots de Julien,
la **liste exacte des fichiers autorisés**, le test attendu, « pas de commit ».
- Bug clair → `correcteur` · bug « une fois sur 10 » → `enqueteur-bug` puis `correcteur`
- Nouvelle fonction → `batisseur`
- Lenteur → `optimiseur` (skills `performance-pygame`, `banc-essai`), puis `correcteur`
- Ménage → skill `menage-code`
- Textes / accents / anglais → `traducteur` (seul à toucher `jeu/langue_en.py`, en fin de vague)
Règles : un fichier = un agent ; au plus 2 agents avec Stockfish en même temps ; jamais
`profil.json`, `parties/`, `puzzles_score.json`, `config.json`, `rapports/`.

## 3. Vérification de chaque vague
Relire chaque diff (un rapport n'est pas une preuve), relancer la série de test concernée, puis :
`testeur` (toujours) · `arbitre-echecs` + skill `verifier-echecs` si règles/analyse/pastilles ·
`relecteur-interface` et `relecteur-textes` si un écran ou un texte a changé.
Un problème trouvé = retour au `correcteur` avant de continuer.

## 4. Contrôle du VRAI jeu sur le PC (utilisation de l'ordinateur)
Après chaque vague qui change quelque chose de visible :
1. Lancer `python SickChess.py` (ou `LANCER.bat`), attendre la fenêtre, faire une capture.
2. Pour chaque tâche faite dans la vague : aller sur l'écran concerné à la souris/au clavier,
   faire ce que Julien ferait, capture d'écran, et juger : accents, textes coupés, contraste
   Onyx & Or, son (dire si tu ne peux pas l'entendre), fluidité, pas de plantage.
3. Tester aussi en **fenêtre réduite** puis agrandie, et en anglais si un texte a changé.
4. Passer les cases de « À tester par Julien » que tu peux juger seul à l'écran : noter
   « Fonctionne / Ne fonctionne pas (vu par Claude Code, capture) ». Laisser à Julien ce qui
   demande ses oreilles, un deuxième PC, ses amis en ligne ou son avis de goût.
5. Ce qui ne marche pas → nouvelle tâche pour `correcteur`, avec la capture et les étapes.
6. Fermer le jeu proprement (bouton Quitter) et vérifier qu'aucun `stockfish.exe` ne reste.
Sécurité à l'écran : ne toucher qu'à la fenêtre SickChess et au terminal. Ne rien acheter,
ne rien publier, ne pas toucher aux réglages de Windows, de Steam ni aux autres programmes ;
si une fenêtre inattendue s'ouvre, s'arrêter et demander à Julien.
Si un test a besoin de Steam ouvert (jeu en ligne) : `python outils/verifier_en_ligne.py`,
sans rien changer dans Steam.

## 5. Commit, version, fin
1. `gardien-depot` → PRÊT, puis un commit par groupe (ses fichiers seulement), message
   `SickChess : <ce qui change>`, `git push` (jamais `--force`).
2. `recetteur`, puis `documentaliste` (une seule fois) : journal daté, A_FAIRE coché,
   « À tester par Julien » (seulement ce que tu n'as pas pu vérifier à l'écran), recette.
3. Tout vert et le jeu a changé → `python outils/verifier_version.py --amis`, puis demander
   l'accord de Julien et publier la version amis (skill `version-amis`).
4. Message final court à Julien, en français simple : ce qui est fait, ce que tu as vérifié
   toi-même à l'écran, ce qui reste à tester par lui, les questions en attente.
