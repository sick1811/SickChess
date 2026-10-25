# tests/test_arbre_ouvertures.py - les ouvertures rangees en arbre coup par
# coup (25/10, demande de Julien) et l'entrainement « ici ».
#     python tests/test_arbre_ouvertures.py
# Progression dans un dossier temporaire.

import json
import os
import random
import subprocess
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import pygame

pygame.init()

import asset_manager
TEMP = tempfile.mkdtemp(prefix="sickchess_arbre_")
asset_manager.dossier_ecriture = lambda: TEMP
import langue
langue.regler("fr")

import arbre_ouvertures as arbre
import entrainement
import ouvertures

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def tous(n):
    pile = [n]
    while pile:
        x = pile.pop()
        yield x
        pile.extend(x.enfants)


racine = arbre.racine()
livre = ouvertures.livre()

print("1. La Partie espagnole, coup par coup")
esp = arbre.noeud("e4 e5 Nf3 Nc6 Bb5")
verifier(esp is not None and esp.famille() == "Partie espagnole",
         "1.e4 e5 2.Nf3 Nc6 3.Bb5 est sous « Partie espagnole » (%s)" % (esp and esp.nom()))
verifier([n.san for n in esp.chemin()] == ["e4", "e5", "Nf3", "Nc6", "Bb5"],
         "un noeud = un demi-coup : 1.e4 › 1...e5 › 2.Nf3 › 2...Nc6 › 3.Bb5")
morphy = arbre.noeud("e4 e5 Nf3 Nc6 Bb5 a6")
verifier(morphy.parent is esp and "Morphy" in morphy.nom(),
         "3...a6 → Morphy : %s" % morphy.nom())
verifier(morphy.nom().startswith("Partie espagnole" + arbre.SEPARATEUR),
         "nom en arbre « famille › variante » : %s" % morphy.nom())
verifier(esp.eco == "C60" and morphy.eco == "C70", "codes ECO lichess : C60, C70")
passage = arbre.noeud("e4 e5 Nf3 Nc6 Bb5 a6 Ba4")
verifier(not passage.est_une_ligne() and passage.nom() == morphy.nom() and passage.code_eco() == "C70",
         "un coup de passage reste dans l'arbre et prend le nom du coup nommé au-dessus")
verifier(arbre.etiquette_coup(esp) == "3.Bb5" and arbre.etiquette_coup(morphy) == "3...a6",
         "étiquettes 3.Bb5 / 3...a6")
import notation
francais = lambda san: str(san).translate(notation.NOTATIONS["francaise"])
verifier(arbre.etiquette_chaine(esp.chemin()[2:], francais) == "2.Cf3 Cc6 3.Fb5",
         "chaîne sur une ligne, notation française : %s" % arbre.etiquette_chaine(esp.chemin()[2:], francais))

print("2. Aucune ligne lichess perdue, aucune en double")
nommes = [n for n in tous(racine) if n.est_une_ligne()]
verifier(len(nommes) == len(livre), "%d noeuds nommés = %d lignes lichess" % (len(nommes), len(livre)))
verifier(all(arbre.noeud(cle) is not None and arbre.noeud(cle).nom_lichess == nom
             for cle, (_eco, nom) in livre.items()),
         "chaque ligne du livre se retrouve à son coup, avec son nom")
cles = [n.cle() for n in tous(racine)]
verifier(len(cles) == len(set(cles)), "une suite de coups n'apparaît qu'une fois (%d noeuds)" % len(cles))
attendues = {c for c in livre if not any(d.startswith(c + " ") for d in livre)}
feuilles = racine.feuilles()
verifier(len(feuilles) == len(attendues) == racine.nb_lignes
         and {f.cle() for f in feuilles} == attendues,
         "feuilles = lignes qui ne sont le début d'aucune autre (%d)" % len(feuilles))
verifier(all(n.nb_lignes == len(n.feuilles()) for n in tous(esp)),
         "chaque noeud connaît le nombre de lignes sous lui")
illegales = []
for f in feuilles:
    try:
        f.position()
    except ValueError:
        illegales.append(f.cle())
verifier(not illegales, "les lignes se jouent sur un vrai échiquier (%s)" % illegales[:2])

print("3. Tri fixe, jamais au hasard")
verifier([e.san for e in racine.enfants[:2]] == ["e4", "d4"], "1.e4 puis 1.d4 en tête")
bien_trie = all(n.enfants == sorted(n.enfants, key=lambda e: (-e.nb_lignes, e.san))
                for n in tous(racine))
