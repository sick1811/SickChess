# background_ai.py - V6 : Stockfish reflechit dans son propre thread
#
# CE QUI CHANGE PAR RAPPORT A V5 (bugs C4 et M1 du rapport) :
#   1. TEMPS DE REFLEXION ALEATOIRE (ta demande n°1).
#      En V5 : get_best_move(fen, 150) - toujours 150 ms, jamais autre chose.
#      En V6 : chaque coup recoit un budget tire au hasard entre deux bornes,
#      module par la position : ouverture rapide, position compliquee plus lente,
#      coup force quasi immediat, et de temps en temps une longue reflexion.
#   2. LES COUPS DE L'IA PASSENT PAR make_move().
#      En V5 : board.push(move) en direct -> les prises de l'IA n'etaient pas
#      comptees, ses coups n'entraient pas dans l'historique, la moitie des sons
#      ne se declenchait pas. Mesure sur une partie complete : 126 demi-coups
#      joues, 63 enregistres, 20 pieces prises, 8 comptees.
#      En V6 : chessboard.make_move(...) est appele comme pour un coup humain.
#   3. Le coup calcule est verifie avant d'etre joue : si la position a change
#      entre-temps (partie abandonnee, retour au menu), il est jete au lieu
#      d'etre applique dans le vide.
#   4. stop() permet d'arreter proprement la reflexion en fin de partie.
#
# AUCUNE FONCTION SUPPRIMEE : __init__, start_thinking, _ai_worker et update
# sont conservees, memes noms. Les nouveaux parametres de __init__ ont tous une
# valeur par defaut : BackgroundAI(board, engine) fonctionne toujours.

import random
import threading
import time

import chess

import freestyle
import rythme


