---
name: seance-sickchess
description: Déroulé d'une séance de travail sur SickChess (lire A_FAIRE et JOURNAL, coder une petite étape, tests, journal, liste de tests pour Julien, commit). À utiliser dès que Julien demande de coder, corriger un bug ou « faire la prochaine tâche ».
---

# Séance de travail SickChess

1. **Lire** `CLAUDE.md`, `docs/A_FAIRE.md`, puis la fin de `docs/JOURNAL.md`.
   Choisir la tâche : celle demandée par Julien, sinon le premier « Retour de Julien »
   non coché, sinon la première « Prochaine étape ».
   Lire aussi les constats « corriger » de la page « Banc d'essai » (ou `tests/banc_essai.json`).
2. **Dire en une phrase** ce qui va être fait.
3. **Avant de coder** : `git status` (ne rien perdre) et `python tests/lancer_tous.py --rapide`
   pour partir d'un état vert. Si une fonction vient de V8, lire son code dans
   `../V8_TURBO_3000` et la reprendre nettoyée, plus courte, sans ce qui ne sert plus.
4. **Un bug** : écrire d'abord le contrôle qui le montre (dans la série `tests/test_*.py`
   qui correspond, avec la fonction `verifier(condition, message)`), puis corriger.
   **Une nouvelle fonction** : ajouter ses contrôles, ou une nouvelle série
   `tests/test_<nom>.py` à déclarer dans `tests/lancer_tous.py`.
5. **Vérifier** : `python tests/lancer_tous.py` (tout vert). Si la séance touche au dessin,
   à l'analyse ou au chargement : `python outils/banc_essai.py --sections vitesse,processeur`
   avant et après, et noter le gain. Si un écran a changé :
   `python tests/captures_ecrans.py` et regarder les images dans `tests/ecrans/`
   (accents, textes qui débordent, contraste Onyx & Or). Sous Windows, lancer aussi
   `python SickChess.py` pour un essai réel quand c'est utile.
5 bis. **Recette** : si la séance ajoute, change ou retire quelque chose que Julien voit,
   mettre à jour la liste `RECETTE` dans `outils/recette.py` (ids R-xxx, une ligne = une
   action + ce qu'on doit voir), puis `python outils/recette.py` pour régénérer
   `docs/RECETTE.md` et `outils/recette.json`. Le dire dans le journal (« Recette : R-0xx
   ajouté/modifié »). Avant une version amis ou Steam : demander à Julien une passe
   complète de la recette, et ne rien livrer tant qu'il reste un R-xxx « Ne fonctionne pas ».
   Si Julien a mis des « Ne fonctionne pas » dans la recette, les traiter en priorité
   (comme un « Retour de Julien »).
6. **Journal** : ajouter en bas de `docs/JOURNAL.md` une section
   `## JJ/MM/AAAA – <titre>` avec « Fait : » (simple, sans jargon) et
   « À vérifier par Julien : » (cases `- [ ]`).
7. **A_FAIRE** : cocher ce qui est fait, ajouter les tests à faire par Julien
   (une ligne = une action concrète + ce qu'il doit observer).
8. **Commit** : `git add` des fichiers touchés (jamais `profil.json`, `parties/`,
   gros fichiers), message en français : `SickChess : <ce qui change>`.
   Pas de `git push` sans demande de Julien.
9. **Finir** par un court message à Julien : ce qui change pour lui, et la liste des
   tests à faire (Fonctionne / Ne fonctionne pas + commentaire).
