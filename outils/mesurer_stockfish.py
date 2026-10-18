# outils/mesurer_stockfish.py - SickChess 18/10 (seance 13) : comment repartir
# Stockfish sur CE PC pour la revue de partie ?
#
# Repond au tableur de Julien (SickChess_repartition_Stockfish.ods) par une
# vraie mesure plutot que par des estimations : pour chaque repartition
# (1 x 12, 3 x 4, 6 x 2, 12 x 1 sur un PC a 12 processeurs logiques), on
# analyse les memes positions avec le MEME budget de calcul (calcul fixe,
# comme la revue par defaut) et on note :
#   - le temps total pour toute la serie (vitesse de la revue entiere) ;
#   - le temps de la premiere position (ce qu'on attend pour le coup regarde) ;
#   - la profondeur moyenne atteinte (a budget egal, plus de threads par
#     Stockfish = un peu moins profond : c'est le prix de la coordination) ;
#   - la vitesse en noeuds par seconde.
# Puis le temps d'une revue complete dans chaque reglage d'Options.
#
# Lancer (Windows, dossier SickChess) :   python outils/mesurer_stockfish.py
#   --positions 20    nombre de positions de la partie (defaut 20)
#   --noeuds 50       millions de noeuds par position (defaut 50 = Maximale)
#   --pgn chemin      une autre partie (defaut : la partie contre dragondu5)
# Duree : environ 10 a 15 minutes sur un i7-8700K. Ne pas jouer pendant.
# Resultat : docs/MESURE_STOCKFISH.md (+ affiche a l'ecran).
# Ne touche a rien d'autre (ni profil, ni parties, ni config).

import argparse
import glob
import json
import os
import subprocess
import sys
import threading
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "jeu"))

import chess
import chess.pgn

HASH_TOTAL_MO = 6144      # comme analyse_partie.HASH_ANALYSE_MB (6 Go, choix de Julien)


def chemin_stockfish():
    chemin = os.environ.get("SICKCHESS_STOCKFISH")
    if not chemin:
        try:
            with open(os.path.join(RACINE, "config.json"), encoding="utf-8") as f:
                chemin = json.load(f).get("stockfish_path")
        except (OSError, ValueError):
            chemin = None
    chemin = chemin or os.path.join("moteur", "stockfish.exe")
    if not os.path.isabs(chemin):
        chemin = os.path.join(RACINE, chemin)
    return chemin


def positions_de_la_partie(pgn, combien):
    if not pgn:
        trouves = sorted(glob.glob(os.path.join(RACINE, "parties", "*dragondu5*.pgn")))
        pgn = trouves[-1] if trouves else None
    if not pgn or not os.path.exists(pgn):
        sys.exit("Partie introuvable : donne un fichier avec --pgn")
    with open(pgn, encoding="utf-8", errors="replace") as f:
        jeu = chess.pgn.read_game(f)
    plateau = jeu.board()
    fens = []
    for coup in jeu.mainline_moves():
        plateau.push(coup)
        if not plateau.is_game_over():
            fens.append(plateau.fen())
    # Des positions reparties sur toute la partie (ouverture, milieu, finale).
    if len(fens) > combien:
        pas = len(fens) / float(combien)
        fens = [fens[int(i * pas)] for i in range(combien)]
    return os.path.basename(pgn), fens


class Moteur:
    def __init__(self, chemin, threads, hash_mo):
        options = {}
        if os.name == "nt":
            options["creationflags"] = 0x08000000      # pas de fenetre noire
        self.p = subprocess.Popen([chemin], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True, bufsize=1,
                                  cwd=os.path.dirname(chemin) or None, **options)
        self.envoyer("uci")
        self.attendre("uciok")
        self.envoyer("setoption name Threads value %d" % threads)
        self.envoyer("setoption name Hash value %d" % hash_mo)
        self.envoyer("isready")
        self.attendre("readyok")

    def envoyer(self, commande):
        self.p.stdin.write(commande + "\n")
        self.p.stdin.flush()

    def attendre(self, mot):
        while True:
            ligne = self.p.stdout.readline()
            if not ligne:
                raise RuntimeError("Stockfish s'est arrete")
            if ligne.startswith(mot):
                return ligne

    def analyser(self, fen, noeuds):
        self.envoyer("position fen " + fen)
        self.envoyer("go nodes %d" % noeuds)
        profondeur, calcules = 0, 0
        while True:
            ligne = self.p.stdout.readline()
            if not ligne:
                raise RuntimeError("Stockfish s'est arrete")
            mots = ligne.split()
            if mots and mots[0] == "info" and "depth" in mots and "score" in mots:
                profondeur = int(mots[mots.index("depth") + 1])
                if "nodes" in mots:
                    calcules = int(mots[mots.index("nodes") + 1])
            elif mots and mots[0] == "bestmove":
                return profondeur, calcules

    def fermer(self):
        try:
            self.envoyer("quit")
            self.p.wait(5)
        except Exception:
            self.p.kill()


