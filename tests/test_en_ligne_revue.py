# tests/test_en_ligne_revue.py - en ligne : fin de partie et revue comme
# contre l'ordinateur (23/10). Deux joueurs relies sur ce PC (TransportLocal),
# sans Steam ni Stockfish : l'analyse est remplacee par une fausse, qui note
# ce qu'on lui demande. Les parties sont ecrites dans un dossier temporaire.

import os
import sys
import tempfile
import time
import types

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import pygame

pygame.init()
ecran = pygame.display.set_mode((1024, 640))

import asset_manager
TEMP = tempfile.mkdtemp(prefix="sickchess_revue_ligne_")
asset_manager.dossier_ecriture = lambda: TEMP

import analyse_partie
import game_manager
import partie_en_ligne
import statistiques
import succes
from board import ChessBoard
from mode_en_ligne import ModeEnLigne
from partie_en_ligne import EcranFinEnLigne
from reseau_transport import TransportLocal

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


# ------------------------------------------------ faux Stockfish, faux succes

class FausseAnalyse:
    toutes = []

    def __init__(self, fen, coups, chemin=None, puissance=None, suivi=False,
                 threads=None, fichier_cache=None, **_):
        self.coups = list(coups)
        self.suivi = suivi
        self.cache = fichier_cache
        self.erreur = None
        self.fini = False
        self.arretee = False
        self.suivi_fini = False
        self.precisions = (92.0, 60.0)
        FausseAnalyse.toutes.append(self)

    def demarrer(self): pass
    def nombre_de_coups(self): return len(self.coups)
    def ajouter_coups(self, coups): self.coups += list(coups)
    def finir_le_suivi(self): self.suivi_fini = True
    def definir_fichier_cache(self, chemin): self.cache = chemin
    def arreter(self, attendre=0.3): self.arretee = True
    def terminee(self): return self.fini
    def texte_avancement(self): return "Analyse en cours..."

    def rapport(self):
        return {"blancs": {"precision": self.precisions[0]},
                "noirs": {"precision": self.precisions[1]}}


analyse_partie.AnalyseurPartie = FausseAnalyse
succes_debloques, succes_verifies = [], []
succes.debloquer = lambda cle, steam=None: succes_debloques.append(cle)
succes.verifier = lambda conditions: succes_verifies.append(dict(conditions))


class FausseAide:
    def draw(self, *a, **k): pass


class FauxManager:
    """Juste ce que partie_en_ligne demande au vrai GameManager."""

    def __init__(self, board):
        self.board = board
        self.config = {"analyse_pendant_partie": True}
        self.stockfish_path = None
        self.game_mode = "menu"
        self.aide = FausseAide()
        self.revues = []
        G = game_manager.GameManager
        self.brancher_analyse = types.MethodType(G.brancher_analyse, self)
        self._suivre_analyse = types.MethodType(G._suivre_analyse, self)

    def ouvrir_revue(self, noms=None, cote_noir=False, apres_dessin=None):
        self.revues.append((noms, cote_noir, apres_dessin))


# ------------------------------------------------ deux joueurs

class Horloge:
    t = 1000.0
    def __call__(self):
        return self.t


h = Horloge()
PORT = 6050 + os.getpid() % 40
a = TransportLocal(True, "Julien", port=PORT, horloge=h)
b = TransportLocal(False, "Paul", port=PORT, horloge=h)
for _ in range(200):
    a.recevoir(); b.recevoir(); h.t += 0.05; time.sleep(0.002)
    if a.connecte() and b.connecte():
        break
verifier(a.connecte() and b.connecte(), "connexion")

pa = ChessBoard(ecran, {"minutes": 5, "pendule_active": True})
pb = ChessBoard(ecran, {"minutes": 5, "pendule_active": True})
ma = ModeEnLigne(pa, a, "blanc", "Julien", horloge=h)
mb = ModeEnLigne(pb, b, "noir", "Paul", horloge=h)
pa.end_screen = EcranFinEnLigne(pa, ma)
pb.end_screen = EcranFinEnLigne(pb, mb)
gma, gmb = FauxManager(pa), FauxManager(pb)


def image(fois=25):
    """Ce que fait la boucle de partie_en_ligne a chaque image, des deux cotes."""
    for _ in range(fois):
        for g, p, m in ((gma, pa, ma), (gmb, pb, mb)):
            if not getattr(g, "_figee", False):
                g._prochain_suivi = 0      # le vrai jeu attend 250 ms entre deux suivis
            m.update()
            p.update()
            partie_en_ligne.suivre_l_analyse(g, p, m)
        h.t += 0.05
        time.sleep(0.002)


def jouer(p, uci):
    p.make_move(chess.Move.from_uci(uci))
    image()


print("1. Analyse pendant la partie (en silence, comme contre l'ordinateur)")
jouer(pa, "f2f3")
direct_a = getattr(gma, "analyse_en_direct", None)
verifier(direct_a is not None and direct_a.suivi, "l'analyse en direct démarre chez Julien")
verifier(getattr(gmb, "analyse_en_direct", None) is not None, "et chez Paul (chacun la sienne)")
jouer(pb, "e7e5")
jouer(pa, "g2g4")
verifier(direct_a.nombre_de_coups() == 3, "elle suit les coups (%d)" % direct_a.nombre_de_coups())
gma._figee, gma._prochain_suivi = True, 10 ** 12   # le dernier coup arrive trop vite
jouer(pb, "d8h4")          # mat du lion

