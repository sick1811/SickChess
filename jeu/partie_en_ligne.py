# partie_en_ligne.py - SickChess : tout le parcours "Jouer en ligne".
#
#   salon (salon_en_ligne.py) -> partie (mode_en_ligne.py) -> fin de partie
#   -> revanche (couleurs inversees, meme salon) ou retour au menu.
#
# Ce fichier a sa propre boucle de partie, pour ne pas charger celle de
# game_manager.py avec le chat, la revanche et le reseau. game_manager n'a
# besoin que de deux lignes pour le brancher :
#
#     if partie_en_ligne.invitation_en_attente():   # dans la boucle du menu
#         choix = "en_ligne"
#     ...
#     partie_en_ligne.lancer(self)                   # quand choix == "en_ligne"

import os
import sys

import chess
import pygame

import apparence
import steam as module_steam
import ui
from board import ChessBoard
from ecran_fin import EcranFin
from mode_en_ligne import ModeEnLigne
from salon_en_ligne import SalonEnLigne

_INVITATION = {"essai": False, "salon": 0}


# ---------------------------------------------------------------- invitations

def invitation_en_attente():
    """A appeler a chaque image du menu. Renvoie le numero du salon d'un ami
    dont on vient d'accepter l'invitation dans Steam (ou 0).

    Au premier appel : lit '+connect_lobby' (jeu lance par une invitation) et
    branche Steam si steam_appid.txt est la ou si le jeu vient de Steam."""
    s = module_steam.instance()
    if not _INVITATION["essai"]:
        _INVITATION["essai"] = True
        depuis_steam = module_steam.salon_depuis_ligne_de_commande()
        if depuis_steam:
            _INVITATION["salon"] = depuis_steam
        if depuis_steam or os.path.exists("steam_appid.txt") \
                or getattr(sys, "frozen", False):
            s.demarrer()
    if s.actif:
        s.pomper()
        for evenement in s.evenements("invitation_acceptee"):
            _INVITATION["salon"] = evenement["salon"]
            import invitations
            invitations.oublier(evenement["salon"])   # acceptee dans Steam
    return _INVITATION["salon"]


def demander_a_rejoindre(salon):
    """24/10 (p36) : « Rejoindre » du bandeau d'invitation. Le menu lit ce
    salon (invitation_en_attente) et file au salon de l'ami."""
    _INVITATION["salon"] = int(salon)


def _prendre_invitation():
    salon = _INVITATION["salon"]
    _INVITATION["salon"] = 0
    return salon


def arreter():
    """A appeler en quittant le jeu."""
    module_steam.instance().arreter()


# ---------------------------------------------------------------- fin de partie

