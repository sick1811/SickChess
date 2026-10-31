# tests/test_distribution.py - un seul reglage « distribution » : amis / steam / itch
# (31/10, demande de Julien : itch.io sans le numero 480 ni Steam).
#     python tests/test_distribution.py
# Faux Steam (rien n'est charge), fenetre invisible, dossier temporaire : ni
# profil.json ni parties/ ne sont touches.

import json
import os
import shutil
import sys
import tempfile
import types

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.pop("SICKCHESS_DISTRIBUTION", None)

import pygame

pygame.init()
ecran = pygame.display.set_mode((1024, 640), pygame.RESIZABLE)

import asset_manager

TEMP = tempfile.mkdtemp(prefix="sickchess_distribution_")
asset_manager.dossier_ecriture = lambda: TEMP

import classements
import distribution
import ecran_classements
import langue_en
import partie_en_ligne
import salon_en_ligne
import steam as module_steam
import ui
from menu_principal import MainMenu

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def touche(cle):
    return pygame.event.Event(pygame.KEYDOWN, key=cle, mod=0, unicode="")


class FauxSteam:
    """Un Steam eteint qui compte les tentatives de demarrage."""

    def __init__(self):
        self.actif = False
        self.erreur = self.conseil = ""
        self.appid = 0
        self.demarrages = 0
        self.pompes = 0

    def demarrer(self):
        self.demarrages += 1
        self.erreur = "Steam n'est pas lancé."
        return False

    def pomper(self):
        self.pompes += 1

    def evenements(self, *types):
        return []

    def amis(self):
        return []

    def rejoindre_salon(self, salon):
        raise AssertionError("rejoindre_salon sans Steam")

    def creer_salon(self, places=2):
        raise AssertionError("creer_salon sans Steam")

    def quitter_salon(self, salon):
        pass


# ------------------------------------------------------------------ 1
print("1. Le reglage lui-meme (jeu/distribution.py)")
d = tempfile.mkdtemp(prefix="sickchess_dist_fichier_")
verifier(distribution.lire(d) == "amis", "distribution.json absent : amis (comme aujourd'hui)")
for nom in distribution.DISTRIBUTIONS:
    with open(os.path.join(d, distribution.FICHIER), "w", encoding="utf-8") as f:
        f.write(distribution.contenu_fichier(nom))
    verifier(distribution.lire(d) == nom, "distribution.json = %s : relu %s" % (nom, nom))
for contenu in ("pas du json", '{"distribution": "xbox"}', "[1, 2]", "{}"):
    with open(os.path.join(d, distribution.FICHIER), "w", encoding="utf-8") as f:
        f.write(contenu)
    verifier(distribution.lire(d) == "amis", "distribution.json illisible (%s) : amis" % contenu[:20])
shutil.rmtree(d, ignore_errors=True)
try:
    distribution.contenu_fichier("xbox")
    verifier(False, "distribution inconnue refusee a la compilation")
except ValueError:
    verifier(True, "distribution inconnue refusee a la compilation")
verifier(json.loads(distribution.contenu_fichier("itch")) == {"distribution": "itch"},
         "distribution.json ecrit : {\"distribution\": \"itch\"}")
verifier(not os.path.exists(os.path.join(RACINE, distribution.FICHIER)),
         "pas de distribution.json dans le dossier de developpement (= amis)")
distribution.fixer(None)
verifier(distribution.actuelle() == "amis", "le dossier de developpement est en amis")
os.environ["SICKCHESS_DISTRIBUTION"] = "itch"
distribution.fixer(None)
verifier(distribution.actuelle() == "itch", "essai sans compiler : SICKCHESS_DISTRIBUTION=itch")
os.environ["SICKCHESS_DISTRIBUTION"] = "n'importe quoi"
distribution.fixer(None)
verifier(distribution.actuelle() == "amis", "variable inconnue : ignoree (amis)")
os.environ.pop("SICKCHESS_DISTRIBUTION", None)
distribution.fixer(None)

