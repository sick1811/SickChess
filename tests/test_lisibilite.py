# tests/test_lisibilite.py - lisibilite pour tous (24/10, travail p33).
#     python tests/test_lisibilite.py
# 1. Les pastilles se reconnaissent SANS la couleur (daltoniens) : un symbole
#    different pour chacune, lisible sur sa couleur (contour sombre).
# 2. Contrastes des textes de tous les themes (norme WCAG : 4,5 pour un texte).
# 3. Petits et grands ecrans : 1366x768 (portables) et 4K (3840x2160).

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((64, 64))

import annotations
import apparence
import design
import layout
import ui

# 26/10 : la disposition suit aussi « Taille des textes » ; on mesure avec la
# taille par defaut, pas avec le reglage du joueur qui lance les tests.
_reglage = apparence.reglage
apparence.reglage = lambda cle, defaut=None: (
    1.0 if cle == "echelle_interface" else _reglage(cle, defaut))

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


print("1. Pastilles sans la couleur")
symboles = [g for _n, _c, g in annotations.PASTILLES.values()]
verifier(len(set(symboles)) == len(symboles), "un symbole different par pastille : %s" % symboles)
for nom, couleur, _g in annotations.PASTILLES.values():
    blanc = design.contraste((255, 255, 255), couleur)
    contour = design.contraste(annotations.CONTOUR_GLYPHE, couleur)
    verifier(max(blanc, contour) >= 3.0, "%s : symbole lisible (blanc %.1f, contour %.1f)" % (nom, blanc, contour))
# Le contour est vraiment dessine : des pixels sombres autour du symbole jaune.
s = pygame.Surface((60, 60))
s.fill((40, 40, 40))
annotations.dessiner_pastille(s, (30, 30), 24, "imprecision")
sombres = sum(1 for x in range(12, 48) for y in range(12, 48)
              if max(s.get_at((x, y))[:3]) < 60)
verifier(sombres > 20, "contour sombre visible sur la pastille Imprecision (%d pixels)" % sombres)
# En gris : les pastilles d'une meme famille (fautes) restent differentes a l'oeil
# grace au symbole ; on verifie que deux pastilles ne donnent jamais la meme image.
images = {}
for cle in annotations.PASTILLES:
    s = pygame.Surface((40, 40))
    s.fill((40, 40, 40))
    annotations.dessiner_pastille(s, (20, 20), 16, cle)
    images[cle] = pygame.image.tobytes(pygame.transform.grayscale(s), "RGB")
verifier(len(set(images.values())) == len(images), "en noir et blanc, 10 pastilles toutes differentes")

print("2. Contrastes des textes (tous les plateaux)")
for nom in apparence.THEMES:
    t = apparence.theme(nom)
    mesures = [("texte", "panneau", 4.5), ("texte", "fond", 4.5),
               ("texte_discret", "panneau", 4.5), ("accent", "panneau", 3.0)]
    pire = min((design.contraste(t[a], t[b]) / mini, a, b) for a, b, mini in mesures if a in t and b in t)
    verifier(pire[0] >= 1.0, "%s : textes lisibles (le plus juste : %s sur %s)" % (nom, pire[1], pire[2]))

print("3. Tailles d'ecran")
d = layout.Disposition(1366, 768)
verifier(d.grand == 1.0 and d.panneau_x + d.panneau_l <= 1366 and d.cote_plateau >= 640,
         "1366x768 : comme avant (plateau %d px, panneau dans l'ecran)" % d.cote_plateau)
verifier(layout.Disposition(1920, 1080).grand < 1.05, "1920x1080 : presque inchange")
d = layout.Disposition(3840, 2160)
verifier(d.echelle > 3.0 and d.panneau_l >= 800 and d.panneau_x + d.panneau_l <= 3840,
         "4K : tout grandit (echelle %.2f, panneau %d px)" % (d.echelle, d.panneau_l))
bas = d.boutons[1] + d.boutons[3]
verifier(bas <= d.panneau_y + d.panneau_h, "4K : les boutons restent dans le panneau")
verifier(ui.grand_ecran((1366, 768)) == 1.0 and ui.grand_ecran((1024, 640)) == 1.0,
         "petits ecrans : les textes ne changent pas")
verifier(1.9 < ui.grand_ecran((3840, 2160)) < 2.2, "4K : textes des boutons ~2 fois plus grands")
verifier(ui.echelle((3840, 2160)) > 2.5, "4K : echelle des textes %.2f (1,65 avant)" % ui.echelle((3840, 2160)))
grand = pygame.Surface((3840, 2160))
rect = pygame.Rect(100, 100, 420, 60)
r = ui.texte_centre_dans(grand, "Commencer la partie", rect, 17)
petit = pygame.Surface((1366, 768))
r2 = ui.texte_centre_dans(petit, "Commencer la partie", rect, 17)
verifier(rect.contains(r) and r.height > 1.5 * r2.height,
         "4K : texte de bouton plus grand (%d px au lieu de %d) et dans le bouton" % (r.height, r2.height))

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
