# tests/test_classements.py - classements Steam et succes prepares (24/10, travail p37).
#     python tests/test_classements.py
# Sans Steam : un faux Steam repond comme le vrai (appels, puis reponses dans
# evenements()). Dossier temporaire : tes records et ton profil ne sont pas touches.

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
ecran = pygame.display.set_mode((1024, 640))

import asset_manager
TEMP = tempfile.mkdtemp(prefix="sickchess_classements_")
asset_manager.dossier_ecriture = lambda: TEMP

import classements
import modes_problemes
import puzzles
import steam as module_steam
import succes

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


class FauxSteam:
    """Les classements de Steam, en memoire : chaque appel rend un numero, la
    reponse arrive au pomper() suivant (comme le vrai)."""

    def __init__(self, moi=1, appid=480):
        self.actif = True
        self.erreur = self.conseil = ""
        self.appid = appid
        self.moi = moi
        self.tableaux = {}          # nom -> {joueur: score}
        self.poignees = {}          # poignee -> nom
        self._ev, self._a_repondre = [], []
        self._appel = 100
        self.succes_envoyes = []
        self.ranges = 0
        self.repond = True

    def demarrer(self):
        return True

    def pomper(self):
        pass

    def _nouvel_appel(self, ev):
        self._appel += 1
        ev["appel"] = self._appel
        self._a_repondre.append(ev)
        return self._appel

    def evenements(self, *types):
        if self.repond:
            self._ev += self._a_repondre
            self._a_repondre = []
        pris = [e for e in self._ev if e["type"] in types]
        self._ev = [e for e in self._ev if e["type"] not in types]
        return pris

    def chercher_classement(self, nom):
        poignee = 5000 + len(self.poignees) if nom not in self.poignees.values() else \
            next(p for p, n in self.poignees.items() if n == nom)
        self.poignees[poignee] = nom
        self.tableaux.setdefault(nom, {})
        return self._nouvel_appel({"type": "classement_trouve", "ok": True, "classement": poignee})

    def envoyer_score(self, poignee, score, methode):
        t = self.tableaux[self.poignees[poignee]]
        if methode == 2 or score > t.get(self.moi, -1):
            t[self.moi] = score
        rang = sorted(t.values(), reverse=True).index(t[self.moi]) + 1
        return self._nouvel_appel({"type": "score_envoye", "ok": True, "score": t[self.moi],
                                   "rang": rang, "rang_avant": 0})

    def telecharger_classement(self, poignee, demande, debut, fin):
        t = self.tableaux[self.poignees[poignee]]
        tries = sorted(t.items(), key=lambda kv: -kv[1])
        lignes = [{"rang": i + 1, "joueur": j, "score": s} for i, (j, s) in enumerate(tries)]
        if demande == 2:
            lignes = [l for l in lignes if l["joueur"] in (self.moi, 2)]
        elif demande == 1:
            mon_rang = next((l["rang"] for l in lignes if l["joueur"] == self.moi), 1)
            lignes = [l for l in lignes if mon_rang + debut <= l["rang"] <= mon_rang + fin]
        else:
            lignes = lignes[debut - 1:fin]
        return self._nouvel_appel({"type": "classement_telecharge", "lignes": lignes})

    def mon_id(self):
        return self.moi

    def nom_de(self, joueur):
        return {1: "Julien", 2: "Paul"}.get(joueur, "")

    def demander_le_nom(self, joueur):
        return False

    def succes_possibles(self):
        return self.appid != module_steam.APPID_DE_TEST

    def debloquer_succes(self, nom, enregistrer=True):
        self.succes_envoyes.append(nom)
        return True

    def ranger_les_succes(self):
        self.ranges += 1
        return True


def suivre_jusqu_a(c, condition, tours=10):
    for _ in range(tours):
        c.suivre()
        if condition():
            return True
    return False


print("1. Steam : les reponses des classements sont lues")
s = module_steam.Steam(TEMP)
for numero, structure, attendu in (
        (module_steam.CB_CLASSEMENT_TROUVE, module_steam.ClassementTrouve(classement=77, trouve=1),
         {"type": "classement_trouve", "ok": True, "classement": 77}),
        (module_steam.CB_SCORE_ENVOYE, module_steam.ScoreEnvoye(reussi=1, classement=77, score=1432,
                                                                change=1, rang=12, rang_avant=40),
         {"type": "score_envoye", "ok": True, "score": 1432, "rang": 12})):
    s._appel_courant = 9
    s._lire(numero, ctypes.addressof(structure), ctypes.sizeof(structure))
    ev = s.evenements(attendu["type"])
    verifier(ev and all(ev[0].get(k) == v for k, v in attendu.items()) and ev[0]["appel"] == 9,
             "%s : %s" % (attendu["type"], ev[0] if ev else "rien"))