verifier(distribution.numero_steam("amis") == 480, "amis : numero Steam 480")
verifier(distribution.numero_steam("steam") == distribution.APPID_STEAM_REEL,
         "steam : le vrai numero (APPID_STEAM_REEL = %s)" % distribution.APPID_STEAM_REEL)
verifier(distribution.APPID_STEAM_REEL is None,
         "APPID_STEAM_REEL = None tant que Julien n'a pas le compte Steamworks")
verifier(distribution.numero_steam("itch") is None, "itch : aucun numero Steam")
verifier(module_steam.APPID_DE_TEST == distribution.APPID_DE_TEST == 480,
         "steam.py lit le 480 dans distribution.py (un seul endroit)")
verifier(distribution.steam_permis("amis") and distribution.steam_permis("steam")
         and not distribution.steam_permis("itch"), "Steam permis pour amis et steam, jamais pour itch")

# ------------------------------------------------------------------ 2
print("2. steam.demarrer() : la DLL n'est jamais chargee en itch")
chargees = []


class FausseDLL:
    def __init__(self, chemin):
        chargees.append(chemin)
        raise OSError("fausse DLL (test)")


vrai_ctypes_cdll = module_steam.ctypes.CDLL
vrai_sys = module_steam.sys
module_steam.ctypes.CDLL = FausseDLL
# Meme hors Windows (Claude dans le cloud), on fait comme sous Windows.
module_steam.sys = types.SimpleNamespace(platform="win32", argv=[], frozen=False)
try:
    for nom in ("amis", "steam", "itch"):
        distribution.fixer(nom)
        s = module_steam.Steam(TEMP)
        s._chemin_dll = lambda: os.path.join(TEMP, "steam_api64.dll")
        avant = len(chargees)
        ok = s.demarrer()
        if nom == "itch":
            verifier(not ok and len(chargees) == avant and not s.actif,
                     "itch : demarrer() refuse sans charger steam_api64.dll (meme si Steam est ouvert)")
            verifier(s.erreur == module_steam.MESSAGE_SANS_STEAM, "itch : la raison est claire (%s)" % s.erreur)
            s.demarrer()
            verifier(len(chargees) == avant, "itch : un 2e essai ne charge rien non plus")
        else:
            verifier(not ok and len(chargees) == avant + 1,
                     "%s : demarrer() essaie la DLL comme avant" % nom)
finally:
    module_steam.ctypes.CDLL = vrai_ctypes_cdll
    module_steam.sys = vrai_sys

# ------------------------------------------------------------------ 3
print("3. Invitation Steam au menu (partie_en_ligne)")
argv = list(sys.argv)
for nom in ("amis", "steam", "itch"):
    distribution.fixer(nom)
    faux = FauxSteam()
    module_steam._INSTANCE = faux
    partie_en_ligne._INVITATION.update({"essai": False, "salon": 0})
    sys.argv = [argv[0], "+connect_lobby", "123456"]
    try:
        salon = partie_en_ligne.invitation_en_attente()
        partie_en_ligne.invitation_en_attente()
    finally:
        sys.argv = argv
    if nom == "itch":
        verifier(faux.demarrages == 0 and salon == 0,
                 "itch : Steam jamais demarre, meme lance par une invitation (+connect_lobby)")
    else:
        verifier(faux.demarrages == 1 and salon == 123456,
                 "%s : l'invitation demarre Steam comme avant" % nom)
module_steam._INSTANCE = None
partie_en_ligne._INVITATION.update({"essai": False, "salon": 0})

# ------------------------------------------------------------------ 4
print("4. Ecran « Jouer en ligne »")
textes = []
vrai_texte, vrai_paragraphe = ui.texte, ui.paragraphe


def note_texte(surface, chaine, *a, **k):
    textes.append(str(chaine))
    return vrai_texte(surface, chaine, *a, **k)


def note_paragraphe(surface, chaine, *a, **k):
    textes.append(str(chaine))
    return vrai_paragraphe(surface, chaine, *a, **k)


