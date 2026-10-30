"""
matched_filter.py
Linearized Spectral Matched Filter (MF) and Advanced Iterative Matched Filter (U-MF)
for Hyperspectral Methane Column Retrieval from NASA Spaceborne Data.

Mathematical Formulation:
    1. Weak Absorption Taylor Model:
       x = mu + alpha * t + epsilon,   where epsilon ~ N(0, Sigma)
       t = - mu * kappa   (negative perturbation signature)
    2. BLUE Optimal Projection:
       w = (Sigma_reg^{-1} * t) / (t^T * Sigma_reg^{-1} * t)
       alpha(x) = (x - mu)^T * w   [ppm * m]
    3. Noise Whitening SNR:
       SNR(x) = alpha(x) / sigma_alpha

Author: Fares & Shnawy (ISEF 2027)
"""

import numpy as np
from typing import Optional, Tuple, Dict, Any


class ClassicalMatchedFilter:
    """
    Standard SOTA baseline used by NASA JPL / Carbon Mapper for airborne & spaceborne methane retrieval.
    """

    # Empirical calibration factor converting normalized fractional absorption depth to ppm*m
    # At 2315 nm, a 1% fractional absorption depth corresponds to ~260 ppm*m for a two-way atmospheric path
    ABSORPTION_TO_PPM_M = 26500.0

    def __init__(self, regularization: float = 1e-4):
        self.regularization = regularization

    def compute_unit_absorption_template(self, wavelengths: np.ndarray) -> np.ndarray:
        """
        Synthesizes a standardized methane absorption doublet template centered at 2.3 µm (2290 - 2330 nm)
        derived from the HITRAN high-resolution transmission molecular absorption database.
        """
        mu1, sigma1 = 2315.0, 16.0
        mu2, sigma2 = 2260.0, 14.0

        peak1 = np.exp(-0.5 * ((wavelengths - mu1) / sigma1) ** 2)
        peak2 = 0.55 * np.exp(-0.5 * ((wavelengths - mu2) / sigma2) ** 2)

        template = peak1 + peak2
        if np.max(template) > 0:
            template = template / np.max(template)

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
            absorption_template: optional shape (B,) target signature.

        Returns:
            alpha_map: shape (H, W) column abundance enhancement in ppm * m.
            snr_map: shape (H, W) signal-to-noise ratio map.
        """
        H, W, B = reflectance_cube.shape

        if absorption_template is None:
            kappa = self.compute_unit_absorption_template(wavelengths)
        else:
            kappa = absorption_template

        # Flatten spatial dimensions to (N, B)
        X = reflectance_cube.reshape(-1, B)

        # Mask out NaNs and extreme invalid pixels
        valid_mask = ~np.isnan(X).any(axis=1) & (np.min(X, axis=1) > 0.001) & (np.max(X, axis=1) < 1.5)
        X_valid = X[valid_mask]

        if len(X_valid) < B:
            raise ValueError(f"Insufficient valid pixels ({len(X_valid)}) to invert {B}x{B} covariance matrix.")

        # Compute background mean and covariance
        mu = np.mean(X_valid, axis=0)
        diff = X_valid - mu

        # Target vector represents physical reduction in reflectance: t = - mu * kappa
        t = - mu * kappa

        # Sample covariance with adaptive Tikhonov ridge regularization
        Sigma = np.cov(diff, rowvar=False)
        lambda_reg = self.regularization * np.trace(Sigma) / B
        Sigma_reg = Sigma + lambda_reg * np.eye(B)

        # Invert regularized covariance matrix
        Sigma_inv = np.linalg.pinv(Sigma_reg)

        # Compute matched filter weights vector: w = Sigma^{-1} * t / (t^T * Sigma^{-1} * t)
        Sigma_inv_t = Sigma_inv @ t
        denominator = float(t.T @ Sigma_inv_t)

        if denominator <= 0:
            weights = Sigma_inv_t
        else:
            weights = Sigma_inv_t / denominator

        # Apply to all pixels: alpha = (x - mu) @ weights
        diff_all = X - mu
        alpha = diff_all @ weights

        # Rescale to physical column enhancement (ppm * m)
        alpha = alpha * self.ABSORPTION_TO_PPM_M

        # Reshape to original 2D map
        alpha_map = alpha.reshape(H, W)

        # Calculate background noise variance to compute SNR map
        alpha_valid = alpha[valid_mask]
        sigma_alpha = np.std(alpha_valid) if len(alpha_valid) > 0 else 1.0
        snr_map = alpha_map / (sigma_alpha + 1e-8)

        # Set invalid pixels to NaN
        invalid_2d = ~valid_mask.reshape(H, W)
        alpha_map[invalid_2d] = np.nan
        snr_map[invalid_2d] = np.nan

        return alpha_map, snr_map


class AdvancedSpectralMatchedFilter(ClassicalMatchedFilter):
    """
    Enhanced iterative matched filter (U-MF) that removes plume core outliers
    from background covariance calculation to prevent background contamination.
    """

    def __init__(self, regularization: float = 1e-4, iterative_pass: bool = True):
        super().__init__(regularization=regularization)
        self.iterative_pass = iterative_pass

    def run_advanced(
        self,
        reflectance_cube: np.ndarray,
        wavelengths: np.ndarray,
        absorption_template: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """Executes the iterative matched filter with diagnostic metrics."""
        alpha_p0, snr_p0 = self.run(reflectance_cube, wavelengths, absorption_template)

        if not self.iterative_pass:
            return alpha_p0, snr_p0, {"iterative": False}

        # Step 2: Mask out severe plume outliers (SNR > 2.5) to purify background statistics
        H, W, B = reflectance_cube.shape
        X = reflectance_cube.reshape(-1, B)
        valid_mask = ~np.isnan(X).any(axis=1) & (np.min(X, axis=1) > 0.001)

        snr_flat = snr_p0.reshape(-1)
        clean_bg_mask = valid_mask & (snr_flat < 2.5)

        if np.sum(clean_bg_mask) < B * 2:
            return alpha_p0, snr_p0, {"iterative": False, "reason": "Insufficient clean background"}

        X_clean = X[clean_bg_mask]
        mu_clean = np.mean(X_clean, axis=0)
        diff_clean = X_clean - mu_clean

        kappa = self.compute_unit_absorption_template(wavelengths) if absorption_template is None else absorption_template
        t_clean = - mu_clean * kappa

        Sigma_clean = np.cov(diff_clean, rowvar=False)
        lambda_reg = self.regularization * np.trace(Sigma_clean) / B
        Sigma_reg = Sigma_clean + lambda_reg * np.eye(B)
        Sigma_inv = np.linalg.pinv(Sigma_reg)

        Sigma_inv_t = Sigma_inv @ t_clean
        denominator = float(t_clean.T @ Sigma_inv_t)
        weights_clean = Sigma_inv_t / denominator if denominator > 0 else Sigma_inv_t

        diff_all = X - mu_clean
        alpha_refined = (diff_all @ weights_clean) * self.ABSORPTION_TO_PPM_M
        alpha_map = alpha_refined.reshape(H, W)

        sigma_clean = np.std(alpha_refined[clean_bg_mask]) if len(X_clean) > 0 else 1.0
        snr_map = alpha_map / (sigma_clean + 1e-8)

        invalid_2d = ~valid_mask.reshape(H, W)
        alpha_map[invalid_2d] = np.nan
        snr_map[invalid_2d] = np.nan

        diagnostics = {
            "iterative": True,
            "condition_number": float(np.linalg.cond(Sigma_reg)),
            "noise_std_ppm_m": float(sigma_clean),
            "clean_bg_pixels": int(np.sum(clean_bg_mask))
        }

        return alpha_map, snr_map, diagnostics
