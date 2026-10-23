# outils/banc_essai.py - le banc d'essai complet de SickChess.
#
#     python outils/banc_essai.py              -> tout
#     python outils/banc_essai.py --rapide     -> tests sans Stockfish, mesures plus courtes
#     python outils/banc_essai.py --sections vitesse,menage
#
# Sections : tests (bugs), vitesse (images/s, demarrage), processeur (charge au repos),
# memoire, moteur (Stockfish : vitesse, reglages), menage (code et fichiers inutiles),
# conflits (Git, dependances, syntaxe, noms de fichiers).
#
# Resultats :
#   - tests/banc_essai.json             le dernier passage (lu par Claude, recopie dans la
#                                       page « SickChess – Banc d'essai »)
#   - tests/banc_essai_historique.jsonl un passage par ligne (pour voir les progres)
#   - docs/BANC_ESSAI.md                le meme rapport, lisible
#
# Rien n'est modifie ni supprime dans le jeu : le banc MESURE et SIGNALE. Le menage se
# fait ensuite a la main (skill « menage-code »), un lot a la fois, tests a l'appui.
#
# Les vraies mesures se font sur le PC de Julien (Windows) : Claude Code les lance.
# Dans Cowork (Linux, sans carte graphique ni Stockfish.exe), les chiffres de vitesse
# sont indicatifs et la section « moteur » est grisee.

import hashlib
import json
import os
import platform
import re
import statistics
import subprocess
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))

SECTIONS = ["tests", "vitesse", "processeur", "memoire", "moteur", "menage", "conflits"]
TITRES = {
    "tests": "Bugs (tests automatiques)",
    "vitesse": "Vitesse d'affichage",
    "processeur": "Charge du processeur au repos",
    "memoire": "Mémoire",
    "moteur": "Moteur d'analyse (Stockfish)",
    "menage": "Ménage (code et fichiers inutiles)",
    "conflits": "Conflits et santé du projet",
}
# Budget d'une image a 60 images/s : 16,7 ms. Au-dela de 8 ms, le jeu chauffe le
# processeur pour rien ; au-dela de 16 ms, il saccade.
SEUIL_IMAGE_VERT, SEUIL_IMAGE_ORANGE = 5.0, 10.0
GROS_DOSSIERS = ("puzzles", "syzygy", "publier", "build_amis", ".git", "parties",
                 "__pycache__", "maj_temp", "build", "dist")


def constat(section, titre, detail="", gravite="info"):
    """Un point a montrer a Julien. L'id ne depend que de la section et du titre :
    sa decision (OK / a corriger / ignorer) reste attachee d'un passage a l'autre."""
    cle = hashlib.sha1((section + "|" + titre).encode("utf-8")).hexdigest()[:10]
    return {"id": section[:3] + "-" + cle, "titre": titre, "detail": detail,
            "gravite": gravite}


def pire(*statuts):
    ordre = ["rouge", "orange", "vert", "gris"]
    for s in ordre:
        if s in statuts:
            return s
    return "gris"


def lancer(cmd, timeout=600):
    # GIT_OPTIONAL_LOCKS=0 : « git status » ne pose plus .git/index.lock. Sans ca, lance
    # depuis Cowork (qui n'a pas le droit de supprimer de fichiers), le verrou restait
    # et bloquait les commits de Claude Code (23/10).
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    try:
        p = subprocess.run(cmd, cwd=RACINE, capture_output=True, text=True, env=env,
                           timeout=timeout, encoding="utf-8", errors="replace")
        return p.returncode, p.stdout + p.stderr
    except OSError:          # absent, ou .exe Windows lance sous Linux
        return None, "introuvable"
    except subprocess.TimeoutExpired:
        return None, "trop long"


def fichiers_python():
    for dossier in ("jeu", "outils", "tests"):
        for racine, dirs, fichiers in os.walk(dossier):
            dirs[:] = [d for d in dirs if d not in GROS_DOSSIERS]
            for f in fichiers:
                if f.endswith(".py"):
                    yield os.path.join(racine, f)
    yield "SickChess.py"


def taille_dossier(chemin):
    total = 0
    for racine, _, fichiers in os.walk(chemin):
        for f in fichiers:
            try:
                total += os.path.getsize(os.path.join(racine, f))
            except OSError:
                pass
    return total


def mo(octets):
    return round(octets / 1048576, 1)


# ------------------------------------------------------------------ tests

def section_tests(rapide):
    cmd = [sys.executable, "tests/lancer_tous.py"] + (["--rapide"] if rapide else [])
    debut = time.time()
    code, sortie = lancer(cmd, timeout=1800)
    duree = round(time.time() - debut)
    series, rouges = [], []
    for ligne in sortie.splitlines():
        m = re.match(r"(test_\w+\.py)\s+(VERT|ROUGE)\s+(\d+) OK\s+(\d+) echec", ligne)
        if m:
            series.append(m.group(1))
            if m.group(2) == "ROUGE":
                rouges.append((m.group(1), int(m.group(4))))
    m = re.search(r"(\d+) controles OK", sortie)
    nb_ok = int(m.group(1)) if m else 0
    constats = [constat("tests", "Série en rouge : " + nom,
                        "%d contrôle(s) en échec. Relancer : python tests/%s" % (n, nom),
                        "grave") for nom, n in rouges]
    if code is None:
        constats.append(constat("tests", "Les tests n'ont pas pu tourner", sortie[-300:], "grave"))
    statut = "rouge" if (rouges or code is None) else ("vert" if series else "gris")
    return {"statut": statut,
            "resume": "%d contrôles OK sur %d séries%s, en %d s" % (
                nb_ok, len(series), " (sans Stockfish)" if rapide else "", duree),
            "mesures": {"controles_ok": nb_ok, "series": len(series),
                        "series_rouges": len(rouges), "duree_s": duree},
            "constats": constats}


