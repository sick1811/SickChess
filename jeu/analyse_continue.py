# analyse_continue.py - SickChess 24/10 (travail p35, « Analyse libre »).
#
# Stockfish reflechit SANS ARRET sur la position affichee, comme sur lichess :
# les 3 meilleures lignes s'affinent en direct (profondeur qui monte), et des
# qu'on change de position il repart sur la nouvelle. Un fil de fond lit ce que
# le moteur ecrit ; l'ecran se contente de lire resultat() a chaque image.
#
# Pour ne pas chauffer le PC pour rien, la recherche s'arrete d'elle-meme apres
# DUREE_MAX_S secondes sur une meme position (ou a PROFONDEUR_MAX) : le
# resultat reste affiche. Le moteur tourne en priorite basse (moteurs.py).
#
# On trouve aussi ici ce qui sert a l'editeur de position et au collage :
#   lire_fen_ou_pgn(texte)   -> (fen de depart, coups) ou une erreur lisible ;
#   probleme_de_position(b)  -> pourquoi une position ne peut pas etre jouee ;
#   finale_des_tables(b)     -> gain / nulle / perte lu dans les tables Syzygy.

import io
import os
import threading
import time

import chess
import freestyle
import chess.pgn
import chess.syzygy

LIGNES = 3
DUREE_MAX_S = 60
PROFONDEUR_MAX = 40
ROLE = "libre"         # pas "analyse..." : liberer_les_analyses() ne le ferme pas


# ------------------------------------------------------------------ moteur

