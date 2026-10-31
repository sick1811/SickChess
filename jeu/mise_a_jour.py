# mise_a_jour.py - SickChess : le bouton "Mise a jour" de la version amis.
#
# L'IDEE : au lieu d'envoyer un nouveau jeu complet a chaque correction, Julien
# publie la nouvelle version a UN endroit (une "release" GitHub). Le jeu de ses
# amis va y lire un petit fichier, maj.json, et ne telecharge que ce qui a change.
#
# LE JEU EST COUPE EN PAQUETS, parce qu'ils ne changent pas au meme rythme :
#   programme : SickChess.exe + _internal (Python, pygame)   ~ 30 Mo, rarement
#   jeu       : le code (jeu/*.py), images, sons, polices     ~ 10 Mo, souvent
#   moteur    : Stockfish                                     ~ 110 Mo, rarement
#   puzzles   : la base de problemes                          ~ 220 Mo, rarement
#   syzygy    : les tables de finales (WDL + DTZ, 31/10)      ~ 940 Mo, rarement
# Une correction de bug ne fait donc telecharger que quelques Mo.
#
# CHAQUE PAQUET a une "empreinte" (calculee par outils/publier_maj.py a partir
# de son contenu). Le jeu note dans paquets_installes.json les empreintes qu'il
# a : un paquet dont l'empreinte a change (ou qui manque) est a telecharger.
#
# LES ETAPES :
#   1. Verification   : lire maj.json (quelques Ko), comparer.
#   2. Telechargement : chaque paquet manquant, dans maj_temp/, avec sa somme
#                       SHA-256 verifiee (un fichier abime est refuse).
#   3. Preparation    : les zips sont decompresses dans maj_temp/extrait/.
#   4. Installation   : le jeu ecrit _maj.bat, le lance, et se ferme. Le .bat
#                       attend que SickChess soit ferme (Windows interdit de
#                       remplacer un .exe qui tourne), recopie les fichiers,
#                       efface maj_temp et relance le jeu.
#
# UNE PAR UNE (25/10, regle de Julien) : un ami reste a la n° 3 recoit la n° 4,
# puis la n° 5, puis la n° 6, chacune a son tour (ses paquets telecharges et poses
# dans l'ordre), et le jeu ne redemarre qu'UNE fois, a la fin ; un ami a la n° 5
# ne recoit que la n° 6. Le maj.json de la derniere version porte la liste "versions" (numero +
# adresse du maj.json de chaque version, publiee par outils/publier_maj.py) : le
# jeu prend TOUTES les versions plus recentes que la sienne. Sans cette liste
# (versions publiees avant le 25/10), il prend la derniere, comme avant.
# Les versions publiees ne doivent donc JAMAIS etre effacees de GitHub.
#
# SANS RIEN DEMANDER AU JOUEUR (25/10) : chaque lecture reseau est reessayee
# (3 essais), et si le DNS du PC ne trouve pas GitHub (box, reseau public), le jeu
# demande l'adresse a un DNS securise (Cloudflare, Google, en HTTPS) ; la
# connexion reste verifiee par le certificat de GitHub, rien n'est contourne.
#
# TES DONNEES NE SONT JAMAIS TOUCHEES : config.json, profil.json, parties/,
# scores des problemes, sauvegardes... sont exclus de la copie (FICHIERS_A_TOI).

import hashlib
import json
import os
import shutil
import socket
import ssl
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

FICHIER_INSTALLE = "paquets_installes.json"
DOSSIER_TEMP = "maj_temp"
SCRIPT_INSTALLATION = "_maj.bat"
FORMAT = 1

NOMS_LISIBLES = {
    "programme": "Programme",
    "jeu": "Jeu (code, images, sons)",
    "moteur": "Moteur Stockfish",
    "puzzles": "Problèmes",
    "syzygy": "Tables de finales",
}

