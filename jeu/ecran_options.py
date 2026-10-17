# ecran_options.py - SickChess : l'ecran Options (apparence, partie, son, affichage).
#
# Reprend l'idee de personnalisation_screen.py (V8_TURBO_3000), en plus simple :
#   - quatre onglets au lieu d'une seule longue liste ;
#   - un apercu de l'echiquier qui change EN DIRECT pendant qu'on choisit ;
#   - uniquement des reglages qui font vraiment quelque chose dans SickChess
#     (la voix des puzzles, la poussiere du fond, etc. reviendront avec les
#     ecrans qui s'en servent) ;
#   - Annuler remet tout comme avant, meme ce qui a ete applique en direct.
#
# Ajouter un reglage = ajouter une ligne dans ONGLETS (et sa valeur par
# defaut dans apparence.DEFAUTS ou DEFAUTS_EN_PLUS ci-dessous).

import json

import chess
import pygame

import apparence
import board_geometry as geo
import design
import ui
from settings_screen import charger_config, _chemin_config

OUI_NON = [("Oui", True), ("Non", False)]

DEFAUTS_EN_PLUS = {
    "hotseat_retourner_plateau": True,
    "plein_ecran": False,
}

POSITION_APERCU = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1"


class Reglage:
    """Une ligne : un libelle, une explication, des valeurs cliquables."""

    def __init__(self, cle, libelle, explication, valeurs, colonnes=4):
        self.cle = cle
        self.libelle = libelle
        self.explication = explication
        self.valeurs = list(valeurs)          # [(libelle, valeur), ...]
        self.colonnes = colonnes
        self.zones = []                       # [(rect, valeur)] apres dessin

    def rang_choisi(self, actuel):
        """Le rang de la valeur actuelle. Pour un nombre : la plus proche
        (un config.json ecrit a la main avec 0.55 allume quand meme 'Moyen')."""
        for rang, (_nom, v) in enumerate(self.valeurs):
            if v == actuel and type(v) is type(actuel):
                return rang
        if isinstance(actuel, (int, float)) and not isinstance(actuel, bool):
            nombres = [(abs(float(v) - actuel), rang)
                       for rang, (_n, v) in enumerate(self.valeurs)
                       if isinstance(v, (int, float)) and not isinstance(v, bool)]
            if nombres:
                return min(nombres)[1]
        return -1


def _onglets():
    damiers = [(apparence.nom_theme(c), c) for c in apparence.ORDRE_THEMES]
    accents = [(nom, cle) for cle, nom in apparence.accents_disponibles()]
    jeux = [(apparence.nom_jeu(c), c) for c in apparence.jeux_disponibles()]
    echiquier = [
        Reglage("theme_plateau", "Damier", "Les couleurs des cases",
                damiers, 4),
        Reglage("accent", "Couleur d'accent",
                "Titres, surlignages et boutons", accents, 3),
    ]
    if len(jeux) > 1:          # un choix a une seule valeur n'est pas un choix
        echiquier.append(Reglage("jeu_pieces", "Pièces", "Le dessin des pièces",
                                 jeux, 3))
    echiquier += [
        Reglage("afficher_coordonnees", "Coordonnées",
                "Les lettres et les chiffres sur le bord", OUI_NON, 2),
        Reglage("surbrillance_dernier_coup", "Dernier coup",
                "Surligner les deux cases du coup joue", OUI_NON, 2),
        Reglage("points_coups_possibles", "Coups possibles",
                "Des points sur les cases où la pièce peut aller", OUI_NON, 2),
        Reglage("fleche_cavalier_en_L", "Flèche du cavalier",
                "Au clic droit : en L ou droite",
                [("En L", True), ("Droite", False)], 2),
    ]
    return [
        ("echiquier", "Échiquier", echiquier),
        ("partie", "Partie", [
            Reglage("vitesse_animation", "Déplacement des pièces",
                    "Le temps qu'une pièce met à glisser",
                    [("Rapide", 0.10), ("Normal", 0.18), ("Lent", 0.30),
                     ("Aucun", 0.0)], 4),
            Reglage("duree_retournement", "Retournement du plateau",
                    "Quand le plateau tourne",
                    [("Vif", 0.20), ("Normal", 0.32), ("Pose", 0.50),
                     ("Immédiat", 0.0)], 4),
            Reglage("notation", "Notation des coups",
                    "Les lettres des pièces dans la liste des coups",
                    [("Anglaise (Nf3)", "anglaise"), ("Française (Cf3)", "francaise")], 2),
            Reglage("premouvement", "Pré-mouvement",
                    "Jouer d'avance pendant que l'adversaire reflechit",
                    OUI_NON, 2),
            Reglage("hotseat_retourner_plateau", "Partie à deux",
                    "Tourner le plateau vers le joueur qui doit jouer",
                    OUI_NON, 2),
        ]),
        ("son", "Son", [
            Reglage("volume_sons", "Volume",
                    "Pièces et pendule - clique pour entendre",
                    [("Muet", 0.0), ("25 %", 0.25), ("50 %", 0.5),
                     ("75 %", 0.75), ("100 %", 1.0)], 5),
        ]),
        ("affichage", "Affichage", [
            Reglage("plein_ecran", "Mode d'affichage", "Touche F11 en jeu",
                    [("Fenêtre", False), ("Plein écran", True)], 2),
            Reglage("echelle_interface", "Taille des textes",
                    "Textes et boutons",
                    [("Petite", 0.88), ("Normale", 1.0), ("Grande", 1.15),
                     ("Très grande", 1.30)], 4),
            Reglage("police_livree", "Police",
                    "Celle du jeu, ou celle de Windows",
                    [("SickChess", True), ("Système", False)], 2),
        ]),
    ]


