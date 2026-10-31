# ecran_classements.py - SickChess 24/10 (travail p37) : les classements Steam.
#
# Problemes -> « Classements ». En haut : Problemes / Contre la montre / Survie ;
# en dessous : Mondial / Amis / Autour de moi ; puis la liste (rang, joueur,
# score), ta ligne en or. Sans Steam : pourquoi, et tes scores, qui partiront
# a la prochaine connexion. Les donnees viennent de classements.py.

import pygame

import apparence
import classements
import design
import distribution
import langue
import ui

# 31/10 : version itch.io (jamais de Steam). Le cadre remplace la liste
# mondiale ; les records gardes dans le jeu restent visibles en dessous.
SANS_STEAM_TITRE = "Les classements mondiaux passent par Steam"
SANS_STEAM_TEXTE = ("Cette version de SickChess fonctionne sans Steam. Tes records sont "
                    "gardés dans le jeu :")


class EcranClassements:
    def __init__(self, screen, config=None, steam=None, gestionnaire=None):
        self.screen = screen
        self.config = dict(config or {})
        self.gestion = gestionnaire or classements.instance()
        self.steam = steam or self.gestion.steam()
        self.sans_steam = not distribution.steam_permis()
        if not self.sans_steam and not getattr(self.steam, "actif", False):
            try:
                self.steam.demarrer()
            except Exception as e:
                print("[CLASSEMENTS] Steam : %s" % e)
        self.tableau = "problemes"
        self.vue = "mondial"
        b = ui.Bouton
        self.btns_tableaux = [b((0, 0, 10, 10), titre, "tableau:" + cle, taille=17)
                              for cle, _api, titre, _m in classements.TABLEAUX]
        self.btns_vues = [b((0, 0, 10, 10), titre, "vue:" + cle, taille=15, gras=False)
                          for cle, titre, _d, _a, _z in classements.VUES]
        self.btn_actualiser = b((0, 0, 10, 10), "Actualiser", "actualiser", taille=15, gras=False)
        self.btn_retour = b((0, 0, 10, 10), "Retour", "retour", taille=16)
        self.boutons = self.btns_tableaux + self.btns_vues + [self.btn_actualiser, self.btn_retour]
        if self.sans_steam:
            self.boutons = [self.btn_retour]     # rien a choisir sans Steam
        self._noms = {}
        self._placer()
        self._demander()

    def _demander(self, forcer=False):
        if not self.sans_steam and getattr(self.steam, "actif", False):
            self.gestion.demander(self.tableau, self.vue, forcer)

    # ------------------------------------------------------------- placement

    def _placer(self, screen=None):
        if screen is not None:
            self.screen = screen
        largeur, hauteur = self.screen.get_size()
        ech = self.ech = ui.echelle(self.screen)
        lc = min(int(620 * ech), largeur - 40)
        x = (largeur - lc) // 2
        y = int(hauteur * 0.15)
        ecart = int(8 * ech)
        h = int(44 * ech)
        l3 = (lc - 2 * ecart) // 3
        for i, bouton in enumerate(self.btns_tableaux):
            bouton.placer((x + i * (l3 + ecart), y, l3, h))
        y += h + ecart
        h2 = int(34 * ech)
        for i, bouton in enumerate(self.btns_vues):
            bouton.placer((x + i * (l3 + ecart), y, l3, h2))
        y += h2 + int(14 * ech)
        bas = hauteur - int(24 * ech)
        hb = int(40 * ech)
        self.btn_retour.placer((x + lc - l3, bas - hb, l3, hb))
        self.btn_actualiser.placer((x, bas - hb, l3, hb))
        self.zone = pygame.Rect(x, y, lc, bas - hb - int(14 * ech) - y)
        self.h_ligne = int(34 * ech)

    # ------------------------------------------------------------- evenements

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return "quitter"
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "retour"
            if self.sans_steam:
                return None
            if event.key == pygame.K_r:
                self._demander(forcer=True)
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                cles = [t[0] for t in classements.TABLEAUX]
                i = cles.index(self.tableau) + (1 if event.key == pygame.K_RIGHT else -1)
                self.choisir(cles[i % len(cles)], self.vue)
            return None
        cle = ui.gerer_boutons(self.boutons, event)
        if cle == "retour":
            return "retour"
        if cle == "actualiser":
            self._demander(forcer=True)
        elif cle and cle.startswith("tableau:"):
            self.choisir(cle[8:], self.vue)
        elif cle and cle.startswith("vue:"):
            self.choisir(self.tableau, cle[4:])
        return None

    def choisir(self, tableau, vue):
        self.tableau, self.vue = tableau, vue
        self._demander()

    # ------------------------------------------------------------- dessin

    def _nom(self, joueur):
        """Les noms sont gardes une seconde (un appel a Steam par ligne sinon)."""
        maintenant = pygame.time.get_ticks()
        deja = self._noms.get(joueur)
        if deja is None or (deja[0] == "..." and maintenant - deja[1] > 1000):
            deja = self._noms[joueur] = (self.gestion.nom(joueur), maintenant)
        return deja[0]

    def mes_scores(self):
        """Ce que le jeu garde de toi (meme sans Steam)."""
        import modes_problemes
        import puzzles
        score = puzzles.charger_le_score()
        return {"problemes": int(score.get("classement", puzzles.CLASSEMENT_DEPART)),
                "chrono": modes_problemes.record("chrono"),
                "survie": modes_problemes.record("survie")}

    def _scores_gardes(self):
        """mes_scores() lus une fois par ouverture de l'ecran (31/10 : plus de
        lecture de fichier a chaque image)."""
        if getattr(self, "_scores", None) is None:
            self._scores = self.mes_scores()
        return self._scores

    def draw(self):
        ecran, ech = self.screen, self.ech
        largeur, hauteur = ecran.get_size()
        t = apparence.theme(self.config.get("theme_plateau"))
        cle = (ecran.get_size(), t["fond"])
        if getattr(self, "_fond", (None,))[0] != cle:      # degrade calcule une fois
            fond = pygame.Surface(ecran.get_size())
            design.degrade_vertical(fond, fond.get_rect(), design.eclaircir(t["fond"], 0.06),
                                    design.assombrir(t["fond"], 0.10))
            self._fond = (cle, fond)
        ecran.blit(self._fond[1], (0, 0))
        ui.texte(ecran, "Classements" if self.sans_steam else "Classements Steam", largeur // 2, int(hauteur * 0.04), ui.t(40, ech),
                 t["texte"], gras=True, ancre="centre")
        steam_actif = not self.sans_steam and getattr(self.steam, "actif", False)
        if steam_actif:
            self.gestion.suivre()
        for bouton in self.btns_tableaux:
            bouton.selectionne = bouton.cle == "tableau:" + self.tableau
        for bouton in self.btns_vues:
            bouton.selectionne = bouton.cle == "vue:" + self.vue
        self.btn_actualiser.actif = bool(steam_actif)
        souris = pygame.mouse.get_pos()
        for bouton in self.boutons:
            bouton.maj_survol(souris)
            bouton.dessiner(ecran, t, rayon=10)
        if self.sans_steam:
            self._dessiner_version_sans_steam(ecran, t, ech)
        elif steam_actif:
            ui.cadre(ecran, self.zone, t["panneau"], t["bord"], 1, 12)
            self._dessiner_liste(ecran, t, ech)
        else:
            ui.cadre(ecran, self.zone, t["panneau"], t["bord"], 1, 12)
            self._dessiner_sans_steam(ecran, t, ech)
        import succes
        succes.dessiner_annonce(ecran)

    def _dessiner_liste(self, ecran, t, ech):
        zone = self.zone
        r = self.gestion.resultat(self.tableau, self.vue)
        x = zone.x + int(16 * ech)
        y = zone.y + int(10 * ech)
        petite = ui.t(14, ech)
        if not r["lignes"]:
            if r["etat"] == "attente":
                texte = "Chargement du classement..."
            elif r["etat"] == "erreur":
                texte = "Steam ne répond pas. Réessaie avec « Actualiser »."
            elif self.vue == "amis":
                texte = "Aucun de tes amis Steam n'a encore de score ici."
            else:
                texte = "Personne n'est encore classé ici : sois le premier !"
            ui.paragraphe(ecran, texte, pygame.Rect(x, y + int(8 * ech), zone.width - int(32 * ech),
                                                    zone.height - int(20 * ech)),
                          ui.t(16, ech), t["texte_discret"])
            return
        largeur_rang = int(70 * ech)
        largeur_score = int(110 * ech)
        ui.texte(ecran, "RANG", x, y, ui.t(12, ech), t["texte_discret"], gras=True)
        ui.texte(ecran, "JOUEUR", x + largeur_rang, y, ui.t(12, ech), t["texte_discret"], gras=True)
        ui.texte(ecran, self._titre_du_score(), zone.right - int(16 * ech), y, ui.t(12, ech),
                 t["texte_discret"], gras=True, ancre="droite")
        y += ui.police(ui.t(12, ech), True).get_height() + int(8 * ech)
        visibles = max(1, (zone.bottom - y - int(8 * ech)) // self.h_ligne)
        for ligne in r["lignes"][:visibles]:
            rect = pygame.Rect(zone.x + int(6 * ech), y, zone.width - int(12 * ech),
                               self.h_ligne - int(4 * ech))
            moi = ligne.get("moi")
            if moi:
                ui.cadre(ecran, rect, t["accent"], t["accent"], 1, 8)
            couleur = t["fond"] if moi else t["texte"]
            ty = rect.centery - ui.police(ui.t(16, ech), True).get_height() // 2
            ui.texte(ecran, "%d" % ligne["rang"], x, ty, ui.t(16, ech), couleur, gras=True,
                     largeur_max=largeur_rang - int(8 * ech))
            nom = "Toi" if moi else self._nom(ligne["joueur"])
            ui.texte(ecran, nom, x + largeur_rang, ty, ui.t(16, ech), couleur, gras=moi,
                     largeur_max=zone.width - largeur_rang - largeur_score - int(40 * ech))
            ui.texte(ecran, "%d" % ligne["score"], zone.right - int(16 * ech), ty, ui.t(16, ech),
                     couleur, gras=True, ancre="droite", largeur_max=largeur_score)
            y += self.h_ligne
        if r["etat"] == "erreur":
            ui.texte(ecran, "Steam ne répond plus : liste peut-être ancienne.", x,
                     zone.bottom - ui.police(petite).get_height() - int(6 * ech), petite,
                     t["texte_discret"], largeur_max=zone.width - int(32 * ech))

    def _titre_du_score(self):
        return {"problemes": "CLASSEMENT", "chrono": "TROUVÉS EN 3 MIN",
                "survie": "TROUVÉS"}[self.tableau]

    def _dessiner_sans_steam(self, ecran, t, ech):
        zone = self.zone
        x = zone.x + int(20 * ech)
        l = zone.width - int(40 * ech)
        y = zone.y + int(18 * ech)
        message = getattr(self.steam, "erreur", "") or "Steam n'est pas disponible."
        ui.texte(ecran, message, x, y, ui.t(18, ech), (240, 140, 120), gras=True,
                 largeur_max=l, ajuster=True)
        y += ui.police(ui.t(18, ech), True).get_height() + int(8 * ech)
        conseil = getattr(self.steam, "conseil", "")
        if conseil:
            ui.paragraphe(ecran, conseil, pygame.Rect(x, y, l, int(44 * ech)), ui.t(14, ech),
                          t["texte_discret"])
            y += int(50 * ech)
        ui.paragraphe(ecran, "Les classements Steam ont besoin de Steam ouvert. Tes scores "
                             "sont gardés dans le jeu et partiront à la prochaine connexion :",
                      pygame.Rect(x, y, l, int(64 * ech)), ui.t(15, ech), t["texte"])
        y += int(78 * ech)
        scores = self._scores_gardes()
        for cle, _api, titre, _m in classements.TABLEAUX:
            ui.texte(ecran, titre, x, y, ui.t(16, ech), t["texte_discret"], largeur_max=l // 2)
            ui.texte(ecran, str(scores[cle]), x + l, y, ui.t(16, ech), t["accent"], gras=True,
                     ancre="droite")
            y += int(30 * ech)

    def _dessiner_version_sans_steam(self, ecran, t, ech):
        """31/10 : version itch.io. Cadre bordé d'or (toute la zone, les boutons
        Steam sont caches) : pourquoi, puis tes records."""
        haut = self.btns_tableaux[0].rect.y + int(10 * ech)   # un peu d'air sous le titre
        l = self.zone.width - int(48 * ech)
        # Cadre a la taille de son contenu (plus de grand vide en bas).
        lignes = len(ui.couper_en_lignes(langue.traduire(SANS_STEAM_TEXTE), ui.t(16, ech), l)[:4])
        besoin = (int(22 * ech) + ui.police(ui.t(22, ech), True).get_height() + int(14 * ech)
                  + lignes * int(ui.police(ui.t(16, ech)).get_height() * 1.3) + int(18 * ech)
                  + len(classements.TABLEAUX) * int(36 * ech) + int(14 * ech))
        zone = pygame.Rect(self.zone.x, haut, self.zone.width,
                           max(0, min(besoin, self.zone.bottom - haut)))
        ui.cadre(ecran, zone, t["panneau"], t.get("accent"), 2, 14, ombre=True)
        x = zone.x + int(24 * ech)
        y = zone.y + int(22 * ech)
        ui.texte(ecran, SANS_STEAM_TITRE, zone.centerx, y, ui.t(22, ech), t["accent"],
                 gras=True, ancre="centre", largeur_max=l, ajuster=True)
        y += ui.police(ui.t(22, ech), True).get_height() + int(14 * ech)
        y += ui.paragraphe(ecran, SANS_STEAM_TEXTE, (x, y, l, 0), ui.t(16, ech), t["texte"],
                           max_lignes=4) + int(18 * ech)
        scores = self._scores_gardes()
        for cle, _api, titre, _m in classements.TABLEAUX:
            ui.texte(ecran, titre, x, y, ui.t(18, ech), t["texte_discret"], largeur_max=l // 2)
            ui.texte(ecran, str(scores[cle]), x + l, y, ui.t(18, ech), t["accent"], gras=True,
                     ancre="droite")
            y += int(36 * ech)

    # ------------------------------------------------------------- boucle

    def run(self, clock, evenement_fenetre=None, apres_dessin=None):
        """Renvoie 'retour' ou 'quitter'."""
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
            clock.tick(cadence.suivante(evenements))