verifier(ctypes.sizeof(module_steam.LigneDeClassement) == 32, "ligne de classement : 32 octets (SDK)")
verifier(s.chercher_classement("X") == 0 and s.envoyer_score(1, 5) == 0,
         "sans Steam : aucun appel, aucune erreur")

print("2. Envoyer un score et telecharger un classement")
faux = FauxSteam()
faux.tableaux["SICKCHESS_CONTRE_LA_MONTRE"] = {2: 18, 3: 9}
c = classements.Classements(faux)
c.envoyer("chrono", 12)
c.envoyer("chrono", 7)                      # moins bien : on garde 12
verifier(suivre_jusqu_a(c, lambda: faux.tableaux["SICKCHESS_CONTRE_LA_MONTRE"].get(1) == 12),
         "record de contre la montre envoye (12, pas 7)")
verifier(c.derniers_envois.get("chrono", {}).get("rang") == 2, "Steam rend le rang (2e)")
c.demander("chrono", "mondial")
verifier(suivre_jusqu_a(c, lambda: c.resultat("chrono", "mondial")["etat"] == "pret"),
         "classement mondial telecharge")
lignes = c.resultat("chrono", "mondial")["lignes"]
verifier([(l["rang"], l["score"], l["moi"]) for l in lignes] == [(1, 18, False), (2, 12, True), (3, 9, False)],
         "Paul 18, toi 12 (ta ligne marquee), 9")
c.demander("chrono", "amis")
suivre_jusqu_a(c, lambda: c.resultat("chrono", "amis")["etat"] == "pret")
verifier([l["joueur"] for l in c.resultat("chrono", "amis")["lignes"]] == [2, 1], "vue Amis")
c.demander("chrono", "autour")
suivre_jusqu_a(c, lambda: c.resultat("chrono", "autour")["etat"] == "pret")
verifier(any(l["moi"] for l in c.resultat("chrono", "autour")["lignes"]), "vue Autour de moi")
c.envoyer("problemes", 1500)
c.envoyer("problemes", 1450)                # le classement des problemes peut baisser
suivre_jusqu_a(c, lambda: faux.tableaux.get("SICKCHESS_PROBLEMES", {}).get(1) == 1450)
verifier(faux.tableaux["SICKCHESS_PROBLEMES"].get(1) == 1450,
         "classement des problemes : la valeur du jour remplace l'ancienne")
faux.repond = False
c.demander("survie", "mondial")
c.suivre()
r = c.resultat("survie", "mondial")
r["quand"] -= classements.DELAI_S + 1
verifier(c.resultat("survie", "mondial")["etat"] == "erreur", "Steam muet : erreur au bout de 15 s")
faux.repond = True

print("3. Les problemes envoient leurs scores")
inst = classements.instance()
inst.a_envoyer.clear()
session = puzzles.Session(puzzles.MODE_CLASSE)
puzzle = {"id": "t1", "classement": 1500, "fen": "8/8/8/8/8/8/8/8 w - - 0 1", "coups": []}
session.noter_un_puzzle(puzzle, True, secondes=10)
verifier(inst.a_envoyer.get("problemes") == session.classement(),
         "un probleme classe : classement mis de cote pour Steam (%s)" % inst.a_envoyer.get("problemes"))
t = [0.0]
defi = modes_problemes.SessionDefi("chrono", maintenant=lambda: t[0])
defi.demarrer()
for _ in range(4):
    defi.noter_un_puzzle({"id": "x", "classement": 1200}, True)
t[0] = modes_problemes.DUREE_CHRONO + 1
defi.terminee()
verifier(inst.a_envoyer.get("chrono") == 4, "fin de contre la montre : 4 mis de cote")
verifier(modes_problemes.record("chrono") == 4, "record local garde aussi (sans Steam)")

