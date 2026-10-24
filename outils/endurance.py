"""Le test d'endurance : un robot joue a SickChess pendant 2 heures (24/10, travail p28).

    python outils/endurance.py                 2 heures (Stockfish necessaire)
    python outils/endurance.py --minutes 15    un essai plus court
    python outils/endurance.py --sortie DOSSIER

Le robot utilise le VRAI jeu, dans une fenetre invisible (on peut se servir du PC) et
avec un dossier temporaire (profil, parties, records de Julien jamais touches). Il
enchaine en boucle, a la vitesse normale du jeu (60 images/s) :
    menu -> partie contre l'ordinateur (coups au hasard) -> sa revue -> partie a deux
    quittee en cours -> problemes (bons et mauvais coups) -> analyse libre ->
    Options, Mes parties, Statistiques -> menu...
Apres chaque scenario il releve : memoire du jeu et des Stockfish, nombre de
Stockfish ouverts, fils d'execution, objets Python, temps d'une image, erreurs.

A la fin, il juge :
    FUITE           la memoire du jeu monte toujours (Mo par heure, apres l'echauffement)
    STOCKFISH       des processus Stockfish s'accumulent
    RALENTISSEMENT  les images prennent plus de temps a la fin qu'au debut
    PLANTAGES       une erreur dans un scenario, ou un « Traceback » dans le journal
Ecrit SORTIE/rapport.json, SORTIE/journal.txt (tout ce que le jeu a affiche) et, pour
un passage d'au moins une heure, docs/ENDURANCE.md. SORTIE = tests/endurance/.
Code de sortie : 0 si tout est vert, 1 sinon. Le banc d'essai le lance (section
« endurance », hors --rapide).
"""
import collections
import gc
import json
import os
import random
import statistics
import sys
import tempfile
import threading
import time
import traceback

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

FUITE_VERT, FUITE_ORANGE = 30.0, 100.0          # Mo par heure
LENTEUR_VERT, LENTEUR_ORANGE = 1.3, 1.8         # image de la fin / image du debut


def _argument(nom, defaut):
    if nom in sys.argv:
        return sys.argv[sys.argv.index(nom) + 1]
    return defaut


class Journal:
    """Recopie la sortie du jeu dans journal.txt et compte les « Traceback »."""

    def __init__(self, flux, chemin):
        self.flux, self.fichier, self.tracebacks = flux, open(chemin, "w", encoding="utf-8"), []

    def write(self, texte):
        self.fichier.write(texte)
        if "Traceback" in texte:
            self.tracebacks.append(time.strftime("%H:%M:%S"))
        return len(texte)

    def flush(self):
        self.fichier.flush()

    def isatty(self):
        return False


