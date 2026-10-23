#!/bin/bash
# outils/cloud/configuration.sh - SickChess dans Claude Code « cloud » (claude.ai/code).
#
# A COLLER dans l'environnement du cloud : claude.ai/code -> environnement ->
# « Setup script » (voir docs/CLAUDE_CLOUD.md). Il tourne une fois, en root, sur
# l'ordinateur Linux (Ubuntu 24.04) du cloud, AVANT que Claude commence ; le
# resultat est garde en memoire pour les sessions suivantes (s'il dure moins de
# 5 minutes environ).
#
# Ce qu'il installe :
#   - les bibliotheques Python du jeu et des outils (pygame, python-chess, ruff,
#     vulture, psutil) ;
#   - Stockfish 17.1 pour Linux (la meme version que stockfish.exe chez Julien),
#     ou, si le telechargement echoue, le Stockfish d'Ubuntu ;
#   - la base des problemes (puzzles/, 223 Mo) prise dans la version amis publiee
#     (sick1811/SickChess-amis), rangee dans /opt/sickchess/puzzles ; le script
#     de debut de session la relie au dossier du jeu ;
#   - la commande « python » si seul « python3 » existe (les tests l'appellent).
#
# Ce qui reste impossible dans le cloud (Windows seulement) : Steam, le vrai jeu
# a l'ecran, le .exe, l'installeur. Les tests, eux, tournent (sans ecran).
#
# Le script ne s'arrete jamais en erreur : une installation ratee ne doit pas
# empecher la session de demarrer (Claude le verra et pourra la refaire).

set -u
journal() { echo "[SICKCHESS CLOUD] $*"; }

# 1. « python » (les tests et le crochet de .claude/settings.json l'appellent)
if ! command -v python >/dev/null 2>&1; then
    journal "commande python absente : installation de python-is-python3"
    (apt-get update -qq && apt-get install -y -qq python-is-python3) >/dev/null 2>&1 \
        || ln -sf "$(command -v python3)" /usr/local/bin/python
fi

# 2. Bibliotheques Python (en parallele avec Stockfish : le cloud donne 5 min).
#    --use-pep517 : sans lui, python-chess ne s installe pas avec le pip du cloud
#    (pip 24.0, Python 3.13) - vu le 23/10 dans une vraie session.
installer_python() {
    local dossier=""
    for essai in "${CLAUDE_PROJECT_DIR:-}" "$PWD" /home/user/SickChess /workspace/SickChess; do
        if [ -n "$essai" ] && [ -f "$essai/requirements.txt" ]; then dossier="$essai"; break; fi
    done
    if [ -n "$dossier" ]; then
        python3 -m pip install -q --break-system-packages --use-pep517 -r "$dossier/requirements.txt" \
            ruff vulture psutil numpy || journal "pip : echec (refait au demarrage de la session)"
    else
        # Le depot n'est pas encore la : on installe la liste connue.
        python3 -m pip install -q --break-system-packages --use-pep517 "pygame>=2.5" "chess>=1.10" \
            ruff vulture psutil numpy || journal "pip : echec (refait au demarrage de la session)"
    fi
    journal "Python : $(python3 -c 'import pygame, chess; print("pygame", pygame.version.ver, "- python-chess", chess.__version__)' 2>/dev/null || echo 'incomplet')"
}

# 3. Stockfish 17.1 pour Linux, rangé dans /usr/local/bin/stockfish
installer_stockfish() {
    local cible=/usr/local/bin/stockfish
    if [ -x "$cible" ]; then journal "Stockfish deja la"; return; fi
    local tmp; tmp="$(mktemp -d)"
    local base="https://github.com/official-stockfish/Stockfish/releases/download/sf_17.1"
    local variante="stockfish-ubuntu-x86-64-avx2"
    grep -q avx2 /proc/cpuinfo 2>/dev/null || variante="stockfish-ubuntu-x86-64-sse41-popcnt"
    if curl -fsSL --max-time 120 -o "$tmp/sf.tar" "$base/$variante.tar" \
            && tar -xf "$tmp/sf.tar" -C "$tmp" \
            && install -m 755 "$tmp/stockfish/$variante" "$cible"; then
        journal "Stockfish 17.1 installe ($variante)"
    else
        journal "telechargement de Stockfish 17.1 impossible : Stockfish d'Ubuntu a la place"
        (apt-get update -qq && apt-get install -y -qq stockfish) >/dev/null 2>&1 \
            && ln -sf /usr/games/stockfish "$cible" \
            || journal "Stockfish non installe : seuls les tests sans moteur tourneront"
    fi
    rm -rf "$tmp"
}

# 4. Base des problemes : le paquet « puzzles » de la derniere version amis
installer_problemes() {
    local cible=/opt/sickchess/puzzles
    if [ -f "$cible/tranches.tsv" ]; then journal "problemes deja la"; return; fi
    local tmp; tmp="$(mktemp -d)"
    local url
    url="$(curl -fsSL --max-time 30         https://github.com/sick1811/SickChess-amis/releases/latest/download/maj.json         | python3 -c 'import json,sys; print(json.load(sys.stdin)["paquets"]["puzzles"]["url"])' 2>/dev/null)"
    if [ -n "$url" ] && curl -fsSL --max-time 240 -o "$tmp/puzzles.zip" "$url"             && mkdir -p /opt/sickchess             && python3 -m zipfile -e "$tmp/puzzles.zip" /opt/sickchess             && [ -f "$cible/tranches.tsv" ]; then
        journal "problemes installes ($(ls "$cible" | wc -l) fichiers)"
    else
        journal "problemes non telecharges : les tests qui en ont besoin seront sautes"
    fi
    rm -rf "$tmp"
}

installer_python &
installer_stockfish &
installer_problemes &
wait

if [ -x /usr/local/bin/stockfish ]; then
    journal "$(echo quit | /usr/local/bin/stockfish 2>/dev/null | head -1)"
fi
journal "fini. Pensez a la variable SICKCHESS_STOCKFISH=/usr/local/bin/stockfish (docs/CLAUDE_CLOUD.md)."
exit 0
