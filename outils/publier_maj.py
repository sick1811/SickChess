# publier_maj.py - fabrique une nouvelle version amis de SickChess.
#
# Lance par CONSTRUIRE_VERSION_AMIS.bat. A la main :
#     py outils/publier_maj.py --notes "Son corrige ; nouvel ecran de revue"
#
# CE QU'IL FAIT :
#   1. Calcule l'empreinte de chaque paquet (programme, jeu, moteur, puzzles,
#      syzygy) et la compare a la version precedente (publier/maj.json).
#   2. Refait l'exe avec PyInstaller SEULEMENT si le lanceur, la recette ou la
#      liste des modules Python utilises ont change.
#   3. Zippe uniquement les paquets qui ont change, dans publier/<etiquette>/.
#   4. Ecrit maj.json (le fichier que le jeu des amis va lire) et
#      SickChess_amis.zip (le jeu a donner a un NOUVEL ami : programme + jeu ;
#      le reste se telecharge au premier clic sur "Mise a jour").
#   5. Si GitHub CLI (gh) est installe et connecte : cree la "release" sur
#      GitHub et y envoie les fichiers. Sinon, explique quoi glisser ou.
#
# OU C'EST HEBERGE : les "releases" d'un depot GitHub (gratuit, 2 Go par
# fichier). Le depot est dans outils/maj_config.json. Le jeu des amis lit
# toujours la meme adresse :
#     https://github.com/<depot>/releases/latest/download/maj.json
# ("latest" = la release la plus recente).

import argparse
import ast
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_PUBLIER = os.path.join(RACINE, "publier")
DOSSIER_BUILD = os.path.join(RACINE, "build_amis")
RECETTE = os.path.join(RACINE, "outils", "sickchess_amis.spec")
CONFIG = os.path.join(RACINE, "outils", "maj_config.json")
FORMAT = 1

# Ce que contient chaque paquet (chemins depuis la racine du projet).
PAQUETS = {
    # Pas de config.json : c'est celui de Julien. Le jeu a ses reglages par
    # defaut et cree config.json chez l'ami au premier passage dans Options.
    "jeu": ["jeu", "assets", "sounds", "music", "polices", "ouvertures", "docs/CREDITS.md", "LICENSE", "LICENCE.md", "licenses",
            "moteur/COPYING-Stockfish.txt", "steam_api64.dll", "steam_appid.txt",
            "LISEZ-MOI_AMIS.txt",
            # 25/10 : l'adresse du salon Discord de « Signaler » (hors Git).
            "signalement.json"],
    "moteur": ["moteur"],
    "puzzles": ["puzzles"],
    "syzygy": ["syzygy"],
}
ORDRE = ["programme", "jeu", "moteur", "puzzles", "syzygy"]
DEJA_COMPRESSES = (".gz", ".zip", ".rtbw", ".rtbz", ".png", ".jpg", ".ogg", ".mp3")
IGNORES = ("__pycache__", ".pyc", ".pyo", "Thumbs.db", ".DS_Store")


def dire(texte=""):
    print(texte, flush=True)


# ---------------------------------------------------------------- empreintes

def _sha256_fichier(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloc)
    return h.hexdigest()


def fichiers_du_paquet(racine, elements):
    """[(chemin_absolu, nom_dans_le_zip)] tries, sans les fichiers de cache."""
    trouves = []
    for element in elements:
        chemin = os.path.join(racine, element)
        if os.path.isfile(chemin):
            trouves.append((chemin, element.replace("\\", "/")))
        elif os.path.isdir(chemin):
            for dossier, sous, fichiers in os.walk(chemin):
                sous[:] = sorted(d for d in sous if d not in IGNORES)
                for nom in sorted(fichiers):
                    if nom.endswith(IGNORES) or nom in IGNORES:
                        continue
                    if element == "jeu" and not nom.endswith(".py"):
                        continue
                    absolu = os.path.join(dossier, nom)
                    trouves.append((absolu, os.path.relpath(absolu, racine)
                                    .replace("\\", "/")))
    return sorted(trouves, key=lambda e: e[1])


def empreinte(fichiers):
    h = hashlib.sha256()
    for absolu, nom in fichiers:
        h.update(nom.encode("utf-8") + b"\0" + _sha256_fichier(absolu).encode() + b"\n")
    return h.hexdigest()


