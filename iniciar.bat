@echo off
title Painel Financeiro - Iniciador
cd /d "%~dp0"

call "%~dp0parar.bat" >nul 2>&1

if defined PAINEL_BACKUP_DIR call "%~dp0backup.bat"

echo.
echo  ========================================
echo   Iniciando Painel Financeiro
echo  ========================================
echo.
echo  Backend  : http://localhost:8000
echo  Frontend : http://localhost:5173
echo  Docs API : http://localhost:8000/docs
echo.

start "Painel - Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\activate.bat && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

start "Painel - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo  Aguardando o frontend subir...

set tentativas=0
:wait
timeout /t 1 /nobreak >nul
set /a tentativas+=1
powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri 'http://localhost:5173' -UseBasicParsing -TimeoutSec 1).StatusCode } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
  if %tentativas% lss 30 goto wait
)

start "" "http://localhost:5173"

exit
