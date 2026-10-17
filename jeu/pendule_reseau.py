# pendule_reseau.py - V7.2 : NOUVEAU FICHIER
#
# LES DEUX PENDULES QUI NE DISENT PAS LA MEME HEURE.
#
# TA REMARQUE : "des fois le temps n'est pas le meme dans la partie, j'ai deja
# perdu au temps alors que mon ami etait encore en train de jouer".
#
# CE QUI SE PASSAIT, ET C'EST ECRIT NOIR SUR BLANC DANS LE CODE. Dans
# mode_online.py, a la reception d'un message de pendule :
#
#     elif genre == "pendule":
#         pass          # en cours de partie, chacun tient sa propre pendule
#
# Chacun tenait sa propre pendule, et PERSONNE n'arbitrait. Trois consequences,
# toutes les trois pour de vrai :
#
#   1. LA DERIVE. Ton coup part de chez toi a l'instant T ; il arrive chez ton
#      ami a T + le temps du reseau. Chez lui, ta pendule a donc tourne un peu
#      plus longtemps que chez toi. Quelques dixiemes par coup, quarante coups
#      dans la partie : au bout d'un moment il y a plusieurs secondes d'ecart.
#      Et si une des deux machines rame - l'analyse qui tourne, la fenetre
#      reduite, un coup de moteur - l'ecart grandit d'un coup.
#
#   2. LES DEUX MACHINES DECIDENT TOUTES SEULES. board.update() terminait la
#      partie des que SA copie de la pendule touchait zero, pour l'un comme
#      pour l'autre camp. Chez toi ta pendule tombait a zero, la partie
#      s'arretait ; chez ton ami elle affichait encore du temps, et il
#      continuait de jouer. Personne n'avait tort : vous lisiez deux horloges
#      differentes.
#
#   3. L'INCREMENT. Il est ajoute localement a chaque coup. Rien ne verifiait
#      que les deux machines l'avaient bien ajoute au meme moment.
#
# ---------------------------------------------------------------------------
# LA REGLE, MAINTENANT. Il n'y a pas de serveur entre vous deux, donc on ne
# peut pas mettre l'arbitre "au milieu". On fait ce que font les vrais sites :
# ON DESIGNE UN PROPRIETAIRE POUR CHAQUE PENDULE.
#
#   TA PENDULE T'APPARTIENT. Toi seul sais combien de temps tu as vraiment
#       consomme, puisque c'est ta machine qui le compte. Tu envoies ce nombre
#       avec CHAQUE coup, et ton ami remplace sa copie par le tien. La derive
#       est donc remise a zero a chaque coup : elle ne peut plus s'accumuler.
#
#   TOI SEUL PEUX ANNONCER QUE TU AS PERDU AU TEMPS. Quand ta pendule touche
#       zero chez toi, ta machine le dit a l'autre, et la partie se termine des
#       deux cotes en meme temps, avec le meme resultat. Chez ton ami, ta
#       pendule a zero n'arrete plus rien toute seule : elle attend ton mot.
#
#   SAUF SI TU NE DIS RIEN. Si le message n'arrive jamais - machine plantee,
#       reseau coupe, ou quelqu'un qui essaie de gagner du temps en tirant la
#       prise - l'autre peut reclamer le drapeau apres une marge (MARGE_RESEAU).
#       Sans ca, il suffirait de debrancher son cable pour ne jamais perdre.
#
#   ET ON NE PEUT PAS S'INVENTER DU TEMPS. Le temps annonce n'est accepte que
#       s'il est INFERIEUR OU EGAL a ce que la machine d'en face avait deja
#       compte (a une petite tolerance pres, pour le reseau). On peut donc
#       toujours declarer qu'on a moins de temps qu'on ne croyait ; jamais
#       plus.
#
# CE FICHIER NE DESSINE RIEN ET NE DECIDE RIEN TOUT SEUL. Il repond a deux
# questions que board.py et mode_online.py lui posent : "quel temps j'annonce"
# et "est-ce que j'ai le droit de dire que ce camp a perdu".
#
# AUCUNE FONCTION SUPPRIMEE : ce fichier n'existait pas. Sans lui - partie
# locale, contre l'IA, hotseat - tout se comporte exactement comme avant.

