# tests/test_anglais.py - le jeu en anglais (17/10, travail p12).
#     python tests/test_anglais.py
# Dessine tous les ecrans en anglais et liste les textes restes en francais.
# Dossier temporaire : tes donnees ne sont pas touchees.

import os as _os_envoi
_os_envoi.environ["SICKCHESS_SANS_ENVOI"] = "1"   # 25/10 : jamais de faux message dans le vrai salon Discord
import os
import re
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import pygame

pygame.init()
ecran = pygame.display.set_mode((1280, 720))

import asset_manager
TEMP = tempfile.mkdtemp(prefix="sickchess_en_")
asset_manager.dossier_ecriture = lambda: TEMP

import langue
langue.regler("en")
import ouvertures
ouvertures.recharger()

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def photo(nom):
    pygame.image.save(ecran, os.path.join("tests", "ecrans_en", nom + ".png"))


os.makedirs(os.path.join("tests", "ecrans_en"), exist_ok=True)

print("1. Traductions")
verifier(langue.traduire("Jouer contre l'ordinateur") == "Play against the computer", "texte simple")
verifier(langue.traduire("Mode classé  -  ton classement : 1300") == "Rated mode  -  your rating: 1300",
         "texte avec un nombre")
verifier(langue.traduire("OPTIONS") == "OPTIONS" and langue.traduire("QUITTER") == "QUIT", "majuscules du menu")
verifier(ouvertures.nom_de_l_ouverture(["e4", "c5"]).startswith("Sicilian"),
         "ouvertures en anglais : %s" % ouvertures.nom_de_l_ouverture(["e4", "c5"]))

verifier(langue.traduire("111 problèmes joues, 55 % réussis, meilleure série 7 - enregistré")
         == "111 puzzles played, 55 % solved, best streak 7 - saved",
         "« %% » suivi d'un mot (Cowork, t62 : « 55 %%10olved ») : %r" % langue.traduire(
             "111 problèmes joues, 55 % réussis, meilleure série 7 - enregistré"))
verifier(langue.traduire("Ordinateur (400) - Toi") == "Computer (400) - You",
         "haut de la revue : %r" % langue.traduire("Ordinateur (400) - Toi"))
verifier(langue.traduire("Contre l'ordinateur (3000 Elo)  -  coup 2  -  24/10/2026 13:02").startswith("Against the computer (3000 Elo)  -  move 2"),
         "reprise au menu en anglais")

import ui
verifier(ui.mesurer("NOIRS", 15, True) == ui.mesurer("BLACK", 15, True),
         "on mesure le texte traduit (pendule : « BLA… » coupe)")

print("2. Tous les ecrans")
from menu_principal import MainMenu
m = MainMenu(ecran, "0.1.0"); m.annoncer_reprise(True, "Two players on this PC")
m.draw(); photo("menu")
from settings_screen import SettingsScreen
for mode in ("stockfish", "hotseat"):
    s = SettingsScreen(ecran, mode); s.draw(); photo("reglages_" + mode)
from board import ChessBoard
from ecran_fin import EcranFin
b = ChessBoard(ecran, {"pendule_active": True, "minutes": 3})
b.end_screen = EcranFin(b, "hotseat")
for u in ("e2e4", "e7e5", "g1f3", "b8c6"):
    b.make_move(chess.Move.from_uci(u))
b.draw(); photo("partie")
import menu_pause
mp = menu_pause.MenuPause(ecran); mp.ouvrir(); b.draw(); mp.draw(); photo("pause")
from raccourcis import AideRaccourcis
aide = AideRaccourcis(ecran); aide.visible = True; b.draw(); aide.draw(ecran); photo("aide")
for u in ("f1c4", "g8f6", "f3g5", "d7d5", "e4d5", "f6d5", "g5f7"):
    b.make_move(chess.Move.from_uci(u))