def modules_utilises(racine):
    """Les modules (hors jeu) importes par jeu/*.py et SickChess.py."""
    dossier = os.path.join(racine, "jeu")
    locaux = {os.path.splitext(n)[0] for n in os.listdir(dossier) if n.endswith(".py")}
    noms = set()
    sources = [os.path.join(dossier, n) for n in os.listdir(dossier) if n.endswith(".py")]
    sources.append(os.path.join(racine, "SickChess.py"))
    for source in sources:
        try:
            with open(source, "r", encoding="utf-8") as f:
                arbre = ast.parse(f.read())
        except (OSError, SyntaxError, ValueError):
            continue
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Import):
                noms.update(a.name for a in noeud.names)
            elif isinstance(noeud, ast.ImportFrom) and noeud.module and not noeud.level:
                noms.add(noeud.module)
    return sorted(n for n in noms if n.split(".")[0] not in locaux)


def version_paquet(nom_module):
    try:
        from importlib.metadata import version
        return version(nom_module)
    except Exception:
        return "?"


def recette_programme(racine):
    """Empreinte de tout ce qui change l'exe. Si elle ne bouge pas, on garde
    l'exe deja publie (les amis ne retelechargent pas 30 Mo pour rien)."""
    h = hashlib.sha256()
    for chemin in (os.path.join(racine, "SickChess.py"), RECETTE,
                   os.path.join(racine, "assets", "icone.ico")):
        if os.path.exists(chemin):
            h.update(_sha256_fichier(chemin).encode())
    h.update(("%s|%s|%s" % (platform.python_version(), sys.platform,
                            platform.architecture()[0])).encode())
    for module in ("pygame", "chess", "pyinstaller"):
        h.update(("%s=%s;" % (module, version_paquet(module))).encode())
    h.update("|".join(modules_utilises(racine)).encode())
    return h.hexdigest()


# ---------------------------------------------------------------- briques

def lire_version(racine):
    with open(os.path.join(racine, "SickChess.py"), "r", encoding="utf-8") as f:
        trouve = re.search(r'^VERSION\s*=\s*"([^"]+)"', f.read(), re.M)
    return trouve.group(1) if trouve else "0.0.0"


