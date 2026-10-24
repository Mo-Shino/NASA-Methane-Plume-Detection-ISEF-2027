"""
data_loader.py
NASA EMIT L2A Surface Reflectance & Methane Absorption Data Ingestion Pipeline.

Author: Fares & Shnawy (ISEF 2027)
Dataset: NASA EMIT (Earth Surface Mineral Dust Source Investigation) onboard ISS
Product: EMIT_L2A_RFL (Estimated Surface Reflectance)
"""

import os
import numpy as np
import xarray as xr
from typing import Tuple, Dict, Any, Optional

try:
    import earthaccess
except ImportError:
    earthaccess = None


class EMITDataLoader:
    """
    Handles downloading, caching, and preprocessing of NASA EMIT hyperspectral data.
    EMIT covers 380 - 2500 nm with 285 bands. Methane absorption focuses on 2150 - 2450 nm.
    """

    METHANE_MIN_WAVELENGTH = 2150.0  # nm
    METHANE_MAX_WAVELENGTH = 2450.0  # nm

    def __init__(self, cache_dir: str = "./data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def login_earthdata(self, username: Optional[str] = None, password: Optional[str] = None):
        """Authenticate with NASA Earthdata Login via earthaccess library."""
        if earthaccess is None:
            raise ImportError("Please install 'earthaccess' via pip: pip install earthaccess")
        
        if username and password:
            auth = earthaccess.login(strategy="interactive", username=username, password=password)
        else:
            auth = earthaccess.login(strategy="netrc")
        return auth

    def search_emit_granules(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: str = "2023-01-01",
        end_date: str = "2024-12-31"
    ):
        """
        Search for EMIT L2A Reflectance granules over a geographic bounding box.
        bbox format: (lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat)
        """
        if earthaccess is None:
            raise ImportError("earthaccess not installed")
        
        results = earthaccess.search_data(
            short_name="EMIT_L2A_RFL",
            bounding_box=bbox,
            temporal=(start_date, end_date),
            count=10
        )
        return results

    def load_local_nc(self, filepath: str) -> Dict[str, Any]:
        """
        Parses a local NASA EMIT NetCDF4 (.nc) file and extracts:
        - Reflectance cube: shape (lines, samples, bands)
        - Wavelength array: shape (bands,)
        - Latitude & Longitude arrays
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        ds = xr.open_dataset(filepath, engine="netcdf4")

        # Extract wavelengths
        wavelengths = ds["wavelengths"].values if "wavelengths" in ds else None
        
        # Extract reflectance (handling scale factors and nodata)
        reflectance = ds["reflectance"].values
        reflectance = np.where(reflectance < -0.01, np.nan, reflectance)

        # Extract spatial coordinates if present
        lat = ds["latitude"].values if "latitude" in ds else None
        lon = ds["longitude"].values if "longitude" in ds else None

        return {
            "reflectance": reflectance,
            "wavelengths": wavelengths,
            "latitude": lat,
            "longitude": lon,
            "metadata": ds.attrs
        }

    def extract_methane_window(
        self,
        reflectance: np.ndarray,
        wavelengths: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Filters spectral bands to the primary methane SWIR absorption window (2150 - 2450 nm).
        Returns:
            sub_cube: reflectance in the methane window
            sub_wavelengths: wavelengths in the methane window
            band_indices: indices of selected bands in original cube
        """
        indices = np.where(
            (wavelengths >= self.METHANE_MIN_WAVELENGTH) & 
            (wavelengths <= self.METHANE_MAX_WAVELENGTH)
        )[0]

        sub_cube = reflectance[:, :, indices]
        sub_wavelengths = wavelengths[indices]

        return sub_cube, sub_wavelengths, indices
