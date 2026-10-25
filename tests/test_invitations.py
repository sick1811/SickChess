# tests/test_invitations.py - l'invitation d'un ami Steam affichee dans le jeu
# (24/10, travail p36).
#     python tests/test_invitations.py
# Sans Steam : un faux Steam apporte les invitations. Bandeau au menu, dans un
# autre ecran, en pleine partie (confirmation, partie gardee), « Plus tard »,
# liste dans « Jouer en ligne ». Dossier temporaire : tes donnees ne sont pas touchees.

import os as _os_envoi
_os_envoi.environ["SICKCHESS_SANS_ENVOI"] = "1"   # 25/10 : jamais de faux message dans le vrai salon Discord
import ctypes
import os
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((1024, 640))

import asset_manager
TEMP = tempfile.mkdtemp(prefix="sickchess_invit_")
asset_manager.dossier_ecriture = lambda: TEMP
import sauvegarde
sauvegarde.FICHIER = os.path.join(TEMP, "partie_en_cours.json")

import invitations
import partie_en_ligne
import steam as module_steam
import ui

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def clic(pos):
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos))


def touche(cle):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=cle, mod=0, unicode=""))


class FauxSteam:
    actif = True
    appid = 480

    def __init__(self):
        self._ev = []

    def pomper(self):
        pass

    def evenements(self, *types):
        pris = [e for e in self._ev if e["type"] in types]
        self._ev = [e for e in self._ev if e["type"] not in types]
        return pris

    def nom_de(self, ami):
        return {7: "Paul", 8: "Léa"}.get(ami, "")

    def inviter_moi(self, ami, salon):
        self._ev.append({"type": "invitation_recue", "ami": ami, "salon": salon})


print("1. Steam : l'invitation recue est lue (LobbyInvite_t)")
s = module_steam.Steam(TEMP)
s.appid = 480
for jeu, attendu in ((480, True), (730, False), (0, True)):
    brut = module_steam.InvitationRecue(ami=7, salon=111, jeu=jeu)
    s._lire(module_steam.CB_INVITATION_RECUE, ctypes.addressof(brut), ctypes.sizeof(brut))
    ev = s.evenements("invitation_recue")
    verifier(bool(ev) == attendu and (not ev or (ev[0]["ami"], ev[0]["salon"]) == (7, 111)),
             "invitation pour le jeu %d : %s" % (jeu, "gardee" if attendu else "ignoree"))

print("2. La liste des invitations")
faux = FauxSteam()
invitations.vider()
faux.inviter_moi(7, 1001)
faux.inviter_moi(8, 1002)
faux.inviter_moi(7, 1001)
nouvelles = invitations.recevoir(faux, maintenant=100.0)
verifier([i["nom"] for i in nouvelles] == ["Paul", "Léa", "Paul"], "noms des amis lus dans Steam")
verifier([i["salon"] for i in invitations.en_attente(100.0)] == [1001, 1002],
         "la plus recente d'abord, sans doublon")
verifier(invitations.depuis_quand(invitations.en_attente(100.0)[0], 100.0 + 190) == "il y a 3 min",
         "« il y a 3 min »")
verifier(invitations.en_attente(100.0 + invitations.DUREE_DE_VIE_S + 1) == [],
         "au bout de 10 minutes, l'invitation n'est plus proposee")

print("3. Le bandeau, dans le vrai jeu")
from game_manager import GameManager
gm = GameManager("test")
gm.bandeau.steam = faux
ecran = gm.screen


def image():
    """Une image du jeu : les evenements passent par le bandeau, puis on affiche."""
    restants = ui.evenements()
    ui.afficher()
    return restants


invitations.vider()
partie_en_ligne._INVITATION["salon"] = 0
gm.au_menu = True
faux.inviter_moi(7, 2001)
gm.bandeau._pompe_le = 0
image()
verifier(gm.bandeau._rect is not None, "« Paul t'invite à jouer » s'affiche en haut")
verifier(gm.bandeau._rect.top < 30 and gm.bandeau._rect.right <= ecran.get_width(),
         "le bandeau tient dans la fenetre, en haut")
rejoindre = gm.bandeau._boutons["rejoindre"].rect.center
pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(5, 600)))
verifier(len(image()) == 1, "un clic ailleurs va a l'ecran")
clic(rejoindre)
restants = image()
verifier(partie_en_ligne._INVITATION["salon"] == 2001 and not restants,
         "au menu, Rejoindre : le menu va au salon de Paul (clic pris par le bandeau)")
verifier(invitations.en_attente() == [], "l'invitation acceptee quitte la liste")
partie_en_ligne._INVITATION["salon"] = 0

print("4. Plus tard, et le bandeau qui se range tout seul")
faux.inviter_moi(8, 2002)
gm.bandeau._pompe_le = 0
image()
clic(gm.bandeau._boutons["plus_tard"].rect.center)
image()
verifier(gm.bandeau.affichee() is None and len(invitations.en_attente()) == 1,
         "Plus tard : le bandeau part, l'invitation reste dans la liste")
invitations.ajouter(3003, "Marc", maintenant=0.0)
verifier(gm.bandeau.affichee(maintenant=invitations.BANDEAU_S + 1) is None,
         "apres 45 s sans reponse, le bandeau se range")

print("5. Depuis un autre ecran : retour au menu, puis salon")
gm.au_menu = False
invitations.vider()
invitations.ajouter(4004, "Paul")
image()
clic(gm.bandeau._boutons["rejoindre"].rect.center)
try:
    image()
    leve = False
