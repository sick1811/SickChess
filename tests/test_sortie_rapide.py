# tests/test_sortie_rapide.py - quitter et lancer vite (24/10, retours de Julien :
# « des fois le jeu ne repond pas quand on appuie sur Quitter » ; « quitter une
# partie ou en lancer une est des fois long »).
#     python tests/test_sortie_rapide.py
#
# Causes trouvees (mesures sur le PC de Julien) :
#   - fermer un Stockfish attendait la fin de sa recherche en cours (le verrou
#     est tenu jusqu'a « bestmove ») : 1 a 1,3 s de fenetre figee ;
#   - arreter l'analyse laissait les recherches finir (Stockfish a 100 % apres
#     avoir quitte la partie) et attendait 0,3 s PAR fil ;
#   - creer un Stockfish (~1 s) se faisait sous le verrou general : quitter a ce
#     moment attendait la fin de ce demarrage ;
#   - l'adversaire attendait jusqu'a 2 s la fin de sa reflexion ;
#   - l'adversaire etait ferme a chaque fin de partie : ~0,6 s pour le relancer.
# Sans Stockfish : moteurs factices. Avec Stockfish (config.json ou variable
# SICKCHESS_STOCKFISH) : les vraies fermetures et interruptions.

import json
import os
import sys
import tempfile
import threading
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import asset_manager
_DOSSIER = tempfile.mkdtemp()
asset_manager.dossier_ecriture = lambda: _DOSSIER       # jamais les vraies donnees

import chess
import analyse_partie as A
import background_ai
import moteurs

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def chemin_stockfish():
    chemin = os.environ.get("SICKCHESS_STOCKFISH")
    if not chemin:
        try:
            with open("config.json", encoding="utf-8") as f:
                chemin = json.load(f).get("stockfish_path")
        except (OSError, ValueError):
            chemin = None
    return chemin if chemin and os.path.exists(chemin) else None


class MoteurFaux:
    def __init__(self):
        self.ferme = False
        self.interrompu = 0

    def est_vivant(self):
        return not self.ferme

    def quit(self):
        self.ferme = True

    def interrompre(self):
        self.interrompu += 1


print("1. Creer un Stockfish ne bloque plus liberer() (bouton Quitter)")
lent = threading.Event()
vrai_fabriquer = moteurs._fabriquer


def fabriquer_lent(chemin):
    lent.set()
    time.sleep(1.5)                      # un Stockfish qui demarre
    return MoteurFaux()


moteurs._fabriquer = fabriquer_lent
sauves = dict(moteurs._moteurs)
moteurs._moteurs.clear()
deja = MoteurFaux()
moteurs._moteurs["jeu"] = deja
try:
    fil = threading.Thread(target=lambda: moteurs.moteur_d_analyse_n(1, "x"), daemon=True)
    fil.start()
    lent.wait(5)
    debut = time.perf_counter()
    moteurs.liberer("jeu")
    duree = time.perf_counter() - debut
    verifier(duree < 0.3, "liberer(jeu) pendant le demarrage d'un autre moteur : %.2f s (avant ~1 s)" % duree)
    verifier(deja.ferme, "le moteur de jeu est bien ferme")
    # deux demandes du meme role en meme temps : un seul Stockfish demarre
    compte = []
    moteurs._fabriquer = lambda c: (compte.append(1), time.sleep(0.4), MoteurFaux())[2]
    fils = [threading.Thread(target=lambda: moteurs.moteur_de_jeu("x"), daemon=True) for _ in range(3)]
    for f in fils:
        f.start()
    for f in fils:
        f.join(5)
    verifier(len(compte) == 1 and "jeu" in moteurs._moteurs,
             "3 demandes du moteur de jeu en meme temps : %d demarrage(s)" % len(compte))
    fil.join(5)
finally:
    moteurs._fabriquer = vrai_fabriquer
    for m in list(moteurs._moteurs.values()):
        if isinstance(m, MoteurFaux):
            m.quit()
    moteurs._moteurs.clear()
    moteurs._moteurs.update(sauves)

print("2. L'adversaire interrompt sa reflexion au lieu de l'attendre")


class MoteurQuiReflechit(MoteurFaux):
    """get_best_move dure 5 s, sauf si on l'interrompt."""
    elo_bride = None

    def __init__(self):
        super().__init__()
        self._stop = threading.Event()

    def interrompre(self):
        super().interrompre()
        self._stop.set()

    def get_best_move(self, fen, temps):
        self._stop.wait(5)
        return next(iter(chess.Board(fen).legal_moves)).uci()


class Plateau:
    def __init__(self):
        self.board = chess.Board()
        self.game_over = False


m = MoteurQuiReflechit()
ia = background_ai.BackgroundAI(Plateau(), m) if hasattr(background_ai, "BackgroundAI") else None
if ia is None:
    nom = [n for n in dir(background_ai) if n.lower().endswith("manager") or n.lower().endswith("ai")]
    print("   (classe de l'adversaire introuvable : %s)" % nom)
