# ecran_revue.py - SickChess : la revue de partie.
#
# Reecrit a partir de replay_screen.py de V8_TURBO_3000 (1269 lignes). Meme
# esprit que ecran_revoir.py (la relecture simple de "Mes parties"), avec
# l'analyse de Stockfish en plus :
#   - a gauche : l'echiquier, et la barre d'avantage le long de son bord ;
#   - sur l'echiquier : la pastille du coup (!!, ?!, ??...) et, quand le coup
#     etait mauvais, une fleche verte vers celui qu'il fallait jouer ;
#   - a droite : la precision de chaque joueur, le detail du coup affiche, la
#     courbe de la partie et la feuille de partie avec une pastille par coup.
# L'analyse tourne en tache de fond (analyse_partie.py) et le coup regarde
# passe toujours en premier : tout se remplit pendant qu'on navigue.
#
# Commandes : fleches gauche/droite (ou molette) = coup precedent/suivant,
# Debut/Fin = premier/dernier coup, F = retourner l'echiquier, Echap = retour,
# A = analyser la position regardee dans l'analyse libre (24/10, p35).
# Un clic sur un coup de la feuille ou sur la courbe y saute directement.
#
# 17/10 (Julien : « Stockfish joue a ma place dans la revue ; il ne doit
# jamais jouer, seulement proposer le meilleur coup ») :
#   - fleches BLEUES : le meilleur coup de la position affichee, et les coups
#     aussi bons quand il y en a (touche B : les cacher) ;
#   - fleche VERTE : apres une faute, le coup qu'il fallait jouer ;
#   - un coup joue sur l'echiquier ouvre une variante : TU joues les deux
#     camps, Stockfish ne repond jamais, il montre ses meilleurs coups ;
#   - la feuille montre l'evaluation apres chaque coup, coloree selon ce que
#     le coup a gagne ou perdu ;
#   - « Exporter » ecrit un PGN annote (export_revue.py).

import chess
import pygame

import annotations
import apparence
import board_geometry as geo
import retournement
import threading

import notation
import ui
from board import ChessBoard
from layout import MARGE, Disposition

# Les pastilles comptees sous la precision de chaque joueur.
PASTILLES_COMPTEES = ["brillant", "tres_bon", "meilleur", "excellent",
                      "imprecision", "erreur", "manque", "gaffe"]
# Pour ces coups-la, on montre le coup qu'il fallait jouer.
NOTES_A_CORRIGER = ("imprecision", "erreur", "manque", "gaffe")
VERT_FLECHE = (40, 190, 90, 200)
BLEU_MEILLEUR = (70, 145, 235, 215)
BLEU_AUSSI_BON = (110, 170, 240, 135)
# Un seul calcul a la fois sur le moteur des variantes.
_VERROU_VARIANTE = threading.Lock()