import time

import chess

# Ce qu'on tolere en plus quand l'adversaire annonce son temps. Le reseau met
# quelques dixiemes de seconde, et il ne faut pas qu'un aller-retour un peu
# lent passe pour une tricherie.
TOLERANCE_RESEAU = 2.0

# Combien de temps on attend le "j'ai perdu au temps" de l'adversaire avant de
# reclamer le drapeau soi-meme. Sans ce delai, debrancher sa prise suffirait a
# ne jamais perdre.
MARGE_RESEAU = 4.0

# A quelle frequence on renvoie son temps meme sans jouer de coup. Sert
# uniquement a ce que la pendule AFFICHEE chez l'autre reste juste pendant une
# longue reflexion ; ca ne decide jamais de la fin de la partie.
PERIODE_BATTEMENT = 3.0


def _secondes(valeur, defaut=None):
    try:
        valeur = float(valeur)
    except (TypeError, ValueError):
        return defaut
    if valeur != valeur or valeur in (float("inf"), float("-inf")):
        return defaut
    return valeur


class PenduleReseau(object):
    """L'arbitre des deux pendules d'une partie en ligne.

    'timer'          : le ChessTimer du plateau, inchange.
    'couleur_locale' : chess.WHITE ou chess.BLACK - la pendule qui t'appartient.
    """

    def __init__(self, timer, couleur_locale, envoyer=None,
                 horloge=None):
        self.timer = timer
        self.couleur_locale = couleur_locale
        self.couleur_adverse = (chess.BLACK if couleur_locale == chess.WHITE
                                else chess.WHITE)
        self.envoyer = envoyer            # fonction d'envoi reseau, ou None
        self._horloge = horloge or time.time
        self.actif = True
        # Le moment ou la pendule de l'adversaire est tombee a zero CHEZ NOUS.
        # On attend son message avant de reclamer ; passe MARGE_RESEAU, on
        # reclame quand meme.
        self._zero_adverse_depuis = None
        self._dernier_battement = 0.0
        self._annonce_envoyee = False
        # Statistiques honnetes, pour le journal : de combien les deux pendules
        # se sont ecartees. C'est la mesure de ton bug.
        self.ecart_max = 0.0
        self.corrections = 0

    # ------------------------------------------------------------------ envoi

    def paquet(self):
        """Le message a joindre a chaque coup : mon temps, tel que JE le compte."""
        temps = self.timer.time_left
        return {
            "type": "pendule",
            "blanc": float(temps[chess.WHITE]),
            "noir": float(temps[chess.BLACK]),
            # C'est CE champ qui fait autorite : celui qui parle dit sa couleur,
            # et on ne le croit que sur sa propre pendule.
            "proprietaire": ("blanc" if self.couleur_locale == chess.WHITE
                             else "noir"),
            "quand": self._horloge(),
        }

    def battement(self):
        """A appeler a chaque image. Renvoie le paquet a envoyer, ou None.

        Sert seulement a l'AFFICHAGE : sans lui, pendant que tu reflechis
        trente secondes, ton ami voit ta pendule descendre selon SA copie a lui,
        qui derive. Avec lui, elle est recalee toutes les trois secondes.
        """
        if not self.actif or not getattr(self.timer, "demarree", False):
            return None
        maintenant = self._horloge()
        if maintenant - self._dernier_battement < PERIODE_BATTEMENT:
            return None
        self._dernier_battement = maintenant
        return self.paquet()

    # ------------------------------------------------------------- reception

    def appliquer(self, message):
        """Recale la pendule de l'ADVERSAIRE avec le temps qu'il annonce.

        On ne touche JAMAIS a la sienne : personne d'autre que nous ne sait
        combien de temps nous avons consomme.
        Renvoie l'ecart corrige, en secondes (0.0 si rien n'a bouge).
        """
        if not self.actif or not message:
            return 0.0
        proprietaire = str(message.get("proprietaire") or "").lower()
        if proprietaire in ("blanc", "noir"):
            couleur = chess.WHITE if proprietaire == "blanc" else chess.BLACK
            # Un message qui pretend parler de NOTRE pendule est ignore : c'est
            # soit un vieux message, soit quelqu'un qui essaie de nous voler du
            # temps.
            if couleur == self.couleur_locale:
                return 0.0
        else:
            # Ancien format, sans proprietaire : on suppose que l'expediteur
            # parlait de lui. C'est ce que faisait la V7.1.
            couleur = self.couleur_adverse
        annonce = _secondes(message.get("blanc" if couleur == chess.WHITE
                                        else "noir"))
        if annonce is None:
            return 0.0
        annonce = max(0.0, annonce)
        chez_nous = float(self.timer.time_left.get(couleur, 0.0))
        # ON NE PEUT PAS S'INVENTER DU TEMPS : on n'accepte une valeur PLUS
        # GRANDE que la notre que dans la tolerance du reseau.
        if annonce > chez_nous + TOLERANCE_RESEAU:
            annonce = chez_nous + TOLERANCE_RESEAU
        ecart = abs(chez_nous - annonce)
        if ecart < 0.05:
            return 0.0
        self.timer.time_left[couleur] = annonce
        self.ecart_max = max(self.ecart_max, ecart)
        self.corrections += 1
        if annonce > 0.0:
            self._zero_adverse_depuis = None
        return ecart

    def temps_ecoule_annonce(self, message):
        """L'adversaire annonce lui-meme qu'il a perdu au temps. C'est valable.

        Renvoie la couleur qui perd, ou None si le message ne tient pas debout.
        """
        if not message:
            return None
        proprietaire = str(message.get("proprietaire") or "").lower()
        couleur = self.couleur_adverse
        if proprietaire in ("blanc", "noir"):
            couleur = chess.WHITE if proprietaire == "blanc" else chess.BLACK
        if couleur == self.couleur_locale:
            # Personne ne peut declarer NOTRE defaite a notre place.
            return None
        self.timer.time_left[couleur] = 0.0
        return couleur

    # ------------------------------------------------------------- arbitrage

    def peut_declarer(self, couleur):
        """A-t-on le droit de terminer la partie parce que ce camp est a zero ?

        NOTRE pendule : oui, tout de suite. On est le seul a savoir.
        CELLE D'EN FACE : seulement apres MARGE_RESEAU sans nouvelle de sa part.
        Le reste du temps on attend son message, pour que la partie se termine
        des deux cotes avec le meme resultat.
        """
        if not self.actif:
            return True
        if couleur == self.couleur_locale:
            return True
        maintenant = self._horloge()
        if self._zero_adverse_depuis is None:
            self._zero_adverse_depuis = maintenant
            return False
        return (maintenant - self._zero_adverse_depuis) >= MARGE_RESEAU

    def secondes_avant_reclamation(self):
        """Combien de temps il reste a attendre avant de pouvoir reclamer. 0 = maintenant."""
        if self._zero_adverse_depuis is None:
            return MARGE_RESEAU
        reste = MARGE_RESEAU - (self._horloge() - self._zero_adverse_depuis)
        return max(0.0, reste)

    def annoncer_notre_defaite(self):
        """Previent l'adversaire que NOTRE pendule est tombee. Une seule fois."""
        if self._annonce_envoyee or self.envoyer is None:
            return False
        self._annonce_envoyee = True
        paquet = self.paquet()
        paquet["type"] = "temps_ecoule"
        try:
            self.envoyer(paquet)
        except Exception as souci:
            print("[PENDULE] annonce impossible : %s" % souci)
            return False
        return True

    def resume(self):
        """Une ligne pour le journal : est-ce que les deux pendules ont derive ?"""
        if not self.corrections:
            return "pendules synchronisees, aucune correction"
        return ("pendules recalées %d fois, écart maximum %.1f s"
                % (self.corrections, self.ecart_max))
