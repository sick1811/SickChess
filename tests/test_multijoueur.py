# tests/test_multijoueur.py - verifie le multijoueur sans ouvrir de fenetre
# et sans Steam.
#     python tests/test_multijoueur.py
#
# 1. Deux joueurs relies par TransportLocal (TCP sur ce PC) : poignee de main,
#    coups, premouvement, chat, abandon, revanche (couleurs inversees, messages
#    de l'ancienne partie ignores), pendule, message perdu rattrape, depart et
#    coupure de l'adversaire.
# 2. Le salon Steam, avec un FAUX Steam (memes fonctions que steam.py) : creer,
#    rejoindre avec le code, recevoir les reglages, lancer la partie.
# 3. steam.py : codes de salon, ligne de commande, tailles des structures.

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import time

import chess
import pygame

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
ecran = pygame.display.set_mode((1024, 640))

import reseau_transport
import salon_en_ligne
import steam as module_steam
from board import ChessBoard
from mode_en_ligne import ModeEnLigne
from reseau_transport import TransportLocal, TransportSteam
from partie_en_ligne import EcranFinEnLigne

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


class Horloge:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


PORT = 5600 + os.getpid() % 300


def paire(horloge, port):
    a = TransportLocal(True, "Julien", port=port, horloge=horloge)
    b = TransportLocal(False, "Paul", port=port, horloge=horloge)
    for _ in range(200):
        a.recevoir()
        b.recevoir()
        horloge.t += 0.05
        time.sleep(0.002)
        if a.connecte() and b.connecte():
            break
    return a, b


def deux_parties(a, b, horloge, numero=1, couleur_a="blanc"):
    pa = ChessBoard(ecran, {"minutes": 5, "increment": 0, "pendule_active": True})
    pb = ChessBoard(ecran, {"minutes": 5, "increment": 0, "pendule_active": True})
    ma = ModeEnLigne(pa, a, couleur_a, "Julien", horloge=horloge, numero=numero)
    mb = ModeEnLigne(pb, b, "noir" if couleur_a == "blanc" else "blanc", "Paul",
                     horloge=horloge, numero=numero)
    return pa, pb, ma, mb


def tourner(ma, mb, horloge, fois=20, pas=0.05):
    for _ in range(fois):
        ma.update()
        ma.board.update()
        mb.update()
        mb.board.update()
        horloge.t += pas
        time.sleep(0.002)          # le temps reel d'une image, a peu pres


def jouer(plateau, uci):
    return plateau.make_move(chess.Move.from_uci(uci))


print("1. Connexion")
h = Horloge()
a, b = paire(h, PORT)
verifier(a.connecte() and b.connecte(), "les deux transports se connectent")
verifier(a.nom_adverse == "Paul" and b.nom_adverse == "Julien",
         "chacun connait le nom de l'autre (%r / %r)" % (a.nom_adverse, b.nom_adverse))

print("2. Coups")
pa, pb, ma, mb = deux_parties(a, b, h)
verifier(pa.couleur_joueur == chess.WHITE and pb.couleur_joueur == chess.BLACK,
         "couleurs : hote Blancs, invite Noirs")
verifier(pb.flipped and not pa.flipped, "le plateau de l'invite est retourne")
jouer(pa, "e2e4")
tourner(ma, mb, h)
verifier(pb.board.move_stack and pb.board.move_stack[-1].uci() == "e2e4",
         "e2e4 arrive chez l'adversaire")
# Premouvement de l'hote pendant que l'invite reflechit
pa.definir_premouvement(chess.Move.from_uci("g1f3"))
jouer(pb, "e7e5")
tourner(ma, mb, h)
verifier([m.uci() for m in pa.board.move_stack] == ["e2e4", "e7e5", "g1f3"],
         "le premouvement part et arrive")
verifier([m.uci() for m in pb.board.move_stack] == ["e2e4", "e7e5", "g1f3"],
         "les deux plateaux sont identiques")
# Le joueur ne peut pas jouer les pieces de l'autre
jouer(pb, "b8c6")
tourner(ma, mb, h)
verifier(pa.cest_mon_tour() and not pb.cest_mon_tour(), "chacun ne joue que son camp")

