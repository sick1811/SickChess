# premier_lancement.py - SickChess 17/10 (travail p11, demande de Julien).
#
# 30 secondes au tout premier lancement : ton nom, ton niveau, et les trois
# choses a connaitre (jouer, la revue, les problemes). Moins de joueurs perdus
# = meilleures notes sur Steam. Ne s'affiche qu'une fois (cle
# "premier_lancement_fait" dans config.json), et jamais si un profil a deja
# des parties (comme celui de Julien).

import os

import pygame

import apparence
import ui

NIVEAUX = [
    ("debutant", "Je débute", "Je connais à peine les règles.", 600),
    ("regles", "Je connais les règles", "Je joue de temps en temps.", 1000),
    ("club", "Je joue souvent", "Je connais quelques ouvertures et tactiques.", 1400),
    ("fort", "Je suis fort", "Joueur de club confirmé.", 1800),
]
CARTES = [
    ("Jouer", "Contre l'ordinateur, à ton niveau, ou contre un ami (à deux ou en ligne). "
              "Échap met la partie en pause."),
    ("La revue", "À la fin de chaque partie, l'analyse montre tes meilleurs coups et tes "
                 "fautes, expliquées avec des mots. Tu peux rejouer d'autres coups."),
    ("Progresser", "Problèmes à ton niveau, défis contre la montre, tes propres erreurs "
                   "en exercices et l'entraînement aux ouvertures."),
]


def a_afficher(config, profil):
    """Vrai au tout premier lancement seulement."""
    if (config or {}).get("premier_lancement_fait"):
        return False
    return not getattr(profil, "parties", None)


def nom_par_defaut():
    nom = (os.environ.get("USERNAME") or os.environ.get("USER") or "").strip()
    return nom[:18] or "Joueur"


