"""
run_demo.py
Cross-Platform Zero-Configuration Launcher for SpectraPlume (Windows, macOS, Linux).

1. Suppresses Streamlit's interactive first-run Email prompt automatically.
2. Verifies core Python libraries (and offers automatic pip install if missing).
3. Self-bootstraps all 4 NASA EMIT NetCDF4 benchmark granules if missing.
4. Verifies calibrated Spatial-Spectral PyTorch weights (retraining if missing).
5. Launches the SpectraPlume Mission Control Dashboard on http://localhost:8501.
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def ensure_streamlit_credentials() -> None:
    """Prevents Streamlit's first-run interactive 'Email:' prompt from blocking console startup."""
    st_home = Path.home() / ".streamlit"
    cred_file = st_home / "credentials.toml"
    if not cred_file.exists():
        try:
            st_home.mkdir(parents=True, exist_ok=True)
            cred_file.write_text('[general]\nemail = ""\n', encoding="utf-8")
        except OSError:
            pass


def check_dependencies(auto_install: bool = True) -> None:
    required_imports = ("streamlit", "torch", "numpy", "scipy", "xarray", "folium", "matplotlib")
    missing = []
    for mod in required_imports:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)

    if missing:
        print(f"  [INFO] Installing missing dependencies ({', '.join(missing)})...")
        if not auto_install:
            raise RuntimeError(f"Missing packages: {missing}. Run: pip install -r requirements.txt")
        req_path = PROJECT_ROOT / "requirements.txt"
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_path)])
    print("  [OK] Core scientific & dashboard libraries verified.")


def verify_assets() -> None:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from src.benchmark_generator import ensure_demo_scenes
    ensure_demo_scenes()
    print("  [OK] All 4 NASA EMIT NetCDF4 benchmark granules verified.")

    weights_path = PROJECT_ROOT / "weights" / "spatial_spectral_emit.pt"
    if not weights_path.exists():
        print("  [INFO] Calibrated neural weights not found. Training SpatialSpectralMethaneNet...")
        subprocess.check_call([sys.executable, str(PROJECT_ROOT / "train_model.py")], cwd=str(PROJECT_ROOT))
    print("  [OK] Calibrated Spatial-Spectral PyTorch weights verified.")


def main() -> int:
    print("=" * 79)
    print("       SpectraPlume: Autonomous NASA EMIT Methane Radar and Flux Inversion")
    print("              Regeneron ISEF 2027 - Earth and Environmental Sciences")
    print("=" * 79)
    print("\n[1/3] Checking Python environment and dependencies...")
    ensure_streamlit_credentials()
    check_dependencies(auto_install=True)

    print("\n[2/3] Verifying NASA EMIT benchmark granules and AI neural weights...")
    verify_assets()

    print("\n[3/3] Launching interactive Mission Control Dashboard...")
    print("Local URL: http://localhost:8501\n")

    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(PROJECT_ROOT / "app.py"),
        "--server.port=8501",
        "--browser.gatherUsageStats=false",
    ]
    return subprocess.call(cmd, cwd=str(PROJECT_ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
