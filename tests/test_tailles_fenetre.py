# tests/test_tailles_fenetre.py - tout reste visible, quelle que soit la fenetre (25/10).
#     python tests/test_tailles_fenetre.py
# Demande de Julien : en petite fenetre, des panneaux disparaissaient (VARIANTE,
# RYTHME, NIVEAU dans les reglages) et, dans la revue, les boutons recouvraient
# la courbe et la liste des coups. Chaque ecran est place a plusieurs tailles de
# fenetre ET avec les 4 tailles de textes (Options > Affichage) ; on verifie :
#   - aucun element ne sort de la fenetre,
#   - aucun bloc ne chevauche son voisin,
#   - aucun panneau ne disparait,
#   - aucun texte n'est dessine sous la taille minimale lisible (ui.TEXTE_MINI).

import os
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import pygame

pygame.init()
pygame.display.set_mode((64, 64))

import apparence
import asset_manager

TEMP = tempfile.mkdtemp()
asset_manager.dossier_ecriture = lambda: TEMP

import ui

TAILLES = [(900, 560), (1024, 640), (1280, 720), (1366, 768), (1920, 1080),
           (3840, 2160), (900, 1200)]
TEXTES = [0.88, 1.0, 1.15, 1.30]          # Petite, Normale, Grande, Tres grande
_ECHELLE = {"valeur": 1.0}
_reglage = apparence.reglage
apparence.reglage = lambda cle, defaut=None: (
    _ECHELLE["valeur"] if cle == "echelle_interface" else _reglage(cle, defaut))

echecs = []


def verifier(condition, message):
    if not condition:
        print("  ECHEC " + message)
        echecs.append(message)
    return condition


# --- les tailles de police vraiment demandees pendant un dessin
_police = ui.police
_tailles_vues = []


def _police_espion(taille, gras=False, mono=False):
    appelant = sys._getframe(1)
    if appelant.f_code.co_filename.endswith("ui.py"):
        appelant = appelant.f_back
    _tailles_vues.append((taille, "%s:%d" % (os.path.basename(appelant.f_code.co_filename),
                                             appelant.f_lineno)))
    return _police(taille, gras, mono)


ui.police = _police_espion


def textes_lisibles(nom, dessiner):
    del _tailles_vues[:]
    dessiner()
    if _tailles_vues:
        taille, ou = min(_tailles_vues)
        verifier(taille >= ui.TEXTE_MINI,
                 "%s : texte de %d px (minimum %d, %s)" % (nom, taille, ui.TEXTE_MINI, ou))


def R(r):
    return pygame.Rect(r)


def dans(nom, rects, cadre):
    for etiquette, r in rects:
        r = R(r)
        verifier(r.width > 0 and r.height > 0 and cadre.contains(r),
                 "%s : %s %s hors de %s" % (nom, etiquette, tuple(r), tuple(cadre)))


def sans_chevauchement(nom, rects):
    rects = [(e, R(r)) for e, r in rects]
    for i, (e1, r1) in enumerate(rects):
        for e2, r2 in rects[i + 1:]:
            verifier(not r1.colliderect(r2),
                     "%s : %s %s chevauche %s %s" % (nom, e1, tuple(r1), e2, tuple(r2)))


def ecran(taille):
    ui.vider_cache()
    return pygame.display.set_mode(taille)


# ----------------------------------------------------------------- partie
import layout

print("1. Partie (Normal et Freestyle) : echiquier et panneau")
for taille in TAILLES:
    for echelle_texte in TEXTES:
        _ECHELLE["valeur"] = echelle_texte
        nom = "partie %dx%d textes %.2f" % (taille + (echelle_texte,))
        d = layout.Disposition(*taille)
        fenetre = pygame.Rect(0, 0, *taille)
        blocs = [("plateau", d.rect_plateau()), ("horloge_haut", d.horloge_haut),
                 ("captures_haut", d.captures_haut), ("infos", d.infos),
                 ("coups", d.coups), ("captures_bas", d.captures_bas),
                 ("horloge_bas", d.horloge_bas), ("boutons", d.boutons)]
        dans(nom, blocs, fenetre)
        sans_chevauchement(nom, blocs)
        verifier(d.cote_plateau == d.taille_case * 8, nom + " : echiquier carre")
        verifier(d.cote_plateau >= 0.75 * min(taille[0] - d.panneau_l, taille[1])
                 or getattr(d, "mode", "") == "hauteur", nom + " : l'echiquier garde la priorite (%d px)" % d.cote_plateau)
        verifier(abs(d.echelle - ui.echelle(taille)) < 0.01 or d.echelle < ui.echelle(taille),
                 nom + " : une seule echelle (disposition %.2f, textes %.2f)"
                 % (d.echelle, ui.echelle(taille)))
    if taille[1] > taille[0]:
        verifier(getattr(layout.Disposition(*taille), "mode", "") == "hauteur",
                 "%dx%d : fenetre en hauteur, le panneau passe sous l'echiquier" % taille)

