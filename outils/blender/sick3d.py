"""SickChess - bibliotheque 3D (Blender / bpy).

Pieces originales construites par tour (profil tourne autour de l'axe) +
cavalier extrude depuis une silhouette dessinee a la main. Trois familles :
  - tournoi : Staunton simplifie, courbes douces
  - arene   : moderne, cylindres et chanfreins nets
  - prisme  : comme arene mais a facettes (8 cotes)
Une case du plateau = 1 unite Blender.
"""
import bpy, bmesh, math
from mathutils import Vector

# ------------------------------------------------------------------ outils
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def _link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj

def lathe(name, prof, steps=96, smooth=True):
    """prof : liste (r, z) du bas vers le haut ; r=0 aux extremites."""
    bm = bmesh.new()
    verts = [bm.verts.new((r, 0, z)) for r, z in prof]
    edges = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=math.tau, steps=steps, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    obj = _link(bpy.data.objects.new(name, me))
    for p in me.polygons:
        p.use_smooth = smooth
    if smooth:
        m = obj.modifiers.new("aretes", "EDGE_SPLIT"); m.split_angle = math.radians(35)
    return obj

def box(name, size, loc):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    o = _link(bpy.data.objects.new(name, me)); o.scale = size; o.location = loc
    return o

def sphere(name, r, loc, seg=48):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    bm.to_mesh(me); bm.free()
    o = _link(bpy.data.objects.new(name, me)); o.location = loc
    for p in me.polygons: p.use_smooth = True
    return o

def cut(target, cutter):
    m = target.modifiers.new("coupe", "BOOLEAN"); m.object = cutter; m.operation = "DIFFERENCE"
    m.solver = "EXACT"
    cutter.hide_render = True; cutter.hide_viewport = True
    return target

def join(objs, name):
    """Applique les modificateurs et fusionne en un seul objet."""
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for o in objs:
        ev = o.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev)
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    out = bpy.data.meshes.new(name); bm.to_mesh(out); bm.free()
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    obj = _link(bpy.data.objects.new(name, out))
    return obj

def bevel(obj, w=0.01, seg=2, ang=40):
    m = obj.modifiers.new("biseau", "BEVEL"); m.width = w; m.segments = seg
    m.limit_method = "ANGLE"; m.angle_limit = math.radians(ang)
    return obj

def shade(obj, smooth=True, ang=35):
    for p in obj.data.polygons: p.use_smooth = smooth
    if smooth:
        m = obj.modifiers.new("aretes", "EDGE_SPLIT"); m.split_angle = math.radians(ang)

# ------------------------------------------------------------------ profils
# Socle commun (r, z). Chaque famille a son socle.
def socle(fam, R):
    if fam == "tournoi":
        return [(0, 0), (R, 0), (R, 0.045), (R * .97, 0.06), (R * .86, 0.075), (R * .84, 0.105),
                (R * .9, 0.125), (R * .86, 0.15), (R * .72, 0.17)]
    # arene / prisme : marches nettes
    return [(0, 0), (R, 0), (R, 0.06), (R * .9, 0.07), (R * .9, 0.11), (R * .74, 0.12)]

