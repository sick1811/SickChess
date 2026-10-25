# tests/test_temps_revue.py - le temps restant annonce pendant l'analyse de la revue (25/10).
#     python tests/test_temps_revue.py      (sans Stockfish : moteur factice, temps simule)
# Retours t71 / t99 (Cowork, PC de Julien) : « temps annonce faux », une revue de
# 17 coups a pris environ 7 min. Ici, une horloge simulee : chaque recherche du
# moteur factice « dure » un temps choisi (sans attendre pour de vrai), trois
# moteurs travaillent en meme temps comme sur le PC de Julien, et on compare
# l'annonce au temps qu'il restait vraiment.

import os
import random
import sys
import threading
import time as vrai_temps
import zlib

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import analyse_partie as A

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


class Horloge:
    """Temps simule. Chaque fil qui « attend » note quand il se reveille ;
    le chef d'orchestre (la boucle du test) avance l'horloge jusqu'au prochain
    reveil quand TOUS les fils attendent."""
    def __init__(self):
        self.t = 0.0
        self.cond = threading.Condition()
        self.reveils = []

    def time(self):
        return self.t

    def sleep(self, duree):
        with self.cond:
            fin = self.t + max(1e-6, duree)
            self.reveils.append(fin)
            while self.t < fin:
                self.cond.wait()
            self.reveils.remove(fin)


class MoteurSimule:
    """Moteur factice : la duree de chaque recherche vient de 'duree(k, niveau)'.
    Il rend aussi ce que rend le vrai (noeuds calcules, temps de Stockfish)."""
    def __init__(self, horloge, positions, evaluations, duree, compte=1.0):
        self.horloge = horloge
        self.positions = positions           # fen -> indice
        self.evaluations = evaluations       # indice -> pions (Blancs)
        self.duree = duree
        self.compte = compte                 # part du vrai temps comptee par Stockfish

    def analyser_position(self, fen, profondeur, temps, lignes=1, noeuds=0):
        k = self.positions[fen]
        niveau = 1 if not noeuds else (2 if lignes > 1 else 3)
        d = self.duree(k, niveau)
        self.horloge.sleep(d)
        plateau = chess.Board(fen)
        signe = 1.0 if plateau.turn == chess.WHITE else -1.0
        ev = signe * self.evaluations[k]
        coups = [c.uci() for c in list(plateau.legal_moves)[:3]]
        lignes_moteur = [{"coup": u, "cp": int(round(ev * 100)) - 40 * n, "mat": None,
                          "profondeur": 24, "suite": []}
                         for n, u in enumerate(coups[:max(1, lignes)])]
        return {"coup": coups[0], "evaluation": ev, "mat": None, "profondeur": 24,
                "lignes": lignes_moteur,
                "second_evaluation": ev - 0.4 if lignes > 1 else None,
                "second_mat": None,
                "noeuds": noeuds or 200000, "temps_ms": int(d * 1000 * self.compte)}


def partie_au_hasard(graine, demi_coups=34):
    """Une partie de 17 coups hors du livre d'ouvertures."""
    hasard = random.Random(graine)
    plateau = chess.Board()
    coups = []
    while len(coups) < demi_coups:
        legaux = list(plateau.legal_moves)
        coup = hasard.choice(legaux)
        plateau.push(coup)
        if plateau.is_game_over():
            plateau.pop()
            continue
        coups.append(coup.uci())
    return coups


def simuler(nom, duree, graine=3, ouvriers=3, puissance="calcul_forte", compte=1.0):
    """Lance la revue en temps simule ; rend [(t, annonce)] et la duree totale."""
    coups = partie_au_hasard(graine)
    horloge = Horloge()
    ancien = A.time
    A.time = horloge
    try:
        an = A.AnalyseurPartie(None, coups, None, puissance, moteur=True)
        hasard = random.Random(graine * 31 + 1)
        evaluations, ev = {}, 0.2
        for k in range(len(an.fens)):
            evaluations[k] = ev
            ev += hasard.choice([-0.9, -0.5, -0.2, 0.0, 0.1, 0.3, 0.6, 1.0])
        positions = dict((f, k) for k, f in enumerate(an.fens))
        an._moteur_fourni = MoteurSimule(horloge, positions, evaluations, duree,
                                          compte)
        an._stop, an.en_cours = False, True
        an._lancer_ouvriers(ouvriers)
        releves = []
        dernier = -1.0
        while any(f.is_alive() for f in an._fils):
            with horloge.cond:
                vivants = sum(1 for f in an._fils if f.is_alive())
                prets = len(horloge.reveils) == vivants and vivants \
                    and all(r > horloge.t for r in horloge.reveils)
                if prets:
                    if horloge.t - dernier >= 1.0:
                        an._memo_reste = None
                        releves.append((horloge.t, an.temps_restant()))
                        dernier = horloge.t
                    horloge.t = min(horloge.reveils)
                    horloge.cond.notify_all()
            if not prets:
                vrai_temps.sleep(0.0005)
        fin = horloge.t
        verifies = sum(1 for k in range(len(an.fens))
                       if k not in an.allegees and not an.finie[k])
        print("  (%s : %d s simulees, %d positions verifiees sur %d)"
              % (nom, fin, verifies, len(an.fens)))
        return releves, fin, an
    finally:
        A.time = ancien


