---
name: menage-code
description: Faire le ménage dans SickChess sans rien casser - imports et variables inutiles, fonctions jamais appelées, fichiers orphelins, ressources non utilisées, doublons, restes de fabrication. À utiliser quand Julien demande de nettoyer, d'alléger ou d'enlever le code inutile.
---

# Ménage du code et des fichiers

Point de départ : `python outils/banc_essai.py --sections menage,conflits` puis
`docs/BANC_ESSAI.md` (section Ménage). Avant tout : `git status` propre (ou commit), tests verts.

## Ordre (du plus sûr au plus délicat), un lot = un commit
1. **Imports et variables inutiles** (sûr) :
   `python -m ruff check --select F401,F841 --fix jeu outils SickChess.py`
   puis `python tests/lancer_tous.py --rapide`.
2. **Fonctions, méthodes, classes jamais appelées** (vulture) – vérifier CHACUNE :
   - `grep -rn "nom" jeu tests outils SickChess.py` : appel par texte (`getattr`,
     dictionnaire de commandes, `"nom"` dans un JSON), tests qui l'utilisent ?
   - Méthodes appelées par pygame, Steam, threading, json (`handle_event`, `run`,
     `default`…) : faux positifs → les ajouter à `outils/vulture_liste_blanche.py`
     avec la raison.
   - Code commenté « gardé pour plus tard » : demander à Julien.
   - Supprimer, tests verts, commit « Ménage : <fichier> ».
3. **Fichiers de `jeu/` jamais importés** (ex. `fond_anime.py`) : vérifier qu'aucun
   écran ne le charge par son nom, le retirer, tests + lancement réel du jeu.
4. **Ressources non citées** (images, sons) : beaucoup de noms sont fabriqués
   (`"%s.png" % piece`, dossiers de thèmes) → chercher le dossier et le motif avant de
   retirer ; en cas de doute, déplacer dans `assets_src/retire/` plutôt que supprimer,
   et mettre à jour `docs/CREDITS.md`.
5. **Doublons** : garder un seul fichier si le code peut pointer dessus (sons de nulle
   identiques : un seul fichier, plusieurs noms dans le code).
6. **Restes sur le disque** (`publier/`, `build_amis/`, `__pycache__`, `tests/capture_*.png`) :
   pas sur GitHub, mais ils prennent de la place. Les supprimer seulement avec l'accord
   de Julien (`publier/` et `build_amis/` se refont avec `CONSTRUIRE_VERSION_AMIS.bat`).

## Ne jamais toucher
`profil.json`, `parties/`, `puzzles_score.json`, `succes.json`, `mes_erreurs.json`,
`puzzles/`, `syzygy/`, `moteur/`, l'archive `../V8_TURBO_3000`.

## Après
Banc `--sections menage,vitesse` pour voir le gain, ligne dans `docs/JOURNAL.md`
(« Ménage : −N lignes, −X Mo »), recette : rien à changer sauf fonction retirée.

## Règles d'échecs intouchables
Mat, pat, matériel insuffisant, position morte, 3 et 5 répétitions, 50 et 75 coups, chute
au temps sans matériel de mat = nulle, roque (et roque Freestyle), prise en passant,
promotion (4 pièces) : valables dans tous les modes. Ne jamais les supprimer, les
affaiblir ni retirer leurs contrôles (`tests/test_regles.py`, `tests/test_freestyle.py`).
Un test de règle rouge = c'est le code qu'on corrige, jamais le test qu'on retire.
