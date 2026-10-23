"""La recette faite par Claude : les lignes de docs/RECETTE.md qu'un programme peut verifier.

    python outils/recette_auto.py            (Stockfish necessaire ; Windows ou Linux)

On pilote le VRAI jeu comme un joueur : clics souris sur les cases et les boutons,
touches du clavier, avec le vrai Stockfish, dans une fenetre invisible (rien ne
s'affiche, on peut continuer a utiliser le PC). Ce qui demande des yeux, Steam ou
un ami reste a Julien.

Ecrit tests/recette_auto/resultats.json ({R-xxx: [[ok, texte], ...]}) et des
captures v_*.png dans le meme dossier. Dossier temporaire pour le profil, les
parties et la sauvegarde : tes donnees ne sont pas touchees.
24/10/2026 (travail p35 a p37). Code de sortie 0 si tout est vert.
"""
import os, sys, time, json, tempfile
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE); sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ["SDL_VIDEODRIVER"] = "dummy"; os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame, chess, psutil
pygame.init()
ecran = pygame.display.set_mode((1280, 720))
import asset_manager
TEMP = tempfile.mkdtemp(prefix="verif_"); asset_manager.dossier_ecriture = lambda: TEMP
import sauvegarde; sauvegarde.FICHIER = os.path.join(TEMP, "partie_en_cours.json")
import ui, board_geometry as geo
SF = os.environ.get("SICKCHESS_STOCKFISH")
if not SF:
    try:
        with open("config.json", encoding="utf-8") as f:
            SF = json.load(f).get("stockfish_path")
    except (OSError, ValueError):
        SF = None
    SF = SF or os.path.join("moteur", "stockfish.exe")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RACINE, "tests", "recette_auto")
os.makedirs(OUT, exist_ok=True)
R = {}

def note(cle, ok, texte):
    R.setdefault(cle, []).append((bool(ok), texte))
    print(("  OK   " if ok else "  NON  ") + cle + " : " + texte, flush=True)

def stockfish_cpu(secondes=1.5):
    procs = [p for p in psutil.process_iter(["name", "cmdline"])
             if "stockfish" in (p.info["name"] or "") or any("stockfish" in c for c in (p.info["cmdline"] or []))]
    for p in procs:
        try: p.cpu_percent(None)
        except Exception: pass
    time.sleep(secondes)
    tot = 0.0
    for p in procs:
        try: tot += p.cpu_percent(None)
        except Exception: pass
    return len(procs), tot

def clic(pos, bouton=1):
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=bouton, pos=pos))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=bouton, pos=pos))

def touche(k, mod=0):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k, mod=mod, unicode=""))

def images(ecr, n=1, pause=0.03):
    """n images de l'ecran : evenements (par ui.evenements, comme le jeu), dessin, affichage."""
    rep = None
    for _ in range(n):
        for ev in ui.evenements():
            r = ecr.handle_event(ev)
            rep = r if r is not None else rep
        ecr.draw(); ui.afficher(); time.sleep(pause)
    return rep

def case(ecr, nom):
    return geo.centre_case(chess.parse_square(nom), ecr.plateau.SQ_SIZE, ecr.plateau.flipped)

def jouer(ecr, de, a):
    """Clic-clic, comme un joueur."""
    clic(case(ecr, de)); images(ecr, 2); clic(case(ecr, a)); images(ecr, 3)

def glisser(ecr, de, a):
    p1, p2 = case(ecr, de), case(ecr, a)
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=p1))
    images(ecr, 1)
    pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, pos=p2, rel=(0, 0), buttons=(1, 0, 0)))
    images(ecr, 1)
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=p2))
    images(ecr, 3)

def attendre(ecr, cond, s=20):
    fin = time.time() + s
    while time.time() < fin:
        images(ecr, 1)
        if cond(): return True
    return False

from game_manager import GameManager
gm = GameManager("verif")
gm.screen = ecran

# ------------------------------------------------------------ analyse libre (t82, t83, R-140..143)
print("== Analyse libre")
from ecran_analyse_libre import EcranAnalyseLibre
gm.au_menu = False
e = EcranAnalyseLibre(ecran, {}, stockfish_path=SF)
debut = time.time()
ok = attendre(e, lambda: len(e.lignes()) == 3, 25)
note("R-140", ok, "3 lignes de Stockfish en %.1f s (dont ~4,5 s de demarrage de Stockfish dans le cloud)" % (time.time() - debut))
p1 = e.analyse.resultat()["profondeur"]; time.sleep(2); images(e, 3); p2 = e.analyse.resultat()["profondeur"]
note("R-140", p2 > p1 and e.etat_du_moteur().startswith("Trait aux Blancs  ·  profondeur"),
     "profondeur qui monte (%d -> %d), ligne d'etat « %s »" % (p1, p2, e.etat_du_moteur()))