# Fichiers et dossiers du joueur : une mise a jour ne les ecrase jamais.
FICHIERS_A_TOI = ["config.json", "profil.json", "puzzles_score.json",
                  "statistiques.json", "sauvegarde*.json", "partie_en_cours.json",
                  "journal_du_jeu.txt", "diagnostic_son.txt", "pare_feu.json",
                  FICHIER_INSTALLE]
DOSSIERS_A_TOI = ["parties", DOSSIER_TEMP]

DELAI_RESEAU = 20
# Attente avant chaque essai (secondes) : 3 essais, puis on abandonne pour cette
# fois (le menu reessaie tout seul quelques minutes plus tard).
ATTENTES_ESSAIS = (0, 3, 8)
TAILLE_BLOC = 256 * 1024


# ---------------------------------------------------------------- utilitaires

def dossier_du_jeu():
    """Ou le jeu est installe (a cote de SickChess.exe)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lire_installe(dossier=None):
    """Contenu de paquets_installes.json, ou None (version de developpement)."""
    chemin = os.path.join(dossier or dossier_du_jeu(), FICHIER_INSTALLE)
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            donnees = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(donnees, dict) or not isinstance(donnees.get("paquets"), dict):
        return None
    return donnees


def installation_geree(dossier=None):
    """Vrai pour la version amis (installee avec paquets_installes.json)."""
    installe = lire_installe(dossier)
    return bool(installe and installe.get("source"))


def version_affichee(defaut="", dossier=None):
    """'0.2.0 (n°7)' pour la version amis, sinon la version du code."""
    installe = lire_installe(dossier)
    if not installe:
        return defaut
    version = installe.get("version") or defaut
    numero = installe.get("numero")
    return "%s (n°%s)" % (version, numero) if numero else version


def taille_lisible(octets):
    octets = float(octets or 0)
    if octets >= 1024 ** 3:
        return "%.1f Go" % (octets / 1024 ** 3)
    if octets >= 1024 ** 2:
        return "%.0f Mo" % (octets / 1024 ** 2)
    return "%.0f Ko" % max(1, octets / 1024)


def cause_lisible(souci):
    """La vraie raison d'un echec, en mots simples (affichee dans le jeu).

    24/10 : avant, toute erreur reseau donnait « pas de connexion Internet » ;
    un fichier absent sur le site (version en cours de publication, erreur 404)
    faisait donc croire a Julien que son Internet etait coupe."""
    raison = getattr(souci, "reason", None)
    if isinstance(souci, urllib.error.HTTPError):
        if souci.code == 404:
            return ("fichier de mise à jour introuvable sur le site (erreur 404) : "
                    "une version est peut-être en cours de publication, réessaie "
                    "dans quelques minutes")
        return "le site de mise à jour a répondu par une erreur (%d)" % souci.code
    if isinstance(souci, urllib.error.URLError) and isinstance(raison, BaseException):
        souci = raison                     # la vraie cause est dedans
    if isinstance(souci, ssl.SSLError):
        return ("connexion sécurisée refusée (certificat) : vérifie la date et "
                "l'heure du PC, ou ton antivirus")
    if isinstance(souci, socket.gaierror):
        return ("pas d'Internet, ou adresse du site de mise à jour introuvable "
                "(vérifie ta connexion)")
    if isinstance(souci, (TimeoutError, socket.timeout)):
        return "le site de mise à jour ne répond pas (délai dépassé), réessaie plus tard"
    if isinstance(souci, ConnectionRefusedError):
        return "connexion refusée par le site de mise à jour (pare-feu ou antivirus ?)"
    if isinstance(souci, (ConnectionResetError, ConnectionAbortedError)):
        return "connexion coupée pendant l'échange avec le site, réessaie"
    if isinstance(souci, FileNotFoundError):
        return "fichier introuvable sur le PC : %s" % (souci.filename or souci)
    if isinstance(souci, PermissionError):
        return "le jeu n'a pas le droit d'écrire dans son dossier : %s" % (souci.filename or souci)
    if isinstance(souci, OSError):
        return "pas de connexion Internet, ou le site ne répond pas"
    return str(souci) or souci.__class__.__name__


# ---------------------------------------------------------------- DNS de secours
# 25/10 : un ami avait « adresse du site introuvable » alors que GitHub marchait :
# c'est le DNS de son reseau (box, Wi-Fi public, ecole) qui ne repondait pas. Pour
# les seuls sites de la mise a jour, quand le DNS du PC echoue, on demande
# l'adresse a un DNS public en HTTPS. Le certificat du site reste verifie.
HOTES_SECOURS = ("github.com", "githubusercontent.com")
SERVEURS_DNS_SECOURS = ("https://1.1.1.1/dns-query?name=%s&type=A",
                        "https://8.8.8.8/resolve?name=%s&type=A")
_getaddrinfo_systeme = socket.getaddrinfo
_DNS_CACHE = {}


def hote_de_secours(hote):
    hote = str(hote or "").lower().rstrip(".")
    return any(hote == h or hote.endswith("." + h) for h in HOTES_SECOURS)


def resoudre_par_https(hote, serveurs=SERVEURS_DNS_SECOURS, timeout=8):
    """Adresses IPv4 de hote, demandees a un DNS public en HTTPS ([] si rien)."""
    if hote in _DNS_CACHE:
        return _DNS_CACHE[hote]
    for modele in serveurs:
        try:
            requete = urllib.request.Request(modele % hote, headers={
                "Accept": "application/dns-json", "User-Agent": "SickChess-maj"})
            with urllib.request.urlopen(requete, timeout=timeout) as reponse:
                donnees = json.loads(reponse.read(65536).decode("utf-8"))
            ips = [r["data"] for r in donnees.get("Answer", [])
                   if r.get("type") == 1 and r.get("data")]
            if ips:
                _DNS_CACHE[hote] = ips
                print("[MAJ] DNS du PC sans reponse pour %s : adresse obtenue par "
                      "DNS securise (%s)" % (hote, ", ".join(ips[:3])))
                return ips
        except Exception as souci:
            print("[MAJ] DNS securise %s : %s" % (modele.split("/")[2], souci))
    return []


def _getaddrinfo_avec_secours(hote, port, *args, **kwargs):
    try:
        return _getaddrinfo_systeme(hote, port, *args, **kwargs)
    except socket.gaierror:
        if not hote_de_secours(hote):
            raise
        ips = resoudre_par_https(str(hote).lower().rstrip("."))
        if not ips:
            raise
        resultat = []
        for ip in ips:
            try:
                resultat.extend(_getaddrinfo_systeme(ip, port, *args, **kwargs))
            except socket.gaierror:
                pass
        if not resultat:
            raise
        return resultat


def activer_dns_de_secours():
    """Branche le DNS de secours (une fois). Ne change rien pour les autres sites."""
    if socket.getaddrinfo is not _getaddrinfo_avec_secours:
        socket.getaddrinfo = _getaddrinfo_avec_secours


activer_dns_de_secours()


def _reessayable(souci):
    if isinstance(souci, urllib.error.HTTPError):
        return souci.code >= 500 or souci.code == 429
    return isinstance(souci, (urllib.error.URLError, OSError))


def _ouvrir_une_fois(url, timeout):
    requete = urllib.request.Request(url, headers={"User-Agent": "SickChess-maj"})
    return urllib.request.urlopen(requete, timeout=timeout)


def _ouvrir(url, timeout=DELAI_RESEAU):
    """Ouvre url ; reessaie seul (reseau qui flanche) avant d'abandonner."""
    souci = None
    for numero, attente in enumerate(ATTENTES_ESSAIS, 1):
        if attente:
            time.sleep(attente)
        try:
            return _ouvrir_une_fois(url, timeout)
        except Exception as e:
            souci = e
            hote = urllib.parse.urlparse(url).hostname
            print("[MAJ] essai %d/%d rate (%s) : %s: %s" % (
                numero, len(ATTENTES_ESSAIS), hote, e.__class__.__name__, e))
            if not _reessayable(e):
                break
    raise souci


