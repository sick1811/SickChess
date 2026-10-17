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
# Debut/Fin = premier/dernier coup, F = retourner l'echiquier, Echap = retour.
# Un clic sur un coup de la feuille ou sur la courbe y saute directement.

import chess
import pygame

import annotations
import apparence
import board_geometry as geo
import retournement
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


class DispositionRevue(Disposition):
    """La disposition de la partie, avec la place pour la barre d'avantage."""

    def recalculer(self, largeur, hauteur):
        Disposition.recalculer(self, largeur, hauteur)
        ech = self.echelle
        self.barre_l = max(12, int(16 * ech))
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
        self.boutons = self.boutons_nav + [self.btn_retourner, self.btn_retour]
        self._placer()
        self.analyseur.demarrer()
        # SickChess 17/10 (remarque de Julien) : la revue s'ouvre sur la
        # position de depart ; la fleche droite montre le coup 1.
        self.aller_a(0, son=False)

    # ------------------------------------------------------------- position

    def aller_a(self, index, son=True):
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

    def _marquer_le_coup(self):
        """Pastille du coup affiche et fleche du coup qu'il fallait jouer.

        Recalcule a chaque image : l'analyse arrive pendant qu'on regarde.
        """
        p = self.plateau
        p.pastille_coup = p.pastille_case = p.indice = None
        if self.index == 0:
            return
        infos = self.analyseur.detail(self.index - 1)
        if not infos["pret"]:
            return
        p.pastille_coup = infos["note"]
        p.pastille_case = self.coups[self.index - 1].to_square
        meilleur = infos.get("meilleur_uci")
        if infos["note"] in NOTES_A_CORRIGER and meilleur:
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
        self.btn_retourner.placer((x, bas - int(36 * ech), moitie, int(36 * ech)))
        self.btn_retour.placer((x + moitie + espace, bas - int(36 * ech),
                                l - moitie - espace, int(36 * ech)))
        bas -= int(36 * ech) + espace
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
        self.zone_detail = pygame.Rect(x, y, l, int(76 * ech))
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
        action = None
        if event.type == pygame.KEYDOWN:
            action = {pygame.K_LEFT: "precedent", pygame.K_RIGHT: "suivant",
                      pygame.K_HOME: "debut", pygame.K_END: "fin",
                      pygame.K_UP: "debut", pygame.K_DOWN: "fin",
                      pygame.K_f: "retourner",
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
        return None

    # ------------------------------------------------------------- dessin

    def draw(self):
        ecran = self.screen
        p = self.plateau
        t = apparence.theme(p.theme_plateau)
        ech = self.ech
        p.animation.update()
        p.retournement.update()
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

    def _dessiner_barre(self, ecran, t, ech):
        """Barre d'avantage : la part blanche = les chances des Blancs."""
        barre = self.disposition.barre
        evaluation = self.analyseur.evaluation_connue(self.index)
        chances = annotations.chances_de_gagner(evaluation) / 100.0
        pygame.draw.rect(ecran, (58, 56, 52), barre, border_radius=4)
        h_blanc = int(barre.height * chances)
        if self.plateau.flipped:
            blanc = pygame.Rect(barre.x, barre.y, barre.width, h_blanc)
        else:
            blanc = pygame.Rect(barre.x, barre.bottom - h_blanc, barre.width, h_blanc)
        pygame.draw.rect(ecran, (232, 229, 220), blanc, border_radius=4)
        pygame.draw.rect(ecran, t["bord"], barre, 1, border_radius=4)
        texte = self.analyseur.texte_evaluation(self.index).replace("+", "")
        if texte in ("", "..."):
            return
        taille = ui.t(10, ech)
        cote_blanc = evaluation >= 0
        en_bas = cote_blanc != self.plateau.flipped
        y = barre.bottom - ui.police(taille, True).get_height() - 3 if en_bas \
            else barre.y + 3
        couleur = (40, 38, 34) if cote_blanc else (232, 229, 220)
        ui.texte(ecran, texte, barre.centerx, y, taille, couleur, gras=True,
                 ancre="centre", largeur_max=barre.width + 4, ajuster=True)

    def _dessiner_titre(self, ecran, t, ech):
        zone = self.zone_titre
        ui.texte(ecran, "%s  -  %s" % self.noms, zone.x, zone.y, ui.t(17, ech),
                 t["texte"], gras=True, largeur_max=zone.width, ajuster=True)
        y = zone.y + ui.police(ui.t(17, ech), True).get_height() + int(4 * ech)
        morceaux = [m for m in (self.resultat, self.analyseur.texte_avancement()) if m]
        ui.texte(ecran, "   ".join(morceaux), zone.x, y, ui.t(12, ech),
                 t["texte_discret"], largeur_max=zone.width)

    def _dessiner_precision(self, ecran, t, ech):
        zone = self.zone_precision
        ui.cadre(ecran, zone, t["fond"], t["bord"], 1, 10)
        rapport = self.analyseur.rapport()
        pret = self.analyseur.survol_fini()
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
        if self.index == 0:
            ui.texte(ecran, "Position de départ", x, y, grande, t["texte"],
                     gras=True, largeur_max=l)
            y += ui.police(grande, True).get_height() + int(4 * ech)
            ui.texte(ecran, "Flèches ou molette pour avancer coup par coup.",
                     x, y, petite, t["texte_discret"], largeur_max=l)
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
        suivant = self.analyseur.san_du_meilleur(self.index)
        if suivant and self.index < len(self.coups) + 1 \
                and not self.plateau.board.is_game_over():
            ui.texte(ecran, "Meilleur coup maintenant : %s" % notation.afficher(suivant), x, y,
                     petite, t["texte_discret"], largeur_max=l)

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
                ui.texte(ecran, notation.afficher(self.sans[index]),
                         centre[0] + rayon + int(5 * ech), y, taille,
                         t["fond"] if courant else t["texte"], gras=courant,
                         largeur_max=rect.right - centre[0] - rayon - int(6 * ech))
                self.rects_coups.append((rect, index))
            y += self.hauteur_ligne

    # ------------------------------------------------------------- boucle

    def run(self, clock, evenement_fenetre=None, apres_dessin=None):
        """Renvoie 'retour' ou 'quitter'."""
        while True:
            for event in pygame.event.get():
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
            clock.tick(60)
