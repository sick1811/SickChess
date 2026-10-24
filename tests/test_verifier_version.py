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


def projet(mode_test=True, appid="480", version="0.2.0", licences=True, credits_propres=False):
    d = tempfile.mkdtemp(prefix="sickchess_version_")
    os.makedirs(os.path.join(d, "jeu"))
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
etat, phrase = vv.controle_numero_steam(projet(appid="3412345"), "steam")
verifier(etat == vv.OK and "ne doit PAS contenir" in phrase, "Steam : vrai numero ok, avec le rappel")

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

print("8. Le vrai projet (sans tests ni banc)")
controles = vv.verifier("amis", RACINE, tests=False, banc=False, version_publiee="0.1.0", afficher=False)
verifier(not [c for c in controles if c[1] == vv.BLOQUANT],
         "rien de bloquant pour une version amis : %s" % [(c[0], c[1]) for c in controles])
steam = dict((c[0], c[1]) for c in vv.verifier("steam", RACINE, tests=False, banc=False,
                                               version_publiee="0.1.0", afficher=False))
verifier(steam["mode test"] == vv.BLOQUANT, "pour Steam aujourd'hui : MODE_TEST = True bloque (normal)")

print()
print("RESULTAT : %s" % ("tout est bon" if not echecs else "%d echec(s)" % len(echecs)))
sys.exit(1 if echecs else 0)
