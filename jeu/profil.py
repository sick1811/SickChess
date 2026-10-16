# profil.py - V7 : NOUVEAU FICHIER
#
# Profil du joueur : un nom, un Elo estime qui bouge selon les resultats, et
# l'historique de toutes les parties jouees.
#
# Tout est range dans profil.json, a cote du jeu (ou a cote de l'executable
# quand le jeu est compile). Aucune connexion, aucun compte : c'est un fichier
# texte que tu peux ouvrir et modifier.

import datetime
import json
import os

FICHIER = "profil.json"
ELO_DEPART = 1200
K_MAX = 40          # les premieres parties font bouger le classement plus vite
K_MIN = 16
PARTIES_MAX = 500


def _dossier():
    try:
        from asset_manager import dossier_ecriture
        return dossier_ecriture()
    except Exception:
        return os.getcwd()


def chemin_profil():
    return os.path.join(_dossier(), FICHIER)


class Profil:
    def __init__(self, charger=True):
        self.nom = "Joueur"
        self.elo = ELO_DEPART
        self.parties = []
        self.cree_le = datetime.date.today().isoformat()
        # V7.1 (ta demande : "chacun a une adresse differente en fonction du
        # profil") : un numero tire une seule fois, garde a vie dans
        # profil.json. C'est lui qui donne son adresse personnelle au joueur,
        # du genre JULIEN-4821. Elle ne change pas d'une partie a l'autre.
        self.numero = None
        if charger:
            self.charger()
        self._assurer_numero()

    # ------------------------------------------------------------------ adresse

    def _assurer_numero(self):
        """Tire le numero personnel une seule fois, puis le garde a vie."""
        if not self.numero:
            import random
            self.numero = "%04d" % random.randint(1, 9999)
            self.enregistrer()
        return self.numero

    def identifiant(self):
        """Adresse personnelle du joueur, stable : 'JULIEN-4821'.

        C'est elle qui sert de code de partie sur le serveur relais : ton ami
        garde toujours la meme, il n'a pas a te redemander un code a chaque
        fois. Elle suit ton nom : renomme-toi et elle se met a jour, en gardant
        ton numero.
        """
        import unicodedata
        brut = unicodedata.normalize("NFKD", str(self.nom or "Joueur"))
        propre = "".join(c for c in brut
                         if c.isalnum() and ord(c) < 128).upper()[:12]
        return "%s-%s" % (propre or "JOUEUR", self._assurer_numero())

    # ------------------------------------------------------------------ disque

    def charger(self):
        chemin = chemin_profil()
        if not os.path.exists(chemin):
            return False
        try:
            with open(chemin, "r", encoding="utf-8") as f:
                donnees = json.load(f)
        except (OSError, ValueError) as e:
            print("[PROFIL] profil.json illisible (%s), profil neuf" % e)
            return False
        # 04/09 : un profil.json coupe rendait None ou une liste, et le .get()
        # qui suit plantait au demarrage.
        if not isinstance(donnees, dict):
            print("[PROFIL] profil.json n'est pas un dictionnaire, profil neuf")
            return False
        self.nom = donnees.get("nom", self.nom)
        # 04/09 : un elo ecrit en toutes lettres (fichier bricole a la main,
        # ecriture coupee) levait un ValueError sur int() et le jeu refusait
        # de s'ouvrir. On garde le reste du profil et on repart du classement
        # de depart plutot que de tout jeter.
        try:
            self.elo = int(donnees.get("elo", ELO_DEPART))
        except (TypeError, ValueError):
            print("[PROFIL] classement illisible (%r), on repart de %d"
                  % (donnees.get("elo"), ELO_DEPART))
            self.elo = ELO_DEPART
        parties = donnees.get("parties", [])
        self.parties = parties if isinstance(parties, list) else []
        self.cree_le = donnees.get("cree_le", self.cree_le)
        self.numero = donnees.get("numero") or None
        return True

    def enregistrer(self):
        try:
            with open(chemin_profil(), "w", encoding="utf-8") as f:
                json.dump({"nom": self.nom, "elo": self.elo,
                           "cree_le": self.cree_le,
                           "numero": self.numero,
                           "parties": self.parties[-PARTIES_MAX:]},
                          f, indent=2, ensure_ascii=False)
            return True
        except OSError as e:
            print("[PROFIL] enregistrement impossible : %s" % e)
            return False

    # ------------------------------------------------------------------ elo

    def _facteur_k(self):
        jouees = len(self.parties)
        if jouees < 10:
            return K_MAX
        if jouees < 30:
            return 28
        return K_MIN

    def nouveau_classement(self, elo_adversaire, score):
        """score : 1 victoire, 0.5 nulle, 0 defaite. Renvoie le nouvel Elo."""
        attendu = 1.0 / (1.0 + 10 ** ((elo_adversaire - self.elo) / 400.0))
        return int(round(self.elo + self._facteur_k() * (score - attendu)))

    # ------------------------------------------------------------------ parties

    def ajouter_partie(self, adversaire, elo_adversaire, resultat, couleur,
                       nombre_de_coups, classee=True, precision=None,
                       raison="", pgn=None):
        """resultat : '1-0', '0-1' ou '1/2-1/2'. couleur : 'blanc' ou 'noir'."""
        if resultat == "1/2-1/2":
            score = 0.5
        elif (resultat == "1-0") == (couleur == "blanc"):
            score = 1.0
        else:
            score = 0.0

        elo_avant = self.elo
        if classee:
            self.elo = max(100, self.nouveau_classement(int(elo_adversaire), score))

        entree = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "adversaire": adversaire,
            "elo_adversaire": int(elo_adversaire),
            "couleur": couleur,
            "resultat": resultat,
            "score": score,
            "coups": int(nombre_de_coups),
            "elo_avant": elo_avant,
            "elo_apres": self.elo,
            "classee": bool(classee),
            "raison": raison,
        }
        if precision is not None:
            entree["precision"] = round(float(precision), 1)
        if pgn:
            entree["pgn"] = pgn
        self.parties.append(entree)
        self.enregistrer()
        return entree

    # ------------------------------------------------------------------ stats

    def statistiques(self):
        victoires = nulles = defaites = 0
        for p in self.parties:
            if p.get("score") == 1.0:
                victoires += 1
            elif p.get("score") == 0.5:
                nulles += 1
            else:
                defaites += 1
        total = len(self.parties)
        precisions = [p["precision"] for p in self.parties if "precision" in p]
        return {
            "parties": total,
            "victoires": victoires,
            "nulles": nulles,
            "defaites": defaites,
            "pourcentage": round(100.0 * (victoires + 0.5 * nulles) / total, 1) if total else 0.0,
            "precision_moyenne": round(sum(precisions) / len(precisions), 1) if precisions else None,
            "meilleur_elo": max([p["elo_apres"] for p in self.parties] + [self.elo]),
        }

    def dernieres_parties(self, nombre=12):
        return list(reversed(self.parties[-nombre:]))

    def courbe_elo(self, points=40):
        """Suite des Elo pour dessiner une petite courbe de progression."""
        valeurs = [p["elo_apres"] for p in self.parties if p.get("classee")]
        if not valeurs:
            return [self.elo]
        if len(valeurs) <= points:
            return valeurs
        pas = len(valeurs) / float(points)
        return [valeurs[int(i * pas)] for i in range(points)]


_profil = None


def get_profil():
    """Profil unique de l'application."""
    global _profil
    if _profil is None:
        _profil = Profil()
    return _profil
