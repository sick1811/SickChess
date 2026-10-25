# tests/test_menu_echap.py - Échap au menu principal (25/10, décision de Julien).
#     python tests/test_menu_echap.py
# Avant : Échap au menu fermait le jeu sans rien demander (deux fois par
# accident). Maintenant : une petite fenêtre « Quitter SickChess ? » Oui / Non.

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
ecran = pygame.display.set_mode((1024, 640), pygame.RESIZABLE)

import ui
from menu_principal import MainMenu

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def touche(cle):
    return pygame.event.Event(pygame.KEYDOWN, key=cle, mod=0, unicode="")


def clic(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


menu = MainMenu(ecran, "test")

print("1. Échap ouvre la fenêtre, il ne quitte pas")
choix = menu.handle_event(touche(pygame.K_ESCAPE))
verifier(choix != "quitter", "Échap au menu ne quitte pas directement (%r)" % choix)
verifier(getattr(menu, "confirmer_quitter", False), "la fenêtre « Quitter SickChess ? » est ouverte")
menu.draw()
pygame.image.save(ecran, os.path.join(RACINE, "tests", "capture_menu_quitter.png"))
boutons = getattr(menu, "boutons_quitter", {})
verifier("oui" in boutons and "non" in boutons, "deux boutons Oui / Non dessinés")

print("2. Échap une deuxième fois : on reste")
choix = menu.handle_event(touche(pygame.K_ESCAPE))
verifier(choix is None and not getattr(menu, "confirmer_quitter", True),
         "2e Échap ferme la fenêtre, on reste au menu (%r)" % choix)

print("3. Non, et clic à côté : on reste")
menu.handle_event(touche(pygame.K_ESCAPE)); menu.draw()
choix = menu.handle_event(clic(boutons["non"].rect.center)) if "non" in boutons else "?"
verifier(choix is None and not getattr(menu, "confirmer_quitter", True), "Non : on reste (%r)" % choix)
menu.handle_event(touche(pygame.K_ESCAPE)); menu.draw()
choix = menu.handle_event(clic((3, 3)))
verifier(choix is None and not getattr(menu, "confirmer_quitter", True), "clic à côté : on reste (%r)" % choix)
menu.handle_event(touche(pygame.K_ESCAPE)); menu.draw()
fenetre = getattr(menu, "_rect_quitter", None)
choix = menu.handle_event(clic((fenetre.centerx, fenetre.y + 6))) if fenetre else "?"
verifier(choix is None and getattr(menu, "confirmer_quitter", False),
         "clic dans la fenêtre (hors boutons) : elle reste ouverte (%r)" % choix)
choix = menu.handle_event(clic(menu.boutons[0].rect.center))
verifier(choix is None, "un bouton du menu derrière la fenêtre ne s'ouvre pas (%r)" % choix)

print("4. Oui ou Entrée : on quitte")
menu.handle_event(touche(pygame.K_ESCAPE)); menu.draw()
choix = menu.handle_event(clic(menu.boutons_quitter["oui"].rect.center)) if "oui" in boutons else "?"
verifier(choix == "quitter", "Oui : quitter (%r)" % choix)
menu.confirmer_quitter = False
menu.handle_event(touche(pygame.K_ESCAPE))
verifier(menu.handle_event(touche(pygame.K_RETURN)) == "quitter", "Entrée : quitter")
menu.confirmer_quitter = False
menu.handle_event(touche(pygame.K_ESCAPE))
verifier(menu.handle_event(touche(pygame.K_KP_ENTER)) == "quitter", "Entrée du pavé : quitter")
menu.confirmer_quitter = False

print("5. Le bouton « Quitter » du menu garde son comportement")
quitter = next(b for b in menu.boutons if b.cle == "quitter")
menu.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=quitter.rect.center, rel=(0, 0), buttons=(0, 0, 0)))
choix = menu.handle_event(clic(quitter.rect.center))
verifier(choix == "quitter", "clic sur « Quitter » : on quitte comme avant (%r)" % choix)

print("6. F11 et redimensionnement pendant la fenêtre")
# Dans game_manager, ui.evenement_fenetre passe AVANT menu.handle_event :
# la fenêtre ne doit pas se mettre en travers (aucune boucle à elle).
menu.confirmer_quitter = False
menu.handle_event(touche(pygame.K_ESCAPE))
nouvelle = ui.evenement_fenetre(pygame.event.Event(pygame.VIDEORESIZE, w=1366, h=768, size=(1366, 768)))
verifier(nouvelle is not None and nouvelle.get_size() == (1366, 768), "redimensionnement pris en compte")
menu.screen = nouvelle
menu.redimensionner(1366, 768)
menu.draw()
verifier(menu.confirmer_quitter and menu._rect_quitter.center == (683, 384),
         "fenêtre toujours ouverte et recentrée après redimensionnement")
nouvelle = ui.evenement_fenetre(touche(pygame.K_F11))
verifier(nouvelle is not None, "F11 bascule le plein écran pendant la fenêtre")
ui.evenement_fenetre(touche(pygame.K_F11))
verifier(menu.confirmer_quitter, "fenêtre encore ouverte après F11")
import inspect
import game_manager
source = inspect.getsource(game_manager.GameManager._evenements_du_menu)
verifier(source.index("evenement_fenetre") < source.index("self.menu.handle_event"),
         "game_manager traite F11 / taille avant le menu")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