class DispositionRevue(Disposition):
    """La disposition de la partie, avec la place pour la barre d'avantage."""

    def recalculer(self, largeur, hauteur):
        Disposition.recalculer(self, largeur, hauteur)
        ech = self.echelle
        self.barre_l = max(18, int(22 * ech))   # 17/10 : assez large pour « 0.3 »
        ecart = max(6, int(8 * ech))
        besoin = MARGE + self.barre_l + ecart
        if self.plateau_x < besoin:
            largeur_dispo = self.panneau_x - MARGE - besoin
            cote = max(240, min(self.cote_plateau, largeur_dispo))
            self.taille_case = int(cote // 8)
            self.cote_plateau = self.taille_case * 8
            self.plateau_x = besoin + max(0, (largeur_dispo - self.cote_plateau) // 2)
            self.plateau_y = MARGE + (self.hauteur - 2 * MARGE
                                      - self.cote_plateau) // 2
            geo.configurer(self.plateau_x, self.plateau_y, self.taille_case)
        self.barre = pygame.Rect(self.plateau_x - ecart - self.barre_l,
                                 self.plateau_y, self.barre_l, self.cote_plateau)
        return self


def dessiner_barre_avantage(ecran, barre, evaluation, texte, retourne, t, ech):
    """La barre d'avantage le long de l'echiquier (revue, analyse libre) : la
    part blanche = les chances des Blancs, l'evaluation ecrite du cote du mieux."""
    chances = annotations.chances_de_gagner(evaluation)
    chances = 0.5 if chances is None else chances / 100.0
    pygame.draw.rect(ecran, (58, 56, 52), barre, border_radius=4)
    h_blanc = int(barre.height * chances)
    if retourne:
        blanc = pygame.Rect(barre.x, barre.y, barre.width, h_blanc)
    else:
        blanc = pygame.Rect(barre.x, barre.bottom - h_blanc, barre.width, h_blanc)
    pygame.draw.rect(ecran, (232, 229, 220), blanc, border_radius=4)
    pygame.draw.rect(ecran, t["bord"], barre, 1, border_radius=4)
    texte = (texte or "").replace("+", "")
    if texte in ("", "..."):
        return
    # 17/10 (recette R-130) : « -0.25 » ne tenait pas dans la barre et etait coupe.
    # Le cote de la barre dit deja qui est mieux : on enleve le signe et on
    # garde une decimale (0.3, 2.5, M3).
    texte = texte.lstrip("+-")
    try:
        texte = "%.1f" % float(texte)
    except ValueError:
        pass
    taille = ui.t(10, ech)
    cote_blanc = (evaluation or 0) >= 0
    en_bas = cote_blanc != retourne
    y = barre.bottom - ui.police(taille, True).get_height() - 3 if en_bas \
        else barre.y + 3
    couleur = (40, 38, 34) if cote_blanc else (232, 229, 220)
    ui.texte(ecran, texte, barre.centerx, y, taille, couleur, gras=True,
             ancre="centre", largeur_max=barre.width + 4, ajuster=True)


class EcranRevue:
    def __init__(self, screen, analyseur, preferences=None,
                 noms=("Blancs", "Noirs"), resultat="", raison="",
                 cote_noir=False):
        """analyseur : un AnalyseurPartie (deja lance ou non)."""
        self.screen = screen
        self.analyseur = analyseur
        self.noms = noms
        self.resultat = resultat
        self.raison = raison
        prefs = dict(preferences or {})
        self.preferences = prefs

        self.fen = analyseur.fen_initiale
        self.coups = [chess.Move.from_uci(u) for u in analyseur.coups]
        self.sans = list(analyseur.sans)
        depart = chess.Board(self.fen)
        self.numero_depart = depart.fullmove_number
        self.noirs_commencent = depart.turn == chess.BLACK

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
        p.flipped = bool(cote_noir)       # on regarde du cote du joueur

        self.index = 0
        self.premiere_ligne = 0
        self.rects_coups = []
        self.boutons_nav = [ui.Bouton((0, 0, 10, 10), s, c, taille=18)
                            for s, c in (("|<", "debut"), ("<", "precedent"),
                                         (">", "suivant"), (">|", "fin"))]
        self.btn_retourner = ui.Bouton((0, 0, 10, 10), "Retourner (F)",
                                       "retourner", taille=15, gras=False)
        self.btn_retour = ui.Bouton((0, 0, 10, 10), "Retour", "retour", taille=16)
        self.btn_exporter = ui.Bouton((0, 0, 10, 10), "Exporter", "exporter",
                                      taille=15, gras=False)
        # 24/10 (p35) : la position regardee (variante comprise) dans l'analyse libre.
        self.btn_analyser = ui.Bouton((0, 0, 10, 10), "Analyser (A)", "analyser",
                                      taille=15, gras=False)
        self.boutons = self.boutons_nav + [self.btn_retourner, self.btn_exporter,
                                           self.btn_analyser, self.btn_retour]
        self.message = ""
        self.message_fin = 0
        self.fleches_visibles = bool(prefs.get("revue_fleches", True))
        # VARIANTES : le coup de la partie fait avancer la revue ; un autre coup
        # ouvre une variante ou l'on joue les deux camps. Stockfish ne joue
        # JAMAIS : il calcule les meilleurs coups de chaque position (conseils).
        self.variante = None            # coups (chess.Move) joues depuis self.index
        self.eval_variante = None       # pions, point de vue des Blancs
        self.texte_eval_variante = ""
        self._conseils = {}             # fen -> {"evaluation", "mat", "coups"}
        self._en_calcul = set()         # fens en cours de calcul
        p.hotseat_mode = True           # on deplace les deux camps
        p.premouvement_actif = False
        p.make_move = self._coup_sur_l_echiquier
        self._placer()
        self.analyseur.demarrer()
        # SickChess 17/10 (remarque de Julien) : la revue s'ouvre sur la
        # position de depart ; la fleche droite montre le coup 1.
        self.aller_a(0, son=False)

    # ------------------------------------------------------------- position

    def aller_a(self, index, son=True):
        self._quitter_la_variante()
        index = max(0, min(len(self.coups), int(index)))
        avance_d_un = index == self.index + 1
        p = self.plateau
        avant = chess.Board(self.fen)
        for coup in self.coups[:max(0, index - 1)]:
            avant.push(coup)
        p.board = avant.copy()
        if index:
            p.board.push(self.coups[index - 1])
        self.index = index
        p.animation.clear()
        if index:
            dernier = self.coups[index - 1]
            p.last_move_highlight.set_last_move(dernier.from_square, dernier.to_square)
            p.highlights.set_last_move(dernier.from_square, dernier.to_square)
        else:
            p.last_move_highlight.clear()
            p.highlights.clear()
        p.highlights.set_case_echec(p.board.king(p.board.turn)
                                    if p.board.is_check() else None)
        if avance_d_un and son:
            # Le coup glisse et sonne, comme pendant la partie.
            dernier = self.coups[index - 1]
            prise = avant.piece_at(dernier.to_square)
            if avant.is_en_passant(dernier):
                prise = chess.Piece(chess.PAWN, not avant.turn)
            p.animation.start_animation(dernier.from_square, dernier.to_square,
                                        p.board.piece_at(dernier.to_square),
                                        p.SQ_SIZE)
            p._jouer_son_du_coup(dernier, avant.piece_at(dernier.from_square), prise,
                                 avant.is_castling(dernier),
                                 avant.is_en_passant(dernier))
        self.analyseur.prioriser(index - 1)
        self._suivre_le_coup()

    # ------------------------------------------------------------- variantes

    def _coup_sur_l_echiquier(self, move, engine=None):
        """Un coup joue a la souris sur l'echiquier de la revue."""
        p = self.plateau
        if move not in p.board.legal_moves:
            return False
        if self.variante is None and self.index < len(self.coups) \
                and move == self.coups[self.index]:
            self.aller_a(self.index + 1)          # le coup de la partie : on avance
            return True
        if self.variante is None:
            self.variante = []
        if not ChessBoard.make_move(p, move, engine):
            return False
        self.variante.append(move)
        self._maj_eval_variante()
        return True

    def _annuler_un_coup_de_variante(self):
        """Fleche gauche dans une variante : on reprend le dernier coup."""
        if not self.variante:
            self.aller_a(self.index, son=False)
            return
        reste = self.variante[:-1]
        self.aller_a(self.index, son=False)
        if reste:
            self.variante = []
            for coup in reste:
                ChessBoard.make_move(self.plateau, coup)
                self.variante.append(coup)
            self._maj_eval_variante()

    def _jeton_en_attente(self):
        return self.variante is not None \
            and self.plateau.board.fen() in self._en_calcul

    def _quitter_la_variante(self):
        self.variante = None
        self.eval_variante = None
        self.texte_eval_variante = ""

    def _maj_eval_variante(self):
        """L'evaluation de la variante = celle des conseils de sa position."""
        p = self.plateau
        if p.board.is_game_over():
            self.texte_eval_variante = "Mat" if p.board.is_checkmate() else "Nulle"
            self.eval_variante = (-20.0 if p.board.turn == chess.WHITE else 20.0) \
                if p.board.is_checkmate() else 0.0
            return
        conseil = self.conseil(p.board.fen())
        if conseil is None:
            self.texte_eval_variante = ""
            return
        self.eval_variante = conseil["evaluation"]
        self.texte_eval_variante = self.analyseur.texte_d_une_evaluation(
            conseil["evaluation"], conseil["mat"])

    def conseil(self, fen):
        """Les meilleurs coups d'une position HORS de la partie (variante).
        Calcules en tache de fond, une seule fois par position."""
        if fen in self._conseils:
            return self._conseils[fen]
        if fen not in self._en_calcul and not chess.Board(fen).is_game_over():
            self._en_calcul.add(fen)
            chemin = getattr(self.analyseur, "chemin", None)
            moteur_fourni = getattr(self.analyseur, "_moteur_fourni", None)
            profondeur, noeuds, temps = self.analyseur.limites_variante()
            # 18/10 (tableur de Julien : « 1 x 12 pour la variante ») : une
            # fois l'analyse de la partie finie, la variante prend tous les
            # processeurs sauf un ; pendant l'analyse, 1 seul (23/10,
            # surveillance : les 12 processeurs sont deja pris par l'analyse).
            threads = 1
            if not getattr(self.analyseur, "en_cours", False):
                import os
                threads = max(1, (os.cpu_count() or 2) - 1)

            def travail():
                details = None
                try:
                    with _VERROU_VARIANTE:
                        moteur = moteur_fourni
                        if moteur is None:
                            import moteurs
                            moteur = moteurs.moteur_d_analyse_n(5, chemin, threads=threads,
                                                                hash_mb=256)
                        if moteur is not None:
                            import analyse_partie
                            if noeuds:
                                try:
                                    details = moteur.analyser_position(
                                        fen, profondeur, temps,
                                        lignes=analyse_partie.LIGNES_FINES,
                                        noeuds=noeuds)
                                except TypeError:   # moteur de test
                                    details = moteur.analyser_position(
                                        fen, profondeur or 22, temps,
                                        lignes=analyse_partie.LIGNES_FINES)
                            else:
                                details = moteur.analyser_position(
                                    fen, profondeur, temps,
                                    lignes=analyse_partie.LIGNES_FINES)
                except Exception as souci:
                    print("[REVUE] Stockfish indisponible : %s" % souci)
                self._ranger_conseil(fen, details)

            threading.Thread(target=travail, daemon=True).start()
        return None

    def _ranger_conseil(self, fen, details):
        import analyse_partie
        lignes = analyse_partie.lignes_du_moteur(fen, details)
        if lignes:
            self._conseils[fen] = {
                "evaluation": lignes[0][1], "mat": lignes[0][2],
                "coups": analyse_partie.meilleurs_depuis_lignes(fen, lignes)}
        self._en_calcul.discard(fen)

    def _suivre_la_variante(self):
        """Appele a chaque image : l'evaluation de la variante arrive."""
        if self.variante is not None and not self.texte_eval_variante:
            self._maj_eval_variante()

    def coups_conseilles(self):
        """Les meilleurs coups de la position AFFICHEE (partie ou variante)."""
        p = self.plateau
        if p.board.is_game_over():
            return []
        if self.variante is not None:
            c = self.conseil(p.board.fen())
            return c["coups"] if c else []
        return self.analyseur.meilleurs_coups(self.index)

    def texte_de_la_variante(self):
        """'12... Cf6 13. Dxf7#' : la variante, en notation choisie."""
        if not self.variante:
            return ""
        plateau = chess.Board(self.fen)
        for coup in self.coups[:self.index]:
            plateau.push(coup)
        morceaux = []
        for i, coup in enumerate(self.variante):
            numero = plateau.fullmove_number
            san = notation.afficher(plateau.san(coup))
            if plateau.turn == chess.WHITE:
                morceaux.append("%d. %s" % (numero, san))
            elif i == 0:
                morceaux.append("%d... %s" % (numero, san))
            else:
                morceaux.append(san)
            plateau.push(coup)
        return " ".join(morceaux)

    def _marquer_le_coup(self):
        """Pastille du coup affiche et fleche du coup qu'il fallait jouer.

        Recalcule a chaque image : l'analyse arrive pendant qu'on regarde.
        """
        p = self.plateau
        p.pastille_coup = p.pastille_case = p.indice = None
        p.fleches_conseil = []
        if self.fleches_visibles:
            for n, c in enumerate(self.coups_conseilles()):
                try:
                    coup = chess.Move.from_uci(c["uci"])
                except ValueError:
                    continue
                p.fleches_conseil.append(
                    (coup.from_square, coup.to_square,
                     BLEU_MEILLEUR if n == 0 else BLEU_AUSSI_BON,
                     0.12 if n == 0 else 0.08))
        if self.index == 0 or self.variante is not None:
            return
        infos = self.analyseur.detail(self.index - 1)
        if not infos["pret"]:
            return
        p.pastille_coup = infos["note"]
        p.pastille_case = self.coups[self.index - 1].to_square
        meilleur = infos.get("meilleur_uci")
        if infos["note"] in NOTES_A_CORRIGER and meilleur and self.fleches_visibles:
            coup = chess.Move.from_uci(meilleur)
            p.indice = (coup.from_square, coup.to_square)

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
        h_bouton = int(42 * ech)
        bas = panneau.bottom - int(12 * ech)

        moitie = (l - espace) // 2
        h36 = int(36 * ech)
        # 24/10 (p35) : deux rangees de deux, pour faire de la place a « Analyser ».
        self.btn_analyser.placer((x, bas - h36, moitie, h36))
        self.btn_retour.placer((x + moitie + espace, bas - h36, l - moitie - espace, h36))
        bas -= h36 + espace
        self.btn_retourner.placer((x, bas - h36, moitie, h36))
        self.btn_exporter.placer((x + moitie + espace, bas - h36, l - moitie - espace, h36))
        bas -= h36 + espace
        lb = (l - 3 * int(6 * ech)) // 4
        for i, bouton in enumerate(self.boutons_nav):
            bouton.placer((x + i * (lb + int(6 * ech)), bas - h_bouton, lb, h_bouton))
        bas -= h_bouton + espace

        y = panneau.y + int(12 * ech)
        h_titre = ui.police(ui.t(17, ech), True).get_height() \
            + ui.police(ui.t(12, ech)).get_height() + int(6 * ech)
        self.zone_titre = pygame.Rect(x, y, l, h_titre)
        y += h_titre + espace
        self.zone_precision = pygame.Rect(x, y, l, int(104 * ech))
        y += self.zone_precision.height + espace
        # 24/10 (Cowork, t51 : explication d'une gaffe coupee) : le cadre du coup
        # grandit (jusqu'a 2 lignes de plus) tant que la feuille garde 6 lignes.
        h_detail = int(118 * ech)  # 17/10 : + meilleurs coups
        ligne_coup = ui.police(ui.t(14, ech), mono=True).get_height() + int(5 * ech)
        reste = bas - (y + h_detail + espace + int(58 * ech) + espace) - int(10 * ech)
        h_detail += max(0, min(int(46 * ech), reste - 5 * ligne_coup))
        self.zone_detail = pygame.Rect(x, y, l, h_detail)
        y += self.zone_detail.height + espace
        self.zone_courbe = pygame.Rect(x, y, l, int(58 * ech))
        y += self.zone_courbe.height + espace
        self.zone_coups = pygame.Rect(x, y, l, max(int(40 * ech), bas - y))

        self.taille_coup = ui.t(14, ech)
        self.hauteur_ligne = ui.police(self.taille_coup, mono=True).get_height() \
            + int(5 * ech)
        self.lignes_visibles = max(1, (self.zone_coups.height - int(10 * ech))
                                   // self.hauteur_ligne)
        self._suivre_le_coup()

    def _ligne_du_coup(self, index):
        return (index + (1 if self.noirs_commencent else 0)) // 2

    def _total_lignes(self):
        return self._ligne_du_coup(len(self.sans) - 1) + 1 if self.sans else 0

    def _suivre_le_coup(self):
        """Fait defiler la feuille pour que le coup courant reste visible."""
        if not hasattr(self, "lignes_visibles"):
            return
        if self.index == 0:
            self.premiere_ligne = 0
            return
        ligne = self._ligne_du_coup(self.index - 1)
        if ligne < self.premiere_ligne:
            self.premiere_ligne = ligne
        elif ligne >= self.premiere_ligne + self.lignes_visibles:
            self.premiere_ligne = ligne - self.lignes_visibles + 1
        self.premiere_ligne = max(0, min(self.premiere_ligne,
                                         self._total_lignes() - self.lignes_visibles))

    # ------------------------------------------------------------- evenements

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return "quitter"
        p = self.plateau
        # La souris sur l'echiquier : on joue (variantes), comme en partie.
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                          pygame.MOUSEMOTION):
            d = self.disposition
            sur_le_plateau = pygame.Rect(d.plateau_x, d.plateau_y, d.cote_plateau,
                                         d.cote_plateau).collidepoint(event.pos)
            if sur_le_plateau or p.dragging or p.promotion.est_actif():
                p.handle_event(event)
                if event.type != pygame.MOUSEMOTION:
                    return None
            elif p.selected_square is not None and event.type == pygame.MOUSEBUTTONDOWN:
                # 24/10 (Cowork, t65) : une piece selectionnee « mangeait » le
                # clic sur la feuille des coups (rien ne se passait). On la
                # deselectionne ET le clic fait son travail.
                p.annuler_selection()
        if self.variante is not None and event.type == pygame.KEYDOWN \
                and event.key in (pygame.K_ESCAPE, pygame.K_LEFT, pygame.K_BACKSPACE):
            if p.selected_square is not None or p.dragging:
                p.handle_event(event)
                return None
            if event.key == pygame.K_ESCAPE:
                self.aller_a(self.index, son=False)   # retour a la partie
            else:
                self._annuler_un_coup_de_variante()
            return None
        action = None
        if event.type == pygame.KEYDOWN:
            action = {pygame.K_LEFT: "precedent", pygame.K_RIGHT: "suivant",
                      pygame.K_HOME: "debut", pygame.K_END: "fin",
                      pygame.K_UP: "debut", pygame.K_DOWN: "fin",
                      pygame.K_f: "retourner", pygame.K_b: "fleches",
                      pygame.K_e: "exporter", pygame.K_a: "analyser",
                      pygame.K_ESCAPE: "retour"}.get(event.key)
        elif event.type == pygame.MOUSEWHEEL:
            action = "precedent" if getattr(event, "y", 0) > 0 else "suivant"
        else:
            action = ui.gerer_boutons(self.boutons, event)
            if action is None and event.type == pygame.MOUSEBUTTONDOWN \
                    and event.button == 1:
                for rect, index in self.rects_coups:
                    if rect.collidepoint(event.pos):
                        self.aller_a(index + 1, son=False)
                        return None
                position = self._position_sous_la_courbe(event.pos)
                if position is not None:
                    self.aller_a(position, son=False)
                    return None
        if action == "retour":
            self.analyseur.prioriser(-1)
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
            retournement.retourner(self.plateau, self.plateau.board,
                                   self.plateau.SQ_SIZE)
        elif action == "fleches":
            self.fleches_visibles = not self.fleches_visibles
            self._afficher_message("Flèches de Stockfish : %s"
                                   % ("affichées" if self.fleches_visibles else "cachées"))
        elif action == "exporter":
            self.exporter()
        elif action == "analyser":
            return self.ouvrir_l_analyse_libre()
        return None

    def ouvrir_l_analyse_libre(self, clock=None, evenement_fenetre=None):
        """La position regardee (et sa variante) dans l'analyse libre (p35) ;
        on revient ensuite a la revue la ou on l'avait laissee."""
        from ecran_analyse_libre import EcranAnalyseLibre, threads_conseilles
        if self.variante is not None:
            coups, index = self.coups[:self.index] + list(self.variante), None
        else:
            coups, index = self.coups, self.index
        libre = EcranAnalyseLibre(
            self.screen, self.preferences, self.fen, coups, index,
            stockfish_path=getattr(self.analyseur, "chemin", None),
            threads=threads_conseilles(getattr(self.analyseur, "en_cours", False)),
            retourne=self.plateau.flipped)
        self.analyse_libre = libre
        clock = clock or getattr(self, "_horloge", None)
        if clock is None:                 # tests : l'ecran est cree, pas lance
            return None
        reponse = libre.run(clock, evenement_fenetre or getattr(self, "_evenement_fenetre", None),
                            getattr(self, "_apres_dessin", None))
        self.analyse_libre = None
        self._placer(pygame.display.get_surface())
        return "quitter" if reponse == "quitter" else None

    def _afficher_message(self, texte, secondes=5):
        self.message = texte
        self.message_fin = pygame.time.get_ticks() + int(secondes * 1000)

    def exporter(self, dossier=None):
        """Ecrit le PGN annote (exports/) et le copie. Renvoie le chemin."""
        if not self.analyseur.terminee():
            self._afficher_message("Attends la fin de l'analyse pour exporter.")
            return None
        import os
        import export_revue
        resultat = (self.resultat or "").split(" ")[0]
        try:
            chemin, copie = export_revue.exporter(self.analyseur, self.noms[0],
                                                  self.noms[1], resultat, dossier)
        except Exception as souci:
            self._afficher_message("Export impossible : %s" % souci)
            return None
        self._afficher_message("PGN %sdans exports/%s" % (
            "copié et enregistré " if copie else "enregistré ",
            os.path.basename(chemin)), 7)
        return chemin

    # ------------------------------------------------------------- dessin

    def draw(self):
        ecran = self.screen
        p = self.plateau
        t = apparence.theme(p.theme_plateau)
        ech = self.ech
        p.animation.update()
        p.retournement.update()
        self._suivre_la_variante()
        self._marquer_le_coup()

        ecran.fill(t["fond"])
        p.renderer.dessiner_plateau(avec_interaction=True)
        self._dessiner_barre(ecran, t, ech)

        ui.cadre(ecran, self.panneau, t["panneau"], t["bord"], 1, 14)
        self._dessiner_titre(ecran, t, ech)
        self._dessiner_precision(ecran, t, ech)
        self._dessiner_detail(ecran, t, ech)
        self._dessiner_courbe(ecran, t, ech)
        self._dessiner_feuille(ecran, t, ech)

        souris = pygame.mouse.get_pos()
        self.boutons_nav[0].actif = self.boutons_nav[1].actif = self.index > 0
        self.boutons_nav[2].actif = self.boutons_nav[3].actif = \
            self.index < len(self.coups)
        for bouton in self.boutons:
            bouton.maj_survol(souris)
            bouton.dessiner(ecran, t, rayon=10)
        import effets
        effets.fondu(ecran, "revue", t["fond"])

    def _dessiner_barre(self, ecran, t, ech):
        """Barre d'avantage : la part blanche = les chances des Blancs."""
        evaluation = self.analyseur.evaluation_connue(self.index)
        texte = self.analyseur.texte_evaluation(self.index)
        if self.variante is not None:
            if self.eval_variante is not None:
                evaluation = self.eval_variante       # la barre suit la variante
            texte = self.texte_eval_variante or "..."
        dessiner_barre_avantage(ecran, self.disposition.barre, evaluation, texte,
                                self.plateau.flipped, t, ech)

    def _dessiner_titre(self, ecran, t, ech):
        zone = self.zone_titre
        ui.texte(ecran, "%s  -  %s" % self.noms, zone.x, zone.y, ui.t(17, ech),
                 t["texte"], gras=True, largeur_max=zone.width, ajuster=True)
        y = zone.y + ui.police(ui.t(17, ech), True).get_height() + int(4 * ech)
        morceaux = [m for m in (self.resultat, self.analyseur.texte_avancement()) if m]
        couleur = t["texte_discret"]
        if self.message and pygame.time.get_ticks() < self.message_fin:
            morceaux, couleur = [self.message], t["accent"]
        ui.texte(ecran, "   ".join(morceaux), zone.x, y, ui.t(12, ech),
                 couleur, largeur_max=zone.width)

    def _dessiner_precision(self, ecran, t, ech):
        zone = self.zone_precision
        ui.cadre(ecran, zone, t["fond"], t["bord"], 1, 10)
        rapport = self.analyseur.rapport()
        # 17/10 : la precision n'apparait qu'une fois TOUTE l'analyse fine
        # finie : un chiffre affiche ne change plus.
        pret = self.analyseur.terminee()
        colonne = zone.width // 2
        for n, camp in enumerate(("blancs", "noirs")):
            x = zone.x + n * colonne + int(10 * ech)
            l = colonne - int(16 * ech)
            y = zone.y + int(6 * ech)
            ui.texte(ecran, self.noms[n], x, y, ui.t(12, ech), t["texte_discret"],
                     largeur_max=l)
            y += ui.police(ui.t(12, ech)).get_height()
            precision = rapport[camp]["precision"]
            texte = ("%.1f %%" % precision) if (pret and precision is not None) \
                else "..."
            ui.texte(ecran, texte, x, y, ui.t(24, ech), t["texte"], gras=True,
                     largeur_max=l, ajuster=True)
            y += ui.police(ui.t(24, ech), True).get_height() + int(4 * ech)
            # Deux rangees de quatre pastilles, avec leur nombre.
            cellule = max(1, l // 4)
            rayon = max(6, int(7 * ech))
            for i, cle in enumerate(PASTILLES_COMPTEES):
                cx = x + (i % 4) * cellule + rayon
                cy = y + (i // 4) * (2 * rayon + int(5 * ech)) + rayon
                nombre = rapport[camp]["pastilles"].get(cle, 0)
                if nombre:
                    annotations.dessiner_pastille(ecran, (cx, cy), rayon, cle,
                                                  ui.police(max(9, rayon), True))
                else:
                    pygame.draw.circle(ecran, t["bord"], (cx, cy), rayon, 1)
                ui.texte(ecran, str(nombre), cx + rayon + int(3 * ech),
                         cy - ui.police(ui.t(11, ech)).get_height() // 2,
                         ui.t(11, ech), t["texte"] if nombre else t["texte_discret"],
                         largeur_max=cellule - 2 * rayon - int(3 * ech))
        pygame.draw.line(ecran, t["bord"], (zone.x + colonne, zone.y + int(8 * ech)),
                         (zone.x + colonne, zone.bottom - int(8 * ech)), 1)

    def _explication(self, i):
        """La faute du coup i en mots (explication_revue.py), calculee une fois."""
        cache = self.__dict__.setdefault("_explications", {})
        cle = (i, self.analyseur.meilleurs[i])
        if cle not in cache:
            try:
                import explication_revue
                cache[cle] = explication_revue.expliquer(
                    self.analyseur.fens[i], self.analyseur.coups[i],
                    self.analyseur.meilleurs[i])
            except Exception as e:
                print("[REVUE] explication impossible : %s" % e)
                cache[cle] = ""
        return cache[cle]

    def _phrase_du_coup(self, infos):
        cle = infos["note"]
        nom = annotations.libelle(cle)
        if cle == "theorique":
            return "Coup de théorie (ouverture connue)"
        if cle in NOTES_A_CORRIGER:
            meilleur = infos.get("meilleur_san")
            return ("%s. Il fallait jouer %s" % (nom, notation.afficher(meilleur))) if meilleur else nom
        if infos.get("est_le_meilleur"):
            return "%s : le coup de Stockfish" % nom
        return nom

    def _dessiner_detail(self, ecran, t, ech):
        zone = self.zone_detail
        ui.cadre(ecran, zone, t["fond"], t["bord"], 1, 10)
        x = zone.x + int(10 * ech)
        l = zone.width - int(20 * ech)
        y = zone.y + int(8 * ech)
        grande = ui.t(16, ech)
        petite = ui.t(12, ech)
        if self.variante is not None:
            r = ui.texte(ecran, "Variante (tu joues les deux camps)", x, y, grande,
                         t["accent"], gras=True, largeur_max=l, ajuster=True)
            texte_eval = self.texte_eval_variante or ("..." if self._jeton_en_attente() else "")
            ui.texte(ecran, texte_eval, zone.right - int(10 * ech), y, grande,
                     t["accent"], gras=True, ancre="droite",
                     largeur_max=max(10, zone.right - r.right - int(16 * ech)))
            y += ui.police(grande, True).get_height() + int(6 * ech)
            ui.texte(ecran, self.texte_de_la_variante(), x, y, ui.t(13, ech),
                     t["texte"], gras=True, largeur_max=l, ajuster=True)
            y += ui.police(ui.t(13, ech), True).get_height() + int(3 * ech)
            y = self._ligne_meilleurs(ecran, t, ech, x, y, l)
            aide = ("Stockfish calcule..." if self._jeton_en_attente()
                    else "Flèche gauche : annuler un coup  -  Échap : revenir à la partie")
            ui.texte(ecran, aide, x, max(y, zone.bottom - ui.police(petite).get_height()
                                         - int(6 * ech)),
                     petite, t["texte_discret"], largeur_max=l)
            return
        if self.index == 0:
            ui.texte(ecran, "Position de départ", x, y, grande, t["texte"],
                     gras=True, largeur_max=l)
            y += ui.police(grande, True).get_height() + int(4 * ech)
            ui.texte(ecran, "Flèches pour avancer, ou joue un coup sur l'échiquier.",
                     x, y, petite, t["texte_discret"], largeur_max=l)
            y += ui.police(petite).get_height() + int(4 * ech)
            self._ligne_meilleurs(ecran, t, ech, x, y, l)
            return
        infos = self.analyseur.detail(self.index - 1)
        rayon = max(9, int(11 * ech))
        decalage = 0
        if infos["pret"] and infos["note"]:
            annotations.dessiner_pastille(
                ecran, (x + rayon, y + ui.police(grande, True).get_height() // 2),
                rayon, infos["note"], ui.police(max(10, rayon), True))
            decalage = 2 * rayon + int(8 * ech)
        trait = "." if infos["par_les_blancs"] else "..."
        titre = "%d%s %s" % (infos["numero"] + self.numero_depart - 1, trait,
                             notation.afficher(infos["san"]))
        r = ui.texte(ecran, titre, x + decalage, y, grande, t["texte"], gras=True,
                     largeur_max=l - decalage)
        ui.texte(ecran, infos["texte_evaluation"], zone.right - int(10 * ech), y,
                 grande, t["accent"], gras=True, ancre="droite",
                 largeur_max=max(10, zone.right - r.right - int(16 * ech)))
        y += ui.police(grande, True).get_height() + int(6 * ech)
        if not infos["pret"]:
            phrase, couleur = "Analyse de ce coup...", t["texte_discret"]
        else:
            phrase = self._phrase_du_coup(infos)
            couleur = annotations.couleur(infos["note"])
        ui.texte(ecran, phrase, x, y, ui.t(13, ech), couleur, gras=True,
                 largeur_max=l, ajuster=True)
        y += ui.police(ui.t(13, ech), True).get_height() + int(3 * ech)
        # 17/10 (travail p03) : la faute expliquee avec des mots.
        explication = None
        if infos["pret"] and infos["note"] in NOTES_A_CORRIGER:
            explication = self._explication(self.index - 1)
        # La ligne des meilleurs coups reste toujours en bas du cadre. 24/10
        # (Cowork, t51) : avec une explication, on enleve la « Suite prevue »
        # pour lui laisser une ligne de plus (elle etait coupee).
        lignes_meilleurs = 1 if explication else 2
        h_meilleurs = lignes_meilleurs * ui.police(petite).get_height() + int(4 * ech)
        bas_meilleurs = zone.bottom - h_meilleurs - int(6 * ech)
        if explication and bas_meilleurs - y > ui.police(ui.t(12, ech)).get_height():
            ui.paragraphe(ecran, explication,
                          pygame.Rect(x, y, l, bas_meilleurs - y),
                          ui.t(12, ech), t["texte"], interligne=1.15)
        self._ligne_meilleurs(ecran, t, ech, x, max(y, bas_meilleurs), l,
                              avec_suite=not explication)

    def _ligne_meilleurs(self, ecran, t, ech, x, y, l, avec_suite=True):
        """« Meilleur ici : Nf3 (+0.35)  ·  aussi bon : d4 (+0.30) » et la suite
        prevue par Stockfish. Renvoie le y suivant."""
        petite = ui.t(12, ech)
        h = ui.police(petite).get_height()
        if self.plateau.board.is_game_over():
            return y
        coups = self.coups_conseilles()
        if not coups:
            ui.texte(ecran, "Stockfish cherche le meilleur coup...", x, y, petite,
                     t["texte_discret"], largeur_max=l)
            return y + h + int(2 * ech)
        premier = coups[0]
        texte = "Meilleur ici : %s (%s)" % (notation.afficher(premier["san"]),
                                            premier["texte"])
        if len(coups) > 1:
            texte += "   aussi bon : " + ", ".join(
                "%s (%s)" % (notation.afficher(c["san"]), c["texte"]) for c in coups[1:])
        ui.texte(ecran, texte, x, y, petite, BLEU_MEILLEUR[:3], gras=True,
                 largeur_max=l, ajuster=True)
        y += h + int(2 * ech)
        if premier["suite_san"] and avec_suite:
            suite = " ".join(notation.afficher(c) for c in premier["suite_san"])
            ui.texte(ecran, "Suite prévue : " + suite, x, y, petite,
                     t["texte_discret"], largeur_max=l)
            y += h + int(2 * ech)
        return y

    # --- la courbe : position 0 a gauche, derniere position a droite.

    def _x_courbe(self, k, n):
        zone = self.zone_courbe
        return zone.x + (zone.width * k / float(n - 1) if n > 1 else zone.width / 2)

    def _position_sous_la_courbe(self, pos):
        n = len(self.coups) + 1
        if n < 2 or not self.zone_courbe.collidepoint(pos):
            return None
        part = (pos[0] - self.zone_courbe.x) / float(max(1, self.zone_courbe.width))
        return max(0, min(n - 1, int(round(part * (n - 1)))))

    def _dessiner_courbe(self, ecran, t, ech):
        zone = self.zone_courbe
        pygame.draw.rect(ecran, (58, 56, 52), zone, border_radius=int(6 * ech))
        n = len(self.coups) + 1
        milieu = zone.y + zone.height / 2.0

        def y_de(chances):
            return zone.bottom - max(0.0, min(100.0, chances)) / 100.0 * zone.height

        if n >= 2:
            chances, derniere = [], 50.0
            for k in range(n):
                c = annotations.chances_de_gagner(self.analyseur.evaluation(k))
                derniere = derniere if c is None else c
                chances.append(derniere)
            points = [(self._x_courbe(k, n), y_de(c)) for k, c in enumerate(chances)]
            pygame.draw.polygon(ecran, (232, 229, 220),
                                [(zone.x, zone.bottom)] + points
                                + [(zone.right, zone.bottom)])
            pygame.draw.line(ecran, t["bord"], (zone.x, milieu), (zone.right, milieu), 1)
            # Les fautes : un point de la couleur de leur pastille.
            for i, note in enumerate(self.analyseur.notes()):
                if note in ("erreur", "manque", "gaffe"):
                    pygame.draw.circle(ecran, annotations.couleur(note),
                                       (int(points[i + 1][0]), int(points[i + 1][1])),
                                       max(3, int(3.5 * ech)))
            cx = self._x_courbe(self.index, n)
            pygame.draw.line(ecran, t["accent"], (cx, zone.y), (cx, zone.bottom),
                             max(1, int(2 * ech)))
        pygame.draw.rect(ecran, t["bord"], zone, 1, border_radius=int(6 * ech))

    def _dessiner_feuille(self, ecran, t, ech):
        zone = self.zone_coups
        ui.cadre(ecran, zone, t["fond"], t["bord"], 1, 10)
        self.rects_coups = []
        taille = self.taille_coup
        x0 = zone.x + int(8 * ech)
        larg_num = ui.mesurer("999.", taille, mono=True)[0] + int(4 * ech)
        colonne = max(40, (zone.width - larg_num - int(16 * ech)) // 2)
        rayon = max(5, int(self.hauteur_ligne * 0.28))
        y = zone.y + int(5 * ech)
        fin = min(self._total_lignes(), self.premiere_ligne + self.lignes_visibles)
        for ligne in range(self.premiere_ligne, fin):
            ui.texte(ecran, "%d." % (self.numero_depart + ligne), x0, y, taille,
                     t["texte_discret"], mono=True, largeur_max=larg_num)
            for demi in (0, 1):
                index = ligne * 2 + demi - (1 if self.noirs_commencent else 0)
                if index < 0 or index >= len(self.sans):
                    continue
                rect = pygame.Rect(x0 + larg_num + demi * colonne - int(3 * ech),
                                   y - int(2 * ech), colonne - int(4 * ech),
                                   self.hauteur_ligne)
                courant = index == self.index - 1
                if courant:
                    pygame.draw.rect(ecran, t["accent"], rect,
                                     border_radius=int(6 * ech))
                centre = (rect.x + int(4 * ech) + rayon,
                          rect.y + self.hauteur_ligne // 2)
                infos = self.analyseur.detail(index)
                if infos["pret"] and infos["note"]:
                    annotations.dessiner_pastille(ecran, centre, rayon, infos["note"],
                                                  ui.police(max(9, rayon + 2), True))
                else:
                    annotations.dessiner_pastille_en_attente(ecran, centre, rayon - 1)
                # 17/10 : l'evaluation apres le coup, a droite de la case,
                # de la couleur de la pastille quand le coup a coute cher.
                texte_ev = self.analyseur.texte_evaluation(index + 1)
                larg_ev = 0
                if texte_ev and texte_ev != "...":
                    petite = max(9, taille - 3)
                    if infos["pret"] and infos["note"] in NOTES_A_CORRIGER:
                        couleur_ev = annotations.couleur(infos["note"])
                    else:
                        couleur_ev = t["texte_discret"]
                    if courant:
                        couleur_ev = t["fond"]
                    larg_ev = ui.mesurer(texte_ev, petite, mono=True)[0] + int(6 * ech)
                    ui.texte(ecran, texte_ev, rect.right - int(5 * ech),
                             y + (ui.police(taille, mono=True).get_height()
                                  - ui.police(petite, mono=True).get_height()) // 2,
                             petite, couleur_ev, mono=True, ancre="droite")
                ui.texte(ecran, notation.afficher(self.sans[index]),
                         centre[0] + rayon + int(5 * ech), y, taille,
                         t["fond"] if courant else t["texte"], gras=courant,
                         largeur_max=rect.right - larg_ev - centre[0] - rayon - int(6 * ech))
                self.rects_coups.append((rect, index))
            y += self.hauteur_ligne

    # ------------------------------------------------------------- boucle

    def run(self, clock, evenement_fenetre=None, apres_dessin=None):
        """Renvoie 'retour' ou 'quitter'."""
        try:
            return self._boucle(clock, evenement_fenetre, apres_dessin)
        finally:
            self._liberer_la_variante()

    def _boucle(self, clock, evenement_fenetre, apres_dessin):
        self._horloge, self._evenement_fenetre = clock, evenement_fenetre
        self._apres_dessin = apres_dessin
        cadence = ui.Cadence()
        while True:
            evenements = ui.evenements()
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
            ui.afficher()
            animation = getattr(self.plateau, "animation", None)
            clock.tick(cadence.suivante(evenements, bool(getattr(animation, "animations", None))))

    def _liberer_la_variante(self):
        """23/10 (surveillance) : le moteur des variantes restait ouvert jusqu'a
        la fermeture du jeu. On le ferme en quittant la revue, apres la
        recherche en cours (en tache de fond : on n'attend pas)."""
        if getattr(self.analyseur, "_moteur_fourni", None) is not None:
            return

        def fermer():
            with _VERROU_VARIANTE:
                try:
                    import moteurs
                    moteurs.liberer_la_variante()
                except Exception as e:
                    print("[REVUE] moteur des variantes non ferme : %s" % e)
        threading.Thread(target=fermer, daemon=True).start()
