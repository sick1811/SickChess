# pare_feu.py - SickChess : autoriser le jeu dans le pare-feu de Windows.
#
# 25/10 (demande de Julien) : le jeu doit pouvoir aller sur Internet pour ses
# mises a jour et pour jouer en ligne par Steam, sur un reseau PRIVE comme
# PUBLIC (Wi-Fi d'un cafe, d'une ecole...), sans que le joueur ait rien a regler.
#
# CE QUE FAIT LE JEU, la premiere fois (et apres un changement de dossier) :
#   - il regarde si la regle « SickChess » existe deja (sans droits speciaux) ;
#   - sinon, Windows affiche UNE fois sa fenetre « Voulez-vous autoriser cette
#     application a apporter des modifications ? » : c'est la regle de Windows,
#     personne ne peut modifier le pare-feu sans cet accord ;
#   - avec l'accord : les anciennes regles de SickChess.exe sont retirees (dont
#     les regles de BLOCAGE que Windows cree quand on a clique « Annuler » sur
#     son message du pare-feu), puis deux regles « Autoriser » (entree et sortie)
#     sont ajoutees pour SickChess.exe, sur tous les reseaux (prive, public,
#     domaine). Rien d'autre n'est touche : ni l'antivirus, ni les autres programmes.
#   - refuse : le jeu marche quand meme (Windows laisse sortir les programmes par
#     defaut) ; il redemandera a la prochaine version, pas a chaque lancement.
# L'installeur (outils/installeur_amis.iss) fait la meme chose a l'installation.
# Pour les essais automatiques : SICKCHESS_SANS_PARE_FEU=1 ne demande rien.

import json
import os
import subprocess
import sys

NOM_REGLE = "SickChess"
FICHIER_ETAT = "pare_feu.json"


def _netsh(*args):
    return ["netsh", "advfirewall", "firewall"] + list(args)


def commandes(exe):
    """Les commandes netsh (dans l'ordre) qui autorisent exe sur tous les reseaux."""
    desc = "description=SickChess : mises a jour et parties en ligne (Steam)"
    return [
        _netsh("delete", "rule", "name=%s" % NOM_REGLE),
        _netsh("delete", "rule", "name=all", "program=%s" % exe),
        _netsh("add", "rule", "name=%s" % NOM_REGLE, "dir=in", "action=allow",
               "program=%s" % exe, "enable=yes", "profile=any", desc),
        _netsh("add", "rule", "name=%s" % NOM_REGLE, "dir=out", "action=allow",
               "program=%s" % exe, "enable=yes", "profile=any", desc),
    ]


def ligne_de_commande(exe):
    """Les commandes reunies en une ligne pour cmd /c (une seule demande Windows)."""
    return " & ".join(" ".join(_citer(a) for a in cmd) for cmd in commandes(exe))


def _citer(argument):
    """name=SickChess -> name="SickChess" ; les espaces du chemin sont proteges."""
    if "=" in argument:
        cle, valeur = argument.split("=", 1)
        if any(c in valeur for c in ' &()^,;'):
            return '%s="%s"' % (cle, valeur)
    return argument


def regle_presente(exe, lancer=subprocess.run):
    """Vrai si les regles « SickChess » (entree ET sortie) existent pour exe."""
    for sens in ("in", "out"):
        try:
            r = lancer(_netsh("show", "rule", "name=%s" % NOM_REGLE, "dir=%s" % sens,
                              "verbose"), capture_output=True, timeout=20,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except (OSError, subprocess.SubprocessError):
            return False
        if r.returncode != 0:
            return False
        texte = (r.stdout or b"")
        if isinstance(texte, bytes):
            texte = texte.decode("oem" if os.name == "nt" else "utf-8", errors="replace")
        if os.path.normcase(exe).lower() not in texte.lower():
            return False
    return True


def demander_autorisation(exe):
    """Fenetre Windows « autoriser les modifications », puis les regles.
    Renvoie True si la demande est partie (pas forcement acceptee)."""
    import ctypes
    code = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe",
                                               "/c " + ligne_de_commande(exe), None, 0)
    return int(code) > 32


def _lire_etat(dossier):
    try:
        with open(os.path.join(dossier, FICHIER_ETAT), "r", encoding="utf-8") as f:
            etat = json.load(f)
        return etat if isinstance(etat, dict) else {}
    except (OSError, ValueError):
        return {}


def _ecrire_etat(dossier, etat):
    try:
        with open(os.path.join(dossier, FICHIER_ETAT), "w", encoding="utf-8") as f:
            json.dump(etat, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def decider(exe, presente, etat, numero):
    """Que faire au demarrage : "ok" (deja autorise), "demander", ou "attendre"
    (deja demande pour cette version et ce dossier : on ne harcele pas)."""
    if presente:
        return "ok"
    if etat.get("exe") == exe and etat.get("numero") == numero and etat.get("demande"):
        return "attendre"
    return "demander"


def au_demarrage(dossier=None, exe=None, numero=None):
    """Appele par SickChess.py avant d'ouvrir la fenetre. Ne plante jamais."""
    try:
        if sys.platform != "win32" or not getattr(sys, "frozen", False):
            return "hors_exe"
        if os.environ.get("SICKCHESS_SANS_PARE_FEU"):
            return "desactive"
        import distribution
        if not distribution.steam_permis():
            # 31/10 : version itch.io : ni Steam ni mise a jour automatique, donc
            # pas de regle de pare-feu (et pas de demande de droits a l'acheteur).
            return "itch"
        exe = os.path.abspath(exe or sys.executable)
        dossier = dossier or os.path.dirname(exe)
        if numero is None:
            try:
                import mise_a_jour
                numero = (mise_a_jour.lire_installe(dossier) or {}).get("numero")
            except Exception:
                numero = None
        etat = _lire_etat(dossier)
        action = decider(exe, regle_presente(exe), etat, numero)
        if action == "demander":
            partie = demander_autorisation(exe)
            _ecrire_etat(dossier, {"exe": exe, "numero": numero, "demande": True,
                                   "lancee": partie})
        print("[PARE-FEU] %s (%s)" % (action, exe))
        return action
    except Exception as souci:
        print("[PARE-FEU] verification impossible : %s" % souci)
        return "erreur"
