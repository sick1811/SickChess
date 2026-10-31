# Crédits et licences – SickChess

Chaque ressource livrée avec le jeu doit figurer ici, avec sa licence vérifiée.
Rien de copié d'un autre jeu ou d'un site sans licence claire.

| Ressource | Dossier | Origine | Licence |
|---|---|---|---|
| Code du jeu | `jeu/` | Julien (sick1811), avec Claude | Propriété du projet |
| Bruitages – carillons (échec, mat, début/fin, problèmes) | `sounds/` | Synthétisés par `outils/generer_sons.py` | Propriété du projet |
| Bruitages – chocs de bois (coups, prises, roque) | `sounds/`, sources dans `assets_src/sons_kenney/` | Pack « Impact Sounds » de Kenney (kenney.nl), assemblé par `outils/generer_sons.py` | CC0 (domaine public, `assets_src/sons_kenney/License.txt`) – mention de Kenney conseillée |
| Pièces « Classique » | `jeu/pieces_vectorielles.py` | Contours inspirés des pièces « Cburnett » (Wikimedia Commons) | **À vérifier** avant la sortie : licence d'origine + mention de l'auteur, ou redessiner nos propres pièces |
| Pièces Relief (Prisme, Arène, Tournoi) | `assets/pieces/relief_*` | Modèles 3D créés pour SickChess (`outils/blender/sick3d.py`), rendus dans Blender, retouchés par `outils/retoucher_pieces.py` (originaux : `assets_src/pieces_relief_origine/`) | Propriété du projet |
| Pièces plates (Arène, Tournoi) | `assets/pieces/plat_*` | Tirées des mêmes profils (`outils/blender/gen_2d.py`) | Propriété du projet |
| Plateaux en matière (marbre, onyx, noyer) | `assets/plateaux/` | Textures calculées (`outils/blender/gen_plateaux.py`) | Propriété du projet |
| Icône et logo | `assets/icone.*`, `assets/logo*.png` | Fabriqués par `outils/generer_logo.py` (cavalier « Tournoi plat » du projet + police Barlow) | Propriété du projet |
| Icônes des succès Steam | `docs/steam_succes/` | Fabriquées par `outils/generer_icones_succes.py` (pièces « Tournoi plat » du projet + police Barlow) ; pour Steamworks, pas chargées par le jeu | Propriété du projet |
| Fond du menu | `assets/menu/fond_menu.jpg` | Rendu Blender (`outils/blender/rendu_menu.py`) | Propriété du projet |
| Police Barlow Semi Condensed | `polices/` | Google Fonts (The Barlow Project) | SIL Open Font License (`BarlowSemiCondensed-OFL.txt`) |
| Police Outfit | `polices/` | Google Fonts | SIL Open Font License (`Outfit-OFL.txt`) |
| Police JetBrains Mono | `polices/` | JetBrains | SIL Open Font License (`JetBrainsMono-OFL.txt`) |
| Ouvertures (noms et coups) | `ouvertures/` | Base « chess-openings » de Lichess | CC0 – **origine à confirmer** |
| Problèmes (4 180 151) | `puzzles/` | Base de problèmes de Lichess (database.lichess.org) | CC0 (domaine public) – mention de Lichess conseillée |
| Moteur Stockfish | `moteur/` | stockfishchess.org | GNU GPL v3 (`moteur/COPYING-Stockfish.txt`) |
| Tables de finales Syzygy 3-4-5 pièces, WDL (`.rtbw`) et DTZ (`.rtbz`) | `syzygy/` | Ronald de Man (générateur github.com/syzygy1/tb), miroir lichess tablebase.lichess.ovh/tables/standard/ ; empreintes SHA-256 vérifiées le 31/10 (fichier `sha256` du miroir) | Libre redistribution : « All tablebase files generated using this generator may be freely redistributed » (README de syzygy1/tb, vérifié le 31/10/2026) ; sans droit d'auteur selon ce README (US : Feist ; UE : Football Dataco) |

## Retiré de V8_TURBO_3000 (ne jamais réintégrer)
- Pièces Pokémon (`assets/*.png`, `assets/pokemon/`) – marque et personnages protégés.
- Pièces « bois » (`assets/bois/`) – origine inconnue.
- `sounds/Nouveau dossier/` – extraits de films, chansons et mèmes.
- Anciens bruitages `.mp3/.ogg` – origine inconnue, remplacés.
- Logo, fond animé du menu, musique `game_start.mp3`, `icone.ico`, `wood_button.png` – origine inconnue.
- Nom « Pokemon Chess » – remplacé par SickChess.

## Sons « Feutre » et musique d'ambiance (17/10/2026)
- `sounds/feutre/` : les sons du pack « Bois » adoucis par `outils/generer_sons.py --feutre`
  (mêmes licences que les originaux : Kenney CC0 et sons synthétisés).
- `music/calme.wav` : musique entièrement synthétisée par `outils/generer_sons.py --musique`
  (aucune source extérieure, propriété du projet).