class Robot:
    def __init__(self, minutes, sortie):
        import psutil
        import pygame
        self.pygame, self.psutil = pygame, psutil
        self.fin = time.time() + minutes * 60
        self.minutes = minutes
        self.sortie = sortie
        self.hasard = random.Random(2810)
        self.mesures = []
        self.plantages = []
        self.temps_images = {}
        self.debut = time.time()
        pygame.init()
        self.ecran = pygame.display.set_mode((1280, 720))
        self.clock = pygame.time.Clock()
        import asset_manager
        self.donnees = tempfile.mkdtemp(prefix="sickchess_endurance_")
        asset_manager.dossier_ecriture = lambda: self.donnees
        import sauvegarde
        sauvegarde.FICHIER = os.path.join(self.donnees, "partie_en_cours.json")
        from game_manager import GameManager
        self.gm = GameManager("endurance")
        self.gm.screen = self.ecran
        self.gm.stockfish_path = os.environ.get("SICKCHESS_STOCKFISH") or self.gm.stockfish_path
        self.processus = psutil.Process()
        self.scenario_courant = None
        self.tour = 0

    # ------------------------------------------------------------ outils

    def images(self, nom, dessiner, secondes=None, n=None, avant=None):
        """Fait tourner un ecran a 60 images/s ; garde le temps de chaque image."""
        pg = self.pygame
        fin = time.time() + (secondes or 0)
        # 600 images au plus par ecran : garder les temps de 2 heures d'images ferait
        # grossir... le robot lui-meme (essai du 24/10 : fausse alarme de fuite).
        temps = self.temps_images.setdefault(self.scenario_courant or nom,
                                             collections.deque(maxlen=600))
        k = 0
        while (n is not None and k < n) or (n is None and time.time() < fin):
            pg.event.pump()
            if avant is not None and avant() is False:
                break
            t = time.perf_counter()
            dessiner()
            pg.display.flip()
            temps.append((time.perf_counter() - t) * 1000)
            self.clock.tick(60)
            k += 1

    def stockfish(self):
        n, rss = 0, 0
        for p in self.processus.children(recursive=True):
            try:
                if "stockfish" in p.name().lower():
                    n += 1
                    rss += p.memory_info().rss
            except Exception:
                pass
        return n, rss / 1048576.0

    def mesurer(self, scenario):
        n_sf, rss_sf = self.stockfish()
        temps = list(self.temps_images.get(scenario) or [0])
        m = {"t_min": round((time.time() - self.debut) / 60.0, 2), "scenario": scenario,
             "tour": self.tour,
             "memoire_jeu_mo": round(self.processus.memory_info().rss / 1048576.0, 1),
             "stockfish": n_sf, "memoire_stockfish_mo": round(rss_sf, 1),
             "fils": threading.active_count(), "objets_python": len(gc.get_objects()),
             "image_ms": round(statistics.median(temps[-600:]), 2)}
        self.mesures.append(m)
        print("[ENDURANCE] %(t_min)6.1f min  %(scenario)-14s jeu %(memoire_jeu_mo)6.1f Mo  "
              "stockfish %(stockfish)d (%(memoire_stockfish_mo)6.1f Mo)  fils %(fils)3d  "
              "image %(image_ms)5.2f ms" % m, file=sys.__stdout__, flush=True)

    def scenario(self, nom, fonction):
        self.scenario_courant = nom
        try:
            fonction()
        except Exception as e:
            self.plantages.append({"t_min": round((time.time() - self.debut) / 60.0, 2),
                                   "scenario": nom, "erreur": "%s: %s" % (type(e).__name__, e),
                                   "trace": traceback.format_exc()[-3000:]})
            print("[ENDURANCE] PLANTAGE dans %s : %s" % (nom, e), file=sys.__stdout__, flush=True)
            try:
                self.gm.cleanup_game()
            except Exception:
                pass
        self.mesurer(nom)

    # ------------------------------------------------------------ scenarios

    def menu(self):
        self.gm.au_menu = True
        self.images("menu", self.gm.menu.draw, secondes=4)
        self.gm.au_menu = False

    def coup_au_hasard(self, board):
        coups = list(board.legal_moves)
        prises = [c for c in coups if board.is_capture(c)]
        return self.hasard.choice(prises if prises and self.hasard.random() < 0.6 else coups)

    def contre_l_ordinateur(self):
        gm = self.gm
        gm.game_mode = "stockfish"
        gm.reglages = {"elo": self.hasard.choice([800, 1400, 2000]), "minutes": 10, "increment": 0,
                       "pendule_active": True, "ia_temps_min_ms": 80, "ia_temps_max_ms": 300,
                       "ia_temps_humain": False}
        if not gm.preparer_partie():
            raise RuntimeError("partie contre l'ordinateur impossible a preparer")
        b, mode = gm.board, gm.current_mode
        demi_coups = [0]
        limite = time.time() + 150

        def image():
            mode.update()
            b.update()
            if not b.game_over and not mode.cest_le_tour_de_lia() and not b.animation.animations:
                if demi_coups[0] >= 80 or time.time() > limite:
                    b.terminer_partie("Abandon", "0-1" if b.board.turn == 1 else "1-0")
                else:
                    b.make_move(self.coup_au_hasard(b.board))
            demi_coups[0] = len(b.board.move_stack)
            gm._suivre_analyse()
            b.draw()

        self.images("partie", image, avant=lambda: not b.game_over and time.time() < limite + 30,
                    secondes=200)
        if not b.game_over:
            b.terminer_partie("Abandon", "1/2-1/2")
        gm._partie_terminee()
        self.images("fin", b.draw, secondes=2)
        self.revue()
        gm.cleanup_game()

    def revue(self):
        from ecran_revue import EcranRevue
        import analyse_partie
        gm = self.gm
        analyseur = gm.board.end_screen.lancer_analyse(gm.stockfish_path,
                                                       analyse_partie.puissance_de(gm.config))
        r = EcranRevue(self.ecran, analyseur, gm.config, ("Robot", "Ordinateur"), "*")
        index = [0]

        def image():
            if self.hasard.random() < 0.05:
                index[0] = (index[0] + 1) % (len(r.coups) + 1)
                r.aller_a(index[0])
            r.plateau.update()
            r.draw()

        self.images("revue", image, secondes=25)
        r._liberer_la_variante()

    def a_deux(self):
        gm = self.gm
        gm.game_mode = "hotseat"
        gm.reglages = {"minutes": 5, "increment": 0, "pendule_active": True,
                       "retourner_plateau": True}
        gm.preparer_partie()
        b = gm.board

        def image():
            b.update()
            if not b.game_over and len(b.board.move_stack) < 30 and not b.animation.animations \
                    and not b.retournement.vols:
                b.make_move(self.coup_au_hasard(b.board))
            b.draw()

        self.images("a_deux", image, secondes=20)
        import sauvegarde
        sauvegarde.enregistrer(b, "hotseat", gm.reglages)       # « Menu » en pleine partie
        gm.cleanup_game()

    def problemes(self):
        import puzzles
        if not puzzles.disponible():
            return
        from ecran_problemes import EcranProblemes
        e = EcranProblemes(self.ecran, self.gm.config)
        e.commencer(puzzles.MODE_LIBRE, 1500)
        resolus = [0]
        import chess

        def image():
            e.update()
            if e.puzzle and not e.fini and not e.coup_en_attente and not e.plateau.animation.animations:
                attendu = puzzles.coup_attendu(e.puzzle, e.avance)
                if attendu:
                    coup = chess.Move.from_uci(attendu)
                    if self.hasard.random() < 0.15:                 # parfois un mauvais coup
                        autres = [c for c in e.plateau.board.legal_moves if c != coup]
                        coup = self.hasard.choice(autres) if autres else coup
                    e.plateau.make_move(coup)
            elif e.fini and resolus[0] < 8:
                resolus[0] += 1
                e.nouveau_puzzle()
            e.draw()

        self.images("problemes", image, secondes=30)

    def analyse_libre(self):
        from ecran_analyse_libre import EcranAnalyseLibre
        e = EcranAnalyseLibre(self.ecran, self.gm.config, stockfish_path=self.gm.stockfish_path,
                              threads=2)

        def image():
            if self.hasard.random() < 0.02 and not e.plateau.board.is_game_over():
                e._coup_sur_l_echiquier(self.coup_au_hasard(e.plateau.board))
            e.draw()

        self.images("analyse_libre", image, secondes=20)
        e.analyse.arreter()

    def ecrans(self):
        from ecran_mes_parties import EcranMesParties
        from ecran_options import EcranOptions
        from ecran_statistiques import EcranStatistiques
        for nom, fabrique in (("options", lambda: EcranOptions(self.ecran)),
                              ("mes_parties", lambda: EcranMesParties(self.ecran)),
                              ("statistiques", lambda: EcranStatistiques(self.ecran))):
            e = fabrique()
            self.images(nom, e.draw, secondes=3)

    # ------------------------------------------------------------ boucle

    def tourner(self):
        scenarios = [("menu", self.menu), ("partie", self.contre_l_ordinateur),
                     ("a_deux", self.a_deux), ("problemes", self.problemes),
                     ("analyse_libre", self.analyse_libre), ("ecrans", self.ecrans)]
        while time.time() < self.fin:
            self.tour += 1
            for nom, fonction in scenarios:
                if time.time() >= self.fin and nom != "menu":
                    break
                self.scenario(nom, fonction)
            gc.collect()
        return self.tour


