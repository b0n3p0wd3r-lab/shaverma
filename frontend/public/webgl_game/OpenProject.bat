@echo off
echo Create server Node.js...
start "" /B node server.js

timeout /t 2 >nul

echo Open in Firefox...
start "" "C:\Program Files\Mozilla Firefox\firefox.exe" http://localhost:3000
