# plantage.py - SickChess 24/10 (travail p29) : le rapport de plantage.
#
# Si le jeu plante chez un joueur, journal_du_jeu.txt est remis a zero au
# lancement suivant : l'erreur serait perdue. Ici :
#   1. AU PLANTAGE (SickChess.py) : noter() range l'erreur, son detail technique
#      et la fin du journal dans plantage.json, a cote du jeu ;
#   2. AU LANCEMENT SUIVANT (game_manager) : une carte propose de l'envoyer avec
#      « Signaler un probleme » (ecran deja rempli, journal DU PLANTAGE) ;
#      « Non merci » l'efface ; Echap = plus tard (proposee 3 fois au plus).
# Rien n'est jamais envoye sans que le joueur clique.

import datetime
import json
import os
import platform
import traceback

FICHIER = "plantage.json"
PROPOSITIONS_MAX = 3
LIGNES_DU_JOURNAL = 150


def _chemin():
    try:
        from asset_manager import dossier_ecriture
        return os.path.join(dossier_ecriture(), FICHIER)
    except Exception:
        return os.path.join(os.getcwd(), FICHIER)


def noter(erreur=None, version="", maintenant=None):
    """A appeler dans le « except » qui rattrape le plantage. Ne plante jamais."""
    try:
        maintenant = maintenant or datetime.datetime.now()
        if erreur is None:
            trace = traceback.format_exc()
            resume = trace.strip().splitlines()[-1] if trace.strip() else "Erreur inconnue"
        else:
            trace = "".join(traceback.format_exception(type(erreur), erreur, erreur.__traceback__))
            resume = "%s: %s" % (type(erreur).__name__, erreur)
        try:
            import signalement
            journal = signalement.fin_du_journal(LIGNES_DU_JOURNAL)
        except Exception:
            journal = "(pas de journal)"
        donnees = {"date": maintenant.strftime("%d/%m/%Y %H:%M"), "version": version or "?",
                   "systeme": "%s %s, Python %s" % (platform.system(), platform.release(),
                                                   platform.python_version()),
                   "erreur": resume[:300], "trace": trace[-6000:], "journal": journal,
                   "propose": 0}
        with open(_chemin(), "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, indent=1)
        print("[PLANTAGE] rapport garde pour le prochain lancement : %s" % resume[:120])
        return donnees
    except Exception as e:
        print("[PLANTAGE] rapport non garde : %s" % e)
        return None


def en_attente():
    """Le plantage a proposer (dict), ou None."""
    try:
        with open(_chemin(), "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) and d.get("erreur") else None
    except (OSError, ValueError):
        return None


def propose_une_fois_de_plus():
    """« Plus tard » : on le reproposera, 3 fois au plus, puis on l'oublie."""
    d = en_attente()
    if d is None:
        return
    d["propose"] = int(d.get("propose", 0)) + 1
    if d["propose"] >= PROPOSITIONS_MAX:
        oublier()
        return
    try:
        with open(_chemin(), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    except OSError:
        pass


def oublier():
    try:
        os.remove(_chemin())
    except OSError:
        pass


def message(d):
    """La phrase mise dans « Signaler » (le joueur peut la completer)."""
    return "Le jeu s'est fermé tout seul le %s (version %s). Erreur : %s\n" \
           "Ce que je faisais à ce moment-là : " % (d.get("date"), d.get("version"), d.get("erreur"))


def journal(d):
    """Ce qui part avec le rapport : le detail de l'erreur, puis la fin du journal
    du lancement qui a plante (pas celui d'aujourd'hui)."""
    return "--- Erreur (detail technique) ---\n%s\n--- Journal du lancement qui a plante ---\n%s" % (
        d.get("trace", ""), d.get("journal", ""))
