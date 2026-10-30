@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title SpectraPlume - NASA EMIT Methane Radar - ISEF 2027
color 0B

python run_demo.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] SpectraPlume encountered an issue during startup.
    pause
    exit /b %errorlevel%
)
pause