class BackgroundAI:
    def __init__(self, chessboard, engine,
                 temps_min_ms=700, temps_max_ms=5000, humain=True,
                 temps_moteur_max_ms=1500):
        self.chessboard = chessboard
        self.engine = engine
        self.thread = None
        self.lock = threading.Lock()
        self.is_thinking = False
        self.pending_ai_move = None

        # --- reglage du temps de reflexion ---
        self.temps_min_ms = max(50, int(temps_min_ms))
        self.temps_max_ms = max(self.temps_min_ms, int(temps_max_ms))
        self.humain = bool(humain)
        # Temps reellement accorde au calcul. Au-dela, Stockfish ne joue pas
        # mieux a ces niveaux : le reste du budget est une pause d'attente.
        self.temps_moteur_max_ms = max(50, int(temps_moteur_max_ms))

        # --- etat interne ---
        self._stop = False
        self.fen_au_moment_du_calcul = None
        self.derniere_evaluation = None

        # V7.2 - LA CADENCE COMMANDE LE RYTHME (ta remarque : "rapidite
        # stockfish pas adapte en bullet"). On regarde la pendule du moteur
        # avant chaque coup : en 1+0 il joue en une demi-seconde, en 30+20 il
        # prend ses huit secondes. Sans pendule, on garde exactement l'ancien
        # comportement, avec les bornes de config.json.
        self.suivre_la_pendule = True

    # ------------------------------------------------------------------ pilotage

    def start_thinking(self):
        with self.lock:
            if self._stop or self.is_thinking:
                return False
            if self.thread is not None and self.thread.is_alive():
                return False
            self.is_thinking = True
        self.thread = threading.Thread(target=self._ai_worker, daemon=True)
        self.thread.start()
        return True

    def est_en_train_de_reflechir(self):
        with self.lock:
            return self.is_thinking

    def a_un_coup_en_attente(self):
        """Un coup est calcule et attend d'etre joue.

        V7.2 : sans ce garde-fou, on relancait une reflexion sur la position
        d'AVANT pendant qu'un coup deja pret attendait - et ce nouveau calcul
        etait forcement jete ensuite.
        """
        with self.lock:
            return self.pending_ai_move is not None

    def stop(self):
        """Arrete la reflexion en cours (fin de partie, retour au menu)."""
        self._stop = True
        with self.lock:
            self.pending_ai_move = None
        thread = self.thread
        if thread is not None and thread.is_alive():
            # 24/10 (« quitter une partie est long ») : on interrompt la
            # recherche de Stockfish (« stop ») au lieu d'attendre qu'elle
            # finisse : le fil voit _stop et jette le coup.
            interrompre = getattr(self.engine, "interrompre", None)
            if interrompre is not None:
                try:
                    interrompre()
                except Exception:
                    pass
            thread.join(timeout=2.0)

    def reprendre(self):
        """Annule un stop() precedent (nouvelle partie)."""
        self._stop = False

    # ------------------------------------------- temps de reflexion "humain"

    def _temps_de_la_pendule(self, board):
        """Ce qu'il reste au MOTEUR a sa pendule, en secondes. None si pas de pendule.

        On lit la vraie horloge de la partie : c'est la seule facon d'avoir un
        rythme qui colle a la cadence choisie, du bullet a la partie longue.
        """
        if not self.suivre_la_pendule:
            return None, 0
        pendule = getattr(self.chessboard, "timer", None)
        if pendule is None or not getattr(pendule, "active", False):
            return None, 0
        try:
            restant = pendule.secondes_restantes(board.turn == chess.WHITE)
            increment = getattr(pendule, "increment", 0) or 0
            if not restant or restant <= 0:
                return None, 0
            return float(restant), float(increment)
        except Exception:
            return None, 0

    def bornes_du_moment(self, board):
        """Les bornes du tirage, adaptees a la cadence. Publique : testable."""
        restant, increment = self._temps_de_la_pendule(board)
        if restant is None:
            return self.temps_min_ms, self.temps_max_ms, None
        mini, maxi = rythme.bornes_ms(restant, increment,
                                      len(board.move_stack),
                                      self.temps_min_ms, self.temps_max_ms)
        return mini, maxi, restant

    def _tirer_temps_de_reflexion(self, board):
        """Budget en millisecondes pour ce coup precis.

        Le hasard seul donnerait un rythme mecanique. On le module donc par la
        position, comme le ferait un joueur : vite en ouverture, vite quand il
        n'y a qu'un coup, plus longtemps quand la position est riche.

        V7.2 : les bornes ne sont plus fixes. Elles viennent de la PENDULE quand
        il y en a une, donc une partie d'une minute et une partie de trente
        minutes n'ont plus du tout le meme rythme.
        """
        bas, haut, restant = self.bornes_du_moment(board)
        if not self.humain:
            return bas

        coups_possibles = board.legal_moves.count() if hasattr(board.legal_moves, "count") \
            else len(list(board.legal_moves))
        demi_coups = len(board.move_stack)

        # 1. Un coup force ne demande pas de reflexion.
        if coups_possibles <= 1:
            plafond = min(600, max(120, bas)) if restant else 600
            return int(random.uniform(min(250, plafond), plafond))

        # 2. Tirage de base, biaise vers le bas (la plupart des coups sont rapides).
        base = bas + (haut - bas) * (random.random() ** 1.9)

        # 3. Les premiers coups sont joues de memoire.
        if demi_coups < 8:
            base *= random.uniform(0.30, 0.55)
        elif demi_coups < 16:
            base *= random.uniform(0.55, 0.85)

        # 4. Position riche = plus de temps ; position pauvre = moins.
        base *= 0.75 + min(1.0, coups_possibles / 38.0) * 0.6

        # 5. L'echec force a repondre vite.
        if board.is_check():
            base *= random.uniform(0.45, 0.8)

        # 5 bis. SickChess 17/10 (travail p08) : on regarde la position comme un
        # joueur. Reprendre une piece qu'on vient de perdre : presque reflexe.
        # Pieces menacees, prises et echecs partout : on s'arrete.
        try:
            if rythme.est_une_reprise_evidente(board) and random.random() < 0.7:
                base *= random.uniform(0.30, 0.55)
            else:
                base *= rythme.facteur_de_complexite(board)
                if 16 <= demi_coups <= 70:
                    base *= 1.12          # le milieu de partie se pense
        except Exception as e:
            print("[BACKGROUND AI] rythme : %s" % e)

        # 6. De temps en temps, une vraie longue reflexion (8 %).
        if random.random() < 0.08:
            base *= random.uniform(1.6, 2.4)
        # ... et parfois une reponse du tac au tac (12 %).
        elif random.random() < 0.12:
            base *= random.uniform(0.25, 0.45)

        # Le plafond suit lui aussi la cadence : en bullet, "une longue
        # reflexion" ne peut pas depasser une seconde.
        plancher = 200 if restant is None else max(100, int(bas * 0.5))
        # Personne ne joue en 0,1 s quand il lui reste plus d'une minute.
        if restant is None or restant > 60:
            plancher = max(plancher, 350)
        if restant is None:
            plafond = self.temps_max_ms * 2.2
        else:
            # Meme une "longue reflexion" reste dans le plafond de la cadence :
            # personne n'attend douze secondes devant son ecran.
            plafond = min(haut * 1.3, rythme.BUDGET_PLAFOND_MS)
        return int(max(plancher, min(base, plafond)))

    def _attendre(self, secondes):
        """Pause interruptible : stop() ne reste jamais bloque."""
        fin = time.time() + secondes
        while time.time() < fin:
            if self._stop:
                return False
            time.sleep(min(0.05, max(0.0, fin - time.time())))
        return True

    # ------------------------------------------------------------------ calcul

    # Ce que le classement d'un debutant a le droit de prendre sur le budget.
    # 0.80 : il reste toujours de quoi faire une vraie pause apres, sinon le
    # rythme humain disparait et le bot repond du tac au tac.
    PART_DU_BUDGET_POUR_CLASSER = 0.80
    PLAFOND_CLASSEMENT_MS = 3000

    def _temps_pour_classer(self, budget_ms, temps_moteur):
        """Plus de temps moteur quand le bot est BRIDE, sans ralentir la partie.

        POURQUOI (correction du 01/09, ta remarque "les bots a 1000 Elo ont
        peut-etre 400") :
          Sous 1320 Elo, le coup n'est plus choisi par Stockfish mais par
          faiblesse.py, a partir du CLASSEMENT de 16 a 48 coups. Ce classement
          demande beaucoup plus de calcul qu'une simple recherche du meilleur
          coup - et il ne servait a rien de le faire vite, puisqu'il etait
          coupe avant d'etre fini, donc faux.

          Or le temps etait deja la : le bot calcule pendant `temps_moteur`
          (1,5 s au maximum), puis DORT tout le reste du budget pour avoir l'air
          humain. On prend donc sur la pause, pas sur ta patience : le coup
          arrive exactement au meme moment qu'avant, mais il est classe
          correctement.

        Le moteur non bride, lui, ne change pas d'un millimetre.
        """
        try:
            if getattr(self.engine, "elo_bride", None) is None:
                return temps_moteur
        except Exception:
            return temps_moteur
        voulu = int(budget_ms * self.PART_DU_BUDGET_POUR_CLASSER)
        return max(int(temps_moteur), min(voulu, self.PLAFOND_CLASSEMENT_MS))

    def _elo_du_bot(self):
        """Le classement auquel le bot est regle, quel que soit le chemin."""
        for attribut in ("elo_bride", "elo_courant"):
            valeur = getattr(self.engine, attribut, None)
            if valeur:
                try:
                    return int(valeur)
                except (TypeError, ValueError):
                    pass
        return 1200

    def _coup_du_livre(self, board):
        """Un coup de theorie, ou None quand le bot doit calculer.

        Se coupe par "bot_livre_ouvertures": false dans config.json.
        """
        if not self._livre_demande():
            return None
        try:
            import ouvertures
            sans = self._sans_joues(board)
            if sans is None:
                return None
            choix = ouvertures.coup_du_livre(sans, self._elo_du_bot())
            if not choix:
                return None
            return board.parse_san(choix)
        except Exception:
            # Le livre ne doit JAMAIS empecher le bot de jouer : au moindre
            # doute on retombe sur le moteur, qui lui ne se trompe pas.
            return None

    @staticmethod
    def _sans_joues(board):
        """Les coups de la partie en notation courte, comme dans le livre."""
        try:
            plateau = chess.Board()
            sans = []
            for coup in board.move_stack:
                sans.append(plateau.san(coup))
                plateau.push(coup)
            # Une partie partie d'une position chargee n'a pas de theorie.
            if plateau.fen() != board.fen():
                return None
            return sans
        except Exception:
            return None

    _LIVRE_DEMANDE = None

    @classmethod
    def _livre_demande(cls):
        if cls._LIVRE_DEMANDE is not None:
            return cls._LIVRE_DEMANDE
        cls._LIVRE_DEMANDE = True
        try:
            import json
            import os
            for dossier in (os.getcwd(),
                            os.path.dirname(os.path.abspath(__file__))):
                chemin = os.path.join(dossier, "config.json")
                if os.path.exists(chemin):
                    with open(chemin, "r", encoding="utf-8") as f:
                        cls._LIVRE_DEMANDE = bool(
                            json.load(f).get("bot_livre_ouvertures", True))
                    break
        except Exception:
            cls._LIVRE_DEMANDE = True
        return cls._LIVRE_DEMANDE

    def _ai_worker(self):
        try:
            if self._stop:
                return
            board = self.chessboard.board
            fen = board.fen()
            plateau_du_calcul = board.copy(stack=False)  # lire le coup rendu
            budget_ms = self._tirer_temps_de_reflexion(board)
            # V7.2 : le temps de CALCUL suit le budget. En bullet on ne laisse
            # pas le moteur chercher une seconde et demie sur un coup qui doit
            # partir en un demi-quart de seconde.
            temps_moteur = rythme.temps_moteur_ms(budget_ms,
                                                  self.temps_moteur_max_ms)
            temps_moteur = self._temps_pour_classer(budget_ms, temps_moteur)

            depart = time.time()
            details = None
            trait_aux_blancs = board.turn == chess.WHITE
            # V7.2 (03/09) - LE LIVRE D'OUVERTURES DU BOT (ta demande).
            # Avant, il choisissait TOUS ses coups dans le classement de
            # Stockfish, y compris les trois premiers - et a profondeur fixe,
            # ce classement ne change jamais : il jouait toujours les memes
            # debuts. Maintenant il pioche dans les 3 810 ouvertures, avec un
            # tirage pondere, et il en sort d'autant plus tot qu'il est faible.
            # Bonus : aucun calcul moteur dans l'ouverture, donc rien a
            # attendre. La pause du rythme humain, elle, ne change pas.
            coup_de_livre = self._coup_du_livre(board)
            if coup_de_livre is not None:
                best_uci = coup_de_livre.uci()
            # 31/10 : le moteur doit savoir si la PARTIE est Freestyle. La FEN
            # seule ne suffit pas (n° 77 : roi en e1, droits « KQkq ») : il
            # rendait e1g1, absent du plateau Freestyle, et ne jouait plus.
            elif hasattr(self.engine, "get_best_move_details"):
                details = self.engine.get_best_move_details(
                    fen, temps_moteur, **freestyle.options_moteur(board))
                best_uci = details["coup"] if details else None
            else:
                best_uci = self.engine.get_best_move(
                    fen, temps_moteur, **freestyle.options_moteur(board))

            if not best_uci or best_uci == "(none)":
                return

            # Le reste du budget est une pause : c'est ce qui donne au moteur
            # un rythme humain sans lui faire perdre de la force de calcul.
            reste = budget_ms / 1000.0 - (time.time() - depart)
            if reste > 0 and not self._attendre(reste):
                return

            move = freestyle.lire_coup(plateau_du_calcul, best_uci)
            with self.lock:
                if self._stop:
                    return
                self.pending_ai_move = move
                self.fen_au_moment_du_calcul = fen
                if details and details.get("evaluation") is not None:
                    # Stockfish donne le score du point de vue du joueur au trait.
                    # On le ramene au point de vue des BLANCS, convention de la
                    # barre d'avantage et du PGN.
                    ev = float(details["evaluation"])
                    self.derniere_evaluation = ev if trait_aux_blancs else -ev
                else:
                    self.derniere_evaluation = None
        except Exception as e:
            print("[BACKGROUND AI] erreur pendant la reflexion : " + str(e))
        finally:
            with self.lock:
                self.is_thinking = False

    # ------------------------------------------------------------------ jeu

    def update(self):
        """Joue le coup calcule, s'il est encore valable. Renvoie True si joue."""
        with self.lock:
            move = self.pending_ai_move
            fen_calcul = self.fen_au_moment_du_calcul
            self.pending_ai_move = None
            self.fen_au_moment_du_calcul = None

        if move is None:
            return False
        if getattr(self.chessboard, "game_over", False):
            return False

        # La position a-t-elle bouge pendant que le moteur calculait ?
        if fen_calcul is not None and fen_calcul != self.chessboard.board.fen():
            print("[BACKGROUND AI] position modifiee pendant le calcul, coup ignore")
            return False

        if move not in self.chessboard.board.legal_moves:
            print("[BACKGROUND AI] coup " + move.uci() + " devenu illegal, ignore")
            return False

        # CORRECTION C4 : on passe par le meme chemin qu'un coup humain, donc
        # historique, pieces capturees, animation, highlights et sons suivent.
        self.chessboard.make_move(move, self.engine)

        # L'evaluation a deja ete calculee par le moteur : on la garde pour la
        # barre d'avantage du replay et pour l'export PGN, sans rien recalculer.
        historique = getattr(self.chessboard, "move_history", None)
        if historique is not None and self.derniere_evaluation is not None:
            historique.set_evaluation(historique.get_move_count() - 1,
                                      self.derniere_evaluation)
        return True
