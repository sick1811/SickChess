# mode_en_ligne.py - SickChess : une partie contre un ami, par Steam.
#
# Reprend les idees du ModeOnline de V8_TURBO_3000 (pendules arbitrees, chat,
# revanche), mais en plus simple et en plus solide :
#
#   - LA PARTIE VOYAGE EN ENTIER. Chaque coup envoie la liste complete des coups
#     joues ("e2e4 e7e5 g1f3..."). Celui qui recoit joue ce qui lui manque. Un
#     message perdu ou en double ne peut donc plus desynchroniser la partie :
#     le suivant remet tout d'aplomb. Et toutes les 3 secondes, chacun dit
#     combien de coups il a : si l'autre en a moins, il redemande la liste.
#   - LES PENDULES : pendule_reseau.py (repris tel quel de V8) - chacun est
#     seul juge de SA pendule, et c'est lui qui annonce s'il perd au temps.
#   - L'ADVERSAIRE QUITTE (bouton Menu, fenetre fermee, sortie du salon) :
#     partie gagnee pour celui qui reste.
#   - LA CONNEXION SE TAIT (coupure Internet, plantage) : on attend 60 s en le
#     disant a l'ecran. S'il revient, la partie reprend toute seule. Sinon elle
#     est declaree interrompue (nulle) : on ne sait pas qui a coupe.

import time

import chess

from chat import Chat
from pendule_reseau import PenduleReseau
from revanche import Revanche

PERIODE_ETAT = 3.0
DELAI_FORFAIT = 60.0


