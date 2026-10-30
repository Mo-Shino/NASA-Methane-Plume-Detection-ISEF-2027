@echo off
title SpectraPlume - NASA EMIT Methane Radar (ISEF 2027)
color 0B
echo ===============================================================================
echo        SpectraPlume: Autonomous NASA EMIT Methane Radar ^& Flux Inversion
echo               Regeneron ISEF 2027 - Earth ^& Environmental Sciences
echo ===============================================================================
echo.
echo [1/3] Checking environment ^& dependencies...
python -c "import streamlit, torch, xarray, folium; print('  [OK] All core scientific libraries verified!')"
if %errorlevel% neq 0 (
    echo   [ERROR] Python environment missing dependencies. Please run: pip install -r requirements.txt
    pause
    exit /b
)

echo.
echo [2/3] Verifying benchmark scenes and AI neural weights...
if not exist "data\benchmark_scenes\EMIT_Permian_SuperEmitter_31N102W.nc" (
    echo   [INFO] Generating benchmark EMIT scenes for offline demonstration...
    python src/benchmark_generator.py
)
if exist "data\benchmark_scenes\EMIT_Permian_SuperEmitter_31N102W.nc" (
    echo   [OK] NASA EMIT benchmark scenes verified (Permian Basin, Sinai Testbed, Gulf of Suez).
)

if not exist "weights\spatial_spectral_emit.pt" (
    echo   [INFO] Model weights not found. Training and saving calibrated weights...
    python train_model.py
)
if exist "weights\spatial_spectral_emit.pt" (
    echo   [OK] Calibrated Spatial-Spectral weights verified!
)

echo.
echo [3/3] Launching interactive Mission Control Dashboard...
echo Local URL: http://localhost:8501
start http://localhost:8501
streamlit run app.py --server.headless=true --theme.base="dark"
pause
