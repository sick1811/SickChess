# ecran_entrainement.py - SickChess 17/10 (travail p06) : l'ecran de
# l'entraineur d'ouvertures. La logique est dans entrainement.py ; le plateau
# est celui des problemes (PlateauProbleme : le vrai plateau de la partie, dont
# seul le coup du joueur est arbitre).
#   1. l'ARBRE des ouvertures, coup par coup (25/10, arbre_ouvertures.py) :
#      a gauche l'arbre qui se deplie, en haut le fil d'Ariane, a droite la
#      position du noeud choisi, son nom, son code ECO et la progression ;
#   2. « S'entrainer ici » : les lignes sous ce noeud, la plus jouee d'abord,
#      puis les ratees repassent (au hasard dans le groupe : en option) ;
#   3. le jeu joue les coups adverses de la theorie, tu trouves les tiens ;
#      faux : rouge, on reessaie ; « Montrer le coup » (H) dessine la fleche ;
#   4. fin de ligne : ton score, le nom exact de la variante, et la suivante.

import random

import chess
import pygame

import apparence
import arbre_ouvertures as arbre
import entrainement
import notation
import ouvertures
import ui
from ecran_problemes import PlateauProbleme, VERT, ROUGE, AMBRE
from layout import Disposition

PAUSE_ADVERSE = 500
DUREE_FLASH = 500
DOUBLE_CLIC = 400          # ms
NIVEAUX_EN_RETRAIT = 14    # au-dela, les coups ne se decalent plus (lignes de 36 demi-coups)


