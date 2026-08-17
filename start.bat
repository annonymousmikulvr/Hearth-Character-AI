@echo off
setlocal EnableExtensions
title Hearth Launcher
cd /d "%~dp0"

echo.
echo  ========================================
echo   Hearth - Local Character AI
echo  ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo  [ERROR] Python not found on PATH.
  echo  Install Python 3.11+ from https://www.python.org/downloads/
  echo  Enable "Add python.exe to PATH" during setup.
  echo.
  pause
  exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
  echo  [ERROR] Node.js not found on PATH.
  echo  Install Node 18+ LTS from https://nodejs.org/
  echo.
  pause
  exit /b 1
)

echo  [1/4] Backend virtual environment...
if not exist "backend\.venv\Scripts\python.exe" (
  python -m venv "backend\.venv"
  if errorlevel 1 (
    echo  [ERROR] Could not create venv.
    pause
    exit /b 1
  )
)

echo  [2/4] Python packages...
"backend\.venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
"backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 (
  echo  [ERROR] pip install failed.
  pause
  exit /b 1
)

echo  [3/4] Frontend packages...
if not exist "frontend\node_modules" (
  pushd frontend
  call npm install
  if errorlevel 1 (
    echo  [ERROR] npm install failed.
    popd
    pause
    exit /b 1
  )
  popd
)

echo  [4/4] Starting API + UI...
echo.
echo  Backend:  http://127.0.0.1:8741
echo  Frontend: http://127.0.0.1:5173
echo.
echo  Keep BOTH windows open. Close them to stop Hearth.
echo  Tip: install Ollama and run:  ollama pull llama3.2
echo.

start "Hearth Backend" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe run.py"
timeout /t 2 /nobreak >nul
start "Hearth Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo  Launch complete. Opening browser in a few seconds...
timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:5173"

echo.
echo  If the page is blank, wait a few more seconds for Vite to finish starting.
echo.
pause
