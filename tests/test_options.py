# tests/test_options.py - verifie l'ecran Options sans ouvrir de fenetre.
#     python tests/test_options.py
# Teste : les quatre onglets se dessinent, un clic change le reglage et
# l'apercu, Annuler ne touche pas a config.json, Enregistrer l'ecrit, et
# le menu ouvre bien l'ecran. config.json est remis tel quel a la fin.

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
ecran = pygame.display.set_mode((1024, 640))

import apparence
from ecran_options import EcranOptions
from settings_screen import charger_config, _chemin_config

echecs = []
CAPTURES = os.path.join(RACINE, "tests")


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def clic(ecr, pos):
    return ecr.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                               button=1, pos=pos))


def zone_de(ecr, cle, valeur):
    for _id, _nom, reglages in ecr.onglets:
        for r in reglages:
            if r.cle == cle:
                for rect, v in r.zones:
                    if v == valeur:
                        return rect.center
    return None


chemin = _chemin_config()
with open(chemin, "rb") as f:
    sauvegarde = f.read()            # gardee en memoire, rien a nettoyer
try:
    print("1. Les quatre onglets se dessinent")
    ecr = EcranOptions(ecran)
    for rang, (ident, nom, reglages) in enumerate(ecr.onglets):
        ecr.onglet = rang
        ecr.draw()
        pygame.image.save(ecr.screen, os.path.join(CAPTURES, "capture_options_%s.png" % ident))
        verifier(all(r.zones for r in reglages), "onglet %s : %d reglages dessines" % (nom, len(reglages)))
    verifier(len(ecr.onglets) == 4, "4 onglets")

    print("2. Un clic change le reglage et l'apercu")
    ecr.onglet = 0
    ecr.draw()
    avant_config = open(chemin, encoding="utf-8").read()
    pos = zone_de(ecr, "theme_plateau", "foret")
    clic(ecr, pos)
    verifier(ecr.valeurs["theme_plateau"] == "foret", "damier Foret choisi")
    pos = zone_de(ecr, "accent", "bleu")
    clic(ecr, pos)
    verifier(apparence.ACCENT_ACTUEL == "bleu", "accent bleu applique en direct")
    clic(ecr, zone_de(ecr, "points_coups_possibles", False))
    ecr.draw()
    pygame.image.save(ecr.screen, os.path.join(CAPTURES, "capture_options_modifie.png"))

    print("3. Annuler remet tout comme avant")
    accent_avant = charger_config().get("accent", apparence.DEFAUTS["accent"])
    reponse = clic(ecr, ecr.btn_annuler.rect.center)
    verifier(reponse == "annule", "Annuler renvoie 'annule'")
    verifier(open(chemin, encoding="utf-8").read() == avant_config, "config.json intact")
    verifier(apparence.ACCENT_ACTUEL == accent_avant, "accent d'origine restaure (%s)" % accent_avant)

    print("4. Enregistrer ecrit config.json")
    ecr = EcranOptions(ecran)
    ecr.draw()
    clic(ecr, zone_de(ecr, "theme_plateau", "noyer"))
    ecr.onglet = 2
    ecr.draw()
    clic(ecr, zone_de(ecr, "volume_sons", 0.0))
    ecr.onglet = 3
    ecr.draw()
    clic(ecr, zone_de(ecr, "echelle_interface", 1.15))
    ecr.draw()
    verifier(ecr.ech > 0.95, "taille des textes appliquee en direct (x%.2f)" % ecr.ech)
    reponse = ecr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode="\r"))
    config = charger_config()
    verifier(reponse == "enregistre", "Entree enregistre")
    verifier(config.get("theme_plateau") == "noyer", "damier Noyer ecrit")
    verifier(config.get("volume_sons") == 0.0 and config.get("sons_actifs") is False,
             "volume muet ecrit (sons coupes)")
    verifier(config.get("stockfish_path") is not None, "les autres cles sont conservees")

    print("5. Echap = annuler, Tab = onglet suivant")
    ecr = EcranOptions(ecran)
    ecr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB, mod=0, unicode="\t"))
    verifier(ecr.onglet == 1, "Tab passe a l'onglet Partie")
    verifier(ecr.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode="")) == "annule",
             "Echap annule")

    print("6. Le menu ouvre les Options")
    import menu_principal
    menu = menu_principal.MainMenu(ecran)
    bouton = [b for b in menu.boutons if b.cle == "options"][0]
    verifier(bouton.actif, "entree Options active")
    verifier(menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                                  pos=bouton.rect.center)) == "options",
             "clic sur Options")
finally:
    with open(chemin, "wb") as f:
        f.write(sauvegarde)

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
