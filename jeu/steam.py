# steam.py - SickChess : le lien avec Steam (multijoueur).
#
# On parle directement a steam_api64.dll (la bibliotheque du Steamworks SDK)
# avec ctypes, le module standard de Python pour appeler une DLL. Rien a
# compiler, rien a installer en plus de pygame et python-chess.
#
# CE QUE STEAM NOUS DONNE, GRATUITEMENT :
#   - les SALONS (lobbies) : un joueur cree un salon, son ami le rejoint ;
#   - les INVITATIONS : depuis la liste d'amis Steam ou depuis le jeu ;
#   - le RELAIS RESEAU de Valve : les messages passent par les serveurs de
#     Steam, donc rien a ouvrir sur la box, aucun serveur a louer, et les
#     adresses IP des joueurs ne sont jamais montrees a l'autre.
#
# CE QU'IL FAUT A COTE DU JEU :
#   - steam_api64.dll (dossier redistributable_bin/win64 du Steamworks SDK) ;
#   - steam_appid.txt avec le numero du jeu. Tant que SickChess n'a pas son
#     propre numero, on utilise 480 ("Spacewar"), le numero de test que Valve
#     donne a tous les developpeurs. A RETIRER du paquet envoye sur Steam.
#   - le client Steam lance et connecte.
#
# Si l'un des trois manque, Steam.demarrer() renvoie False et Steam.erreur
# explique pourquoi, en francais. Le reste du jeu continue sans multijoueur.
#
# Les fonctions utilisees sont celles de "l'API plate" (steam_api_flat.h) et
# les structures sont recopiees de steam_api.json (SDK 1.6x). Les evenements
# Steam (salon cree, ami arrive...) sont lus "a la main" a chaque image par
# pomper() : c'est le mode prevu par Valve pour les langages autres que le C++.

import ctypes
import os
import sys
from ctypes import (POINTER, Structure, byref, c_bool, c_char_p, c_int,
                    c_int64, c_uint16, c_uint32, c_uint64, c_ubyte, c_void_p,
                    sizeof)

APPID_DE_TEST = 480                # "Spacewar" : le numero de test de Valve
NOM_DU_JEU = "SickChess"           # ecrit dans chaque salon, verifie a l'entree

# Types de salon (ELobbyType)
SALON_PRIVE = 0
SALON_AMIS = 1                     # visible et rejoignable par les amis
SALON_PUBLIC = 2

# Etat de presence d'un ami (EPersonaState)
HORS_LIGNE = 0

# Envoi : fiable (renvoye jusqu'a reception, dans l'ordre) + session relancee
# toute seule si elle casse (k_nSteamNetworkingSend_Reliable |
# k_nSteamNetworkingSend_AutoRestartBrokenSession).
ENVOI_FIABLE = 8 | 32
CANAL = 0

# Numeros des evenements Steam utilises (k_iCallback)
CB_INVITATION_ACCEPTEE = 333       # GameLobbyJoinRequested_t
CB_INVITATION_RECUE = 503          # LobbyInvite_t (24/10, p36 : jeu ouvert)
CB_SALON_ENTRE = 504               # LobbyEnter_t
CB_SALON_INFOS = 505               # LobbyDataUpdate_t
CB_SALON_MEMBRE = 506              # LobbyChatUpdate_t
CB_SALON_CREE = 513                # LobbyCreated_t
CB_APPEL_TERMINE = 703             # SteamAPICallCompleted_t
CB_DEMANDE_SESSION = 1251          # SteamNetworkingMessagesSessionRequest_t

# Changement d'un membre du salon (EChatMemberStateChange)
MEMBRE_ENTRE = 1
MEMBRE_PARTI = 2 | 4 | 8 | 16      # parti, deconnecte, expulse, banni


# ---------------------------------------------------------------- structures
# Windows : alignement naturel (pack 8), le meme que ctypes par defaut.

