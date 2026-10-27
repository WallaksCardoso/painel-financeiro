@echo off
echo  Parando servidores do Painel Financeiro...

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000" ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":5173" ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1

taskkill /F /FI "WINDOWTITLE eq Painel - Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Painel - Frontend*" >nul 2>&1

echo  Pronto.

exit /b 0
