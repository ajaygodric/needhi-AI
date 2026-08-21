@echo off
echo Starting Needhi AI Full-Stack Legal Suite...
echo.

cd /d "%~dp0"

echo Starting Python Backend Server...
start "Needhi AI Backend" cmd /c "python backend/server.py"

echo Starting React Frontend Dev Server...
cd frontend
start "Needhi AI Frontend" cmd /c "npm run dev"

echo.
echo Application started! Open http://localhost:5173 to view the React frontend.
echo The backend is running on http://localhost:8000.
echo.
pause