class IdentiteReseau(Structure):           # SteamNetworkingIdentity (136 o)
    _fields_ = [("type", c_int), ("taille", c_int), ("brut", c_ubyte * 128)]


class MessageReseau(Structure):            # SteamNetworkingMessage_t
    _fields_ = [("donnees", c_void_p), ("taille", c_int),
                ("connexion", c_uint32), ("pair", IdentiteReseau),
                ("donnee_connexion", c_int64), ("recu_le", c_int64),
                ("numero", c_int64), ("liberer_donnees", c_void_p),
                ("liberer", c_void_p), ("canal", c_int), ("drapeaux", c_int),
                ("donnee_utilisateur", c_int64), ("voie", c_uint16),
                ("_bourrage", c_uint16)]


class MessageRappel(Structure):            # CallbackMsg_t
    _fields_ = [("utilisateur", c_int), ("numero", c_int),
                ("parametre", c_void_p), ("taille", c_int)]


class AppelTermine(Structure):             # SteamAPICallCompleted_t
    _fields_ = [("appel", c_uint64), ("numero", c_int), ("taille", c_uint32)]


class SalonCree(Structure):                # LobbyCreated_t
    _fields_ = [("resultat", c_int), ("salon", c_uint64)]


class SalonEntre(Structure):               # LobbyEnter_t
    _fields_ = [("salon", c_uint64), ("permissions", c_uint32),
                ("verrouille", c_bool), ("reponse", c_uint32)]


class InvitationAcceptee(Structure):       # GameLobbyJoinRequested_t
    _fields_ = [("salon", c_uint64), ("ami", c_uint64)]


class InvitationRecue(Structure):          # LobbyInvite_t
    _fields_ = [("ami", c_uint64), ("salon", c_uint64), ("jeu", c_uint64)]


class MembreChange(Structure):             # LobbyChatUpdate_t
    _fields_ = [("salon", c_uint64), ("membre", c_uint64),
                ("auteur", c_uint64), ("changement", c_uint32)]


class InfoJeuAmi(Structure):               # FriendGameInfo_t
    _fields_ = [("jeu", c_uint64), ("ip", c_uint32), ("port", c_uint16),
                ("port_requete", c_uint16), ("salon", c_uint64)]


# Verification des tailles, une fois pour toutes (memes valeurs que le SDK).
assert sizeof(IdentiteReseau) == 136
assert sizeof(MessageReseau) == 216
assert sizeof(MessageRappel) == 24
assert sizeof(SalonEntre) == 24
assert sizeof(MembreChange) == 32
assert sizeof(InvitationRecue) == 24
assert sizeof(InfoJeuAmi) == 24


# ---------------------------------------------------------------- codes de salon
# Le numero d'un salon fait 18 chiffres. On l'ecrit en base 36, par groupes de
# quatre : "2K7F-9QXA-31BZ". C'est le "code" qu'on peut dicter a un ami.

_CHIFFRES = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def code_depuis_salon(salon):
    n = int(salon)
    if n <= 0:
        return ""
    texte = ""
    while n:
        n, reste = divmod(n, 36)
        texte = _CHIFFRES[reste] + texte
    return "-".join(texte[i:i + 4] for i in range(0, len(texte), 4))


def salon_depuis_code(code):
    """Renvoie le numero du salon, ou None si le code ne veut rien dire."""
    propre = "".join(c for c in str(code).upper() if c.isalnum())
    if not propre or len(propre) > 13:
        return None
    n = 0
    for c in propre:
        if c not in _CHIFFRES:
            return None
        n = n * 36 + _CHIFFRES.index(c)
    return n or None


def salon_depuis_ligne_de_commande(arguments=None):
    """Steam lance le jeu avec '+connect_lobby <numero>' quand on accepte une
    invitation alors que SickChess etait ferme."""
    arguments = list(sys.argv[1:] if arguments is None else arguments)
    for i, argument in enumerate(arguments):
        if argument == "+connect_lobby" and i + 1 < len(arguments):
            try:
                return int(arguments[i + 1])
            except ValueError:
                return None
    return None


