# Atelier graphique SickChess (provisoire)

Rendus et ressources de travail pour choisir la direction artistique.
Rien ici n'est encore branché dans le jeu : on déplacera dans `assets/` ce qui sera retenu.

- `rendus/` : fond du menu (Blender, Cycles 1920x1080) et familles de pièces 3D (Arène, Tournoi, Prisme)
- `plateaux/` : plateaux 1024x1024 vus de dessus (marbre, onyx & or, noyer, ardoise, tournoi)
- `pieces2d/` : pièces plates SVG, `<famille>_<w|b><k|q|r|b|n|p>.svg`
- `../blender/scene_menu.blend` : la scène du menu, à ouvrir dans Blender

Tout est créé pour SickChess (modèles faits par script, textures calculées) : aucun droit tiers.

## Régénérer (dossier `outils/blender/`)
- Pièces 2D : `python gen_2d.py ../../assets_src/atelier/pieces2d`
- Plateaux : `python gen_plateaux.py ../../assets_src/atelier/plateaux` (numpy + Pillow)
- Rendus 3D : nécessitent Blender. Exemple :
  `blender -b -P rendu_menu.py -- arene C:/chemin/menu.png 64 1920`
  ou avec le module Python `bpy` (`pip install bpy`) : `python rendu_menu.py arene menu.png 64 1920`
