# mes_erreurs.py - SickChess : des problemes tires de TES propres fautes.
#
# Idee retenue le 17/10 (travaux proposes, p04) : chaque gaffe, erreur ou coup
# manque que l'analyse a trouve dans tes parties devient un probleme. On te
# remet dans la position, l'adversaire rejoue son coup d'avant, et c'est a toi
# de trouver ce qu'il fallait jouer.
#
# D'OU VIENNENT LES PROBLEMES : les analyses enregistrees a cote des parties
# (parties/<partie>.analyse.json, voir analyse_partie.py). Une partie dont
# l'analyse n'est pas terminee n'en donne pas encore : il suffit d'ouvrir sa
# revue une fois.
#
# FORMAT : le meme que la base lichess (puzzles.py), pour que l'ecran des
# problemes s'en serve tel quel :
#   fen   = la position AVANT le coup de l'adversaire qui precede ta faute
#   coups = [coup de l'adversaire, le coup qu'il fallait jouer]
# Ton suivi (reussis / rates) est dans mes_erreurs.json, a la racine du jeu.

import json
import os

import chess

import annotations

NOTES_RETENUES = ("gaffe", "erreur", "manque")
NOM_DU_MODE = "Mes erreurs"
FICHIER_SUIVI = "mes_erreurs.json"
# Un coup different de celui du moteur est accepte s'il ne perd presque rien
# (moins de 5 points de chances de gagner, comme « Bon » dans la revue).


def _dossier_ecriture():
    try:
        from asset_manager import dossier_ecriture
        return dossier_ecriture()
    except Exception:
        return os.getcwd()


def chemin_du_suivi():
    return os.path.join(_dossier_ecriture(), FICHIER_SUIVI)


def charger_le_suivi():
    try:
        with open(chemin_du_suivi(), "r", encoding="utf-8") as f:
            donnees = json.load(f)
        if isinstance(donnees, dict):
            donnees.setdefault("reussis", {})
            donnees.setdefault("rates", {})
            return donnees
    except (OSError, ValueError):
        pass
    return {"reussis": {}, "rates": {}}


def enregistrer_le_suivi(suivi):
    try:
        with open(chemin_du_suivi(), "w", encoding="utf-8") as f:
            json.dump(suivi, f, ensure_ascii=False, indent=1)
        return True
    except OSError as souci:
        print("[MES ERREURS] suivi non enregistre : %s" % souci)
        return False


def _camps_du_joueur(partie):
    """Les couleurs jouees par Julien dans cette partie (les deux a deux)."""
    camp = str(partie.get("camp") or "").lower()
    if camp.startswith("blanc"):
        return {chess.WHITE}
    if camp.startswith("noir"):
        return {chess.BLACK}
    if partie.get("importee"):
        # 24/10 (Cowork, r01) : une partie importee ou Julien ne joue pas (ton
        # nom n'est ni aux Blancs ni aux Noirs, ex. Morphy 1858) n'est pas une
        # de « tes » erreurs. L'import reconnait tes parties a ton nom.
        return set()
    return {chess.WHITE, chess.BLACK}


def problemes_d_une_partie(partie):
    """Les problemes tires d'une partie de "Mes parties" (liste, peut etre vide)."""
    import historique_parties
    from analyse_partie import AnalyseurPartie
    chemin = partie.get("chemin", "")
    cache = os.path.splitext(chemin)[0] + ".analyse.json"
    if not chemin or not os.path.exists(cache):
        return []
    donnees, erreur = historique_parties.lire_partie(chemin)
    if erreur or not donnees:
        return []
    # "rapide" : toute analyse enregistree (profondeur 16 ou plus) est acceptee.
    analyseur = AnalyseurPartie(donnees["fen"], donnees["coups"], None, "rapide",
                                fichier_cache=cache, version_min=1)
    if not analyseur.terminee():
        return []
    camps = _camps_du_joueur(partie)
    problemes = []
    for i in range(1, analyseur.nombre_de_coups()):
        d = analyseur.detail(i)
        if d.get("note") not in NOTES_RETENUES:
            continue
        blancs = d["par_les_blancs"]
        if (chess.WHITE if blancs else chess.BLACK) not in camps:
            continue
        meilleur = d.get("meilleur_uci")
        if not meilleur or meilleur == d["uci"]:
            continue
        problemes.append({
            "id": "moi:%s:%d" % (partie.get("fichier", os.path.basename(chemin)), i),
            "classement": 0,
            "themes": ["mes_erreurs", d["note"]],
            "fen": analyseur.fens[i - 1],
            "coups": [analyseur.coups[i - 1], meilleur],
            "source": {
                "fichier": partie.get("fichier", ""),
                "date": partie.get("date", ""),
                "numero": d["numero"],
                "par_les_blancs": blancs,
                "joue": d["san"],
                "note": d["note"],
                "eval_meilleur": analyseur.evaluations[i],
            },
        })
    return problemes


def tous_les_problemes(parties=None):
    """Tous les problemes, les moins reussis et les plus recents d'abord."""
    if parties is None:
        import historique_parties
        parties = historique_parties.lister()
    suivi = charger_le_suivi()
    tous = []
    for rang, partie in enumerate(parties):          # la plus recente d'abord
        for p in problemes_d_une_partie(partie):
            p["_rang"] = rang
            tous.append(p)
    tous.sort(key=lambda p: (int(suivi["reussis"].get(p["id"], 0)), p["_rang"]))
    return tous


