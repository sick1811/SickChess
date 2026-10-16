# moteurs.py - V7.2 : NOUVEAU FICHIER
#
# LES DEUX MOTEURS STOCKFISH, GARDES EN VIE.
#
# TA REMARQUE : "il n'y a qu'un processus stockfish et pas deux - il doit y en
# avoir 2 normalement".
#
# Tu as raison, et voila ce qui se passait vraiment. Il y a bien DEUX roles :
#
#   MOTEUR DE JEU      bride a ton classement (Skill Level bas, profondeur
#                      limitee). C'est ton adversaire. Il doit rester faible,
#                      sinon la partie n'a plus d'interet.
#   MOTEUR D'ANALYSE   aucune bride, Elo maximum, tous les coeurs, grosse table
#                      de hachage. C'est lui qui juge tes coups. Il doit rester
#                      fort, sinon l'analyse ne vaut rien.
#
# Mais dans ton journal du 31/08, on lit QUATRE FOIS de suite :
#
#     ENGINE : lancement du processus stockfish
#     ENGINE : mode ANALYSE - Elo maximum, aucune bride
#     ENGINE : fermeture stockfish
#
# Chaque ecran (fin de partie, replay, relance par la touche A) creait SON
# processus d'analyse, le configurait, puis le tuait en partant. Resultat :
#   - a un instant donne il n'y en avait effectivement qu'un seul de vivant,
#     d'ou ce que tu as vu dans le gestionnaire des taches ;
#   - et surtout, chaque relance repartait avec une table de hachage VIDE. Tout
#     le travail deja fait etait jete. C'est une des raisons de la lenteur.
#
# CE FICHIER REGLE LES DEUX. Les moteurs sont crees une seule fois, gardes en
# vie tant que le jeu tourne, et rendus a qui les demande. Deux processus
# stockfish.exe, en permanence, chacun dans son role. La table de hachage de
# l'analyse survit d'un ecran a l'autre : la deuxieme analyse est quasi
# instantanee.
#
# AUCUNE FONCTION SUPPRIMEE : ce fichier n'existait pas. StockfishEngine garde
# tout ce qu'il avait, on ne fait que le partager au lieu de le recreer.

import atexit
import threading

_verrou = threading.RLock()
_moteurs = {}          # "jeu" / "analyse" -> StockfishEngine
_reglages_analyse = {}  # ce avec quoi le moteur d'analyse a ete configure


def _fabriquer(chemin):
    from engine import StockfishEngine
    return StockfishEngine(chemin)


def moteur_de_jeu(chemin=None, elo=None, creer=True):
    """Le moteur qui JOUE contre toi. Bride a ton classement.

    On ne le confond jamais avec celui d'analyse : regler l'analyse a fond ne
    rend donc pas ton adversaire plus fort.
    """
    with _verrou:
        moteur = _moteurs.get("jeu")
        if moteur is not None and not _vivant(moteur):
            _oublier("jeu")
            moteur = None
        if moteur is None:
            if not creer:
                return None
            moteur = _fabriquer(chemin)
            if not _vivant(moteur):
                return None
            _moteurs["jeu"] = moteur
            print("[MOTEURS] moteur de JEU pret (processus 1/2)")
        if elo is not None:
            try:
                if getattr(moteur, "elo_courant", None) != int(elo) \
                        or getattr(moteur, "mode_analyse", False):
                    moteur.set_custom_elo(int(elo))
            except Exception as e:
                print("[MOTEURS] reglage du niveau impossible : %s" % e)
        return moteur


def role_d_analyse(indice):
    """Le nom du n-ieme moteur d'analyse. Le premier garde son nom d'origine."""
    indice = max(0, int(indice))
    return "analyse" if indice == 0 else "analyse-%d" % (indice + 1)


def moteur_d_analyse(chemin=None, threads=None, hash_mb=2048, creer=True):
    """Le moteur qui ANALYSE. Pleine puissance, et GARDE EN VIE.

    C'est la le vrai gain de vitesse : sa table de hachage n'est plus jetee
    entre l'ecran de fin et le replay, ni quand tu relances l'analyse.

    SIGNATURE INCHANGEE : tout ce qui l'appelait continue de marcher et recoit
    toujours le PREMIER moteur d'analyse.
    """
    return moteur_d_analyse_n(0, chemin, threads, hash_mb, creer)


def moteur_d_analyse_n(indice, chemin=None, threads=None, hash_mb=1024,
                       creer=True):
    """Le n-ieme moteur d'analyse (V7.2 : l'analyse en tourne plusieurs).

    POURQUOI PLUSIEURS (ta demande : "je veux la precision, la puissance ET la
    vitesse") : Stockfish monte tres mal en threads - 12 threads ne vont que
    6,3 fois plus vite qu'un seul. Quatre moteurs a 3 threads vont, eux, 9,4
    fois plus vite AU TOTAL. Voir parallele.py pour les chiffres.

    Chacun garde SA table de hachage et SON morceau de la partie : deux
    positions qui se suivent restent chez le meme moteur, qui retrouve donc le
    travail de la precedente.
    """
    role = role_d_analyse(indice)
    with _verrou:
        moteur = _moteurs.get(role)
        if moteur is not None and not _vivant(moteur):
            _oublier(role)
            moteur = None
        if moteur is None:
            if not creer:
                return None
            moteur = _fabriquer(chemin)
            if not _vivant(moteur):
                return None
            _moteurs[role] = moteur
            print("[MOTEURS] moteur d'ANALYSE %s pret" % role)
        voulu = (threads, int(hash_mb or 0))
        # On ne renvoie les options que si elles ont change : "setoption Hash"
        # VIDE la table de hachage, ce serait perdre exactement ce qu'on essaie
        # de garder.
        if _reglages_analyse.get(role) != voulu \
                or not getattr(moteur, "mode_analyse", False):
            try:
                moteur.configurer_pour_analyse(threads, hash_mb)
                _reglages_analyse[role] = voulu
            except Exception as e:
                print("[MOTEURS] configuration de %s impossible : %s"
                      % (role, e))
        return moteur