from game_manager import GameManager
gm = GameManager("test")
for variante in ("normal", "freestyle"):
    for taille in ((900, 560), (1920, 1080), (900, 1200)):
        for echelle_texte in (0.88, 1.30):
            _ECHELLE["valeur"] = echelle_texte
            gm.screen = ecran(taille)
            gm._appliquer_taille(*taille)
            gm.game_mode = "hotseat"
            gm.reglages = {"minutes": 5, "increment": 3, "pendule_active": True,
                           "retourner_plateau": False, "variante": variante}
            gm.preparer_partie()
            for uci in ("e2e4", "e7e5", "g1f3", "b8c6") if variante == "normal" else ():
                gm.board.make_move(chess.Move.from_uci(uci))
            textes_lisibles("partie %s %dx%d textes %.2f" % ((variante,) + taille + (echelle_texte,)),
                            gm.board.draw)
            gm.cleanup_game()

# ----------------------------------------------------------------- reglages
print("2. Reglages avant partie : aucun panneau ne disparait")
from settings_screen import SettingsScreen

for taille in TAILLES:
    for echelle_texte in TEXTES:
        _ECHELLE["valeur"] = echelle_texte
        surface = ecran(taille)
        fenetre = surface.get_rect()
        for mode in ("stockfish", "hotseat"):
            for variante in ("normal", "freestyle"):
                s = SettingsScreen(surface, mode)
                s.variante = variante
                s.freestyle_hasard = False
                s._placer()
                s._synchroniser_chips()
                nom = "reglages %s %s %dx%d textes %.2f" % ((mode, variante) + taille + (echelle_texte,))
                panneaux = [("niveau", s.panneau_niveau), ("temps", s.panneau_temps),
                            ("variante", s.panneau_variante)]
                if mode == "stockfish":
                    panneaux.append(("rythme", s.panneau_rythme))
                manquants = [e for e, p in panneaux if p is None]
                if not verifier(not manquants, "%s : panneau(x) absent(s) %s" % (nom, manquants)):
                    continue
                boutons = [("commencer", s.btn_commencer.rect), ("retour", s.btn_retour.rect),
                           ("retenir", s.zone_retenir)]
                dans(nom, panneaux + boutons, fenetre)
                sans_chevauchement(nom, panneaux + boutons)
                contenu = {"niveau": s.chips_niveau if mode == "stockfish" else s.chips_plateau,
                           "rythme": s.chips_rythme, "temps": s.chips_duree + s.chips_increment,
                           "variante": s.chips_variante + s.chips_position + s.chips_pas_960}
                for etiquette, panneau in panneaux:
                    dans(nom + " " + etiquette,
                         [(c.libelle, c.rect) for c in contenu[etiquette]], panneau)
                if mode == "stockfish":
                    dans(nom + " niveau", [("curseur elo", s.slider.rect),
                                           ("case profil", s.case_profil)], s.panneau_niveau)
                dans(nom + " variante", [("curseur 960", s.slider_960.rect)], s.panneau_variante)
                textes_lisibles(nom, s.draw)

# ----------------------------------------------------------------- revue
print("3. Revue : les pourcentages et la feuille restent visibles")
from analyse_partie import AnalyseurPartie
from ecran_revue import EcranRevue

PARTIE = ("e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 f3g5 d7d5 e4d5 f6d5 g5f7 e8f7 d1f3 "
          "f7e6 b1c3 c6b4 f3e4 c7c6 d2d4 b4d3").split()


class MoteurFactice:
    def analyser_position(self, fen, profondeur=0, temps_max_ms=0, lignes=1):
        coup = next(iter(chess.Board(fen).legal_moves))
        return {"coup": coup.uci(), "evaluation": 0.2, "mat": None,
                "second_evaluation": 0.1, "second_mat": None}