print("4. Rattrapage a la connexion a Steam")
faux2 = FauxSteam(appid=480)
classements._INSTANCE[:] = [classements.Classements(faux2)]
classements.rattraper(faux2)
inst2 = classements.instance()
verifier(suivre_jusqu_a(inst2, lambda: faux2.tableaux.get("SICKCHESS_CONTRE_LA_MONTRE", {}).get(1) == 4
                       and faux2.tableaux.get("SICKCHESS_PROBLEMES", {}).get(1) == session.classement()),
         "record et classement faits sans Steam : envoyes a la connexion")
verifier(not inst2.a_envoyer, "plus rien en attente")
succes.debloquer("premiere_victoire", steam=faux2)
succes.debloquer("importer", steam=faux2)
faux2.succes_envoyes.clear()
verifier(succes.rattraper(faux2) == 0 and not faux2.succes_envoyes,
         "numero de test 480 : les succes restent dans le jeu")
vrai = FauxSteam(appid=3412345)
verifier(succes.rattraper(vrai) == 2 and sorted(vrai.succes_envoyes) == ["IMPORTER", "PREMIERE_VICTOIRE"]
         and vrai.ranges == 1, "vrai numero : les succes deja gagnes partent tous, en une fois")
s480 = module_steam.Steam(TEMP)
s480.actif, s480._i, s480.appid = True, {"stats": 1}, 480
verifier(not s480.succes_possibles(), "Steam : pas de succes avec 480")
s480.appid = 3412345
verifier(s480.succes_possibles(), "Steam : succes possibles avec le vrai numero")
s480.actif = False

print("5. Succes : icones et notice prets pour Steamworks")
noms = [api for _c, api, _t, _d in succes.SUCCES]
dossier = os.path.join("docs", "steam_succes")
verifier(all(os.path.exists(os.path.join(dossier, n + ".jpg"))
             and os.path.exists(os.path.join(dossier, n + "_gris.jpg")) for n in noms),
         "une icone debloquee + une grise par succes (%d)" % len(noms))
with open(os.path.join("docs", "SUCCES_STEAM.md"), encoding="utf-8") as f:
    notice = f.read()
verifier(all(n in notice for n in noms) and all(t[1] in notice for t in classements.TABLEAUX),
         "docs/SUCCES_STEAM.md cite tous les succes et les 3 classements")

print("6. L'ecran des classements")
from ecran_classements import EcranClassements
faux3 = FauxSteam()
faux3.tableaux["SICKCHESS_PROBLEMES"] = {2: 1720, 1: 1450}
gestion = classements.Classements(faux3)
e = EcranClassements(ecran, {}, steam=faux3, gestionnaire=gestion)
for _ in range(5):
    e.draw()
r = gestion.resultat("problemes", "mondial")
verifier(r["etat"] == "pret" and len(r["lignes"]) == 2, "ouverture : classement mondial des problemes")
verifier(e._nom(2) == "Paul", "noms Steam des joueurs")
e.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT, mod=0, unicode=""))
verifier(e.tableau == "chrono", "fleche droite : Contre la montre")
pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=e.btns_vues[1].rect.center))
for ev in pygame.event.get():
    e.handle_event(ev)
verifier(e.vue == "amis", "clic : vue Amis")
for _ in range(3):
    e.draw()
verifier(gestion.resultat("chrono", "amis")["etat"] == "pret", "la vue demandee se charge")
verifier(e.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0,
                                           unicode="")) == "retour", "Echap : retour")
sans = FauxSteam()
sans.actif, sans.erreur = False, "Steam n'est pas lancé."
sans.demarrer = lambda: False
e2 = EcranClassements(ecran, {}, steam=sans, gestionnaire=classements.Classements(sans))
e2.draw()
verifier(e2.mes_scores()["chrono"] == 4 and not e2.btn_actualiser.actif,
         "sans Steam : message, et tes scores gardes dans le jeu")

print("7. Le bouton dans les Problemes")
if puzzles.disponible():
    from ecran_problemes import EcranProblemes
    pb = EcranProblemes(ecran, {})
    pb.draw()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                         pos=pb.btn_classements.rect.center))
    reponses = [pb.handle_event(ev) for ev in pygame.event.get()]
    verifier("classements" in reponses, "« Classements Steam » ouvre les classements")
    verifier(not pb.btn_classements.rect.colliderect(pb.btn_retour_choix.rect)
             and pb.btn_classements.rect.bottom <= ecran.get_height(),
             "a cote de Retour, sans chevauchement")
else:
    print("      (base des problemes absente : bouton non verifie)")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