# ------------------------------------------------------------------ vitesse

PARTIE = ("e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 f3g5 d7d5 e4d5 f6d5 g5f7 e8f7 d1f3 "
          "f7e6 b1c3 c6b4 f3e4 c7c6 d2d4 b4d3").split()


class MoteurFactice:
    def analyser_position(self, fen, profondeur=0, temps_max_ms=0, lignes=1):
        import chess
        coup = next(iter(chess.Board(fen).legal_moves))
        return {"coup": coup.uci(), "evaluation": 0.2, "mat": None,
                "second_evaluation": 0.1, "second_mat": None}


def _ecrans(gm):
    """(nom, fonction qui dessine une image) pour chaque ecran mesure."""
    import chess
    ecrans = [("Menu", lambda: gm.menu.draw())]

    def partie():
        gm.game_mode = "hotseat"
        gm.reglages = {"minutes": 5, "increment": 3, "pendule_active": True,
                       "retourner_plateau": False}
        gm.preparer_partie()
        p = gm.board
        for uci in PARTIE[:12]:
            p.make_move(chess.Move.from_uci(uci))

        def image():
            p.update()
            p.draw()
        return image
    ecrans.append(("Partie", partie))

    def revue():
        from analyse_partie import AnalyseurPartie
        from ecran_revue import EcranRevue
        a = AnalyseurPartie(None, PARTIE, moteur=MoteurFactice())
        r = EcranRevue(gm.screen, a, gm.config, noms=("Toi", "Ordinateur"), resultat="*")
        fin = time.time() + 10
        while getattr(a, "en_cours", False) and time.time() < fin:
            time.sleep(0.05)
        try:
            r.aller_a(10, son=False)
        except Exception:
            pass

        def image():
            r.plateau.update()
            r.draw()
        return image
    ecrans.append(("Revue", revue))

    def simple(module, classe, *args):
        def fabrique():
            mod = __import__(module)
            e = getattr(mod, classe)(gm.screen, *args)
            return e.draw
        return fabrique
    ecrans.append(("Options", simple("ecran_options", "EcranOptions")))
    ecrans.append(("Mes parties", simple("ecran_mes_parties", "EcranMesParties")))
    ecrans.append(("Statistiques", simple("ecran_statistiques", "EcranStatistiques")))
    ecrans.append(("Ouvertures", simple("ecran_entrainement", "EcranEntrainement")))
    if os.path.isdir("puzzles"):
        ecrans.append(("Problèmes", simple("ecran_problemes", "EcranProblemes")))
    return ecrans


def points_chauds(image, n=40, top=6):
    """Ou passe le temps d'une image : les fonctions les plus couteuses (cProfile)."""
    import cProfile
    import pstats
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(n):
        image()
    pr.disable()
    st = pstats.Stats(pr)
    total = st.total_tt or 1
    lignes = []
    for (fichier, ligne, fonction), (cc, nc, tt, ct, _) in st.stats.items():
        nom = fonction if fichier == "~" else "%s:%s %s" % (
            os.path.basename(fichier), ligne, fonction)
        nom = nom.replace("<method ", "").replace("<built-in method ", "").rstrip(">")
        lignes.append((tt, nc, nom))
    lignes.sort(reverse=True)
    # qui ouvre des fichiers pendant le dessin ? (lecture disque a chaque image)
    lecteurs = []
    for (fichier, ligne, fonction), v in st.stats.items():
        if fonction.endswith("io.open>"):
            for (f2, l2, fn2), cv in v[4].items():
                lecteurs.append("%s:%s %s (%d fois par image)" % (
                    os.path.basename(f2), l2, fn2, round(cv[0] / n)))
    return {"postes": [{"fonction": nom, "part_pc": round(100 * tt / total),
                        "appels_par_image": round(nc / n)} for tt, nc, nom in lignes[:top]],
            "lit_des_fichiers": lecteurs}


def _preparer_pygame():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame
    pygame.init()
    return pygame


