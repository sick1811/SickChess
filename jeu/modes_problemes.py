# modes_problemes.py - SickChess 17/10 (travail p07, demande de Julien).
#
# Trois defis en plus des modes Classe / Libre / Mes erreurs :
#   - CONTRE LA MONTRE : 3 minutes, le plus de problemes possible ; ils
#     deviennent plus durs a chaque reussite ; une faute = probleme suivant.
#   - SURVIE : pas de temps limite, mais 3 fautes et c'est fini ; la difficulte
#     monte aussi.
#   - PROBLEME DU JOUR : le meme pour tout le monde ce jour-la (tire avec la
#     date), un seul essai ; on garde la serie de jours reussis.
# Meme interface que puzzles.Session (l'ecran des problemes ne voit pas la
# difference), plus quelques methodes propres aux defis. Le classement des
# problemes n'est jamais touche. Records dans modes_problemes.json.

import copy
import datetime
import json
import os
import random

import puzzles

CHRONO = "chrono"
SURVIE = "survie"
DU_JOUR = "jour"
NOMS = {CHRONO: "Contre la montre", SURVIE: "Survie", DU_JOUR: "Problème du jour"}

DUREE_CHRONO = 180.0           # secondes
VIES_SURVIE = 3
DEPART_ECHELLE = 600
PAS_ECHELLE = {CHRONO: 70, SURVIE: 100}
NIVEAU_DU_JOUR = 1500
FICHIER = "modes_problemes.json"


def _chemin():
    try:
        from asset_manager import dossier_ecriture
        return os.path.join(dossier_ecriture(), FICHIER)
    except Exception:
        return os.path.join(os.getcwd(), FICHIER)


# 23/10 (banc d'essai) : l'ecran Problemes relisait le fichier 3 fois par
# image. Lu une fois, puis garde en memoire (par chemin : les tests en
# changent) et mis a jour a chaque enregistrement.
_EN_MEMOIRE = {}


def charger():
    chemin = _chemin()
    if chemin not in _EN_MEMOIRE:
        donnees = {}
        try:
            with open(chemin, "r", encoding="utf-8") as f:
                lu = json.load(f)
            if isinstance(lu, dict):
                donnees = lu
        except (OSError, ValueError):
            pass
        _EN_MEMOIRE[chemin] = donnees
    return copy.deepcopy(_EN_MEMOIRE[chemin])