print("3. Message perdu")
original = a._envoyer_octets
perdus = []
a._envoyer_octets = lambda octets: (perdus.append(octets) or True) \
    if b'"coups"' in octets else original(octets)
jouer(pa, "f1b5")
tourner(ma, mb, h, 4)
a._envoyer_octets = original
verifier(len(pb.board.move_stack) == 4 and perdus, "le coup de l'hote s'est perdu")
tourner(ma, mb, h, 120, 0.05)
verifier([m.uci() for m in pb.board.move_stack][-1:] == ["f1b5"],
         "rattrape tout seul grace au message d'etat")

print("4. Chat")
ma.envoyer_chat("Bien joue !")
tourner(ma, mb, h, 5)
verifier(pb.chat.messages and pb.chat.messages[-1]["texte"] == "Bien joue !",
         "le message de chat arrive")

print("5. Pendules")
pa.timer.time_left[chess.WHITE] = 200.0
ma._envoyer(ma.arbitre.paquet())
tourner(ma, mb, h, 5)
verifier(abs(pb.timer.time_left[chess.WHITE] - 200.0) < 0.5,
         "la pendule adverse est recalee sur ce que l'autre annonce")

print("6. Abandon")
pb.game_buttons._abandonner()
mb.abandonner()
tourner(ma, mb, h, 5)
verifier(pa.game_over and pa.result == "1-0", "l'abandon des Noirs : 1-0 chez l'hote")
verifier(pb.result == "1-0", "meme resultat chez l'invite")
fin = EcranFinEnLigne(pa, ma)
verifier(fin.titre() == "Victoire !", "l'hote voit Victoire")
verifier(EcranFinEnLigne(pb, mb).titre() == "Défaite", "l'invité voit Défaite")

print("7. Revanche")
ma.demander_revanche()
tourner(ma, mb, h, 5)
verifier(mb.revanche.a_repondre(), "l'invite voit la demande")
mb.demander_revanche()          # cliquer REVANCHE vaut accepter
tourner(ma, mb, h, 5)
verifier(ma.revanche_acceptee() and mb.revanche_acceptee(), "revanche acceptee des deux cotes")
verifier(ma.couleur_revanche() == "noir" and mb.couleur_revanche() == "blanc",
         "les couleurs s'inversent")
# L'invite demarre la nouvelle partie AVANT que l'hote ait quitte l'ancienne :
# un message 'etat' de l'ancienne partie ne doit pas y injecter des coups.
pb2 = ChessBoard(ecran, {"minutes": 5, "increment": 0})
mb2 = ModeEnLigne(pb2, b, "blanc", "Paul", horloge=h, numero=2)
for _ in range(20):
    mb2.update()
    ma.update()            # l'hote est encore sur l'ancienne partie
    h.t += 0.2
    time.sleep(0.002)
verifier(len(pb2.board.move_stack) == 0, "aucun coup de l'ancienne partie ne passe")
pa2 = ChessBoard(ecran, {"minutes": 5, "increment": 0})
ma2 = ModeEnLigne(pa2, a, "noir", "Julien", horloge=h, numero=2)
jouer(pb2, "d2d4")
tourner(ma2, mb2, h)
verifier([m.uci() for m in pa2.board.move_stack] == ["d2d4"],
         "la revanche se joue normalement")

print("8. Temps ecoule")
pb2.timer.time_left[chess.WHITE] = 0.01       # les Blancs (invite) n'ont plus de temps
jouer(pa2, "d7d5")
h.t += 1
tourner(ma2, mb2, h, 30, 0.05)
verifier(pb2.game_over and pa2.game_over and pa2.result == "0-1",
         "perte au temps annoncee par son proprietaire, meme resultat des deux cotes")

print("9. Depart et coupure")
pa3, pb3, ma3, mb3 = deux_parties(a, b, h, numero=3)
b.fermer()
tourner(ma3, mb3, h, 10)
verifier(pa3.game_over and pa3.result == "1-0", "l'adversaire quitte : victoire")
verifier(ma3.revanche.etat == "impossible", "plus de revanche possible")
a.fermer()

