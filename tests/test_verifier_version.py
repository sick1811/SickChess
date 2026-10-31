# tests/test_verifier_version.py - la verification avant chaque version (24/10, travail p32).
#     python tests/test_verifier_version.py
# Chaque controle sur un faux projet (dossier temporaire) : bons et mauvais cas,
# version amis et version Steam. Les tests et le banc d'essai sont simules.

import os
import shutil
import subprocess
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "outils"))

import verifier_version as vv

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def projet(mode_test=True, appid="480", version="0.2.0", licences=True, credits_propres=False,
           reel="None"):
    d = tempfile.mkdtemp(prefix="sickchess_version_")
    os.makedirs(os.path.join(d, "jeu"))
    # 31/10 : le vrai numero Steam n'est ecrit qu'a un endroit, jeu/distribution.py.
    with open(os.path.join(d, "jeu", "distribution.py"), "w", encoding="utf-8") as f:
        f.write("APPID_DE_TEST = 480\nAPPID_STEAM_REEL = %s   # le jour venu\n" % reel)
    with open(os.path.join(d, "jeu", "salon_en_ligne.py"), "w", encoding="utf-8") as f:
        f.write("import os\n\nMODE_TEST = %s\n" % mode_test)
    if appid is not None:
        with open(os.path.join(d, "steam_appid.txt"), "w", encoding="utf-8") as f:
            f.write(appid + "\n")
    with open(os.path.join(d, "SickChess.py"), "w", encoding="utf-8") as f:
        f.write('import os\n\nVERSION = "%s"\n' % version)
    if licences:
        for chemin in vv.LICENCES:
            os.makedirs(os.path.join(d, os.path.dirname(chemin)), exist_ok=True)
            with open(os.path.join(d, chemin), "w", encoding="utf-8") as f:
                f.write("licence\n")
        with open(os.path.join(d, "docs", "CREDITS.md"), "w", encoding="utf-8") as f:
            f.write("| Ressource | Dossier | Origine | Licence |\n|---|---|---|---|\n")
            f.write("| Code | `jeu/` | Julien | Propriété du projet |\n")
            if not credits_propres:
                f.write("| Pièces « Classique » | `jeu/` | Cburnett | **À vérifier** avant la sortie |\n")
    return d


print("1. MODE_TEST")
verifier(vv.controle_mode_test(projet(), "amis")[0] == vv.OK, "amis : MODE_TEST = True permis")
verifier(vv.controle_mode_test(projet(), "steam")[0] == vv.BLOQUANT, "Steam : MODE_TEST = True bloque")
verifier(vv.controle_mode_test(projet(mode_test=False), "steam")[0] == vv.OK, "Steam : MODE_TEST = False ok")

print("2. Numero Steam")
verifier(vv.controle_numero_steam(projet(), "amis")[0] == vv.OK, "amis : 480 ok")
verifier(vv.controle_numero_steam(projet(appid=None), "amis")[0] == vv.A_REVOIR,
         "amis : steam_appid.txt absent, a revoir")
verifier(vv.controle_numero_steam(projet(), "steam")[0] == vv.BLOQUANT, "Steam : 480 bloque")
etat, phrase = vv.controle_numero_steam(projet(appid="3412345", reel="3412345"), "steam")
verifier(etat == vv.OK and "ne doit PAS contenir" in phrase and "3412345" in phrase,
         "Steam : vrai numero ok, avec le rappel")
verifier(vv.controle_numero_steam(projet(appid=None, reel="3412345"), "steam")[0] == vv.OK,
         "Steam : vrai numero dans distribution.py, sans steam_appid.txt : ok")
etat, phrase = vv.controle_numero_steam(projet(appid="3412345"), "steam")
verifier(etat == vv.BLOQUANT and "APPID_STEAM_REEL = None" in phrase,
         "Steam : APPID_STEAM_REEL = None bloque (meme avec un steam_appid.txt)")
verifier(vv.controle_numero_steam(projet(appid=None, reel="480"), "steam")[0] == vv.BLOQUANT,
         "Steam : APPID_STEAM_REEL = 480 bloque")
