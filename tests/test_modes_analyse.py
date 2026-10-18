# tests/test_modes_analyse.py - les trois facons d'analyser (18/10, seance 13).
#     python tests/test_modes_analyse.py
# Choix de Julien : plusieurs modes, le CALCUL FIXE par defaut (meme quantite
# de calcul pour chaque position, comme lichess), la profondeur et le temps
# au choix dans Options -> Partie.
# Sans Stockfish : moteurs factices. Avec Stockfish (config.json ou variable
# SICKCHESS_STOCKFISH) : la commande « go nodes » est verifiee pour de vrai.

import json
import os
import shutil
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import analyse_partie as A

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


class Factice:
    """Moteur de test : note chaque demande. 'profondeur_au_temps' simule un
    PC lent (profondeur atteinte = temps en secondes x 3)."""
    def __init__(self, profondeur_au_temps=False, connait_les_noeuds=True):
        self.appels = []
        self.lent = profondeur_au_temps
        self.noeuds_ok = connait_les_noeuds

    def analyser_position(self, fen, profondeur, temps, lignes=1, **reste):
        if "noeuds" in reste and not self.noeuds_ok:
            raise TypeError("moteur sans noeuds")
        noeuds = reste.get("noeuds", 0)
        self.appels.append((profondeur, noeuds, temps, lignes))
        atteinte = profondeur or (int(temps / 1000 * 3) if self.lent else 28)
        coups = [c.uci() for c in list(chess.Board(fen).legal_moves)[:3]]
        lignes_moteur = [{"coup": u, "cp": 30 - 5 * n, "mat": None,
                          "profondeur": atteinte, "suite": []}
                         for n, u in enumerate(coups[:lignes])]
        return {"coup": coups[0], "evaluation": 0.3, "mat": None,
                "profondeur": atteinte, "lignes": lignes_moteur,
                "second_evaluation": 0.25 if lignes > 1 else None,
                "second_mat": None, "noeuds": noeuds or 1000000, "temps_ms": 500}


COUPS = ["e2e4", "e7e5", "g1f3", "b8c6"]

print("1. Le reglage choisi dans Options")
verifier(A.puissance_de({}) == "calcul_maximale", "rien de regle : calcul fixe maximal")
verifier(A.puissance_de({"analyse_puissance": "forte"}) == "calcul_forte",
         "ancien reglage « forte » (26) : calcul fixe fort")
verifier(A.puissance_de({"analyse_mode": "profondeur", "analyse_niveau": "maximale"})
         == "profondeur_maximale", "profondeur maximale = 30")
verifier(A.REGLAGES["profondeur_maximale"]["profondeur"] == 30, "profondeur 30")
verifier(A.puissance_de({"analyse_mode": "temps", "analyse_niveau": "rapide"})
         == "temps_rapide", "temps rapide")
verifier(A.puissance_de({"analyse_mode": "n'importe quoi"}) == "calcul_maximale",
         "valeur inconnue : retour au defaut")
for nom in ("rapide", "normale", "forte", "maximale"):
    verifier(nom in A.REGLAGES, "ancien nom « %s » toujours accepte" % nom)

print("2. Calcul fixe : la meme quantite de calcul pour chaque position")
m = Factice()
a = A.AnalyseurPartie(None, COUPS, None, "calcul_maximale", moteur=m)
a._travailler()
verifier(a.terminee(), "analyse terminee")
finales = [c for c in m.appels if c[1] == 50000000]
verifier(len(finales) == len(COUPS) + 1 and all(c[3] == 1 for c in finales),
         "passe finale : 50 millions de noeuds, meilleur coup seul, pour chaque position")
verifier(all(c[0] == 0 for c in finales), "aucune profondeur imposee")
verifier(any(c[1] == 10000000 and c[3] == 3 for c in m.appels),
         "trois meilleurs coups a 10 millions de noeuds")
verifier(not any(c[2] > 240000 for c in m.appels), "jamais refaite (pas de profondeur minimale)")
verifier("profondeur 28 à 28" in a.texte_avancement(),
         "fin : %s" % a.texte_avancement())