note("R-140", bool(e.plateau.fleches_conseil) and e.evaluation()[1] != "", "fleche bleue + barre d'avantage (%s)" % e.evaluation()[1])
pygame.image.save(ecran, os.path.join(OUT, "v_analyse_depart.png"))
glisser(e, "e2", "e4")
jouer(e, "e7", "e5")
jouer(e, "g1", "f3")
note("R-141", [c.uci() for c in e.coups] == ["e2e4", "e7e5", "g1f3"], "glisser puis clic-clic, les deux camps : %s" % [c.uci() for c in e.coups])
t0 = time.time()
ok = attendre(e, lambda: e.lignes() and chess.Move.from_uci(e.lignes()[0]["uci"]) in e.plateau.board.legal_moves
              and e.plateau.board.turn == chess.BLACK, 10)
note("R-141", ok, "Stockfish repart sur la nouvelle position en %.2f s (coups noirs proposes : %s)" % (time.time() - t0, e.lignes()[0]["san"] if e.lignes() else "-"))
touche(pygame.K_LEFT); images(e, 2)
touche(pygame.K_HOME); images(e, 2)
d = e.index
touche(pygame.K_END); images(e, 2)
f = e.index
clic(e.rects_coups[1][0].center); images(e, 2)
note("R-141", d == 0 and f == 3 and e.index == 2, "fleches, Debut (%d), Fin (%d), clic sur le 2e coup de la feuille (%d)" % (d, f, e.index))
jouer(e, "b1", "c3")
note("R-141", [c.uci() for c in e.coups] == ["e2e4", "e7e5", "b1c3"], "un autre coup au milieu (Cc3 au lieu de Cf3) remplace la suite : %s" % [c.uci() for c in e.coups])
attendre(e, lambda: len(e.lignes()) >= 1, 10)
images(e, 2)
premier = e.lignes()[0]["uci"]; n = len(e.coups)
clic(e.rects_lignes[0][0].center); images(e, 3)
note("R-142", len(e.coups) == n + 1 and e.coups[-1].uci() == premier, "clic sur la 1re ligne : %s joue" % premier)
attendre(e, lambda: e.analyse.resultat()["profondeur"] >= 10, 15)
nb, cpu_marche = stockfish_cpu()
touche(pygame.K_SPACE); images(e, 3)
time.sleep(0.5)
nb2, cpu_pause = stockfish_cpu()
images(e, 1)
note("R-143", (not e.analyse.actif) and e.btn_moteur.libelle == "Relancer" and e.btn_moteur.selectionne,
     "Espace : « %s », bouton « %s » en or" % (e.etat_du_moteur(), e.btn_moteur.libelle))
note("R-143", cpu_pause < 10 and cpu_marche > 50,
     "processeur de Stockfish : %.0f %% en marche, %.0f %% a l'arret (%d coeurs)" % (cpu_marche, cpu_pause, psutil.cpu_count()))
pygame.image.save(ecran, os.path.join(OUT, "v_analyse_pause.png"))
touche(pygame.K_SPACE); images(e, 2)
p = e.analyse.resultat()["profondeur"]
ok = attendre(e, lambda: e.analyse.resultat()["en_cours"], 5)
note("R-143", e.analyse.actif and ok, "Espace encore : l'analyse reprend")
# collage (R-144) : le presse-papiers de Windows n'existe pas ici -> on donne le texte directement
ok1 = e.coller_texte("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4")
ok_m = attendre(e, lambda: e.lignes() and e.lignes()[0]["texte"] == "M1", 15)
note("R-144", ok1 and ok_m and e.message == "Position collée", "FEN colle : « %s », Stockfish trouve %s (%s)" % (e.message, e.lignes()[0]["san"] if e.lignes() else "-", e.lignes()[0]["texte"] if e.lignes() else "-"))
pgn = '[Event "Test"]\n[White "Julien"]\n[Black "dragondu5"]\n\n1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6 *'
ok2 = e.coller_texte(pgn)
note("R-144", ok2 and len(e.coups) == 10 and e.index == 0 and e.message == "Partie collée : 10 coups", "PGN colle : « %s », affichee depuis le debut" % e.message)
for _ in range(10): touche(pygame.K_RIGHT)
images(e, 3)
note("R-144", e.index == 10, "fleche droite x10 : on arrive au dernier coup (Najdorf)")
ok3 = e.coller_texte("bonjour, ceci n'est pas une partie")
images(e, 1)
note("R-144", not ok3 and e.message == "Ce texte n'est ni un FEN ni une partie PGN." and e.index == 10, "texte quelconque : « %s », rien ne casse" % e.message)
fen = e.copier_fen()
note("R-146", fen == e.plateau.board.fen(), "C : le FEN de la position affichee (%s) — copie vers Windows et lichess non testables ici" % fen)
# editeur (R-145)
touche(pygame.K_e); images(e, 2)
ed = e.edition
def outil(o):
    rect = next(r for r, x in e.rects_palette if x == o); clic(rect.center); images(e, 1)
