@echo off
cd /d "%~dp0"
where wt >nul 2>nul
if %errorlevel%==0 (
    wt -d "%CD%" cmd
) else (
    cmd
)