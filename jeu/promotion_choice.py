# promotion_choice.py - V6 : NOUVEAU FICHIER
#
# POURQUOI CE FICHIER (bug C3 du rapport) :
# En V5, le joueur ne pouvait PAS promouvoir un pion. Le coup etait construit
# avec chess.Move(depart, arrivee) sans pièce de promotion, or "e7e8" n'est pas
# un coup legal aux echecs : il faut "e7e8q". Le coup etait donc rejete par
# make_move et le son "coup interdit" se declenchait. Teste : un pion blanc en
# a7 ne pouvait jamais atteindre a8.
#
# Ce panneau s'ouvre sur la case d'arrivee et propose Dame / Tour / Fou /
# Cavalier, comme sur Lichess et Chess.com.

import chess
import pygame

import board_geometry as geo

ORDRE = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
NOMS = {chess.QUEEN: "Dame", chess.ROOK: "Tour",
        chess.BISHOP: "Fou", chess.KNIGHT: "Cavalier"}
SYMBOLES = {chess.QUEEN: "q", chess.ROOK: "r", chess.BISHOP: "b", chess.KNIGHT: "n"}

FOND = (248, 246, 242)
FOND_SURVOL = (255, 232, 170)
BORDURE = (60, 48, 36)
VOILE = (0, 0, 0, 120)


class PromotionChoice:
    """Petit panneau de choix de la piece de promotion."""

    def __init__(self, chessboard):
        self.chessboard = chessboard
        self.actif = False
        self.premouvement = False
        self.from_square = None
        self.to_square = None
        self.couleur = chess.WHITE
        # 31/10 : True quand le choix est pour un coup prepare d'avance.
        self.premouvement = False
        self.cases = []          # [(pygame.Rect, type_de_piece)]
        self.survole = None
        self.font = None

    # ------------------------------------------------------------------ etat

    def est_actif(self):
        return self.actif

    def ouvrir(self, from_square, to_square, couleur, premouvement=False):
        self.actif = True
        self.premouvement = premouvement
        self.from_square = from_square
        self.to_square = to_square
        self.couleur = couleur
        self.survole = None
        self._calculer_cases()

    def fermer(self):
        self.actif = False
        self.from_square = None
        self.to_square = None
        self.cases = []
        self.survole = None

    def _calculer_cases(self):
        """Empile les 4 choix depuis la case d'arrivee, vers le bas si possible."""
        sq = self.chessboard.SQ_SIZE
        x, y = geo.case_vers_pixel(self.to_square, sq, self.chessboard.flipped)
        # V7.1 : la comparaison se faisait avec 8*sq alors que y est une
        # coordonnee d'ecran. Depuis que le plateau n'est plus colle en haut a
        # gauche, le panneau sortait du plateau vers le bas.
        vers_le_bas = (y + 4 * sq) <= (geo.ORIGINE_Y + 8 * sq)
        self.cases = []
        for i, piece in enumerate(ORDRE):
            case_y = y + i * sq if vers_le_bas else y - i * sq
            self.cases.append((pygame.Rect(x, case_y, sq, sq), piece))

    # ------------------------------------------------------------------ souris

    def survol(self, pos):
        self.survole = None
        for rect, piece in self.cases:
            if rect.collidepoint(pos):
                self.survole = piece
                return piece
        return None

    def handle_event(self, event):
        """Renvoie le type de piece choisi, "annule", ou None."""
        if not self.actif:
            return None
        if event.type == pygame.MOUSEMOTION:
            self.survol(event.pos)
            return None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "annule"
            raccourcis = {pygame.K_d: chess.QUEEN, pygame.K_q: chess.QUEEN,
                          pygame.K_t: chess.ROOK, pygame.K_r: chess.ROOK,
                          pygame.K_f: chess.BISHOP, pygame.K_b: chess.BISHOP,
                          pygame.K_c: chess.KNIGHT, pygame.K_n: chess.KNIGHT}
            if event.key in raccourcis:
                return raccourcis[event.key]
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, piece in self.cases:
                if rect.collidepoint(event.pos):
                    return piece
            return "annule"    # clic a cote = on annule la promotion
        return None

    # ------------------------------------------------------------------ dessin

    def draw(self, screen):
        if not self.actif:
            return
        sq = self.chessboard.SQ_SIZE

        # Voile sombre sur le plateau pour montrer qu'il faut choisir.
        cote = 8 * sq
        voile = pygame.Surface((cote, cote), pygame.SRCALPHA)
        voile.fill(VOILE)
        screen.blit(voile, (geo.ORIGINE_X, geo.ORIGINE_Y))

        if self.font is None:
            self.font = pygame.font.SysFont("Arial", 13, bold=True)

        images = getattr(self.chessboard, "piece_images", {})
        for rect, piece in self.cases:
            couleur_fond = FOND_SURVOL if self.survole == piece else FOND
            pygame.draw.rect(screen, couleur_fond, rect)
            pygame.draw.rect(screen, BORDURE, rect, 2)

            symbole = SYMBOLES[piece]
            cle = symbole.upper() if self.couleur == chess.WHITE else symbole
            if cle in images:
                image = images[cle]
                screen.blit(image, (rect.x + (sq - image.get_width()) // 2,
                                    rect.y + (sq - image.get_height()) // 2))
            else:
                texte = self.font.render(NOMS[piece], True, BORDURE)
                screen.blit(texte, (rect.centerx - texte.get_width() // 2,
                                    rect.centery - texte.get_height() // 2))