def section_vitesse(rapide):
    # 1. demarrage a froid, dans un Python neuf
    code_demarrage = (
        "import os,sys,time;t=time.time();"
        "os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy');"
        "sys.path.insert(0,'jeu');import pygame;pygame.init();"
        "from game_manager import GameManager;gm=GameManager('banc');gm.menu.draw();"
        "print('DEMARRAGE',time.time()-t)")
    code, sortie = lancer([sys.executable, "-c", code_demarrage], timeout=120)
    m = re.search(r"DEMARRAGE ([\d.]+)", sortie)
    demarrage = round(float(m.group(1)), 2) if m else None

    pygame = _preparer_pygame()
    from game_manager import GameManager
    gm = GameManager("banc")
    taille = (1280, 720)
    gm.screen = pygame.display.set_mode(taille)
    gm._appliquer_taille(*taille)

    nb = 30 if rapide else 90
    mesures, constats, statuts = {}, [], []
    for nom, fabrique in _ecrans(gm):
        try:
            image = fabrique()
            if nom == "Menu":
                image = fabrique
            for _ in range(5):
                image()
            temps = []
            for _ in range(nb):
                t = time.perf_counter()
                image()
                pygame.display.flip()
                temps.append((time.perf_counter() - t) * 1000)
            med = statistics.median(temps)
            pire_ms = sorted(temps)[int(len(temps) * 0.95) - 1]
            mesures[nom] = {"ms_image": round(med, 2), "ms_pire_5pc": round(pire_ms, 2),
                            "images_par_s_max": int(1000 / med) if med > 0 else None}
            texte_chauds = ""
            if med > SEUIL_IMAGE_VERT:
                chauds = points_chauds(image, n=15 if rapide else 40)
                mesures[nom]["points_chauds"] = chauds
                texte_chauds = "\n\nOù passe le temps d'une image :\n" + "\n".join(
                    "%s : %d %% (%d appels par image)" % (
                        c["fonction"], c["part_pc"], c["appels_par_image"]) for c in chauds["postes"])
                if chauds["lit_des_fichiers"]:
                    constats.append(constat(
                        "vitesse", "« %s » relit des fichiers à chaque image" % nom,
                        "Le disque est lu pendant le dessin, 60 fois par seconde :\n"
                        + "\n".join(chauds["lit_des_fichiers"])
                        + "\nLire une fois à l'ouverture de l'écran (ou après un changement), "
                        "puis garder en mémoire.", "grave"))
            s = "vert" if med <= SEUIL_IMAGE_VERT else ("orange" if med <= SEUIL_IMAGE_ORANGE else "rouge")
            statuts.append(s)
            if s != "vert":
                constats.append(constat(
                    "vitesse", "Écran « %s » lent à dessiner" % nom,
                    "%.1f ms par image (budget conseillé : %.0f ms). Chaque image redessine tout : "
                    "mettre en cache ce qui ne bouge pas (fond, textes, cases)." % (med, SEUIL_IMAGE_VERT)
                    + texte_chauds, "moyen" if s == "orange" else "grave"))
            if pire_ms > 3 * med and pire_ms > 12:
                constats.append(constat(
                    "vitesse", "À-coups sur « %s »" % nom,
                    "Certaines images prennent %.0f ms (médiane %.1f ms) : un calcul ou un "
                    "chargement se fait pendant le dessin." % (pire_ms, med), "moyen"))
        except Exception as e:
            mesures[nom] = {"erreur": str(e)[:160]}
            constats.append(constat("vitesse", "Écran « %s » non mesuré" % nom,
                                    "Erreur pendant la mesure : %s" % str(e)[:200], "info"))
    try:
        gm.cleanup_game()
    except Exception:
        pass
    if demarrage is not None and demarrage > 4:
        constats.append(constat("vitesse", "Démarrage lent",
                                "%.1f s jusqu'au menu (hors musique). Charger plus tard ce qui "
                                "ne sert pas au menu." % demarrage, "moyen"))
        statuts.append("orange")
    meds = [v["ms_image"] for v in mesures.values() if "ms_image" in v]
    lent = max(mesures.items(), key=lambda kv: kv[1].get("ms_image", 0))[0] if meds else "-"
    return {"statut": pire(*statuts) if statuts else "gris",
            "resume": "Démarrage %s s · écran le plus lent : %s (%.1f ms/image)" % (
                demarrage if demarrage is not None else "?", lent, max(meds) if meds else 0),
            "mesures": {"demarrage_s": demarrage, "ecrans": mesures},
            "constats": constats}


# ------------------------------------------------------------------ processeur