def lire_manifeste(url):
    """Telecharge et verifie maj.json. Leve ValueError si illisible."""
    with _ouvrir(url) as reponse:
        brut = reponse.read(2 * 1024 * 1024)
    donnees = json.loads(brut.decode("utf-8"))
    if not isinstance(donnees, dict) or not isinstance(donnees.get("paquets"), dict):
        raise ValueError("fichier de mise à jour illisible (pas un manifeste SickChess)")
    if int(donnees.get("format", 0)) > FORMAT:
        raise ValueError("Cette mise à jour demande une version plus récente du "
                         "programme : redemande le jeu complet à Julien.")
    for nom, paquet in donnees["paquets"].items():
        for cle in ("empreinte", "url", "sha256", "taille"):
            if cle not in paquet:
                raise ValueError("paquet %s incomplet (%s manque)" % (nom, cle))
    return donnees


def versions_manquantes(dernier, numero_installe):
    """Les versions a installer, dans l'ordre : [(numero, adresse du maj.json)].
    Vide si la liste "versions" manque ou si le numero installe est inconnu."""
    try:
        numero_installe = int(numero_installe)
    except (TypeError, ValueError):
        return []
    liste = []
    for v in (dernier or {}).get("versions") or []:
        try:
            n = int(v["numero"])
        except (KeyError, TypeError, ValueError):
            continue
        if n > numero_installe and v.get("manifeste"):
            liste.append((n, str(v["manifeste"])))
    return sorted(set(liste))


