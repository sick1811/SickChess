# ecran_statistiques.py - SickChess 17/10 (travail p05) : l'ecran des
# statistiques de progression. Les calculs sont dans statistiques.py.

import threading

import pygame

import apparence
import statistiques
import ui

VERT = (120, 200, 130)
ROUGE = (232, 118, 108)
NOMS_PHASES = (("ouverture", "Ouverture"), ("milieu", "Milieu de partie"),
               ("finale", "Finale"))


def _pc(valeur, decimales=0):
    return "-" if valeur is None else ("%." + str(decimales) + "f %%") % valeur


class EcranStatistiques:
    def __init__(self, screen, theme_plateau=None, parties=None):
        self.screen = screen
        self.theme_plateau = theme_plateau
        self.stats = None
        self.btn_retour = ui.Bouton((0, 0, 10, 10), "Retour", "retour")
        # 17/10 (p19) : la liste des succes, dans le meme ecran.
        self.btn_succes = ui.Bouton((0, 0, 10, 10), "Succès", "succes")
        self.vue = "stats"
        # Le calcul relit toutes les analyses : en tache de fond.
        self._fil = threading.Thread(target=self._calculer, args=(parties,), daemon=True)
        self._fil.start()

    def _calculer(self, parties):
        try:
            self.stats = statistiques.calculer(parties)
        except Exception as e:
            print("[STATS] calcul impossible : %s" % e)
            self.stats = {"erreur": str(e)}

    def attendre(self, secondes=30):
        self._fil.join(secondes)
        return self.stats

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return "quitter"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "retour"
        cle = ui.gerer_boutons([self.btn_retour, self.btn_succes], event)
        if cle == "retour":
            if self.vue == "succes":
                self.vue = "stats"
                return None
            return "retour"
        if cle == "succes":
            self.vue = "succes" if self.vue == "stats" else "stats"
        return None

    # ------------------------------------------------------------ dessin

    def draw(self):
        self._dessiner()
        import effets
        effets.fondu(self.screen, "statistiques", apparence.theme(self.theme_plateau)["fond"])

    def _dessiner(self):
        ecran = self.screen
        largeur, hauteur = ecran.get_size()
        ech = ui.echelle(ecran)
        t = apparence.theme(self.theme_plateau)
        ecran.fill(t["fond"])
        marge = int(24 * ech)
        ui.texte(ecran, "Succès" if self.vue == "succes" else "Statistiques", marge, marge,
                 ui.t(30, ech), t["texte"], gras=True)
        self.btn_retour.placer((marge, hauteur - marge - int(46 * ech), int(200 * ech),
                                int(46 * ech)))
        import succes
        faits = succes.obtenus()
        self.btn_succes.libelle = ("Statistiques" if self.vue == "succes"
                                   else "Succès  %d / %d" % (len(faits), len(succes.SUCCES)))
        self.btn_succes.placer((largeur - marge - int(240 * ech), hauteur - marge - int(46 * ech),
                                int(240 * ech), int(46 * ech)))
        for b in (self.btn_retour, self.btn_succes):
            b.maj_survol(pygame.mouse.get_pos())
            b.dessiner(ecran, t)
        if self.vue == "succes":
            self._succes(ecran, t, ech, marge, faits)
            return
        s = self.stats
        haut = marge + ui.t(52, ech)
        if s is None:
            ui.texte(ecran, "Calcul en cours...", marge, haut, ui.t(16, ech), t["texte_discret"])
            return
        if s.get("erreur") or not s["bilan"]["parties"]:
            ui.paragraphe(ecran, "Pas encore de statistiques : joue des parties contre "
                          "l'ordinateur (ou importe les tiennes) et ouvre leur revue.",
                          (marge, haut, largeur - 2 * marge, ui.t(60, ech)),
                          ui.t(16, ech), t["texte_discret"])
            return
        b = s["bilan"]

        # --- cartes du haut
        cartes = [
            ("Parties", str(b["parties"]),
             "%d V · %d N · %d D" % (b["victoires"], b["nulles"], b["defaites"])),
            ("Score", _pc(s["score"]), "Blancs %s · Noirs %s" % (_pc(s["score_blanc"]),
                                                                _pc(s["score_noir"]))),
            ("Précision moyenne", _pc(s["precision_moyenne"], 1),
             "%d partie%s analysée%s" % (s["parties_analysees"],
                                        "s" if s["parties_analysees"] > 1 else "",
                                        "s" if s["parties_analysees"] > 1 else "")),
            ("Tendance", self._tendance(s), "10 dernières contre avant"),
        ]
        ecart = int(14 * ech)
        lc = (largeur - 2 * marge - 3 * ecart) // 4
        hc = int(96 * ech)
        for i, (titre, valeur, sous) in enumerate(cartes):
            r = pygame.Rect(marge + i * (lc + ecart), haut, lc, hc)
            ui.cadre(ecran, r, t["panneau"], t["bord"], 1, 12)
            ui.texte(ecran, titre, r.x + int(12 * ech), r.y + int(8 * ech), ui.t(13, ech),
                     t["texte_discret"], largeur_max=r.width - int(20 * ech))
            couleur = t["texte"]
            if titre == "Tendance" and s["precision_avant"] is not None:
                couleur = VERT if s["precision_recente"] >= s["precision_avant"] else ROUGE
            ui.texte(ecran, valeur, r.x + int(12 * ech), r.y + int(28 * ech), ui.t(28, ech),
                     couleur, gras=True, largeur_max=r.width - int(20 * ech), ajuster=True)
            ui.texte(ecran, sous, r.x + int(12 * ech), r.bottom - int(24 * ech),
                     ui.t(12, ech), t["texte_discret"], largeur_max=r.width - int(20 * ech))

        # --- ouvertures (gauche) et fautes / courbe (droite)
        y = haut + hc + int(18 * ech)
        bas = self.btn_retour.rect.y - int(14 * ech)
        lg = (largeur - 2 * marge - ecart) // 2
        gauche = pygame.Rect(marge, y, lg, bas - y)
        droite = pygame.Rect(marge + lg + ecart, y, largeur - 2 * marge - lg - ecart, bas - y)
        self._ouvertures(ecran, t, ech, gauche, s)
        self._fautes(ecran, t, ech, droite, s)

    def _succes(self, ecran, t, ech, marge, faits):
        import succes
        largeur, hauteur = ecran.get_size()
        y0 = marge + ui.t(52, ech)
        colonnes = 2
        ecart = int(12 * ech)
        lc = (largeur - 2 * marge - ecart) // colonnes
        hc = int(54 * ech)
        for i, (cle, _api, titre, description) in enumerate(succes.SUCCES):
            ligne, col = divmod(i, colonnes)
            r = pygame.Rect(marge + col * (lc + ecart), y0 + ligne * (hc + int(8 * ech)), lc, hc)
            if r.bottom > self.btn_retour.rect.y - int(8 * ech):
                break
            obtenu = cle in faits
            ui.cadre(ecran, r, t["panneau"], t["accent"] if obtenu else t["bord"], 2 if obtenu else 1, 10)
            ui.texte(ecran, titre, r.x + int(12 * ech), r.y + int(7 * ech), ui.t(16, ech),
                     t["accent"] if obtenu else t["texte_discret"], gras=True,
                     largeur_max=r.width - int(110 * ech))
            ui.texte(ecran, description, r.x + int(12 * ech), r.y + int(30 * ech), ui.t(12, ech),
                     t["texte"] if obtenu else t["texte_discret"], largeur_max=r.width - int(24 * ech))
            date = faits.get(cle, "")
            if len(date) == 10:
                date = "%s/%s/%s" % (date[8:10], date[5:7], date[0:4])
            ui.texte(ecran, date if obtenu else "à débloquer", r.right - int(12 * ech),
                     r.y + int(9 * ech), ui.t(11, ech), t["texte_discret"], ancre="droite")

    def _tendance(self, s):
        if s["precision_avant"] is None or s["precision_recente"] is None:
            return "-"
        d = s["precision_recente"] - s["precision_avant"]
        return "%+.1f pts" % d

    def _ouvertures(self, ecran, t, ech, zone, s):
        ui.cadre(ecran, zone, t["panneau"], t["bord"], 1, 12)
        x = zone.x + int(14 * ech)
        l = zone.width - int(28 * ech)
        y = zone.y + int(10 * ech)
        ui.texte(ecran, "Tes ouvertures", x, y, ui.t(16, ech), t["texte"], gras=True)
        y += ui.t(28, ech)
        h = ui.t(30, ech)
        for nom, n, score in s["ouvertures"]:
            if y + h > zone.bottom - int(8 * ech):
                break
            ui.texte(ecran, nom, x, y, ui.t(14, ech), t["texte"], largeur_max=int(l * 0.55))
            barre = pygame.Rect(x + int(l * 0.58), y + int(4 * ech), int(l * 0.27), int(12 * ech))
            pygame.draw.rect(ecran, t["bord"], barre, border_radius=4)
            plein = barre.copy()
            plein.width = int(barre.width * (score or 0) / 100.0)
            if plein.width:
                pygame.draw.rect(ecran, t["accent"], plein, border_radius=4)
            ui.texte(ecran, "%d · %s" % (n, _pc(score)), x + l, y, ui.t(12, ech),
                     t["texte_discret"], ancre="droite")
            y += h

    def _fautes(self, ecran, t, ech, zone, s):
        ui.cadre(ecran, zone, t["panneau"], t["bord"], 1, 12)
        x = zone.x + int(14 * ech)
        l = zone.width - int(28 * ech)
        y = zone.y + int(10 * ech)
        ui.texte(ecran, "Tes fautes selon la phase", x, y, ui.t(16, ech), t["texte"], gras=True)
        y += ui.t(24, ech)
        ui.texte(ecran, "imprécisions, erreurs et gaffes pour 100 coups joués", x, y,
                 ui.t(12, ech), t["texte_discret"], largeur_max=l)
        y += ui.t(24, ech)
        valeurs = s["fautes_pour_100"]
        maxi = max([v for v in valeurs.values() if v is not None] + [1.0])
        for cle, nom in NOMS_PHASES:
            v = valeurs.get(cle)
            ui.texte(ecran, nom, x, y, ui.t(14, ech), t["texte"], largeur_max=int(l * 0.35))
            barre = pygame.Rect(x + int(l * 0.38), y + int(4 * ech), int(l * 0.47), int(12 * ech))
            pygame.draw.rect(ecran, t["bord"], barre, border_radius=4)
            if v:
                plein = barre.copy()
                plein.width = max(3, int(barre.width * v / maxi))
                pygame.draw.rect(ecran, ROUGE if v == maxi else t["accent"], plein,
                                 border_radius=4)
            ui.texte(ecran, "-" if v is None else "%.0f" % v, x + l, y, ui.t(13, ech),
                     t["texte_discret"], ancre="droite")
            y += ui.t(30, ech)
        # Courbe de precision
        y += int(6 * ech)
        ui.texte(ecran, "Précision partie après partie", x, y, ui.t(14, ech), t["texte"], gras=True)
        y += ui.t(24, ech)
        rect = pygame.Rect(x, y, l, max(20, zone.bottom - y - int(12 * ech)))
        ui.cadre(ecran, rect, t["fond"], t["bord"], 1, 8)
        valeurs = s["precisions"]
        if len(valeurs) >= 2 and rect.height > 30:
            interieur = rect.inflate(-int(16 * ech), -int(16 * ech))
            points = [(int(interieur.x + interieur.width * i / float(len(valeurs) - 1)),
                       int(interieur.bottom - interieur.height * v / 100.0))
                      for i, v in enumerate(valeurs)]
            pygame.draw.lines(ecran, t["accent"], False, points, max(2, int(2 * ech)))
            for p in points:
                pygame.draw.circle(ecran, t["accent"], p, max(2, int(3 * ech)))
        else:
            ui.texte(ecran, "Il faut au moins deux parties analysées.", rect.x + int(10 * ech),
                     rect.y + int(8 * ech), ui.t(12, ech), t["texte_discret"])

    def run(self, clock, evenement_fenetre=None):
        cadence = ui.Cadence()       # 23/10 : 30 images/s au repos
        while True:
            evenements = pygame.event.get()
            for event in evenements:
                if evenement_fenetre is not None and evenement_fenetre(event):
                    self.screen = pygame.display.get_surface()
                    continue
                reponse = self.handle_event(event)
                if reponse:
                    return reponse
            self.draw()
            pygame.display.flip()
            clock.tick(cadence.suivante(evenements))
