"""Images de la page Steam de SickChess (formats Steamworks, verifies le 17/10/2026)."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
B = "/tmp/claude-0/-home-claude/871d864b-9b4a-5f6b-b2d5-d5bfbc1b0e87/scratchpad/blender/out"
L = "/home/claude/logo"
LARGE = Image.open(f"{B}/steam_large.png").convert("RGB")
CENTRE = Image.open(f"{B}/steam_large_centre.png").convert("RGB")
HAUT = Image.open(f"{B}/steam_haut.png").convert("RGB")
ICONE = Image.open(f"{L}/png/hd_icone_officiel.png").convert("RGBA")
FB = f"{L}/BarlowSemiCondensed-Bold.ttf"; FR = f"{L}/BarlowSemiCondensed-Regular.ttf"
OR, IVOIRE, GRIS, ONYX = (214, 176, 74), (243, 240, 232), (150, 144, 136), (14, 14, 16)
OUT = "steam"; os.makedirs(OUT, exist_ok=True)

def couvrir(src, w, h, cx=0.5, cy=0.5):
    s = max(w / src.width, h / src.height)
    im = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
    x = int((im.width - w) * cx); y = int((im.height - h) * cy)
    return im.crop((x, y, x + w, y + h))

def voile_gauche(im, part=0.80, force=240):
    w, h = im.size
    v = Image.new("L", (w, 1))
    for x in range(w):
        p = x / w
        v.putpixel((x, 0), force if p < part * 0.45 else max(0, int(force * (1 - (p - part * 0.45) / (part * 0.75)))))
    m = v.resize((w, h))
    noir = Image.new("RGB", (w, h), ONYX)
    return Image.composite(noir, im, m)

def voile_haut(im, part=0.45, force=240):
    w, h = im.size
    v = Image.new("L", (1, h))
    for y in range(h):
        p = y / h
        v.putpixel((0, y), force if p < part * 0.55 else max(0, int(force * (1 - (p - part * 0.55) / (part * 0.6)))))
    return Image.composite(Image.new("RGB", (w, h), ONYX), im, v.resize((w, h)))

def nom(d, x, y, taille, ancre="la"):
    f = ImageFont.truetype(FB, taille)
    w1 = d.textlength("SICK", font=f); w2 = d.textlength("CHESS", font=f)
    if ancre == "ma":
        x = x - (w1 + w2) / 2
    d.text((x, y), "SICK", font=f, fill=IVOIRE); d.text((x + w1, y), "CHESS", font=f, fill=OR)
    return w1 + w2

def devise(d, x, y, taille, ancre="la", esp=0.45):
    f = ImageFont.truetype(FR, taille)
    txt = "ENTRAÎNE  ·  ANALYSE  ·  GAGNE"
    # espacement des lettres a la main
    largeur = sum(d.textlength(c, font=f) + taille * esp for c in txt) - taille * esp
    if ancre == "ma":
        x = x - largeur / 2
    for c in txt:
        d.text((x, y), c, font=f, fill=GRIS); x += d.textlength(c, font=f) + taille * esp
    return largeur

def bloc_horizontal(im, x, cy, h_nom, avec_devise=True):
    """Icone + SICKCHESS (+ devise) ; cy = centre vertical du bloc."""
    d = ImageDraw.Draw(im)
    ic = int(h_nom * 1.25 if avec_devise else h_nom * 1.1)
    hb = ic
    y0 = int(cy - hb / 2)
    icone = ICONE.resize((ic, ic), Image.LANCZOS)
    im.paste(icone, (x, y0), icone)
    tx = x + ic + int(h_nom * 0.25)
    if avec_devise:
        nom(d, tx, y0 - int(h_nom * 0.12), h_nom)
        devise(d, tx + 3, y0 + int(h_nom * 0.95), max(10, int(h_nom * 0.22)))
    else:
        nom(d, tx, y0 + (ic - h_nom) / 2 - h_nom * 0.12, h_nom)

def bloc_vertical(im, cx, y, h_nom):
    d = ImageDraw.Draw(im)
    ic = int(h_nom * 1.7)
    icone = ICONE.resize((ic, ic), Image.LANCZOS)
    im.paste(icone, (int(cx - ic / 2), y), icone)
    nom(d, cx, y + ic + int(h_nom * 0.15), h_nom, "ma")
    devise(d, cx, y + ic + int(h_nom * 1.3), max(10, int(h_nom * 0.2)), "ma", esp=0.4)

def large(w, h, h_nom, devise_=True, cx=0.62):
    im = voile_gauche(couvrir(LARGE, w, h, cx=cx))
    bloc_horizontal(im, int(w * 0.06), h // 2, h_nom, devise_)
    return im

def vertical(w, h):
    im = voile_haut(couvrir(HAUT, w, h, cy=1.0), part=0.5)
    bloc_vertical(im, w // 2, int(h * 0.07), int(w * 0.15))
    return im

large(920, 430, 64).save(f"{OUT}/header_capsule_920x430.png")
large(462, 174, 38, devise_=False, cx=0.5).save(f"{OUT}/small_capsule_462x174.png")
large(1232, 706, 86).save(f"{OUT}/main_capsule_1232x706.png")
vertical(748, 896).save(f"{OUT}/vertical_capsule_748x896.png")
vertical(600, 900).save(f"{OUT}/library_capsule_600x900.png")
large(920, 430, 64).save(f"{OUT}/library_header_920x430.png")
couvrir(CENTRE, 3840, 1240, cx=0.5, cy=0.55).save(f"{OUT}/library_hero_3840x1240.png")
lg = Image.open(f"{L}/final/logo.png").convert("RGBA")
lg.resize((1280, round(lg.height * 1280 / lg.width)), Image.LANCZOS).save(f"{OUT}/library_logo_1280.png")
fond = couvrir(CENTRE, 1438, 810).filter(ImageFilter.GaussianBlur(6))
fond = Image.blend(fond, Image.new("RGB", fond.size, ONYX), 0.6)
fond.save(f"{OUT}/page_background_1438x810.png")
ICONE.resize((184, 184), Image.LANCZOS).save(f"{OUT}/community_icon_184x184.png")
print(sorted(os.listdir(OUT)))