PROFILS = {
 "tournoi": {
  "p": lambda: socle("tournoi", .30) + [(.17, .20), (.12, .36), (.10, .44), (.16, .46), (.16, .49), (.10, .51),
                                        (.135, .54), (.165, .60), (.165, .66), (.13, .73), (.07, .775), (0, .785)],
  "r": lambda: socle("tournoi", .33) + [(.23, .22), (.19, .40), (.18, .62), (.22, .66), (.22, .69), (.19, .71),
                                        (.21, .74), (.23, .76), (.23, .93), (.16, .93), (.16, .86), (0, .86)],
  "b": lambda: socle("tournoi", .34) + [(.20, .22), (.13, .50), (.11, .68), (.19, .70), (.19, .73), (.11, .76),
                                        (.155, .82), (.175, .90), (.165, .99), (.12, 1.07), (.06, 1.12),
                                        (.035, 1.13), (.05, 1.15), (.055, 1.18), (.035, 1.21), (0, 1.22)],
  "q": lambda: socle("tournoi", .38) + [(.24, .22), (.15, .58), (.13, .84), (.23, .87), (.23, .90), (.14, .93),
                                        (.17, 1.00), (.23, 1.12), (.25, 1.18), (.20, 1.19), (.15, 1.22),
                                        (.10, 1.26), (.0, 1.27)],
  "k": lambda: socle("tournoi", .40) + [(.25, .22), (.16, .62), (.14, .92), (.24, .95), (.24, .98), (.15, 1.01),
                                        (.18, 1.08), (.24, 1.22), (.25, 1.27), (.17, 1.30), (.10, 1.33),
                                        (.07, 1.34), (0, 1.34)],
  "n": lambda: socle("tournoi", .35) + [(.25, .21), (.24, .25), (0, .25)],
 },
 "arene": {
  "p": lambda: socle("arene", .29) + [(.14, .14), (.105, .44), (.17, .46), (.17, .50), (.09, .52)]
               + [(.135 * math.cos(a), .645 + .135 * math.sin(a))
                  for a in [math.radians(d) for d in (-62, -40, -15, 10, 35, 58, 78)]] + [(0, .78)],
  "r": lambda: socle("arene", .32) + [(.21, .14), (.18, .66), (.225, .69), (.225, .92), (.155, .92), (.155, .85), (0, .85)],
  "b": lambda: socle("arene", .33) + [(.18, .14), (.11, .70), (.19, .72), (.19, .76), (.12, .78), (.17, .86),
                                      (.17, .98), (.08, 1.12), (0, 1.13)],
  "q": lambda: socle("arene", .37) + [(.23, .14), (.13, .86), (.23, .88), (.23, .92), (.14, .94), (.25, 1.15),
                                      (.25, 1.20), (0, 1.20)],
  "k": lambda: socle("arene", .39) + [(.24, .14), (.14, .94), (.25, .96), (.25, 1.00), (.15, 1.02), (.25, 1.22),
                                      (.25, 1.28), (0, 1.28)],
  "n": lambda: socle("arene", .34) + [(.25, .14), (.25, .18), (0, .18)],
 },
}
PROFILS["prisme"] = PROFILS["arene"]

# silhouette du cavalier (x vers l'avant = -x, z en haut), dessin original
CAVALIER = [(.20, 0), (.23, .30), (.21, .52), (.15, .70), (.08, .82), (.05, .92), (.01, .84), (-.06, .80),
            (-.20, .66), (-.31, .52), (-.33, .44), (-.29, .38), (-.17, .40), (-.07, .42), (-.03, .34),
            (-.12, .18), (-.17, 0)]
CAVALIER_ARENE = [(.20, 0), (.22, .34), (.17, .62), (.07, .80), (.03, .90), (-.02, .80), (-.30, .52),
                  (-.30, .42), (-.08, .42), (-.04, .30), (-.16, 0)]

