# reseau_transport.py - SickChess : le tuyau entre les deux joueurs.
#
# Le mode en ligne ne sait pas COMMENT les messages voyagent : il appelle
# envoyer({...}) et recevoir(). Deux tuyaux existent :
#
#   TransportSteam : le vrai, celui du jeu vendu. Les messages passent par le
#                    relais de Steam, entre les deux membres d'un salon.
#   TransportLocal : une connexion TCP sur ce PC (127.0.0.1). Sert a tester le
#                    multijoueur avec deux fenetres du jeu ouvertes cote a cote,
#                    sans Steam - et aux tests automatiques.
#
# Ce que fait la classe commune Transport, pour les deux :
#   - les messages sont des dictionnaires, transformes en JSON ;
#   - "bonjour" : chacun se presente (nom, version du protocole) jusqu'a ce que
#     l'autre ait repondu. C'est ce qui fait passer l'etat a "connecte" ;
#   - "ping" toutes les 2 secondes : si on n'entend plus rien depuis 12 s, la
#     connexion est consideree comme perdue (plantage, coupure Internet) ;
#   - "au_revoir" : l'autre a quitte proprement (bouton Menu, fenetre fermee).

import json
import socket
import time

VERSION_PROTOCOLE = 1
PERIODE_BONJOUR = 1.0
PERIODE_PING = 2.0
DELAI_SILENCE = 12.0
TAILLE_MAX = 64 * 1024

# Messages geres ici, jamais transmis au mode en ligne.
_INTERNES = ("bonjour", "ping", "au_revoir")


