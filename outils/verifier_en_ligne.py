# outils/verifier_en_ligne.py - verifie que le jeu en ligne marche sur CE PC.
#
#     python outils/verifier_en_ligne.py                      -> depuis les sources
#     python outils/verifier_en_ligne.py --dossier "C:\...\SickChess"   -> une version installee
#
# A lancer sur Windows, Steam ouvert et connecte (Claude Code). Etapes :
#   1. Fichiers : steam_api64.dll et steam_appid.txt a cote du jeu (et lisibles).
#   2. Steam : connexion, ton nom, numero du jeu, nombre d'amis, relais de Valve.
#   3. Salon : creation d'un salon reserve aux amis, son code, puis fermeture.
#   4. Reseau : tests automatiques du multijoueur (deux joueurs simules sur ce PC,
#      coups, pendules, chat, revanche, coupure) : tests/test_multijoueur.py et
#      tests/test_en_ligne_nulle.py.
# Ce qui ne peut PAS se verifier seul : une vraie partie entre deux comptes Steam amis
# sur deux PC. Le resultat dit exactement quoi faire pour ce dernier test.
#
# Resultat lisible : docs/VERIFICATION_EN_LIGNE.md

import os
import subprocess
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "jeu"))

lignes = []
problemes = []


def noter(ok, texte, conseil=""):
    marque = "OK " if ok else ("-- " if ok is None else "NON")
    lignes.append("- %s %s%s" % ({"OK ": "✅", "NON": "❌", "-- ": "⚪"}[marque], texte,
                                 (" → " + conseil) if conseil and not ok else ""))
    print("  [%s] %s%s" % (marque, texte, ("  -> " + conseil) if conseil and not ok else ""),
          flush=True)
    if ok is False:
        problemes.append(texte)


def etape_fichiers(dossier):
    print("1. Fichiers", flush=True)
    dll = os.path.join(dossier, "steam_api64.dll")
    appid = os.path.join(dossier, "steam_appid.txt")
    noter(os.path.exists(dll), "steam_api64.dll présent à côté du jeu",
          "le prendre dans le Steamworks SDK (redistributable_bin/win64)")
    if os.path.exists(appid):
        numero = open(appid, encoding="utf-8", errors="replace").read().strip()
        noter(numero.isdigit(), "steam_appid.txt contient un numéro (%s)" % numero)
        if numero == "480":
            noter(None, "Numéro 480 = test de Valve (« Spacewar ») : accepter une invitation "
                        "quand SickChess est FERMÉ lancerait Spacewar. L'ami doit ouvrir "
                        "SickChess d'abord, puis accepter (ou taper le code).")
    else:
        noter(False, "steam_appid.txt présent", "il doit contenir 480 en attendant le vrai numéro")
    exe = os.path.join(dossier, "SickChess.exe")
    if os.path.exists(exe):
        noter(True, "SickChess.exe présent (version installée)")


def etape_steam(dossier):
    print("2. Steam", flush=True)
    if sys.platform != "win32":
        noter(None, "Steam ne se teste que sous Windows (ici : %s)" % sys.platform)
        return None
    import steam as module_steam
    ancien = os.getcwd()
    os.chdir(dossier)              # Steam lit steam_appid.txt dans le dossier courant
    s = module_steam.Steam(dossier)
    ok = s.demarrer()
    os.chdir(ancien)
    noter(ok, "Connexion à Steam" + ("" if ok else " : " + s.erreur),
          s.conseil or "ouvrir Steam, se connecter, puis relancer")
    if not ok:
        return None
    noter(True, "Compte : %s · numéro du jeu : %d" % (s.mon_nom(), s.appid))
    try:
        amis = s.amis()
        noter(True, "%d ami(s) Steam visibles (dont %d en ligne)" % (
            len(amis), sum(1 for a in amis if a.get("en_ligne", a.get("etat", 0)))))
    except Exception as e:
        noter(False, "Liste d'amis illisible : %s" % e)
    return s