def description(puzzle):
    """'Ta partie du 16/10/2026 - coup 14 : tu as joue Fxf7 (gaffe)'."""
    s = (puzzle or {}).get("source") or {}
    if not s:
        return ""
    import notation
    numero = "%d%s" % (s.get("numero", 0), "." if s.get("par_les_blancs") else "...")
    date = str(s.get("date", "")).split(" ")[0]
    return "Ta partie du %s – coup %s : tu as joué %s (%s)" % (
        date or "?", numero, notation.afficher(s.get("joue", "?")),
        annotations.libelle(s.get("note", "")).lower())


def coup_presque_aussi_bon(fen_avant, coup, puzzle, chemin_stockfish=None):
    """Un autre coup que celui du moteur, mais qui ne perd presque rien ?

    On demande a Stockfish (profondeur 14) l'evaluation apres le coup propose ET
    apres le meilleur coup, et on compare les deux. Sans moteur : non.
    24/10 : la reference etait l'evaluation enregistree par l'analyse de la partie ;
    sur un PC occupe elle etait moins profonde et un bon coup pouvait etre refuse
    (controle « un autre coup qui defend f7 », rouge une fois sur trois sous charge).
    Les deux coups sont maintenant juges par le meme calcul."""
    s = (puzzle or {}).get("source") or {}
    reference = s.get("eval_meilleur")
    coups = (puzzle or {}).get("coups") or []
    meilleur = coups[1] if len(coups) > 1 else None
    if reference is None and meilleur is None:
        return False
    try:
        import moteurs
        moteur = moteurs.moteur_d_analyse(chemin_stockfish, threads=None, hash_mb=256)
        if moteur is None:
            return False
        plateau = chess.Board(fen_avant)

        def apres(c):
            """Evaluation (pions) pour le joueur apres le coup c, ou None."""
            p = plateau.copy()
            p.push(c)
            details = moteur.analyser_position(p.fen(), 14, 5000)
            if not details:
                return None
            import analyse_partie
            v = analyse_partie._en_pions(details.get("evaluation"), details.get("mat"))
            # v est du point de vue de l'adversaire (au trait) : on retourne.
            return None if v is None else -v

        pour_le_joueur = apres(coup)
        if pour_le_joueur is None:
            return False
        joue_meilleur = None
        if meilleur:
            try:
                m = chess.Move.from_uci(meilleur)
                if m in plateau.legal_moves:
                    joue_meilleur = apres(m)
            except ValueError:
                joue_meilleur = None
        if joue_meilleur is None:
            if reference is None:
                return False
            joue_meilleur = reference if plateau.turn == chess.WHITE else -reference
    except Exception as souci:
        print("[MES ERREURS] verification impossible : %s" % souci)
        return False
    # 25/10 : la meme regle que la revue. Un coup qui perd moins de 5 points de
    # chances de gagner y est « Bon » (ou mieux) : ici aussi il est accepte.
    # L'ancienne marge fixe de 0,30 pion etait plus petite que le hasard de
    # Stockfish sur plusieurs coeurs (3...De7 contre 3...g6 : ecart de 0,10 a
    # 0,39 pion d'un calcul a l'autre) : un bon coup etait refuse une fois sur 4.
    perte = annotations.chances_de_gagner(joue_meilleur) - annotations.chances_de_gagner(pour_le_joueur)
    return perte < annotations.SEUIL_IMPRECISION


class SessionErreurs:
    """Meme interface que puzzles.Session, sans classement : on s'entraine."""

    def __init__(self, parties=None):
        self.mode = "erreurs"
        self.classe = False
        self.problemes = tous_les_problemes(parties)
        self.suivi = charger_le_suivi()
        self.index = -1
        self.gain = 0
        self._reussis = 0
        self._rates = 0
        self._serie = 0
        self._meilleure = 0

    def combien(self):
        return len(self.problemes)

    def classement(self):
        """Affiche en gros dans le panneau : la position dans la serie, '3/12'."""
        if not self.problemes:
            return "0"
        return "%d/%d" % (self.index + 1, len(self.problemes))

    def serie(self):
        return self._serie

    def meilleure_serie(self):
        return self._meilleure

    def reussis(self):
        return self._reussis

    def rates(self):
        return self._rates

    def pourcentage(self):
        total = self._reussis + self._rates
        return 100.0 * self._reussis / total if total else 0.0

    def deja_vus(self):
        return set()

    def variation(self):
        return 0

    def nom_du_mode(self):
        return NOM_DU_MODE

    def tirer_un_puzzle(self, themes=None, hasard=None):
        if not self.problemes:
            return None
        self.index = (self.index + 1) % len(self.problemes)
        return dict(self.problemes[self.index])

    def noter_un_puzzle(self, puzzle, reussi, secondes=None, indice=False):
        self.gain = 0
        if not puzzle:
            return 0
        cle = "reussis" if reussi else "rates"
        self.suivi[cle][puzzle["id"]] = int(self.suivi[cle].get(puzzle["id"], 0)) + 1
        enregistrer_le_suivi(self.suivi)
        if reussi:
            self._reussis += 1
            self._serie += 1
            self._meilleure = max(self._meilleure, self._serie)
        else:
            self._rates += 1
            self._serie = 0
        return 0

    def payer_l_indice(self):
        return 0
