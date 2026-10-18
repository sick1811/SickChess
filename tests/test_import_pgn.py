# tests/test_import_pgn.py - importer une partie PGN (17/10, travail p18).
#     python tests/test_import_pgn.py
# Dossier temporaire : ton vrai profil et tes parties ne sont pas touches.

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
TEMP = tempfile.mkdtemp(prefix="sickchess_import_")
asset_manager.dossier_ecriture = lambda: TEMP

import historique_parties
import ui

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


PGN_LICHESS = """[Event "Rated Blitz game"]
[Site "https://lichess.org/abcdEFGH"]
[Date "2026.10.01"]
[White "sick1811"]
[Black "MagnusFan"]
[Result "0-1"]
[ECO "C50"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O Nf6 5. d3 d6 0-1
"""

print("1. Importer un PGN")
chemin, erreur = historique_parties.importer(PGN_LICHESS, "sick1811")
verifier(chemin and not erreur and os.path.exists(chemin), "partie rangee dans parties/")
parties = historique_parties.lister()
verifier(len(parties) == 1 and parties[0]["importee"], "elle apparait dans Mes parties")
p = parties[0]
verifier(p["camp"] == "noir" or p["camp"] == "blanc", "ton camp reconnu par ton nom (%s)" % p["camp"])
verifier(p["verdict"] == "defaite", "verdict de ton point de vue : %s" % p["verdict"])
donnees, err = historique_parties.lire_partie(chemin)
verifier(donnees and len(donnees["coups"]) == 10, "10 demi-coups relus")

chemin2, _ = historique_parties.importer("1. d4 d5 2. c4 e6 3. Nc3 Nf6", "sick1811")
p2 = [x for x in historique_parties.lister() if x["chemin"] == chemin2][0]
verifier(p2["verdict"] == "importee" and not p2["camp"], "coups seuls, sans en-tetes : pastille PGN")

for texte, attendu in (("", "Rien à importer"), ("bonjour", "pas une partie"),
                       ("[White \"a\"]\n\n*", "aucun coup")):
    c, e = historique_parties.importer(texte)
    verifier(not c and attendu in e, "refus : %r -> %s" % (texte[:12], e))

print("2. Lien lichess (telechargement simule)")
class Rep:
    def __init__(self, t): self.t = t
    def read(self): return self.t.encode("utf-8")
    def __enter__(self): return self
    def __exit__(self, *a): return False
demandes = []
def faux(req, timeout=8):
    demandes.append(req.full_url)
    return Rep(PGN_LICHESS)
c, e = historique_parties.importer("https://lichess.org/abcdEFGH", "sick1811", ouvrir=faux)
verifier(c and "game/export/abcdEFGH" in demandes[0], "lien lichess : partie telechargee")
def coupe(req, timeout=8):
    raise OSError("pas de reseau")
c, e = historique_parties.importer("https://lichess.org/abcdEFGHijkl", ouvrir=coupe)
verifier(not c and "Internet" in e, "sans Internet : %s" % e)

print("3. Dans l'ecran Mes parties")
from ecran_mes_parties import EcranMesParties
ecr = EcranMesParties(ecran)
nb_profil = (ecr.profil.elo, len(ecr.profil.parties))
ui.coller = lambda: "1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6"
avant = len(ecr.parties)
action = ecr.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                              pos=ecr.btn_importer.rect.center))
verifier(isinstance(action, dict) and action.get("action") == "revoir",
         "bouton Importer : la revue de la partie s'ouvre")
verifier(len(ecr.parties) == avant + 1, "la liste compte une partie de plus")
ui.coller = lambda: ""
ecr.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                    pos=ecr.btn_importer.rect.center))
verifier("glisse un fichier" in ecr.message, "presse-papiers vide : %s" % ecr.message)
fichier = os.path.join(TEMP, "partie.pgn")
with open(fichier, "w", encoding="utf-8") as f:
    f.write(PGN_LICHESS)
action = ecr.handle_event(pygame.event.Event(pygame.DROPFILE, file=fichier))
verifier(isinstance(action, dict), "fichier .pgn glisse sur la fenetre : importe")
ecr.draw()
pygame.image.save(ecran, "tests/capture_import_pgn.png")
from profil import get_profil
verifier((get_profil().elo, len(get_profil().parties)) == nb_profil,
         "le profil et l'Elo ne bougent pas")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
