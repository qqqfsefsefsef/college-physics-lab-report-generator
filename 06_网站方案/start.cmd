@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0start.ps1" (
  echo [ERR] start.ps1 is missing next to this file.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
if errorlevel 1 pause