class EcranFinEnLigne(EcranFin):
    """Carte de fin en ligne (23/10) : la meme que contre l'ordinateur
    (resultat, precision, REVUE DE LA PARTIE), avec REVANCHE a la place de
    REJOUER. La revue et l'analyse sont locales : chacun a la sienne."""

    def __init__(self, plateau, mode):
        super().__init__(plateau, mode)
        self.bouton_revanche = ui.Bouton((0, 0, 10, 10), "Revanche", "revanche")
        self.boutons = [self.bouton_revue, self.bouton_revanche, self.bouton_menu]

    def camp_du_joueur(self):
        return self.mode.couleur_locale == chess.WHITE

    def titre(self):
        resultat = getattr(self.plateau, "result", None)
        if resultat not in ("1-0", "0-1"):
            return "Partie nulle"
        gagnant = chess.WHITE if resultat == "1-0" else chess.BLACK
        return "Victoire !" if gagnant == self.mode.couleur_locale else "Défaite"

    def ligne_analyse(self):
        """'Precision : toi 84.2 %  -  Paul 79.0 %', ou l'avancement."""
        a = self.analyseur
        if a is None:
            return ""
        if a.erreur or not a.terminee():
            return a.texte_avancement()
        rapport = a.rapport()
        blancs, noirs = rapport["blancs"]["precision"], rapport["noirs"]["precision"]
        if blancs is None or noirs is None:
            return ""
        moi, lui = (blancs, noirs) if self.mode.couleur_locale == chess.WHITE \
            else (noirs, blancs)
        self._succes_precision_90(moi)
        return "Précision : toi %.1f %%   -   %s %.1f %%" % (
            moi, self.mode.nom_adverse, lui)

    def _placer(self, screen):
        largeur, hauteur = screen.get_size()
        carte_l = min(460, largeur - 40)
        dispo = getattr(self.plateau, "disposition", None)
        if dispo is not None and hasattr(dispo, "rect_plateau"):
            zone = pygame.Rect(*dispo.rect_plateau())
        else:
            zone = screen.get_rect()
        carte_h = max(330, min(402, zone.height - 10))   # 24/10 (p27) : le coach
        self.rect = pygame.Rect(0, 0, carte_l, carte_h)
        self.rect.center = zone.center
        bl = (carte_l - 60) // 2
        y = self.rect.bottom - 66
        self.bouton_revanche.placer((self.rect.x + 20, y, bl, 46))
        self.bouton_menu.placer((self.rect.x + 40 + bl, y, bl, 46))
        self.bouton_revue.placer((self.rect.x + 20, y - 56, carte_l - 40, 46))

    def draw(self, screen):
        if not self.plateau.game_over:
            return
        self._placer(screen)
        t = apparence.theme(getattr(self.plateau, "theme_plateau", None))
        revanche = self.mode.revanche
        self.bouton_revanche.libelle = revanche.libelle_bouton().capitalize()
        self.bouton_revanche.actif = revanche.possible() and not revanche.en_attente()
        ui.cadre(screen, self.rect, t["panneau"], t.get("accent"), 2, 16, ombre=True)
        ui.texte(screen, self.titre(), self.rect.centerx, self.rect.y + 20, 34,
                 t["texte"], gras=True, ancre="centre",
                 largeur_max=self.rect.width - 30, ajuster=True)
        raison = getattr(self.plateau, "game_over_reason", "") or ""
        ui.texte(screen, raison, self.rect.centerx, self.rect.y + 72, 16,
                 t["texte_discret"], ancre="centre",
                 largeur_max=self.rect.width - 30, ajuster=True)
        y = self._dessiner_coach(screen, t, self.rect.y + 100)
        ligne = self.ligne_analyse()
        if ligne:
            ui.texte(screen, ligne, self.rect.centerx, y, 14,
                     t["texte_discret"], ancre="centre",
                     largeur_max=self.rect.width - 30, ajuster=True)
        ui.paragraphe(screen, revanche.explication(),
                      (self.rect.x + 20, y + 26, self.rect.width - 40, 54),
                      14, t["accent"])
        for bouton in self.boutons:
            bouton.dessiner(screen, t, rayon=10)

    def handle_event(self, event):
        """Renvoie 'revue', 'revanche', 'menu' ou None."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "menu"
        return ui.gerer_boutons(self.boutons, event)


# ---------------------------------------------------------------- parcours

def _nom_du_joueur():
    try:
        import profil
        nom = (profil.get_profil().nom or "").strip()
        if nom:
            return nom[:20]
    except Exception:
        pass
    return (os.environ.get("USERNAME") or "Joueur")[:20]


def lancer(manager):
    """Tout le parcours en ligne. Revient quand le joueur retourne au menu."""
    salon = SalonEnLigne(manager.screen, manager.clock, manager.evenement_fenetre,
                         _nom_du_joueur(), salon_a_rejoindre=_prendre_invitation(),
                         config=getattr(manager, "config", {}))
    resultat = salon.run()
    if resultat == "quitter":
        manager.quitter()
    if not resultat:
        return "menu"
    transport, reglages = resultat
    numero = 1
    try:
        while True:
            issue = jouer_une_partie(manager, transport, reglages, numero)
            if issue == "quitter":
                transport.fermer()
                manager.quitter()
            if issue != "revanche":
                return "menu"
            numero += 1
            reglages = dict(reglages)
            # Revanche : meme position Freestyle, couleurs inversees, sans
            # nouvelle preparation (on connait deja la position).
            reglages["preparation_s"] = 0
            reglages["couleur_locale"] = ("noir" if reglages["couleur_locale"] == "blanc"
                                          else "blanc")
    finally:
        transport.fermer()
        manager.board = None


def _preparer_plateau(manager, reglages):
    board = ChessBoard(manager.screen, dict(reglages), manager.disposition)
    try:
        manager._appliquer_preferences(board)
    except Exception as souci:
        print("[EN LIGNE] preferences non appliquees : %s" % souci)
    board.competitive = False
    return board


def jouer_une_partie(manager, transport, reglages, numero=1):
    """Une partie. Renvoie 'menu', 'revanche' ou 'quitter'."""
    board = _preparer_plateau(manager, reglages)
    manager.board = board
    mode = ModeEnLigne(board, transport, reglages["couleur_locale"],
                       transport.nom_local, numero=numero)
    board.end_screen = EcranFinEnLigne(board, mode)
    board.game_buttons.bouton_nulle()       # pas de MENU en ligne : NULLE
    if numero > 1:
        mode.afficher("Revanche ! Tu joues les %s."
                      % ("Blancs" if mode.couleur_locale == chess.WHITE else "Noirs"))
    try:
        return _boucle(manager, board, mode)
    finally:
        mode.arreter()
        _arreter_les_analyses(manager, board)


def _arreter_les_analyses(manager, board):
    """En quittant la partie (menu, revanche) : plus besoin d'analyser."""
    direct = getattr(manager, "analyse_en_direct", None)
    if direct is not None:
        direct.arreter()
        manager.analyse_en_direct = None
    analyseur = getattr(board.end_screen, "analyseur", None)
    if analyseur is not None:
        analyseur.arreter()