verifier(bien_trie, "à chaque niveau : le plus de lignes d'abord, puis l'ordre alphabétique")
code = ("import sys; sys.path.insert(0,'jeu'); import arbre_ouvertures as a, hashlib;"
        "r=a.racine(); p=[r]; s=[]\n"
        "while p:\n x=p.pop(); s.append(x.cle()); p.extend(reversed(x.enfants))\n"
        "print(hashlib.md5('|'.join(s).encode()).hexdigest())")
empreintes = set()
for graine in ("1", "2"):
    env = dict(os.environ, PYTHONHASHSEED=graine)
    sortie = subprocess.run([sys.executable, "-X", "utf8", "-c", code], capture_output=True,
                            text=True, env=env, cwd=RACINE).stdout.strip().splitlines()
    empreintes.add(sortie[-1] if sortie else "?")
verifier(len(empreintes) == 1 and "?" not in empreintes,
         "même ordre d'un lancement à l'autre (2 lancements, hachage différent)")

print("4. Construit une fois, gardé en mémoire")
verifier(arbre.racine() is racine, "deuxième appel : le même arbre, rien de relu")
verifier(arbre.noeud(["e4", "e5"]) is arbre.noeud("e4 e5"), "recherche par liste ou par texte")

print("5. Replier les coups de passage")
chaines = [arbre.chaine_depuis(n) for n in tous(racine) if n.parent is not None]
verifier(all(not c[i].nom_lichess and len(c[i].enfants) == 1 for c in chaines for i in range(len(c) - 1)),
         "une chaîne ne replie que des coups sans nom à un seul suivant")
verifier(any(len(c) > 1 for c in chaines), "il y a bien des chaînes repliées")

print("6. S'entraîner ici : jamais hors du groupe")
s = entrainement.Seance(morphy, chess.WHITE)
vues = [s.suivante() for _ in range(morphy.nb_lignes + 5)]
verifier(all(morphy.contient(n) for n in vues), "%d lignes tirées : toutes sous 3...a6" % len(vues))
verifier([n.cle() for n in vues[:morphy.nb_lignes]] == [f.cle() for f in morphy.feuilles()],
         "dans l'ordre de l'arbre, la plus jouée d'abord")
s = entrainement.Seance(morphy, chess.WHITE, hasard=random.Random(4))
melange = [s.suivante() for _ in range(morphy.nb_lignes)]
verifier(all(morphy.contient(n) for n in melange) and len(set(melange)) == morphy.nb_lignes,
         "au hasard dans ce groupe : toutes les lignes, une fois, toujours dans le groupe")
s = entrainement.Seance(morphy, chess.BLACK)
premiere = s.suivante()
s.resultat(50.0)
for _ in range(morphy.nb_lignes - 1):
    s.suivante()
    s.resultat(100.0)
verifier(s.suivante() is premiere and s.tour == 2, "la ligne ratée repasse à la fin du tour")
e = entrainement.Seance(esp, chess.WHITE)
e.suivante()
ligne = e.entrainement()
verifier(ligne.coups == e.courante.coups() and ligne.coups[:5] == ["e4", "e5", "Nf3", "Nc6", "Bb5"],
         "la ligne à réciter part du début de la partie")

print("7. Progression ligne par ligne, et l'ancien fichier repris")
chemin = os.path.join(TEMP, "entrainement.json")
ancien = {"Partie espagnole|blancs": {"lignes": 4, "parfaites": 1, "moyenne": 80.0}}
with open(chemin, "w", encoding="utf-8") as f:
    json.dump(ancien, f)
entrainement._EN_MEMOIRE.clear()
entrainement._REUSSIES.clear()
p = entrainement.progression("Partie espagnole", chess.WHITE)
verifier(p == ancien["Partie espagnole|blancs"], "ancienne progression reprise : %s" % p)
verifier(os.path.exists(chemin + ".bak"), "ancien fichier gardé en .bak")
with open(chemin + ".bak", encoding="utf-8") as f:
    verifier(json.load(f) == ancien, "le .bak est l'ancien fichier, intact")
with open(chemin, encoding="utf-8") as f:
    verifier(json.load(f).get("version") == 2, "le fichier est réécrit au format 2")
feuille = morphy.feuilles()[0]
entrainement.noter_une_ligne(feuille.famille(), chess.WHITE, 100.0, feuille.cle())
verifier(entrainement.reussies_sous(morphy, chess.WHITE) == 1
         and entrainement.reussies_sous(morphy, chess.BLACK) == 0,
         "1 ligne réussie sous 3...a6, avec les Blancs seulement")
verifier(entrainement.reussies_sous(arbre.noeud("e4 c5"), chess.WHITE) == 0,
         "rien de compté dans un autre groupe")
