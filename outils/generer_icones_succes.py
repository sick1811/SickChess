"""Fabrique les icones des succes Steam de SickChess (24/10, travail p37).

    python outils/generer_icones_succes.py

Steamworks demande, pour chaque succes, une icone « debloque » et une icone
« bloque » (grise), en JPG carre. On les fabrique ici, a partir de ressources
du projet seulement : les pieces « Tournoi plat » (assets/pieces/plat_tournoi,
dessinees pour SickChess) et la police Barlow Semi Condensed (licence OFL).
Direction artistique Onyx & Or : disque onyx, anneau or, piece or, chiffre clair.

Ecrit dans docs/steam_succes/ (pas dans assets/ : ces images ne servent qu'a
Steamworks, le jeu ne les charge pas) :
    <NOM_API>.jpg          256 x 256, debloque
    <NOM_API>_gris.jpg     256 x 256, bloque
    apercu.png             toutes les icones sur une planche (pour juger d'un coup d'oeil)
"""
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

SORTIE = os.path.join(RACINE, "docs", "steam_succes")
PIECES = os.path.join(RACINE, "assets", "pieces", "plat_tournoi")
POLICE = os.path.join(RACINE, "polices", "BarlowSemiCondensed-Bold.ttf")
TAILLE = 256

ONYX = (22, 21, 19)
ONYX_CLAIR = (46, 44, 40)
OR = (214, 176, 74)          # #d6b04a, l'accent du jeu
OR_SOMBRE = (150, 116, 40)
IVOIRE = (240, 236, 228)

# Nom API -> (piece, texte sous la piece). Les noms API viennent de jeu/succes.py.
DESSINS = {
    "PREMIERE_VICTOIRE": ("k", "1"),
    "VICTOIRE_1500": ("q", "1500"),
    "VICTOIRE_2000": ("q", "2000"),
    "VICTOIRE_MAT": ("k", "#"),
    "PRECISION_90": ("b", "90%"),
    "SERIE_10": ("n", "x10"),
    "PROBLEMES_100": ("r", "100"),
    "CLASSEMENT_1500": ("n", "1500"),
    "CHRONO_15": ("p", "15"),
    "SURVIE_10": ("r", "10"),
    "JOUR_7": ("p", "7"),
    "OUVERTURE_PARFAITE": ("b", "1.e4"),
    "EN_LIGNE": ("n", "2"),
    "IMPORTER": ("r", "PGN"),
}


def _piece_en_or(lettre, cote):
    """La piece blanche « Tournoi plat », passee en or (le dessin garde ses ombres)."""
    image = pygame.image.load(os.path.join(PIECES, lettre + ".png")).convert_alpha()
    image = pygame.transform.smoothscale(image, (cote, cote))
    teinte = pygame.Surface(image.get_size(), pygame.SRCALPHA)
    teinte.fill(OR + (255,))
    image.blit(teinte, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return image


def icone(nom_api):
    lettre, texte = DESSINS[nom_api]
    s = pygame.Surface((TAILLE, TAILLE))
    s.fill(ONYX)
    centre = TAILLE // 2
    # disque onyx un peu plus clair au centre, anneau or
    for r in range(centre - 10, 0, -2):
        part = r / float(centre - 10)
        couleur = tuple(int(ONYX_CLAIR[i] * (1 - part) + ONYX[i] * part) for i in range(3))
        pygame.draw.circle(s, couleur, (centre, centre), r)
    pygame.draw.circle(s, OR_SOMBRE, (centre, centre), centre - 8, 6)
    pygame.draw.circle(s, OR, (centre, centre), centre - 12, 3)
    piece = _piece_en_or(lettre, int(TAILLE * 0.50))
    s.blit(piece, piece.get_rect(center=(centre, int(TAILLE * 0.42))))
    police = pygame.font.Font(POLICE, int(TAILLE * (0.20 if len(texte) <= 3 else 0.16)))
    rendu = police.render(texte, True, IVOIRE)
    s.blit(rendu, rendu.get_rect(center=(centre, int(TAILLE * 0.76))))
    return s


def en_gris(surface):
    """La version « bloquee » : en gris, plus sombre."""
    gris = pygame.transform.grayscale(surface)
    voile = pygame.Surface(gris.get_size())
    voile.fill((150, 150, 150))
    gris.blit(voile, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    return gris


def main():
    import succes
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(SORTIE, exist_ok=True)
    noms = [api for _cle, api, _t, _d in succes.SUCCES]
    manquants = [n for n in noms if n not in DESSINS]
    if manquants:
        print("Succes sans dessin (a ajouter dans DESSINS) : %s" % ", ".join(manquants))
        return 1
    colonnes = 7
    planche = pygame.Surface((colonnes * 132, ((len(noms) + colonnes - 1) // colonnes) * 2 * 132))
    planche.fill((60, 58, 54))
    for i, nom in enumerate(noms):
        image = icone(nom)
        gris = en_gris(image)
        pygame.image.save(image, os.path.join(SORTIE, nom + ".jpg"))
        pygame.image.save(gris, os.path.join(SORTIE, nom + "_gris.jpg"))
        x, y = (i % colonnes) * 132 + 2, (i // colonnes) * 264 + 2
        planche.blit(pygame.transform.smoothscale(image, (128, 128)), (x, y))
        planche.blit(pygame.transform.smoothscale(gris, (128, 128)), (x, y + 132))
    pygame.image.save(planche, os.path.join(SORTIE, "apercu.png"))
    print("%d succes : %d icones dans %s" % (len(noms), 2 * len(noms), SORTIE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
