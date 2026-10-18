# Crochet de Claude Code : apres chaque modification d'un fichier .py,
# verifie qu'il se compile (faute de frappe, parenthese oubliee, indentation).
# En cas d'erreur, Claude la voit tout de suite et la corrige.
import json
import py_compile
import sys

try:
    donnees = json.load(sys.stdin)
except Exception:
    sys.exit(0)
chemin = (donnees.get("tool_input") or {}).get("file_path", "")
if not chemin.endswith(".py"):
    sys.exit(0)
try:
    py_compile.compile(chemin, doraise=True)
except py_compile.PyCompileError as e:
    print("Erreur de syntaxe dans %s :\n%s" % (chemin, e.msg), file=sys.stderr)
    sys.exit(2)
except FileNotFoundError:
    pass
sys.exit(0)
