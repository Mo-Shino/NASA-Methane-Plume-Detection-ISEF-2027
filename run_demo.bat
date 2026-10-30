@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title SpectraPlume - NASA EMIT Methane Radar - ISEF 2027
color 0B

echo ===============================================================================
echo        SpectraPlume: Autonomous NASA EMIT Methane Radar and Flux Inversion
echo               Regeneron ISEF 2027 - Earth and Environmental Sciences
echo ===============================================================================
echo.

echo [1/3] Checking Python environment and dependencies...
python -c "import streamlit, torch, xarray, folium; print('  [OK] Core scientific libraries verified.')"
if %errorlevel% neq 0 (
    echo   [ERROR] Missing required Python libraries.
    echo   Please run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [2/3] Verifying benchmark scenes and AI neural weights...
if not exist "data\benchmark_scenes\EMIT_Permian_SuperEmitter_31N102W.nc" (
    echo   [INFO] Generating benchmark scenes for offline demonstration...
    python src\benchmark_generator.py
)
if exist "data\benchmark_scenes\EMIT_Permian_SuperEmitter_31N102W.nc" (
    echo   [OK] NASA EMIT benchmark scenes verified.
)

if not exist "weights\spatial_spectral_emit.pt" (
    echo   [INFO] Calibrated weights not found. Generating model weights...
    python train_model.py
)
if exist "weights\spatial_spectral_emit.pt" (
    echo   [OK] Calibrated Spatial-Spectral weights verified.
)

echo.
echo [3/3] Launching interactive Mission Control Dashboard...
echo Local URL: http://localhost:8501
echo Opening browser...
echo.

python -m streamlit run app.py --theme.base="dark" --server.port=8501 --browser.gatherUsageStats=false

pause
