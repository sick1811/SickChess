# classements.py - SickChess 24/10 (travail p37) : les classements Steam.
#
# Trois classements, visibles dans Problemes -> « Classements » :
#   - Problemes        : ton classement des problemes (mode classe), la valeur du jour ;
#   - Contre la montre : ton record (problemes trouves en 3 minutes) ;
#   - Survie           : ton record (problemes trouves avant 3 fautes).
# Pour chacun, trois vues : Mondial (les 10 premiers), Amis, Autour de moi.
#
# Ils marchent DES MAINTENANT, meme avec le numero de test 480 : Steam les cree
# a la premiere demande (FindOrCreateLeaderboard). Le jour ou SickChess aura son
# numero, ils seront recrees a vide pour lui (et a nommer dans Steamworks pour
# apparaitre sur la page communaute : voir docs/SUCCES_STEAM.md).
#
# Rien n'attend jamais Steam : un score est mis de cote, puis envoye quand
# Steam repond (suivre(), appele a chaque image par le bandeau d'invitations).
# Sans Steam, les scores restent dans le jeu (records, classement) et partent
# a la connexion suivante (rattraper()).

import time

TABLEAUX = [
    # (cle, nom API Steam, titre, methode d'envoi)
    ("problemes", "SICKCHESS_PROBLEMES", "Problèmes", "remplacer"),
    ("chrono", "SICKCHESS_CONTRE_LA_MONTRE", "Contre la montre", "meilleur"),
    ("survie", "SICKCHESS_SURVIE", "Survie", "meilleur"),
]
VUES = [
    # (cle, titre, demande Steam, debut, fin)
    ("mondial", "Mondial", 0, 1, 10),
    ("amis", "Amis", 2, 1, 100),
    ("autour", "Autour de moi", 1, -4, 5),
]
DELAI_S = 15            # sans reponse de Steam : on le dit
FRAICHEUR_S = 30        # un classement telecharge reste valable 30 s


def _tableau(cle):
    return next(t for t in TABLEAUX if t[0] == cle)


