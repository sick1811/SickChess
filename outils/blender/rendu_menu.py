"""Fond du menu principal : plateau en marbre, partie en cours, eclairage Onyx & Or.
usage : python3 rendu_menu.py <famille> <sortie.png> [samples] [largeur] [blend]"""
import sys, math, os
sys.path.insert(0, os.path.dirname(__file__))
import bpy
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
import sick3d as S

fam = ARGS[0]; out = ARGS[1]
spp = int(ARGS[2]) if len(ARGS) > 2 else 64
W = int(ARGS[3]) if len(ARGS) > 3 else 1920
blend = ARGS[4] if len(ARGS) > 4 else None

S.reset()
S.cycles(samples=spp, w=W, h=int(W * 9 / 16))
S.monde((0.004, 0.004, 0.005), 1.0)

ivoire = S.mat_piece("Ivoire", (0.86, 0.82, 0.74), rough=0.3, coat=0.5, sss=0.15)
ebene = S.mat_piece("Ebene", (0.018, 0.017, 0.016), rough=0.22, coat=0.8)
clair = S.mat_marbre("MarbreClair", (0.80, 0.78, 0.74), (0.38, 0.37, 0.36), echelle=1.8)
sombre = S.mat_marbre("MarbreSombre", (0.22, 0.21, 0.19), (0.62, 0.55, 0.42), echelle=2.3)
onyx = S.mat_simple("Onyx", (0.012, 0.012, 0.014), rough=0.14)
orr = S.mat_or()

S.plateau(clair, sombre, onyx, orr)
sol = S.box("sol", (80, 80, 0.1), (0, 0, -0.3)); S.assign(sol, S.mat_simple("Sol", (0.004, 0.004, 0.005), 0.75))

# milieu de partie (Italienne, 12 coups)
FEN = "r4rk1/pp2qppp/2np1n2/2b1p1B1/2B1P1b1/2PP1N2/PP1N1PPP/R2Q1RK1"
S.poser(fam, FEN, ivoire, ebene)

S.lampe("cle", "AREA", (-5, -4, 9), (0, 0, 0), 1300, (1, 0.96, 0.9), 5)
S.viser(bpy.data.objects["cle"], (1, 0, 0))
S.lampe("contre", "AREA", (6, 10, 3.5), (0, 0, 0), 3800, (1, 0.74, 0.36), 4)
S.viser(bpy.data.objects["contre"], (1, 0, 0.6))
S.lampe("rase", "AREA", (12, -2, 1.2), (0, 0, 0), 500, (1, 0.8, 0.5), 3)
S.viser(bpy.data.objects["rase"], (2, 0, 0.3))

# camera basse, coin h1, plateau a droite de l'image : la gauche reste libre pour le menu
cam = S.camera((13.5, -11.0, 2.9), (0.8, 0.6, 0.2), focale=58, dof=16.6, fstop=2.0)
cam.data.shift_x = -0.30
cam.data.shift_y = 0.04

bpy.context.scene.render.filepath = out
if blend:
    bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.render.render(write_still=True)
print("OK", out)
