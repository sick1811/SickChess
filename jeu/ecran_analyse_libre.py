# ecran_analyse_libre.py - SickChess 24/10 (travail p35, demande de Julien) :
# l'ANALYSE LIBRE.
#
#   - un echiquier ou l'on joue les deux camps (glisser ou clic-clic) ; la
#     feuille garde la suite jouee ; revenir en arriere puis jouer un autre
#     coup remplace la suite (message a l'ecran) ;
#   - EDITEUR DE POSITION (touche E) : palette des 12 pieces + gomme, clic
#     gauche pose, clic droit enleve ; Vider, Depart, trait aux Blancs / Noirs ;
#     les roques possibles sont deduits de la place des rois et des tours ;
#     une position impossible est refusee avec la raison ;
#   - COLLER un FEN ou un PGN (touche V), COPIER le FEN (touche C) ;
#   - MOTEUR EN CONTINU (Espace : marche / arret) : barre d'avantage,
#     evaluation, profondeur, les 3 meilleures lignes et leurs fleches. Le
#     calcul s'approfondit tout seul (de 0,25 s a 6 s par passe) puis se repose
#     au bout de 90 s sur la meme position (processeur). Stockfish en priorite
#     basse, tables de finale branchees comme pour la revue, ferme en sortant.
#   - ouvert aussi depuis la revue (touche A) sur la position affichee.
#
# Commandes : fleches / molette = coups, Debut / Fin, Retour arriere = coup
# precedent, F = retourner, Espace = moteur, E = editer, V = coller,
# C = copier le FEN, Echap = retour (ou quitter l'editeur).

import io
import os
import threading
import time

import chess
import chess.pgn
import pygame

import annotations
import apparence
import board_geometry as geo
import retournement
import ui
from board import ChessBoard
from ecran_revue import DispositionRevue

ETAPES_MS = (250, 700, 1500, 3000, 6000)
REPOS_APRES_S = 90
INDICE_MOTEUR = 6                       # son propre Stockfish (moteurs.py)
LIGNES = 3
BLEUS = [((70, 145, 235, 215), 0.12), ((110, 170, 240, 140), 0.08),
         ((150, 190, 245, 110), 0.07)]
PALETTE = ["K", "Q", "R", "B", "N", "P", "k", "q", "r", "b", "n", "p"]

RAISONS = [
    (chess.STATUS_NO_WHITE_KING, "il manque le roi blanc"),
    (chess.STATUS_NO_BLACK_KING, "il manque le roi noir"),
    (chess.STATUS_TOO_MANY_KINGS, "il y a trop de rois"),
    (chess.STATUS_TOO_MANY_WHITE_PAWNS, "plus de 8 pions blancs"),
    (chess.STATUS_TOO_MANY_BLACK_PAWNS, "plus de 8 pions noirs"),
    (chess.STATUS_PAWNS_ON_BACKRANK, "un pion est sur la première ou la dernière rangée"),
    (chess.STATUS_TOO_MANY_WHITE_PIECES, "trop de pièces blanches"),
    (chess.STATUS_TOO_MANY_BLACK_PIECES, "trop de pièces noires"),
    (chess.STATUS_OPPOSITE_CHECK, "le camp qui n'a pas le trait est en échec"),
    (chess.STATUS_TOO_MANY_CHECKERS, "le roi est en échec par trop de pièces"),
    (chess.STATUS_IMPOSSIBLE_CHECK, "cet échec est impossible"),
]


def raison_invalide(board):
    """Pourquoi une position est impossible (texte), ou "" si elle est valable."""
    statut = board.status()
    if statut == chess.STATUS_VALID:
        return ""
    for drapeau, texte in RAISONS:
        if statut & drapeau:
            return texte
    return "position impossible"


def position_depuis_texte(texte):
    """FEN ou PGN colle -> (board_de_depart, [coups]) ; None si illisible."""
    texte = (texte or "").strip()
    if not texte:
        return None
    try:
        b = chess.Board(texte)
        if b.is_valid():
            return b, []
    except ValueError:
        pass
    try:
        partie = chess.pgn.read_game(io.StringIO(texte))
    except Exception:
        partie = None
    if partie is None:
        return None
    depart = partie.board()
    coups = list(partie.mainline_moves())
    if not coups and not partie.headers.get("FEN"):
        return None
    return depart, coups


