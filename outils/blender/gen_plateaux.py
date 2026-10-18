"""Textures de plateau procedurales (numpy) - images 1024 x 1024 pretes pour le jeu.
Chaque case est taillee dans une zone differente de la matiere, comme un vrai plateau.
usage : python3 gen_plateaux.py <dossier> [taille]"""
import sys, os
import numpy as np
from PIL import Image, ImageFilter

RNG = np.random.default_rng(1811)

def fbm(n, octaves=6, base=4, persist=0.55, seed=None):
    r = np.random.default_rng(seed) if seed is not None else RNG
    out = np.zeros((n, n), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        g = base * 2 ** o
        grid = (r.random((g + 1, g + 1)) * 255).astype(np.uint8)
        im = Image.fromarray(grid).resize((n, n), Image.BICUBIC)
        out += amp * (np.asarray(im, np.float32) / 255.0); tot += amp; amp *= persist
    return out / tot

def lerp(a, b, t):
    return a[None, None, :] * (1 - t[..., None]) + b[None, None, :] * t[..., None]

def C(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)

def marbre(n, fond, veine, fond2=None, freq=1.3, turb=2.4, finesse=0.05, seed=0):
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) / n
    t = fbm(n, 7, 2, 0.52, seed)
    ang = np.random.default_rng(seed).random() * np.pi
    u = x * np.cos(ang) + y * np.sin(ang)
    v = np.abs(np.sin((u * freq + t * turb) * np.pi))
    vein = np.clip(1 - v / finesse, 0, 1) ** 1.3                 # veines principales
    t2 = fbm(n, 6, 3, 0.5, seed + 31)
    v2 = np.abs(np.sin((u * freq * 2.3 + t2 * turb * 1.6) * np.pi))
    vein = np.maximum(vein, 0.45 * np.clip(1 - v2 / (finesse * 0.6), 0, 1))   # veinules
    vein = np.asarray(Image.fromarray((vein * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    nuage = fbm(n, 5, 2, 0.6, seed + 99)
    base = lerp(C(fond), C(fond2 or fond) , np.clip((nuage - 0.35) * 2, 0, 1))
    grain = (fbm(n, 2, 64, 0.5, seed + 7) - 0.5) * 10
    col = lerp(np.zeros(3), np.ones(3), np.zeros((n, n)))  # placeholder shape
    col = base * (1 - vein[..., None] * 0.85) + C(veine)[None, None, :] * (vein[..., None] * 0.85)
    return np.clip(col + grain[..., None], 0, 255)

def bois(n, clair, fonce, freq=2.2, seed=0, vertical=False):
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) / n
    if vertical: x, y = y, x
    t = fbm(n, 6, 2, 0.5, seed)
    fibre = fbm(n, 3, 48, 0.5, seed + 3)
    w = 0.5 + 0.5 * np.sin((y * freq + t * 1.3) * 2 * np.pi)
    w = w ** 2.2
    fines = 0.5 + 0.5 * np.sin((y * freq * 9 + t * 6 + fibre * 2) * 2 * np.pi)
    col = lerp(C(clair), C(fonce), np.clip(w * 0.5 + fines * 0.18 + (fibre - 0.5) * 0.25, 0, 1))
    return np.clip(col, 0, 255)

def uni(n, c, seed=0, bruit=4):
    g = (fbm(n, 3, 8, 0.5, seed) - 0.5) * bruit
    return np.clip(C(c)[None, None, :] + g[..., None], 0, 255)

JEUX = {
    "marbre":  (lambda s, i: marbre(s, "#ebe8e2", "#9a958e", "#e2ded6", seed=i),
                lambda s, i: marbre(s, "#a29d95", "#e4e0d8", "#948f87", seed=500 + i, finesse=0.04)),
    "onyx_or": (lambda s, i: marbre(s, "#d9d2c3", "#b08a46", "#cfc6b4", seed=i, finesse=0.035),
                lambda s, i: marbre(s, "#18181a", "#b58d45", "#232326", seed=500 + i, finesse=0.03, turb=2.8)),
    "noyer":   (lambda s, i: bois(s, "#e3c79d", "#c49a68", seed=i, vertical=i % 2 == 0),
                lambda s, i: bois(s, "#7b5232", "#4a2d18", seed=500 + i, vertical=i % 2 == 1)),
    "ardoise": (lambda s, i: uni(s, "#c9ced6", i), lambda s, i: uni(s, "#59647a", 500 + i)),
    "tournoi": (lambda s, i: uni(s, "#ecedd1", i, 3), lambda s, i: uni(s, "#78965a", 500 + i, 3)),
}

def plateau(nom, N=1024):
    case = N // 8
    img = np.zeros((N, N, 3), np.float32)
    fc, fs = JEUX[nom]
    if nom in ("marbre", "onyx_or"):
        # deux grandes plaques ; chaque case y est prelevee ailleurs, tournee au hasard
        fc_, fs_ = fc(N, 0), fs(N, 0)
        r_ = np.random.default_rng(7)
        for r in range(8):
            for f in range(8):
                src = fc_ if (r + f) % 2 == 0 else fs_
                a, b = r_.integers(0, 8, 2)
                tile = src[a * case:(a + 1) * case, b * case:(b + 1) * case]
                tile = np.rot90(tile, r_.integers(0, 4))
                img[r * case:(r + 1) * case, f * case:(f + 1) * case] = tile
    else:
      for r in range(8):
        for f in range(8):
            i = r * 8 + f
            tex = (fc if (r + f) % 2 == 0 else fs)(case, i)
            img[r * case:(r + 1) * case, f * case:(f + 1) * case] = tex
    # fin joint entre les cases (pierre/bois uniquement)
    if nom in ("marbre", "onyx_or", "noyer"):
        for k in range(1, 8):
            img[k * case - 1:k * case + 1, :] *= 0.9; img[:, k * case - 1:k * case + 1] *= 0.9
    return Image.fromarray(img.astype(np.uint8))

if __name__ == "__main__":
    out = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
    os.makedirs(out, exist_ok=True)
    for nom in JEUX:
        plateau(nom, N).save(os.path.join(out, f"plateau_{nom}.png")); print("OK", nom)
