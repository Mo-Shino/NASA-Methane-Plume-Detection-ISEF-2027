"""
data_loader.py
NASA EMIT L2A Surface Reflectance & Methane Absorption Data Ingestion Pipeline.

Author: SpectraPlume Research Team (ISEF 2027)
Category: Earth & Environmental Sciences (EAEV - Atmospheric Science)
Dataset: NASA EMIT (Earth Surface Mineral Dust Source Investigation) onboard ISS
Products:
    - EMITL2ARFL: Estimated Surface Reflectance (380 - 2500 nm, 285 channels)
    - EMITL2BCH4PLM: Official NASA JPL Estimated Methane Plume Complexes
    - EMITL2BCH4ENH: NASA JPL Estimated Methane Column Enhancements
"""

import os
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List

import numpy as np
import xarray as xr

# Ensure SSL certificates work smoothly across Windows & Cloud environments
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

try:
    import earthaccess
except ImportError:
    earthaccess = None

try:
    from src.benchmark_generator import REQUIRED_SCENE_FILES, ensure_demo_scenes
except ImportError:
    from benchmark_generator import REQUIRED_SCENE_FILES, ensure_demo_scenes

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class EMITDataLoader:
    """
    Handles downloading, querying, caching, and preprocessing of NASA EMIT hyperspectral data.
    EMIT covers 380 - 2500 nm with 285 bands. Methane absorption focuses on 2150 - 2450 nm.
    """

    METHANE_MIN_WAVELENGTH = 2150.0  # nm
    METHANE_MAX_WAVELENGTH = 2450.0  # nm

    def __init__(self, cache_dir: Optional[str] = None):
        resolved_cache = Path(cache_dir) if cache_dir else (PROJECT_ROOT / "data" / "cache")
        self.cache_dir = str(resolved_cache)
        os.makedirs(self.cache_dir, exist_ok=True)

    @staticmethod
    def _load_env_token() -> Optional[str]:
        """Reads EARTHDATA_TOKEN from environment variables or local .env files safely."""
        if os.environ.get("EARTHDATA_TOKEN"):
            return os.environ["EARTHDATA_TOKEN"].strip()

        for env_candidate in (Path.cwd() / ".env", PROJECT_ROOT / ".env"):
            if env_candidate.exists():
                try:
                    for line in env_candidate.read_text(encoding="utf-8").splitlines():
                        line_s = line.strip()
                        if line_s.startswith("EARTHDATA_TOKEN="):
                            tok = line_s.split("=", 1)[1].strip().strip('"').strip("'")
                            if tok:
                                os.environ["EARTHDATA_TOKEN"] = tok
                                return tok
                except OSError:
                    pass
        return None

    def has_earthdata_token(self) -> bool:
        """Checks whether a NASA Earthdata bearer token is configured."""
        return bool(self._load_env_token())

    def login_earthdata(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None
    ):
        """Authenticate with NASA Earthdata Login via earthaccess library (token, netrc, or credentials)."""
        if earthaccess is None:
            raise ImportError("Please install 'earthaccess' via pip: pip install earthaccess")

        if token:
            os.environ["EARTHDATA_TOKEN"] = token.strip()
        else:
            self._load_env_token()

        if os.environ.get("EARTHDATA_TOKEN"):
            auth = earthaccess.login(strategy="environment")
        elif username and password:
            auth = earthaccess.login(strategy="interactive", username=username, password=password)
        else:
            auth = earthaccess.login(strategy="netrc")
        return auth

    def search_emit_granules(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: str = "2022-08-01",
        end_date: str = "2024-12-31",
        product: str = "EMITL2ARFL",
        count: int = 10
    ) -> List[Any]:
        """
        Search for EMIT granules over a geographic bounding box.

        Args:
            bbox: (lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat)
            product: 'EMITL2ARFL' (reflectance) or 'EMITL2BCH4PLM' (plumes)
            count: maximum number of records to return
        """
        if earthaccess is None:
            raise ImportError("earthaccess not installed")

        results = earthaccess.search_data(
            short_name=product,
            bounding_box=bbox,
            temporal=(start_date, end_date),
            count=count
        )
        return results

    def resolve_scene_path(self, filepath: str) -> Path:
        """
        Resolves a NetCDF path across arbitrary working directories and operating systems.
        If the target is one of the 4 official benchmark scenes and does not exist yet
        (e.g., fresh git clone or serverless cloud boot), automatically synthesizes it.
        """
        raw_path = Path(filepath)
        candidates = [
            raw_path,
            PROJECT_ROOT / raw_path,
            PROJECT_ROOT / "data" / "benchmark_scenes" / raw_path.name,
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate.resolve()

        if raw_path.name in REQUIRED_SCENE_FILES:
            ensure_demo_scenes()
            bootstrapped = PROJECT_ROOT / "data" / "benchmark_scenes" / raw_path.name
            if bootstrapped.exists():
                return bootstrapped.resolve()

        raise FileNotFoundError(f"File not found: {filepath}")

    @staticmethod
    def _open_dataset_portable(resolved_path: Path) -> Dict[str, Any]:
        """
        Opens a NetCDF dataset using available engines, loads arrays eagerly into memory,
        and immediately closes the file handle to prevent OS file-locking issues.
        """
        last_err = None
        for engine in ("netcdf4", "h5netcdf", "scipy", None):
            try:
                kwargs = {"engine": engine} if engine else {}
                with xr.open_dataset(str(resolved_path), **kwargs) as ds:
                    wavelengths = ds["wavelengths"].values.copy() if "wavelengths" in ds else None
                    reflectance = ds["reflectance"].values.copy()
                    lat = ds["latitude"].values.copy() if "latitude" in ds else None
                    lon = ds["longitude"].values.copy() if "longitude" in ds else None
                    metadata = dict(ds.attrs)
                return {
                    "wavelengths": wavelengths,
                    "reflectance": reflectance,
                    "latitude": lat,
                    "longitude": lon,
                    "metadata": metadata,
                }
            except Exception as err:
                last_err = err
        raise RuntimeError(f"Unable to read NetCDF dataset {resolved_path}: {last_err}")

    def load_local_nc(self, filepath: str) -> Dict[str, Any]:
        """
        Parses a local NASA EMIT NetCDF4 (.nc) file and extracts:
        - Reflectance cube: shape (lines, samples, bands)
        - Wavelength array: shape (bands,)
        - Latitude & Longitude arrays
        - Full NetCDF instrument attributes
        """
        resolved_path = self.resolve_scene_path(filepath)
        parsed = self._open_dataset_portable(resolved_path)

        reflectance = parsed["reflectance"]
        reflectance = np.where(reflectance < -0.01, np.nan, reflectance)

        return {
            "reflectance": reflectance,
            "wavelengths": parsed["wavelengths"],
            "latitude": parsed["latitude"],
            "longitude": parsed["longitude"],
            "metadata": parsed["metadata"],
        }

    def extract_methane_window(
        self,
        reflectance: np.ndarray,
        wavelengths: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Filters spectral bands to the primary methane SWIR absorption window (2150 - 2450 nm).
        Returns:
            sub_cube: reflectance in the methane window (H, W, B_sub)
            sub_wavelengths: wavelengths in the methane window (B_sub,)
            band_indices: indices of selected bands in original cube
        """
        if wavelengths is None or len(wavelengths) == 0:
            num_bands = reflectance.shape[-1]
            sub_wl = np.linspace(self.METHANE_MIN_WAVELENGTH, self.METHANE_MAX_WAVELENGTH, num_bands)
            return reflectance, sub_wl, np.arange(num_bands)

        indices = np.where(
            (wavelengths >= self.METHANE_MIN_WAVELENGTH) &
            (wavelengths <= self.METHANE_MAX_WAVELENGTH)
        )[0]

        if len(indices) == 0:
            indices = np.arange(min(40, reflectance.shape[-1]))

        sub_cube = reflectance[:, :, indices]
        sub_wavelengths = wavelengths[indices]

        return sub_cube, sub_wavelengths, indices