def section_processeur(rapide):
    """Fait tourner le menu puis une partie AU REPOS (personne ne touche a rien), avec
    la vraie cadence du jeu (clock.tick(60)), et mesure le temps processeur consomme."""
    pygame = _preparer_pygame()
    from game_manager import GameManager
    import chess
    gm = GameManager("banc")
    gm.screen = pygame.display.set_mode((1280, 720))
    gm._appliquer_taille(1280, 720)
    clock = pygame.time.Clock()
    duree = 2.0 if rapide else 5.0

    def mesurer(image):
        c0, t0 = time.process_time(), time.perf_counter()
        n = 0
        while time.perf_counter() - t0 < duree:
            pygame.event.pump()
            image()
            pygame.display.flip()
            clock.tick(60)
            n += 1
        mur = time.perf_counter() - t0
        return round(100 * (time.process_time() - c0) / mur, 1), round(n / mur)

    resultats, constats = {}, []
    resultats["Menu"] = mesurer(gm.menu.draw)
    gm.game_mode = "hotseat"
    gm.reglages = {"minutes": 5, "increment": 0, "pendule_active": True,
                   "retourner_plateau": False}
    gm.preparer_partie()
    for uci in PARTIE[:8]:
        gm.board.make_move(chess.Move.from_uci(uci))
    resultats["Partie"] = mesurer(lambda: (gm.board.update(), gm.board.draw()))
    try:
        gm.cleanup_game()
    except Exception:
        pass
    coeurs = os.cpu_count() or 1
    statuts = []
    for nom, (pc, ips) in resultats.items():
        # pc = % d'UN coeur. Au repos, un jeu d'echecs devrait rester sous 10 %.
        s = "vert" if pc <= 10 else ("orange" if pc <= 25 else "rouge")
        statuts.append(s)
        if s != "vert":
            constats.append(constat(
                "processeur", "« %s » occupe le processeur sans rien faire" % nom,
                "%.0f %% d'un cœur à %d images/s alors que rien ne bouge. Pistes : ne redessiner "
                "que si quelque chose change, descendre à 30 images/s au repos, mettre en "
                "cache le fond et les textes (skill performance-pygame)." % (pc, ips),
                "moyen" if s == "orange" else "grave"))
    return {"statut": pire(*statuts),
            "resume": " · ".join("%s : %.0f %% d'un cœur (%d img/s)" % (n, v[0], v[1])
                                 for n, v in resultats.items()) + " · %d cœurs logiques" % coeurs,
            "mesures": {n: {"pourcent_un_coeur": v[0], "images_par_s": v[1]}
                        for n, v in resultats.items()} | {"coeurs_logiques": coeurs},
            "constats": constats}


# ------------------------------------------------------------------ memoire

def section_memoire(rapide):
    code_mem = (
        "import os,sys;os.environ.setdefault('SDL_VIDEODRIVER','dummy');"
        "os.environ.setdefault('SDL_AUDIODRIVER','dummy');sys.path.insert(0,'jeu');"
        "import pygame;pygame.init();from game_manager import GameManager;"
        "gm=GameManager('banc');gm.menu.draw();\n"
        "try:\n import psutil;print('MEM',psutil.Process().memory_info().rss)\n"
        "except ImportError:\n import resource;print('MEM',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)\n")
    code, sortie = lancer([sys.executable, "-c", code_mem], timeout=120)
    m = re.search(r"MEM (\d+)", sortie)
    menu_mo = mo(int(m.group(1))) if m else None
    constats = []
    # images trop grandes chargees en memoire
    gros = []
    for dossier in ("assets", "sounds", "music"):
        for racine, _, fichiers in os.walk(dossier):
            for f in fichiers:
                ch = os.path.join(racine, f)
                if os.path.getsize(ch) > 1.5 * 1048576:
                    gros.append((ch, mo(os.path.getsize(ch))))
    for ch, taille in gros:
        constats.append(constat("memoire", "Gros fichier chargé par le jeu : " + ch.replace("\\", "/"),
                                "%.1f Mo. Vérifier s'il peut être plus petit (taille d'image utile, "
                                "son en .ogg)." % taille, "info"))
    s = "gris" if menu_mo is None else ("vert" if menu_mo < 250 else ("orange" if menu_mo < 500 else "rouge"))
    if s in ("orange", "rouge"):
        constats.append(constat("memoire", "Mémoire élevée dès le menu",
                                "%.0f Mo utilisés au menu." % menu_mo, "moyen"))
    try:
        cfg = json.load(open("config.json", encoding="utf-8"))
        hash_mo = cfg.get("analyse_hash_mo") or cfg.get("hash_mo")
    except Exception:
        hash_mo = None
    return {"statut": s,
            "resume": "Jeu au menu : %s Mo" % (menu_mo if menu_mo is not None else "?")
                      + (" · hachage Stockfish réglé : %s Mo" % hash_mo if hash_mo else ""),
            "mesures": {"menu_mo": menu_mo, "gros_fichiers": len(gros)},
            "constats": constats}


# ------------------------------------------------------------------ moteur

def chemin_stockfish():
    ch = os.environ.get("SICKCHESS_STOCKFISH")
    if not ch:
        try:
            ch = json.load(open("config.json", encoding="utf-8")).get("stockfish_path",
                                                                       "moteur/stockfish.exe")
        except Exception:
            ch = "moteur/stockfish.exe"
    # Chemin complet : sous Windows, « moteur/stockfish.exe » n'est pas trouve au lancement.
    return os.path.abspath(ch) if os.path.exists(ch) else None


