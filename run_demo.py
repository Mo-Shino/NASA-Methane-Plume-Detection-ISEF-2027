"""
run_demo.py
Cross-Platform Zero-Configuration Launcher for SpectraPlume 2.0 (Windows, macOS, Linux).

1. Verifies core Python libraries (and performs automatic pip install if missing).
2. Self-bootstraps all 4 NASA EMIT NetCDF4 benchmark granules if missing.
3. Verifies calibrated Spatial-Spectral PyTorch weights (retraining if missing).
4. Launches the SpectraPlume 2.0 Editorial Mission Console (FastAPI + Native Web GIS)
   on http://localhost:8000 and opens the default browser automatically.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def check_dependencies(auto_install: bool = True) -> None:
    required_imports = (
        "fastapi",
        "uvicorn",
        "multipart",
        "torch",
        "numpy",
        "scipy",
        "xarray",
        "matplotlib",
    )
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

    # Verify FastAPI + Starlette runtime compatibility (auto-heal if an older FastAPI is present)
    try:
        import fastapi
        _ = fastapi.FastAPI()
    except Exception:
        if auto_install:
            print("  [INFO] Upgrading FastAPI for Starlette runtime compatibility...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "fastapi>=0.116.0"])
        else:
            raise
    print("  [OK] Core scientific & FastAPI web engine libraries verified.")


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


def is_spectraplume_running(host: str, port: int) -> bool:
    url = f"http://{host}:{port}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=1.2) as resp:
            if resp.status == 200:
                payload = json.loads(resp.read().decode("utf-8"))
                ident = str(payload.get("engine", payload.get("service", "")))
                return payload.get("status") == "ok" and "SpectraPlume" in ident
    except Exception:
        return False
    return False


def is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def find_available_port(host: str, preferred_port: int = 8000) -> int:
    for port in range(preferred_port, preferred_port + 20):
        if is_port_free(host, port):
            return port
    return preferred_port


def open_browser_when_ready(url: str, health_url: str) -> None:
    for _ in range(40):
        try:
            with urllib.request.urlopen(health_url, timeout=1.0) as resp:
                if resp.status == 200:
                    webbrowser.open(url)
                    return
        except Exception:
            time.sleep(0.25)
    webbrowser.open(url)


def main() -> int:
    parser = argparse.ArgumentParser(description="SpectraPlume 2.0 Mission Console Launcher")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")), help="Preferred port")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open web browser")
    parser.add_argument("--legacy-streamlit", action="store_true", help="Launch legacy Streamlit dashboard instead")
    args = parser.parse_args()

    print("=" * 79)
    print("       SpectraPlume 2.0: Autonomous Satellite Methane Intelligence")
    print("              Regeneron ISEF 2027 - Earth and Environmental Sciences")
    print("=" * 79)

    print("\n[1/3] Checking Python environment and dependencies...")
    check_dependencies(auto_install=True)

    print("\n[2/3] Verifying NASA EMIT benchmark granules and AI neural weights...")
    verify_assets()

    if args.legacy_streamlit:
        print("\n[3/3] Launching Legacy Streamlit Dashboard on http://localhost:8501 ...")
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(PROJECT_ROOT / "app.py"),
            "--server.port=8501",
            "--browser.gatherUsageStats=false",
        ]
        return subprocess.call(cmd, cwd=str(PROJECT_ROOT))

    # Check if SpectraPlume 2.0 is already live on preferred port
    probe_host = "127.0.0.1" if args.host in ("0.0.0.0", "127.0.0.1", "localhost") else args.host
    if is_spectraplume_running(probe_host, args.port):
        live_url = f"http://localhost:{args.port}"
        print(f"\n[3/3] SpectraPlume 2.0 is already live at {live_url}")
        if not args.no_browser:
            print("  [OK] Opening Mission Console in your browser...")
            webbrowser.open(live_url)
        return 0

    port = find_available_port(args.host, args.port)
    local_url = f"http://localhost:{port}"
    health_url = f"http://{probe_host}:{port}/api/health"

    print("\n[3/3] Launching SpectraPlume 2.0 Editorial Mission Console...")
    print(f"  Local URL : {local_url}")
    print("  Press Ctrl+C to stop the server.\n")

    if not args.no_browser and os.environ.get("SPACE_ID") is None:
        threading.Thread(
            target=open_browser_when_ready,
            args=(local_url, health_url),
            daemon=True,
        ).start()

    os.chdir(str(PROJECT_ROOT))
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    import uvicorn
    uvicorn.run("server:app", host=args.host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
