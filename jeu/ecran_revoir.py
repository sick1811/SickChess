# ecran_revoir.py - SickChess : relire une partie coup par coup.
#
# Version simple de la relecture : l'echiquier a gauche, la feuille de partie a
# droite, et on avance ou recule d'un coup. L'analyse (evaluations, gaffes,
# meilleur coup) arrivera avec la "Revue de partie" (etape 4 du journal) et se
# branchera ici.
#
# Commandes : fleches gauche/droite (ou molette) = coup precedent/suivant,
# Debut/Fin = premier/dernier coup, F = retourner l'echiquier, Echap = retour.
# Un clic sur un coup de la feuille y saute directement.

import chess
import freestyle
import pygame

import apparence
import historique_parties
import retournement
import notation
import ui
from board import ChessBoard


class EcranRevoir:
    def __init__(self, screen, partie, disposition, preferences=None):
        """partie : une entree de historique_parties.lister()."""
        self.screen = screen
        self.partie = partie
        self.disposition = disposition
        self.erreur = ""
        prefs = dict(preferences or {})

        donnees, self.erreur = historique_parties.lire_partie(partie.get("chemin", ""))
        self.fen = (donnees or {}).get("fen", chess.STARTING_FEN)
        self.coups = [chess.Move.from_uci(u) for u in (donnees or {}).get("coups", [])]

        # Notation lisible de chaque coup, calculee une fois.
        self.sans = []
        b = freestyle.plateau(self.fen)
        for coup in self.coups:
            self.sans.append(b.san(coup))
            b.push(coup)
        self.numero_depart = freestyle.plateau(self.fen).fullmove_number
        self.noirs_commencent = freestyle.plateau(self.fen).turn == chess.BLACK

        self.plateau = ChessBoard(screen, {"pendule_active": False,
                                           "son_de_depart": False,
                                           "theme_plateau": prefs.get("theme_plateau"),
                                           "jeu_pieces": prefs.get("jeu_pieces")},
                                  disposition)
        self.plateau.changer_apparence(prefs.get("theme_plateau"),
                                       prefs.get("jeu_pieces"))
        self.plateau.renderer.afficher_coordonnees = bool(
            prefs.get("afficher_coordonnees", True))
        self.plateau.sounds.set_volume(float(prefs.get("volume_sons", 0.6)))
        self.plateau.sounds.actif = bool(prefs.get("sons_actifs", True))
        vitesse = float(prefs.get("vitesse_animation", 0.18))
        self.plateau.animation.duree = max(0.01, vitesse)
        self.plateau.animation.active = vitesse > 0
        # On regarde la partie du cote du joueur.
        self.plateau.flipped = partie.get("camp") == "noir"

        self.index = 0                # nombre de demi-coups joues a l'ecran
        self.premiere_ligne = 0
        self.rects_coups = []
        self.boutons_nav = [ui.Bouton((0, 0, 10, 10), s, c, taille=18)
                            for s, c in (("|<", "debut"), ("<", "precedent"),
                                         (">", "suivant"), (">|", "fin"))]
        self.btn_retourner = ui.Bouton((0, 0, 10, 10), "Retourner (F)", "retourner",
                                       taille=15, gras=False)
        self.btn_retour = ui.Bouton((0, 0, 10, 10), "Retour", "retour")
        self.boutons = self.boutons_nav + [self.btn_retourner, self.btn_retour]
        self._placer()
        self.aller_a(0, son=False)     # SickChess 17/10 : on ouvre sur le depart

    # ------------------------------------------------------------- position

    def aller_a(self, index, son=True):
        index = max(0, min(len(self.coups), int(index)))
        avance_d_un = index == self.index + 1
        p = self.plateau
        p.board = freestyle.plateau(self.fen)
        for coup in self.coups[:index]:
            p.board.push(coup)
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
            # Le dernier coup glisse et sonne, comme pendant la partie.
            dernier = self.coups[index - 1]
            avant = freestyle.plateau(self.fen)
            for coup in self.coups[:index - 1]:
                avant.push(coup)
            piece = avant.piece_at(dernier.from_square)
            prise = avant.piece_at(dernier.to_square)
            if avant.is_en_passant(dernier):
                prise = chess.Piece(chess.PAWN, not avant.turn)
            p.animation.start_animation(dernier.from_square, dernier.to_square,
                                        p.board.piece_at(dernier.to_square),
                                        p.SQ_SIZE)
            p._jouer_son_du_coup(dernier, piece, prise, avant.is_castling(dernier),
                                 avant.is_en_passant(dernier))
        self._suivre_le_coup()

    # ------------------------------------------------------------- placement

    def _placer(self, screen=None):
        if screen is not None:
            self.screen = screen
            self.plateau.screen = screen
            self.disposition.recalculer(*screen.get_size())
            self.plateau.appliquer_disposition(self.disposition)
        ech = ui.echelle(self.screen)
        self.ech = ech
        panneau = pygame.Rect(*self.disposition.rect_panneau())
        self.panneau = panneau
        x = panneau.x + int(14 * ech)
        l = panneau.width - int(28 * ech)
        h_bouton = int(44 * ech)
        bas = panneau.bottom - int(14 * ech)

        self.btn_retour.placer((x, bas - h_bouton, l, h_bouton))
        bas -= h_bouton + int(8 * ech)
        self.btn_retourner.placer((x, bas - int(34 * ech), l, int(34 * ech)))
        bas -= int(34 * ech) + int(8 * ech)
        ecart = int(6 * ech)
        lb = (l - 3 * ecart) // 4
        for i, bouton in enumerate(self.boutons_nav):
            bouton.placer((x + i * (lb + ecart), bas - h_bouton, lb, h_bouton))
        bas -= h_bouton + int(10 * ech) + ui.police(ui.t(12, ech)).get_height() \
            + int(6 * ech)               # place pour "Coup 5 sur 7"

        self.y_entete = panneau.y + int(14 * ech)
        h_entete = int(98 * ech)
        self.zone_coups = pygame.Rect(x, self.y_entete + h_entete, l,
                                      max(int(40 * ech), bas - self.y_entete - h_entete))
        self.taille_coup = ui.t(15, ech)
        self.hauteur_ligne = ui.police(self.taille_coup, mono=True).get_height() \
            + int(5 * ech)
        self.lignes_visibles = max(1, (self.zone_coups.height - int(12 * ech))
                                   // self.hauteur_ligne)
        self._suivre_le_coup()

    def _ligne_du_coup(self, index):
        """Ligne de la feuille ou s'affiche le demi-coup d'indice 'index'."""
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
        if event.type == pygame.KEYDOWN:
            touches = {pygame.K_LEFT: "precedent", pygame.K_RIGHT: "suivant",
                       pygame.K_HOME: "debut", pygame.K_END: "fin",
                       pygame.K_UP: "debut", pygame.K_DOWN: "fin",
                       pygame.K_f: "retourner", pygame.K_ESCAPE: "retour"}
            action = touches.get(event.key)
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
        if action == "retour":
            return "retour"
        if action == "precedent":
            self.aller_a(self.index - 1, son=False)
        elif action == "suivant":
            self.aller_a(self.index + 1)
        elif action == "debut":
            self.aller_a(0)
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
        ecran.fill(t["fond"])
        p.renderer.dessiner_plateau(avec_interaction=True)

        ui.cadre(ecran, self.panneau, t["panneau"], t["bord"], 1, 14)
        x, l = self.zone_coups.x, self.zone_coups.width
        y = self.y_entete
        partie = self.partie
        ui.texte(ecran, "%s  -  %s" % (partie.get("blancs", "?"), partie.get("noirs", "?")),
                 x, y, ui.t(17, ech), t["texte"], gras=True, largeur_max=l,
                 ajuster=True)
        y += ui.police(ui.t(17, ech), True).get_height() + int(4 * ech)
        ligne2 = "%s   %s" % (partie.get("resultat", "*"), partie.get("date", ""))
        ui.texte(ecran, ligne2, x, y, ui.t(13, ech), t["accent"], gras=True,
                 largeur_max=l)
        y += ui.police(ui.t(13, ech), True).get_height() + int(3 * ech)
        for info in (partie.get("raison", ""), historique_parties.ouverture(partie)):
            if info:
                ui.texte(ecran, info, x, y, ui.t(12, ech), t["texte_discret"],
                         largeur_max=l)
                y += ui.police(ui.t(12, ech)).get_height() + int(2 * ech)

        self._dessiner_feuille(ecran, t, ech)

        position = "Position de départ" if self.index == 0 else \
            "Coup %d sur %d" % (self.index, len(self.coups))
        ui.texte(ecran, position, self.panneau.centerx,
                 self.boutons_nav[0].rect.y - ui.police(ui.t(12, ech)).get_height()
                 - int(4 * ech), ui.t(12, ech), t["texte_discret"], ancre="centre")
        souris = pygame.mouse.get_pos()
        self.boutons_nav[0].actif = self.boutons_nav[1].actif = self.index > 0
        self.boutons_nav[2].actif = self.boutons_nav[3].actif = \
            self.index < len(self.coups)
        for bouton in self.boutons:
            bouton.maj_survol(souris)
            bouton.dessiner(ecran, t, rayon=10)

        if self.erreur:
            ui.texte(ecran, self.erreur, p.disposition.plateau_x + 10,
                     p.disposition.plateau_y + 10, ui.t(16, ech), (240, 120, 110),
                     gras=True)

    def _dessiner_feuille(self, ecran, t, ech):
        zone = self.zone_coups
        ui.cadre(ecran, zone, t["fond"], t["bord"], 1, 10)
        self.rects_coups = []
        taille = self.taille_coup
        x0 = zone.x + int(10 * ech)
        larg_num = ui.mesurer("999.", taille, mono=True)[0] + int(6 * ech)
        colonne = max(40, (zone.width - larg_num - int(20 * ech)) // 2)
        y = zone.y + int(6 * ech)
        fin = min(self._total_lignes(), self.premiere_ligne + self.lignes_visibles)
        for ligne in range(self.premiere_ligne, fin):
            ui.texte(ecran, "%d." % (self.numero_depart + ligne), x0, y, taille,
                     t["texte_discret"], mono=True, largeur_max=larg_num)
            for demi in (0, 1):
                index = ligne * 2 + demi - (1 if self.noirs_commencent else 0)
                if index < 0 or index >= len(self.sans):
                    continue
                rect = pygame.Rect(x0 + larg_num + demi * colonne - int(4 * ech),
                                   y - int(2 * ech), colonne - int(4 * ech),
                                   self.hauteur_ligne)
                courant = index == self.index - 1
                if courant:
                    pygame.draw.rect(ecran, t["accent"], rect,
                                     border_radius=int(6 * ech))
                ui.texte(ecran, notation.afficher(self.sans[index]), rect.x + int(4 * ech), y, taille,
                         t["fond"] if courant else t["texte"], gras=courant,
                         largeur_max=rect.width - int(6 * ech))
                self.rects_coups.append((rect, index))
            y += self.hauteur_ligne

    # ------------------------------------------------------------- boucle

    def run(self, clock, evenement_fenetre=None, apres_dessin=None):
        cadence = ui.Cadence()       # 23/10 : 30 images/s au repos
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
            clock.tick(cadence.suivante(evenements, bool(getattr(getattr(getattr(self, 'plateau', None), 'animation', None), 'animations', None))))