class AnalyseContinue:
    """Analyse sans fin de la position donnee a regarder(fen)."""

    def __init__(self, chemin=None, threads=None, hash_mb=256, moteur=None):
        self.chemin = chemin
        self.threads = threads
        self.hash_mb = hash_mb
        self._moteur = moteur            # fourni par les tests
        self._verrou = threading.Lock()
        self._cible = None               # fen a analyser
        self._en_recherche = None        # fen de la recherche en cours
        self._resultat = {}              # fen -> {"profondeur", "lignes", "fini"}
        self._actif = True
        self._fin = False
        self._reveil = threading.Event()
        self._fil = None
        self.erreur = ""

    # --------------------------------------------------------- commandes

    def regarder(self, fen):
        """La position a analyser (None = plus rien)."""
        with self._verrou:
            if fen == self._cible:
                return
            self._cible = fen
            self._arreter_la_recherche()
        self._demarrer()
        self._reveil.set()

    def mettre_en_pause(self, pause=True):
        with self._verrou:
            self._actif = not pause
            if pause:
                self._arreter_la_recherche()
        self._reveil.set()

    @property
    def actif(self):
        return self._actif

    def arreter(self):
        """En quittant l'ecran : la recherche s'arrete et le moteur est ferme."""
        with self._verrou:
            self._fin = True
            self._arreter_la_recherche()
        self._reveil.set()
        if self._fil is None or not self._fil.is_alive():
            self._liberer_le_moteur()
        # sinon le fil de fond ferme le moteur en sortant : on n'attend pas.

    def _liberer_le_moteur(self):
        if self.chemin is None:          # moteur fourni (tests) : pas a nous
            return
        try:
            import moteurs
            moteurs.liberer(ROLE)
        except Exception as e:
            print("[ANALYSE LIBRE] moteur non ferme : %s" % e)

    def resultat(self, fen=None):
        """{"profondeur", "lignes", "fini", "en_cours"} de la position (celle
        regardee par defaut). lignes : liste de {uci, san, evaluation (pions,
        Blancs), mat (Blancs), texte, suite_san}, meilleure d'abord."""
        with self._verrou:
            fen = fen or self._cible
            r = self._resultat.get(fen) or {"profondeur": 0, "lignes": [], "fini": False}
            r = dict(r, lignes=list(r["lignes"]))
            r["en_cours"] = self._en_recherche == fen and fen is not None
        return r

    # --------------------------------------------------------- fil de fond

    def _demarrer(self):
        if self._fil is None or not self._fil.is_alive():
            self._fil = threading.Thread(target=self._boucle, daemon=True)
            self._fil.start()

    def _arreter_la_recherche(self):
        """Appele SOUS le verrou : on ne parle au moteur que pendant une recherche,
        apres son « go » (sinon le « stop » arriverait avant et serait perdu)."""
        if self._en_recherche is not None and self._moteur is not None:
            self._moteur.send_command("stop")

    def _obtenir_moteur(self):
        if self._moteur is not None and self._moteur.est_vivant():
            if getattr(self._moteur, "multipv_courant", None) != LIGNES:
                self._moteur.send_command("setoption name MultiPV value %d" % LIGNES)
                self._moteur.multipv_courant = LIGNES
            return self._moteur
        try:
            import moteurs
            self._moteur = moteurs.moteur_d_analyse_role(ROLE, self.chemin, self.threads,
                                                         self.hash_mb)
        except Exception as e:
            print("[ANALYSE LIBRE] Stockfish indisponible : %s" % e)
            self._moteur = None
        if self._moteur is None:
            self.erreur = "Stockfish n'a pas pu démarrer."
            return None
        self._moteur.send_command("setoption name MultiPV value %d" % LIGNES)
        self._moteur.multipv_courant = LIGNES
        self.erreur = ""
        return self._moteur

    def _boucle(self):
        try:
            self._boucle_de_recherche()
        finally:
            if self._fin:
                self._liberer_le_moteur()

    def _boucle_de_recherche(self):
        while True:
            self._reveil.wait(0.5)
            self._reveil.clear()
            with self._verrou:
                if self._fin:
                    return
                fen = self._cible
                deja = self._resultat.get(fen)
                if not self._actif or not fen or (deja and deja["fini"]):
                    continue
            try:
                plateau = freestyle.plateau(fen)
            except ValueError:
                continue
            if plateau.is_game_over():
                with self._verrou:
                    self._resultat[fen] = {"profondeur": 0, "lignes": [], "fini": True}
                continue
            moteur = self._obtenir_moteur()
            if self._fin:
                return
            if moteur is None:
                time.sleep(2)
                continue
            self._chercher(moteur, fen)

    def _chercher(self, moteur, fen):
        from engine import StockfishEngine
        with self._verrou:
            if fen != self._cible or not self._actif or self._fin:
                return
            if hasattr(moteur, "envoyer_position"):     # Freestyle : UCI_Chess960
                moteur.envoyer_position(fen)
            else:
                moteur.send_command("position fen " + fen)
            moteur.send_command("go depth %d movetime %d" % (PROFONDEUR_MAX, DUREE_MAX_S * 1000))
            self._en_recherche = fen
        lignes, profondeur, derniere = {}, 0, 0.0
        fini = False
        while True:
            ligne = moteur._lire_ligne()
            if ligne is None:                    # moteur mort
                break
            if ligne.startswith("bestmove"):
                fini = True
                break
            if not ligne.startswith("info "):
                continue
            entree = StockfishEngine._analyser_multipv(ligne)
            if entree is None:
                continue
            rang, donnees = entree
            if donnees.get("borne") and rang in lignes:
                continue
            if rang == 1 and donnees["profondeur"] > profondeur:
                # nouvelle profondeur : les lignes moins profondes sont perimees
                lignes = {r: l for r, l in lignes.items()
                          if l["profondeur"] >= donnees["profondeur"] - 1}
                profondeur = donnees["profondeur"]
            lignes[rang] = donnees
            maintenant = time.time()
            if maintenant - derniere > 0.15 or rang == LIGNES:
                derniere = maintenant
                self._ranger(fen, profondeur, lignes, False)
        with self._verrou:
            interrompue = fen != self._cible or not self._actif or self._fin
            self._en_recherche = None
        # Une recherche arretee parce qu'on a change de position n'est pas
        # « finie » : on la reprendra si on revient sur la position.
        self._ranger(fen, profondeur, lignes, fini and not interrompue)

    def _ranger(self, fen, profondeur, lignes, fini):
        if not lignes:
            if fini:
                with self._verrou:
                    ancien = self._resultat.get(fen)
                    if ancien:
                        ancien["fini"] = True
            return
        details = {"lignes": [lignes[r] for r in sorted(lignes)]}
        en_clair = lignes_en_clair(fen, details)
        with self._verrou:
            ancien = self._resultat.get(fen)
            # On ne remplace jamais un resultat plus profond par un plus court
            # (retour sur une position deja analysee).
            if ancien and ancien["profondeur"] > profondeur and not fini:
                return
            self._resultat[fen] = {"profondeur": profondeur, "lignes": en_clair,
                                   "fini": fini}


