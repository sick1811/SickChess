# outils/generer_sons.py - fabrique les bruitages de SickChess.
#
# 17/10 (remarque de Julien : "les sons ne sont pas super") : les coups, prises
# et roques utilisent maintenant de VRAIS chocs de bois enregistres, tires du
# pack "Impact Sounds" de Kenney (licence CC0 : libre, meme pour un jeu vendu ;
# copie dans assets_src/sons_kenney/ avec sa licence). Les carillons (echec,
# mat, debut et fin de partie, problemes) restent synthetises ci-dessous.
#
# Tous les sons du jeu sont SYNTHETISES ici, a partir de rien (bruit filtre et
# sinusoides amorties). Ils appartiennent donc au projet : aucune licence a
# verifier. Pour les modifier, change les reglages ci-dessous et relance :
#     python outils/generer_sons.py
# (necessite numpy : pip install numpy)

import os
import wave

import numpy as np

FREQ = 44100
DOSSIER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sounds")
rng = np.random.default_rng(1811)


def t(duree):
    return np.arange(int(FREQ * duree)) / FREQ


def clic_bois(hauteur=1.0, force=1.0, duree=0.12):
    """Une piece posee sur un plateau de bois."""
    x = t(duree)
    bruit = rng.standard_normal(len(x))
    # bruit filtre passe-bas (moyenne glissante) pour un "toc" mat
    noyau = np.ones(6) / 6
    bruit = np.convolve(bruit, noyau, mode="same") * np.exp(-x * 90)
    corps = (np.sin(2 * np.pi * 820 * hauteur * x) * 0.6
             + np.sin(2 * np.pi * 1340 * hauteur * x) * 0.3
             + np.sin(2 * np.pi * 210 * hauteur * x) * 0.5) * np.exp(-x * 45)
    return (bruit * 0.55 + corps) * force


def note(freq, duree, amorti=6.0, attaque=0.004):
    x = t(duree)
    env = np.minimum(1.0, x / attaque) * np.exp(-x * amorti)
    son = (np.sin(2 * np.pi * freq * x) + 0.35 * np.sin(2 * np.pi * freq * 2 * x)
           + 0.12 * np.sin(2 * np.pi * freq * 3 * x))
    return son * env


KENNEY = os.path.join(os.path.dirname(DOSSIER), "assets_src", "sons_kenney")


def kenney(nom, garder=None):
    """Un enregistrement du pack Kenney, en mono -1..1 (None s'il manque)."""
    chemin = os.path.join(KENNEY, nom + ".ogg")
    if not os.path.exists(chemin):
        return None
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame
    if not pygame.mixer.get_init():
        pygame.mixer.init(FREQ, -16, 2, 1024)
    a = pygame.sndarray.array(pygame.mixer.Sound(chemin)).astype(np.float64)
    a = a.mean(axis=1) if a.ndim == 2 else a
    a /= (np.max(np.abs(a)) or 1.0)
    if garder:
        a = a[:int(FREQ * garder)]
    return a


def bois(nom, defaut, garder=None):
    """Le choc enregistre s'il est la, sinon le son synthetise."""
    a = kenney(nom, garder)
    return a if a is not None else defaut


def silence(duree):
    return np.zeros(int(FREQ * duree))


def suite(*morceaux):
    return np.concatenate(morceaux)


def superposer(*morceaux):
    n = max(len(m) for m in morceaux)
    total = np.zeros(n)
    for m in morceaux:
        total[:len(m)] += m
    return total


def ecrire(nom, signal, volume=0.8):
    signal = signal / (np.max(np.abs(signal)) or 1) * volume
    fondu = min(len(signal), int(FREQ * 0.01))
    signal[-fondu:] *= np.linspace(1, 0, fondu)
    donnees = (signal * 32767).astype("<i2")
    stereo = np.repeat(donnees[:, None], 2, axis=1).tobytes()
    with wave.open(os.path.join(DOSSIER, nom + ".wav"), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(FREQ)
        f.writeframes(stereo)


def main():
    os.makedirs(DOSSIER, exist_ok=True)
    # Coups : un choc de bois leger, une prise different par piece pour varier.
    ecrire("move", bois("impactWood_light_000", clic_bois(1.0)), 0.62)
    ecrire("knight_move", bois("impactWood_light_001", clic_bois(0.93)), 0.62)
    ecrire("bishop_move", bois("impactWood_light_002", clic_bois(1.04)), 0.62)
    ecrire("rook_move", bois("impactWood_light_003", clic_bois(0.88, duree=0.14)), 0.62)
    ecrire("queen_move", bois("impactWood_light_004", clic_bois(1.08)), 0.62)
    ecrire("king_move", bois("impactWood_medium_000", clic_bois(0.84, duree=0.15)), 0.62)
    # Prise : plus lourde, avec la piece prise qui claque juste apres.
    lourd = bois("impactWood_heavy_000", clic_bois(0.78, 1.0, 0.16))
    leger = bois("impactWood_light_002", clic_bois(1.12, 0.8))
    ecrire("capture", superposer(lourd, suite(silence(0.04), leger * 0.45)), 0.80)
    ecrire("en_passant", superposer(bois("impactWood_heavy_001", clic_bois(0.8, 1.0, 0.16)),
                                    suite(silence(0.05), leger * 0.4)), 0.80)
    # Roque : le roi puis la tour.
    ecrire("castling", superposer(bois("impactWood_medium_001", clic_bois(0.9)),
                                  suite(silence(0.11),
                                        bois("impactWood_light_003", clic_bois(0.95)) * 0.85)),
           0.72)
    ecrire("check", superposer(bois("impactWood_medium_002", clic_bois(1.0)),
                               suite(silence(0.03), note(988, 0.35, 9) * 0.35)), 0.80)
    ecrire("promotion", superposer(bois("impactWood_medium_003", clic_bois(1.0)) * 0.7,
                                   suite(silence(0.05), note(660, 0.09, 14), note(880, 0.09, 14),
                                         note(1320, 0.3, 7))), 0.7)
    ecrire("illegal", bois("impactSoft_medium_000",
                           note(150, 0.18, 14) + 0.4 * note(155, 0.18, 14)), 0.5)
    ecrire("low_time", suite(note(1760, 0.07, 30), silence(0.07),
                             note(1760, 0.07, 30)), 0.55)
    ecrire("game_start", suite(note(523, 0.14, 10), note(784, 0.4, 5)), 0.6)
    ecrire("game_end", superposer(note(523, 0.9, 3.5), note(659, 0.9, 3.5),
                                  note(784, 0.9, 3.5)), 0.6)
    ecrire("checkmate", suite(superposer(note(784, 0.25, 7), note(988, 0.25, 7)),
                              superposer(note(523, 1.0, 3), note(659, 1.0, 3),
                                         note(392, 1.0, 3))), 0.7)
    for nom in ("stalemate", "repetition", "fifty_moves"):
        ecrire(nom, suite(note(659, 0.2, 8), note(587, 0.6, 4)), 0.55)
    # Problemes : trouve (deux notes qui montent) / pas le bon coup (une note
    # grave qui descend, douce : on se trompe souvent, ca ne doit pas agacer).
    ecrire("puzzle_reussi", suite(note(784, 0.09, 16),
                                  superposer(note(1175, 0.32, 8),
                                             note(1568, 0.32, 9) * 0.4)), 0.55)
    ecrire("puzzle_faux", suite(note(330, 0.1, 14), note(262, 0.22, 10)), 0.5)
    print("Sons ecrits dans", DOSSIER)


if __name__ == "__main__":
    main()
