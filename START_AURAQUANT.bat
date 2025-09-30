@echo off
echo ======================================================================
echo AURAQUANT TRADING SYSTEM - FULL STACK STARTUP
echo ======================================================================

echo Starting Backend API Server...
start /B cmd /c "cd backend && python api\main.py"
timeout /t 3 /nobreak > nul

echo Starting Frontend...
start http://localhost:8000
start "" "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\frontend\index.html"

echo ======================================================================
echo System Started Successfully!
echo Backend API: http://localhost:8000
echo Frontend: Open in browser
echo MongoDB: Atlas Cloud Database
echo ======================================================================
pause
