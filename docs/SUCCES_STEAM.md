# Succès Steam – SickChess

Les succès sont gérés par `jeu/succes.py`. Le jeu les garde dans `succes.json` (même sans Steam)
et les envoie à Steam quand il est branché. Pour qu'ils apparaissent sur la page Steam, il faut
les **déclarer dans Steamworks** (App Admin → Stats & Achievements → Achievements) avec
exactement ces noms API, puis publier :

| Nom API | Titre | Comment l'obtenir |
|---|---|---|
| PREMIERE_VICTOIRE | Premier sang | Battre l'ordinateur pour la première fois |
| VICTOIRE_1500 | Joueur de club | Battre l'ordinateur réglé à 1500 Elo ou plus |
| VICTOIRE_2000 | Expert | Battre l'ordinateur réglé à 2000 Elo ou plus |
| VICTOIRE_MAT | Échec et mat | Gagner une partie par mat |
| PRECISION_90 | Chirurgien | Finir une partie avec 90 % de précision ou plus |
| SERIE_10 | Dix d'affilée | Réussir 10 problèmes classés d'affilée |
| PROBLEMES_100 | Centurion | Réussir 100 problèmes classés |
| CLASSEMENT_1500 | Tacticien | Atteindre 1500 au classement des problèmes |
| CHRONO_15 | Éclair | Trouver 15 problèmes en contre la montre |
| SURVIE_10 | Survivant | Trouver 10 problèmes en survie |
| JOUR_7 | Fidèle | Réussir le problème du jour 7 jours de suite |
| OUVERTURE_PARFAITE | Théoricien | Réciter une ligne d'ouverture sans faute |
| EN_LIGNE | Entre amis | Finir une partie en ligne |
| IMPORTER | Archiviste | Importer une partie jouée ailleurs |

Il faut aussi une icône 64×64 par succès (débloqué / bloqué) : à faire avec la direction
artistique. Tant que le jeu utilise le numéro de test 480, Steam ignore ces noms.

Classements Steam (problèmes, contre la montre) : à faire quand SickChess aura son numéro Steam
(ils se créent aussi dans Steamworks).