h2 = Horloge()
c, d = paire(h2, PORT + 1)
pc, pd, mc, md = deux_parties(c, d, h2)
d._envoyer_octets = lambda octets: True        # d se tait (cable coupe)
d._lire_octets = lambda: []
for _ in range(14):
    mc.update()
    h2.t += 1.0
    time.sleep(0.002)
verifier(c.perdu() and not pc.game_over and "Connexion perdue" in (mc.message_actif() or ""),
         "silence de 12 s : connexion perdue, on attend")
for _ in range(70):
    mc.update()
    h2.t += 1.0
verifier(pc.game_over and pc.result == "1/2-1/2", "apres 60 s : partie interrompue")
c.fermer()
d.fermer()


# ======================================================================= Steam
print("10. Codes Steam")
for salon in (109775241234567890, 1, 2 ** 64 - 1):
    code = module_steam.code_depuis_salon(salon)
    verifier(module_steam.salon_depuis_code(code.lower().replace("-", " ")) == salon,
             "code %s <-> salon" % code)
verifier(module_steam.salon_depuis_code("") is None
         and module_steam.salon_depuis_code("ZZZZ-ZZZZ-ZZZZ-ZZ") is None, "code vide ou trop long refuse")
verifier(module_steam.salon_depuis_ligne_de_commande(
    ["+connect_lobby", "109775241234567890"]) == 109775241234567890,
    "lancement par une invitation Steam (+connect_lobby)")


class Nuage:
    """Le 'serveur Steam' partage par deux faux clients."""
    def __init__(self):
        self.salons = {}
        self.infos = {}
        self.boites = {}
        self.clients = {}
        self.prochain = 109775241000000001


class FauxSteam:
    def __init__(self, nuage, moi, nom):
        self.nuage, self.moi, self.nom = nuage, moi, nom
        self.actif = True
        self.erreur = self.conseil = ""
        self.appid = 480
        self._ev = []
        nuage.clients[moi] = self
        nuage.boites[moi] = []

    def demarrer(self): return True
    def pomper(self): pass

    def evenements(self, *types):
        pris = [e for e in self._ev if not types or e["type"] in types]
        self._ev = [e for e in self._ev if types and e["type"] not in types]
        return pris

    def mon_id(self): return self.moi
    def mon_nom(self): return self.nom
    def nom_de(self, j): return self.nuage.clients[j].nom
    def amis(self): return [{"id": j, "nom": c.nom, "en_ligne": True,
                             "sur_sickchess": True}
                            for j, c in self.nuage.clients.items() if j != self.moi]

    def creer_salon(self, places=2):
        salon = self.nuage.prochain
        self.nuage.prochain += 1
        self.nuage.salons[salon] = [self.moi]
        self.nuage.infos[salon] = {}
        self._ev.append({"type": "salon_cree", "ok": True, "salon": salon})
        return True

    def rejoindre_salon(self, salon):
        membres = self.nuage.salons.get(salon)
        if membres is None:
            self._ev.append({"type": "salon_entre", "ok": False, "reponse": 2,
                             "salon": salon})
            return True
        membres.append(self.moi)
        self._ev.append({"type": "salon_entre", "ok": True, "reponse": 1,
                         "salon": salon})
        for j in membres:
            if j != self.moi:
                self.nuage.clients[j]._ev.append({"type": "membre", "salon": salon,
                                                  "membre": self.moi, "entre": True,
                                                  "parti": False})
        return True

    def quitter_salon(self, salon):
        membres = self.nuage.salons.get(salon, [])
        if self.moi in membres:
            membres.remove(self.moi)
            for j in membres:
                self.nuage.clients[j]._ev.append({"type": "membre", "salon": salon,
                                                  "membre": self.moi, "entre": False,
                                                  "parti": True})

    def membres(self, salon): return list(self.nuage.salons.get(salon, []))
    def proprietaire(self, salon):
        m = self.nuage.salons.get(salon, [])
        return m[0] if m else 0
    def ecrire_info(self, salon, cle, valeur): self.nuage.infos[salon][cle] = str(valeur)
    def lire_info(self, salon, cle): return self.nuage.infos.get(salon, {}).get(cle, "")
    def fermer_salon(self, salon): pass
    def inviter(self, salon, ami): return True
    def ouvrir_fenetre_invitation(self, salon): pass
    def envoyer(self, joueur, octets):
        self.nuage.boites[joueur].append((self.moi, bytes(octets)))
        return True
    def recevoir(self):
        recus, self.nuage.boites[self.moi] = self.nuage.boites[self.moi], []
        return recus
    def accepter_session(self, j): pass
    def fermer_session(self, j): pass


