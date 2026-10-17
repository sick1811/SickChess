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

import annotations

# nom -> (profondeur de la passe fine, temps maximum par position en ms)
# SickChess 17/10 (remarque de Julien : "trop imprecis, il faut un moteur tres
# puissant, rapide et surtout precis, c'est un jeu ultra competitif") : une
# marche de plus partout. L'analyse suit maintenant la partie en direct (voir
# ajouter_coups), donc la profondeur ne se paie plus a la fin.
PUISSANCES = {
    "rapide": (16, 1500),
    "normale": (20, 4000),
    "forte": (24, 8000),
}
PUISSANCE_PAR_DEFAUT = "normale"

PROFONDEUR_SURVOL = 12
TEMPS_SURVOL_MS = 500

# Taille de la table de hachage du moteur d'analyse (Mo). Plus grande = les
# positions deja vues ne sont pas recalculees.
HASH_ANALYSE_MB = 1024

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

def precision_du_coup(perte):
    perte = max(0.0, float(perte))
    return max(0.0, min(100.0, 103.1668 * math.exp(-0.04354 * perte) - 3.1669))


def _ecart_type(valeurs):
    if len(valeurs) < 2:
        return 0.5
    moyenne = sum(valeurs) / float(len(valeurs))
    return math.sqrt(sum((v - moyenne) ** 2 for v in valeurs) / len(valeurs))


