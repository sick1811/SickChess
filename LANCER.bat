@echo off
title SickChess
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PY=python"
    ) else (
        echo Python est introuvable.
        echo Installe-le depuis https://www.python.org puis relance ce fichier.
        echo Pense a cocher "Add Python to PATH" pendant l'installation.
        pause
        exit /b 1
    )
)

%PY% -c "import pygame, chess" 2>nul
if errorlevel 1 (
    echo Installation de pygame et python-chess...
    %PY% -m pip install -r requirements.txt
    echo.
)

%PY% SickChess.py

echo.
pause