else:
    ia.thread = threading.Thread(target=lambda: m.get_best_move(chess.Board().fen(), 5000), daemon=True)
    ia.thread.start()
    time.sleep(0.2)
    debut = time.perf_counter()
    ia.stop()
    duree = time.perf_counter() - debut
    verifier(m.interrompu >= 1, "stop() interrompt la recherche de Stockfish")
    verifier(duree < 0.5, "stop() pendant une reflexion de 5 s : %.2f s (avant jusqu'a 2 s)" % duree)

print("3. Arreter l'analyse : recherches interrompues, resultat incomplet jete")


class MoteurAnalyse:
    """analyser_position dure 5 s, sauf si on l'interrompt."""
    def __init__(self):
        self.interrompu = threading.Event()
        self.en_cours = threading.Event()

    def interrompre(self):
        self.interrompu.set()

    def analyser_position(self, fen, profondeur, temps, lignes=1, **reste):
        self.en_cours.set()
        self.interrompu.wait(5)
        coup = next(iter(chess.Board(fen).legal_moves))
        return {"coup": coup.uci(), "evaluation": 0.3, "mat": None, "profondeur": 3,
                "lignes": [{"coup": coup.uci(), "evaluation": 0.3, "mat": None, "suite": []}]}


mm = MoteurAnalyse()
a = A.AnalyseurPartie(None, ["e2e4", "e7e5", "g1f3"], None, "calcul_forte", moteur=mm)
a.demarrer()
mm.en_cours.wait(5)
debut = time.perf_counter()
a.arreter()
duree = time.perf_counter() - debut
verifier(mm.interrompu.is_set(), "arreter() envoie « stop » au moteur qui cherche")
verifier(duree < 0.45, "arreter() : %.2f s (au plus 0,3 s au total ; avant 0,3 s par fil et Stockfish continuait)" % duree)
time.sleep(0.3)
verifier(not any(a.niveau), "la recherche interrompue n'est pas gardee (aucune position notee)")

print("4. En quittant une partie, l'adversaire reste pret ; ferme en quittant le jeu")
import inspect
import game_manager
import petit_pc


def fermetures_apres_cleanup(mode_pc):
    """Les roles fermes par cleanup_game (moteurs.liberer espionne)."""
    fermes = []
    vrai_liberer = moteurs.liberer
    moteurs.liberer = lambda role: fermes.append(role) or True
    petit_pc.forcer(mode_pc)
    try:
        gm = game_manager.GameManager.__new__(game_manager.GameManager)
        gm.board = gm.current_mode = gm.engine = None
        gm.analyse_en_direct = None
        gm.cleanup_game()
    finally:
        moteurs.liberer = vrai_liberer
        petit_pc.forcer(None)
    return fermes


verifier("jeu" not in fermetures_apres_cleanup("normal"),
         "cleanup_game ne ferme plus le Stockfish adversaire (PC normal)")
verifier("jeu" in fermetures_apres_cleanup("petit"),
         "petit PC : cleanup_game le ferme encore (un seul Stockfish a la fois)")
verifier("_preparer_l_adversaire" in inspect.getsource(game_manager.GameManager.run),
         "l'adversaire demarre en tache de fond au menu")

chemin = chemin_stockfish()
if chemin:
    print("5. Avec le vrai Stockfish (%s)" % os.path.basename(chemin))
    from engine import StockfishEngine
    # 5a. fermer pendant une longue recherche
    sf = StockfishEngine(chemin)
    resultat = {}
    fil = threading.Thread(target=lambda: resultat.setdefault(
        "r", sf.analyser_position(chess.Board().fen(), 0, 20000, lignes=1)), daemon=True)
    fil.start()
    time.sleep(0.8)
    debut = time.perf_counter()
    sf.quit()
    duree = time.perf_counter() - debut
    verifier(duree < 1.2, "fermer Stockfish en pleine recherche de 20 s : %.2f s (avant : fin de la recherche)" % duree)
    fil.join(3)
    verifier(not fil.is_alive(), "le fil qui cherchait rend la main")
    # 5b. interrompre une recherche
    sf = StockfishEngine(chemin)
    debut = time.perf_counter()
    fil = threading.Thread(target=lambda: resultat.__setitem__(
        "i", sf.analyser_position(chess.Board().fen(), 0, 20000, lignes=1)), daemon=True)
    fil.start()
    time.sleep(0.8)
    verifier(sf.interrompre(), "interrompre() envoie « stop »")
    fil.join(3)
    verifier(not fil.is_alive() and time.perf_counter() - debut < 3,
             "la recherche de 20 s s'arrete aussitot (%.1f s en tout)" % (time.perf_counter() - debut))
    verifier(sf.est_vivant(), "Stockfish reste vivant apres « stop » (pret pour la suite)")
    sf.quit()
else:
    print("5. (pas de Stockfish : controles avec le vrai moteur sautes)")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