verifier("50 millions" in a.description(), "description : %s" % a.description())
ancien = Factice(connait_les_noeuds=False)
b = A.AnalyseurPartie(None, COUPS[:2], None, "calcul_rapide", moteur=ancien)
b._travailler()
verifier(b.terminee(), "un moteur qui ne connait pas les noeuds marche encore")

print("3. Temps : refaite une fois si la profondeur minimale manque")
lent = Factice(profondeur_au_temps=True)
t = A.AnalyseurPartie(None, COUPS[:2], None, "temps_forte", moteur=lent)
t._travailler()
temps_finals = sorted(set(c[2] for c in lent.appels if c[0] == 0 and c[3] == 1))
verifier(temps_finals == [7000, 14000],
         "7 s donnent la profondeur 21 < 26 : refaite avec 14 s (%s)" % temps_finals)
rapide = Factice(profondeur_au_temps=True)
t2 = A.AnalyseurPartie(None, COUPS[:2], None, "temps_maximale", moteur=rapide)
t2._travailler()
verifier(sorted(set(c[2] for c in rapide.appels if c[0] == 0 and c[3] == 1)) == [15000],
         "15 s donnent la profondeur 45 : pas refaite")

print("4. Profondeur : comme avant (30, trois coups a 22)")
p = Factice()
c = A.AnalyseurPartie(None, COUPS[:2], None, "profondeur_maximale", moteur=p)
c._travailler()
verifier((22, 0, 6000, 3) in p.appels and any(x[0] == 30 for x in p.appels),
         "trois coups a 22, puis la passe a 30")
verifier(c.texte_avancement() == "Analyse terminée (profondeur 30)", c.texte_avancement())

print("5. Une analyse enregistree est reprise si elle est assez forte")
dossier = tempfile.mkdtemp()
try:
    cache = os.path.join(dossier, "partie.analyse.json")
    a.definir_fichier_cache(cache)
    with open(cache, encoding="utf-8") as f:
        d = json.load(f)
    verifier(d.get("effort") == 5 and d.get("reglage") == "calcul_maximale",
             "effort et reglage enregistres")
    for nom, attendu in (("profondeur_maximale", True), ("calcul_forte", True),
                         ("rapide", True)):
        x = A.AnalyseurPartie(None, COUPS, None, nom, moteur=Factice(),
                              fichier_cache=cache)
        verifier(x.terminee() == attendu, "analyse calcul maximale relue en « %s »" % nom)
    # Une ancienne analyse (17/10) : seule la profondeur etait notee.
    d.pop("effort"); d.pop("reglage"); d["profondeur"] = 30
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(d, f)
    x = A.AnalyseurPartie(None, COUPS, None, "calcul_maximale", moteur=Factice(),
                          fichier_cache=cache)
    verifier(x.terminee(), "ancienne analyse a la profondeur 30 : pas refaite")
    d["profondeur"] = 26
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(d, f)
    x = A.AnalyseurPartie(None, COUPS, None, "calcul_maximale", moteur=Factice(),
                          fichier_cache=cache)
    verifier(not x.terminee(), "ancienne analyse a 26 : refaite en calcul maximal")
    x = A.AnalyseurPartie(None, COUPS, None, "calcul_rapide", moteur=Factice(),
                          fichier_cache=cache)
    verifier(x.terminee(), "... mais suffit au calcul rapide")
finally:
    shutil.rmtree(dossier, ignore_errors=True)

print("6. Le temps restant s'affiche")
e = A.AnalyseurPartie(None, COUPS * 1, None, "calcul_maximale", moteur=Factice())
e.en_cours, e._ouvriers = True, 1
for k in range(len(e.fens)):
    e._analyser(e._moteur_fourni, k, 1)
e._analyser(e._moteur_fourni, 0, 2)
e._analyser(e._moteur_fourni, 1, 2)
reste = e.temps_restant()
verifier(reste is not None and reste > 0, "estimation : %s s" % reste)
verifier("·" in e.texte_avancement(), "texte : %s" % e.texte_avancement())
e.en_cours = False
verifier(e.temps_restant() is None, "rien quand l'analyse est arretee")

