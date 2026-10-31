# chat.py - V7.1 : NOUVEAU FICHIER
#
# Le chat du mode en ligne, avec les emoji Windows.
#
# POURQUOI (ta demande : "pour le multijoueur on doit avoir un chat + les emoji
# windows") : la V7 n'avait aucun moyen de se parler pendant une partie en
# ligne. Le reseau savait deja transporter n'importe quel message JSON, il
# manquait juste l'ecran et la saisie.
#
# LES EMOJI :
#   - La saisie Windows (touche Windows + point) fonctionne : le jeu ecoute
#     l'evenement TEXTINPUT de pygame, qui recoit l'Unicode complet, et non les
#     codes de touches. C'est ce qui permet aussi les accents.
#   - Ils sont dessines avec la police Segoe UI Emoji (ui.rendre_ligne).
#   - Une barre d'emoji cliquable est fournie pour les plus courants, pour ne
#     pas avoir a ouvrir le clavier Windows.
#
# AUCUNE FONCTION SUPPRIMEE : ce fichier n'existait pas avant.

import time

import pygame

import ui

EMOJI_RAPIDES = ["\U0001F44D", "\U0001F44F", "\U0001F600", "\U0001F602",
                 "\U0001F62E", "\U0001F614", "\U0001F621", "\U0001F525",
                 "❤️", "\U0001F91D", "♟️", "⏱️"]

MESSAGES_GARDES = 80
LONGUEUR_MAX = 160