# ------------------------------------------------------------ jugement

def _pente(points):
    """Pente (unite par heure) d'une droite passant au mieux par les points (minutes, valeur)."""
    if len(points) < 3:
        return 0.0
    xs, ys = [p[0] / 60.0 for p in points], [p[1] for p in points]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return 0.0 if den == 0 else sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den


def juger(mesures, plantages, tracebacks, minutes):
    constats = []
    statuts = []
    # Fuite : apres l'echauffement = le premier tour complet (chaque ecran charge
    # alors ses donnees une premiere fois : ce n'est pas une fuite). On compare
    # le meme moment de chaque tour (le menu) pour ne pas confondre avec un ecran
    # plus gourmand qu'un autre.
    menus = [(m["t_min"], m["memoire_jeu_mo"]) for m in mesures
             if m["scenario"] == "menu" and m.get("tour", 1) >= 2]
    # Essai du 24/10 (18 min) : les reserves du jeu (textes, tranches de problemes)
    # se remplissent pendant ~8 min puis plafonnent. Une fuite, elle, continue :
    # on prend la pente de la SECONDE moitie (en 2 h : une heure entiere).
    if len(menus) >= 6:
        menus = menus[len(menus) // 2:]
    pente = _pente(menus) if len(menus) >= 3 else 0.0
    debut_mo = mesures[0]["memoire_jeu_mo"] if mesures else 0
    fin_mo = mesures[-1]["memoire_jeu_mo"] if mesures else 0
    s = "vert" if pente < FUITE_VERT else "orange" if pente < FUITE_ORANGE else "rouge"
    statuts.append(s)
    if len(menus) < 3:
        constats.append({"titre": "Trop court pour juger une fuite de mémoire", "gravite": "info",
                         "detail": "Il faut au moins 4 tours (environ 15 minutes) ; le test complet dure 2 heures."})
    elif s != "vert":
        constats.append({"titre": "La mémoire du jeu monte", "gravite": "grave" if s == "rouge" else "moyen",
                         "detail": "+%.0f Mo par heure après l'échauffement (%.0f Mo au début, %.0f Mo à la fin)."
                                   % (pente, debut_mo, fin_mo)})
    # Stockfish : des processus qui s'accumulent.
    n_sf = [m["stockfish"] for m in mesures]
    fin_menu = [m["stockfish"] for m in mesures if m["scenario"] == "menu"]
    s = "vert"
    if fin_menu and fin_menu[-1] > max(fin_menu[:2] + [1]) + 1:
        s = "rouge"
        constats.append({"titre": "Des Stockfish restent ouverts", "gravite": "grave",
                         "detail": "Au menu : %d Stockfish au début, %d à la fin (max %d pendant le test)."
                                   % (fin_menu[0], fin_menu[-1], max(n_sf))})
    statuts.append(s)
    # Ralentissement : temps d'image du premier tiers et du dernier tiers, par ecran.
    lenteurs = {}
    for scenario in sorted({m["scenario"] for m in mesures}):
        serie = [m["image_ms"] for m in mesures if m["scenario"] == scenario and m["image_ms"] > 0]
        if len(serie) >= 3:
            tiers = max(1, len(serie) // 3)
            avant, apres_ = statistics.median(serie[:tiers]), statistics.median(serie[-tiers:])
            if avant > 0:
                lenteurs[scenario] = round(apres_ / avant, 2)
    pire_lenteur = max(lenteurs.values()) if lenteurs else 1.0
    s = "vert" if pire_lenteur < LENTEUR_VERT else "orange" if pire_lenteur < LENTEUR_ORANGE else "rouge"
    statuts.append(s)
    if s != "vert":
        lent = max(lenteurs, key=lenteurs.get)
        constats.append({"titre": "Le jeu ralentit avec le temps (%s)" % lent, "gravite": "moyen",
                         "detail": "Une image de « %s » prend %.1f fois plus de temps à la fin qu'au début."
                                   % (lent, pire_lenteur)})
    # Plantages
    if plantages or tracebacks:
        statuts.append("rouge")
        constats.extend({"titre": "Plantage dans « %s » : %s" % (p["scenario"], p["erreur"][:80]),
                         "gravite": "grave", "detail": "À %.1f min.\n%s" % (p["t_min"], p["trace"])}
                        for p in plantages)
        if tracebacks:
            constats.append({"titre": "Erreurs dans le journal du jeu", "gravite": "grave",
                             "detail": "%d « Traceback » (voir journal.txt), à %s." % (
                                 len(tracebacks), ", ".join(tracebacks[:10]))})
    else:
        statuts.append("vert")
    ordre = ["vert", "orange", "rouge"]
    statut = max(statuts, key=ordre.index)
    resume = ("%d min, %d scénarios : mémoire %+.0f Mo/h, Stockfish max %d, ralentissement x%.2f, "
              "%d plantage(s)" % (minutes, len(mesures), pente, max(n_sf) if n_sf else 0, pire_lenteur,
                                 len(plantages) + len(tracebacks)))
    return {"statut": statut, "resume": resume, "fuite_mo_par_heure": round(pente, 1),
            "memoire_debut_mo": debut_mo, "memoire_fin_mo": fin_mo,
            "stockfish_max": max(n_sf) if n_sf else 0, "lenteurs": lenteurs,
            "plantages": len(plantages) + len(tracebacks), "constats": constats}


def ecrire_le_bilan(rapport, chemin):
    j = rapport["jugement"]
    lignes = ["# Test d'endurance – SickChess", "",
              "Fabriqué par `python outils/endurance.py` le %s (%s)." % (rapport["date"], rapport["machine"]),
              "", "**%s** – %s" % (j["statut"].upper(), j["resume"]), "",
              "| Mesure | Valeur |", "|---|---|",
              "| Durée | %d min, %d tours |" % (rapport["minutes"], rapport["tours"]),
              "| Mémoire du jeu | %.0f Mo au début → %.0f Mo à la fin (%+.0f Mo/h après l'échauffement) |"
              % (j["memoire_debut_mo"], j["memoire_fin_mo"], j["fuite_mo_par_heure"]),
              "| Stockfish ouverts | %d au plus |" % j["stockfish_max"],
              "| Ralentissement (fin / début) | %s |" % (", ".join("%s x%.2f" % kv for kv in sorted(j["lenteurs"].items())) or "-"),
              "| Plantages | %d |" % j["plantages"], ""]
    for c in j["constats"]:
        lignes += ["## %s" % c["titre"], "", c["detail"], ""]
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes))


