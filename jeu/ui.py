# ui.py - V7.1 : NOUVEAU FICHIER
#
# La boite a outils d'affichage commune a TOUS les ecrans du jeu.
#
# POURQUOI (ta remarque : "toutes les dispositions doivent etre revues... pour
# une bonne visibilite et pas de chevauchement de texte") :
#   Chaque ecran calculait ses positions dans son coin, avec des nombres ecrits
#   en dur pour une fenetre de 1280x720. Des que la fenetre changeait de taille,
#   ou qu'un texte etait plus long que prevu (un nom de joueur, une adresse IP,
#   un nom de fichier PGN), les textes se chevauchaient.
#
# CE FICHIER REGLE LE PROBLEME A LA SOURCE :
#   1. ECHELLE. Toutes les tailles de texte sont derivees de la taille reelle de
#      la fenetre : le jeu reste lisible de 1024x640 a 1920x1080.
#   2. TEXTE MESURE. texte() connait la largeur disponible : ce qui depasse est
#      rogne proprement avec des points de suspension, jamais dessine par-dessus
#      le voisin.
#   3. PILE. Les blocs sont empiles dans une zone : un bloc qui ne rentre plus
#      n'est pas dessine du tout, plutot que de deborder sur le suivant.
#   4. EMOJI. rendre_ligne() sait melanger du texte et des emoji Windows dans la
#      meme ligne (necessaire pour le chat du mode en ligne).
#
# AUCUNE FONCTION SUPPRIMEE : ce fichier n'existait pas avant.

import os

import pygame

import design

# ---------------------------------------------------------------- fenetre
#
# Redimensionnement et plein ecran, pour TOUS les ecrans du jeu.
# Avant, seuls le menu et la partie savaient se redimensionner : dans l'ecran de
# reglages, le lobby, le profil ou le replay, F11 et le coin de la fenetre ne
# faisaient rien. L'etat est garde ici, donc il est partage par tous les ecrans.

TAILLE_PAR_DEFAUT = (1024, 640)      # taille de la fenetre au lancement
TAILLE_MINI = (900, 560)             # en dessous, le plateau devient illisible
_etat_fenetre = {"plein_ecran": False, "taille": TAILLE_PAR_DEFAUT}


def est_plein_ecran():
    return _etat_fenetre["plein_ecran"]


def memoriser_taille(largeur, hauteur, plein_ecran=None):
    if plein_ecran is not None:
        _etat_fenetre["plein_ecran"] = bool(plein_ecran)
    if not _etat_fenetre["plein_ecran"]:
        _etat_fenetre["taille"] = (max(TAILLE_MINI[0], int(largeur)),
                                   max(TAILLE_MINI[1], int(hauteur)))


def basculer_plein_ecran():
    """Renvoie la nouvelle surface d'affichage."""
    _etat_fenetre["plein_ecran"] = not _etat_fenetre["plein_ecran"]
    if _etat_fenetre["plein_ecran"]:
        return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    return pygame.display.set_mode(_etat_fenetre["taille"], pygame.RESIZABLE)


def evenement_fenetre(event):
    """A appeler dans TOUTES les boucles d'ecran.

    Gere le redimensionnement a la souris et F11. Renvoie la nouvelle surface
    quand elle a change, sinon None.
    """
    if event.type == getattr(pygame, "VIDEORESIZE", -1):
        if _etat_fenetre["plein_ecran"]:
            return None
        largeur = max(TAILLE_MINI[0], event.w)
        hauteur = max(TAILLE_MINI[1], event.h)
        _etat_fenetre["taille"] = (largeur, hauteur)
        return pygame.display.set_mode((largeur, hauteur), pygame.RESIZABLE)
    if event.type == pygame.KEYDOWN and event.key == getattr(pygame, "K_F11", -1):
        return basculer_plein_ecran()
    return None


def _ouvrir_presse_papiers(u):
    """25/10 : juste apres une copie, Windows et d'autres programmes (historique
    du presse-papiers...) viennent le lire et le tiennent un instant : un seul
    essai echouait ~1 fois sur 25. On reessaie 20 fois, 10 ms d'ecart."""
    import time
    for _ in range(20):
        if u.OpenClipboard(None):
            return True
        time.sleep(0.01)
    return False


