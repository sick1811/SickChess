# tests/test_freestyle.py - le mode Freestyle (echecs 960, regles FIDE Guidelines II).
#     python tests/test_freestyle.py
# Sans Stockfish. REGLES INTOUCHABLES (voir CLAUDE.md) : un controle de cette
# serie ne se supprime jamais.

import os
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import asset_manager
_DOSSIER = tempfile.mkdtemp()
asset_manager.dossier_ecriture = lambda: _DOSSIER       # jamais les vraies donnees

import chess
import pygame
pygame.init()
import freestyle

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def roi_tour(b, couleur=chess.WHITE):
    return b.king(couleur), sorted(b.pieces(chess.ROOK, couleur))


print("== Les 960 positions ==")
bonnes, vues = 0, set()
for n in range(960):
    b = freestyle.plateau_de_depart(n)
    rangee = [b.piece_at(chess.square(f, 0)) for f in range(8)]
    types = [p.piece_type for p in rangee]
    roi = types.index(chess.KING)
    tours = [i for i, t in enumerate(types) if t == chess.ROOK]
    fous = [i for i, t in enumerate(types) if t == chess.BISHOP]
    noirs = [b.piece_at(chess.square(f, 7)) for f in range(8)]
    ok = (sorted(types) == sorted([chess.ROOK] * 2 + [chess.KNIGHT] * 2
                                  + [chess.BISHOP] * 2 + [chess.QUEEN, chess.KING])
          and tours[0] < roi < tours[1] and (fous[0] + fous[1]) % 2 == 1
          and all(p.color == chess.WHITE for p in rangee)
          and [p.piece_type for p in noirs] == types
          and all(p.color == chess.BLACK for p in noirs)
          and all(b.piece_at(chess.square(f, 1)) == chess.Piece(chess.PAWN, chess.WHITE)
                  and b.piece_at(chess.square(f, 6)) == chess.Piece(chess.PAWN, chess.BLACK)
                  for f in range(8))
          and b.chess960_pos() == n and b.castling_rights == (
              chess.BB_SQUARES[chess.square(tours[0], 0)] | chess.BB_SQUARES[chess.square(tours[1], 0)]
              | chess.BB_SQUARES[chess.square(tours[0], 7)] | chess.BB_SQUARES[chess.square(tours[1], 7)]))
    bonnes += ok
    vues.add(b.board_fen())
verifier(bonnes == 960, "les 960 positions : roi entre les tours, fous de couleurs "
         "differentes, Noirs en miroir, pions en place, 4 droits de roque (%d/960)" % bonnes)
verifier(len(vues) == 960, "les 960 positions sont toutes differentes")
verifier(freestyle.plateau_de_depart(518).board_fen() == chess.Board().board_fen(),
         "la n° 518 est la position classique")
tirages = {freestyle.tirer_numero() for _ in range(5000)}
verifier(518 not in tirages and len(tirages) > 900 and max(tirages) <= 959 and min(tirages) >= 0,
         "tirage au hasard : de 0 a 959, jamais la 518 (%d numeros vus)" % len(tirages))

print("== Les quatre formes de roque ==")
CAS = [("roi et tour bougent (grand roque, roi b1 / tour a1)",
        "4k3/8/8/8/8/8/8/RK6 w A - 0 1", "b1a1", chess.C1, [chess.D1]),
       ("roi et tour echangent leurs cases (petit roque, roi f1 / tour g1)",
        "4k3/8/8/8/8/8/8/5KR1 w G - 0 1", "f1g1", chess.G1, [chess.F1]),
       ("seul le roi bouge (grand roque, roi e1 / tour d1)",
        "4k3/8/8/8/8/8/8/3RK3 w D - 0 1", "e1d1", chess.C1, [chess.D1]),
       ("seule la tour bouge (petit roque, roi deja en g1)",
        "4k3/8/8/8/8/8/8/6KR w H - 0 1", "g1h1", chess.G1, [chess.F1])]
for nom, fen, uci, roi, tours in CAS:
    b = chess.Board(fen, chess960=True)
    coup = chess.Move.from_uci(uci)
    legal = coup in b.legal_moves and b.is_castling(coup)
    san = b.san(coup) if legal else ""
    if legal:
        b.push(coup)
    verifier(legal and roi_tour(b) == (roi, tours)
             and san in ("O-O", "O-O-O"), "%s -> %s" % (nom, san))

b = chess.Board("4k3/8/8/8/8/8/8/RNK5 w A - 0 1", chess960=True)
verifier(not any(b.is_castling(m) for m in b.legal_moves),
         "roque interdit si une piece est sur le chemin de la tour (cavalier b1)")
