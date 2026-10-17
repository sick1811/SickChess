"""5 propositions de logo + icone SickChess autour du cavalier du jeu Tournoi."""
import json
BASE = "M50.00,91.00 L76.44,91.00 L76.44,88.13 L75.65,87.17 L72.74,86.22 L72.21,84.30 L73.80,83.03 L72.74,81.43 L69.04,80.16 L68.89,77.60 L68.13,75.05 L31.87,75.05 L31.11,77.60 L30.96,80.16 L27.26,81.43 L26.20,83.03 L27.79,84.30 L27.26,86.22 L24.35,87.17 L23.56,88.13 L23.56,91.00 Z"
TETE = "M65.11,75.69 L67.38,56.55 L65.87,42.52 L61.33,31.03 L56.04,23.38 L53.78,17.00 L50.76,22.10 L45.47,24.66 L34.89,33.59 L26.58,42.52 L25.07,47.62 L28.09,51.45 L37.16,50.17 L44.71,48.90 L47.73,54.00 L40.93,64.21 L37.16,75.69 Z"
OEIL = (46.22, 35.5)
OR, OR2, ONYX, IVOIRE = "#d6b04a", "#a9842c", "#0e0e10", "#f3f0e8"

def cavalier(fill, oeil, tx=0, ty=0, s=1.0, base=True, stroke=None, sw=0):
    st = f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke else ""
    b = f'<path d="{BASE}"/>' if base else ""
    return (f'<g transform="translate({tx},{ty}) scale({s})"><g fill="{fill}"{st}>{b}<path d="{TETE}"/></g>'
            f'<circle cx="{OEIL[0]}" cy="{OEIL[1]}" r="2.8" fill="{oeil}"/></g>')

FONT = "font-family:'Barlow SC',sans-serif"
def mot(x, y, taille, c1, c2, poids=700, esp=0, ancre="start"):
    return (f'<text x="{x}" y="{y}" text-anchor="{ancre}" style="{FONT};font-weight:{poids};font-size:{taille}px;letter-spacing:{esp}px">'
            f'<tspan fill="{c1}">SICK</tspan><tspan fill="{c2}">CHESS</tspan></text>')

V = {}
# 1. Ecusson : cavalier or sur onyx, carre arrondi, filet or
V["ecusson"] = dict(
 nom="1. Écusson", desc="Cavalier doré sur un carré d'onyx, fin filet or. Classique et premium.",
 icone=f'<rect x="4" y="4" width="92" height="92" rx="20" fill="{ONYX}"/><rect x="8" y="8" width="84" height="84" rx="16" fill="none" stroke="{OR}" stroke-width="1.6"/>'
       + cavalier(OR, ONYX, 10, 6.8, 0.80),
 logo=lambda: f'<rect x="0" y="0" width="100" height="100" rx="22" fill="{ONYX}"/><rect x="5" y="5" width="90" height="90" rx="18" fill="none" stroke="{OR}" stroke-width="1.8"/>'
       + cavalier(OR, ONYX, 10, 6.8, 0.80) + mot(124, 74, 64, IVOIRE, OR))
# 2. Bouclier noir/or : cavalier blanc sur or plein, tres lisible petit
V["or"] = dict(
 nom="2. Or plein", desc="Cavalier noir sur fond or. L'icône la plus visible dans une barre des tâches.",
 icone=f'<rect x="4" y="4" width="92" height="92" rx="20" fill="{OR}"/>' + cavalier(ONYX, OR, 7, 3.6, 0.86),
 logo=lambda: f'<rect x="0" y="0" width="100" height="100" rx="22" fill="{OR}"/>' + cavalier(ONYX, OR, 7, 3.6, 0.86)
       + mot(124, 74, 64, IVOIRE, OR))
# 3. Damier : cavalier coupe en deux couleurs sur 2x2 cases
clip = '<clipPath id="g3"><rect x="0" y="0" width="50" height="100"/></clipPath><clipPath id="d3"><rect x="50" y="0" width="50" height="100"/></clipPath>'
def damier(r=20):
    return (f'<clipPath id="arr3"><rect x="4" y="4" width="92" height="92" rx="{r}"/></clipPath>'
            f'<g clip-path="url(#arr3)"><rect x="4" y="4" width="46" height="46" fill="{IVOIRE}"/><rect x="50" y="4" width="46" height="46" fill="{ONYX}"/>'
            f'<rect x="4" y="50" width="46" height="46" fill="{ONYX}"/><rect x="50" y="50" width="46" height="46" fill="{IVOIRE}"/></g>')