print("2. Fin de partie : PGN et analyse rangée à côté")
verifier(pa.game_over and pb.game_over, "mat vu des deux côtés")
for nom, m, p in (("Julien", ma, pa), ("Paul", mb, pb)):
    verifier(m.chemin_pgn and os.path.exists(m.chemin_pgn),
             "%s : partie écrite dans Mes parties" % nom)
    fin = p.end_screen
    attendu = os.path.splitext(m.chemin_pgn)[0] + ".analyse.json"
    verifier(fin.analyseur is not None and fin.analyseur.cache == attendu,
             "%s : analyse rangée à côté du PGN (revue, statistiques, Mes erreurs)" % nom)
verifier(pa.end_screen.analyseur is direct_a and direct_a.suivi_fini,
         "l'analyse faite pendant la partie est reprise (rien à recalculer)")
verifier(len(direct_a.coups) == 4, "avec le dernier coup (%d coups)" % len(direct_a.coups))
nb = len(FausseAnalyse.toutes)
image(10)
verifier(len(FausseAnalyse.toutes) == nb, "une seule fois : pas de nouvelle analyse ensuite")

print("3. Carte de fin")
verifier(pa.end_screen.titre() == "Défaite" and pb.end_screen.titre() == "Victoire !",
         "Défaite pour Julien, Victoire pour Paul")
pb.end_screen.draw(ecran)
fin = pb.end_screen
verifier([x.cle for x in fin.boutons] == ["revue", "revanche", "menu"]
         if hasattr(fin.boutons[0], "cle") else len(fin.boutons) == 3,
         "boutons : Revue de la partie, Revanche, Menu")
verifier(fin.rect.contains(fin.bouton_revue.rect) and fin.rect.contains(fin.bouton_menu.rect),
         "les boutons tiennent dans la carte")
verifier(not fin.bouton_revue.rect.colliderect(fin.bouton_revanche.rect),
         "Revue et Revanche ne se chevauchent pas")
clic = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=fin.bouton_revue.rect.center)
haut = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=fin.bouton_revue.rect.center)
action = fin.handle_event(clic) or fin.handle_event(haut)
verifier(action == "revue", "clic sur Revue de la partie -> 'revue' (%r)" % action)
verifier(fin.ligne_analyse() == "Analyse en cours...", "avancement de l'analyse sur la carte")
fin.analyseur.fini = True
verifier(fin.ligne_analyse() == "Précision : toi 60.0 %   -   Julien 92.0 %",
         "précision : toi / l'adversaire (%r)" % fin.ligne_analyse())
verifier("precision_90" not in succes_debloques, "60 % : pas de succès Chirurgien")
pa.end_screen.analyseur.fini = True
verifier(pa.end_screen.ligne_analyse().startswith("Précision : toi 92.0 %"),
         "côté Julien (Blancs) : sa propre précision")
verifier("precision_90" in succes_debloques, "92 % en ligne : succès Chirurgien")
verifier({"victoire_mat": True} in succes_verifies, "mat en ligne : succès Échec et mat")
pb.end_screen.draw(ecran)
pygame.image.save(ecran, os.path.join(RACINE, "tests", "capture_fin_en_ligne_revue.png"))

print("4. Revue : locale, avec les bons noms, le réseau continue")
partie_en_ligne.ouvrir_la_revue(gmb, pb, mb)
noms, cote_noir, apres_dessin = gmb.revues[-1]
verifier(noms == ("Julien", "Toi") and cote_noir, "Paul (Noirs) : plateau côté noir (%r)" % (noms,))
partie_en_ligne.ouvrir_la_revue(gma, pa, ma)
verifier(gma.revues[-1][:2] == (("Toi", "Paul"), False), "Julien (Blancs) : côté blanc")
ma.demander_revanche()
for _ in range(25):
    ma.update()
    apres_dessin(ecran)          # une image de la revue de Paul
    h.t += 0.05
    time.sleep(0.002)
verifier(mb.revanche.a_repondre(), "pendant sa revue, Paul reçoit la demande de revanche")
ma.envoyer_chat("bien joué")
for _ in range(25):
    ma.update(); apres_dessin(ecran); h.t += 0.05; time.sleep(0.002)
verifier(any("bien joué" in str(m) for m in pb.chat.messages),
         "pendant sa revue, Paul reçoit aussi le chat")
mb.demander_revanche()           # il accepte en revenant sur la carte
for _ in range(25):
    ma.update(); apres_dessin(ecran); h.t += 0.05; time.sleep(0.002)
verifier(ma.revanche_acceptee() and mb.revanche_acceptee(), "la revanche marche après la revue")

print("5. Statistiques et ménage")
stats = statistiques.calculer()
verifier(stats["bilan"]["parties"] == 2,
         "les parties en ligne comptent dans les statistiques (%d)" % stats["bilan"]["parties"])
partie_en_ligne._arreter_les_analyses(gma, pa)
verifier(pa.end_screen.analyseur.arretee, "analyse arrêtée en quittant la partie")

a.fermer()
b.fermer()
print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