def juger(nom, releves, fin):
    """L'annonce doit rester a moins de 25 % du temps qui reste vraiment des
    que 20 % du temps est passe (la passe des trois meilleurs coups a alors vu
    presque toutes les positions ; avant, seules les premieres sont mesurees :
    personne ne peut deviner la duree des suivantes) ; sous 30 s, elle doit
    dire « moins d'une minute ». Elle doit apparaitre dans les 15 premieres s."""
    pires, absents = [], 0
    for t, annonce in releves:
        vrai = fin - t
        if annonce is None:
            if t > 15:
                absents += 1
            continue
        if t < 0.20 * fin:
            continue
        if vrai >= 30:
            ecart = abs(annonce - vrai) / vrai
            if ecart > 0.25:
                pires.append((ecart, t, vrai, annonce))
        elif annonce >= 60:
            pires.append((annonce / max(1.0, vrai), t, vrai, annonce))
    pires.sort(reverse=True)
    detail = ""
    if pires:
        e, t, vrai, annonce = pires[0]
        detail = " ; pire a %d s : annonce %d s, reste vraiment %d s" % (t, annonce, vrai)
    verifier(not pires and not absents,
             "%s : annonce juste a 25 %% pres (%d releves faux sur %d, %d sans annonce%s)"
             % (nom, len(pires), len(releves), absents, detail))


def de_base(k, niveau):
    """Recherche de 3 millions de noeuds en ~2,5 s, 25 millions en ~20 s ;
    chaque position a sa vitesse (finales plus rapides...)."""
    vitesse = 1.0 + (zlib.crc32(b"v%d" % k) % 100) / 200.0      # 1 a 1,5 fois
    if niveau == 1:
        return 0.15 + (zlib.crc32(b"s%d" % k) % 100) / 1000.0
    return (2.5 if niveau == 2 else 20.0) / vitesse


print("1. Des coups aux durees proches")
juger("durees proches", *simuler("durees proches", de_base)[:2])

print("2. Les premiers coups lents (milieu de partie complique), la fin rapide")
juger("debut lent", *simuler(
    "debut lent", lambda k, n: de_base(k, n) * (2.0 if k < 8 else 0.8))[:2])

print("3. Les premiers coups rapides, la suite lente")
juger("debut rapide", *simuler(
    "debut rapide", lambda k, n: de_base(k, n) * (0.5 if k < 8 else 1.3))[:2])


def tres_differentes(k, niveau):
    facteur = (0.3, 3.0, 1.0, 0.5, 2.0, 0.8)[zlib.crc32(b"f%d" % k) % 6]
    return de_base(k, niveau) * facteur


print("4. Des coups aux durees tres differentes")
juger("durees tres differentes", *simuler("durees tres differentes", tres_differentes)[:2])

print("5. Une autre partie, deux moteurs (PC a 6 coeurs)")
juger("deux moteurs", *simuler("deux moteurs", tres_differentes, graine=11,
                                ouvriers=2)[:2])

print("6. Un seul moteur (petit PC)")
juger("un moteur", *simuler("un moteur", de_base, graine=5, ouvriers=1)[:2])

print("7. Stockfish compte moins de temps que la vraie recherche (attente du moteur,")
print("   Windows qui partage le processeur entre les trois moteurs et le jeu)")
juger("temps de Stockfish trop court", *simuler("temps de Stockfish trop court", de_base,
                                                 compte=0.6)[:2])

print("8. Le texte affiche")
an = A.AnalyseurPartie(None, ["e2e4"], None, moteur=True)
verifier(an.texte_temps_restant() == "", "rien tant que l'analyse ne tourne pas")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
