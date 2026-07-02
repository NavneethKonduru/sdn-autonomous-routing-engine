@echo off
setlocal

echo =======================================================
echo    Starting Autonomous Network Command Center...       
echo =======================================================

:: Get the directory of this script
set DIR=%~dp0

:: Check for python vs python3
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
) else (
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=python
    ) else (
        echo Error: Python is not installed or not in PATH.
        exit /b 1
    )
)

:: Start the Python Backend (Flask-SocketIO)
echo [1/2] Starting SDN Backend Controller on port 5000...
start "SDN Backend" cmd /c "%PYTHON_CMD% "%DIR%src\applications\command_center\server.py""

:: Wait a moment to ensure backend is starting
timeout /t 2 /nobreak >nul

:: Start the React Frontend (Vite)
echo [2/2] Starting React Frontend UI...
set FRONTEND_DIR=%DIR%src\applications\command_center\frontend
cd /d "%FRONTEND_DIR%"

if not exist "node_modules\" (
    echo Dependencies not found. Running npm install...
    call npm install
)

start "SDN Frontend" cmd /c "npm run dev"

echo =======================================================
echo    Command Center is RUNNING in separate windows!      
echo    Access UI at: http://localhost:5173                 
echo                                                       
echo    Close the newly opened windows to stop the servers. 
echo =======================================================

endlocal
