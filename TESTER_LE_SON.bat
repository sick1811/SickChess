@echo off
title SickChess - test du son
cd /d "%~dp0"
echo Tu dois entendre 3 sons : un petit carillon, puis deux "toc" de piece.
echo.
where py >nul 2>nul && (set "PY=py") || (set "PY=python")
%PY% outils\diagnostic_son.py
echo.
echo As-tu entendu les 3 sons ? Note-le dans la page "SickChess - A faire".
pause