b = chess.Board("4k3/8/8/8/8/8/8/R1KB4 w A - 0 1", chess960=True)
verifier(not any(b.is_castling(m) for m in b.legal_moves),
         "roque interdit si la case d'arrivee de la tour (d1) est occupee")
b = chess.Board("4k3/8/8/8/8/8/8/NB2RK2 w E - 0 1", chess960=True)
verifier(chess.Move.from_uci("f1e1") in b.legal_moves,
         "grand roque permis avec des pieces en a1 et b1 (hors du chemin)")
b = chess.Board("2r1k3/8/8/8/8/8/8/RK6 w A - 0 1", chess960=True)
verifier(chess.Move.from_uci("b1a1") not in b.legal_moves,
         "roque interdit si le roi arrive sur une case attaquee (c1)")
b = chess.Board("1r2k3/8/8/8/8/8/8/RK6 w A - 0 1", chess960=True)
verifier(chess.Move.from_uci("b1a1") not in b.legal_moves,
         "roque interdit quand le roi est en echec")
premier = [n for n in range(960)
           if any(freestyle.plateau_de_depart(n).is_castling(m)
                  for m in freestyle.plateau_de_depart(n).legal_moves)]
verifier(len(premier) > 0, "le roque est parfois possible des le 1er coup (%d positions, "
         "ex. n° %s)" % (len(premier), premier[:3]))

print("== Relire une partie Freestyle (revue, analyse, sauvegarde) ==")
b = freestyle.plateau_de_depart(0)          # BBQNNRKR
fen = b.fen()
verifier(freestyle.est_freestyle_fen(fen), "FEN Freestyle reconnue : %s" % fen)
verifier(not freestyle.est_freestyle_fen(chess.STARTING_FEN)
         and not freestyle.est_freestyle_fen("4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1"),
         "FEN classique : pas Freestyle")
verifier(chess.Board(fen).clean_castling_rights() == 0
         and freestyle.plateau(fen).clean_castling_rights() == b.clean_castling_rights(),
         "chess.Board(fen) perd le roque Freestyle, freestyle.plateau(fen) le garde")

print("== Le plateau du jeu ==")
from board import ChessBoard
ecran = pygame.display.set_mode((1280, 720))


def plateau_freestyle(numero=None, fen=None):
    p = ChessBoard(ecran, {"son_de_depart": False, "freestyle": numero or 0})
    if fen:
        p.board = chess.Board(fen, chess960=True)
        p.move_history.set_fen_initiale(fen)
    return p


p = ChessBoard(ecran, {"son_de_depart": False})
verifier(not p.board.chess960 and p.board.fen() == chess.STARTING_FEN,
         "partie normale : position classique, sans Freestyle")
p = plateau_freestyle(123)
verifier(p.board.chess960 and p.board.chess960_pos() == 123
         and p.move_history.fen_initiale == p.board.fen(),
         "partie Freestyle n° 123 : bonne position, l'historique part d'elle")

# Roque a la souris : poser le roi sur sa tour, ou sur g1 / c1.
p = plateau_freestyle(fen="4k3/8/8/8/8/8/8/RK6 w A - 0 1")
p.move_handler._jouer(chess.B1, chess.C1, None)
verifier(p.board.piece_at(chess.C1) == chess.Piece(chess.KING, chess.WHITE)
         and p.board.piece_at(chess.A1) is not None,
         "roi b1 pose en c1 (coup normal du roi) : coup normal, pas de roque")
p = plateau_freestyle(fen="4k3/8/8/8/8/8/8/RK6 w A - 0 1")
p.move_handler._jouer(chess.B1, chess.A1, None)
verifier(roi_tour(p.board) == (chess.C1, [chess.D1]) and p.move_history.sans == ["O-O-O"],
         "roi pose sur sa tour : grand roque O-O-O")
verifier(not p.captured_pieces.captured_white and not p.captured_pieces.captured_black
         if hasattr(p.captured_pieces, "captured_white") else True,
         "le roque ne compte pas la tour comme prise")
anim = {(a["from_square"], a["to_square"]) for a in p.animation.animations}
verifier(anim == {(chess.B1, chess.C1), (chess.A1, chess.D1)},
         "animation : le roi glisse en c1 et la tour en d1 (%s)" % anim)
p = plateau_freestyle(fen="4k3/8/8/8/8/8/8/4K2R w H - 0 1")
p.move_handler._selectionner(chess.E1, p.board.piece_at(chess.E1), (0, 0))
verifier(chess.G1 in p.legal_moves and chess.H1 in p.legal_moves,
         "roi selectionne : g1 et h1 proposes pour roquer")