def paquets_a_telecharger(manifeste, installe):
    """Noms des paquets nouveaux ou changes, dans l'ordre du manifeste."""
    deja = (installe or {}).get("paquets", {})
    return [nom for nom, paquet in manifeste["paquets"].items()
            if deja.get(nom) != paquet["empreinte"]]


def _sha256(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(TAILLE_BLOC), b""):
            h.update(bloc)
    return h.hexdigest()


def _extraire(zip_chemin, destination):
    """Decompresse en refusant tout chemin qui sortirait du dossier."""
    racine = os.path.realpath(destination)
    with zipfile.ZipFile(zip_chemin) as archive:
        for membre in archive.infolist():
            cible = os.path.realpath(os.path.join(racine, membre.filename))
            if cible != racine and not cible.startswith(racine + os.sep):
                raise ValueError("chemin interdit dans l'archive : %s" % membre.filename)
        archive.extractall(racine)


# ---------------------------------------------------------------- le travail

class MiseAJour:
    """Tout le cycle, en tache de fond : l'ecran ne gele jamais.

    etat : "rien" | "verification" | "a_jour" | "disponible" | "telechargement"
           | "pret" | "erreur" | "annule"
    """

    def __init__(self, dossier=None, url=None):
        self.dossier = dossier or dossier_du_jeu()
        self.installe = lire_installe(self.dossier)
        self.url = url or (self.installe or {}).get("source", "")
        self.etat = "rien"
        self.erreur = ""
        self.manifeste = None
        self.dernier = None          # maj.json de la toute derniere version
        self.etapes = []             # [(maj.json d'une version, [paquets])], dans l'ordre
        self.a_telecharger = []
        self.octets_total = 0
        self.octets_recus = 0
        self.paquet_en_cours = ""
        self._annuler = False
        self._thread = None

    # ------------------------------------------------------------ infos

    def geree(self):
        return bool(self.url)

    def version_installee(self):
        return version_affichee("", self.dossier) or "?"

    def version_disponible(self):
        m = self.manifeste or {}
        return "%s (n°%s)" % (m.get("version", "?"), m.get("numero", "?"))

    def numeros(self):
        return [m.get("numero") for m, _ in self.etapes]

    def etape(self):
        """« n° 6 », ou « n° 4 à 6 » quand plusieurs versions arrivent ensemble."""
        numeros = self.numeros() or [(self.manifeste or {}).get("numero", "?")]
        if len(numeros) > 1:
            return "n° %s à %s" % (numeros[0], numeros[-1])
        return "n° %s" % numeros[0]

    def notes(self):
        lignes = []
        plusieurs = len(self.etapes) > 1
        for manifeste, _ in (self.etapes or [(self.manifeste or {}, [])]):
            notes = manifeste.get("notes") or []
            notes = [str(n) for n in notes] if isinstance(notes, list) else [str(notes)]
            if plusieurs:
                notes = ["n° %s : %s" % (manifeste.get("numero"), n) for n in notes]
            lignes.extend(notes)
        return lignes[-12:]

    def progression(self):
        if not self.octets_total:
            return 0.0
        return min(1.0, self.octets_recus / float(self.octets_total))

    def occupe(self):
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------ actions

    def verifier(self):
        """Lance la verification en tache de fond."""
        if self.occupe() or not self.geree():
            if not self.geree():
                self.etat, self.erreur = "erreur", ("Les mises à jour ne marchent que "
                                                    "dans la version envoyée aux amis.")
            return
        self.etat = "verification"
        self.erreur = ""
        self._thread = threading.Thread(target=self._verifier, daemon=True)
        self._thread.start()

    def _verifier(self):
        try:
            self.dernier = lire_manifeste(self.url)
            self.installe = lire_installe(self.dossier)
            # Une par une : toutes les versions plus recentes que celle installee,
            # dans l'ordre (la derniere est deja lue).
            manquantes = versions_manquantes(self.dernier,
                                             (self.installe or {}).get("numero"))
            manifestes = []
            for numero, adresse in manquantes:
                if numero == self.dernier.get("numero"):
                    manifestes.append(self.dernier)
                    continue
                version = lire_manifeste(adresse)
                if int(version.get("numero", -1)) != numero:
                    raise ValueError("la version n° %d annoncée ne correspond pas "
                                     "à son fichier" % numero)
                manifestes.append(version)
            if not manifestes or manifestes[-1].get("numero") != self.dernier.get("numero"):
                manifestes.append(self.dernier)      # sans liste : la derniere seule
            # Ce qu'il faut pour chaque version, a partir de ce qu'aura le jeu
            # apres la precedente.
            etat = dict((self.installe or {}).get("paquets", {}))
            self.etapes = []
            for manifeste in manifestes:
                noms = paquets_a_telecharger(manifeste, {"paquets": etat})
                for nom in noms:
                    etat[nom] = manifeste["paquets"][nom]["empreinte"]
                if noms:
                    self.etapes.append((manifeste, noms))
            self.manifeste = self.dernier
            self.a_telecharger = []
            for _, noms in self.etapes:
                self.a_telecharger += [n for n in noms if n not in self.a_telecharger]
            self.octets_total = sum(int(m["paquets"][n]["taille"])
                                    for m, noms in self.etapes for n in noms)
            print("[MAJ] installee : n° %s ; derniere : n° %s ; a installer : %s"
                  % ((self.installe or {}).get("numero"), self.dernier.get("numero"),
                     self.numeros() or "rien"))
            self.etat = "disponible" if self.etapes else "a_jour"
        except Exception as souci:
            self._echec("Impossible de vérifier les mises à jour", souci)

    def telecharger(self):
        """Telecharge, verifie et prepare les paquets. Etat final : 'pret'."""
        if self.occupe() or self.etat != "disponible":
            return
        self._annuler = False
        self.octets_recus = 0
        self.etat = "telechargement"
        self._thread = threading.Thread(target=self._telecharger, daemon=True)
        self._thread.start()

    def annuler(self):
        self._annuler = True

    def _echec(self, quoi, souci):
        self.erreur = "%s : %s" % (quoi, cause_lisible(souci)[:160])
        self.etat = "erreur"
        # Le journal garde aussi l'erreur brute (pour Claude, s'il faut chercher).
        print("[MAJ] %s (%s: %s)" % (self.erreur, souci.__class__.__name__, souci))

    def _telecharger(self):
        temp = os.path.join(self.dossier, DOSSIER_TEMP)
        try:
            shutil.rmtree(temp, ignore_errors=True)
            extrait = os.path.join(temp, "extrait")
            os.makedirs(extrait, exist_ok=True)
            paquets = dict((self.installe or {}).get("paquets", {}))
            # Chaque version a son tour : ses paquets sont poses par-dessus ceux de
            # la precedente (la n° 5 remplace ce que la n° 4 avait change).
            for manifeste, noms in self.etapes:
                for nom in noms:
                    paquet = manifeste["paquets"][nom]
                    self.paquet_en_cours = "n° %s – %s" % (
                        manifeste.get("numero"), NOMS_LISIBLES.get(nom, nom))
                    chemin = os.path.join(temp, nom + ".zip")
                    self._telecharger_un(paquet["url"], chemin)
                    if self._annuler:
                        raise InterruptedError("annule")
                    if _sha256(chemin) != paquet["sha256"]:
                        raise ValueError("le fichier %s est abîmé (somme de contrôle "
                                         "fausse). Réessaie." % nom)
                    _extraire(chemin, extrait)
                    os.remove(chemin)
                    paquets[nom] = paquet["empreinte"]
                print("[MAJ] version n° %s prete (%s)" % (manifeste.get("numero"), ", ".join(noms)))
            # Ce que le jeu aura APRES l'installation (un seul redemarrage).
            installe = dict(self.installe or {})
            installe.update({"paquets": paquets, "numero": self.manifeste.get("numero"),
                             "version": self.manifeste.get("version"),
                             "source": self.url, "installe_le": time.strftime("%Y-%m-%d %H:%M")})
            with open(os.path.join(temp, FICHIER_INSTALLE), "w", encoding="utf-8") as f:
                json.dump(installe, f, indent=2, ensure_ascii=False)
            self.etat = "pret"
        except InterruptedError:
            shutil.rmtree(temp, ignore_errors=True)
            self.etat = "annule"
        except Exception as souci:
            shutil.rmtree(temp, ignore_errors=True)
            self._echec("Téléchargement raté", souci)

    def _telecharger_un(self, url, chemin):
        with _ouvrir(url) as reponse, open(chemin, "wb") as sortie:
            while not self._annuler:
                bloc = reponse.read(TAILLE_BLOC)
                if not bloc:
                    break
                sortie.write(bloc)
                self.octets_recus += len(bloc)

    # ------------------------------------------------------------ installation

    def script_installation(self, pid=None, exe=None):
        """Le texte du .bat qui termine l'installation une fois le jeu ferme."""
        pid = int(pid or os.getpid())
        exe = exe or os.path.basename(sys.executable if getattr(sys, "frozen", False)
                                      else "SickChess.exe")
        exclus_f = " ".join('"%s"' % f for f in FICHIERS_A_TOI)
        exclus_d = " ".join('"%s"' % d for d in DOSSIERS_A_TOI)
        return "\r\n".join([
            "@echo off",
            "chcp 65001 >nul",
            "title SickChess - installation de la mise a jour",
            'cd /d "%~dp0"',
            "echo.",
            "echo   Installation de la mise a jour de SickChess...",
            "echo   (cette fenetre se ferme toute seule)",
            ":attendre",
            'tasklist /FI "PID eq %d" 2>nul | find " %d " >nul' % (pid, pid),
            "if not errorlevel 1 (",
            "    timeout /t 1 /nobreak >nul",
            "    goto attendre",
            ")",
            'robocopy "%s\\extrait" "." /E /R:30 /W:1 /NFL /NDL /NJH /NJS /NP /XF %s /XD %s'
            % (DOSSIER_TEMP, exclus_f, exclus_d),
            "if errorlevel 8 goto echec",
            'copy /y "%s\\%s" "%s" >nul' % (DOSSIER_TEMP, FICHIER_INSTALLE, FICHIER_INSTALLE),
            'rmdir /s /q "%s"' % DOSSIER_TEMP,
            'start "" "%s"' % exe,
            '(goto) 2>nul & del "%~f0"',
            ":echec",
            "echo.",
            "echo   La copie des fichiers a echoue (antivirus ? jeu encore ouvert ?).",
            "echo   Ferme tout, puis relance SickChess et refais la mise a jour.",
            "pause",
            '(goto) 2>nul & del "%~f0"',
            "",
        ])

    def lancer_installation(self):
        """Ecrit _maj.bat et le lance. Le jeu doit se fermer juste apres.
        Renvoie True si le script est parti."""
        if self.etat != "pret":
            return False
        chemin = os.path.join(self.dossier, SCRIPT_INSTALLATION)
        with open(chemin, "w", encoding="utf-8", newline="") as f:
            f.write(self.script_installation())
        if sys.platform != "win32":
            print("[MAJ] (hors Windows) script ecrit sans etre lance : %s" % chemin)
            return False
        try:
            subprocess.Popen(["cmd", "/c", chemin], cwd=self.dossier,
                             creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
                             close_fds=True)
        except OSError as souci:
            self._echec("Impossible de lancer l'installation", souci)
            return False
        return True


