# signalement.py - SickChess 17/10 (travail p16, demande de Julien).
#
# « Signaler un problème / Proposer une idée » : le joueur ecrit son message,
# le jeu y ajoute tout seul la version, le systeme et la fin du journal
# (journal_du_jeu.txt), puis :
#   1. si une adresse d'envoi est reglee (salon Discord de Julien, cle
#      "signalement_webhook" dans signalement.json ou config.json), le rapport
#      part directement, journal en piece jointe ;
#   2. sinon (ou si l'envoi rate), il est range dans le dossier rapports/,
#      le dossier s'ouvre et le texte est copie : il suffit de l'envoyer.
# Rien n'est envoye sans que le joueur clique sur « Envoyer ».

import datetime
import json
import os
import platform
import uuid

LIGNES_DU_JOURNAL = 120
DOSSIER = "rapports"
TYPES = {"probleme": "Problème", "idee": "Idée", "plantage": "Plantage"}

# 25/10 (Julien, recette R-095 / R-096) : les messages arrivent dans le salon
# Discord de SickChess. Couleurs choisies par Julien : les bugs en rouge, les
# idees en vert, les plantages en bleu.
COULEURS = {"probleme": 0xE53935, "idee": 0x43A047, "plantage": 0x1E88E5}
TITRES = {"probleme": "Bug", "idee": "Idée", "plantage": "Plantage"}
# L'adresse du salon (webhook) n'est PAS dans le code (il part sur GitHub) :
# elle est dans signalement.json, a cote du jeu (hors Git), livre avec la
# version amis. Les tests et les robots (endurance, recette automatique)
# mettent cette variable : jamais de faux message dans le vrai salon.
SANS_ENVOI = "SICKCHESS_SANS_ENVOI"


def _racine():
    try:
        from asset_manager import dossier_ecriture
        return dossier_ecriture()
    except Exception:
        return os.getcwd()


def fin_du_journal(lignes=LIGNES_DU_JOURNAL, chemin=None):
    chemin = chemin or os.path.join(_racine(), "journal_du_jeu.txt")
    try:
        with open(chemin, "r", encoding="utf-8", errors="replace") as f:
            return "".join(f.readlines()[-lignes:])
    except OSError:
        return "(pas de journal)"


def construire(type_, message, version="", journal=None, maintenant=None):
    """Le texte complet du rapport."""
    maintenant = maintenant or datetime.datetime.now()
    entete = [
        "SickChess - %s" % TYPES.get(type_, "Message"),
        "Date : %s" % maintenant.strftime("%d/%m/%Y %H:%M"),
        "Version : %s" % (version or "?"),
        "Systeme : %s %s, Python %s" % (platform.system(), platform.release(),
                                        platform.python_version()),
        "",
        "Message :",
        (message or "").strip() or "(vide)",
        "",
    ]
    if type_ in ("probleme", "plantage"):
        entete += ["--- Fin du journal du jeu ---",
                   journal if journal is not None else fin_du_journal()]
    return "\n".join(entete)


def enregistrer(texte, type_="probleme", dossier=None, maintenant=None):
    """Range le rapport dans rapports/ ; renvoie le chemin (ou None)."""
    maintenant = maintenant or datetime.datetime.now()
    dossier = dossier or os.path.join(_racine(), DOSSIER)
    try:
        os.makedirs(dossier, exist_ok=True)
        nom = "%s_%s.txt" % (maintenant.strftime("%Y-%m-%d_%Hh%M%S"), type_)
        chemin = os.path.join(dossier, nom)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(texte)
        return chemin
    except OSError as e:
        print("[SIGNALER] rapport non enregistre : %s" % e)
        return None


def _dossier_du_jeu():
    """Le dossier du jeu (la ou la version amis installe signalement.json)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def adresse_d_envoi():
    """L'adresse du salon Discord (webhook), ou '' si rien n'est regle."""
    if os.environ.get(SANS_ENVOI):
        return ""
    for dossier, nom in ((_racine(), "signalement.json"), (_dossier_du_jeu(), "signalement.json"),
                         (_racine(), "config.json")):
        try:
            with open(os.path.join(dossier, nom), "r", encoding="utf-8") as f:
                url = (json.load(f) or {}).get("signalement_webhook", "")
            if isinstance(url, str) and url.startswith("https://"):
                return url
        except (OSError, ValueError, AttributeError):
            continue
    return ""


def message_discord(type_, message, version=""):
    """Le message du salon : un cadre de la couleur du type (bug rouge, idee
    verte, plantage bleu), le texte du joueur et la version."""
    texte = (message or "").strip() or "(vide)"
    if len(texte) > 4000:
        texte = texte[:3997] + "..."
    cadre = {"title": TITRES.get(type_, "Message"), "description": texte,
             "color": COULEURS.get(type_, 0x9E9E9E)}
    if version:
        cadre["footer"] = {"text": "SickChess %s" % version}
    return {"embeds": [cadre]}


def envoyer(url, type_, message, texte_complet, delai=10, ouvrir=None, version=""):
    """Envoie au webhook Discord (message + rapport en piece jointe).
    Renvoie (ok, explication)."""
    import urllib.request
    frontiere = "----sickchess%s" % uuid.uuid4().hex
    corps = []
    corps.append("--%s\r\nContent-Disposition: form-data; name=\"payload_json\"\r\n"
                 "Content-Type: application/json\r\n\r\n%s\r\n"
                 % (frontiere, json.dumps(message_discord(type_, message, version))))
    corps.append("--%s\r\nContent-Disposition: form-data; name=\"files[0]\"; "
                 "filename=\"rapport.txt\"\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
                 % frontiere)
    donnees = "".join(corps).encode("utf-8") + texte_complet.encode("utf-8") \
        + ("\r\n--%s--\r\n" % frontiere).encode("utf-8")
    requete = urllib.request.Request(url, data=donnees, method="POST", headers={
        "Content-Type": "multipart/form-data; boundary=%s" % frontiere,
        "User-Agent": "SickChess"})
    try:
        ouvrir = ouvrir or urllib.request.urlopen
        with ouvrir(requete, timeout=delai) as reponse:
            code = getattr(reponse, "status", 200)
        if 200 <= int(code) < 300:
            return True, "Merci ! Ton message est bien parti."
        return False, "L'envoi a échoué (code %s)." % code
    except Exception as e:
        print("[SIGNALER] envoi rate : %s" % e)
        return False, "Pas de connexion : le message est gardé dans le dossier rapports."


def ouvrir_le_dossier(chemin):
    """Ouvre l'explorateur sur le dossier du rapport (Windows), sans planter."""
    try:
        dossier = os.path.dirname(chemin)
        if hasattr(os, "startfile"):
            os.startfile(dossier)
            return True
    except Exception as e:
        print("[SIGNALER] dossier non ouvert : %s" % e)
    return False
