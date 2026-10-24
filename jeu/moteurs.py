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
import os
import threading

_verrou = threading.RLock()
_moteurs = {}          # "jeu" / "analyse" -> StockfishEngine
_reglages_analyse = {}  # ce avec quoi le moteur d'analyse a ete configure


def _fabriquer(chemin):
    from engine import StockfishEngine
    return StockfishEngine(chemin)


_creations = {}        # role -> threading.Event (un Stockfish en train de demarrer)


def _obtenir(role, chemin, creer, apres_creation=None):
    """Le moteur du role, cree s'il le faut. 24/10 (« quitter est long ») :
    demarrer Stockfish prend ~1 s ; avant, tout se faisait SOUS le verrou
    general, et liberer() / tout_fermer() (bouton Quitter) attendaient la fin
    de ce demarrage. Maintenant le verrou ne protege que la liste ; un second
    fil qui demande le meme role attend le premier au lieu d'en lancer un autre.
    Renvoie (moteur ou None, True s'il vient d'etre cree)."""
    with _verrou:
        moteur = _moteurs.get(role)
        if moteur is not None and not _vivant(moteur):
            _oublier(role)
            moteur = None
        if moteur is not None or not creer:
            return moteur, False
        attente = _creations.get(role)
        createur = attente is None
        if createur:
            attente = _creations[role] = threading.Event()
    if not createur:
        attente.wait(30)
        with _verrou:
            return _moteurs.get(role), False
    moteur = None
    try:
        moteur = _fabriquer(chemin)
        if not _vivant(moteur):
            moteur = None
        elif apres_creation is not None:
            apres_creation(moteur)
    except Exception as e:
        print("[MOTEURS] demarrage de %s impossible : %s" % (role, e))
        moteur = None
    finally:
        with _verrou:
            if moteur is not None:
                _moteurs[role] = moteur
            _creations.pop(role, None)
        attente.set()
    return moteur, moteur is not None


def _priorite_basse(moteur):
    """23/10 (surveillance en direct) : pendant la revue, les Stockfish
    d'analyse prenaient les 12 processeurs et le jeu devait se battre avec eux
    (PC a 100 %). En priorite basse, ils prennent tout ce qui est libre, mais
    le jeu passe avant : il reste fluide. L'analyse ne perd presque rien."""
    processus = getattr(moteur, "process", None)
    if processus is None:
        return False
    try:
        if os.name == "nt":
            import ctypes
            SOUS_LA_NORMALE = 0x00004000          # BELOW_NORMAL_PRIORITY_CLASS
            return bool(ctypes.windll.kernel32.SetPriorityClass(
                int(processus._handle), SOUS_LA_NORMALE))
        os.setpriority(os.PRIO_PROCESS, processus.pid, 5)
        return True
    except Exception as e:
        print("[MOTEURS] priorite basse impossible : %s" % e)
        return False


def moteur_de_jeu(chemin=None, elo=None, creer=True):
    """Le moteur qui JOUE contre toi. Bride a ton classement.

    On ne le confond jamais avec celui d'analyse : regler l'analyse a fond ne
    rend donc pas ton adversaire plus fort.
    """
    moteur, neuf = _obtenir("jeu", chemin, creer)
    if moteur is None:
        return None
    if neuf:
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
    return moteur_d_analyse_role(role_d_analyse(indice), chemin, threads, hash_mb, creer)


def moteur_d_analyse_role(role, chemin=None, threads=None, hash_mb=1024, creer=True):
    """Un moteur d'analyse sous un nom libre (24/10, p35 : celui de l'analyse
    libre, « libre », ferme en quittant l'ecran)."""
    moteur, neuf = _obtenir(role, chemin, creer, apres_creation=_priorite_basse)
    if moteur is None:
        return None
    if neuf:
        print("[MOTEURS] moteur d'ANALYSE %s pret (priorite basse)" % role)
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


def liberer_les_renforts(combien):
    """Ferme les moteurs d'analyse de renfort (analyse-2, analyse-3...) une
    fois l'analyse de la partie finie : ils gardaient ~1,3 Go chacun jusqu'a
    la fermeture du jeu. Le premier reste (sa table de hachage sert encore)."""
    return sum(1 for indice in range(1, int(combien)) if liberer(role_d_analyse(indice)))


ROLE_VARIANTE = role_d_analyse(5)


def liberer_la_variante():
    """Ferme le moteur des variantes de la revue (en quittant la revue)."""
    return liberer(ROLE_VARIANTE)


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


def _en_recherche(moteur):
    """True si le moteur cherche en ce moment (son verrou est tenu jusqu'a
    « bestmove »)."""
    verrou = getattr(moteur, "_verrou", None)
    if verrou is None:
        return False
    if verrou.acquire(blocking=False):
        verrou.release()
        return False
    return True


def liberer_au_repos(garder=("jeu",)):
    """24/10 (oui de Julien) : au menu, sans rien a analyser, les Stockfish
    d'analyse gardaient ~5,5 Go jusqu'a la fermeture du jeu. On les ferme
    (ils redemarrent en ~1 s a la prochaine revue). Les analyses finies sont
    dans les fichiers .analyse.json : rien n'est perdu. On garde l'adversaire
    (leger, il rend le lancement d'une partie immediat) et on ne coupe jamais
    un moteur en pleine recherche. Renvoie le nombre de moteurs fermes."""
    with _verrou:
        roles = [role for role, m in _moteurs.items()
                 if role not in garder and not _en_recherche(m)]
    return sum(1 for role in roles if liberer(role))


def tout_fermer():
    """A la fermeture du jeu : aucun stockfish.exe ne doit survivre."""
    with _verrou:
        roles = list(_moteurs)
    for role in roles:
        liberer(role)


atexit.register(tout_fermer)
