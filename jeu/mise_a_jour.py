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
#   syzygy    : les tables de finales                         ~ 380 Mo, jamais
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
# TES DONNEES NE SONT JAMAIS TOUCHEES : config.json, profil.json, parties/,
# scores des problemes, sauvegardes... sont exclus de la copie (FICHIERS_A_TOI).

import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
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
                  "journal_du_jeu.txt", "diagnostic_son.txt", FICHIER_INSTALLE]
DOSSIERS_A_TOI = ["parties", DOSSIER_TEMP]

DELAI_RESEAU = 20
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


def _ouvrir(url, timeout=DELAI_RESEAU):
    requete = urllib.request.Request(url, headers={"User-Agent": "SickChess-maj"})
    return urllib.request.urlopen(requete, timeout=timeout)


def lire_manifeste(url):
    """Telecharge et verifie maj.json. Leve ValueError si illisible."""
    with _ouvrir(url) as reponse:
        brut = reponse.read(2 * 1024 * 1024)
    donnees = json.loads(brut.decode("utf-8"))
    if not isinstance(donnees, dict) or not isinstance(donnees.get("paquets"), dict):
        raise ValueError("maj.json ne ressemble pas a un manifeste SickChess")
    if int(donnees.get("format", 0)) > FORMAT:
        raise ValueError("Cette mise à jour demande une version plus récente du "
                         "programme : redemande le jeu complet à Julien.")
    for nom, paquet in donnees["paquets"].items():
        for cle in ("empreinte", "url", "sha256", "taille"):
            if cle not in paquet:
                raise ValueError("paquet %s incomplet (%s manque)" % (nom, cle))
    return donnees


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

    def notes(self):
        notes = (self.manifeste or {}).get("notes") or []
        return [str(n) for n in notes][:12] if isinstance(notes, list) else [str(notes)]

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
            self.manifeste = lire_manifeste(self.url)
            self.installe = lire_installe(self.dossier)
            self.a_telecharger = paquets_a_telecharger(self.manifeste, self.installe)
            self.octets_total = sum(int(self.manifeste["paquets"][n]["taille"])
                                    for n in self.a_telecharger)
            self.etat = "disponible" if self.a_telecharger else "a_jour"
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
        message = str(souci) or souci.__class__.__name__
        if isinstance(souci, OSError) and not isinstance(souci, FileNotFoundError):
            message = "pas de connexion Internet, ou le site ne repond pas"
        self.erreur = "%s : %s" % (quoi, message[:140])
        self.etat = "erreur"
        print("[MAJ] %s" % self.erreur)

    def _telecharger(self):
        temp = os.path.join(self.dossier, DOSSIER_TEMP)
        try:
            shutil.rmtree(temp, ignore_errors=True)
            extrait = os.path.join(temp, "extrait")
            os.makedirs(extrait, exist_ok=True)
            for nom in self.a_telecharger:
                paquet = self.manifeste["paquets"][nom]
                self.paquet_en_cours = NOMS_LISIBLES.get(nom, nom)
                chemin = os.path.join(temp, nom + ".zip")
                self._telecharger_un(paquet["url"], chemin)
                if self._annuler:
                    raise InterruptedError("annule")
                if _sha256(chemin) != paquet["sha256"]:
                    raise ValueError("le fichier %s est abîmé (somme de contrôle "
                                     "fausse). Réessaie." % nom)
                _extraire(chemin, extrait)
                os.remove(chemin)
            # Ce que le jeu aura APRES l'installation.
            installe = dict(self.installe or {})
            paquets = dict(installe.get("paquets", {}))
            for nom in self.a_telecharger:
                paquets[nom] = self.manifeste["paquets"][nom]["empreinte"]
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
# (vrai par defaut). Le jeu reverifie toutes les 20 minutes s'il reste ouvert.
REVERIFIER_TOUTES_LES = 20 * 60
ATTENTE_AVANT_REDEMARRAGE = 3.0


def pas_automatique(maj, config, maintenant, etat_auto):
    """Un pas de la mise a jour automatique, appele a chaque image du menu.
    etat_auto : petit dict garde par l'appelant ({} au depart).
    Renvoie (action, libelle) : action = None | "telecharger" | "installer" |
    "verifier" ; libelle = texte du bouton du menu, ou None (libelle normal)."""
    if maj is None or not (config or {}).get("maj_auto", True):
        return None, None
    etat = maj.etat
    if etat == "disponible":
        return "telecharger", "Mise à jour : téléchargement…"
    if etat == "telechargement":
        return None, "Mise à jour : %d %%" % int(100 * maj.progression())
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
