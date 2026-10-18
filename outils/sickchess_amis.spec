# -*- mode: python ; coding: utf-8 -*-
# sickchess_amis.spec - recette PyInstaller de la version amis.
#
# Lancee par outils/publier_maj.py (via CONSTRUIRE_VERSION_AMIS.bat) :
#     py -m PyInstaller outils/sickchess_amis.spec
#
# PARTICULARITE IMPORTANTE : le code du jeu (jeu/*.py) n'est PAS enferme dans
# l'exe. Il reste en fichiers .py a cote, que SickChess.py ajoute au chemin de
# Python au demarrage. Resultat : une correction dans le code ne demande pas
# de refaire l'exe, et la mise a jour des amis ne pese que quelques Mo.
# On analyse quand meme jeu/*.py, pour que PyInstaller embarque tous les
# modules de Python dont le code a besoin (json, socket, ctypes...), puis on
# retire les modules du jeu eux-memes du paquet.

import glob
import os

from PyInstaller.utils.hooks import collect_submodules

RACINE = os.path.abspath(os.path.join(SPECPATH, ".."))
JEU = os.path.join(RACINE, "jeu")

MODULES_JEU = sorted(os.path.splitext(os.path.basename(p))[0]
                     for p in glob.glob(os.path.join(JEU, "*.py")))

# Modules de Python ajoutes "au cas ou" : si une future version du code en
# utilise un, l'exe n'aura pas a etre refait pour autant.
EN_PLUS = [
    "asyncio", "base64", "bisect", "bz2", "calendar", "colorsys", "concurrent.futures",
    "copy", "csv", "ctypes", "ctypes.wintypes", "dataclasses", "datetime", "decimal",
    "difflib", "email", "fractions", "functools", "glob", "gzip", "hashlib", "heapq",
    "html", "http.client", "io", "itertools", "json", "locale", "logging", "lzma",
    "math", "pathlib", "pickle", "platform", "queue", "random", "re", "secrets",
    "shutil", "socket", "sqlite3", "ssl", "statistics", "string", "struct",
    "subprocess", "tempfile", "textwrap", "threading", "traceback", "typing",
    "unicodedata", "urllib.parse", "urllib.request", "uuid", "wave", "webbrowser",
    "xml.etree.ElementTree", "zipfile", "zlib",
]

a = Analysis(
    [os.path.join(RACINE, "SickChess.py")],
    pathex=[JEU],
    hiddenimports=MODULES_JEU + collect_submodules("chess") + EN_PLUS,
    excludes=["tkinter", "matplotlib", "numpy", "PIL", "IPython", "pytest"],
    noarchive=False,
)

# Le code du jeu reste dehors (voir plus haut).
_dossier_jeu = os.path.normcase(JEU + os.sep)
a.pure = [entree for entree in a.pure
          if not (entree[1] and os.path.normcase(os.path.abspath(entree[1]))
                  .startswith(_dossier_jeu))]

pyz = PYZ(a.pure)

_icone = os.path.join(RACINE, "assets", "icone.ico")
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SickChess",
    icon=_icone if os.path.exists(_icone) else None,
    console=False,
    upx=False,
)

coll = COLLECT(exe, a.binaries, a.datas, name="SickChess", upx=False)