def precision_globale(precisions, chances):
    if not precisions:
        return None
    if len(precisions) == 1:
        return round(precisions[0], 1)
    fenetre = max(2, min(8, len(chances) // 10))
    poids = []
    for i in range(len(precisions)):
        tranche = chances[max(0, i - fenetre):i + fenetre + 1]
        poids.append(max(0.5, _ecart_type(tranche)))
    ponderee = sum(p * w for p, w in zip(precisions, poids)) / (sum(poids) or 1.0)
    harmonique = len(precisions) / sum(1.0 / max(1.0, p) for p in precisions)
    return round(max(0.0, min(100.0, (ponderee + harmonique) / 2.0)), 1)


# ---------------------------------------------------------------- analyseur

class AnalyseurPartie:
    """Analyse une partie en tache de fond, en commencant par le coup regarde."""

    def __init__(self, fen_initiale, coups_uci, chemin_stockfish=None,
                 puissance=None, moteur=None, suivi=False, threads=None,
                 fichier_cache=None):
        self.chemin = chemin_stockfish
        # suivi = l'analyse accompagne une partie EN COURS : elle ne s'arrete
        # pas quand elle a tout vu, elle attend les coups suivants
        # (ajouter_coups). finir_le_suivi() la laisse terminer normalement.
        self.suivi = bool(suivi)
        self.threads = threads
        nom = str(puissance or PUISSANCE_PAR_DEFAUT).strip().lower()
        self.puissance = nom if nom in PUISSANCES else PUISSANCE_PAR_DEFAUT
        self.profondeur, self.temps_max_ms = PUISSANCES[self.puissance]
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

        self.erreur = None
        self.en_cours = False
        self._stop = False
        self._fil = None
        self._priorite = None
        self._cache = {}
        # SickChess 17/10 (remarque de Julien : "les analyses ne sont pas bien
        # enregistrees, une nouvelle evaluation commence a chaque revue") :
        # l'analyse terminee est ecrite a cote du PGN et relue a l'ouverture.
        self.fichier_cache = None
        if fichier_cache:
            self.definir_fichier_cache(fichier_cache)

    def _construire_positions(self, coups):
        plateau = chess.Board(self.fen_initiale)
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

    CHAMPS_CACHE = ("evaluations", "mats", "meilleurs", "premiers", "seconds")

    def definir_fichier_cache(self, chemin):
        """Ou garder l'analyse. Relit le fichier s'il existe deja ; ecrit tout
        de suite si l'analyse est deja terminee."""
        self.fichier_cache = chemin
        if not chemin:
            return
        if os.path.exists(chemin) and not self.terminee():
            self._relire_cache(chemin)
        if self.terminee() and not self.suivi:
            self._ecrire_cache()

    def _relire_cache(self, chemin):
        import json
        try:
            with open(chemin, "r", encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            return False
        if not isinstance(d, dict) or d.get("fen") != self.fen_initiale \
                or d.get("coups") != self.coups \
                or int(d.get("profondeur") or 0) < self.profondeur:
            return False
        n = len(self.fens)
        if any(len(d.get(c) or []) != n for c in self.CHAMPS_CACHE):
            return False
        for champ in self.CHAMPS_CACHE:
            setattr(self, champ, list(d[champ]))
        self.niveau = [2] * n
        self._cache = {}
        print("[ANALYSE] analyse relue (%s)" % os.path.basename(chemin))
        return True

    def _ecrire_cache(self):
        if not self.fichier_cache or not self.terminee():
            return False
        import json
        d = {"fen": self.fen_initiale, "coups": list(self.coups),
             "profondeur": self.profondeur, "version": 1}
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
        plateau = chess.Board(self.fens[-1])
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
                                  (self.seconds, None), (self.niveau, 0)):
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

    # ------------------------------------------------------------------ pilotage

    def demarrer(self):
        if self.en_cours or (self.terminee() and not self.suivi):
            return False
        self._stop = False
        self.en_cours = True
        self._fil = threading.Thread(target=self._travailler, daemon=True)
        self._fil.start()
        return True

    def arreter(self, attendre=0.3):
        self._stop = True
        if self._fil is not None and self._fil.is_alive():
            self._fil.join(attendre)

    def prioriser(self, index_coup):
        """Le joueur regarde le coup index_coup (-1 = position de depart)."""
        self._priorite = int(index_coup)

    def _prochaine(self):
        n = len(self.fens)
        p = self._priorite
        if p is not None:
            # Le coup regarde a besoin des positions p et p+1 ; p+2 donne le
            # meilleur coup de la position suivante.
            for k in (p + 1, p, p + 2):
                if 0 <= k < n and self.niveau[k] < 2:
                    return k, self.niveau[k] + 1
        for niveau in (1, 2):
            for k in range(min(n, len(self.niveau))):
                if self.niveau[k] < niveau:
                    return k, niveau
        return None

    def _moteur(self):
        if self._moteur_fourni is not None:
            return self._moteur_fourni
        import moteurs
        return moteurs.moteur_d_analyse(self.chemin, threads=self.threads,
                                        hash_mb=HASH_ANALYSE_MB)

    def _travailler(self):
        try:
            moteur = self._moteur()
            if moteur is None:
                raise RuntimeError("Stockfish n'a pas demarre")
            while not self._stop:
                suivant = self._prochaine()
                if suivant is None:
                    if self.suivi:
                        time.sleep(0.15)      # on attend le coup suivant
                        continue
                    break
                self._analyser(moteur, *suivant)
        except Exception as e:
            self.erreur = str(e)[:80]
            print("[ANALYSE] impossible : %s" % e)
        finally:
            self.en_cours = False
            if not self._stop and not self.suivi:
                self._ecrire_cache()

    def _lignes_pour(self, k):
        premier = annotations.chances_de_gagner(self.premiers[k])
        second = annotations.chances_de_gagner(self.seconds[k])
        if premier is None or second is None:
            return 1
        return 2 if abs(premier - second) >= ECART_CANDIDAT else 1

    def _analyser(self, moteur, k, niveau):
        if self.finie[k]:
            # Mat ou nulle : rien a demander au moteur.
            if chess.Board(self.fens[k]).is_checkmate():
                self.evaluations[k] = -EVAL_MAT if self.trait[k] else EVAL_MAT
                self.mats[k] = 0
            else:
                self.evaluations[k] = 0.0
            self.niveau[k] = 2
            return
        if niveau <= 1:
            profondeur, temps, lignes = PROFONDEUR_SURVOL, TEMPS_SURVOL_MS, 2
        else:
            profondeur, temps = self.profondeur, self.temps_max_ms
            lignes = self._lignes_pour(k)
        details = moteur.analyser_position(self.fens[k], profondeur, temps,
                                           lignes=lignes)
        if details:
            signe = 1.0 if self.trait[k] else -1.0
            premier = _en_pions(details.get("evaluation"), details.get("mat"))
            if premier is not None:
                self.evaluations[k] = signe * premier
                mat = details.get("mat")
                self.mats[k] = int(signe * mat) if mat is not None else None
            if details.get("coup"):
                self.meilleurs[k] = details["coup"]
            second = _en_pions(details.get("second_evaluation"),
                               details.get("second_mat"))
            if premier is not None and second is not None:
                self.premiers[k] = signe * premier
                self.seconds[k] = signe * second
        self.niveau[k] = max(self.niveau[k], niveau)

    # ------------------------------------------------------------------ avancement

    def avancement(self):
        """(part du survol faite, part de la passe fine faite), de 0 a 1."""
        n = float(len(self.fens) or 1)
        return (sum(1 for v in self.niveau if v >= 1) / n,
                sum(1 for v in self.niveau if v >= 2) / n)

    def survol_fini(self):
        return all(v >= 1 for v in self.niveau)

    def terminee(self):
        return all(v >= 2 for v in self.niveau)

    def texte_avancement(self):
        if self.erreur:
            return "Analyse impossible : %s" % self.erreur
        survol, fine = self.avancement()
        if fine >= 1.0:
            return "Analyse terminée (profondeur %d)" % self.profondeur
        if survol < 1.0:
            return "Analyse rapide... %d %%" % int(survol * 100)
        return "Analyse fine... %d %%" % int(fine * 100)

    # ------------------------------------------------------------------ lecture

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
        mat = self.mats[k]
        if mat is not None:
            if mat == 0:
                return "Mat"
            return ("M%d" if mat > 0 else "-M%d") % abs(mat)
        if self.evaluations[k] is None:
            return "..."
        return "%+.2f" % self.evaluations[k]

    def san_du_meilleur(self, k):
        """Le meilleur coup de la position k, en notation courte."""
        if not 0 <= k < len(self.meilleurs) or not self.meilleurs[k]:
            return None
        try:
            return chess.Board(self.fens[k]).san(
                chess.Move.from_uci(self.meilleurs[k]))
        except Exception:
            return None

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
            "pret": False, "note": None, "perte": None,
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
                and self.niveau[i] >= 2 and self.niveau[i + 1] >= 2:
            infos.update(self._juger(i, avant, apres, blancs))
        self._cache[i] = infos
        return infos

    def _juger(self, i, avant, apres, blancs):
        joue = self.coups[i]
        meilleur = self.meilleurs[i]
        plateau = chess.Board(self.fens[i])
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
        try:
            import ouvertures
            theorique = ouvertures.est_un_coup_de_livre(self.sans, i)
        except Exception:
            theorique = False
        dernier = chess.Move.from_uci(self.coups[i - 1]) if i > 0 else None
        est_le_meilleur = bool(meilleur) and meilleur == joue
        note = annotations.classer(
            perte, est_le_meilleur,
            annotations.est_un_sacrifice(plateau, coup),
            theorique=theorique, chances_avant=chances_avant,
            chances_apres=chances_apres, ecart_second=ecart,
            evident=annotations.coup_evident(plateau, coup, dernier),
            meilleur_connu=bool(meilleur),
            perte_pions=perte_pions, apres_pions=apres_pions)
        return {"pret": True, "note": note, "perte": perte,
                "chances_avant": chances_avant,
                "est_le_meilleur": est_le_meilleur}

    def notes(self):
        """La pastille de chaque coup (None tant qu'il n'est pas juge)."""
        return [self.detail(i)["note"] for i in range(len(self.coups))]

    def rapport(self):
        """Precision, pastilles par camp et moments cles de la partie."""
        camps = {}
        tous = [self.detail(i) for i in range(len(self.coups))]
        for nom, blancs in (("blancs", True), ("noirs", False)):
            juges = [d for d in tous if d["pret"] and d["par_les_blancs"] == blancs]
            compte = dict((cle, 0) for cle in annotations.ORDRE)
            for d in juges:
                if d["note"] in compte:
                    compte[d["note"]] += 1
            camps[nom] = {
                "coups": len(juges),
                "precision": precision_globale(
                    [precision_du_coup(d["perte"]) for d in juges],
                    [d["chances_avant"] for d in juges]),
                "pastilles": compte,
            }
        graves = [d for d in tous if d["pret"]
                  and d["note"] in ("gaffe", "erreur", "manque")]
        graves.sort(key=lambda d: -d["perte"])
        camps["moments_cles"] = sorted(graves[:NOMBRE_MOMENTS_CLES],
                                       key=lambda d: d["index"])
        return camps
