"""ATTENTION (17/10, conversation graphisme) : Julien a choisi les pieces Relief
VUES DE FACE (sans perspective ni ombre au sol). assets_src/pieces_relief_origine/
contient maintenant ces versions-la, et assets/pieces/relief_* aussi. Ne relancer ce
script qu'apres avoir verifie le resultat (il ajoute une ombre de contact).

Retouche des pieces "Relief" (rendus Blender) pour la lisibilite en jeu.

Part des images d'origine gardees dans assets_src/pieces_relief_origine/ et
ecrit le resultat dans assets/pieces/. On peut donc le relancer sans risque :
    python outils/retoucher_pieces.py

Ce qu'il fait, piece par piece :
  1. enleve l'ombre portee qui partait vers la droite (elle salissait la case
     voisine et decentrait la piece) ;
  2. redessine un contour regulier : sombre et franc autour des blancs (pour
     se detacher des cases claires), clair et discret autour des noirs (pour
     les cases sombres) ;
  3. donne un peu plus de modele aux pieces blanches (les ombres propres de la
     piece sont legerement creusees : moins "blanc sur creme") ;
  4. pose une petite ombre de contact, CENTREE sous le socle.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(RACINE, "assets_src", "pieces_relief_origine")
SORTIE = os.path.join(RACINE, "assets", "pieces")
JEUX = ["relief_prisme", "relief_arene", "relief_tournoi"]
NOMS = ["p", "n", "b", "r", "q", "k", "pb", "nb", "bb", "rb", "qb", "kb"]

CONTOUR_BLANC = (34, 30, 26)      # autour des pieces blanches
CONTOUR_NOIR = (214, 208, 196)    # autour des pieces noires
EPAISSEUR = 7                     # en pixels, pour une image de 256


def retoucher(chemin_source, blanc):
    im = Image.open(chemin_source).convert("RGBA")
    T = im.width
    rgba = np.asarray(im).astype(np.float32)
    alpha = rgba[..., 3]

    # 1. La piece = les pixels presque opaques ; l'ombre est en dessous de 100.
    solide = Image.fromarray(((alpha > 200) * 255).astype(np.uint8))
    garde = np.asarray(solide.filter(ImageFilter.MaxFilter(5))).astype(np.float32) / 255
    alpha_net = alpha * garde
    # le contour d'origine (inegal) est retire : on ne garde que la piece elle-meme
    piece_seule = (alpha_net > 200).astype(np.uint8) * 255
    masque = Image.fromarray(piece_seule).filter(ImageFilter.MinFilter(3))
    masque = masque.filter(ImageFilter.GaussianBlur(0.8))
    a_piece = np.asarray(masque).astype(np.float32)

    rgb = rgba[..., :3]
    if blanc:
        # 3. un peu plus de modele : on creuse les tons moyens, pas les clairs
        n = rgb / 255.0
        rgb = (np.power(n, 1.35) * 0.92 + n * 0.08) * 255

    piece = np.dstack([rgb, a_piece]).clip(0, 255).astype(np.uint8)
    piece = Image.fromarray(piece, "RGBA")

    # 2. contour regulier
    base = Image.fromarray((a_piece > 100).astype(np.uint8) * 255)
    epais = base.filter(ImageFilter.MaxFilter(EPAISSEUR)).filter(ImageFilter.GaussianBlur(1.0))
    couleur, force = (CONTOUR_BLANC, 0.95) if blanc else (CONTOUR_NOIR, 0.55)
    bord = Image.new("RGBA", (T, T), couleur + (0,))
    bord.putalpha(epais.point(lambda v: int(v * force)))

    # 4. ombre de contact centree sous le socle
    lignes = np.where(np.asarray(base).max(axis=1) > 0)[0]
    colonnes = np.where(np.asarray(base).max(axis=0) > 0)[0]
    bas = int(lignes.max())
    gauche, droite = int(colonnes.min()), int(colonnes.max())
    centre = (gauche + droite) / 2
    demi = (droite - gauche) / 2 * 1.05
    ombre = Image.new("L", (T, T), 0)
    ImageDraw.Draw(ombre).ellipse((centre - demi, bas - T * 0.03,
                                   centre + demi, bas + T * 0.025), fill=90)
    ombre = ombre.filter(ImageFilter.GaussianBlur(T * 0.018))
    calque_ombre = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    calque_ombre.putalpha(ombre)

    resultat = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    for calque in (calque_ombre, bord, piece):
        resultat = Image.alpha_composite(resultat, calque)
    return resultat


def main():
    for jeu in JEUX:
        dossier = os.path.join(SORTIE, jeu)
        os.makedirs(dossier, exist_ok=True)
        for nom in NOMS:
            source = os.path.join(SOURCE, jeu, nom + ".png")
            retoucher(source, blanc=(len(nom) == 1)).save(
                os.path.join(dossier, nom + ".png"))
        print("OK", jeu)


if __name__ == "__main__":
    main()
