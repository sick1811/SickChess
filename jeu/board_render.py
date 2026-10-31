# board_render.py - V7.1 : dessin de tout l'ecran de jeu
#
# CE QUI CHANGE PAR RAPPORT A LA V7 :
#   1. TOUS LES TEXTES PASSENT PAR ui.py : ils sont mesures et rognes, donc plus
#      aucun chevauchement, quelle que soit la taille de la fenetre ou la
#      longueur du texte (nom d'adversaire, cadence, notation).
#   2. L'HORLOGE DU BAS EST CELLE DU JOUEUR DU BAS. C'etait ton bug : les
#      horloges etaient toujours Noirs en haut / Blancs en bas, meme plateau
#      retourne. Les pieces prises avaient le meme defaut.
#   3. La liste des coups est en vraies colonnes calculees, plus en texte a
#      espacement fixe qui debordait des que la notation etait longue (Cxe4+).
#   4. ONGLETS COUPS / CHAT dans le panneau, pour le mode en ligne.
#   5. dessiner_plateau() est separee : le replay reutilise exactement le meme
#      echiquier sans recopier le panneau de jeu par-dessus le sien.
#   6. Coup "fantome" : un coup peut etre montre en transparence (le meilleur
#      coup de Stockfish dans le replay).
#
# AUCUNE FONCTION SUPPRIMEE : draw() existe toujours et dessine tout.

import math

import chess
import pygame

import annotations
import apparence
import board_geometry as geo
import ui

# Fleches deja dessinees (voir BoardRenderer._fleche).
_FLECHES = {}
_DAMIERS = {}
# Pieces transparentes des coups prepares d'avance : (image, opacite) -> copie.
_TRANSPARENTES = {}
# 31/10 (ta demande) : le coup prepare est presque transparent, la vraie piece
# qui va bouger reste un peu plus visible - on voit ou sont les pieces
# maintenant et ou elles iront.
OPACITE_FANTOME = 80
OPACITE_PIECE_QUI_PART = 165


