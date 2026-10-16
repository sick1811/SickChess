# captured_pieces.py - V7 : pieces prises et avantage materiel
#
# EN V5 : le comptage etait faux (les prises de Stockfish n'etaient pas
# enregistrees : 20 pieces prises, 8 comptees) et l'affichage debordait sur la
# pendule au-dela de quinze pieces.
# EN V7 : les pieces s'affichent dans les zones que la disposition leur donne,
# donc jamais par-dessus autre chose, quelle que soit la taille de la fenetre.
#
# AUCUNE FONCTION SUPPRIMEE : add_captured, get_material_advantage et draw.

import chess
import pygame

import apparence

VALEURS = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
           chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
ORDRE = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]

# Zones par defaut si la disposition ne les a pas encore fixees.
ZONE_HAUT_DEFAUT = (680, 100, 400, 70)
ZONE_BAS_DEFAUT = (680, 470, 400, 70)


class CapturedPieces:
    def __init__(self, chessboard):
        self.chessboard = chessboard
        self.captured_white = []   # pieces BLANCHES prises par les Noirs
        self.captured_black = []   # pieces NOIRES prises par les Blancs
        self.zone_haut = ZONE_HAUT_DEFAUT
        self.zone_bas = ZONE_BAS_DEFAUT
        self.theme = None
        self.font = None
        self._cache = {}
        # V7.1 : meme correction que pour les horloges. Les prises du joueur
        # affiche en bas doivent etre en bas, y compris plateau retourne.
        self.flipped = False

    # ------------------------------------------------------------------ donnees

    def add_captured(self, piece):
        if piece is None:
            return
        if piece.color == chess.WHITE:
            self.captured_white.append(piece)
        else:
            self.captured_black.append(piece)

    def clear(self):
        self.captured_white = []
        self.captured_black = []

    def get_material_advantage(self):
        """Positif = les Blancs menent."""
        points_blancs = sum(VALEURS.get(p.piece_type, 0) for p in self.captured_black)
        points_noirs = sum(VALEURS.get(p.piece_type, 0) for p in self.captured_white)
        return points_blancs - points_noirs

    def _triees(self, pieces):
        return sorted(pieces, key=lambda p: ORDRE.index(p.piece_type)
                      if p.piece_type in ORDRE else 99)

    # ------------------------------------------------------------------ dessin

    def _miniature(self, piece, taille):
        cle = (piece.symbol(), taille)
        if cle in self._cache:
            return self._cache[cle]
        source = self.chessboard.piece_images.get(piece.symbol())
        if source is None:
            return None
        image = pygame.transform.smoothscale(source, (taille, taille))
        self._cache[cle] = image
        return image

    def _serie(self, screen, pieces, zone, taille, largeur_utile):
        """Aligne les miniatures dans la zone, sans jamais en sortir."""
        x0, y0, largeur, hauteur = zone
        largeur = max(40, min(largeur, largeur_utile))
        pas = max(8, int(taille * 0.58))
        par_ligne = max(4, largeur // pas)
        lignes_possibles = max(1, hauteur // (taille + 2))
        x, y = x0, y0
        for index, piece in enumerate(self._triees(pieces)):
            ligne = index // par_ligne
            if ligne >= lignes_possibles:
                return
            if index and index % par_ligne == 0:
                x = x0
                y += taille + 2
            image = self._miniature(piece, taille)
            if image is not None:
                screen.blit(image, (x, y))
            x += pas

    def camp_en_bas(self):
        return chess.BLACK if self.flipped else chess.WHITE

    def prises_de(self, couleur):
        """Les pieces prises PAR ce camp (donc des pieces de l'autre couleur)."""
        return self.captured_black if couleur == chess.WHITE else self.captured_white

    def draw(self, screen):
        import ui

        t = self.theme or apparence.theme(getattr(self.chessboard, "theme_plateau", None))
        bas = self.camp_en_bas()
        haut = not bas

        taille = max(16, min(30, self.zone_haut[3] // 2))
        avantage = self.get_material_advantage()          # positif = Blancs mènent
        taille_texte = max(13, min(20, taille - 4))

        for couleur, zone in ((haut, self.zone_haut), (bas, self.zone_bas)):
            zone = tuple(zone)
            if zone[2] < 60 or zone[3] < 16:
                continue
            points = avantage if couleur == chess.WHITE else -avantage
            etiquette = "+%d" % points if points > 0 else ""
            largeur_etiquette = ui.mesurer(etiquette, taille_texte, gras=True)[0] + 8 \
                if etiquette else 0
            self._serie(screen, self.prises_de(couleur), zone, taille,
                        zone[2] - largeur_etiquette)
            if etiquette:
                ui.texte(screen, etiquette, zone[0] + zone[2],
                         zone[1] + max(0, (taille - taille_texte) // 2),
                         taille_texte, t.get("accent", (120, 220, 130)),
                         gras=True, ancre="droite")
