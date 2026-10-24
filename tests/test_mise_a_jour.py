# tests/test_mise_a_jour.py - verifie tout le circuit des mises a jour,
# sans Internet et sans toucher au vrai jeu :
#     python tests/test_mise_a_jour.py
#
# Dans un dossier temporaire : un faux projet SickChess, publie deux fois avec
# outils/publier_maj.py, servi par un petit serveur web local. Un "ami"
# installe SickChess_amis.zip, clique Mise a jour, recoit les paquets
# manquants ; puis Julien change seulement le code et republie : l'ami ne
# telecharge que le paquet "jeu". On verifie aussi qu'un fichier abime est
# refuse, qu'une coupure Internet est bien expliquee, et que ses donnees
# (config, profil, parties) ne sont jamais ecrasees.

import functools
import http.server
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import zipfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "jeu"))
sys.path.insert(0, os.path.join(RACINE, "outils"))

import mise_a_jour
import publier_maj

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def ecrire(chemin, contenu):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    mode = "wb" if isinstance(contenu, bytes) else "w"
    with open(chemin, mode) as f:
        f.write(contenu)


def attendre(maj, *etats, delai=20):
    fin = time.time() + delai
    while maj.etat not in etats and time.time() < fin:
        time.sleep(0.02)
    return maj.etat


def copier_comme_le_bat(source, cible):
    """Ce que fait robocopy dans _maj.bat, en Python (pour tester hors Windows) :
    tout recopier SAUF les fichiers et dossiers du joueur."""
    import fnmatch
    for dossier, sous, fichiers in os.walk(source):
        rel = os.path.relpath(dossier, source)
        sous[:] = [d for d in sous if d not in mise_a_jour.DOSSIERS_A_TOI]
        for nom in fichiers:
            if any(fnmatch.fnmatch(nom, motif) for motif in mise_a_jour.FICHIERS_A_TOI):
                continue
            destination = os.path.join(cible, rel, nom)
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copyfile(os.path.join(dossier, nom), destination)


base = tempfile.mkdtemp(prefix="sickchess_maj_")
projet = os.path.join(base, "projet")
publier = os.path.join(base, "publier")
dist = os.path.join(base, "dist")
ami = os.path.join(base, "chez_paul")

# ---------------------------------------------------------------- faux projet
ecrire(os.path.join(projet, "SickChess.py"), 'VERSION = "0.2.0"\nimport json\n')
ecrire(os.path.join(projet, "jeu", "ui.py"), "VALEUR = 1\n")
ecrire(os.path.join(projet, "jeu", "board.py"), "import ui\nimport chess\n")
ecrire(os.path.join(projet, "jeu", "__pycache__", "ui.cpython-313.pyc"), b"cache")
ecrire(os.path.join(projet, "assets", "logo.png"), b"\x89PNG logo")
ecrire(os.path.join(projet, "sounds", "move.wav"), b"RIFF son")
ecrire(os.path.join(projet, "config.json"), '{"volume": 0.6}')
ecrire(os.path.join(projet, "moteur", "stockfish.exe"), b"MZ" + b"x" * 50000)
ecrire(os.path.join(projet, "puzzles", "p00.tsv.gz"), b"\x1f\x8b" + b"p" * 30000)
ecrire(os.path.join(dist, "SickChess.exe"), b"MZ exe v1")
ecrire(os.path.join(dist, "_internal", "python313.dll"), b"dll")

# ---------------------------------------------------------------- serveur local
class Discret(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


serveur = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0), functools.partial(Discret, directory=publier))
threading.Thread(target=serveur.serve_forever, daemon=True).start()
ADRESSE = "http://127.0.0.1:%d" % serveur.server_address[1]
DEPOT = "julien/SickChess-amis"


