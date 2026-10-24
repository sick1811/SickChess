# petit_pc.py - SickChess 24/10 (travail p31) : le mode « petit PC ».
#
# Les acheteurs Steam n'ont pas tous l'i7 de Julien. Au lancement, le jeu regarde
# le processeur et la memoire ; un PC modeste (4 coeurs ou moins, ou 8 Go ou moins)
# passe tout seul en « petit PC » :
#   - analyse : un seul Stockfish (au lieu de 2 ou 3), 1 Go de memoire au plus
#     (au lieu de 4), un seul coeur pendant la partie (l'adversaire reste fluide),
#     puissance « Rapide » par defaut (si le joueur n'a rien choisi) ;
#   - affichage : effets plus legers (moins de confettis), 24 images/s au repos.
# Options -> Affichage -> « Puissance du PC » : Automatique (par defaut), Petit PC
# ou PC normal. Le reglage est lu une fois (apparence.reglage) : jamais de disque
# pendant le dessin.

import os

COEURS_PETIT = 4              # 4 coeurs logiques ou moins
MEMOIRE_PETIT_MO = 8600       # « 8 Go » : Windows en annonce souvent 7,8 a 8,1
HACHAGE_PETIT_MO = 1024
IMAGES_AU_REPOS_PETIT = 24
CONFETTIS_PETIT = 30          # au lieu de 90

_DETECTE = {}
_FORCE = [None]               # tests : forcer("normal") rend le resultat independant du PC


def forcer(choix):
    """Pour les tests : 'petit', 'normal' ou None (retour a la normale)."""
    _FORCE[0] = choix


def materiel(coeurs=None, memoire_mo=None):
    """(coeurs logiques, memoire en Mo) de ce PC ; memoire None si illisible."""
    if coeurs is None:
        coeurs = os.cpu_count() or 2
    if memoire_mo is None:
        try:
            import analyse_partie
            memoire_mo = analyse_partie.memoire_totale_mo()
        except Exception:
            memoire_mo = None
    return int(coeurs), memoire_mo


def detecter(coeurs=None, memoire_mo=None):
    """'petit' ou 'normal', d'apres le materiel (garde apres le premier appel)."""
    cle = (coeurs, memoire_mo)
    if cle not in _DETECTE:
        c, m = materiel(coeurs, memoire_mo)
        petit = c <= COEURS_PETIT or (m is not None and m <= MEMOIRE_PETIT_MO)
        _DETECTE[cle] = "petit" if petit else "normal"
        if coeurs is None and memoire_mo is None:
            print("[PC] %d coeurs, %s : %s" % (c, "%.1f Go" % (m / 1024.0) if m else "memoire inconnue",
                                              "PETIT PC" if petit else "PC normal"))
    return _DETECTE[cle]


def mode(choix=None):
    """Le mode en vigueur : 'petit' ou 'normal'. choix = 'auto', 'petit', 'normal'
    (Options) ; None = celui de config.json."""
    if _FORCE[0] in ("petit", "normal"):
        return _FORCE[0]
    if choix is None:
        try:
            import apparence
            choix = apparence.reglage("mode_pc", "auto")
        except Exception:
            choix = "auto"
    if choix in ("petit", "normal"):
        return choix
    return detecter()


def est_petit(choix=None):
    return mode(choix) == "petit"


def description():
    """« 4 cœurs, 7,9 Go : petit PC » (Options)."""
    c, m = materiel()
    memoire = ("%.0f Go" % (m / 1024.0)).replace(".", ",") if m else "mémoire inconnue"
    if detecter() == "petit":                 # phrases entieres : traduites en anglais
        return "Ce PC : %d cœurs, %s : petit PC" % (c, memoire)
    return "Ce PC : %d cœurs, %s : PC normal" % (c, memoire)
