"""Rend chaque famille de pieces alignee (blancs devant, noirs derriere).
usage : python3 rendu_familles.py <famille> <sortie.png> [samples] [largeur]"""
import sys, math, os
sys.path.insert(0, os.path.dirname(__file__))
import bpy
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
import sick3d as S

fam = ARGS[0]; out = ARGS[1]
spp = int(ARGS[2]) if len(ARGS) > 2 else 64
W = int(ARGS[3]) if len(ARGS) > 3 else 1600

S.reset()
S.cycles(samples=spp, w=W, h=int(W * 9 / 16))
S.monde((0.006, 0.006, 0.007), 1.0)

ivoire = S.mat_piece("Ivoire", (0.86, 0.82, 0.74), rough=0.3, coat=0.5, sss=0.15)
ebene = S.mat_piece("Ebene", (0.018, 0.017, 0.016), rough=0.22, coat=0.8)
onyx = S.mat_simple("Onyx", (0.012, 0.012, 0.013), rough=0.18)
orr = S.mat_or()

# socle : plaque d'onyx avec filet dore
sol = S.box("sol", (40, 40, 0.1), (0, 0, -0.05)); S.assign(sol, onyx)
fil = S.box("filet", (7.6, 0.03, 0.012), (0, -1.05, 0.0)); S.assign(fil, orr)

ordre = ["r", "n", "b", "q", "k", "p"]
for i, k in enumerate(ordre):
    x = (i - 2.5) * 1.15
    w = S.piece(fam, k, name=f"B_{k}"); w.location = (x, -0.35, 0); S.assign(w, ivoire)
    b = S.piece(fam, k, name=f"N_{k}"); b.location = (x + 0.35, 0.95, 0); S.assign(b, ebene)
    if k == "n":
        w.rotation_euler.z = math.radians(160); b.rotation_euler.z = math.radians(160)
    elif fam == "prisme":
        w.rotation_euler.z = b.rotation_euler.z = math.radians(22.5)

S.lampe("cle", "AREA", (-4, -6, 6), (0, 0, 0), 900, (1, 0.97, 0.92), 4)
S.viser(bpy.data.objects["cle"], (0, 0, 0.5))
S.lampe("contre", "AREA", (3, 7, 3.5), (0, 0, 0), 900, (1, 0.78, 0.42), 3)
S.viser(bpy.data.objects["contre"], (0, 0, 0.7))
S.lampe("bouche", "AREA", (7, -3, 2), (0, 0, 0), 180, (0.85, 0.9, 1), 3)
S.viser(bpy.data.objects["bouche"], (0, 0, 0.5))

S.camera((0.6, -10.5, 3.9), (0.35, 0.3, 0.5), focale=50, dof=10.8, fstop=5.6)
bpy.context.scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("OK", out)