def bouton(b):
    clic(b.rect.center); images(e, 2)
bouton(e.btn_vider)
for o, c in (("K", "e1"), ("k", "e8"), ("R", "h1"), ("R", "a1"), ("P", "e2")):
    outil(o); clic(case(e, c)); images(e, 1)
outil("P"); clic(case(e, "a8")); images(e, 1)
bouton(e.btn_valider)
note("R-145", e.edition is not None and "pion" in e.edition.message, "pion pose en a8 : refuse (« %s »)" % (e.edition.message if e.edition else ""))
clic(case(e, "a8"), bouton=3); images(e, 1)
outil("gomme"); clic(case(e, "a1")); images(e, 1)
outil(None); clic(case(e, "e2")); images(e, 1); clic(case(e, "e3")); images(e, 1)
roque_h = next((r for r, m in e.rects_roques if m == chess.BB_H1), None)
roque_a = next((r for r, m in e.rects_roques if m == chess.BB_A1), None)
if roque_h: clic(roque_h.center); images(e, 1)
note("R-145", roque_a is None and roque_h is not None and e.edition.plateau.castling_rights == chess.BB_H1,
     "roques : seul le petit roque blanc est cochable (roi e1, tour h1), coche")
bouton(e.btn_noirs)
pygame.image.save(ecran, os.path.join(OUT, "v_editeur.png"))
bouton(e.btn_valider)
note("R-145", e.edition is None and e.fen_depart == "4k3/8/8/8/8/4P3/8/4K2R b K - 0 1",
     "clic droit, gomme, Deplacer, trait aux Noirs, Analyser : %s" % e.fen_depart)
ok = attendre(e, lambda: len(e.lignes()) >= 1, 15)
note("R-145", ok, "Stockfish analyse la position fabriquee (%s %s)" % (e.lignes()[0]["san"] if e.lignes() else "-", e.lignes()[0]["texte"] if e.lignes() else ""))
touche(pygame.K_e); images(e, 1); bouton(e.btn_vider); touche(pygame.K_ESCAPE); images(e, 2)
note("R-145", e.edition is None and e.fen_depart == "4k3/8/8/8/8/4P3/8/4K2R b K - 0 1", "Echap annule l'editeur, la position revient")
# R-148 : pas de dossier syzygy/ dans le cloud
e.coller_texte("8/8/8/4k3/8/8/4P3/4K3 w - - 0 1"); images(e, 2)
note("R-148", os.path.isdir("syzygy") or "Tables" not in e.position()["fen"], "sans dossier syzygy/ : aucune ligne « Tables de finale », aucune erreur (avec les tables : a voir sur ton PC)")
# R-149 : arret tout seul apres 1 minute, sur une vraie position de milieu de partie
e.coller_texte("r1bq1rk1/pp2bppp/2n1pn2/2pp4/3P4/2PBPN2/PP1N1PPP/R1BQ1RK1 w - - 0 8")
t0 = time.time()
ok = attendre(e, lambda: e.analyse.resultat()["fini"], 75)
note("R-149", ok and time.time() - t0 > 30, "« %s » apres %.0f s" % (e.etat_du_moteur(), time.time() - t0))
images(e, 2); time.sleep(0.5)
nb, cpu_fini = stockfish_cpu()
note("R-149", cpu_fini < 10, "processeur de Stockfish apres l'arret tout seul : %.0f %%" % cpu_fini)
touche(pygame.K_ESCAPE)
rep = images(e, 1)
e.analyse.arreter(); time.sleep(2)
import moteurs
note("R-149", rep == "retour" and "libre" not in moteurs.roles_vivants() and stockfish_cpu(0.2)[0] == 0,
     "Echap : retour ; plus aucun stockfish d'analyse libre (%s)" % moteurs.roles_vivants())

# ------------------------------------------------------------ revue -> Analyser (R-147)
print("== Revue -> Analyser")
from analyse_partie import AnalyseurPartie
from ecran_revue import EcranRevue
import ecran_analyse_libre as eal
vus = []
_orig = eal.EcranAnalyseLibre.__init__
def espion(self, *a, **k):
    _orig(self, *a, **k); vus.append((self.plateau.board.fen(), self.index, len(self.coups)))