class ModeEnLigne:
    def __init__(self, board, transport, couleur_locale, nom_local="Toi",
                 horloge=None, numero=1):
        self.board = board
        self.transport = transport
        # Numero de la partie dans la serie (1, puis 2 apres une revanche...).
        # Chaque message le porte : un message en retard de la partie
        # precedente ne peut pas se meler a la nouvelle.
        self.numero = int(numero)
        self.nom_local = nom_local or "Toi"
        self.nom_adverse = transport.nom_adverse or "Adversaire"
        self._horloge = horloge or time.monotonic

        self.couleur_locale = chess.WHITE if couleur_locale == "blanc" else chess.BLACK
        board.ai_manager = None
        board.ia_joue_blancs = False
        board.hotseat_mode = False
        board.couleur_joueur = self.couleur_locale
        board.flipped = self.couleur_locale == chess.BLACK
        board.engine = None

        board.chat = Chat(self.nom_local, self.nom_adverse)
        board.chat.systeme("Tu joues les %s contre %s."
                           % ("Blancs" if self.couleur_locale == chess.WHITE
                              else "Noirs", self.nom_adverse))

        self.arbitre = PenduleReseau(board.timer, self.couleur_locale,
                                     self._envoyer)
        board.arbitre_pendule = self.arbitre
        self.revanche = Revanche(self.nom_adverse)

        self.coups = []                 # coups connus des deux cotes
        self._dernier_etat = 0.0
        self.message = ""
        self._message_jusqu_a = 0.0
        self.coupure_depuis = None
        # Nulle (17/10, travail p18) : proposee par l'un, acceptee par l'autre.
        self.nulle_proposee = False      # par nous, en attente
        self.nulle_recue = False         # par l'adversaire, en attente
        self._coups_a_la_proposition = -10
        self.partie_enregistree = False
        self.chemin_pgn = ""            # la partie dans parties/ (revue, Mes erreurs)

    # ------------------------------------------------------------ boucle

    def update(self):
        messages = self.transport.recevoir()
        self._envoyer_nos_coups()
        for message in messages:
            try:
                self._traiter(message)
            except Exception as souci:      # un message abime ne ferme pas le jeu
                print("[EN LIGNE] message ignore (%s) : %r" % (souci, str(message)[:120]))
        self._etat_periodique()
        self._surveiller_connexion()
        self._oublier_les_propositions()
        if self.board.game_over:
            self.enregistrer()

    def _envoyer(self, message):
        message = dict(message)
        message["partie"] = self.numero
        return self.transport.envoyer(message)

    def _liste_locale(self):
        return [coup.uci() for coup in self.board.board.move_stack]

    def _envoyer_nos_coups(self):
        locale = self._liste_locale()
        if len(locale) > len(self.coups) and locale[:len(self.coups)] == self.coups:
            self.coups = locale
            self._envoyer_liste()
            self._envoyer(self.arbitre.paquet())

    def _envoyer_liste(self):
        self._envoyer({"type": "coups", "coups": list(self.coups)})

    def _etat_periodique(self):
        maintenant = self._horloge()
        if maintenant - self._dernier_etat >= PERIODE_ETAT:
            self._dernier_etat = maintenant
            self._envoyer({"type": "etat",
                                    "nb": len(self.board.board.move_stack)})
        paquet = self.arbitre.battement()
        if paquet is not None and not self.board.game_over:
            self._envoyer(paquet)

    def _surveiller_connexion(self):
        t = self.transport
        if t.parti:
            self.revanche.adversaire_parti()
            if not self.board.game_over:
                gagnant = "1-0" if self.couleur_locale == chess.WHITE else "0-1"
                self.board.terminer_partie("%s a quitte la partie" % self.nom_adverse,
                                           gagnant)
            return
        if t.perdu():
            if self.coupure_depuis is None:
                self.coupure_depuis = self._horloge()
            attente = self._horloge() - self.coupure_depuis
            if not self.board.game_over:
                reste = max(0, int(DELAI_FORFAIT - attente))
                self.afficher("Connexion perdue avec %s... on l'attend encore %d s"
                              % (self.nom_adverse, reste), 1500)
                if attente >= DELAI_FORFAIT:
                    self.board.terminer_partie(
                        "Connexion perdue avec %s : partie interrompue"
                        % self.nom_adverse, "1/2-1/2")
        elif self.coupure_depuis is not None:
            self.coupure_depuis = None
            self.afficher("%s est de retour." % self.nom_adverse, 4000)

    # ------------------------------------------------------------ messages

    def _traiter(self, message):
        genre = message.get("type", "")
        if message.get("partie", self.numero) != self.numero:
            return                      # reste d'une autre partie de la serie

        if genre == "coups":
            self._recevoir_coups(message.get("coups") or [])

        elif genre == "etat":
            if int(message.get("nb", 0)) < len(self.board.board.move_stack):
                self._envoyer_liste()           # il lui manque des coups
            elif int(message.get("nb", 0)) > len(self.board.board.move_stack):
                self._envoyer({"type": "renvoyer"})

        elif genre == "renvoyer":
            self._envoyer_liste()

        elif genre == "abandon":
            gagnant = "1-0" if self.couleur_locale == chess.WHITE else "0-1"
            self.board.terminer_partie("%s a abandonne" % self.nom_adverse, gagnant)

        elif genre == "pendule":
            self.arbitre.appliquer(message)

        elif genre == "temps_ecoule":
            perdant = self.arbitre.temps_ecoule_annonce(message)
            if perdant is not None and not self.board.game_over:
                gagnant = "0-1" if perdant == chess.WHITE else "1-0"
                camp = "BLANCS" if perdant == chess.WHITE else "NOIRS"
                self.board.terminer_partie("TEMPS ÉCOULÉ - les %s perdent au temps"
                                           % camp, gagnant)

        elif genre == "nulle":
            action = message.get("action")
            if action == "proposer" and not self.board.game_over:
                self.nulle_recue = True
                self._nb_a_la_reception = len(self.board.board.move_stack)
                self.afficher("%s propose la nulle : clique NULLE pour accepter."
                              % self.nom_adverse, 15000)
                self.board.chat.systeme("%s propose la nulle." % self.nom_adverse)
            elif action == "accepter" and self.nulle_proposee and not self.board.game_over:
                self.nulle_proposee = False
                self.board.terminer_partie("Nulle d'un commun accord", "1/2-1/2")
            elif action == "refuser":
                self.nulle_proposee = False
                self.afficher("%s refuse la nulle." % self.nom_adverse)

        elif genre == "chat":
            self.board.chat.recevoir(self.nom_adverse, message.get("texte", ""))

        elif genre == "revanche":
            reponse = self.revanche.recevoir(message)
            if reponse is not None:
                self._envoyer(reponse)
            if self.revanche.a_repondre():
                self.afficher("%s demande une revanche." % self.nom_adverse, 15000)

    def _recevoir_coups(self, recue):
        recue = [str(c) for c in recue][:600]
        locale = self._liste_locale()
        if len(recue) <= len(locale):
            return                               # rien de neuf (ou en retard)
        if recue[:len(locale)] != locale:
            print("[EN LIGNE] parties differentes : %s / %s" % (locale, recue))
            self.afficher("Les deux plateaux ne sont plus d'accord. Ce n'est pas "
                          "normal : signale-le.", 8000)
            return
        for uci in recue[len(locale):]:
            try:
                coup = chess.Move.from_uci(uci)
            except ValueError:
                coup = None
            if coup is None or coup not in self.board.board.legal_moves:
                print("[EN LIGNE] coup refuse : %r" % uci)
                break
            self.board.make_move(coup)
        self.coups = self._liste_locale()

    # ------------------------------------------------------------ actions

    def abandonner(self):
        """Appele quand le joueur local a clique ABANDONNER."""
        self._envoyer({"type": "abandon"})

    def nulle(self):
        """Bouton NULLE : accepte la proposition recue, sinon en propose une
        (au plus une fois tous les deux coups)."""
        if self.board.game_over:
            return None
        if self.nulle_recue:
            self.nulle_recue = False
            self._envoyer({"type": "nulle", "action": "accepter"})
            self.board.terminer_partie("Nulle d'un commun accord", "1/2-1/2")
            return "acceptee"
        nb = len(self.board.board.move_stack)
        if self.nulle_proposee or nb - self._coups_a_la_proposition < 2:
            self.afficher("Nulle déjà proposée : attends deux coups.")
            return None
        self.nulle_proposee = True
        self._coups_a_la_proposition = nb
        self._envoyer({"type": "nulle", "action": "proposer"})
        self.afficher("Nulle proposée à %s." % self.nom_adverse)
        return "proposee"

    def _oublier_les_propositions(self):
        """Un coup joue annule une proposition de nulle en attente."""
        nb = len(self.board.board.move_stack)
        if self.nulle_recue and nb > getattr(self, "_nb_a_la_reception", nb):
            self.nulle_recue = False
        if self.nulle_proposee and nb > self._coups_a_la_proposition + 1:
            self.nulle_proposee = False

    def enregistrer(self):
        """La partie finie entre dans « Mes parties » (avec revue), sans
        toucher au profil ni a l'Elo. Une seule fois."""
        if self.partie_enregistree or not self.board.game_over:
            return ""
        self.partie_enregistree = True
        try:
            import historique_parties
            blanc = self.couleur_locale == chess.WHITE
            blancs, noirs = (self.nom_local, self.nom_adverse) if blanc \
                else (self.nom_adverse, self.nom_local)
            try:
                cadence = self.board.timer.description_cadence()
            except Exception:
                cadence = ""
            raison = self.board.game_over_reason or ""
            try:
                import succes
                succes.debloquer("en_ligne")
                gagne = self.board.result == ("1-0" if blanc else "0-1")
                succes.verifier({"victoire_mat": gagne and "MAT" in raison.upper()})
            except Exception as e2:
                print("[SUCCES] %s" % e2)
            self.chemin_pgn = historique_parties.enregistrer(
                self.board.move_history, blancs, noirs, self.board.result or "*",
                cadence=cadence, camp_du_joueur="blanc" if blanc else "noir",
                raison=raison, mode="en_ligne")
            return self.chemin_pgn
        except Exception as e:
            print("[EN LIGNE] partie non enregistree : %s" % e)
            return ""

    def envoyer_chat(self, texte):
        texte = str(texte).strip()[:160]
        if texte:
            self._envoyer({"type": "chat", "texte": texte})

    def demander_revanche(self):
        message = self.revanche.demander()
        if message is not None:
            self._envoyer(message)

    def refuser_revanche(self):
        message = self.revanche.refuser()
        if message is not None:
            self._envoyer(message)

    def revanche_acceptee(self):
        return self.revanche.acceptee()

    def couleur_revanche(self):
        """Les couleurs s'inversent pour la revanche."""
        return "noir" if self.couleur_locale == chess.WHITE else "blanc"

    def quitter(self):
        """Le joueur retourne au menu. En pleine partie, ca vaut abandon."""
        if not self.board.game_over:
            self.abandonner()

    # ------------------------------------------------------------ bandeau

    def afficher(self, texte, duree_ms=6000):
        self.message = texte
        self._message_jusqu_a = self._horloge() + duree_ms / 1000.0

    def message_actif(self):
        if self.message and self._horloge() < self._message_jusqu_a:
            return self.message
        return None

    def arreter(self):
        self.board.arbitre_pendule = None