analyseur = AnalyseurPartie(None, PARTIE, moteur=MoteurFactice())
analyseur._travailler()
for taille in TAILLES:
    for echelle_texte in TEXTES:
        _ECHELLE["valeur"] = echelle_texte
        surface = ecran(taille)
        r = EcranRevue(surface, analyseur, {}, ("Toi", "Ordinateur (1200)"), "0-1")
        r.aller_a(10, son=False)
        nom = "revue %dx%d textes %.2f" % (taille + (echelle_texte,))
        blocs = [("titre", r.zone_titre), ("precision", r.zone_precision),
                 ("detail", r.zone_detail), ("courbe", r.zone_courbe),
                 ("coups", r.zone_coups)]
        boutons = [(b.libelle if hasattr(b, "libelle") else "bouton", b.rect)
                   for b in list(r.boutons_nav) + [r.btn_retourner, r.btn_exporter,
                                                   r.btn_analyser, r.btn_retour]]
        dans(nom, blocs + boutons, r.panneau)
        dans(nom, [("panneau", r.panneau), ("barre", r.disposition.barre),
                   ("plateau", r.disposition.rect_plateau())], surface.get_rect())
        sans_chevauchement(nom, blocs + boutons)
        sans_chevauchement(nom, [("panneau", r.panneau), ("barre", r.disposition.barre),
                                 ("plateau", r.disposition.rect_plateau())])
        verifier(r.lignes_visibles >= 3, nom + " : %d ligne(s) de coups visibles" % r.lignes_visibles)
        textes_lisibles(nom, r.draw)

# ----------------------------------------------------------------- analyse libre
print("4. Analyse libre")
from ecran_analyse_libre import EcranAnalyseLibre

for taille in TAILLES:
    for echelle_texte in TEXTES:
        _ECHELLE["valeur"] = echelle_texte
        surface = ecran(taille)
        lib = EcranAnalyseLibre(surface, {}, coups=PARTIE[:10], stockfish_path=None, threads=1)
        lib.analyse.mettre_en_pause(True)
        nom = "analyse libre %dx%d textes %.2f" % (taille + (echelle_texte,))
        blocs = [("titre", lib.zone_titre), ("lignes", lib.zone_lignes), ("coups", lib.zone_coups)]
        boutons = [("bouton", b.rect) for b in list(lib.boutons_nav) + [
            lib.btn_moteur, lib.btn_retourner, lib.btn_retour, lib.btn_editer,
            lib.btn_coller, lib.btn_copier]]
        dans(nom, blocs + boutons, lib.panneau)
        sans_chevauchement(nom, blocs + boutons)
        verifier(lib.lignes_visibles >= 3, nom + " : %d ligne(s) de coups" % lib.lignes_visibles)
        textes_lisibles(nom, lib.draw)
        lib.analyse.arreter()

# ----------------------------------------------------------------- autres ecrans
print("5. Autres ecrans : tous les boutons dans la fenetre")


def boutons_de(objet):
    """Tous les rectangles cliquables d'un ecran (boutons, pastilles)."""
    trouves = []
    for cle, valeur in vars(objet).items():
        elements = valeur if isinstance(valeur, (list, tuple)) else [valeur]
        if isinstance(valeur, dict):
            elements = list(valeur.values())
        for e in elements:
            rect = getattr(e, "rect", None)
            if isinstance(rect, pygame.Rect) and rect.width > 0 and rect.height > 0:
                trouves.append((cle, rect))
    return trouves


import ecran_classements
import ecran_entrainement
import ecran_mes_parties
import ecran_mise_a_jour
import ecran_options
import ecran_problemes
import ecran_statistiques
import menu_pause

FABRIQUES = [
    ("menu", lambda s: (gm.menu.redimensionner(*s.get_size()), gm.menu)[1]),
    ("options", lambda s: ecran_options.EcranOptions(s)),
    ("problemes", lambda s: ecran_problemes.EcranProblemes(s, {})),
    ("ouvertures", lambda s: ecran_entrainement.EcranEntrainement(s, {})),
    ("mes parties", lambda s: ecran_mes_parties.EcranMesParties(s)),
    ("statistiques", lambda s: ecran_statistiques.EcranStatistiques(s, parties=[])),
    ("classements", lambda s: ecran_classements.EcranClassements(s, {})),
    ("pause", lambda s: menu_pause.MenuPause(s)),
    ("mise a jour", lambda s: ecran_mise_a_jour.EcranMiseAJour(s)),
]
for taille in TAILLES:
    for echelle_texte in (0.88, 1.30):
        _ECHELLE["valeur"] = echelle_texte
        surface = ecran(taille)
        gm.screen = surface
        gm.menu.screen = surface
        interieur = surface.get_rect().inflate(-8, -8)      # au moins 4 px du bord
        for nom_ecran, fabrique in FABRIQUES:
            nom = "%s %dx%d textes %.2f" % ((nom_ecran,) + taille + (echelle_texte,))
            e = fabrique(surface)
            if nom_ecran == "pause":
                e.ouvrir()
            textes_lisibles(nom, e.draw)
            dans(nom, boutons_de(e), interieur)

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