def moteurs_d_analyse(combien, chemin=None, threads=None, hash_mb=1024,
                      creer=True):
    """Les 'combien' moteurs d'analyse, prets a travailler en parallele.

    Renvoie la liste de ceux qui ont vraiment demarre - jamais None. Si la
    machine ne peut pas en lancer quatre, on travaille avec ce qu'on a plutot
    que d'echouer.
    """
    sortie = []
    for indice in range(max(1, int(combien))):
        moteur = moteur_d_analyse_n(indice, chemin, threads, hash_mb, creer)
        if moteur is None:
            if indice == 0:
                return []
            print("[MOTEURS] seulement %d moteur(s) d'analyse disponible(s)"
                  % indice)
            break
        sortie.append(moteur)
    return sortie


def nombre_d_analyse():
    """Combien de moteurs d'analyse sont vivants."""
    with _verrou:
        return sum(1 for role, m in _moteurs.items()
                   if role.startswith("analyse") and _vivant(m))


def liberer_les_analyses(garder=1):
    """Ferme les moteurs d'analyse en trop et rend la memoire.

    On en garde toujours au moins un : sa table de hachage est ce qui rend la
    deuxieme analyse d'une partie quasi instantanee.
    """
    with _verrou:
        roles = sorted(role for role in _moteurs
                       if role.startswith("analyse"))
    fermes = 0
    for role in roles[max(0, int(garder)):]:
        if liberer(role):
            fermes += 1
    return fermes


# --------------------------------------------------------------- moteur de jeu
#
# PENDANT L'ANALYSE, LE MOTEUR DE JEU NE FAIT RIEN - MAIS IL GARDE SES THREADS.
#
# Ton journal : "[CACHE MANAGER] Cache = 512 MB, Threads = 4". Ces 4 threads
# sont reserves au moteur qui joue contre toi. Quand la partie est finie et que
# l'analyse tourne, il ne calcule plus rien : ces 4 coeurs sur 12 sont donc
# immobilises pour rien, pendant que l'analyse se bat pour aller vite.
#
# On les lui retire le temps de l'analyse, et on les lui rend apres. On ne
# FERME pas le processus : tu peux demander une revanche a tout moment, et le
# relancer couterait plus cher que de le laisser dormir a 1 thread.

_threads_de_jeu_rendus = {}


def mettre_le_jeu_en_veille(threads=1):
    """Ramene le moteur de JEU a 1 thread pendant l'analyse. Reversible."""
    with _verrou:
        moteur = _moteurs.get("jeu")
        if moteur is None or not _vivant(moteur) \
                or "avant" in _threads_de_jeu_rendus:
            return False
        avant = getattr(moteur, "threads_courant", None)
        if avant is None:
            try:
                from cache_manager import get_cache_manager
                avant = get_cache_manager().get_threads()
            except Exception:
                avant = None
        try:
            moteur.regler_threads(max(1, int(threads)))
        except Exception as e:
            print("[MOTEURS] mise en veille du moteur de jeu impossible : %s" % e)
            return False
        _threads_de_jeu_rendus["avant"] = avant
        print("[MOTEURS] moteur de JEU en veille (%s -> %d thread(s)) : "
              "ses coeurs passent a l'analyse" % (avant, max(1, int(threads))))
        return True


def reveiller_le_jeu():
    """Rend au moteur de JEU les threads qu'on lui avait pris."""
    with _verrou:
        avant = _threads_de_jeu_rendus.pop("avant", None)
        moteur = _moteurs.get("jeu")
        if avant is None or moteur is None or not _vivant(moteur):
            return False
        try:
            moteur.regler_threads(int(avant))
        except Exception as e:
            print("[MOTEURS] reveil du moteur de jeu impossible : %s" % e)
            return False
        print("[MOTEURS] moteur de JEU reveille (%d thread(s))" % int(avant))
        return True


def _vivant(moteur):
    try:
        return bool(moteur.est_vivant())
    except Exception:
        return False


def _oublier(role):
    moteur = _moteurs.pop(role, None)
    _reglages_analyse.pop(role, None)
    if role == "jeu":
        _threads_de_jeu_rendus.pop("avant", None)
    return moteur


def moteurs_vivants():
    """Combien de processus stockfish le jeu tient ouverts. Doit valoir 2."""
    with _verrou:
        return sum(1 for m in _moteurs.values() if _vivant(m))


def roles_vivants():
    with _verrou:
        return sorted(role for role, m in _moteurs.items() if _vivant(m))


def liberer(role):
    """Ferme UN des deux moteurs (par exemple le moteur de jeu en fin de partie)."""
    with _verrou:
        moteur = _oublier(role)
    if moteur is not None:
        try:
            moteur.quit()
        except Exception:
            pass
        print("[MOTEURS] moteur %s ferme" % role)
        return True
    return False


def tout_fermer():
    """A la fermeture du jeu : aucun stockfish.exe ne doit survivre."""
    with _verrou:
        roles = list(_moteurs)
    for role in roles:
        liberer(role)


atexit.register(tout_fermer)