def _windows_ecrire(texte):
    """25/10 (defaut Cowork : les accents disparaissaient au collage) : le
    presse-papiers Unicode de Windows (CF_UNICODETEXT). pygame 2.6 ne connait
    que CF_TEXT (Windows-1252), ou « à » devient un octet que la lecture en
    UTF-8 jetait. True si ca a marche."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        from ctypes import wintypes
        k, u = ctypes.windll.kernel32, ctypes.windll.user32
        k.GlobalAlloc.restype = ctypes.c_void_p
        k.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        k.GlobalLock.restype = ctypes.c_void_p
        k.GlobalLock.argtypes = [ctypes.c_void_p]
        k.GlobalUnlock.argtypes = [ctypes.c_void_p]
        u.SetClipboardData.restype = ctypes.c_void_p
        u.SetClipboardData.argtypes = [wintypes.UINT, ctypes.c_void_p]
        u.OpenClipboard.argtypes = [ctypes.c_void_p]
        donnees = texte.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-16-le") + b"\0\0"
        memoire = k.GlobalAlloc(0x0042, len(donnees))           # GMEM_MOVEABLE | ZEROINIT
        if not memoire:
            return False
        ctypes.memmove(k.GlobalLock(memoire), donnees, len(donnees))
        k.GlobalUnlock(memoire)
        if not _ouvrir_presse_papiers(u):
            return False
        try:
            u.EmptyClipboard()
            return bool(u.SetClipboardData(13, memoire))       # CF_UNICODETEXT
        finally:
            u.CloseClipboard()
    except Exception:
        return False


def _windows_lire():
    """Le texte Unicode du presse-papiers de Windows, ou None."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        k, u = ctypes.windll.kernel32, ctypes.windll.user32
        u.GetClipboardData.restype = ctypes.c_void_p
        k.GlobalLock.restype = ctypes.c_void_p
        k.GlobalLock.argtypes = [ctypes.c_void_p]
        k.GlobalUnlock.argtypes = [ctypes.c_void_p]
        u.OpenClipboard.argtypes = [ctypes.c_void_p]
        if not _ouvrir_presse_papiers(u):
            return None
        try:
            memoire = u.GetClipboardData(13)                   # CF_UNICODETEXT
            if not memoire:
                return None
            pointeur = k.GlobalLock(memoire)
            try:
                return ctypes.wstring_at(pointeur) if pointeur else None
            finally:
                k.GlobalUnlock(memoire)
        finally:
            u.CloseClipboard()
    except Exception:
        return None


def _decoder(donnees):
    """Octets du presse-papiers -> texte : UTF-8, sinon Windows-1252 (jamais
    de lettre perdue comme avec decode('utf-8', 'ignore'))."""
    if not isinstance(donnees, bytes):
        return donnees
    try:
        return donnees.decode("utf-8")
    except UnicodeDecodeError:
        return donnees.decode("cp1252", "replace")


def copier(texte):
    """Met du texte dans le presse-papiers. True si ca a marche."""
    texte = str(texte or "")
    if not texte:
        return False
    if _windows_ecrire(texte):
        return True
    try:
        pygame.scrap.init()
        pygame.scrap.put(pygame.SCRAP_TEXT, texte.encode("utf-8"))
        return True
    except Exception:
        pass
    try:                                  # secours Windows
        import subprocess
        subprocess.run("clip", input=texte.encode("utf-16le"),
                       shell=True, check=True)
        return True
    except Exception:
        return False