def section_moteur(rapide):
    ch = chemin_stockfish()
    coeurs = os.cpu_count() or 1
    if not ch:
        return {"statut": "gris", "resume": "Stockfish absent ici : à mesurer sur le PC Windows",
                "mesures": {}, "constats": []}
    # « bench » : la mesure officielle de Stockfish (noeuds par seconde).
    threads = max(1, coeurs - 2)
    args = [ch, "bench", "64", str(threads), "13" if rapide else "16"]
    code, sortie = lancer(args, timeout=170)
    if code is None and sortie == "introuvable":
        return {"statut": "gris", "resume": "Stockfish ne démarre pas sur cette machine",
                "mesures": {}, "constats": []}
    m = re.search(r"Nodes/second\s*:\s*(\d+)", sortie)
    nps = int(m.group(1)) if m else None
    constats = []
    try:
        import cache_manager  # noqa: F401  (le jeu lit ses reglages ici)
    except Exception:
        pass
    statut = "vert" if nps else "orange"
    if not nps:
        constats.append(constat("moteur", "Mesure de Stockfish impossible", sortie[-300:], "moyen"))
    return {"statut": statut,
            "resume": "%s nœuds/s avec %d fils de calcul (sur %d)" % (
                "{:,}".format(nps).replace(",", " ") if nps else "?", threads, coeurs),
            "mesures": {"noeuds_par_s": nps, "threads": threads, "coeurs_logiques": coeurs},
            "constats": constats}


# ------------------------------------------------------------------ menage

