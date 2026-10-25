# analyse_de_fond.py - SickChess 25/10 (travail p25, « Je veux » de Julien) :
# l'analyse des parties en tache de fond quand le PC ne fait rien.
#
# Au menu et pendant les Problemes, les parties de « Mes parties » qui n'ont pas
# encore d'analyse (importees, jouees a deux, revue jamais ouverte...) se
# calculent toutes seules, la plus recente d'abord. Quand on ouvre leur revue,
# elle est deja prete (pastille « Revue prête » dans Mes parties).
#
# Leger par construction :
#   - UN seul Stockfish, a lui (pas ceux de la revue : la liberation au repos
#     du menu ne le touche pas), en priorite basse, 1/4 des coeurs (1 sur un
#     petit PC), 256 Mo de hachage ;
#   - en pause des qu'on lance une partie, une revue, l'analyse libre... : le
#     Stockfish est ferme, mais le travail deja fait reste en memoire et la
#     revue de cette partie le reprend (AnalyseurPartie.reprendre_de) ;
#   - la meme puissance que la revue : le fichier .analyse.json ecrit ici est
#     celui que la revue relit (sinon elle referait tout).
# Reglage « analyse_de_fond » de config.json (vrai par defaut).

import os
import threading
import time

HACHAGE_MO = 256


def _chemin_cache(chemin_pgn):
    return os.path.splitext(chemin_pgn)[0] + ".analyse.json"


def revue_prete(chemin_pgn):
    """Une analyse est enregistree a cote de la partie (Mes parties)."""
    return bool(chemin_pgn) and os.path.exists(_chemin_cache(chemin_pgn))