class EcranEntrainement:
    def __init__(self, screen, preferences=None):
        self.screen = screen
        self.preferences = dict(preferences or {})
        self.etape = "arbre"
        self.couleur = chess.WHITE
        self.racine = arbre.racine()
        self.choisi = self.racine.enfants[0] if self.racine.enfants else self.racine
        self.deplies = set()            # les noeuds dont on voit les suivants
        self.defilement = 0             # premiere rangee visible
        self.au_hasard = False
        self.seance = None
        self.entr = None
        self.message, self.couleur_message = "", None
        self.flash = None
        self.adverse_a = 0
        self._rangees = None            # [(chaine de noeuds, niveau)], refaite au besoin
        self._image_arbre = None        # (cle, surface) : l'arbre dessine une fois
        self._image_position = None     # (cle, surface) : l'echiquier du noeud choisi
        self._pieces = {}               # taille de case -> images (mini echiquier)
        self._ariane = []               # [(rect, noeud)] du fil d'Ariane
        self._dernier_clic = (None, 0)
        self.survol = None
        self.disposition = Disposition(*screen.get_size())
        self.plateau = PlateauProbleme(screen, self.preferences, self.disposition, self)

        self.btn_blancs = ui.Bouton((0, 0, 10, 10), "Je joue les Blancs", "blancs", taille=15)
        self.btn_noirs = ui.Bouton((0, 0, 10, 10), "Je joue les Noirs", "noirs", taille=15)
        self.btn_ici = ui.Bouton((0, 0, 10, 10), "S'entraîner ici", "ici", taille=18)
        self.btn_retour_choix = ui.Bouton((0, 0, 10, 10), "Retour", "retour", taille=15)
        self.zone_hasard = pygame.Rect(0, 0, 0, 0)

        self.btn_montrer = ui.Bouton((0, 0, 10, 10), "Montrer le coup (H)", "montrer", taille=15)
        self.btn_suivante = ui.Bouton((0, 0, 10, 10), "Ligne suivante", "suivante", taille=17)
        self.btn_changer = ui.Bouton((0, 0, 10, 10), "Changer de groupe", "changer", taille=14)
        self.btn_retour = ui.Bouton((0, 0, 10, 10), "Retour", "retour", taille=14)
        self.boutons_jeu = [self.btn_montrer, self.btn_suivante, self.btn_changer, self.btn_retour]
        self._placer()

    # ------------------------------------------------------------ placement
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
        # jeu : panneau a droite
        self.panneau = pygame.Rect(*self.disposition.rect_panneau())
        x = self.panneau.x + int(14 * ech)
        l = self.panneau.width - int(28 * ech)
        self.x, self.l = x, l
        bas = self.panneau.bottom - int(12 * ech)
        h = int(36 * ech)
        moitie = (l - int(8 * ech)) // 2
        self.btn_changer.placer((x, bas - h, moitie, h))
        self.btn_retour.placer((x + l - moitie, bas - h, moitie, h))
        bas -= h + int(8 * ech)
        self.btn_montrer.placer((x, bas - h, l, h))
        bas -= h + int(8 * ech)
        self.btn_suivante.placer((x, bas - int(46 * ech), l, int(46 * ech)))
        self.bas_texte = bas - int(54 * ech)
        self._placer_arbre(largeur, hauteur, ech)

    def _placer_arbre(self, largeur, hauteur, ech):
        """L'ecran de l'arbre : titre et fil d'Ariane en haut, l'arbre a
        gauche, l'echiquier et ses boutons a droite."""
        marge = int(16 * ech)
        self.marge = marge
        self.y_titre = marge
        self.y_ariane = marge + ui.t(36, ech)
        self.h_ariane = ui.t(26, ech)
        haut = self.y_ariane + self.h_ariane + int(10 * ech)
        h_infos = int(214 * ech)
        cote = min(hauteur - haut - marge - h_infos, int(largeur * 0.40))
        cote = max(8 * 16, cote - cote % 8)
        self.rect_echiquier = pygame.Rect(largeur - marge - cote, haut, cote, cote)
        self.rect_arbre = pygame.Rect(marge, haut, self.rect_echiquier.x - 2 * marge,
                                      hauteur - haut - marge)
        self.h_rangee = max(18, int(30 * ech))
        self.rangees_visibles = max(1, (self.rect_arbre.height - int(12 * ech)) // self.h_rangee)
        # sous l'echiquier : nom, ECO, progression, puis les boutons
        x, l = self.rect_echiquier.x, cote
        y = self.rect_echiquier.bottom + int(10 * ech)
        self.y_infos = y
        hb = int(34 * ech)
        bas = hauteur - marge
        self.btn_retour_choix.placer((x + l - int(120 * ech), bas - hb, int(120 * ech), hb))
        self.zone_hasard = pygame.Rect(x, bas - hb, l - int(130 * ech), hb)
        bas -= hb + int(8 * ech)
        self.btn_ici.placer((x, bas - int(40 * ech), l, int(40 * ech)))
        bas -= int(40 * ech) + int(8 * ech)
        demi = (l - int(8 * ech)) // 2
        self.btn_blancs.placer((x, bas - hb, demi, hb))
        self.btn_noirs.placer((x + l - demi, bas - hb, demi, hb))
        self.bas_infos = bas - hb - int(6 * ech)
        self._image_arbre = None
        self._image_position = None
        self._voir_le_choisi()

    # ------------------------------------------------------------ l'arbre
    def rangees(self):
        """Ce que montre l'arbre : [(chaine de noeuds, niveau)]. Une chaine =
        un noeud et ses coups de passage replies avec lui."""
        if self._rangees is None:
            sortie = []
            pile = [(e, 0) for e in reversed(self.racine.enfants)]
            while pile:
                n, niveau = pile.pop()
                chaine = arbre.chaine_depuis(n)
                sortie.append((chaine, niveau))
                fin = chaine[-1]
                if fin in self.deplies:
                    pile.extend((e, niveau + 1) for e in reversed(fin.enfants))
            self._rangees = sortie
        return self._rangees

    def _rang_du_choisi(self):
        for i, (chaine, _niveau) in enumerate(self.rangees()):
            if self.choisi in chaine:
                return i
        return None

    def _changer_l_arbre(self):
        self._rangees = None
        self._image_arbre = None

    def deplier(self, noeud, ouvrir=True):
        fin = arbre.chaine_depuis(noeud)[-1] if noeud.parent is not None else noeud
        if ouvrir and fin.enfants:
            self.deplies.add(fin)
        else:
            self.deplies.discard(fin)
        self._changer_l_arbre()

    def choisir(self, noeud):
        """Choisit un noeud : ses parents sont deplies pour qu'on le voie."""
        if noeud is None:
            return
        self.choisi = noeud
        # chaque rangee au-dessus de lui se deplie (dans une chaine repliee,
        # c'est le bout de la chaine qui se deplie)
        for ancetre in noeud.chemin()[:-1]:
            fin = arbre.chaine_depuis(ancetre)[-1]
            if fin is not noeud and fin.contient(noeud) and fin not in self.deplies:
                self.deplies.add(fin)
                self._rangees = None
        self._image_arbre = None
        self._image_position = None
        self._voir_le_choisi()

    def _voir_le_choisi(self):
        rang = self._rang_du_choisi()
        if rang is None:
            return
        if rang < self.defilement:
            self.defilement = rang
        elif rang >= self.defilement + self.rangees_visibles:
            self.defilement = rang - self.rangees_visibles + 1
        self._borner_defilement()

    def _borner_defilement(self):
        maxi = max(0, len(self.rangees()) - self.rangees_visibles)
        self.defilement = max(0, min(maxi, self.defilement))

    def _deplacer(self, pas):
        rangees = self.rangees()
        rang = self._rang_du_choisi()
        rang = (-1 if pas > 0 else len(rangees)) if rang is None else rang
        rang = max(0, min(len(rangees) - 1, rang + pas))
        if rangees:
            self.choisir(rangees[rang][0][-1])

    def _droite(self):
        fin = arbre.chaine_depuis(self.choisi)[-1] if self.choisi is not self.racine else self.racine
        if not fin.enfants:
            return
        if fin is self.racine or fin in self.deplies:
            self.choisir(fin.enfants[0] if fin is self.racine else arbre.chaine_depuis(
                fin.enfants[0])[-1])
        else:
            self.choisi = fin
            self.deplier(fin, True)
            self._image_position = None

    def _gauche(self):
        rangees = self.rangees()
        rang = self._rang_du_choisi()
        if rang is None:
            return
        chaine = rangees[rang][0]
        fin = chaine[-1]
        if fin in self.deplies:
            self.deplier(fin, False)
            self.choisi = fin
            self._image_position = None
            return
        parent = chaine[0].parent
        if parent is not None and parent is not self.racine:
            self.choisir(parent)

    # ------------------------------------------------------------ deroulement
    def commencer(self, noeud=None, couleur=None):
        """S'entraine sous ce noeud (par defaut : celui qui est choisi). Un nom
        de famille (« Partie italienne ») marche aussi."""
        if isinstance(noeud, str):
            noeud = self._noeud_de_famille(noeud)
        noeud = noeud or self.choisi
        if couleur is not None:
            self.couleur = couleur
        self.choisi = noeud
        hasard = random.Random() if self.au_hasard else None
        self.seance = entrainement.Seance(noeud, self.couleur, hasard)
        self.entr = None
        self.etape = "jeu"
        self.nouvelle_ligne()

    def _noeud_de_famille(self, famille):
        """Le premier noeud (le moins profond) qui porte ce nom exact."""
        pile = list(self.racine.enfants)
        while pile:
            n = pile.pop(0)
            if n.nom_lichess == famille:
                return n
            pile.extend(n.enfants)
        return None

    def nouvelle_ligne(self):
        if self.seance is None:
            return
        if self.entr is not None and not self.entr.termine():
            self.seance.resultat(0.0)            # passee sans la finir : elle repasse
        if self.seance.suivante() is None:
            self._dire("Aucune ligne pour cette ouverture.", AMBRE)
            return
        self.entr = self.seance.entrainement()
        p = self.plateau
        p.board = chess.Board()
        p.game_over = False
        p.premove = None
        p.indice = None
        p.annuler_selection()
        p.animation.clear()
        p.last_move_highlight.clear()
        p.highlights.clear()
        p.couleur_joueur = self.couleur
        p.flipped = self.couleur == chess.BLACK
        self.ligne_notee = False
        if self.entr.a_moi_de_jouer():
            self._dire("À toi : le premier coup de la théorie.")
        else:
            self._programmer_l_adversaire()

    def _programmer_l_adversaire(self):
        self.adverse_a = pygame.time.get_ticks() + PAUSE_ADVERSE
        self._dire("L'adversaire joue...")

    def _jouer_l_adversaire(self):
        self.adverse_a = 0
        coup = self.entr.jouer_le_coup_de_theorie()
        if coup is not None:
            from board import ChessBoard
            ChessBoard.make_move(self.plateau, coup)
        self._apres_un_coup()

    def _apres_un_coup(self):
        self.plateau.indice = None
        if self.entr.termine():
            self._fin_de_ligne()
        elif self.entr.a_moi_de_jouer():
            self._dire("À toi.")
        else:
            self._programmer_l_adversaire()

    def _fin_de_ligne(self):
        note = self.entr.note()
        if not self.ligne_notee:
            self.ligne_notee = True
            ligne = self.seance.courante if self.seance else None
            entrainement.noter_une_ligne(ligne.famille() if ligne else self.entr.nom,
                                         self.couleur, note,
                                         ligne.cle() if ligne else None)
            if self.seance:
                self.seance.resultat(note)
            self._image_arbre = None             # la progression a change
        self.plateau.game_over = True
        if note >= 99.9:
            self.plateau.sounds.play("puzzle_reussi")
            self.flash = (VERT, pygame.time.get_ticks())
            self._dire("Parfait ! Toute la ligne du premier coup.", VERT)
        else:
            self._dire("Ligne terminée : %d coup%s trouvé%s du premier coup sur %d." % (
                self.entr.trouves, "s" if self.entr.trouves > 1 else "",
                "s" if self.entr.trouves > 1 else "", self.entr.trouves + self.entr.fautes),
                AMBRE)

    def _dire(self, message, couleur=None):
        self.message, self.couleur_message = message, couleur

    # --- appele par PlateauProbleme
    def juger(self, coup):
        if self.entr is None or self.adverse_a:
            return False
        return self.entr.proposer(coup)

    def refuser(self, coup):
        self.plateau.sounds.play("puzzle_faux")
        self.plateau.premove = None
        self.flash = (ROUGE, pygame.time.get_ticks())
        self._dire("Ce n'est pas le coup de la théorie. Réessaie, ou « Montrer le coup ».",
                   ROUGE)

    def apres_bon_coup(self, coup, position_avant):
        self._dire("Oui !", VERT)
        self._apres_un_coup()

    def demander_un_indice(self):
        """Touche H / bouton : la fleche du coup de theorie (compte comme rate)."""
        if self.entr is None or not self.entr.a_moi_de_jouer():
            return False
        uci = self.entr.coup_attendu_uci()
        if not uci:
            return False
        coup = chess.Move.from_uci(uci)
        if not self.entr.faute_sur_ce_coup:
            self.entr.fautes += 1
            self.entr.faute_sur_ce_coup = True
        self.plateau.indice = (coup.from_square, coup.to_square)
        self._dire("Le coup de la théorie : joue-le pour continuer.", AMBRE)
        return True

    # ------------------------------------------------------------ evenements
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return "quitter"
        if self.etape == "arbre":
            return self._evenement_arbre(event)
        return self._evenement_jeu(event)

    def _evenement_arbre(self, event):
        if event.type == pygame.KEYDOWN:
            touche = event.key
            if touche == pygame.K_ESCAPE:
                return "retour"
            if touche == pygame.K_DOWN:
                self._deplacer(1)
            elif touche == pygame.K_UP:
                self._deplacer(-1)
            elif touche == pygame.K_PAGEDOWN:
                self._deplacer(self.rangees_visibles - 1)
            elif touche == pygame.K_PAGEUP:
                self._deplacer(-(self.rangees_visibles - 1))
            elif touche in (pygame.K_RIGHT, pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                self._droite()
            elif touche in (pygame.K_LEFT, pygame.K_MINUS, pygame.K_KP_MINUS):
                self._gauche()
            elif touche in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.commencer()
            elif touche == pygame.K_BACKSPACE and self.choisi.parent is not None:
                self.choisir(self.choisi.parent)
            return None
        if event.type == pygame.MOUSEWHEEL:
            self.defilement -= 3 * int(getattr(event, "y", 0))
            self._borner_defilement()
            self._image_arbre = None
            return None
        if event.type == pygame.MOUSEMOTION:
            survol = self._rangee_sous(event.pos)
            if survol != self.survol:
                self.survol = survol
                self._image_arbre = None
        boutons = [self.btn_blancs, self.btn_noirs, self.btn_ici, self.btn_retour_choix]
        cle = ui.gerer_boutons(boutons, event)
        if cle == "retour":
            return "retour"
        if cle in ("blancs", "noirs"):
            self.couleur = chess.WHITE if cle == "blancs" else chess.BLACK
            self._image_arbre = None
            self._image_position = None
        elif cle == "ici":
            self.commencer()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._clic_arbre(event.pos)
        return None

    def _rangee_sous(self, pos):
        if not self.rect_arbre.collidepoint(pos):
            return None
        rang = self.defilement + (pos[1] - self.rect_arbre.y - int(6 * self.ech)) // self.h_rangee
        return rang if 0 <= rang < len(self.rangees()) else None

    def _clic_arbre(self, pos):
        if self.zone_hasard.collidepoint(pos):
            self.au_hasard = not self.au_hasard
            return
        for rect, noeud in self._ariane:
            if rect.collidepoint(pos):
                self.choisir(noeud)
                return
        rang = self._rangee_sous(pos)
        if rang is None:
            return
        chaine, niveau = self.rangees()[rang]
        fin = chaine[-1]
        maintenant = pygame.time.get_ticks()
        x_signe = self.rect_arbre.x + int(10 * self.ech) + min(niveau, NIVEAUX_EN_RETRAIT) * int(
            18 * self.ech)
        sur_le_signe = pos[0] < x_signe + int(24 * self.ech)
        deja = self.choisi in chaine
        double = self._dernier_clic[0] is fin and maintenant - self._dernier_clic[1] < DOUBLE_CLIC
        self._dernier_clic = (fin, maintenant)
        if fin.enfants and (sur_le_signe or deja or double):
            self.choisi = fin
            self.deplier(fin, fin not in self.deplies)
            self._image_position = None
            self._borner_defilement()
        else:
            self.choisir(fin)

    def _evenement_jeu(self, event):
        p = self.plateau
        if p.promotion.est_actif():
            p.handle_event(event)
            return None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if p.selected_square is not None or p.dragging or p.premove:
                    p.handle_event(event)
                    return None
                self._revenir_a_l_arbre()
                return None
            if event.key in (pygame.K_SPACE, pygame.K_RETURN) and self.entr and self.entr.termine():
                self.nouvelle_ligne()
                return None
        cle = ui.gerer_boutons([b for b in self.boutons_jeu if b.actif], event)
        if cle == "retour":
            return "retour"
        if cle == "changer":
            self._revenir_a_l_arbre()
        elif cle == "suivante":
            self.nouvelle_ligne()
        elif cle == "montrer":
            self.demander_un_indice()
        elif cle is None:
            p.handle_event(event)
        return None

    def _revenir_a_l_arbre(self):
        self.etape = "arbre"
        self._image_arbre = None
        self._image_position = None

    def update(self):
        if self.etape != "jeu":
            return
        if self.adverse_a and pygame.time.get_ticks() >= self.adverse_a:
            self._jouer_l_adversaire()
        self.plateau.update()

    # ------------------------------------------------------------ dessin
    def draw(self):
        t = apparence.theme(self.plateau.theme_plateau)
        self.screen.fill(t["fond"])
        if self.etape == "arbre":
            self._dessiner_arbre(t)
        else:
            self._dessiner_jeu(t)
        import succes
        succes.dessiner_annonce(self.screen)

    def _dessiner_arbre(self, t):
        ecran, ech = self.screen, self.ech
        largeur, _hauteur = ecran.get_size()
        m = self.marge
        ui.texte(ecran, "Entraînement aux ouvertures", m, self.y_titre, ui.t(26, ech),
                 t["texte"], gras=True)
        ui.texte(ecran, "Flèches ou clic pour avancer coup par coup, + / − pour déplier, "
                 "Entrée pour t'entraîner.", largeur - m, self.y_titre + ui.t(10, ech),
                 ui.t(12, ech), t["texte_discret"], ancre="droite",
                 largeur_max=largeur - 2 * m - ui.mesurer("Entraînement aux ouvertures",
                                                         ui.t(26, ech), True)[0] - m)
        self._dessiner_ariane(t)
        cle = self._cle_arbre(t)
        if self._image_arbre is None or self._image_arbre[0] != cle:
            self._image_arbre = (cle, self._fabriquer_l_arbre(t))
        ecran.blit(self._image_arbre[1], self.rect_arbre.topleft)
        self._dessiner_le_choisi(t)

    def _cle_arbre(self, t):
        return (self.defilement, self.choisi, self.survol, self.couleur, notation.choix(),
                self.rect_arbre.size, tuple(t["accent"]), tuple(t["panneau"]),
                len(entrainement.lignes_reussies(self.couleur)))

    def _fabriquer_l_arbre(self, t):
        """L'arbre dessine sur sa propre image : refaite seulement quand il
        change (deplier, choisir, defiler, survoler) - pas a chaque image."""
        ech = self.ech
        r = self.rect_arbre
        image = pygame.Surface(r.size).convert() if pygame.display.get_surface() else \
            pygame.Surface(r.size)
        image.fill(t["fond"])
        ui.cadre(image, image.get_rect(), t["panneau"], t["bord"], 1, 14)
        rangees = self.rangees()
        h = self.h_rangee
        y = int(6 * ech)
        taille = ui.t(14, ech)
        petite = ui.t(12, ech)
        l_droite = int(118 * ech)
        for i in range(self.defilement, min(len(rangees), self.defilement + self.rangees_visibles)):
            chaine, niveau = rangees[i]
            fin = chaine[-1]
            zone = pygame.Rect(int(6 * ech), y, r.width - int(12 * ech), h - 2)
            choisi = self.choisi in chaine
            if choisi:
                ui.cadre(image, zone, t["accent_doux"], t["accent"], 1, 6)
            elif i == self.survol:
                ui.cadre(image, zone, t["panneau_haut"], None, 0, 6)
            x = zone.x + int(4 * ech) + min(niveau, NIVEAUX_EN_RETRAIT) * int(18 * ech)
            yc = zone.centery
            # ligne choisie : texte sombre sur l'or (comme un bouton choisi)
            clair, discret = (t["fond"], t["fond"]) if choisi else (t["texte"], t["texte_discret"])
            if fin.enfants:
                signe = "−" if fin in self.deplies else "+"
                carre = pygame.Rect(x, yc - int(8 * ech), int(16 * ech), int(16 * ech))
                ui.cadre(image, carre, None, discret, 1, 3)
                ui.texte_centre_dans(image, signe, carre, ui.t(13, ech), clair, gras=True,
                                     marge=0)
            x += int(24 * ech)
            coups = arbre.etiquette_chaine(chaine, notation.afficher)
            couleur_coups = clair
            fin_x = zone.right - l_droite
            rect_coups = ui.texte(image, coups, x, yc - taille * 0.62, taille, couleur_coups,
                                  gras=True, largeur_max=max(20, fin_x - x))
            x = rect_coups.right + int(12 * ech)
            if fin.nom_lichess and fin_x - x > int(30 * ech):
                ui.texte(image, arbre.nom_en_arbre(fin.nom_lichess), x, yc - petite * 0.62,
                         petite, discret, largeur_max=fin_x - x)
            reussies = entrainement.reussies_sous(fin, self.couleur)
            ui.texte(image, "%d / %d" % (reussies, fin.nb_lignes), zone.right - int(8 * ech),
                     yc - petite * 0.62, petite,
                     discret if choisi else (t["succes"] if reussies == fin.nb_lignes else (
                         t["accent"] if reussies else t["texte_faible"])), ancre="droite")
            if fin.eco:
                ui.texte(image, fin.eco, zone.right - int(66 * ech), yc - petite * 0.62, petite,
                         discret, ancre="droite")
            y += h
        # barre de defilement
        if len(rangees) > self.rangees_visibles:
            haut = r.height - int(16 * ech)
            part = self.rangees_visibles / float(len(rangees))
            debut = self.defilement / float(len(rangees))
            pygame.draw.rect(image, t["accent_doux"], pygame.Rect(
                r.width - int(5 * ech), int(8 * ech) + int(haut * debut), max(3, int(3 * ech)),
                max(int(20 * ech), int(haut * part))), border_radius=2)
        return image

    def _dessiner_ariane(self, t):
        """« Début › 1.e4 › 1...e5 › 2.Nf3 » : chaque morceau ramene a son coup."""
        ecran, ech = self.screen, self.ech
        taille = ui.t(15, ech)
        x0, y = self.marge, self.y_ariane
        l_max = self.screen.get_width() - 2 * self.marge
        chemin = [self.racine] + self.choisi.chemin()
        morceaux = [("Début" if n is self.racine else arbre.etiquette_coup(n, True,
                                                                          notation.afficher), n)
                    for n in chemin]
        sep = arbre.SEPARATEUR
        l_sep = ui.mesurer(sep, taille)[0]
        largeurs = [ui.mesurer(txt, taille, True)[0] for txt, _n in morceaux]
        # trop long : on garde « Début », puis « … », puis la fin du chemin
        debut = 1
        total = sum(largeurs) + l_sep * (len(morceaux) - 1)
        l_points = ui.mesurer("…", taille)[0] + l_sep
        while total + (l_points if debut > 1 else 0) > l_max and debut < len(morceaux) - 1:
            total -= largeurs[debut] + l_sep
            debut += 1
        self._ariane = []
        x = x0
        for i, (txt, n) in enumerate(morceaux):
            if 0 < i < debut:
                if i == 1:
                    ui.texte(ecran, "…", x, y, taille, t["texte_discret"])
                    x += l_points - l_sep
                    ui.texte(ecran, sep, x, y, taille, t["texte_faible"])
                    x += l_sep
                continue
            dernier = i == len(morceaux) - 1
            rect = ui.texte(ecran, txt, x, y, taille,
                            t["accent"] if dernier else t["texte"], gras=True)
            self._ariane.append((rect.inflate(int(6 * ech), int(6 * ech)), n))
            x = rect.right
            if not dernier:
                ui.texte(ecran, sep, x, y, taille, t["texte_faible"])
                x += l_sep

    def _image_de_la_position(self, t):
        cote = self.rect_echiquier.width
        cle = (self.choisi, self.couleur, cote, tuple(t["clair"]), tuple(t["sombre"]),
               self.plateau.jeu_pieces)
        if self._image_position is not None and self._image_position[0] == cle:
            return self._image_position[1]
        sq = cote // 8
        image = pygame.Surface((cote, cote))
        matiere = apparence.damier_texture(t, cote)
        if matiere is not None:
            image.blit(matiere, (0, 0))
        retourne = self.couleur == chess.BLACK

        def place(case):
            col, rang = chess.square_file(case), chess.square_rank(case)
            return ((7 - col) * sq, rang * sq) if retourne else (col * sq, (7 - rang) * sq)
        for case in chess.SQUARES:
            if matiere is None:
                couleur = t["clair"] if (chess.square_file(case) + chess.square_rank(case)) % 2 \
                    else t["sombre"]
                image.fill(couleur, pygame.Rect(place(case), (sq, sq)))
        plateau = self.choisi.position()
        if plateau.move_stack:
            dernier = plateau.peek()
            voile = pygame.Surface((sq, sq), pygame.SRCALPHA)
            voile.fill(t["dernier"])
            for case in (dernier.from_square, dernier.to_square):
                image.blit(voile, place(case))
        if sq not in self._pieces:
            self._pieces = {sq: apparence.charger_jeu(self.plateau.jeu_pieces, sq)}
        pieces = self._pieces[sq]
        for case, piece in plateau.piece_map().items():
            img = pieces.get(piece.symbol())
            if img is not None:
                x, y = place(case)
                image.blit(img, (x + (sq - img.get_width()) // 2, y + (sq - img.get_height()) // 2))
        self._image_position = (cle, image)
        return image

    def _dessiner_le_choisi(self, t):
        ecran, ech = self.screen, self.ech
        r = self.rect_echiquier
        ecran.blit(self._image_de_la_position(t), r.topleft)
        pygame.draw.rect(ecran, t["bord"], r.inflate(4, 4), 2)
        n = self.choisi
        x, l = r.x, r.width
        y = self.y_infos
        nom = n.nom() if n is not self.racine else "Toutes les ouvertures"
        hauteur_nom = ui.paragraphe(ecran, nom or "Position de départ",
                                    (x, y, l, ui.t(17, ech) * 3), ui.t(17, ech),
                                    t["texte"], gras=True, interligne=1.15, max_lignes=2)
        y += hauteur_nom + int(4 * ech)
        reussies = entrainement.reussies_sous(n, self.couleur)
        eco = n.code_eco()
        ligne = ("ECO %s   ·   %d lignes" % (eco, n.nb_lignes)) if eco else "%d lignes" % n.nb_lignes
        ui.texte(ecran, ligne, x, y, ui.t(13, ech), t["texte_discret"], largeur_max=l)
        y += ui.t(20, ech)
        ui.texte(ecran, "Réussies sans faute : %d / %d" % (reussies, n.nb_lignes), x, y,
                 ui.t(13, ech), t["accent"] if reussies else t["texte_discret"], largeur_max=l)
        y += ui.t(20, ech)
        if y + int(6 * ech) <= self.bas_infos:
            fond = pygame.Rect(x, y, l, max(3, int(5 * ech)))
            pygame.draw.rect(ecran, t["panneau_haut"], fond, border_radius=3)
            if reussies:
                plein = fond.copy()
                plein.width = max(3, int(l * reussies / float(max(1, n.nb_lignes))))
                pygame.draw.rect(ecran, t["accent"], plein, border_radius=3)
        self.btn_blancs.selectionne = self.couleur == chess.WHITE
        self.btn_noirs.selectionne = self.couleur == chess.BLACK
        self.btn_ici.couleur_fond = t["accent_doux"]
        souris = pygame.mouse.get_pos()
        for b in (self.btn_blancs, self.btn_noirs, self.btn_ici, self.btn_retour_choix):
            b.maj_survol(souris)
            b.dessiner(ecran, t)
        z = self.zone_hasard
        case = pygame.Rect(z.x, z.centery - int(9 * ech), int(18 * ech), int(18 * ech))
        ui.case_a_cocher(ecran, case, self.au_hasard, "Au hasard dans ce groupe", t,
                         taille=ui.t(13, ech), largeur_max=z.width - case.width - int(12 * ech))

    def _dessiner_jeu(self, t):
        ecran, ech, p = self.screen, self.ech, self.plateau
        p.renderer.dessiner_plateau(avec_interaction=True)
        cote = p.SQ_SIZE * 8
        rect_plateau = pygame.Rect(self.disposition.plateau_x, self.disposition.plateau_y,
                                   cote, cote)
        if self.flash:
            couleur, debut = self.flash
            age = pygame.time.get_ticks() - debut
            if age < DUREE_FLASH:
                ui.voile(ecran, rect_plateau, int(90 * (1 - age / float(DUREE_FLASH))), couleur)
            else:
                self.flash = None
        p.promotion.draw(ecran)
        ui.cadre(ecran, self.panneau, t["panneau"], t["bord"], 1, 14)
        x, l = self.x, self.l
        y = self.panneau.y + int(12 * ech)
        ui.texte(ecran, "Ouvertures  -  %s" % ("avec les Blancs" if self.couleur == chess.WHITE
                                              else "avec les Noirs"), x, y, ui.t(13, ech),
                 t["texte_discret"], largeur_max=l)
        y += ui.t(22, ech)
        groupe = self.seance.noeud if self.seance else None
        titre = (groupe.nom() if groupe is not None and groupe is not self.racine
                 else "Toutes les ouvertures")
        ui.texte(ecran, titre, x, y, ui.t(20, ech), t["texte"], gras=True,
                 largeur_max=l, ajuster=True)
        y += ui.t(30, ech)
        e = self.entr
        if e is not None:
            fini = e.termine()
            nom = e.resume() if fini else (ouvertures.nom_de_l_ouverture(e.coups[:e.avance])
                                           or "Position de départ")
            ui.texte(ecran, nom, x, y, ui.t(13, ech), t["accent"] if fini else t["texte_discret"],
                     largeur_max=l, ajuster=True)
            y += ui.t(22, ech)
            s = self.seance
            if s is not None:
                ui.texte(ecran, "Ligne %d / %d   ·   tour %d   ·   à revoir %d" % (
                    s.numero, s.taille_tour, s.tour, len(s.a_revoir)), x, y, ui.t(13, ech),
                    t["texte_discret"], largeur_max=l)
                y += ui.t(20, ech)
            ui.texte(ecran, "Coup %d / %d   ·   trouvés %d   ·   ratés %d" % (
                e.avance, len(e.coups), e.trouves, e.fautes), x, y, ui.t(13, ech),
                t["texte_discret"], largeur_max=l)
            y += ui.t(24, ech)
            ui.separateur(ecran, x, y, l, t["bord"])
            y += int(10 * ech)
            ui.texte(ecran, self.message, x, y, ui.t(15, ech), self.couleur_message or t["texte"],
                     gras=True, largeur_max=l, ajuster=True)
            y += ui.t(28, ech)
            morceaux = []
            for i, san in enumerate(e.coups[:e.avance]):
                san = notation.afficher(san)
                morceaux.append(("%d. %s" % (i // 2 + 1, san)) if i % 2 == 0 else san)
            ui.paragraphe(ecran, "  ".join(morceaux), (x, y, l, max(0, self.bas_texte - y)),
                          ui.t(14, ech), t["texte"])
            self.btn_montrer.actif = e.a_moi_de_jouer() and not self.adverse_a
            self.btn_suivante.selectionne = fini
        souris = pygame.mouse.get_pos()
        for b in self.boutons_jeu:
            b.maj_survol(souris)
            b.dessiner(ecran, t)

    def run(self, clock, evenement_fenetre=None):
        cadence = ui.Cadence()       # 23/10 : 30 images/s au repos
        while True:
            evenements = ui.evenements()
            for event in evenements:
                if evenement_fenetre is not None and evenement_fenetre(event):
                    self._placer(pygame.display.get_surface())
                    continue
                reponse = self.handle_event(event)
                if reponse:
                    return reponse
            self.update()
            self.draw()
            ui.afficher()
            clock.tick(cadence.suivante(evenements, bool(getattr(getattr(getattr(self, 'plateau', None), 'animation', None), 'animations', None))))