def section_menage(rapide):
    constats, mesures = [], {}
    # 1. ruff : imports et variables inutiles, definitions en double
    code, sortie = lancer([sys.executable, "-m", "ruff", "check", "--select", "F401,F811,F841",
                           "--output-format", "concise", "--quiet", "jeu", "outils", "SickChess.py"])
    if code is None or "No module named ruff" in sortie:
        mesures["ruff"] = None
        constats.append(constat("menage", "Outil ruff non installé",
                                "pip install -r requirements-dev.txt", "info"))
    else:
        lignes = [l for l in sortie.splitlines() if re.search(r":\d+:\d+: F\d+", l)]
        mesures["ruff"] = len(lignes)
        par_fichier = {}
        for l in lignes:
            par_fichier.setdefault(l.split(":")[0].replace("\\", "/"), []).append(l)
        if lignes:
            constats.append(constat(
                "menage", "Imports et variables inutiles",
                "%d ligne(s) dans %d fichier(s). Correction sûre et automatique :\n"
                "python -m ruff check --select F401,F841 --fix jeu outils SickChess.py\n\n%s"
                % (len(lignes), len(par_fichier), "\n".join(
                    "%s : %s" % (f, " ; ".join(x.split(" ", 1)[-1] for x in ls[:3]))
                    for f, ls in sorted(par_fichier.items(), key=lambda kv: -len(kv[1])))),
                "faible"))
    # 2. vulture : fonctions, classes, methodes jamais appelees
    code, sortie = lancer([sys.executable, "-m", "vulture", "jeu", "SickChess.py",
                           "outils/vulture_liste_blanche.py", "--min-confidence", "60"])
    if code is None or "No module named vulture" in sortie:
        mesures["vulture"] = None
        constats.append(constat("menage", "Outil vulture non installé",
                                "pip install -r requirements-dev.txt", "info"))
    else:
        lignes = [l for l in sortie.splitlines() if re.search(r"\.py:\d+: unused", l)]
        mesures["vulture"] = len(lignes)
        # les « attribute » (valeur posee mais jamais relue) sont du petit menage ;
        # fonctions, methodes, classes et variables comptent davantage.
        mesures["vulture_fonctions"] = sum(1 for l in lignes if re.search(r"unused (function|method|class|variable)", l))
        par_fichier = {}
        for l in lignes:
            par_fichier.setdefault(l.split(":")[0].replace("\\", "/"), []).append(l)
        # deux constats seulement : fonctions/methodes/classes, puis attributs. Le detail
        # complet est dans tests/banc_essai.json (mesures.menage.vulture_detail).
        detail = {}
        for f, ls in par_fichier.items():
            for x in ls:
                mm = re.search(r"unused (\w+) '([^']+)'", x)
                if mm:
                    genre = "attribut" if mm.group(1) == "attribute" else "code"
                    detail.setdefault(genre, {}).setdefault(f, []).append(
                        "%s (l.%s)" % (mm.group(2), x.split(":")[1]))
        mesures["vulture_detail"] = detail
        for genre, titre, gravite in (("code", "Fonctions et méthodes peut-être jamais utilisées", "moyen"),
                                      ("attribut", "Valeurs rangées mais jamais relues (attributs)", "faible")):
            fichiers = detail.get(genre, {})
            if fichiers:
                n = sum(len(v) for v in fichiers.values())
                constats.append(constat(
                    "menage", titre,
                    "%d élément(s) dans %d fichier(s), à vérifier un par un avant de retirer "
                    "(skill menage-code) :\n%s" % (n, len(fichiers), "\n".join(
                        "%s : %s" % (f, ", ".join(v[:8]) + (" …" if len(v) > 8 else ""))
                        for f, v in sorted(fichiers.items(), key=lambda kv: -len(kv[1])))),
                    gravite))
    # 3. modules de jeu/ que personne n'importe
    tout_le_code = ""
    for f in fichiers_python():
        try:
            tout_le_code += open(f, encoding="utf-8", errors="replace").read() + "\n"
        except OSError:
            pass
    orphelins = []
    for f in sorted(os.listdir("jeu")):
        if f.endswith(".py"):
            nom = f[:-3]
            if not re.search(r"(import|from)\s+[\w., ]*\b%s\b|['\"]%s['\"]" % (nom, nom), tout_le_code):
                orphelins.append(f)
    mesures["modules_orphelins"] = len(orphelins)
    for f in orphelins:
        constats.append(constat("menage", "Fichier jamais importé : jeu/" + f,
                                "Aucun autre fichier ne l'utilise. Probablement un reste de V8.",
                                "moyen"))
    # 4. ressources jamais citees dans le code (a verifier : certains noms sont fabriques)
    textes = tout_le_code
    for f in ("config.json",):
        try:
            textes += open(f, encoding="utf-8").read()
        except OSError:
            pass
    inutilisees = []
    for dossier in ("assets", "sounds", "music", "polices"):
        for racine, _, fichiers in os.walk(dossier):
            for f in fichiers:
                base = os.path.splitext(f)[0]
                if f.lower().endswith((".txt", ".md", ".ofl")) or "LISEZ" in f.upper():
                    continue
                if f not in textes and base not in textes and os.path.basename(racine) not in textes:
                    ch = os.path.join(racine, f)
                    inutilisees.append((ch.replace("\\", "/"), os.path.getsize(ch)))
    mesures["ressources_non_citees"] = len(inutilisees)
    if inutilisees:
        total = sum(t for _, t in inutilisees)
        constats.append(constat("menage", "Ressources jamais citées dans le code",
                                "%d fichier(s), %.1f Mo. Certains noms sont fabriqués par le code "
                                "(ex. « piece_%%s.png ») : vérifier avant de retirer.\n%s"
                                % (len(inutilisees), mo(total),
                                   "\n".join(c for c, _ in inutilisees[:15])), "faible"))
    # 5. doublons exacts (meme contenu)
    vus, doublons = {}, []
    for dossier in ("assets", "sounds", "music", "polices", "assets_src", "jeu", "outils"):
        for racine, dirs, fichiers in os.walk(dossier):
            dirs[:] = [d for d in dirs if d not in GROS_DOSSIERS]
            for f in fichiers:
                ch = os.path.join(racine, f)
                try:
                    if os.path.getsize(ch) < 2048:
                        continue
                    h = hashlib.md5(open(ch, "rb").read()).hexdigest()
                except OSError:
                    continue
                if h in vus:
                    doublons.append((vus[h], ch, os.path.getsize(ch)))
                else:
                    vus[h] = ch
    mesures["doublons"] = len(doublons)
    if doublons:
        constats.append(constat("menage", "Fichiers en double",
                                "%d fichier(s) identiques (%.1f Mo) :\n%s" % (
                                    len(doublons), mo(sum(d[2] for d in doublons)),
                                    "\n".join("%s = %s" % (a.replace("\\", "/"), b.replace("\\", "/"))
                                              for a, b, _ in doublons[:10])), "faible"))
    # 6. place prise par les restes (hors GitHub, mais sur le disque)
    restes = {}
    for d in ("build_amis", "publier", "maj_temp", "build", "dist", "tests/ecrans",
              "tests/ecrans_en", "tests/ecrans_revue"):
        if os.path.isdir(d):
            restes[d] = mo(taille_dossier(d))
    pycache = 0
    for racine, dirs, _ in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ("puzzles", "syzygy", ".git", "publier")]
        if os.path.basename(racine) == "__pycache__":
            pycache += taille_dossier(racine)
    restes["__pycache__ (tous)"] = mo(pycache)
    captures = [f for f in os.listdir("tests") if f.startswith("capture_") and f.endswith(".png")]
    restes["tests/capture_*.png"] = mo(sum(os.path.getsize(os.path.join("tests", f)) for f in captures))
    mesures["restes_mo"] = restes
    total_restes = sum(restes.values())
    if total_restes > 100:
        constats.append(constat("menage", "Restes de fabrication et de tests sur le disque",
                                "%.0f Mo au total (rien de tout ça n'est sur GitHub) :\n%s\n"
                                "« publier » et « build_amis » se refont à chaque version amis."
                                % (total_restes, "\n".join("%s : %.0f Mo" % kv for kv in restes.items())),
                                "info"))
    # 7. lignes de code
    nb_lignes = 0
    for f in os.listdir("jeu"):
        if f.endswith(".py"):
            nb_lignes += sum(1 for _ in open(os.path.join("jeu", f), encoding="utf-8", errors="replace"))
    mesures["lignes_jeu"] = nb_lignes
    nb_points = (mesures.get("ruff") or 0) + (mesures.get("vulture_fonctions") or 0) + 5 * len(orphelins)
    statut = "vert" if nb_points < 15 else ("orange" if nb_points < 150 else "rouge")
    if mesures.get("ruff") is None and mesures.get("vulture") is None:
        statut = "gris"
    return {"statut": statut,
            "resume": "%d lignes de jeu · %s imports/variables inutiles · %s éléments peut-être morts · "
                      "%d fichier(s) jamais importé(s) · %.0f Mo de restes" % (
                          nb_lignes, mesures.get("ruff", "?"), mesures.get("vulture", "?"),
                          len(orphelins), total_restes),
            "mesures": mesures, "constats": constats}


