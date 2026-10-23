# revanche.py - V7.2 : NOUVEAU FICHIER
#
# LA REVANCHE A LA FIN D'UNE PARTIE EN LIGNE (ta demande : "a la fin d'une
# partie online on peut demander une revanche").
#
# COMMENT CA MARCHE, EN UNE PHRASE : celui qui veut rejouer clique REVANCHE,
# l'autre voit la demande sur SON ecran de fin et repond OUI ou NON. Si les deux
# sont d'accord, une nouvelle partie repart DANS LE MEME SALON, avec les memes
# reglages et LES COULEURS INVERSEES - comme dans un club.
#
# POURQUOI UN FICHIER A PART : parce que l'etat d'une revanche est plus subtil
# qu'il n'y parait (les deux peuvent cliquer en meme temps, l'autre peut partir
# entre-temps, on peut redemander apres un refus...). Ici il est ecrit une fois,
# lisible, et testable SANS ouvrir de fenetre ni de connexion.
#
# LES COULEURS : elles s'inversent toutes seules, chacun de son cote, sans se
# consulter. C'est voulu : si les deux calculaient leur couleur a partir d'un
# message de l'autre, un croisement de messages pouvait donner deux joueurs avec
# les blancs. En inversant simplement la sienne, l'echange reste juste meme si
# les deux cliquent exactement en meme temps.

RIEN = "rien"                # personne n'a rien demande
DEMANDEE = "demandee"        # j'ai demande, j'attends sa reponse
RECUE = "recue"              # il demande, je dois repondre
ACCEPTEE = "acceptee"        # les deux sont d'accord : on relance
REFUSEE = "refusee"          # il a dit non
IMPOSSIBLE = "impossible"    # il est parti


class Revanche:
    """L'etat d'une demande de revanche, des deux cotes."""

    def __init__(self, nom_adverse="Ton adversaire"):
        self.etat = RIEN
        self.nom_adverse = nom_adverse or "Ton adversaire"
        self.parties_jouees = 1        # celle qui vient de finir

    # ------------------------------------------------------------- questions

    def possible(self, connecte=True):
        """Peut-on encore proposer quelque chose ? Non si l'autre est parti."""
        return bool(connecte) and self.etat not in (ACCEPTEE, IMPOSSIBLE)

    def en_attente(self):
        return self.etat == DEMANDEE

    def a_repondre(self):
        return self.etat == RECUE

    def acceptee(self):
        return self.etat == ACCEPTEE

    def libelle_bouton(self):
        """Ce qu'on ecrit sur le bouton, selon la situation."""
        if self.etat == RECUE:
            return "ACCEPTER LA REVANCHE"
        if self.etat == DEMANDEE:
            return "REVANCHE DEMANDEE..."
        if self.etat == REFUSEE:
            return "REDEMANDER UNE REVANCHE"
        return "REVANCHE"

    def explication(self):
        """La ligne qu'on affiche sous le bouton. Vide s'il n'y a rien a dire."""
        if self.etat == DEMANDEE:
            return "Revanche proposée. On attend la réponse de %s." % self.nom_adverse
        if self.etat == RECUE:
            return "%s demande une revanche. Les couleurs seront inversées." \
                % self.nom_adverse
        if self.etat == REFUSEE:
            return "%s ne veut pas rejouer tout de suite." % self.nom_adverse
        if self.etat == ACCEPTEE:
            return "Revanche acceptée : nouvelle partie, couleurs inversées."
        if self.etat == IMPOSSIBLE:
            return "%s a quitte la partie." % self.nom_adverse
        return ""

    # ------------------------------------------------------------- actions

    def demander(self):
        """Je clique REVANCHE. Renvoie le message a envoyer, ou None.

        Si l'autre avait DEJA demande, cliquer vaut acceptation : c'est le cas
        des deux joueurs qui cliquent en meme temps, et il ne doit surtout pas
        finir en blocage ou chacun attend l'autre.
        """
        if self.etat == IMPOSSIBLE or self.etat == ACCEPTEE:
            return None
        if self.etat == RECUE:
            return self.accepter()
        self.etat = DEMANDEE
        return {"type": "revanche", "action": "demande"}

    def accepter(self):
        if self.etat == IMPOSSIBLE:
            return None
        self.etat = ACCEPTEE
        return {"type": "revanche", "action": "oui"}

    def refuser(self):
        if self.etat == IMPOSSIBLE:
            return None
        self.etat = RIEN
        return {"type": "revanche", "action": "non"}

    def adversaire_parti(self):
        self.etat = IMPOSSIBLE

    # ------------------------------------------------------------- reception

    def recevoir(self, message):
        """Traite un message 'revanche' venu de l'autre.

        Renvoie la reponse a renvoyer tout de suite (ou None).
        """
        if not isinstance(message, dict) or message.get("type") != "revanche":
            return None
        action = str(message.get("action") or "")
        nom = str(message.get("nom") or "").strip()
        if nom:
            self.nom_adverse = nom[:24]

        if action == "demande":
            if self.etat == DEMANDEE:
                # On a demande tous les deux : personne n'attend, on relance.
                self.etat = ACCEPTEE
                return {"type": "revanche", "action": "oui"}
            if self.etat != ACCEPTEE:
                self.etat = RECUE
            return None

        if action == "oui":
            self.etat = ACCEPTEE
            return None

        if action == "non":
            if self.etat == DEMANDEE:
                self.etat = REFUSEE
            return None

        return None

    # ------------------------------------------------------------- relance

    def couleur_suivante(self, couleur_locale):
        """Les couleurs s'inversent : celui qui avait les blancs prend les noirs."""
        return "noir" if str(couleur_locale).lower() == "blanc" else "blanc"

    def repartir(self):
        """Remet le compteur a zero pour la partie qui commence."""
        self.parties_jouees += 1
        self.etat = RIEN
        return self.parties_jouees
