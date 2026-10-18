"""Pieces 2D (SVG) tirees des MEMES profils que les modeles 3D.
Ainsi la version plate et la version relief ont exactement la meme silhouette.
usage : python3 gen_2d.py <dossier_sortie>  -> <famille>_<w|b><piece>.svg + pieces2d.json"""
import json, os, sys, math, types

# on lit les profils sans importer bpy
src = open(os.path.join(os.path.dirname(__file__), "sick3d.py")).read()
deb = src.index("# ------------------------------------------------------------------ profils")
fin = src.index("def _extrude")
ns = {"math": math}
exec(src[deb:fin], ns)
PROFILS, CAV, CAV_A = ns["PROFILS"], ns["CAVALIER"], ns["CAVALIER_ARENE"]

BASE_Y = 91
XOFF = 0.0
CIBLE = {"p": 58, "r": 66, "n": 74, "b": 76, "q": 82, "k": 88}   # hauteur a l'ecran, sur 100
LARGE = 1.32                         # un peu plus large qu'en 3D : lisibilite en 2D
SX = SY = 52                         # recalcules pour chaque piece
COUL = {
    "w": {"fill": "#f6f3ec", "stroke": "#17181a", "detail": "#17181a"},
    "b": {"fill": "#26282d", "stroke": "#0b0b0c", "detail": "#8c919b"},
}

def P(x, z):
    return (50 + (x + XOFF) * SX, BASE_Y - z * SY)

def poly(pts):
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + " Z"

def tour(prof):
    droite = [P(r, z) for r, z in prof]
    gauche = [P(-r, z) for r, z in reversed(prof)]
    return poly(droite + gauche)

def rect(x, z, w, h):
    x0, y0 = P(x, z + h)
    return f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{w*SX:.2f}" height="{h*SY:.2f}"/>'

def hauteur(fam, kind):
    prof = PROFILS[fam][kind](); top = prof[-1][1]
    if kind == "q": return 1.38 if fam == "tournoi" else 1.325
    if kind == "k": return top + 0.29
    if kind == "n":
        sil = CAV if fam == "tournoi" else CAV_A
        return top - 0.01 + max(z for _, z in sil)
    return top

def svg(fam, kind, col):
    global SX, SY, XOFF
    SY = CIBLE[kind] / hauteur(fam, kind)
    sy_roi = CIBLE["k"] / hauteur(fam, "k")
    # la largeur suit a peine l'agrandissement : sinon la tour devient enorme
    SX = sy_roi * LARGE * (SY / sy_roi) ** 0.35
    XOFF = 0.0
    if kind == "n":   # centrer la silhouette asymetrique du cavalier
        sil = CAV if fam == "tournoi" else CAV_A
        base_r = PROFILS[fam]["n"]()[1][0]
        xs = [x for x, _ in sil] + [-base_r, base_r]
        XOFF = -(min(xs) + max(xs)) / 2
    c = COUL[col]; sw = 2.4
    prof = PROFILS[fam][kind]()
    top = prof[-1][1]
    corps, extra, details = [tour(prof)], [], []
    if kind == "r":   # creneaux : 2 encoches vues de face
        for x in (-0.115, 0.07):
            details.append(("notch", rect(x, top - 0.075, 0.045, 0.09)))
    if kind == "b":   # fente
        x1, y1 = P(-0.02, 0.86 if fam == "tournoi" else 0.88)
        x2, y2 = P(0.12, 1.02 if fam == "tournoi" else 1.03)
        details.append(("line", f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>'))
    if kind == "q":
        if fam == "tournoi":
            for i in range(5):
                x = -0.2 + i * 0.1
                cx, cy = P(x, 1.19 + (0.02 if i in (1, 3) else 0))
                extra.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{0.04*SX:.2f}"/>')
            cx, cy = P(0, 1.31); extra.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{0.07*SX:.2f}"/>')
        else:
            for x in (-0.16, -0.04, 0.08):
                details.append(("notch", rect(x, 1.13, 0.08, 0.08)))
            cx, cy = P(0, 1.26); extra.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{0.065*SX:.2f}"/>')
    if kind == "k":
        w = 0.075 if fam == "tournoi" else 0.085
        extra.append(rect(-w / 2, top - 0.01, w, 0.30 if fam == "tournoi" else 0.28))
        extra.append(rect(-0.115, top + 0.12, 0.23, w))
    if kind == "n":
        sil = CAV if fam == "tournoi" else CAV_A
        corps.append(poly([P(x, z + top - 0.01) for x, z in sil]))
        ex, ey = P(-0.05, top + 0.62 if fam == "tournoi" else top + 0.60)
        details.append(("eye", f'<circle cx="{ex:.2f}" cy="{ey:.2f}" r="2.6"/>'))
    body = "".join(f'<path d="{d}"/>' for d in corps) + "".join(extra)
    det = ""
    for typ, el in details:
        if typ == "notch":
            det += el.replace("<rect", f'<rect fill="{c["detail"] if col=="b" else c["stroke"]}" stroke="none"')
        elif typ == "line":
            det += el.replace("<line", f'<line stroke="{c["detail"]}" stroke-width="2.6" stroke-linecap="round"')
        else:
            det += el.replace("<circle", f'<circle fill="{c["detail"]}"')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            f'<g fill="{c["fill"]}" stroke="{c["stroke"]}" stroke-width="{sw}" stroke-linejoin="round">{body}</g>'
            f'{det}</svg>')

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    data = {}
    for fam in ("tournoi", "arene"):
        for col in "wb":
            for k in "kqrbnp":
                s = svg(fam, k, col)
                data[f"{fam}_{col}{k}"] = s
                open(os.path.join(out, f"{fam}_{col}{k}.svg"), "w").write(s)
    json.dump(data, open(os.path.join(out, "pieces2d.json"), "w"))
    print(len(data), "pieces")