# ------------------------------------------------------------------ conflits

def section_conflits(rapide):
    constats, statuts, mesures = [], [], {}
    # 1. marques de conflit Git oubliees (<<<<<<< ======= >>>>>>>)
    marques = []
    for f in list(fichiers_python()) + ["CLAUDE.md", "config.json"] + \
            [os.path.join("docs", x) for x in os.listdir("docs")]:
        try:
            for i, l in enumerate(open(f, encoding="utf-8", errors="replace"), 1):
                if l.startswith(("<<<<<<< ", ">>>>>>> ")) or l.rstrip() == "=======" and f.endswith(".py"):
                    marques.append("%s:%d" % (f, i))
        except OSError:
            pass
    mesures["marques_conflit"] = len(marques)
    if marques:
        statuts.append("rouge")
        constats.append(constat("conflits", "Conflit Git non résolu dans le code",
                                "\n".join(marques[:10]), "grave"))
    # 2. syntaxe de tous les fichiers Python
    import py_compile
    erreurs = []
    for f in fichiers_python():
        try:
            py_compile.compile(f, doraise=True, cfile=os.devnull if os.name != "nt" else None)
        except py_compile.PyCompileError as e:
            erreurs.append("%s : %s" % (f, str(e.msg).splitlines()[-1]))
        except Exception:
            pass
    mesures["erreurs_syntaxe"] = len(erreurs)
    if erreurs:
        statuts.append("rouge")
        constats.append(constat("conflits", "Fichier Python qui ne se lit pas", "\n".join(erreurs), "grave"))
    # 3. noms de fichiers qui cachent une bibliotheque (ex. jeu/chess.py cacherait python-chess)
    caches = []
    reserves = set(getattr(sys, "stdlib_module_names", ())) | {"pygame", "chess", "psutil", "steam"}
    for f in os.listdir("jeu"):
        if f.endswith(".py") and f[:-3] in reserves and f[:-3] != "steam":
            caches.append(f)
    if caches:
        statuts.append("orange")
        constats.append(constat("conflits", "Fichier qui porte le nom d'une bibliothèque Python",
                                ", ".join(caches) + " : risque d'importer le mauvais module.", "moyen"))
    # 4. dependances compatibles entre elles
    code, sortie = lancer([sys.executable, "-m", "pip", "check"], timeout=60)
    # seules comptent les bibliotheques du jeu et de ses outils
    utiles = ("pygame", "chess", "psutil", "pyinstaller", "ruff", "vulture", "steam")
    lignes_pip = [l for l in sortie.splitlines() if any(u in l.lower() for u in utiles)]
    if code not in (0, None) and not lignes_pip:
        code, sortie = 0, "ok (problemes hors du jeu ignores)"
    if code not in (0, None):
        statuts.append("orange")
        constats.append(constat("conflits", "Bibliothèques Python incompatibles entre elles",
                                sortie.strip()[-500:], "moyen"))
    mesures["pip_check"] = "ok" if code == 0 else "\n".join(lignes_pip)[-200:]
    # 5. Git : travail non enregistre, retard / avance sur GitHub
    code, sortie = lancer(["git", "--no-optional-locks", "status", "--porcelain", "--branch"], timeout=30)
    if code == 0:
        lignes = sortie.splitlines()
        tete = lignes[0] if lignes else ""
        modifs = [l for l in lignes[1:] if l.strip()]
        mesures["git_branche"] = tete.replace("## ", "")
        mesures["git_fichiers_non_enregistres"] = len(modifs)
        avance = re.search(r"ahead (\d+)", tete)
        retard = re.search(r"behind (\d+)", tete)
        if len(modifs) > 15:
            statuts.append("orange")
            constats.append(constat("conflits", "Beaucoup de changements pas encore enregistrés dans Git",
                                    "%d fichiers modifiés depuis le dernier commit. Si Cowork et Claude "
                                    "Code travaillent en même temps, demander à Claude Code un commit "
                                    "avant la séance suivante." % len(modifs), "moyen"))
        if retard:
            statuts.append("orange")
            constats.append(constat("conflits", "GitHub a des changements que ce PC n'a pas",
                                    "%s commit(s) de retard : faire « git pull » avant de modifier." % retard.group(1),
                                    "moyen"))
        if avance:
            constats.append(constat("conflits", "Commits pas encore envoyés sur GitHub",
                                    "%s commit(s) d'avance : penser au push." % avance.group(1), "info"))
    else:
        mesures["git_branche"] = None
    # 6. verrous Git laisses par une operation interrompue
    for verrou in (".git/index.lock", ".git/HEAD.lock"):
        if os.path.exists(verrou):
            statuts.append("orange")
            constats.append(constat("conflits", "Verrou Git oublié : " + verrou,
                                    "Une opération Git a été coupée. Si aucun Git ne tourne, le "
                                    "supprimer (Claude Code peut le faire).", "moyen"))
    # 7. reglages : cles de config.json inconnues du jeu
    try:
        cfg = json.load(open("config.json", encoding="utf-8"))
        tout = "".join(open(f, encoding="utf-8", errors="replace").read()
                       for f in fichiers_python() if f.startswith("jeu"))
        inconnues = [k for k in cfg if ("\"%s\"" % k) not in tout and ("'%s'" % k) not in tout]
        mesures["cles_config_inconnues"] = inconnues
        if inconnues:
            constats.append(constat("conflits", "Réglages de config.json que le jeu ne lit plus",
                                    ", ".join(inconnues[:20]), "faible"))
    except Exception as e:
        constats.append(constat("conflits", "config.json illisible", str(e), "grave"))
        statuts.append("rouge")
    return {"statut": pire(*statuts) if statuts else "vert",
            "resume": "%d conflit(s) Git · %d erreur(s) de syntaxe · dépendances %s · %s fichier(s) "
                      "non enregistré(s)" % (len(marques), len(erreurs),
                                             "OK" if mesures["pip_check"] == "ok" else "à voir",
                                             mesures.get("git_fichiers_non_enregistres", "?")),
            "mesures": mesures, "constats": constats}