# ---------------------------------------------------------------- Steam

class Steam:
    """Une seule instance pour tout le jeu : voir instance()."""

    def __init__(self, dossier=None):
        self.dossier = dossier or os.getcwd()
        self.dll = None
        self.actif = False
        self.erreur = ""
        self.conseil = ""
        self.appid = 0
        self._pipe = 0
        self._evenements = []
        self._i = {}                      # interfaces (pointeurs C)

    # ------------------------------------------------------------ demarrage

    def _chemin_dll(self):
        nom = "steam_api64.dll" if sizeof(c_void_p) == 8 else "steam_api.dll"
        candidats = [os.path.join(self.dossier, nom),
                     os.path.join(self.dossier, "steam", nom)]
        base = getattr(sys, "_MEIPASS", None)
        if base:
            candidats.append(os.path.join(base, nom))
        for chemin in candidats:
            if os.path.exists(chemin):
                return chemin
        return None

    def demarrer(self):
        """Branche le jeu sur Steam. True si tout est pret. Sans danger si
        appele plusieurs fois."""
        if self.actif:
            return True
        if sys.platform != "win32":
            return self._echec("Le multijoueur Steam n'existe que sous Windows.")
        chemin = self._chemin_dll()
        if chemin is None:
            return self._echec("steam_api64.dll est introuvable.",
                               "Copie-le a cote de SickChess.py (voir "
                               "docs/MULTIJOUEUR_STEAM.md).")
        try:
            self.dll = ctypes.CDLL(chemin)
            self._declarer_fonctions()
        except (OSError, AttributeError) as souci:
            return self._echec("steam_api64.dll n'a pas pu être chargé.",
                               str(souci)[:90])

        if not os.path.exists(os.path.join(self.dossier, "steam_appid.txt")) \
                and not getattr(sys, "frozen", False):
            return self._echec("steam_appid.txt manque a cote du jeu.",
                               "Il doit contenir 480 tant que SickChess n'a pas "
                               "son propre numéro Steam.")

        if not self._initialiser():
            return False
        try:
            self._ouvrir_interfaces()
            self.dll.SteamAPI_ManualDispatch_Init()
            self._pipe = self.dll.SteamAPI_GetHSteamPipe()
            self.appid = int(self.dll.SteamAPI_ISteamUtils_GetAppID(self._i["utils"]))
            if self._i.get("reseau_utils"):
                # Prepare le relais de Valve des maintenant : la premiere
                # connexion avec l'ami sera plus rapide.
                self.dll.SteamAPI_ISteamNetworkingUtils_InitRelayNetworkAccess(
                    self._i["reseau_utils"])
        except Exception as souci:
            self._fermer_dll()
            return self._echec("Steam a repondu de facon inattendue.",
                               str(souci)[:90])
        self.actif = True
        self.erreur = ""
        print("[STEAM] connecte : %s (jeu %d)" % (self.mon_nom(), self.appid))
        return True

    def _echec(self, erreur, conseil=""):
        self.erreur = erreur
        self.conseil = conseil
        print("[STEAM] %s %s" % (erreur, conseil))
        return False

    def _initialiser(self):
        d = self.dll
        if hasattr(d, "SteamAPI_InitFlat"):
            message = ctypes.create_string_buffer(1024)
            resultat = d.SteamAPI_InitFlat(ctypes.cast(message, c_void_p))
            if resultat == 0:
                return True
            detail = message.value.decode("utf-8", "replace")
            if resultat == 2:
                return self._echec("Steam n'est pas lance.",
                                   "Ouvre Steam, connecte-toi, puis reviens ici.")
            if resultat == 3:
                return self._echec("Steam doit être mis à jour.", detail)
            return self._echec("Steam refuse la connexion.", detail
                               or "Vérifie que Steam est ouvert et connecté.")
        if hasattr(d, "SteamAPI_Init"):           # tres vieilles DLL
            d.SteamAPI_Init.restype = c_bool
            if d.SteamAPI_Init():
                return True
        return self._echec("Steam refuse la connexion.",
                           "Vérifie que Steam est ouvert et connecté.")

    def _accesseur(self, base):
        """Les fonctions d'acces portent un numero de version qui change avec
        le SDK (SteamAPI_SteamFriends_v018...). On prend la plus recente."""
        for version in range(40, 0, -1):
            nom = "%s_v%03d" % (base, version)
            fonction = getattr(self.dll, nom, None)
            if fonction is not None:
                fonction.restype = c_void_p
                fonction.argtypes = []
                return fonction()
        return None

    def _ouvrir_interfaces(self):
        self._i = {
            "user": self._accesseur("SteamAPI_SteamUser"),
            "amis": self._accesseur("SteamAPI_SteamFriends"),
            "utils": self._accesseur("SteamAPI_SteamUtils"),
            "salons": self._accesseur("SteamAPI_SteamMatchmaking"),
            "messages": self._accesseur("SteamAPI_SteamNetworkingMessages_SteamAPI"),
            "reseau_utils": self._accesseur("SteamAPI_SteamNetworkingUtils_SteamAPI"),
            # 17/10 (p19) : les succes Steam. Facultatif : sans elle, le jeu
            # garde ses succes pour lui (succes.json).
            "stats": self._accesseur("SteamAPI_SteamUserStats"),
        }
        manquantes = [cle for cle in ("user", "amis", "utils", "salons", "messages")
                      if not self._i.get(cle)]
        if manquantes:
            raise RuntimeError("interfaces absentes : %s" % ", ".join(manquantes))

    def _declarer_fonctions(self):
        d = self.dll
        P = c_void_p
        U64 = c_uint64

        def f(nom, restype, *argtypes, facultative=False):
            fonction = getattr(d, nom, None)
            if fonction is None:
                if facultative:
                    return
                raise AttributeError(nom)
            fonction.restype = restype
            fonction.argtypes = list(argtypes)

        if hasattr(d, "SteamAPI_InitFlat"):
            f("SteamAPI_InitFlat", c_int, c_void_p)
        f("SteamAPI_Shutdown", None)
        f("SteamAPI_ManualDispatch_Init", None)
        f("SteamAPI_GetHSteamPipe", c_int)
        f("SteamAPI_ManualDispatch_RunFrame", None, c_int)
        f("SteamAPI_ManualDispatch_GetNextCallback", c_bool, c_int,
          POINTER(MessageRappel))
        f("SteamAPI_ManualDispatch_FreeLastCallback", None, c_int)
        f("SteamAPI_ManualDispatch_GetAPICallResult", c_bool, c_int, U64, P,
          c_int, c_int, POINTER(c_bool))

        f("SteamAPI_ISteamUser_GetSteamID", U64, P)
        f("SteamAPI_ISteamUserStats_SetAchievement", c_bool, P, c_char_p, facultative=True)
        f("SteamAPI_ISteamUserStats_StoreStats", c_bool, P, facultative=True)
        f("SteamAPI_ISteamUtils_GetAppID", c_uint32, P)
        f("SteamAPI_ISteamFriends_GetPersonaName", c_char_p, P)
        f("SteamAPI_ISteamFriends_GetFriendPersonaName", c_char_p, P, U64)
        f("SteamAPI_ISteamFriends_GetFriendCount", c_int, P, c_int)
        f("SteamAPI_ISteamFriends_GetFriendByIndex", U64, P, c_int, c_int)
        f("SteamAPI_ISteamFriends_GetFriendPersonaState", c_int, P, U64)
        f("SteamAPI_ISteamFriends_GetFriendGamePlayed", c_bool, P, U64,
          POINTER(InfoJeuAmi))
        f("SteamAPI_ISteamFriends_ActivateGameOverlayInviteDialog", None, P, U64)
        f("SteamAPI_ISteamFriends_SetRichPresence", c_bool, P, c_char_p, c_char_p,
          facultative=True)

        f("SteamAPI_ISteamMatchmaking_CreateLobby", U64, P, c_int, c_int)
        f("SteamAPI_ISteamMatchmaking_JoinLobby", U64, P, U64)
        f("SteamAPI_ISteamMatchmaking_LeaveLobby", None, P, U64)
        f("SteamAPI_ISteamMatchmaking_InviteUserToLobby", c_bool, P, U64, U64)
        f("SteamAPI_ISteamMatchmaking_GetNumLobbyMembers", c_int, P, U64)
        f("SteamAPI_ISteamMatchmaking_GetLobbyMemberByIndex", U64, P, U64, c_int)
        f("SteamAPI_ISteamMatchmaking_GetLobbyOwner", U64, P, U64)
        f("SteamAPI_ISteamMatchmaking_GetLobbyData", c_char_p, P, U64, c_char_p)
        f("SteamAPI_ISteamMatchmaking_SetLobbyData", c_bool, P, U64, c_char_p,
          c_char_p)
        f("SteamAPI_ISteamMatchmaking_SetLobbyJoinable", c_bool, P, U64, c_bool)

        f("SteamAPI_SteamNetworkingIdentity_Clear", None, POINTER(IdentiteReseau))
        f("SteamAPI_SteamNetworkingIdentity_SetSteamID64", None,
          POINTER(IdentiteReseau), U64)
        f("SteamAPI_SteamNetworkingIdentity_GetSteamID64", U64,
          POINTER(IdentiteReseau))
        f("SteamAPI_ISteamNetworkingMessages_SendMessageToUser", c_int, P,
          POINTER(IdentiteReseau), P, c_uint32, c_int, c_int)
        f("SteamAPI_ISteamNetworkingMessages_ReceiveMessagesOnChannel", c_int, P,
          c_int, POINTER(POINTER(MessageReseau)), c_int)
        f("SteamAPI_ISteamNetworkingMessages_AcceptSessionWithUser", c_bool, P,
          POINTER(IdentiteReseau))
        f("SteamAPI_ISteamNetworkingMessages_CloseSessionWithUser", c_bool, P,
          POINTER(IdentiteReseau))
        f("SteamAPI_SteamNetworkingMessage_t_Release", None, POINTER(MessageReseau))
        f("SteamAPI_ISteamNetworkingUtils_InitRelayNetworkAccess", None, P,
          facultative=True)

    # ------------------------------------------------------------ evenements

    def pomper(self):
        """A appeler a chaque image : lit les evenements Steam en attente."""
        if not self.actif:
            return
        d = self.dll
        try:
            d.SteamAPI_ManualDispatch_RunFrame(self._pipe)
            rappel = MessageRappel()
            while d.SteamAPI_ManualDispatch_GetNextCallback(self._pipe, byref(rappel)):
                try:
                    if rappel.numero == CB_APPEL_TERMINE:
                        self._resultat_d_appel(rappel)
                    else:
                        self._lire(rappel.numero, rappel.parametre, rappel.taille)
                except Exception as souci:
                    print("[STEAM] evenement %d illisible : %s" % (rappel.numero, souci))
                finally:
                    d.SteamAPI_ManualDispatch_FreeLastCallback(self._pipe)
        except Exception as souci:
            print("[STEAM] pomper : %s" % souci)
        if len(self._evenements) > 200:
            del self._evenements[:-200]

    def _resultat_d_appel(self, rappel):
        termine = AppelTermine.from_buffer_copy(
            ctypes.string_at(rappel.parametre, sizeof(AppelTermine)))
        tampon = ctypes.create_string_buffer(max(1, termine.taille))
        rate = c_bool(False)
        if self.dll.SteamAPI_ManualDispatch_GetAPICallResult(
                self._pipe, termine.appel, ctypes.cast(tampon, c_void_p),
                termine.taille, termine.numero, byref(rate)):
            if rate.value and termine.numero == CB_SALON_CREE:
                self._evenements.append({"type": "salon_cree", "ok": False,
                                         "salon": 0})
                return
            self._lire(termine.numero, ctypes.addressof(tampon), termine.taille)

    def _lire(self, numero, adresse, taille):
        def copie(structure):
            if not adresse or taille < sizeof(structure):
                return None
            return structure.from_buffer_copy(ctypes.string_at(adresse,
                                                               sizeof(structure)))

        if numero == CB_SALON_CREE:
            s = copie(SalonCree)
            if s is not None:
                self._evenements.append({"type": "salon_cree",
                                         "ok": s.resultat == 1,
                                         "salon": int(s.salon)})
        elif numero == CB_SALON_ENTRE:
            s = copie(SalonEntre)
            if s is not None:
                # reponse 1 = k_EChatRoomEnterResponseSuccess
                self._evenements.append({"type": "salon_entre",
                                         "ok": s.reponse == 1,
                                         "reponse": int(s.reponse),
                                         "salon": int(s.salon)})
        elif numero == CB_INVITATION_ACCEPTEE:
            s = copie(InvitationAcceptee)
            if s is not None:
                self._evenements.append({"type": "invitation_acceptee",
                                         "salon": int(s.salon),
                                         "ami": int(s.ami)})
        elif numero == CB_INVITATION_RECUE:
            # 24/10 (p36) : un ami nous invite PENDANT que SickChess est ouvert
            # (Steam l'ecrit aussi dans sa discussion). Le jeu affiche un
            # bandeau « X t'invite » (invitations.py). On ne garde que les
            # invitations pour CE jeu (les 24 bits bas de l'identifiant de jeu).
            s = copie(InvitationRecue)
            if s is not None and (not s.jeu or not self.appid
                                  or int(s.jeu) & 0xFFFFFF == int(self.appid)):
                self._evenements.append({"type": "invitation_recue",
                                         "salon": int(s.salon),
                                         "ami": int(s.ami)})
        elif numero == CB_SALON_MEMBRE:
            s = copie(MembreChange)
            if s is not None:
                self._evenements.append({
                    "type": "membre", "salon": int(s.salon),
                    "membre": int(s.membre),
                    "entre": bool(s.changement & MEMBRE_ENTRE),
                    "parti": bool(s.changement & MEMBRE_PARTI)})
        elif numero == CB_DEMANDE_SESSION:
            s = copie(IdentiteReseau)
            if s is not None:
                ami = int(self.dll.SteamAPI_SteamNetworkingIdentity_GetSteamID64(
                    byref(s)))
                self._evenements.append({"type": "demande_session", "ami": ami})

    def evenements(self, *types):
        """Retire et renvoie les evenements des types demandes (tous si vide)."""
        pris = [e for e in self._evenements if not types or e["type"] in types]
        self._evenements = [e for e in self._evenements
                            if types and e["type"] not in types]
        return pris

    # ------------------------------------------------------------ joueurs

    def mon_id(self):
        if not self.actif:
            return 0
        return int(self.dll.SteamAPI_ISteamUser_GetSteamID(self._i["user"]))

    def mon_nom(self):
        if not self.actif:
            return ""
        nom = self.dll.SteamAPI_ISteamFriends_GetPersonaName(self._i["amis"])
        return (nom or b"").decode("utf-8", "replace")

    def nom_de(self, joueur):
        if not self.actif or not joueur:
            return ""
        nom = self.dll.SteamAPI_ISteamFriends_GetFriendPersonaName(
            self._i["amis"], c_uint64(joueur))
        return (nom or b"").decode("utf-8", "replace")

    def amis(self):
        """Les amis Steam : [{id, nom, en_ligne, sur_sickchess}], les plus
        utiles en premier (ceux qui jouent deja a SickChess, puis en ligne)."""
        if not self.actif:
            return []
        d, amis = self.dll, self._i["amis"]
        resultat = []
        nombre = d.SteamAPI_ISteamFriends_GetFriendCount(amis, 4)  # Immediate
        for index in range(max(0, min(nombre, 500))):
            ami = int(d.SteamAPI_ISteamFriends_GetFriendByIndex(amis, index, 4))
            if not ami:
                continue
            etat = d.SteamAPI_ISteamFriends_GetFriendPersonaState(amis, ami)
            info = InfoJeuAmi()
            dans_le_jeu = bool(d.SteamAPI_ISteamFriends_GetFriendGamePlayed(
                amis, ami, byref(info))) and (info.jeu & 0xFFFFFF) == self.appid
            resultat.append({"id": ami, "nom": self.nom_de(ami),
                             "en_ligne": etat != HORS_LIGNE,
                             "sur_sickchess": dans_le_jeu})
        resultat.sort(key=lambda a: (not a["sur_sickchess"], not a["en_ligne"],
                                     a["nom"].lower()))
        return resultat

    # ------------------------------------------------------------ salons

    def creer_salon(self, places=2):
        """Demande la creation d'un salon. La reponse arrive plus tard sous la
        forme d'un evenement 'salon_cree'."""
        if not self.actif:
            return False
        self.dll.SteamAPI_ISteamMatchmaking_CreateLobby(self._i["salons"],
                                                         SALON_AMIS, int(places))
        return True

    def rejoindre_salon(self, salon):
        """Reponse : evenement 'salon_entre'."""
        if not self.actif or not salon:
            return False
        self.dll.SteamAPI_ISteamMatchmaking_JoinLobby(self._i["salons"],
                                                       c_uint64(salon))
        return True

    def quitter_salon(self, salon):
        if self.actif and salon:
            self.dll.SteamAPI_ISteamMatchmaking_LeaveLobby(self._i["salons"],
                                                            c_uint64(salon))

    def membres(self, salon):
        if not self.actif or not salon:
            return []
        d, s = self.dll, self._i["salons"]
        nombre = d.SteamAPI_ISteamMatchmaking_GetNumLobbyMembers(s, salon)
        return [int(d.SteamAPI_ISteamMatchmaking_GetLobbyMemberByIndex(s, salon, i))
                for i in range(max(0, nombre))]

    def proprietaire(self, salon):
        if not self.actif or not salon:
            return 0
        return int(self.dll.SteamAPI_ISteamMatchmaking_GetLobbyOwner(
            self._i["salons"], salon))

    def ecrire_info(self, salon, cle, valeur):
        if self.actif and salon:
            self.dll.SteamAPI_ISteamMatchmaking_SetLobbyData(
                self._i["salons"], salon, cle.encode(), str(valeur).encode())

    def lire_info(self, salon, cle):
        if not self.actif or not salon:
            return ""
        valeur = self.dll.SteamAPI_ISteamMatchmaking_GetLobbyData(
            self._i["salons"], salon, cle.encode())
        return (valeur or b"").decode("utf-8", "replace")

    def fermer_salon(self, salon):
        """Plus personne ne peut entrer (la partie a commence)."""
        if self.actif and salon:
            self.dll.SteamAPI_ISteamMatchmaking_SetLobbyJoinable(
                self._i["salons"], salon, False)

    def inviter(self, salon, ami):
        """Envoie l'invitation dans la discussion Steam de l'ami."""
        if not self.actif or not salon or not ami:
            return False
        return bool(self.dll.SteamAPI_ISteamMatchmaking_InviteUserToLobby(
            self._i["salons"], salon, ami))

    def ouvrir_fenetre_invitation(self, salon):
        """Ouvre la fenetre d'invitation de l'overlay Steam (Maj+Tab)."""
        if self.actif and salon:
            self.dll.SteamAPI_ISteamFriends_ActivateGameOverlayInviteDialog(
                self._i["amis"], salon)

    def presence(self, cle, valeur):
        """Texte affiche aux amis dans Steam ("En partie contre Paul")."""
        fonction = getattr(self.dll, "SteamAPI_ISteamFriends_SetRichPresence", None)
        if self.actif and fonction is not None:
            fonction(self._i["amis"], cle.encode(), str(valeur or "").encode("utf-8"))

    # ------------------------------------------------------------ messages

    def _identite(self, joueur):
        identite = IdentiteReseau()
        self.dll.SteamAPI_SteamNetworkingIdentity_Clear(byref(identite))
        self.dll.SteamAPI_SteamNetworkingIdentity_SetSteamID64(byref(identite),
                                                               c_uint64(joueur))
        return identite

    def envoyer(self, joueur, octets):
        """Envoie des octets a un joueur, par le relais de Steam. True si
        Steam a accepte le message."""
        if not self.actif or not joueur:
            return False
        tampon = ctypes.create_string_buffer(bytes(octets), len(octets))
        resultat = self.dll.SteamAPI_ISteamNetworkingMessages_SendMessageToUser(
            self._i["messages"], byref(self._identite(joueur)),
            ctypes.cast(tampon, c_void_p), len(octets), ENVOI_FIABLE, CANAL)
        return resultat == 1                      # k_EResultOK

    def recevoir(self):
        """Renvoie [(expediteur, octets), ...] : tout ce qui est arrive."""
        if not self.actif:
            return []
        recus = []
        tableau = (POINTER(MessageReseau) * 32)()
        while True:
            nombre = self.dll.SteamAPI_ISteamNetworkingMessages_ReceiveMessagesOnChannel(
                self._i["messages"], CANAL, tableau, 32)
            for i in range(max(0, nombre)):
                message = tableau[i]
                try:
                    contenu = message.contents
                    octets = ctypes.string_at(contenu.donnees, contenu.taille)
                    expediteur = int(self.dll.SteamAPI_SteamNetworkingIdentity_GetSteamID64(
                        byref(contenu.pair)))
                    recus.append((expediteur, octets))
                finally:
                    self.dll.SteamAPI_SteamNetworkingMessage_t_Release(message)
            if nombre < 32:
                return recus

    def accepter_session(self, joueur):
        if self.actif and joueur:
            self.dll.SteamAPI_ISteamNetworkingMessages_AcceptSessionWithUser(
                self._i["messages"], byref(self._identite(joueur)))

    def fermer_session(self, joueur):
        if self.actif and joueur:
            self.dll.SteamAPI_ISteamNetworkingMessages_CloseSessionWithUser(
                self._i["messages"], byref(self._identite(joueur)))

    # ------------------------------------------------------------ succes

    def debloquer_succes(self, nom):
        """Debloque un succes Steam (nom API, ex. 'PREMIERE_VICTOIRE'). Il doit
        exister dans la page Steamworks du jeu ; sinon Steam l'ignore."""
        if not self.actif or not self._i.get("stats"):
            return False
        fixer = getattr(self.dll, "SteamAPI_ISteamUserStats_SetAchievement", None)
        ranger = getattr(self.dll, "SteamAPI_ISteamUserStats_StoreStats", None)
        if fixer is None or ranger is None:
            return False
        try:
            ok = bool(fixer(self._i["stats"], nom.encode("ascii")))
            return bool(ranger(self._i["stats"])) and ok
        except Exception as souci:
            print("[STEAM] succes %s : %s" % (nom, souci))
            return False

    # ------------------------------------------------------------ arret

    def _fermer_dll(self):
        self._i = {}
        self.actif = False

    def arreter(self):
        if self.actif:
            try:
                self.dll.SteamAPI_Shutdown()
            except Exception:
                pass
        self._fermer_dll()


_INSTANCE = None


def instance():
    """Le Steam du jeu, cree au premier appel (sans le demarrer)."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = Steam()
    return _INSTANCE