class Transport:
    """Base commune. Les sous-classes fournissent _envoyer_octets,
    _lire_octets, _entretien et _fermer."""

    def __init__(self, nom_local="Joueur", horloge=None):
        self.nom_local = (nom_local or "Joueur")[:24]
        self.nom_adverse = ""
        self.hote = False
        self.erreur = ""
        self.parti = False                # l'autre a quitte
        self.ferme = False
        self.bonjour_recu = False
        self._horloge = horloge or time.monotonic
        self._dernier_recu = None
        self._dernier_bonjour = -999.0
        self._dernier_ping = -999.0

    # ------------------------------------------------------ a fournir

    def _pair_connu(self):
        """Sait-on a qui parler ? (adversaire arrive dans le salon / socket ouverte)"""
        return False

    def _envoyer_octets(self, octets):
        return False

    def _lire_octets(self):
        return []

    def _entretien(self):
        pass

    def _fermer(self):
        pass

    # ------------------------------------------------------ etat

    def connecte(self):
        return self.bonjour_recu and not self.parti and not self.ferme \
            and not self.perdu()

    def silence(self):
        """Secondes depuis le dernier message recu (0 si jamais connecte)."""
        if self._dernier_recu is None:
            return 0.0
        return max(0.0, self._horloge() - self._dernier_recu)

    def perdu(self):
        return self.bonjour_recu and not self.parti \
            and self.silence() > DELAI_SILENCE

    def etat(self):
        """Une phrase pour l'ecran."""
        if self.erreur:
            return self.erreur
        if self.parti:
            return "%s a quitte." % (self.nom_adverse or "L'adversaire")
        if self.perdu():
            return "Connexion perdue avec %s..." % (self.nom_adverse or "l'adversaire")
        if self.bonjour_recu:
            return "Connecté à %s." % self.nom_adverse
        if self._pair_connu():
            return "Connexion en cours..."
        return "En attente d'un adversaire..."

    # ------------------------------------------------------ envoi / reception

    def envoyer(self, message):
        """Envoie un dictionnaire. True si le message est parti."""
        if self.ferme or not self._pair_connu():
            return False
        try:
            octets = json.dumps(message, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError) as souci:
            print("[RESEAU] message impossible a envoyer : %s" % souci)
            return False
        if len(octets) > TAILLE_MAX:
            print("[RESEAU] message trop gros (%d octets)" % len(octets))
            return False
        try:
            return bool(self._envoyer_octets(octets))
        except OSError as souci:
            print("[RESEAU] envoi rate : %s" % souci)
            return False

    def _bonjour(self, reponse=False):
        self.envoyer({"type": "bonjour", "nom": self.nom_local,
                      "version": VERSION_PROTOCOLE, "reponse": bool(reponse)})

    def remettre(self, messages):
        """Remet des messages en tete de file : ils seront rendus par le
        prochain recevoir(). Sert au salon, qui passe la main a la partie au
        milieu d'un paquet de messages."""
        self._remis = list(messages) + list(getattr(self, "_remis", []))

    def recevoir(self):
        """A appeler a chaque image. Renvoie les messages de jeu arrives."""
        if self.ferme:
            return []
        remis = list(getattr(self, "_remis", []))
        self._remis = []
        return remis + self._recevoir()

    def _recevoir(self):
        try:
            self._entretien()
        except OSError as souci:
            print("[RESEAU] entretien : %s" % souci)
        maintenant = self._horloge()

        if self._pair_connu() and not self.parti:
            if not self.bonjour_recu and maintenant - self._dernier_bonjour >= PERIODE_BONJOUR:
                self._dernier_bonjour = maintenant
                self._bonjour()
            elif self.bonjour_recu and maintenant - self._dernier_ping >= PERIODE_PING:
                self._dernier_ping = maintenant
                self.envoyer({"type": "ping"})

        messages = []
        try:
            paquets = self._lire_octets()
        except OSError as souci:
            print("[RESEAU] lecture : %s" % souci)
            paquets = []
        for octets in paquets:
            try:
                message = json.loads(octets.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                print("[RESEAU] message illisible ignore")
                continue
            if not isinstance(message, dict):
                continue
            self._dernier_recu = maintenant
            genre = message.get("type")
            if genre == "bonjour":
                self._recevoir_bonjour(message)
            elif genre == "au_revoir":
                self.parti = True
            elif genre == "ping":
                pass
            elif self.bonjour_recu:
                messages.append(message)
        return messages

    def _recevoir_bonjour(self, message):
        version = message.get("version")
        if version != VERSION_PROTOCOLE:
            self.erreur = ("Versions différentes : mettez tous les deux "
                           "SickChess à jour.")
            return
        nom = str(message.get("nom") or "").strip()
        if nom:
            self.nom_adverse = nom[:24]
        premier = not self.bonjour_recu
        self.bonjour_recu = True
        self.parti = False
        # On repond une fois, pour que l'autre sache qu'on l'a entendu meme si
        # notre premier bonjour s'est perdu.
        if premier or not message.get("reponse"):
            self._bonjour(reponse=True)

    def oublier_adversaire(self):
        """L'adversaire est parti avant le debut : on attend le suivant."""
        self.parti = False
        self.bonjour_recu = False
        self.nom_adverse = ""
        self._dernier_recu = None
        self._dernier_bonjour = -999.0

    def fermer(self):
        """Quitte proprement : previent l'autre puis coupe."""
        if self.ferme:
            return
        try:
            if self._pair_connu() and not self.parti:
                self.envoyer({"type": "au_revoir"})
        except Exception:
            pass
        self.ferme = True
        try:
            self._fermer()
        except Exception:
            pass


# ======================================================================= Steam

class TransportSteam(Transport):
    """Les deux membres d'un salon Steam se parlent par le relais de Valve."""

    def __init__(self, steam, salon, nom_local=None, horloge=None):
        super().__init__(nom_local or steam.mon_nom(), horloge)
        self.steam = steam
        self.salon = int(salon)
        self.moi = steam.mon_id()
        self.adversaire = 0
        self.hote = steam.proprietaire(self.salon) == self.moi
        self._dernier_regard = -999.0
        self._vu_dans_le_salon = False

    def _pair_connu(self):
        return bool(self.adversaire)

    def _chercher_adversaire(self):
        membres = [m for m in self.steam.membres(self.salon) if m != self.moi]
        if self.adversaire:
            if self.adversaire in membres:
                self._vu_dans_le_salon = True
            elif self._vu_dans_le_salon:
                self.parti = True              # parti sans dire au revoir
            return
        if membres:
            self.adversaire = membres[0]
            self._vu_dans_le_salon = True
            self.nom_adverse = self.steam.nom_de(self.adversaire)[:24]
            print("[STEAM] adversaire : %s" % self.nom_adverse)

    def _entretien(self):
        self.steam.pomper()
        for evenement in self.steam.evenements("membre", "demande_session"):
            if evenement["type"] == "demande_session":
                membres = self.steam.membres(self.salon)
                if evenement["ami"] in membres and evenement["ami"] != self.moi:
                    self.steam.accepter_session(evenement["ami"])
            elif evenement.get("salon") == self.salon:
                if evenement.get("parti") and evenement["membre"] == self.adversaire:
                    self.parti = True
                elif evenement.get("entre") and evenement["membre"] != self.moi:
                    self._dernier_regard = -999.0        # regarder tout de suite
        maintenant = self._horloge()
        if maintenant - self._dernier_regard >= 0.5:
            self._dernier_regard = maintenant
            self._chercher_adversaire()

    def oublier_adversaire(self):
        if self.adversaire:
            self.steam.fermer_session(self.adversaire)
        self.adversaire = 0
        self._vu_dans_le_salon = False
        super().oublier_adversaire()

    def _envoyer_octets(self, octets):
        return self.steam.envoyer(self.adversaire, octets)

    def _lire_octets(self):
        paquets = []
        for expediteur, octets in self.steam.recevoir():
            if not self.adversaire and expediteur in self.steam.membres(self.salon):
                self.adversaire = expediteur
                self.nom_adverse = self.steam.nom_de(expediteur)[:24]
            if expediteur == self.adversaire:
                paquets.append(octets)
        return paquets

    def _fermer(self):
        if self.adversaire:
            self.steam.fermer_session(self.adversaire)
        self.steam.quitter_salon(self.salon)


# ======================================================================= Local

PORT_LOCAL = 5577


class TransportLocal(Transport):
    """Connexion TCP sur ce PC, pour tester avec deux fenetres. L'hote ecoute,
    l'invite se connecte. Tout est non bloquant : jamais de gel de l'image."""

    def __init__(self, hote, nom_local="Joueur", adresse="127.0.0.1",
                 port=PORT_LOCAL, horloge=None):
        super().__init__(nom_local, horloge)
        self.hote = bool(hote)
        self.adresse = adresse
        self.port = int(port)
        self._ecoute = None
        self._sock = None
        self._tampon = b""
        self._a_envoyer = b""
        self._prochain_essai = 0.0
        if self.hote:
            try:
                self._ecoute = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._ecoute.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._ecoute.bind((adresse, self.port))
                self._ecoute.listen(1)
                self._ecoute.setblocking(False)
            except OSError as souci:
                self.erreur = "Port %d déjà pris : une autre partie test est ouverte ?" \
                    % self.port
                print("[RESEAU] ecoute impossible : %s" % souci)
                self._ecoute = None

    def _pair_connu(self):
        return self._sock is not None

    def _entretien(self):
        if self._sock is not None:
            self._vider_envois()
            return
        if self.hote and self._ecoute is not None:
            try:
                sock, _ = self._ecoute.accept()
            except (BlockingIOError, OSError):
                return
            self._brancher(sock)
        elif not self.hote and self._horloge() >= self._prochain_essai:
            self._prochain_essai = self._horloge() + 1.0
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            try:
                sock.connect((self.adresse, self.port))
            except OSError:
                sock.close()
                return
            self._brancher(sock)

    def _brancher(self, sock):
        sock.setblocking(False)
        # Sans ca, Windows et Linux retiennent les petits messages ~40 ms
        # (algorithme de Nagle) : un coup mettrait du temps a partir.
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass
        self._sock = sock

    def _envoyer_octets(self, octets):
        self._a_envoyer += octets + b"\n"
        self._vider_envois()
        return True

    def _vider_envois(self):
        while self._a_envoyer and self._sock is not None:
            try:
                n = self._sock.send(self._a_envoyer)
            except BlockingIOError:
                return
            except OSError:
                self._coupure()
                return
            self._a_envoyer = self._a_envoyer[n:]

    def _coupure(self):
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
        self._sock = None
        if self.bonjour_recu:
            self.parti = True

    def _lire_octets(self):
        if self._sock is None:
            return []
        while True:
            try:
                bloc = self._sock.recv(65536)
            except BlockingIOError:
                break
            except OSError:
                self._coupure()
                break
            if not bloc:                       # l'autre a ferme
                self._coupure()
                break
            self._tampon += bloc
        lignes = self._tampon.split(b"\n")
        self._tampon = lignes.pop()
        return [ligne for ligne in lignes if ligne.strip()]

    def _fermer(self):
        self._vider_envois()
        for sock in (self._sock, self._ecoute):
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
        self._sock = None
        self._ecoute = None