verifier(vv.controle_numero_steam(projet(appid="480", reel="3412345"), "steam")[0] == vv.BLOQUANT,
         "Steam : vrai numero mais steam_appid.txt = 480, bloque toujours")
verifier(vv.controle_numero_steam(projet(appid="999", reel="3412345"), "steam")[0] == vv.BLOQUANT,
         "Steam : steam_appid.txt et APPID_STEAM_REEL differents, bloque")
verifier(vv.appid_steam_reel(projet(reel="3412345")) == "3412345"
         and vv.appid_steam_reel(projet()) == "", "APPID_STEAM_REEL lu (commentaire ignore)")
verifier(vv.controle_numero_steam(projet(), "itch")[0] == vv.OK
         and vv.controle_numero_steam(projet(appid=None), "itch")[0] == vv.OK,
         "itch : aucun numero Steam demande")
verifier(vv.appid_steam_reel(RACINE) is not None,
         "le vrai projet : APPID_STEAM_REEL trouve dans jeu/distribution.py")

print("2b. Version itch : MODE_TEST et fichiers Steam (31/10)")
verifier(vv.controle_mode_test(projet(), "itch")[0] == vv.BLOQUANT, "itch : MODE_TEST = True bloque")
verifier(vv.controle_mode_test(projet(mode_test=False), "itch")[0] == vv.OK, "itch : MODE_TEST = False ok")
import zipfile

import publier_maj


def projet_itch(avec_dll=False, distribution="itch", exe=True):
    """Un faux projet + un faux zip itch."""
    d = projet(mode_test=False)
    for chemin in ("jeu/ui.py", "moteur/stockfish.exe", "steam_api64.dll", "steam_appid.txt",
                   "LISEZ-MOI_AMIS.txt"):
        os.makedirs(os.path.join(d, os.path.dirname(chemin)), exist_ok=True)
        with open(os.path.join(d, chemin), "w") as f:
            f.write("x")
    z = os.path.join(d, "essai_itch.zip")
    with zipfile.ZipFile(z, "w") as archive:
        if exe:
            archive.writestr("SickChess/SickChess.exe", "exe")
        archive.writestr("SickChess/jeu/ui.py", "x")
        if avec_dll:
            archive.writestr("SickChess/steam_api64.dll", "dll")
        if distribution:
            archive.writestr("SickChess/distribution.json", '{"distribution": "%s"}' % distribution)
    return d, z


d, z = projet_itch()
noms = [n for _a, n in publier_maj.fichiers_itch(d)]
verifier("jeu/ui.py" in noms and "moteur/stockfish.exe" in noms
         and not vv.fichiers_steam_dans(noms) and "LISEZ-MOI_AMIS.txt" not in noms,
         "fichiers de la version itch : le jeu et Stockfish, sans DLL ni steam_appid.txt (%s)" % noms)
verifier(vv.controle_paquet_itch(d, "itch", z)[0] == vv.OK, "zip itch propre : ok")
verifier(vv.controle_paquet_itch(d, "itch")[0] == vv.OK,
         "zip pas encore fabrique : ok (controle a la fabrication)")
d, z = projet_itch(avec_dll=True)
etat, phrase = vv.controle_paquet_itch(d, "itch", z)
verifier(etat == vv.BLOQUANT and "steam_api64.dll" in phrase, "steam_api64.dll dans le zip itch : BLOQUANT")
d, z = projet_itch(distribution="amis")
verifier(vv.controle_paquet_itch(d, "itch", z)[0] == vv.BLOQUANT,
         "distribution.json = amis dans le zip itch : BLOQUANT")
d, z = projet_itch(distribution=None)
verifier(vv.controle_paquet_itch(d, "itch", z)[0] == vv.BLOQUANT,
         "distribution.json absent du zip itch : BLOQUANT")
d, z = projet_itch(exe=False)
verifier(vv.controle_paquet_itch(d, "itch", z)[0] == vv.BLOQUANT, "zip itch sans SickChess.exe : BLOQUANT")
verifier(vv.controle_paquet_itch(d, "itch", os.path.join(d, "pas_un_zip.zip"))[0] == vv.BLOQUANT,
         "zip itch introuvable : BLOQUANT")