def mesurer(chemin, moteurs, threads, fens, noeuds):
    """Analyse toutes les positions avec 'moteurs' Stockfish de 'threads'
    threads chacun. Renvoie un dictionnaire de resultats."""
    hash_mo = max(16, HASH_TOTAL_MO // moteurs)
    m = [Moteur(chemin, threads, hash_mo) for _ in range(moteurs)]
    file_attente = list(enumerate(fens))
    verrou = threading.Lock()
    resultats = {}
    premiere = [None]
    debut = time.time()

    def ouvrier(moteur):
        while True:
            with verrou:
                if not file_attente:
                    return
                k, fen = file_attente.pop(0)
            t = time.time()
            profondeur, calcules = moteur.analyser(fen, noeuds)
            duree = time.time() - t
            with verrou:
                resultats[k] = (profondeur, calcules, duree)
                if premiere[0] is None:
                    premiere[0] = duree

    fils = [threading.Thread(target=ouvrier, args=(x,)) for x in m]
    for f in fils:
        f.start()
    for f in fils:
        f.join()
    total = time.time() - debut
    for x in m:
        x.fermer()
    profondeurs = [r[0] for r in resultats.values()]
    calcul = sum(r[1] for r in resultats.values())
    return {"moteurs": moteurs, "threads": threads, "total_s": total,
            "par_position_s": total / len(fens),
            "premiere_s": premiere[0] or 0.0,
            "profondeur_moy": sum(profondeurs) / float(len(profondeurs)),
            "profondeur_min": min(profondeurs),
            "vitesse": calcul / total}


def repartitions(processeurs):
    choix = []
    for moteurs in (1, 3, processeurs // 2, processeurs):
        if moteurs >= 1 and processeurs % moteurs == 0:
            couple = (moteurs, processeurs // moteurs)
            if couple not in choix:
                choix.append(couple)
    return choix


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--positions", type=int, default=20)
    parser.add_argument("--noeuds", type=float, default=50.0,
                        help="millions de noeuds par position")
    parser.add_argument("--pgn", default=None)
    args = parser.parse_args()

    chemin = chemin_stockfish()
    if not os.path.exists(chemin):
        sys.exit("Stockfish introuvable : %s" % chemin)
    processeurs = os.cpu_count() or 2
    noeuds = int(args.noeuds * 1000000)
    nom, fens = positions_de_la_partie(args.pgn, args.positions)
    print("Stockfish : %s" % chemin)
    print("Processeurs logiques : %d - partie : %s - %d positions - %d millions de "
          "noeuds par position" % (processeurs, nom, len(fens), noeuds // 1000000))
    lignes = []
    for moteurs, threads in repartitions(processeurs):
        print("Mesure %d x %d..." % (moteurs, threads), flush=True)
        r = mesurer(chemin, moteurs, threads, fens, noeuds)
        lignes.append(r)
        print("  %.0f s en tout, %.1f s par position, premiere position %.1f s, "
              "profondeur %.1f (min %d), %.1f millions de noeuds/s"
              % (r["total_s"], r["par_position_s"], r["premiere_s"],
                 r["profondeur_moy"], r["profondeur_min"], r["vitesse"] / 1e6),
              flush=True)

    meilleure = min(lignes, key=lambda r: r["total_s"])
    vitesse = meilleure["vitesse"]
    sortie = ["# Mesure de Stockfish sur ce PC",
              "",
              "Fait par `outils/mesurer_stockfish.py` le %s." % time.strftime("%d/%m/%Y %H:%M"),
              "%d processeurs logiques ; partie %s, %d positions ; %d millions de noeuds "
              "par position (calcul fixe)." % (processeurs, nom, len(fens), noeuds // 1000000),
              "",
              "| Répartition | Toute la série | Par position | 1re position | "
              "Profondeur moyenne (min) | Millions de nœuds/s |",
              "|---|---|---|---|---|---|"]
    for r in lignes:
        sortie.append("| %d × %d | %.0f s | %.1f s | %.1f s | %.1f (%d) | %.1f |"
                      % (r["moteurs"], r["threads"], r["total_s"], r["par_position_s"],
                         r["premiere_s"], r["profondeur_moy"], r["profondeur_min"],
                         r["vitesse"] / 1e6))
    sortie += ["",
               "Plus rapide pour toute la série : **%d × %d**." % (meilleure["moteurs"],
                                                                 meilleure["threads"]),
               "",
               "## Durée estimée d'une revue (partie de 40 coups = 80 positions)",
               "",
               "Avec la répartition la plus rapide (%.1f millions de nœuds/s) :" % (vitesse / 1e6),
               ""]
    for libelle, millions in (("Calcul fixe – Rapide (10 M)", 10),
                              ("Calcul fixe – Forte (25 M)", 25),
                              ("Calcul fixe – Maximale (50 M)", 50)):
        # passe finale + passe des trois coups (un cinquieme du budget)
        secondes = 80 * millions * 1.2 * 1e6 / vitesse
        sortie.append("- %s : environ %.1f min" % (libelle, secondes / 60.0))
    sortie.append("")
    texte = "\n".join(sortie)
    print()
    print(texte)
    chemin_doc = os.path.join(RACINE, "docs", "MESURE_STOCKFISH.md")
    with open(chemin_doc, "w", encoding="utf-8") as f:
        f.write(texte)
    print("Ecrit dans %s" % chemin_doc)


if __name__ == "__main__":
    main()