class BoardRender:
    def __init__(self, chessboard):
        self.chessboard = chessboard
        self.afficher_coordonnees = True
        self.onglet = "coups"          # "coups" ou "chat"
        self.rect_onglets = []         # [(rect, "coups"), (rect, "chat")]
        self._zones_coups = []         # [(rect, index)] - liste cliquable

    # ------------------------------------------------------------------ outils

    def police(self, taille, gras=False, mono=False):
        """Conservee pour compatibilite ; delegue au cache commun de ui.py."""
        return ui.police(taille, gras, mono)

    def theme(self):
        return apparence.theme(getattr(self.chessboard, "theme_plateau", None))

    def echelle(self):
        return getattr(self.chessboard.disposition, "echelle", 1.0)

    def _texte(self, texte, x, y, taille=17, couleur=None, gras=False,
               mono=False, centre=False, droite=False, largeur_max=None):
        """Conservee pour compatibilite avec la V7."""
        ancre = "centre" if centre else ("droite" if droite else "gauche")
        rect = ui.texte(self.chessboard.screen, texte, x, y, taille,
                        couleur or self.theme()["texte"], gras, mono,
                        largeur_max, ancre)
        return rect.width

    # ------------------------------------------------------------------ plateau

    def _dessiner_cases(self):
        plateau = self.chessboard
        t = self.theme()
        sq = plateau.SQ_SIZE
        matiere = apparence.damier_texture(t, 8 * sq)
        if matiere is not None:          # plateau en marbre, en bois...
            plateau.screen.blit(matiere, (geo.ORIGINE_X, geo.ORIGINE_Y))
        else:
            # 23/10 (banc d'essai) : le damier uni est dessine une fois puis garde.
            cle = (sq, tuple(t["clair"]), tuple(t["sombre"]))
            damier = _DAMIERS.get(cle)
            if damier is None:
                if len(_DAMIERS) >= 8:
                    _DAMIERS.clear()
                damier = _DAMIERS[cle] = pygame.Surface((8 * sq, 8 * sq))
                for square in chess.SQUARES:
                    couleur = t["clair"] if geo.case_claire(square) else t["sombre"]
                    colonne, ligne = geo.colonne_ligne_ecran(square, False)
                    pygame.draw.rect(damier, couleur, pygame.Rect(colonne * sq, ligne * sq, sq, sq))
            # retourne ou non, le damier est le meme (a1 reste une case sombre)
            plateau.screen.blit(damier, (geo.ORIGINE_X, geo.ORIGINE_Y))
        pygame.draw.rect(plateau.screen, t["bord"],
                         pygame.Rect(geo.ORIGINE_X - 2, geo.ORIGINE_Y - 2,
                                     8 * sq + 4, 8 * sq + 4), 2)

    def _dessiner_coordonnees(self):
        plateau = self.chessboard
        t = self.theme()
        sq = plateau.SQ_SIZE
        taille = max(ui.TEXTE_MINI, sq // 6)

        rang_bas = 7 if plateau.flipped else 0
        for colonne in range(8):
            case = chess.square(colonne, rang_bas)
            x, y = geo.case_vers_pixel(case, sq, plateau.flipped)
            couleur = t["sombre"] if geo.case_claire(case) else t["clair"]
            rendu = ui.rendu_texte("abcdefgh"[colonne], taille, couleur, gras=True)
            plateau.screen.blit(rendu, (x + sq - rendu.get_width() - 3,
                                        y + sq - rendu.get_height() - 2))

        colonne_gauche = 7 if plateau.flipped else 0
        for rang in range(8):
            case = chess.square(colonne_gauche, rang)
            x, y = geo.case_vers_pixel(case, sq, plateau.flipped)
            couleur = t["sombre"] if geo.case_claire(case) else t["clair"]
            rendu = ui.rendu_texte(str(rang + 1), taille, couleur, gras=True)
            plateau.screen.blit(rendu, (x + 3, y + 2))

    def _dessiner_pieces(self):
        plateau = self.chessboard
        images = plateau.piece_images
        animees = plateau.animation.cases_en_cours() if hasattr(plateau, "animation") else set()
        # V7.2 (03/09) : les pieces qui traversent le plateau pendant un
        # retournement sont dessinees par retournement.py, pas ici - sinon on
        # les verrait DEUX fois, une a l'arrivee et une en vol. Meme contrat
        # que PieceAnimation, et c'est exactement pour ca qu'il a ce nom-la.
        if getattr(plateau, "retournement", None) is not None:
            animees = animees | plateau.retournement.cases_en_cours()
        case_glissee = plateau.selected_square if plateau.dragging else None
        # Coups prepares d'avance : la position telle qu'elle sera ensuite.
        avance = plateau.plateau_premouvements()             if getattr(plateau, "premoves", None) else None

        for square in chess.SQUARES:
            if square in animees:
                continue
            piece = plateau.board.piece_at(square)
            future = avance.piece_at(square) if avance is not None else piece
            if square == case_glissee and piece == future:
                continue                # la piece est dans la main
            if piece:
                bouge = avance is not None and future != piece                     and piece.color == avance.turn
                self._poser_piece(images.get(piece.symbol()), square,
                                  OPACITE_PIECE_QUI_PART if bouge else None)
            if future and future != piece and square != case_glissee:
                self._poser_piece(images.get(future.symbol()), square, OPACITE_FANTOME)

    def _poser_piece(self, image, square, opacite=None):
        """Dessine une piece sur sa case, en transparence si `opacite`."""
        if image is None:
            return
        plateau = self.chessboard
        sq = plateau.SQ_SIZE
        if opacite is not None:
            cle = (id(image), opacite)
            copie = _TRANSPARENTES.get(cle)
            if copie is None:
                if len(_TRANSPARENTES) >= 64:
                    _TRANSPARENTES.clear()
                copie = _TRANSPARENTES[cle] = image.copy()
                copie.set_alpha(opacite)
            image = copie
        x, y = geo.case_vers_pixel(square, sq, plateau.flipped)
        plateau.screen.blit(image, (x + (sq - image.get_width()) // 2,
                                    y + (sq - image.get_height()) // 2))

    def _dessiner_piece_glissee(self):
        plateau = self.chessboard
        if not plateau.dragging or not plateau.drag_piece or not plateau.drag_pos:
            return
        image = plateau.piece_images.get(plateau.drag_piece.symbol())
        if image is None:
            return
        x = plateau.drag_pos[0] - image.get_width() // 2
        y = plateau.drag_pos[1] - image.get_height() // 2
        plateau.screen.blit(image, (x, y))

    def _fleche(self, depart, arrivee, couleur, epaisseur_relative=0.11):
        """Fleche d'une case a une autre (indice Stockfish, coup fantome).

        23/10 (banc d'essai) : la fleche etait refaite a chaque image sur un
        calque transparent grand comme le plateau. Elle est gardee en memoire,
        rognee a sa taille utile."""
        plateau = self.chessboard
        sq = plateau.SQ_SIZE
        cle = (depart, arrivee, tuple(couleur), epaisseur_relative, sq, plateau.flipped)
        deja = _FLECHES.get(cle)
        if deja is None:
            if len(_FLECHES) >= 64:
                _FLECHES.clear()
            calque = self._calque_fleche(depart, arrivee, couleur, epaisseur_relative, sq)
            zone = calque.get_bounding_rect()
            if not zone.width or not zone.height:
                zone = pygame.Rect(0, 0, 1, 1)
            deja = _FLECHES[cle] = (calque.subsurface(zone).copy(), zone.topleft)
        image, (dx, dy) = deja
        plateau.screen.blit(image, (geo.ORIGINE_X + dx, geo.ORIGINE_Y + dy))

    def _calque_fleche(self, depart, arrivee, couleur, epaisseur_relative, sq):
        plateau = self.chessboard
        calque = pygame.Surface((8 * sq, 8 * sq), pygame.SRCALPHA)
        x1, y1 = geo.case_vers_pixel_local(depart, sq, plateau.flipped)
        x2, y2 = geo.case_vers_pixel_local(arrivee, sq, plateau.flipped)
        x1 += sq // 2; y1 += sq // 2
        x2 += sq // 2; y2 += sq // 2
        angle = math.atan2(y2 - y1, x2 - x1)
        pointe = max(10, sq // 4)
        xt = x2 - pointe * 0.8 * math.cos(angle)
        yt = y2 - pointe * 0.8 * math.sin(angle)
        pygame.draw.line(calque, couleur, (x1, y1), (xt, yt),
                         max(4, int(sq * epaisseur_relative)))
        pygame.draw.polygon(calque, couleur, [
            (x2, y2),
            (x2 - pointe * math.cos(angle - 0.5), y2 - pointe * math.sin(angle - 0.5)),
            (x2 - pointe * math.cos(angle + 0.5), y2 - pointe * math.sin(angle + 0.5)),
        ])
        return calque

    def _dessiner_indice(self):
        indice = getattr(self.chessboard, "indice", None)
        if indice:
            self._fleche(indice[0], indice[1], (40, 190, 90, 200))

    def _dessiner_fleches_conseil(self):
        """17/10 : les meilleurs coups de Stockfish dans la revue
        [(depart, arrivee, couleur, epaisseur), ...], le meilleur en dernier
        (dessine par-dessus)."""
        for depart, arrivee, couleur, epaisseur in reversed(
                getattr(self.chessboard, "fleches_conseil", None) or []):
            self._fleche(depart, arrivee, couleur, epaisseur)

    def _dessiner_coup_fantome(self):
        """Le meilleur coup de Stockfish, montre en transparence.

        Utilise par le replay : on voit la piece se poser en fantome sur la case
        que Stockfish aurait choisie, avec une fleche pale.
        """
        coup = getattr(self.chessboard, "coup_fantome", None)
        if coup is None:
            return
        plateau = self.chessboard
        sq = plateau.SQ_SIZE
        self._fleche(coup.from_square, coup.to_square, (129, 182, 76, 110), 0.085)

        piece = plateau.board.piece_at(coup.from_square)
        if piece is None:
            return
        image = plateau.piece_images.get(piece.symbol())
        if image is None:
            return
        fantome = image.copy()
        fantome.set_alpha(105)
        x, y = geo.case_vers_pixel(coup.to_square, sq, plateau.flipped)
        plateau.screen.blit(fantome, (x + (sq - image.get_width()) // 2,
                                      y + (sq - image.get_height()) // 2))

    def _dessiner_pastille_du_coup(self):
        """Pastille ! / ?! / ?? sur la case d'arrivee du coup affiche."""
        cle = getattr(self.chessboard, "pastille_coup", None)
        case = getattr(self.chessboard, "pastille_case", None)
        if not cle or case is None:
            return
        sq = self.chessboard.SQ_SIZE
        x, y = geo.case_vers_pixel(case, sq, self.chessboard.flipped)
        # V7.2 : on donne les limites du plateau pour que la pastille d'une
        # case du bord (colonne h, rangee 8) ne sorte pas de l'echiquier.
        annotations.dessiner_pastille_sur_case(
            self.chessboard.screen, (x, y, sq, sq), cle,
            ui.police(max(10, int(sq * 0.22)), gras=True),
            rect_plateau=(geo.ORIGINE_X, geo.ORIGINE_Y, sq * 8, sq * 8))

    def _dessiner_premouvement(self):
        """Les cases de tous les coups prepares d'avance, en bleu. Avec plusieurs
        coups, un petit numero dans le coin de l'arrivee donne l'ordre."""
        premoves = getattr(self.chessboard, "premoves", None)
        if not premoves:
            return
        plateau = self.chessboard
        sq = plateau.SQ_SIZE
        calque = pygame.Surface((8 * sq, 8 * sq), pygame.SRCALPHA)
        cases = set()
        for coup in premoves:
            cases.update((coup.from_square, coup.to_square))
        for case in cases:
            colonne, ligne = geo.colonne_ligne_ecran(case, plateau.flipped)
            pygame.draw.rect(calque, (110, 160, 230, 120),
                             pygame.Rect(colonne * sq, ligne * sq, sq, sq))
        plateau.screen.blit(calque, (geo.ORIGINE_X, geo.ORIGINE_Y))
        if len(premoves) < 2:
            return
        taille = max(10, int(sq * 0.2))
        for numero, coup in enumerate(premoves, 1):
            x, y = geo.case_vers_pixel(coup.to_square, sq, plateau.flipped)
            ui.texte(plateau.screen, str(numero), x + sq - max(3, sq // 16), y + 1,
                     taille, (235, 240, 255), gras=True, ancre="droite")

    def dessiner_plateau(self, avec_interaction=True):
        """L'echiquier seul : cases, surbrillances, pieces, fleches.

        Le replay appelle cette methode-la : il a son propre panneau, il ne veut
        surtout pas celui de la partie par-dessus.
        """
        plateau = self.chessboard
        # PENDANT LE RETOURNEMENT, AUCUNE SURBRILLANCE. Les cases ne bougent pas
        # (le damier est identique apres une rotation de 180 degres), mais un
        # voile de dernier coup qui sauterait a sa nouvelle case pendant que la
        # piece est encore en vol se lirait comme un bug. Trois dixiemes de
        # seconde sans voile, c'est ce qui se voit le moins.
        rotation = getattr(plateau, "retournement", None) is not None \
            and plateau.retournement.en_cours()

        self._dessiner_cases()
        if not rotation:
            plateau.last_move_highlight.draw(plateau.screen, plateau.SQ_SIZE)
        # V7.2 : meme sans interaction de partie (le replay), on montre la piece
        # choisie et ses cases d'arrivee. Sans ca, cliquer une piece dans le
        # replay ne donnait aucun retour visuel et on jouait a l'aveugle.
        if not rotation and not avec_interaction \
                and getattr(plateau, "selected_square", None) is not None:
            self._dessiner_selection_simple(plateau.selected_square)
        if avec_interaction and not rotation:
            plateau.highlights.draw(plateau.screen, plateau.SQ_SIZE)
            if getattr(plateau, "right_click_manager", None):
                plateau.right_click_manager.draw_cases(plateau.screen)
            self._dessiner_premouvement()
        if self.afficher_coordonnees:
            self._dessiner_coordonnees()
        self._dessiner_coup_fantome()
        self._dessiner_pieces()
        # L'animation de glissement n'a de sens que dans la partie : dans le
        # replay elle dessinait une piece restee en l'air depuis le dernier coup
        # joue, a une position calculee avec l'ancienne taille de cases.
        if avec_interaction and hasattr(plateau, "animation"):
            plateau.animation.draw(plateau.screen)
        # LES PIECES QUI TRAVERSENT LE PLATEAU. Dans les deux cas : le replay se
        # retourne lui aussi (touche F et bouton RETOURNER).
        if getattr(plateau, "retournement", None) is not None:
            plateau.retournement.draw(plateau.screen, plateau.piece_images,
                                      plateau.SQ_SIZE)
        if avec_interaction and not rotation:
            if getattr(plateau, "right_click_manager", None):
                plateau.right_click_manager.draw_fleches(plateau.screen)
        # V7.2 : la fleche d'indice et la piece glissee sont dessinees DANS LES
        # DEUX CAS. Le replay s'en sert maintenant (touche H et glisser-deposer)
        # et il n'y avait aucune raison de les reserver a la partie : ce ne sont
        # que deux dessins de plus, pilotes par les memes attributs du plateau.
        self._dessiner_fleches_conseil()
        self._dessiner_piece_glissee()
        self._dessiner_indice()
        self._dessiner_pastille_du_coup()
        effets = getattr(plateau, "effets", None)
        if effets is not None:
            effets.draw(plateau.screen, plateau.SQ_SIZE, plateau.flipped,
                        plateau.disposition.rect_plateau())

    def _dessiner_selection_simple(self, case):
        """Case choisie + points sur les arrivees possibles, pour le replay."""
        plateau = self.chessboard
        t = self.theme()
        try:
            rect = geo.rectangle_case(case, plateau.SQ_SIZE, plateau.flipped)
        except Exception:
            return
        calque = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        calque.fill(tuple(t.get("selection", (200, 170, 90))[:3]) + (110,))
        plateau.screen.blit(calque, (rect[0], rect[1]))
        rayon = max(3, plateau.SQ_SIZE // 8)
        for coup in plateau.board.legal_moves:
            if coup.from_square != case:
                continue
            centre = geo.centre_case(coup.to_square, plateau.SQ_SIZE,
                                     plateau.flipped)
            prise = plateau.board.piece_at(coup.to_square) is not None \
                or plateau.board.is_en_passant(coup)
            couleur = tuple(t.get("prise", (200, 90, 80))[:3]) if prise \
                else tuple(t.get("coup", (110, 140, 110))[:3])
            if prise:
                pygame.draw.circle(plateau.screen, couleur, centre,
                                   plateau.SQ_SIZE // 2 - 3, 4)
            else:
                pygame.draw.circle(plateau.screen, couleur, centre, rayon)

    # ------------------------------------------------------------------ panneau

    def _dessiner_panneau(self):
        plateau = self.chessboard
        dispo = plateau.disposition
        t = self.theme()
        ui.cadre(plateau.screen, dispo.rect_panneau(), t["panneau"],
                 t.get("bord"), 1, 14)

        # Horloges : elles suivent l'orientation du plateau (correction V7.1).
        plateau.timer.zone_haut = dispo.horloge_haut
        plateau.timer.zone_bas = dispo.horloge_bas
        plateau.timer.theme = t
        plateau.timer.flipped = plateau.flipped
        try:
            plateau.timer.draw(plateau.screen, plateau.board.turn)
        except TypeError:
            plateau.timer.draw(plateau.screen)

        # Pieces prises et avantage materiel, du bon cote eux aussi.
        plateau.captured_pieces.zone_haut = dispo.captures_haut
        plateau.captured_pieces.zone_bas = dispo.captures_bas
        plateau.captured_pieces.theme = t
        plateau.captured_pieces.flipped = plateau.flipped
        plateau.captured_pieces.draw(plateau.screen)

        self._dessiner_infos(dispo.infos, t)
        self._dessiner_zone_centrale(dispo.coups, t)

    def _dessiner_infos(self, zone, t):
        x, y, largeur, hauteur = zone
        plateau = self.chessboard
        ech = self.echelle()
        lignes = []
        reglages = getattr(plateau, "reglages", None) or {}
        if plateau.ai_manager is not None and reglages.get("elo"):
            lignes.append("Ordinateur  %d Elo" % reglages["elo"])
        elif getattr(plateau, "couleur_joueur", None) is not None:
            couleur = "Blancs" if plateau.couleur_joueur == chess.WHITE else "Noirs"
            lignes.append("En ligne - tu joues les %s" % couleur)
        elif getattr(plateau, "hotseat_mode", False):
            lignes.append("Deux joueurs sur ce PC")
        if hasattr(plateau.timer, "description_cadence"):
            lignes.append(plateau.timer.description_cadence())

        taille = ui.t(14, ech)
        hauteur_ligne = ui.police(taille).get_height() + 3
        pile = ui.Pile(x, y, largeur, hauteur, espace=0)
        for ligne in lignes:
            bloc = pile.bloc(hauteur_ligne)
            if bloc is None:
                break
            ui.texte(plateau.screen, ligne, bloc.x, bloc.y, taille,
                     t["texte_discret"], largeur_max=largeur)

    # ------------------------------------------- onglets COUPS / CHAT

    def _dessiner_onglets(self, zone, t, ech):
        """En-tete de la zone centrale. Renvoie la hauteur utilisee."""
        plateau = self.chessboard
        chat = getattr(plateau, "chat", None)
        x, y, largeur, _ = zone
        taille = ui.t(12, ech)
        hauteur = ui.t(22, ech)
        self.rect_onglets = []

        if chat is None:
            ui.texte(plateau.screen, "COUPS JOUÉS", x + ui.t(8, ech), y + 4,
                     taille, t["texte_discret"], gras=True, largeur_max=largeur - 16)
            return hauteur

        moitie = largeur // 2
        for index, (cle, libelle) in enumerate((("coups", "COUPS"),
                                                ("chat", "CHAT"))):
            rect = pygame.Rect(x + index * moitie, y, moitie - 2, hauteur)
            actif = self.onglet == cle
            ui.cadre(plateau.screen, rect,
                     t["panneau"] if actif else t["fond"],
                     t["accent"] if actif else t.get("bord"), 1, 6)
            etiquette = libelle
            if cle == "chat" and chat.non_lus:
                etiquette = "%s (%d)" % (libelle, min(99, chat.non_lus))
            ui.texte_centre_dans(plateau.screen, etiquette, rect, taille,
                                 t["accent"] if actif else t["texte_discret"],
                                 gras=True, marge=4)
            self.rect_onglets.append((rect, cle))
        return hauteur

    def _dessiner_zone_centrale(self, zone, t):
        plateau = self.chessboard
        x, y, largeur, hauteur = zone
        if hauteur < 50:
            return
        ech = self.echelle()
        ui.cadre(plateau.screen, zone, t["fond"], None, 0, 8)

        haut = self._dessiner_onglets((x, y + 3, largeur, hauteur), t, ech)
        # V7.2 : L'AVERTISSEMENT DE NULLE (ta remarque). Les regles marchaient
        # deja - c'est qu'on ne te prevenait pas. Il ne prend de la place QUE
        # quand il y a quelque chose a dire.
        # V7.2 (03/09) : L'OUVERTURE, EN DIRECT PENDANT LA PARTIE.
        # C'est le seul endroit ou elle change quelque chose a la facon de
        # jouer : on voit le moment ou on sort de la theorie.
        haut += self._dessiner_ouverture(
            pygame.Rect(x, y + haut + 4, largeur, hauteur - haut - 8), t, ech)
        haut += self._dessiner_avertissement_nulle(
            pygame.Rect(x, y + haut + 4, largeur, hauteur - haut - 8), t, ech)
        interieur = pygame.Rect(x, y + haut + 4, largeur, hauteur - haut - 8)

        chat = getattr(plateau, "chat", None)
        if chat is not None and self.onglet == "chat":
            chat.dessiner(plateau.screen, interieur, t, ech)
        else:
            self._dessiner_liste_coups(interieur, t, ech)

    def _dessiner_ouverture(self, zone, t, ech):
        """Le nom de l'ouverture en cours. Renvoie la hauteur prise (0 si rien).

        V7.2 (03/09) - TA DEMANDE : "ajoute aussi les ouvertures dans le
        logiciel". C'est ICI que ca sert vraiment : pendant la partie. On voit
        quelle ouverture on joue, et surtout LE MOMENT OU L'ON SORT DU LIVRE -
        a partir de la, on est tout seul, et c'est bon a savoir.
        Comme l'avertissement de nulle, ca ne prend de la place que quand il y
        a quelque chose a dire.
        """
        plateau = self.chessboard
        if zone.height < int(20 * ech):
            return 0
        numero = getattr(plateau, "numero_freestyle", None)
        if numero is not None:
            # Freestyle : pas de theorie d'ouverture, on montre le numero de
            # la position de depart a la place.
            import freestyle
            taille = ui.t(12, ech)
            ui.texte(plateau.screen,
                     freestyle.libelle(numero, getattr(plateau, "tournoi_fide", False)),
                     zone.x + int(8 * ech), zone.y, taille,
                     t.get("accent", (200, 165, 90)),
                     largeur_max=zone.width - int(16 * ech))
            return ui.police(taille).get_height() + int(4 * ech)
        historique = getattr(plateau, "move_history", None)
        sans = list(getattr(historique, "sans", [])) if historique else []
        if not sans:
            return 0
        try:
            import ouvertures
            reconnu = ouvertures.reconnaitre(sans)
        except Exception:
            return 0
        if not reconnu:
            return 0
        _eco, nom, combien = reconnu
        dans_le_livre = combien >= len(sans)
        if dans_le_livre:
            texte = nom
            couleur = t.get("texte_discret", (150, 150, 150))
        else:
            # On est sorti : on dit quand, une bonne fois. C'est l'information
            # qui manque le plus quand on relit ses parties.
            texte = "%s  -  hors théorie depuis le coup %d" % (
                nom, combien // 2 + 1)
            couleur = t.get("texte_discret", (150, 150, 150))
        taille = ui.t(12, ech)
        ui.texte(plateau.screen, texte, zone.x + int(8 * ech), zone.y, taille,
                 couleur, largeur_max=zone.width - int(16 * ech))
        return ui.police(taille).get_height() + int(4 * ech)

    def _dessiner_avertissement_nulle(self, zone, t, ech):
        """Previent avant la nulle. Renvoie la hauteur prise (0 s'il n'y a rien).

        C'est ce qui manquait : la partie s'arretait sur une repetition ou sur
        les 50 coups sans que rien ne t'ait averti que tu approchais.
        """
        plateau = self.chessboard
        if getattr(plateau, "game_over", False) or zone.height < int(24 * ech):
            return 0
        try:
            import regles_nulle
            a_dire = regles_nulle.lignes(plateau.board)
        except Exception:
            return 0
        if not a_dire:
            return 0

        taille = ui.t(12, ech)
        hauteur_ligne = ui.police(taille).get_height() + int(3 * ech)
        place = min(len(a_dire), max(1, (zone.height // 2) // hauteur_ligne))
        y = zone.y
        for texte, niveau in a_dire[:place]:
            ui.texte(plateau.screen, texte, zone.x + int(8 * ech), y, taille,
                     regles_nulle.couleur(niveau, t),
                     largeur_max=zone.width - int(16 * ech))
            y += hauteur_ligne
        return (y - zone.y) + int(2 * ech)

    def _dessiner_liste_coups(self, zone, t, ech):
        """Liste des coups en vraies colonnes, avec pastilles si l'analyse existe."""
        plateau = self.chessboard
        historique = getattr(plateau, "move_history", None)
        sans = list(getattr(historique, "sans", [])) if historique else []
        self._zones_coups = []
        if zone.height < 24:
            return
        if not sans:
            ui.texte(plateau.screen, "Aucun coup joué", zone.x + ui.t(8, ech),
                     zone.y + 2, ui.t(13, ech), t["texte_discret"],
                     largeur_max=zone.width - 16)
            return

        taille = ui.t(14, ech)
        hauteur_ligne = ui.police(taille, mono=True).get_height() + ui.t(4, ech)
        largeur_num = ui.mesurer("99.", taille, gras=False, mono=True)[0] + ui.t(6, ech)
        colonne = max(40, (zone.width - largeur_num - ui.t(14, ech)) // 2)

        total_lignes = (len(sans) + 1) // 2
        visibles = max(1, zone.height // hauteur_ligne)
        debut = max(0, total_lignes - visibles)

        y = zone.y
        for numero in range(debut, total_lignes):
            if y + hauteur_ligne > zone.bottom:
                break
            i = numero * 2
            ui.texte(plateau.screen, "%d." % (numero + 1), zone.x + ui.t(8, ech), y,
                     taille, t["texte_discret"], mono=True, largeur_max=largeur_num)
            for demi in (0, 1):
                index = i + demi
                if index >= len(sans):
                    break
                x = zone.x + ui.t(8, ech) + largeur_num + demi * colonne
                dernier = index == len(sans) - 1
                import notation
                ui.texte(plateau.screen, notation.afficher(sans[index]), x, y, taille,
                         t["accent"] if dernier else t["texte"],
                         gras=dernier, largeur_max=colonne - ui.t(6, ech))
                self._zones_coups.append(
                    (pygame.Rect(x, y, colonne - ui.t(6, ech), hauteur_ligne), index))
            y += hauteur_ligne

    # ------------------------------------------------------------------ tout

    def clic_onglet(self, position):
        """Renvoie l'onglet clique ("coups"/"chat"), ou None."""
        for rect, cle in self.rect_onglets:
            if rect.collidepoint(position):
                return cle
        return None

    def draw(self):
        plateau = self.chessboard
        t = self.theme()

        # 1. TOUTE la fenetre est repeinte : plus rien du menu ne traverse.
        plateau.screen.fill(t["fond"])

        # 2. Panneau de droite.
        self._dessiner_panneau()

        # 3. L'echiquier et tout ce qui se pose dessus.
        self.dessiner_plateau(avec_interaction=True)

        # 4. Bulles des derniers messages du chat, sous le plateau.
        chat = getattr(plateau, "chat", None)
        if chat is not None and self.onglet != "chat":
            import chat as module_chat
            module_chat.dessiner_bulles(plateau.screen, chat,
                                        plateau.disposition.zone_sous_le_plateau(46),
                                        t, self.echelle())

        # 5. Boutons de jeu.
        plateau.game_buttons.zone = plateau.disposition.boutons
        plateau.game_buttons.draw(plateau.screen)

        # 6. Bouton abandonner de l'interface, s'il est active.
        if plateau.ui_manager is not None and hasattr(plateau.ui_manager, "draw"):
            plateau.ui_manager.draw(plateau.screen)

        # 7. Choix de la piece de promotion.
        if getattr(plateau, "promotion", None) is not None:
            plateau.promotion.draw(plateau.screen)

        # 8. Ecran de fin de partie.
        if plateau.game_over and hasattr(plateau, "end_screen"):
            plateau.end_screen.draw(plateau.screen)

        # 9. Fondu d'arrivee (17/10, p13).
        import effets
        effets.fondu(plateau.screen, "partie", t["fond"])
        import succes
        succes.dessiner_annonce(plateau.screen)
