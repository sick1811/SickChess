# settings_screen.py - V6 : NOUVEAU FICHIER
#
# POURQUOI CE FICHIER :
# Le niveau de Stockfish, la duree de la partie et le rythme de l'IA existaient
# deja, mais uniquement dans config.json : il fallait fermer le jeu, ouvrir un
# fichier au Bloc-notes et relancer pour changer quoi que ce soit.
# Cet ecran apparait maintenant entre le menu et la partie, et permet de tout
# regler a la souris avant chaque partie.
#
# Il renvoie un dictionnaire de reglages a game_manager, qui le transmet a
# ChessTimer (duree, increment) et a ModeStockfish (niveau, rythme).
# La case "Retenir ces reglages" reecrit config.json pour que ce soit le choix
# par defaut la prochaine fois.

import json
import os

import pygame

import apparence
import design
import mise_en_page as mep
import ui

# ----------------------------------------------------------------- apparence
FOND = (20, 18, 26)
PANNEAU = (32, 29, 40)
BORDURE = (62, 56, 74)
TITRE = (255, 215, 0)
TEXTE = (234, 230, 224)
DISCRET = (150, 145, 138)
CHIP = (48, 44, 58)
CHIP_SURVOL = (68, 62, 80)
CHIP_ACTIF = (181, 136, 99)
CHIP_ACTIF_TEXTE = (26, 20, 14)
PISTE = (56, 51, 66)
CURSEUR = (240, 217, 181)


def _appliquer_theme():
    """SickChess : les couleurs viennent du theme (Onyx & Or par defaut).

    Ces constantes etaient des couleurs ecrites en dur (titres jaune vif,
    pastilles cuivre, fond violet) : l'ecran ne suivait ni la direction
    artistique ni l'accent choisi dans Options. Elles sont recalculees a
    chaque dessin a partir du theme courant.
    """
    global FOND, PANNEAU, BORDURE, TITRE, TEXTE, DISCRET, CHIP, CHIP_SURVOL
    global CHIP_ACTIF, CHIP_ACTIF_TEXTE, PISTE, CURSEUR
    t = apparence.theme()
    FOND = t["fond"]
    PANNEAU = t["panneau"]
    BORDURE = t.get("trait", t["bord"])
    TITRE = t["texte"]
    TEXTE = t["texte"]
    DISCRET = t["texte_discret"]
    CHIP = t.get("panneau_haut", t["panneau"])
    CHIP_SURVOL = design.eclaircir(CHIP, 0.08)
    CHIP_ACTIF = t["accent"]
    CHIP_ACTIF_TEXTE = t["fond"]
    PISTE = design.eclaircir(t["panneau"], 0.10)
    CURSEUR = design.eclaircir(t["accent"], 0.25)
    return t


