# enregistrement.py - SickChess : ce qui se passe quand une partie se termine.
#
# Appele une seule fois par partie, par game_manager, des que le plateau passe
# en "partie finie" :
#   1. contre l'ordinateur, la partie entre dans le profil (profil.json) : le
#      classement Elo estime bouge, les statistiques aussi ;
#   2. dans tous les cas, la partie est ecrite en PGN dans parties/, pour
#      l'ecran "Mes parties".
#
# Partie a deux sur ce PC : PGN seulement. Le profil ne sait pas lequel des
# deux joueurs tu etais, il ne compte donc que tes parties contre l'ordinateur.
# Une partie de moins de deux demi-coups (abandon immediat) n'est pas gardee.

import historique_parties
from profil import get_profil


def enregistrer_la_partie(plateau, mode):
    """Renvoie {'classee', 'elo_avant', 'elo_apres', 'pgn'} ou None."""
    historique = getattr(plateau, "move_history", None)
    if historique is None or len(historique.moves) < 2:
        return None
    resultat = plateau.result or "*"
    raison = plateau.game_over_reason or ""
    reglages = getattr(plateau, "reglages", None) or {}
    try:
        cadence = plateau.timer.description_cadence()
    except Exception:
        cadence = ""

    profil = get_profil()
    infos = {"mode": mode, "classee": False, "elo_avant": profil.elo,
             "elo_apres": profil.elo, "pgn": ""}

    if mode == "stockfish":
        couleur = "noir" if getattr(plateau, "ia_joue_blancs", False) else "blanc"
        try:
            elo_ia = int(reglages.get("elo") or 1500)
        except (TypeError, ValueError):
            elo_ia = 1500
        # Une partie ou l'on a demande des indices compte dans les
        # statistiques, mais ne fait pas bouger le classement.
        classee = int(getattr(plateau, "indices_utilises", 0) or 0) == 0
        elo_avant = profil.elo
        profil.ajouter_partie(adversaire="Ordinateur", elo_adversaire=elo_ia,
                              resultat=resultat, couleur=couleur,
                              nombre_de_coups=len(historique.moves),
                              classee=classee, raison=raison)
        infos.update(classee=classee, elo_avant=elo_avant, elo_apres=profil.elo)
        blancs, noirs = (profil.nom, "Ordinateur") if couleur == "blanc" \
            else ("Ordinateur", profil.nom)
        elo_b, elo_n = (elo_avant, elo_ia) if couleur == "blanc" \
            else (elo_ia, elo_avant)
        infos["pgn"] = historique_parties.enregistrer(
            historique, blancs, noirs, resultat, elo_b, elo_n, cadence,
            classee=classee, camp_du_joueur=couleur, raison=raison,
            mode="ordinateur")
        print("[PROFIL] partie enregistree : %d -> %d Elo%s"
              % (elo_avant, profil.elo, "" if classee else " (non classee)"))
        # 17/10 (p19) : les succes
        try:
            import succes
            gagne = resultat == ("1-0" if couleur == "blanc" else "0-1")
            succes.verifier({
                "premiere_victoire": gagne,
                "victoire_1500": gagne and elo_ia >= 1500,
                "victoire_2000": gagne and elo_ia >= 2000,
                "victoire_mat": gagne and "MAT" in raison.upper(),
            })
        except Exception as e:
            print("[SUCCES] %s" % e)
    else:
        infos["pgn"] = historique_parties.enregistrer(
            historique, "Blancs", "Noirs", resultat, cadence=cadence,
            classee=False, raison=raison, mode="à deux")
    return infos


def texte_classement(infos):
    """'Classement : 1200 -> 1214  (+14)' pour la carte de fin, ou ''."""
    if not infos or infos.get("mode") != "stockfish":
        return ""
    if not infos.get("classee"):
        return "Partie non classee (indices utilises)"
    ecart = infos["elo_apres"] - infos["elo_avant"]
    return "Classement : %d -> %d  (%s%d)" % (infos["elo_avant"], infos["elo_apres"],
                                             "+" if ecart >= 0 else "", ecart)
