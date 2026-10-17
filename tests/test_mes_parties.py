# tests/test_mes_parties.py - verifie "Mes parties et profil" sans fenetre.
#     python tests/test_mes_parties.py
# Tout est ecrit dans un dossier temporaire : ton vrai profil.json et ton
# dossier parties/ ne sont jamais touches.

import os
import shutil
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import pygame

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
ecran = pygame.display.set_mode((1024, 640))

import asset_manager
TEMP = tempfile.mkdtemp(prefix="sickchess_test_")
asset_manager.dossier_ecriture = lambda: TEMP

import enregistrement
import historique_parties
import sauvegarde
from board import ChessBoard
from ecran_fin import EcranFin
from ecran_mes_parties import EcranMesParties
from ecran_revoir import EcranRevoir
from layout import Disposition
from menu_principal import MainMenu
from profil import get_profil

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def jouer(plateau, coups):
    for uci in coups:
        plateau.make_move(chess.Move.from_uci(uci))
        plateau.update()


def capture(nom):
    pygame.image.save(ecran, os.path.join(RACINE, "tests", nom))


BERGER = ["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"]

print("1. Partie gagnee contre l'ordinateur -> profil + PGN")
profil = get_profil()
verifier(profil.elo == 1200 and not profil.parties, "profil neuf a 1200")
p = ChessBoard(ecran, {"elo": 1400, "pendule_active": True, "minutes": 5,
                       "increment": 0})
p.end_screen = EcranFin(p, "stockfish")
p.ia_joue_blancs = False                       # le joueur a les Blancs
jouer(p, BERGER)
verifier(p.game_over and p.result == "1-0", "mat du berger, 1-0")
infos = enregistrement.enregistrer_la_partie(p, "stockfish")
verifier(infos["classee"] and infos["elo_apres"] > 1200,
         "Elo monte : %d -> %d" % (infos["elo_avant"], infos["elo_apres"]))
verifier(len(profil.parties) == 1 and profil.parties[0]["score"] == 1.0,
         "partie ajoutee au profil (victoire)")
verifier(os.path.exists(os.path.join(TEMP, "profil.json")), "profil.json ecrit")
verifier(os.path.exists(infos["pgn"]), "fichier PGN cree")
e = historique_parties.lire_entetes(infos["pgn"])
verifier(e.get("White") == profil.nom and e.get("Black") == "Ordinateur",
         "noms dans le PGN (%s - %s)" % (e.get("White"), e.get("Black")))
verifier(e.get("Joueur") == "blanc" and e.get("Result") == "1-0", "camp et resultat")
verifier(e.get("BlackElo") == "1400" and e.get("TimeControl") == "5 min",
         "Elo adverse et cadence")
verifier(bool(e.get("ECO")), "ouverture reconnue (%s %s)" % (e.get("ECO"),
                                                             e.get("Opening")))
print("     ", enregistrement.texte_classement(infos))

print("2. Partie perdue avec les Noirs, avec un indice -> non classee")
p2 = ChessBoard(ecran, {"elo": 800, "pendule_active": False})
p2.ia_joue_blancs = True
p2.indices_utilises = 1
jouer(p2, BERGER)
elo = profil.elo
infos2 = enregistrement.enregistrer_la_partie(p2, "stockfish")
verifier(not infos2["classee"] and profil.elo == elo, "Elo inchange (indice)")
verifier(profil.statistiques()["defaites"] == 1, "defaite comptee")
verifier("non classee" in enregistrement.texte_classement(infos2), "texte non classee")

print("3. Partie a deux -> PGN seulement")
p3 = ChessBoard(ecran, {"pendule_active": False})
jouer(p3, ["f2f3", "e7e5", "g2g4", "d8h4"])
nb = len(profil.parties)
infos3 = enregistrement.enregistrer_la_partie(p3, "hotseat")
verifier(len(profil.parties) == nb and os.path.exists(infos3["pgn"]),
         "profil inchange, PGN ecrit")
p4 = ChessBoard(ecran, {"pendule_active": False})
jouer(p4, ["e2e4"])
verifier(enregistrement.enregistrer_la_partie(p4, "hotseat") is None,
         "partie d'un seul demi-coup ignoree")

print("4. Liste et relecture du PGN")
os.utime(infos["pgn"], (1, 1))                 # ordre stable pour le test
os.utime(infos2["pgn"], (2, 2))
liste = historique_parties.lister()
verifier(len(liste) == 3, "3 parties listees")
verdicts = [x["verdict"] for x in liste]
verifier(verdicts == ["", "defaite", "victoire"], "verdicts %s" % verdicts)
donnees, erreur = historique_parties.lire_partie(infos["pgn"])
verifier(not erreur and donnees["coups"] == BERGER, "coups relus a l'identique")

