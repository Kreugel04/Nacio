@echo off
echo Hunting for Nacio Server on Port 8501...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8501 ^| findstr LISTENING') do taskkill /F /PID %%a
echo Server successfully terminated!
pause