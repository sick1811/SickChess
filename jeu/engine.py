# engine.py - V6 : dialogue UCI avec Stockfish
#
# CE QUI CHANGE PAR RAPPORT A V5 (bugs M1, M7, m3 du rapport) :
#   1. set_custom_elo() applique un niveau qui MARCHE VRAIMENT.
#      En V5 elle envoyait UCI_Elo=100/300/600 : Stockfish refuse ces valeurs
#      (son minimum est 1320) et continuait a jouer a pleine puissance.
#      Maintenant les options acceptees par le moteur sont lues au demarrage,
#      et sous le minimum du moteur on passe par "Skill Level" + une limite de
#      profondeur, qui eux fonctionnent a tous les niveaux.
#   2. set_custom_elo() ne touche plus au Hash ni aux Threads : c'est le role
#      de CacheManager. Les deux ne se contredisent plus.
#   3. quit() tue reellement le processus, et un atexit garantit qu'aucun
#      stockfish.exe ne survit a la fermeture du jeu (bug M7).
#   4. Le chemin est resolu par rapport au dossier du jeu : plus besoin de
#      chemin absolu dans config.json.
#   5. Sur Windows, la console noire de Stockfish ne s'ouvre plus.
#   6. Un verrou empeche deux threads d'ecrire dans le moteur en meme temps.
#   7. Les logs "ENGINE RECV" (des centaines de lignes par coup) sont derriere
#      un interrupteur : engine.verbeux = True pour les revoir.
#
# AUCUNE FONCTION SUPPRIMEE : __init__, _send_command, _wait_response,
# set_custom_elo, get_best_move et quit sont toutes conservees, memes noms,
# memes signatures.

import atexit
import json
import os
import subprocess
import sys
import threading
import time

# === Connexion au CacheManager (Hash / Threads) ===
import faiblesse
from cache_manager import get_cache_manager

_SECOND_COUP = None


def _second_coup_demande():
    """config.json : "analyse_second_coup": true fait chercher DEUX lignes.

    Par defaut NON. Deux lignes coutent de la profondeur a temps egal, donc de
    la precision : ca ne vaut le coup que si tu tiens vraiment a la pastille
    "Excellent".
    """
    global _SECOND_COUP
    if _SECOND_COUP is not None:
        return _SECOND_COUP
    _SECOND_COUP = False
    try:
        import json
        import os
        for dossier in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
            chemin = os.path.join(dossier, "config.json")
            if os.path.exists(chemin):
                with open(chemin, "r", encoding="utf-8") as f:
                    _SECOND_COUP = bool(json.load(f).get("analyse_second_coup",
                                                         False))
                break
    except Exception:
        _SECOND_COUP = False
    return _SECOND_COUP


def _lire_config():
    """Lit config.json (dossier courant ou dossier du jeu). Jamais bloquant."""
    for dossier in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        chemin = os.path.join(dossier, "config.json")
        if os.path.exists(chemin):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    contenu = json.load(f)
                # 04/09 : un config.json coupe ("null", "[]") passait json.load
                # et l'appelant faisait .get() dessus -> AttributeError.
                return contenu if isinstance(contenu, dict) else {}
            except (ValueError, OSError):
                return {}
    return {}

# Tous les moteurs lances, pour n'en laisser aucun derriere soi.
_moteurs_actifs = []


def _tuer_les_moteurs_restants():
    for moteur in list(_moteurs_actifs):
        try:
            moteur.quit()
        except Exception:
            pass


atexit.register(_tuer_les_moteurs_restants)


def _flags_windows():
    """Empeche la console noire de Stockfish de s'ouvrir sous Windows."""
    if os.name != "nt":
        return {}
    info = subprocess.STARTUPINFO()
    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return {
        "startupinfo": info,
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
    }


