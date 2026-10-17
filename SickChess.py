# SickChess.py - le lanceur du jeu.
#
# Le code du jeu vit dans le dossier jeu/ ; les ressources (sons, polices,
# ouvertures, moteur) et les fichiers modifiables (config.json, parties/) vivent
# ici, a la racine. Ce fichier cale le dossier de travail sur la racine, rend
# jeu/ importable, puis lance la boucle principale.

import os
import sys
import traceback

VERSION = "0.1.0"

if sys.stdout is None:          # lance sans console (pythonw ou .exe fenetre)
    class _Poubelle:
        def write(self, _t): return 0
        def flush(self): pass
        def isatty(self): return False
    sys.stdout = _Poubelle()
    sys.stderr = _Poubelle()
else:
    # Une console Windows en cp1252 plantait sur un caractere qu'elle ne sait
    # pas afficher (V8 retirait donc tous les accents du jeu). On lui demande
    # de remplacer ce caractere par "?" au lieu de s'arreter.
    for _flux in (sys.stdout, sys.stderr):
        try:
            _flux.reconfigure(errors="replace")
        except Exception:
            pass

if getattr(sys, "frozen", False):
    RACINE = os.path.dirname(os.path.abspath(sys.executable))
else:
    RACINE = os.path.dirname(os.path.abspath(__file__))
os.chdir(RACINE)
DOSSIER_CODE = os.path.join(RACINE, "jeu")
for chemin in (DOSSIER_CODE, getattr(sys, "_MEIPASS", None)):
    if chemin and chemin not in sys.path:
        sys.path.insert(0, chemin)


def main():
    print("[SICKCHESS] Demarrage de SickChess %s" % VERSION)
    try:
        from asset_manager import preparer_dossier_utilisateur
        preparer_dossier_utilisateur()
    except Exception:
        pass
    manager = None
    try:
        from game_manager import GameManager
        manager = GameManager(VERSION)
        manager.run()
    except SystemExit:
        pass
    except Exception as e:
        print("[SICKCHESS] Erreur : %s" % e)
        traceback.print_exc()
        return 1
    finally:
        if manager is not None:
            try:
                manager.cleanup()
            except Exception:
                pass
    print("[SICKCHESS] Fin normale")
    return 0


if __name__ == "__main__":
    sys.exit(main())