b.terminer_partie("ÉCHEC ET MAT !", "1-0"); b.draw(); photo("fin")
from analyse_partie import AnalyseurPartie
from ecran_revue import EcranRevue
a = AnalyseurPartie(None, ["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"])
r = EcranRevue(ecran, a, {}, ("You", "Computer"), "1-0")
r.aller_a(3, son=False); r.draw(); photo("revue")
from ecran_options import EcranOptions
o = EcranOptions(ecran)
for i in range(len(o.onglets)):
    o._changer_onglet(i); o.draw(); photo("options_%d" % i)
from ecran_mes_parties import EcranMesParties
mp2 = EcranMesParties(ecran); mp2.draw(); photo("mes_parties")
from ecran_statistiques import EcranStatistiques
st = EcranStatistiques(ecran); st.attendre(); st.draw(); st.vue = "succes"; st.draw(); photo("succes")
if os.path.exists(os.path.join("puzzles", "tranches.tsv")):   # pas de base : ecrans sautes
    from ecran_problemes import EcranProblemes
    pb = EcranProblemes(ecran, {}); pb.draw(); photo("problemes_choix")
    pb.commencer("chrono"); pb.draw(); photo("problemes_chrono")
    pb.commencer("classe"); pb.attente_jusqu_a = 0; pb.update(); pb.draw(); photo("problemes")
from ecran_entrainement import EcranEntrainement
en = EcranEntrainement(ecran, {}); en.draw(); photo("ouvertures")
en.commencer(en.familles[0][0]); en.draw()
from ecran_analyse_libre import EcranAnalyseLibre      # 24/10 (p35)


class MoteurMuet:
    multipv_courant = 3

    def est_vivant(self):
        return True

    def send_command(self, cmd):
        pass

    def _lire_ligne(self):
        import time
        time.sleep(0.2)
        return ""


al = EcranAnalyseLibre(ecran, {}, moteur=MoteurMuet())
al.draw(); al.analyse.mettre_en_pause(True); al.draw(); photo("analyse_libre")
al.coller_texte("rien"); al.draw()
verifier(langue.traduire(al.etat_du_moteur()) == "White to move  ·  Stockfish paused (Space)",
         "analyse libre : %s" % langue.traduire(al.etat_du_moteur()))
verifier(langue.traduire("Trait aux Noirs  ·  profondeur 18 (analyse terminée)")
         == "Black to move  ·  depth 18 (analysis complete)", "analyse libre : profondeur finie")
al.ouvrir_l_editeur(); al.edition.vider(); al.fermer_l_editeur(True); al.draw()
al.edition.choisir_outil("Q"); al.draw(); photo("editeur_position")
al.analyse.arreter()
import invitations                                   # 24/10 (p36)


class Gestionnaire:
    au_menu, en_ligne, config = True, False, {}


bandeau = invitations.BandeauInvitation(Gestionnaire(), steam=MoteurMuet())
invitations.ajouter(1, "Paul")
m.draw(); bandeau.dessiner(ecran); photo("invitation")
invitations.vider()
from ecran_classements import EcranClassements      # 24/10 (p37)
EcranClassements(ecran, {}).draw(); photo("classements")
from ecran_plantage import EcranPlantage               # 24/10 (p29)
EcranPlantage(ecran, {"date": "24/10/2026 10:00", "version": "0.2.0", "erreur": "KeyError: 'x'"}).draw()
photo("plantage")
from ecran_signaler import EcranSignaler
EcranSignaler(ecran, "0.1").draw(); photo("signaler")
import premier_lancement
from profil import Profil
pl = premier_lancement.EcranPremierLancement(ecran, Profil()); pl.draw(); pl.etape = 2; pl.draw(); photo("accueil")

print("3. Ce qui reste en francais")
mots_fr = re.compile(r"\b(le|la|les|des|du|une|est|pas|pour|avec|sur|ton|ta|tes|tu|à|é|è|ê|ç|coup|partie|joue|pièce)\b|[éèêàçôû]", re.I)
print("      TOUS :", sorted(langue.manquants()))
restes = sorted(t for t in langue.manquants() if mots_fr.search(t))
for t in restes:
    print("      reste : %r" % t)
verifier(len(restes) <= 5, "%d texte(s) encore en francais a l'ecran" % len(restes))

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