ui.texte, ui.paragraphe = note_texte, note_paragraphe
horloge = pygame.time.Clock()
try:
    distribution.fixer("itch")
    faux = FauxSteam()
    salon = salon_en_ligne.SalonEnLigne(ecran, horloge, None, "Moi", steam=faux,
                                        salon_a_rejoindre=987654)
    for taille in ((1024, 640), (800, 600), (1920, 1080)):
        salon.screen = pygame.display.set_mode(taille, pygame.RESIZABLE)
        del textes[:]
        salon.update()
        salon.draw()
    cles = [b.cle for b in salon._visibles]
    verifier(faux.demarrages == 0 and faux.pompes == 0,
             "itch : ouvrir l'ecran ne demarre pas Steam (meme avec un salon a rejoindre)")
    verifier(salon_en_ligne.SANS_STEAM_TITRE in textes and salon_en_ligne.SANS_STEAM_TEXTE in textes,
             "itch : le message clair est affiche")
    verifier(cles == ["retour"], "itch : seul « Retour » reste (pas de Créer / Rejoindre / tests) : %s" % cles)
    salon.creer()
    salon.rejoindre(42)
    salon._clic("reessayer")
    verifier(faux.demarrages == 0 and salon.etape == "accueil", "itch : Créer / Rejoindre / Réessayer ne font rien")
    verifier(salon.handle_event(touche(pygame.K_ESCAPE)) == "retour", "itch : Échap revient au menu")
    pygame.event.clear()
    pygame.event.post(touche(pygame.K_ESCAPE))
    verifier(salon.run() is None, "itch : l'ecran s'ouvre et se ferme sans planter (run)")
    ecran = pygame.display.set_mode((1024, 640), pygame.RESIZABLE)

    for nom in ("amis", "steam"):
        distribution.fixer(nom)
        faux = FauxSteam()
        salon = salon_en_ligne.SalonEnLigne(ecran, horloge, None, "Moi", steam=faux)
        del textes[:]
        salon.update()
        salon.draw()
        cles = [b.cle for b in salon._visibles]
        verifier(faux.demarrages == 1 and "creer" in cles and "rejoindre" in cles,
                 "%s : comme avant (Steam essaye, Créer / Rejoindre presents)" % nom)
        verifier(salon_en_ligne.SANS_STEAM_TITRE not in textes, "%s : pas de message itch" % nom)
        pygame.event.clear()
        pygame.event.post(touche(pygame.K_ESCAPE))
        verifier(salon.run() is None, "%s : l'ecran s'ouvre et se ferme sans planter" % nom)

    # ------------------------------------------------------------------ 5
    print("5. Ecran « Classements »")
    distribution.fixer("itch")
    faux = FauxSteam()
    e = ecran_classements.EcranClassements(ecran, {}, steam=faux, gestionnaire=classements.Classements(faux))
    del textes[:]
    for _ in range(3):
        e.draw()
    scores = e.mes_scores()
    verifier(faux.demarrages == 0, "itch : ouvrir les classements ne demarre pas Steam")
    verifier(e.boutons == [e.btn_retour], "itch : seul « Retour » (pas de Mondial / Amis / Actualiser)")
    verifier("Classements" in textes and "Classements Steam" not in textes, "itch : titre « Classements »")
    verifier(ecran_classements.SANS_STEAM_TITRE in textes and ecran_classements.SANS_STEAM_TEXTE in textes,
             "itch : le message clair est affiche")
    verifier(all(titre in textes for _c, _a, titre, _m in classements.TABLEAUX)
             and all(str(scores[c]) in textes for c, _a, _t, _m in classements.TABLEAUX),
             "itch : tes records restent visibles (%s)" % scores)
    lus = []
    e.mes_scores = lambda: lus.append(1) or scores
    e._scores = None
    for _ in range(5):
        e.draw()
    verifier(len(lus) == 1, "les records sont lus une fois, pas a chaque image")
    e.handle_event(touche(pygame.K_r))
    e.handle_event(touche(pygame.K_RIGHT))
    verifier(faux.demarrages == 0 and e.tableau == "problemes", "itch : R et flèches ne font rien")
    e._placer(pygame.display.set_mode((800, 600), pygame.RESIZABLE))
    e.draw()
    e._placer(pygame.display.set_mode((1920, 1080), pygame.RESIZABLE))
    e.draw()
    verifier(True, "itch : dessin en 800x600 et 1920x1080 sans planter")
    ecran = pygame.display.set_mode((1024, 640), pygame.RESIZABLE)
    e._placer(ecran)
    pygame.event.clear()
    pygame.event.post(touche(pygame.K_ESCAPE))
    verifier(e.run(horloge) == "retour", "itch : l'ecran s'ouvre et se ferme sans planter (run)")

    for nom in ("amis", "steam"):
        distribution.fixer(nom)
        faux = FauxSteam()
        e = ecran_classements.EcranClassements(ecran, {}, steam=faux, gestionnaire=classements.Classements(faux))
        del textes[:]
        e.draw()
        verifier(faux.demarrages == 1 and len(e.boutons) > 1 and "Classements Steam" in textes,
                 "%s : comme avant (Steam essaye, tous les boutons, « Classements Steam »)" % nom)
        pygame.event.clear()
        pygame.event.post(touche(pygame.K_ESCAPE))
        verifier(e.run(horloge) == "retour", "%s : l'ecran s'ouvre et se ferme sans planter" % nom)