d, z = projet_itch()
ancien = publier_maj.PAQUETS["jeu"]
publier_maj.PAQUETS["jeu"] = ancien + ["steam/steam_api64.dll"]
os.makedirs(os.path.join(d, "steam"), exist_ok=True)
with open(os.path.join(d, "steam", "steam_api64.dll"), "w") as f:
    f.write("x")
etat, phrase = vv.controle_paquet_itch(d, "itch", z)
publier_maj.PAQUETS["jeu"] = ancien
verifier(etat == vv.OK, "une DLL Steam rangee ailleurs est retiree aussi (%s)" % phrase)

print("2c. Le zip itch fabrique par publier_maj (sans PyInstaller, sans GitHub)")
d, _z = projet_itch()
dist = tempfile.mkdtemp(prefix="sickchess_dist_")
for chemin in ("SickChess.exe", "_internal/python3.dll", "steam_api64.dll"):
    os.makedirs(os.path.join(dist, os.path.dirname(chemin)), exist_ok=True)
    with open(os.path.join(dist, chemin), "w") as f:
        f.write("x")
sortie = tempfile.mkdtemp(prefix="sickchess_itch_")
envois = []
reel_gh, reel_exe = publier_maj._envoyer_sur_github, publier_maj.construire_exe
publier_maj._envoyer_sur_github = lambda *a, **k: envois.append(a) or True
publier_maj.construire_exe = lambda *a, **k: envois.append("pyinstaller") or dist
try:
    chemin = publier_maj.publier_itch(d, dist=dist, sortie=sortie)
finally:
    publier_maj._envoyer_sur_github, publier_maj.construire_exe = reel_gh, reel_exe
with zipfile.ZipFile(chemin) as archive:
    contenu = archive.namelist()
    choix = archive.read("SickChess/distribution.json").decode("utf-8")
verifier(os.path.basename(chemin) == "SickChess_0.2.0_itch.zip",
         "nom du zip : SickChess_<version>_itch.zip (%s)" % os.path.basename(chemin))
verifier("SickChess/SickChess.exe" in contenu and "SickChess/jeu/ui.py" in contenu
         and "SickChess/moteur/stockfish.exe" in contenu, "le zip contient l'exe, le code et Stockfish")
verifier(not vv.fichiers_steam_dans(contenu),
         "aucun fichier Steam dans le zip (%s)" % vv.fichiers_steam_dans(contenu))
verifier('"itch"' in choix, "distribution.json = itch dans le zip")
verifier(len(contenu) == len(set(contenu)), "aucun fichier en double dans le zip (COPYING-Stockfish)")
verifier("SickChess/paquets_installes.json" not in contenu,
         "pas de paquets_installes.json : la version itch ne se met pas a jour par GitHub")
verifier(not envois, "rien n'est envoye sur GitHub en mode itch (ni exe refait quand on le donne)")
verifier(os.path.dirname(chemin) == sortie, "le zip est a part (dossier itch), pas dans une version amis")
for dossier in (dist, sortie):
    shutil.rmtree(dossier, ignore_errors=True)

print("3. Licences")
verifier(vv.controle_licences(projet(licences=False), "amis")[0] == vv.BLOQUANT, "licence absente : bloque")
etat, phrase = vv.controle_licences(projet(), "amis")
verifier(etat == vv.A_REVOIR and "Pièces « Classique »" in phrase, "amis : ligne « À vérifier » a revoir")
verifier(vv.controle_licences(projet(), "steam")[0] == vv.BLOQUANT, "Steam : ligne « À vérifier » bloque")
verifier(vv.controle_licences(projet(credits_propres=True), "steam")[0] == vv.OK, "Steam : credits propres ok")
verifier(vv.controle_licences(RACINE, "amis")[0] in (vv.OK, vv.A_REVOIR),
         "le vrai projet : licences presentes (%s)" % vv.controle_licences(RACINE, "amis")[1][:70])

