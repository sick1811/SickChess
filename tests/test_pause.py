# tests/test_pause.py - menu pause en pleine partie (17/10, travail p10).
#     python tests/test_pause.py
# Echap ouvre la pause, la pendule s'arrete, Reprendre la relance ; nulle a deux,
# nulle refusee / acceptee par l'ordinateur ; abandon ; retour au menu (la
# partie est gardee) ; le tout dans la vraie boucle de game_manager.
# La sauvegarde est ecrite dans un dossier temporaire.

import os
import sys
import tempfile
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import chess
import pygame

pygame.init()
pygame.display.set_mode((1024, 640))

import menu_pause
import petit_pc
petit_pc.forcer("normal")      # 24/10 (p31) : la cadence controlee ici est celle d'un PC normal
import sauvegarde

sauvegarde.FICHIER = os.path.join(tempfile.mkdtemp(), "partie_en_cours.json")

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def touche(cle):
    return pygame.event.Event(pygame.KEYDOWN, key=cle, mod=0, unicode="")


def clic(pos):
    return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos),
            pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos)]


from game_manager import GameManager
gm = GameManager("test")


def nouvelle_partie(mode="hotseat"):
    gm.game_mode = mode
    gm.reglages = {"pendule_active": True, "minutes": 3, "increment_secondes": 0}
    gm.preparer_partie()
    gm.pause = menu_pause.MenuPause(gm.screen, gm.board.theme_plateau,
                                    nulle_possible=True)
    return gm.board


print("1. Echap ouvre la pause, la pendule s'arrete")
b = nouvelle_partie()
b.make_move(chess.Move.from_uci("e2e4"))
verifier(b.timer.demarree and b.timer.active, "la pendule tourne apres le 1er coup")
verifier(gm._peut_ouvrir_la_pause(touche(pygame.K_ESCAPE)), "Echap ouvre la pause")
verifier(not gm._peut_ouvrir_la_pause(touche(pygame.K_a)), "une autre touche non")
b.selected_square = chess.E7
verifier(not gm._peut_ouvrir_la_pause(touche(pygame.K_ESCAPE)),
         "piece selectionnee : Echap annule d'abord la selection")
b.selected_square = None
gm._ouvrir_la_pause()
verifier(gm.pause.ouvert and not b.timer.active, "pause ouverte, pendule arretee")
avant = dict(b.timer.time_left)
time.sleep(0.3)
b.timer.update(b.board.turn)
verifier(b.timer.time_left == avant, "le temps ne descend pas pendant la pause")
b.draw()
gm.pause.draw()
pygame.image.save(gm.screen, os.path.join("tests", "capture_pause.png"))
verifier(gm.pause.handle_event(touche(pygame.K_ESCAPE)) == "reprendre",
         "Echap dans la pause = reprendre")
gm._action_de_pause("reprendre")
verifier(not gm.pause.ouvert and b.timer.active, "Reprendre : la pendule repart")

print("2. Nulle a deux")
gm._ouvrir_la_pause()
gm._action_de_pause("nulle")
verifier(b.game_over and b.result == "1/2-1/2", "nulle d'un commun accord (%s)" % b.result)

print("3. Nulle contre l'ordinateur")
plateau = chess.Board()
ok, raison = menu_pause.ordinateur_accepte_la_nulle(plateau, chess.BLACK)
verifier(not ok and "tôt" in raison, "refusee au debut : %s" % raison)
plateau = chess.Board("4k3/8/8/8/8/8/4P3/3QK3 w - - 0 30")
ok, raison = menu_pause.ordinateur_accepte_la_nulle(plateau, chess.BLACK)
ok, raison = menu_pause.ordinateur_accepte_la_nulle(plateau, chess.WHITE)
verifier(not ok and "mieux" in raison, "l'ordinateur (Blancs, dame en plus) refuse : %s" % raison)
ok, raison = menu_pause.ordinateur_accepte_la_nulle(plateau, chess.BLACK)
verifier(ok, "l'ordinateur (Noirs, perdu) accepte : %s" % raison)
ok, raison = menu_pause.ordinateur_accepte_la_nulle(chess.Board(), chess.WHITE, 0.1)
verifier(not ok, "evaluation egale mais 1er coup : refusee")
p = chess.Board()
p.fullmove_number = 25
ok, raison = menu_pause.ordinateur_accepte_la_nulle(p, chess.WHITE, 0.2)
verifier(ok, "evaluation egale au 25e coup : acceptee")
ok, raison = menu_pause.ordinateur_accepte_la_nulle(p, chess.WHITE, 1.5)
verifier(not ok, "Blancs +1.5 pour l'ordinateur : refusee")
ok, raison = menu_pause.ordinateur_accepte_la_nulle(p, chess.BLACK, 1.5)
verifier(ok, "Blancs +1.5, ordinateur Noirs : acceptee")