def vers_local(manifeste):
    """Les adresses GitHub du manifeste -> le serveur local."""
    for paquet in manifeste["paquets"].values():
        paquet["url"] = paquet["url"].replace(
            "https://github.com/%s/releases/download" % DEPOT, ADRESSE)
    for chemin in (os.path.join(publier, "maj.json"),
                   os.path.join(publier, manifeste["etiquette"], "maj.json")):
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(manifeste, f)


print("1. Premiere publication")
m1 = publier_maj.publier("Premiere version ; Son corrige", racine=projet,
                         dossier_publier=publier, dist=dist, envoyer=False,
                         depot=DEPOT)
verifier(m1 is not None and m1["numero"] == 1, "version n°1 publiee")
verifier(set(m1["paquets"]) == {"programme", "jeu", "moteur", "puzzles"},
         "paquets : programme, jeu, moteur, puzzles (syzygy absent = ignore)")
verifier(m1["notes"] == ["Premiere version", "Son corrige"], "notes de version decoupees")
dossier_v1 = os.path.join(publier, m1["etiquette"])
with zipfile.ZipFile(os.path.join(dossier_v1, os.path.basename(
        m1["paquets"]["jeu"]["url"]))) as z:
    noms = z.namelist()
verifier("jeu/ui.py" in noms and not any("__pycache__" in n for n in noms),
         "le paquet jeu contient le code, sans les fichiers de cache")
verifier(m1["paquets"]["moteur"]["url"].startswith(
    "https://github.com/%s/releases/download/v0.2.0-n1/" % DEPOT),
    "adresses GitHub correctes")
vers_local(m1)

print("2. Un ami installe SickChess_amis.zip")
with zipfile.ZipFile(os.path.join(dossier_v1, "SickChess_amis.zip")) as z:
    z.extractall(ami)
ami = os.path.join(ami, "SickChess")
installe = mise_a_jour.lire_installe(ami)
verifier(installe and set(installe["paquets"]) == {"programme", "jeu"},
         "le zip d'installation contient programme + jeu")
verifier(os.path.exists(os.path.join(ami, "SickChess.exe"))
         and os.path.exists(os.path.join(ami, "jeu", "board.py")), "exe et code en place")
verifier(installe["source"] == "https://github.com/%s/releases/latest/download/maj.json"
         % DEPOT, "l'adresse de verification est celle de GitHub 'latest'")
verifier(mise_a_jour.version_affichee("x", ami) == "0.2.0 (n°1)", "version affichee 0.2.0 (n°1)")
# Pour le test, on fait pointer l'ami vers le serveur local.
installe["source"] = ADRESSE + "/maj.json"
ecrire(os.path.join(ami, "paquets_installes.json"), json.dumps(installe))
# Il joue : ses donnees a lui
ecrire(os.path.join(ami, "config.json"), '{"volume": 0.1, "a_moi": true}')
ecrire(os.path.join(ami, "profil.json"), '{"nom": "Paul", "elo": 1450}')
ecrire(os.path.join(ami, "parties", "partie1.pgn"), "1. e4 e5")

print("3. Premier clic sur Mise a jour : il manque moteur et puzzles")
maj = mise_a_jour.MiseAJour(dossier=ami)
maj.verifier()
verifier(attendre(maj, "disponible", "a_jour", "erreur") == "disponible",
         "mise a jour disponible (%s)" % maj.erreur)
verifier(maj.a_telecharger == ["moteur", "puzzles"], "a telecharger : %s" % maj.a_telecharger)
maj.telecharger()
verifier(attendre(maj, "pret", "erreur") == "pret", "telecharge et prepare (%s)" % maj.erreur)
verifier(maj.progression() == 1.0, "barre de progression a 100 %")
extrait = os.path.join(ami, "maj_temp", "extrait")
verifier(os.path.exists(os.path.join(extrait, "moteur", "stockfish.exe")),
         "Stockfish decompresse dans maj_temp/extrait")
script = maj.script_installation(pid=4242, exe="SickChess.exe")
verifier('find " 4242 "' in script and "robocopy" in script
         and '"config.json"' in script and '"parties"' in script
         and '"profil.json"' in script, "le .bat attend le jeu et protege tes donnees")
