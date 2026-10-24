# effets.py - SickChess 17/10 (travail p13, « finitions visuelles ») :
# les petits effets qui rendent le jeu satisfaisant, sans gener la lecture.
#   - une onde breve sur la case d'une prise ;
#   - au mat : un halo rouge qui bat autour du roi mate, et des confettis
#     dores quand c'est TOI qui gagnes (ou a deux sur ce PC) ;
#   - fondu() : un fondu d'arrivee de 0,25 s quand un ecran apparait.
# Tout est dessine par-dessus l'echiquier ; rien ne change le jeu.

import math
import random

import pygame

import board_geometry as geo

DUREE_ONDE = 0.32
DUREE_MAT = 2.4
DUREE_FONDU = 0.25
OR = (232, 196, 110)


def _maintenant():
    return pygame.time.get_ticks() / 1000.0


class Effets:
    def __init__(self):
        self.liste = []

    def prise(self, case):
        self.liste.append({"type": "onde", "case": case, "debut": _maintenant()})

    def mat(self, case_du_roi, confettis=True, hasard=None):
        h = hasard or random.Random()
        effet = {"type": "mat", "case": case_du_roi, "debut": _maintenant(), "particules": []}
        if confettis:
            # 24/10 (p31) : moins de confettis sur un petit PC.
            try:
                import petit_pc
                nombre = petit_pc.CONFETTIS_PETIT if petit_pc.est_petit() else 90
            except Exception:
                nombre = 90
            for _ in range(nombre):
                effet["particules"].append({
                    "x": h.random(), "y": -h.random() * 0.3,
                    "vx": (h.random() - 0.5) * 0.25, "vy": 0.35 + h.random() * 0.45,
                    "taille": 7 + h.random() * 6, "teinte": h.choice(
                        [OR, (240, 240, 235), (120, 200, 130), (110, 160, 240)]),
                    "rot": h.random() * 6.28})
        self.liste.append(effet)

    def actifs(self):
        maintenant = _maintenant()
        self.liste = [e for e in self.liste if maintenant - e["debut"] <
                      (DUREE_ONDE if e["type"] == "onde" else DUREE_MAT)]
        return self.liste

    def vider(self):
        self.liste = []

    def draw(self, surface, sq_size, flipped, rect_plateau):
        if not self.liste:
            return
        maintenant = _maintenant()
        for e in self.actifs():
            age = maintenant - e["debut"]
            if e["type"] == "onde":
                x, y, taille, _ = geo.rectangle_case(e["case"], sq_size, flipped)
                part = age / DUREE_ONDE
                rayon = int(taille * (0.25 + 0.55 * part))
                alpha = int(170 * (1 - part))
                calque = pygame.Surface((taille * 2, taille * 2), pygame.SRCALPHA)
                pygame.draw.circle(calque, (255, 255, 255, alpha), (taille, taille), rayon,
                                   max(2, taille // 14))
                surface.blit(calque, (x + taille // 2 - taille, y + taille // 2 - taille))
            elif e["type"] == "mat":
                if e["case"] is not None:
                    x, y, taille, _ = geo.rectangle_case(e["case"], sq_size, flipped)
                    battement = 0.5 + 0.5 * math.sin(age * 9)
                    alpha = int((90 + 90 * battement) * max(0.0, 1 - age / DUREE_MAT))
                    calque = pygame.Surface((taille, taille), pygame.SRCALPHA)
                    pygame.draw.rect(calque, (230, 70, 60, alpha), calque.get_rect(),
                                     border_radius=taille // 6)
                    surface.blit(calque, (x, y))
                if e["particules"]:
                    zone = pygame.Rect(rect_plateau)
                    ancien = surface.get_clip()
                    surface.set_clip(zone)
                    fondu = max(0.0, 1 - max(0.0, age - DUREE_MAT * 0.6) / (DUREE_MAT * 0.4))
                    for p in e["particules"]:
                        px = zone.x + (p["x"] + p["vx"] * age) * zone.width
                        py = zone.y + (p["y"] + p["vy"] * age) * zone.height
                        t = p["taille"] * (zone.width / 640.0)
                        largeur = max(1, int(abs(math.cos(p["rot"] + age * 7)) * t * 1.6))
                        r = pygame.Rect(0, 0, largeur, max(1, int(t)))
                        r.center = (int(px), int(py))
                        couleur = tuple(int(c * fondu + 20 * (1 - fondu)) for c in p["teinte"])
                        pygame.draw.rect(surface, couleur, r)
                    surface.set_clip(ancien)


_FONDUS = {}
# Sans ecran (tests, captures pour Steam) : pas de fondu, sinon les images
# seraient noires.
import os as _os
FONDU_ACTIF = _os.environ.get("SDL_VIDEODRIVER") != "dummy"


def fondu(surface, cle, couleur=(12, 12, 12)):
    """A appeler a la fin du dessin d'un ecran : s'il vient d'apparaitre (pas
    dessine depuis 0,3 s), un voile qui s'efface en 0,25 s."""
    if not FONDU_ACTIF:
        return
    maintenant = _maintenant()
    etat = _FONDUS.get(cle)
    if etat is None or maintenant - etat["dernier"] > 0.3:
        etat = {"debut": maintenant}
        _FONDUS[cle] = etat
    etat["dernier"] = maintenant
    age = maintenant - etat["debut"]
    if age < DUREE_FONDU:
        voile = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        voile.fill(couleur + (int(255 * (1 - age / DUREE_FONDU)),))
        surface.blit(voile, (0, 0))