class _Bouton:
    """Bouton du bas de l'ecran, dessine comme ceux d'Options (ui.Bouton).
    Meme interface que l'ancien WoodButton : rect, update, handle_event, draw."""

    def __init__(self, libelle, primaire=False):
        self.rect = pygame.Rect(0, 0, 10, 10)
        self.libelle = libelle
        self.primaire = primaire
        self.survol = False

    def update(self, souris):
        self.survol = self.rect.collidepoint(souris)

    def handle_event(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))

    def draw(self, ecran):
        b = ui.Bouton(self.rect, self.libelle, taille=max(14, min(19, self.rect.height // 3)))
        b.survol = self.survol
        b.selectionne = self.primaire
        b.dessiner(ecran, apparence.theme(), rayon=10)

# ----------------------------------------------------------------- valeurs
NIVEAUX = [
    ("Débutant", 400), ("Facile", 800), ("Moyen", 1200), ("Club", 1600),
    ("Fort", 2000), ("Très fort", 2400), ("Maximum", 3000),
]
DUREES = [("1 min", 1), ("3 min", 3), ("5 min", 5), ("10 min", 10),
          ("15 min", 15), ("30 min", 30), ("Sans limite", 0)]
INCREMENTS = [("+0 s", 0), ("+1 s", 1), ("+2 s", 2), ("+3 s", 3),
              ("+5 s", 5), ("+10 s", 10)]
RYTHMES = [
    ("Rapide", "rapide", 200, 1500, 800),
    ("Humain", "humain", 700, 5000, 1500),
    ("Posé", "pose", 1500, 9000, 2500),
]

DESCRIPTIONS = [
    (600, "Laisse des pièces en prise. Pour apprendre les règles."),
    (1000, "Joue des coups corrects mais rate les tactiques."),
    (1400, "Niveau d'un joueur occasionnel régulier."),
    (1800, "Niveau d'un joueur de club. Punit les erreurs."),
    (2200, "Très solide. Il faut un vrai plan pour l'inquiéter."),
    (2600, "Niveau maître. Aucune faute ne pardonne."),
    (3300, "Pleine puissance. Aucun humain ne bat ça."),
]


def _chemin_config():
    """config.json modifiable : a cote du jeu, ou a cote de l'exe si compile."""
    try:
        from asset_manager import dossier_ecriture
        prioritaires = [os.path.join(dossier_ecriture(), "config.json")]
    except Exception:
        prioritaires = []
    for chemin in prioritaires:
        if os.path.exists(chemin):
            return chemin
    for dossier in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        chemin = os.path.join(dossier, "config.json")
        if os.path.exists(chemin):
            return chemin
    return prioritaires[0] if prioritaires else os.path.join(os.getcwd(), "config.json")


def charger_config():
    """Les reglages du disque. TOUJOURS un dictionnaire.

    JOURNEE DEBUG DU 04/09 : un config.json contenant "null" ou "[]" - ce que
    donne une ecriture coupee en plein milieu, une coupure de courant ou un
    disque plein - passait le json.load() sans erreur et rendait None ou une
    liste. Tous les appelants font config.get(...) : le jeu ne demarrait plus
    du tout, avec un AttributeError incomprehensible. Un fichier qui n'est pas
    un dictionnaire vaut maintenant un fichier absent.
    """
    try:
        with open(_chemin_config(), "r", encoding="utf-8") as f:
            config = json.load(f)
    except (OSError, ValueError):
        return {}
    if not isinstance(config, dict):
        print("[REGLAGES] config.json n'est pas un dictionnaire (%s), "
              "on repart des reglages par defaut" % type(config).__name__)
        return {}
    return config


def enregistrer_config(reglages):
    """Ecrit les nouveaux reglages dans config.json sans perdre le reste."""
    config = charger_config()
    config["elo"] = reglages["elo"]
    config["elo_suit_profil"] = bool(reglages.get("elo_suit_profil", False))
    config["minutes"] = reglages["minutes"] if reglages["minutes"] else None
    config["pendule_active"] = reglages["pendule_active"]
    config["increment_secondes"] = reglages["increment"]
    config["ia_temps_min_ms"] = reglages["ia_temps_min_ms"]
    config["ia_temps_max_ms"] = reglages["ia_temps_max_ms"]
    config["ia_temps_moteur_max_ms"] = reglages["ia_temps_moteur_max_ms"]
    config["ia_temps_humain"] = reglages["ia_temps_humain"]
    config["hotseat_retourner_plateau"] = reglages.get("retourner_plateau", False)
    try:
        with open(_chemin_config(), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("[REGLAGES] config.json mis a jour")
        return True
    except OSError as e:
        print("[REGLAGES] Enregistrement impossible : %s" % e)
        return False


class Chip:
    """Petit bouton rectangulaire a selectionner.

    V7.1 : le libelle est mesure et retreci pour tenir dans la pastille. Avant,
    "Il tourne a chaque coup" debordait des que la fenetre etait etroite.
    """

    def __init__(self, x, y, largeur, hauteur, libelle, valeur, police=None):
        self.rect = pygame.Rect(x, y, largeur, hauteur)
        self.libelle = libelle
        self.valeur = valeur
        self.police = police
        self.actif = False
        self.survole = False

    def placer(self, rect):
        self.rect = pygame.Rect(rect)
        return self

    def update(self, souris):
        self.survole = self.rect.collidepoint(souris)

    def clique(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, ecran):
        if self.actif:
            fond, couleur = CHIP_ACTIF, CHIP_ACTIF_TEXTE
        elif self.survole:
            fond, couleur = CHIP_SURVOL, TEXTE
        else:
            fond, couleur = CHIP, DISCRET
        ui.cadre(ecran, self.rect, fond, None if self.actif else BORDURE, 1, 8)
        taille = max(11, min(17, int(self.rect.height * 0.42)))
        ui.texte_centre_dans(ecran, self.libelle, self.rect, taille, couleur,
                             gras=True, marge=6)


class Slider:
    """Reglage fin de l'Elo, a la souris ou aux fleches."""

    def __init__(self, x, y, largeur, mini, maxi, pas, valeur):
        self.rect = pygame.Rect(x, y, largeur, 26)
        self.mini, self.maxi, self.pas = mini, maxi, pas
        self.valeur = valeur
        self.attrape = False

    def placer(self, rect):
        self.rect = pygame.Rect(rect)
        return self

    def _position_curseur(self):
        part = (self.valeur - self.mini) / float(self.maxi - self.mini)
        return int(self.rect.x + part * self.rect.width)

    def set_depuis_x(self, x):
        part = (x - self.rect.x) / float(max(1, self.rect.width))
        part = max(0.0, min(1.0, part))
        brute = self.mini + part * (self.maxi - self.mini)
        self.valeur = int(round(brute / self.pas) * self.pas)
        self.valeur = max(self.mini, min(self.maxi, self.valeur))

    def handle_event(self, event):
        zone = self.rect.inflate(20, 26)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if zone.collidepoint(event.pos):
                self.attrape = True
                self.set_depuis_x(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.attrape = False
        elif event.type == pygame.MOUSEMOTION and self.attrape:
            self.set_depuis_x(event.pos[0])
            return True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.valeur = max(self.mini, self.valeur - self.pas)
                return True
            if event.key == pygame.K_RIGHT:
                self.valeur = min(self.maxi, self.valeur + self.pas)
                return True
        return False

    def draw(self, ecran):
        rayon = max(7, self.rect.height // 2 - 2)
        piste = pygame.Rect(self.rect.x, self.rect.centery - 4, self.rect.width, 8)
        pygame.draw.rect(ecran, PISTE, piste, border_radius=4)
        x = self._position_curseur()
        remplie = pygame.Rect(self.rect.x, piste.y, max(0, x - self.rect.x), 8)
        pygame.draw.rect(ecran, CHIP_ACTIF, remplie, border_radius=4)
        pygame.draw.circle(ecran, CURSEUR, (x, self.rect.centery), rayon)
        pygame.draw.circle(ecran, (90, 78, 60), (x, self.rect.centery), rayon, 2)


class SettingsScreen:
    """Ecran de reglages affiche avant chaque partie.

    V7.1 - DISPOSITION ENTIEREMENT RECALCULEE :
      L'ecran etait dessine a des coordonnees fixes prevues pour 1280x720 (la
      colonne de droite commencait a x=672 et faisait 582 de large : il fallait
      1254 pixels rien que pour elle). En 1024x640, la moitie de l'ecran sortait
      de la fenetre et les textes se chevauchaient.
      Ici, deux colonnes calculees a partir de la fenetre, des pastilles qui se
      repartissent toutes seules sur autant de lignes que necessaire, et chaque
      panneau qui reserve sa hauteur avant que le suivant ne commence.
      F11 et le redimensionnement fonctionnent aussi sur cet ecran.
    """

    def __init__(self, screen, mode="stockfish"):
        self.screen = screen
        self.largeur, self.hauteur = screen.get_size()
        self.mode = mode                    # stockfish | hotseat | online
        self.afficher_niveau = (mode == "stockfish")

        # Polices conservees pour compatibilite ; l'affichage passe par ui.py.

        config = charger_config()
        # V7.1 (ta demande) : par defaut, Stockfish joue AU NIVEAU DE TON
        # CLASSEMENT. Le classement du profil monte et descend apres chaque
        # partie, donc l'adversaire se recale tout seul. Decoche la case du
        # panneau NIVEAU pour choisir un Elo fixe.
        self.suivre_profil = bool(config.get("elo_suit_profil", True))
        self.elo_profil = self._elo_du_profil()
        self.elo = self.elo_profil if self.suivre_profil \
            else int(config.get("elo", 1500))
        minutes = config.get("minutes")
        if minutes is None:
            presets = {1: 1, 2: 5, 3: 10, 4: 15}
            minutes = presets.get(config.get("preset_pendule", 2), 5)
        self.minutes = 0 if not config.get("pendule_active", True) else int(minutes)
        self.increment = int(config.get("increment_secondes", 0))
        self.rythme = self._rythme_depuis_config(config)
        self.retourner_plateau = bool(config.get("hotseat_retourner_plateau", True))
        self.charger_position = False
        self.retenir = False

        self.running = True
        self.resultat = None

        self._construire()

    # ------------------------------------------------------------------ mise en place

    @staticmethod
    def _elo_du_profil(defaut=1200):
        """Classement estime du joueur, borne aux valeurs acceptees par le jeu."""
        try:
            from profil import get_profil
            valeur = int(get_profil().elo)
        except Exception:
            valeur = defaut
        return max(100, min(3200, valeur))

    def _rythme_depuis_config(self, config):
        if not config.get("ia_temps_humain", True):
            return "rapide"
        maxi = int(config.get("ia_temps_max_ms", 5000))
        proche = min(RYTHMES, key=lambda r: abs(r[3] - maxi))
        return proche[1]

    def _construire(self):
        """Cree les elements une fois ; _placer() les positionne."""
        self.chips_niveau = [Chip(0, 0, 10, 10, libelle, valeur)
                             for libelle, valeur in NIVEAUX]
        self.chips_duree = [Chip(0, 0, 10, 10, libelle, valeur)
                            for libelle, valeur in DUREES]
        self.chips_increment = [Chip(0, 0, 10, 10, libelle, valeur)
                                for libelle, valeur in INCREMENTS]
        self.chips_rythme = [Chip(0, 0, 10, 10, libelle, cle)
                             for libelle, cle, _, _, _ in RYTHMES]
        self.chips_plateau = [Chip(0, 0, 10, 10, "Plateau fixe", False),
                              Chip(0, 0, 10, 10, "Il tourne à chaque coup", True)]
        self.slider = Slider(0, 0, 100, 100, 3200, 25, self.elo)
        self.btn_commencer = _Bouton("Commencer la partie", primaire=True)
        self.btn_retour = _Bouton("Retour au menu")
        self.case_retenir = pygame.Rect(0, 0, 22, 22)
        self.case_profil = pygame.Rect(0, 0, 22, 22)
        self.zone_retenir = pygame.Rect(0, 0, 0, 0)
        self.zone_profil = pygame.Rect(0, 0, 0, 0)
        self._placer()
        self._synchroniser_chips()

    # -------------------------------------------------- placement

    _grille = staticmethod(ui.grille)

    def _placer(self):
        self.largeur, self.hauteur = self.screen.get_size()
        ech = ui.echelle(self.screen)
        self.ech = ech
        # V7.2 : TOUT PASSE PAR LA GRILLE (mise_en_page.py). Voir ce fichier
        # pour les trois defauts mesures : le quart de fenetre vide, les deux
        # alignements de la bande du bas, et les soixante espacements melanges.
        marge = mep.l(ech)

        # --- bandeau du titre : le titre ET le rappel des touches sur la MEME
        # ligne. Avant, le rappel etait dessous : trois lignes pour deux mots.
        self.h_titre = ui.police(ui.t(30, ech), True).get_height()
        self.y_titre = marge
        haut = self.y_titre + self.h_titre + mep.m(ech)

        # --- bandeau du bas : cases A GAUCHE, boutons A DROITE, meme ligne de
        # base, un seul bord de reference des deux cotes.
        zone_cases, zone_boutons, y_haut_bande = mep.bande_du_bas(
            self.largeur, self.hauteur, ech)
        h_bouton = zone_boutons.height
        y_boutons = zone_boutons.y
        ecart_bouton = mep.m(ech)
        largeur_bouton = (zone_boutons.width - ecart_bouton) // 2
        self.btn_commencer.rect = pygame.Rect(zone_boutons.x, y_boutons,
                                              largeur_bouton, h_bouton)
        self.btn_retour.rect = pygame.Rect(
            zone_boutons.x + largeur_bouton + ecart_bouton, y_boutons,
            largeur_bouton, h_bouton)

        # --- les cases a cocher.
        # SUR LA MEME LIGNE QUE LES BOUTONS quand elles tiennent, SUR LA LIGNE
        # AU-DESSUS sinon. Le libelle "Partir d'une position chargee (FEN ou
        # PGN)" fait 300 pixels : sur une fenetre de 1024, les deux cases plus
        # les deux boutons ne tiennent pas cote a cote. Dans les deux cas elles
        # partent du MEME bord que tout le reste.
        h_case = mep.pas(2.5, ech)
        taille_case_texte = ui.t(15, ech)
        besoin = (h_case + 12
                  + ui.mesurer("Retenir ces réglages", taille_case_texte)[0]
                  + mep.xl(ech) + h_case + 12
                  + ui.mesurer("Partir d'une position chargée (FEN ou PGN)",
                               taille_case_texte)[0])
        self.cases_sur_la_ligne = besoin <= zone_cases.width
        if self.cases_sur_la_ligne:
            y_cases = y_boutons + (h_bouton - h_case) // 2
            droite_cases = zone_cases.right
        else:
            y_cases = y_boutons - mep.m(ech) - h_case
            droite_cases = self.largeur - marge
            y_haut_bande = y_cases - mep.m(ech)
        self.case_retenir = pygame.Rect(marge, y_cases, h_case, h_case)
        largeur_libelle = ui.mesurer("Retenir ces réglages", taille_case_texte)[0]
        self.zone_retenir = pygame.Rect(self.case_retenir.x, y_cases - 4,
                                        h_case + 12 + largeur_libelle, h_case + 8)
        libelle_position = "Partir d'une position chargée (FEN ou PGN)"
        largeur_position = ui.mesurer(libelle_position, taille_case_texte)[0]
        x_position = min(droite_cases - h_case - 12 - largeur_position,
                         self.zone_retenir.right + mep.xl(ech))
        x_position = max(x_position, self.zone_retenir.right + mep.m(ech))
        self.taille_case_texte = taille_case_texte

        # --- deux colonnes entre les deux bandeaux.
        # 40/60 : a gauche un paragraphe ou un niveau, a droite douze pastilles
        # de cadence. Les couper en deux parts egales laissait un cote vide et
        # l'autre serre.
        bas = y_haut_bande - mep.m(ech)
        zone_colonnes = pygame.Rect(marge, haut, self.largeur - 2 * marge,
                                    max(1, bas - haut))
        parts = (2, 3) if self.mode == "online" else (1, 1)
        col_g, col_d = mep.colonnes(zone_colonnes, parts, ech)
        colonne = col_g.width
        self.colonne_droite_l = col_d.width
        gauche = ui.Pile(col_g.x, haut, col_g.width, bas - haut,
                         espace=mep.m(ech))
        droite = ui.Pile(col_d.x, haut, col_d.width, bas - haut,
                         espace=mep.m(ech))

        h_chip = int(38 * ech)
        ecart = int(8 * ech)
        h_section = ui.police(ui.t(17, ech), True).get_height() + int(8 * ech)
        h_ligne = ui.police(ui.t(16, ech)).get_height() + int(4 * ech)
        interieur = colonne - 2 * mep.m(ech)
        interieur_d = self.colonne_droite_l - 2 * mep.m(ech)
        x_int_g = col_g.x + mep.m(ech)
        x_int_d = col_d.x + mep.m(ech)

        # ---- colonne gauche
        if self.afficher_niveau:
            lignes_niveau = self._grille(self.chips_niveau, 0, 0, interieur,
                                         h_chip, ecart, int(112 * ech))
            h_case_profil = int(22 * ech) + int(10 * ech)
            hauteur_panneau = (h_section + lignes_niveau + int(10 * ech)
                               + int(40 * ech) + int(30 * ech) + h_ligne * 2
                               + h_case_profil + int(16 * ech))
            self.panneau_niveau = gauche.bloc(hauteur_panneau)
            if self.panneau_niveau is not None:
                y = self.panneau_niveau.y + int(10 * ech)
                self.titre_niveau = (x_int_g, y)
                y += h_section
                self._grille(self.chips_niveau, x_int_g, y, interieur, h_chip,
                             ecart, int(112 * ech))
                y += lignes_niveau + int(10 * ech)
                self.pos_elo = (x_int_g, y)
                y += int(40 * ech)
                self.slider.placer((x_int_g, y, interieur, int(26 * ech)))
                y += int(30 * ech)
                self.pos_description = pygame.Rect(x_int_g, y, interieur, h_ligne * 2)
                y += h_ligne * 2 + int(6 * ech)
                self.case_profil = pygame.Rect(x_int_g, y, int(22 * ech),
                                               int(22 * ech))

            lignes_rythme = self._grille(self.chips_rythme, 0, 0, interieur,
                                         h_chip, ecart, int(120 * ech))
            self.panneau_rythme = gauche.bloc(h_section + lignes_rythme
                                              + int(20 * ech))
            if self.panneau_rythme is not None:
                y = self.panneau_rythme.y + int(10 * ech)
                self.titre_rythme = (x_int_g, y)
                self._grille(self.chips_rythme, x_int_g, y + h_section, interieur,
                             h_chip, ecart, int(120 * ech))
        else:
            self.panneau_niveau = gauche.bloc(min(gauche.reste(), int(250 * ech)))
            self.panneau_rythme = None
            if self.mode == "hotseat" and self.panneau_niveau is not None:
                y = self.panneau_niveau.y + int(10 * ech) + h_section + h_ligne * 2
                self._grille(self.chips_plateau, x_int_g, y, interieur,
                             int(42 * ech), ecart, int(140 * ech))
                self.pos_info_hotseat = pygame.Rect(
                    x_int_g, y + int(42 * ech) + int(12 * ech), interieur, h_ligne * 2)

        # ---- colonne droite
        lignes_duree = self._grille(self.chips_duree, 0, 0, interieur_d, h_chip,
                                    ecart, int(104 * ech))
        lignes_inc = self._grille(self.chips_increment, 0, 0, interieur_d,
                                  int(34 * ech), ecart, int(74 * ech))
        hauteur_droite = (h_section + lignes_duree + int(14 * ech) + h_ligne
                          + lignes_inc + int(14 * ech) + h_ligne * 2 + int(16 * ech))
        self.panneau_temps = droite.bloc(min(hauteur_droite, droite.reste()))
        if self.panneau_temps is not None:
            y = self.panneau_temps.y + int(10 * ech)
            self.titre_temps = (x_int_d, y)
            y += h_section
            self._grille(self.chips_duree, x_int_d, y, interieur_d, h_chip,
                         ecart, int(104 * ech))
            y += lignes_duree + int(14 * ech)
            self.pos_libelle_increment = (x_int_d, y)
            y += h_ligne
            self._grille(self.chips_increment, x_int_d, y, interieur_d,
                         int(34 * ech), ecart, int(74 * ech))
            y += lignes_inc + int(14 * ech)
            self.pos_resume_temps = pygame.Rect(x_int_d, y, interieur_d,
                                                h_ligne * 2)

        # LE CORRECTIF DU QUART DE FENETRE VIDE : le dernier panneau de chaque
        # colonne s'etire jusqu'a la bande du bas au lieu de flotter en haut.
        mep.etirer([self.panneau_niveau, self.panneau_rythme], bas)
        mep.etirer([self.panneau_temps], bas)

        self.x_int_g, self.x_int_d, self.interieur = x_int_g, x_int_d, interieur
        self.interieur_d = interieur_d
        self.h_ligne = h_ligne
        self.h_section = h_section

    def _synchroniser_chips(self):
        for chip in self.chips_niveau:
            chip.actif = (chip.valeur == self.elo)
        for chip in self.chips_duree:
            chip.actif = (chip.valeur == self.minutes)
        for chip in self.chips_increment:
            chip.actif = (chip.valeur == self.increment)
        for chip in self.chips_rythme:
            chip.actif = (chip.valeur == self.rythme)
        for chip in self.chips_plateau:
            chip.actif = (chip.valeur == self.retourner_plateau)
        self.slider.valeur = self.elo

    # ------------------------------------------------------------------ resultat

    def reglages(self):
        rythme = next((r for r in RYTHMES if r[1] == self.rythme), RYTHMES[1])
        return {
            "elo": self.elo,
            "minutes": self.minutes,                 # 0 = sans limite
            "pendule_active": self.minutes > 0,
            "increment": self.increment,
            "rythme": self.rythme,
            "ia_temps_min_ms": rythme[2],
            "ia_temps_max_ms": rythme[3],
            "ia_temps_moteur_max_ms": rythme[4],
            "ia_temps_humain": self.rythme != "rapide",
            "retourner_plateau": self.retourner_plateau,
            "charger_position": self.charger_position,
            "elo_suit_profil": self.suivre_profil,
        }

    def _description(self):
        for seuil, texte in DESCRIPTIONS:
            if self.elo < seuil:
                return texte
        return DESCRIPTIONS[-1][1]

    # ------------------------------------------------------------------ evenements

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            self.resultat = "quitter"
            return

        nouvelle = ui.evenement_fenetre(event)
        if nouvelle is not None:
            self.screen = nouvelle
            self._placer()
            return

        souris = pygame.mouse.get_pos()
        for chip in self._toutes_les_chips():
            chip.update(souris)
        self.btn_commencer.update(souris)
        self.btn_retour.update(souris)

        if self.afficher_niveau and self.slider.handle_event(event):
            self.elo = self.slider.valeur
            self.suivre_profil = False      # choix manuel : on ne suit plus le profil
            self._synchroniser_chips()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.retenir:
                    enregistrer_config(self.reglages())
                self.resultat = self.reglages()
                self.running = False
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.afficher_niveau:
                if self.zone_profil.collidepoint(event.pos):
                    self.suivre_profil = not self.suivre_profil
                    if self.suivre_profil:
                        self.elo_profil = self._elo_du_profil()
                        self.elo = self.elo_profil
                    self._synchroniser_chips()
                    return
                for chip in self.chips_niveau:
                    if chip.clique(event.pos):
                        self.elo = chip.valeur
                        self.suivre_profil = False
                        self._synchroniser_chips()
                        return
                for chip in self.chips_rythme:
                    if chip.clique(event.pos):
                        self.rythme = chip.valeur
                        self._synchroniser_chips()
                        return
            if self.mode == "hotseat":
                for chip in self.chips_plateau:
                    if chip.clique(event.pos):
                        self.retourner_plateau = chip.valeur
                        self._synchroniser_chips()
                        return
            for chip in self.chips_duree:
                if chip.clique(event.pos):
                    self.minutes = chip.valeur
                    self._synchroniser_chips()
                    return
            for chip in self.chips_increment:
                if chip.clique(event.pos):
                    self.increment = chip.valeur
                    self._synchroniser_chips()
                    return
            if self.zone_retenir.collidepoint(event.pos):
                self.retenir = not self.retenir
                return
            if self.btn_commencer.handle_event(event):
                if self.retenir:
                    enregistrer_config(self.reglages())
                self.resultat = self.reglages()
                self.running = False
                return
            if self.btn_retour.handle_event(event):
                self.running = False
                return

    def _toutes_les_chips(self):
        chips = list(self.chips_duree) + list(self.chips_increment)
        if self.afficher_niveau:
            chips += list(self.chips_niveau) + list(self.chips_rythme)
        if self.mode == "hotseat":
            chips += list(self.chips_plateau)
        return chips

    # ------------------------------------------------------------------ dessin

    def _panneau(self, rect, titre, position_titre):
        if rect is None:
            return
        ui.cadre(self.screen, rect, PANNEAU, BORDURE, 1, 12)
        if titre:
            ui.texte(self.screen, titre, position_titre[0], position_titre[1],
                     ui.t(17, self.ech), TITRE, gras=True,
                     largeur_max=rect.width - 2 * (position_titre[0] - rect.x))

    def _case_a_cocher(self, case, cochee, libelle):
        ui.cadre(self.screen, case, CHIP_ACTIF if cochee else CHIP, BORDURE, 1, 5)
        if cochee:
            pygame.draw.lines(self.screen, CHIP_ACTIF_TEXTE, False, [
                (case.x + case.width * 0.22, case.centery),
                (case.x + case.width * 0.44, case.bottom - case.height * 0.28),
                (case.right - case.width * 0.20, case.y + case.height * 0.26)], 2)
        ui.texte(self.screen, libelle, case.right + 10,
                 case.centery - self.taille_case_texte // 2 - 1,
                 self.taille_case_texte, TEXTE if cochee else DISCRET,
                 largeur_max=self.largeur - case.right - 20)

    def draw(self):
        t = _appliquer_theme()
        design.degrade_vertical(self.screen, self.screen.get_rect(),
                                design.eclaircir(t["fond"], 0.06),
                                design.assombrir(t["fond"], 0.10))
        ech = self.ech

        titres = {"stockfish": "Partie contre l'ordinateur",
                  "hotseat": "Partie à deux sur ce PC",
                  "online": "Partie en ligne"}
        # V7.2 : titre A GAUCHE, rappel des touches A DROITE, sur la MEME
        # ligne. Avant, le rappel occupait une ligne a lui tout seul sous le
        # titre : trois lignes de haut pour deux mots.
        marge = mep.l(ech)
        rappel = ("Entrée : commencer   -   Échap : menu   -   F11 : plein écran")
        largeur_rappel = ui.mesurer(rappel, ui.t(13, ech))[0]
        ui.texte(self.screen, titres.get(self.mode, "REGLAGES"), marge,
                 self.y_titre, ui.t(30, ech), TITRE, gras=True,
                 largeur_max=max(80, self.largeur - 2 * marge - largeur_rappel
                                 - mep.xl(ech)))
        ui.texte(self.screen, rappel, self.largeur - marge,
                 self.y_titre + (self.h_titre
                                 - ui.police(ui.t(13, ech)).get_height()) // 2,
                 ui.t(13, ech), DISCRET, ancre="droite",
                 largeur_max=largeur_rappel + 4)

        # ---- colonne de gauche
        if self.afficher_niveau:
            self._panneau(self.panneau_niveau, "NIVEAU DE L'ORDINATEUR",
                          getattr(self, "titre_niveau", (0, 0)))
            if self.panneau_niveau is not None:
                for chip in self.chips_niveau:
                    chip.draw(self.screen)
                ui.texte(self.screen, "%d Elo" % self.elo, self.pos_elo[0],
                         self.pos_elo[1], ui.t(34, ech), TEXTE, gras=True, mono=True,
                         largeur_max=self.interieur)
                self.slider.draw(self.screen)
                ui.paragraphe(self.screen, self._description(), self.pos_description,
                              ui.t(15, ech), DISCRET)
                theme_case = {"accent": CHIP_ACTIF, "panneau": CHIP, "bord": BORDURE,
                              "fond": CHIP_ACTIF_TEXTE, "texte": TEXTE,
                              "texte_discret": DISCRET}
                self.zone_profil = ui.case_a_cocher(
                    self.screen, self.case_profil, self.suivre_profil,
                    "Se caler sur mon classement (%d Elo)" % self.elo_profil,
                    theme_case, ui.t(15, ech), self.interieur)
            self._panneau(self.panneau_rythme, "RYTHME DE L'ORDINATEUR",
                          getattr(self, "titre_rythme", (0, 0)))
            if self.panneau_rythme is not None:
                for chip in self.chips_rythme:
                    chip.draw(self.screen)
        else:
            titre = "PARTIE À DEUX SUR CE PC" if self.mode == "hotseat" \
                else "PARTIE EN RESEAU"
            self._panneau(self.panneau_niveau, titre,
                          (self.x_int_g, (self.panneau_niveau.y + int(10 * ech))
                           if self.panneau_niveau else 0))
            if self.panneau_niveau is not None:
                zone = pygame.Rect(self.x_int_g,
                                   self.panneau_niveau.y + int(10 * ech) + self.h_section,
                                   self.interieur, self.h_ligne * 2)
                if self.mode == "hotseat":
                    ui.paragraphe(self.screen, "Deux joueurs sur le même ordinateur, "
                                               "chacun à son tour.", zone,
                                  ui.t(15, ech), DISCRET)
                    for chip in self.chips_plateau:
                        chip.draw(self.screen)
                    info = ("Le joueur au trait a toujours ses pièces en bas."
                            if self.retourner_plateau
                            else "Les Blancs restent en bas toute la partie.")
                    ui.paragraphe(self.screen, info, self.pos_info_hotseat,
                                  ui.t(15, ech), TEXTE)
                else:
                    zone = pygame.Rect(zone.x, zone.y, zone.width,
                                       self.panneau_niveau.bottom - zone.y - int(10 * ech))
                    # V7.2 : cet ecran n'est PLUS OUVERT en mode en ligne - le
                    # jeu va directement au salon (ton accord du 31/08). Le
                    # panneau reste en place, et son texte a ete corrige : il
                    # decrivait encore le reseau local de la V7.1, et affirmait
                    # que la cadence n'etait remplacee que "si tu rejoins",
                    # alors qu'elle l'etait dans tous les cas.
                    ui.paragraphe(self.screen,
                                  "Tout se règle maintenant DANS LE SALON, une fois que "
                                  "ton adversaire est arrive : la cadence, compétitive "
                                  "ou amicale, et les couleurs. Rien de ce qui est "
                                  "choisi ici n'est utilise pour une partie en ligne.",
                                  zone, ui.t(15, ech), DISCRET)

        # ---- colonne de droite
        self._panneau(self.panneau_temps, "DURÉE DE LA PARTIE",
                      getattr(self, "titre_temps", (0, 0)))
        if self.panneau_temps is not None:
            for chip in self.chips_duree:
                chip.draw(self.screen)
            ui.texte(self.screen, "Secondes ajoutées à chaque coup :",
                     self.pos_libelle_increment[0], self.pos_libelle_increment[1],
                     ui.t(15, ech), DISCRET, largeur_max=self.interieur)
            for chip in self.chips_increment:
                chip.draw(self.screen)
            if self.minutes == 0:
                info = "Aucune limite de temps : la pendule est désactivée."
            else:
                info = "%d minute%s par joueur, +%d s par coup." % (self.minutes, "s" if self.minutes > 1 else "",
                                                                  self.increment)
            ui.paragraphe(self.screen, info, self.pos_resume_temps,
                          ui.t(15, ech), TEXTE)

        # ---- cases a cocher et boutons
        self._case_a_cocher(self.case_retenir, self.retenir, "Retenir ces réglages")
        # SickChess : "Partir d'une position chargee" n'est plus branche (le
        # chargement de position reviendra avec son ecran) : case cachee.
        self.btn_commencer.draw(self.screen)
        self.btn_retour.draw(self.screen)

    # ------------------------------------------------------------------ boucle

    def run(self, clock=None):
        """Renvoie un dictionnaire de reglages, None (retour au menu)
        ou la chaine 'quitter'."""
        while self.running:
            for event in ui.evenements():
                self.handle_event(event)
            self.draw()
            ui.afficher()
            if clock is not None:
                clock.tick(60)
            else:
                pygame.time.wait(16)
        return self.resultat