verifier(script.count("\r\n") > 20, "le .bat a des fins de ligne Windows")
# Ce que fera le .bat :
copier_comme_le_bat(extrait, ami)
shutil.copyfile(os.path.join(ami, "maj_temp", "paquets_installes.json"),
                os.path.join(ami, "paquets_installes.json"))
shutil.rmtree(os.path.join(ami, "maj_temp"))
verifier(os.path.exists(os.path.join(ami, "moteur", "stockfish.exe")), "Stockfish installe")
apres = mise_a_jour.lire_installe(ami)
verifier(set(apres["paquets"]) == {"programme", "jeu", "moteur", "puzzles"}
         and apres["source"] == ADRESSE + "/maj.json", "paquets_installes.json a jour")

maj = mise_a_jour.MiseAJour(dossier=ami)
maj.verifier()
verifier(attendre(maj, "a_jour", "disponible", "erreur") == "a_jour",
         "ensuite : 'tu as la derniere version'")

print("4. Julien corrige un bug dans le code et republie")
ecrire(os.path.join(projet, "jeu", "ui.py"), "VALEUR = 2  # bug corrige\n")
m2 = publier_maj.publier("Bug de la pendule corrige", racine=projet,
                         dossier_publier=publier, dist=dist, envoyer=False, depot=DEPOT)
verifier(m2["numero"] == 2, "version n°2")
nouveaux = sorted(n for n in m2["paquets"]
                  if m2["paquets"][n]["empreinte"] != m1["paquets"][n]["empreinte"])
verifier(nouveaux == ["jeu"], "seul le paquet jeu change (%s)" % nouveaux)
verifier(m2["paquets"]["moteur"]["url"] == m1["paquets"]["moteur"]["url"],
         "le moteur n'est pas re-envoye : on garde l'ancienne adresse")
zips_v2 = sorted(n for n in os.listdir(os.path.join(publier, m2["etiquette"]))
                 if n.endswith(".zip"))
verifier(zips_v2 == sorted(["SickChess_amis.zip",
                            os.path.basename(m2["paquets"]["jeu"]["url"])]),
         "a envoyer sur GitHub : %s" % zips_v2)
vers_local(m2)
maj = mise_a_jour.MiseAJour(dossier=ami)
maj.verifier()
attendre(maj, "disponible", "a_jour", "erreur")
verifier(maj.a_telecharger == ["jeu"] and maj.octets_total < 5000,
         "l'ami ne telecharge que le code (%s)" % mise_a_jour.taille_lisible(maj.octets_total))
verifier(maj.notes() == ["Bug de la pendule corrige"], "il voit ce qui change")
maj.telecharger()
attendre(maj, "pret", "erreur")
copier_comme_le_bat(os.path.join(ami, "maj_temp", "extrait"), ami)
with open(os.path.join(ami, "jeu", "ui.py")) as f:
    verifier("bug corrige" in f.read(), "le nouveau code est installe")
with open(os.path.join(ami, "config.json")) as f:
    verifier('"a_moi": true' in f.read(), "ses reglages ne sont PAS ecrases")
with open(os.path.join(ami, "profil.json")) as f:
    verifier("Paul" in f.read(), "son profil est garde")
verifier(os.path.exists(os.path.join(ami, "parties", "partie1.pgn")), "ses parties sont gardees")
shutil.rmtree(os.path.join(ami, "maj_temp"), ignore_errors=True)

print("5. Rien de change : rien a publier")
verifier(publier_maj.publier("", racine=projet, dossier_publier=publier,
                             envoyer=False, depot=DEPOT) is None,
         "republier sans changement ne cree pas de version vide")

