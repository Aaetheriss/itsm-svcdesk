@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0capture-rework.ps1"
exit /b %ERRORLEVEL%
