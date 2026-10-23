#!/bin/bash
# outils/cloud/demarrage_session.sh - lance au debut de chaque session Claude Code
# (crochet SessionStart de .claude/settings.json).
#
# Sur le PC de Julien : ne fait RIEN (CLAUDE_CODE_REMOTE n'y vaut jamais "true").
# Dans le cloud : remet les bibliotheques Python a jour si requirements.txt a
# change depuis la configuration, et rappelle a Claude ce qu'il peut faire ou pas.

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
marque=/tmp/.sickchess_requirements.sha256
# On reinstalle si requirements.txt a change OU si pygame / python-chess manquent
# (le 23/10, la configuration les avait rates sans que personne ne le voie).
# --use-pep517 : sans lui, python-chess ne s'installe pas avec le pip du cloud.
if ! sha256sum --check --status "$marque" 2>/dev/null \
        || ! python3 -c "import pygame, chess" >/dev/null 2>&1; then
    if python3 -m pip install -q --break-system-packages --use-pep517 \
            -r requirements.txt ruff vulture psutil numpy >/dev/null 2>&1; then
        sha256sum requirements.txt > "$marque"
    fi
fi
if python3 -c "import pygame, chess" >/dev/null 2>&1; then
    biblios="pygame et python-chess : installes"
else
    biblios="ATTENTION : pygame ou python-chess MANQUE, lancer : python3 -m pip install --break-system-packages --use-pep517 -r requirements.txt"
fi

# La base des problemes, telechargee par configuration.sh
if [ ! -e puzzles ] && [ -f /opt/sickchess/puzzles/tranches.tsv ]; then
    ln -s /opt/sickchess/puzzles puzzles
fi
if [ -f puzzles/tranches.tsv ]; then
    problemes="Problemes : presents"
else
    problemes="Problemes ABSENTS : les tests qui en ont besoin sont sautes"
fi

stockfish="${SICKCHESS_STOCKFISH:-/usr/local/bin/stockfish}"
if [ -x "$stockfish" ]; then
    moteur="Stockfish : $stockfish"
else
    moteur="Stockfish ABSENT : seuls les tests rapides tournent (python tests/lancer_tous.py --rapide)"
fi

# Ce qui est ecrit ici est lu par Claude au debut de la session.
cat <<EOF
SickChess dans le cloud (Linux, sans ecran). $biblios. $moteur. $problemes.
- Tests : python tests/lancer_tous.py (tout) ou --rapide (sans Stockfish).
- Impossible ici (Windows seulement, a laisser a Claude Code sur le PC de Julien) :
  lancer le vrai jeu, Steam et le jeu en ligne, stockfish.exe, le .exe, l'installeur,
  la version amis, la surveillance en direct.
- Pas de syzygy/ (tables de finales, trop grosses) : l'analyse marche sans.
EOF
exit 0
