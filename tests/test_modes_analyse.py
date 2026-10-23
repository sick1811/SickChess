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
        blancs = chess.Board(fen).turn == chess.WHITE
        return {"coup": coups[0], "evaluation": 0.3 if blancs else -0.3, "mat": None,
                "profondeur": atteinte, "lignes": lignes_moteur,
                "second_evaluation": 0.25 if lignes > 1 else None,
                "second_mat": None, "noeuds": noeuds or 1000000, "temps_ms": 500}


COUPS = ["e2e4", "e7e5", "g1f3", "b8c6"]

print("1. Le reglage choisi dans Options")
verifier(A.puissance_de({}) == "calcul_forte", "rien de regle : calcul fixe fort (18/10 (14))")
verifier(A.puissance_de({"analyse_puissance": "maximale"}) == "calcul_forte",
         "ancien defaut « maximale » seul : calcul fixe fort")
verifier(A.puissance_de({"analyse_puissance": "forte"}) == "calcul_forte",
         "ancien reglage « forte » (26) : calcul fixe fort")
verifier(A.puissance_de({"analyse_mode": "profondeur", "analyse_niveau": "maximale"})
         == "profondeur_maximale", "profondeur maximale = 30")
verifier(A.REGLAGES["profondeur_maximale"]["profondeur"] == 30, "profondeur 30")
verifier(A.puissance_de({"analyse_mode": "temps", "analyse_niveau": "rapide"})
         == "temps_rapide", "temps rapide")
verifier(A.puissance_de({"analyse_mode": "n'importe quoi"}) == "calcul_forte",
         "valeur inconnue : retour au defaut")
for nom in ("rapide", "normale", "forte", "maximale"):
    verifier(nom in A.REGLAGES, "ancien nom « %s » toujours accepte" % nom)

print("2. Calcul fixe : analyse rapide partout, verification la ou le verdict hesite")
HORS_LIVRE = ["h2h3", "a7a6", "h1h2", "a8a7", "h2h1", "a7a8"]   # 1.h3 seul est theorique
m = Factice()
a = A.AnalyseurPartie(None, HORS_LIVRE, None, "calcul_maximale", moteur=m)
a._travailler()
verifier(a.terminee(), "analyse terminee")
verifier(any(c[1] == 5000000 and c[3] == 3 for c in m.appels),
         "analyse rapide : trois meilleurs coups a 5 millions de noeuds")
verifier(not [c for c in m.appels if c[1] == 50000000],
         "partie calme (+0.30 partout) : aucune verification necessaire")
verifier(len(a.allegees) == len(HORS_LIVRE) + 1, "toutes les pastilles sures : %d positions"
         % len(a.allegees))
verifier(all(a.detail(i)["pret"] for i in range(len(HORS_LIVRE))), "toutes les pastilles posees")


class Hesitant(Factice):
    """Apres 2.Rh2 (position 3 et suivantes), les Blancs perdent ~4 points de
    chances : tout pres du seuil Imprecision (5). Le verdict hesite."""
    def analyser_position(self, fen, profondeur, temps, lignes=1, **reste):
        d = Factice.analyser_position(self, fen, profondeur, temps, lignes, **reste)
        plateau = chess.Board(fen)
        if plateau.fullmove_number >= 3 or (plateau.fullmove_number == 2
                                            and plateau.turn == chess.BLACK):
            blanc = -0.11
            d["evaluation"] = blanc if plateau.turn == chess.WHITE else -blanc
            for l in d["lignes"]:
                l["cp"] = int(d["evaluation"] * 100)
        return d


h = Hesitant()
b = A.AnalyseurPartie(None, HORS_LIVRE, None, "calcul_maximale", moteur=h)
b._travailler()
perte = A.annotations.chances_de_gagner(0.3) - A.annotations.chances_de_gagner(-0.11)
verifiees = [k for k in range(len(b.fens)) if k not in b.allegees]
verifier(b.terminee() and verifiees == [2, 3],
         "perte de %.1f points (seuil Imprecision : 5) : positions 2 et 3 verifiees, %s" % (perte, verifiees))
verifier(len([c for c in h.appels if c[1] == 50000000]) == 2,
         "deux verifications a 50 millions, pas plus")
verifier(not [c for c in h.appels if c[2] > 240000], "jamais refaite (pas de profondeur minimale)")
verifier("vérifiée (2 sur 7)" in b.description(), "description : %s" % b.description())
verifier("profondeur 28 à 28" in b.texte_avancement(), "fin : %s" % b.texte_avancement())
ancien = Factice(connait_les_noeuds=False)
b = A.AnalyseurPartie(None, COUPS[:2], None, "calcul_rapide", moteur=ancien)
b._travailler()
verifier(b.terminee(), "un moteur qui ne connait pas les noeuds marche encore")

print("2b. Pas de passe profonde quand elle ne changerait rien (18/10)")
class Gagnant(Factice):
    def analyser_position(self, fen, profondeur, temps, lignes=1, **reste):
        d = Factice.analyser_position(self, fen, profondeur, temps, lignes, **reste)
        d["evaluation"] = 9.0
        for l in d["lignes"]:
            l["cp"] = 900
        return d