def suivre_l_analyse(manager, board, mode):
    """A chaque image. Comme contre l'ordinateur : Stockfish analyse en
    silence pendant la partie, puis la fin branche l'analyse sur la carte."""
    if board.game_over:
        if not getattr(board, "fin_en_ligne_faite", False):
            board.fin_en_ligne_faite = True
            fin_de_partie(manager, mode)
    else:
        manager._suivre_analyse(en_ligne=True)


def fin_de_partie(manager, mode):
    """Une fois, des que la partie est finie : le PGN, puis l'analyse
    (reprise de celle faite pendant la partie) rangee a cote du PGN - comme
    contre l'ordinateur : precision sur la carte, revue, statistiques,
    Mes erreurs."""
    mode.enregistrer()
    try:
        manager.brancher_analyse(mode.chemin_pgn)
    except Exception as souci:
        print("[EN LIGNE] analyse non lancee : %s" % souci)


def ouvrir_la_revue(manager, board, mode):
    """Revue locale (l'adversaire ne la voit pas). Le reseau continue de
    tourner pendant ce temps : chat, demande de revanche, depart."""
    if mode.couleur_locale == chess.WHITE:
        noms, cote_noir = ("Toi", mode.nom_adverse), False
    else:
        noms, cote_noir = (mode.nom_adverse, "Toi"), True
    manager.ouvrir_revue(noms, cote_noir, pendant_la_revue(manager, board, mode))


def pendant_la_revue(manager, board, mode):
    """Appele a chaque image de la revue : le reseau, puis un bandeau si
    l'adversaire demande une revanche ou s'en va."""
    def apres_dessin(ecran):
        mode.update()
        _bandeau_revue(ecran, board, mode)
        manager.aide.draw(ecran, board.theme_plateau)
    return apres_dessin


def _bandeau_revue(ecran, board, mode):
    revanche = mode.revanche
    message = mode.message_actif() or (
        revanche.explication() if revanche.a_repondre() or revanche.acceptee() else "")
    if not message:
        return
    t = apparence.theme(board.theme_plateau)
    largeur = min(ecran.get_width() - 20, ui.mesurer(message, 16)[0] + 40)
    rect = pygame.Rect(0, 0, max(120, largeur), 40)
    rect.midtop = (ecran.get_width() // 2, 8)
    ui.cadre(ecran, rect, t["panneau"], t.get("accent"), 2, 12, ombre=True)
    ui.texte_centre_dans(ecran, message, rect, 16, t["texte"], marge=14)


def _boucle(manager, board, mode):
    while True:
        for event in ui.evenements():
            if event.type == pygame.QUIT:
                mode.quitter()
                return "quitter"
            if manager.evenement_fenetre(event):
                continue
            if _evenement_chat(board, mode, event):
                continue
            if board.game_over:
                action = board.end_screen.handle_event(event)
                if action == "menu":
                    return "menu"
                if action == "revue":
                    ouvrir_la_revue(manager, board, mode)
                    continue
                if action == "revanche":
                    mode.demander_revanche()
                    continue
            action = board.game_buttons.handle_event(event)
            if action == "return_to_menu":
                mode.quitter()
                return "menu"
            if action == "abandon":
                mode.abandonner()
                continue
            if action == "nulle":
                mode.nulle()
                continue
            board.handle_event(event, None)

        mode.update()
        if mode.revanche_acceptee():
            return "revanche"
        board.update()
        suivre_l_analyse(manager, board, mode)

        board.draw()
        _dessiner_bandeau(board, mode)
        manager.aide.draw(manager.screen, board.theme_plateau)
        ui.afficher()
        manager.clock.tick(60)


def _evenement_chat(board, mode, event):
    """Onglets COUPS / CHAT et saisie du chat. True si l'evenement est pris."""
    chat = board.chat
    if chat is None:
        return False
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        onglet = board.renderer.clic_onglet(event.pos)
        if onglet:
            board.renderer.onglet = onglet
            chat.ouvrir(onglet == "chat")
            return True
    if board.renderer.onglet != "chat":
        return False
    texte = chat.handle_event(event)
    if texte:
        mode.envoyer_chat(texte)
        return True
    # Tant qu'on ecrit, le clavier est au chat.
    return chat.champ.actif and event.type in (pygame.KEYDOWN,
                                               getattr(pygame, "TEXTINPUT", -1))


def _dessiner_bandeau(board, mode):
    message = mode.message_actif()
    if not message:
        return
    ecran = board.screen
    t = apparence.theme(board.theme_plateau)
    zone = pygame.Rect(*board.disposition.rect_plateau())
    largeur = min(zone.width - 20, ui.mesurer(message, 16)[0] + 40)
    rect = pygame.Rect(0, 0, max(120, largeur), 40)
    rect.midtop = (zone.centerx, zone.y + 12)
    ui.cadre(ecran, rect, t["panneau"], t.get("accent"), 2, 12, ombre=True)
    ui.texte_centre_dans(ecran, message, rect, 16, t["texte"], marge=14)
