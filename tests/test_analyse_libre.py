# tests/test_analyse_libre.py - l'analyse libre (24/10, travail p35).
#     python tests/test_analyse_libre.py
# Sans Stockfish : un faux moteur repond comme lui (lignes « info ... pv »).
# Les verifications avec le vrai Stockfish sont dans test_analyse_libre_moteur.py.
# Dossier temporaire : tes donnees ne sont pas touchees.

import os
import queue
import sys
import tempfile
import time

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
TEMP = tempfile.mkdtemp(prefix="sickchess_libre_")
asset_manager.dossier_ecriture = lambda: TEMP

import analyse_continue
from ecran_analyse_libre import EcranAnalyseLibre, EditeurPosition

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


class FauxMoteur:
    """Parle comme Stockfish : a « go », des lignes de profondeur 1 a 6 avec
    3 coups classes (les premiers coups legaux), puis il attend « stop »."""

    def __init__(self):
        self.lignes = queue.Queue()
        self.fen = chess.STARTING_FEN
        self.recus = []
        self.multipv_courant = 1

    def est_vivant(self):
        return True

    def send_command(self, cmd):
        self.recus.append(cmd)
        if cmd.startswith("position fen "):
            self.fen = cmd[len("position fen "):]
        elif cmd.startswith("go"):
            plateau = chess.Board(self.fen)
            coups = sorted(c.uci() for c in plateau.legal_moves)[:3]
            for profondeur in range(1, 7):
                for rang, coup in enumerate(coups, 1):
                    self.lignes.put("info depth %d multipv %d score cp %d nodes 100 pv %s"
                                    % (profondeur, rang, 50 - 20 * rang, coup))
        elif cmd == "stop":
            self.lignes.put("bestmove 0000")

    def _lire_ligne(self):
        try:
            return self.lignes.get(timeout=5)
        except queue.Empty:
            return None


def attendre(condition, secondes=5, ecran_=None):
    fin = time.time() + secondes
    while time.time() < fin:
        if ecran_ is not None:
            ecran_.draw()
        if condition():
            return True
        time.sleep(0.02)
    return False


