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


def marimba(freq, duree=0.9):
    """Une lame de marimba : chaude et ronde (partiels 1 / 4 / 9.9, aigus brefs)."""
    x = t(duree)
    attaque = np.minimum(1.0, x / 0.003)
    son = (np.sin(2 * np.pi * freq * x) * np.exp(-x * 5.5)
           + 0.30 * np.sin(2 * np.pi * freq * 3.98 * x) * np.exp(-x * 18)
           + 0.08 * np.sin(2 * np.pi * freq * 9.9 * x) * np.exp(-x * 40))
    return son * attaque


def reverb(signal, piece=0.28, longueur=0.6):
    """Une petite salle : quelques echos qui s'eteignent, sans effet de tunnel."""
    sortie = np.concatenate([signal, np.zeros(int(FREQ * longueur))])
    for retard, gain in ((0.031, 0.32), (0.047, 0.26), (0.071, 0.20),
                         (0.113, 0.14), (0.167, 0.09), (0.241, 0.05)):
        d = int(FREQ * retard)
        sortie[d:d + len(signal)] += signal * gain * piece / 0.28
    return sortie


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
    # 17/10 (Julien : "le son de victoire des problemes n'est pas ouf") :
    # un petit arpege de marimba (sol, si, re, sol) dans une salle, doux et net.
    arpege = superposer(marimba(784), suite(silence(0.07), marimba(988)),
                        suite(silence(0.14), marimba(1175)),
                        suite(silence(0.21), marimba(1568, 1.1) * 0.9))
    ecrire("puzzle_reussi", reverb(arpege), 0.55)
    # Pas le bon coup : deux notes graves de marimba qui descendent, sans buzzer.
    ecrire("puzzle_faux", reverb(superposer(marimba(392, 0.6),
                                            suite(silence(0.12), marimba(330, 0.7)))), 0.45)
    print("Sons ecrits dans", DOSSIER)


# ---------------------------------------------------------------------------
# 17/10 (travaux p15 et p14, demandes de Julien) : un 2e pack de sons
# « Feutre » (les memes sons, plus doux et plus sourds) et une musique
# d'ambiance douce, entierement synthetisee ici (aucun droit a payer).

def lire_wav(chemin):
    with wave.open(chemin, "rb") as f:
        n, canaux = f.getnframes(), f.getnchannels()
        a = np.frombuffer(f.readframes(n), dtype="<i2").astype(np.float64) / 32768
    return a.reshape(-1, canaux).mean(axis=1) if canaux > 1 else a


def passe_bas(signal, coupure=1800.0):
    """Filtre doux (FFT) : enleve le claquant des aigus."""
    spectre = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(len(signal), 1.0 / FREQ)
    spectre *= 1.0 / (1.0 + (freqs / coupure) ** 4)
    return np.fft.irfft(spectre, len(signal))


def generer_feutre():
    """sounds/feutre/ : chaque son du pack « Bois », adouci."""
    dossier = os.path.join(DOSSIER, "feutre")
    os.makedirs(dossier, exist_ok=True)
    for nom in sorted(os.listdir(DOSSIER)):
        if not nom.endswith(".wav"):
            continue
        s = lire_wav(os.path.join(DOSSIER, nom))
        s = reverb(passe_bas(s, 1500.0 if "move" in nom or nom in ("capture.wav", "castling.wav",
                                                                       "en_passant.wav") else 2600.0),
                   piece=0.18, longueur=0.25)
        crete = np.max(np.abs(s)) or 1.0
        s = s / crete * 0.5
        fondu = min(len(s), int(FREQ * 0.01))
        s[-fondu:] *= np.linspace(1, 0, fondu)
        donnees = (s * 32767).astype("<i2")
        with wave.open(os.path.join(dossier, nom), "wb") as f:
            f.setnchannels(2)
            f.setsampwidth(2)
            f.setframerate(FREQ)
            f.writeframes(np.repeat(donnees[:, None], 2, axis=1).tobytes())
    print("Pack Feutre ecrit dans", dossier)


def generer_musique(duree_mesure=4.0, frequence=22050):
    """music/calme.wav : 4 accords tenus (la-, fa, do, sol) et un arpege de
    marimba tres doux, 2 tours = 32 s qui bouclent sans couture. Mono 22 kHz
    pour rester leger."""
    global FREQ
    ancien, FREQ = FREQ, frequence
    try:
        accords = [(220.0, 261.63, 329.63, 392.0),      # la mineur 7
                   (174.61, 220.0, 261.63, 329.63),     # fa majeur 7
                   (130.81, 196.0, 261.63, 329.63),     # do majeur
                   (196.0, 246.94, 293.66, 392.0)]      # sol majeur
        n = int(FREQ * duree_mesure)
        x = t(duree_mesure)
        pistes = []
        for tour in range(2):
            for i, accord in enumerate(accords):
                env = np.minimum(1.0, x / 1.2) * np.minimum(1.0, (duree_mesure - x) / 1.2)
                nappe = sum(np.sin(2 * np.pi * f * x + k) * (0.9 - 0.15 * k)
                            for k, f in enumerate(accord)) * env * 0.16
                nappe += np.sin(2 * np.pi * accord[0] / 2 * x) * env * 0.10
                arpege = np.zeros(n)
                pas = duree_mesure / 8
                for j in range(8):
                    if (j + tour) % 3 == 2:
                        continue                     # quelques silences
                    f = accord[(j * 2 + i) % 4] * 2
                    m = marimba(f, min(1.2, duree_mesure - j * pas)) * 0.12
                    d = int(FREQ * j * pas)
                    arpege[d:d + len(m)] += m[:n - d]
                pistes.append(nappe + arpege)
        musique = np.concatenate(pistes)
        longueur = len(musique)
        avec_echo = reverb(musique, piece=0.3, longueur=0.5)
        musique = avec_echo[:longueur].copy()
        queue = avec_echo[longueur:]
        musique[:len(queue)] += queue          # la fin de l'echo retombe au debut : boucle sans couture
        musique = musique / (np.max(np.abs(musique)) or 1) * 0.6
        dossier = os.path.join(os.path.dirname(DOSSIER), "music")
        os.makedirs(dossier, exist_ok=True)
        with wave.open(os.path.join(dossier, "calme.wav"), "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(FREQ)
            f.writeframes((musique * 32767).astype("<i2").tobytes())
        print("Musique ecrite dans", dossier)
    finally:
        FREQ = ancien


if __name__ == "__main__":
    import sys
    if "--feutre" in sys.argv or "--tout" in sys.argv:
        if "--tout" in sys.argv:
            main()
        generer_feutre()
    if "--musique" in sys.argv or "--tout" in sys.argv:
        generer_musique()
    if len(sys.argv) == 1:
        main()
