# sauvegarde.py - SickChess : reprendre une partie interrompue.
#
# Repris de V8_TURBO_3000 (V7). La partie en cours est ecrite toutes les cinq
# secondes dans partie_en_cours.json, et encore une fois a la fermeture du jeu.
# Au lancement suivant, le menu propose "Reprendre la partie", avec les
# pendules la ou tu les avais laissees. Le fichier est efface des que la partie
# se termine ou que tu reviens au menu de toi-meme.

import json
import os
import time

FICHIER = "partie_en_cours.json"
PERIODE = 5.0        # secondes entre deux enregistrements


def _dossier():
    try:
        from asset_manager import dossier_ecriture
        return dossier_ecriture()
    except Exception:
        return os.getcwd()


def chemin():
    return os.path.join(_dossier(), FICHIER)


def existe():
    return os.path.exists(chemin())


def effacer():
    try:
        if existe():
            os.remove(chemin())
        return True
    except OSError as e:
        print("[SAUVEGARDE] suppression impossible : %s" % e)
        return False


def enregistrer(board, mode_nom, reglages):
    """Ecrit l'etat de la partie en cours. False si rien a sauver."""
    if board is None or board.game_over or mode_nom not in ("stockfish", "hotseat"):
        return False
    if not board.move_history.moves:
        return False                     # aucun coup joue : rien a reprendre
    try:
        import chess
        propres = {cle: valeur for cle, valeur in (reglages or {}).items()
                   if isinstance(valeur, (str, int, float, bool)) or valeur is None}
        donnees = {
            "version": 1,
            "date": time.strftime("%d/%m/%Y %H:%M"),
            "mode": mode_nom,
            "reglages": propres,
            "fen_initiale": board.move_history.fen_initiale,
            "coups": list(board.move_history.moves),
            "flipped": bool(board.flipped),
            "ia_joue_blancs": bool(board.ia_joue_blancs),
            "temps_blancs": float(board.timer.time_left[chess.WHITE]),
            "temps_noirs": float(board.timer.time_left[chess.BLACK]),
            # avec_pendule et non active : une partie en pause garde sa cadence.
            "pendule_active": bool(getattr(board.timer, "avec_pendule",
                                           board.timer.active)),
            "increment": float(board.timer.increment),
            "indices_utilises": int(getattr(board, "indices_utilises", 0)),
            # 31/10 (s50) : la FEN seule ne dit pas toujours Freestyle (roi en e1,
            # tours en a1 / h1 : n° 414, 518...) ; on l'ecrit donc en clair.
            "freestyle": bool(board.board.chess960),
            "numero_freestyle": getattr(board, "numero_freestyle", None),
            "tournoi_fide": bool(getattr(board, "tournoi_fide", False)),
        }
        provisoire = chemin() + ".tmp"
        with open(provisoire, "w", encoding="utf-8") as f:
            json.dump(donnees, f, indent=2, ensure_ascii=False)
        os.replace(provisoire, chemin())  # jamais de fichier coupe en deux
        return True
    except Exception as e:
        print("[SAUVEGARDE] enregistrement impossible : %s" % e)
        return False


def lire():
    """Renvoie la sauvegarde, ou None."""
    if not existe():
        return None
    try:
        with open(chemin(), "r", encoding="utf-8") as f:
            donnees = json.load(f)
    except (OSError, ValueError) as e:
        print("[SAUVEGARDE] fichier illisible : %s" % e)
        return None
    if not isinstance(donnees, dict) or not donnees.get("coups") \
            or donnees.get("mode") not in ("stockfish", "hotseat"):
        return None
    return donnees


def resume(donnees):
    """'Contre l'ordinateur (1400 Elo) - coup 23 - 16/10/2026 14:02'."""
    if not donnees:
        return ""
    if donnees.get("mode") == "stockfish":
        elo = (donnees.get("reglages") or {}).get("elo")
        mode = "Contre l'ordinateur" + (" (%s Elo)" % elo if elo else "")
    else:
        mode = "À deux sur ce PC"
    coup = len(donnees.get("coups", [])) // 2 + 1
    return "%s  -  coup %d  -  %s" % (mode, coup, donnees.get("date", ""))


def appliquer(board, donnees):
    """Rejoue les coups sauvegardes sur un plateau neuf, sans son ni animation."""
    import chess
    if not donnees:
        return False
    import freestyle
    fen = donnees.get("fen_initiale")
    # 31/10 (s50) : l'indicateur de la sauvegarde d'abord ; une sauvegarde
    # d'avant (sans lui) est jugee a sa FEN, comme avant.
    libre = donnees.get("freestyle")
    if libre is None:
        libre = freestyle.est_freestyle_fen(fen)
    if fen and (fen != chess.STARTING_FEN or libre):
        board.board.chess960 = bool(libre)
        board.board.set_fen(fen)
        board.move_history.set_fen_initiale(fen)
    if libre and donnees.get("numero_freestyle") is not None:
        try:
            board.numero_freestyle = int(donnees["numero_freestyle"])
        except (TypeError, ValueError):
            print("[SAUVEGARDE] numero Freestyle illisible, ignore")
        board.tournoi_fide = bool(donnees.get("tournoi_fide", board.tournoi_fide))

    sons, anim = board.sounds.actif, board.animation.active
    board.sounds.actif = False
    board.animation.active = False
    for uci in donnees.get("coups", []):
        try:
            coup = chess.Move.from_uci(uci)
        except ValueError:
            break
        if coup not in board.board.legal_moves:
            print("[SAUVEGARDE] coup %s impossible, reprise partielle" % uci)
            break
        board.make_move(coup)
    board.sounds.actif = sons
    board.animation.active = anim
    board.animation.clear()
    board.highlights.clear_legal_moves()

    board.flipped = bool(donnees.get("flipped", False))
    board.ia_joue_blancs = bool(donnees.get("ia_joue_blancs", False))
    board.indices_utilises = int(donnees.get("indices_utilises", 0))

    timer = board.timer
    timer.time_left[chess.WHITE] = float(donnees.get("temps_blancs",
                                                     timer.initial_time))
    timer.time_left[chess.BLACK] = float(donnees.get("temps_noirs",
                                                     timer.initial_time))
    timer.active = bool(donnees.get("pendule_active", True))
    timer.avec_pendule = timer.active
    timer.increment = float(donnees.get("increment", 0))
    timer.demarree = bool(board.board.move_stack)
    try:
        import pygame
        timer.last_update = pygame.time.get_ticks()
    except Exception:
        pass
    print("[SAUVEGARDE] partie reprise (%d demi-coups)" % len(board.board.move_stack))
    return True


class Sauvegardeur:
    """Enregistre la partie regulierement, sans y penser."""

    def __init__(self, periode=PERIODE):
        self.periode = periode
        self._dernier = 0.0

    def peut_etre(self, board, mode_nom, reglages):
        maintenant = time.time()
        if maintenant - self._dernier < self.periode:
            return False
        self._dernier = maintenant
        return enregistrer(board, mode_nom, reglages)