finally:
    ui.texte, ui.paragraphe = vrai_texte, vrai_paragraphe

# ------------------------------------------------------------------ 6
print("6. Menu principal")
for nom, attendu in (("amis", "Jouer en ligne (Steam)"), ("steam", "Jouer en ligne (Steam)"),
                     ("itch", "Jouer en ligne")):
    distribution.fixer(nom)
    menu = MainMenu(ecran, "test")
    bouton = [b for b in menu.boutons if b.cle == "en_ligne"][0]
    verifier(bouton.libelle == attendu and bouton.actif,
             "%s : bouton « %s » (actif)" % (nom, bouton.libelle))
    deux = [b for b in menu.boutons if b.cle == "hotseat"]
    verifier(deux and deux[0].actif, "%s : « Jouer à deux sur ce PC » toujours là" % nom)

# ------------------------------------------------------------------ 7
print("7. Textes en anglais")
for phrase in (module_steam.MESSAGE_SANS_STEAM, salon_en_ligne.SANS_STEAM_TITRE,
               salon_en_ligne.SANS_STEAM_TEXTE, ecran_classements.SANS_STEAM_TITRE,
               ecran_classements.SANS_STEAM_TEXTE, "Classements", "Jouer en ligne"):
    verifier(phrase in langue_en.EN and langue_en.EN[phrase].strip(), "anglais : « %s »" % phrase[:50])
verifier("« Jouer à deux sur ce PC »" in salon_en_ligne.SANS_STEAM_TEXTE
         and "gardés" in ecran_classements.SANS_STEAM_TEXTE, "textes francais avec accents")

# 31/10 (testeur) : la version itch ne demande jamais les droits de Windows
# pour le pare-feu au premier lancement (ni Steam ni mise a jour automatique).
import pare_feu
appels = []
vrai_frozen, vrai_plateforme = getattr(sys, "frozen", None), sys.platform
vrai_regle = getattr(pare_feu, "_lire_etat", None)
try:
    sys.frozen, sys.platform = True, "win32"
    pare_feu._lire_etat = lambda *a, **k: appels.append("pare-feu") or {}
    os.environ.pop("SICKCHESS_SANS_PARE_FEU", None)
    distribution.fixer(distribution.ITCH)
    verifier(pare_feu.au_demarrage(dossier=TEMP, exe=os.path.join(TEMP, "SickChess.exe")) == "itch"
             and not appels, "itch : pas de règle de pare-feu (pas de demande de droits)")
finally:
    sys.platform = vrai_plateforme
    if vrai_frozen is None:
        del sys.frozen
    else:
        sys.frozen = vrai_frozen
    if vrai_regle is not None:
        pare_feu._lire_etat = vrai_regle

distribution.fixer(None)
shutil.rmtree(TEMP, ignore_errors=True)
print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
