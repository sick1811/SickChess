# tests/test_niveaux_elo.py - niveaux de l'ordinateur en vrai Elo (31/10, travail p34).
#     python tests/test_niveaux_elo.py
# Sans Stockfish. La table de calibrage (jeu/niveaux_elo.py) est croissante,
# couvre tout le curseur, chaque niveau du menu y a sa place, le moteur reçoit
# la CONSIGNE de la table et le jeu affiche l'Elo choisi. Le calcul d'Elo de
# l'outil outils/calibrer_elo.py est juste.

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "jeu"))
sys.path.insert(0, os.path.join(RACINE, "outils"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import calibrer_elo  # noqa: E402
import engine  # noqa: E402
import langue_en  # noqa: E402
import niveaux_elo  # noqa: E402
import settings_screen  # noqa: E402

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def table_valide(table):
    """Les deux premières colonnes strictement croissantes, bornes couvertes."""
    affiches = [ligne[0] for ligne in table]
    consignes = [ligne[1] for ligne in table]
    return (all(a < b for a, b in zip(affiches, affiches[1:]))
            and all(a < b for a, b in zip(consignes, consignes[1:]))
            and affiches[0] <= niveaux_elo.ELO_MIN
            and affiches[-1] >= niveaux_elo.ELO_MAX
            and all(100 <= c <= 3200 for c in consignes))


print("1. La table de calibrage")
T = niveaux_elo.TABLE
verifier(all(len(ligne) == 4 for ligne in T), "chaque ligne : affiché, consigne, mesuré, marge")
verifier(table_valide(T), "Elo affichés et consignes strictement croissants, de %d à %d"
         % (niveaux_elo.ELO_MIN, niveaux_elo.ELO_MAX))
verifier(T[0][0] <= 400 and T[-1][0] >= max(e for _n, e in niveaux_elo.NIVEAUX),
         "la table couvre 400 ... Maximum")
for ligne in T:
    if ligne[2] is not None:
        verifier(ligne[3] is not None and ligne[3] > 0,
                 "ligne %d mesurée : sa marge est donnée" % ligne[0])
verifier(niveaux_elo.est_calibree() or niveaux_elo.ETALON is None,
         "sans mesure, pas d'étalon annoncé")
for elo in (100, 400, 650, 1320, 1999, 3000, 3200):
    c = niveaux_elo.consigne(elo)
    verifier(abs(niveaux_elo.elo_affiche(c) - elo) <= 1,
             "consigne(%d) = %d, et l'inverse redonne %d" % (elo, c, elo))
precedent = -1
croissante = True
for elo in range(niveaux_elo.ELO_MIN, niveaux_elo.ELO_MAX + 1, 25):
    c = niveaux_elo.consigne(elo)
    croissante = croissante and c >= precedent
    precedent = c
verifier(croissante, "tout le curseur (pas de 25) : la consigne ne redescend jamais")
verifier(niveaux_elo.consigne(-50) == niveaux_elo.consigne(niveaux_elo.ELO_MIN)
         and niveaux_elo.consigne(9999) == niveaux_elo.consigne(niveaux_elo.ELO_MAX)
         and niveaux_elo.consigne("abc") == niveaux_elo.consigne(niveaux_elo.ELO_MIN),
         "valeurs hors bornes ou abîmées : bornées, jamais d'erreur")
if not niveaux_elo.est_calibree():
    verifier(all(niveaux_elo.consigne(e) == e for e in range(100, 3201, 25)),
             "pas encore de mesure : consigne = Elo affiché (le jeu ne change pas)")

print("2. Les niveaux du menu")
elos_menu = [e for _n, e in niveaux_elo.NIVEAUX]
verifier(elos_menu == sorted(elos_menu) and len(set(elos_menu)) == len(elos_menu),
         "niveaux du menu croissants, sans doublon")
verifier([n for n, _e in niveaux_elo.NIVEAUX][0] == "Débutant"
         and niveaux_elo.NIVEAUX[-1][0] == "Maximum", "de Débutant à Maximum")
for nom, elo in niveaux_elo.NIVEAUX:
    verifier(niveaux_elo.ELO_MIN <= elo <= niveaux_elo.ELO_MAX
             and T[0][0] <= elo <= T[-1][0],
             "%s (%d) : dans la table et dans le curseur" % (nom, elo))
    verifier(nom in langue_en.EN, "« %s » a sa traduction anglaise" % nom)
verifier(settings_screen.NIVEAUX is niveaux_elo.NIVEAUX,
         "Options : les boutons de niveau viennent de la table")

print("3. Options : le curseur et l'Elo affiché suivent la table")
import pygame  # noqa: E402

pygame.init()
ecran = pygame.display.set_mode((1280, 800))
original = settings_screen.charger_config
settings_screen.charger_config = lambda: {"elo_suit_profil": False, "elo": 1600}
try:
    options = settings_screen.SettingsScreen(ecran, "stockfish")
finally:
    settings_screen.charger_config = original
verifier((options.slider.mini, options.slider.maxi) == (niveaux_elo.ELO_MIN, niveaux_elo.ELO_MAX),
         "curseur de %d à %d" % (niveaux_elo.ELO_MIN, niveaux_elo.ELO_MAX))
verifier([(c.libelle, c.valeur) for c in options.chips_niveau] == list(niveaux_elo.NIVEAUX),
         "un bouton par niveau de la table, dans l'ordre")
verifier(options.reglages()["elo"] == 1600, "Options rend l'Elo AFFICHÉ (1600), pas la consigne")


print("4. Le moteur reçoit la consigne de la table, le jeu garde l'Elo affiché")


class MoteurMuet(engine.StockfishEngine):
    """Un StockfishEngine sans processus : on note ce qu'il enverrait."""

    def __init__(self):
        import threading
        self._verrou = threading.RLock()
        self.envoye = []
        self.options_disponibles = {"UCI_Elo": {"min": 1320, "max": 3190},
                                    "UCI_LimitStrength": {}, "Skill Level": {},
                                    "MultiPV": {}, "Threads": {}}
        self.elo_courant = None
        self.elo_consigne = None
        self.elo_bride = None
        self.multipv_courant = 1
        self.profondeur_max = None
        self.process = None

    def _send_command(self, cmd):
        self.envoye.append(cmd)
        return True

    def _wait_response(self, expected, timeout=8.0):
        return True


def uci_elo(moteur):
    valeurs = [c for c in moteur.envoye if c.startswith("setoption name UCI_Elo value")]
    return int(valeurs[-1].split()[-1]) if valeurs else None


sauve = niveaux_elo.TABLE
niveaux_elo.TABLE = [(100, 100, None, None), (1600, 1800, 1600, 40),
                     (2000, 2150, 2000, 45), (3200, 3200, None, None)]
try:
    m = MoteurMuet()
    m.set_custom_elo(1600)
    verifier(uci_elo(m) == 1800 and m.elo_consigne == 1800,
             "table d'essai 1600 -> 1800 : Stockfish reçoit UCI_Elo 1800 (%s)" % uci_elo(m))
    verifier(m.elo_courant == 1600, "elo_courant reste l'Elo affiché (1600)")
    m = MoteurMuet()
    m.set_custom_elo(1800)
    verifier(uci_elo(m) == 1975, "entre deux lignes : 1800 -> 1975 (%s)" % uci_elo(m))
    m = MoteurMuet()
    m.set_custom_elo(1600, brut=True)
    verifier(uci_elo(m) == 1600 and m.elo_courant == 1600,
             "brut=True (outil de calibrage) : la consigne part telle quelle")
    m = MoteurMuet()
    m.set_custom_elo(900)
    verifier(m.elo_bride == niveaux_elo.consigne(900) and m.elo_bride < 1320
             and any("UCI_LimitStrength value false" in c for c in m.envoye),
             "sous 1320 : le choix maison reçoit la consigne (%s)" % m.elo_bride)
    # 31/10 (testeur) : le livre d'ouvertures et le temps de réflexion du bot
    # doivent voir l'Elo AFFICHE, pas la consigne envoyée au moteur.
    import background_ai
    from types import SimpleNamespace
    vu = background_ai.BackgroundAI._elo_du_bot(SimpleNamespace(engine=m))
    verifier(vu == 900, "le bot réglé à 900 affiché se voit à 900 (pas %s)" % vu)
finally:
    niveaux_elo.TABLE = sauve
m = MoteurMuet()
m.set_custom_elo(2000)
verifier(uci_elo(m) == niveaux_elo.consigne(2000), "table du jeu : 2000 -> %d" % niveaux_elo.consigne(2000))

print("5. Le calcul d'Elo de l'outil de calibrage")
p = calibrer_elo.performance([(1500, 0.5)] * 10)
verifier(abs(p["elo"] - 1500) < 1 and p["borne"] is None, "50 %% contre 1500 = 1500 (%.0f)" % p["elo"])
p = calibrer_elo.performance([(1500, 1.0)] * 3 + [(1500, 0.0)])
verifier(abs(p["elo"] - 1691) < 2, "75 %% contre 1500 = 1691 (%.0f)" % p["elo"])
p20 = calibrer_elo.performance([(1500, 1.0), (1500, 0.0)] * 10)
p80 = calibrer_elo.performance([(1500, 1.0), (1500, 0.0)] * 40)
verifier(p80["marge"] < p20["marge"], "plus de parties = marge plus petite (%.0f < %.0f)"
         % (p80["marge"], p20["marge"]))
p = calibrer_elo.performance([(1320, 0.0)] * 6)
verifier(p["borne"] == "max" and p["elo"] < 1320, "tout perdu : seulement une borne (au plus %.0f)" % p["elo"])
p = calibrer_elo.performance([(2000, 1.0), (1600, 0.5), (1800, 0.5)])
verifier(1700 < p["elo"] < 2100, "adversaires mélangés : %.0f" % p["elo"])
verifier(calibrer_elo.performance([]) is None, "aucune partie : pas de mesure")

table, changee = calibrer_elo.proposer_table({800: {"elo": 790, "marge": 80, "borne": None},
                                              1600: {"elo": 1610, "marge": 70, "borne": None}})
verifier(not changee and table_valide(table) and all(a == c for a, c, _m, _g in table),
         "mesures dans la marge : la table reste l'identité")
table, changee = calibrer_elo.proposer_table({800: {"elo": 600, "marge": 60, "borne": None},
                                              1600: {"elo": 1400, "marge": 60, "borne": None},
                                              2400: {"elo": 2450, "marge": 60, "borne": None}})
verifier(changee and table_valide(table), "niveaux trop faibles : nouvelle table valide %s" % table)
sauve = niveaux_elo.TABLE
niveaux_elo.TABLE = table
try:
    verifier(niveaux_elo.consigne(1400) == 1600 and niveaux_elo.consigne(600) == 800,
             "avec elle, afficher 1400 envoie 1600 et afficher 600 envoie 800")
finally:
    niveaux_elo.TABLE = sauve
table, changee = calibrer_elo.proposer_table({1600: {"elo": 1700, "marge": 50, "borne": None},
                                              2000: {"elo": 1650, "marge": 50, "borne": None}})
verifier(table_valide(table), "mesures qui se contredisent : table quand même croissante")
verifier(calibrer_elo.lire_cadence("120+1") == (120.0, 1.0)
         and calibrer_elo.lire_cadence("60+0,6") == (60.0, 0.6)
         and calibrer_elo.lire_cadence("5") == (5.0, 0.0), "lecture des cadences")
adv = calibrer_elo.choisir_adversaire(1600, [], {})
verifier(adv == {"type": "stockfish", "elo": 1600}, "premier adversaire de 1600 : Stockfish 1600")
adv = calibrer_elo.choisir_adversaire(400, [], {})
verifier(adv == {"type": "stockfish", "elo": 1320}, "sous 1320 sans échelon : Stockfish 1320")
parties = [{"niveau": 1200, "adversaire": {"type": "stockfish", "elo": 1320}, "score": 0.5}] * 10
mesures = {1200: {"elo": 1000, "marge": 80, "borne": None, "parties": 10},
           400: {"elo": 700, "marge": 90, "borne": None, "parties": 20}}
adv = calibrer_elo.choisir_adversaire(400, parties, mesures)
verifier(adv["type"] == "niveau" and adv["consigne"] == 1200,
         "sous 1320 : le niveau 1200 déjà mesuré sert d'échelon (%s)" % adv)

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
