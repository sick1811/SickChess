# outils/banc_vers_page.py - prepare la recopie du banc d'essai dans la page
# « SickChess – Banc d'essai » (base de la page : collections passages / constats).
#
#     python outils/banc_vers_page.py tests/banc_essai.json <dossier_sortie> [machine]
#
# Ecrit un fichier JSON par document dans <dossier_sortie>/docs/ et la liste des
# ecritures (par lots de 50) dans <dossier_sortie>/lot0.json, lot1.json...
# Cowork passe chaque lot a ArtifactData (action "batch", file_path par document).
# Les decisions de Julien (decision, commentaire) ne sont JAMAIS ecrasees : un constat
# deja connu recoit un « update » sans ces champs.
#   --connus id1,id2,...   ids des constats deja dans la page (lus avant avec ArtifactData)

import json
import os
import sys


def main():
    source, sortie = sys.argv[1], sys.argv[2]
    machine = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else None
    connus = set()
    if "--connus" in sys.argv:
        connus = set(x for x in sys.argv[sys.argv.index("--connus") + 1].split(",") if x)
    r = json.load(open(source, encoding="utf-8"))
    S = r["sections"]
    date = r["date"]
    os.makedirs(os.path.join(sortie, "docs"), exist_ok=True)

    cles = {}
    try:
        ecrans = S["vitesse"]["mesures"]["ecrans"]
        ms = {k: v["ms_image"] for k, v in ecrans.items() if "ms_image" in v}
        lent = max(ms, key=ms.get)
        cles.update(partie_ms=ms.get("Partie"), ecran_lent=lent, ecran_lent_ms=ms[lent])
    except Exception:
        pass
    try:
        cles["partie_cpu"] = S["processeur"]["mesures"]["Partie"]["pourcent_un_coeur"]
    except Exception:
        pass
    try:
        m = S["menage"]["mesures"]
        cles["code_mort"] = (m.get("ruff") or 0) + (m.get("vulture_fonctions") or 0)
    except Exception:
        pass
    try:
        cles["controles_ok"] = S["tests"]["mesures"]["controles_ok"]
    except Exception:
        pass

    ecritures = []

    def ajouter(op, collection, doc_id, data):
        chemin = os.path.abspath(os.path.join(sortie, "docs", "%s_%s.json" % (collection, doc_id)))
        json.dump(data, open(chemin, "w", encoding="utf-8"), ensure_ascii=False)
        ecritures.append({"op": op, "collection": collection, "doc_id": doc_id, "file_path": chemin})

    ajouter("set", "passages", date.replace(" ", "_").replace(":", "h"), {
        "date": date, "machine": machine or r["machine"]["resume"], "rapide": r["rapide"],
        "cles": cles,
        "sections": {k: {"statut": s["statut"], "resume": s["resume"]} for k, s in S.items()}})
    vus = set()
    for nom, s in S.items():
        for c in s["constats"]:
            vus.add(c["id"])
            data = {"section": nom, "titre": c["titre"], "detail": c["detail"][:1800],
                    "gravite": c["gravite"], "vu_le": date, "actif": True}
            if c["id"] in connus:
                ajouter("update", "constats", c["id"], data)
            else:
                data["premier_vu"] = date
                ajouter("set", "constats", c["id"], data)
    # constats connus qui n'apparaissent plus : regles
    for cid in sorted(connus - vus):
        section = {"tes": "tests", "vit": "vitesse", "pro": "processeur", "mem": "memoire",
                   "mot": "moteur", "men": "menage", "con": "conflits"}.get(cid[:3])
        if section in S:   # seulement pour les sections refaites a ce passage
            ajouter("update", "constats", cid, {"actif": False})
    for i in range(0, len(ecritures), 50):
        json.dump(ecritures[i:i + 50], open(os.path.join(sortie, "lot%d.json" % (i // 50)), "w"),
                  ensure_ascii=False)
    print("%d ecritures, %d lot(s) dans %s" % (len(ecritures), (len(ecritures) + 49) // 50, sortie))


if __name__ == "__main__":
    main()