def diagnostic(path, cherche_dans=()):
    """POURQUOI Stockfish manque, en francais, avec ce qu'il faut faire.

    V8 (04/09) - "stockfish introuvable ou illisible apres decompilation".
    L'ancien message disait "Verifie 'stockfish_path' dans config.json", ce qui
    n'avait aucun rapport avec la vraie cause : l'archive etait complete, mais
    PowerShell l'avait ecrite avec des antislashs, et la decompression n'avait
    pas recree le dossier _internal. Un message qui envoie chercher au mauvais
    endroit coute plus cher que pas de message du tout.
    """
    base = os.path.basename(path or "stockfish.exe")
    a_cote = (os.path.dirname(os.path.abspath(sys.executable))
              if getattr(sys, "frozen", False) else os.getcwd())
    interne = os.path.join(a_cote, "_internal")

    if getattr(sys, "frozen", False) and not os.path.isdir(interne):
        # Le cas le plus frequent, et de loin : le paquet a ete mal decompresse.
        plats = []
        try:
            plats = [n for n in os.listdir(a_cote) if "_internal" in n]
        except OSError:
            pass
        if plats:
            return ("Le dossier _internal n'a pas ete recree : l'archive a ete "
                    "decompressee a plat. Decompresse-la avec l'Explorateur "
                    "Windows (clic droit / Extraire tout) ou avec 7-Zip, puis "
                    "relance Echec.exe.")
        return ("Le dossier _internal est absent a cote de Echec.exe. "
                "Garde TOUT le dossier ensemble : l'executable ne sait pas "
                "jouer sans lui.")

    voisin = os.path.join(interne, base)
    if os.path.exists(voisin):
        return ("%s est bien la, mais Windows refuse de l'ouvrir. Regarde la "
                "quarantaine de ton antivirus : un moteur d'echecs de 114 Mo "
                "est souvent pris pour un intrus." % base)

    if getattr(sys, "frozen", False):
        return ("%s est introuvable dans _internal. Il a probablement ete mis "
                "en quarantaine par l'antivirus, ou perdu a la decompression. "
                "Redecompresse l'archive et autorise %s." % (base, base))

    return ("%s est introuvable. Pose-le a cote du jeu, ou indique son chemin "
            "dans 'stockfish_path' de config.json.%s"
            % (base,
               ("\nCherche dans : %s" % cherche_dans[0]) if cherche_dans else ""))


