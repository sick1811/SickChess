# historique_parties.py - SickChess : chaque partie finie, rangee en PGN.
#
# Repris de V8_TURBO_3000 (V7.2) et nettoye. Chaque partie terminee est ecrite
# dans son propre fichier .pgn, dans le dossier parties/ a cote du jeu. Le PGN
# est le format standard des echecs : ces fichiers s'ouvrent aussi dans
# lichess, chess.com, SCID...
#
# Un fichier par partie : on peut en envoyer une seule a un ami, en supprimer
# une, et un fichier abime ne fait pas perdre les autres.
#
# En-tete propre a SickChess : [Joueur "blanc"|"noir"] dit quel camp etait
# celui du profil. C'est ce qui permet d'afficher Victoire / Defaite meme si tu
# as change de nom depuis. Les parties a deux sur ce PC n'en ont pas.

import datetime
import io
import os
import re

DOSSIER = "parties"
MAX_FICHIERS = 400          # au-dela, on efface les plus vieilles


def _dossier_de_base():
    try:
        from asset_manager import dossier_ecriture
        return dossier_ecriture()
    except Exception:
        return os.getcwd()


def dossier_parties():
    chemin = os.path.join(_dossier_de_base(), DOSSIER)
    try:
        os.makedirs(chemin, exist_ok=True)
    except OSError:
        pass
    return chemin


def _nom_de_fichier(blancs, noirs, quand):
    propre = re.sub(r"[^A-Za-z0-9]+", "-", "%s-%s" % (blancs, noirs)).strip("-")
    base = "%s_%s" % (quand.strftime("%Y-%m-%d_%Hh%M"), propre[:40] or "partie")
    nom = base + ".pgn"
    numero = 2
    while os.path.exists(os.path.join(dossier_parties(), nom)):
        nom = "%s_%d.pgn" % (base, numero)        # deux parties la meme minute
        numero += 1
    return nom


def enregistrer(move_history, blancs="Blancs", noirs="Noirs", resultat="*",
                elo_blancs=None, elo_noirs=None, cadence="", classee=False,
                camp_du_joueur="", raison="", mode=""):
    """Ecrit la partie en PGN. Renvoie le chemin du fichier, ou ""."""
    if move_history is None or not getattr(move_history, "moves", None):
        return ""
    try:
        corps = move_history.export_pgn(blancs, noirs, resultat)
    except Exception as e:
        print("[HISTORIQUE] PGN impossible : %s" % e)
        return ""
    if not corps:
        return ""

    maintenant = datetime.datetime.now()
    entetes = [
        ("Event", "Partie classee" if classee else "Partie amicale"),
        ("Site", "SickChess"),
        ("Date", maintenant.strftime("%Y.%m.%d")),
        ("Time", maintenant.strftime("%H:%M:%S")),
        ("White", blancs),
        ("Black", noirs),
        ("Result", resultat or "*"),
    ]
    if elo_blancs:
        entetes.append(("WhiteElo", str(int(elo_blancs))))
    if elo_noirs:
        entetes.append(("BlackElo", str(int(elo_noirs))))
    if cadence:
        entetes.append(("TimeControl", str(cadence)))
    if raison:
        entetes.append(("Termination", str(raison)))
    fen = getattr(move_history, "fen_initiale", None)
    if fen:
        import chess
        if fen != chess.STARTING_FEN:
            entetes.append(("SetUp", "1"))
            entetes.append(("FEN", fen))
    # Ouverture : les deux etiquettes normalisees ECO et Opening.
    try:
        import ouvertures
        for cle, valeur in sorted(ouvertures.entetes_pgn(
                list(getattr(move_history, "sans", []) or [])).items()):
            entetes.append((cle, valeur))
    except Exception as souci:
        print("[HISTORIQUE] ouverture non reconnue : %s" % souci)
    # En-tetes propres a SickChess (les autres logiciels les ignorent).
    entetes.append(("Classee", "oui" if classee else "non"))
    if camp_du_joueur in ("blanc", "noir"):
        entetes.append(("Joueur", camp_du_joueur))
    if mode:
        entetes.append(("Mode", mode))

    # On ne garde du PGN produit que les COUPS : les en-tetes sont les notres.
    coups = "\n".join(ligne for ligne in corps.splitlines()
                      if not ligne.startswith("["))
    texte = "\n".join('[%s "%s"]' % (cle, str(valeur).replace('"', "'"))
                      for cle, valeur in entetes)
    texte += "\n\n" + coups.strip() + "\n"

    chemin = os.path.join(dossier_parties(),
                          _nom_de_fichier(blancs, noirs, maintenant))
    try:
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(texte)
    except OSError as e:
        print("[HISTORIQUE] enregistrement impossible : %s" % e)
        return ""
    print("[HISTORIQUE] partie enregistree : %s" % os.path.basename(chemin))
    _faire_le_menage()
    return chemin


