"""Sprites de pieces pour le jeu : 12 PNG transparents par famille, cadrage IDENTIQUE
pour toutes les pieces (meme camera orthographique), ombre de contact incluse.
usage : python3 rendu_sprites.py <famille> <dossier> [taille] [samples]
fichiers : p.png n.png b.png r.png q.png k.png (blancs), pb.png ... kb.png (noirs)"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import bpy
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
import sick3d as S

fam, out = ARGS[0], ARGS[1]
T = int(ARGS[2]) if len(ARGS) > 2 else 256
spp = int(ARGS[3]) if len(ARGS) > 3 else 48
os.makedirs(out, exist_ok=True)

# Legere remise a l'echelle : en 2D vu de dessus, un pion a l'echelle reelle est
# trop petit pour se lire. On rapproche les tailles sans les egaliser.
GROSSIR = {"p": 1.30, "n": 1.10, "b": 1.06, "r": 1.08, "q": 1.0, "k": 0.96}

S.reset()
sc = S.cycles(samples=spp, w=T, h=T)
sc.render.film_transparent = True
sc.render.image_settings.color_mode = "RGBA"
S.monde((0.55, 0.56, 0.6), 0.12)

ivoire = S.mat_piece("Ivoire", (0.95, 0.92, 0.85), rough=0.38, coat=0.35, sss=0.1)
ebene = S.mat_piece("Ebene", (0.012, 0.012, 0.013), rough=0.3, coat=0.5)

if os.environ.get("OMBRE", "1") == "1":
    sol = S.box("ombre", (6, 6, 0.01), (0, 0, -0.005)); sol.is_shadow_catcher = True

S.lampe("cle", "AREA", (-1.6, -2.0, 5.0), (0, 0, 0), 560, (1, 0.97, 0.92), 3)
S.viser(bpy.data.objects["cle"], (0, 0, 0.6))
S.lampe("contre", "AREA", (2.2, 3.5, 3.2), (0, 0, 0), 520, (1, 0.86, 0.62), 2.2)
S.viser(bpy.data.objects["contre"], (0, 0, 0.8))
S.lampe("bouche", "AREA", (3.5, -2.5, 1.2), (0, 0, 0), 45, (0.85, 0.9, 1), 2)
S.viser(bpy.data.objects["bouche"], (0, 0, 0.5))

el = math.radians(float(os.environ.get("ELEVATION", "16")))
cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"; cd.ortho_scale = 1.74
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
d = 12
cam.location = (0, -d * math.cos(el), 0.80 + d * math.sin(el))
S.viser(cam, (0, 0, 0.80))
cd.shift_y = 0.045

for kind in "pnbrqk":
    for blanc in (True, False):
        o = S.piece(fam, kind, name=kind)
        g = GROSSIR[kind]; L = 1.32; o.scale = (g * L, g * L, g)
        if kind == "n":
            o.rotation_euler.z = math.radians(float(os.environ.get("ROT_CAVALIER", "-20")))  # tete vers la gauche, un peu de 3/4
            # recentrer la silhouette (le cavalier n'est pas symetrique)
            o.location.x = 0.03
        elif fam == "prisme":
            o.rotation_euler.z = math.radians(22.5)
        S.assign(o, ivoire if blanc else ebene)
        nom = kind + ("" if blanc else "b")
        sc.render.filepath = os.path.join(out, nom + ".png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(o, do_unlink=True)
        print("OK", fam, nom)
