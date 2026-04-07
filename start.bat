@echo off
echo Starting Matrix-Based Force Distribution Simulator...
echo.
echo [1/2] Starting Flask backend on http://localhost:5000
start "Flask Backend" cmd /k "cd /d %~dp0backend && python app.py"
timeout /t 2 >nul
echo [2/2] Opening frontend in browser...
start "" "%~dp0frontend\index.html"
echo.
echo Done! Backend running at http://localhost:5000