def enregistrer(donnees):
    _EN_MEMOIRE[_chemin()] = copy.deepcopy(donnees)
    try:
        with open(_chemin(), "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, indent=1)
        return True
    except OSError as e:
        print("[DEFIS] records non enregistres : %s" % e)
        return False


def record(mode):
    return int(charger().get("record_" + mode, 0))


def aujourd_hui(date=None):
    return (date or datetime.date.today()).isoformat()


def etat_du_jour(date=None):
    """{'fait': bool, 'reussi': bool, 'serie': n} pour la date (aujourd'hui)."""
    d = charger()
    jour = d.get("jour", {})
    resultat = jour.get(aujourd_hui(date))
    return {"fait": resultat is not None, "reussi": bool(resultat),
            "serie": int(d.get("serie_jour", 0))}


def probleme_du_jour(date=None):
    """Le meme probleme toute la journee (graine = la date)."""
    date = date or datetime.date.today()
    graine = int(date.strftime("%Y%m%d"))
    return puzzles.tirer(NIVEAU_DU_JOUR, hasard=random.Random(graine))


class SessionDefi:
    """Contre la montre, survie ou probleme du jour."""

    def __init__(self, mode, maintenant=None, date=None):
        self.mode = mode
        self.classe = False
        self.enchaine_sur_erreur = mode in (CHRONO, SURVIE)
        self.date = date
        self._reussis = 0
        self._rates = 0
        self._serie = 0
        self._meilleure = 0
        self.vies_restantes = VIES_SURVIE if mode == SURVIE else None
        self.niveau = DEPART_ECHELLE
        self.vus = set()
        self.gain = 0
        self.debut = None              # le chrono global part au 1er probleme
        self._maintenant = maintenant  # pour les tests (fonction -> secondes)
        self.nouveau_record = False
        self._fin_notee = False
        self.record_avant = record(mode) if mode != DU_JOUR else 0

    # --- temps
    def _heure(self):
        if self._maintenant is not None:
            return self._maintenant()
        import time
        return time.time()

    def demarrer(self):
        if self.debut is None:
            self.debut = self._heure()

    def temps_restant(self):
        """Secondes restantes (contre la montre), sinon None."""
        if self.mode != CHRONO:
            return None
        if self.debut is None:
            return DUREE_CHRONO
        return max(0.0, DUREE_CHRONO - (self._heure() - self.debut))

    def terminee(self):
        if self.mode == CHRONO:
            fini = self.temps_restant() <= 0
        elif self.mode == SURVIE:
            fini = self.vies_restantes <= 0
        else:
            fini = self._reussis + self._rates >= 1
        if fini:
            self._noter_la_fin()
        return fini

    def _noter_la_fin(self):
        if self._fin_notee:
            return
        self._fin_notee = True
        if self.mode == DU_JOUR:
            return
        try:
            import succes
            succes.verifier({"chrono_15": self.mode == CHRONO and self._reussis >= 15,
                             "survie_10": self.mode == SURVIE and self._reussis >= 10})
        except Exception as e:
            print("[SUCCES] %s" % e)
        if self._reussis > self.record_avant:
            self.nouveau_record = True
            d = charger()
            d["record_" + self.mode] = self._reussis
            enregistrer(d)

    def resume(self):
        """La phrase de fin de defi."""
        if self.mode == DU_JOUR:
            e = etat_du_jour(self.date)
            if e["reussi"]:
                return "Problème du jour réussi ! Série : %d jour%s." % (
                    e["serie"], "s" if e["serie"] > 1 else "")
            return "Raté pour aujourd'hui. Reviens demain pour un nouveau problème."
        debut = "Temps écoulé ! " if self.mode == CHRONO else "Trois fautes : fini ! "
        texte = debut + "%d problème%s trouvé%s." % (
            self._reussis, "s" if self._reussis > 1 else "", "s" if self._reussis > 1 else "")
        if self.nouveau_record:
            texte += " Nouveau record !"
        else:
            texte += " Record : %d." % max(self.record_avant, self._reussis)
        return texte

    # --- interface de puzzles.Session
    def classement(self):
        """Le gros chiffre du panneau : le score du defi."""
        return self._reussis

    def serie(self):
        return self._serie

    def meilleure_serie(self):
        return self._meilleure

    def reussis(self):
        return self._reussis

    def rates(self):
        return self._rates

    def pourcentage(self):
        total = self._reussis + self._rates
        return 100.0 * self._reussis / total if total else 0.0

    def deja_vus(self):
        return set(self.vus)

    def variation(self):
        return 0

    def nom_du_mode(self):
        return NOMS[self.mode]

    def compteurs(self):
        """La ligne sous le gros chiffre."""
        if self.mode == CHRONO:
            return "Trouvés : %d   Fautes : %d   Niveau %d   Record %d" % (
                self._reussis, self._rates, self.niveau, self.record_avant)
        if self.mode == SURVIE:
            return "Vies : %d/%d   Trouvés : %d   Niveau %d   Record %d" % (
                self.vies_restantes, VIES_SURVIE, self._reussis, self.niveau,
                self.record_avant)
        e = etat_du_jour(self.date)
        return "Série de jours réussis : %d" % e["serie"]

    def message_si_vide(self):
        if self.mode == DU_JOUR:
            return "Tu as déjà fait le problème du jour. Reviens demain !"
        return "Aucun problème trouvé."

    def tirer_un_puzzle(self, themes=None, hasard=None):
        if self.terminee():
            return None
        if self.mode == DU_JOUR:
            if etat_du_jour(self.date)["fait"]:
                return None
            p = probleme_du_jour(self.date)
        else:
            p = puzzles.tirer(self.niveau, hasard=hasard, deja_vus=self.vus)
        if p:
            self.vus.add(p.get("id"))
            self.demarrer()
        return p

    def noter_un_puzzle(self, puzzle, reussi, secondes=None, indice=False):
        self.gain = 0
        if not puzzle or self.terminee():
            return 0
        if reussi and not indice:
            self._reussis += 1
            self._serie += 1
            self._meilleure = max(self._meilleure, self._serie)
            self.niveau = min(puzzles.CLASSEMENT_MAXIMUM - 200,
                              self.niveau + PAS_ECHELLE.get(self.mode, 0))
        else:
            self._rates += 1
            self._serie = 0
            if self.vies_restantes is not None:
                self.vies_restantes -= 1
        if self.mode == DU_JOUR:
            d = charger()
            jours = d.setdefault("jour", {})
            jours[aujourd_hui(self.date)] = bool(reussi and not indice)
            hier = ((self.date or datetime.date.today())
                    - datetime.timedelta(days=1)).isoformat()
            if reussi and not indice:
                d["serie_jour"] = (int(d.get("serie_jour", 0)) + 1) if jours.get(hier) else 1
            else:
                d["serie_jour"] = 0
            enregistrer(d)
            if d["serie_jour"] >= 7:
                try:
                    import succes
                    succes.debloquer("jour_7")
                except Exception as e:
                    print("[SUCCES] %s" % e)
        self.terminee()
        return 0

    def payer_l_indice(self):
        return 0