def _extrude(name, pts, depth, z0):
    bm = bmesh.new()
    vs = [bm.verts.new((x, -depth / 2, z + z0)) for x, z in pts]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=nv, vec=(0, depth, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return _link(bpy.data.objects.new(name, me))

STEPS = {"tournoi": 96, "arene": 96, "prisme": 8}

def piece(fam, kind, name=None):
    name = name or f"{fam}_{kind}"
    st = STEPS[fam]; sm = fam != "prisme"
    parts = [lathe(name + "_corps", PROFILS[fam][kind](), steps=st, smooth=sm)]
    top = PROFILS[fam][kind]()[-1][1]
    if kind == "r":  # creneaux
        for a in (0, 90):
            c = box("cr", (0.08, 0.7, 0.2), (0, 0, top + 0.03)); c.rotation_euler.z = math.radians(a + (22.5 if fam == "prisme" else 0))
            cut(parts[0], c)
    if kind == "b":  # fente de la mitre
        z = 0.95 if fam == "tournoi" else 0.97
        c = box("fente", (0.035, 0.6, 0.5), (0.06, 0, z + 0.1)); c.rotation_euler.y = math.radians(35)
        cut(parts[0], c)
    if kind == "q":
        if fam == "tournoi":
            n = 10
            for i in range(n):
                a = math.tau * i / n
                parts.append(sphere("perle", .035, (math.cos(a) * .23, math.sin(a) * .23, 1.19), seg=24))
            parts.append(sphere("tete", .065, (0, 0, 1.31)))
        else:
            n = 8
            for i in range(n):
                a = math.tau * i / n
                c = box("dent", (0.08, 0.3, 0.12), (math.cos(a) * .25, math.sin(a) * .25, 1.22))
                c.rotation_euler.z = a; cut(parts[0], c)
            parts.append(sphere("tete", .06, (0, 0, 1.26), seg=(8 if fam == "prisme" else 32)))
    if kind == "k":
        if fam == "tournoi":
            parts.append(box("croixv", (0.07, 0.07, 0.30), (0, 0, top + 0.14)))
            parts.append(box("croixh", (0.22, 0.07, 0.07), (0, 0, top + 0.18)))
        else:
            parts.append(box("croixv", (0.08, 0.08, 0.28), (0, 0, top + 0.13)))
            parts.append(box("croixh", (0.24, 0.08, 0.08), (0, 0, top + 0.16)))
    if kind == "n":
        sil = CAVALIER if fam == "tournoi" else CAVALIER_ARENE
        k = _extrude("tete_cheval", sil, 0.24 if fam == "tournoi" else 0.26, top - 0.01)
        bevel(k, w=(0.035 if fam == "tournoi" else 0.012), seg=(4 if fam == "tournoi" else 1), ang=60)
        parts.append(k)
    obj = join(parts, name)
    if fam == "prisme":
        shade(obj, smooth=False)
    else:
        shade(obj, smooth=True, ang=38)
        bevel(obj, w=0.004, seg=2, ang=50)
    obj["famille"] = fam; obj["type"] = kind
    return obj

# ------------------------------------------------------------------ materiaux
def mat_piece(nom, couleur, rough=0.28, coat=0.6, sss=0.0):
    m = bpy.data.materials.new(nom); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*couleur, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.08
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.4, 0.3, 0.2)
        b.inputs["Subsurface Scale"].default_value = 0.02
    return m

def mat_or(nom="Or", rough=0.22):
    m = bpy.data.materials.new(nom); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.86, 0.66, 0.30, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    return m

def mat_marbre(nom, base, veine, echelle=2.2, rough=0.12):
    """Marbre procedural : bruit deforme + rampe pour les veines."""
    m = bpy.data.materials.new(nom); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (echelle, echelle * 0.6, echelle)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6
    nz.inputs["Detail"].default_value = 12; nz.inputs["Roughness"].default_value = 0.62
    nz.inputs["Distortion"].default_value = 3.2
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 1.4
    wv.inputs["Distortion"].default_value = 14.0; wv.inputs["Detail"].default_value = 8
    L.new(mp.outputs["Vector"], wv.inputs["Vector"])
    mix = N.new("ShaderNodeMix"); mix.data_type = "FLOAT"; mix.inputs[0].default_value = 0.12
    L.new(nz.outputs["Fac"], mix.inputs[2]); L.new(wv.outputs["Fac"], mix.inputs[3])
    cr = N.new("ShaderNodeValToRGB")
    e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = (*base, 1)
    e[1].position = 0.50; e[1].color = (*base, 1)
    e3 = e.new(0.525); e3.color = (*veine, 1)
    e4 = e.new(0.545); e4.color = (*base, 1)
    L.new(mix.outputs[0], cr.inputs["Fac"])
    L.new(cr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 0.35
    return m

def mat_simple(nom, couleur, rough=0.4, metal=0.0):
    m = bpy.data.materials.new(nom); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*couleur, 1)
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    return m

def assign(obj, mat):
    obj.data.materials.clear(); obj.data.materials.append(mat)

# ------------------------------------------------------------------ plateau
def plateau(mat_clair, mat_sombre, mat_cadre, mat_filet, epaisseur=0.18, bord=0.55):
    objs = []
    for f in range(8):
        for r in range(8):
            c = box(f"case_{f}{r}", (1, 1, epaisseur), (f - 3.5, r - 3.5, -epaisseur / 2))
            assign(c, mat_clair if (f + r) % 2 else mat_sombre)
            objs.append(c)
    s = 8 + 2 * bord
    cadre = box("cadre", (s, s, epaisseur + 0.04), (0, 0, -(epaisseur + 0.04) / 2 - 0.004))
    bevel(cadre, w=0.04, seg=3); assign(cadre, mat_cadre)
    # filet dore autour des cases
    t = 0.035; L = 8 + 2 * 0.09
    for (sx, sy, x, y) in ((L, t, 0, L / 2), (L, t, 0, -L / 2), (t, L, L / 2, 0), (t, L, -L / 2, 0)):
        fb = box("filet", (sx, sy, 0.01), (x, y, 0.0)); assign(fb, mat_filet)
    return objs