def main():
    minutes = float(_argument("--minutes", "120"))
    sortie = _argument("--sortie", os.path.join(RACINE, "tests", "endurance"))
    os.makedirs(sortie, exist_ok=True)
    journal = Journal(sys.stdout, os.path.join(sortie, "journal.txt"))
    sys.stdout = sys.stderr = journal
    robot = Robot(minutes, sortie)
    tours = robot.tourner()
    try:
        robot.gm.cleanup_game()
        import moteurs
        moteurs.tout_fermer()
    except Exception:
        pass
    import platform
    rapport = {"date": time.strftime("%Y-%m-%d %H:%M"), "minutes": round(minutes),
               "machine": "%s %s, %d cœurs" % (platform.system(), platform.release(), os.cpu_count() or 0),
               "tours": tours, "mesures": robot.mesures, "plantages": robot.plantages,
               "tracebacks_journal": journal.tracebacks,
               "jugement": juger(robot.mesures, robot.plantages, journal.tracebacks, minutes)}
    with open(os.path.join(sortie, "rapport.json"), "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=1)
    if minutes >= 60:
        ecrire_le_bilan(rapport, os.path.join(RACINE, "docs", "ENDURANCE.md"))
    journal.flush()
    sys.stdout = sys.__stdout__
    print("[ENDURANCE] %s : %s" % (rapport["jugement"]["statut"].upper(), rapport["jugement"]["resume"]))
    for c in rapport["jugement"]["constats"]:
        print("   - %s" % c["titre"])
    os._exit(0 if rapport["jugement"]["statut"] == "vert" else 1)


if __name__ == "__main__":
    main()
