# ecran_mes_parties.py - SickChess : "Mes parties et profil".
#
# Reunit en un seul ecran ce qui etait eclate dans V8_TURBO_3000
# (profil_screen.py + ecran_historique.py) :
#   - a gauche, la fiche du joueur : nom (modifiable), classement Elo estime,
#     victoires / nulles / defaites contre l'ordinateur, courbe de progression ;
#   - a droite, toutes les parties terminees (dossier parties/, en PGN), la plus
#     recente en haut. Un clic sur une ligne ouvre la relecture coup par coup.
#
# run() renvoie "retour", "quitter" ou {"action": "revoir", "partie": {...}}.

import os

import pygame

import apparence
import design
import historique_parties
import ui
from profil import get_profil

VERT = (112, 188, 112)
ROUGE = (222, 112, 100)

ETIQUETTES = {"victoire": ("V", VERT), "defaite": ("D", ROUGE),
              "nulle": ("N", None)}


class EcranMesParties:
    def __init__(self, screen, theme_plateau=None):
        self.screen = screen
        self.theme_plateau = theme_plateau
        self.profil = get_profil()
        self.parties = historique_parties.lister()
        self.message = ""
        self.premiere_ligne = 0
        self.lignes_visibles = 1
        self.rects_lignes = []

        self.champ_nom = ui.ChampTexte(18)
        self.edition = False

        self.btn_retour = ui.Bouton((0, 0, 10, 10), "Retour", "retour")
        self.btn_dossier = ui.Bouton((0, 0, 10, 10), "Ouvrir le dossier", "dossier",
                                     taille=16)
        self.btn_nom = ui.Bouton((0, 0, 10, 10), "Changer de nom", "nom",
                                 taille=14, gras=False)
        self.boutons = [self.btn_retour, self.btn_dossier, self.btn_nom]
        self._placer()

    # ------------------------------------------------------------- placement

    def _placer(self, screen=None):
        if screen is not None:
            self.screen = screen
        largeur, hauteur = self.screen.get_size()
        ech = ui.echelle(self.screen)
        self.ech = ech
        marge = int(24 * ech)

        h_titre = ui.police(ui.t(30, ech), True).get_height()
        self.y_titre = marge
        haut = marge + h_titre + int(30 * ech)

        h_bouton = int(46 * ech)
        bas = hauteur - marge - h_bouton
        l_bouton = int(210 * ech)
        self.btn_retour.placer((marge, bas, l_bouton, h_bouton))
        self.btn_dossier.placer((largeur - marge - l_bouton, bas, l_bouton, h_bouton))

        zone_h = bas - int(16 * ech) - haut
        l_fiche = max(int(270 * ech), min(int(360 * ech), int(largeur * 0.32)))
        self.fiche = pygame.Rect(marge, haut, l_fiche, zone_h)
        x_liste = self.fiche.right + int(18 * ech)
        self.liste = pygame.Rect(x_liste, haut, largeur - marge - x_liste, zone_h)

        self.hauteur_ligne = int(60 * ech)
        self.lignes_visibles = max(1, (self.liste.height - int(36 * ech))
                                   // self.hauteur_ligne)
        self._borner()

    def _borner(self):
        maximum = max(0, len(self.parties) - self.lignes_visibles)
        self.premiere_ligne = max(0, min(self.premiere_ligne, maximum))

    def defiler(self, pas):
        self.premiere_ligne += pas
        self._borner()

    # ------------------------------------------------------------- actions

    def _commencer_edition(self):
        self.edition = True
        self.champ_nom.contenu = self.profil.nom
        self.champ_nom.activer(True)

    def _finir_edition(self, garder=True):
        if not self.edition:
            return
        nom = " ".join(self.champ_nom.contenu.split())[:18]
        if garder and nom:
            self.profil.nom = nom
            self.profil.enregistrer()
        self.edition = False
        self.champ_nom.activer(False)

    def ouvrir_le_dossier(self):
        dossier = historique_parties.dossier_parties()
        try:
            os.startfile(dossier)                       # Windows
            return True
        except AttributeError:
            self.message = "Dossier : %s" % dossier      # autre systeme
        except OSError as souci:
            self.message = str(souci)
        return False

    def revoir(self, index):
        try:
            partie = self.parties[int(index)]
        except (ValueError, IndexError, TypeError):
            return None
        if not os.path.exists(partie.get("chemin", "")):
            self.message = "Ce fichier n'existe plus : %s" % partie.get("fichier")
            return None
        return {"action": "revoir", "partie": partie}

    # ------------------------------------------------------------- evenements

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return "quitter"

        if self.edition:
            reponse = self.champ_nom.handle_event(event)
            if reponse == "valider":
                self._finir_edition(True)
                return None
            if reponse == "annuler":
                self._finir_edition(False)
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                    and not self.rect_champ.collidepoint(event.pos):
                self._finir_edition(True)
            elif event.type != pygame.MOUSEBUTTONDOWN:
                return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "retour"
            pas = {pygame.K_DOWN: 1, pygame.K_UP: -1,
                   pygame.K_PAGEDOWN: self.lignes_visibles,
                   pygame.K_PAGEUP: -self.lignes_visibles}.get(event.key)
            if pas:
                self.defiler(pas)
            return None

        if event.type == pygame.MOUSEWHEEL:
            self.defiler(-int(getattr(event, "y", 0)))
            return None

        cle = ui.gerer_boutons(self.boutons, event)
        if cle == "retour":
            return "retour"
        if cle == "dossier":
            self.ouvrir_le_dossier()
            return None
        if cle == "nom":
            self._commencer_edition()
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, index in self.rects_lignes:
                if rect.collidepoint(event.pos):
                    return self.revoir(index)
        return None

    # ------------------------------------------------------------- dessin

    def draw(self):
        ecran = self.screen
        t = apparence.theme(self.theme_plateau)
        ech = self.ech
        largeur, hauteur = ecran.get_size()
        design.degrade_vertical(ecran, ecran.get_rect(),
                                design.eclaircir(t["fond"], 0.06),
                                design.assombrir(t["fond"], 0.10))

        marge = self.fiche.x
        ui.texte(ecran, "Mes parties", marge, self.y_titre, ui.t(30, ech),
                 t["texte"], gras=True)
        sous_titre = self.message or (
            "Clique une partie pour la revoir coup par coup."
            if self.parties else "Tes parties terminées apparaîtront ici.")
        ui.texte(ecran, sous_titre, marge,
                 self.y_titre + ui.police(ui.t(30, ech), True).get_height() + 2,
                 ui.t(14, ech), ROUGE if self.message else t["texte_discret"],
                 largeur_max=largeur - 2 * marge)

        self._dessiner_fiche(ecran, t, ech)
        self._dessiner_liste(ecran, t, ech)

        souris = pygame.mouse.get_pos()
        for bouton in (self.btn_retour, self.btn_dossier):
            bouton.maj_survol(souris)
            bouton.dessiner(ecran, t, rayon=10)

    # ---- fiche du joueur

    def _dessiner_fiche(self, ecran, t, ech):
        zone = self.fiche
        ui.cadre(ecran, zone, t["panneau"], t["bord"], 1, 14, ombre=True)
        x = zone.x + int(18 * ech)
        l = zone.width - int(36 * ech)
        y = zone.y + int(16 * ech)

        ui.texte(ecran, "PROFIL", x, y, ui.t(12, ech), t["texte_discret"], gras=True)
        y += ui.police(ui.t(12, ech), True).get_height() + int(6 * ech)

        h_nom = ui.police(ui.t(22, ech), True).get_height() + int(10 * ech)
        self.rect_champ = pygame.Rect(x, y, l, h_nom)
        if self.edition:
            self.champ_nom.dessiner(ecran, self.rect_champ, t, ui.t(18, ech),
                                    invite="Ton nom")
            ui.texte(ecran, "Entrée pour valider, Échap pour annuler", x,
                     y + h_nom + int(6 * ech), ui.t(12, ech), t["texte_discret"],
                     largeur_max=l)
            self.btn_nom.placer((0, 0, 0, 0))
        else:
            ui.texte(ecran, self.profil.nom, x, y + int(4 * ech), ui.t(22, ech),
                     t["texte"], gras=True, largeur_max=l, ajuster=True)
            self.btn_nom.placer((x, y + h_nom + int(2 * ech), int(150 * ech),
                                 int(28 * ech)))
            self.btn_nom.maj_survol(pygame.mouse.get_pos())
            self.btn_nom.dessiner(ecran, t, rayon=8)
        y += h_nom + int(44 * ech)

        stats = self.profil.statistiques()
        taille_elo = ui.t(46, ech)
        ui.texte(ecran, str(self.profil.elo), x, y, taille_elo, t["accent"], gras=True)
        larg_elo = ui.mesurer(str(self.profil.elo), taille_elo, True)[0]
        h_elo = ui.police(taille_elo, True).get_height()
        ui.texte(ecran, "Elo estimé", x + larg_elo + int(10 * ech),
                 y + h_elo - ui.police(ui.t(14, ech)).get_height() - int(8 * ech),
                 ui.t(14, ech), t["texte_discret"],
                 largeur_max=l - larg_elo - int(10 * ech))
        y += h_elo + int(2 * ech)
        detail = "Meilleur : %d" % stats["meilleur_elo"] if stats["parties"] \
            else "Départ à %d, il bouge à chaque partie contre l'ordinateur" \
            % self.profil.elo
        ui.texte(ecran, detail, x, y, ui.t(13, ech), t["texte_discret"],
                 largeur_max=l, ajuster=True)
        y += ui.police(ui.t(13, ech)).get_height() + int(16 * ech)

        # Trois tuiles : victoires / nulles / defaites
        ecart = int(8 * ech)
        lt = (l - 2 * ecart) // 3
        ht = int(58 * ech)
        for i, (nombre, libelle, couleur) in enumerate((
                (stats["victoires"], "victoires", VERT),
                (stats["nulles"], "nulles", t["texte"]),
                (stats["defaites"], "defaites", ROUGE))):
            tuile = pygame.Rect(x + i * (lt + ecart), y, lt, ht)
            ui.cadre(ecran, tuile, t["fond"], t["bord"], 1, 10)
            ui.texte(ecran, str(nombre), tuile.centerx, tuile.y + int(6 * ech),
                     ui.t(22, ech), couleur, gras=True, ancre="centre")
            ui.texte(ecran, libelle, tuile.centerx,
                     tuile.bottom - ui.police(ui.t(12, ech)).get_height() - int(6 * ech),
                     ui.t(12, ech), t["texte_discret"], ancre="centre",
                     largeur_max=lt - 6)
        y += ht + int(10 * ech)
        if stats["parties"]:
            ligne = "%d partie%s contre l'ordinateur  -  %s %% des points" % (
                stats["parties"], "s" if stats["parties"] > 1 else "",
                ("%.0f" % stats["pourcentage"]))
        else:
            ligne = "Aucune partie contre l'ordinateur pour l'instant"
        ui.texte(ecran, ligne, x, y, ui.t(13, ech), t["texte_discret"],
                 largeur_max=l, ajuster=True)
        y += ui.police(ui.t(13, ech)).get_height() + int(18 * ech)

        # Courbe de progression, dans la place qui reste
        bas = zone.bottom - int(16 * ech)
        if bas - y >= int(70 * ech):
            ui.texte(ecran, "PROGRESSION", x, y, ui.t(12, ech), t["texte_discret"],
                     gras=True)
            y += ui.police(ui.t(12, ech), True).get_height() + int(6 * ech)
            self._courbe(ecran, t, pygame.Rect(x, y, l, bas - y), ech)

    def _courbe(self, ecran, t, rect, ech):
        ui.cadre(ecran, rect, t["fond"], t["bord"], 1, 10)
        valeurs = [self.profil.parties[0].get("elo_avant", self.profil.elo)] \
            if self.profil.parties else []
        valeurs += self.profil.courbe_elo(60)
        if len(valeurs) < 2:
            ui.paragraphe(ecran, "La courbe se dessine après ta première partie "
                          "contre l'ordinateur.",
                          rect.inflate(-int(20 * ech), -int(16 * ech)),
                          ui.t(12, ech), t["texte_discret"])
            return
        bas_v, haut_v = min(valeurs), max(valeurs)
        if haut_v - bas_v < 40:                      # evite une courbe ecrasee
            milieu = (haut_v + bas_v) / 2.0
            bas_v, haut_v = milieu - 20, milieu + 20
        interieur = rect.inflate(-int(24 * ech), -int(24 * ech))
        points = []
        for i, v in enumerate(valeurs):
            px = interieur.x + interieur.width * i / float(len(valeurs) - 1)
            py = interieur.bottom - interieur.height * (v - bas_v) / float(haut_v - bas_v)
            points.append((int(px), int(py)))
        pygame.draw.lines(ecran, t["accent"], False, points, max(2, int(2 * ech)))
        pygame.draw.circle(ecran, t["accent"], points[-1], max(3, int(4 * ech)))
        ui.texte(ecran, str(int(max(valeurs))), rect.right - int(8 * ech),
                 rect.y + int(4 * ech), ui.t(11, ech), t["texte_discret"],
                 ancre="droite")
        ui.texte(ecran, str(int(min(valeurs))), rect.right - int(8 * ech),
                 rect.bottom - ui.police(ui.t(11, ech)).get_height() - int(4 * ech),
                 ui.t(11, ech), t["texte_discret"], ancre="droite")

    # ---- liste des parties

    def _dessiner_liste(self, ecran, t, ech):
        zone = self.liste
        ui.cadre(ecran, zone, t["panneau"], t["bord"], 1, 14, ombre=True)
        self.rects_lignes = []
        if not self.parties:
            ui.paragraphe(ecran,
                          "Aucune partie enregistrée pour l'instant.\n\n"
                          "Chaque partie terminée (contre l'ordinateur ou à deux) "
                          "est rangee toute seule dans le dossier parties/, au "
                          "format PGN, que lichess et chess.com savent aussi lire.",
                          zone.inflate(-int(40 * ech), -int(40 * ech)),
                          ui.t(15, ech), t["texte_discret"])
            return

        souris = pygame.mouse.get_pos()
        y = zone.y + int(10 * ech)
        fin = min(len(self.parties), self.premiere_ligne + self.lignes_visibles)
        for index in range(self.premiere_ligne, fin):
            partie = self.parties[index]
            rect = pygame.Rect(zone.x + int(10 * ech), y,
                               zone.width - int(20 * ech),
                               self.hauteur_ligne - int(6 * ech))
            survol = rect.collidepoint(souris)
            ui.cadre(ecran, rect, t["fond"], t["accent"] if survol else t["bord"],
                     2 if survol else 1, 10)

            # Pastille : V / N / D pour tes parties, "2J" pour une partie a deux
            cote = rect.height - int(18 * ech)
            pastille = pygame.Rect(rect.x + int(9 * ech),
                                   rect.centery - cote // 2, cote, cote)
            lettre, couleur = ETIQUETTES.get(partie.get("verdict"), ("2J", None))
            couleur = couleur or t["texte_discret"]
            pygame.draw.rect(ecran, couleur, pastille, border_radius=int(8 * ech))
            ui.texte_centre_dans(ecran, lettre, pastille, ui.t(16, ech),
                                 t["fond"], gras=True, marge=2)

            l_bouton = int(92 * ech)
            x_texte = pastille.right + int(12 * ech)
            place = rect.right - l_bouton - int(20 * ech) - x_texte
            h1 = ui.police(ui.t(15, ech), True).get_height()
            y_texte = rect.y + (rect.height - h1 - ui.police(ui.t(12, ech)).get_height()
                                - int(2 * ech)) // 2
            ui.texte(ecran, historique_parties.resume(partie), x_texte, y_texte,
                     ui.t(15, ech), t["texte"], gras=True, largeur_max=place)
            details = [partie.get("date", ""), partie.get("cadence", ""),
                       historique_parties.ouverture(partie)]
            if not partie.get("ouverture"):
                details.append(partie.get("raison", ""))
            ui.texte(ecran, "  -  ".join(d for d in details if d), x_texte,
                     y_texte + h1 + int(2 * ech), ui.t(12, ech),
                     t["texte_discret"], largeur_max=place)

            bouton = pygame.Rect(rect.right - int(10 * ech) - l_bouton,
                                 rect.centery - int(15 * ech), l_bouton, int(30 * ech))
            ui.cadre(ecran, bouton, t["accent"] if survol else t["panneau"],
                     None if survol else t["bord"], 1, 8)
            ui.texte_centre_dans(ecran, "Revoir", bouton, ui.t(14, ech),
                                 t["fond"] if survol else t["texte"], gras=True)

            self.rects_lignes.append((rect, index))
            y += self.hauteur_ligne

        if len(self.parties) > self.lignes_visibles:
            note = "%d-%d sur %d  (molette pour defiler)" % (
                self.premiere_ligne + 1, fin, len(self.parties))
            ui.texte(ecran, note, zone.right - int(12 * ech),
                     zone.bottom - ui.police(ui.t(12, ech)).get_height() - int(6 * ech),
                     ui.t(12, ech), t["texte_discret"], ancre="droite")

    # ------------------------------------------------------------- boucle

    def run(self, clock, evenement_fenetre=None, apres_dessin=None):
        """Boucle autonome. evenement_fenetre(event) -> True si F11/F1/taille."""
        while True:
            for event in pygame.event.get():
                if evenement_fenetre is not None and evenement_fenetre(event):
                    self._placer(pygame.display.get_surface())
                    continue
                reponse = self.handle_event(event)
                if reponse is not None:
                    self._finir_edition(True)
                    return reponse
            self.draw()
            if apres_dessin is not None:
                apres_dessin(self.screen)
            pygame.display.flip()
            clock.tick(60)