def case_xy(sq):
    return ("abcdefgh".index(sq[0]) - 3.5, int(sq[1]) - 3.5)

def poser(fam, fen, mat_b, mat_n, rot_cavalier=True):
    placed = []
    rows = fen.split()[0].split("/")
    for i, row in enumerate(rows):
        f = 0
        for ch in row:
            if ch.isdigit():
                f += int(ch); continue
            sq = "abcdefgh"[f] + str(8 - i)
            o = piece(fam, ch.lower(), name=f"{ch}_{sq}")
            x, y = case_xy(sq); o.location = (x, y, 0)
            white = ch.isupper()
            if ch.lower() == "n":
                o.rotation_euler.z = math.radians(90 if white else -90)
            elif fam == "prisme":
                o.rotation_euler.z = math.radians(22.5)
            assign(o, mat_b if white else mat_n)
            placed.append(o)
            f += 1
    return placed

# ------------------------------------------------------------------ rendu
def cycles(samples=64, w=1600, h=900, pct=100):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    try:
        sc.cycles.use_denoising = True
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.cycles.max_bounces = 6; sc.cycles.glossy_bounces = 3; sc.cycles.transparent_max_bounces = 4
    sc.render.resolution_x = w; sc.render.resolution_y = h; sc.render.resolution_percentage = pct
    sc.view_settings.view_transform = "AgX"
    try: sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception: pass
    sc.render.image_settings.file_format = "PNG"
    return sc

def monde(couleur=(0.01, 0.01, 0.012), force=1.0):
    w = bpy.data.worlds.new("Monde"); bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*couleur, 1); bg.inputs["Strength"].default_value = force
    return w

def lampe(nom, typ, loc, rot, energie, couleur=(1, 1, 1), taille=2.0):
    ld = bpy.data.lights.new(nom, typ); ld.energy = energie; ld.color = couleur
    if typ == "AREA":
        ld.size = taille; ld.shape = "DISK"
    o = _link(bpy.data.objects.new(nom, ld)); o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]
    return o

def viser(obj, cible):
    d = Vector(cible) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

def camera(loc, cible, focale=50, dof=None, fstop=2.8):
    cd = bpy.data.cameras.new("Cam"); cd.lens = focale
    o = _link(bpy.data.objects.new("Cam", cd)); o.location = loc; viser(o, cible)
    bpy.context.scene.camera = o
    if dof:
        cd.dof.use_dof = True; cd.dof.focus_distance = dof; cd.dof.aperture_fstop = fstop
    return o

def mat_bois(nom, clair, fonce, echelle=6.0, rough=0.35, rot=0.0):
    """Bois procedural : veinage par bandes deformees."""
    m = bpy.data.materials.new(nom); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (echelle * 0.15, echelle, echelle)
    mp.inputs["Rotation"].default_value = (0, 0, rot)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.0; nz.inputs["Detail"].default_value = 6
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Y"
    wv.inputs["Scale"].default_value = 1.2; wv.inputs["Distortion"].default_value = 4.0
    wv.inputs["Detail"].default_value = 4
    L.new(mp.outputs["Vector"], wv.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].color = (*fonce, 1); e[1].color = (*clair, 1); e[0].position = 0.15; e[1].position = 0.85
    mx = N.new("ShaderNodeMix"); mx.data_type = "FLOAT"; mx.inputs[0].default_value = 0.3
    L.new(wv.outputs["Fac"], mx.inputs[2]); L.new(nz.outputs["Fac"], mx.inputs[3])
    L.new(mx.outputs[0], cr.inputs["Fac"]); L.new(cr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough; b.inputs["Coat Weight"].default_value = 0.4
    return m