# ------------------------------------------------------------------ rapport

def ecrire_markdown(rapport):
    icone = {"vert": "🟢", "orange": "🟠", "rouge": "🔴", "gris": "⚪"}
    l = ["# Banc d'essai – SickChess", "",
         "Dernier passage : %s · %s · %s" % (rapport["date"], rapport["machine"]["resume"],
                                             "rapide" if rapport["rapide"] else "complet"),
         "", "Fabriqué par `python outils/banc_essai.py` (ne pas modifier à la main).", ""]
    for nom in SECTIONS:
        s = rapport["sections"].get(nom)
        if not s:
            continue
        l += ["## %s %s" % (icone.get(s["statut"], ""), TITRES[nom]), "", s["resume"], ""]
        for c in s["constats"]:
            l.append("- **%s** (%s) – %s" % (c["titre"], c["gravite"],
                                            c["detail"].replace("\n", " · ")[:400]))
        l.append("")
    open(os.path.join("docs", "BANC_ESSAI.md"), "w", encoding="utf-8").write("\n".join(l))


def main():
    rapide = "--rapide" in sys.argv
    choisies = SECTIONS
    if "--sections" in sys.argv:
        choisies = [s.strip() for s in sys.argv[sys.argv.index("--sections") + 1].split(",")]
    try:
        import pygame
        version_pygame = pygame.version.ver
    except Exception:
        version_pygame = "?"
    machine = {"systeme": platform.system() + " " + platform.release(),
               "processeur": platform.processor() or platform.machine(),
               "coeurs_logiques": os.cpu_count(),
               "python": platform.python_version(), "pygame": version_pygame}
    machine["resume"] = "%s · %s cœurs · Python %s · pygame %s" % (
        machine["systeme"], machine["coeurs_logiques"], machine["python"], version_pygame)
    rapport = {"date": time.strftime("%Y-%m-%d %H:%M"), "rapide": rapide,
               "machine": machine, "sections": {}}
    # on garde les sections d'un passage precedent qui ne sont pas refaites
    ancien = os.path.join("tests", "banc_essai.json")
    if choisies != SECTIONS and os.path.exists(ancien):
        try:
            rapport["sections"] = json.load(open(ancien, encoding="utf-8")).get("sections", {})
        except Exception:
            pass
    fonctions = {"tests": section_tests, "vitesse": section_vitesse,
                 "processeur": section_processeur, "memoire": section_memoire,
                 "moteur": section_moteur, "menage": section_menage,
                 "conflits": section_conflits}
    for nom in choisies:
        print("== %s ..." % TITRES[nom], flush=True)
        debut = time.time()
        try:
            s = fonctions[nom](rapide)
        except Exception as e:
            import traceback
            s = {"statut": "gris", "resume": "Mesure impossible : %s" % e, "mesures": {},
                 "constats": [constat(nom, "Le banc d'essai a planté sur cette section",
                                      traceback.format_exc()[-600:], "moyen")]}
        s["date"] = rapport["date"]
        s["machine"] = machine["systeme"]
        s["duree_s"] = round(time.time() - debut, 1)
        rapport["sections"][nom] = s
        print("   %s – %s" % (s["statut"].upper(), s["resume"]), flush=True)
        for c in s["constats"][:8]:
            print("     · %s" % c["titre"])
    json.dump(rapport, open(ancien, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join("tests", "banc_essai_historique.jsonl"), "a", encoding="utf-8") as f:
        resume = {"date": rapport["date"], "machine": machine["systeme"], "rapide": rapide,
                  "statuts": {n: s["statut"] for n, s in rapport["sections"].items() if n in choisies},
                  "mesures": {n: s["mesures"] for n, s in rapport["sections"].items() if n in choisies}}
        f.write(json.dumps(resume, ensure_ascii=False) + "\n")
    ecrire_markdown(rapport)
    rouges = [n for n in choisies if rapport["sections"][n]["statut"] == "rouge"]
    print("\nRapport : docs/BANC_ESSAI.md et tests/banc_essai.json")
    print("En rouge : " + ", ".join(rouges) if rouges else "Rien en rouge.")
    return 1 if rouges else 0


if __name__ == "__main__":
    sys.exit(main())