print("4. Version")
verifier(vv.controle_version(projet(version="0.2.0"), "amis", "0.1.0")[0] == vv.OK, "0.2.0 apres 0.1.0 : ok")
verifier(vv.controle_version(projet(version="0.2.0"), "amis", "0.2.0")[0] == vv.OK,
         "amis : meme version, ok (le n° amis augmente tout seul)")
verifier(vv.controle_version(projet(version="0.1.9"), "amis", "0.2.0")[0] == vv.BLOQUANT,
         "version plus petite que celle publiee : bloque")
verifier(vv.controle_version(projet(version="0.2.0"), "steam", "0.2.0")[0] == vv.A_REVOIR,
         "Steam : meme version que la version amis, a revoir")
verifier(vv.controle_version(projet(version="0.10.0"), "amis", "0.9.0")[0] == vv.OK,
         "0.10.0 est bien plus grand que 0.9.0")

print("5. Git")
d = projet()
subprocess.run(["git", "init", "-q"], cwd=d)
subprocess.run(["git", "add", "."], cwd=d)
subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"], cwd=d)
verifier(vv.controle_git(d, "amis")[0] == vv.OK, "tout enregistre : ok")
with open(os.path.join(d, "profil.json"), "w") as f:
    f.write("{}")
verifier(vv.controle_git(d, "amis")[0] == vv.OK, "profil.json (donnees de Julien) ne compte pas")
with open(os.path.join(d, "SickChess.py"), "a") as f:
    f.write("# change\n")
verifier(vv.controle_git(d, "amis")[0] == vv.A_REVOIR, "un fichier du jeu pas enregistre : a revoir")


class Resultat:
    def __init__(self, code, sortie):
        self.returncode, self.stdout = code, sortie


print("6. Tests et banc d'essai (simules)")
verifier(vv.controle_tests(RACINE, lambda cmd: Resultat(0, "...\n900 controles OK. Tout est vert."))[0] == vv.OK,
         "tests verts : ok")
etat, phrase = vv.controle_tests(RACINE, lambda cmd: Resultat(
    1, "test_revue.py              ROUGE   30 OK   2 echec(s)\n"
       "      ECHEC partie_x, coup 12 (Fxf7) : erreur\n2 echec(s)."))
verifier(etat == vv.BLOQUANT and "test_revue.py" in phrase, "un test rouge : bloque, et on dit lequel")
verifier("coup 12 (Fxf7)" in phrase, "et on montre le controle en echec (avant : seulement le nom de la serie)")
d = projet()
os.makedirs(os.path.join(d, "tests"))


def faux_banc(statuts):
    def lancer(cmd):
        import json
        with open(os.path.join(d, "tests", "banc_essai.json"), "w", encoding="utf-8") as f:
            json.dump({"sections": {k: {"statut": v} for k, v in statuts.items()}}, f)
        return Resultat(0, "")
    return lancer


verts = {k: "vert" for k in vv.SECTIONS_DU_BANC.split(",")}
verifier(vv.controle_banc(d, faux_banc(verts))[0] == vv.OK, "banc vert : ok")
verifier(vv.controle_banc(d, faux_banc(dict(verts, precision="rouge")))[0] == vv.BLOQUANT,
         "banc rouge (precision) : bloque")
verifier(vv.controle_banc(d, faux_banc(dict(verts, vitesse="orange")))[0] == vv.A_REVOIR,
         "banc orange : a revoir")

print("7. Le .exe dans un dossier neuf (simule)")
dist = tempfile.mkdtemp(prefix="sickchess_dist_")
with open(os.path.join(dist, "SickChess.exe"), "w") as f:
    f.write("exe")
vus = []


def lancer_exe(journal, vivant=True):
    def lancer(dossier, secondes):
        vus.append(dossier)
        return vivant, journal
    return lancer


verifier(vv.controle_exe(dist, 25, lancer_exe("[SICKCHESS] Demarrage de SickChess 0.2.0\n"))[0] == vv.OK
         and vus and vus[0] != dist and not os.path.exists(vus[0]),
         "lance depuis une COPIE neuve (effacee ensuite) : ok")
