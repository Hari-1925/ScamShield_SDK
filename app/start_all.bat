@echo off
echo Starting ScamShield Social Network...

REM Change directory to where the batch script is located (the app folder)
cd /d "%~dp0"

echo Starting Node.js Backend...
start cmd /k "cd backend && npm start"

echo Starting Local Python AI Agent...
start cmd /k "cd local_agent && pip install -r requirements.txt && uvicorn agent:app --port 8001"

echo Starting React Frontend...
start cmd /k "cd frontend && npm run dev"

echo All systems launched!
