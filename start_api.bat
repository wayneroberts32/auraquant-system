@echo off
echo ===============================================
echo     Starting AuraQuant Quantum Brain API
echo ===============================================
echo.

cd /d "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\backend"

echo Starting API server...
echo.
echo API will be available at:
echo   http://localhost:8000
echo   http://localhost:8000/docs (documentation)
echo.
echo Default Login:
echo   Email: wayneroberts32@outlook.com.au
echo   Password: admin123 (change after deployment)
echo.
echo Press Ctrl+C to stop the server
echo ===============================================
echo.

py -3.13 -m api.main

pause