def tick_salons(*salons, fois=30):
    for _ in range(fois):
        for s in salons:
            if s.resultat is None:
                s.update()
                s.draw()


print("11. Salon Steam (faux Steam)")
nuage = Nuage()
sj = FauxSteam(nuage, 1001, "Julien")
sp = FauxSteam(nuage, 1002, "Paul")
hote = salon_en_ligne.SalonEnLigne(ecran, None, None, "Julien", steam=sj)
hote.creer()
tick_salons(hote, fois=3)
verifier(hote.etape == "salon" and hote.salon, "l'hote a cree son salon")
verifier(sj.lire_info(hote.salon, "jeu") == "SickChess", "le salon est marque SickChess")
code = module_steam.code_depuis_salon(hote.salon)
invite = salon_en_ligne.SalonEnLigne(ecran, None, None, "Paul", steam=sp)
invite.champ_code.contenu = code
invite._clic("rejoindre")
tick_salons(hote, invite, fois=40)
verifier(hote.transport.connecte() and invite.transport.connecte(),
         "l'ami rejoint avec le code, les deux sont connectes")
verifier(hote.transport.hote and not invite.transport.hote, "qui est l'hote est clair")
verifier(hote.transport.nom_adverse == "Paul", "l'hote voit le nom Steam de l'ami")
hote._clic("cadence:3+2")
hote._clic("couleur:noir")
tick_salons(hote, invite, fois=10)
verifier(invite.reglages_hote and invite.reglages_hote["minutes"] == 3
         and invite.reglages_hote["couleur_hote"] == "noir",
         "l'invite voit les reglages de l'hote en direct")
hote._clic("lancer")
tick_salons(invite, fois=10)
verifier(hote.resultat and invite.resultat, "la partie demarre des deux cotes")
if hote.resultat and invite.resultat:
    rh, ri = hote.resultat[1], invite.resultat[1]
    verifier(rh["couleur_locale"] == "noir" and ri["couleur_locale"] == "blanc",
             "couleurs coherentes (hote Noirs, ami Blancs)")
    verifier(rh["minutes"] == ri["minutes"] == 3 and rh["increment"] == 2,
             "meme cadence des deux cotes (3 min + 2 s)")
    pygame.image.save(ecran, os.path.join("tests", "capture_salon.png"))

print("12. Code invalide / mauvais salon")
autre = FauxSteam(nuage, 1003, "Lea")
s3 = salon_en_ligne.SalonEnLigne(ecran, None, None, "Lea", steam=autre)
s3.rejoindre(42)
tick_salons(s3, fois=3)
verifier(s3.etape == "accueil" and "existe plus" in s3.erreur,
         "salon inexistant : message clair (%s)" % s3.erreur)

print("13. Captures d'ecran")
s4 = salon_en_ligne.SalonEnLigne(ecran, None, None, "Julien",
                                 steam=FauxSteam(Nuage(), 2001, "Julien"))
s4.draw()
pygame.image.save(ecran, os.path.join("tests", "capture_accueil_en_ligne.png"))
n2 = Nuage()
s5 = salon_en_ligne.SalonEnLigne(ecran, None, None, "Julien",
                                 steam=FauxSteam(n2, 3001, "Julien"))
for i, nom in enumerate(["Paul", "Lea", "Marc", "Sophie"]):
    FauxSteam(n2, 3002 + i, nom)
s5.creer()
tick_salons(s5, fois=3)
s5._amis_le = -999
s5.update()
s5.draw()
pygame.image.save(ecran, os.path.join("tests", "capture_salon_hote.png"))
pa.draw()
EcranFinEnLigne(pa, ma).draw(ecran)
pygame.image.save(ecran, os.path.join("tests", "capture_fin_en_ligne.png"))

print()
if echecs:
    print("%d ECHEC(S)" % len(echecs))
    sys.exit(1)
print("TOUT EST OK")
