# ecran_problemes.py - SickChess : l'ecran des problemes d'echecs.
#
# Reecrit a partir de ecran_puzzles.py de V8_TURBO_3000 (1377 lignes, plus
# plateau_simple.py). Ici, PAS DE PLATEAU MAISON : on reprend le vrai plateau
# de la partie (ChessBoard), donc glisser-deposer, clic-clic, fleches au clic
# droit, pre-mouvement, promotion, animations, sons et retournement (F) sont
# exactement ceux de la partie. Seul make_move() est intercepte : un coup du
# joueur n'est joue que s'il est le bon.
#
# Deroulement :
#   1. ecran de choix : mode CLASSE (ton classement, enregistre) ou LIBRE
#      (niveau de depart au choix, rien n'est enregistre), + filtre de themes ;
#   2. le coup de l'adversaire est joue tout seul, puis c'est a toi ;
#   3. faux : le plateau clignote en rouge, on te dit ce qui cloche (sans la
#      solution) et tu peux reessayer - mais le probleme compte comme rate ;
#   4. juste du premier coup : vert, puis le suivant arrive tout seul ;
#   5. une fois fini, on se promene dans la solution (fleches, Debut/Fin).
# Touches : H indice (coute 8 points), Espace/Entree probleme suivant,
# F retourner, fleches = solution, Echap = retour.
#
# Pas repris de V8 : la voix (trop robotique), le classement en ligne par le
# relais bore.pub (il reviendra avec les classements Steam).

import chess
import pygame

import apparence
import explication_puzzle
import puzzles
import notation
import ui
from board import ChessBoard
from layout import Disposition
from move_history import MoveHistory

PAUSE_ADVERSE = 550        # ms avant que l'adversaire joue
PAUSE_REUSSITE = 900       # ms avant d'enchainer apres une reussite
PAUSE_FAUTE = 2200         # 24/10 (Cowork, t52) : le temps de voir le bon coup
DUREE_FLASH = 600          # clignotement rouge / vert du plateau
DUREE_FONDU = 240          # fondu d'arrivee d'un nouveau probleme

NIVEAUX = [600, 800, 1000, 1200, 1500, 1800, 2100, 2500]
PAS_DE_NIVEAU = 50

VERT = (120, 200, 125)
ROUGE = (232, 118, 108)
AMBRE = (232, 196, 118)


class PlateauProbleme(ChessBoard):
    """Le plateau de la partie, mais qui demande a l'ecran si le coup est bon."""

    def __init__(self, screen, preferences, disposition, ecran):
        prefs = dict(preferences or {})
        ChessBoard.__init__(self, screen, {
            "pendule_active": False, "son_de_depart": False,
            "theme_plateau": prefs.get("theme_plateau"),
            "jeu_pieces": prefs.get("jeu_pieces"),
            "premouvement": prefs.get("premouvement", True)}, disposition)
        self.ecran = ecran
        self.ui_manager = None              # pas de bouton Abandonner ici
        self.changer_apparence(prefs.get("theme_plateau"), prefs.get("jeu_pieces"))
        self.renderer.afficher_coordonnees = bool(prefs.get("afficher_coordonnees", True))
        self.sounds.set_volume(float(prefs.get("volume_sons", 0.6)))
        self.sounds.actif = bool(prefs.get("sons_actifs", True))
        vitesse = float(prefs.get("vitesse_animation", 0.18))
        self.animation.duree = max(0.01, vitesse)
        self.animation.active = vitesse > 0

    def make_move(self, move, engine=None):
        a_nous = self.couleur_joueur is not None \
            and self.board.turn == self.couleur_joueur
        if a_nous and move in self.board.legal_moves and not self.ecran.juger(move):
            self.ecran.refuser(move)
            return False
        position_avant = self.board.copy()
        if not ChessBoard.make_move(self, move, engine):
            return False
        if a_nous:
            self.ecran.apres_bon_coup(move, position_avant)
        return True

    def demander_indice(self, engine=None, temps_ms=0):
        """Touche H : l'indice du probleme, pas celui de Stockfish."""
        self.ecran.demander_un_indice()
        return None

    def update(self):
        """Ni pendule ni fin de partie : c'est l'ecran qui arbitre."""
        self.animation.update()
        self.retournement.update()
        echec = self.board.king(self.board.turn) if self.board.is_check() else None
        self.highlights.set_case_echec(echec)
        if not self.game_over:
            self.jouer_premouvement()


