@echo off
setlocal
title Vivarium social - MVP alpha
cd /d "%~dp0"

set "VIVARIUM_PY=.venv\Scripts\python.exe"
set "VIVARIUM_DB=data\vivarium-alpha.sqlite"

if not exist "%VIVARIUM_PY%" (
    echo.
    echo ERREUR : environnement Python introuvable.
    echo Ouvre Codex dans ce dossier et demande de reparer l'installation.
    echo.
    pause
    exit /b 2
)

if not exist "%VIVARIUM_DB%" (
    echo Creation de la residence alpha initiale...
    "%VIVARIUM_PY%" -m vivarium mvp-init --db "%VIVARIUM_DB%"
    if errorlevel 1 (
        echo.
        echo La residence n'a pas pu etre creee.
        pause
        exit /b 2
    )
)

echo.
echo Lancement du Vivarium...
echo LM Studio doit etre ouvert avec Gemma charge et le Local Server actif.
echo L'adresse du tableau de controle apparaitra ci-dessous.
echo Pour arreter proprement : Ctrl+C
echo.
"%VIVARIUM_PY%" -m vivarium mvp-run --db "%VIVARIUM_DB%" --enable-local-llm

echo.
echo Le Vivarium est arrete.
pause