print("4. Abandon depuis la pause")
b = nouvelle_partie()
b.make_move(chess.Move.from_uci("e2e4"))
gm._ouvrir_la_pause()
gm.pause._placer()
verifier(gm.pause.handle_event(clic(gm.pause.bouton("abandon").rect.center)[0]) is None,
         "1er clic sur Abandonner : on demande confirmation")
verifier(gm.pause.bouton("abandon").libelle.startswith("Sûr"), "libelle « Sûr ? »")
cle = gm.pause.handle_event(clic(gm.pause.bouton("abandon").rect.center)[0])
verifier(cle == "abandon", "2e clic : abandon")
gm._action_de_pause(cle)
verifier(b.game_over and b.result == "1-0",
         "a deux, celui qui a le trait (Noirs) abandonne : %s" % b.result)

print("5. Retour au menu depuis la pause, dans la vraie boucle")
b = nouvelle_partie()
b.make_move(chess.Move.from_uci("d2d4"))
essai = menu_pause.MenuPause(gm.screen)
essai._placer()
centre_menu = essai.bouton("menu").rect.center
pygame.event.clear()
pygame.event.post(touche(pygame.K_ESCAPE))
for ev in clic(centre_menu):
    pygame.event.post(ev)
debut = time.time()
retour = gm.boucle_de_partie()
verifier(retour == "menu", "la boucle rend 'menu' (%r)" % retour)
verifier(time.time() - debut < 5, "sans attendre")
verifier(not gm.board.game_over, "la partie n'est pas terminee")
d = sauvegarde.lire()
verifier(d is not None and "d2d4" in str(d), "la partie est gardee pour la reprendre")

print("6. Cadence : 30 images/s au repos, 60 quand il se passe quelque chose (banc 23/10)")
b = nouvelle_partie()
gm.pause.ouvert = False
horloge = [10000]
vraie_horloge = pygame.time.get_ticks
pygame.time.get_ticks = lambda: horloge[0]
try:
    verifier(gm.cadence_de_partie([object()]) == 60, "un geste : 60 images/s")
    horloge[0] += 1000
    verifier(gm.cadence_de_partie() == 60, "1 s apres : encore 60")
    horloge[0] += 1000
    verifier(gm.cadence_de_partie() == 30, "2 s sans rien : 30 images/s")
    b.make_move(chess.Move.from_uci("e2e4"))
    verifier(gm.cadence_de_partie() == 60, "un coup joue (par l'ordinateur aussi) : 60")
    horloge[0] += 5000
    b.animation.animations.append({"to_square": chess.E4})
    verifier(gm.cadence_de_partie() == 60, "pendant une animation : 60")
    b.animation.animations.clear()
    horloge[0] += 5000
    gm.pause.ouvert = True
    verifier(gm.cadence_de_partie() == 60, "pause ouverte : 60")
    gm.pause.ouvert = False
    # 23/10 (surveillance) : menus et ecrans, meme regle (ui.Cadence)
    import ui
    c = ui.Cadence()
    verifier(c.suivante() == 60, "ecran qui s'ouvre : 60 images/s")
    horloge[0] += 2000
    verifier(c.suivante() == 30, "menu immobile 2 s : 30 images/s")
    verifier(c.suivante([object()]) == 60, "un geste dans le menu : 60")
    horloge[0] += 2000
    verifier(c.suivante(anime=True) == 60, "une animation dans l'ecran : 60")
finally:
    pygame.time.get_ticks = vraie_horloge

gm.cleanup_game()
gm.cleanup()
print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
