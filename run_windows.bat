@echo off
cd /d "%~dp0"
where wt >nul 2>nul
if errorlevel 1 (
    cmd /k python batchGDL/main.py
) else (
    wt -d "%CD%" cmd /k python batchGDL/main.py
)
