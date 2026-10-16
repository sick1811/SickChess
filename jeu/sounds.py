# sounds.py - V6 : les bruitages du jeu
#
# CE QUI CHANGE PAR RAPPORT A V5 (bug m1 du rapport, ta note "son du jeu a mute") :
#   1. LE FORMAT. Les 19 bruitages sont des .mp3 charges avec
#      pygame.mixer.Sound(). SDL_mixer gere mal le MP3 dans un Sound : selon la
#      version et le fichier, ca leve une erreur ou ca joue dans le vide.
#      C'est la cause la plus probable du son qui ne sort pas.
#      Le chargeur cherche donc d'abord un .ogg, puis un .wav, et ne retombe
#      sur le .mp3 qu'en dernier recours. Les .ogg ont ete generes a partir de
#      tes mp3 et places dans sounds/ : rien a faire de ton cote.
#   2. LES CANAUX. pygame n'a que 8 canaux par defaut ; sur un coup avec
#      capture et echec, un son pouvait etre coupe. On monte a 24.
#   3. Le volume est reglable dans config.json ("volume_sons", de 0 a 1) et un
#      interrupteur "sons_actifs" permet de tout couper.
#   4. Un resume clair au demarrage : combien de sons charges, lesquels
#      manquent, et dans quel format ils ont ete pris.
#
# AUCUNE FONCTION SUPPRIMEE : __init__, load_sounds et play(name) sont
# conservees, memes noms.

import json
import os

import pygame

# Ordre de preference : le premier format trouve gagne.
EXTENSIONS = (".ogg", ".wav", ".mp3")

SOUND_KEYS = [
    "move", "knight_move", "bishop_move", "rook_move", "queen_move", "king_move",
    "capture", "illegal", "check", "checkmate", "stalemate",
    "en_passant", "castling", "promotion", "low_time", "game_start", "game_end",
    "fifty_moves", "repetition",
]


class SoundManager:
    def __init__(self, volume=None):
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except pygame.error as e:
                print("[SONS] Carte son indisponible (%s) - jeu en silencieux" % e)
        try:
            pygame.mixer.set_num_channels(24)
        except Exception:
            pass

        self.sounds = {}
        self.formats = {}
        self.actif = True
        self.volume = 0.6 if volume is None else float(volume)
        self._charger_reglages()
        self.load_sounds()

    def _charger_reglages(self):
        for dossier in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
            chemin = os.path.join(dossier, "config.json")
            if os.path.exists(chemin):
                try:
                    with open(chemin, "r", encoding="utf-8") as f:
                        contenu = json.load(f)
                    # JOURNEE DEBUG DU 04/09 : config.json abime ("null", "[]")
                    # faisait planter la creation des sons, donc le demarrage
                    # de toute partie. On ignore un fichier qui n'est pas un
                    # dictionnaire au lieu de laisser filer l'AttributeError.
                    if not isinstance(contenu, dict):
                        contenu = {}
                    self.volume = float(contenu.get("volume_sons", self.volume))
                    self.actif = bool(contenu.get("sons_actifs", True))
                except (ValueError, OSError, TypeError):
                    pass
                break

    # ------------------------------------------------------------------ chargement

    def _dossiers_de_recherche(self):
        ici = os.path.dirname(os.path.abspath(__file__))
        return [os.path.join(os.getcwd(), "sounds"), os.path.join(ici, "sounds")]

    def _trouver_fichier(self, cle, config):
        # 1. Chemin explicite dans config.json (comportement V5 conserve).
        chemin = config.get("sound_" + cle)
        if chemin and os.path.exists(chemin):
            return chemin
        # 2. Dossier sounds/, en preferant .ogg puis .wav puis .mp3.
        for dossier in self._dossiers_de_recherche():
            for extension in EXTENSIONS:
                candidat = os.path.join(dossier, cle + extension)
                if os.path.exists(candidat):
                    return candidat
        return None

    def load_sounds(self):
        config = {}
        for dossier in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
            chemin = os.path.join(dossier, "config.json")
            if os.path.exists(chemin):
                try:
                    with open(chemin, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    if not isinstance(config, dict):
                        config = {}
                except (ValueError, OSError):
                    config = {}
                break

        manquants = []
        for cle in SOUND_KEYS:
            chemin = self._trouver_fichier(cle, config)
            if not chemin:
                manquants.append(cle)
                continue
            try:
                son = pygame.mixer.Sound(chemin)
                son.set_volume(self.volume)
                self.sounds[cle] = son
                self.formats[cle] = os.path.splitext(chemin)[1]
            except Exception as e:
                print("[SONS] Echec du chargement de %s : %s" % (os.path.basename(chemin), e))
                manquants.append(cle)

        formats = {}
        for extension in self.formats.values():
            formats[extension] = formats.get(extension, 0) + 1
        detail = ", ".join("%d en %s" % (n, ext) for ext, n in sorted(formats.items()))
        print("[SONS] %d/%d bruitages charges (%s), volume %d%%"
              % (len(self.sounds), len(SOUND_KEYS), detail or "aucun", int(self.volume * 100)))
        if manquants:
            print("[SONS] Introuvables : %s" % ", ".join(manquants))

    # ------------------------------------------------------------------ lecture

    def play(self, name):
        if not self.actif:
            return False
        son = self.sounds.get(name)
        if son is None:
            return False
        try:
            son.set_volume(self.volume)
            son.play()
            return True
        except Exception as e:
            print("[SONS] Lecture impossible de %s : %s" % (name, e))
            return False

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, float(volume)))
        for son in self.sounds.values():
            try:
                son.set_volume(self.volume)
            except Exception:
                pass

    def couper(self, coupe=True):
        self.actif = not coupe

    def est_charge(self, name):
        return name in self.sounds
