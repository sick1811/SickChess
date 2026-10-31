# asset_manager.py - ou trouver les ressources et ou ecrire les donnees
#
# Les fichiers sont cherches a cote du script aussi bien que dans le dossier
# courant : indispensable une fois le jeu compile en .exe.
#
# 31/10 (menage) : la classe AssetManager (fond anime et musique du menu V6)
# n'etait plus creee nulle part : retiree. Restent les chemins (ressources,
# donnees, dossier d'ecriture).

import os
import sys



def dossier_ressources():
    """Dossier des assets, y compris quand le jeu est compile avec PyInstaller."""
    base = getattr(sys, "_MEIPASS", None)
    if base and os.path.isdir(os.path.join(base, "assets")):
        return base
    for candidat in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        if os.path.isdir(os.path.join(candidat, "assets")):
            return candidat
    return os.getcwd()


def chemin_ressource(*morceaux):
    return os.path.join(dossier_ressources(), *morceaux)


def dossier_de_donnees(nom):
    """Ou trouver un dossier de DONNEES LIVREES : ouvertures/, puzzles/, syzygy/.

    V8 (04/09) - LE BUG QUE JULIEN A SENTI EN DEMANDANT "ya pas les ouvertures ?"
    Ces trois dossiers etaient cherches avec dossier_ecriture(), c'est-a-dire A
    COTE de l'executable. Or PyInstaller range tout ce qu'il embarque dans le
    sous-dossier _internal. En lancant le jeu depuis les sources, tout marchait ;
    UNE FOIS COMPILE, les 3 810 ouvertures et les 4 180 151 problemes etaient
    introuvables - et le jeu ne disait rien, il retombait sur ses 103 ouvertures
    ecrites a la main et eteignait le mode PROBLEMES tout seul. Le genre de bug
    qu'on ne decouvre que chez celui a qui on a donne le jeu.

    On regarde donc dans l'ordre : le paquet compile (_MEIPASS), le dossier de
    l'executable, le dossier courant, celui du code. Le premier qui existe gagne.
    Si aucun n'existe, on renvoie le chemin "a cote de l'executable" : c'est la
    qu'on ira le deposer a la main.
    """
    candidats = [getattr(sys, "_MEIPASS", None)]
    if getattr(sys, "frozen", False):
        candidats.append(os.path.dirname(os.path.abspath(sys.executable)))
    candidats.append(os.getcwd())
    candidats.append(os.path.dirname(os.path.abspath(__file__)))
    for base in candidats:
        if not base:
            continue
        chemin = os.path.join(base, nom)
        if os.path.isdir(chemin):
            return chemin
    return os.path.join(dossier_ecriture(), nom)


def dossier_ecriture():
    """Dossier ou le jeu a le droit d'ecrire : config.json, parties/, logs.

    Une fois compile en .exe, les fichiers embarques sont dans un sous-dossier
    interne que Windows peut protéger. Tout ce qui doit etre modifiable vit
    donc a cote de l'executable.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    # SickChess : le code vit dans jeu/, les fichiers modifiables (config.json,
    # parties/, profil) vivent a la racine du projet, a cote de SickChess.py.
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def preparer_dossier_utilisateur():
    """Au premier lancement de l'exe, sort les fichiers modifiables a cote.

    Sans cela, l'ecran de reglages ne pourrait pas enregistrer les choix de
    l'utilisateur (case "retenir ces reglages").
    """
    if not getattr(sys, "frozen", False):
        return
    import shutil
    cible = dossier_ecriture()
    for nom in ("config.json", "REGLAGES.txt"):
        source = chemin_ressource(nom)
        destination = os.path.join(cible, nom)
        if os.path.exists(source) and not os.path.exists(destination):
            try:
                shutil.copyfile(source, destination)
                print("[ASSETS] %s copie a cote de l'executable" % nom)
            except OSError as e:
                print("[ASSETS] copie de %s impossible : %s" % (nom, e))