eal.EcranAnalyseLibre.__init__ = espion
a = AnalyseurPartie(None, ["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"], SF, "rapide")
r = EcranRevue(ecran, a, {}, ("Toi", "Ordinateur"), "1-0")
r.aller_a(5, son=False)
fen_revue = r.plateau.board.fen()
clock = pygame.time.Clock()
touche(pygame.K_a)
pygame.time.set_timer(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode=""), 4000, 1)
_run = eal.EcranAnalyseLibre.run
def run_puis_sortir(self, *args, **kw):
    rep = _run(self, *args, **kw)
    pygame.time.set_timer(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode=""), 1500, 1)
    return rep
eal.EcranAnalyseLibre.run = run_puis_sortir
rep = r.run(clock, gm.evenement_fenetre, None)
eal.EcranAnalyseLibre.run = _run; eal.EcranAnalyseLibre.__init__ = _orig
note("R-147", vus and vus[0][0] == fen_revue and vus[0][1] == 5 and vus[0][2] == 7,
     "touche A au coup 5 : analyse libre sur la meme position, la partie (7 coups) dans la feuille")
note("R-147", rep == "retour" and r.index == 5, "Retour : la revue revient au meme coup (%d)" % r.index)
r.aller_a(5, son=False); r.plateau.make_move(chess.Move.from_uci("g7g6")); fen_var = r.plateau.board.fen()
r._horloge = None                       # ouvrir sans lancer la boucle de l'ecran
r.ouvrir_l_analyse_libre(); lib = r.analyse_libre; lib.analyse.arreter()
note("R-147", lib.plateau.board.fen() == fen_var, "depuis une variante (3...g6) : la position de la variante")
r.draw(); pygame.image.save(ecran, os.path.join(OUT, "v_revue_boutons.png"))
rects = [b.rect for b in r.boutons]
note("t86", all(not x.colliderect(y) for i, x in enumerate(rects) for y in rects[i + 1:]) and all(b.rect.right <= ecran.get_width() for b in r.boutons),
     "1280x720 : les boutons du bas de la revue ne se chevauchent pas")
a.arreter()

# ------------------------------------------------------------ invitation de test (R-10E, t88)
print("== Invitation de test")
import invitations, salon_en_ligne
sons = []
import sounds
_play = sounds.SoundManager.play
sounds.SoundManager.play = lambda self, nom: (sons.append(nom), _play(self, nom))[1]
gm.config["sons_actifs"] = True
gm.en_ligne = True
salon = salon_en_ligne.SalonEnLigne(ecran, clock, None, "Julien", config={})
salon.draw()
pygame.image.save(ecran, os.path.join(OUT, "v_salon_avant.png"))
clic(salon._boutons["test_invitation"].rect.center)
for ev in ui.evenements(): salon.handle_event(ev)
salon.draw(); ui.afficher()
pygame.image.save(ecran, os.path.join(OUT, "v_salon_invitation.png"))
note("R-10E", "invitation:%d" % invitations.en_attente()[0]["salon"] in salon._boutons and "menu" in salon.info,
     "« Test : invitation » : « %s », la liste « INVITATIONS REÇUES » la montre" % salon.info)
gm.en_ligne = False
gm.au_menu = True
gm.menu.draw(); ui.afficher(); ui.evenements(); gm.menu.draw(); ui.afficher()
pygame.image.save(ecran, os.path.join(OUT, "v_menu_bandeau.png"))
note("R-10E", gm.bandeau._rect is not None and "game_start" in sons, "au menu : bandeau « Ami de test t'invite à jouer » + petit son")
clic(gm.bandeau._boutons["plus_tard"].rect.center); ui.evenements(); gm.menu.draw(); ui.afficher()
note("t88", gm.bandeau._rect is None and len(invitations.en_attente()) == 1, "Plus tard : le bandeau part, l'invitation reste dans la liste")
salon2 = salon_en_ligne.SalonEnLigne(ecran, clock, None, "Julien", config={}); salon2.draw()
inv = invitations.en_attente()[0]
salon2._clic("invitation:%d" % inv["salon"]); salon2.draw()
pygame.image.save(ecran, os.path.join(OUT, "v_salon_rejoindre.png"))
# Sans Steam : message tout de suite ; avec Steam : il cherche le salon (qui n'existe pas),
# puis « Impossible d'entrer » au bout de quelques secondes.
note("R-10E", salon2.erreur != "" or salon2.etape == "attente_steam",
     "Rejoindre l'invitation de test : %s" % (salon2.erreur or "connexion a Steam en cours"))
sounds.SoundManager.play = _play

with open(os.path.join(OUT, "resultats.json"), "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=1)
rouges = sorted({k for k, v in R.items() if not all(ok for ok, _t in v)})
print()
print("RESULTAT : %s" % ("tout est bon (%d lignes de recette)" % len(R) if not rouges
                         else "a corriger : " + ", ".join(rouges)))
os._exit(1 if rouges else 0)