except invitations.RetourAuMenu:
    leve = True
verifier(leve and partie_en_ligne._INVITATION["salon"] == 4004,
         "Rejoindre dans un ecran : l'ecran se ferme (retour au menu) et le salon est retenu")
verifier(not issubclass(invitations.RetourAuMenu, Exception),
         "les « except Exception » des ecrans ne l'arretent pas")
partie_en_ligne._INVITATION["salon"] = 0

print("6. En pleine partie : confirmation, partie gardee")
import chess
gm.game_mode = "hotseat"
gm.reglages = {"minutes": 5, "increment": 0, "pendule_active": True, "retourner_plateau": False}
gm.preparer_partie()
for u in ("e2e4", "e7e5", "g1f3"):
    gm.board.make_move(chess.Move.from_uci(u))
gm.en_partie = True
sauvegarde.effacer()
invitations.ajouter(5005, "Léa")
image()
clic(gm.bandeau._boutons["rejoindre"].rect.center)
image()
verifier(gm.bandeau.confirmation is not None and "confirmer" in gm.bandeau._boutons,
         "une fenetre demande « Rejoindre Léa ? »")
verifier(not gm.board.timer.active, "la pendule est arretee pendant la question")
touche(pygame.K_a)
verifier(image() == [], "pendant la question, le clavier ne va pas a la partie")
clic(gm.bandeau._boutons["rester"].rect.center)
image()
verifier(gm.bandeau.confirmation is None and not sauvegarde.existe()
         and partie_en_ligne._INVITATION["salon"] == 0, "Rester : on continue la partie")
verifier(gm.board.timer.active, "la pendule repart")
invitations.ajouter(5006, "Léa")
image()
clic(gm.bandeau._boutons["rejoindre"].rect.center)
image()
clic(gm.bandeau._boutons["confirmer"].rect.center)
try:
    image()
    leve = False
except invitations.RetourAuMenu:
    leve = True
verifier(leve and partie_en_ligne._INVITATION["salon"] == 5006, "Rejoindre : retour au menu, salon retenu")
verifier(sauvegarde.lire() is not None, "la partie est gardee (Reprendre la partie)")
partie_en_ligne._INVITATION["salon"] = 0
gm.en_partie = False
gm.cleanup_game()

print("7. Pas de bandeau dans le jeu en ligne")
gm.en_ligne = True
invitations.ajouter(6006, "Paul")
image()
verifier(gm.bandeau._rect is None, "en ligne : pas de bandeau")
pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(ecran.get_width() // 2, 30)))
verifier(len(image()) == 1, "en ligne : les clics vont au salon")
gm.en_ligne = False

print("8. « Jouer en ligne » : liste des invitations recues")
from salon_en_ligne import SalonEnLigne


class SteamSalon(FauxSteam):
    def __init__(self):
        super().__init__()
        self.rejoints = []

    def demarrer(self):
        return True

    def rejoindre_salon(self, salon):
        self.rejoints.append(salon)
        return True


steam_salon = SteamSalon()
gm.en_ligne = True
salon = SalonEnLigne(ecran, gm.clock, None, "Moi", steam=steam_salon)
salon.draw()
verifier("invitation:6006" in salon._boutons, "l'invitation de Paul est listee avec « Rejoindre »")
salon._clic("invitation:6006")
verifier(steam_salon.rejoints == [6006] and salon.etape == "attente_steam"
         and all(i["salon"] != 6006 for i in invitations.en_attente()),
         "Rejoindre : connexion au salon de Paul, l'invitation quitte la liste")
salon_test = SalonEnLigne(ecran, gm.clock, None, "Moi", steam=SteamSalon())
salon_test._clic("test_invitation")
verifier(invitations.en_attente()[0]["nom"] == "Ami de test" and "menu" in salon_test.info,
         "« Test : invitation » : une fausse invitation pour voir le bandeau")
gm.en_ligne = False

print("9. Le menu et la partie rattrapent le retour au menu")


class Fin(BaseException):
    pass


ouvert = []
invitations.vider()


def faux_signaler():
    partie_en_ligne.demander_a_rejoindre(7007)
    raise invitations.RetourAuMenu()


def faux_en_ligne():
    ouvert.append(partie_en_ligne._prendre_invitation())
    raise Fin()


gm.ouvrir_signaler = faux_signaler
gm.ouvrir_en_ligne = faux_en_ligne
gm.menu.redimensionner(*ecran.get_size())
bouton = next(b for b in gm.menu.boutons if b.cle == "signaler")
clic(bouton.rect.center)
try:
    gm.show_menu()
except Fin:
    pass
verifier(ouvert == [7007], "depuis un ecran du menu : retour au menu puis salon de l'ami")
verifier(gm.au_menu is not None, "le menu se redessine sans erreur")

etapes = []


def faux_menu():
    etapes.append("menu")
    if len(etapes) == 1:
        raise invitations.RetourAuMenu()
    raise Fin()


gm.show_menu = faux_menu
gm._premier_lancement = lambda: None
try:
    gm.run()
except Fin:
    pass
verifier(etapes == ["menu", "menu"] and not gm.en_partie, "run() rattrape le retour au menu et repart")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
ui.retirer_crochet(gm.bandeau)
pygame.quit()
sys.exit(1 if echecs else 0)
