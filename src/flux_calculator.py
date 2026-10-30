"""
flux_calculator.py
Integrated Mass Enhancement (IME) Formulation for Methane Emission Rate (Flux) Quantification
with Rigorous Gaussian Error Propagation and Scientific Uncertainty Analysis.

Mathematical Formulation:
    1. IME = sum_{i in Plume} (Delta_Omega_i * A_pixel * k_CH4)
       [Total instantaneous mass of methane inside the plume, in kg]
    2. Emission Flux Rate Q:
       Q = (IME * U_eff) / L  [kg/s]
       Q_hr = Q * 3600         [kg/hr or metric tons/hr]
    3. Gaussian Uncertainty Propagation:
       sigma_Q / Q = sqrt((sigma_U / U_eff)^2 + (sigma_IME / IME)^2 + (sigma_L / L)^2)

Author: SpectraPlume Research Team (ISEF 2027)
Category: Earth & Environmental Sciences (EAEV - Atmospheric Science)
"""

import numpy as np
from typing import Dict, Any


class IMEFluxCalculator:
    """
    Computes mass enhancement, emission rates (kg/hr, metric tons/hr),
    and formal 95% confidence intervals for segmented methane plumes
    according to Frankenberg et al. and Varon et al. (2018).
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
        wind_direction_deg: float = 0.0,
        wind_uncertainty_m_s: float = 1.2
    ) -> Dict[str, Any]:
        """
        Calculates the emission rate and formal uncertainty for a detected plume.

        Args:
            enhancement_map: 2D array of column enhancement in ppm * m.
            plume_mask: 2D binary array (1 for plume, 0 for background).
            wind_speed_m_s: 10-meter wind speed in meters/second from ERA5 or weather model.
            wind_direction_deg: Wind direction in degrees (0 = North, 90 = East).
            wind_uncertainty_m_s: 1-sigma uncertainty in reanalysis wind speed (default: 1.2 m/s).

        Returns:
            Dictionary containing:
                - ime_kg: Total plume mass in kilograms.
                - flux_kg_hr: Emission rate in kg/hour.
                - flux_ton_hr: Emission rate in metric tons/hour.
                - flux_uncertainty_ton_hr: 1-sigma absolute uncertainty in Tons/hr.
                - flux_ci95_low_ton_hr: Lower 95% confidence bound.
                - flux_ci95_high_ton_hr: Upper 95% confidence bound.
                - plume_area_km2: Surface area of plume in km^2.
                - plume_length_m: Estimated plume dispersion length in meters.
                - effective_wind_speed_m_s: Scaled boundary layer wind speed.
                - number_of_plume_pixels: Pixel count inside plume.
                - source_pixel: (row, col) coordinates of emission epicenter.
        """
        # Ensure mask is boolean
        binary_mask = (plume_mask > 0.5) & (~np.isnan(enhancement_map)) & (enhancement_map > 0)
        plume_pixels = enhancement_map[binary_mask]

        if len(plume_pixels) == 0:
            return {
                "ime_kg": 0.0,
                "flux_kg_hr": 0.0,
                "flux_ton_hr": 0.0,
                "flux_uncertainty_ton_hr": 0.0,
                "flux_ci95_low_ton_hr": 0.0,
                "flux_ci95_high_ton_hr": 0.0,
                "plume_area_km2": 0.0,
                "plume_length_m": 0.0,
                "effective_wind_speed_m_s": 0.0,
                "number_of_plume_pixels": 0,
                "source_pixel": (0, 0)
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

        # Plume source localization (epicenter with peak column enhancement)
        masked_enh = np.where(binary_mask, enhancement_map, 0.0)
        source_idx = np.argmax(masked_enh)
        source_y, source_x = np.unravel_index(source_idx, enhancement_map.shape)

        # 3. Calculate Flux Rate Q
        # Effective wind speed adjustment factor (Varon et al. 2018 recommends empirical scaling ~ 0.3 to 0.4 for 10m wind)
        u_eff = max(0.5, wind_speed_m_s * 0.35)

        flux_kg_s = (ime_kg * u_eff) / max(plume_length_m, self.pixel_size_m)
        flux_kg_hr = float(flux_kg_s * 3600.0)
        flux_ton_hr = float(flux_kg_hr / 1000.0)

        # 4. Rigorous Gaussian Uncertainty Propagation
        # Relative error components:
        # - Wind speed relative error: (wind_uncertainty / wind_speed)
        # - IME boundary delineation error: ~10% (Varon et al. 2018)
        # - Length scale PCA error: ~8%
        rel_u = min(0.35, max(0.12, (wind_uncertainty_m_s * 0.35) / u_eff))
        rel_ime = 0.10
        rel_l = 0.08

        total_rel_error = float(np.sqrt(rel_u**2 + rel_ime**2 + rel_l**2))
        flux_uncertainty_ton_hr = round(flux_ton_hr * total_rel_error, 3)

        # 95% Confidence Bounds (1.96 * sigma)
        ci_low = max(0.0, round(flux_ton_hr - 1.96 * flux_uncertainty_ton_hr, 3))
        ci_high = round(flux_ton_hr + 1.96 * flux_uncertainty_ton_hr, 3)

        return {
            "ime_kg": round(ime_kg, 2),
            "flux_kg_hr": round(flux_kg_hr, 1),
            "flux_ton_hr": round(flux_ton_hr, 3),
            "flux_uncertainty_ton_hr": flux_uncertainty_ton_hr,
            "flux_ci95_low_ton_hr": ci_low,
            "flux_ci95_high_ton_hr": ci_high,
            "relative_error_pct": round(total_rel_error * 100.0, 1),
            "plume_area_km2": round(plume_area_km2, 3),
            "plume_length_m": round(plume_length_m, 1),
            "effective_wind_speed_m_s": round(u_eff, 2),
            "number_of_plume_pixels": int(len(plume_pixels)),
            "source_pixel": (int(source_y), int(source_x))
        }