print("1. Coller un FEN ou une partie PGN")
fen, coups, erreur = analyse_continue.lire_fen_ou_pgn(
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3")
verifier(fen and not coups and not erreur, "un FEN complet")
fen, coups, erreur = analyse_continue.lire_fen_ou_pgn("8/8/8/4k3/8/8/4P3/4K3 b")
verifier(fen == "8/8/8/4k3/8/8/4P3/4K3 b - - 0 1", "un FEN sans les compteurs (%s)" % fen)
fen, coups, erreur = analyse_continue.lire_fen_ou_pgn(
    '[Event "?"]\n[White "A"]\n[Black "B"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 *')
verifier(fen == chess.STARTING_FEN and coups[:2] == ["e2e4", "e7e5"] and len(coups) == 6,
         "une partie PGN : 6 coups")
fen, coups, erreur = analyse_continue.lire_fen_ou_pgn(
    '[FEN "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1"]\n[SetUp "1"]\n\n1. e4+ Kd6 *')
verifier(fen.startswith("8/8/8/4k3") and coups == ["e2e4", "e5d6"],
         "une partie PGN qui part d'une position (en-tete FEN)")
verifier(analyse_continue.lire_fen_ou_pgn("bonjour")[2], "un texte quelconque : refuse")
verifier(analyse_continue.lire_fen_ou_pgn("")[2].startswith("Le presse-papiers est vide"),
         "presse-papiers vide : message clair")
verifier("roi" in analyse_continue.lire_fen_ou_pgn("8/8/8/8/8/8/8/K7 w - - 0 1")[2],
         "un FEN sans roi noir : refuse avec la raison")

print("2. Positions impossibles (editeur)")
pb = analyse_continue.probleme_de_position
verifier(pb(chess.Board()) == "", "position de depart : bonne")
verifier("pion" in pb(chess.Board("4k3/8/8/8/8/8/8/P3K3 w - - 0 1")), "pion sur la 1re rangee")
verifier("trait" in pb(chess.Board("4k3/8/8/8/8/8/8/4KR2 w - - 0 1").copy()) or
         pb(chess.Board("4k3/8/8/8/8/8/8/4R1K1 w - - 0 1")) != "",
         "le camp sans le trait en echec")
verifier(pb(chess.Board("4k3/8/8/8/8/8/8/4R1K1 w - - 0 1")).startswith("Le camp qui n'a pas"),
         "message : changer le trait")
verifier("plus d'un roi" in pb(chess.Board("4k3/8/8/8/8/8/8/K3K3 w - - 0 1")), "deux rois blancs")

e = EditeurPosition(chess.STARTING_FEN)
e.vider()
verifier(e.valider() is None and "roi" in e.message, "plateau vide : on ne peut pas valider")
e.choisir_outil("K"); e.clic(chess.E1)
e.choisir_outil("k"); e.clic(chess.E8)
e.choisir_outil("Q"); e.clic(chess.D1)
e.choisir_outil("Q"); e.clic(chess.D1)
verifier(e.outil == "Q" and e.plateau.piece_at(chess.D1) is None,
         "la piece reste choisie ; la reposer au meme endroit l'enleve")
e.clic(chess.D1)
e.clic(chess.D1, bouton=3)
verifier(e.plateau.piece_at(chess.D1) is None, "clic droit : la piece est enlevee")
e.choisir_outil("R"); e.clic(chess.H1)
e.choisir_outil(None)                      # « Deplacer »
e.clic(chess.H1); e.clic(chess.H4)
verifier(e.plateau.piece_at(chess.H4) == chess.Piece.from_symbol("R")
         and e.plateau.piece_at(chess.H1) is None, "sans outil : on deplace une piece")
e.clic(chess.H4); e.clic(chess.H1)
e.basculer_roque(chess.BB_H1)
verifier(e.plateau.castling_rights == chess.BB_H1, "petit roque blanc coche (roi e1, tour h1)")
e.basculer_roque(chess.BB_A1)
verifier(e.plateau.castling_rights == chess.BB_H1, "grand roque impossible sans tour en a1")
e.clic(chess.H1, bouton=3)
verifier(e.plateau.castling_rights == 0, "tour enlevee : le roque disparait")
e.changer_trait(chess.BLACK)
fen = e.valider()
verifier(fen == "4k3/8/8/8/8/8/8/4K3 b - - 0 1", "position validee : %s" % fen)
e.position_de_depart()
verifier(e.plateau.fen() == chess.STARTING_FEN, "bouton Depart")

print("3. L'ecran : jouer les deux camps, naviguer")
moteur = FauxMoteur()
ecr = EcranAnalyseLibre(ecran, {}, moteur=moteur)
p = ecr.plateau
verifier(ecr.index == 0 and ecr.coups == [], "position de depart, aucun coup")
verifier(attendre(lambda: len(ecr.lignes()) == 3, ecran_=ecr),
         "3 lignes du moteur affichees (%d)" % len(ecr.lignes()))
verifier(attendre(lambda: ecr.analyse.resultat()["profondeur"] == 6, ecran_=ecr),
         "la profondeur monte (%d)" % ecr.analyse.resultat()["profondeur"])
verifier(any(c.startswith("setoption name MultiPV value 3") for c in moteur.recus),
         "Stockfish classe 3 coups")
verifier(len(p.fleches_conseil) >= 1, "fleche du meilleur coup sur l'echiquier")
verifier(ecr.etat_du_moteur().startswith("Trait aux Blancs") and "profondeur 6" in ecr.etat_du_moteur(),
         "ligne d'etat : %s" % ecr.etat_du_moteur())
for u in ("e2e4", "e7e5", "g1f3"):
    verifier(p.make_move(chess.Move.from_uci(u)), "coup %s joue" % u)
verifier(ecr.index == 3 and p.board.turn == chess.BLACK, "les deux camps se jouent")
verifier(attendre(lambda: moteur.fen == p.board.fen(), ecran_=ecr),
         "le moteur suit la nouvelle position")
verifier("stop" in moteur.recus, "la recherche precedente a ete arretee")
ecr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT, mod=0, unicode=""))
verifier(ecr.index == 2 and len(ecr.coups) == 3, "fleche gauche : un coup en arriere, la suite reste")
verifier(p.make_move(chess.Move.from_uci("g1f3")) and ecr.index == 3 and len(ecr.coups) == 3,
         "rejouer le coup suivant : on avance dans la suite")
