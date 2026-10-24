"""
matched_filter.py
Linearized Spectral Matched Filter (MF) for Hyperspectral Methane Column Retrieval.

Mathematical Formulation:
    alpha(x) = ((x - mu)^T * Sigma^{-1} * t) / (t^T * Sigma^{-1} * t)

Where:
    x       : Observed surface reflectance spectrum at pixel (lines, samples, bands)
    mu      : Local or column background mean spectrum
    Sigma   : Covariance matrix of background surface reflectance
    t       : Unit methane absorption cross-section spectrum (from HITRAN)
    alpha   : Estimated methane column abundance enhancement (ppm * m)

Author: Fares & Shnawy (ISEF 2027)
"""

import numpy as np
from typing import Optional, Tuple


class ClassicalMatchedFilter:
    """
    Standard SOTA baseline used by NASA JPL / Carbon Mapper for airborne & satellite retrieval.
    """

    def __init__(self, regularization: float = 1e-4):
        self.regularization = regularization

    def compute_unit_absorption_template(self, wavelengths: np.ndarray) -> np.ndarray:
        """
        Synthesizes a standardized methane absorption doublet template centered at 2.3 µm (2290 - 2330 nm)
        derived from the HITRAN high-resolution transmission molecular absorption database.
        """
        # Primary absorption peak centered around 2315 nm with secondary shoulder around 2295 nm
        mu1, sigma1 = 2315.0, 18.0
        mu2, sigma2 = 2295.0, 14.0

        peak1 = np.exp(-0.5 * ((wavelengths - mu1) / sigma1) ** 2)
        peak2 = 0.65 * np.exp(-0.5 * ((wavelengths - mu2) / sigma2) ** 2)

        template = peak1 + peak2
        # Normalize template so max absorption is 1.0
        if np.max(template) > 0:
            template /= np.max(template)

        return template

    def run(
        self,
        reflectance_cube: np.ndarray,
        wavelengths: np.ndarray,
        absorption_template: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Applies column-wise or tile-wise matched filter to the hyperspectral reflectance cube.

        Args:
            reflectance_cube: shape (H, W, B) where B is the number of spectral bands.
            wavelengths: shape (B,) wavelengths in nanometers.
            absorption_template: optional shape (B,) target signature t.

        Returns:
            alpha_map: shape (H, W) column abundance enhancement in ppm * m.
            snr_map: shape (H, W) signal-to-noise ratio map.
        """
        H, W, B = reflectance_cube.shape

        if absorption_template is None:
            t = self.compute_unit_absorption_template(wavelengths)
        else:
            t = absorption_template

        # Flatten spatial dimensions to (N, B)
        X = reflectance_cube.reshape(-1, B)

        # Mask out NaNs and extreme invalid pixels
        valid_mask = ~np.isnan(X).any(axis=1) & (np.min(X, axis=1) > 0.0)
        X_valid = X[valid_mask]

        if len(X_valid) < B:
            raise ValueError(f"Insufficient valid pixels ({len(X_valid)}) to invert {B}x{B} covariance matrix.")

        # Compute mean and covariance of background
        mu = np.mean(X_valid, axis=0)
        diff = X_valid - mu

        # Sample covariance with Tikhonov regularization on the diagonal
        Sigma = np.cov(diff, rowvar=False)
        Sigma_reg = Sigma + self.regularization * np.eye(B)

        # Invert regularized covariance matrix
        Sigma_inv = np.linalg.pinv(Sigma_reg)

        # Compute matched filter weights vector: w = Sigma^{-1} * t / (t^T * Sigma^{-1} * t)
        Sigma_inv_t = Sigma_inv @ t
        denominator = t.T @ Sigma_inv_t

        if denominator <= 0:
            weights = Sigma_inv_t
        else:
            weights = Sigma_inv_t / denominator

        # Apply to all pixels: alpha = (x - mu) @ weights
        diff_all = X - mu
        alpha = diff_all @ weights

        # Reshape to original 2D map
        alpha_map = alpha.reshape(H, W)
        
        # Calculate background variance of alpha to compute SNR map
        alpha_valid = alpha[valid_mask]
        sigma_alpha = np.std(alpha_valid) if len(alpha_valid) > 0 else 1.0
        snr_map = alpha_map / (sigma_alpha + 1e-8)

        # Set invalid pixels to NaN
        invalid_2d = ~valid_mask.reshape(H, W)
        alpha_map[invalid_2d] = np.nan
        snr_map[invalid_2d] = np.nan

        return alpha_map, snr_map
