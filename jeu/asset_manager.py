# asset_manager.py - V6 : chargement et vidange des images du menu
#
# CE QUI CHANGE PAR RAPPORT A V5 :
#   1. IL N'ETAIT UTILISE NULLE PART. MainMenu rechargeait les memes frames de
#      son cote : deux chemins de chargement differents pour la meme chose.
#      MainMenu passe desormais par cette classe.
#   2. cleanup() FAISAIT pygame.mixer.quit(), ce qui aurait coupe TOUS les
#      bruitages du jeu, pas seulement la musique du menu. Il ne coupe plus que
#      la musique et libere les images. (parametre fermer_mixer, False par
#      defaut, si tu veux vraiment l'ancien comportement.)
#   3. Les 241 frames sont chargees, pas seulement 40 : le plafond vient de
#      config.json ("menu_frames_max", 0 = toutes).
#   4. Les fichiers sont cherches a cote du script aussi bien que dans le
#      dossier courant : indispensable une fois le jeu compile en .exe.
#
# AUCUNE FONCTION SUPPRIMEE : __init__, load_menu_assets(max_frames) et
# cleanup() sont conservees.

import json
import os
import sys

import pygame


def dossier_ressources():
    """Dossier des assets, y compris quand le jeu est compile avec PyInstaller."""
    base = getattr(sys, "_MEIPASS", None)
    if base and os.path.isdir(os.path.join(base, "assets")):
        return base
    for candidat in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        if os.path.isdir(os.path.join(candidat, "assets")):
            return candidat
    return os.getcwd()


def chemin_ressource(*morceaux):
    return os.path.join(dossier_ressources(), *morceaux)


def dossier_de_donnees(nom):
    """Ou trouver un dossier de DONNEES LIVREES : ouvertures/, puzzles/, syzygy/.

    V8 (04/09) - LE BUG QUE JULIEN A SENTI EN DEMANDANT "ya pas les ouvertures ?"
    Ces trois dossiers etaient cherches avec dossier_ecriture(), c'est-a-dire A
    COTE de l'executable. Or PyInstaller range tout ce qu'il embarque dans le
    sous-dossier _internal. En lancant le jeu depuis les sources, tout marchait ;
    UNE FOIS COMPILE, les 3 810 ouvertures et les 4 180 151 problemes etaient
    introuvables - et le jeu ne disait rien, il retombait sur ses 103 ouvertures
    ecrites a la main et eteignait le mode PROBLEMES tout seul. Le genre de bug
    qu'on ne decouvre que chez celui a qui on a donne le jeu.

    On regarde donc dans l'ordre : le paquet compile (_MEIPASS), le dossier de
    l'executable, le dossier courant, celui du code. Le premier qui existe gagne.
    Si aucun n'existe, on renvoie le chemin "a cote de l'executable" : c'est la
    qu'on ira le deposer a la main.
    """
    candidats = [getattr(sys, "_MEIPASS", None)]
    if getattr(sys, "frozen", False):
        candidats.append(os.path.dirname(os.path.abspath(sys.executable)))
    candidats.append(os.getcwd())
    candidats.append(os.path.dirname(os.path.abspath(__file__)))
    for base in candidats:
        if not base:
            continue
        chemin = os.path.join(base, nom)
        if os.path.isdir(chemin):
            return chemin
    return os.path.join(dossier_ecriture(), nom)


