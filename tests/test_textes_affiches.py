# tests/test_textes_affiches.py - les textes affiches : accents, anglais complet
# (25/10, defauts trouves par Cowork sur le PC de Julien).
#     python tests/test_textes_affiches.py

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
sys.path.insert(0, os.path.join(RACINE, "jeu"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import langue_en

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def sources():
    texte = {}
    for nom in os.listdir("jeu"):
        if nom.endswith(".py"):
            with open(os.path.join("jeu", nom), encoding="utf-8") as f:
                texte[nom] = f.read()
    return texte


SOURCES = sources()
TOUT = "\n".join(t for n, t in SOURCES.items() if n != "langue_en.py")

print("1. Accents des textes affiches (signales par Cowork)")
CORRIGES = {
    "Aucun coup joue": "Aucun coup joué",
    "Surligner les deux cases du coup joue": "Surligner les deux cases du coup joué",
    "Jouer d'avance pendant que l'adversaire reflechit": "Jouer d'avance pendant que l'adversaire réfléchit",
    "%d problèmes joues,": "%d problèmes joués,",
    "Cree une partie": "Crée une partie",
    "qu'il t'a donne.": "qu'il t'a donné.",
}
for faux, juste in CORRIGES.items():
    verifier(('"%s' % faux) not in TOUT and faux not in "".join(
                 l for l in TOUT.splitlines(True) if not l.strip().startswith(("#", '"""'))) ,
             "plus de « %s » affiche" % faux)
    verifier(juste in TOUT, "« %s » est bien ecrit" % juste)

print("2. Chaque texte corrige garde sa traduction anglaise")
for juste in ("Aucun coup joué", "Surligner les deux cases du coup joué",
              "Jouer d'avance pendant que l'adversaire réfléchit"):
    verifier(juste in langue_en.EN, "traduction anglaise de « %s »" % juste)
verifier(any(k.startswith("%d problèmes joués,") for k in langue_en.EN),
         "traduction anglaise de « %d problèmes joués, ... »")
verifier(any(k.startswith("Joue contre un ami Steam. Crée une partie") for k in langue_en.EN),
         "traduction anglaise de « Joue contre un ami Steam. Crée une partie ... »")

print("3. Anglais : un « %% » dans la phrase ne mange plus la valeur suivante")
import langue
langue.regler("en")
try:
    obtenu = langue.traduire("111 problèmes joués, 55 % réussis, meilleure série 10 - enregistré")
    verifier(obtenu == "111 puzzles played, 55 % solved, best streak 10 - saved",
             "« %s » (avant : « 55 %%10olved »)" % obtenu)
finally:
    langue.regler("fr")

print("4. Anglais : reprise de partie, revue, pendule")
langue.regler("en")
try:
    reprise = langue.traduire("Contre l'ordinateur (3000 Elo)  -  coup 2  -  24/10/2026 18:00")
    verifier("Contre" not in reprise and "3000" in reprise and "move 2" in reprise,
             "reprise au menu : « %s »" % reprise)
    revue = langue.traduire("Ordinateur (400)")
    verifier(revue == "Computer (400)", "en haut de la revue : « %s »" % revue)
    # La pendule : la place du nom doit suffire pour le nom AFFICHE (anglais).
    import pygame
    pygame.init()
    ecran = pygame.display.set_mode((1280, 720))
    import ui
    import timer as module_timer
    appels = []
    vrai_texte = ui.texte

    def espion(surface, chaine, x, y, taille=17, couleur=None, gras=False, mono=False,
               largeur_max=None, **reste):
        appels.append((chaine, taille, gras, mono, largeur_max))
        return vrai_texte(surface, chaine, x, y, taille, couleur or (255, 255, 255), gras,
                          mono, largeur_max, **reste)
    ui.texte = espion
    try:
        pendule = module_timer.ChessTimer(5, 0) if hasattr(module_timer, "ChessTimer") else None
        if pendule is None:
            classe = next(getattr(module_timer, n) for n in dir(module_timer)
                          if isinstance(getattr(module_timer, n), type) and hasattr(getattr(module_timer, n), "draw"))
            pendule = classe(5, 0)
        zones = {}
        import chess
        zones[chess.WHITE] = (900, 600, 300, 70)
        zones[chess.BLACK] = (900, 20, 300, 70)
        try:
            pendule.draw(ecran, zones) if pendule.draw.__code__.co_argcount <= 3 else pendule.draw(ecran, zones, None)
        except TypeError:
            pendule.draw(ecran, zones, chess.WHITE)
    finally:
        ui.texte = vrai_texte
    noms = [a for a in appels if a[0] in ("NOIRS", "BLANCS")]
    coupes = [a[0] for a in noms if a[4] is not None
              and ui.mesurer(langue.traduire(a[0]), a[1], gras=a[2])[0] > a[4]]
    verifier(noms and not coupes, "pendule : « BLACK » / « WHITE » ont leur place (coupes : %s)" % coupes)
finally:
    langue.regler("fr")

print("5. Aide F1 de la revue : les vraies touches")
import raccourcis
aide = dict(e for e in raccourcis.RACCOURCIS if e[1]) if hasattr(raccourcis, "RACCOURCIS") else {}
if not aide:
    for nom in dir(raccourcis):
        valeur = getattr(raccourcis, nom)
        if isinstance(valeur, list) and valeur and isinstance(valeur[0], tuple):
            aide.update(dict(e for e in valeur if len(e) == 2 and e[1]))
textes = " | ".join(aide.values())
for perime in ("Lecture automatique", "Cinq coups d'un coup", "Relancer ou interrompre l'analyse"):
    verifier(perime not in textes, "l'aide n'annonce plus « %s » (n'existe pas dans la revue)" % perime)
verifier(any("analyse libre" in v for v in aide.values()), "A : ouvre l'analyse libre")
verifier("Debut / Fin" not in aide and " a ce coup" not in textes,
         "accents de l'aide (« à ce coup », « Début / Fin »)")
verifier(len([k for k in aide if k]) >= 6, "l'aide de la revue a ses lignes (%d en tout)" % len(aide))

print("6. Salon en ligne : la phrase d'accueil tient en entier (Cowork, 24/10)")
import salon_en_ligne


class SteamFactice:
    actif = False
    erreur = "Steam n'est pas disponible."
    conseil = "Ouvre Steam puis réessaie."

    def demarrer(self):
        return False


PHRASE_SALON = "Joue contre un ami Steam. Crée une partie"
for code in ("fr", "en"):
    for taille in ((1366, 768), (1920, 1080)):
        langue.regler(code)
        lignes_vues = []
        vrai_texte = ui.texte

        def espion_salon(surface, chaine, *args, _vues=lignes_vues, _vrai=vrai_texte,
                         **reste):
            _vues.append(str(chaine))
            return _vrai(surface, chaine, *args, **reste)
        ui.texte = espion_salon
        try:
            ecran = pygame.display.set_mode(taille)
            salon = salon_en_ligne.SalonEnLigne(ecran, None, steam=SteamFactice())
            salon.draw()
        finally:
            ui.texte = vrai_texte
            langue.regler("fr")
        attendu = PHRASE_SALON + " et invite-le, ou entre le code qu'il t'a donné."
        if code == "en":
            langue.regler("en")
            attendu = langue.traduire(attendu)
            langue.regler("fr")
        premier = attendu.split(" ")[0] + " "
        debut = next((i for i, l in enumerate(lignes_vues) if l.startswith(premier)), None)
        affiche = ""
        if debut is not None:
            for ligne in lignes_vues[debut:]:
                affiche = (affiche + " " + ligne).strip()
                if len(affiche) >= len(attendu) or ligne.endswith("..."):
                    break
        verifier(affiche == attendu, "%s %dx%d : « %s » (attendu « %s »)"
                 % (code, taille[0], taille[1], affiche, attendu))

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
