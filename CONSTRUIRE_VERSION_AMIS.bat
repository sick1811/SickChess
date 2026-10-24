@echo off
chcp 65001 >nul
title SickChess - publier une version pour les amis
cd /d "%~dp0"

echo.
echo  ================================================================
echo   SickChess - nouvelle version pour les amis
echo  ================================================================
echo   Ce script fabrique le jeu (SickChess.exe), ne garde que ce qui a
echo   change depuis la derniere fois, et l'envoie sur GitHub.
echo   Tes amis n'auront plus qu'a cliquer sur "Mise a jour".
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

REM 24/10 (p32) : la verification avant chaque version (tests, banc d'essai,
REM MODE_TEST, numero Steam, licences, version, Git). Rien ne se fabrique si un
REM point est BLOQUANT.
echo  Verification avant la version (tests et banc d'essai : quelques minutes)...
%PY% outils\verifier_version.py --amis
if errorlevel 1 (
    echo.
    echo  La version n'est PAS fabriquee : corrige d'abord les points BLOQUANT ci-dessus.
    pause
    exit /b 1
)

echo  Pense a changer VERSION dans SickChess.py si c'est une grosse nouveaute
echo  (sinon le numero de version amis augmente tout seul).
echo.
set "NOTES="
set /p NOTES= Qu'est-ce qui change ? (separe par des ; ) : 
echo.

%PY% outils\publier_maj.py --notes "%NOTES%"

echo.
pause