def suite_en_notation(fen, ucis, maximum=8):
    """['e2e4', 'e7e5'...] depuis fen -> '1. e4 e5 2. Cf3' (notation choisie)."""
    import notation
    b = chess.Board(fen)
    morceaux = []
    for i, u in enumerate(list(ucis)[:maximum]):
        try:
            coup = chess.Move.from_uci(u)
        except ValueError:
            break
        if coup not in b.legal_moves:
            break
        san = notation.afficher(b.san(coup)) if hasattr(notation, "afficher") else b.san(coup)
        if b.turn == chess.WHITE:
            morceaux.append("%d. %s" % (b.fullmove_number, san))
        elif i == 0:
            morceaux.append("%d... %s" % (b.fullmove_number, san))
        else:
            morceaux.append(san)
        b.push(coup)
    return " ".join(morceaux)


def texte_eval(evaluation, mat):
    if mat is not None:
        return "Mat" if mat == 0 else ("M%d" % abs(mat) if mat > 0 else "-M%d" % abs(mat))
    if evaluation is None:
        return "..."
    return "%+.2f" % evaluation


# ---------------------------------------------------------------- moteur

class MoteurContinu:
    """Analyse la position demandee en tache de fond, de plus en plus fort.

    moteur : un moteur deja pret (tests) ; sinon le Stockfish d'analyse n° 7
    de moteurs.py, cree a la premiere demande."""

    def __init__(self, chemin=None, moteur=None):
        self.chemin = chemin
        self._fourni = moteur
        self._moteur = moteur
        self._verrou = threading.Lock()
        self._fen = None
        self._version = 0
        self._resultat = None             # {"fen", "lignes", "profondeur"}
        self.actif = True
        self.au_repos = False
        self.erreur = ""
        self._fini = False
        self._thread = None

    # -- commandes (fil du jeu)
    def demander(self, fen):
        if fen == self._fen:
            return
        self._fen = fen
        self._version += 1
        self.au_repos = False
        self._interrompre()
        self._demarrer()

    def basculer(self):
        self.actif = not self.actif
        if not self.actif:
            self._interrompre()
        else:
            self.au_repos = False
            self._version += 1
        return self.actif

    def info(self, fen):
        r = self._resultat
        return r if r is not None and r["fen"] == fen else None

    def arreter(self):
        self._fini = True
        self._interrompre()
        if self._fourni is None:
            try:
                import moteurs
                threading.Thread(target=moteurs.liberer,
                                 args=(moteurs.role_d_analyse(INDICE_MOTEUR),),
                                 daemon=True).start()
            except Exception:
                pass

    # -- interne
    def _demarrer(self):
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._boucle, daemon=True)
            self._thread.start()

    def _interrompre(self):
        """Arrete la recherche en cours tout de suite (« stop » ecrit
        directement : le verrou du moteur est tenu par la recherche)."""
        m = self._moteur
        processus = getattr(m, "process", None)
        if processus is None:
            if hasattr(m, "interrompre"):
                m.interrompre()
            return
        try:
            processus.stdin.write("stop\n")
            processus.stdin.flush()
        except Exception:
            pass

    def _obtenir_moteur(self):
        if self._moteur is not None:
            return self._moteur
        try:
            import moteurs
            threads = max(1, (os.cpu_count() or 2) - 2)
            self._moteur = moteurs.moteur_d_analyse_n(INDICE_MOTEUR, self.chemin,
                                                      threads=threads, hash_mb=512)
        except Exception as souci:
            self.erreur = "Stockfish indisponible : %s" % souci
        if self._moteur is None and not self.erreur:
            self.erreur = "Stockfish indisponible (moteur/stockfish.exe)."
        return self._moteur

    def _boucle(self):
        import analyse_partie
        while not self._fini:
            fen, version = self._fen, self._version
            if fen is None or not self.actif or self.au_repos \
                    or chess.Board(fen).is_game_over():
                time.sleep(0.05)
                continue
            moteur = self._obtenir_moteur()
            if moteur is None:
                time.sleep(0.5)
                continue
            debut = time.time()
            etape = 0
            while not self._fini and self.actif and version == self._version:
                if time.time() - debut > REPOS_APRES_S:
                    self.au_repos = True          # le processeur se repose
                    break
                ms = ETAPES_MS[min(etape, len(ETAPES_MS) - 1)]
                try:
                    details = moteur.analyser_position(fen, 0, ms, lignes=LIGNES)
                except Exception as souci:
                    self.erreur = "Stockfish : %s" % souci
                    details = None
                if version != self._version or self._fini:
                    break
                lignes = analyse_partie.lignes_du_moteur(fen, details)
                if lignes:
                    self._resultat = {"fen": fen, "lignes": lignes,
                                      "profondeur": (details or {}).get("profondeur", 0)}
                    self.erreur = ""
                elif details is None:
                    time.sleep(0.2)
                etape += 1