ecr.aller_a(2)
verifier(p.make_move(chess.Move.from_uci("b1c3")) and ecr.coups[-1].uci() == "b1c3"
         and len(ecr.coups) == 3, "un autre coup remplace la suite")
ecr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_HOME, mod=0, unicode=""))
verifier(ecr.index == 0 and p.board.fen() == chess.STARTING_FEN, "Debut : position de depart")
ecr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_END, mod=0, unicode=""))
verifier(ecr.index == 3, "Fin : dernier coup")
avant = len(ecr.coups)
attendre(lambda: len(ecr.lignes()) == 3, ecran_=ecr)
premier = ecr.lignes()[0]["uci"]
ecr.jouer_ligne(0)
verifier(len(ecr.coups) == avant + 1 and ecr.coups[-1].uci() == premier,
         "clic sur une ligne : son premier coup est joue (%s)" % premier)
texte = ecr.texte_d_une_ligne({"suite_san": ["Nc6", "Bb5", "a6"]})
verifier(texte.startswith("2...") or texte.startswith("3"), "ligne numerotee : %s" % texte)

print("4. Moteur a l'arret, editeur, collage")
ecr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, mod=0, unicode=""))
verifier(not ecr.analyse.actif and "arrêt" in ecr.etat_du_moteur(), "Espace : Stockfish a l'arret")
ecr.draw()
verifier(ecr.btn_moteur.libelle == "Relancer" and ecr.btn_moteur.selectionne,
         "le bouton dit « Relancer », en or")
ecr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, mod=0, unicode=""))
verifier(ecr.analyse.actif, "Espace : relance")
ecr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e, mod=0, unicode=""))
verifier(ecr.edition is not None, "E : editeur ouvert")
ecr.draw()
ecr.edition.vider()
verifier(not ecr.fermer_l_editeur(True) and ecr.edition is not None,
         "Analyser refuse un plateau vide (%s)" % ecr.edition.message)
ecr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode=""))
verifier(ecr.edition is None and ecr.index == len(ecr.coups) and ecr.plateau.board.fen() != "8/8/8/8/8/8/8/8 w - - 0 1",
         "Echap : editeur annule, la partie revient")
ecr.ouvrir_l_editeur()
ecr.edition.vider()
for s, c in (("K", chess.G1), ("k", chess.G8), ("R", chess.A1), ("p", chess.F7),
             ("p", chess.G7), ("p", chess.H7), ("P", chess.F2), ("P", chess.G2), ("P", chess.H2)):
    ecr.edition.choisir_outil(s); ecr.edition.clic(c)
d = ecr.disposition
pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                     pos=ecr.btn_valider.rect.center))
for event in pygame.event.get():
    ecr.handle_event(event)
verifier(ecr.edition is None and ecr.fen_depart.startswith("6k1/5ppp/8/8/8/8/5PPP/R5K1 w"),
         "bouton Analyser : la position fabriquee est analysee")
verifier(attendre(lambda: moteur.fen == ecr.plateau.board.fen(), ecran_=ecr),
         "Stockfish passe sur la nouvelle position")
verifier(ecr.coller_texte("1. d4 d5 2. c4 *") and len(ecr.coups) == 3 and ecr.index == 0,
         "PGN colle : la partie s'affiche depuis le debut")
verifier(not ecr.coller_texte("rien du tout") and ecr.message, "collage refuse : message (%s)" % ecr.message)
verifier(ecr.coller_texte("8/8/8/4k3/8/8/4P3/4K3 w - - 0 1") and ecr.coups == [],
         "FEN colle : la position s'affiche")
verifier(analyse_continue.finale_des_tables(ecr.plateau.board, dossier=os.path.join(TEMP, "rien")) is None,
         "tables de finale absentes : rien d'affiche, pas d'erreur")