g = Gagnant()
x = A.AnalyseurPartie(None, HORS_LIVRE, None, "calcul_maximale", moteur=g)
x._travailler()
verifier(x.terminee() and not [c for c in g.appels if c[1] == 50000000],
         "partie jouee (+9) : aucune passe profonde, %d positions allegees" % len(x.allegees))
livre = Factice()
y = A.AnalyseurPartie(None, COUPS, None, "calcul_maximale", moteur=livre)
y._travailler()
verifier({0, 1, 2, 3} <= y.allegees, "theorie (1.e4 e5 2.Nf3 Nc6) : positions 0 a 3 allegees (%s)"
         % sorted(y.allegees))
verifier(y.detail(0)["note"] == "theorique", "les coups de theorie gardent leur pastille")

print("2c. Threads : jamais plus que de processeurs (bug des 35 min)")
ancien_cpu = os.cpu_count
os.cpu_count = lambda: 12
try:
    z = A.AnalyseurPartie(None, COUPS, "x")
    verifier([z._threads_par_moteur(c) for c in (1, 2, 3)] == [4, 4, 4],
             "apres la partie : 3 moteurs x 4 threads, quel que soit l'ordre de demarrage")
    z.suivi = True
    verifier(z._threads_par_moteur(1) == 6, "pendant la partie : 1 moteur, 6 threads")
finally:
    os.cpu_count = ancien_cpu

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
        x = A.AnalyseurPartie(None, HORS_LIVRE, None, nom, moteur=Factice(),
                              fichier_cache=cache)
        verifier(x.terminee() == attendu, "analyse calcul maximale relue en « %s »" % nom)
    # Une ancienne analyse (17/10) : seule la profondeur etait notee.
    d.pop("effort"); d.pop("reglage"); d["profondeur"] = 30
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(d, f)
    x = A.AnalyseurPartie(None, HORS_LIVRE, None, "calcul_maximale", moteur=Factice(),
                          fichier_cache=cache)
    verifier(x.terminee(), "ancienne analyse a la profondeur 30 : pas refaite")
    d["profondeur"] = 26
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(d, f)
    x = A.AnalyseurPartie(None, HORS_LIVRE, None, "calcul_maximale", moteur=Factice(),
                          fichier_cache=cache)
    verifier(not x.terminee(), "ancienne analyse a 26 : refaite en calcul maximal")
    x = A.AnalyseurPartie(None, HORS_LIVRE, None, "calcul_rapide", moteur=Factice(),
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

print("7b. Hachage : 4 Go au total (choix de Julien, 18/10), sans etouffer un petit PC")
verifier(A.HASH_ANALYSE_MB == 4096, "4 Go demandes")
verifier(A.hachage_total_mo(16384) == 4096, "PC a 16 Go : 4 Go")
verifier(A.hachage_total_mo(32768) == 4096, "PC a 32 Go : 4 Go (jamais plus)")
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

print("9. Surveillance du 23/10 : moteurs fermes apres l'analyse, priorite basse")


class MoteurFaux:
    def __init__(self):
        self.ferme = False

    def est_vivant(self):
        return not self.ferme

    def quit(self):
        self.ferme = True


faux = {role: MoteurFaux() for role in ("jeu", "analyse", "analyse-2", "analyse-3",
                                        moteurs.ROLE_VARIANTE)}
sauves = dict(moteurs._moteurs)
moteurs._moteurs.clear()
moteurs._moteurs.update(faux)
try:
    verifier(moteurs.liberer_les_renforts(3) == 2, "les 2 moteurs de renfort sont fermes")
    verifier(faux["analyse-2"].ferme and faux["analyse-3"].ferme, "analyse-2 et analyse-3 fermes")
    verifier(not faux["analyse"].ferme and not faux["jeu"].ferme,
             "le premier moteur d'analyse et le moteur de jeu restent")
    verifier(not faux[moteurs.ROLE_VARIANTE].ferme, "le moteur des variantes reste (revue ouverte)")
    verifier(moteurs.liberer_la_variante() and faux[moteurs.ROLE_VARIANTE].ferme,
             "en quittant la revue, le moteur des variantes est ferme")
finally:
    moteurs._moteurs.clear()
    moteurs._moteurs.update(sauves)

if chemin and os.path.exists(chemin) and os.name == "nt":
    try:
        import psutil
    except ImportError:
        psutil = None
    if psutil is not None:
        m = moteurs.moteur_d_analyse_n(7, chemin, threads=1, hash_mb=16)
        try:
            p = psutil.Process(m.process.pid)
            verifier(p.nice() == psutil.BELOW_NORMAL_PRIORITY_CLASS,
                     "moteur d'analyse en priorite basse (%s)" % p.nice())
        finally:
            moteurs.liberer(moteurs.role_d_analyse(7))

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