def valeurs_par_defaut():
    defauts = dict(apparence.DEFAUTS)
    defauts.update(DEFAUTS_EN_PLUS)
    return defauts


def enregistrer(valeurs):
    """Ecrit les options dans config.json sans toucher aux autres cles."""
    config = charger_config()
    config.update(valeurs)
    config["sons_actifs"] = float(valeurs.get("volume_sons", 0.6)) > 0
    try:
        with open(_chemin_config(), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("[OPTIONS] options enregistrees")
        return True
    except OSError as e:
        print("[OPTIONS] enregistrement impossible : %s" % e)
        return False


class EcranOptions:
    def __init__(self, screen):
        self.screen = screen
        self.onglets = _onglets()
        self.onglet = 0
        self.defilement = 0
        self._hauteur_liste = 0

        config = charger_config()
        defauts = valeurs_par_defaut()
        self.valeurs = {}
        for _id, _nom, reglages in self.onglets:
            for r in reglages:
                valeur = config.get(r.cle, defauts.get(r.cle))
                if valeur is None:
                    valeur = defauts.get(r.cle)
                self.valeurs[r.cle] = valeur
        self.valeurs["plein_ecran"] = ui.est_plein_ecran()
        self.avant = dict(self.valeurs)

        self.plateau_apercu = chess.Board(POSITION_APERCU)
        self._images = {}
        self._cle_images = None
        self._sons = None

        self.btn_onglets = [ui.Bouton((0, 0, 10, 10), nom, i)
                            for i, (_id, nom, _r) in enumerate(self.onglets)]
        self.btn_defaut = ui.Bouton((0, 0, 10, 10), "Valeurs par défaut", "defaut")
        self.btn_annuler = ui.Bouton((0, 0, 10, 10), "Annuler", "annuler")
        self.btn_ok = ui.Bouton((0, 0, 10, 10), "Enregistrer", "ok")
        self._appliquer_en_direct()
        self._placer()

    # ------------------------------------------------------------- en direct

    def _appliquer_en_direct(self, cle=None):
        """Tout ce qui se voit est applique tout de suite, pour l'apercu ET
        pour l'ecran lui-meme (taille des textes, police, accent)."""
        prefs = apparence.preferences()
        for k, v in self.valeurs.items():
            if k in apparence.DEFAUTS:
                prefs[k] = v
        apparence.appliquer(prefs)
        ui.vider_cache()
        design.vider_le_cache()
        if cle == "plein_ecran" and bool(self.valeurs["plein_ecran"]) != ui.est_plein_ecran():
            self.screen = ui.basculer_plein_ecran()
        if cle in ("plein_ecran", "echelle_interface", "police_livree"):
            self._placer()

    def _remettre_comme_avant(self):
        self.valeurs = dict(self.avant)
        apparence.preferences(recharger=True)
        ui.vider_cache()
        design.vider_le_cache()
        if bool(self.avant["plein_ecran"]) != ui.est_plein_ecran():
            self.screen = ui.basculer_plein_ecran()

    def _faire_entendre(self, volume):
        try:
            if self._sons is None:
                import sounds
                self._sons = sounds.SoundManager(volume)
            self._sons.actif = volume > 0
            self._sons.set_volume(volume)
            self._sons.play("move")
        except Exception as e:
            print("[OPTIONS] essai du son impossible : %s" % e)

    # ------------------------------------------------------------- mise en page

    def _placer(self):
        self.screen = pygame.display.get_surface() or self.screen
        largeur, hauteur = self.screen.get_size()
        ech = self.ech = ui.echelle(self.screen)
        marge = self.marge = int(28 * ech)
        self.y_titre = marge
        haut = marge + ui.police(ui.t(30, ech), True).get_height() + int(18 * ech)
        h_bouton = int(40 * ech)
        bas = hauteur - marge - h_bouton - int(16 * ech)

        # Onglets a gauche
        l_onglets = int(170 * ech)
        y = haut
        for b in self.btn_onglets:
            b.taille = ui.t(16, ech)
            b.placer((marge, y, l_onglets, int(42 * ech)))
            y += int(50 * ech)

        # Apercu a droite
        l_apercu = max(int(230 * ech), min(int(360 * ech), int(largeur * 0.30)))
        # Hauteur ajustee au contenu : echiquier + une ligne + un bouton.
        sq = max(14, (l_apercu - int(28 * ech)) // 8)
        h_contenu = (int(36 * ech) + 8 * sq + int(18 * ech)
                     + ui.police(ui.t(14, ech), True).get_height()
                     + int(10 * ech) + int(36 * ech) + int(16 * ech))
        self.zone_apercu = pygame.Rect(largeur - marge - l_apercu, haut,
                                       l_apercu, min(bas - haut, h_contenu))
        x_liste = marge + l_onglets + int(26 * ech)
        self.zone_liste = pygame.Rect(x_liste, haut,
                                      self.zone_apercu.x - int(26 * ech) - x_liste,
                                      bas - haut)
        self.defilement = min(self.defilement, self._defilement_max())

        # Boutons du bas
        y = hauteur - marge - h_bouton
        l = int(190 * ech)
        for b in (self.btn_defaut, self.btn_annuler, self.btn_ok):
            b.taille = ui.t(15, ech)
        self.btn_defaut.placer((marge, y, l, h_bouton))
        self.btn_ok.placer((largeur - marge - l, y, l, h_bouton))
        self.btn_annuler.placer((largeur - marge - 2 * l - int(12 * ech), y, l,
                                 h_bouton))

    def _defilement_max(self):
        return max(0, self._hauteur_liste - self.zone_liste.height)

    # ------------------------------------------------------------- evenements

    def _boutons(self):
        return self.btn_onglets + [self.btn_defaut, self.btn_annuler, self.btn_ok]

    def handle_event(self, event):
        """Renvoie 'enregistre', 'annule', 'quitter' ou None."""
        if event.type == pygame.QUIT:
            self._remettre_comme_avant()
            return "quitter"
        nouvelle = ui.evenement_fenetre(event)
        if nouvelle is not None:
            self.screen = nouvelle
            self.valeurs["plein_ecran"] = ui.est_plein_ecran()
            self._placer()
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._remettre_comme_avant()
                return "annule"
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._valider()
            if event.key == pygame.K_TAB:
                sens = -1 if event.mod & pygame.KMOD_SHIFT else 1
                self._changer_onglet((self.onglet + sens) % len(self.onglets))
            elif event.key == pygame.K_DOWN:
                self.defilement = min(self._defilement_max(), self.defilement + 40)
            elif event.key == pygame.K_UP:
                self.defilement = max(0, self.defilement - 40)
            return None

        if event.type == pygame.MOUSEWHEEL:
            self.defilement = max(0, min(self._defilement_max(),
                                         self.defilement - event.y * 40))
            return None

        cle = ui.gerer_boutons(self._boutons(), event)
        if isinstance(cle, int) and not isinstance(cle, bool):
            self._changer_onglet(cle)
            return None
        if cle == "ok":
            return self._valider()
        if cle == "annuler":
            self._remettre_comme_avant()
            return "annule"
        if cle == "defaut":
            plein = self.valeurs["plein_ecran"]
            self.valeurs.update({k: v for k, v in valeurs_par_defaut().items()
                                 if k in self.valeurs})
            self.valeurs["plein_ecran"] = plein   # pas de saut d'ecran surprise
            self._appliquer_en_direct("echelle_interface")
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for r in self.onglets[self.onglet][2]:
                for rect, valeur in r.zones:
                    if rect.collidepoint(event.pos) and self.zone_liste.collidepoint(event.pos):
                        self.valeurs[r.cle] = valeur
                        self._appliquer_en_direct(r.cle)
                        if r.cle == "volume_sons":
                            self._faire_entendre(float(valeur))
                        return None
        return None

    def _changer_onglet(self, rang):
        self.onglet = rang
        self.defilement = 0

    def _valider(self):
        a_ecrire = dict(self.valeurs)
        enregistrer(a_ecrire)
        apparence.preferences(recharger=True)
        ui.vider_cache()
        design.vider_le_cache()
        return "enregistre"

    # ------------------------------------------------------------- dessin

    def draw(self):
        ecran = self.screen
        largeur, hauteur = ecran.get_size()
        t = apparence.theme(self.valeurs.get("theme_plateau"))
        ech = self.ech
        design.degrade_vertical(ecran, ecran.get_rect(),
                                design.eclaircir(t["fond"], 0.06),
                                design.assombrir(t["fond"], 0.10))
        ui.texte(ecran, "Options", self.marge,
                 self.y_titre, ui.t(30, ech), t["texte"], gras=True)

        for i, b in enumerate(self.btn_onglets):
            b.selectionne = (i == self.onglet)
            b.dessiner(ecran, t, rayon=int(10 * ech))
        self._dessiner_liste(t)
        self._dessiner_apercu(t)
        for b in (self.btn_defaut, self.btn_annuler, self.btn_ok):
            b.selectionne = (b is self.btn_ok)
            b.dessiner(ecran, t, rayon=int(10 * ech))
        ui.texte(ecran, "Entrée : enregistrer   ·   Échap : annuler   ·   Tab : onglet suivant",
                 largeur // 2, hauteur - int(18 * ech), ui.t(11, ech),
                 t.get("texte_faible", t["texte_discret"]), ancre="centre")

    def _dessiner_liste(self, t):
        ecran = self.screen
        ech = self.ech
        zone = self.zone_liste
        ancien = ecran.get_clip()
        ecran.set_clip(zone)
        y = zone.y - self.defilement
        for r in self.onglets[self.onglet][2]:
            y = self._dessiner_reglage(t, r, y)
            y += int(14 * ech)
        self._hauteur_liste = y + self.defilement - zone.y
        ecran.set_clip(ancien)

        if self._defilement_max() > 0:
            h = max(int(28 * ech), int(zone.height * zone.height / float(self._hauteur_liste)))
            part = self.defilement / float(self._defilement_max())
            barre = pygame.Rect(zone.right - int(4 * ech),
                                zone.y + int((zone.height - h) * part), int(4 * ech), h)
            pygame.draw.rect(ecran, t.get("trait_fort", t["bord"]), barre, border_radius=2)

    def _dessiner_reglage(self, t, r, y):
        ecran = self.screen
        ech = self.ech
        zone = self.zone_liste
        l_utile = zone.width - int(12 * ech)
        h_titre = ui.police(ui.t(15, ech), True).get_height()
        ui.texte(ecran, r.libelle, zone.x, y, ui.t(15, ech), t["texte"], gras=True,
                 largeur_max=l_utile)
        y += h_titre + int(1 * ech)
        h_expl = ui.police(ui.t(12, ech)).get_height()
        ui.texte(ecran, r.explication, zone.x, y, ui.t(12, ech),
                 t.get("texte_faible", t["texte_discret"]), largeur_max=l_utile)
        y += h_expl + int(8 * ech)

        colonnes = max(1, min(r.colonnes, len(r.valeurs)))
        ecart = int(8 * ech)
        h_chip = int(34 * ech)
        l_chip = (l_utile - (colonnes - 1) * ecart) // colonnes
        choisi = r.rang_choisi(self.valeurs.get(r.cle))
        r.zones = []
        for rang, (libelle, valeur) in enumerate(r.valeurs):
            rect = pygame.Rect(zone.x + (rang % colonnes) * (l_chip + ecart),
                               y + (rang // colonnes) * (h_chip + ecart),
                               l_chip, h_chip)
            r.zones.append((rect, valeur))
            if rect.bottom < zone.y or rect.y > zone.bottom:
                continue
            actif = rang == choisi
            survol = rect.collidepoint(pygame.mouse.get_pos())
            design.panneau(ecran, rect, t, rayon=int(7 * ech), ombre=False,
                           actif=actif, survol=survol and not actif)
            decale = 0
            if r.cle == "theme_plateau":
                self._pastille_damier(rect, valeur)
                decale = int(26 * ech)
            elif r.cle == "accent":
                couleur = design.ACCENTS.get(valeur, {}).get("vif", (128, 128, 128))
                pygame.draw.circle(ecran, couleur,
                                   (rect.x + int(16 * ech), rect.centery), int(7 * ech))
                decale = int(24 * ech)
            zone_texte = pygame.Rect(rect.x + decale, rect.y, rect.width - decale,
                                     rect.height)
            ui.texte_centre_dans(ecran, libelle, zone_texte, ui.t(13, ech),
                                 t["accent"] if actif else t["texte"], gras=actif,
                                 marge=int(6 * ech))
        lignes = (len(r.valeurs) + colonnes - 1) // colonnes
        return y + lignes * (h_chip + ecart)

    def _pastille_damier(self, rect, cle):
        couleurs = apparence.theme(cle)
        cote = max(5, int(8 * self.ech))
        x = rect.x + int(8 * self.ech)
        y = rect.centery - cote
        matiere = apparence.damier_texture(couleurs, cote * 8)
        if matiere is not None:
            self.screen.blit(matiere, (x, y), pygame.Rect(0, 0, 2 * cote, 2 * cote))
            return
        for ligne in range(2):
            for col in range(2):
                c = couleurs["clair"] if (ligne + col) % 2 == 0 else couleurs["sombre"]
                pygame.draw.rect(self.screen, c,
                                 pygame.Rect(x + col * cote, y + ligne * cote, cote, cote))

    def _pieces(self, taille):
        cle = (self.valeurs.get("jeu_pieces"), taille)
        if cle != self._cle_images:
            self._images = apparence.charger_jeu(cle[0] or apparence.JEU_PAR_DEFAUT,
                                                 taille)
            self._cle_images = cle
        return self._images

    def _dessiner_apercu(self, t):
        ecran = self.screen
        ech = self.ech
        zone = self.zone_apercu
        design.panneau(ecran, zone, t, rayon=int(12 * ech))
        ui.texte(ecran, "APERÇU", zone.x + int(14 * ech), zone.y + int(12 * ech),
                 ui.t(11, ech), t.get("texte_faible", t["texte_discret"]), gras=True)

        cote_dispo = min(zone.width - int(28 * ech), zone.height - int(140 * ech))
        sq = max(14, cote_dispo // 8)
        x0 = zone.x + (zone.width - 8 * sq) // 2
        y0 = zone.y + int(36 * ech)
        geo.configurer(x0, y0, sq)
        plateau = self.plateau_apercu
        v = self.valeurs

        pygame.draw.rect(ecran, t["bord"], pygame.Rect(x0 - 2, y0 - 2, 8 * sq + 4, 8 * sq + 4), 2)
        voile = pygame.Surface((sq, sq), pygame.SRCALPHA)
        cases_dernier = (chess.E2, chess.E4) if v.get("surbrillance_dernier_coup") else ()
        selection = chess.C4
        matiere = apparence.damier_texture(t, 8 * sq)
        if matiere is not None:
            ecran.blit(matiere, (x0, y0))
        for case in chess.SQUARES:
            x, y = geo.case_vers_pixel(case, sq, False)
            if matiere is None:
                couleur = t["clair"] if geo.case_claire(case) else t["sombre"]
                pygame.draw.rect(ecran, couleur, pygame.Rect(x, y, sq, sq))
            if case in cases_dernier or case == selection:
                voile.fill(t.get("selection" if case == selection else "dernier",
                                 (255, 220, 90, 110)))
                ecran.blit(voile, (x, y))

        if v.get("afficher_coordonnees"):
            taille = max(8, sq // 6)
            for col in range(8):
                case = chess.square(col, 0)
                x, y = geo.case_vers_pixel(case, sq, False)
                c = t["sombre"] if geo.case_claire(case) else t["clair"]
                rendu = ui.police(taille, True).render("abcdefgh"[col], True, c)
                ecran.blit(rendu, (x + sq - rendu.get_width() - 2, y + sq - rendu.get_height() - 1))
            for rang in range(8):
                case = chess.square(0, rang)
                x, y = geo.case_vers_pixel(case, sq, False)
                c = t["sombre"] if geo.case_claire(case) else t["clair"]
                rendu = ui.police(taille, True).render(str(rang + 1), True, c)
                ecran.blit(rendu, (x + 2, y + 1))

        images = self._pieces(sq)
        for case in chess.SQUARES:
            piece = plateau.piece_at(case)
            if piece and piece.symbol() in images:
                image = images[piece.symbol()]
                x, y = geo.case_vers_pixel(case, sq, False)
                ecran.blit(image, (x + (sq - image.get_width()) // 2,
                                   y + (sq - image.get_height()) // 2))

        if v.get("points_coups_possibles"):
            couleur = t.get("coup", (0, 0, 0, 90))
            for coup in plateau.legal_moves:
                if coup.from_square != selection:
                    continue
                x, y = geo.case_vers_pixel(coup.to_square, sq, False)
                pastille = pygame.Surface((sq, sq), pygame.SRCALPHA)
                if plateau.piece_at(coup.to_square):
                    pygame.draw.circle(pastille, couleur, (sq // 2, sq // 2), sq // 2 - 1,
                                       max(2, sq // 10))
                else:
                    pygame.draw.circle(pastille, couleur, (sq // 2, sq // 2), max(3, sq // 7))
                ecran.blit(pastille, (x, y))

        # Sous l'echiquier : un texte et un bouton, pour juger l'accent et la police.
        y = y0 + 8 * sq + int(18 * ech)
        ui.texte(ecran, "Partie rapide · 5 min + 3 s", zone.x + int(16 * ech), y,
                 ui.t(14, ech), t["texte"], gras=True, largeur_max=zone.width - int(32 * ech))
        y += ui.police(ui.t(14, ech), True).get_height() + int(10 * ech)
        bouton = pygame.Rect(zone.x + int(16 * ech), y, zone.width - int(32 * ech), int(36 * ech))
        if bouton.bottom < zone.bottom - int(6 * ech):
            ui.cadre(ecran, bouton, t["accent"], t["accent"], 2, int(9 * ech))
            ui.texte_centre_dans(ecran, "Jouer", bouton, ui.t(15, ech),
                                 design.lisible_sur(t["accent"]), gras=True)

    # ------------------------------------------------------------- boucle

    def run(self, clock=None):
        clock = clock or pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                reponse = self.handle_event(event)
                if reponse:
                    return reponse
            self.draw()
            pygame.display.flip()
            clock.tick(60)
