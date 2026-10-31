"""La verification avant chaque version (24/10, travail p32).

    python outils/verifier_version.py --amis     avant une version amis (CONSTRUIRE_VERSION_AMIS.bat)
    python outils/verifier_version.py --steam    avant d'envoyer sur Steam (plus strict)
    python outils/verifier_version.py --itch     avant de deposer sur itch.io (31/10 : sans Steam)
    options : --sans-tests (ne relance pas tests/lancer_tous.py), --sans-banc,
              --exe DOSSIER (essaie le .exe fabrique, dans un dossier neuf)

Un seul passage, une liste claire OK / A REVOIR / BLOQUANT :
  1. tests          tests/lancer_tous.py tout vert
  2. banc d'essai   pas de section rouge (vitesse, processeur, memoire, conflits, precision)
  3. mode test      MODE_TEST de jeu/salon_en_ligne.py : permis pour les amis, coupe pour Steam et itch
  4. numero Steam   steam_appid.txt : 480 (test de Valve) pour les amis ; pour Steam, le vrai numero
                    (APPID_STEAM_REEL de jeu/distribution.py) ; itch : aucun
  4b. paquet itch   (--itch) aucun fichier Steam dans le zip, distribution.json = itch
  5. licences       fichiers de licence presents ; docs/CREDITS.md sans ligne « a verifier » (Steam)
  6. version        VERSION de SickChess.py jamais plus petite que la derniere version publiee
  7. Git            tout est enregistre (rien d'oublie dans la version)
  8. .exe           (--exe) demarre depuis un dossier neuf, sans erreur, pendant 25 s
Code de sortie : 0 s'il n'y a rien de BLOQUANT, 1 sinon. CONSTRUIRE_VERSION_AMIS.bat
s'arrete alors avant de fabriquer quoi que ce soit.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPID_DE_TEST = "480"
VENDUES = ("steam", "itch")            # versions vendues : controles stricts
FICHIERS_STEAM = ("steam_api64.dll", "steam_api.dll", "steam_appid.txt")
OK, A_REVOIR, BLOQUANT = "OK", "A REVOIR", "BLOQUANT"
LICENCES = ["moteur/COPYING-Stockfish.txt", "polices/BarlowSemiCondensed-OFL.txt",
            "polices/JetBrainsMono-OFL.txt", "polices/Outfit-OFL.txt", "docs/CREDITS.md",
            "LICENSE", "LICENCE.md", "licenses/LISEZ-MOI.txt"]
SECTIONS_DU_BANC = "vitesse,processeur,memoire,conflits,precision"


def _lire(racine, chemin):
    try:
        with open(os.path.join(racine, chemin), "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


# ------------------------------------------------------------------ les controles
# Chacun renvoie (etat, phrase pour Julien).

def controle_mode_test(racine, cible):
    texte = _lire(racine, os.path.join("jeu", "salon_en_ligne.py")) or ""
    m = re.search(r"^MODE_TEST\s*=\s*(True|False)", texte, re.M)
    if not m:
        return BLOQUANT, "MODE_TEST introuvable dans jeu/salon_en_ligne.py."
    actif = m.group(1) == "True"
    if cible in VENDUES and actif:
        return BLOQUANT, ("MODE_TEST = True : les boutons de test du jeu en ligne seraient visibles "
                          "des joueurs. Le passer à False dans jeu/salon_en_ligne.py.")
    if actif:
        return OK, "MODE_TEST = True (permis pour les amis : boutons de test visibles)."
    return OK, "MODE_TEST = False."


def appid_steam_reel(racine):
    """APPID_STEAM_REEL de jeu/distribution.py : le numero (texte), "" s'il vaut
    None, ou None si la ligne est introuvable."""
    texte = _lire(racine, os.path.join("jeu", "distribution.py")) or ""
    m = re.search(r"^APPID_STEAM_REEL\s*=\s*([^#\n]+)", texte, re.M)
    if not m:
        return None
    valeur = m.group(1).strip()
    return "" if valeur == "None" else valeur


def controle_numero_steam(racine, cible):
    texte = _lire(racine, "steam_appid.txt")
    numero = (texte or "").strip()
    if cible == "itch":
        return OK, "Version itch : aucun numéro Steam (Steam n'est jamais démarré)."
    if cible == "steam":
        reel = appid_steam_reel(racine)
        if reel is None:
            return BLOQUANT, "APPID_STEAM_REEL introuvable dans jeu/distribution.py."
        if not reel:
            return BLOQUANT, ("APPID_STEAM_REEL = None dans jeu/distribution.py : y mettre le vrai "
                              "numéro de SickChess (compte Steamworks).")
        if reel == APPID_DE_TEST or not reel.isdigit():
            return BLOQUANT, ("APPID_STEAM_REEL = %s dans jeu/distribution.py : il faut le vrai "
                              "numéro de SickChess, pas 480." % reel[:30])
        if numero and numero.isdigit() and numero not in (reel, APPID_DE_TEST):
            return BLOQUANT, ("steam_appid.txt (%s) et APPID_STEAM_REEL (%s) ne disent pas le même "
                              "numéro." % (numero, reel))
        if numero == APPID_DE_TEST:
            return BLOQUANT, ("steam_appid.txt contient 480 (le numéro de test de Valve) : mettre le "
                              "vrai numéro de SickChess (compte Steamworks).")
        if numero and not numero.isdigit():
            return BLOQUANT, "steam_appid.txt ne contient pas un numéro : « %s »." % numero[:30]
        return OK, ("Numéro Steam %s. Rappel : le paquet envoyé à Steam ne doit PAS contenir "
                    "steam_appid.txt (Steam lance le jeu avec son numéro)." % reel)
    if not numero:
        return A_REVOIR, ("steam_appid.txt absent : le jeu en ligne ne marchera pas chez les amis "
                          "(il doit contenir 480 pour l'instant).")
    if numero != APPID_DE_TEST:
        return A_REVOIR, "steam_appid.txt contient %s (et pas 480) : c'est voulu ?" % numero
    return OK, "steam_appid.txt = 480 (numéro de test, normal pour les amis)."


def _publier_maj():
    dossier = os.path.join(RACINE, "outils")
    if dossier not in sys.path:
        sys.path.insert(0, dossier)
    import publier_maj
    return publier_maj


def fichiers_steam_dans(noms):
    return sorted(n for n in noms
                  if os.path.basename(n.replace("\\", "/")).lower() in FICHIERS_STEAM)


def controle_paquet_itch(racine, cible, zip_itch=None):
    """31/10 : la version itch.io ne contient AUCUN fichier Steam, et son
    distribution.json dit « itch » (sinon le jeu essaierait Steam)."""
    if cible != "itch":
        return OK, "(pas une version itch)"
    publier_maj = _publier_maj()
    trouves = fichiers_steam_dans(n for _a, n in publier_maj.fichiers_itch(racine))
    if trouves:
        return BLOQUANT, "Fichiers Steam prévus dans la version itch : %s." % ", ".join(trouves)
    if zip_itch is None:
        zip_itch = os.path.join(racine, "publier", "itch",
                                publier_maj.nom_zip_itch(publier_maj.lire_version(racine)))
        if not os.path.exists(zip_itch):
            return OK, "Aucun fichier Steam prévu (le zip itch sera contrôlé à sa fabrication)."
    nom = os.path.basename(zip_itch)
    try:
        with zipfile.ZipFile(zip_itch) as archive:
            noms = archive.namelist()
            choix = None
            if "SickChess/distribution.json" in noms:
                try:
                    choix = json.loads(archive.read("SickChess/distribution.json")
                                       .decode("utf-8")).get("distribution")
                except (ValueError, AttributeError):
                    choix = None
    except (OSError, zipfile.BadZipFile) as souci:
        return BLOQUANT, "Zip itch illisible (%s) : %s" % (nom, souci)
    trouves = fichiers_steam_dans(noms)
    if trouves:
        return BLOQUANT, "Fichiers Steam dans %s : %s." % (nom, ", ".join(trouves))
    if choix != "itch":
        return BLOQUANT, ("%s : distribution.json absent ou faux (%s) : le jeu essaierait Steam."
                          % (nom, choix))
    if not any(n.lower().endswith("sickchess.exe") for n in noms):
        return BLOQUANT, "%s : SickChess.exe absent." % nom
    return OK, "%s : aucun fichier Steam, distribution = itch." % nom


def controle_licences(racine, cible):
    manquants = [c for c in LICENCES if not os.path.exists(os.path.join(racine, c))]
    if manquants:
        return BLOQUANT, "Fichiers de licence absents : %s." % ", ".join(manquants)
    credits = _lire(racine, os.path.join("docs", "CREDITS.md")) or ""
    a_verifier = [ligne.split("|")[1].strip() for ligne in credits.splitlines()
                  if ligne.startswith("|") and re.search(r"à vérifier|à confirmer", ligne, re.I)]
    if a_verifier:
        phrase = "Licences encore « à vérifier » dans docs/CREDITS.md : %s." % ", ".join(a_verifier)
        return (BLOQUANT if cible in VENDUES else A_REVOIR), phrase
    return OK, "Licences présentes, docs/CREDITS.md sans ligne à vérifier."


def _version_en_nombres(texte):
    return tuple(int(n) for n in re.findall(r"\d+", texte or "")[:3]) or (0,)


def controle_version(racine, cible, version_publiee=None):
    texte = _lire(racine, "SickChess.py") or ""
    m = re.search(r'^VERSION\s*=\s*"([^"]+)"', texte, re.M)
    if not m:
        return BLOQUANT, "VERSION introuvable dans SickChess.py."
    version = m.group(1)
    if version_publiee is None:
        return OK, "Version %s (dernière version publiée inconnue : pas d'Internet ?)." % version
    if _version_en_nombres(version) < _version_en_nombres(version_publiee):
        return BLOQUANT, ("VERSION %s est plus petite que la version déjà publiée (%s) : les amis ne "
                          "recevraient pas la mise à jour." % (version, version_publiee))
    if cible == "steam" and _version_en_nombres(version) == _version_en_nombres(version_publiee):
        return A_REVOIR, ("VERSION %s = celle de la dernière version amis : pour Steam, l'augmenter "
                          "dans SickChess.py." % version)
    return OK, "Version %s (dernière publiée : %s ; le n° amis augmente tout seul)." % (
        version, version_publiee)


def controle_git(racine, cible):
    try:
        p = subprocess.run(["git", "status", "--porcelain"], cwd=racine, capture_output=True,
                           text=True, timeout=30, env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    except (OSError, subprocess.TimeoutExpired):
        return A_REVOIR, "Git indisponible : impossible de vérifier que tout est enregistré."
    perso = ("profil.json", "parties/", "puzzles_score.json", "config.json", "journal_du_jeu.txt",
             "succes.json", "plantage.json", "rapports/")
    lignes = [l for l in p.stdout.splitlines() if l.strip() and not any(x in l for x in perso)]
    if lignes:
        return A_REVOIR, ("%d fichier(s) modifié(s) pas encore enregistré(s) dans Git (ex. %s) : la "
                          "version les contiendra, mais GitHub ne les a pas." % (
                              len(lignes), lignes[0][3:].strip()))
    return OK, "Tout est enregistré dans Git."


def controle_tests(racine, lancer=None):
    lancer = lancer or (lambda cmd: subprocess.run(cmd, cwd=racine, capture_output=True, text=True,
                                                   encoding="utf-8", errors="replace", timeout=3600))
    p = lancer([sys.executable, os.path.join(racine, "tests", "lancer_tous.py")])
    sortie = p.stdout or ""
    fin = sortie.strip().splitlines()[-1:] or [""]
    # 25/10 : tout le compte rendu des tests est garde (tests/verification_tests.txt) et
    # les controles en ECHEC sont montres : avant, on ne voyait que le nom de la serie.
    try:
        with open(os.path.join(racine, "tests", "verification_tests.txt"), "w",
                  encoding="utf-8") as f:
            f.write(sortie)
    except OSError:
        pass
    if p.returncode == 0:
        return OK, "Tests : %s" % fin[0]
    rouges = [l.split()[0] for l in sortie.splitlines() if " ROUGE " in l]
    details = [l.strip() for l in sortie.splitlines() if l.startswith("    ") and "ECHEC" in l][:10]
    return BLOQUANT, "Tests en rouge : %s (%s).%s" % (
        ", ".join(rouges) or "?", fin[0],
        "".join("\n                          " + d for d in details)
        + "\n                          (tout le detail : tests/verification_tests.txt)")


def controle_banc(racine, lancer=None):
    lancer = lancer or (lambda cmd: subprocess.run(cmd, cwd=racine, capture_output=True, text=True,
                                                   encoding="utf-8", errors="replace", timeout=3600))
    lancer([sys.executable, os.path.join(racine, "outils", "banc_essai.py"), "--sections",
            SECTIONS_DU_BANC])
    try:
        with open(os.path.join(racine, "tests", "banc_essai.json"), encoding="utf-8") as f:
            sections = json.load(f).get("sections", {})
    except (OSError, ValueError):
        return A_REVOIR, "Banc d'essai : pas de résultat (tests/banc_essai.json)."
    rouges = [nom for nom in SECTIONS_DU_BANC.split(",") if sections.get(nom, {}).get("statut") == "rouge"]
    oranges = [nom for nom in SECTIONS_DU_BANC.split(",") if sections.get(nom, {}).get("statut") == "orange"]
    if rouges:
        return BLOQUANT, "Banc d'essai rouge : %s (voir docs/BANC_ESSAI.md)." % ", ".join(rouges)
    if oranges:
        return A_REVOIR, "Banc d'essai orange : %s (voir docs/BANC_ESSAI.md)." % ", ".join(oranges)
    return OK, "Banc d'essai vert (%s)." % SECTIONS_DU_BANC.replace(",", ", ")


def controle_exe(dossier_exe, secondes=25, lancer=None):
    """Copie le jeu fabrique dans un dossier NEUF (comme chez un ami), le lance, et
    regarde son journal : il doit tourner 25 s sans erreur."""
    exe = os.path.join(dossier_exe or "", "SickChess.exe")
    if not dossier_exe or not os.path.exists(exe):
        return BLOQUANT, "Pas de SickChess.exe dans %s." % dossier_exe
    neuf = tempfile.mkdtemp(prefix="sickchess_essai_")
    copie = os.path.join(neuf, "SickChess")
    shutil.copytree(dossier_exe, copie)
    try:
        if lancer is not None:
            vivant, journal = lancer(copie, secondes)
        else:
            p = subprocess.Popen([os.path.join(copie, "SickChess.exe")], cwd=copie)
            time.sleep(secondes)
            vivant = p.poll() is None
            if vivant:
                p.terminate()
                try:
                    p.wait(10)
                except subprocess.TimeoutExpired:
                    p.kill()
            journal = _lire(copie, "journal_du_jeu.txt") or ""
        if "Traceback" in journal or "[SICKCHESS] Erreur" in journal:
            ligne = next((l for l in journal.splitlines() if "Error" in l or "Erreur" in l), "")
            return BLOQUANT, "Le .exe a une erreur au démarrage : %s" % ligne[:160]
        if not vivant:
            return BLOQUANT, "Le .exe s'est fermé tout seul avant %d s." % secondes
        if "[SICKCHESS] Demarrage" not in journal:
            return A_REVOIR, "Le .exe tourne, mais son journal ne dit pas « Demarrage »."
        return OK, "Le .exe démarre depuis un dossier neuf et tourne %d s sans erreur." % secondes
    finally:
        shutil.rmtree(neuf, ignore_errors=True)


# ------------------------------------------------------------------ ensemble

def derniere_version_publiee():
    try:
        sys.path.insert(0, os.path.join(RACINE, "outils"))
        import publier_maj
        precedent = publier_maj.manifeste_precedent(publier_maj.lire_config()["depot"],
                                                    publier_maj.DOSSIER_PUBLIER)
        return (precedent or {}).get("version")
    except Exception:
        return None


def verifier(cible="amis", racine=RACINE, tests=True, banc=True, exe=None, version_publiee=None,
             afficher=True, zip_itch=None):
    controles = []

    def ajouter(nom, resultat):
        controles.append((nom,) + resultat)
        if afficher:
            print("  %-9s %-13s %s" % (resultat[0], nom, resultat[1]), flush=True)

    ajouter("mode test", controle_mode_test(racine, cible))
    ajouter("numéro Steam", controle_numero_steam(racine, cible))
    if cible == "itch":
        ajouter("paquet itch", controle_paquet_itch(racine, cible, zip_itch))
    ajouter("licences", controle_licences(racine, cible))
    ajouter("version", controle_version(racine, cible, version_publiee))
    ajouter("Git", controle_git(racine, cible))
    if tests:
        if afficher:
            print("  ...       tests         (quelques minutes)", flush=True)
        ajouter("tests", controle_tests(racine))
    if banc:
        if afficher:
            print("  ...       banc d'essai  (quelques minutes)", flush=True)
        ajouter("banc d'essai", controle_banc(racine))
    if exe:
        ajouter(".exe", controle_exe(exe))
    return controles


def main():
    cible = "steam" if "--steam" in sys.argv else "itch" if "--itch" in sys.argv else "amis"
    exe = sys.argv[sys.argv.index("--exe") + 1] if "--exe" in sys.argv else None
    zip_itch = sys.argv[sys.argv.index("--paquet") + 1] if "--paquet" in sys.argv else None
    print()
    print("  Vérification avant une version %s" % {"steam": "STEAM", "itch": "ITCH.IO (sans Steam)"}
          .get(cible, "pour les amis"))
    print("  " + "-" * 60)
    controles = verifier(cible, tests="--sans-tests" not in sys.argv, banc="--sans-banc" not in sys.argv,
                         exe=exe, version_publiee=derniere_version_publiee(), zip_itch=zip_itch)
    bloquants = [c for c in controles if c[1] == BLOQUANT]
    a_revoir = [c for c in controles if c[1] == A_REVOIR]
    print("  " + "-" * 60)
    if bloquants:
        print("  BLOQUANT : %d point(s) à corriger avant de publier." % len(bloquants))
    elif a_revoir:
        print("  Rien de bloquant ; %d point(s) à revoir (on peut publier)." % len(a_revoir))
    else:
        print("  Tout est bon : on peut publier.")
    print()
    return 1 if bloquants else 0


if __name__ == "__main__":
    sys.exit(main())
