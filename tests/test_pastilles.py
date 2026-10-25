# tests/test_pastilles.py - les pastilles de la feuille de coups de la revue
# (25/10, retour t100 de Julien : "peu lisibles", a faire plus grosses ET plus
# contrastees).
#     python tests/test_pastilles.py
# On dessine la vraie feuille (moteur factice, une pastille de chaque sorte) a
# 900x560, 1366x768 et 1920x1080, puis on MESURE les pixels :
# 1. la pastille est grosse : au moins 75 % de la hauteur d'une ligne ;
# 2. elle reste dans sa ligne (ne touche pas les lignes voisines), alignee avec
#    le texte du coup, et ne chevauche pas ce texte ;
# 3. son contour se detache du fond (contraste >= 4,5, ligne surlignee comprise) ;
# 4. le signe se lit sur sa couleur (contraste >= 4,5), une couleur par sorte.

import os
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import pygame

pygame.init()
ecran = pygame.display.set_mode((1366, 768))

import annotations
import apparence
import design
from analyse_partie import AnalyseurPartie
from ecran_revue import EcranRevue

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


PARTIE = ("e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 f3g5 d7d5 e4d5 f6d5 g5f7 e8f7 d1f3 "
          "f7e6 b1c3 c6b4 f3e4 c7c6 d2d4 b4d3").split()
SORTES = ["imprecision", "brillant", "gaffe", "tres_bon", "erreur", "meilleur",
          "manque", "excellent", "theorique", "bon"]


class MoteurFactice:
    def analyser_position(self, fen, profondeur=0, temps_max_ms=0, lignes=1):
        coup = next(iter(chess.Board(fen).legal_moves))
        return {"coup": coup.uci(), "evaluation": 0.2, "mat": None,
                "second_evaluation": 0.1, "second_mat": None}


a = AnalyseurPartie(None, PARTIE, moteur=MoteurFactice())
a.demarrer()
fin = time.time() + 60
while a.en_cours and time.time() < fin:
    time.sleep(0.1)
detail_vrai = a.detail


def detail_force(i):
    """Une sorte de pastille differente a chaque coup : les dix sont visibles."""
    d = dict(detail_vrai(i))
    d["pret"], d["note"] = True, SORTES[i % len(SORTES)]
    return d


a.detail = detail_force

# La couleur du signe (blanc avant la correction : c'etait le defaut).
couleur_signe = getattr(annotations, "couleur_signe", lambda cle: (255, 255, 255))

print("1. Le signe sur sa couleur, une couleur par sorte")
couleurs = [annotations.couleur(c) for c in annotations.PASTILLES]
verifier(len(set(couleurs)) == len(couleurs), "une couleur differente par sorte")
for cle in annotations.PASTILLES:
    c = design.contraste(couleur_signe(cle), annotations.couleur(cle))
    verifier(c >= 4.5, "%s : signe lisible sur sa couleur (contraste %.1f)"
             % (annotations.libelle(cle), c))

print("2. La feuille de coups, mesuree au pixel")
for taille in ((900, 560), (1366, 768), (1920, 1080)):
    ecran = pygame.display.set_mode(taille)
    r = EcranRevue(ecran, a, {}, ("Toi", "Ordinateur"), "0-1")
    r.aller_a(5, son=False)        # le coup 5 est surligne (fond accent)
    r.draw()
    t = apparence.theme(r.plateau.theme_plateau)
    h = r.hauteur_ligne
    petits, debordes, colles, decales, ternes, signes = [], [], [], [], [], []
    diametres = []
    for rect, index in r.rects_coups:
        cle = SORTES[index % len(SORTES)]
        courant = index == r.index - 1
        # Le fond reel de chaque rang (le cadre a un leger degrade) : le pixel
        # juste a gauche de la case ; sur la ligne surlignee, l'accent.
        fonds = {y: {tuple(ecran.get_at((rect.x - 1, y)))[:3], tuple(t["accent"])}
                 for y in range(rect.y, rect.bottom)}

        def encre(x, rect=rect, fonds=fonds, ecran=ecran):
            return [y for y in range(rect.y, rect.bottom)
                    if tuple(ecran.get_at((x, y)))[:3] not in fonds[y]]
        # La pastille = la premiere tache de pixels a gauche de la case.
        x = rect.x + 2
        while x < rect.right and not encre(x):
            x += 1
        gauche = x
        while x < rect.right and encre(x):
            x += 1
        droite = x - 1
        rangs = [y for xx in range(gauche, droite + 1) for y in encre(xx)]
        haut, bas = min(rangs), max(rangs)
        diametre = droite - gauche + 1
        diametres.append(diametre)
        cy = (haut + bas) / 2.0
        if diametre < 0.75 * h:
            petits.append(diametre)
        if haut <= rect.y or bas >= rect.bottom - 1:
            debordes.append(index)
        # Le texte du coup : la tache suivante, a 3 pixels au moins.
        x = droite + 1
        while x < rect.right and not encre(x):
            x += 1
        if x - droite - 1 < 3:
            colles.append(index)
        rangs_texte = [y for xx in range(x, min(rect.right, x + int(1.2 * h)))
                       for y in encre(xx)]
        if rangs_texte:
            centre_texte = (min(rangs_texte) + max(rangs_texte)) / 2.0
            if abs(centre_texte - cy) > max(3, 0.15 * h):
                decales.append((index, round(centre_texte - cy, 1)))
        # Le contour (2e colonne de la pastille, a mi-hauteur) contre le fond.
        bord = tuple(ecran.get_at((gauche + 1, int(cy))))[:3]
        fond = tuple(t["accent"]) if courant else tuple(ecran.get_at((rect.x - 1, int(cy))))[:3]
        if design.contraste(bord, fond) < 4.5:
            ternes.append((index, round(design.contraste(bord, fond), 1)))
        # Le signe est bien dessine : au coeur de la pastille (hors contour), des
        # pixels nets (contraste >= 3 avec la couleur de la pastille, lissage compris).
        cx, ry = (gauche + droite) / 2.0, diametre * 0.32
        nets = sum(1 for xx in range(gauche, droite + 1) for yy in range(haut, bas + 1)
                   if (xx - cx) ** 2 + (yy - cy) ** 2 <= ry * ry
                   and design.contraste(tuple(ecran.get_at((xx, yy)))[:3],
                                        annotations.couleur(cle)) >= 3.0)
        if nets < 4:
            signes.append((cle, nets))
    nom = "%dx%d" % taille
    verifier(not petits, "%s : pastilles de %d px au moins (75 %% d'une ligne de %d px) %s"
             % (nom, min(diametres), h, petits[:3]))
    verifier(not debordes, "%s : chaque pastille reste dans sa ligne %s" % (nom, debordes[:3]))
    verifier(not colles, "%s : la pastille ne touche pas le texte du coup %s" % (nom, colles[:3]))
    verifier(not decales, "%s : pastille alignee avec le texte %s" % (nom, decales[:3]))
    verifier(not ternes, "%s : contour detache du fond, ligne surlignee comprise %s"
             % (nom, ternes[:3]))
    verifier(not signes, "%s : signe dessine dans sa couleur lisible %s" % (nom, signes[:3]))
    if taille == (1366, 768):
        verifier(len(r.rects_coups) >= 10, "1366x768 : %d coups visibles (dix sortes)"
                 % len(r.rects_coups))

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
