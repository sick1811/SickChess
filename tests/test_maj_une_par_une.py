# tests/test_maj_une_par_une.py - 25/10, regles de Julien pour la version amis :
#   1. les mises a jour s'installent UNE PAR UNE : un ami a la n° 1 recoit la
#      n° 2, puis la n° 3, puis la n° 4, a la suite, avec UN SEUL redemarrage ;
#      un ami a la n° 3 ne recoit que la n° 4 ;
#   2. le jeu insiste tout seul quand le reseau flanche (reessais, DNS de secours) ;
#   3. le jeu s'autorise dans le pare-feu de Windows (prive ET public).
# Sans Internet : un faux site sur la machine, de faux paquets.
#     python tests/test_maj_une_par_une.py

import functools
import hashlib
import http.server
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
import zipfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "jeu"))
sys.path.insert(0, os.path.join(RACINE, "outils"))

import mise_a_jour as m
import pare_feu
import publier_maj

echecs = []


def verifier(condition, message):
    print(("  OK   " if condition else "  ECHEC ") + message)
    if not condition:
        echecs.append(message)


def attendre(maj, *etats, delai=20):
    fin = time.time() + delai
    while maj.etat not in etats and time.time() < fin:
        time.sleep(0.02)
    return maj.etat


m.ATTENTES_ESSAIS = (0, 0.05, 0.05)
base = tempfile.mkdtemp(prefix="sickchess_une_par_une_")
site = os.path.join(base, "site")


# ---------------------------------------------------------------- faux site
class Site(http.server.SimpleHTTPRequestHandler):
    demandes = []
    pannes = {}                     # chemin -> nombre de reponses 503 a donner

    def do_GET(self):
        Site.demandes.append(self.path)
        if Site.pannes.get(self.path, 0) > 0:
            Site.pannes[self.path] -= 1
            self.send_error(503)
            return
        super().do_GET()

    def log_message(self, *args):
        pass