print("5. Sauvegarde et reprise")
p5 = ChessBoard(ecran, {"pendule_active": True, "minutes": 3, "increment": 2})
p5.ia_joue_blancs = True
jouer(p5, ["d2d4", "d7d5", "c2c4"])
p5.timer.time_left[chess.WHITE] = 101.5
p5.flipped = True
verifier(sauvegarde.enregistrer(p5, "stockfish", {"elo": 1500, "minutes": 3}),
         "partie sauvegardee")
d = sauvegarde.lire()
verifier(d is not None and len(d["coups"]) == 3, "sauvegarde relue")
print("      menu :", sauvegarde.resume(d))
p6 = ChessBoard(ecran, {"pendule_active": True, "minutes": 3, "increment": 2})
sauvegarde.appliquer(p6, d)
verifier(p6.board.fen() == p5.board.fen(), "meme position apres reprise")
verifier(abs(p6.timer.time_left[chess.WHITE] - 101.5) < 0.01, "pendules reprises")
verifier(p6.flipped and p6.ia_joue_blancs, "orientation et couleur de l'IA")
verifier(len(p6.move_history.moves) == 3, "historique des coups repris")
verifier(not sauvegarde.enregistrer(p, "stockfish", {}), "partie finie : pas sauvee")

print("6. Menu")
menu = MainMenu(ecran, "0.1.0")
menu.annoncer_reprise(True, sauvegarde.resume(d))
cles = [b.cle for b in menu.boutons]
verifier(cles[0] == "reprendre", "bouton Reprendre en tete")
verifier(all(b.actif for b in menu.boutons if b.cle == "historique"),
         "Mes parties et profil actif")
menu.draw()
verifier(max(b.rect.bottom for b in menu.boutons) <= 640, "les 7 boutons tiennent en 640 px")
capture("capture_menu_reprise.png")
menu.annoncer_reprise(False)
verifier(menu.boutons[0].cle != "reprendre", "bouton retire ensuite")
sauvegarde.effacer()
verifier(sauvegarde.lire() is None, "sauvegarde effacee")

print("7. Ecran Mes parties")
mp = EcranMesParties(ecran)
mp.draw()
capture("capture_mes_parties.png")
verifier(len(mp.rects_lignes) == 3, "3 lignes affichees")
rect, index = mp.rects_lignes[2]
clic = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)
r = mp.handle_event(clic)
verifier(isinstance(r, dict) and r["partie"]["verdict"] == "victoire",
         "clic sur une ligne -> relecture")
mp.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                   pos=mp.btn_nom.rect.center))
verifier(mp.edition, "edition du nom")
mp.champ_nom.contenu = "Julien"
mp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0,
                                   unicode="\r"))
verifier(get_profil().nom == "Julien", "nom change et enregistre")
mp.draw()
verifier(mp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE,
                                            mod=0, unicode="")) == "retour",
         "Echap = retour")
ecran = pygame.display.set_mode((900, 560))
mp._placer(ecran)
mp.draw()
capture("capture_mes_parties_petit.png")
vide = tempfile.mkdtemp(prefix="sickchess_vide_")
asset_manager.dossier_ecriture = lambda: vide
EcranMesParties(ecran).draw()
asset_manager.dossier_ecriture = lambda: TEMP
capture("capture_mes_parties_vide.png")

print("8. Relecture coup par coup")
ecran = pygame.display.set_mode((1024, 640))
rv = EcranRevoir(ecran, r["partie"], Disposition(1024, 640))
verifier(rv.index == 7 and rv.plateau.board.is_checkmate(), "s'ouvre sur le mat final")
rv.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_HOME, mod=0, unicode=""))
verifier(rv.plateau.board.fen() == chess.STARTING_FEN, "Debut = position initiale")
for _ in range(3):
    rv.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT, mod=0,
                                       unicode=""))
verifier(rv.index == 3 and rv.plateau.board.piece_at(chess.C4) is not None,
         "3 coups en avant (Fc4 joue)")
rv.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT, mod=0, unicode=""))
verifier(rv.index == 2, "un coup en arriere")
rv.draw()
rect, index = rv.rects_coups[4]
rv.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))
verifier(rv.index == 5, "clic sur Dh5 -> coup 5")
for _ in range(40):
    rv.draw()
capture("capture_revoir.png")
verifier(rv.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE,
                                            mod=0, unicode="")) == "retour",
         "Echap = retour")

print("9. Carte de fin avec le classement")
p.end_screen.ligne_classement = enregistrement.texte_classement(infos)
p.draw()
capture("capture_fin_classement.png")

shutil.rmtree(TEMP, ignore_errors=True)
shutil.rmtree(vide, ignore_errors=True)
print()
print("RESULTAT : " + ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
