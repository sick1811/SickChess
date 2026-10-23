# outils/surveiller.py - regarde les performances du PC EN DIRECT pendant que Julien joue.
#
#     python outils/surveiller.py                 -> lance le jeu et mesure jusqu'a sa fermeture
#     python outils/surveiller.py --duree 120     -> s'arrete au bout de 120 s
#     python outils/surveiller.py --pid 1234      -> mesure un jeu deja lance
#
# Chaque seconde : processeur du jeu et de ses Stockfish (en % d'un coeur et en % du PC),
# memoire, charge de chaque coeur du PC, carte graphique (NVIDIA via nvidia-smi, sinon
# compteurs Windows). A la fin : un resume (moyenne, pics, moments ou ca monte).
#
# Resultats : tests/surveillance.csv (toutes les secondes), docs/SURVEILLANCE.md (resume).
# A lancer par Claude Code sur le PC Windows : depuis Cowork (machine Linux), on ne voit
# pas le vrai Windows.

import csv
import os
import shutil
import statistics
import subprocess
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)

try:
    import psutil
except ImportError:
    print("Il faut psutil : pip install -r requirements-dev.txt")
    sys.exit(1)


def carte_graphique():
    """(utilisation %, memoire Mo) de la carte graphique, ou (None, None)."""
    if shutil.which("nvidia-smi"):
        try:
            sortie = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used",
                 "--format=csv,noheader,nounits"], capture_output=True, text=True,
                timeout=3).stdout.strip().splitlines()[0]
            u, m = [float(x) for x in sortie.split(",")]
            return u, m
        except Exception:
            pass
    if os.name == "nt":
        # Compteurs Windows (toutes marques de carte) : moteur 3D le plus charge.
        try:
            sortie = subprocess.run(
                ["typeperf", r"\GPU Engine(*engtype_3D)\Utilization Percentage", "-sc", "1"],
                capture_output=True, text=True, timeout=6).stdout
            lignes = [l for l in sortie.splitlines() if l.startswith('"') and "/" in l[:12]]
            if lignes:
                valeurs = [float(v.strip('"') or 0) for v in lignes[-1].split(",")[1:] if v.strip('"')]
                return (round(min(100.0, sum(valeurs)), 1) if valeurs else None), None
        except Exception:
            pass
    return None, None


def arbre(proc):
    try:
        return [proc] + proc.children(recursive=True)
    except psutil.Error:
        return [proc]