def lire_config():
    try:
        with open(CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (OSError, ValueError):
        config = {}
    config.setdefault("depot", "sick1811/SickChess-amis")
    return config


def url_manifeste(depot):
    return "https://github.com/%s/releases/latest/download/maj.json" % depot


def manifeste_precedent(depot, dossier_publier):
    chemin = os.path.join(dossier_publier, "maj.json")
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        pass
    try:                                   # pas de copie locale : celle en ligne
        requete = urllib.request.Request(url_manifeste(depot),
                                         headers={"User-Agent": "SickChess"})
        with urllib.request.urlopen(requete, timeout=15) as reponse:
            return json.loads(reponse.read().decode("utf-8"))
    except Exception:
        return None


def url_manifeste_de(depot, etiquette):
    """Adresse fixe du maj.json d'UNE version (pour les mises a jour une par une)."""
    return "https://github.com/%s/releases/download/%s/maj.json" % (depot, etiquette)


def etiquettes_en_ligne(depot):
    """Les etiquettes deja publiees (v0.1.0-n4...) lues sur GitHub avec git.
    Sert une seule fois : quand la version precedente n'a pas encore de liste."""
    try:
        sortie = subprocess.run(["git", "ls-remote", "--tags",
                                 "https://github.com/%s.git" % depot],
                                capture_output=True, text=True, timeout=60,
                                env=dict(os.environ, GIT_TERMINAL_PROMPT="0")).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return sorted({ligne.split("refs/tags/")[-1].replace("^{}", "")
                   for ligne in sortie.splitlines() if "refs/tags/" in ligne})


def liste_des_versions(depot, precedent, numero, etiquette, en_ligne=None):
    """25/10 (regle de Julien : les mises a jour s'installent UNE PAR UNE) :
    la liste de toutes les versions publiees, ecrite dans chaque maj.json.
    Le jeu d'un ami y prend la premiere version plus recente que la sienne."""
    versions = {}
    anciennes = (precedent or {}).get("versions") or []
    if not anciennes and precedent:
        # Premiere fois : on retrouve les versions deja en ligne (n° 1 a 6).
        tags = etiquettes_en_ligne(depot) if en_ligne is None else en_ligne
        anciennes = []
        for tag in tags:
            m = re.match(r"^v[\w.]+-n(\d+)$", tag)
            if m:
                anciennes.append({"numero": int(m.group(1)), "etiquette": tag})
        if precedent and precedent.get("etiquette"):
            anciennes.append({"numero": int(precedent["numero"]),
                              "etiquette": precedent["etiquette"]})
    for v in anciennes:
        try:
            n = int(v["numero"])
        except (KeyError, TypeError, ValueError):
            continue
        if n < numero and v.get("etiquette"):
            versions[n] = {"numero": n, "etiquette": v["etiquette"],
                           "manifeste": v.get("manifeste")
                           or url_manifeste_de(depot, v["etiquette"])}
    versions[numero] = {"numero": numero, "etiquette": etiquette,
                        "manifeste": url_manifeste_de(depot, etiquette)}
    return [versions[n] for n in sorted(versions)]


def zipper(fichiers, destination):
    with zipfile.ZipFile(destination, "w") as archive:
        for absolu, nom in fichiers:
            mode = zipfile.ZIP_STORED if nom.lower().endswith(DEJA_COMPRESSES) \
                else zipfile.ZIP_DEFLATED
            archive.write(absolu, nom, compress_type=mode)


def construire_exe(racine):
    dire("  PyInstaller fabrique SickChess.exe (2 a 5 minutes)...")
    commande = [sys.executable, "-m", "PyInstaller", RECETTE, "--noconfirm",
                "--clean", "--distpath", os.path.join(DOSSIER_BUILD, "dist"),
                "--workpath", os.path.join(DOSSIER_BUILD, "travail")]
    resultat = subprocess.run(commande, cwd=racine)
    if resultat.returncode != 0:
        raise SystemExit("PyInstaller a echoue : regarde les messages au-dessus.")
    dist = os.path.join(DOSSIER_BUILD, "dist", "SickChess")
    signer([os.path.join(dist, "SickChess.exe")])
    return dist


# ---------------------------------------------------------------- signature

def signer(chemins):
    """Signe les fichiers si une signature est reglee dans outils/maj_config.json :
        "signature": {"commande": ["signtool", "sign", "/fd", "SHA256",
                                   "/tr", "http://timestamp.digicert.com", "/td", "SHA256", "/a"]}
    (certificat de signature de code installe sur le PC). Sans reglage : rien, le jeu
    marche quand meme, Windows affichera seulement « editeur inconnu »."""
    commande = (lire_config().get("signature") or {}).get("commande")
    if not commande:
        return False
    for chemin in chemins:
        if os.path.exists(chemin):
            r = subprocess.run(list(commande) + [chemin])
            dire("  signature %s : %s" % (os.path.basename(chemin),
                                          "OK" if r.returncode == 0 else "ECHEC"))
    return True


# ---------------------------------------------------------------- installeur

ISS = os.path.join(RACINE, "outils", "installeur_amis.iss")


def trouver_iscc():
    """Le compilateur d'Inno Setup (winget install JRSoftware.InnoSetup)."""
    for nom in ("ISCC", "iscc"):
        if shutil.which(nom):
            return shutil.which(nom)
    for variable, sous in (("ProgramFiles(x86)", ""), ("ProgramFiles", ""),
                           ("LOCALAPPDATA", "Programs")):
        base = os.environ.get(variable)
        if base:
            chemin = os.path.join(base, sous, "Inno Setup 6", "ISCC.exe")
            if os.path.exists(chemin):
                return chemin
    return None


def dossier_d_essai(contenus, racine, dist, base=None):
    """25/10 : le dossier du jeu tel qu'un ami l'a : programme (SickChess.exe) +
    jeu (le code, a cote de l'exe) + moteur. L'essai du .exe se faisait sur le
    programme SEUL : « No module named 'game_manager' », et la n° 6 bloquee a tort.
    Renvoie le dossier, ou dist si l'exe n'est pas la."""
    if not dist or not os.path.isfile(os.path.join(dist, "SickChess.exe")):
        return dist
    dossier = os.path.join(base or os.path.join(DOSSIER_BUILD, "essai"), "SickChess")
    shutil.rmtree(dossier, ignore_errors=True)
    shutil.copytree(dist, dossier)
    for nom in ("jeu", "moteur"):
        fichiers = (contenus or {}).get(nom) or fichiers_du_paquet(racine, PAQUETS[nom])
        for absolu, relatif in fichiers:
            cible = os.path.join(dossier, relatif)
            os.makedirs(os.path.dirname(cible), exist_ok=True)
            shutil.copy2(absolu, cible)
    return dossier


# 31/10 (demande de Julien) : l'installeur ne doit jamais depasser 1 Go.
LIMITE_INSTALLEUR = 1024 ** 3
DANS_L_INSTALLEUR = ["jeu", "moteur"]
TELECHARGES = ["puzzles", "syzygy"]     # telecharges PAR l'installeur


def lignes_telechargement(manifeste, noms, contenus=None):
    """Lignes [Files] d'Inno Setup qui telechargent les paquets `noms` depuis leur
    release GitHub (adresse du maj.json), verifient leur SHA-256 et les decompressent
    dans le dossier du jeu. ExternalSize = taille decompressee (place sur le disque)."""
    lignes = []
    for nom in noms:
        paquet = manifeste["paquets"].get(nom)
        if not paquet:
            continue
        fichiers = (contenus or {}).get(nom) or []
        taille = sum(os.path.getsize(a) for a, _ in fichiers) or paquet["taille"]
        lignes.append(
            'Source: "%s"; DestName: "%s.zip"; DestDir: "{app}"; Hash: "%s"; '
            'ExternalSize: %d; Flags: external download extractarchive recursesubdirs '
            'createallsubdirs ignoreversion'
            % (paquet["url"], nom, paquet["sha256"].lower(), taille))
    return lignes


def _installeur(manifeste, contenus, racine, dist, sortie, depot):
    """SickChess_Installation.exe : installeur Windows pour un NOUVEL ami.
    Dedans : programme, jeu, Stockfish (~100 Mo). 31/10 : problemes et tables de
    finales (~1,2 Go avec les DTZ) depassaient 1 Go : l'installeur les TELECHARGE
    pendant l'installation (somme SHA-256 verifiee). Tout marche des la fin de
    l'installation, comme avant. SICKCHESS_INSTALLEUR_LEGER=1 : pas de
    telechargement (ils arrivent alors par la mise a jour automatique)."""
    iscc = trouver_iscc()
    if iscc is None:
        dire("  (Installeur non fabrique : Inno Setup absent. Pour l'avoir :"
             " winget install JRSoftware.InnoSetup)")
        return None
    programme = contenus.get("programme")
    if programme is None:
        dossier = dist or os.path.join(DOSSIER_BUILD, "dist", "SickChess")
        if not os.path.isdir(dossier):
            dire("  (Installeur non fabrique : l'exe n'est pas dans build_amis/.)")
            return None
        programme = fichiers_du_paquet(dossier, sorted(os.listdir(dossier)))
    scene = os.path.join(DOSSIER_BUILD, "installeur", "SickChess")
    shutil.rmtree(os.path.dirname(scene), ignore_errors=True)
    leger = os.environ.get("SICKCHESS_INSTALLEUR_LEGER") == "1"
    inclus = ["programme"] + [n for n in DANS_L_INSTALLEUR if contenus.get(n)]
    telecharges = [] if leger else [n for n in TELECHARGES if n in manifeste["paquets"]]
    tous = list(programme)
    for n in inclus[1:]:
        tous += contenus[n]
    for absolu, nom in tous:
        cible = os.path.join(scene, nom)
        os.makedirs(os.path.dirname(cible), exist_ok=True)
        shutil.copy2(absolu, cible)
    installe = {"source": url_manifeste(depot), "numero": manifeste["numero"],
                "version": manifeste["version"],
                "paquets": {n: manifeste["paquets"][n]["empreinte"]
                            for n in inclus + telecharges if n in manifeste["paquets"]}}
    with open(os.path.join(scene, "paquets_installes.json"), "w", encoding="utf-8") as f:
        json.dump(installe, f, indent=2, ensure_ascii=False)
    commande = [iscc, "/Q", "/DVersion=%s" % manifeste["version"],
                "/DNumero=%d" % manifeste["numero"], "/DSource=%s" % scene,
                "/DSortie=%s" % sortie]
    if telecharges:
        include = os.path.join(os.path.dirname(scene), "telechargements.iss")
        with open(include, "w", encoding="utf-8-sig") as f:
            f.write("\n".join(lignes_telechargement(manifeste, telecharges, contenus)) + "\n")
        commande.append("/DTelechargements=%s" % include)
    dire("  installeur : Inno Setup compresse %s%s (2 a 4 minutes)..."
         % (", ".join(inclus), " ; telecharges a l'installation : " + ", ".join(telecharges)
            if telecharges else ""))
    r = subprocess.run(commande + [ISS])
    chemin = os.path.join(sortie, "SickChess_Installation.exe")
    if r.returncode != 0 or not os.path.exists(chemin):
        dire("  (Installeur : Inno Setup a echoue, voir les messages au-dessus.)")
        return None
    if os.path.getsize(chemin) > LIMITE_INSTALLEUR:
        taille = os.path.getsize(chemin)
        os.remove(chemin)
        raise SystemExit("Installeur trop gros (%s, limite 1 Go) : rien n'est envoye."
                         % _mo(taille))
    signer([chemin])
    dire("  SickChess_Installation.exe (nouvel ami) : %s" % _mo(os.path.getsize(chemin)))
    return chemin


# ---------------------------------------------------------------- publication

def publier(notes, racine=RACINE, dossier_publier=DOSSIER_PUBLIER, dist=None,
            sans_construire=False, envoyer=True, depot=None):
    config = lire_config()
    depot = depot or config["depot"]
    precedent = manifeste_precedent(depot, dossier_publier) or {}
    anciens = precedent.get("paquets", {})
    numero = int(precedent.get("numero", 0)) + 1
    version = lire_version(racine)
    etiquette = "v%s-n%d" % (version, numero)
    sortie = os.path.join(dossier_publier, etiquette)
    os.makedirs(sortie, exist_ok=True)
    base_url = "https://github.com/%s/releases/download/%s/" % (depot, etiquette)

    dire("SickChess %s  -  version amis n°%d" % (version, numero))
    dire("Depot : %s" % depot)
    dire()

    paquets = {}
    a_envoyer = []
    contenus = {}                    # pour le zip "premiere installation"

    # -- programme
    recette = recette_programme(racine)
    if anciens.get("programme", {}).get("empreinte") == recette:
        dire("  programme : inchange")
        paquets["programme"] = anciens["programme"]
        contenus["programme"] = None
    else:
        if dist is None:
            if sans_construire:
                raise SystemExit("Le programme a change mais --sans-construire est donne.")
            dist = construire_exe(racine)
        fichiers = fichiers_du_paquet(dist, sorted(os.listdir(dist)))
        contenus["programme"] = fichiers
        nom_zip = "programme-%s.zip" % recette[:10]
        zipper(fichiers, os.path.join(sortie, nom_zip))
        paquets["programme"] = _entree(recette, base_url + nom_zip,
                                       os.path.join(sortie, nom_zip))
        a_envoyer.append(os.path.join(sortie, nom_zip))
        dire("  programme : NOUVEAU (%s)" % _mo(paquets["programme"]["taille"]))

    # -- les autres paquets
    for nom in ORDRE[1:]:
        fichiers = fichiers_du_paquet(racine, PAQUETS[nom])
        if not fichiers:
            dire("  %s : absent, ignore" % nom)
            continue
        emp = empreinte(fichiers)
        contenus[nom] = fichiers
        if anciens.get(nom, {}).get("empreinte") == emp:
            dire("  %s : inchange" % nom)
            paquets[nom] = anciens[nom]
            continue
        nom_zip = "%s-%s.zip" % (nom, emp[:10])
        dire("  %s : NOUVEAU, compression..." % nom)
        zipper(fichiers, os.path.join(sortie, nom_zip))
        paquets[nom] = _entree(emp, base_url + nom_zip, os.path.join(sortie, nom_zip))
        a_envoyer.append(os.path.join(sortie, nom_zip))
        dire("      %s" % _mo(paquets[nom]["taille"]))

    if not a_envoyer:
        dire()
        dire("Rien n'a change depuis la version n°%d : rien a publier."
             % (numero - 1))
        shutil.rmtree(sortie, ignore_errors=True)
        return None

    manifeste = {
        "jeu": "SickChess", "format": FORMAT, "numero": numero, "version": version,
        "date": time.strftime("%Y-%m-%d"), "etiquette": etiquette,
        "notes": [n.strip() for n in re.split(r"[;|\n]", notes or "") if n.strip()],
        "paquets": paquets,
        "versions": liste_des_versions(depot, precedent, numero, etiquette),
    }
    chemin_manifeste = os.path.join(sortie, "maj.json")
    with open(chemin_manifeste, "w", encoding="utf-8") as f:
        json.dump(manifeste, f, indent=2, ensure_ascii=False)
    a_envoyer.append(chemin_manifeste)

    # -- le jeu a donner a un nouvel ami (programme + jeu)
    installation = _zip_installation(manifeste, contenus, racine, dist, sortie, depot)
    if installation:
        a_envoyer.append(installation)
    installeur = _installeur(manifeste, contenus, racine, dist, sortie, depot)
    if installeur:
        a_envoyer.append(installeur)

    dire()
    dire("Fichiers prets dans %s" % sortie)
    if envoyer and os.name == "nt":
        # 24/10 (p32) : le .exe doit demarrer chez un ami (dossier neuf) AVANT
        # d'etre envoye : sinon, rien ne part.
        import verifier_version
        dossier_exe = dossier_d_essai(contenus, racine,
                                      dist or os.path.join(DOSSIER_BUILD, "dist", "SickChess"))
        etat, phrase = verifier_version.controle_exe(dossier_exe)
        dire("  essai du .exe : %s - %s" % (etat, phrase))
        if etat == verifier_version.BLOQUANT:
            raise SystemExit("Le .exe ne demarre pas correctement : rien n'est envoye.")
    if envoyer and not _envoyer_sur_github(depot, etiquette, manifeste, a_envoyer, sortie):
        return manifeste
    # 25/10 : la copie locale (« derniere version publiee ») n'est ecrite qu'APRES
    # l'envoi. Avant, elle l'etait avant l'essai du .exe : la n° 6 bloquee par l'essai
    # passait pour publiee (« Rien n'a change depuis la version n°6 »).
    with open(os.path.join(dossier_publier, "maj.json"), "w", encoding="utf-8") as f:
        json.dump(manifeste, f, indent=2, ensure_ascii=False)
    return manifeste


def _entree(emp, url, chemin_zip):
    return {"empreinte": emp, "url": url, "sha256": _sha256_fichier(chemin_zip),
            "taille": os.path.getsize(chemin_zip)}


def _mo(octets):
    return "%.1f Mo" % (octets / 1024.0 / 1024.0)


def _zip_installation(manifeste, contenus, racine, dist, sortie, depot):
    """SickChess_amis.zip : ce qu'on envoie a un NOUVEL ami."""
    programme = contenus.get("programme")
    if programme is None:
        dossier = dist or os.path.join(DOSSIER_BUILD, "dist", "SickChess")
        if not os.path.isdir(dossier):
            dire("  (SickChess_amis.zip non refait : l'exe n'est pas dans build_amis/."
                 " La version precedente reste valable.)")
            return None
        programme = fichiers_du_paquet(dossier, sorted(os.listdir(dossier)))
    jeu = contenus.get("jeu") or []
    installe = {"source": url_manifeste(depot), "numero": manifeste["numero"],
                "version": manifeste["version"],
                "paquets": {n: manifeste["paquets"][n]["empreinte"]
                            for n in ("programme", "jeu") if n in manifeste["paquets"]}}
    chemin = os.path.join(sortie, "SickChess_amis.zip")
    with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as archive:
        for absolu, nom in programme + jeu:
            archive.write(absolu, "SickChess/" + nom)
        archive.writestr("SickChess/paquets_installes.json",
                         json.dumps(installe, indent=2, ensure_ascii=False))
    dire("  SickChess_amis.zip (nouvel ami) : %s" % _mo(os.path.getsize(chemin)))
    return chemin


def _gh_pret():
    if shutil.which("gh") is None:
        return False
    return subprocess.run(["gh", "auth", "status"], capture_output=True).returncode == 0


def _envoyer_sur_github(depot, etiquette, manifeste, fichiers, sortie):
    dire()
    if not _gh_pret():
        dire("ENVOI A LA MAIN (GitHub CLI absent ou pas connecte) :")
        dire("  1. Ouvre https://github.com/%s/releases/new" % depot)
        dire("  2. Tag : %s   -   Titre : SickChess %s (n°%d)"
             % (etiquette, manifeste["version"], manifeste["numero"]))
        dire("  3. Glisse TOUS les fichiers du dossier qui va s'ouvrir, puis Publish.")
        if sys.platform == "win32":
            os.startfile(sortie)
        return True
    if subprocess.run(["gh", "repo", "view", depot], capture_output=True).returncode != 0:
        reponse = input("Le depot %s n'existe pas. Le creer (public) ? [o/n] " % depot)
        if reponse.strip().lower() not in ("o", "oui", "y"):
            dire("Rien n'est envoye. Les fichiers restent dans %s" % sortie)
            return False
        subprocess.run(["gh", "repo", "create", depot, "--public", "--description",
                        "Versions de SickChess pour les amis (mises a jour du jeu)"],
                       check=True)
    notes = "\n".join("- " + n for n in manifeste["notes"]) or "Corrections diverses."
    dire("Envoi sur GitHub (%d fichiers)..." % len(fichiers))
    subprocess.run(["gh", "release", "create", etiquette, *fichiers, "--repo", depot,
                    "--title", "SickChess %s (n°%d)" % (manifeste["version"],
                                                         manifeste["numero"]),
                    "--notes", notes, "--latest"], check=True)
    dire()
    dire("C'est en ligne. Tes amis n'ont plus qu'a cliquer sur \"Mise a jour\".")
    dire("Lien pour un nouvel ami (installeur) : https://github.com/%s/releases/latest/"
         "download/SickChess_Installation.exe" % depot)
    dire("  (ou le zip : https://github.com/%s/releases/latest/download/SickChess_amis.zip)"
         % depot)
    return True


def installeur_seul(racine=RACINE, dossier_publier=DOSSIER_PUBLIER, envoyer=True):
    """Refait SEULEMENT l'installeur de la derniere version publiee (sans nouvelle
    version) et le remplace dans sa release GitHub. Sert quand l'installeur change
    (ex. 24/10 : installeur complet) alors que le jeu, lui, n'a pas bouge."""
    config = lire_config()
    depot = config["depot"]
    manifeste = manifeste_precedent(depot, dossier_publier)
    if not manifeste:
        raise SystemExit("Aucune version publiee : lance d'abord CONSTRUIRE_VERSION_AMIS.bat.")
    contenus = {}
    for nom in ORDRE[1:]:
        fichiers = fichiers_du_paquet(racine, PAQUETS[nom])
        if fichiers:
            if empreinte(fichiers) != manifeste["paquets"].get(nom, {}).get("empreinte"):
                raise SystemExit("Le paquet « %s » a change depuis la version n°%s : publie "
                                 "plutot une nouvelle version." % (nom, manifeste["numero"]))
            contenus[nom] = fichiers
    contenus["programme"] = None          # pris dans build_amis/dist/SickChess
    sortie = os.path.join(dossier_publier, manifeste["etiquette"])
    os.makedirs(sortie, exist_ok=True)
    dire("Installeur seul pour SickChess %s (n°%s)" % (manifeste["version"], manifeste["numero"]))
    chemin = _installeur(manifeste, contenus, racine, None, sortie, depot)
    if not chemin:
        raise SystemExit("Installeur non fabrique.")
    if envoyer and _gh_pret():
        subprocess.run(["gh", "release", "upload", manifeste["etiquette"], chemin,
                        "--clobber", "--repo", depot], check=True)
        dire("Installeur remplace en ligne : https://github.com/%s/releases/latest/download/"
             "SickChess_Installation.exe" % depot)
    elif envoyer:
        dire("GitHub CLI absent : glisse %s dans la release %s." % (chemin, manifeste["etiquette"]))
    return chemin


def main():
    parser = argparse.ArgumentParser(description="Publie une version amis de SickChess")
    parser.add_argument("--notes", default="", help="ce qui change (separe par ;)")
    parser.add_argument("--sans-envoi", action="store_true",
                        help="prepare les fichiers sans les envoyer sur GitHub")
    parser.add_argument("--installeur-seul", action="store_true",
                        help="refait seulement l'installeur de la derniere version publiee")
    args = parser.parse_args()
    if args.installeur_seul:
        installeur_seul(envoyer=not args.sans_envoi)
        return
    publier(args.notes, envoyer=not args.sans_envoi)


if __name__ == "__main__":
    main()
