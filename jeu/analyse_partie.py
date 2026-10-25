# analyse_partie.py - SickChess : l'analyse Stockfish d'une partie, coup par coup.
#
# Reecrit a partir de celui de V8_TURBO_3000 (1016 lignes, quatre moteurs en
# parallele, sept profils de puissance). Ici : UN moteur d'analyse, trois
# puissances, et les memes regles de pastilles (annotations.py).
#
# COMMENT CA MARCHE
#   1. Un SURVOL de toute la partie a faible profondeur : la courbe, les
#      pastilles et la precision arrivent en quelques secondes.
#   2. Une PASSE FINE repasse ensuite sur chaque position pour affiner.
#   La position que le joueur regarde dans la revue passe toujours en tete :
#   le detail du coup affiche arrive presque tout de suite.
#
# VOCABULAIRE
#   position k = la position APRES k demi-coups (0 = position de depart)
#   coup i     = le demi-coup qui mene de la position i a la position i+1
#   Toutes les evaluations sont en pions, du point de vue des BLANCS.

import math
import os
import threading
import time

import chess
import freestyle

import annotations

# nom -> (profondeur de la passe fine, temps maximum par position en ms)
# SickChess 17/10 (remarque de Julien : "trop imprecis, il faut un moteur tres
# puissant, rapide et surtout precis, c'est un jeu ultra competitif") : une
# marche de plus partout. L'analyse suit maintenant la partie en direct (voir
# ajouter_coups), donc la profondeur ne se paie plus a la fin.
# 17/10 (Julien : « aussi precise que si les meilleurs joueurs du monde
# utilisaient mon jeu ») : une marche de plus. La vitesse vient maintenant des
# moteurs en parallele et du survol allege, plus d'une profondeur au rabais.
# 18/10 (13) - TROIS FACONS DE DIRE A STOCKFISH « C'EST ASSEZ » (choix de
# Julien : plusieurs modes, le calcul fixe par defaut) :
#   calcul     : la MEME quantite de calcul (noeuds) pour chaque position, comme
#                lichess (mais 10 a 30 fois plus). Meme resultat sur tous les PC
#                (un PC lent prend juste plus de temps), duree previsible, et une
#                version plus recente de Stockfish compte pour ce qu'elle vaut.
#   profondeur : jusqu'a une profondeur. Duree imprevisible : sur la partie
#                contre dragondu5, la profondeur 30 coute de 3 a 78 millions de
#                noeuds selon la position (mesure du 18/10, Stockfish 17.1).
#   temps      : X secondes par position ; refaite une fois avec le double si
#                la profondeur minimale n'est pas atteinte (« jamais sous 26 »).
# Mesure du 18/10 : entre la profondeur 22 et la 30, l'evaluation bouge de
# 0,05 pion en position equilibree. 50 millions de noeuds = profondeur 28 a 33.
#
# Chaque reglage :
#   mode, profondeur (0 = pas de plafond), noeuds (0 = pas de budget), temps
#   (ms ; en mode calcul c'est un simple garde-fou), profondeur_min (refaite
#   une fois si elle n'est pas atteinte), lignes = la passe des trois meilleurs
#   coups (profondeur, noeuds, temps) ou None si la passe finale les donne,
#   effort = de 1 a 5, pour comparer deux analyses faites avec des reglages
#   differents (une analyse enregistree est reprise si son effort suffit).
def _r(mode, profondeur, noeuds, temps_ms, profondeur_min, effort, lignes):
    return {"mode": mode, "profondeur": profondeur, "noeuds": noeuds,
            "temps_ms": temps_ms, "profondeur_min": profondeur_min,
            "effort": effort, "lignes": lignes}


_LIGNES_22 = (22, 0, 6000)
REGLAGES = {
    # 18/10 (16) - VERIFICATION CIBLEE (Julien : « plus precise que maintenant
    # et quasiment instantanee »). En calcul fixe, chaque position recoit une
    # analyse rapide (trois meilleurs coups : 2 / 3 / 5 millions), puis SEULS
    # les coups dont la pastille pourrait changer sont verifies en profondeur
    # (15 / 25 / 50 millions). Mesure sur les parties de Julien : 20 a 35 %
    # des positions a verifier (13 sur 39 contre dragondu5). Forte : la meme
    # verification qu'en (14) (25 millions) la ou le verdict se joue, pour
    # environ 1,7 fois moins de calcul au total ; Maximale : deux fois plus
    # profond que Forte la ou ca compte.
    "calcul_rapide": _r("calcul", 0, 15000000, 120000, 0, 3, (0, 2000000, 60000)),
    "calcul_forte": _r("calcul", 0, 25000000, 180000, 0, 4, (0, 3000000, 60000)),
    "calcul_maximale": _r("calcul", 0, 50000000, 240000, 0, 5, (0, 5000000, 60000)),
    "profondeur_rapide": _r("profondeur", 22, 0, 6000, 22, 2, None),
    "profondeur_forte": _r("profondeur", 26, 0, 12000, 26, 3, _LIGNES_22),
    "profondeur_maximale": _r("profondeur", 30, 0, 30000, 30, 5, _LIGNES_22),
    "temps_rapide": _r("temps", 0, 0, 3000, 22, 2, None),
    "temps_forte": _r("temps", 0, 0, 7000, 26, 4, _LIGNES_22),
    "temps_maximale": _r("temps", 0, 0, 15000, 26, 5, _LIGNES_22),
    # Les anciens noms : config.json d'avant le 18/10, « Mes erreurs » et les
    # statistiques (« rapide » = toute analyse enregistree convient).
    "rapide": _r("profondeur", 18, 0, 2500, 18, 1, None),
    "normale": _r("profondeur", 22, 0, 6000, 22, 2, None),
    "forte": _r("profondeur", 26, 0, 12000, 26, 3, None),
    "maximale": _r("profondeur", 30, 0, 30000, 30, 5, _LIGNES_22),
}
# Compatibilite : (profondeur visee, temps) par nom.
PUISSANCES = dict((nom, (r["profondeur"] or r["profondeur_min"], r["temps_ms"]))
                  for nom, r in REGLAGES.items())
MODES = ("calcul", "profondeur", "temps")
NIVEAUX = ("rapide", "forte", "maximale")
PUISSANCE_PAR_DEFAUT = "calcul_forte"   # 18/10 (14) : Forte, choix de Julien
TEMPS_LIGNES_MS = 6000


def puissance_de(config):
    """Le reglage d'analyse choisi dans Options (config.json) :
    "analyse_mode" (calcul / profondeur / temps) + "analyse_niveau"
    (rapide / forte / maximale). L'ancien "analyse_puissance" donne le
    niveau quand le nouveau n'existe pas encore."""
    config = config or {}
    mode = config.get("analyse_mode")
    if mode not in MODES:
        mode = "calcul"
    niveau = config.get("analyse_niveau")
    if niveau not in NIVEAUX:
        # 24/10 (p31) : rien de choisi -> Forte, ou Rapide sur un petit PC.
        niveau = {"rapide": "rapide", "normale": "rapide", "forte": "forte"}.get(
            config.get("analyse_puissance"), "rapide" if _petit_pc() else "forte")
    return "%s_%s" % (mode, niveau)


def effort_d_une_profondeur(profondeur):
    """L'effort d'une analyse enregistree avant le 18/10 (seule sa profondeur
    etait notee)."""
    profondeur = int(profondeur or 0)
    if profondeur >= 30:
        return 5
    if profondeur >= 26:
        return 3
    return 2 if profondeur >= 22 else 1

PROFONDEUR_SURVOL = 10           # la courbe en quelques secondes, rien de plus
TEMPS_SURVOL_MS = 300

# Taille de la table de hachage du moteur d'analyse (Mo). Plus grande = les
# positions deja vues ne sont pas recalculees.
# 18/10 (13) - Julien : « JE VEUX 6 GO DE HACHAGE ». C'est le TOTAL pour
# l'analyse, partage entre les moteurs (3 x 2 Go sur son i7-8700K), pendant la
# partie comme apres. Garde-fou pour les PC des acheteurs : jamais plus de la
# moitie de la memoire qui reste une fois 4 Go laisses a Windows et au jeu
# (16 Go de memoire -> 6 Go ; 8 Go -> 2 Go).
# 18/10 (15) - Julien, apres explication (au-dela de 4 Go, aucun gain visible
# pour des analyses de cette duree) : « OK 4 ». Total 4 Go (3 x 1,3 Go).
HASH_ANALYSE_MB = 4096


