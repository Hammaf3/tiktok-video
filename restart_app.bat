@echo off
echo ============================================================
echo Restarting Integrated App with Debug Logging
echo ============================================================
echo.
echo Step 1: Stopping old process on port 5000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    echo Killing process ID: %%a
    taskkill /F /PID %%a
)
timeout /t 2 /nobreak >nul

echo.
echo Step 2: Starting app with debug logging...
echo.
python integrated_app.py

pause