class AnalyseDeFond:
    def __init__(self, chemin_stockfish, config=None, lister=None, fabriquer=None,
                 threads=None):
        self.chemin = chemin_stockfish
        self.config = config if config is not None else {}
        self._lister = lister            # les tests passent le leur
        self._fabriquer = fabriquer      # idem (faux moteur)
        self._threads = threads
        self._verrou = threading.Lock()
        self._fil = None
        self._pause = threading.Event()
        self._moteur = None
        self._analyseurs = {}            # chemin du pgn -> AnalyseurPartie (partielle)
        self._ratees = set()             # parties illisibles / en erreur : on ne boucle pas
        self._rien_a_faire_depuis = None
        self.en_cours = None             # chemin de la partie analysee en ce moment
        self.terminees = 0               # parties analysees depuis le lancement

    # ---------------------------------------------------------------- reglages

    def actif(self):
        return bool(self.config.get("analyse_de_fond", True)) and bool(
            self.chemin or self._fabriquer)

    def _puissance(self):
        import analyse_partie
        return analyse_partie.puissance_de(self.config)

    def _nombre_de_threads(self):
        if self._threads:
            return int(self._threads)
        try:
            import petit_pc
            if petit_pc.est_petit():
                return 1
        except Exception:
            pass
        return max(1, (os.cpu_count() or 2) // 4)

    # ---------------------------------------------------------------- commande

    def reprendre(self):
        """Au menu / dans les Problemes, a chaque image : relance le travail
        s'il est arrete. Ne fait rien (et ne coute rien) s'il tourne deja."""
        if not self.actif():
            return False
        with self._verrou:
            if self._fil is not None and self._fil.is_alive():
                return False
            # Rien a faire au dernier passage : on ne relit la liste qu'une fois
            # par minute (une partie finie entre-temps sera vue).
            if self._rien_a_faire_depuis is not None \
                    and time.time() - self._rien_a_faire_depuis < 60:
                return False
            self._pause.clear()
            self._fil = threading.Thread(target=self._travailler, daemon=True,
                                         name="analyse-de-fond")
            self._fil.start()
            return True

    def pause(self, attendre=1.0):
        """Une partie, une revue, l'analyse libre... commence : on rend tout le
        processeur. Le travail deja fait est garde."""
        self._pause.set()
        self._rien_a_faire_depuis = None
        fil = self._fil
        en_cours = self._analyseurs.get(self.en_cours) if self.en_cours else None
        if en_cours is not None:
            en_cours.arreter()
        if fil is not None and fil.is_alive():
            fil.join(attendre)
        self._fermer_le_moteur()

    def fermer(self):
        """A la fermeture du jeu."""
        self.pause(attendre=0.5)
        self._analyseurs.clear()

    def prendre(self, chemin_pgn):
        """La revue de cette partie s'ouvre : l'analyse partielle faite ici
        (ou None). Elle n'est plus continuee en fond."""
        self.pause()
        return self._analyseurs.pop(chemin_pgn, None)

    def nouvelle_partie(self):
        """Une partie vient d'etre enregistree : a regarder au prochain menu."""
        self._rien_a_faire_depuis = None

    # ---------------------------------------------------------------- travail

    def _parties(self):
        if self._lister is not None:
            return self._lister()
        import historique_parties
        return historique_parties.lister()

    def _suivante(self):
        """(chemin, analyseur) de la plus recente partie sans analyse, ou None."""
        import historique_parties
        from analyse_partie import AnalyseurPartie
        for partie in self._parties():
            chemin = partie.get("chemin", "")
            if not chemin or chemin in self._ratees:
                continue
            if chemin in self._analyseurs:
                return chemin, self._analyseurs[chemin]
            if revue_prete(chemin):
                # Deja un fichier : la revue le relira (s'il est trop faible
                # pour les reglages actuels, c'est elle qui le refera).
                continue
            donnees, erreur = historique_parties.lire_partie(chemin)
            if erreur or not donnees or len(donnees.get("coups") or []) < 2:
                self._ratees.add(chemin)
                continue
            analyseur = AnalyseurPartie(donnees["fen"], donnees["coups"], None,
                                        self._puissance(), moteur=_MoteurDifere(self),
                                        fichier_cache=_chemin_cache(chemin))
            if analyseur.terminee():
                continue
            self._analyseurs[chemin] = analyseur
            return chemin, analyseur
        return None

    def _travailler(self):
        try:
            while not self._pause.is_set():
                suivante = self._suivante()
                if suivante is None:
                    self._rien_a_faire_depuis = time.time()
                    break
                chemin, analyseur = suivante
                self.en_cours = chemin
                print("[FOND] analyse de %s" % os.path.basename(chemin))
                analyseur.erreur = None          # celle d'une pause precedente
                analyseur.demarrer()
                while not self._pause.is_set() and analyseur.en_cours:
                    time.sleep(0.2)
                if analyseur.terminee():
                    self._analyseurs.pop(chemin, None)
                    self.terminees += 1
                    print("[FOND] revue prete : %s" % os.path.basename(chemin))
                elif analyseur.erreur and not self._pause.is_set():
                    self._ratees.add(chemin)
                    self._analyseurs.pop(chemin, None)
        except Exception as e:
            print("[FOND] arret : %s" % e)
        finally:
            self.en_cours = None
            self._fermer_le_moteur()

    # ---------------------------------------------------------------- moteur

    def moteur(self):
        """Le Stockfish de l'analyse de fond, cree a la demande."""
        if self._moteur is not None and _vivant(self._moteur):
            return self._moteur
        if self._pause.is_set():
            return None
        if self._fabriquer is not None:
            self._moteur = self._fabriquer()
        else:
            from engine import StockfishEngine
            self._moteur = StockfishEngine(self.chemin)
            try:
                self._moteur.configurer_pour_analyse(self._nombre_de_threads(), HACHAGE_MO)
            except Exception as e:
                print("[FOND] configuration de Stockfish impossible : %s" % e)
            try:
                import moteurs
                moteurs._priorite_basse(self._moteur)
            except Exception:
                pass
        return self._moteur

    def _fermer_le_moteur(self):
        moteur, self._moteur = self._moteur, None
        if moteur is not None:
            try:
                moteur.quit()
            except Exception:
                pass


def _vivant(moteur):
    try:
        return bool(moteur.est_vivant())
    except Exception:
        return False


class _MoteurDifere:
    """Ce que l'AnalyseurPartie croit etre son moteur : il cree le vrai
    Stockfish de l'analyse de fond au premier besoin (et le recree apres une
    pause). arreter() de l'analyseur passe par interrompre()."""

    def __init__(self, fond):
        self._fond = fond

    def _vrai(self):
        moteur = self._fond.moteur()
        if moteur is None:
            raise RuntimeError("analyse de fond en pause")
        return moteur

    def analyser_position(self, *args, **kwargs):
        return self._vrai().analyser_position(*args, **kwargs)

    def interrompre(self):
        moteur = self._fond._moteur
        if moteur is not None and hasattr(moteur, "interrompre"):
            return moteur.interrompre()
        return False

    def est_vivant(self):
        return True

    def __getattr__(self, nom):
        return getattr(self._vrai(), nom)
