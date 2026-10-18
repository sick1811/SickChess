# tests/test_signaler.py - « Signaler un problème / une idée » (17/10, p16).
#     python tests/test_signaler.py
# Tout se passe dans un dossier temporaire ; l'envoi est simule (aucun
# message ne part vraiment).

import json
import os
import sys
import tempfile
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
ecran = pygame.display.set_mode((1024, 640))

import signalement
import ui

TEMP = tempfile.mkdtemp(prefix="sickchess_signaler_")
signalement._racine = lambda: TEMP
signalement.ouvrir_le_dossier = lambda chemin: True
ui.copier = lambda texte: True
with open(os.path.join(TEMP, "journal_du_jeu.txt"), "w", encoding="utf-8") as f:
    f.write("".join("ligne %d\n" % i for i in range(300)))

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


print("1. Le rapport")
texte = signalement.construire("probleme", "Le son coupe en partie", "0.1.0 (n°3)")
verifier("Version : 0.1.0 (n°3)" in texte and "Le son coupe en partie" in texte,
         "message et version dans le rapport")
verifier("ligne 299" in texte and "ligne 100" not in texte,
         "les 120 dernieres lignes du journal, pas plus")
idee = signalement.construire("idee", "Un mode aveugle", "0.1.0")
verifier("journal" not in idee.lower(), "une idee n'embarque pas le journal")
chemin = signalement.enregistrer(texte, "probleme")
verifier(chemin and os.path.exists(chemin) and chemin.startswith(os.path.join(TEMP, "rapports")),
         "rapport range dans rapports/")

print("2. L'adresse d'envoi")
verifier(signalement.adresse_d_envoi() == "", "rien de regle : pas d'envoi direct")
with open(os.path.join(TEMP, "signalement.json"), "w", encoding="utf-8") as f:
    json.dump({"signalement_webhook": "https://discord.com/api/webhooks/1/abc"}, f)
verifier(signalement.adresse_d_envoi().startswith("https://discord.com"), "adresse lue dans signalement.json")

print("3. L'envoi (simule)")
envoyes = []


class Reponse:
    status = 204
    def __enter__(self): return self
    def __exit__(self, *a): return False


def faux_envoi(requete, timeout=10):
    envoyes.append(requete)
    return Reponse()


ok, msg = signalement.envoyer("https://discord.com/api/webhooks/1/abc", "probleme",
                              "Le son coupe", texte, ouvrir=faux_envoi)
verifier(ok and "Merci" in msg, "envoi reussi : %s" % msg)
corps = envoyes[0].data.decode("utf-8")
verifier("Le son coupe" in corps and "rapport.txt" in corps and "ligne 299" in corps,
         "message + journal en piece jointe")


def coupe(requete, timeout=10):
    raise OSError("pas de reseau")


ok, msg = signalement.envoyer("https://x", "probleme", "m", texte, ouvrir=coupe)
verifier(not ok and "rapports" in msg, "sans Internet : %s" % msg)

print("4. L'ecran")
os.remove(os.path.join(TEMP, "signalement.json"))
from ecran_signaler import EcranSignaler
e = EcranSignaler(ecran, "0.1.0")
e.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=e.btn_envoyer.rect.center))
verifier(e.etat == "saisie" and "Écris" in e.message, "message vide : refuse")
for car in "Le jeu plante quand je clique":
    e.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=car))
verifier(e.champ.contenu == "Le jeu plante quand je clique", "saisie au clavier")
e.draw()
pygame.image.save(ecran, "tests/capture_signaler.png")
e.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=e.btn_envoyer.rect.center))
fin = time.time() + 5
while e.etat != "fini" and time.time() < fin:
    e.update()
    time.sleep(0.05)
verifier(e.etat == "fini" and "rapports" in e.message, "sans adresse : %s" % e.message)
verifier(e.chemin and "Le jeu plante" in open(e.chemin, encoding="utf-8").read(),
         "le rapport contient le message")
e.draw()
verifier(e.btn_annuler.libelle == "Fermer", "bouton Fermer")
verifier(e.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode="")) == "retour",
         "Echap ferme")

print("5. Le menu")
from menu_principal import MainMenu
m = MainMenu(ecran)
m.annoncer_reprise(True, "x")
verifier(any(b.cle == "signaler" for b in m.boutons), "entree « Signaler » dans le menu")
verifier(max(b.rect.bottom for b in m.boutons) <= 640, "les 9 entrees tiennent en 640 px")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
pygame.quit()
sys.exit(1 if echecs else 0)
