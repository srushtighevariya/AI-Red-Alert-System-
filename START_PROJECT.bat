@echo off
title AI Document Red Alert - launcher
cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"

echo ==============================================
echo   AI Document Red Alert - starting...
echo ==============================================
echo.

:: ── 1. Check the tools are there ───────────────────────────────
if not exist "%PYTHON%" (
    echo [ERROR] Python virtual environment not found: .venv
    echo         Create it once with:
    echo           python -m venv .venv
    echo           .venv\Scripts\python -m pip install -r backend\requirements.txt
    pause
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js / npm is not installed. Get it from https://nodejs.org
    pause
    exit /b 1
)

sc query MongoDB 2>nul | find "RUNNING" >nul
if errorlevel 1 (
    echo [WARNING] The MongoDB service is not running. Trying to start it...
    net start MongoDB >nul 2>&1
    if errorlevel 1 echo [WARNING] Could not start MongoDB - login and history will fail until it runs.
)

if not exist "frontend\node_modules" (
    echo Installing frontend packages - first run only...
    pushd frontend
    call npm install
    popd
)

:: ── 2. Stop an old copy if one is still running ──────────────
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_servers.ps1"

:: ── 3. Start backend and frontend in their own windows ─────────
start "Red Alert Backend :8000" cmd /k "cd /d "%~dp0backend" && "%PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
start "Red Alert Frontend :5173" cmd /k "cd /d "%~dp0frontend" && npm run dev -- --port 5173 --strictPort"

:: ── 4. Wait until the website answers, then open the browser ───
echo Waiting for the servers to start...
powershell -NoProfile -Command "$deadline=(Get-Date).AddSeconds(60); while((Get-Date) -lt $deadline){ try { Invoke-WebRequest -UseBasicParsing http://localhost:5173 -TimeoutSec 2 | Out-Null; exit 0 } catch { Start-Sleep -Milliseconds 700 } }; exit 1"
if errorlevel 1 (
    echo [WARNING] The website did not answer within 60 seconds. Check the two server windows for errors.
) else (
    start "" http://localhost:5173
)

echo.
echo   Website:  http://localhost:5173
echo   API docs: http://127.0.0.1:8000/docs
echo.
echo To stop the project, close the "Red Alert Backend" and "Red Alert Frontend" windows.
echo The very first start downloads the AI model (about 1 GB) - this can take a few minutes.
timeout /t 8 >nul