class EcranProblemes:
    def __init__(self, screen, preferences=None, mode=None, depart=None, themes=None):
        self.screen = screen
        self.preferences = dict(preferences or {})
        self.themes = set(themes or ())
        self.etape = "choix" if mode is None else "jeu"
        self.niveau_choisi = int(depart or puzzles.CLASSEMENT_DEPART)
        self.score_classe = puzzles.charger_le_score()

        self.disposition = Disposition(*screen.get_size())
        self.plateau = PlateauProbleme(screen, self.preferences, self.disposition, self)

        self.session = None
        self.puzzle = None
        self.message = ""
        self.couleur_message = None
        self.explication = ""
        self.flash = None                 # (couleur, debut)
        self.fondu_debut = 0
        self.rects_solution = []

        # Boutons de l'ecran de choix
        self.btn_classe = ui.Bouton((0, 0, 10, 10), "Mode classé", "classe", taille=20)
        self.btn_libre = ui.Bouton((0, 0, 10, 10), "Mode libre", "libre", taille=20)
        self.btn_moins = ui.Bouton((0, 0, 10, 10), "-%d" % PAS_DE_NIVEAU, "moins", taille=16)
        self.btn_plus = ui.Bouton((0, 0, 10, 10), "+%d" % PAS_DE_NIVEAU, "plus", taille=16)
        self.btns_niveaux = [ui.Bouton((0, 0, 10, 10), str(n), "niveau_%d" % n,
                                       taille=14, gras=False) for n in NIVEAUX]
        self.btns_themes = [ui.Bouton((0, 0, 10, 10), puzzles.nom_du_theme(th),
                                      "theme_" + th, taille=13, gras=False)
                            for th in puzzles.THEMES_PROPOSES]
        self.btn_retour_choix = ui.Bouton((0, 0, 10, 10), "Retour", "retour", taille=16)
        # 24/10 (travail p37) : les classements Steam (ecran_classements.py).
        self.btn_classements = ui.Bouton((0, 0, 10, 10), "Classements Steam", "classements",
                                         taille=16)
        # 17/10 : les problemes tires de tes propres fautes (mes_erreurs.py).
        self.btn_erreurs = ui.Bouton((0, 0, 10, 10), "Mes erreurs", "erreurs", taille=20)
        self.nombre_erreurs = None
        # 17/10 (travail p07) : les defis.
        self.btns_defis = [ui.Bouton((0, 0, 10, 10), nom, "defi_" + cle, taille=15)
                           for cle, nom in (("chrono", "Contre la montre"),
                                            ("survie", "Survie"),
                                            ("jour", "Problème du jour"))]
        self.boutons_choix = ([self.btn_classe, self.btn_libre, self.btn_moins,
                               self.btn_plus] + self.btns_niveaux + self.btns_themes
                              + self.btns_defis
                              + [self.btn_erreurs, self.btn_classements,
                                 self.btn_retour_choix])

        # Boutons de l'ecran de jeu
        self.btn_suivant = ui.Bouton((0, 0, 10, 10), "Problème suivant", "suivant", taille=17)
        self.btn_indice = ui.Bouton((0, 0, 10, 10), "Indice (H)", "indice", taille=15)
        self.btn_solution = ui.Bouton((0, 0, 10, 10), "Solution", "solution", taille=15)
        self.boutons_nav = [ui.Bouton((0, 0, 10, 10), s, c, taille=17)
                            for s, c in (("|<", "debut"), ("<", "precedent"),
                                         (">", "avant"), (">|", "fin"))]
        self.btn_retourner = ui.Bouton((0, 0, 10, 10), "Retourner (F)", "retourner",
                                       taille=14, gras=False)
        self.btn_retour = ui.Bouton((0, 0, 10, 10), "Retour", "retour", taille=15)
        self.boutons_jeu = ([self.btn_suivant, self.btn_indice, self.btn_solution]
                            + self.boutons_nav + [self.btn_retourner, self.btn_retour])

        self._placer()
        if self.etape == "jeu":
            self.commencer(mode, depart)

    # ================================================================ placement

    def _placer(self, screen=None):
        if screen is not None:
            self.screen = screen
            self.plateau.screen = screen
        largeur, hauteur = self.screen.get_size()
        self.disposition.recalculer(largeur, hauteur)
        p = self.plateau
        if p.SQ_SIZE != self.disposition.taille_case:
            p.SQ_SIZE = self.disposition.taille_case
            p.load_piece_images()
        p.disposition = self.disposition
        ech = ui.echelle(self.screen)
        self.ech = ech

        # --- jeu : panneau a droite
        panneau = pygame.Rect(*self.disposition.rect_panneau())
        self.panneau = panneau
        x = panneau.x + int(14 * ech)
        l = panneau.width - int(28 * ech)
        self.x, self.l = x, l
        espace = int(8 * ech)
        bas = panneau.bottom - int(12 * ech)
        h = int(34 * ech)
        moitie = (l - espace) // 2
        self.btn_retourner.placer((x, bas - h, moitie, h))
        self.btn_retour.placer((x + moitie + espace, bas - h, l - moitie - espace, h))
        bas -= h + espace
        lb = (l - 3 * int(6 * ech)) // 4
        for i, bouton in enumerate(self.boutons_nav):
            bouton.placer((x + i * (lb + int(6 * ech)), bas - h, lb, h))
        bas -= h + espace
        self.btn_indice.placer((x, bas - h, moitie, h))
        self.btn_solution.placer((x + moitie + espace, bas - h, l - moitie - espace, h))
        bas -= h + espace
        h_gros = int(44 * ech)
        self.btn_suivant.placer((x, bas - h_gros, l, h_gros))
        self.bas_texte = bas - h_gros - espace

        # --- choix : une colonne au centre
        lc = min(int(520 * ech), largeur - 60)
        cx = (largeur - lc) // 2
        y = int(hauteur * 0.20)
        h_mode = int(56 * ech)
        self.btn_classe.placer((cx, y, lc, h_mode))
        y += h_mode + int(26 * ech)
        self.btn_libre.placer((cx, y, lc, h_mode))
        y += h_mode + int(10 * ech)
        petit = int(30 * ech)
        ecart = int(5 * ech)
        lp = (lc - 7 * ecart) // 8
        for i, bouton in enumerate(self.btns_niveaux):
            bouton.placer((cx + i * (lp + ecart), y, lp, petit))
        y += petit + ecart
        lm = int(90 * ech)
        self.btn_moins.placer((cx, y, lm, petit))
        self.btn_plus.placer((cx + lc - lm, y, lm, petit))
        self.rect_niveau = pygame.Rect(cx + lm, y, lc - 2 * lm, petit)
        y += petit + int(30 * ech)
        self.y_titre_themes = y - int(22 * ech)
        lt = (lc - 3 * ecart) // 4
        for i, bouton in enumerate(self.btns_themes):
            ligne, col = divmod(i, 4)
            bouton.placer((cx + col * (lt + ecart), y + ligne * (petit + ecart), lt, petit))
        lignes = (len(self.btns_themes) + 3) // 4
        y += lignes * (petit + ecart) + int(16 * ech)
        h_defi = int(46 * ech)
        ld = (lc - 2 * ecart) // 3
        for i, bouton in enumerate(self.btns_defis):
            bouton.placer((cx + i * (ld + ecart), y, ld, h_defi))
        y += h_defi + int(12 * ech)
        self.btn_erreurs.placer((cx, y, lc, h_mode))
        y += h_mode + int(18 * ech)
        y_bas = min(y, hauteur - int(50 * ech))
        moitie = (lc - ecart) // 2
        self.btn_classements.placer((cx, y_bas, moitie, int(38 * ech)))
        self.btn_retour_choix.placer((cx + moitie + ecart, y_bas, lc - moitie - ecart,
                                      int(38 * ech)))
        self.colonne_choix = (cx, lc)

    # ================================================================ choix

    def commencer(self, mode, depart=None):
        if mode in ("chrono", "survie", "jour"):
            import modes_problemes
            self.session = modes_problemes.SessionDefi(mode)
            self.etape = "jeu"
            self.nouveau_puzzle()
            return
        if mode == "erreurs":
            import mes_erreurs
            self.session = mes_erreurs.SessionErreurs()
            self.etape = "jeu"
            self.nouveau_puzzle()
            return
        self.session = puzzles.Session(mode, depart)
        self.etape = "jeu"
        self.nouveau_puzzle()

    def regler_le_niveau(self, valeur):
        self.niveau_choisi = int(max(puzzles.CLASSEMENT_MINIMUM,
                                     min(puzzles.CLASSEMENT_MAXIMUM, int(valeur))))
        return self.niveau_choisi

    def basculer_theme(self, theme):
        if theme in self.themes:
            self.themes.discard(theme)
        else:
            self.themes.add(theme)

    # ================================================================ probleme

    def nouveau_puzzle(self):
        p = self.plateau
        self.puzzle = self.session.tirer_un_puzzle(themes=self.themes)
        self.avance = 0                 # coups trouves
        self.premiere_tentative = True
        self.fini = False
        self.reussi = False
        self.indice_utilise = False
        self.gain = None
        self.explication = ""
        self.flash = None
        self.enchainer_a = 0
        self.chrono_debut = 0
        self.temps_final = None
        self.index_solution = None
        # 24/10 (plantage trouve par Cowork) : sans probleme a tirer (Probleme du
        # jour deja fait), draw() lisait une solution qui n'existait pas.
        self.solution = []
        self.positions = []
        self.coup_en_attente = None
        self.fondu_debut = pygame.time.get_ticks()

        p.annuler_selection()
        p.premove = None
        p.indice = None
        p.game_over = False
        p.animation.clear()
        p.last_move_highlight.clear()
        p.highlights.clear()
        p.move_history = MoveHistory()
        if p.right_click_manager is not None:
            p.right_click_manager.clear()

        if not self.puzzle:
            p.board = chess.Board()
            p.couleur_joueur = None
            p.game_over = True
            self.fini = True
            if hasattr(self.session, "message_si_vide") and self.session.terminee():
                self._dire(self.session.resume(), AMBRE)
            elif hasattr(self.session, "message_si_vide"):
                self._dire(self.session.message_si_vide(), AMBRE)
            elif getattr(self.session, "mode", "") == "erreurs":
                self._dire("Pas encore d'erreur analysée : finis une partie et ouvre "
                           "sa revue.", AMBRE)
            else:
                self._dire("Aucun problème ne correspond (essaie sans filtre de thème).",
                           AMBRE)
            return
        try:
            p.board = chess.Board(self.puzzle["fen"])
        except ValueError:
            p.board = chess.Board()
            self._dire("Problème illisible.", ROUGE)
            return
        self._preparer_la_solution()
        p.couleur_joueur = not p.board.turn      # le 1er coup est celui d'en face
        p.flipped = p.couleur_joueur == chess.BLACK
        self.coup_en_attente = puzzles.coup_d_ouverture(self.puzzle)
        self.attente_jusqu_a = pygame.time.get_ticks() + PAUSE_ADVERSE
        self._dire("L'adversaire joue...")

    def _preparer_la_solution(self):
        """[(san, uci)] et les FEN (une de plus que de coups), pour la navigation."""
        self.solution = []
        self.positions = []
        plateau = chess.Board(self.puzzle["fen"])
        self.positions.append(plateau.fen())
        for uci in self.puzzle.get("coups", []):
            try:
                coup = chess.Move.from_uci(uci)
            except ValueError:
                break
            if coup not in plateau.legal_moves:
                break
            self.solution.append((plateau.san(coup), uci))
            plateau.push(coup)
            self.positions.append(plateau.fen())

    def _dire(self, message, couleur=None):
        self.message = message
        self.couleur_message = couleur

    def _nom_du_camp(self):
        return "Blancs" if self.plateau.couleur_joueur == chess.WHITE else "Noirs"

    def _jouer_le_coup_adverse(self):
        uci, self.coup_en_attente = self.coup_en_attente, None
        try:
            coup = chess.Move.from_uci(uci)
        except (TypeError, ValueError):
            return
        ChessBoard.make_move(self.plateau, coup)
        if not self.chrono_debut:
            # Le chrono part quand c'est a toi, pas pendant le coup adverse.
            self.chrono_debut = pygame.time.get_ticks()
            self._dire("À toi : le meilleur coup pour les %s." % self._nom_du_camp())

    # ---------------------------------------------------------------- arbitre

    def juger(self, coup):
        """Le coup propose est-il le bon ? (appele avant de le jouer)"""
        if self.fini or not self.puzzle or self.coup_en_attente:
            return False
        attendu = puzzles.coup_attendu(self.puzzle, self.avance)
        if attendu is None:
            return False
        if coup.uci() == attendu:
            return True
        # Un mat immediat est toujours accepte, meme s'il n'est pas celui de la base.
        essai = self.plateau.board.copy()
        essai.push(coup)
        if essai.is_checkmate():
            return True
        # Mes erreurs : un autre coup qui ne perd presque rien est accepte aussi
        # (Stockfish verifie). La base lichess, elle, n'a qu'une solution.
        if self.puzzle.get("source"):
            import mes_erreurs
            return mes_erreurs.coup_presque_aussi_bon(
                self.plateau.board.fen(), coup, self.puzzle,
                self.preferences.get("stockfish_path"))
        return False

    def refuser(self, coup):
        p = self.plateau
        p.sounds.play("puzzle_faux")
        p.premove = None
        self.flash = (ROUGE, pygame.time.get_ticks())
        if self.premiere_tentative:
            self.premiere_tentative = False
            self._noter(False)
        attendu = puzzles.coup_attendu(self.puzzle, self.avance)
        try:
            self.explication = explication_puzzle.expliquer(
                p.board, coup, chess.Move.from_uci(attendu) if attendu else None,
                self.puzzle)
        except Exception as souci:
            print("[PROBLEMES] explication impossible : %s" % souci)
            self.explication = ""
        if getattr(self.session, "enchaine_sur_erreur", False) \
                or getattr(self.session, "mode", "") == "jour":
            # Defis : pas de deuxieme essai, on montre la solution et on passe.
            self.explication = ""
            self._arreter_le_chrono()
            self.coup_en_attente = None
            self.fini = True
            p.game_over = True
            # 24/10 (Cowork, t52 : « la solution ne se voit pas ») : on joue
            # sous tes yeux LE coup qu'il fallait jouer (anime, case en
            # couleur), et on le laisse 2 s avant le probleme suivant.
            index_bon = min(len(self.solution), 2 * self.avance + 2)
            self.index_solution = index_bon - 1
            self.aller_au_coup(index_bon, son=True)
            bon = self.solution[index_bon - 1][0] if self.solution else ""
            if self.session.terminee():
                self._dire(self.session.resume(), AMBRE)
            else:
                self._dire("Raté ! Il fallait %s. Problème suivant..." % notation.afficher(bon)
                           if bon else "Raté ! Problème suivant...", ROUGE)
                self.enchainer_a = pygame.time.get_ticks() + PAUSE_FAUTE
            return
        self._dire("Ce n'est pas ça. Réessaie.", ROUGE)

    def apres_bon_coup(self, coup, position_avant):
        self.avance += 1
        self.plateau.indice = None
        reponse = puzzles.reponse_apres(self.puzzle, self.avance - 1)
        if self.plateau.board.is_checkmate() or reponse is None:
            self._terminer()
            return
        self.coup_en_attente = reponse
        self.attente_jusqu_a = pygame.time.get_ticks() + PAUSE_ADVERSE
        self._dire("Bien ! Continue...", VERT)

    def _terminer(self):
        secondes = self._arreter_le_chrono()
        self.fini = True
        self.plateau.game_over = True       # plus de saisie, plus de pre-mouvement
        self.plateau.premove = None
        self.reussi = self.premiere_tentative and not self.indice_utilise
        if self.premiere_tentative:
            self.premiere_tentative = False
            self._noter(True, secondes)
        self.index_solution = min(len(self.solution), 2 * self.avance)
        if self.reussi:
            self.plateau.sounds.play("puzzle_reussi")
            self.flash = (VERT, pygame.time.get_ticks())
            self.enchainer_a = pygame.time.get_ticks() + PAUSE_REUSSITE
            self._dire("Trouvé en %s !" % self.chrono_lisible(), VERT)
            if hasattr(self.session, "resume") and self.session.terminee():
                self.enchainer_a = 0
                self._dire(self.session.resume(), VERT)
        elif self.indice_utilise:
            self._dire("Trouve avec l'indice : aucun gain.", AMBRE)
        else:
            self._dire("C'est ça, mais pas du premier coup.", AMBRE)

    def _noter(self, reussi, secondes=None):
        self.gain = self.session.noter_un_puzzle(self.puzzle, reussi, secondes=secondes,
                                                 indice=self.indice_utilise)

    # ---------------------------------------------------------------- chrono

    def temps_ecoule(self):
        if self.temps_final is not None:
            return self.temps_final
        if not self.chrono_debut:
            return 0.0
        return max(0.0, (pygame.time.get_ticks() - self.chrono_debut) / 1000.0)

    def _arreter_le_chrono(self):
        if self.temps_final is None:
            self.temps_final = self.temps_ecoule()
        return self.temps_final

    def chrono_lisible(self):
        s = self.temps_ecoule()
        return "%d:%04.1f" % (int(s // 60), s % 60)

    # ---------------------------------------------------------------- aides

    def demander_un_indice(self):
        """Montre le coup (fleche verte). 8 points, une seule fois par probleme."""
        if not self.puzzle or self.fini or self.coup_en_attente:
            return False
        if hasattr(self.session, "resume"):
            self._dire("Pas d'indice pendant un défi.", AMBRE)
            return False
        attendu = puzzles.coup_attendu(self.puzzle, self.avance)
        if not attendu:
            return False
        coup = chess.Move.from_uci(attendu)
        self.plateau.indice = (coup.from_square, coup.to_square)
        if not self.indice_utilise:
            self.indice_utilise = True
            perte = self.session.payer_l_indice()
            self.gain = perte
            self._dire("Indice : %d points, et ce problème ne rapportera rien." % perte,
                       AMBRE)
        return True

    def montrer_la_solution(self):
        if not self.puzzle or self.fini:
            return
        self._arreter_le_chrono()
        if self.premiere_tentative:
            self.premiere_tentative = False
            self._noter(False)
        self.coup_en_attente = None
        self.fini = True
        self.plateau.game_over = True
        self.plateau.premove = None
        self.plateau.indice = None
        self.index_solution = 2 * self.avance
        self.aller_au_coup(len(self.solution))
        self._dire("Voici la solution.", AMBRE)

    def solution_lisible(self):
        """'Dxh7+ Rxh7 Th3#' (sans le coup d'ouverture de l'adversaire)."""
        return " ".join(notation.afficher(san) for san, _ in self.solution[1:])

    # ---------------------------------------------------------------- navigation

    def aller_au_coup(self, index, son=True):
        """La position APRES le coup 'index' de la solution (1 = coup adverse)."""
        if not self.fini or not self.positions:
            return
        index = max(1, min(len(self.solution), int(index)))
        p = self.plateau
        avance_d_un = self.index_solution is not None and index == self.index_solution + 1
        avant = chess.Board(self.positions[index - 1])
        coup = chess.Move.from_uci(self.solution[index - 1][1])
        p.board = chess.Board(self.positions[index])
        p.animation.clear()
        p.last_move_highlight.set_last_move(coup.from_square, coup.to_square)
        p.highlights.set_last_move(coup.from_square, coup.to_square)
        if avance_d_un and son:
            prise = avant.piece_at(coup.to_square)
            p.animation.start_animation(coup.from_square, coup.to_square,
                                        p.board.piece_at(coup.to_square), p.SQ_SIZE)
            p._jouer_son_du_coup(coup, avant.piece_at(coup.from_square), prise,
                                 avant.is_castling(coup), avant.is_en_passant(coup))
        self.index_solution = index
        self.enchainer_a = 0

    # ================================================================ evenements

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return "quitter"
        if self.etape == "choix":
            return self._evenement_choix(event)
        return self._evenement_jeu(event)

    def _evenement_choix(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "retour"
        cle = ui.gerer_boutons(self.boutons_choix, event)
        if cle is None:
            return None
        if cle == "retour":
            return "retour"
        if cle == "classements":
            return "classements"            # ouvert par run() (il a l'horloge)
        if cle == "classe":
            self.commencer(puzzles.MODE_CLASSE)
        elif cle == "libre":
            self.commencer(puzzles.MODE_LIBRE, self.niveau_choisi)
        elif cle == "erreurs":
            self.commencer("erreurs")
        elif cle.startswith("defi_"):
            self.commencer(cle[5:])
        elif cle == "moins":
            self.regler_le_niveau(self.niveau_choisi - PAS_DE_NIVEAU)
        elif cle == "plus":
            self.regler_le_niveau(self.niveau_choisi + PAS_DE_NIVEAU)
        elif cle.startswith("niveau_"):
            self.regler_le_niveau(int(cle[7:]))
        elif cle.startswith("theme_"):
            self.basculer_theme(cle[6:])
        return None

    def _evenement_jeu(self, event):
        p = self.plateau
        # Le choix de la piece de promotion capte tout tant qu'il est ouvert.
        if p.promotion.est_actif():
            p.handle_event(event)
            return None
        action = None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if p.selected_square is not None or p.dragging or p.premove:
                    p.handle_event(event)
                    return None
                action = "retour"
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                action = "suivant" if self.fini else None
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_HOME, pygame.K_END):
                action = {pygame.K_LEFT: "precedent", pygame.K_RIGHT: "avant",
                          pygame.K_HOME: "debut", pygame.K_END: "fin"}[event.key]
        elif event.type == pygame.MOUSEWHEEL and self.fini:
            action = "precedent" if getattr(event, "y", 0) > 0 else "avant"
        else:
            action = ui.gerer_boutons([b for b in self.boutons_jeu if b.actif], event)
            if action is None and event.type == pygame.MOUSEBUTTONDOWN \
                    and event.button == 1:
                for rect, index in self.rects_solution:
                    if rect.collidepoint(event.pos):
                        self.aller_au_coup(index, son=False)
                        return None

        if action == "retour":
            return "retour"
        if action == "suivant":
            if hasattr(self.session, "resume") and self.session.terminee():
                if self.session.mode == "jour":
                    return "retour"
                self._defi_clos = False
                self.commencer(self.session.mode)       # rejouer le defi
                return None
            if not self.fini and self.premiere_tentative and self.chrono_debut:
                self._noter(False)        # passer un probleme commence = rate
            self.nouveau_puzzle()
        elif action == "indice":
            self.demander_un_indice()
        elif action == "solution":
            self.montrer_la_solution()
        elif action == "retourner":
            import retournement
            retournement.retourner(p)
        elif action in ("precedent", "avant", "debut", "fin"):
            if self.fini and self.solution:
                courant = self.index_solution or len(self.solution)
                cible = {"precedent": courant - 1, "avant": courant + 1,
                         "debut": 1, "fin": len(self.solution)}[action]
                self.aller_au_coup(cible, son=action == "avant")
        elif action is None:
            if event.type == pygame.MOUSEBUTTONDOWN and self.enchainer_a:
                self.enchainer_a = 0     # on touche au plateau : on reste dessus
            p.handle_event(event)
        return None

    # ================================================================ boucle

    def update(self):
        if self.etape != "jeu":
            return
        maintenant = pygame.time.get_ticks()
        s = self.session
        if hasattr(s, "temps_restant") and s.temps_restant() is not None \
                and s.temps_restant() <= 0 and not getattr(self, "_defi_clos", False):
            self._defi_clos = True
            self.coup_en_attente = None
            self.enchainer_a = 0
            self.fini = True
            self.plateau.game_over = True
            self.plateau.premove = None
            self.plateau.sounds.play("puzzle_reussi")
            self._dire(s.resume(), AMBRE)
        if self.coup_en_attente and maintenant >= self.attente_jusqu_a:
            self._jouer_le_coup_adverse()
        if self.enchainer_a and maintenant >= self.enchainer_a:
            self.nouveau_puzzle()
        self.plateau.update()

    def run(self, clock, evenement_fenetre=None, apres_dessin=None):
        """Renvoie 'retour' ou 'quitter'."""
        cadence = ui.Cadence()       # 23/10 : 30 images/s au repos
        while True:
            evenements = ui.evenements()
            for event in evenements:
                if evenement_fenetre is not None and evenement_fenetre(event):
                    self._placer(pygame.display.get_surface())
                    continue
                reponse = self.handle_event(event)
                if reponse == "classements":
                    from ecran_classements import EcranClassements
                    reponse = EcranClassements(self.screen, self.preferences).run(
                        clock, evenement_fenetre, apres_dessin)
                    self._placer(pygame.display.get_surface())
                    if reponse != "quitter":
                        continue
                if reponse is not None:
                    return reponse
            self.update()
            self.draw()
            if apres_dessin is not None:
                apres_dessin(self.screen)
            ui.afficher()
            clock.tick(cadence.suivante(evenements, bool(getattr(getattr(getattr(self, 'plateau', None), 'animation', None), 'animations', None))))

    # ================================================================ dessin

    def draw(self):
        t = apparence.theme(self.plateau.theme_plateau)
        self.screen.fill(t["fond"])
        if self.etape == "choix":
            self._dessiner_choix(t)
        else:
            self._dessiner_jeu(t)
        import succes
        succes.dessiner_annonce(self.screen)

    # ---------------------------------------------------------------- choix

    def _dessiner_choix(self, t):
        ecran, ech = self.screen, self.ech
        largeur, hauteur = ecran.get_size()
        cx, lc = self.colonne_choix
        ui.texte(ecran, "Problèmes", largeur // 2, int(hauteur * 0.06),
                 ui.t(40, ech), t["texte"], gras=True, ancre="centre")
        nombre = "{:,}".format(puzzles.combien()).replace(",", " ")
        ui.texte(ecran, "%s positions tirées de vraies parties (base lichess)" % nombre,
                 largeur // 2, int(hauteur * 0.06) + ui.t(50, ech), ui.t(15, ech),
                 t["texte_discret"], ancre="centre")

        souris = pygame.mouse.get_pos()
        score = self.score_classe
        joues = int(score.get("reussis", 0)) + int(score.get("rates", 0))
        self.btn_classe.libelle = "Mode classé  -  ton classement : %d" % int(
            score.get("classement", puzzles.CLASSEMENT_DEPART))
        self.btn_libre.libelle = "Mode libre  -  départ à %d" % self.niveau_choisi
        if self.nombre_erreurs is None:
            try:
                import mes_erreurs
                self.nombre_erreurs = len(mes_erreurs.tous_les_problemes())
            except Exception as souci:
                print("[MES ERREURS] %s" % souci)
                self.nombre_erreurs = 0
        self.btn_erreurs.libelle = ("Mes erreurs  -  %d position%s de tes parties"
                                    % (self.nombre_erreurs,
                                       "s" if self.nombre_erreurs > 1 else ""))
        try:
            import modes_problemes as mp
            jour = mp.etat_du_jour()
            self.btns_defis[0].libelle = "Contre la montre · %d" % mp.record("chrono")
            self.btns_defis[1].libelle = "Survie · %d" % mp.record("survie")
            self.btns_defis[2].libelle = ("Problème du jour · fait" if jour["fait"]
                                          else "Problème du jour")
        except Exception as souci:
            print("[DEFIS] %s" % souci)
        for bouton in self.btns_niveaux:
            bouton.selectionne = bouton.cle == "niveau_%d" % self.niveau_choisi
        for bouton in self.btns_themes:
            bouton.selectionne = bouton.cle[6:] in self.themes
        for bouton in self.boutons_choix:
            bouton.maj_survol(souris)
            bouton.dessiner(ecran, t, rayon=10)

        sous = ("%d problèmes joués, %.0f %% réussis, meilleure série %d - enregistré"
                % (joues, puzzles.pourcentage(score), int(score.get("meilleure_serie", 0)))
                if joues else "Ton vrai niveau en tactique. Les résultats sont enregistrés.")
        ui.texte(ecran, sous, largeur // 2, self.btn_classe.rect.bottom + int(5 * ech),
                 ui.t(12, ech), t["texte_discret"], ancre="centre", largeur_max=lc)
        ui.texte_centre_dans(ecran, "Niveau de départ : %d" % self.niveau_choisi,
                             self.rect_niveau, ui.t(15, ech), t["texte"])
        filtre = ("Thèmes : %d choisi(s)" % len(self.themes)) if self.themes \
            else "Thèmes : tous (clique pour filtrer)"
        ui.texte(ecran, filtre, cx, self.y_titre_themes, ui.t(13, ech),
                 t["texte_discret"])

    # ---------------------------------------------------------------- jeu

    def _dessiner_jeu(self, t):
        ecran, p = self.screen, self.plateau
        p.renderer.dessiner_plateau(avec_interaction=True)
        cote = p.SQ_SIZE * 8
        rect_plateau = pygame.Rect(self.disposition.plateau_x, self.disposition.plateau_y,
                                   cote, cote)
        maintenant = pygame.time.get_ticks()
        if self.flash:
            couleur, debut = self.flash
            age = maintenant - debut
            if age < DUREE_FLASH:
                # deux battements
                force = abs(((age / float(DUREE_FLASH)) * 2.0) % 2.0 - 1.0)
                ui.voile(ecran, rect_plateau, int(30 + 70 * (1 - force)), couleur)
            else:
                self.flash = None
        age = maintenant - self.fondu_debut
        if age < DUREE_FONDU:
            ui.voile(ecran, rect_plateau, int(255 * (1 - age / float(DUREE_FONDU))),
                     t["fond"])
        # Le choix de la piece de promotion : dessiner_plateau() ne le fait pas
        # (c'est draw() de la partie qui s'en charge) - sans cette ligne il
        # etait invisible ici et le clic suivant l'annulait.
        p.promotion.draw(ecran)
        self._dessiner_panneau(t)

    def _dessiner_panneau(self, t):
        ecran, ech = self.screen, self.ech
        ui.cadre(ecran, self.panneau, t["panneau"], t["bord"], 1, 14)
        x, l = self.x, self.l
        y = self.panneau.y + int(12 * ech)
        s = self.session

        ui.texte(ecran, "Problèmes  -  mode %s" % s.nom_du_mode().lower(), x, y,
                 ui.t(14, ech), t["texte_discret"], largeur_max=l)
        y += ui.t(22, ech)

        # Classement (gros) et chrono, cote a cote
        ui.texte(ecran, str(s.classement()), x, y, ui.t(34, ech), t["texte"], gras=True)
        restant = s.temps_restant() if hasattr(s, "temps_restant") else None
        if restant is not None:
            couleur_chrono = ROUGE if restant < 20 else t["texte"]
            ui.texte(ecran, "%d:%02d" % (int(restant) // 60, int(restant) % 60), x + l, y,
                     ui.t(28, ech), couleur_chrono, mono=True, ancre="droite")
        else:
            ui.texte(ecran, self.chrono_lisible(), x + l, y, ui.t(28, ech),
                     t["texte"], mono=True, ancre="droite")
        y += ui.t(40, ech)
        if self.puzzle and not self.fini and self.chrono_debut \
                and not self.puzzle.get("source") and s.classe:
            bonus = "gain x%.1f" % puzzles.bonus_de_vitesse(self.temps_ecoule(), self.puzzle)
            ui.texte(ecran, bonus, x + l, y - int(4 * ech), ui.t(12, ech),
                     t["texte_discret"], ancre="droite")
        morceaux = []
        if self.gain:
            morceaux.append(("ce problème %+d" % self.gain, self.gain))
        if s.variation():
            morceaux.append(("séance %+d" % s.variation(), s.variation()))
        cx = x
        for libelle, valeur in morceaux:
            r = ui.texte(ecran, libelle, cx, y - int(4 * ech), ui.t(12, ech),
                         VERT if valeur > 0 else ROUGE)
            cx = r.right + int(12 * ech)
        y += ui.t(16, ech)

        # Compteurs
        if hasattr(s, "compteurs"):
            compteurs = s.compteurs()
        else:
            compteurs = "Série %d  (record %d)    %d/%d réussis  %.0f %%" % (
                s.serie(), s.meilleure_serie(), s.reussis(), s.reussis() + s.rates(),
                s.pourcentage())
        ui.texte(ecran, compteurs, x, y, ui.t(13, ech), t["texte_discret"], largeur_max=l)
        y += ui.t(22, ech)
        ui.separateur(ecran, x, y, l, t["bord"])
        y += int(10 * ech)

        # Le probleme
        if self.puzzle and self.puzzle.get("source"):
            import mes_erreurs
            # 24/10 (Cowork, r01 : « tu as joué… » coupe) : la hauteur fixe ne
            # laissait qu'une ligne ; jusqu'a 3 lignes, toute la phrase.
            y += ui.paragraphe(ecran, mes_erreurs.description(self.puzzle),
                               (x, y, l, 0), ui.t(14, ech), t["texte"],
                               max_lignes=3) + int(4 * ech)
        elif self.puzzle:
            ui.texte(ecran, "Niveau %d  -  %s" % (self.puzzle["classement"],
                                                 puzzles.description(self.puzzle)),
                     x, y, ui.t(14, ech), t["texte"], largeur_max=l)
            y += ui.t(22, ech)
        # 24/10 (Cowork, t52 / r01 : « Rec… », « ne rap… ») : le message passe
        # a la ligne au lieu d'etre rogne.
        hauteur = ui.paragraphe(ecran, self.message, (x, y, l, 0), ui.t(16, ech),
                                self.couleur_message or t["texte"], gras=True,
                                interligne=1.2, max_lignes=3)
        y += max(ui.t(26, ech), hauteur + int(6 * ech))
        if self.explication and not self.fini:
            y += ui.paragraphe(ecran, self.explication,
                               (x, y, l, max(0, self.bas_texte - y)),
                               ui.t(13, ech), t["texte_discret"], max_lignes=4)
            y += int(6 * ech)

        # La solution, une fois fini
        self.rects_solution = []
        if self.fini and self.solution:
            y += int(4 * ech)
            ui.texte(ecran, "Solution", x, y, ui.t(13, ech), t["texte_discret"])
            y += ui.t(20, ech)
            y = self._dessiner_solution(t, x, y, l)

        # Boutons
        en_jeu = bool(self.puzzle) and not self.fini
        defi = hasattr(s, "resume")
        self.btn_indice.actif = en_jeu and not self.coup_en_attente and not defi
        self.btn_solution.actif = en_jeu
        self.btn_suivant.actif = True
        self.btn_suivant.selectionne = self.fini
        self.btn_suivant.libelle = "Problème suivant" if self.fini else "Passer ce problème"
        if defi and s.terminee():
            self.btn_suivant.libelle = "Retour" if s.mode == "jour" else "Rejouer le défi"
        for bouton in self.boutons_nav:
            bouton.actif = self.fini and bool(self.solution)
        souris = pygame.mouse.get_pos()
        for bouton in self.boutons_jeu:
            bouton.maj_survol(souris)
            bouton.dessiner(ecran, t, rayon=10)

    def _dessiner_solution(self, t, x, y, l):
        """Les coups en pastilles cliquables ; celui affiche est surligne."""
        ecran, ech = self.screen, self.ech
        taille = ui.t(14, ech)
        h = ui.t(24, ech)
        cx = x
        depart = chess.Board(self.puzzle["fen"])
        numero = depart.fullmove_number
        trait = depart.turn
        for i, (san, _uci) in enumerate(self.solution):
            san = notation.afficher(san)
            libelle = ("%d. %s" % (numero, san)) if trait == chess.WHITE \
                else ("%d... %s" % (numero, san) if i == 0 else san)
            if trait == chess.BLACK:
                numero += 1
            trait = not trait
            largeur = ui.mesurer(libelle, taille)[0] + int(14 * ech)
            if cx + largeur > x + l:
                cx = x
                y += h + int(4 * ech)
            if y + h > self.bas_texte:
                break
            rect = pygame.Rect(cx, y, largeur, h)
            courant = (i + 1) == self.index_solution
            adverse = (i % 2) == 0
            fond = t["accent"] if courant else t["fond"]
            ui.cadre(ecran, rect, fond, None, 0, 6, plat=True)
            couleur = t["fond"] if courant else (t["texte_discret"] if adverse else t["texte"])
            ui.texte_centre_dans(ecran, libelle, rect, taille, couleur,
                                 gras=not adverse, marge=4, ajuster=False)
            self.rects_solution.append((rect, i + 1))
            cx += largeur + int(5 * ech)
        return y + h + int(6 * ech)
