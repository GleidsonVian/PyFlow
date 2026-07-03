@echo off
title PyFlow RPA
cd /d "%~dp0"

REM Usa o venv local se existir, senão usa o Python do sistema
if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else (
    set PYTHON=python
)

start "" %PYTHON% main.py
