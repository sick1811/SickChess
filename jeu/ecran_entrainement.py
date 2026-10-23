# ecran_entrainement.py - SickChess 17/10 (travail p06) : l'ecran de
# l'entraineur d'ouvertures. La logique est dans entrainement.py ; le plateau
# est celui des problemes (PlateauProbleme : le vrai plateau de la partie, dont
# seul le coup du joueur est arbitre).
#   1. choix de la couleur et de l'ouverture (les plus jouees d'abord) ;
#   2. le jeu joue les coups adverses de la theorie, tu trouves les tiens ;
#   3. faux : rouge, on reessaie ; « Montrer le coup » (H) dessine la fleche ;
#   4. fin de ligne : ton score, le nom exact de la variante, et la suivante.

import chess
import pygame

import apparence
import entrainement
import notation
import ouvertures
import ui
from ecran_problemes import PlateauProbleme, VERT, ROUGE, AMBRE
from layout import Disposition

PAUSE_ADVERSE = 500
DUREE_FLASH = 500
PAR_PAGE = 24


class EcranEntrainement:
    def __init__(self, screen, preferences=None):
        self.screen = screen
        self.preferences = dict(preferences or {})
        self.etape = "choix"
        self.couleur = chess.WHITE
        self.page = 0
        self.familles = entrainement.familles()
        self.famille = None
        self.entr = None
        self.message, self.couleur_message = "", None
        self.flash = None
        self.adverse_a = 0
        self.disposition = Disposition(*screen.get_size())
        self.plateau = PlateauProbleme(screen, self.preferences, self.disposition, self)

        self.btn_blancs = ui.Bouton((0, 0, 10, 10), "Je joue les Blancs", "blancs", taille=17)
        self.btn_noirs = ui.Bouton((0, 0, 10, 10), "Je joue les Noirs", "noirs", taille=17)
        self.btn_page_moins = ui.Bouton((0, 0, 10, 10), "<", "page_moins", taille=18)
        self.btn_page_plus = ui.Bouton((0, 0, 10, 10), ">", "page_plus", taille=18)
        self.btn_retour_choix = ui.Bouton((0, 0, 10, 10), "Retour", "retour", taille=16)
        self.btns_familles = []

        self.btn_montrer = ui.Bouton((0, 0, 10, 10), "Montrer le coup (H)", "montrer", taille=15)
        self.btn_suivante = ui.Bouton((0, 0, 10, 10), "Ligne suivante", "suivante", taille=17)
        self.btn_changer = ui.Bouton((0, 0, 10, 10), "Changer d'ouverture", "changer", taille=14)
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
        # choix
        lc = min(int(900 * ech), largeur - 40)
        cx = (largeur - lc) // 2
        y = int(hauteur * 0.17)
        hb = int(44 * ech)
        demi = (lc - int(12 * ech)) // 2
        self.btn_blancs.placer((cx, y, demi, hb))
        self.btn_noirs.placer((cx + lc - demi, y, demi, hb))
        y += hb + int(22 * ech)
        colonnes = 3
        ecart = int(8 * ech)
        lf = (lc - (colonnes - 1) * ecart) // colonnes
        hf = int(38 * ech)
        lignes = max(1, (hauteur - y - int(110 * ech)) // (hf + ecart))
        self.par_page = min(PAR_PAGE, lignes * colonnes)
        debut = self.page * self.par_page
        self.btns_familles = []
        for i, (nom, n) in enumerate(self.familles[debut:debut + self.par_page]):
            ligne, col = divmod(i, colonnes)
            b = ui.Bouton((cx + col * (lf + ecart), y + ligne * (hf + ecart), lf, hf),
                          nom, "famille_" + nom, taille=14, gras=False)
            b.nombre = n
            self.btns_familles.append(b)
        y_bas = hauteur - int(70 * ech)
        self.btn_page_moins.placer((cx, y_bas, int(60 * ech), int(40 * ech)))
        self.btn_page_plus.placer((cx + lc - int(60 * ech), y_bas, int(60 * ech), int(40 * ech)))
        self.btn_retour_choix.placer((cx + lc // 2 - int(100 * ech), y_bas, int(200 * ech),
                                      int(40 * ech)))
        self.colonne_choix = (cx, lc)

    def pages(self):
        return max(1, (len(self.familles) + self.par_page - 1) // self.par_page)

    # ------------------------------------------------------------ deroulement
    def commencer(self, famille, couleur=None):
        self.famille = famille
        if couleur is not None:
            self.couleur = couleur
        self.etape = "jeu"
        self.nouvelle_ligne()

    def nouvelle_ligne(self):
        sauf = self.entr.coups if self.entr else None
        ligne = entrainement.tirer_une_ligne(self.famille, sauf=sauf)
        if ligne is None:
            self._dire("Aucune ligne pour cette ouverture.", AMBRE)
            return
        self.entr = entrainement.Entrainement(ligne, self.couleur)
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
            entrainement.noter_une_ligne(self.famille, self.couleur, note)
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
        if self.etape == "choix":
            return self._evenement_choix(event)
        return self._evenement_jeu(event)

    def _evenement_choix(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "retour"
        if event.type == pygame.MOUSEWHEEL:
            self.page = max(0, min(self.pages() - 1, self.page - int(getattr(event, "y", 0))))
            self._placer()
            return None
        boutons = [self.btn_blancs, self.btn_noirs, self.btn_page_moins, self.btn_page_plus,
                   self.btn_retour_choix] + self.btns_familles
        cle = ui.gerer_boutons(boutons, event)
        if cle == "retour":
            return "retour"
        if cle == "blancs":
            self.couleur = chess.WHITE
        elif cle == "noirs":
            self.couleur = chess.BLACK
        elif cle in ("page_moins", "page_plus"):
            self.page = max(0, min(self.pages() - 1, self.page + (1 if cle == "page_plus" else -1)))
            self._placer()
        elif cle and cle.startswith("famille_"):
            self.commencer(cle[8:])
        return None

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
                self.etape = "choix"
                return None
            if event.key in (pygame.K_SPACE, pygame.K_RETURN) and self.entr and self.entr.termine():
                self.nouvelle_ligne()
                return None
        cle = ui.gerer_boutons([b for b in self.boutons_jeu if b.actif], event)
        if cle == "retour":
            return "retour"
        if cle == "changer":
            self.etape = "choix"
        elif cle == "suivante":
            self.nouvelle_ligne()
        elif cle == "montrer":
            self.demander_un_indice()
        elif cle is None:
            p.handle_event(event)
        return None

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
        if self.etape == "choix":
            self._dessiner_choix(t)
        else:
            self._dessiner_jeu(t)
        import succes
        succes.dessiner_annonce(self.screen)

    def _dessiner_choix(self, t):
        ecran, ech = self.screen, self.ech
        largeur, hauteur = ecran.get_size()
        cx, lc = self.colonne_choix
        ui.texte(ecran, "Entraînement aux ouvertures", largeur // 2, int(hauteur * 0.05),
                 ui.t(34, ech), t["texte"], gras=True, ancre="centre")
        ui.texte(ecran, "Le jeu joue les coups adverses de la théorie, à toi de trouver les tiens.",
                 largeur // 2, int(hauteur * 0.05) + ui.t(44, ech), ui.t(14, ech),
                 t["texte_discret"], ancre="centre", largeur_max=lc)
        self.btn_blancs.selectionne = self.couleur == chess.WHITE
        self.btn_noirs.selectionne = self.couleur == chess.BLACK
        souris = pygame.mouse.get_pos()
        for b in [self.btn_blancs, self.btn_noirs, self.btn_retour_choix]:
            b.maj_survol(souris)
            b.dessiner(ecran, t)
        self.btn_page_moins.actif = self.page > 0
        self.btn_page_plus.actif = self.page < self.pages() - 1
        for b in (self.btn_page_moins, self.btn_page_plus):
            b.maj_survol(souris)
            b.dessiner(ecran, t)
        for b in self.btns_familles:
            b.maj_survol(souris)
            b.dessiner(ecran, t)
            nom = b.cle[8:]
            prog = entrainement.progression(nom, self.couleur)
            info = ("%d lignes" % b.nombre) if not prog else "%.0f %%" % prog["moyenne"]
            ui.texte(ecran, info, b.rect.right - int(8 * ech), b.rect.bottom - int(14 * ech),
                     ui.t(10, ech), t["accent"] if prog else t["texte_discret"], ancre="droite")
        ui.texte(ecran, "Page %d / %d" % (self.page + 1, self.pages()), largeur // 2,
                 self.btn_retour_choix.rect.y - int(22 * ech), ui.t(12, ech),
                 t["texte_discret"], ancre="centre")

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
        ui.texte(ecran, self.famille or "", x, y, ui.t(22, ech), t["texte"], gras=True,
                 largeur_max=l, ajuster=True)
        y += ui.t(32, ech)
        e = self.entr
        if e is not None:
            fini = e.termine()
            nom = e.resume() if fini else (ouvertures.nom_de_l_ouverture(e.coups[:e.avance])
                                           or "Position de départ")
            ui.texte(ecran, nom, x, y, ui.t(13, ech), t["accent"] if fini else t["texte_discret"],
                     largeur_max=l, ajuster=True)
            y += ui.t(22, ech)
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
