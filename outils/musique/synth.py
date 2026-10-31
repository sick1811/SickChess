"""Petite boite a outils de synthese (numpy/scipy) pour les essais de musique SickChess.
Tout est synthetise : aucun echantillon externe, aucun droit a payer."""
import numpy as np
from scipy import signal

SR = 44100
RNG = np.random.default_rng(1811)


def f(n):
    return 440.0 * 2 ** ((n - 69) / 12.0)


def tt(d):
    return np.arange(int(d * SR)) / SR


def lp(x, fc, order=2):
    sos = signal.butter(order, min(fc, SR * 0.45), "low", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=-1)


def hp(x, fc, order=2):
    sos = signal.butter(order, fc, "high", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=-1)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "band", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=-1)


def env(n, a, r, total):
    """Enveloppe attaque lineaire / maintien / relache sur `total` secondes."""
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    na = min(na, n)
    if na:
        e[:na] = np.linspace(0, 1, na) ** 1.5
    nt = min(int(total * SR), n)
    if nr and nt < n:
        e[nt:] = 0
        rel = min(nr, n - nt)
        e[nt:nt + rel] = np.linspace(1, 0, rel) ** 2
    return e


class Mix:
    def __init__(self, duree, queue=8.0):
        self.L = int(duree * SR)
        self.n = self.L + int(queue * SR)
        self.dry = np.zeros((2, self.n))
        self.rev = np.zeros((2, self.n))
        self.dly = np.zeros((2, self.n))

    def add(self, x, t0, pan=0.0, gain=1.0, rev=0.0, dly=0.0):
        x = np.asarray(x, dtype=float)
        if x.ndim == 1:
            a = (pan + 1) * np.pi / 4
            x = np.vstack([x * np.cos(a), x * np.sin(a)]) * np.sqrt(2)
        i = int(t0 * SR)
        if i >= self.n:
            return
        m = min(x.shape[1], self.n - i)
        self.dry[:, i:i + m] += x[:, :m] * gain
        if rev:
            self.rev[:, i:i + m] += x[:, :m] * gain * rev
        if dly:
            self.dly[:, i:i + m] += x[:, :m] * gain * dly

    def render(self, rev_decay=3.5, rev_lp=5000, delay_t=0.375, delay_fb=0.45, delay_lp=3000,
               duck=None, master_lp=None, wet=0.35):
        out = self.dry.copy()
        # delai ping-pong
        if np.any(self.dly):
            d = int(delay_t * SR)
            src = lp(self.dly, delay_lp)
            acc = np.zeros_like(src)
            g = 1.0
            for k in range(1, 9):
                g *= delay_fb
                sh = d * k
                if sh >= self.n:
                    break
                ch = k % 2
                acc[ch, sh:] += src[0 if ch else 1, :-sh] * g * 0.5 + src[ch, :-sh] * g * 0.5
            out += acc
            self.rev += acc * 0.6
        # reverb a convolution (reponse impulsionnelle synthetique)
        if np.any(self.rev):
            n_ir = int(rev_decay * 1.6 * SR)
            tir = np.arange(n_ir) / SR
            ir = RNG.standard_normal((2, n_ir)) * np.exp(-tir * 6.9 / rev_decay)
            ir = lp(ir, rev_lp)
            ir[:, :int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
            ir /= np.sqrt(np.sum(ir ** 2, axis=1, keepdims=True))
            w = np.vstack([signal.fftconvolve(self.rev[c], ir[c])[:self.n] for c in range(2)])
            out += w * wet
        if duck is not None:
            out *= duck[:self.n]
        if master_lp:
            out = lp(out, master_lp, 1)
        # boucle : la queue revient au debut
        loop = out[:, :self.L].copy()
        tail = out[:, self.L:]
        k = min(tail.shape[1], self.L)
        loop[:, :k] += tail[:, :k]
        loop = hp(loop, 28)
        loop = np.tanh(loop / np.max(np.abs(loop)) * 1.3) / np.tanh(1.3)
        return loop * 0.89


# ---------- instruments ----------

def saw_pad(notes, duree, a=2.0, r=3.0, cutoff=1400, detune=0.12, voix=3, brillance=None):
    n = int((duree + r) * SR)
    t = np.arange(n) / SR
    out = np.zeros((2, n))
    for note in notes:
        fr = f(note)
        for c in range(2):
            for v in range(voix):
                cents = (v - (voix - 1) / 2) * detune * 100 / max(1, voix - 1) * (1 if c == 0 else -1) * 2
                ph = RNG.random()
                out[c] += signal.sawtooth(2 * np.pi * (fr * 2 ** (cents / 1200) * t + ph))
    out /= len(notes) * voix
    out = lp(out, cutoff, 4)
    if brillance is not None:  # balayage : melange sombre/clair
        clair = lp(out, cutoff * 3, 2)
        b = np.interp(t, np.linspace(0, t[-1], len(brillance)), brillance)
        out = out * (1 - b) + clair * b
    return out * env(n, a, r, duree)


def sine_pad(notes, duree, a=3.0, r=4.0):
    n = int((duree + r) * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for note in notes:
        fr = f(note)
        x += np.sin(2 * np.pi * fr * t) + 0.3 * np.sin(2 * np.pi * fr * 2.003 * t) + 0.12 * np.sin(2 * np.pi * fr * 3.01 * t)
    x /= len(notes)
    trem = 1 + 0.15 * np.sin(2 * np.pi * 0.17 * t)
    return x * env(n, a, r, duree) * trem


def epiano(note, duree=1.5, vel=1.0, bright=1.0):
    d = duree + 1.2
    t = tt(d)
    fr = f(note)
    idx = (1.6 * bright * vel) * np.exp(-t * 4)
    x = np.sin(2 * np.pi * fr * t + idx * np.sin(2 * np.pi * fr * t))
    x += 0.25 * np.sin(2 * np.pi * fr * 7.0 * t) * np.exp(-t * 18) * bright  # tine
    a = np.exp(-t * 1.1) * env(len(t), 0.003, 0.6, duree)
    return x * a * vel


def bell(note, vel=1.0, dec=1.6):
    t = tt(5.0)
    fr = f(note)
    idx = 2.2 * np.exp(-t * 2.5)
    x = np.sin(2 * np.pi * fr * t + idx * np.sin(2 * np.pi * fr * 3.5 * t))
    x += 0.3 * np.sin(2 * np.pi * fr * 2.01 * t) * np.exp(-t * 3)
    return x * np.exp(-t * dec) * env(len(t), 0.002, 0.1, 10) * vel


def pluck(note, vel=1.0, dec=3.0, harm=10, duree=1.2):
    t = tt(duree)
    fr = f(note)
    x = np.zeros_like(t)
    for k in range(1, harm + 1):
        if fr * k > 12000:
            break
        x += (1.0 / k) * np.sin(2 * np.pi * fr * k * t + RNG.random()) * np.exp(-t * (dec + k * 1.8))
    x[:40] *= np.linspace(0, 1, 40)
    return x * vel


def bass(note, duree, vel=1.0, drive=1.5, cutoff=400):
    d = duree + 0.15
    t = tt(d)
    fr = f(note)
    x = np.sin(2 * np.pi * fr * t) + 0.35 * signal.sawtooth(2 * np.pi * fr * t)
    x = lp(np.tanh(x * drive), cutoff)
    return x * env(len(t), 0.008, 0.12, duree) * vel


def sub(note, duree, vel=1.0):
    t = tt(duree + 0.3)
    x = np.sin(2 * np.pi * f(note) * t)
    return x * env(len(t), 0.02, 0.3, duree) * vel


def kick(vel=1.0, ton=48, dec=0.4, click=0.3):
    t = tt(0.6)
    fr = ton + ton * 2.5 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(fr) / SR
    x = np.sin(ph) * np.exp(-t / dec * 2.5)
    x += click * RNG.standard_normal(len(t)) * np.exp(-t * 300)
    return np.tanh(x * 1.4) * vel


def tick(vel=1.0, haut=True):
    """Tic-tac de pendule d'echecs : bois sec, court."""
    t = tt(0.12)
    fr = 2600 if haut else 1900
    x = np.sin(2 * np.pi * fr * t) * np.exp(-t * 160)
    x += 0.6 * bp(RNG.standard_normal(len(t)), fr * 0.7, fr * 1.6) * np.exp(-t * 120)
    x += 0.4 * np.sin(2 * np.pi * fr * 0.47 * t) * np.exp(-t * 90)
    return x * vel


def hat(vel=1.0, dec=40, ouvert=False):
    t = tt(0.4 if ouvert else 0.12)
    x = hp(RNG.standard_normal(len(t)), 7000, 2) * np.exp(-t * (12 if ouvert else dec))
    return x * vel


def snare(vel=1.0, dec=14, ton=190):
    t = tt(0.35)
    x = 0.7 * bp(RNG.standard_normal(len(t)), 1200, 6500) * np.exp(-t * dec)
    x += 0.6 * np.sin(2 * np.pi * ton * t) * np.exp(-t * 25)
    return x * vel


def rim(vel=1.0):
    t = tt(0.08)
    x = np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 200) + 0.4 * bp(RNG.standard_normal(len(t)), 2000, 5000) * np.exp(-t * 150)
    return x * vel


def taiko(vel=1.0):
    t = tt(1.4)
    fr = 55 + 60 * np.exp(-t * 14)
    ph = 2 * np.pi * np.cumsum(fr) / SR
    x = np.sin(ph) * np.exp(-t * 3.2)
    x += 0.5 * lp(RNG.standard_normal(len(t)), 600) * np.exp(-t * 18)
    return np.tanh(x * 1.6) * vel


def swell(duree, lo=300, hi=6000):
    """Souffle montant (bruit filtre) pour les transitions."""
    t = tt(duree)
    x = RNG.standard_normal(len(t))
    x = bp(x, lo, hi)
    return x * (t / duree) ** 2.2


def vinyle(duree, densite=7, niveau=1.0):
    n = int(duree * SR)
    x = lp(RNG.standard_normal(n), 3000) * 0.02
    clics = RNG.random(n) < densite / SR
    imp = np.zeros(n)
    imp[clics] = RNG.standard_normal(clics.sum()) * 0.6
    x += bp(imp, 1500, 9000)
    return x * niveau


def duck_env(n, temps, prof=0.5, rel=0.22):
    """Enveloppe de 'pompe' (sidechain) sur chaque temps."""
    g = np.ones(n)
    k = int(rel * 4 * SR)
    seg = 1 - prof * np.exp(-np.arange(k) / (rel * SR))
    for t0 in temps:
        i = int(t0 * SR)
        if i >= n:
            break
        m = min(k, n - i)
        g[i:i + m] = np.minimum(g[i:i + m], seg[:m])
    return np.vstack([g, g])