verifier(entrainement.progression("Partie espagnole", chess.WHITE)["lignes"] == 5,
         "la famille continue de compter (5 lignes)")
s = entrainement.Seance(morphy, chess.WHITE)
verifier(s.suivante() is not feuille, "une ligne déjà réussie passe après les autres")
entrainement._EN_MEMOIRE.clear()
entrainement._REUSSIES.clear()
verifier(entrainement.ligne(feuille.cle(), chess.WHITE)["reussie"], "relue après redémarrage")

print("8. L'écran : arbre, fil d'Ariane, échiquier, « S'entraîner ici »")
import ui
from ecran_entrainement import EcranEntrainement
for (l, h) in [(1366, 768), (1920, 1080), (3840, 2160)]:
    ecran = pygame.display.set_mode((l, h))
    ecr = EcranEntrainement(ecran, {})
    ecr.choisir(arbre.noeud("e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7"))
    ecr.draw()
    dans = ecran.get_rect()
    rects = [ecr.rect_arbre, ecr.rect_echiquier, ecr.btn_ici.rect, ecr.btn_blancs.rect,
             ecr.btn_noirs.rect, ecr.btn_retour_choix.rect]
    verifier(all(dans.contains(r) for r in rects) and not ecr.rect_arbre.colliderect(ecr.rect_echiquier),
             "%dx%d : tout tient dans l'écran, l'arbre à gauche, l'échiquier à droite" % (l, h))
    besoin = ui.t(17, ecr.ech) * 2 + ui.t(20, ecr.ech) * 2
    verifier(ecr.bas_infos - ecr.y_infos >= besoin,
             "%dx%d : nom sur 2 lignes + ECO + progression tiennent au-dessus des boutons" % (l, h))
ecran = pygame.display.set_mode((1366, 768))
ecr = EcranEntrainement(ecran, {})
verifier(ecr.choisi.san == "e4" and len(ecr.rangees()) == len(racine.enfants),
         "au départ : les premiers coups, 1.e4 choisi")
touche = lambda k: ecr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode=""))
touche(pygame.K_RIGHT)
verifier(ecr.choisi.san == "e4" and len(ecr.rangees()) > len(racine.enfants), "→ déplie 1.e4")
touche(pygame.K_RIGHT)
verifier(ecr.choisi.parent.san == "e4", "→ encore : on descend sur le premier suivant (%s)" % ecr.choisi)
touche(pygame.K_LEFT)
verifier(ecr.choisi.san == "e4", "← remonte au coup du dessus")
touche(pygame.K_MINUS)
verifier(len(ecr.rangees()) == len(racine.enfants), "− replie")
ecr.choisir(morphy)
ecr.draw()
verifier([n.san for _r, n in ecr._ariane] == ["", "e4", "e5", "Nf3", "Nc6", "Bb5", "a6"],
         "fil d'Ariane : Début › 1.e4 › … › 3...a6")
rect_e4 = ecr._ariane[1][0]
ecr.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect_e4.center))
verifier(ecr.choisi is arbre.noeud("e4"), "clic sur « 1.e4 » du fil d'Ariane : on remonte")
ecr.choisir(morphy)
rang = ecr._rang_du_choisi()
verifier(rang is not None and ecr.defilement <= rang < ecr.defilement + ecr.rangees_visibles,
         "le noeud choisi est visible dans l'arbre")
ecr.draw()
image = ecr._image_position[1]
verifier(image.get_size() == ecr.rect_echiquier.size, "l'échiquier montre la position du noeud")
avant = ecr._image_position
ecr.draw()
verifier(ecr._image_position is avant and ecr._image_arbre[1] is not None,
         "rien n'est redessiné quand rien ne bouge (images gardées)")
ecr.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=ecr.btn_ici.rect.center))
verifier(ecr.etape == "jeu" and ecr.seance.noeud is morphy and morphy.contient(ecr.seance.courante),
         "« S'entraîner ici » : une ligne sous 3...a6")
for _ in range(3):
    n = 0
    while not ecr.entr.termine() and n < 60:
        n += 1
        if ecr.adverse_a:
            ecr.adverse_a = 1
            ecr.update()
        elif ecr.entr.a_moi_de_jouer():
            ecr.plateau.make_move(chess.Move.from_uci(ecr.entr.coup_attendu_uci()))
    verifier(morphy.contient(ecr.seance.courante) and ecr.entr.termine(),
             "ligne %d finie, toujours sous 3...a6" % ecr.seance.numero)
    ecr.nouvelle_ligne()
ecr.draw()
touche(pygame.K_ESCAPE)
verifier(ecr.etape == "arbre" and ecr.choisi is morphy, "Échap : retour à l'arbre, au même noeud")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