def lignes_en_clair(fen, details, longueur=10):
    """Les lignes du moteur, en notation lisible, meilleure d'abord."""
    import analyse_partie
    texte_eval = analyse_partie.AnalyseurPartie.texte_d_une_evaluation
    plateau = freestyle.plateau(fen)
    sortie = []
    for uci, valeur, mat, suite in analyse_partie.lignes_du_moteur(fen, details):
        try:
            coup = chess.Move.from_uci(uci)
            if coup not in plateau.legal_moves:
                continue
        except ValueError:
            continue
        san, essai = [], plateau.copy()
        for u in (suite or [uci])[:longueur]:
            try:
                c = chess.Move.from_uci(u)
            except ValueError:
                break
            if c not in essai.legal_moves:
                break
            san.append(essai.san(c))
            essai.push(c)
        if not san:
            san = [plateau.san(coup)]
        sortie.append({"uci": uci, "san": san[0], "evaluation": valeur, "mat": mat,
                       "texte": texte_eval(valeur, mat), "suite_san": san})
    return sortie


# ------------------------------------------------------------------ collage

def lire_fen_ou_pgn(texte):
    """Un FEN ou une partie PGN collee. Renvoie (fen_de_depart, [coups uci], "")
    ou (None, [], erreur lisible)."""
    texte = (texte or "").strip()
    if not texte:
        return None, [], "Le presse-papiers est vide : copie d'abord un FEN ou un PGN."
    premiere = texte.splitlines()[0].strip()
    if premiere.count("/") == 7 and "[" not in premiere:
        # Un FEN sans les compteurs (ou sans le trait) est accepte.
        try:
            plateau = freestyle.plateau(" ".join(premiere.split()[:6]))
        except ValueError:
            return None, [], "Ce FEN n'est pas valable."
        probleme = probleme_de_position(plateau)
        if probleme:
            return None, [], probleme
        return plateau.fen(), [], ""
    try:
        jeu = chess.pgn.read_game(io.StringIO(texte))
    except Exception:
        jeu = None
    if jeu is None:
        return None, [], "Ce texte n'est ni un FEN ni une partie PGN."
    coups = [c.uci() for c in jeu.mainline_moves()]
    try:
        depart = jeu.board()
    except ValueError:
        return None, [], "Le FEN de cette partie n'est pas valable."
    if not coups and "FEN" not in jeu.headers:
        return None, [], "Ce texte n'est ni un FEN ni une partie PGN."
    return depart.fen(), coups, ""


# ------------------------------------------------------------------ editeur

