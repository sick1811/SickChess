# resume_coach.py - SickChess 24/10 (travail p27) : le resume du coach.
#
# Des la fin de la partie, la carte de fin (ecran_fin.py) donne trois lignes a
# lire tout de suite, sans ouvrir la revue :
#   1. l'ouverture jouee (et combien de coups de theorie) ;
#   2. le plus gros moment du joueur : sa pire faute (avec le meilleur coup),
#      ou son plus beau coup s'il n'a fait aucune faute ;
#   3. sa precision (« provisoire » tant que l'analyse tourne), comparee a
#      ses 10 dernieres parties analysees (« ta meilleure des 10 dernieres »).
# Les phrases sont entieres (une par cas) : elles se traduisent en anglais.
# Les precisions passees se lisent UNE fois, dans un fil (jamais au dessin).

import os
import threading

import chess

NOMBRE_DE_PARTIES = 10
MEME_NIVEAU = 2.0                 # +/- 2 points : « comme ta moyenne »

FAUTES = {
    "gaffe": "Plus gros moment : %s ?? (gaffe), mieux : %s",
    "manque": "Plus gros moment : %s (occasion manquée), mieux : %s",
    "erreur": "Plus gros moment : %s ? (erreur), mieux : %s",
    "imprecision": "Plus gros moment : %s ?! (imprécision), mieux : %s",
}
BEAUX_COUPS = {
    "brillant": "Plus beau coup : %s !! (brillant)",
    "tres_bon": "Plus beau coup : %s ! (très bien)",
}
GRAVITE = {"imprecision": 1, "erreur": 2, "manque": 3, "gaffe": 4}


def nom_du_coup(detail):
    """'23. Fxh7' (Blancs) ou '23... Fxh7' (Noirs)."""
    return "%d%s %s" % (detail["numero"], "." if detail["par_les_blancs"] else "...",
                        detail["san"])


def ligne_ouverture(sans, depuis_le_depart=True):
    """'Ouverture : C60 - Partie espagnole  (5 coups de théorie)'."""
    if not sans or not depuis_le_depart:
        return ""
    import ouvertures
    reconnu = ouvertures.reconnaitre(sans)
    if not reconnu:
        return "Ouverture : sortie du livre dès le premier coup"
    combien = (reconnu[2] + 1) // 2
    # Le nom court (« C77 - Partie espagnole ») : la variante entiere ne tient pas.
    nom = ouvertures.etiquette(sans).split(",")[0].split(":")[0].strip()
    if combien <= 1:
        return "Ouverture : %s  (1 coup de théorie)" % nom
    return "Ouverture : %s  (%d coups de théorie)" % (nom, combien)


def ligne_moment(details, camp, terminee):
    """La pire faute du joueur (camp : True = Blancs, False = Noirs, None =
    les deux), ou son plus beau coup, ou '' tant que rien n'est juge."""
    juges = [d for d in details if d.get("pret")
             and (camp is None or d["par_les_blancs"] == camp)]
    fautes = [d for d in juges if d.get("note") in FAUTES]
    if fautes:
        pire = max(fautes, key=lambda d: (d.get("perte") or 0.0, GRAVITE[d["note"]]))
        mieux = pire.get("meilleur_san") or "?"
        return FAUTES[pire["note"]] % (nom_du_coup(pire), mieux)
    for note in ("brillant", "tres_bon"):
        beaux = [d for d in juges if d.get("note") == note]
        if beaux:
            return BEAUX_COUPS[note] % nom_du_coup(beaux[0])
    if terminee and juges:
        return "Aucune faute : bravo !"
    if not terminee:
        return "Plus gros moment : analyse en cours..."
    return ""


def ligne_precision(precision, terminee, passees):
    """'Précision : 84 %, ta meilleure de tes 10 dernières parties'."""
    if precision is None:
        return ""
    p = int(round(precision))
    if not terminee:
        return "Précision provisoire : %d %% (analyse en cours)" % p
    passees = [x for x in (passees or []) if x is not None]
    if not passees:
        return "Précision : %d %%" % p
    if precision > max(passees):
        if len(passees) == 1:
            return "Précision : %d %%, mieux que ta partie précédente" % p
        return "Précision : %d %%, ta meilleure de tes %d dernières parties" % (p, len(passees))
    moyenne = sum(passees) / len(passees)
    m = int(round(moyenne))
    if precision >= moyenne + MEME_NIVEAU:
        return "Précision : %d %%, au-dessus de ta moyenne (%d %%)" % (p, m)
    if precision <= moyenne - MEME_NIVEAU:
        return "Précision : %d %%, sous ta moyenne (%d %%)" % (p, m)
    return "Précision : %d %%, comme ta moyenne (%d %%)" % (p, m)


def lignes(analyseur, camp, passees=None):
    """Les trois lignes du coach pour cet analyseur (AnalyseurPartie)."""
    if analyseur is None or getattr(analyseur, "erreur", None):
        return []
    terminee = analyseur.terminee()
    details = [analyseur.detail(i) for i in range(analyseur.nombre_de_coups())]
    depart = getattr(analyseur, "fens", [chess.STARTING_FEN])[0]
    sortie = [ligne_ouverture(list(analyseur.sans),
                              depart.split(" ")[0] == chess.STARTING_FEN.split(" ")[0]),
              ligne_moment(details, camp, terminee)]
    if camp is not None:
        rapport = analyseur.rapport()
        sortie.append(ligne_precision(rapport["blancs" if camp else "noirs"]["precision"],
                                      terminee, passees))
    return [s for s in sortie if s]


# ------------------------------------------------------- parties precedentes

def precisions_passees(exclure="", nombre=NOMBRE_DE_PARTIES, parties=None):
    """Precision du joueur dans ses `nombre` dernieres parties analysees (la
    plus recente d'abord), sans la partie `exclure` (chemin de son PGN)."""
    import historique_parties
    import statistiques
    if parties is None:
        parties = historique_parties.lister(60)
    exclure = os.path.normcase(os.path.abspath(exclure)) if exclure else ""
    sortie = []
    for p in parties:
        if len(sortie) >= nombre:
            break
        if p.get("camp") not in ("blanc", "noir"):
            continue
        if exclure and os.path.normcase(os.path.abspath(p.get("chemin", ""))) == exclure:
            continue
        try:
            a = statistiques._analyse(p)
        except Exception as e:
            print("[COACH] %s : %s" % (p.get("fichier"), e))
            a = None
        if a and a.get("precision") is not None:
            sortie.append(a["precision"])
    return sortie


class PrecisionsPassees:
    """Lit les precisions passees dans un fil : la carte de fin ne bloque pas."""

    def __init__(self, exclure="", lire=precisions_passees):
        self.valeurs = None
        self._fil = threading.Thread(target=self._lire, args=(exclure, lire), daemon=True)
        self._fil.start()

    def _lire(self, exclure, lire):
        try:
            self.valeurs = lire(exclure)
        except Exception as e:
            print("[COACH] %s" % e)
            self.valeurs = []

    def attendre(self, secondes=10):
        self._fil.join(secondes)
        return self.valeurs