def memoire_totale_mo():
    """La memoire vive du PC en Mo, ou None si on ne sait pas la lire."""
    try:
        if os.name == "nt":
            import ctypes

            class _Etat(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            etat = _Etat()
            etat.dwLength = ctypes.sizeof(_Etat)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(etat)):
                return int(etat.ullTotalPhys // (1024 * 1024))
            return None
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
                   // (1024 * 1024))
    except Exception:
        return None


def hachage_total_mo(memoire=None):
    """Le hachage total de l'analyse : 4 Go, sauf si le PC n'a pas assez de
    memoire (voir HASH_ANALYSE_MB)."""
    memoire = memoire_totale_mo() if memoire is None else memoire
    total = HASH_ANALYSE_MB if not memoire else int(min(HASH_ANALYSE_MB, max(512, (memoire - 4096) // 2)))
    if _petit_pc():
        total = min(total, _module_petit_pc().HACHAGE_PETIT_MO)    # 24/10 (p31)
    return total


def _module_petit_pc():
    import petit_pc
    return petit_pc


def _petit_pc():
    """24/10 (p31) : PC modeste (petit_pc.py) : un seul Stockfish, 1 Go, 1 coeur en partie."""
    try:
        return _module_petit_pc().est_petit()
    except Exception:
        return False

# Pour juger un coup en pions, une evaluation est bornee a +/- 15 : au-dela, la
# partie est jouee, et un mat (20) ne doit pas compter comme "15 pions de plus".
BORNE_PIONS = 15.0

# Au survol on calcule toujours deux lignes (c'est presque gratuit a faible
# profondeur). A la passe fine, seulement si le meilleur coup devancait
# nettement le deuxieme : ce sont les seules positions ou "Tres bien" (le seul
# coup qui tenait) est possible. Partout ailleurs, une ligne : deux fois plus
# rapide.
ECART_CANDIDAT = 15.0

# Un mat force compte pour +/- 20 pions : les chances de gagner sont alors a
# 100 %, et un mat ne fausse pas l'echelle de la courbe.
EVAL_MAT = 20.0

NOMBRE_MOMENTS_CLES = 3

# 18/10 (16) : marge autour des seuils de pastille (points de chances, pions)
# en dessous de laquelle un coup est verifie en profondeur.
MARGE_VERDICT = 3.0
MARGE_PIONS = 0.3

# 18/10 (13) : au-dela de 8 pions d'avance (95 % de chances de gagner) ou d'un
# mat, la passe profonde ne change aucune pastille : on s'en passe.
PIONS_PARTIE_JOUEE = 8.0

# 17/10 (Julien : « il calculera toujours le meilleur coup, et s'il y a
# plusieurs coups aussi bons, il les propose ») : la passe fine classe TOUJOURS
# les trois meilleurs coups de chaque position. Ils sont enregistres avec
# l'analyse : la revue les montre en fleches sans rien recalculer.
LIGNES_FINES = 3
# Deux coups sont « aussi bons » quand leurs chances de gagner different de
# moins de 2 points (environ 0,1 pion dans une position equilibree).
SEUIL_EQUIVALENT = 2.0
# Un coup joue qui vaut le meilleur a moins d'un demi-point pres EST un
# meilleur coup (deux coups de meme evaluation : les deux sont « Meilleur »).
SEUIL_MEME_VALEUR = 0.5
# La passe fine est refaite une fois (avec deux fois plus de temps) quand
# Stockfish n'a pas atteint la profondeur demandee - par exemple parce que
# l'ordinateur jouait en meme temps.
TOLERANCE_PROFONDEUR = 2
VERSION_CACHE = 2


def _en_pions(evaluation, mat):
    """Evaluation du point de vue du joueur au trait, mat compris."""
    if mat is not None:
        return EVAL_MAT if int(mat) > 0 else -EVAL_MAT
    if evaluation is None:
        return None
    return float(evaluation)


# ---------------------------------------------------------------- precision
# Methode de lichess : chaque coup recoit une note de 0 a 100 d'apres les
# chances de gagner qu'il a fait perdre ; la precision d'un joueur est la
# moyenne d'une moyenne ponderee (par la tension de la position) et d'une
# moyenne harmonique (qui punit franchement les gaffes).

def chances_lichess(evaluation):
    """Chances de gagner des Blancs (0-100) EXACTEMENT comme lichess pour la
    precision : evaluation bornee a +/- 10 pions, un mat compte pour 10."""
    if evaluation is None:
        return None
    centipions = max(-1000.0, min(1000.0, float(evaluation) * 100.0))
    return 50.0 + 50.0 * (2.0 / (1.0 + math.exp(-0.00368208 * centipions)) - 1.0)


def precision_du_coup(perte):
    """Precision d'un coup (0-100) d'apres les chances perdues, formule de
    lichess (AccuracyPercent.scala), bonus d'incertitude de 1 compris."""
    perte = float(perte)
    if perte <= 0:
        return 100.0
    brut = 103.1668100711649 * math.exp(-0.04354415386753951 * perte) \
        - 3.166924740191411
    return max(0.0, min(100.0, brut + 1.0))


def _ecart_type(valeurs):
    if len(valeurs) < 2:
        return 0.5
    moyenne = sum(valeurs) / float(len(valeurs))
    return math.sqrt(sum((v - moyenne) ** 2 for v in valeurs) / len(valeurs))


def poids_lichess(chances_positions):
    """Le poids de chaque coup (lichess gameAccuracy) : l'ecart type des
    chances sur une fenetre glissante, borne entre 0,5 et 12. Une liste par
    coup (positions - 1)."""
    n = len(chances_positions)
    if n < 2:
        return []
    taille = max(2, min(8, (n - 1) // 10))
    fenetres = [chances_positions[:taille]] * max(0, min(taille, n) - 2)
    fenetres += [chances_positions[i:i + taille]
                 for i in range(max(1, n - taille + 1))]
    return [max(0.5, min(12.0, _ecart_type(f) if len(f) > 1 else 0.5))
            for f in fenetres][:n - 1]


def precision_globale(precisions, poids):
    """Moyenne de la moyenne ponderee et de la moyenne harmonique (lichess)."""
    if not precisions:
        return None
    poids = list(poids) + [0.5] * (len(precisions) - len(poids))
    ponderee = sum(p * w for p, w in zip(precisions, poids)) / (sum(poids) or 1.0)
    harmonique = len(precisions) / sum(1.0 / max(1e-9, p) for p in precisions)
    return round(max(0.0, min(100.0, (ponderee + harmonique) / 2.0)), 1)


# ---------------------------------------------------------------- analyseur

class AnalyseurPartie:
    """Analyse une partie en tache de fond, en commencant par le coup regarde."""

    def __init__(self, fen_initiale, coups_uci, chemin_stockfish=None,
                 puissance=None, moteur=None, suivi=False, threads=None,
                 fichier_cache=None, version_min=None):
        self.chemin = chemin_stockfish
        # Les statistiques acceptent une analyse d'avant (format 1) : elle est
        # juste, il lui manque seulement les trois meilleurs coups.
        self.version_min = VERSION_CACHE if version_min is None else int(version_min)
        # suivi = l'analyse accompagne une partie EN COURS : elle ne s'arrete
        # pas quand elle a tout vu, elle attend les coups suivants
        # (ajouter_coups). finir_le_suivi() la laisse terminer normalement.
        self.suivi = bool(suivi)
        self.threads = threads
        nom = str(puissance or PUISSANCE_PAR_DEFAUT).strip().lower()
        self.puissance = nom if nom in REGLAGES else PUISSANCE_PAR_DEFAUT
        r = REGLAGES[self.puissance]
        self.mode = r["mode"]
        self.profondeur = r["profondeur"]          # 0 en mode calcul et temps
        self.noeuds = r["noeuds"]
        self.temps_max_ms = r["temps_ms"]
        self.profondeur_min = r["profondeur_min"]
        self.effort = r["effort"]
        self.lignes_spec = r["lignes"]
        # 1 = survol, 2 = trois meilleurs coups, 3 = passe profonde (si elle
        # existe). Une position est finie a self.niveau_final.
        self.niveau_final = 3 if self.lignes_spec else 2
        # 18/10 : durees mesurees par passe et vitesse du moteur (noeuds par
        # seconde) : le temps restant affiche dans la revue.
        self._durees = {1: [], 2: [], 3: []}
        self._vitesses = []             # (noeuds, ms) des vraies recherches
        # 25/10 (t71 / t99) : duree de chaque recherche par (position, passe)
        # et debut des recherches en cours (position -> (debut, passe)).
        self._duree_de = {}
        self._depuis = {}
        self.allegees = set()           # positions sans passe profonde (inutile)
        self._moteur_fourni = moteur          # les tests passent le leur

        self.fen_initiale = fen_initiale or chess.STARTING_FEN
        self.fens, self.coups, self.sans = [], [], []
        self.trait, self.finie = [], []
        self._construire_positions([str(c) for c in (coups_uci or [])])

        n = len(self.fens)
        self.evaluations = [None] * n   # pions, point de vue des Blancs
        self.mats = [None] * n          # coups avant mat, + = les Blancs matent
        self.meilleurs = [None] * n     # meilleur coup (UCI) dans la position
        # Le meilleur coup et le deuxieme, mesures par LA MEME recherche :
        # comparer deux profondeurs differentes ne voudrait rien dire.
        self.premiers = [None] * n
        self.seconds = [None] * n
        self.niveau = [0] * n           # 0 = rien, 1 = survol, 2 = passe fine
        # 17/10 : les trois meilleurs coups de chaque position, meilleur
        # d'abord : [uci, evaluation (pions, Blancs), mat (Blancs), suite].
        self.lignes = [None] * n
        self.profondeurs = [0] * n      # profondeur VRAIMENT atteinte
        self._essais = [0] * n

        self.erreur = None
        self.en_cours = False
        self._stop = False
        self._fil = None
        # 17/10 (Julien : « enormement plus rapide ») : plusieurs moteurs
        # analysent des positions differentes en meme temps.
        self._fils = []
        self._rates = {}             # 25/10 : recherches revenues sans evaluation
        self._en_travail = set()
        # 24/10 : les moteurs qui cherchent EN CE MOMENT pour cette analyse
        # (arreter() n'interrompt qu'eux, jamais une autre analyse).
        self._moteurs_en_cours = set()
        self._verrou_choix = threading.Lock()
        self._ouvriers = 0
        self._priorite = None
        # 25/10 : _prochaine n'a rien rendu parce qu'une voisine est en cours
        # sur un autre moteur : il faut attendre, pas quitter la revue.
        self._attendre = False
        self._cache = {}
        # SickChess 17/10 (remarque de Julien : "les analyses ne sont pas bien
        # enregistrees, une nouvelle evaluation commence a chaque revue") :
        # l'analyse terminee est ecrite a cote du PGN et relue a l'ouverture.
        self.fichier_cache = None
        if fichier_cache:
            self.definir_fichier_cache(fichier_cache)

    def _construire_positions(self, coups):
        plateau = freestyle.plateau(self.fen_initiale)
        self._noter(plateau)
        for uci in coups:
            try:
                coup = chess.Move.from_uci(uci)
            except ValueError:
                break
            if coup not in plateau.legal_moves:
                break
            self.sans.append(plateau.san(coup))
            self.coups.append(uci)
            plateau.push(coup)
            self._noter(plateau)

    def _noter(self, plateau):
        self.fens.append(plateau.fen())
        self.trait.append(plateau.turn == chess.WHITE)
        self.finie.append(plateau.is_game_over())

    def nombre_de_coups(self):
        return len(self.coups)

    # ------------------------------------------------------------------ cache

    CHAMPS_CACHE = ("evaluations", "mats", "meilleurs", "premiers", "seconds",
                    "lignes", "profondeurs")

    def definir_fichier_cache(self, chemin):
        """Ou garder l'analyse. Relit le fichier s'il existe deja ; ecrit tout
        de suite si l'analyse est deja terminee."""
        self.fichier_cache = chemin
        if not chemin:
            return
        relue = False
        if os.path.exists(chemin) and not self.terminee():
            relue = self._relire_cache(chemin)
        # 17/10 : on ne reecrit PAS une analyse qu'on vient de relire. Avant, le
        # bouton « Mes erreurs » (puissance « rapide ») relisait une analyse de
        # profondeur 20 puis la reecrivait en « profondeur 16 » : la revue
        # suivante la jugeait trop faible et refaisait toute l'analyse.
        if self.terminee() and not self.suivi and not relue:
            self._ecrire_cache()

    def _relire_cache(self, chemin):
        import json
        try:
            with open(chemin, "r", encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            return False
        # 18/10 : on compare l'EFFORT (de 1 a 5), plus la profondeur : une
        # analyse a la profondeur 30 vaut une analyse en calcul fixe maximal,
        # et changer de mode dans Options ne refait pas toutes les parties.
        effort = d.get("effort") if isinstance(d, dict) else None
        if effort is None and isinstance(d, dict):
            effort = effort_d_une_profondeur(d.get("profondeur"))
        if not isinstance(d, dict) or d.get("fen") != self.fen_initiale \
                or d.get("coups") != self.coups \
                or int(effort or 0) < self.effort \
                or int(d.get("version") or 1) < self.version_min:
            # 17/10 : une analyse d'avant (sans les trois meilleurs coups ni
            # la profondeur atteinte) est refaite une fois, puis gardee.
            return False
        n = len(self.fens)
        anciens = ("lignes", "profondeurs")
        if any(len(d.get(c) or []) != n for c in self.CHAMPS_CACHE if c not in anciens):
            return False
        for champ in self.CHAMPS_CACHE:
            valeur = d.get(champ)
            if champ in anciens and (not valeur or len(valeur) != n):
                valeur = [None] * n if champ == "lignes" else [int(d.get("profondeur") or 0)] * n
            setattr(self, champ, list(valeur))
        self.profondeur_lue = int(d.get("profondeur") or 0)
        self.effort_lu = int(effort or 0)
        self.allegees = set(int(k) for k in (d.get("allegees") or []) if 0 <= int(k) < n)
        self.reglage_lu = d.get("reglage")
        self.niveau = [self.niveau_final] * n
        self._cache = {}
        print("[ANALYSE] analyse relue (%s)" % os.path.basename(chemin))
        return True

    def _ecrire_cache(self):
        if not self.fichier_cache or not self.terminee():
            return False
        import json
        d = {"fen": self.fen_initiale, "coups": list(self.coups),
             "profondeur": max(self.profondeur_atteinte(),
                               getattr(self, "profondeur_lue", 0)),
             "effort": max(self.effort, getattr(self, "effort_lu", 0)),
             "reglage": getattr(self, "reglage_lu", None) or self.puissance,
             "allegees": sorted(self.allegees),
             "version": VERSION_CACHE}
        for champ in self.CHAMPS_CACHE:
            d[champ] = list(getattr(self, champ))
        try:
            with open(self.fichier_cache, "w", encoding="utf-8") as f:
                json.dump(d, f)
            return True
        except OSError as e:
            print("[ANALYSE] analyse non enregistree : %s" % e)
            return False

    def ajouter_coups(self, coups_uci):
        """Ajoute les coups joues depuis le dernier appel (analyse en direct).

        On ajoute d'abord les cases des tableaux, puis les positions : le fil
        d'analyse ne voit jamais une position sans sa case."""
        plateau = freestyle.plateau(self.fens[-1])
        for uci in coups_uci:
            uci = str(uci)
            try:
                coup = chess.Move.from_uci(uci)
            except ValueError:
                break
            if coup not in plateau.legal_moves:
                break
            for tableau, vide in ((self.evaluations, None), (self.mats, None),
                                  (self.meilleurs, None), (self.premiers, None),
                                  (self.seconds, None), (self.niveau, 0),
                                  (self.lignes, None), (self.profondeurs, 0),
                                  (self._essais, 0)):
                tableau.append(vide)
            self.sans.append(plateau.san(coup))
            self.coups.append(uci)
            plateau.push(coup)
            self.trait.append(plateau.turn == chess.WHITE)
            self.finie.append(plateau.is_game_over())
            self.fens.append(plateau.fen())
        if not self.en_cours and not self._stop:
            self.demarrer()

    def finir_le_suivi(self):
        """La partie est finie : l'analyse se termine quand tout est vu."""
        self.suivi = False
        if not self.en_cours and not self.terminee():
            self.demarrer()
        elif self.en_cours and self._moteur_fourni is None:
            # La partie est finie : le processeur est libre, on ajoute des
            # moteurs pour finir l'analyse plus vite.
            plus = self._nombre_de_moteurs() - self._ouvriers
            if plus > 0:
                self._lancer_ouvriers(plus, premier_indice=1)

    # ------------------------------------------------------------------ pilotage

    def _nombre_de_moteurs(self):
        """1 pendant la partie (l'adversaire a besoin du processeur) ; apres,
        jusqu'a 3 moteurs selon les coeurs. Stockfish monte mal en threads :
        trois moteurs sur des positions differentes vont bien plus vite qu'un
        seul moteur avec tous les coeurs."""
        if self._moteur_fourni is not None or self.suivi or _petit_pc():
            return 1
        coeurs = os.cpu_count() or 2
        return 1 if coeurs < 4 else (2 if coeurs < 8 else 3)

    def _threads_par_moteur(self, combien=None):
        """Threads de CHAQUE moteur d'analyse.

        18/10 (13) - BUG trouve dans le journal de Julien (revue de 35 min) :
        le nombre de threads dependait du nombre de moteurs DEJA lances au
        moment ou chacun demarrait. Le premier se croyait seul (11 threads),
        le deuxieme en voyait deux (6), le troisieme trois (4) : 21 threads
        pour 12 processeurs logiques, qui se marchaient dessus. Maintenant on
        partage selon le nombre de moteurs PREVUS : 3 x 4 = 12, jamais plus.
        'combien' est garde pour les anciens appels, il ne sert plus."""
        coeurs = os.cpu_count() or 2
        if self.suivi:
            # Pendant la partie : un seul moteur, la moitie des coeurs
            # (l'adversaire a besoin du reste) ; un seul coeur sur un petit PC.
            if _petit_pc():
                return 1
            return self.threads or max(1, coeurs // 2)
        prevus = self._moteurs_prevus()
        if prevus == 1:
            return self.threads or max(1, coeurs - 1)
        return max(1, coeurs // prevus)

    def _lancer_ouvriers(self, combien, premier_indice=0):
        for n in range(combien):
            indice = premier_indice + n
            with self._verrou_choix:
                self._ouvriers += 1
            fil = threading.Thread(target=self._travailler, args=(indice,),
                                   daemon=True)
            self._fils.append(fil)
            if self._fil is None:
                self._fil = fil
            fil.start()

    def demarrer(self):
        if self.en_cours or (self.terminee() and not self.suivi):
            return False
        self._stop = False
        self.en_cours = True
        self._fils = [f for f in self._fils if f.is_alive()]
        self._fil = None
        self._lancer_ouvriers(self._nombre_de_moteurs())
        return True

    def arreter(self, attendre=0.3):
        """24/10 (« quitter une partie est long ») : avant, les recherches en
        cours continuaient jusqu'au bout (plusieurs secondes a 100 % des
        processeurs, apres avoir quitte la partie) et on attendait 0,3 s PAR
        fil. Maintenant on interrompt Stockfish (« stop » : leur resultat,
        incomplet, n'est pas garde) et on attend 0,3 s AU TOTAL."""
        self._stop = True
        for moteur in list(self._moteurs_en_cours):
            interrompre = getattr(moteur, "interrompre", None)
            if interrompre is not None:
                try:
                    interrompre()
                except Exception:
                    pass
        limite = time.time() + attendre
        for fil in list(self._fils):
            if fil.is_alive():
                fil.join(max(0.0, limite - time.time()))

    def prioriser(self, index_coup):
        """Le joueur regarde le coup index_coup (-1 = position de depart)."""
        self._priorite = int(index_coup)

    def _prochaine(self):
        n = len(self.fens)
        p = self._priorite
        occupe = self._en_travail
        self._attendre = False
        if p is not None:
            # Le coup regarde a besoin des positions p et p+1 ; p+2 donne le
            # meilleur coup de la position suivante. 18/10 (16) : les quatre
            # voisines passent d'abord l'analyse rapide (pour savoir s'il faut
            # verifier), puis la verification.
            # 25/10 (t71) : la passe des 3 coups va jusqu'a p-2 et p+3, les
            # voisines de p-1 et p+2 : sans elles, leur verdict restait
            # incertain et elles etaient verifiees pour rien.
            for niveau in range(1, self.niveau_final + 1):
                autour = (p + 1, p, p + 2, p - 1, p + 3, p - 2) \
                    if niveau < self.niveau_final else (p + 1, p, p + 2, p - 1)
                for k in autour:
                    if 0 <= k < n and self.niveau[k] < niveau and k not in occupe:
                        choix = self._voisine_d_abord(k, niveau)
                        if choix is not None:
                            return choix
        for niveau in range(1, self.niveau_final + 1):
            for k in range(min(n, len(self.niveau))):
                if self.niveau[k] < niveau and k not in occupe:
                    choix = self._voisine_d_abord(k, niveau)
                    if choix is not None:
                        return choix
        return None

    def _voisine_d_abord(self, k, niveau):
        """25/10 (t71, revue lente) : la verification de k attend la passe des
        3 coups de ses deux voisines (sans elles, _coup_sur ne sait pas et la
        position etait verifiee « par accident » : 9 positions au lieu de 6,
        111 s au lieu de 90 s). On fait d'abord la voisine si elle est libre ;
        sinon (un autre moteur la fait) on passe a une autre position."""
        if niveau < self.niveau_final or not self.lignes_spec:
            return k, niveau
        # 25/10 : bornee par les positions construites (ajouter_coups agrandit
        # niveau avant finie et fens, sans le verrou).
        n = min(len(self.fens), len(self.finie), len(self.niveau))
        for j in (k - 1, k + 1):
            if 0 <= j < n and self.niveau[j] < 2 and not self.finie[j]:
                if j in self._en_travail:
                    self._attendre = True
                    return None
                return j, 2
        return k, niveau

    def _moteur(self, indice=0, combien=1):
        if self._moteur_fourni is not None:
            return self._moteur_fourni
        import moteurs
        return moteurs.moteur_d_analyse_n(
            indice, self.chemin, threads=self._threads_par_moteur(combien),
            # 18/10 : le total (6 Go) est partage entre TOUS les moteurs prevus
            # apres la partie, meme pendant la partie ou un seul tourne : ceux
            # qu'on ajoute a la fin ne font pas depasser les 6 Go.
            hash_mb=hachage_total_mo() // max(1, self._moteurs_prevus()))

    def _moteurs_prevus(self):
        """Le nombre de moteurs d'analyse une fois la partie finie."""
        if self._moteur_fourni is not None or _petit_pc():
            return 1
        coeurs = os.cpu_count() or 2
        return 1 if coeurs < 4 else (2 if coeurs < 8 else 3)

    def _travailler(self, indice=0):
        try:
            moteur = self._moteur(indice, max(1, self._ouvriers))
            if moteur is None:
                if indice == 0:
                    raise RuntimeError("Stockfish n'a pas demarre")
                return                         # un moteur de renfort en moins
            while not self._stop:
                with self._verrou_choix:
                    suivant = self._prochaine()
                    attendre = self._attendre
                    if suivant is not None:
                        self._en_travail.add(suivant[0])
                if suivant is None:
                    # 25/10 : un renfort attend aussi la voisine prise par un
                    # autre moteur (avant, il quittait : le moteur 0 finissait seul).
                    if self.suivi or attendre or (self._en_travail and indice == 0):
                        time.sleep(0.15)      # on attend le coup suivant
                        continue
                    break
                if self._moteur_fourni is None and not self._vivant(moteur):
                    # 25/10 : moteur ferme sous nos pieds (renfort libere par
                    # l'analyse precedente au moment ou celle-ci demarrait,
                    # Stockfish qui ne repondait plus) : on en reprend un neuf.
                    moteur = self._moteur(indice, max(1, self._ouvriers))
                    if moteur is None:
                        with self._verrou_choix:
                            self._en_travail.discard(suivant[0])
                        if indice == 0:
                            raise RuntimeError("Stockfish n'a pas redemarre")
                        return
                try:
                    self._analyser(moteur, *suivant)
                finally:
                    with self._verrou_choix:
                        self._en_travail.discard(suivant[0])
        except Exception as e:
            self.erreur = str(e)[:80]
            print("[ANALYSE] impossible : %s" % e)
        finally:
            with self._verrou_choix:
                self._ouvriers -= 1
                dernier = self._ouvriers <= 0
            if dernier:
                self.en_cours = False
                if not self._stop and not self.suivi:
                    self._ecrire_cache()
                    self._liberer_les_renforts()

    @staticmethod
    def _vivant(moteur):
        try:
            return bool(moteur.est_vivant())
        except Exception:
            return True                        # moteur de test sans est_vivant

    def _liberer_les_renforts(self):
        """23/10 (surveillance) : l'analyse finie, les moteurs de renfort
        gardaient leur memoire jusqu'a la fermeture du jeu."""
        if self._moteur_fourni is not None or not self.terminee():
            return
        try:
            import moteurs
            moteurs.liberer_les_renforts(self._moteurs_prevus())
        except Exception as e:
            print("[ANALYSE] moteurs de renfort non fermes : %s" % e)

    def _analyser(self, moteur, k, niveau):
        if self.finie[k]:
            # Mat ou nulle : rien a demander au moteur.
            if freestyle.plateau(self.fens[k]).is_checkmate():
                self.evaluations[k] = -EVAL_MAT if self.trait[k] else EVAL_MAT
                self.mats[k] = 0
            else:
                self.evaluations[k] = 0.0
            self.lignes[k] = []
            self.profondeurs[k] = self.profondeur or self.profondeur_min
            self.niveau[k] = self.niveau_final
            return
        final = niveau >= self.niveau_final
        if final and self.lignes_spec and self.niveau[k] >= 2 \
                and self._inutile_de_creuser(k):
            # 18/10 : rien a gagner a creuser (partie jouee, mat, theorie) :
            # le resultat de la passe des trois coups devient definitif.
            self.allegees.add(k)
            self.niveau[k] = self.niveau_final
            return
        # Avant de chercher : le bon nombre de threads (le moteur gardait
        # celui de la partie quand la partie se termine).
        if self._moteur_fourni is None and hasattr(moteur, "regler_threads"):
            try:
                moteur.regler_threads(self._threads_par_moteur())
            except Exception:
                pass
        if niveau <= 1:
            spec, lignes = (PROFONDEUR_SURVOL, 0, TEMPS_SURVOL_MS), 1
        elif not final:                      # les trois meilleurs coups
            spec, lignes = self.lignes_spec, LIGNES_FINES
        else:
            # Refaite (essai 1) : deux fois plus de temps. Le budget de noeuds,
            # lui, ne change pas : c'est ce qui rend le calcul fixe juste.
            spec = (self.profondeur, self.noeuds,
                    self.temps_max_ms * (1 + self._essais[k]))
            lignes = 1 if self.lignes_spec else LIGNES_FINES
        details = self._chercher(moteur, self.fens[k], spec, lignes,
                                 min(niveau, self.niveau_final), k)
        if self._stop:
            # 24/10 : recherche interrompue par arreter() : resultat incomplet,
            # on ne le garde pas (la position sera refaite si l'analyse reprend).
            return
        if not details or _en_pions(details.get("evaluation"), details.get("mat")) is None:
            # 25/10 : recherche revenue SANS evaluation (Stockfish ferme ou relance
            # pendant la recherche : il renvoie un dernier « bestmove » vide).
            # Avant, la position etait notee faite sans evaluation : pastille
            # absente dans la revue. Maintenant elle est refaite (un moteur neuf
            # si le sien est ferme, voir _travailler), 3 fois au plus.
            self._rates[k] = self._rates.get(k, 0) + 1
            if self._rates[k] <= 3:
                return
        if details:
            signe = 1.0 if self.trait[k] else -1.0
            classees = lignes_du_moteur(self.fens[k], details)
            if final and lignes == 1 and classees and self.lignes[k]:
                # Passe profonde : son meilleur coup passe en tete, avec son
                # evaluation ; les autres coups gardent celle de la passe a 22.
                profond = classees[0]
                autres = [l for l in self.lignes[k] if l[0] != profond[0]]
                classees = [profond] + autres[:LIGNES_FINES - 1]
            if classees:
                self.lignes[k] = classees
            atteinte = int(details.get("profondeur") or 0)
            # Profondeur minimale : a 2 pres en mode profondeur (comme avant),
            # stricte en mode temps (« jamais sous 26 »), aucune en calcul fixe.
            minimum = 0
            if self.mode == "profondeur":
                minimum = self.profondeur_min - TOLERANCE_PROFONDEUR
            elif self.mode == "temps":
                minimum = self.profondeur_min
            if final and atteinte < minimum \
                    and self._essais[k] < 1 and not self._stop:
                # Pas assez profond (l'ordinateur jouait ?) : on garde ce
                # resultat pour la courbe et on recommence avec plus de temps.
                self._essais[k] += 1
                niveau = self.niveau_final - 1
                final = False
            if final or not self.profondeurs[k]:
                self.profondeurs[k] = atteinte
            premier = _en_pions(details.get("evaluation"), details.get("mat"))
            if premier is not None:
                self.evaluations[k] = signe * premier
                mat = details.get("mat")
                self.mats[k] = int(signe * mat) if mat is not None else None
            if details.get("coup"):
                self.meilleurs[k] = details["coup"]
            second = _en_pions(details.get("second_evaluation"),
                               details.get("second_mat"))
            # L'ecart entre le 1er et le 2e coup se mesure dans UNE recherche
            # (la passe a trois coups) : la passe profonde n'y touche pas.
            if premier is not None and second is not None and lignes > 1:
                self.premiers[k] = signe * premier
                self.seconds[k] = signe * second
        self.niveau[k] = max(self.niveau[k], niveau)

    # ------------------------------------------------------------------ avancement

    def _profondeurs_vues(self):
        """Les profondeurs vraiment atteintes par la passe finale (sans les
        positions finies ni celles qu'on n'a pas eu besoin de creuser)."""
        return [p for k, (p, fini) in enumerate(zip(self.profondeurs, self.finie))
                if p and not fini and k not in self.allegees]

    def _coup_sur(self, i, niveau_min=2):
        """La pastille du coup i est-elle SURE avec l'analyse rapide ?
        True / False, ou None tant que les deux positions ne sont pas passees.
        Pas sure quand la perte est a moins de MARGE_VERDICT points d'un seuil
        de pastille (5 / 10 / 20), ou d'un seuil en pions, ou quand le coup
        peut etre « Tres bien », « Brillant » ou « Manque » : la, une analyse
        plus profonde peut changer le verdict ; ailleurs, non (de 22 a 30,
        l'evaluation bouge de 0,05 pion : 1 a 2 points de chances).
        niveau_min=1 (25/10, temps restant) : un avis provisoire des le survol."""
        if not 0 <= i < len(self.coups):
            return True
        for k in (i, i + 1):
            if self.niveau[k] < niveau_min and not self.finie[k]:
                return None
        avant, apres = self.evaluations[i], self.evaluations[i + 1]
        if avant is None or apres is None:
            return False
        blancs = self.trait[i]

        def du_joueur(v):
            c = annotations.chances_de_gagner(v)
            return c if blancs else 100.0 - c

        perte = max(0.0, du_joueur(avant) - du_joueur(apres))
        m = MARGE_VERDICT
        for seuil in (annotations.SEUIL_IMPRECISION, annotations.SEUIL_ERREUR,
                      annotations.SEUIL_GAFFE):
            if abs(perte - seuil) < m:
                return False
        signe = 1.0 if blancs else -1.0
        borne = lambda v: max(-BORNE_PIONS, min(BORNE_PIONS, signe * v))
        perte_pions = max(0.0, borne(avant) - borne(apres))
        for seuil in (annotations.PIONS_IMPRECISION, annotations.PIONS_ERREUR):
            if abs(perte_pions - seuil) < MARGE_PIONS:
                return False
        if abs(borne(apres) - annotations.TOUJOURS_ECRASANT) < MARGE_PIONS:
            return False
        if self.premiers[i] is not None and self.seconds[i] is not None \
                and perte <= annotations.PERTE_QUASI_MEILLEUR + m:
            ecart = du_joueur(self.premiers[i]) - du_joueur(self.seconds[i])
            if abs(ecart - annotations.ECART_SEUL_COUP) < m:
                return False                    # « Tres bien » ou pas ?
        if perte <= annotations.PERTE_QUASI_MEILLEUR + m:
            try:
                if annotations.est_un_sacrifice(freestyle.plateau(self.fens[i]),
                                                chess.Move.from_uci(self.coups[i])):
                    return False                # « Brillant » ou pas ?
            except Exception:
                return False
        if abs(du_joueur(avant) - annotations.CHANCES_GAGNANTES) < m \
                and perte >= annotations.SEUIL_ERREUR - m:
            return False                        # « Manque » ou pas ?
        return True

    def _verdicts_surs(self, k, niveau_min=2):
        """Les deux coups qui touchent la position k ont une pastille sure."""
        return self._coup_sur(k - 1, niveau_min) is True \
            and self._coup_sur(k, niveau_min) is True

    def _inutile_de_creuser(self, k, niveau_min=2):
        """La passe profonde ne changerait rien pour la position k :
          - la partie y est jouee (au moins 8 pions d'avance, ou un mat) :
            les chances de gagner sont deja a 95 % et plus, aucune pastille ne
            peut changer (mesure du 18/10 : de 22 a 30, l'evaluation bouge de
            moins de 0,3 pion dans ces positions) ;
          - on est encore dans la theorie (le coup qui y mene et celui qu'on y
            joue sont des coups de livre : pastille « Theorique » de toute
            facon).
        C'est la que partaient la moitie des calculs sur une partie comme
        celle contre dragondu5 (-8 des le coup 11)."""
        if self.mats[k] is not None:
            return True
        # 18/10 (16) : plus de raccourci « partie jouee » (8 pions) : la regle
        # du materiel perdu (1 pion = Imprecision) joue justement la. Mesure
        # sur la partie contre dragondu5 : 12...d4 passait d'Imprecision a
        # Excellent. Ces positions passent maintenant par _coup_sur, qui
        # surveille aussi les seuils en pions.
        # 18/10 (16) : en calcul fixe, on ne verifie que ce qui peut changer.
        if self.mode == "calcul" and self._verdicts_surs(k, niveau_min):
            return True
        try:
            import ouvertures
            # Le livre ne connait que les parties parties du debut.
            if self.fen_initiale == chess.STARTING_FEN and k < len(self.coups) \
                    and ouvertures.est_un_coup_de_livre(self.sans, k) \
                    and (k == 0 or ouvertures.est_un_coup_de_livre(self.sans, k - 1)):
                return True
        except Exception:
            pass
        return False

    def _chercher(self, moteur, fen, spec, lignes, niveau, k=None):
        """Une recherche de Stockfish ; note sa duree et sa vitesse."""
        profondeur, noeuds, temps = spec
        debut = time.time()
        if k is not None:
            self._depuis[k] = (debut, niveau)
        self._moteurs_en_cours.add(moteur)
        try:
            if noeuds:
                try:
                    details = moteur.analyser_position(fen, profondeur, temps,
                                                       lignes=lignes, noeuds=noeuds)
                except TypeError:
                    # Un moteur de test qui ne connait pas les noeuds.
                    details = moteur.analyser_position(fen, profondeur or 22, temps,
                                                       lignes=lignes)
            else:
                details = moteur.analyser_position(fen, profondeur, temps, lignes=lignes)
        finally:
            self._moteurs_en_cours.discard(moteur)
            self._depuis.pop(k, None)
        duree = time.time() - debut
        self._durees.setdefault(niveau, []).append(duree)
        if k is not None:
            self._duree_de[(k, niveau)] = duree
        # 18/10 : la vitesse ne se mesure que sur les vraies recherches (au
        # moins un million de noeuds) : les toutes petites (survol) demarrent
        # lentement et faisaient annoncer un temps restant trop long.
        if details and (details.get("noeuds") or 0) >= 1000000 \
                and details.get("temps_ms"):
            self._vitesses.append((details["noeuds"], details["temps_ms"]))
        for liste in [self._durees[niveau], self._vitesses]:
            if len(liste) > 60:
                del liste[:-30]
        return details

    def temps_restant(self):
        """Secondes restantes estimees pour finir l'analyse, ou None tant
        qu'on ne peut pas le dire (au moins deux positions mesurees, ou la
        vitesse du moteur en mode calcul)."""
        if not self.en_cours or self.suivi:
            return None
        # Calcul couteux (l'affichage le demande a chaque image) : une fois
        # par seconde suffit.
        maintenant = time.time()
        memo = getattr(self, "_memo_reste", None)
        if memo is not None and maintenant - memo[0] < 1.0:
            return memo[1]
        reste = self._calculer_temps_restant()
        self._memo_reste = (maintenant, reste)
        return reste

    def _calculer_temps_restant(self):
        """25/10 (t71 / t99, « temps annonce faux » : 17 coups en 7 min) : avant,
        le calcul fixe prenait la vitesse annoncee par Stockfish et jamais les
        durees vraiment mesurees, supposait 30 % de positions a verifier,
        comptait les recherches en cours pour entieres et divisait la fin par
        le nombre de moteurs meme quand il en restait moins a faire. Maintenant
        chaque recherche qui reste a sa duree prevue (la passe profonde d'une
        position = sa passe des trois coups x le rapport mesure), on devine
        des le survol les positions a verifier, les recherches en cours ne
        comptent que ce qui leur reste et les moteurs se partagent le travail
        comme pour de vrai."""
        ouvriers = max(1, self._ouvriers)
        final = self.niveau_final
        n = len(self.niveau)
        duree_de = dict(self._duree_de)
        en_cours = dict(self._depuis)
        maintenant = time.time()
        vitesse = None
        if len(self._vitesses) >= 2:
            recentes = self._vitesses[-20:]
            vitesse = sum(n for n, _t in recentes) * 1000.0 / max(
                1, sum(t for _n, t in recentes))

        def moyenne(niveau):
            mesures = (self._durees.get(niveau) or [])[-20:]
            return sum(mesures) / len(mesures) if mesures else None

        def sans_mesure(niveau):
            """Duree d'une recherche de cette passe quand rien n'est mesure."""
            if niveau == final:
                spec = (self.profondeur, self.noeuds, self.temps_max_ms)
            elif niveau == 1:
                return TEMPS_SURVOL_MS / 1000.0
            else:
                spec = self.lignes_spec
            if spec[1] and vitesse:
                return spec[1] / vitesse             # calcul fixe : previsible
            if self.mode == "temps" and niveau == final:
                return self.temps_max_ms / 1000.0
            return None

        # Passe profonde / passe des trois coups, pour la meme position : le
        # rapport mesure, ou celui des quantites de calcul (calcul fixe).
        rapport = None
        if final == 3:
            paires = [(duree_de[(k, 2)], duree_de[(k, 3)]) for k in range(n)
                      if (k, 2) in duree_de and (k, 3) in duree_de][-20:]
            if len(paires) >= 2:
                rapport = sum(b for _a, b in paires) / max(1e-6, sum(a for a, _b in paires))
            elif self.noeuds and self.lignes_spec and self.lignes_spec[1]:
                rapport = self.noeuds / float(self.lignes_spec[1])
            elif moyenne(3) and moyenne(2):
                rapport = moyenne(3) / moyenne(2)

        def prevue(k, niveau):
            if niveau == 3 and rapport:
                if (k, 2) in duree_de:
                    return duree_de[(k, 2)] * rapport
                if moyenne(2):
                    return moyenne(2) * rapport
            return moyenne(niveau) or sans_mesure(niveau)

        # Ce qui reste aux recherches en cours.
        charges = []
        for k, (debut, niveau) in en_cours.items():
            d = prevue(k, niveau)
            if d is None:
                return None
            charges.append(max(0.0, d - (maintenant - debut)))
        # Les recherches a faire, dans l'ordre ou les moteurs les prennent.
        surveillees = [k for k in range(n) if self.niveau[k] >= 1 and not self.finie[k]]
        taches = []
        for niveau in range(1, final + 1):
            a_creuser = None
            if niveau == final and final > 2:
                # Passe profonde : seules les positions a verifier comptent,
                # devinees avec la meilleure evaluation deja connue (survol
                # compris). Sans survol : la meme part qu'ailleurs.
                a_creuser = set(k for k in surveillees
                                if self.niveau[k] < final
                                and not self._inutile_de_creuser(k, niveau_min=1))
                faites = sum(1 for k in surveillees if self.niveau[k] >= final
                             and k not in self.allegees)
                part = (len(a_creuser) + faites) / float(len(surveillees)) \
                    if surveillees else 0.3
            for k in range(n):
                if self.finie[k] or self.niveau[k] >= niveau \
                        or en_cours.get(k, (0, 0))[1] == niveau:
                    continue
                poids = 1.0
                if a_creuser is not None:
                    if self.niveau[k] >= 1:
                        if k not in a_creuser:
                            continue
                    else:
                        poids = part
                d = prevue(k, niveau)
                if d is None:
                    return None
                taches.append(d * poids)
        charges = sorted(charges)[:ouvriers]
        charges += [0.0] * (ouvriers - len(charges))
        for d in taches:
            i = charges.index(min(charges))
            charges[i] += d
        return max(charges)

    def limites_variante(self):
        """(profondeur, noeuds, temps_ms) pour les conseils d'une variante :
        le reglage de la passe des trois meilleurs coups (rapide, puisqu'on
        attend la reponse), ou celui de la passe finale s'il n'y en a pas."""
        if self.lignes_spec:
            return self.lignes_spec
        return (self.profondeur, self.noeuds, self.temps_max_ms)

    def texte_temps_restant(self):
        secondes = self.temps_restant()
        if secondes is None:
            return ""
        if secondes < 60:
            return "moins d'une minute"
        return "environ %d min" % int(round(secondes / 60.0))

    def description(self):
        """Le reglage, en clair (en-tete de l'export, fin d'analyse)."""
        vues = self._profondeurs_vues()
        bas, haut = (min(vues), max(vues)) if vues else (self.profondeur_min,) * 2
        if self.mode == "calcul":
            verifiees = sum(1 for k in range(len(self.fens))
                            if not self.finie[k] and k not in self.allegees)
            return ("%d millions de calculs par position vérifiée (%d sur %d), "
                    "%d millions pour les autres, profondeur %d à %d") % (
                self.noeuds // 1000000, verifiees, len(self.fens),
                (self.lignes_spec or (0, 0, 0))[1] // 1000000, bas, haut)
        if self.mode == "temps":
            return "%d s par position, profondeur %d à %d" % (
                self.temps_max_ms // 1000, bas, haut)
        return "profondeur %d" % bas

    def avancement(self):
        """(part du survol faite, part de la passe fine faite), de 0 a 1."""
        n = float(len(self.fens) or 1)
        return (sum(1 for v in self.niveau if v >= 1) / n,
                sum(1 for v in self.niveau if v >= self.niveau_final) / n)

    def avancement_lignes(self):
        n = float(len(self.fens) or 1)
        return sum(1 for v in self.niveau if v >= 2) / n

    def survol_fini(self):
        return all(v >= 1 for v in self.niveau)

    def terminee(self):
        return all(v >= self.niveau_final for v in self.niveau)

    def reprendre_de(self, autre):
        """25/10 (p25) : reprend le travail d'une autre analyse de la MEME
        partie (l'analyse de fond, mise en pause quand la revue s'ouvre) au lieu
        de tout recommencer. Seulement si elle est au moins aussi forte.
        Renvoie le nombre de positions reprises."""
        if autre is None or autre is self or autre.fens != self.fens \
                or autre.effort < self.effort or autre.niveau_final != self.niveau_final:
            return 0
        reprises = 0
        for k in range(len(self.fens)):
            if autre.niveau[k] > self.niveau[k]:
                for champ in self.CHAMPS_CACHE:
                    getattr(self, champ)[k] = getattr(autre, champ)[k]
                self.niveau[k] = autre.niveau[k]
                if k in autre.allegees:
                    self.allegees.add(k)
                reprises += 1
        if reprises:
            self._cache = {}
            if self.terminee():
                self._ecrire_cache()
        return reprises

    def texte_avancement(self):
        if self.erreur:
            return "Analyse impossible : %s" % self.erreur
        survol, fine = self.avancement()
        if fine >= 1.0:
            if self.mode == "profondeur":
                return "Analyse terminée (profondeur %d)" % self.profondeur_atteinte()
            vues = self._profondeurs_vues()
            bas, haut = (min(vues), max(vues)) if vues else (self.profondeur_min,) * 2
            return "Analyse terminée (profondeur %d à %d)" % (bas, haut)
        if survol < 1.0:
            texte = "Analyse rapide... %d %%" % int(survol * 100)
        elif self.niveau_final == 3 and self.avancement_lignes() < 1.0:
            texte = "Meilleurs coups... %d %%" % int(self.avancement_lignes() * 100)
        elif self.mode == "profondeur":
            texte = "Analyse profondeur %d... %d %%" % (self.profondeur, int(fine * 100))
        else:
            texte = "Analyse fine... %d %%" % int(fine * 100)
        # 18/10 : le temps restant, pour que la duree de la revue soit connue.
        reste = self.temps_restant()
        if reste is None:
            return texte
        if reste < 60:
            return texte + "  ·  moins d'une minute"
        return texte + "  ·  environ %d min" % int(round(reste / 60.0))

    def profondeur_atteinte(self):
        """La plus petite profondeur vraiment atteinte (honnete : c'est la
        position la moins bien analysee qui compte)."""
        vues = self._profondeurs_vues()
        return min(vues) if vues else (self.profondeur or self.profondeur_min)

    # ------------------------------------------------------------------ lecture

    @staticmethod
    def texte_d_une_evaluation(evaluation, mat):
        if mat is not None:
            if mat == 0:
                return "Mat"
            return ("M%d" if mat > 0 else "-M%d") % abs(mat)
        if evaluation is None:
            return "..."
        return "%+.2f" % evaluation

    def meilleurs_coups(self, k, maximum=3):
        """Les meilleurs coups de la position k : le meilleur, puis ceux qui
        valent presque autant (SEUIL_EQUIVALENT). Liste de dictionnaires
        {uci, san, evaluation, mat, texte, suite_san}, meilleur d'abord."""
        if not 0 <= k < len(self.fens) or self.finie[k]:
            return []
        lignes = self.lignes[k] or []
        if not lignes and self.meilleurs[k]:
            lignes = [[self.meilleurs[k], self.evaluations[k], self.mats[k], []]]
        return meilleurs_depuis_lignes(self.fens[k], lignes, maximum)



    def evaluation(self, k):
        if 0 <= k < len(self.evaluations):
            return self.evaluations[k]
        return None

    def evaluation_connue(self, k):
        """La derniere evaluation connue jusqu'a k (la barre ne saute pas a 0)."""
        for j in range(min(k, len(self.evaluations) - 1), -1, -1):
            if self.evaluations[j] is not None:
                return self.evaluations[j]
        return 0.0

    def texte_evaluation(self, k):
        """'+1.37', '-0.42', 'M3', '-M2', 'Mat' ou '...'."""
        if not 0 <= k < len(self.evaluations):
            return ""
        return self.texte_d_une_evaluation(self.evaluations[k], self.mats[k])

    def san_du_meilleur(self, k):
        """Le meilleur coup de la position k, en notation courte."""
        if not 0 <= k < len(self.meilleurs) or not self.meilleurs[k]:
            return None
        try:
            return freestyle.plateau(self.fens[k]).san(
                chess.Move.from_uci(self.meilleurs[k]))
        except Exception:
            return None

    def coup_de_livre(self, i):
        """Le coup i est-il de la theorie d'ouverture ? 24/10 (p30, banque de
        positions) : seulement pour une partie partie de la position initiale.
        Avant, le 1er coup d'une partie commencee ailleurs (« e3 » au milieu
        d'une partie) etait pris pour le 1.e3 d'une ouverture : une gaffe
        devenait « Theorique »."""
        if freestyle.plateau(self.fen_initiale).board_fen() != chess.Board().board_fen():
            return False
        try:
            import ouvertures
            return ouvertures.est_un_coup_de_livre(self.sans, i)
        except Exception:
            return False

    def detail(self, i):
        """Tout ce qu'on sait du coup i. Toujours un dictionnaire."""
        if not 0 <= i < len(self.coups):
            return {"index": i, "pret": False, "note": None}
        cle = (i, self.niveau[i], self.niveau[i + 1],
               self.evaluations[i], self.evaluations[i + 1])
        infos = self._cache.get(i)
        if infos is not None and infos["_cle"] == cle:
            return infos
        blancs = self.trait[i]
        infos = {
            "_cle": cle, "index": i, "uci": self.coups[i], "san": self.sans[i],
            "par_les_blancs": blancs, "numero": i // 2 + 1,
            "pret": False, "note": None, "perte": None, "precision": None,
            "evaluation_avant": self.evaluations[i],
            "evaluation_apres": self.evaluations[i + 1],
            "chances_avant": None,
            "meilleur_uci": self.meilleurs[i],
            "meilleur_san": self.san_du_meilleur(i),
            "est_le_meilleur": False,
            "texte_evaluation": self.texte_evaluation(i + 1),
        }
        avant, apres = self.evaluations[i], self.evaluations[i + 1]
        # SickChess 17/10 (remarque de Julien : "les pastilles doivent etre
        # justes et pas modifiees") : une pastille ne s'affiche qu'une fois les
        # deux positions analysees en profondeur. Le survol rapide sert a la
        # courbe et a la barre, plus aux pastilles : elles ne changent plus.
        if avant is not None and apres is not None \
                and self.niveau[i] >= self.niveau_final \
                and self.niveau[i + 1] >= self.niveau_final:
            infos.update(self._juger(i, avant, apres, blancs))
        self._cache[i] = infos
        return infos

    def _juger(self, i, avant, apres, blancs):
        joue = self.coups[i]
        meilleur = self.meilleurs[i]
        plateau = freestyle.plateau(self.fens[i])
        coup = chess.Move.from_uci(joue)

        def du_joueur(evaluation):
            c = annotations.chances_de_gagner(evaluation)
            return c if blancs else 100.0 - c

        chances_avant, chances_apres = du_joueur(avant), du_joueur(apres)
        perte = max(0.0, chances_avant - chances_apres)
        # La meme perte, en PIONS (point de vue du joueur, bornee a 15) : une
        # dame donnee reste une gaffe meme quand les chances de gagner
        # bougeaient peu (position deja tres desequilibree).
        signe = 1.0 if blancs else -1.0
        borne = lambda v: max(-BORNE_PIONS, min(BORNE_PIONS, signe * v))
        perte_pions = max(0.0, borne(avant) - borne(apres))
        apres_pions = borne(apres)
        ecart = None
        if self.premiers[i] is not None and self.seconds[i] is not None:
            ecart = max(0.0, du_joueur(self.premiers[i])
                        - du_joueur(self.seconds[i]))
        theorique = self.coup_de_livre(i)
        dernier = chess.Move.from_uci(self.coups[i - 1]) if i > 0 else None
        est_le_meilleur = bool(meilleur) and meilleur == joue
        if not est_le_meilleur and self.lignes[i]:
            # Deux coups de meme valeur : le coup joue est AUSSI un meilleur coup.
            meilleure = du_joueur(self.lignes[i][0][1])
            for uci, valeur, _mat, _suite in self.lignes[i][1:]:
                if uci == joue and meilleure - du_joueur(valeur) <= SEUIL_MEME_VALEUR:
                    est_le_meilleur = True
        note = annotations.classer(
            perte, est_le_meilleur,
            annotations.est_un_sacrifice(plateau, coup),
            theorique=theorique, chances_avant=chances_avant,
            chances_apres=chances_apres, ecart_second=ecart,
            evident=annotations.coup_evident(plateau, coup, dernier),
            meilleur_connu=bool(meilleur),
            perte_pions=perte_pions, apres_pions=apres_pions)
        # La precision du coup, mesuree EXACTEMENT comme lichess (evaluations
        # bornees a 10 pions) : on peut comparer avec lichess et chess.com.
        lc_avant, lc_apres = chances_lichess(avant), chances_lichess(apres)
        if not blancs:
            lc_avant, lc_apres = 100.0 - lc_avant, 100.0 - lc_apres
        return {"pret": True, "note": note, "perte": perte,
                "chances_avant": chances_avant,
                "perte_lichess": max(0.0, lc_avant - lc_apres),
                "precision": precision_du_coup(lc_avant - lc_apres),
                "est_le_meilleur": est_le_meilleur}

    def notes(self):
        """La pastille de chaque coup (None tant qu'il n'est pas juge)."""
        return [self.detail(i)["note"] for i in range(len(self.coups))]

    def rapport(self):
        """Precision, pastilles par camp et moments cles de la partie."""
        camps = {}
        tous = [self.detail(i) for i in range(len(self.coups))]
        # Les poids de lichess : chances (Blancs) de TOUTES les positions.
        chances, derniere = [], 50.0
        for v in self.evaluations:
            c = chances_lichess(v)
            derniere = derniere if c is None else c
            chances.append(derniere)
        poids = poids_lichess(chances)
        for nom, blancs in (("blancs", True), ("noirs", False)):
            juges = [d for d in tous if d["pret"] and d["par_les_blancs"] == blancs]
            compte = dict((cle, 0) for cle in annotations.ORDRE)
            for d in juges:
                if d["note"] in compte:
                    compte[d["note"]] += 1
            camps[nom] = {
                "coups": len(juges),
                "precision": precision_globale(
                    [d["precision"] for d in juges],
                    [poids[d["index"]] if d["index"] < len(poids) else 0.5
                     for d in juges]),
                "pastilles": compte,
            }
        graves = [d for d in tous if d["pret"]
                  and d["note"] in ("gaffe", "erreur", "manque")]
        graves.sort(key=lambda d: -d["perte"])
        camps["moments_cles"] = sorted(graves[:NOMBRE_MOMENTS_CLES],
                                       key=lambda d: d["index"])
        return camps


def lignes_du_moteur(fen, details):
    """Les lignes classees d'une reponse du moteur, au format de l'analyse :
    [uci, evaluation (pions, Blancs), mat (Blancs), suite], meilleure d'abord."""
    signe = 1.0 if freestyle.plateau(fen).turn == chess.WHITE else -1.0
    classees = []
    for ligne in (details or {}).get("lignes") or []:
        v = _en_pions(None if ligne.get("cp") is None else ligne["cp"] / 100.0,
                      ligne.get("mat"))
        if v is None or not ligne.get("coup"):
            continue
        m = ligne.get("mat")
        classees.append([ligne["coup"], signe * v,
                         int(signe * m) if m is not None else None,
                         list(ligne.get("suite") or [])[:8]])
    return classees


# 23/10 (banc d'essai) : la revue demandait les meilleurs coups deux fois par
# image (notation des coups + suites). Meme position et memes lignes = meme
# reponse : on la garde (cle = la position et les lignes elles-memes).
_MEILLEURS = {}


def meilleurs_depuis_lignes(fen, lignes, maximum=3):
    """Voir AnalyseurPartie.meilleurs_coups."""
    if not lignes:
        return []
    try:
        cle = (fen, maximum, tuple((l[0], l[1], l[2], tuple(l[3] or ())) for l in lignes))
    except Exception:
        cle = None
    if cle is not None and cle in _MEILLEURS:
        return [dict(c, suite_san=list(c["suite_san"])) for c in _MEILLEURS[cle]]
    choisis = _calculer_meilleurs(fen, lignes, maximum)
    if cle is not None:
        if len(_MEILLEURS) >= 2000:
            _MEILLEURS.clear()
        _MEILLEURS[cle] = [dict(c, suite_san=list(c["suite_san"])) for c in choisis]
    return choisis


def _calculer_meilleurs(fen, lignes, maximum):
    texte_eval = AnalyseurPartie.texte_d_une_evaluation
    blancs = freestyle.plateau(fen).turn == chess.WHITE

    def du_joueur(v):
        c = annotations.chances_de_gagner(v)
        return c if blancs else 100.0 - c

    plateau = freestyle.plateau(fen)
    # 24/10 (Cowork, t65) : « Meilleur ici : e4 (+0.33)  aussi bon : Nf3 (+0.35),
    # Nf3 (+0.35) » : des lignes de deux calculs melangees. Un coup une seule
    # fois (la premiere ligne qui le donne), et le mieux note d'abord.
    vus, uniques = set(), []
    for ligne in lignes:
        if ligne[0] not in vus:
            vus.add(ligne[0])
            uniques.append(ligne)
    lignes = sorted(uniques, key=lambda l: -du_joueur(l[1]))
    reference = du_joueur(lignes[0][1])
    choisis = []
    for uci, valeur, mat, suite in lignes[:maximum]:
        if choisis and reference - du_joueur(valeur) > SEUIL_EQUIVALENT:
            break
        try:
            coup = chess.Move.from_uci(uci)
            san = plateau.san(coup)
        except Exception:
            continue
        suite_san = []
        essai = plateau.copy()
        for u in (suite or [])[:6]:
            try:
                c = chess.Move.from_uci(u)
                if c not in essai.legal_moves:
                    break
                suite_san.append(essai.san(c))
                essai.push(c)
            except Exception:
                break
        choisis.append({"uci": uci, "san": san, "evaluation": valeur, "mat": mat,
                        "texte": texte_eval(valeur, mat),
                        "suite_san": suite_san})
    return choisis