print("6. Fichier abime et coupure Internet")
abime = json.load(open(os.path.join(publier, "maj.json")))
abime["paquets"]["jeu"]["empreinte"] = "autre"
abime["paquets"]["jeu"]["sha256"] = "0" * 64
ecrire(os.path.join(publier, "maj.json"), json.dumps(abime))
maj = mise_a_jour.MiseAJour(dossier=ami)
maj.verifier()
attendre(maj, "disponible", "erreur")
maj.telecharger()
verifier(attendre(maj, "pret", "erreur") == "erreur" and "abîmé" in maj.erreur,
         "un fichier abime est refuse (%s)" % maj.erreur)
verifier(not os.path.exists(os.path.join(ami, "maj_temp")), "et rien ne reste sur le disque")
serveur.shutdown()
serveur.server_close()
maj = mise_a_jour.MiseAJour(dossier=ami)
maj.verifier()
verifier(attendre(maj, "erreur", "a_jour", "disponible") == "erreur"
         and "connexion" in maj.erreur, "pas d'Internet : message clair (%s)" % maj.erreur)

print("6 bis. La vraie cause d'un echec (24/10 : la v1 disait toujours « pas de connexion »)")
import socket
import ssl
import urllib.error
causes = [
    (urllib.error.HTTPError("u", 404, "Not Found", None, None), "introuvable"),
    (urllib.error.HTTPError("u", 503, "Unavailable", None, None), "503"),
    (urllib.error.URLError(socket.gaierror(11001, "getaddrinfo failed")), "Internet"),
    (urllib.error.URLError(TimeoutError("timed out")), "ne répond pas"),
    (TimeoutError("timed out"), "ne répond pas"),
    (urllib.error.URLError(ConnectionRefusedError(10061, "refused")), "refusée"),
    (urllib.error.URLError(ssl.SSLCertVerificationError(1, "certificate verify failed")),
     "sécurisée"),
    (ValueError("fichier de mise à jour illisible (pas un manifeste SickChess)"), "illisible"),
]
for souci, attendu in causes:
    texte = mise_a_jour.cause_lisible(souci)
    verifier(attendu in texte, "%s -> %s" % (souci.__class__.__name__, texte))
verifier(mise_a_jour.cause_lisible(urllib.error.HTTPError("u", 404, "x", None, None))
         != mise_a_jour.cause_lisible(urllib.error.URLError(socket.gaierror(11001, "x"))),
         "fichier absent et pas d'Internet ne donnent plus le meme message")
# Pour de vrai : un site qui repond mais n'a pas maj.json (version en cours de publication)
class Vide(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_error(404)

    def log_message(self, *args):
        pass


vide = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Vide)
threading.Thread(target=vide.serve_forever, daemon=True).start()
maj = mise_a_jour.MiseAJour(dossier=ami,
                            url="http://127.0.0.1:%d/maj.json" % vide.server_address[1])
maj.verifier()
verifier(attendre(maj, "erreur", "a_jour", "disponible") == "erreur"
         and "introuvable" in maj.erreur and "connexion Internet" not in maj.erreur,
         "fichier absent sur le site : dit « introuvable », pas « pas d'Internet » (%s)"
         % maj.erreur)
vide.shutdown()
vide.server_close()

print("7. Archive piegee")
piege = os.path.join(base, "piege.zip")
with zipfile.ZipFile(piege, "w") as z:
    z.writestr("../../hors_du_jeu.txt", "non")
try:
    mise_a_jour._extraire(piege, os.path.join(base, "x"))
    verifier(False, "une archive qui sort du dossier est refusee")
except ValueError:
    verifier(True, "une archive qui sort du dossier est refusee")

print("8. Version de developpement")
verifier(not mise_a_jour.installation_geree(projet), "depuis les sources : pas de mise a jour")
verifier(mise_a_jour.version_affichee("0.2.0", projet) == "0.2.0", "version des sources affichee")

shutil.rmtree(base, ignore_errors=True)
print()
if echecs:
    print("%d ECHEC(S)" % len(echecs))
    sys.exit(1)
print("TOUT EST OK")
