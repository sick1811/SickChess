"""Post-traitement des sprites rendus : cadrage commun serre + contour de lisibilite.
usage : python3 finir_sprites.py <dossier_rendu> <dossier_sortie> [taille]"""
import sys, os
import numpy as np
from PIL import Image, ImageFilter

NOMS = ["p", "n", "b", "r", "q", "k", "pb", "nb", "bb", "rb", "qb", "kb"]

def finir(src, dst, T=256, haut=0.05, bas=0.09):
    os.makedirs(dst, exist_ok=True)
    ims = {n: Image.open(os.path.join(src, n + ".png")).convert("RGBA") for n in NOMS}
    W = ims["k"].width
    # cadre commun : la boite de TOUTES les pieces (sans l'ombre legere), meme pour le pion
    top, bot = W, 0
    for im in ims.values():
        a = np.asarray(im)[..., 3]
        ys = np.where(a.max(axis=1) > 200)[0]
        top, bot = min(top, ys.min()), max(bot, ys.max())
    h = bot - top
    cote = int(h / (1 - haut - bas))
    y0 = top - int(cote * haut); x0 = W // 2 - cote // 2
    for n, im in ims.items():
        c = im.crop((x0, y0, x0 + cote, y0 + cote)).resize((T, T), Image.LANCZOS)
        a = c.split()[3]
        solide = a.point(lambda v: 255 if v > 110 else 0)
        epais = solide.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(0.7))
        blanc = len(n) == 1   # "b" = fou BLANC, "bb" = fou noir
        couleur = (24, 22, 20) if blanc else (205, 200, 190)
        force = 0.85 if blanc else 0.35
        bord = Image.new("RGBA", (T, T), couleur + (0,))
        bord.putalpha(epais.point(lambda v: int(v * force)))
        out = Image.alpha_composite(bord, c)
        out.save(os.path.join(dst, n + ".png"))
    print("OK", dst, "cadre", cote, "px")

if __name__ == "__main__":
    finir(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 256)