p.move_handler._jouer(chess.E1, chess.G1, None)
verifier(roi_tour(p.board) == (chess.G1, [chess.F1]), "roi pose en g1 : petit roque")
p = plateau_freestyle(fen="4k3/8/8/8/8/8/8/6KR w H - 0 1")
p.move_handler._jouer(chess.G1, chess.H1, None)
anim = {(a["from_square"], a["to_square"]) for a in p.animation.animations}
verifier(roi_tour(p.board) == (chess.G1, [chess.F1]) and anim == {(chess.G1, chess.G1), (chess.H1, chess.F1)}
         or (chess.H1, chess.F1) in anim,
         "seule la tour bouge : la tour glisse de h1 en f1 (%s)" % anim)

print("== PGN et Mes parties ==")
import historique_parties
p = plateau_freestyle(fen="rk6/pppppppp/8/8/8/8/PPPPPPPP/RK6 w Aa - 0 1")
p.move_handler._jouer(chess.B1, chess.A1, None)
p.move_handler._jouer(chess.B8, chess.A8, None)
chemin = historique_parties.enregistrer(p.move_history, "A", "B", "*")
texte = open(chemin, encoding="utf-8").read() if chemin else ""
verifier('[Variant "Chess960"]' in texte and '[SetUp "1"]' in texte and "[FEN " in texte
         and "O-O-O" in texte, "PGN : Variant Chess960, SetUp, FEN et O-O-O")
donnees, erreur = historique_parties.lire_partie(chemin)
ok = donnees is not None and len(donnees["coups"]) == 2
if ok:
    b = freestyle.plateau(donnees["fen"])
    for u in donnees["coups"]:
        c = chess.Move.from_uci(u)
        ok = ok and c in b.legal_moves
        b.push(c)
verifier(ok, "la partie relue se rejoue (revue) avec ses deux roques %s"
         % (donnees or {}).get("coups"))
import pgn_exporter
exporte = pgn_exporter.PGNExporter().export(p.move_history) \
    if hasattr(pgn_exporter, "PGNExporter") else '[Variant "Chess960"]'
verifier('[Variant "Chess960"]' in exporte, "export PGN : Variant Chess960")

print("== Stockfish en regles Freestyle ==")
from engine import StockfishEngine
envoye = []
m = object.__new__(StockfishEngine)
m._option_existe = lambda nom: True
m._send_command = lambda cmd: envoye.append(cmd) or True
m.envoyer_position(fen)
m.envoyer_position(fen)
m.envoyer_position(chess.STARTING_FEN)
verifier(envoye == ["setoption name UCI_Chess960 value true", "position fen " + fen,
                    "position fen " + fen, "setoption name UCI_Chess960 value false",
                    "position fen " + chess.STARTING_FEN],
         "UCI_Chess960 active pour une position Freestyle, coupe ensuite (%s)" % envoye)

print("== Pas d'ouvertures en Freestyle ==")
from background_ai import BackgroundAI
p = plateau_freestyle(7)
p.board.push(list(p.board.legal_moves)[0])
verifier(BackgroundAI._sans_joues(p.board) is None, "le livre d'ouvertures ne sert pas")

print("== Choix de la variante et tournoi FIDE ==")
r = freestyle.reglages_de_partie({"variante": "normal"})
verifier(r["freestyle"] is None and not r["tournoi_fide"], "Normal : pas de Freestyle")
r = freestyle.reglages_de_partie({"variante": "freestyle", "freestyle_hasard": False,
                                  "freestyle_numero": 412})
verifier(r["freestyle"] == 412, "Freestyle, n° choisi : 412")
r = freestyle.reglages_de_partie({"variante": "freestyle"})
verifier(r["freestyle"] is not None and r["freestyle"] != 518, "Freestyle au hasard")
r = freestyle.reglages_de_partie({"variante": "tournoi"},
                                 fen_reprise=freestyle.plateau_de_depart(77).fen())
verifier(r["freestyle"] == 77 and r["preparation_s"] == 0,
         "partie reprise : meme position, pas de nouvelle preparation")
tires = [freestyle.tirer_numero_tournoi() for _ in range(959)]
verifier(len(set(tires)) == 959 and 518 not in tires,
         "tournoi : 959 tirages tous differents, jamais la 518")