def dossier_ecriture():
    """Dossier ou le jeu a le droit d'ecrire : config.json, parties/, logs.

    Une fois compile en .exe, les fichiers embarques sont dans un sous-dossier
    interne que Windows peut protéger. Tout ce qui doit etre modifiable vit
    donc a cote de l'executable.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    # SickChess : le code vit dans jeu/, les fichiers modifiables (config.json,
    # parties/, profil) vivent a la racine du projet, a cote de SickChess.py.
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def preparer_dossier_utilisateur():
    """Au premier lancement de l'exe, sort les fichiers modifiables a cote.

    Sans cela, l'ecran de reglages ne pourrait pas enregistrer les choix de
    l'utilisateur (case "retenir ces reglages").
    """
    if not getattr(sys, "frozen", False):
        return
    import shutil
    cible = dossier_ecriture()
    for nom in ("config.json", "REGLAGES.txt"):
        source = chemin_ressource(nom)
        destination = os.path.join(cible, nom)
        if os.path.exists(source) and not os.path.exists(destination):
            try:
                shutil.copyfile(source, destination)
                print("[ASSETS] %s copie a cote de l'executable" % nom)
            except OSError as e:
                print("[ASSETS] copie de %s impossible : %s" % (nom, e))


def _plafond_frames():
    for dossier in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        chemin = os.path.join(dossier, "config.json")
        if os.path.exists(chemin):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    contenu = json.load(f)
            # JOURNEE DEBUG DU 04/09 : un config.json coupe en plein
            # milieu (coupure de courant, disque plein) contient
            # "null" ou "[]". json.load() ne bronche pas, et le .get()
            # qui suit levait un AttributeError QUE PERSONNE N'ATTRAPAIT :
            # le jeu ne demarrait plus. Un fichier qui n'est pas un
            # dictionnaire vaut desormais un fichier absent.
                if not isinstance(contenu, dict):
                    return 0
                return int(contenu.get("menu_frames_max", 0))
            except (ValueError, OSError, TypeError):
                return 0
    return 0


class AssetManager:
    def __init__(self):
        if not pygame.get_init():
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.init()

        self.frames = []
        self.images = {}
        self.sounds = {}
        self.music = None
        self.taille_ecran = (1280, 720)

    # ------------------------------------------------------------------ menu

    def load_menu_assets(self, max_frames=None, musique=True):
        """Charge le fond anime et la musique du menu.

        V7.1 : "musique" (nouveau, optionnel, vrai par defaut - AUCUN appel
        existant n'est casse) permet de charger la musique SANS la jouer, quand
        la case "couper la musique du menu" est cochee. On la charge quand meme
        pour que decocher la case la relance tout de suite, sans rien recharger.
        """
        if max_frames is None:
            max_frames = _plafond_frames()
        print("[ASSETS] Chargement du menu...")

        self.frames = []
        dossier = chemin_ressource("assets", "menu_frames")
        if os.path.isdir(dossier):
            noms = sorted(f for f in os.listdir(dossier)
                          if f.startswith("frame_") and f.lower().endswith(".png"))
            if max_frames and max_frames > 0:
                noms = noms[:max_frames]
            for nom in noms:
                try:
                    image = pygame.image.load(os.path.join(dossier, nom)).convert()
                    self.frames.append(pygame.transform.scale(image, self.taille_ecran))
                except pygame.error as e:
                    print("[ASSETS] frame illisible %s : %s" % (nom, e))
            print("[ASSETS] %d frames de fond chargees" % len(self.frames))
        else:
            print("[ASSETS] Pas de dossier assets/menu_frames")

        # Logo
        for nom in ("logo.png", "logo.jpg"):
            chemin = chemin_ressource("assets", nom)
            if os.path.exists(chemin):
                try:
                    logo = pygame.image.load(chemin).convert_alpha()
                    self.images["logo"] = pygame.transform.scale(logo, (600, 180))
                    print("[ASSETS] Logo charge (%s)" % nom)
                    break
                except pygame.error as e:
                    print("[ASSETS] logo illisible : %s" % e)

        # Musique du menu : on prefere le canal 'music', fait pour les fichiers longs.
        for nom in ("menu_music.ogg", "menu_music.mp3", "game_start.ogg", "game_start.mp3"):
            chemin = chemin_ressource("assets", nom)
            if os.path.exists(chemin):
                try:
                    pygame.mixer.music.load(chemin)
                    pygame.mixer.music.set_volume(0.25)
                    if musique:
                        pygame.mixer.music.play(-1)
                    self.music = chemin
                    print("[ASSETS] Musique du menu : %s (%s)"
                          % (nom, "volume 25%" if musique else "coupee"))
                    break
                except pygame.error as e:
                    print("[ASSETS] musique illisible (%s) : %s" % (nom, e))
        if self.music is None:
            print("[ASSETS] Pas de musique de menu trouvee")

        print("[ASSETS] Menu pret")
        return self.frames

    def get_frames(self):
        return self.frames

    def get_image(self, nom):
        return self.images.get(nom)

    def stop_music(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except pygame.error:
            pass

    # ------------------------------------------------------------------ vidange

    def cleanup(self, fermer_mixer=False):
        """Libere la memoire du menu quand la partie demarre."""
        print("[ASSETS] Vidange des ressources du menu...")
        self.stop_music()
        if fermer_mixer:
            # ATTENTION : coupe TOUS les sons du jeu. C'etait le comportement
            # de la V5, conserve seulement sur demande explicite.
            try:
                pygame.mixer.quit()
            except pygame.error:
                pass
        self.frames = []
        self.images.clear()
        self.sounds.clear()
        print("[ASSETS] Memoire du menu liberee")