# ---------------------------------------------------------------- pour le menu

_FOND = {"maj": None}


def verifier_en_arriere_plan():
    """Au demarrage : verification discrete. Renvoie l'objet MiseAJour (ou
    None pour la version de developpement)."""
    if _FOND["maj"] is None:
        if not installation_geree():
            return None
        _FOND["maj"] = MiseAJour()
        _FOND["maj"].verifier()
    return _FOND["maj"]


# 23/10 - MISE A JOUR AUTOMATIQUE (demande de Julien : « il se met a jour a chaque
# nouvelle modification »). Dans le menu, une nouvelle version publiee est
# telechargee toute seule, puis installee (le jeu redemarre) - jamais pendant une
# partie, puisque seul le menu appelle ceci. Reglage "maj_auto" de config.json
# (vrai par defaut). 25/10 : le jeu reverifie toutes les 3 minutes s'il reste
# ouvert (avant : 20 min), et apres un echec aussi : il insiste tout seul.
REVERIFIER_TOUTES_LES = 3 * 60
ATTENTE_AVANT_REDEMARRAGE = 3.0


def pas_automatique(maj, config, maintenant, etat_auto):
    """Un pas de la mise a jour automatique, appele a chaque image du menu.
    etat_auto : petit dict garde par l'appelant ({} au depart).
    Renvoie (action, libelle) : action = None | "telecharger" | "installer" |
    "verifier" ; libelle = texte du bouton du menu, ou None (libelle normal)."""
    if maj is None or not (config or {}).get("maj_auto", True):
        return None, None
    etat = maj.etat
    etape = maj.etape() if hasattr(maj, "etape") else ""
    nom = ("Mise à jour %s" % etape) if etape else "Mise à jour"
    if etat == "disponible":
        return "telecharger", "%s : téléchargement…" % nom
    if etat == "telechargement":
        return None, "%s : %d %%" % (nom, int(100 * maj.progression()))
    if etat == "pret":
        depuis = etat_auto.setdefault("pret_depuis", maintenant)
        if maintenant - depuis >= ATTENTE_AVANT_REDEMARRAGE:
            if etat_auto.get("installation_lancee"):
                return None, "Nouvelle version : redémarrage…"
            etat_auto["installation_lancee"] = True      # une seule tentative
            return "installer", "Nouvelle version : redémarrage…"
        return None, "Nouvelle version prête : redémarrage…"
    if etat in ("a_jour", "erreur"):
        derniere = etat_auto.setdefault("verifie_le", maintenant)
        if maintenant - derniere >= REVERIFIER_TOUTES_LES:
            etat_auto["verifie_le"] = maintenant
            return "verifier", None
    return None, None


def disponible():
    """Vrai si la verification de fond a trouve une mise a jour."""
    maj = _FOND["maj"]
    return maj is not None and maj.etat == "disponible"


def nettoyer_restes(dossier=None):
    """Efface un maj_temp/ abandonne (jeu ferme pendant un telechargement)."""
    dossier = dossier or dossier_du_jeu()
    if not os.path.exists(os.path.join(dossier, SCRIPT_INSTALLATION)):
        shutil.rmtree(os.path.join(dossier, DOSSIER_TEMP), ignore_errors=True)
