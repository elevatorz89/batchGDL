@echo off
cd /d "%~dp0"
wt -d "%CD%" cmd /k python batchGDL/main.py