def decoder_presse_papiers(donnees):
    """24/10 (Cowork, t54 : le « à » disparaissait en collant) : sous Windows,
    le presse-papiers « texte » arrive dans l'ancien encodage de Windows
    (cp1252), pas en UTF-8 ; decoder en UTF-8 en ignorant les erreurs jetait
    toutes les lettres accentuees. On essaie UTF-8, puis UTF-16 (octets nuls
    un sur deux), puis cp1252, puis latin-1 (qui ne rate jamais)."""
    if not isinstance(donnees, (bytes, bytearray)):
        return str(donnees or "")
    donnees = bytes(donnees)
    if len(donnees) >= 4 and donnees[1::2].count(0) > len(donnees) // 4:
        brut = donnees[:len(donnees) // 2 * 2]
        try:
            return brut.decode("utf-16-le").replace("\x00", "")
        except UnicodeDecodeError:
            pass
    donnees = donnees.rstrip(b"\x00")
    for encodage in ("utf-8", "cp1252", "latin-1"):
        try:
            return donnees.decode(encodage)
        except UnicodeDecodeError:
            continue
    return donnees.decode("latin-1", "replace")


def coller():
    """Lit le presse-papiers. Chaine vide si on n'y arrive pas.

    V7.2 : c'est ce qui fait marcher le bouton COLLER UN LIEN. Trois chemins,
    du plus propre au plus bricole, parce qu'aucun ne marche partout :
    pygame.scrap, puis PowerShell sous Windows, puis les outils Linux. Si tout
    echoue on renvoie "" et l'ecran propose de taper le lien a la main - jamais
    de plantage pour un presse-papiers.
    """
    texte = _windows_lire()
    if texte:
        return texte.replace("\x00", "").strip()
    try:
        pygame.scrap.init()
        donnees = pygame.scrap.get(pygame.SCRAP_TEXT)
        if donnees:
            if isinstance(donnees, bytes):
                donnees = decoder_presse_papiers(donnees)
            return donnees.replace("\x00", "").strip()
    except Exception:
        pass
    import subprocess
    essais = []
    if os.name == "nt":
        essais.append(["powershell", "-NoProfile", "-Command", "Get-Clipboard"])
    else:
        essais.append(["xclip", "-selection", "clipboard", "-o"])
        essais.append(["xsel", "--clipboard", "--output"])
    for commande in essais:
        try:
            sortie = subprocess.run(commande, capture_output=True, timeout=2.0)
            texte = _decoder(sortie.stdout or b"").strip()
            if texte:
                return texte
        except Exception:
            continue
    return ""


# ---------------------------------------------------------------- polices

_POLICES = {}
_POLICE_EMOJI = {}
_NOMS_EMOJI = ("Segoe UI Emoji", "seguiemj", "Segoe UI Symbol", "Apple Color Emoji",
               "Noto Color Emoji", "DejaVu Sans", "Arial Unicode MS")


# V8 : LES POLICES SONT LIVREES AVEC LE JEU.
#
# En v7.2 on demandait "Segoe UI" au systeme. Ca marche sous Windows, ca ne
# ressemble a rien ailleurs, et surtout : Segoe UI est la police de l'explorateur
# de fichiers. Un jeu qui utilise la police du systeme a l'air d'un utilitaire.
#
# On livre donc deux familles dans polices/ :
#   OUTFIT       - geometrique, un peu large, excellente en gros titres comme en
#                  petit. C'est elle qui donne son caractere a l'interface.
#   JETBRAINSMONO- pour les CHIFFRES : pendules, classements, evaluations. Une
#                  chasse fixe empeche les nombres de danser quand ils changent,
#                  et c'est tres visible sur une pendule.
# Si les fichiers manquent, on retombe exactement sur le comportement de la
# v7.2 - le jeu ne depend donc pas d'eux pour demarrer.
_FICHIERS_POLICES = {
    # SickChess : Barlow Semi Condensed (OFL), choisie dans l'atelier graphique.
    # Etroite et nette, style tableau de score. Outfit reste dans polices/.
    (False, False): "BarlowSemiCondensed-Regular.ttf",
    (True, False): "BarlowSemiCondensed-SemiBold.ttf",
    (False, True): "JetBrainsMono-Regular.ttf",
    (True, True): "JetBrainsMono-Bold.ttf",
}


def _police_livree_voulue():
    """Le reglage "police livree". Vrai par defaut, faux = police du systeme.

    Lu paresseusement et sans planter : ui.py est importe par a peu pres tout,
    y compris avant que la configuration soit lisible.
    """
    try:
        import apparence
        return bool(apparence.reglage("police_livree", True))
    except Exception:
        return True


def _dossier_polices():
    try:
        from asset_manager import dossier_ressources
        base = dossier_ressources()
    except Exception:
        base = os.getcwd()
    return os.path.join(base, "polices")


def police(taille, gras=False, mono=False):
    """Police du jeu, mise en cache (creer une police est lent)."""
    taille = max(8, int(taille))
    cle = (taille, bool(gras), bool(mono))
    if cle in _POLICES:
        return _POLICES[cle]
    chemin = os.path.join(_dossier_polices(),
                          _FICHIERS_POLICES[(bool(gras), bool(mono))])
    if os.path.exists(chemin) and _police_livree_voulue():
        try:
            # Barlow est plus petite qu'Outfit a taille egale : on compense
            # pour que les mises en page calibrees sur Outfit restent justes.
            reelle = taille if mono else int(round(taille * 1.10))
            _POLICES[cle] = pygame.font.Font(chemin, reelle)
            return _POLICES[cle]
        except Exception as souci:
            print("[UI] police %s illisible : %s" % (chemin, souci))
    nom = "Consolas,DejaVu Sans Mono,Courier New" if mono \
        else "Segoe UI,Arial,DejaVu Sans"
    try:
        _POLICES[cle] = pygame.font.SysFont(nom, taille, bold=gras)
    except Exception:
        _POLICES[cle] = pygame.font.Font(None, int(taille * 1.25))
    return _POLICES[cle]


def police_emoji(taille):
    """Police capable d'afficher les emoji (Segoe UI Emoji sous Windows)."""
    taille = max(8, int(taille))
    if taille not in _POLICE_EMOJI:
        trouvee = None
        for nom in _NOMS_EMOJI:
            try:
                candidate = pygame.font.SysFont(nom, taille)
            except Exception:
                continue
            if candidate is not None:
                trouvee = candidate
                break
        _POLICE_EMOJI[taille] = trouvee or police(taille)
    return _POLICE_EMOJI[taille]


def vider_cache():
    _POLICES.clear()
    _POLICE_EMOJI.clear()
    _LARGEURS.clear()
    _RENDUS.clear()
    _ROGNES.clear()
    _TAILLES_PARAGRAPHE.clear()


# 23/10 (banc d'essai) : mesurer et dessiner les textes prenait 40 a 60 % de
# chaque image, alors que ce sont presque toujours les memes. On garde les
# mesures, les textes rognes et les textes dessines (cle = la police elle-meme,
# qui ne change qu'apres vider_cache). Quand c'est plein, on vide tout.
_LARGEURS = {}
_RENDUS = {}
_ROGNES = {}
_MAX_LARGEURS = 20000
_MAX_RENDUS = 3000


def _taille_de(pol, chaine):
    cle = (pol, chaine)
    taille = _LARGEURS.get(cle)
    if taille is None:
        if len(_LARGEURS) >= _MAX_LARGEURS:
            _LARGEURS.clear()
        taille = _LARGEURS[cle] = pol.size(chaine)
    return taille


def rendu_texte(chaine, taille, couleur, gras=False, mono=False):
    """Un texte dessine, garde en memoire (ne pas modifier l'image rendue)."""
    return _rendu_de(police(taille, gras, mono), str(chaine), couleur)


def _rendu_de(pol, chaine, couleur):
    """Texte dessine (a ne pas modifier : la meme image resert)."""
    try:
        cle_couleur = tuple(couleur)
    except TypeError:
        cle_couleur = couleur
    cle = (pol, chaine, cle_couleur)
    rendu = _RENDUS.get(cle)
    if rendu is None:
        if len(_RENDUS) >= _MAX_RENDUS:
            _RENDUS.clear()
        rendu = _RENDUS[cle] = pol.render(chaine, True, couleur)
    return rendu


# ---------------------------------------------------------------- crochets
# 24/10 (travail p36) : tous les ecrans lisent les evenements par
# ui.evenements() et affichent l'image par ui.afficher(). Un « crochet » (le
# bandeau d'invitation Steam, invitations.py) peut ainsi se dessiner par-dessus
# N'IMPORTE QUEL ecran et prendre ses propres clics, sans toucher aux ecrans.
# Sans crochet installe, c'est exactement pygame.event.get() et
# pygame.display.flip().

_CROCHETS = []


def installer_crochet(crochet):
    """crochet.filtrer(evenements) -> evenements restants ;
    crochet.dessiner(surface) -> dessine juste avant l'affichage."""
    if crochet not in _CROCHETS:
        _CROCHETS.append(crochet)


def retirer_crochet(crochet):
    if crochet in _CROCHETS:
        _CROCHETS.remove(crochet)


def evenements():
    """pygame.event.get(), moins les evenements pris par un crochet."""
    liste = pygame.event.get()
    for crochet in _CROCHETS:
        liste = crochet.filtrer(liste)
    return liste


def afficher():
    """pygame.display.flip(), apres le dessin des crochets."""
    surface = pygame.display.get_surface()
    if surface is not None:
        for crochet in _CROCHETS:
            crochet.dessiner(surface)
    pygame.display.flip()


class Cadence:
    """23/10 (surveillance en direct) : les menus et les ecrans dessinaient 60
    images/s meme quand rien ne bougeait (jeu a ~30 % d'un coeur). 60 images/s
    pendant 1,5 s apres un geste ou pendant une animation ; 30 sinon.

        cadence = ui.Cadence()
        ... clock.tick(cadence.suivante(evenements, anime=...))
    """
    REPOS_APRES_MS = 1500

    def __init__(self):
        self._activite_ms = None

    def suivante(self, evenements=(), anime=False):
        maintenant = pygame.time.get_ticks()
        if evenements or anime or self._activite_ms is None:
            self._activite_ms = maintenant
        return 60 if maintenant - self._activite_ms < self.REPOS_APRES_MS else images_au_repos()


def images_au_repos():
    """30 images/s quand rien ne bouge ; 24 sur un petit PC (24/10, p31)."""
    try:
        import petit_pc
        return petit_pc.IMAGES_AU_REPOS_PETIT if petit_pc.est_petit() else 30
    except Exception:
        return 30


# ---------------------------------------------------------------- echelle

# 24/10 (p33) : 1,65 au plus, c'etait un texte deux fois trop petit en 4K
# (3840x2160 = 3,4 fois la fenetre de base). Jusqu'a 1,65 rien ne change.
ECHELLE_MAX = 3.4

def echelle(cible):
    """Facteur de taille deduit de la fenetre. 1.0 = 1024x640 (taille par defaut).

    V8 : multiplie par le reglage "echelle_interface", pour ceux qui trouvent
    tout trop petit (ou trop gros) quelle que soit la taille de la fenetre. Les
    bornes restent les memes : au-dela, le menu ne tient plus dans l'ecran.
    """
    if hasattr(cible, "get_size"):
        largeur, hauteur = cible.get_size()
    else:
        largeur, hauteur = cible
    facteur = min(largeur / 1024.0, hauteur / 640.0)
    try:
        import apparence
        facteur *= float(apparence.reglage("echelle_interface", 1.0))
    except Exception:
        pass
    return max(0.86, min(ECHELLE_MAX, facteur))


def grand_ecran(cible):
    """24/10 (p33) : 1.0 jusqu'a environ 1700x1050 (rien ne change), puis
    jusqu'a ~2 en 4K. Pour les tailles ecrites en pixels (boutons, pendules)."""
    if hasattr(cible, "get_size"):
        largeur, hauteur = cible.get_size()
    else:
        largeur, hauteur = cible
    return max(1.0, min(ECHELLE_MAX, min(largeur / 1024.0, hauteur / 640.0)) / 1.65)


# 25/10 (petites fenetres) : en dessous, un texte n'est plus lisible.
TEXTE_MINI = 11


def t(base, ech=1.0):
    """Taille de texte a l'echelle, jamais sous TEXTE_MINI."""
    return max(TEXTE_MINI, int(round(base * ech)))


# ---------------------------------------------------------------- mesure

def mesurer(chaine, taille, gras=False, mono=False):
    # 24/10 (Cowork, t62 : « BLA… » sur la pendule) : on mesure le texte tel
    # qu'il sera affiche (traduit), pas le francais.
    return _taille_de(police(taille, gras, mono), _tr(str(chaine)))


def rogner(chaine, taille, largeur_max, gras=False, mono=False, suffixe="..."):
    """Raccourcit une chaine pour qu'elle tienne dans la largeur donnee."""
    chaine = str(chaine)
    if largeur_max is None or largeur_max <= 0:
        return chaine
    pol = police(taille, gras, mono)
    cle = (pol, chaine, largeur_max, suffixe)
    deja = _ROGNES.get(cle)
    if deja is not None:
        return deja
    if len(_ROGNES) >= _MAX_RENDUS:
        _ROGNES.clear()
    if _taille_de(pol, chaine)[0] <= largeur_max:
        _ROGNES[cle] = chaine
        return chaine
    largeur_suffixe = _taille_de(pol, suffixe)[0]
    if largeur_suffixe >= largeur_max:
        _ROGNES[cle] = ""
        return ""
    bas, haut = 0, len(chaine)
    while bas < haut:
        milieu = (bas + haut + 1) // 2
        if pol.size(chaine[:milieu])[0] + largeur_suffixe <= largeur_max:
            bas = milieu
        else:
            haut = milieu - 1
    _ROGNES[cle] = chaine[:bas].rstrip() + suffixe
    return _ROGNES[cle]


def taille_qui_tient(chaine, taille_max, taille_min, largeur_max,
                     gras=False, mono=False):
    """Plus grande taille de police pour laquelle la chaine tient."""
    taille = int(taille_max)
    while taille > taille_min:
        if _taille_de(police(taille, gras, mono), str(chaine))[0] <= largeur_max:
            return taille
        taille -= 1
    return max(int(taille_min), TEXTE_MINI)


# ---------------------------------------------------------------- dessin

def _tr(chaine):
    """17/10 (p12) : la traduction au moment d'afficher (langue.py)."""
    try:
        import langue
        return langue.traduire(chaine)
    except Exception:
        return chaine


def texte(surface, chaine, x, y, taille=17, couleur=(235, 232, 226), gras=False,
          mono=False, largeur_max=None, ancre="gauche", ajuster=False):
    """Ecrit une ligne de texte. Renvoie son rectangle.

    largeur_max : ce qui depasse est rogne (ou la police retrecit si ajuster).
    ancre : "gauche", "centre" ou "droite" - x est le point d'ancrage.
    """
    chaine = _tr(str(chaine))
    if largeur_max:
        if ajuster:
            taille = taille_qui_tient(chaine, taille, max(TEXTE_MINI, taille * 0.6),
                                      largeur_max, gras, mono)
        # Meme apres avoir retreci la police, on rogne : c'est la garantie
        # qu'un texte ne depasse JAMAIS de sa zone.
        chaine = rogner(chaine, taille, largeur_max, gras, mono)
    rendu = _rendu_de(police(taille, gras, mono), chaine, couleur)
    if ancre == "centre":
        x -= rendu.get_width() // 2
    elif ancre == "droite":
        x -= rendu.get_width()
    surface.blit(rendu, (int(x), int(y)))
    return pygame.Rect(int(x), int(y), rendu.get_width(), rendu.get_height())


def texte_centre_dans(surface, chaine, rect, taille=17, couleur=(235, 232, 226),
                      gras=False, mono=False, marge=8, ajuster=True):
    """Texte centre dans un rectangle, garanti de ne pas en sortir."""
    rect = pygame.Rect(rect)
    chaine = _tr(str(chaine))
    g = grand_ecran(surface)        # 24/10 (p33) : en 4K, a la taille du bouton
    if g > 1.0:
        taille = max(taille, min(int(taille * g), int(rect.height * 0.6)))
        marge = int(marge * g)
    largeur = max(10, rect.width - 2 * marge)
    if ajuster:
        taille = taille_qui_tient(chaine, taille, max(TEXTE_MINI, taille * 0.55),
                                  largeur, gras, mono)
    chaine = rogner(chaine, taille, largeur, gras, mono)
    rendu = _rendu_de(police(taille, gras, mono), str(chaine), couleur)
    surface.blit(rendu, (rect.centerx - rendu.get_width() // 2,
                         rect.centery - rendu.get_height() // 2))
    return rendu.get_rect(center=rect.center)


_COLLES_AVANT = (":", ";", "!", "?", "»")


def _mots_insecables(morceau):
    """Les mots d'une ligne, ponctuation francaise collee (31/10, relecteur-textes) :
    « reste avec le mot suivant ; : ; ! ? » restent avec le mot precedent. Sinon
    un « ou un : pouvait finir seul au bout d'une ligne."""
    mots = []
    for mot in morceau.split(" "):
        if mots and (mot in _COLLES_AVANT or mots[-1] == "«"):
            mots[-1] += " " + mot
        else:
            mots.append(mot)
    return mots


def couper_en_lignes(chaine, taille, largeur_max, gras=False, mono=False):
    """Coupe un paragraphe aux espaces pour tenir dans la largeur."""
    pol = police(taille, gras, mono)
    lignes = []
    for morceau in str(chaine).split("\n"):
        mots = _mots_insecables(morceau)
        courante = ""
        for mot in mots:
            essai = mot if not courante else courante + " " + mot
            if _taille_de(pol, essai)[0] <= largeur_max or not courante:
                courante = essai
            else:
                lignes.append(courante)
                courante = mot
        lignes.append(courante)
    return lignes


_TAILLES_PARAGRAPHE = {}


def _taille_du_paragraphe(chaine, taille, largeur, hauteur, gras, interligne, max_lignes):
    """La plus grande police (au plus 'taille') qui fait tenir tout le texte."""
    cle = (chaine, taille, largeur, hauteur, gras, interligne, max_lignes)
    if cle not in _TAILLES_PARAGRAPHE:
        if len(_TAILLES_PARAGRAPHE) > 2000:
            _TAILLES_PARAGRAPHE.clear()
        essai = int(taille)
        while essai > TEXTE_MINI:
            lignes = len(couper_en_lignes(chaine, essai, largeur, gras))
            place = hauteur // max(1, int(police(essai, gras).get_height() * interligne))
            if lignes <= min(place, max_lignes or 999):
                break
            essai -= 1
        _TAILLES_PARAGRAPHE[cle] = max(min(int(taille), TEXTE_MINI), essai)
    return _TAILLES_PARAGRAPHE[cle]


def paragraphe(surface, chaine, rect, taille=16, couleur=(180, 176, 170),
               gras=False, interligne=1.3, max_lignes=None):
    """Texte sur plusieurs lignes, coupe aux espaces, jamais hors du rectangle.

    25/10 (petites fenetres) : si le texte ne tient pas, la police retrecit
    (jusqu'a TEXTE_MINI) AVANT qu'on coupe la fin avec « ... »."""
    rect = pygame.Rect(rect)
    chaine = _tr(str(chaine))
    if rect.height:
        taille = _taille_du_paragraphe(chaine, taille, rect.width, rect.height, gras,
                                       interligne, max_lignes)
    lignes = couper_en_lignes(chaine, taille, rect.width, gras)
    hauteur_ligne = int(police(taille, gras).get_height() * interligne)
    place = max(1, rect.height // hauteur_ligne) if rect.height else len(lignes)
    limite = min(len(lignes), place, max_lignes or 999)
    y = rect.y
    for i in range(limite):
        contenu = lignes[i]
        if i == limite - 1 and limite < len(lignes):
            contenu = rogner(contenu + " ...", taille, rect.width, gras)
        texte(surface, contenu, rect.x, y, taille, couleur, gras)
        y += hauteur_ligne
    return y - rect.y


def cadre(surface, rect, fond=None, bordure=None, epaisseur=2, rayon=10,
          plat=False, ombre=False):
    """Un panneau. LA brique de toute l'interface - elle est appelee partout.

    V8 : C'EST ICI QUE SE JOUE LE DESIGN DE TOUT LE LOGICIEL. En v7.2 cette
    fonction posait un aplat uni ; les quatre-vingts ecrans du jeu avaient donc
    tous l'air de rectangles gris. On lui a ajoute les deux choses qui font la
    difference, et une seule fois pour tout le monde :
      - un DEGRADE tres court, plus clair en haut : la lumiere vient d'en haut,
        et c'est ce qui donne de la matiere a une surface ;
      - un LISET d'un pixel sur l'arete superieure, qui detache le panneau de
        ce qu'il y a derriere.
    Les deux sont mis en cache par taille et par couleur (voir design.py) :
    a l'usage, ca ne coute pas plus cher qu'un rectangle.

    'plat=True' rend exactement l'ancien dessin, pour les cas ou on veut un
    aplat franc (les cases du plateau, par exemple). Aucun appel existant n'a
    besoin d'etre modifie : la signature n'a fait que s'allonger.
    """
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return rect
    if fond is not None:
        if plat or rect.height < 8 or rect.width < 8:
            pygame.draw.rect(surface, fond, rect, border_radius=rayon)
        else:
            if ombre:
                design.ombre_douce(surface, rect, rayon)
            design.degrade_vertical(surface, rect,
                                    design.eclaircir(fond, 0.055),
                                    design.assombrir(fond, 0.05), rayon)
            design.liset(surface, rect, (255, 255, 255), rayon, 32)
    if bordure is not None and epaisseur > 0:
        pygame.draw.rect(surface, bordure, rect, epaisseur, border_radius=rayon)
    return rect


def voile(surface, rect=None, opacite=170, couleur=(0, 0, 0)):
    """Assombrit le fond pour faire ressortir une fenetre par-dessus."""
    rect = pygame.Rect(rect) if rect else surface.get_rect()
    calque = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    calque.fill((couleur[0], couleur[1], couleur[2], opacite))
    surface.blit(calque, rect.topleft)


def separateur(surface, x, y, largeur, couleur):
    pygame.draw.line(surface, couleur, (x, y), (x + largeur, y), 1)


# ---------------------------------------------------------------- empilement

class Pile:
    """Empile des blocs verticalement dans une zone.

    C'est la garantie anti-chevauchement : un bloc qui ne rentre plus n'est pas
    dessine du tout au lieu de deborder sur le suivant.
    """

    def __init__(self, x, y=None, largeur=None, hauteur=None, espace=10):
        # V7.2 : on accepte aussi un rectangle en un seul argument -
        # Pile(zone, espace=8) - ce qui evite de recopier x, y, largeur,
        # hauteur a chaque appel. L'ancienne forme a quatre nombres marche
        # exactement comme avant : rien n'a ete retire.
        if y is None and hasattr(x, "width"):
            x, y, largeur, hauteur = x.x, x.y, x.width, x.height
        elif y is None and isinstance(x, (tuple, list)) and len(x) == 4:
            x, y, largeur, hauteur = x
        self.x = int(x)
        self.y = int(y)
        self.depart_y = int(y)
        self.largeur = int(largeur)
        self.hauteur = int(hauteur) if hauteur else None
        self.espace = int(espace)

    def bloc(self, hauteur, espace=None):
        """Reserve un bloc. Renvoie son rectangle, ou None s'il n'y a plus place."""
        hauteur = int(hauteur)
        if self.hauteur is not None and \
                self.y + hauteur > self.depart_y + self.hauteur:
            return None
        rect = pygame.Rect(self.x, self.y, self.largeur, hauteur)
        self.y += hauteur + (self.espace if espace is None else int(espace))
        return rect

    def reste(self):
        if self.hauteur is None:
            return 10 ** 6
        return max(0, self.depart_y + self.hauteur - self.y)

def grille(elements, x, y, largeur, hauteur, ecart, largeur_mini):
    """Repartit des pastilles sur autant de lignes qu'il faut.

    Chaque element doit avoir une methode placer(rect). Renvoie la hauteur
    utilisee. Aucun element ne sort de la largeur donnee : c'est ce qui evite
    les pastilles qui se marchaient dessus sur une fenetre etroite.
    """
    if not elements:
        return 0
    par_ligne = max(1, (largeur + ecart) // (largeur_mini + ecart))
    par_ligne = min(par_ligne, len(elements))
    lignes = (len(elements) + par_ligne - 1) // par_ligne
    largeur_element = (largeur - (par_ligne - 1) * ecart) // par_ligne
    for index, element in enumerate(elements):
        ligne, colonne = divmod(index, par_ligne)
        element.placer((x + colonne * (largeur_element + ecart),
                        y + ligne * (hauteur + ecart), largeur_element, hauteur))
    return lignes * (hauteur + ecart) - ecart


def case_a_cocher(surface, rect, cochee, libelle, theme, taille=15,
                  largeur_max=None):
    """Case a cocher + libelle. Renvoie la zone cliquable (case + libelle)."""
    rect = pygame.Rect(rect)
    cadre(surface, rect, theme.get("accent") if cochee else theme.get("panneau"),
          theme.get("bord"), 1, 5)
    if cochee:
        pygame.draw.lines(surface, theme.get("fond", (20, 18, 16)), False, [
            (rect.x + rect.width * 0.22, rect.centery),
            (rect.x + rect.width * 0.44, rect.bottom - rect.height * 0.28),
            (rect.right - rect.width * 0.20, rect.y + rect.height * 0.26)], 2)
    largeur_libelle = mesurer(libelle, taille)[0]
    if largeur_max:
        largeur_libelle = min(largeur_libelle, largeur_max)
    texte(surface, libelle, rect.right + 10, rect.centery - taille // 2 - 1,
          taille, theme.get("texte") if cochee else theme.get("texte_discret"),
          largeur_max=largeur_libelle)
    return pygame.Rect(rect.x, rect.y - 4, rect.width + 10 + largeur_libelle,
                       rect.height + 8)


# ---------------------------------------------------------------- boutons

class Bouton:
    """Bouton rectangulaire, dessine a partir du theme, jamais deborde."""

    def __init__(self, rect, libelle, cle=None, taille=18, gras=True,
                 couleur_fond=None, couleur_texte=None, actif=True):
        self.rect = pygame.Rect(rect)
        self.libelle = libelle
        self.cle = cle if cle is not None else libelle
        self.taille = taille
        self.gras = gras
        self.couleur_fond = couleur_fond
        self.couleur_texte = couleur_texte
        self.actif = actif
        self.survol = False
        self.selectionne = False

    def placer(self, rect):
        self.rect = pygame.Rect(rect)
        return self

    def contient(self, position):
        return self.actif and self.rect.collidepoint(position)

    def maj_survol(self, position):
        self.survol = self.actif and self.rect.collidepoint(position)
        return self.survol

    def dessiner(self, surface, theme, rayon=10):
        fond = self.couleur_fond or theme.get("panneau", (48, 46, 44))
        bord = theme.get("bord", (110, 105, 98))
        texte_couleur = self.couleur_texte or theme.get("texte", (235, 232, 226))
        if not self.actif:
            fond = theme.get("fond", (32, 30, 28))
            texte_couleur = theme.get("texte_discret", (130, 126, 120))
        elif self.selectionne:
            fond = theme.get("accent", (200, 165, 90))
            texte_couleur = theme.get("fond", (28, 26, 24))
            bord = fond
        elif self.survol:
            bord = theme.get("accent", (200, 165, 90))
        cadre(surface, self.rect, fond, bord, 2, rayon)
        texte_centre_dans(surface, self.libelle, self.rect, self.taille,
                          texte_couleur, gras=self.gras, marge=10)
        return self.rect


def gerer_boutons(boutons, event):
    """Renvoie la cle du bouton clique, ou None. Gere aussi le survol."""
    if event.type == pygame.MOUSEMOTION:
        for bouton in boutons:
            bouton.maj_survol(event.pos)
        return None
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for bouton in boutons:
            if bouton.contient(event.pos):
                return bouton.cle
    return None


# ---------------------------------------------------------------- emoji + saisie

def _est_emoji(caractere):
    code = ord(caractere)
    return (0x1F000 <= code <= 0x1FAFF or 0x2600 <= code <= 0x27BF
            or 0x2B00 <= code <= 0x2BFF or 0xFE00 <= code <= 0xFE0F
            or 0x1F1E6 <= code <= 0x1F1FF or code == 0x200D
            or 0x2190 <= code <= 0x21FF or 0x2700 <= code <= 0x27BF)


def _tronçons(chaine):
    """Decoupe une chaine en morceaux (texte normal / emoji)."""
    morceaux = []
    courant = ""
    emoji_courant = None
    for caractere in str(chaine):
        emoji = _est_emoji(caractere)
        if emoji_courant is None or emoji == emoji_courant:
            courant += caractere
            emoji_courant = emoji
        else:
            morceaux.append((courant, emoji_courant))
            courant = caractere
            emoji_courant = emoji
    if courant:
        morceaux.append((courant, emoji_courant))
    return morceaux


def rendre_ligne(chaine, taille, couleur, gras=False):
    """Rend une ligne pouvant melanger texte et emoji Windows.

    C'est ce qui permet d'ecrire "bien joue !" avec un emoji dans le chat :
    les emoji sont dessines avec la police Segoe UI Emoji, le reste avec la
    police du jeu.
    """
    morceaux = _tronçons(chaine)
    if not morceaux:
        return police(taille, gras).render("", True, couleur)
    rendus = []
    for contenu, emoji in morceaux:
        pol = police_emoji(taille) if emoji else police(taille, gras)
        try:
            rendus.append(pol.render(contenu, True, couleur))
        except Exception:
            rendus.append(police(taille, gras).render("?" * len(contenu),
                                                      True, couleur))
    largeur = sum(r.get_width() for r in rendus)
    hauteur = max(r.get_height() for r in rendus)
    ligne = pygame.Surface((max(1, largeur), hauteur), pygame.SRCALPHA)
    x = 0
    for rendu in rendus:
        ligne.blit(rendu, (x, (hauteur - rendu.get_height()) // 2))
        x += rendu.get_width()
    return ligne


def couper_en_lignes_riches(chaine, taille, largeur_max, gras=False):
    """Comme couper_en_lignes, mais en mesurant aussi les emoji."""
    mots = _mots_insecables(str(chaine))
    lignes = []
    courante = ""
    for mot in mots:
        essai = mot if not courante else courante + " " + mot
        if rendre_ligne(essai, taille, (0, 0, 0), gras).get_width() <= largeur_max \
                or not courante:
            courante = essai
        else:
            lignes.append(courante)
            courante = mot
    if courante:
        lignes.append(courante)
    return lignes


class ChampTexte:
    """Zone de saisie : accepte les accents et les emoji Windows (touche Win + .)."""

    def __init__(self, longueur_max=140, coller_remplace=True):
        self.contenu = ""
        self.longueur_max = int(longueur_max)
        self.actif = False
        # 24/10 (Cowork, t54) : Ctrl+V REMPLACE dans un champ court (code d'un
        # salon, lien) ; il AJOUTE au texte deja ecrit dans un long message.
        self.coller_remplace = bool(coller_remplace)

    def activer(self, actif=True):
        self.actif = bool(actif)
        try:
            if actif:
                pygame.key.set_repeat(350, 35)
                if hasattr(pygame.key, "start_text_input"):
                    pygame.key.start_text_input()
            else:
                if hasattr(pygame.key, "stop_text_input"):
                    pygame.key.stop_text_input()
        except Exception:
            pass
        return self

    def vider(self):
        self.contenu = ""

    def handle_event(self, event):
        """Renvoie "valider" quand on appuie sur Entree, sinon None."""
        if not self.actif:
            return None
        if event.type == getattr(pygame, "TEXTINPUT", -1):
            ajout = getattr(event, "text", "")
            if ajout and len(self.contenu) + len(ajout) <= self.longueur_max:
                self.contenu += ajout
            return None
        if event.type == pygame.KEYDOWN:
            # V7.2 : Ctrl+V colle dans le champ. Sans ca, il fallait retaper a
            # la main une adresse recue par message - et sur certains PC la
            # saisie clavier ne parvenait meme pas au champ.
            if event.key == pygame.K_v and (event.mod & getattr(pygame, "KMOD_CTRL", 0)):
                self.coller_le_presse_papiers(remplacer=self.coller_remplace)
                return None
            if event.key == pygame.K_BACKSPACE:
                self.contenu = self.contenu[:-1]
                return None
            if event.key in (pygame.K_RETURN, getattr(pygame, "K_KP_ENTER", -2)):
                return "valider"
            if event.key == pygame.K_ESCAPE:
                return "annuler"
            # Secours pour les environnements sans evenement TEXTINPUT.
            if not hasattr(pygame, "TEXTINPUT"):
                caractere = getattr(event, "unicode", "")
                if caractere and caractere.isprintable() \
                        and len(self.contenu) < self.longueur_max:
                    self.contenu += caractere
        return None

    def ajouter(self, texte_ajoute):
        # 25/10 : ce qui depasse est coupe (avant, tout le texte etait refuse).
        place = self.longueur_max - len(self.contenu)
        if place > 0:
            self.contenu += texte_ajoute[:place]

    def coller_le_presse_papiers(self, remplacer=True):
        """Met le presse-papiers dans le champ. Renvoie ce qui a ete colle.

        V7.2 : c'est ce qui fait marcher le bouton COLLER a cote des champs
        d'adresse. On enleve les retours a la ligne : une adresse ou un lien
        tient sur une ligne, et un texte multiligne colle casserait l'affichage.
        """
        texte = (coller() or "").strip()
        if not texte:
            return ""
        texte = " ".join(texte.split())[:self.longueur_max]
        if remplacer:
            self.contenu = texte
        else:
            self.ajouter(texte)
        return texte

    def dessiner(self, surface, rect, theme, taille=16, invite=""):
        rect = pygame.Rect(rect)
        cadre(surface, rect, theme.get("fond", (30, 28, 26)),
              theme.get("accent") if self.actif else theme.get("bord"), 2, 8)
        interieur = rect.width - 20
        contenu = self.contenu
        couleur = theme.get("texte", (235, 232, 226))
        if not contenu and invite:
            contenu = invite
            couleur = theme.get("texte_discret", (140, 136, 130))
        ligne = rendre_ligne(contenu, taille, couleur)
        decalage = max(0, ligne.get_width() - interieur)
        zone = pygame.Rect(decalage, 0, min(interieur, ligne.get_width()),
                           ligne.get_height())
        if zone.width > 0:
            surface.blit(ligne, (rect.x + 10, rect.centery - ligne.get_height() // 2),
                         zone)
        if self.actif and (pygame.time.get_ticks() // 500) % 2 == 0:
            x = rect.x + 10 + min(interieur, ligne.get_width()) + 2
            pygame.draw.line(surface, theme.get("accent", (200, 165, 90)),
                             (x, rect.centery - taille // 2),
                             (x, rect.centery + taille // 2), 2)
        return rect