class EcranPremierLancement:
    def __init__(self, screen, profil):
        self.screen = screen
        self.profil = profil
        self.etape = 1
        self.niveau = "regles"
        self.champ = ui.ChampTexte(18)
        self.champ.contenu = profil.nom if profil.nom and profil.nom != "Joueur" else nom_par_defaut()
        self.champ.activer(True)
        self.btns_niveaux = [ui.Bouton((0, 0, 10, 10), libelle, cle, taille=17)
                             for cle, libelle, _d, _e in NIVEAUX]
        self.btn_suivant = ui.Bouton((0, 0, 10, 10), "Suivant", "suivant", taille=19)
        self.btn_go = ui.Bouton((0, 0, 10, 10), "C'est parti !", "go", taille=20)
        self.btn_passer = ui.Bouton((0, 0, 10, 10), "Passer", "passer", taille=14, gras=False)

    def _placer(self):
        largeur, hauteur = self.screen.get_size()
        ech = ui.echelle(self.screen)
        self.ech = ech
        l = min(int(760 * ech), largeur - 60)
        x = (largeur - l) // 2
        self.colonne = (x, l)
        self.rect_champ = pygame.Rect(x, int(hauteur * 0.30), l, int(46 * ech))
        y = self.rect_champ.bottom + int(56 * ech)
        demi = (l - int(12 * ech)) // 2
        h = int(62 * ech)
        for i, b in enumerate(self.btns_niveaux):
            ligne, col = divmod(i, 2)
            b.placer((x + col * (demi + int(12 * ech)), y + ligne * (h + int(10 * ech)), demi, h))
        bas = hauteur - int(80 * ech)
        self.btn_suivant.placer((x + l - int(220 * ech), bas, int(220 * ech), int(50 * ech)))
        self.btn_go.placer((x + l - int(240 * ech), bas, int(240 * ech), int(50 * ech)))
        self.btn_passer.placer((x, bas + int(8 * ech), int(120 * ech), int(36 * ech)))

    def terminer(self):
        """Ecrit le nom, le niveau et la cle « deja vu »."""
        nom = " ".join(self.champ.contenu.split())[:18]
        if nom:
            self.profil.nom = nom
        elo = next(e for c, _l, _d, e in NIVEAUX if c == self.niveau)
        if not self.profil.parties:
            self.profil.elo = elo
        self.profil.enregistrer()
        try:
            import ecran_options
            ecran_options.enregistrer({"premier_lancement_fait": True, "elo": elo,
                                       "elo_suit_profil": True})
        except Exception as e:
            print("[ACCUEIL] reglages non enregistres : %s" % e)
        self.champ.activer(False)
        return "fini"

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return "quitter"
        self._placer()
        if self.etape == 1:
            reponse = self.champ.handle_event(event)
            if reponse == "valider":
                self.etape = 2
                return None
            cle = ui.gerer_boutons(self.btns_niveaux + [self.btn_suivant, self.btn_passer], event)
        else:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                return self.terminer()
            cle = ui.gerer_boutons([self.btn_go, self.btn_passer], event)
        if cle in [c for c, _l, _d, _e in NIVEAUX]:
            self.niveau = cle
        elif cle == "suivant":
            self.etape = 2
        elif cle in ("go", "passer"):
            return self.terminer()
        return None

    def draw(self):
        self._placer()
        ecran, ech = self.screen, self.ech
        t = apparence.theme()
        ecran.fill(t["fond"])
        largeur, hauteur = ecran.get_size()
        x, l = self.colonne
        souris = pygame.mouse.get_pos()
        ui.texte(ecran, "Bienvenue dans SickChess", largeur // 2, int(hauteur * 0.08),
                 ui.t(38, ech), t["texte"], gras=True, ancre="centre")
        ui.texte(ecran, "Étape %d sur 2" % self.etape, largeur // 2,
                 int(hauteur * 0.08) + ui.t(50, ech), ui.t(14, ech), t["texte_discret"],
                 ancre="centre")
        if self.etape == 1:
            ui.texte(ecran, "Comment t'appelles-tu ?", x, self.rect_champ.y - ui.t(28, ech),
                     ui.t(18, ech), t["texte"], gras=True)
            self.champ.dessiner(ecran, self.rect_champ, t, ui.t(20, ech), "Ton nom")
            ui.texte(ecran, "Ton niveau aux échecs ?", x,
                     self.btns_niveaux[0].rect.y - ui.t(30, ech), ui.t(18, ech), t["texte"],
                     gras=True)
            for b, (cle, _l, detail, _e) in zip(self.btns_niveaux, NIVEAUX):
                b.selectionne = cle == self.niveau
                b.maj_survol(souris)
                b.dessiner(ecran, t)
                ui.texte(ecran, detail, b.rect.centerx, b.rect.bottom - ui.t(18, ech),
                         ui.t(11, ech), t["fond"] if b.selectionne else t["texte_discret"],
                         ancre="centre", largeur_max=b.rect.width - 10)
            self.btn_suivant.selectionne = True
            for b in (self.btn_suivant, self.btn_passer):
                b.maj_survol(souris)
                b.dessiner(ecran, t)
        else:
            ui.texte(ecran, "Trois choses à savoir, %s :" % (self.champ.contenu.strip() or "Joueur"),
                     x, int(hauteur * 0.24), ui.t(20, ech), t["texte"], gras=True,
                     largeur_max=l)
            y = int(hauteur * 0.24) + ui.t(44, ech)
            lc = (l - 2 * int(14 * ech)) // 3
            hc = int(hauteur * 0.42)
            for i, (titre, texte) in enumerate(CARTES):
                r = pygame.Rect(x + i * (lc + int(14 * ech)), y, lc, hc)
                ui.cadre(ecran, r, t["panneau"], t["bord"], 1, 14)
                ui.texte(ecran, "%d" % (i + 1), r.x + int(16 * ech), r.y + int(12 * ech),
                         ui.t(34, ech), t["accent"], gras=True)
                ui.texte(ecran, titre, r.x + int(16 * ech), r.y + int(62 * ech), ui.t(20, ech),
                         t["texte"], gras=True, largeur_max=r.width - int(24 * ech))
                ui.paragraphe(ecran, texte, (r.x + int(16 * ech), r.y + int(96 * ech),
                                             r.width - int(32 * ech), r.height - int(110 * ech)),
                              ui.t(14, ech), t["texte_discret"])
            self.btn_go.selectionne = True
            for b in (self.btn_go, self.btn_passer):
                b.maj_survol(souris)
                b.dessiner(ecran, t)

    def run(self, clock, evenement_fenetre=None):
        while True:
            for event in ui.evenements():
                if evenement_fenetre is not None and evenement_fenetre(event):
                    self.screen = pygame.display.get_surface()
                    continue
                reponse = self.handle_event(event)
                if reponse:
                    return reponse
            self.draw()
            ui.afficher()
            clock.tick(60)
