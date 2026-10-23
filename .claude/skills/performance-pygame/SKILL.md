---
name: performance-pygame
description: Rendre SickChess rapide et léger - moins de processeur au repos, images plus rapides, Stockfish bien réparti sur les cœurs, et ce que la carte graphique peut prendre en charge. À utiliser pour toute demande de vitesse, de fluidité, de chauffe, de ventilateur, de « le jeu rame » ou de carte graphique.
---

# Performance de SickChess (pygame + Stockfish)

Toujours : mesurer avec le banc (`python outils/banc_essai.py --sections vitesse,processeur`),
changer UNE chose, remesurer, garder si ça gagne. Tests verts.

## 1. Ce que le banc a montré (23/10/2026)
- Chaque écran **redessine tout, 60 fois par seconde**, même quand rien ne bouge.
- **Textes** : `font.size` + `font.render` (via `ui.texte` / `ui.rogner`) = 40 à 60 % du
  temps d'une image. Les mêmes textes sont recoupés et refaits à chaque image.
- **Fichiers relus à chaque image** (le pire) : `entrainement.charger_progression`
  (24 lectures par image dans « Ouvertures »), `modes_problemes.charger` (Problèmes),
  `succes.obtenus` (Statistiques).

## 2. Remèdes, du plus rentable au moins rentable
1. **Ne rien lire sur le disque dans `draw()`** : lire à l'ouverture de l'écran ou après
   un changement, garder en mémoire (attribut ou petit cache invalidé à l'écriture).
2. **Cache des textes** dans `ui.py` : dictionnaire `(texte, police, couleur, largeur_max)`
   → surface déjà rendue et rognée. Vider si la taille de la fenêtre ou la police change.
   Limiter la taille (ex. 2000 entrées, on vide tout quand c'est plein).
3. **Calques** : dessiner une fois sur une surface ce qui ne bouge pas (fond, cadre,
   cases du plateau, coordonnées, panneaux) ; la refaire seulement au redimensionnement ou
   au changement de thème. Chaque image = 1 blit du fond + ce qui bouge.
4. **Redessiner seulement si besoin** : un drapeau `self.sale` mis à True par un
   événement, une animation, la pendule qui change de seconde, l'analyse qui avance.
   Sinon on saute `draw()` + `flip()`. Au repos : `clock.tick(30)` au lieu de 60 ; en
   animation : 60.
5. **Images** : `convert()` / `convert_alpha()` après chaque `image.load`, et
   `smoothscale` une seule fois par taille (cache), jamais dans `draw()`.
6. **Règles d'échecs** : `check_game_over` / répétitions seulement après un coup, pas à
   chaque image.

## 3. Stockfish et les cœurs du processeur (PC de Julien : 6 cœurs / 12 logiques)
- Stockfish ne sait calculer **que sur le processeur** (pas de carte graphique) : c'est
  normal et c'est le meilleur moteur.
- Répartition : l'adversaire = 1 fil ; l'analyse = cœurs logiques − 2 (garder de quoi
  faire tourner le jeu et Windows) ; jamais deux analyses lourdes en même temps.
- Mettre les Stockfish d'analyse en **priorité basse** (Windows : `BELOW_NORMAL_PRIORITY_CLASS`
  via `creationflags`, ou `psutil.Process(pid).nice(...)`) : l'analyse prend tout ce qui
  est libre mais le jeu reste fluide.
- Hachage : taille selon la mémoire libre (déjà plafonnée dans `cache_manager.py`).
- Mesure : section « moteur » du banc (`stockfish bench`, nœuds/s).

## 4. Et la carte graphique ?
- pygame classique dessine **avec le processeur** (surfaces en mémoire). La carte graphique
  ne sert qu'à afficher l'image finale.
- Ce qu'elle peut prendre facilement : **l'agrandissement**. Avec
  `pygame.display.set_mode(taille_logique, pygame.SCALED | pygame.RESIZABLE, vsync=1)`, le jeu
  dessine en 1280×720 et la carte graphique agrandit en plein écran (moins de pixels à
  dessiner, synchro écran sans déchirure). À essayer sur une branche : cela change la
  mise en page (le jeu ne voit plus la vraie taille de la fenêtre), mesurer et faire
  valider par Julien (netteté en 1440p / 4K).
- Pour aller plus loin : `pygame._sdl2.video` (Renderer / Texture, dessin par la carte
  graphique) ou **pygame-ce** qui l'expose mieux. Gros chantier (tout le dessin à
  réécrire) : seulement si, **après** les remèdes 1 à 4, le banc reste orange.
- Ne pas passer à Godot ni changer de moteur d'échecs (décisions de Julien).

## 5. Vérifier sur le vrai PC
Claude Code lance `python outils/banc_essai.py` sous Windows, puis
`python outils/surveiller.py` pendant que Julien joue (processeur, Stockfish, mémoire,
carte graphique, seconde par seconde). Ensuite Julien regarde le
Gestionnaire des tâches (onglet Processus, colonne Processeur) : menu et partie au repos
doivent rester très bas ; le ventilateur ne doit pas accélérer hors analyse.
