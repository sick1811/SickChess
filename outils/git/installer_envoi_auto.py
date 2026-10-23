# outils/git/installer_envoi_auto.py - installe l'envoi automatique sur GitHub.
#
#     python outils/git/installer_envoi_auto.py           -> installe (ou met a jour)
#     python outils/git/installer_envoi_auto.py --retirer -> enleve
#
# Copie outils/git/post-commit dans .git/hooks/ : apres chaque commit, Git envoie
# la branche sur GitHub (voir le fichier pour le detail). A refaire apres un
# nouveau « git clone » : Git ne recopie jamais les crochets d'un depot.

import os
import shutil
import stat
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = os.path.join(RACINE, "outils", "git", "post-commit")


def dossier_des_crochets():
    sortie = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=RACINE,
                            capture_output=True, text=True, check=True).stdout.strip()
    return os.path.join(RACINE, sortie)


def main():
    cible = os.path.join(dossier_des_crochets(), "post-commit")
    if "--retirer" in sys.argv:
        if os.path.exists(cible):
            os.remove(cible)
        print("Envoi automatique retire : les commits restent sur ce PC.")
        return
    os.makedirs(os.path.dirname(cible), exist_ok=True)
    if os.path.exists(cible):
        with open(cible, encoding="utf-8", errors="replace") as f:
            if "SickChess" not in f.read():
                shutil.copy2(cible, cible + ".ancien")
                print("Un autre crochet post-commit existait : garde dans post-commit.ancien")
    # Fins de ligne Linux obligatoires (sh plante sur les \r de Windows).
    with open(SOURCE, encoding="utf-8") as f:
        texte = f.read().replace("\r\n", "\n")
    with open(cible, "w", encoding="utf-8", newline="\n") as f:
        f.write(texte)
    os.chmod(cible, os.stat(cible).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print("Envoi automatique installe : chaque commit part sur GitHub (%s)." % cible)


if __name__ == "__main__":
    main()
