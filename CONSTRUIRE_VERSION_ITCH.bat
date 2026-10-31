@echo off
chcp 65001 >nul
title SickChess - fabriquer la version itch.io (sans Steam)
cd /d "%~dp0"

echo.
echo  ================================================================
echo   SickChess - version itch.io (sans Steam)
echo  ================================================================
echo   Ce script fabrique le jeu (SickChess.exe) et le zip
echo   publier\itch\SickChess_^<version^>_itch.zip : le jeu complet, SANS
echo   steam_api64.dll ni steam_appid.txt. Le jeu ne demarre jamais Steam.
echo   Rien n'est envoye sur Internet : le zip se depose a la main sur itch.io.
echo.

set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
    echo Python est introuvable. Installe-le depuis https://www.python.org
    pause
    exit /b 1
)

%PY% -c "import PyInstaller, pygame, chess" 2>nul
if errorlevel 1 (
    echo Installation de PyInstaller, pygame et python-chess...
    %PY% -m pip install pyinstaller -r requirements.txt
    echo.
)

REM 31/10 : verification avant la version itch (tests, banc d'essai, MODE_TEST
REM coupe, licences, aucun fichier Steam). Rien ne se fabrique si un point est BLOQUANT.
echo  Verification avant la version (tests et banc d'essai : quelques minutes)...
%PY% outils\verifier_version.py --itch
if errorlevel 1 (
    echo.
    echo  La version n'est PAS fabriquee : corrige d'abord les points BLOQUANT ci-dessus.
    pause
    exit /b 1
)

%PY% outils\publier_maj.py --itch

echo.
pause
