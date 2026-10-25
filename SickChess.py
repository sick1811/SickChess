# SickChess.py - le lanceur du jeu.
#
# Le code du jeu vit dans le dossier jeu/ ; les ressources (sons, polices,
# ouvertures, moteur) et les fichiers modifiables (config.json, parties/) vivent
# ici, a la racine. Ce fichier cale le dossier de travail sur la racine, rend
# jeu/ importable, puis lance la boucle principale.

import os
import sys
import traceback

VERSION = "0.3.0"

# 17/10 (recette R-002) : en plein ecran, SDL reduisait la fenetre des qu'une
# autre fenetre prenait la main (notification, Alt+Tab rate...), et le jeu
# revenait tout noir. On garde la fenetre affichee.
os.environ.setdefault("SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS", "0")

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


class _Journal:
    """Recopie tout ce que le jeu affiche dans journal_du_jeu.txt (a la racine).

    Le fichier est remis a zero a chaque lancement. Apres un test, Claude peut
    le lire pour voir les erreurs, meme si la console s'est refermee.
    """

    def __init__(self, flux, fichier):
        self.flux = flux
        self.fichier = fichier

    def write(self, texte):
        try:
            self.fichier.write(texte)
            self.fichier.flush()
        except Exception:
            pass
        try:
            return self.flux.write(texte)
        except Exception:
            return len(texte)

    def flush(self):
        try:
            self.flux.flush()
        except Exception:
            pass

    def isatty(self):
        return False


try:
    _fichier_journal = open(os.path.join(RACINE, "journal_du_jeu.txt"), "w",
                            encoding="utf-8", errors="replace")
    sys.stdout = _Journal(sys.stdout, _fichier_journal)
    sys.stderr = _Journal(sys.stderr, _fichier_journal)
except OSError:
    pass

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
    try:
        # 25/10 : le jeu s'autorise dans le pare-feu de Windows (Internet et Steam,
        # reseau prive ET public), une fois, avec l'accord de Windows. Voir pare_feu.py.
        import pare_feu
        pare_feu.au_demarrage()
    except Exception:
        pass
    manager = None
    try:
        from game_manager import GameManager
        manager = GameManager(VERSION)
        if "--plantage-test" in sys.argv:
            # 24/10 (p29, recette R-124) : un plantage volontaire, pour essayer le
            # rapport de plantage. Relancer ensuite le jeu normalement.
            raise RuntimeError("Plantage de test (--plantage-test)")
        manager.run()
    except SystemExit:
        pass
    except Exception as e:
        print("[SICKCHESS] Erreur : %s" % e)
        traceback.print_exc()
        # 24/10 (p29) : l'erreur et la fin du journal sont gardees ; le jeu
        # proposera de les envoyer au prochain lancement (jeu/plantage.py).
        try:
            import plantage
            plantage.noter(e, VERSION)
        except Exception:
            pass
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
