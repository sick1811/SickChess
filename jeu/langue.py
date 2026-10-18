# langue.py - SickChess 17/10 (travail p12, demande de Julien) : le jeu en
# anglais, en plus du francais.
#
# La traduction se fait AU MOMENT D'AFFICHER (ui.texte, ui.paragraphe,
# ui.texte_centre_dans) : le code continue d'ecrire en francais, et chaque
# texte affiche passe par traduire(). Les textes avec des nombres (« Coup 4
# sur 10 ») sont reconnus grace a leur modele (« Coup %d sur %d ») dans
# langue_en.py. Reglage : Options -> Affichage -> Langue (config "langue" :
# "fr" ou "en" ; par defaut, la langue de Windows).
# manquants() liste les textes affiches sans traduction (pour les tests).

import json
import locale
import os
import re

_etat = {"langue": None}
_memo = {}
_modeles = []
_manquants = set()
_SPEC = re.compile(r"%(?:[-+ 0#]*\d*(?:\.\d+)?[sdfi])")


def _langue_du_systeme():
    try:
        code = (locale.getdefaultlocale()[0] or "")
    except Exception:
        code = ""
    return "fr" if code.lower().startswith("fr") or not code else "en"


def langue():
    if _etat["langue"] is None:
        valeur = None
        for base in (os.getcwd(), os.path.dirname(os.path.dirname(os.path.abspath(__file__)))):
            try:
                with open(os.path.join(base, "config.json"), "r", encoding="utf-8") as f:
                    valeur = (json.load(f) or {}).get("langue")
                break
            except (OSError, ValueError, AttributeError):
                continue
        _etat["langue"] = valeur if valeur in ("fr", "en") else _langue_du_systeme()
    return _etat["langue"]


def regler(code):
    """Change la langue tout de suite (Options)."""
    _etat["langue"] = code if code in ("fr", "en") else "fr"
    _memo.clear()


def _table():
    from langue_en import EN
    if not _modeles:
        for fr, en in EN.items():
            if "%" in fr:
                motif = ""
                pos = 0
                for m in _SPEC.finditer(fr):
                    motif += re.escape(fr[pos:m.start()].replace("%%", "%")) + "(.*?)"
                    pos = m.end()
                motif += re.escape(fr[pos:].replace("%%", "%"))
                if pos:
                    _modeles.append((re.compile("^" + motif + "$", re.S), en))
        _modeles.sort(key=lambda x: -len(x[0].pattern))
        _table.majuscules = {fr.upper(): en.upper() for fr, en in EN.items() if "%" not in fr}
    return EN


def _remplir(en, groupes):
    groupes = [traduire(g) for g in groupes]
    if "{" in en and re.search(r"\{\d\}", en):
        try:
            return en.format(*groupes)
        except (IndexError, ValueError):
            pass
    sortie, i, pos = "", 0, 0
    for m in _SPEC.finditer(en):
        sortie += en[pos:m.start()]
        sortie += groupes[i] if i < len(groupes) else ""
        i += 1
        pos = m.end()
    return (sortie + en[pos:]).replace("%%", "%")


def traduire(texte):
    """Le texte dans la langue choisie (inchange en francais ou si inconnu)."""
    if not texte or langue() == "fr" or not isinstance(texte, str):
        return texte
    if texte in _memo:
        return _memo[texte]
    table = _table()
    resultat = table.get(texte)
    if resultat is None and "%" not in texte:
        resultat = getattr(_table, "majuscules", {}).get(texte)
    if resultat is None:
        nu = texte.strip()
        if nu != texte and nu in table:
            resultat = texte.replace(nu, table[nu])
    if resultat is None:
        for motif, en in _modeles:
            m = motif.match(texte)
            if m:
                resultat = _remplir(en, m.groups())
                break
    if resultat is None:
        # Textes composes (« 1-0   Analyse... », themes « Mat, Mat en 1 ») :
        # on traduit chaque morceau.
        for sep in ("   ", "  -  ", " · ", ", "):
            if sep in texte:
                morceaux = texte.split(sep)
                traduits = [traduire(m) for m in morceaux]
                if traduits != morceaux:
                    resultat = sep.join(traduits)
                break
    if resultat is None:
        resultat = texte
        if re.search(r"[A-Za-zÀ-ÿ]{3}", texte):
            _manquants.add(texte)
    if len(_memo) > 5000:
        _memo.clear()
    _memo[texte] = resultat
    return resultat


def manquants():
    return set(_manquants)