def etape_salon(s):
    print("3. Salon", flush=True)
    import steam as module_steam
    s.creer_salon(2)
    fin = time.time() + 15
    salon = None
    while time.time() < fin and salon is None:
        s.pomper()
        for e in s.evenements("salon_cree"):
            salon = e["salon"] if e["ok"] else 0
        time.sleep(0.1)
    if not salon:
        noter(False, "Création d'un salon (réponse de Steam en 15 s)",
              "Steam hors ligne ou serveurs de Valve indisponibles : réessayer plus tard")
        return
    code = module_steam.code_depuis_salon(salon)
    retour = module_steam.salon_depuis_code(code)
    noter(True, "Salon créé, code %s" % code)
    noter(retour == salon, "Le code redonne bien le même salon")
    s.ecrire_info(salon, "verif", "1")
    fin = time.time() + 3
    while time.time() < fin:
        s.pomper()
        time.sleep(0.1)
    noter(s.lire_info(salon, "verif") == "1", "Écriture / lecture des informations du salon")
    noter(s.proprietaire(salon) == s.mon_id(), "Tu es bien l'hôte du salon")
    s.quitter_salon(salon)
    noter(True, "Salon refermé")


def etape_reseau():
    print("4. Réseau (deux joueurs simulés sur ce PC)", flush=True)
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
               PYTHONIOENCODING="utf-8")
    for serie in ("test_multijoueur.py", "test_en_ligne_nulle.py"):
        chemin = os.path.join(RACINE, "tests", serie)
        if not os.path.exists(chemin):
            continue
        p = subprocess.run([sys.executable, chemin], cwd=RACINE, env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=300)
        sortie = p.stdout + p.stderr
        nb_ok, nb_ko = sortie.count("  OK   "), sortie.count("  ECHEC ")
        noter(p.returncode == 0, "%s : %d contrôles OK, %d en échec" % (serie, nb_ok, nb_ko))
        if p.returncode != 0:
            for l in [l for l in sortie.splitlines() if "ECHEC" in l][:8]:
                lignes.append("    - " + l.strip())


def main():
    dossier = RACINE
    if "--dossier" in sys.argv:
        dossier = os.path.abspath(sys.argv[sys.argv.index("--dossier") + 1])
    print("Vérification du jeu en ligne – %s" % dossier, flush=True)
    etape_fichiers(dossier)
    s = etape_steam(dossier)
    if s is not None:
        try:
            etape_salon(s)
        finally:
            try:
                s.arreter()
            except Exception:
                pass
    etape_reseau()
    texte = ["# Vérification du jeu en ligne", "",
             "Le %s · dossier vérifié : `%s`" % (time.strftime("%d/%m/%Y %H:%M"), dossier), "",
             "Fabriqué par `python outils/verifier_en_ligne.py`.", ""] + lignes + [
        "", "## Dernier test, à faire à deux (ne peut pas se faire seul)",
        "1. Deux PC, deux comptes Steam **amis**, Steam ouvert des deux côtés, SickChess "
        "installé chez les deux (installeur ou version amis).",
        "2. Les deux ouvrent SickChess → *Jouer en ligne*.",
        "3. Toi : *Créer une partie* → *Inviter* ton ami (liste dans le jeu) ou donne-lui le code.",
        "4. L'ami : accepte l'invitation dans Steam **avec SickChess déjà ouvert**, ou tape le code.",
        "5. Jouer quelques coups, écrire dans le chat, proposer la nulle, abandonner, revanche.",
        "6. Couper le Wi-Fi d'un PC 20 s : la partie doit reprendre ; plus de 60 s : partie interrompue.",
        "", "**Verdict** : " + ("tout est bon de ce côté." if not problemes else
                                "%d problème(s) à régler avant le test à deux." % len(problemes))]
    with open(os.path.join(RACINE, "docs", "VERIFICATION_EN_LIGNE.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(texte) + "\n")
    print("\nRésultat : docs/VERIFICATION_EN_LIGNE.md")
    return 1 if problemes else 0


if __name__ == "__main__":
    sys.exit(main())