serveur = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0), functools.partial(Site, directory=site))
threading.Thread(target=serveur.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d" % serveur.server_address[1]


def publier_fausse(numero, avec_liste=True):
    """Une version n : un paquet « jeu » qui contient jeu/version.txt = n."""
    dossier = os.path.join(site, "download", "n%d" % numero)
    os.makedirs(dossier, exist_ok=True)
    zip_chemin = os.path.join(dossier, "jeu-%d.zip" % numero)
    with zipfile.ZipFile(zip_chemin, "w") as z:
        z.writestr("jeu/version.txt", str(numero))
    with open(zip_chemin, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    versions = [{"numero": n, "etiquette": "n%d" % n,
                 "manifeste": "%s/download/n%d/maj.json" % (URL, n)}
                for n in range(1, numero + 1)]
    manifeste = {"jeu": "SickChess", "format": 1, "numero": numero, "version": "0.%d.0" % numero,
                 "etiquette": "n%d" % numero, "notes": ["version %d" % numero],
                 "paquets": {"jeu": {"empreinte": "e%d" % numero,
                                     "url": "%s/download/n%d/jeu-%d.zip" % (URL, numero, numero),
                                     "sha256": sha, "taille": os.path.getsize(zip_chemin)}}}
    if avec_liste:
        manifeste["versions"] = versions
    with open(os.path.join(dossier, "maj.json"), "w", encoding="utf-8") as f:
        json.dump(manifeste, f)
    os.makedirs(os.path.join(site, "latest"), exist_ok=True)
    shutil.copy(os.path.join(dossier, "maj.json"), os.path.join(site, "latest", "maj.json"))


def ami_a(numero, nom):
    dossier = os.path.join(base, nom)
    os.makedirs(os.path.join(dossier, "jeu"), exist_ok=True)
    with open(os.path.join(dossier, "jeu", "version.txt"), "w") as f:
        f.write(str(numero))
    with open(os.path.join(dossier, m.FICHIER_INSTALLE), "w", encoding="utf-8") as f:
        json.dump({"source": URL + "/latest/maj.json", "numero": numero,
                   "paquets": {"jeu": "e%d" % numero}}, f)
    with open(os.path.join(dossier, "profil.json"), "w") as f:
        f.write('{"nom": "ami"}')
    return dossier


def installer_comme_le_bat(dossier):
    """Ce que fait _maj.bat apres le telechargement (sans Windows)."""
    temp = os.path.join(dossier, m.DOSSIER_TEMP)
    extrait = os.path.join(temp, "extrait")
    for racine_, _, fichiers in os.walk(extrait):
        for nom in fichiers:
            source = os.path.join(racine_, nom)
            cible = os.path.join(dossier, os.path.relpath(source, extrait))
            os.makedirs(os.path.dirname(cible), exist_ok=True)
            shutil.copy(source, cible)
    shutil.copy(os.path.join(temp, m.FICHIER_INSTALLE), os.path.join(dossier, m.FICHIER_INSTALLE))
    shutil.rmtree(temp)


def un_redemarrage(dossier):
    """Le jeu demarre, verifie, telecharge la version suivante et l'installe.
    Renvoie (numero installe ensuite, etape affichee) ou (None, etat)."""
    maj = m.MiseAJour(dossier=dossier)
    maj.verifier()
    etat = attendre(maj, "disponible", "a_jour", "erreur")
    if etat != "disponible":
        return None, etat if etat != "erreur" else maj.erreur
    etape = maj.etape()
    maj.telecharger()
    if attendre(maj, "pret", "erreur") != "pret":
        return None, maj.erreur
    installer_comme_le_bat(dossier)
    return m.lire_installe(dossier)["numero"], etape


print("1. Une par une")
for n in (1, 2, 3, 4):
    publier_fausse(n)
verifier([n for n, _ in m.versions_manquantes(
    json.load(open(os.path.join(site, "latest", "maj.json"))), 1)] == [2, 3, 4],
    "ami a la n° 1 : il lui manque 2, 3 et 4, dans l'ordre")
verifier(m.versions_manquantes({"versions": [{"numero": 3, "manifeste": "x"}]}, None) == [],
         "numero installe inconnu : pas de liste (on prend la derniere)")

ami = ami_a(1, "ami_n1")
maj = m.MiseAJour(dossier=ami)
maj.verifier()
attendre(maj, "disponible", "a_jour", "erreur")
verifier(maj.numeros() == [2, 3, 4], "ami a la n° 1 : recoit la n° 2, la n° 3 et la n° 4 (%s)"
         % maj.numeros())
verifier(maj.etape() == "n° 2 à 4", "le bouton annonce « Mise à jour n° 2 à 4 » (%s)" % maj.etape())
verifier(maj.notes() == ["n° 2 : version 2", "n° 3 : version 3", "n° 4 : version 4"],
         "ce qui change : les notes de chaque version (%s)" % maj.notes())
Site.demandes.clear()
suite = []
for _ in range(5):
    numero, etape = un_redemarrage(ami)
    if numero is None:
        break
    suite.append((numero, etape))
verifier([n for n, _ in suite] == [4],
         "un seul redemarrage, et l'ami est a la n° 4 (%s)" % suite)
verifier([d for d in Site.demandes if d.endswith(".zip")]
         == ["/download/n2/jeu-2.zip", "/download/n3/jeu-3.zip", "/download/n4/jeu-4.zip"],
         "les paquets des n° 2, 3 et 4 sont tous recus, dans l'ordre")
verifier(open(os.path.join(ami, "jeu", "version.txt")).read() == "4",
         "a la fin, le jeu de l'ami est bien la n° 4")
verifier(open(os.path.join(ami, "profil.json")).read() == '{"nom": "ami"}', "son profil est garde")
numero, etat = un_redemarrage(ami)
verifier(numero is None and etat == "a_jour", "puis : a jour, plus rien a installer")

ami3 = ami_a(3, "ami_n3")
suite = []
for _ in range(3):
    numero, etape = un_redemarrage(ami3)
    if numero is None:
        break
    suite.append(numero)
verifier(suite == [4], "ami a la n° 3 : n'installe que la n° 4 (%s)" % suite)

print("2. Anciennes versions sans liste")
publier_fausse(5, avec_liste=False)
ami_vieux = ami_a(2, "ami_sans_liste")
numero, _ = un_redemarrage(ami_vieux)
verifier(numero == 5, "maj.json sans liste : on prend la derniere, comme avant (%s)" % numero)

print("3. Publication : la liste des versions")
liste = publier_maj.liste_des_versions(
    "sick1811/SickChess-amis", {"numero": 6, "etiquette": "v0.2.0-n6"}, 7, "v0.2.1-n7",
    en_ligne=["v0.1.0-n1", "v0.1.0-n2", "v0.1.0-n3", "v0.1.0-n4", "v0.1.0-n5", "v0.2.0-n6"])
verifier([v["numero"] for v in liste] == [1, 2, 3, 4, 5, 6, 7],
         "la n° 7 retrouve les n° 1 a 6 deja en ligne")
verifier(liste[3]["manifeste"].endswith("/releases/download/v0.1.0-n4/maj.json"),
         "chaque version garde l'adresse de son propre maj.json")
suivante = publier_maj.liste_des_versions("d", {"numero": 7, "versions": liste}, 8, "v0.3.0-n8",
                                          en_ligne=[])
verifier([v["numero"] for v in suivante] == list(range(1, 9)),
         "la n° 8 reprend la liste de la n° 7 et s'y ajoute")
verifier(publier_maj.liste_des_versions("d", {}, 1, "v0.1.0-n1", en_ligne=["zz"])
         == [{"numero": 1, "etiquette": "v0.1.0-n1",
              "manifeste": "https://github.com/d/releases/download/v0.1.0-n1/maj.json"}],
         "toute premiere version : la liste ne contient qu'elle")

print("4. Le reseau flanche : le jeu insiste")
Site.pannes["/latest/maj.json"] = 2
ami5 = ami_a(4, "ami_panne")
maj = m.MiseAJour(dossier=ami5)
maj.verifier()
verifier(attendre(maj, "disponible", "a_jour", "erreur") == "disponible",
         "deux pannes (503) puis le site repond : la mise a jour passe quand meme")
Site.demandes.clear()
maj = m.MiseAJour(dossier=ami5, url=URL + "/absent/maj.json")
maj.verifier()
attendre(maj, "erreur", "a_jour", "disponible")
verifier(Site.demandes.count("/absent/maj.json") == 1,
         "fichier absent (404) : pas de reessai inutile")
verifier(m._reessayable(socket.timeout()) and m._reessayable(ConnectionResetError()),
         "delai depasse, connexion coupee : on reessaie")

print("5. DNS de secours")
verifier(socket.getaddrinfo is m._getaddrinfo_avec_secours, "branche des le chargement du jeu")
verifier(m.hote_de_secours("github.com") and m.hote_de_secours("release-assets.githubusercontent.com")
         and not m.hote_de_secours("example.com") and not m.hote_de_secours("evilgithub.com"),
         "seulement pour les sites de la mise a jour")
vrai_systeme, vrai_doh = m._getaddrinfo_systeme, m.resoudre_par_https


def dns_en_panne(hote, port, *a, **k):
    if not str(hote)[0].isdigit():
        raise socket.gaierror(11001, "getaddrinfo failed")
    return vrai_systeme(hote, port, *a, **k)


m._getaddrinfo_systeme = dns_en_panne
m.resoudre_par_https = lambda hote, **k: ["127.0.0.1"]
try:
    adresses = socket.getaddrinfo("github.com", 443, type=socket.SOCK_STREAM)
    verifier(adresses and adresses[0][4][0] == "127.0.0.1",
             "DNS du PC en panne : github.com trouve par le DNS securise")
    try:
        socket.getaddrinfo("example.com", 80)
        verifier(False, "les autres sites ne passent pas par le secours")
    except socket.gaierror:
        verifier(True, "les autres sites ne passent pas par le secours")
    m.resoudre_par_https = lambda hote, **k: []
    try:
        socket.getaddrinfo("github.com", 443)
        verifier(False, "secours sans reponse : l'erreur d'origine remonte")
    except socket.gaierror:
        verifier(True, "secours sans reponse : l'erreur d'origine remonte")
finally:
    m._getaddrinfo_systeme, m.resoudre_par_https = vrai_systeme, vrai_doh

print("6. Pare-feu (prive et public)")
exe = r"C:\Users\Jean Dupont\AppData\Local\Programs\SickChess\SickChess.exe"
ligne = pare_feu.ligne_de_commande(exe)
verifier(ligne.count("profile=any") == 2 and "dir=in" in ligne and "dir=out" in ligne,
         "deux regles Autoriser (entree, sortie) sur tous les reseaux")
verifier('delete rule name=all program="%s"' % exe in ligne,
         "les anciennes regles du jeu (dont les blocages de Windows) sont retirees d'abord")
verifier(ligne.index("delete") < ligne.index("add"), "retirer avant d'ajouter")
verifier(ligne.count('"%s"' % exe) == 3, "chemin avec espaces bien entre guillemets")
verifier(pare_feu.decider(exe, True, {}, 6) == "ok", "regle deja la : rien a demander")
verifier(pare_feu.decider(exe, False, {}, 6) == "demander", "regle absente : Windows demande l'accord")
deja = {"exe": exe, "numero": 6, "demande": True}
verifier(pare_feu.decider(exe, False, deja, 6) == "attendre",
         "refuse pour cette version : on ne redemande pas a chaque lancement")
verifier(pare_feu.decider(exe, False, deja, 7) == "demander", "nouvelle version : on redemande")
verifier(pare_feu.decider(exe.replace("Jean", "Paul"), False, deja, 6) == "demander",
         "jeu deplace dans un autre dossier : on redemande")


class Reponse:
    def __init__(self, code, texte):
        self.returncode, self.stdout = code, texte.encode("utf-8")


verifier(pare_feu.regle_presente(exe, lancer=lambda *a, **k: Reponse(0, "Programme: %s" % exe)),
         "regle trouvee pour ce chemin")
verifier(not pare_feu.regle_presente(exe, lancer=lambda *a, **k: Reponse(1, "Aucune regle")),
         "aucune regle : absente")
verifier(not pare_feu.regle_presente(exe, lancer=lambda *a, **k: Reponse(0, r"C:\Autre\SickChess.exe")),
         "regle d'un ancien dossier : comptee comme absente")
verifier(pare_feu.au_demarrage() in ("hors_exe", "desactive"),
         "depuis les sources (ou hors Windows) : rien n'est demande")
verifier("pare_feu.json" in m.FICHIERS_A_TOI, "pare_feu.json n'est jamais ecrase par une mise a jour")
iss = open(os.path.join(RACINE, "outils", "installeur_amis.iss"), encoding="utf-8").read()
verifier("profile=any" in iss and "'runas'" in iss and "not WizardSilent" in iss,
         "l'installeur autorise aussi le jeu (accord Windows, pas en silencieux)")

# 31/10 (demande de Julien) : l'installeur ne depasse pas 1 Go ; problemes et tables
# de finales sont telecharges PAR l'installeur, pas mis dedans.
verifier(not set(publier_maj.DANS_L_INSTALLEUR) & {"puzzles", "syzygy"}
         and set(publier_maj.TELECHARGES) == {"puzzles", "syzygy"},
         "problemes et finales : telecharges par l'installeur, pas dedans")
verifier(publier_maj.LIMITE_INSTALLEUR == 1024 ** 3, "limite de l'installeur : 1 Go")
verifier("ArchiveExtraction=full" in iss and "#include Telechargements" in iss,
         "l'installeur sait telecharger et decompresser les .zip")
faux = {"paquets": {"syzygy": {"url": "https://github.com/x/y/releases/download/v1/syzygy-ab.zip",
                               "sha256": "ABCDEF", "taille": 1234}}}
lignes = publier_maj.lignes_telechargement(faux, ["puzzles", "syzygy"])
verifier(len(lignes) == 1 and 'Source: "https://github.com/x/y/releases/download/v1/syzygy-ab.zip"'
         in lignes[0] and 'Hash: "abcdef"' in lignes[0] and "external download extractarchive"
         in lignes[0] and "ExternalSize: 1234" in lignes[0] and 'DestDir: "{app}"' in lignes[0],
         "ligne de telechargement : adresse, SHA-256, decompression dans le dossier du jeu")

serveur.shutdown()
serveur.server_close()
shutil.rmtree(base, ignore_errors=True)
print()
if echecs:
    print("%d ECHEC(S)" % len(echecs))
    sys.exit(1)
print("TOUT EST OK")