print("7. Options -> Partie : deux lignes, en francais et en anglais")
import ecran_options
cles = [r.cle for _i, _n, rs in ecran_options._onglets() for r in rs]
verifier("analyse_mode" in cles and "analyse_niveau" in cles, "deux lignes dans Options")
verifier(ecran_options.DEFAUTS_EN_PLUS["analyse_mode"] == "calcul", "calcul fixe par defaut")
import langue
langue.regler("en")
for texte in ("Façon d'analyser", "Puissance de l'analyse", "Calcul fixe",
              "Analyse fine... 40 %  ·  environ 3 min",
              "Analyse terminée (profondeur 27 à 33)"):
    verifier(langue.traduire(texte) != texte, "anglais : %s" % langue.traduire(texte))
langue.regler("fr")

print("7b. Hachage : 6 Go au total (demande de Julien), sans etouffer un petit PC")
verifier(A.HASH_ANALYSE_MB == 6144, "6 Go demandes")
verifier(A.hachage_total_mo(16384) == 6144, "PC a 16 Go : 6 Go")
verifier(A.hachage_total_mo(32768) == 6144, "PC a 32 Go : 6 Go (jamais plus)")
verifier(A.hachage_total_mo(8192) == 2048, "PC a 8 Go : 2 Go seulement")
verifier(A.hachage_total_mo(4096) == 512, "PC a 4 Go : 512 Mo")
verifier(A.memoire_totale_mo() is None or A.memoire_totale_mo() > 500,
         "memoire de ce PC lue : %s Mo" % A.memoire_totale_mo())
appels = []
import moteurs
ancien_n = moteurs.moteur_d_analyse_n
moteurs.moteur_d_analyse_n = lambda i, c, threads=None, hash_mb=0, creer=True: \
    appels.append(hash_mb) or None
try:
    ancien_cpu = os.cpu_count
    os.cpu_count = lambda: 12
    s = A.AnalyseurPartie(None, COUPS, "x", suivi=True)
    s._moteur(0, 1)
    verifier(appels[-1] == A.hachage_total_mo() // 3,
             "pendant la partie : %d Mo (le tiers, deux autres moteurs viendront)" % appels[-1])
    s.suivi = False
    s._moteur(1, 3)
    verifier(appels[-1] == A.hachage_total_mo() // 3, "apres : 3 x %d Mo" % appels[-1])
finally:
    moteurs.moteur_d_analyse_n = ancien_n
    os.cpu_count = ancien_cpu

print("8. Stockfish pour de vrai : go nodes")
chemin = os.environ.get("SICKCHESS_STOCKFISH")
if not chemin:
    try:
        with open("config.json", encoding="utf-8") as f:
            chemin = json.load(f).get("stockfish_path")
    except (OSError, ValueError):
        chemin = None
moteur = None
if chemin and os.path.exists(chemin):
    try:
        from engine import StockfishEngine
        moteur = StockfishEngine(chemin)
        envoyes = []
        envoyer = moteur._send_command
        moteur._send_command = lambda c: envoyes.append(c) or envoyer(c)
        moteur.configurer_pour_analyse(1, 100)
        verifier("setoption name Hash value 100" in envoyes,
                 "taille exacte envoyee a Stockfish (100 Mo, avant arrondie a 64)")
        moteur.configurer_pour_analyse(1, 64)
    except Exception as souci:
        print("  (Stockfish ne demarre pas : %s)" % souci)
        moteur = None
if moteur is None:
    print("  (Stockfish absent : partie sautee)")
else:
    d = moteur.analyser_position(chess.STARTING_FEN, 0, 60000, lignes=1,
                                 noeuds=300000)
    verifier(d is not None and 300000 <= d.get("noeuds", 0) < 400000,
             "300 000 noeuds demandes : %s faits" % (d or {}).get("noeuds"))
    verifier(d.get("temps_ms") is not None and d.get("profondeur", 0) >= 10,
             "temps (%s ms) et profondeur (%s) rendus" % (d.get("temps_ms"), d.get("profondeur")))
    moteur.quit()

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
