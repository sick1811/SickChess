"""Illustrations Steam (sans texte) : plateau marbre, pieces Tournoi, lumiere Onyx & Or.
usage : python3 rendu_steam.py <large|haut> <sortie.png> [samples] [largeur]"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import bpy
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
import sick3d as S
mode, out = ARGS[0], ARGS[1]
spp = int(ARGS[2]) if len(ARGS) > 2 else 48
W = int(ARGS[3]) if len(ARGS) > 3 else 2560
H = int(W * 9 / 16) if mode == "large" else int(W * 1.2)
S.reset(); S.cycles(samples=spp, w=W, h=H); S.monde((0.004, 0.004, 0.005), 1.0)
ivoire = S.mat_piece("Ivoire", (0.86, 0.82, 0.74), rough=0.3, coat=0.5, sss=0.15)
ebene = S.mat_piece("Ebene", (0.018, 0.017, 0.016), rough=0.22, coat=0.8)
clair = S.mat_marbre("MarbreClair", (0.80, 0.78, 0.74), (0.38, 0.37, 0.36), echelle=1.8)
sombre = S.mat_marbre("MarbreSombre", (0.22, 0.21, 0.19), (0.62, 0.55, 0.42), echelle=2.3)
onyx = S.mat_simple("Onyx", (0.012, 0.012, 0.014), rough=0.14)
S.plateau(clair, sombre, onyx, S.mat_or())
sol = S.box("sol", (80, 80, 0.1), (0, 0, -0.3)); S.assign(sol, S.mat_simple("Sol", (0.004, 0.004, 0.005), 0.75))
# finale tendue : le cavalier blanc au centre de l'image
FEN = "r4rk1/pp2qppp/2np1n2/2b1p1B1/2B1P1b1/2PP1N2/PP1N1PPP/R2Q1RK1"
S.poser("tournoi", FEN, ivoire, ebene)
S.lampe("cle", "AREA", (-5, -4, 9), (0, 0, 0), 1300, (1, 0.96, 0.9), 5); S.viser(bpy.data.objects["cle"], (0, 0, 0))
S.lampe("contre", "AREA", (6, 10, 3.5), (0, 0, 0), 3800, (1, 0.74, 0.36), 4); S.viser(bpy.data.objects["contre"], (0, 0, 0.6))
S.lampe("rase", "AREA", (12, -2, 1.2), (0, 0, 0), 500, (1, 0.8, 0.5), 3); S.viser(bpy.data.objects["rase"], (2, 0, 0.3))
cav = (-0.5, 1.5, 0.6)   # d5
if mode == "large":
    cam = S.camera((14.0, -11.4, 3.0), (0.8, 0.6, 0.2), focale=58, dof=17.3, fstop=2.0)
    cam.data.shift_x = -0.42
else:
    cam = S.camera((2.2, -10.5, 4.4), (0.0, 0.6, 0.4), focale=55, dof=11.0, fstop=2.2)
    cam.data.shift_y = 0.20
bpy.context.scene.render.filepath = out
bpy.ops.render.render(write_still=True); print("OK", out)