def _faire_le_menage():
    """Garde les MAX_FICHIERS parties les plus recentes."""
    try:
        fichiers = [os.path.join(dossier_parties(), n)
                    for n in os.listdir(dossier_parties()) if n.endswith(".pgn")]
    except OSError:
        return 0
    if len(fichiers) <= MAX_FICHIERS:
        return 0
    fichiers.sort(key=os.path.getmtime)
    efface = 0
    for chemin in fichiers[:len(fichiers) - MAX_FICHIERS]:
        try:
            os.remove(chemin)
            efface += 1
        except OSError:
            pass
    return efface


# ---------------------------------------------------------------- lecture

def lire_entetes(chemin):
    """Les en-tetes d'un PGN, en dictionnaire. {} si illisible."""
    entetes = {}
    try:
        with open(chemin, "r", encoding="utf-8", errors="replace") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne:
                    if entetes:
                        break
                    continue
                trouve = re.match(r'^\[(\w+)\s+"(.*)"\]$', ligne)
                if trouve:
                    entetes[trouve.group(1)] = trouve.group(2)
                else:
                    break
    except OSError:
        return {}
    return entetes


def _verdict(resultat, camp):
    """'victoire', 'nulle', 'defaite' du point de vue du joueur, ou ''."""
    if camp not in ("blanc", "noir"):
        return ""
    if resultat == "1/2-1/2":
        return "nulle"
    if resultat in ("1-0", "0-1"):
        return "victoire" if (resultat == "1-0") == (camp == "blanc") \
            else "defaite"
    return ""


def lister(nombre=200):
    """Les dernieres parties, la plus recente d'abord (une entree par fichier)."""
    try:
        noms = [n for n in os.listdir(dossier_parties()) if n.endswith(".pgn")]
    except OSError:
        return []
    chemins = sorted((os.path.join(dossier_parties(), n) for n in noms),
                     key=os.path.getmtime, reverse=True)
    parties = []
    for chemin in chemins[:nombre]:
        e = lire_entetes(chemin)
        camp = e.get("Joueur", "")
        date = e.get("Date", "").replace(".", "/")
        if len(date) == 10:                       # 2026/10/16 -> 16/10/2026
            date = "%s/%s/%s" % (date[8:10], date[5:7], date[0:4])
        parties.append({
            "chemin": chemin,
            "fichier": os.path.basename(chemin),
            "date": ("%s %s" % (date, e.get("Time", "")[:5])).strip(),
            "blancs": e.get("White", "?"),
            "noirs": e.get("Black", "?"),
            "elo_blancs": e.get("WhiteElo", ""),
            "elo_noirs": e.get("BlackElo", ""),
            "resultat": e.get("Result", "*"),
            "classee": e.get("Classee", "non") == "oui",
            "cadence": e.get("TimeControl", ""),
            "raison": e.get("Termination", ""),
            "eco": e.get("ECO", ""),
            "ouverture": e.get("Opening", ""),
            "camp": camp,
            "verdict": _verdict(e.get("Result", "*"), camp),
        })
    return parties


def resume(partie):
    """'Julien 1-0 Stockfish (1400)'."""
    def nom(cle_nom, cle_elo):
        n = partie.get(cle_nom, "?")
        elo = partie.get(cle_elo)
        return "%s (%s)" % (n, elo) if elo else n
    return "%s  %s  %s" % (nom("blancs", "elo_blancs"),
                           partie.get("resultat", "*"),
                           nom("noirs", "elo_noirs"))


def ouverture(partie):
    """'C60 - Partie espagnole', ou '' si inconnue."""
    eco = (partie or {}).get("eco") or ""
    nom = (partie or {}).get("ouverture") or ""
    if nom and eco:
        return "%s - %s" % (eco, nom)
    return nom or eco


def lire_partie(chemin):
    """Relit les coups d'un fichier. Renvoie ({'fen', 'coups'}, erreur)."""
    try:
        import chess.pgn
        with open(chemin, "r", encoding="utf-8", errors="replace") as f:
            jeu = chess.pgn.read_game(io.StringIO(f.read()))
    except OSError as souci:
        return None, "Fichier illisible : %s" % souci
    except Exception as souci:
        return None, "PGN illisible : %s" % souci
    if jeu is None:
        return None, "Ce fichier ne contient aucune partie."
    plateau = jeu.board()
    fen = plateau.fen()
    coups = []
    for coup in jeu.mainline_moves():
        if coup not in plateau.legal_moves:
            break
        coups.append(coup.uci())
        plateau.push(coup)
    if not coups:
        return None, "Cette partie ne contient aucun coup à rejouer."
    return {"fen": fen, "coups": coups}, ""

