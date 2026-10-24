"""
flux_calculator.py
Integrated Mass Enhancement (IME) Formulation for Methane Emission Rate (Flux) Quantification.

Mathematical Formulation:
    1. IME = sum_{i in Plume} (Delta_Omega_i * A_pixel * k_CH4)
       [Total instantaneous mass of methane inside the plume, in kg]
    2. Emission Flux Rate Q:
       Q = (IME * U_eff) / L  [kg/s]
       Q_hr = Q * 3600         [kg/hr or metric tons/hr]

Where:
    Delta_Omega_i : Column abundance enhancement at pixel i (ppm * m)
    A_pixel       : Ground pixel area (for EMIT: 60m x 60m = 3600 m^2)
    k_CH4         : Conversion constant from ppm*m to kg/m^2 (~ 0.00067 kg/m^3 standard air)
    U_eff         : Effective 10m wind speed (from ERA5 / HRRR atmospheric reanalysis)
    L             : Plume length along the wind dispersion axis (meters)

Author: Fares & Shnawy (ISEF 2027)
"""

import numpy as np
from typing import Dict, Any


class IMEFluxCalculator:
    """
    Computes mass enhancement and emission rates (kg/hr, metric tons/hr)
    for segmented methane plumes according to Frankenberg et al. and Varon et al. (2018).
    """

    # Molar mass of CH4 = 16.04 g/mol; molar volume of air at STP = 22.4 L/mol
    # Conversion: 1 ppm * m of CH4 = 1e-6 * (16.04e-3 kg / 0.0224 m^3) = 7.16e-4 g/m^2 = 7.16e-7 kg/m^2
    PPM_M_TO_KG_M2 = 7.16e-7  # kg / (m^2 * ppm * m)

    def __init__(self, pixel_size_m: float = 60.0):
        self.pixel_size_m = pixel_size_m
        self.pixel_area_m2 = pixel_size_m * pixel_size_m

    def compute_flux(
        self,
        enhancement_map: np.ndarray,
        plume_mask: np.ndarray,
        wind_speed_m_s: float,
        wind_direction_deg: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calculates the emission rate for a detected plume.

        Args:
            enhancement_map: 2D array of column enhancement in ppm * m.
            plume_mask: 2D binary array (1 for plume, 0 for background).
            wind_speed_m_s: 10-meter wind speed in meters/second from ERA5 or weather model.
            wind_direction_deg: Wind direction in degrees (0 = North, 90 = East).

        Returns:
            Dictionary containing:
                - ime_kg: Total plume mass in kilograms.
                - flux_kg_hr: Emission rate in kg/hour.
                - flux_ton_hr: Emission rate in metric tons/hour.
                - plume_area_km2: Surface area of plume in km^2.
                - plume_length_m: Estimated plume dispersion length in meters.
        """
        # Ensure mask is boolean
        binary_mask = (plume_mask > 0.5) & (~np.isnan(enhancement_map)) & (enhancement_map > 0)
        plume_pixels = enhancement_map[binary_mask]

        if len(plume_pixels) == 0:
            return {
                "ime_kg": 0.0,
                "flux_kg_hr": 0.0,
                "flux_ton_hr": 0.0,
                "plume_area_km2": 0.0,
                "plume_length_m": 0.0
            }

        # 1. Calculate IME (Integrated Mass Enhancement) in kg
        pixel_masses_kg = plume_pixels * self.PPM_M_TO_KG_M2 * self.pixel_area_m2
        ime_kg = float(np.sum(pixel_masses_kg))

        # 2. Plume geometric features
        plume_area_km2 = float((len(plume_pixels) * self.pixel_area_m2) / 1e6)

        # Estimate effective plume length along dominant axis using bounding box or PCA
        y_coords, x_coords = np.where(binary_mask)
        dx = (np.max(x_coords) - np.min(x_coords) + 1) * self.pixel_size_m
        dy = (np.max(y_coords) - np.min(y_coords) + 1) * self.pixel_size_m
        plume_length_m = float(np.sqrt(dx**2 + dy**2))

        # 3. Calculate Flux Rate Q
        # Effective wind speed adjustment factor (Varon et al. 2018 recommends empirical scaling ~ 0.3 to 0.4 for 10m wind)
        u_eff = max(0.5, wind_speed_m_s * 0.35)

        flux_kg_s = (ime_kg * u_eff) / max(plume_length_m, self.pixel_size_m)
        flux_kg_hr = float(flux_kg_s * 3600.0)
        flux_ton_hr = float(flux_kg_hr / 1000.0)

        return {
            "ime_kg": round(ime_kg, 2),
            "flux_kg_hr": round(flux_kg_hr, 1),
            "flux_ton_hr": round(flux_ton_hr, 3),
            "plume_area_km2": round(plume_area_km2, 3),
            "plume_length_m": round(plume_length_m, 1),
            "effective_wind_speed_m_s": round(u_eff, 2),
            "number_of_plume_pixels": int(len(plume_pixels))
        }