class StockfishEngine:
    def __init__(self, path, verbeux=False):
        self.cherche_dans = []
        self.path = self._resoudre_chemin(path)
        self.process = None
        self.verbeux = verbeux
        self._verrou = threading.RLock()
        self.options_disponibles = {}   # nom -> dict(min, max, type)
        self.elo_courant = None
        self.skill_courant = None
        # V7.2 : quand le classement vise est SOUS le minimum de Stockfish, ce
        # n'est plus lui qui choisit le coup, c'est nous (voir faiblesse.py).
        # None = Stockfish choisit tout seul, comme avant.
        self.elo_bride = None
        self.multipv_courant = 1
        self.profondeur_max = None      # None = pas de limite
        self.mode_analyse = False       # True = moteur d'analyse, jamais bride
        self.threads_courant = None     # V7.2 : dernier "setoption Threads" envoye

        print("ENGINE : verification du chemin stockfish")
        if not self.path or not os.path.exists(self.path):
            print("ERROR Stockfish introuvable : " + str(path))
            for essai in self.cherche_dans:
                print("ENGINE :   cherche dans %s" % essai)
            raise FileNotFoundError(diagnostic(path, self.cherche_dans))

        print("ENGINE : lancement du processus stockfish")
        self.process = subprocess.Popen(
            self.path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            cwd=os.path.dirname(self.path) or None,
            **_flags_windows()
        )
        _moteurs_actifs.append(self)
        print("ENGINE : processus stockfish demarre")

        self._send_command("uci")
        if not self._lire_options_uci():
            raise RuntimeError("Stockfish n'a pas repondu 'uciok'")
        self._send_command("isready")
        self._wait_response("readyok")

        print("ENGINE : stockfish initialise avec succes (%d options detectees)"
              % len(self.options_disponibles))

        # === Options de performance (Hash / Threads) via CacheManager ===
        config = _lire_config()
        self.cache_manager = get_cache_manager(
            config.get("stockfish_hash_mb", 512), config.get("stockfish_threads")
        )
        self.cache_manager.apply_to_engine(self)
        self._send_command("isready")
        self._wait_response("readyok")

    # ------------------------------------------------------------------ chemins

    def _candidats(self, path):
        """Tous les endroits ou Stockfish peut raisonnablement se trouver."""
        base = os.path.basename(path)
        candidats = [
            path,
            os.path.join(os.getcwd(), path),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), path),
        ]
        # Une fois compile en .exe, les fichiers embarques sont ailleurs.
        interne = getattr(sys, "_MEIPASS", None)
        if interne:
            candidats.append(os.path.join(interne, path))
            candidats.append(os.path.join(interne, base))
        a_cote = None
        if getattr(sys, "frozen", False):
            a_cote = os.path.dirname(os.path.abspath(sys.executable))
            candidats.append(os.path.join(a_cote, base))
            candidats.append(os.path.join(a_cote, "_internal", base))
        # V8 (04/09) - LA DECOMPRESSION RATEE, ton "stockfish introuvable ou
        # illisible apres decompilation". Compress-Archive de PowerShell ecrit
        # les noms avec des ANTISLASHS ("_internal\stockfish.exe") au lieu des
        # barres obliques imposees par le format ZIP. Selon le logiciel qui
        # ouvre l'archive, on n'obtient alors pas un dossier _internal mais des
        # fichiers a plat PORTANT L'ANTISLASH DANS LEUR NOM. Le paquet est
        # complet, et pourtant le jeu ne trouve rien. On regarde donc aussi ce
        # nom-la : mieux vaut demarrer que d'avoir raison.
        for racine in (a_cote, os.getcwd()):
            if racine:
                candidats.append(os.path.join(racine, "_internal\\" + base))
                candidats.append(os.path.join(racine, "_internal/" + base))
        return candidats

    def _resoudre_chemin(self, path):
        """Accepte un chemin absolu, relatif au dossier courant, ou au dossier du jeu.

        Retient AUSSI la liste de ce qui a ete essaye : quand ca rate, c'est la
        seule chose qui permette de dire pourquoi.
        """
        if not path:
            self.cherche_dans = []
            return path
        self.cherche_dans = self._candidats(path)
        for c in self.cherche_dans:
            if os.path.exists(c):
                return os.path.abspath(c)
        return path

    # ------------------------------------------------------------ communication

    def est_vivant(self):
        """True si le processus Stockfish tourne toujours."""
        return self.process is not None and self.process.poll() is None

    def _send_command(self, cmd):
        with self._verrou:
            if not self.est_vivant():
                return False
            if self.verbeux:
                print("ENGINE SEND -> " + cmd)
            try:
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()
                return True
            except (OSError, ValueError) as e:
                print("ENGINE : ecriture impossible (" + str(e) + ")")
                return False

    def send_command(self, cmd):
        """Version publique de _send_command (utilisee par CacheManager)."""
        return self._send_command(cmd)

    def _lire_ligne(self):
        """Lit une ligne du moteur. Renvoie None si le processus est mort."""
        if not self.est_vivant():
            return None
        try:
            ligne = self.process.stdout.readline()
        except (OSError, ValueError):
            return None
        if ligne == "":          # flux ferme = processus termine
            return None
        ligne = ligne.strip()
        if ligne and self.verbeux:
            print("ENGINE RECV <- " + ligne)
        return ligne

    def _wait_response(self, expected, timeout=8.0):
        start = time.time()
        while time.time() - start < timeout:
            ligne = self._lire_ligne()
            if ligne is None:
                print("ENGINE : processus termine pendant l'attente de '%s'" % expected)
                return False
            if expected.lower() in ligne.lower():
                return True
        print("ENGINE : delai depasse en attendant '%s'" % expected)
        return False

    def _lire_options_uci(self, timeout=10.0):
        """Lit la reponse a 'uci' et memorise les options que ce moteur accepte."""
        start = time.time()
        while time.time() - start < timeout:
            ligne = self._lire_ligne()
            if ligne is None:
                return False
            if ligne.startswith("option name "):
                self._analyser_option(ligne)
            elif ligne.lower() == "uciok":
                return True
        return False

    def _analyser_option(self, ligne):
        """'option name UCI_Elo type spin default 1320 min 1320 max 3190'"""
        mots = ligne.split()
        try:
            i_type = mots.index("type")
        except ValueError:
            return
        nom = " ".join(mots[2:i_type])
        infos = {"type": mots[i_type + 1] if i_type + 1 < len(mots) else ""}
        for cle in ("min", "max", "default"):
            if cle in mots:
                valeur = mots[mots.index(cle) + 1]
                try:
                    infos[cle] = int(valeur)
                except ValueError:
                    infos[cle] = valeur
        self.options_disponibles[nom] = infos

    def _option_existe(self, nom):
        return nom in self.options_disponibles or not self.options_disponibles

    # ------------------------------------------------------------------ niveau

    def set_custom_elo(self, elo):
        """Regle la force de jeu. Fonctionne a TOUS les niveaux, meme sous 1320."""
        elo = max(100, min(3200, int(elo)))
        print("ENGINE : configuration elo " + str(elo))

        infos_elo = self.options_disponibles.get("UCI_Elo", {})
        elo_min = infos_elo.get("min", 1320)
        elo_max = infos_elo.get("max", 3190)

        skill = self._elo_vers_skill(elo)
        self.elo_courant = elo
        self.skill_courant = skill

        if self._option_existe("UCI_LimitStrength") and elo >= elo_min:
            # Le moteur sait limiter sa force lui-meme : c'est le plus fidele.
            self._send_command("setoption name UCI_LimitStrength value true")
            self._send_command("setoption name UCI_Elo value %d"
                               % max(elo_min, min(elo, elo_max)))
            self._send_command("setoption name Skill Level value %d" % skill)
            self._regler_multipv(1)
            self.profondeur_max = None
            self.elo_bride = None
        else:
            # SOUS LE MINIMUM DU MOTEUR (ta remarque du 31/08 : "a 100 Elo il
            # est 10x plus fort"). Tu avais raison, et l'ancienne methode etait
            # fausse sur le principe :
            #   - "Skill Level 0" n'est pas un debutant, c'est le plancher de
            #     Stockfish : environ 1350 Elo a lui seul ;
            #   - "profondeur 1" ne rend pas faible, parce que la recherche de
            #     quiescence deroule quand meme toutes les prises : le moteur
            #     ne laissait jamais une piece en prise et ramassait toujours
            #     le materiel gratuit.
            # On change donc de principe : Stockfish CLASSE les coups en toute
            # lucidite (Skill 20) mais a faible profondeur, et c'est NOUS qui
            # choisissons, plus ou moins mal, selon le niveau vise.
            self._send_command("setoption name UCI_LimitStrength value false")
            self._send_command("setoption name Skill Level value 20")
            self.profondeur_max = faiblesse.profondeur(elo)
            self._regler_multipv(faiblesse.multipv(elo))
            self.elo_bride = elo
            print("ENGINE : elo %d sous le minimum du moteur (%d) -> %s"
                  % (elo, elo_min, faiblesse.description(elo)))

        # Marge de temps pour l'affichage : evite que le moteur depasse son budget.
        self._send_command("setoption name Move Overhead value 100")
        self._send_command("isready")
        self._wait_response("readyok", timeout=4.0)
        print("ENGINE : stockfish configure a elo " + str(elo)
              + " (Skill Level " + str(skill) + ")")

    def _regler_multipv(self, combien):
        """Combien de coups Stockfish doit classer. 1 = comportement d'origine."""
        combien = max(1, int(combien))
        if combien == self.multipv_courant:
            return False
        if not self._option_existe("MultiPV") and combien > 1:
            # Un moteur sans MultiPV : on retombe sur l'ancien comportement
            # plutot que d'envoyer une option qu'il ne comprend pas.
            print("ENGINE : ce moteur n'a pas MultiPV, choix maison desactive")
            return False
        self._send_command("setoption name MultiPV value %d" % combien)
        self.multipv_courant = combien
        return True

    def _elo_vers_skill(self, elo):
        """Skill Level 0-20. 0 ~= 1350 elo, 20 = pleine puissance."""
        if elo <= 800:
            return 0
        if elo >= 2850:
            return 20
        return max(0, min(20, int(round((elo - 800) / 102.5))))

    def _elo_vers_profondeur(self, elo):
        """Profondeur de recherche pour les niveaux tres faibles."""
        if elo <= 300:
            return 1
        if elo <= 600:
            return 2
        if elo <= 900:
            return 3
        if elo <= 1100:
            return 5
        return 7

    DOSSIER_TABLES = "syzygy"

    def _brancher_les_tables_de_finale(self):
        """Donne a Stockfish les tables Syzygy si le dossier existe.

        LES TABLES SONT LIVREES AVEC LA V8, dans le dossier syzygy/.
        (Le 03/09 je te disais ne pas pouvoir les trouver : les serveurs
        habituels me sont fermes. Elles sont en fait sur github, dans le depot
        hyperbotauthor/syzygy - je les ai cherchees a nouveau quand tu as
        demande "le meilleur", et cette fois je les ai eues.)

        CE QU'ELLES FONT : elles disent la VERITE sur une finale a cinq pieces
        ou moins - gagne, nulle, perdu - sans aucune recherche. Le moteur
        arrete de deviner et sait. Tes parties finissent souvent en tour contre
        fou ou en finale de pions : c'est exactement la que ca sert.

        POURQUOI SEULEMENT LES .rtbw (WDL) ET PAS LES .rtbz (DTZ) : les WDL
        pesent 378 Mo et donnent le RESULTAT, ce dont la recherche a besoin a
        chaque noeud. Les DTZ pesent 560 Mo de plus et ne servent qu'a compter
        les coups jusqu'a la prise ou la poussee de pion, pour gagner sous la
        regle des 50 coups. Trois fois moins de place pour l'essentiel du gain.
        Si tu veux les DTZ aussi, dis-le : meme depot, meme methode.

        Sans le dossier, il ne se passe rien - pas de message, pas de ralenti.
        """
        if not self._option_existe("SyzygyPath"):
            return False
        dossiers = []
        interne = getattr(sys, "_MEIPASS", None)
        for base in (os.getcwd(),
                     os.path.dirname(os.path.abspath(__file__)),
                     interne):
            if not base:
                continue
            chemin = os.path.join(base, self.DOSSIER_TABLES)
            if os.path.isdir(chemin) and chemin not in dossiers:
                try:
                    if any(n.lower().endswith((".rtbw", ".rtbz"))
                           for n in os.listdir(chemin)):
                        dossiers.append(chemin)
                except OSError:
                    pass
        if not dossiers:
            return False
        self._send_command("setoption name SyzygyPath value %s"
                           % os.pathsep.join(dossiers))
        print("ENGINE : tables de finale Syzygy branchees (%s)"
              % ", ".join(dossiers))
        return True

    def regler_threads(self, combien):
        """Change le nombre de coeurs du moteur, et se souvient de la valeur.

        V7.2 : sert a deux choses. A configurer le moteur d'analyse, comme
        avant ; et a ENDORMIR le moteur de jeu pendant l'analyse (moteurs.py) -
        il ne calcule rien a ce moment-la, mais il gardait quand meme ses
        quatre coeurs immobilises.
        """
        try:
            combien = max(1, int(combien))
        except (TypeError, ValueError):
            return False
        if not self._option_existe("Threads"):
            return False
        if getattr(self, "threads_courant", None) == combien:
            return False
        maxi = self.options_disponibles.get("Threads", {}).get("max", 512)
        combien = min(combien, int(maxi or 512))
        self._send_command("setoption name Threads value %d" % combien)
        self.threads_courant = combien
        return True

    def configurer_pour_analyse(self, threads=None, hash_mb=256, profondeur=None):
        """Met le moteur a PLEINE PUISSANCE pour analyser une partie.

        POURQUOI (ta remarque : "l'evaluation des analyses n'est pas puissante
        et donne la precision a plus ou moins 3%") :
          - le moteur qui JOUE est volontairement affaibli (Skill Level bas et
            profondeur bridee pour tenir ton Elo) ; ses evaluations ne valent
            rien pour juger une partie. Ici on releve toutes les brides ;
          - on lui donne plusieurs coeurs et une vraie table de hachage : il
            descend beaucoup plus profond dans le meme temps ;
          - et on analysera a PROFONDEUR FIXE plutot qu'au chronometre, ce qui
            rend le resultat reproductible : c'etait la cause des 3% d'ecart
            d'une analyse a l'autre.
        """
        # threads : None = tous les coeurs sauf un (on laisse de quoi afficher)
        #           0    = TOUS les coeurs (pleine puissance)
        #           N    = N coeurs
        coeurs = 2
        try:
            coeurs = os.cpu_count() or 2
        except Exception:
            pass
        if threads is None:
            threads = max(1, coeurs - 1)
        elif int(threads) <= 0:
            threads = coeurs
        threads = max(1, int(threads))
        # MEMOIRE : la table de hachage est le levier de vitesse le plus
        # efficace de Stockfish. Elle garde le resultat des positions deja
        # calculees ; comme on analyse les positions d'une partie DANS L'ORDRE,
        # chacune retrouve dedans presque tout le travail de la precedente.
        # Grosse table = meme force, beaucoup moins de temps.
        # Stockfish arrondit lui-meme a la puissance de 2 inferieure : autant
        # lui donner directement une puissance de 2, sinon on paie de la
        # memoire pour rien.
        hash_mb = max(16, int(hash_mb))
        puissance_de_deux = 16
        while puissance_de_deux * 2 <= hash_mb:
            puissance_de_deux *= 2
        hash_mb = puissance_de_deux

        # ELO MAXIMUM, et uniquement ici : le moteur qui JOUE garde ton niveau.
        # L'analyse tourne dans un processus Stockfish separe, donc regler
        # celui-ci a fond ne change rien a la force de ton adversaire.
        if self._option_existe("UCI_LimitStrength"):
            self._send_command("setoption name UCI_LimitStrength value false")
        if self._option_existe("UCI_Elo"):
            maxi = self.options_disponibles.get("UCI_Elo", {}).get("max", 3190)
            self._send_command("setoption name UCI_Elo value %d" % int(maxi or 3190))
        if self._option_existe("Skill Level"):
            self._send_command("setoption name Skill Level value 20")
        # L'analyse ne passe JAMAIS par le choix maison : elle doit dire le
        # meilleur coup, pas celui d'un debutant.
        self.elo_bride = None
        # V7.2 (03/09) - "EXCELLENT" REVIENT, MAIS PAS AU MEME PRIX.
        #
        # LE 01/09 j'avais coupe MultiPV 2 parce qu'il coutait de la profondeur.
        # LE 03/09 j'ai mesure combien, avec un vrai Stockfish, sur six
        # positions de milieu de partie :
        #
        #     profondeur 22 : MultiPV 1 = 1,36 s   MultiPV 2 = 3,25 s   (x2,4)
        #     profondeur 12 : MultiPV 1 = 0,04 s   MultiPV 2 = 0,09 s   (x2,4)
        #
        # Le RAPPORT est le meme, mais pas la facture : x2,4 sur la passe fine,
        # c'est +3 minutes sur une partie de 150 coups - plus que tout ce que
        # les quatre moteurs paralleles font gagner. x2,4 sur le SURVOL, c'est
        # +2 secondes en tout.
        #
        # On demande donc le deuxieme coup LA OU IL EST GRATUIT : au survol,
        # pour toutes les positions. La passe fine ne le redemande que pour les
        # rares positions ou le survol a vu un gros ecart - les seules qui
        # peuvent donner un "Excellent". Voir analyse_partie._effort_pour.
        #
        # "analyse_second_coup": true force les deux lignes partout, pour qui
        # veut le maximum et accepte de payer les trois minutes.
        self._regler_multipv(2 if _second_coup_demande() else 1)
        self.regler_threads(threads)
        self._brancher_les_tables_de_finale()
        if self._option_existe("Hash"):
            maxi = self.options_disponibles.get("Hash", {}).get("max", 33554432)
            self._send_command("setoption name Hash value %d"
                               % min(hash_mb, int(maxi or 33554432)))
        self.profondeur_max = int(profondeur) if profondeur else None
        self.elo_courant = None
        self.skill_courant = 20
        self._send_command("isready")
        self._wait_response("readyok", timeout=6.0)
        self.mode_analyse = True
        print("ENGINE : mode ANALYSE - Elo maximum, aucune bride "
              "(%d thread(s) sur %d, %d Mo, profondeur %s)"
              % (threads, coeurs, hash_mb, self.profondeur_max or "libre"))
        return self

    def analyser_position(self, fen, profondeur=0, temps_max_ms=8000,
                          lignes=None):
        """Voir la vraie methode juste en dessous : 'lignes' est le nombre de
        coups a classer pour CETTE position (1 = le plus rapide, 2 = on veut
        aussi le deuxieme meilleur coup)."""
        if lignes is not None:
            self._regler_multipv(max(1, int(lignes)))
        return self._analyser_position(fen, profondeur, temps_max_ms)

    def _analyser_position(self, fen, profondeur=0, temps_max_ms=8000):
        """Analyse une position. Deux facons de s'arreter, au choix :

        profondeur > 0 : le moteur s'arrete a cette profondeur. Le resultat est
                         alors reproductible a l'identique.
        profondeur = 0 : PLEINE PUISSANCE. Aucun plafond de profondeur : le
                         moteur creuse aussi loin qu'il peut dans le temps
                         donne. C'est le reglage le plus fort - il n'existe pas
                         d'analyse "sans limite du tout", il faut bien s'arreter
                         quelque part, et le temps est alors le seul frein.
        """
        profondeur = max(0, int(profondeur))
        temps_max_ms = max(50, int(temps_max_ms))
        with self._verrou:
            if not self.est_vivant():
                return None
            try:
                self._send_command("position fen " + fen)
                if profondeur:
                    self._send_command("go depth %d movetime %d"
                                       % (profondeur, temps_max_ms))
                else:
                    self._send_command("go movetime %d" % temps_max_ms)
                lignes = {}
                atteinte = 0
                limite = time.time() + (temps_max_ms / 1000.0) + 8.0
                while time.time() < limite:
                    ligne = self._lire_ligne()
                    if ligne is None:
                        return None
                    if ligne.startswith("info "):
                        entree = self._analyser_multipv(ligne)
                        if entree is not None:
                            rang, donnees = entree
                            lignes[rang] = donnees
                            atteinte = max(atteinte,
                                           donnees.get("profondeur", 0))
                    elif ligne.startswith("bestmove"):
                        morceaux = ligne.split()
                        best = morceaux[1] if len(morceaux) > 1 else "(none)"
                        if best in ("(none)", "0000"):
                            return None
                        premier = lignes.get(1) or {}
                        second = lignes.get(2)
                        return {
                            "coup": premier.get("coup") or best,
                            "evaluation": (premier["cp"] / 100.0
                                           if premier.get("cp") is not None
                                           else None),
                            "mat": premier.get("mat"),
                            "profondeur": atteinte,
                            # V7.2 : le deuxieme meilleur coup, quand il existe.
                            # Sert a reperer "le seul coup qui tenait".
                            "second_coup": (second or {}).get("coup"),
                            "second_evaluation": (
                                second["cp"] / 100.0
                                if second and second.get("cp") is not None
                                else None),
                            "second_mat": (second or {}).get("mat"),
                        }
                self._send_command("stop")
                return None
            except Exception as e:
                print("ENGINE : erreur analyser_position = " + str(e))
                return None

    def nouvelle_partie(self):
        """Vide le cache du moteur entre deux parties (evite les coups 'appris')."""
        self._send_command("ucinewgame")
        self._send_command("isready")
        return self._wait_response("readyok", timeout=5.0)

    # ------------------------------------------------------------------ analyse

    def get_best_move(self, fen, max_time_ms=1500):
        """Renvoie le meilleur coup en notation UCI, ou None."""
        resultat = self.get_best_move_details(fen, max_time_ms)
        return resultat["coup"] if resultat else None

    def get_best_move_details(self, fen, max_time_ms=1500):
        """Comme get_best_move, mais renvoie aussi l'evaluation et la profondeur.

        {'coup': 'e2e4', 'evaluation': 0.34, 'mat': None, 'profondeur': 12}
        L'evaluation sert au lot 4 (barre d'avantage et export PGN).
        """
        max_time_ms = max(20, int(max_time_ms))
        if self.verbeux:
            print("ENGINE : demande bestmove (temps " + str(max_time_ms) + "ms)")

        with self._verrou:
            if not self.est_vivant():
                print("ENGINE : le processus est mort, aucun coup possible")
                return None
            if self.elo_bride is not None and self.multipv_courant > 1:
                # V7.2 : niveau debutant - Stockfish classe, nous choisissons.
                return self._coup_bride(fen, max_time_ms)
            try:
                self._send_command("position fen " + fen)
                if self.profondeur_max:
                    self._send_command("go movetime %d depth %d"
                                       % (max_time_ms, self.profondeur_max))
                else:
                    self._send_command("go movetime %d" % max_time_ms)

                evaluation, mat, profondeur = None, None, 0
                limite = time.time() + (max_time_ms / 1000.0) + 5.0
                while time.time() < limite:
                    ligne = self._lire_ligne()
                    if ligne is None:
                        print("ENGINE : processus termine pendant la recherche")
                        return None
                    if ligne.startswith("info "):
                        ev, mt, pf = self._analyser_info(ligne)
                        if ev is not None:
                            evaluation = ev
                        if mt is not None:
                            mat = mt
                        if pf:
                            profondeur = pf
                    elif ligne.startswith("bestmove"):
                        morceaux = ligne.split()
                        best = morceaux[1] if len(morceaux) > 1 else "(none)"
                        if best == "(none)" or best == "0000":
                            return None
                        return {"coup": best, "evaluation": evaluation,
                                "mat": mat, "profondeur": profondeur}
                print("ENGINE : timeout - pas de bestmove")
                self._send_command("stop")
                return None
            except Exception as e:
                print("ENGINE : erreur get_best_move = " + str(e))
                return None

    def _lire_les_coups_classes(self, fen, max_time_ms):
        """Demande le classement des coups et le renvoie, meilleur en premier.

        ([{coup, cp, mat, profondeur}, ...], coup_de_secours) ou (None, None)
        si le moteur n'a pas repondu. Le verrou doit deja etre pris.
        """
        self._send_command("position fen " + fen)
        self._send_command("go movetime %d depth %d"
                           % (max_time_ms, self.profondeur_max or 4))
        lignes = {}
        limite = time.time() + (max_time_ms / 1000.0) + 5.0
        while time.time() < limite:
            ligne = self._lire_ligne()
            if ligne is None:
                print("ENGINE : processus termine pendant la recherche")
                return None, None
            if ligne.startswith("info "):
                entree = self._analyser_multipv(ligne)
                if entree is not None:
                    rang, donnees = entree
                    lignes[rang] = donnees
            elif ligne.startswith("bestmove"):
                morceaux = ligne.split()
                secours = morceaux[1] if len(morceaux) > 1 else "(none)"
                return self._classement_coherent(lignes), secours
        print("ENGINE : timeout - pas de bestmove")
        self._send_command("stop")
        return None, None

    # Ecart de profondeur tolere entre deux lignes du meme classement.
    # Stockfish termine normalement TOUTES ses lignes MultiPV a la profondeur d
    # avant de passer a d+1 ; quand on l'arrete en plein milieu, une partie des
    # lignes est deja a d+1 et l'autre encore a d. Un pli d'ecart ne change pas
    # l'ordre. Davantage, si.
    ECART_PROFONDEUR_TOLERE = 1

    @classmethod
    def _classement_coherent(cls, lignes):
        """Le classement, debarrasse des lignes restees a une profondeur morte.

        POURQUOI (correction du 01/09, ta remarque "les bots a 1000 Elo ont
        peut-etre 400") : quand la recherche est coupee par le temps avant
        d'avoir fini son iteration - ce qui arrive tout le temps avec MultiPV a
        48 lignes - certaines lignes datent d'une profondeur bien plus faible
        que les autres. On comparait alors un coup vu a la profondeur 12 avec un
        coup vu a la profondeur 4, et on en tirait un classement. Ce classement
        etait faux, et c'est sur lui que faiblesse.py choisissait.

        Une ligne trop en retard est donc ECARTEE plutot que melangee : mieux
        vaut vingt coups correctement classes que quarante mal classes.
        """
        rangs = sorted(lignes)
        if not rangs:
            return []
        suite = [lignes[r] for r in rangs]
        profondeurs = [int(d.get("profondeur") or 0) for d in suite]
        atteinte = max(profondeurs) if profondeurs else 0
        if atteinte <= 0:
            return suite
        plancher = atteinte - cls.ECART_PROFONDEUR_TOLERE
        gardees = [d for d, p in zip(suite, profondeurs) if p >= plancher]
        # On garde au moins le premier : sans lui il n'y a plus de coup du tout.
        return gardees or suite[:1]

    @staticmethod
    def _en_details(choix, secours):
        """Met un coup classe au format attendu par le reste du jeu."""
        if choix is None:
            if not secours or secours in ("(none)", "0000"):
                return None
            return {"coup": secours, "evaluation": None, "mat": None,
                    "profondeur": 0}
        return {"coup": choix["coup"],
                "evaluation": (choix.get("cp") / 100.0
                               if choix.get("cp") is not None else None),
                "mat": choix.get("mat"),
                "profondeur": choix.get("profondeur", 0)}

    def _coup_bride(self, fen, max_time_ms):
        """Le coup d'un DEBUTANT : Stockfish classe, nous choisissons mal.

        Appelee seulement quand le classement vise est sous le minimum du
        moteur. Voir faiblesse.py pour le pourquoi et le comment.
        Le verrou est deja pris par get_best_move_details.
        """
        try:
            classes, secours = self._lire_les_coups_classes(fen, max_time_ms)
            if classes is None:
                return None
            choix = faiblesse.choisir(classes, self.elo_bride)
            if self.verbeux and choix is not None and classes:
                print("ENGINE : %d coups classes, choisi %s (le meilleur "
                      "etait %s)" % (len(classes), choix["coup"],
                                     classes[0].get("coup")))
            return self._en_details(choix, secours)
        except Exception as e:
            print("ENGINE : erreur choix bride = " + str(e))
            return None

    def meilleur_coup_honnete(self, fen, max_time_ms=1500):
        """LE MEILLEUR COUP, meme quand le moteur joue en debutant.

        POURQUOI ELLE EXISTE : l'indice (touche H) passe par le moteur de JEU.
        Sans elle, a 900 Elo, l'indice aurait souffle un coup de debutant au
        lieu du meilleur coup - l'inverse de ce qu'on attend d'un indice.
        """
        max_time_ms = max(20, int(max_time_ms))
        with self._verrou:
            if not self.est_vivant():
                return None
            if self.elo_bride is None or self.multipv_courant <= 1:
                return None            # le chemin normal donne deja le meilleur
            try:
                classes, secours = self._lire_les_coups_classes(fen,
                                                                max_time_ms)
                if classes is None:
                    return None
                return self._en_details(classes[0] if classes else None,
                                        secours)
            except Exception as e:
                print("ENGINE : erreur meilleur coup honnete = " + str(e))
                return None

    @staticmethod
    def _analyser_multipv(ligne):
        """(rang, {coup, cp, mat, profondeur}) d'une ligne 'info ... pv ...'.

        None si la ligne ne porte pas de coup (les lignes de progression du
        moteur, 'info depth 3 currmove ...', n'en portent pas).
        """
        mots = ligne.split()
        if "pv" not in mots:
            return None
        try:
            coup = mots[mots.index("pv") + 1]
        except IndexError:
            return None
        if not coup or coup in ("(none)", "0000"):
            return None
        rang = 1
        if "multipv" in mots:
            try:
                rang = int(mots[mots.index("multipv") + 1])
            except (ValueError, IndexError):
                rang = 1
        cp = mat = None
        profondeur = 0
        try:
            if "depth" in mots:
                profondeur = int(mots[mots.index("depth") + 1])
        except (ValueError, IndexError):
            profondeur = 0
        if "score" in mots:
            try:
                i = mots.index("score")
                if mots[i + 1] == "cp":
                    cp = int(mots[i + 2])
                elif mots[i + 1] == "mate":
                    mat = int(mots[i + 2])
            except (ValueError, IndexError):
                pass
        return rang, {"coup": coup, "cp": cp, "mat": mat,
                      "profondeur": profondeur}

    def _analyser_info(self, ligne):
        """Extrait score cp / score mate / depth d'une ligne 'info'."""
        mots = ligne.split()
        evaluation = mat = None
        profondeur = 0
        try:
            if "depth" in mots:
                profondeur = int(mots[mots.index("depth") + 1])
            if "score" in mots:
                i = mots.index("score")
                genre = mots[i + 1]
                valeur = int(mots[i + 2])
                if genre == "cp":
                    evaluation = valeur / 100.0
                elif genre == "mate":
                    mat = valeur
                    evaluation = 100.0 if valeur > 0 else -100.0
        except (ValueError, IndexError):
            pass
        return evaluation, mat, profondeur

    # ------------------------------------------------------------------ arret

    def quit(self):
        """Ferme Stockfish. Garantit qu'aucun processus ne survit au jeu."""
        if self.process is None:
            return
        print("ENGINE : fermeture stockfish")
        try:
            self._send_command("quit")
            self.process.wait(timeout=2)
        except Exception:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
        for flux in (self.process.stdin, self.process.stdout):
            try:
                if flux:
                    flux.close()
            except Exception:
                pass
        self.process = None
        if self in _moteurs_actifs:
            _moteurs_actifs.remove(self)
        print("ENGINE : stockfish termine")

    def __del__(self):
        try:
            self.quit()
        except Exception:
            pass