# ---------------------------------------------------------------- ecran

class EcranAnalyseLibre:
    def __init__(self, screen, preferences=None, chemin_stockfish=None, fen=None,
                 coups=None, moteur=None, cote_noir=False):
        self.screen = screen
        prefs = dict(preferences or {})
        self.prefs = prefs
        self.disposition = DispositionRevue(*screen.get_size())
        self.plateau = ChessBoard(screen, {"pendule_active": False,
                                           "son_de_depart": False,
                                           "theme_plateau": prefs.get("theme_plateau"),
                                           "jeu_pieces": prefs.get("jeu_pieces")},
                                  self.disposition)
        p = self.plateau
        p.changer_apparence(prefs.get("theme_plateau"), prefs.get("jeu_pieces"))
        p.renderer.afficher_coordonnees = bool(prefs.get("afficher_coordonnees", True))
        p.sounds.set_volume(float(prefs.get("volume_sons", 0.6)))
        p.sounds.actif = bool(prefs.get("sons_actifs", True))
        vitesse = float(prefs.get("vitesse_animation", 0.18))
        p.animation.duree = max(0.01, vitesse)
        p.animation.active = vitesse > 0
        p.flipped = bool(cote_noir)
        p.hotseat_mode = True
        p.premouvement_actif = False
        p.make_move = self._coup_joue

        try:
            self.depart = chess.Board(fen) if fen else chess.Board()
        except ValueError:
            self.depart = chess.Board()
        self.coups = list(coups or [])
        self.index = len(self.coups)
        self.moteur = MoteurContinu(chemin_stockfish, moteur)
        self.edition = None               # {"board": chess.Board, "piece": "Q" | None}
        self.message = ""
        self.message_fin = 0
        self.rects_coups = []
        self.rects_palette = []
        self.premiere_ligne = 0

        def b(texte, cle, taille=15, gras=False):
            return ui.Bouton((0, 0, 10, 10), texte, cle, taille=taille, gras=gras)
        self.boutons_nav = [ui.Bouton((0, 0, 10, 10), s, c, taille=18)
                            for s, c in (("|<", "debut"), ("<", "precedent"),
                                         (">", "suivant"), (">|", "fin"))]
        self.btn_editer = b("Éditer (E)", "editer")
        self.btn_coller = b("Coller FEN / PGN (V)", "coller")
        self.btn_copier = b("Copier FEN (C)", "copier")
        self.btn_moteur = b("Moteur : marche (Espace)", "moteur")
        self.btn_retourner = b("Retourner (F)", "retourner")
        self.btn_retour = b("Retour", "retour", 16, True)
        self.boutons_analyse = self.boutons_nav + [
            self.btn_editer, self.btn_coller, self.btn_copier, self.btn_moteur,
            self.btn_retourner, self.btn_retour]
        self.btn_vider = b("Vider", "vider")
        self.btn_depart = b("Départ", "depart")
        self.btn_trait = b("Trait : Blancs", "trait")
        self.btn_gomme = b("Gomme", "gomme")
        self.btn_valider = b("Valider", "valider", 16, True)
        self.btn_annuler = b("Annuler", "annuler", 16)
        self.boutons_edition = [self.btn_vider, self.btn_depart, self.btn_trait,
                                self.btn_gomme, self.btn_valider, self.btn_annuler]
        self._placer()
        self.aller_a(self.index, son=False)

    # ------------------------------------------------------------- position

    def fen(self):
        return self.plateau.board.fen()

    def aller_a(self, index, son=True):
        index = max(0, min(len(self.coups), int(index)))
        p = self.plateau
        avant = self.depart.copy()
        for coup in self.coups[:max(0, index - 1)]:
            avant.push(coup)
        p.board = avant.copy()
        if index:
            p.board.push(self.coups[index - 1])
        avance = index == self.index + 1
        self.index = index
        p.animation.clear()
        p.selected_square = None
        if index:
            dernier = self.coups[index - 1]
            p.last_move_highlight.set_last_move(dernier.from_square, dernier.to_square)
            p.highlights.set_last_move(dernier.from_square, dernier.to_square)
        else:
            p.last_move_highlight.clear()
            p.highlights.clear()
        p.highlights.set_case_echec(p.board.king(p.board.turn)
                                    if p.board.is_check() else None)
        if avance and son:
            dernier = self.coups[index - 1]
            prise = avant.piece_at(dernier.to_square)
            if avant.is_en_passant(dernier):
                prise = chess.Piece(chess.PAWN, not avant.turn)
            p.animation.start_animation(dernier.from_square, dernier.to_square,
                                        p.board.piece_at(dernier.to_square), p.SQ_SIZE)
            p._jouer_son_du_coup(dernier, avant.piece_at(dernier.from_square), prise,
                                 avant.is_castling(dernier), avant.is_en_passant(dernier))
        self.moteur.demander(p.board.fen())
        self._suivre_le_coup()

    def _coup_joue(self, move, engine=None):
        """Un coup joue a la souris (les deux camps)."""
        p = self.plateau
        if self.edition is not None or move not in p.board.legal_moves:
            return False
        if self.index < len(self.coups) and move == self.coups[self.index]:
            self.aller_a(self.index + 1)
            return True
        remplaces = len(self.coups) - self.index
        if not ChessBoard.make_move(p, move, engine):
            return False
        del self.coups[self.index:]
        self.coups.append(move)
        self.index = len(self.coups)
        if remplaces:
            self._afficher_message("Nouvelle suite : %d coup(s) suivant(s) remplacé(s)."
                                   % remplaces)
        p.highlights.set_case_echec(p.board.king(p.board.turn)
                                    if p.board.is_check() else None)
        self.moteur.demander(p.board.fen())
        self._suivre_le_coup()
        return True

    def charger(self, depart, coups=()):
        self.depart = depart.copy()
        self.coups = list(coups)
        self.index = len(self.coups)
        self.aller_a(self.index, son=False)

    # ------------------------------------------------------------- edition

    def ouvrir_edition(self):
        b = self.plateau.board.copy(stack=False)
        self.edition = {"board": b, "piece": "Q"}
        self.plateau.fleches_conseil = []
        self._maj_trait()

    def _maj_trait(self):
        if self.edition is not None:
            blancs = self.edition["board"].turn == chess.WHITE
            self.btn_trait.libelle = "Trait : Blancs" if blancs else "Trait : Noirs"

    def poser(self, case, symbole):
        """Pose (ou enleve si symbole None) une piece dans l'editeur."""
        b = self.edition["board"]
        if symbole is None or (b.piece_at(case) and b.piece_at(case).symbol() == symbole):
            b.remove_piece_at(case)
        else:
            b.set_piece_at(case, chess.Piece.from_symbol(symbole))

    def valider_edition(self):
        b = self.edition["board"].copy(stack=False)
        b.ep_square = None
        b.set_castling_fen("KQkq")
        b.castling_rights = b.clean_castling_rights()
        b.halfmove_clock = 0
        b.fullmove_number = 1
        raison = raison_invalide(b)
        if raison:
            self._afficher_message("Position impossible : %s." % raison, 6)
            return False
        self.edition = None
        self.charger(b)
        self._afficher_message("Position chargée : le moteur l'analyse.")
        return True

    # ------------------------------------------------------------- placement

    def _placer(self, screen=None):
        if screen is not None:
            self.screen = screen
            self.plateau.screen = screen
        self.disposition.recalculer(*self.screen.get_size())
        p = self.plateau
        if p.SQ_SIZE != self.disposition.taille_case:
            p.SQ_SIZE = self.disposition.taille_case
            p.load_piece_images()
        p.disposition = self.disposition
        ech = ui.echelle(self.screen)
        self.ech = ech
        panneau = pygame.Rect(*self.disposition.rect_panneau())
        self.panneau = panneau
        x = panneau.x + int(14 * ech)
        l = panneau.width - int(28 * ech)
        self.x, self.l = x, l
        espace = int(8 * ech)
        h = int(36 * ech)
        bas = panneau.bottom - int(12 * ech)
        demi = (l - espace) // 2
        tiers = (l - 2 * espace) // 3

        # mode analyse
        self.btn_retourner.placer((x, bas - h, demi, h))
        self.btn_retour.placer((x + demi + espace, bas - h, l - demi - espace, h))
        y = bas - h - espace
        self.btn_copier.placer((x, y - h, demi, h))
        self.btn_moteur.placer((x + demi + espace, y - h, l - demi - espace, h))
        y -= h + espace
        self.btn_editer.placer((x, y - h, demi, h))
        self.btn_coller.placer((x + demi + espace, y - h, l - demi - espace, h))
        y -= h + espace
        h_nav = int(40 * ech)
        lb = (l - 3 * int(6 * ech)) // 4
        for i, bouton in enumerate(self.boutons_nav):
            bouton.placer((x + i * (lb + int(6 * ech)), y - h_nav, lb, h_nav))
        self.bas_analyse = y - h_nav - espace

        # mode edition
        self.btn_valider.placer((x, bas - h, demi, h))
        self.btn_annuler.placer((x + demi + espace, bas - h, l - demi - espace, h))
        y = bas - h - espace
        for i, bouton in enumerate((self.btn_vider, self.btn_depart, self.btn_gomme)):
            bouton.placer((x + i * (tiers + espace), y - h, tiers, h))
        y -= h + espace
        self.btn_trait.placer((x, y - h, l, h))
        self.bas_edition = y - h - espace

        haut = panneau.y + int(12 * ech)
        self.zone_titre = pygame.Rect(x, haut, l, int(46 * ech))
        y = self.zone_titre.bottom + espace
        self.zone_moteur = pygame.Rect(x, y, l, int(150 * ech))
        y = self.zone_moteur.bottom + espace
        self.zone_coups = pygame.Rect(x, y, l, max(int(40 * ech), self.bas_analyse - y))
        self.taille_coup = ui.t(14, ech)
        self.hauteur_ligne = ui.police(self.taille_coup, mono=True).get_height() + int(5 * ech)
        self.lignes_visibles = max(1, (self.zone_coups.height - int(10 * ech))
                                   // self.hauteur_ligne)
        # palette de l'editeur (2 rangees de 6)
        cote = max(24, min(int(56 * ech), (l - 5 * int(6 * ech)) // 6))
        self.rects_palette = []
        y0 = self.zone_titre.bottom + espace + int(26 * ech)
        for i, symbole in enumerate(PALETTE):
            rangee, col = divmod(i, 6)
            self.rects_palette.append((pygame.Rect(x + col * (cote + int(6 * ech)),
                                                   y0 + rangee * (cote + int(6 * ech)),
                                                   cote, cote), symbole))
        self._suivre_le_coup()

    def _ligne_du_coup(self, index):
        return (index + (1 if self.depart.turn == chess.BLACK else 0)) // 2

    def _suivre_le_coup(self):
        if not hasattr(self, "lignes_visibles") or not self.index:
            self.premiere_ligne = 0
            return
        ligne = self._ligne_du_coup(self.index - 1)
        if ligne < self.premiere_ligne:
            self.premiere_ligne = ligne
        elif ligne >= self.premiere_ligne + self.lignes_visibles:
            self.premiere_ligne = ligne - self.lignes_visibles + 1

    # ------------------------------------------------------------- evenements

    def _afficher_message(self, texte, secondes=5):
        self.message = texte
        self.message_fin = pygame.time.get_ticks() + int(secondes * 1000)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return "quitter"
        if self.edition is not None:
            return self._evenement_edition(event)
        p = self.plateau
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            d = self.disposition
            sur = pygame.Rect(d.plateau_x, d.plateau_y, d.cote_plateau,
                              d.cote_plateau).collidepoint(event.pos)
            if sur or p.dragging or p.selected_square is not None or p.promotion.est_actif():
                p.handle_event(event)
                if event.type != pygame.MOUSEMOTION:
                    return None
        action = None
        if event.type == pygame.KEYDOWN:
            if (p.selected_square is not None or p.dragging) and event.key == pygame.K_ESCAPE:
                p.handle_event(event)
                return None
            action = {pygame.K_LEFT: "precedent", pygame.K_BACKSPACE: "precedent",
                      pygame.K_RIGHT: "suivant", pygame.K_HOME: "debut",
                      pygame.K_END: "fin", pygame.K_UP: "debut", pygame.K_DOWN: "fin",
                      pygame.K_f: "retourner", pygame.K_SPACE: "moteur",
                      pygame.K_e: "editer", pygame.K_v: "coller", pygame.K_c: "copier",
                      pygame.K_ESCAPE: "retour"}.get(event.key)
        elif event.type == pygame.MOUSEWHEEL:
            action = "precedent" if getattr(event, "y", 0) > 0 else "suivant"
        else:
            action = ui.gerer_boutons(self.boutons_analyse, event)
            if action is None and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, index in self.rects_coups:
                    if rect.collidepoint(event.pos):
                        self.aller_a(index + 1, son=False)
                        return None
        return self.executer(action)

    def executer(self, action):
        if action == "retour":
            return "retour"
        if action == "precedent":
            self.aller_a(self.index - 1, son=False)
        elif action == "suivant":
            self.aller_a(self.index + 1)
        elif action == "debut":
            self.aller_a(0, son=False)
        elif action == "fin":
            self.aller_a(len(self.coups), son=False)
        elif action == "retourner":
            retournement.retourner(self.plateau, self.plateau.board, self.plateau.SQ_SIZE)
        elif action == "moteur":
            actif = self.moteur.basculer()
            self._afficher_message("Moteur en marche." if actif else
                                   "Moteur arrêté : le processeur se repose.")
        elif action == "editer":
            self.ouvrir_edition()
        elif action == "copier":
            ok = ui.copier(self.fen())
            self._afficher_message("FEN copié." if ok else "Copie impossible : %s" % self.fen(), 6)
        elif action == "coller":
            self.coller(ui.coller())
        return None

    def coller(self, texte):
        lu = position_depuis_texte(texte)
        if lu is None:
            self._afficher_message("Rien de lisible : copie d'abord un FEN ou un PGN.", 6)
            return False
        depart, coups = lu
        self.charger(depart, coups)
        self._afficher_message("Partie collée : %d coup(s)." % len(coups) if coups
                               else "Position collée.")
        return True

    def _evenement_edition(self, event):
        p = self.plateau
        e = self.edition
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.edition = None
                self.aller_a(self.index, son=False)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.valider_edition()
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            case = geo.pixel_vers_case(event.pos, p.SQ_SIZE, p.flipped)
            if case is not None:
                self.poser(case, None if event.button == 3 else e["piece"])
                return None
            if event.button == 1:
                for rect, symbole in self.rects_palette:
                    if rect.collidepoint(event.pos):
                        e["piece"] = symbole
                        return None
        action = ui.gerer_boutons(self.boutons_edition, event)
        if action == "vider":
            e["board"].clear_board()
        elif action == "depart":
            e["board"] = chess.Board()
            self._maj_trait()
        elif action == "trait":
            e["board"].turn = not e["board"].turn
            self._maj_trait()
        elif action == "gomme":
            e["piece"] = None
        elif action == "valider":
            self.valider_edition()
        elif action == "annuler":
            self.edition = None
            self.aller_a(self.index, son=False)
        return None

    # ------------------------------------------------------------- dessin

    def _lignes_affichees(self):
        """[(evaluation, mat, uci, texte_suite)] des lignes du moteur."""
        b = self.plateau.board
        info = self.moteur.info(b.fen())
        if info is None:
            return [], 0
        sortie = []
        for uci, evaluation, mat, suite in info["lignes"][:LIGNES]:
            sortie.append((evaluation, mat, uci, suite_en_notation(b.fen(), suite or [uci])))
        return sortie, info.get("profondeur", 0)

    def draw(self):
        ecran = self.screen
        p = self.plateau
        t = apparence.theme(p.theme_plateau)
        ech = self.ech
        p.animation.update()
        p.retournement.update()
        p.fleches_conseil = []
        lignes, profondeur = ([], 0) if self.edition is not None else self._lignes_affichees()
        if self.moteur.actif:
            for n, (_, _, uci, _) in enumerate(lignes):
                try:
                    coup = chess.Move.from_uci(uci)
                except ValueError:
                    continue
                couleur, epaisseur = BLEUS[min(n, len(BLEUS) - 1)]
                p.fleches_conseil.append((coup.from_square, coup.to_square, couleur, epaisseur))
        if self.edition is not None:
            vrai = p.board
            p.board = self.edition["board"]
            p.last_move_highlight.clear()
            p.highlights.clear()
        ecran.fill(t["fond"])
        p.renderer.dessiner_plateau(avec_interaction=self.edition is None)
        if self.edition is not None:
            p.board = vrai
        else:
            self._dessiner_barre(ecran, t, ech, lignes)
        ui.cadre(ecran, self.panneau, t["panneau"], t["bord"], 1, 14)
        self._dessiner_titre(ecran, t, ech)
        souris = pygame.mouse.get_pos()
        if self.edition is not None:
            self._dessiner_palette(ecran, t, ech)
            boutons = self.boutons_edition
        else:
            self._dessiner_moteur(ecran, t, ech, lignes, profondeur)
            self._dessiner_feuille(ecran, t, ech)
            self.btn_moteur.libelle = ("Moteur : marche (Espace)" if self.moteur.actif
                                       else "Moteur : arrêt (Espace)")
            self.boutons_nav[0].actif = self.boutons_nav[1].actif = self.index > 0
            self.boutons_nav[2].actif = self.boutons_nav[3].actif = self.index < len(self.coups)
            boutons = self.boutons_analyse
        for bouton in boutons:
            bouton.maj_survol(souris)
            bouton.dessiner(ecran, t, rayon=10)

    def _dessiner_titre(self, ecran, t, ech):
        z = self.zone_titre
        titre = "Éditeur de position" if self.edition is not None else "Analyse libre"
        ui.texte(ecran, titre, z.x, z.y, ui.t(17, ech), t["texte"], gras=True,
                 largeur_max=z.width, ajuster=True)
        y = z.y + ui.police(ui.t(17, ech), True).get_height() + int(4 * ech)
        if self.message and pygame.time.get_ticks() < self.message_fin:
            texte, couleur = self.message, t["accent"]
        elif self.edition is not None:
            texte, couleur = "Clic gauche : poser · clic droit : enlever", t["texte_discret"]
        else:
            b = self.plateau.board
            texte = "Trait aux Blancs" if b.turn == chess.WHITE else "Trait aux Noirs"
            couleur = t["texte_discret"]
        ui.texte(ecran, texte, z.x, y, ui.t(12, ech), couleur, largeur_max=z.width)

    def _dessiner_barre(self, ecran, t, ech, lignes):
        barre = self.disposition.barre
        b = self.plateau.board
        evaluation, mat = (lignes[0][0], lignes[0][1]) if lignes else (0.0, None)
        if b.is_checkmate():
            evaluation, mat = (-20.0 if b.turn == chess.WHITE else 20.0), 0
        elif b.is_game_over():
            evaluation, mat = 0.0, None
        chances = annotations.chances_de_gagner(evaluation) / 100.0
        pygame.draw.rect(ecran, (58, 56, 52), barre, border_radius=4)
        h_blanc = int(barre.height * chances)
        if self.plateau.flipped:
            blanc = pygame.Rect(barre.x, barre.y, barre.width, h_blanc)
        else:
            blanc = pygame.Rect(barre.x, barre.bottom - h_blanc, barre.width, h_blanc)
        pygame.draw.rect(ecran, (232, 229, 220), blanc, border_radius=4)
        pygame.draw.rect(ecran, t["bord"], barre, 1, border_radius=4)
        if not lignes and not b.is_game_over():
            return
        texte = texte_eval(evaluation, mat).lstrip("+-")
        try:
            texte = "%.1f" % float(texte)
        except ValueError:
            pass
        taille = ui.t(10, ech)
        cote_blanc = evaluation >= 0
        en_bas = cote_blanc != self.plateau.flipped
        y = barre.bottom - ui.police(taille, True).get_height() - 3 if en_bas else barre.y + 3
        couleur = (40, 38, 34) if cote_blanc else (232, 229, 220)
        ui.texte(ecran, texte, barre.centerx, y, taille, couleur, gras=True,
                 ancre="centre", largeur_max=barre.width + 4, ajuster=True)

    def _dessiner_moteur(self, ecran, t, ech, lignes, profondeur):
        z = self.zone_moteur
        ui.cadre(ecran, z, t["panneau_clair"] if "panneau_clair" in t else t["panneau"],
                 t["bord"], 1, 10)
        x, y, l = z.x + int(10 * ech), z.y + int(8 * ech), z.width - int(20 * ech)
        b = self.plateau.board
        if b.is_checkmate():
            entete = "Échec et mat"
        elif b.is_stalemate():
            entete = "Pat : partie nulle"
        elif b.is_insufficient_material():
            entete = "Nulle : matériel insuffisant"
        elif not self.moteur.actif:
            entete = "Moteur arrêté (Espace pour le relancer)"
        elif self.moteur.erreur and not lignes:
            entete = self.moteur.erreur
        elif not lignes:
            entete = "Le moteur réfléchit…"
        else:
            entete = "%s   ·   profondeur %d%s" % (
                texte_eval(lignes[0][0], lignes[0][1]), profondeur,
                "   ·   au repos" if self.moteur.au_repos else "")
        ui.texte(ecran, entete, x, y, ui.t(16, ech), t["texte"], gras=True,
                 largeur_max=l, ajuster=True)
        y += ui.police(ui.t(16, ech), True).get_height() + int(8 * ech)
        if not self.moteur.actif:
            return
        for evaluation, mat, _, suite in lignes:
            ui.texte(ecran, texte_eval(evaluation, mat), x, y, ui.t(13, ech), t["accent"],
                     gras=True, mono=True, largeur_max=int(64 * ech))
            ui.texte(ecran, suite, x + int(70 * ech), y, ui.t(13, ech), t["texte"],
                     largeur_max=l - int(70 * ech))
            y += ui.police(ui.t(13, ech)).get_height() + int(8 * ech)

    def _dessiner_feuille(self, ecran, t, ech):
        z = self.zone_coups
        ui.cadre(ecran, z, t["panneau"], t["bord"], 1, 10)
        self.rects_coups = []
        if not self.coups:
            ui.texte(ecran, "Joue des coups sur l'échiquier (les deux camps).",
                     z.x + int(10 * ech), z.y + int(8 * ech), ui.t(12, ech),
                     t["texte_discret"], largeur_max=z.width - int(20 * ech))
            return
        b = self.depart.copy()
        sans = []
        for coup in self.coups:
            sans.append(b.san(coup))
            b.push(coup)
        import notation
        decale = 1 if self.depart.turn == chess.BLACK else 0
        numero0 = self.depart.fullmove_number
        police = ui.police(self.taille_coup, mono=True)
        col = (z.width - int(20 * ech)) // 2
        y = z.y + int(6 * ech)
        total = (len(sans) + decale + 1) // 2
        for ligne in range(self.premiere_ligne, min(total, self.premiere_ligne + self.lignes_visibles)):
            x = z.x + int(10 * ech)
            ui.texte(ecran, "%d." % (numero0 + ligne), x, y, self.taille_coup,
                     t["texte_discret"], mono=True)
            for c in range(2):
                i = ligne * 2 + c - decale
                if i < 0 or i >= len(sans):
                    continue
                texte = notation.afficher(sans[i]) if hasattr(notation, "afficher") else sans[i]
                xx = x + int(44 * ech) + c * (col - int(22 * ech))
                rect = pygame.Rect(xx - 4, y - 2, col - int(30 * ech), police.get_height() + 4)
                if i == self.index - 1:
                    pygame.draw.rect(ecran, t["accent"], rect, border_radius=4)
                    couleur = t["fond"]
                else:
                    couleur = t["texte"]
                ui.texte(ecran, texte, xx, y, self.taille_coup, couleur, mono=True,
                         largeur_max=rect.width)
                self.rects_coups.append((rect, i))
            y += self.hauteur_ligne

    def _dessiner_palette(self, ecran, t, ech):
        e = self.edition
        z = self.zone_titre
        ui.texte(ecran, "Pièce à poser :", z.x, z.bottom + int(6 * ech), ui.t(13, ech),
                 t["texte_discret"])
        images = self.plateau.piece_images
        for rect, symbole in self.rects_palette:
            choisi = e["piece"] == symbole
            # fond clair (comme une case claire) : les pieces noires se voient
            pygame.draw.rect(ecran, (214, 209, 198), rect, border_radius=6)
            pygame.draw.rect(ecran, t["accent"] if choisi else t["bord"], rect,
                             4 if choisi else 1, border_radius=6)
            image = images.get(symbole)
            if image is not None:
                cle = (symbole, rect.width, id(image))
                cache = self.__dict__.setdefault("_cache_palette", {})
                if cle not in cache:          # mis a l'echelle une seule fois
                    cache[cle] = pygame.transform.smoothscale(
                        image, (rect.width - 6, rect.height - 6))
                ecran.blit(cache[cle], (rect.x + 3, rect.y + 3))
        self.btn_gomme.selectionne = e["piece"] is None
        if self.rects_palette:
            y = self.rects_palette[-1][0].bottom + int(14 * ech)
            ui.texte(ecran, "Les roques possibles sont déduits de la place des rois et des tours.",
                     z.x, y, ui.t(12, ech), t["texte_discret"], largeur_max=self.l)

    # ------------------------------------------------------------- boucle

    def run(self, clock, evenement_fenetre=None, apres_dessin=None):
        """Renvoie 'retour' ou 'quitter'."""
        try:
            cadence = ui.Cadence()
            while True:
                evenements = pygame.event.get()
                for event in evenements:
                    if evenement_fenetre is not None and evenement_fenetre(event):
                        self._placer(pygame.display.get_surface())
                        continue
                    reponse = self.handle_event(event)
                    if reponse is not None:
                        return reponse
                self.draw()
                if apres_dessin is not None:
                    apres_dessin(self.screen)
                pygame.display.flip()
                anime = bool(getattr(self.plateau.animation, "animations", None))
                clock.tick(cadence.suivante(evenements, anime))
        finally:
            self.moteur.arreter()