def probleme_de_position(plateau):
    """Pourquoi la position ne peut pas etre analysee ; "" si elle est bonne.
    (Phrases entieres, pas de « roi %s » : la traduction anglaise les reconnait.)"""
    for couleur, manque, trop in (
            (chess.WHITE, "Il manque le roi blanc.", "Il y a plus d'un roi blanc."),
            (chess.BLACK, "Il manque le roi noir.", "Il y a plus d'un roi noir.")):
        rois = len(plateau.pieces(chess.KING, couleur))
        if rois == 0:
            return manque
        if rois > 1:
            return trop
    if plateau.pieces(chess.PAWN, chess.WHITE) & (chess.BB_RANK_1 | chess.BB_RANK_8) \
            or plateau.pieces(chess.PAWN, chess.BLACK) & (chess.BB_RANK_1 | chess.BB_RANK_8):
        return "Un pion ne peut pas être sur la première ou la dernière rangée."
    if plateau.was_into_check():
        return "Le camp qui n'a pas le trait est en échec : change le trait."
    if len(plateau.checkers()) > 2:
        return "Le roi est en échec par trop de pièces à la fois."
    for couleur, pions, pieces in (
            (chess.WHITE, "Les Blancs ont plus de 8 pions.", "Les Blancs ont plus de 16 pièces."),
            (chess.BLACK, "Les Noirs ont plus de 8 pions.", "Les Noirs ont plus de 16 pièces.")):
        if len(plateau.pieces(chess.PAWN, couleur)) > 8:
            return pions
        if chess.popcount(plateau.occupied_co[couleur]) > 16:
            return pieces
    return ""


def roques_possibles(plateau):
    """Les droits de roque que la position permet (roi et tour a leur place)."""
    essai = plateau.copy()
    essai.castling_rights = chess.BB_CORNERS
    return essai.clean_castling_rights()


# ------------------------------------------------------------------ Syzygy

_TABLES = {}          # dossier -> tables ouvertes
_VERDICTS = {}        # (dossier, fen) -> verdict : l'ecran le demande a chaque image
_DOSSIER = []


def _dossier_tables():
    """Le dossier syzygy/ (cherche une seule fois : jamais de disque par image)."""
    if not _DOSSIER:
        trouve = None
        for base in (os.getcwd(), os.path.dirname(os.path.dirname(os.path.abspath(__file__)))):
            chemin = os.path.join(base, "syzygy")
            if os.path.isdir(chemin):
                trouve = chemin
                break
        _DOSSIER.append(trouve)
    return _DOSSIER[0]


def finale_des_tables(plateau, dossier=None):
    """« Les Blancs gagnent » / « Nulle » / ... d'apres les tables Syzygy, pour
    une finale qu'elles connaissent. None sans tables ou hors des tables."""
    if chess.popcount(plateau.occupied) > 7:
        return None
    dossier = dossier or _dossier_tables()
    if not dossier:
        return None
    cle = (dossier, plateau.fen())
    if cle not in _VERDICTS:
        if len(_VERDICTS) > 500:
            _VERDICTS.clear()
        _VERDICTS[cle] = _lire_les_tables(plateau, dossier)
    return _VERDICTS[cle]


def _hors_des_50_coups(tables, plateau):
    """31/10 : avec les DTZ (.rtbz), une finale gagnee devient nulle quand la
    prise ou la poussee de pion arrive trop tard pour le compteur des 50 coups.
    Le DTZ peut etre arrondi d'un demi-coup (n veut dire n ou n + 1) : on ne
    dit nulle que si c'est sur. Sans .rtbz : False, verdict WDL comme avant."""
    try:
        dtz = tables.probe_dtz(plateau)
    except Exception:
        return False
    return abs(dtz) + plateau.halfmove_clock > 100


def _lire_les_tables(plateau, dossier):
    if plateau.is_game_over():
        return None
    try:
        tables = _TABLES.get(dossier)
        if tables is None:
            tables = _TABLES[dossier] = chess.syzygy.open_tablebase(dossier)
        wdl = tables.probe_wdl(plateau)
    except Exception:
        return None
    if wdl in (2, -2) and plateau.halfmove_clock and _hors_des_50_coups(tables, plateau):
        wdl = 0
    if wdl in (2, -2):
        blancs_gagnent = (wdl == 2) == (plateau.turn == chess.WHITE)
        return ("Tables de finale : les Blancs gagnent" if blancs_gagnent
                else "Tables de finale : les Noirs gagnent")
    return "Tables de finale : nulle"