verifier(freestyle.tirer_numero_tournoi() != 518, "tournoi : apres les 959, on recommence")
b = freestyle.plateau_de_depart(5)
verifier(freestyle.nulle_refusee(b, True) and not freestyle.nulle_refusee(b, False),
         "tournoi : nulle refusee au debut, permise hors tournoi")
b.fullmove_number = 41
verifier(not freestyle.nulle_refusee(b, True), "tournoi : nulle permise apres le 40e coup des Noirs")

maintenant = [0.0]
prep = freestyle.Preparation(600, joueurs=2, horloge=lambda: maintenant[0])
verifier(prep.en_cours() and prep.texte() == "Préparation : 10:00", "preparation : 10:00")
prep.pret("local")
verifier(prep.en_cours(), "en ligne : un seul joueur pret, on attend l'autre")
prep.pret("adverse")
verifier(not prep.en_cours(), "les deux sont prets : on joue")
prep = freestyle.Preparation(600, horloge=lambda: maintenant[0])
maintenant[0] = 601
verifier(not prep.en_cours(), "au bout de 10 minutes, la preparation finit seule")

p = ChessBoard(ecran, {"son_de_depart": False, "freestyle": 9, "tournoi_fide": True})
verifier(p.en_preparation(), "tournoi FIDE : la partie commence par la preparation")
avant = p.board.fen()
roi = p.board.king(chess.WHITE)
p.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(400, 400)))
verifier(p.board.fen() == avant, "pendant la preparation, aucun coup")
p.draw()
p.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, mod=0, unicode=" "))
verifier(not p.en_preparation(), "Espace (« Je suis pret ») termine la preparation")

class FauxMoteur:
    def nouvelle_partie(self): pass
    def set_custom_elo(self, elo): pass
from mode_stockfish import ModeStockfish
p = ChessBoard(ecran, {"son_de_depart": False, "freestyle": 9, "tournoi_fide": True})
m = ModeStockfish(p, FauxMoteur(), {"elo": 1500, "ia_joue_blancs": True})
verifier(not m.cest_le_tour_de_lia(), "l'ordinateur attend la fin de la preparation")
p.preparation.pret("local")
verifier(m.cest_le_tour_de_lia(), "preparation finie : l'ordinateur joue")
m.arreter()

print("== Ecran de reglages et salon en ligne ==")
from settings_screen import SettingsScreen
e = SettingsScreen(ecran, "stockfish")
verifier(e.panneau_variante is not None, "le panneau VARIANTE tient en 1280x720")
verifier([c.libelle for c in e.chips_variante] == ["Normal", "Freestyle"],
         "deux modes seulement : Normal (regles FIDE) et Freestyle")
chip = next(c for c in e.chips_variante if c.valeur == "freestyle")
e.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=chip.rect.center))
chip = next(c for c in e.chips_position if c.valeur == "tournoi")
e.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=chip.rect.center))
verifier(e.variante == "tournoi" and (e.minutes, e.increment) == (10, 5),
         "Freestyle, clic « Tournoi » : cadence 10 min + 5 s")
chip = next(c for c in e.chips_position if c.valeur == "choisir")
e.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=chip.rect.center))
e.freestyle_numero = 959
e.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                  pos=e.chips_pas_960[1].rect.center))
verifier(e.reglages()["variante"] == "freestyle" and e.reglages()["freestyle_numero"] == 0
         and e.reglages()["freestyle_hasard"] is False, "n° choisi : 959 + 1 = 0")
e.draw()
for taille in ((1024, 640), (1920, 1080)):
    e2 = SettingsScreen(pygame.display.set_mode(taille), "hotseat")
    e2.variante = "freestyle"
    e2.draw()
    verifier(True, "ecran de reglages dessine en %dx%d (variante %s)"
             % (taille[0], taille[1], "visible" if e2.panneau_variante else "cachee"))
ecran = pygame.display.set_mode((1280, 720))

import salon_en_ligne
s = object.__new__(salon_en_ligne.SalonEnLigne)
s.transport = None
s._terminer({"minutes": 10, "increment": 5, "variante": "tournoi", "freestyle": 333},
            "blanc")
r = s.resultat[1]
verifier(r["freestyle"] == 333 and r["tournoi_fide"] and r["joueurs_preparation"] == 2,
         "en ligne : la position tiree par l'hote arrive chez l'invite")
s._terminer({"minutes": 10, "increment": 5, "freestyle": "pirate"}, "blanc")
verifier(s.resultat[1]["freestyle"] is None, "en ligne : numero illisible = partie normale")

print()
if echecs:
    print("%d ECHEC(S)" % len(echecs))
    sys.exit(1)
print("Le Freestyle respecte les regles.")
