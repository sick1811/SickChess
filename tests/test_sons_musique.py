# tests/test_sons_musique.py - packs de sons et musique (17/10, travaux p14, p15).
#     python tests/test_sons_musique.py

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

import sounds
import musique

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


print("1. Les packs")
bois = sounds.SoundManager(0.5, "bois")
verifier(len(bois.sounds) == len(sounds.SOUND_KEYS), "pack Bois : %d sons" % len(bois.sounds))
feutre = sounds.SoundManager(0.5, "feutre")
verifier(len(feutre.sounds) == len(sounds.SOUND_KEYS), "pack Feutre : %d sons" % len(feutre.sounds))
verifier(all(os.path.exists(os.path.join("sounds", "feutre", k + ".wav")) for k in sounds.SOUND_KEYS),
         "les fichiers du pack Feutre existent")
b = pygame.sndarray.array(bois.sounds["move"]).astype(float)
f = pygame.sndarray.array(feutre.sounds["move"]).astype(float)
verifier(abs(f).max() < abs(b).max(), "Feutre est plus doux que Bois")
alertes = sounds.SoundManager(0.5, "alertes")
verifier(not alertes.play("move") and not alertes.play("capture"), "Muet sauf alertes : pas de son de coup")
verifier(alertes.play("check") and alertes.play("low_time"), "... mais l'echec et le temps sonnent")
verifier(bois.changer_de_pack("feutre") == "feutre" and len(bois.sounds) == len(sounds.SOUND_KEYS),
         "changer de pack en direct")

print("2. La musique")
verifier(os.path.exists(os.path.join("music", "calme.wav")), "music/calme.wav existe")
import wave
with wave.open(os.path.join("music", "calme.wav"), "rb") as w:
    duree = w.getnframes() / float(w.getframerate())
verifier(25 <= duree <= 60, "boucle de %.0f s" % duree)
verifier(musique.jouer({"musique": True, "volume_musique": 0.3}) and musique.en_cours(), "elle se lance")
musique.arreter(0)
verifier(not musique.en_cours(), "elle s'arrete")
verifier(not musique.jouer({"musique": False}), "Musique : Non = silence")

print("3. Options")
import ecran_options
cles = [r.cle for _i, _n, rs in ecran_options._onglets() for r in rs]
verifier(all(c in cles for c in ("pack_sons", "musique", "volume_musique")),
         "Options -> Son : pack, musique, volume de la musique")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