print("5. Fin de partie, retournement, retour")
ecr.coller_texte("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2")
p = ecr.plateau
p.make_move(chess.Move.from_uci("d8h4"))
ecr.draw()
verifier(ecr.etat_du_moteur() == "Échec et mat" and ecr.lignes() == [], "mat : plus de lignes")
verifier(ecr.evaluation()[1] == "Mat", "la barre dit Mat")
ecr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f, mod=0, unicode=""))
verifier(p.flipped, "F : echiquier retourne")
verifier(ecr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0,
                                             unicode="")) == "retour", "Echap : retour")
ecr.analyse.arreter()
verifier(attendre(lambda: not ecr.analyse._fil.is_alive()), "le fil du moteur s'arrete en sortant")

print("6. Depuis la revue : « Analyser (A) »")
from analyse_partie import AnalyseurPartie
from ecran_revue import EcranRevue


class MoteurMuet:
    def analyser_position(self, *a, **k):
        return None


a = AnalyseurPartie(None, ["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"],
                    moteur=MoteurMuet())
r = EcranRevue(ecran, a, {}, ("Toi", "Ordinateur"), "1-0")
r.aller_a(4, son=False)
verifier(r.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, mod=0, unicode="")) is None
         and r.analyse_libre is not None, "touche A : l'analyse libre s'ouvre")
libre = r.analyse_libre
verifier(libre.fen_depart == chess.STARTING_FEN and libre.index == 4 and len(libre.coups) == 7,
         "meme partie, meme position (coup 4 sur 7)")
libre.analyse.arreter()
r.aller_a(5, son=False)
r.plateau.make_move(chess.Move.from_uci("g7g6"))           # une variante
r.ouvrir_l_analyse_libre()
libre = r.analyse_libre
verifier(libre.index == 6 and libre.coups[-1].uci() == "g7g6"
         and libre.plateau.board.fen() == r.plateau.board.fen(),
         "depuis une variante : la position de la variante")
libre.analyse.arreter()
r.draw()
verifier(r.btn_analyser.rect.width > 0 and not r.btn_analyser.rect.colliderect(r.btn_retour.rect),
         "le bouton Analyser a sa place, sans chevaucher Retour")
a.arreter()

print("7. Le menu")
from menu_principal import MainMenu
m = MainMenu(ecran)
verifier(any(b.cle == "analyse" and b.libelle == "Analyse libre" for b in m.boutons),
         "entree « Analyse libre » dans le menu")
for taille in ((1024, 640), (1920, 1080)):
    m.redimensionner(*taille)
    rects = [b.rect for b in m.boutons]
    verifier(all(not r1.colliderect(r2) for i, r1 in enumerate(rects) for r2 in rects[i + 1:])
             and max(r.bottom for r in rects) <= taille[1],
             "menu %dx%d : aucune entree ne chevauche ni ne sort" % taille)

print("Grands ecrans : des pixels entiers (plantage de l'editeur trouve par Cowork en 1920x1080)")
from ecran_revue import DispositionRevue
for l, h in ((1920, 1080), (1366, 768), (2560, 1440), (1600, 900)):
    d = DispositionRevue(l, h)
    verifier(all(isinstance(v, int) for v in (d.plateau_x, d.plateau_y, d.taille_case, d.panneau_x, d.panneau_l)),
             "%dx%d : plateau et panneau en pixels entiers (%r, %r)" % (l, h, d.plateau_x, d.panneau_x))
ecran = pygame.display.set_mode((1920, 1080))
grand = EcranAnalyseLibre(ecran, {}, moteur=moteur)
grand.ouvrir_l_editeur()
grand.edition.choisir_outil("R")
d = grand.disposition
case = grand._case_sous((d.plateau_x + 3.5 * d.taille_case, d.plateau_y + 6.5 * d.taille_case))
verifier(isinstance(case, int) and 0 <= case < 64, "1920x1080 : la case sous la souris est un vrai numero (%r)" % case)
try:
    grand.edition.clic(case)
    grand.draw()
    ok = grand.plateau.board.piece_at(case) is not None if hasattr(grand.plateau, "board") else True
except Exception as erreur:
    ok = False
    print("    " + repr(erreur))
verifier(ok, "1920x1080 : poser une tour dans l'editeur ne plante pas")
grand.analyse.arreter()

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