class Chat:
    """Fil de discussion d'une partie en ligne."""

    def __init__(self, nom_local="Toi", nom_adverse="Adversaire"):
        self.nom_local = nom_local
        self.nom_adverse = nom_adverse
        self.messages = []              # {nom, texte, moi, systeme, heure}
        self.champ = ui.ChampTexte(LONGUEUR_MAX)
        self.non_lus = 0
        self.visible = False            # onglet CHAT ouvert ?
        self.defilement = 0             # 0 = colle en bas
        self.zone_emoji = []            # rectangles cliquables, remplis au dessin
        self.rect_messages = pygame.Rect(0, 0, 0, 0)
        self.rect_saisie = pygame.Rect(0, 0, 0, 0)
        self.actif = True               # False = chat coupe (partie locale)

    # ------------------------------------------------------------------ contenu

    def _ajouter(self, nom, texte, moi=False, systeme=False):
        texte = str(texte).strip()
        if not texte:
            return None
        message = {"nom": nom, "texte": texte[:LONGUEUR_MAX], "moi": moi,
                   "systeme": systeme, "heure": time.strftime("%H:%M")}
        self.messages.append(message)
        if len(self.messages) > MESSAGES_GARDES:
            del self.messages[0:len(self.messages) - MESSAGES_GARDES]
        self.defilement = 0
        return message

    def envoyer_local(self, texte):
        return self._ajouter(self.nom_local, texte, moi=True)

    def recevoir(self, nom, texte):
        message = self._ajouter(nom or self.nom_adverse, texte, moi=False)
        if message is not None and not self.visible:
            self.non_lus += 1
        return message

    def systeme(self, texte):
        return self._ajouter("", texte, systeme=True)

    def ouvrir(self, ouvert=True):
        self.visible = bool(ouvert)
        if self.visible:
            self.non_lus = 0
        self.champ.activer(self.visible)
        return self

    def derniers(self, combien=2):
        """Les derniers messages, pour la bulle affichee sous le plateau."""
        return [m for m in self.messages if not m["systeme"]][-combien:]

    # ------------------------------------------------------------------ evenements

    def handle_event(self, event):
        """Renvoie le texte a envoyer a l'adversaire, ou None."""
        if not self.actif or not self.visible:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for rect, emoji in self.zone_emoji:
                    if rect.collidepoint(event.pos):
                        self.champ.ajouter(emoji)
                        return None
                if self.rect_saisie.collidepoint(event.pos):
                    self.champ.activer(True)
                    return None
            elif event.button == 4 and self.rect_messages.collidepoint(event.pos):
                self.defilement += 1
                return None
            elif event.button == 5 and self.rect_messages.collidepoint(event.pos):
                self.defilement = max(0, self.defilement - 1)
                return None

        action = self.champ.handle_event(event)
        if action == "valider":
            texte = self.champ.contenu.strip()
            self.champ.vider()
            if texte:
                self.envoyer_local(texte)
                return texte
        elif action == "annuler":
            self.champ.vider()
        return None

    # ------------------------------------------------------------------ dessin

    def dessiner(self, surface, zone, theme, ech=1.0):
        """Dessine le chat dans la zone donnee (celle de la liste des coups)."""
        zone = pygame.Rect(zone)
        self.zone_emoji = []
        if zone.height < 80:
            return

        h_saisie = ui.t(30, ech)
        h_emoji = ui.t(28, ech)
        marge = ui.t(8, ech)

        self.rect_saisie = pygame.Rect(zone.x + marge,
                                       zone.bottom - marge - h_saisie,
                                       zone.width - 2 * marge, h_saisie)
        rect_emoji = pygame.Rect(zone.x + marge,
                                 self.rect_saisie.y - marge // 2 - h_emoji,
                                 zone.width - 2 * marge, h_emoji)
        self.rect_messages = pygame.Rect(zone.x + marge, zone.y + marge,
                                         zone.width - 2 * marge,
                                         max(20, rect_emoji.y - zone.y - 2 * marge))

        self._dessiner_messages(surface, theme, ech)
        self._dessiner_emoji(surface, rect_emoji, theme, ech)

        invite = "Écris ton message  (Entrée pour envoyer)" if self.actif \
            else "Chat indisponible"
        self.champ.dessiner(surface, self.rect_saisie, theme, ui.t(15, ech), invite)

    def _dessiner_messages(self, surface, theme, ech):
        rect = self.rect_messages
        taille = ui.t(14, ech)
        interligne = ui.t(4, ech)
        couleur_moi = theme.get("accent", (200, 165, 90))
        couleur_autre = theme.get("texte", (235, 232, 226))
        couleur_systeme = theme.get("texte_discret", (150, 145, 138))

        # On compose toutes les lignes, puis on n'affiche que celles qui rentrent.
        lignes = []
        for message in self.messages:
            if message["systeme"]:
                couleur = couleur_systeme
                prefixe = ""
            else:
                couleur = couleur_moi if message["moi"] else couleur_autre
                prefixe = "%s : " % message["nom"]
            for i, contenu in enumerate(
                    ui.couper_en_lignes_riches(prefixe + message["texte"],
                                               taille, rect.width - 4)):
                lignes.append((contenu, couleur, message["systeme"] and i == 0))

        hauteur_ligne = ui.police(taille).get_height() + interligne
        visibles = max(1, rect.height // hauteur_ligne)
        fin = max(visibles, len(lignes) - self.defilement)
        debut = max(0, fin - visibles)

        if not lignes:
            ui.texte(surface, "Aucun message. Dis bonjour !", rect.x, rect.y,
                     taille, couleur_systeme, largeur_max=rect.width)
            return

        y = rect.y
        for contenu, couleur, _italique in lignes[debut:fin]:
            if y + hauteur_ligne > rect.bottom:
                break
            rendu = ui.rendre_ligne(contenu, taille, couleur)
            # On rogne au besoin : une ligne ne sort jamais de la zone du chat.
            zone = pygame.Rect(0, 0, min(rect.width, rendu.get_width()),
                               rendu.get_height())
            surface.blit(rendu, (rect.x, y), zone)
            y += hauteur_ligne

        if debut > 0:
            ui.texte(surface, "▲", rect.right - ui.t(12, ech), rect.y,
                     ui.t(11, ech), couleur_systeme)

    def _dessiner_emoji(self, surface, rect, theme, ech):
        if rect.height < 16:
            return
        taille = ui.t(17, ech)
        largeur = max(rect.height, rect.width // max(1, len(EMOJI_RAPIDES)))
        x = rect.x
        for emoji in EMOJI_RAPIDES:
            case = pygame.Rect(x, rect.y, largeur, rect.height)
            if case.right > rect.right:
                break
            rendu = ui.rendre_ligne(emoji, taille, theme.get("texte", (235, 232, 226)))
            surface.blit(rendu, (case.centerx - rendu.get_width() // 2,
                                 case.centery - rendu.get_height() // 2),
                         pygame.Rect(0, 0, min(case.width, rendu.get_width()),
                                     min(case.height, rendu.get_height())))
            self.zone_emoji.append((case, emoji))
            x += largeur


def dessiner_bulles(surface, chat, zone, theme, ech=1.0):
    """Les deux derniers messages, sous le plateau, meme en onglet COUPS.

    Comme ca on ne rate jamais un message parce qu'on regardait la liste des
    coups.
    """
    if chat is None:
        return
    messages = chat.derniers(2)
    if not messages:
        return
    zone = pygame.Rect(zone)
    if zone.height < 18:
        return
    taille = ui.t(14, ech)
    hauteur_ligne = ui.police(taille).get_height() + ui.t(3, ech)
    y = zone.bottom - hauteur_ligne * len(messages)
    for message in messages:
        couleur = theme.get("accent", (200, 165, 90)) if message["moi"] \
            else theme.get("texte", (235, 232, 226))
        contenu = "%s : %s" % (message["nom"], message["texte"])
        rendu = ui.rendre_ligne(contenu, taille, couleur)
        fond = pygame.Surface((min(rendu.get_width() + 14, zone.width),
                               hauteur_ligne), pygame.SRCALPHA)
        fond.fill((0, 0, 0, 150))
        surface.blit(fond, (zone.x, y))
        surface.blit(rendu, (zone.x + 7, y + (hauteur_ligne - rendu.get_height()) // 2),
                     pygame.Rect(0, 0, zone.width - 14, rendu.get_height()))
        y += hauteur_ligne