class Classements:
    def __init__(self, steam=None):
        self._steam = steam
        self.poignees = {}         # tableau -> numero Steam du classement
        self.recherches = {}       # appel -> tableau
        self.a_envoyer = {}        # tableau -> score en attente
        self.envois = {}           # appel -> tableau
        self.telechargements = {}  # appel -> (tableau, vue)
        self.resultats = {}        # (tableau, vue) -> {etat, lignes, quand}
        self.voulus = set()        # (tableau, vue) demandes avant que la poignee soit la
        self.derniers_envois = {}  # tableau -> {score, rang}

    def steam(self):
        if self._steam is None:
            import steam as module_steam
            self._steam = module_steam.instance()
        return self._steam

    # --------------------------------------------------------- envois

    def envoyer(self, tableau, score):
        """Met un score de cote ; il part des que Steam est la."""
        score = int(score)
        if tableau == "problemes" or score > int(self.a_envoyer.get(tableau, -1)):
            self.a_envoyer[tableau] = score
        self.suivre()

    def demander(self, tableau, vue, forcer=False):
        """Lance le telechargement d'une vue (s'il n'est pas frais)."""
        cle = (tableau, vue)
        deja = self.resultats.get(cle)
        if deja and not forcer and deja["etat"] == "attente" \
                and time.monotonic() - deja["quand"] < DELAI_S:
            return
        if deja and not forcer and deja["etat"] == "pret" \
                and time.monotonic() - deja["quand"] < FRAICHEUR_S:
            return
        self.resultats[cle] = {"etat": "attente", "lignes": list((deja or {}).get("lignes", [])),
                               "quand": time.monotonic()}
        self.voulus.add(cle)
        self.suivre()

    def resultat(self, tableau, vue):
        """{etat: attente / pret / erreur, lignes: [{rang, joueur, score, nom, moi}]}"""
        r = self.resultats.get((tableau, vue))
        if r and r["etat"] == "attente" and time.monotonic() - r["quand"] > DELAI_S:
            r["etat"] = "erreur"
        return r or {"etat": "attente", "lignes": [], "quand": 0}

    # --------------------------------------------------------- suivi

    def suivre(self):
        """A chaque image : fait avancer les demandes en cours."""
        s = self.steam()
        if not getattr(s, "actif", False):
            return
        for ev in s.evenements("classement_trouve", "score_envoye", "classement_telecharge",
                               "classement_rate"):
            self._reponse(ev)
        besoin = set(self.a_envoyer) | {t for t, _v in self.voulus}
        for tableau in besoin:
            if tableau not in self.poignees and tableau not in self.recherches.values():
                appel = s.chercher_classement(_tableau(tableau)[1])
                if appel:
                    self.recherches[appel] = tableau
        for tableau, score in list(self.a_envoyer.items()):
            if tableau in self.poignees and tableau not in self.envois.values():
                methode = 2 if _tableau(tableau)[3] == "remplacer" else 1
                appel = s.envoyer_score(self.poignees[tableau], score, methode)
                if appel:
                    self.envois[appel] = tableau
                    del self.a_envoyer[tableau]
        for cle in list(self.voulus):
            tableau, vue = cle
            if tableau in self.poignees:
                _v, _t, demande, debut, fin = next(v for v in VUES if v[0] == vue)
                appel = s.telecharger_classement(self.poignees[tableau], demande, debut, fin)
                if appel:
                    self.telechargements[appel] = cle
                    self.voulus.discard(cle)

    def _reponse(self, ev):
        appel = ev.get("appel")
        if ev["type"] == "classement_rate":
            tableau = self.recherches.pop(appel, None) or self.envois.pop(appel, None)
            cle = self.telechargements.pop(appel, None)
            if cle:
                self.resultats[cle] = dict(self.resultats.get(cle, {}), etat="erreur",
                                           quand=time.monotonic())
            if tableau:
                print("[CLASSEMENTS] Steam n'a pas repondu pour %s" % tableau)
        elif ev["type"] == "classement_trouve":
            tableau = self.recherches.pop(appel, None)
            if tableau and ev.get("ok") and ev.get("classement"):
                self.poignees[tableau] = ev["classement"]
        elif ev["type"] == "score_envoye":
            tableau = self.envois.pop(appel, None)
            if tableau:
                self.derniers_envois[tableau] = {"score": ev.get("score"), "rang": ev.get("rang")}
                print("[CLASSEMENTS] %s : %s envoye (rang %s)" % (tableau, ev.get("score"),
                                                                 ev.get("rang")))
                # Les vues de ce classement ne sont plus a jour.
                for cle in list(self.resultats):
                    if cle[0] == tableau:
                        self.resultats[cle]["quand"] = 0
        elif ev["type"] == "classement_telecharge":
            cle = self.telechargements.pop(appel, None)
            if cle:
                s = self.steam()
                moi = s.mon_id() if hasattr(s, "mon_id") else 0
                lignes = [dict(l, moi=l["joueur"] == moi) for l in ev.get("lignes", [])]
                self.resultats[cle] = {"etat": "pret", "lignes": lignes, "quand": time.monotonic()}

    def nom(self, joueur):
        """Le nom Steam d'un joueur (demande a Steam s'il n'est pas un ami)."""
        s = self.steam()
        try:
            nom = s.nom_de(joueur)
            if not nom or nom == "[unknown]":
                s.demander_le_nom(joueur)
                return "..."
            return nom
        except Exception:
            return "?"


_INSTANCE = []


def instance():
    if not _INSTANCE:
        _INSTANCE.append(Classements())
    return _INSTANCE[0]


def envoyer(tableau, score):
    """Appele par les problemes (sans jamais bloquer ni planter le jeu)."""
    try:
        instance().envoyer(tableau, score)
    except Exception as e:
        print("[CLASSEMENTS] %s" % e)


def rattraper(steam):
    """A la connexion a Steam : le classement et les records du joueur partent
    (meme ceux faits sans Steam). Steam garde le meilleur des records."""
    import modes_problemes
    import puzzles
    c = instance()
    if c._steam is None:
        c._steam = steam
    score = puzzles.charger_le_score()
    if int(score.get("reussis", 0)) + int(score.get("rates", 0)) > 0:
        c.envoyer("problemes", int(score.get("classement", puzzles.CLASSEMENT_DEPART)))
    for mode in ("chrono", "survie"):
        record = modes_problemes.record(mode)
        if record > 0:
            c.envoyer(mode, record)