def main():
    duree = None
    if "--duree" in sys.argv:
        duree = float(sys.argv[sys.argv.index("--duree") + 1])
    lance = None
    if "--pid" in sys.argv:
        jeu = psutil.Process(int(sys.argv[sys.argv.index("--pid") + 1]))
    else:
        lance = subprocess.Popen([sys.executable, "SickChess.py"], cwd=RACINE)
        jeu = psutil.Process(lance.pid)
        print("Jeu lance (pid %d). Joue normalement ; ferme le jeu pour finir." % lance.pid)
    coeurs = psutil.cpu_count() or 1
    psutil.cpu_percent(percpu=True)
    gpu_dispo = carte_graphique()[0] is not None
    os.makedirs("tests", exist_ok=True)
    lignes = []
    debut = time.time()
    connus = {}
    try:
        while jeu.is_running() and (duree is None or time.time() - debut < duree):
            if jeu.status() == psutil.STATUS_ZOMBIE:
                break
            procs = arbre(jeu)
            for p in procs:
                if p.pid not in connus:
                    connus[p.pid] = p
                    try:
                        p.cpu_percent(None)
                    except psutil.Error:
                        pass
            time.sleep(1.0)
            jeu_cpu = sf_cpu = 0.0
            jeu_mo = sf_mo = 0.0
            nb_sf = 0
            for p in arbre(jeu):
                try:
                    p = connus.get(p.pid, p)
                    c = p.cpu_percent(None)
                    m = p.memory_info().rss / 1048576
                    if "stockfish" in p.name().lower():
                        sf_cpu += c
                        sf_mo += m
                        nb_sf += 1
                    else:
                        jeu_cpu += c
                        jeu_mo += m
                except psutil.Error:
                    pass
            par_coeur = psutil.cpu_percent(percpu=True)
            gpu, gpu_mo = carte_graphique() if gpu_dispo else (None, None)
            t = round(time.time() - debut)
            lignes.append({
                "seconde": t, "jeu_pc_un_coeur": round(jeu_cpu, 1),
                "stockfish_pc_un_coeur": round(sf_cpu, 1), "stockfish_nb": nb_sf,
                "total_pc_du_pc": round((jeu_cpu + sf_cpu) / coeurs, 1),
                "pc_global": round(sum(par_coeur) / len(par_coeur), 1),
                "coeur_le_plus_charge": max(par_coeur),
                "jeu_mo": round(jeu_mo), "stockfish_mo": round(sf_mo),
                "memoire_pc_pc": psutil.virtual_memory().percent,
                "gpu_pc": gpu, "gpu_mo": gpu_mo})
            d = lignes[-1]
            print("%4ds  jeu %5.1f%% d'un coeur | Stockfish x%d %6.1f%% | PC %5.1f%% | "
                  "memoire jeu %4d Mo + SF %4d Mo | carte graphique %s" % (
                      t, d["jeu_pc_un_coeur"], nb_sf, d["stockfish_pc_un_coeur"], d["pc_global"],
                      d["jeu_mo"], d["stockfish_mo"], "%s%%" % gpu if gpu is not None else "-"),
                  flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        if lance is not None and duree is not None and lance.poll() is None:
            lance.terminate()
    if not lignes:
        print("Aucune mesure.")
        return 1
    with open(os.path.join("tests", "surveillance.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(lignes)
    ecrire_resume(lignes, coeurs, gpu_dispo)
    return 0


def ecrire_resume(lignes, coeurs, gpu_dispo):
    def stat(cle):
        v = [l[cle] for l in lignes if l[cle] is not None]
        if not v:
            return None
        return {"moyenne": round(statistics.mean(v), 1), "pic": max(v),
                "median": round(statistics.median(v), 1)}
    jeu = stat("jeu_pc_un_coeur")
    sf = stat("stockfish_pc_un_coeur")
    pc = stat("pc_global")
    mem = stat("jeu_mo")
    sfm = stat("stockfish_mo")
    gpu = stat("gpu_pc")
    calme = [l["jeu_pc_un_coeur"] for l in lignes if l["stockfish_pc_un_coeur"] < 5]
    pics = sorted(lignes, key=lambda l: -(l["jeu_pc_un_coeur"] + l["stockfish_pc_un_coeur"]))[:5]
    r = ["# Surveillance en direct – SickChess", "",
         "Le %s · %d s de mesure · %d cœurs logiques · %s" % (
             time.strftime("%d/%m/%Y %H:%M"), lignes[-1]["seconde"], coeurs,
             "carte graphique mesurée" if gpu_dispo else "carte graphique non mesurée"),
         "", "Fabriqué par `python outils/surveiller.py`. Détail seconde par seconde : "
         "`tests/surveillance.csv`.", "",
         "| Mesure | Moyenne | Pic |", "|---|---:|---:|",
         "| Jeu (dessin, sons, logique), en %% d'un cœur | %s | %s |" % (jeu["moyenne"], jeu["pic"]),
         "| Stockfish (tous), en %% d'un cœur | %s | %s |" % (sf["moyenne"], sf["pic"]),
         "| Tout le PC, en %% | %s | %s |" % (pc["moyenne"], pc["pic"]),
         "| Mémoire du jeu (Mo) | %s | %s |" % (mem["moyenne"], mem["pic"]),
         "| Mémoire de Stockfish (Mo) | %s | %s |" % (sfm["moyenne"], sfm["pic"])]
    if gpu:
        r.append("| Carte graphique, en %% | %s | %s |" % (gpu["moyenne"], gpu["pic"]))
    r += ["", "**Jeu seul quand Stockfish ne calcule pas** (repos, menus) : %s %% d'un cœur en "
          "moyenne%s." % (round(statistics.mean(calme), 1) if calme else "?",
                          " — au-dessus de 10 %, le dessin travaille pour rien (skill performance-pygame)"
                          if calme and statistics.mean(calme) > 10 else ""),
          "", "Les 5 secondes les plus chargées :", ""]
    for l in pics:
        r.append("- %d s : jeu %s %%, Stockfish ×%d %s %%, PC %s %%" % (
            l["seconde"], l["jeu_pc_un_coeur"], l["stockfish_nb"], l["stockfish_pc_un_coeur"],
            l["pc_global"]))
    open(os.path.join("docs", "SURVEILLANCE.md"), "w", encoding="utf-8").write("\n".join(r) + "\n")
    print("\n".join(r))


if __name__ == "__main__":
    sys.exit(main())
