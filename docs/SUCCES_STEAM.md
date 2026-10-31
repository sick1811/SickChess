# Succès et classements Steam – SickChess

Mis à jour le 24/10/2026 (travail p37).

## Où on en est
- **Classements** : ils marchent **dès maintenant**, même avec le numéro de test 480 (Steam les crée
  tout seul à la première demande). Dans le jeu : Problèmes → « Classements Steam ».
- **Succès** : 14 succès gardés dans le jeu (`succes.json`, Statistiques → Succès). Steam ne peut les
  afficher qu'avec le **vrai numéro** de SickChess (compte Steamworks + 100 $, travail p21). Tout est
  prêt pour ce jour-là : le jeu **renvoie à Steam tous les succès déjà gagnés** à chaque connexion
  (`succes.rattraper`), donc personne ne perd ce qu'il a obtenu avant.

## Le jour où SickChess a son numéro Steam
0. Écrire le vrai numéro dans `APPID_STEAM_REEL` (`jeu/distribution.py`) : c'est le seul chiffre du
   code à changer ; `verifier_version.py --steam` bloque tant qu'il vaut `None`.
1. `steam_appid.txt` : remplacer 480 par le vrai numéro (et `MODE_TEST = False` dans
   `jeu/salon_en_ligne.py`).
2. Steamworks → App Admin → **Stats & Achievements → Achievements** : créer les 14 succès ci-dessous,
   **avec exactement ces noms API**, et donner à chacun ses deux icônes (dossier `docs/steam_succes/`,
   `<NOM_API>.jpg` = débloqué, `<NOM_API>_gris.jpg` = bloqué, 256 × 256). Noms et descriptions en
   français, puis onglet « English » avec les textes anglais.
3. Steamworks → **Stats & Achievements → Leaderboards** : les 3 classements se créent tout seuls à la
   première partie ; leur donner un « Community Name » (sinon ils n'apparaissent pas sur la page
   communauté du jeu) : voir le tableau plus bas.
4. **Publish** (bouton en haut de la page Steamworks), puis lancer SickChess : les succès déjà gagnés
   apparaissent dans Steam.

Les icônes sont refaites par `python outils/generer_icones_succes.py` (pièces « Tournoi plat » du
projet et police Barlow : aucune licence extérieure). Aperçu : `docs/steam_succes/apercu.png`.

## Les 14 succès

| Nom API | Titre | Comment l'obtenir | Icône |
|---|---|---|---|
| PREMIERE_VICTOIRE | Premier sang | Battre l'ordinateur pour la première fois | roi, « 1 » |
| VICTOIRE_1500 | Joueur de club | Battre l'ordinateur réglé à 1500 Elo ou plus | dame, « 1500 » |
| VICTOIRE_2000 | Expert | Battre l'ordinateur réglé à 2000 Elo ou plus | dame, « 2000 » |
| VICTOIRE_MAT | Échec et mat | Gagner une partie par mat | roi, « # » |
| PRECISION_90 | Chirurgien | Finir une partie avec 90 % de précision ou plus | fou, « 90% » |
| SERIE_10 | Dix d'affilée | Réussir 10 problèmes classés d'affilée | cavalier, « x10 » |
| PROBLEMES_100 | Centurion | Réussir 100 problèmes classés | tour, « 100 » |
| CLASSEMENT_1500 | Tacticien | Atteindre 1500 au classement des problèmes | cavalier, « 1500 » |
| CHRONO_15 | Éclair | Trouver 15 problèmes en contre la montre | pion, « 15 » |
| SURVIE_10 | Survivant | Trouver 10 problèmes en survie | tour, « 10 » |
| JOUR_7 | Fidèle | Réussir le problème du jour 7 jours de suite | pion, « 7 » |
| OUVERTURE_PARFAITE | Théoricien | Réciter une ligne d'ouverture sans faute | fou, « 1.e4 » |
| EN_LIGNE | Entre amis | Finir une partie en ligne | cavalier, « 2 » |
| IMPORTER | Archiviste | Importer une partie jouée ailleurs | tour, « PGN » |

## Les 3 classements

| Nom API | Community Name (à saisir) | Score | Envoi |
|---|---|---|---|
| SICKCHESS_PROBLEMES | Problèmes – classement | Classement des problèmes (mode classé) | remplacé à chaque problème (il peut baisser) |
| SICKCHESS_CONTRE_LA_MONTRE | Contre la montre | Problèmes trouvés en 3 minutes | Steam garde le meilleur |
| SICKCHESS_SURVIE | Survie | Problèmes trouvés avant la 3e faute | Steam garde le meilleur |

Tri : du plus grand au plus petit ; affichage : nombre. Trois vues dans le jeu : Mondial (10 premiers),
Amis, Autour de moi. Sans Steam, les scores restent dans le jeu et partent à la connexion suivante.

Version itch.io (31/10) : jamais de Steam ; le bouton s'appelle « Classements » et montre seulement les
records gardés dans le jeu, sous le message « Les classements mondiaux passent par Steam ».

Avec le numéro de test 480, ces classements sont partagés avec tous les développeurs qui testent sur
« Spacewar » : nos noms sont propres à SickChess, donc on n'y voit que des joueurs de SickChess. Ils
repartiront à zéro avec le vrai numéro.
