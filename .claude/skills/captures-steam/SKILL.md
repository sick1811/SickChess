---
name: captures-steam
description: Produire les images de la page Steam et itch.io de SickChess (captures d'écran du jeu, capsules, logo) aux bonnes tailles. À utiliser quand Julien prépare sa page boutique.
---

# Images pour Steam et itch.io

Tailles Steam à **revérifier sur partner.steamgames.com avant l'envoi** (elles changent) :
- Captures d'écran : au moins 5, en 1920×1080 (16:9), le vrai jeu, pas de montage.
- Capsule d'en-tête 920×430 · petite capsule 462×174 · capsule principale 1232×706 ·
  capsule verticale 748×896 · bibliothèque 600×900 · héros 3840×1240 ·
  logo de bibliothèque 1280×720 (fond transparent).
- itch.io : image de couverture 630×500, captures libres.

## Captures du jeu
1. `python tests/captures_ecrans.py` donne les écrans à petite taille : l'adapter (ou
   une variante `tests/captures_steam.py`) pour photographier en 1920×1080 :
   menu Vitrine, partie en cours (position intéressante, flèches), revue avec pastilles
   et courbe, problèmes, Options (personnalisation), salon en ligne.
2. Les ranger dans `assets_src/steam/captures/`.

## Capsules
- Style Onyx & Or : fond onyx, cavalier doré (`assets/logo.png`, `logo_fond.png`),
  titre SICK**CHESS** lisible même en petite capsule.
- Fond possible : le rendu Blender du menu (`assets/menu/fond_menu.jpg`, sources dans
  `outils/blender/`).
- Les fabriquer avec un script Pillow (`outils/generer_capsules.py`) pour pouvoir les
  refaire, ou dans Canva depuis Cowork. Ranger dans `assets_src/steam/capsules/`.
- Aucune image ou police sans licence (voir `docs/CREDITS.md`).