verifier(vv.controle_exe(dist, 25, lancer_exe("[SICKCHESS] Demarrage\nTraceback (most recent call last):\n"
                                              "KeyError: 'x'\n"))[0] == vv.BLOQUANT, "erreur au demarrage : bloque")
verifier(vv.controle_exe(dist, 25, lancer_exe("[SICKCHESS] Demarrage\n", vivant=False))[0] == vv.BLOQUANT,
         "s'est ferme tout seul : bloque")
verifier(vv.controle_exe(os.path.join(dist, "rien"))[0] == vv.BLOQUANT, "pas de .exe : bloque")
shutil.rmtree(dist, ignore_errors=True)

print("7b. Le dossier d'essai = le jeu d'un ami (programme + jeu + moteur)")
# 25/10 : l'essai se faisait sur le programme seul : « No module named 'game_manager' »,
# et la n° 6 a ete bloquee a tort.
import publier_maj
dist = tempfile.mkdtemp(prefix="sickchess_dist_")
with open(os.path.join(dist, "SickChess.exe"), "w") as f:
    f.write("exe")
racine = tempfile.mkdtemp(prefix="sickchess_racine_")
for chemin in ("jeu/game_manager.py", "jeu/notes.txt", "moteur/stockfish.exe", "assets/logo.png"):
    os.makedirs(os.path.join(racine, os.path.dirname(chemin)), exist_ok=True)
    with open(os.path.join(racine, chemin), "w") as f:
        f.write("x")
base = tempfile.mkdtemp(prefix="sickchess_essai_")
d = publier_maj.dossier_d_essai({}, racine, dist, base=base)
verifier(os.path.isfile(os.path.join(d, "SickChess.exe")) and os.path.isfile(os.path.join(d, "jeu", "game_manager.py"))
         and os.path.isfile(os.path.join(d, "moteur", "stockfish.exe")) and os.path.isfile(os.path.join(d, "assets", "logo.png")),
         "le .exe, le code du jeu, les images et Stockfish sont dans le dossier d'essai")
verifier(not os.path.exists(os.path.join(d, "jeu", "notes.txt")), "comme chez un ami : seulement les .py du code")
verifier(publier_maj.dossier_d_essai({}, racine, os.path.join(dist, "rien")) == os.path.join(dist, "rien"),
         "pas d'exe : on ne fabrique rien (l'essai dira BLOQUANT)")
for dossier in (dist, racine, base):
    shutil.rmtree(dossier, ignore_errors=True)

print("8. Le vrai projet (sans tests ni banc)")
controles = vv.verifier("amis", RACINE, tests=False, banc=False, version_publiee="0.1.0", afficher=False)
verifier(not [c for c in controles if c[1] == vv.BLOQUANT],
         "rien de bloquant pour une version amis : %s" % [(c[0], c[1]) for c in controles])
steam = dict((c[0], c[1]) for c in vv.verifier("steam", RACINE, tests=False, banc=False,
                                               version_publiee="0.1.0", afficher=False))
verifier(steam["mode test"] == vv.BLOQUANT, "pour Steam aujourd'hui : MODE_TEST = True bloque (normal)")
verifier(steam["numéro Steam"] == vv.BLOQUANT,
         "pour Steam aujourd'hui : APPID_STEAM_REEL = None bloque (normal)")
itch = dict((c[0], c[1]) for c in vv.verifier("itch", RACINE, tests=False, banc=False,
                                              version_publiee="0.1.0", afficher=False))
verifier(itch["mode test"] == vv.BLOQUANT, "pour itch aujourd'hui : MODE_TEST = True bloque (normal)")
verifier(itch["numéro Steam"] == vv.OK and "paquet itch" in itch,
         "pour itch : pas de numero Steam, et le paquet est controle (%s)" % itch)
amis = dict((c[0], c[1]) for c in controles)
verifier(amis["numéro Steam"] == vv.OK and "paquet itch" not in amis,
         "pour les amis : rien ne change (480, pas de controle itch)")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
