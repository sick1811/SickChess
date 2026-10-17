"""Fabrique l'icone et le logo de SickChess (Onyx & Or).

    python outils/generer_logo.py

Tout est fait a partir de ressources du projet : le cavalier du jeu de pieces
"Tournoi plat" (assets/pieces/plat_tournoi, dessine pour SickChess) et la
police Barlow Semi Condensed (licence OFL). Ecrit :
    assets/icone.ico          icone de la fenetre et du futur .exe (16 a 256 px)
    assets/icone.png          la meme en 256 px
    assets/logo.png           logo horizontal, fond transparent
    assets/logo_fond.png      logo sur fond onyx (pages Steam / itch.io)
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(RACINE, "assets")
POLICE = os.path.join(RACINE, "polices", "BarlowSemiCondensed-Bold.ttf")
CAVALIER = os.path.join(ASSETS, "pieces", "plat_tournoi", "n.png")

OR = np.array((214, 176, 74), dtype=np.float32)          # #d6b04a, l'accent du jeu
OR_CLAIR = np.array((240, 210, 128), dtype=np.float32)
OR_SOMBRE = np.array((150, 116, 40), dtype=np.float32)
ONYX_HAUT = (30, 29, 27)
ONYX_BAS = (11, 11, 10)
BLANC = (240, 236, 228)


def cavalier_or(taille):
    """Le cavalier en or : corps en degrade dore, traits interieurs sombres."""
    im = Image.open(CAVALIER).convert("RGBA")
    # on recadre sur la piece elle-meme pour qu'elle remplisse l'icone
    boite = im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
    im = im.crop(boite)
    cote = max(im.size)
    carre = Image.new("RGBA", (cote, cote), (0, 0, 0, 0))
    carre.paste(im, ((cote - im.width) // 2, (cote - im.height) // 2))
    carre = carre.resize((taille, taille), Image.LANCZOS)
    a = np.asarray(carre).astype(np.float32)
    # les pixels presque transparents de l'image d'origine faisaient un carre
    # sombre visible derriere la piece : on les efface franchement
    a[..., 3] = np.where(a[..., 3] < 24, 0, a[..., 3])
    lum = a[..., :3].mean(axis=2) / 255.0                 # 1 = blanc, 0 = trait noir
    hauteur = np.linspace(0, 1, taille)[:, None, None]
    corps = OR_CLAIR * (1 - hauteur) + OR_SOMBRE * hauteur   # lumiere du haut
    trait = np.array(ONYX_BAS, dtype=np.float32)
    rgb = trait * (1 - lum[..., None]) + corps * lum[..., None]
    out = np.dstack([rgb, a[..., 3]]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def tuile(T):
    """Tuile onyx aux coins arrondis, filet dore, cavalier au centre."""
    rayon = int(T * 0.2)
    masque = Image.new("L", (T, T), 0)
    ImageDraw.Draw(masque).rounded_rectangle((0, 0, T - 1, T - 1), rayon, fill=255)
    fond = Image.new("RGBA", (T, T))
    d = ImageDraw.Draw(fond)
    for y in range(T):
        k = y / (T - 1)
        d.line((0, y, T, y), fill=tuple(int(ONYX_HAUT[i] * (1 - k) + ONYX_BAS[i] * k)
                                       for i in range(3)) + (255,))
    fond.putalpha(masque)
    # filet dore interieur (seulement quand l'icone est assez grande pour le voir)
    if T >= 48:
        e = max(2, T // 40)
        m = int(T * 0.045)
        ImageDraw.Draw(fond).rounded_rectangle((m, m, T - 1 - m, T - 1 - m),
                                               rayon - m, outline=tuple(int(c) for c in OR) + (255,),
                                               width=e)
    piece = cavalier_or(int(T * (0.74 if T >= 48 else 0.86)))
    # halo tres doux derriere la piece, pour la detacher du fond
    halo = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    halo_a = piece.getchannel("A").filter(ImageFilter.GaussianBlur(T * 0.05))
    couche = Image.new("RGBA", piece.size, tuple(int(c) for c in OR) + (0,))
    couche.putalpha(halo_a.point(lambda v: int(v * 0.25)))
    pos = ((T - piece.width) // 2, (T - piece.height) // 2 + int(T * 0.01))
    halo.alpha_composite(couche, pos)
    fond.alpha_composite(halo)
    fond.alpha_composite(piece, pos)
    return fond


def logo(hauteur=300, avec_fond=False):
    police = ImageFont.truetype(POLICE, int(hauteur * 0.62))
    gauche, droite = "SICK", "CHESS"
    l1 = police.getlength(gauche)
    l2 = police.getlength(droite)
    icone = tuile(int(hauteur * 0.82))
    ecart = int(hauteur * 0.16)
    marge = int(hauteur * 0.12)
    L = int(marge + icone.width + ecart + l1 + l2 + marge)
    im = Image.new("RGBA", (L, hauteur), (ONYX_BAS + (255,)) if avec_fond else (0, 0, 0, 0))
    im.alpha_composite(icone, (marge, (hauteur - icone.height) // 2))
    d = ImageDraw.Draw(im)
    x = marge + icone.width + ecart
    y = (hauteur - police.getbbox("SICKCHESS")[3]) // 2 - int(hauteur * 0.02)
    d.text((x, y), gauche, font=police, fill=BLANC)
    d.text((x + l1, y), droite, font=police, fill=tuple(int(c) for c in OR))
    return im


def main():
    grande = tuile(256)
    grande.save(os.path.join(ASSETS, "icone.png"))
    # chaque taille est dessinee pour elle-meme (pas une reduction de la 256)
    tailles = [16, 24, 32, 48, 64, 128, 256]
    images = [tuile(t) for t in tailles]
    images[-1].save(os.path.join(ASSETS, "icone.ico"), sizes=[(t, t) for t in tailles],
                    append_images=images[:-1])
    logo().save(os.path.join(ASSETS, "logo.png"))
    logo(avec_fond=True).save(os.path.join(ASSETS, "logo_fond.png"))
    print("icone et logo ecrits dans", ASSETS)


if __name__ == "__main__":
    main()
