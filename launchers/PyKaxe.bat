@echo off
setlocal
title PyKaxe

rem Double-click launcher for PyKaxe on Windows.
rem Opens a console automatically, checks prerequisites, then runs the app
rem via `pipx run pykaxe` -- no install step, always the latest PyPI release.

set "PYTHON_CMD="
where python >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=python"
if "%PYTHON_CMD%"=="" (
    where py >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=py"
)

if "%PYTHON_CMD%"=="" (
    echo PyKaxe needs Python, but it wasn't found on this PC.
    echo Install it from https://www.python.org/downloads/
    echo IMPORTANT: check "Add python.exe to PATH" during setup, then double-click PyKaxe again.
    pause
    exit /b 1
)

where pipx >nul 2>nul
if errorlevel 1 (
    echo PyKaxe needs pipx, but it wasn't found on this PC.
    echo.
    echo Open Command Prompt and run these two commands:
    echo   %PYTHON_CMD% -m pip install --user pipx
    echo   %PYTHON_CMD% -m pipx ensurepath
    echo.
    echo Then close this window, open a new Command Prompt ^(or double-click PyKaxe again^),
    echo and it will work from then on.
    pause
    exit /b 1
)

pipx run pykaxe
pause