def cav_split():
    # le cavalier prend la couleur opposee a la case sous lui : moitie gauche/droite
    return (f'<defs>{clip}</defs><g clip-path="url(#g3)">{cavalier(OR, ONYX, 7, 3.6, 0.86)}</g>'
            f'<g clip-path="url(#d3)">{cavalier(OR, ONYX, 7, 3.6, 0.86)}</g>')
V["damier"] = dict(
 nom="3. Damier", desc="Quatre cases d'échiquier, cavalier doré par-dessus. Dit « échecs » au premier regard.",
 icone=damier() + f'<g>{cavalier(OR, ONYX, 7, 3.6, 0.86, stroke=ONYX, sw=3)}</g>',
 logo=lambda: damier() + cavalier(OR, ONYX, 7, 3.6, 0.86, stroke=ONYX, sw=3) + mot(124, 74, 64, IVOIRE, OR))
# 4. Anneau : cavalier ivoire dans un cercle or, sans fond
V["anneau"] = dict(
 nom="4. Anneau", desc="Cavalier ivoire dans un cercle doré. Style médaille, sobre, compétitif.",
 icone=f'<circle cx="50" cy="50" r="46" fill="{ONYX}"/><circle cx="50" cy="50" r="41" fill="none" stroke="{OR}" stroke-width="3.2"/>'
       + cavalier(IVOIRE, ONYX, 14, 11, 0.72),
 logo=lambda: f'<circle cx="50" cy="50" r="48" fill="{ONYX}"/><circle cx="50" cy="50" r="43" fill="none" stroke="{OR}" stroke-width="3.4"/>'
       + cavalier(IVOIRE, ONYX, 14, 11, 0.72) + mot(124, 74, 64, IVOIRE, OR, esp=4))
# 5. Monogramme : cavalier + S stylise / SC, wordmark empile
V["eclat"] = dict(
 nom="5. Éclat", desc="Cavalier seul, sans cadre, coupé par une diagonale or. Moderne, style e-sport.",
 icone=f'<rect x="4" y="4" width="92" height="92" rx="20" fill="{ONYX}"/>'
       + f'<clipPath id="c5"><polygon points="0,100 100,8 100,100"/></clipPath><clipPath id="h5"><polygon points="0,0 100,0 100,8 0,100"/></clipPath>'
       + f'<g clip-path="url(#h5)">{cavalier(IVOIRE, ONYX, 7, 3.6, 0.86)}</g><g clip-path="url(#c5)">{cavalier(OR, ONYX, 7, 3.6, 0.86)}</g>',
 logo=lambda: f'<rect x="0" y="0" width="100" height="100" rx="22" fill="{ONYX}"/>'
       + f'<g clip-path="url(#h5)">{cavalier(IVOIRE, ONYX, 7, 3.6, 0.86)}</g><g clip-path="url(#c5)">{cavalier(OR, ONYX, 7, 3.6, 0.86)}</g>'
       + mot(124, 52, 48, IVOIRE, OR) + f'<text x="126" y="84" style="{FONT};font-weight:500;font-size:15px;letter-spacing:6px" fill="#8f8a80">ENTRAÎNE · ANALYSE · GAGNE</text>'
       + '<defs><clipPath id="c5"><polygon points="0,100 100,8 100,100"/></clipPath><clipPath id="h5"><polygon points="0,0 100,0 100,8 0,100"/></clipPath></defs>')

def svg_icone(k, taille=512):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{taille}" height="{taille}" viewBox="0 0 100 100">{V[k]["icone"]}</svg>'
def svg_logo(k, h=200):
    return f'<svg xmlns="http://www.w3.org/2000/svg" height="{h}" width="{h*4.6}" viewBox="0 0 460 100">{V[k]["logo"]()}</svg>'

json.dump({k: {"nom": v["nom"], "desc": v["desc"], "icone": svg_icone(k), "logo": svg_logo(k)} for k, v in V.items()},
          open("logos.json", "w"))
print(list(V))
