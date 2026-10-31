"""5 essais de musique pour SickChess : chill, atmospherique, mais avec une tension competitive."""
import os
import subprocess
import sys
import wave

import numpy as np

from synth import *  # noqa

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sortie")
os.makedirs(OUT, exist_ok=True)


def pad_ducke(m, x, t0, duck, **kw):
    i = int(t0 * SR)
    g = duck[:, i:i + x.shape[1]]
    if g.shape[1] < x.shape[1]:
        g = np.pad(g, ((0, 0), (0, x.shape[1] - g.shape[1])), constant_values=1)
    m.add(x * g, t0, **kw)


# ------------------------------------------------------------------ 1
def horloge():
    bpm = 76
    B = 60 / bpm
    bar = 4 * B
    nb = 32
    m = Mix(nb * bar)
    chords = [[50, 57, 60, 64, 65], [46, 53, 57, 60, 62], [43, 50, 53, 57, 58], [45, 52, 62, 64, 67]]
    roots = [38, 34, 31, 33]
    for c in range(nb // 2):
        t0 = c * 2 * bar
        k = c % 4
        br = [0.0, 0.6, 0.2] if 4 <= c < 14 else [0.0, 0.2, 0.0]
        m.add(saw_pad(chords[k], 2 * bar + 0.4, a=2.5, r=3.5, cutoff=900, brillance=br), t0, gain=0.55, rev=0.6)
        if 4 <= c < 14:
            m.add(sub(roots[k], 2 * bar - 0.1, 1.0), t0, gain=0.55)
            m.add(sub(roots[k] + 12, 2 * bar - 0.1, 0.5), t0, gain=0.15)
    for b in range(nb):
        t0 = b * bar
        for q in range(4):
            m.add(tick(1.0, q % 2 == 0), t0 + q * B, pan=0.25 if q % 2 else -0.25, gain=0.09, rev=0.25)
        if 8 <= b < 28:  # battement de coeur
            m.add(kick(1.0, ton=46, dec=0.35, click=0.1), t0, gain=0.6, rev=0.1)
            m.add(kick(0.6, ton=44, dec=0.3, click=0.05), t0 + 0.38 * B, gain=0.45)
        if b in (7, 23):
            m.add(swell(bar, 400, 5000), t0, gain=0.10, rev=0.5)
    motifs = [
        [(0, 74, 1), (1.5, 72, .7), (2, 69, .8), (3, 67, .6), (4.5, 69, .7), (6, 65, .8)],
        [(0, 77, .9), (1, 76, .6), (2, 74, .8), (3.5, 72, .6), (5, 74, .7), (6.5, 69, .6)],
    ]
    for c in range(2, nb // 2):
        mot = motifs[c % 2]
        vel = 0.55 if c >= 14 else 1.0
        for (bt, n, v) in mot:
            inst = bell(n, v * vel, dec=1.8) if c % 4 >= 2 else epiano(n, 1.2, v * vel, 0.8)
            m.add(inst, c * 2 * bar + bt * B, pan=0.3 * np.sin(n), gain=0.28, rev=0.45, dly=0.35)
    return m.render(rev_decay=4.5, delay_t=0.75 * B, delay_fb=0.42, wet=0.4), "1_Horloge"


# ------------------------------------------------------------------ 2
def profondeur():
    bpm = 60
    B = 60 / bpm
    bar = 4 * B
    nb = 24
    m = Mix(nb * bar, queue=10)
    chords = [[45, 52, 59, 60, 64], [41, 48, 52, 57, 59], [48, 55, 59, 64], [40, 47, 50, 55],
              [45, 52, 59, 62, 64], [41, 48, 55, 57, 60]]
    roots = [33, 29, 36, 28, 33, 29]
    for c in range(6):
        t0 = c * 4 * bar
        m.add(sine_pad(chords[c], 4 * bar + 0.5, a=4, r=5), t0, gain=0.45, rev=0.7)
        m.add(saw_pad([n + 12 for n in chords[c][1:]], 4 * bar + 0.5, a=5, r=5, cutoff=700, detune=0.18,
                      brillance=[0, 0.5, 0.1]), t0, gain=0.3, rev=0.8)
        m.add(sub(roots[c], 4 * bar, 1.0), t0, gain=0.35)
    gamme = [69, 72, 74, 76, 79, 81, 84, 86, 88]
    for b in range(nb):
        t0 = b * bar
        if 4 <= b < 20:
            for q in (0, 2):
                m.add(kick(0.8, ton=40, dec=0.5, click=0.0), t0 + q * B, gain=0.45, rev=0.2)
        if 8 <= b < 22:
            for q in range(4):
                m.add(tick(1.0, q % 2 == 0), t0 + q * B, pan=0.4 if q % 2 else -0.4, gain=0.05, rev=0.4)
        if b >= 2:
            for _ in range(2):
                if RNG.random() < 0.8:
                    pos = RNG.integers(0, 8) * 0.5
                    n = int(RNG.choice(gamme))
                    m.add(bell(n, 0.5 + 0.4 * RNG.random(), dec=1.2), t0 + pos * B,
                          pan=float(RNG.uniform(-0.7, 0.7)), gain=0.2, rev=0.8, dly=0.5)
        if b in (3, 11, 19):
            m.add(swell(bar, 800, 9000), t0, gain=0.06, rev=0.8)
    return m.render(rev_decay=7.0, rev_lp=4000, delay_t=1.5 * B, delay_fb=0.55, wet=0.55), "2_Profondeur"


# ------------------------------------------------------------------ 3
def tournoi():
    bpm = 104
    B = 60 / bpm
    bar = 4 * B
    nb = 32
    m = Mix(nb * bar)
    chords = [[52, 55, 59, 62, 66], [48, 52, 55, 59, 62], [43, 55, 59, 62, 64], [50, 57, 62, 64]]
    arps = [[64, 67, 71, 74, 78], [64, 67, 71, 74, 76], [62, 67, 71, 74, 79], [62, 66, 69, 74, 76]]
    roots = [40, 36, 43, 38]
    motif = [0, 2, 1, 3, 2, 4, 1, 3, 0, 2, 1, 4, 3, 2, 1, 2]
    beats = [b * bar + q * B for b in range(12, 28) for q in range(4)]
    duck = duck_env(m.n, beats, prof=0.55, rel=0.18)
    for c in range(nb // 2):
        t0 = c * 2 * bar
        k = c % 4
        if c >= 2:
            pad_ducke(m, saw_pad(chords[k], 2 * bar + 0.3, a=0.8, r=2.0, cutoff=1300 if 6 <= c < 14 else 800,
                                 detune=0.15), t0, duck, gain=0.45, rev=0.4)
        for s in range(32):
            n = arps[k][motif[s % 16]]
            vel = 0.6 + 0.4 * (s % 4 == 0)
            m.add(pluck(n, vel, dec=6, harm=8, duree=0.5), t0 + s * B / 4, pan=0.35 * (1 if s % 2 else -1),
                  gain=0.16, rev=0.2, dly=0.4)
        if 2 <= c < 14:
            for e in range(16):
                pad_ducke(m, np.vstack([bass(roots[k] + (12 if e % 4 == 3 else 0), B / 2 * 0.8, 0.9, cutoff=500)] * 2),
                          t0 + e * B / 2, duck, gain=0.38)
    for b in range(nb):
        t0 = b * bar
        if 12 <= b < 28:
            for q in range(4):
                m.add(kick(0.9, ton=50, dec=0.3, click=0.2), t0 + q * B, gain=0.6)
                m.add(hat(0.8), t0 + q * B + B / 2, pan=0.2, gain=0.09)
            if b >= 16:
                for q in (1, 3):
                    m.add(snare(0.9, dec=16), t0 + q * B, gain=0.3, rev=0.4)
            if b >= 20:  # pendule qui s'accelere
                for s in range(16):
                    m.add(tick(1.0, s % 2 == 0), t0 + s * B / 4, pan=-0.5 if s % 2 else 0.5, gain=0.05)
        if b in (11, 27):
            m.add(swell(bar, 500, 8000), t0, gain=0.12, rev=0.4)
    return m.render(rev_decay=2.8, delay_t=0.75 * B, delay_fb=0.4, wet=0.35), "3_Tournoi"


# ------------------------------------------------------------------ 4
def blitz_de_nuit():
    bpm = 82
    B = 60 / bpm
    bar = 4 * B
    nb = 32
    sw = 0.62
    m = Mix(nb * bar)
    chords = [[56, 60, 63, 67], [53, 56, 60, 63], [56, 60, 61, 65], [52, 58, 61, 67]]
    roots = [41, 37, 34, 36]
    for b in range(nb):
        t0 = b * bar
        k = b % 4
        for (pos, d, v) in ((0, 1.6, 0.9), (1 + sw, 1.2, 0.6), (3 + sw, 0.4, 0.4)):
            for j, n in enumerate(chords[k]):
                m.add(epiano(n, d * B, v * (0.85 + 0.15 * RNG.random()), 0.7), t0 + pos * B + j * 0.012,
                      pan=-0.3 + 0.2 * j, gain=0.14, rev=0.3)
        m.add(bass(roots[k], 1.4 * B, 1.0, drive=1.1, cutoff=320), t0, gain=0.45)
        m.add(bass(roots[k] + 7, 0.5 * B, 0.7, drive=1.1, cutoff=320), t0 + (2 + sw) * B, gain=0.4)
        m.add(bass(roots[k] + 12 if k % 2 else roots[k], 0.8 * B, 0.8, drive=1.1, cutoff=320), t0 + 3 * B, gain=0.4)
        if 4 <= b < 28:
            m.add(kick(0.9, ton=52, dec=0.25, click=0.15), t0, gain=0.55)
            m.add(kick(0.7, ton=52, dec=0.25, click=0.1), t0 + (1 + sw) * B, gain=0.45)
            m.add(kick(0.6, ton=52, dec=0.25, click=0.1), t0 + 2.5 * B + (sw - 0.5) * B, gain=0.3)
            for q in (1, 3):
                m.add(snare(0.9, dec=18, ton=210), t0 + q * B, gain=0.32, rev=0.25)
        if 2 <= b < 30:
            for e in range(8):
                pos = e // 2 + (sw if e % 2 else 0)
                m.add(hat(0.5 + 0.4 * (e % 2 == 0) * RNG.random()), t0 + pos * B, pan=0.3, gain=0.09)
        if 16 <= b < 28:
            for q in range(4):
                m.add(rim(0.7), t0 + q * B + B * (sw + 0.5 if q == 3 else 0), pan=-0.4, gain=0.04 if q != 3 else 0.06)
    mel = [(0, 72, .8), (1 + sw, 75, .6), (2, 77, .7), (3, 75, .5), (4.5, 79, .7), (6, 77, .6), (7, 72, .5)]
    for p in range(4, 12):
        if p in (7, 11):
            continue
        for (bt, n, v) in mel:
            nn = n - (3 if p % 2 and n == 79 else 0)
            m.add(bell(nn, v, dec=2.5), p * 2 * bar + bt * B, pan=0.2, gain=0.13, rev=0.5, dly=0.3)
    m.add(vinyle(nb * bar + 4, densite=6), 0, gain=0.5)
    return m.render(rev_decay=2.2, delay_t=(1 + sw - 1) * B + B / 2, delay_fb=0.35, master_lp=7500, wet=0.3), "4_Blitz_de_nuit"


# ------------------------------------------------------------------ 5
def zugzwang():
    bpm = 90
    B = 60 / bpm
    bar = 4 * B
    nb = 32
    m = Mix(nb * bar, queue=9)
    chords = [[48, 55, 60, 63, 67], [44, 51, 60, 63], [41, 48, 56, 60, 65], [43, 50, 59, 62, 67]]
    roots = [36, 32, 29, 31]
    ost = [0, 0, 12, 0, 7, 0, 3, 0]
    for c in range(nb // 2):
        t0 = c * 2 * bar
        k = c % 4
        intens = min(1.0, c / 12) if c < 14 else 0.15
        m.add(saw_pad(chords[k], 2 * bar + 0.3, a=1.8, r=3.0, cutoff=600 + 900 * intens, detune=0.2,
                      brillance=[0.1, 0.4 * intens + 0.1]), t0, gain=0.45, rev=0.6)
        for e in range(16):
            cut = 280 + 1100 * intens
            v = 1.0 if e % 8 == 0 else 0.75
            m.add(bass(roots[k] + 12 + ost[e % 8], B / 2 * 0.7, v, drive=2.0, cutoff=cut), t0 + e * B / 2,
                  pan=0.15 if e % 2 else -0.15, gain=0.3, rev=0.15)
        m.add(sub(roots[k], 2 * bar - 0.05, 1.0), t0, gain=0.4)
    for b in range(nb):
        t0 = b * bar
        if 8 <= b < 28 and b % 2 == 0:
            m.add(taiko(1.0), t0, gain=0.7, rev=0.5)
            m.add(taiko(0.6), t0 + 2.5 * B, gain=0.5, rev=0.5)
        if b in (22, 23, 26, 27):
            for s in range(12, 16):
                m.add(taiko(0.35 + 0.1 * (s - 12)), t0 + s * B / 4, gain=0.45, rev=0.4)
        if 16 <= b < 28:
            for e in range(8):
                m.add(tick(1.0, e % 2 == 0), t0 + e * B / 2, pan=0.45 if e % 2 else -0.45, gain=0.07, rev=0.2)
        if b in (15, 27):
            m.add(swell(bar, 300, 7000), t0, gain=0.12, rev=0.5)
    theme = [(0, 79, 1), (1.5, 75, .7), (2, 74, .8), (3, 72, .6), (4, 74, .8), (6, 71, .9)]
    for p in range(6, 14):
        for (bt, n, v) in theme:
            nn = n + (3 if p % 4 == 3 and n == 71 else 0)
            m.add(bell(nn, v, dec=2.2), p * 2 * bar + bt * B, pan=-0.2, gain=0.17, rev=0.6, dly=0.3)
    return m.render(rev_decay=4.0, delay_t=0.75 * B, delay_fb=0.4, wet=0.42), "5_Zugzwang"


def ecrire(sig, nom):
    pcm = (np.clip(sig.T, -1, 1) * 32767).astype(np.int16)
    chemin = os.path.join(OUT, nom + ".wav")
    with wave.open(chemin, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", chemin, "-b:a", "192k", os.path.join(OUT, nom + ".mp3")], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", chemin, "-c:a", "libvorbis", "-q:a", "5",
                    os.path.join(OUT, nom + ".ogg")], check=True)
    print(nom, "%.1f s" % (sig.shape[1] / SR), flush=True)


if __name__ == "__main__":
    choix = sys.argv[1:] or ["horloge", "profondeur", "tournoi", "blitz_de_nuit", "zugzwang"]
    for c in choix:
        sig, nom = globals()[c]()
        ecrire(sig, nom)
