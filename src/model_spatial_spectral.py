"""
model_spatial_spectral.py
Dual-Branch Physics-Informed Spatial-Spectral Attention Network for Methane Plume Segmentation.

Architecture Innovation:
    0. Continuum Optical-Depth Normalization Layer:
       Cancels broadband surface albedo variations (bright desert quartz, urban roofs, dark basalt)
       via per-pixel spectral continuum division and scene-level differential optical depth extraction.
    1. Spectral Feature Branch (1x1 Spectral Projection & Squeeze-and-Excitation Attention):
       Learns non-linear absorption manifolds and discriminates methane absorption doublet (2260 / 2315 nm)
       from confounding carbonate mineral absorption singlet (calcite/dolomite at 2330 nm).
    2. Spatial Context Branch (Multi-Scale 2D Convolutional U-Net with Dilated Bottleneck):
       Learns atmospheric dispersion morphology (advection-diffusion Gaussian plumes, wind-driven cones).
    3. Dual Task Heads:
       Outputs calibrated pixel-level plume probability [0, 1] and column enhancement (ppm*m).

Author: Fares & Shnawy (ISEF 2027)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class SpectralAttentionModule(nn.Module):
    """Channel-wise spectral attention focusing on characteristic gas absorption dips."""

    def __init__(self, in_channels: int, reduction: int = 4):
        super().__init__()
        hidden = max(in_channels // reduction, 4)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(in_channels, hidden, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(hidden, in_channels, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        return x * y.expand_as(x)


class DoubleConv(nn.Module):
    """Standard double convolution block with BatchNorm and GELU."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.GELU(),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.GELU()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(x)


class SpatialSpectralMethaneNet(nn.Module):
    """
    End-to-end Deep Neural Network for automated hyperspectral methane plume segmentation.
    Input: Hyperspectral sub-cube of shape (Batch, Bands, Height, Width)
    Output: Binary plume probability mask (Batch, 1, Height, Width) & Column Enhancement Map (Batch, 1, Height, Width)
    """

    def __init__(self, in_spectral_bands: int = 40, base_features: int = 32):
        super().__init__()
        self.in_spectral_bands = in_spectral_bands

        # Spectral feature reduction & attention
        self.spectral_proj = nn.Sequential(
            nn.Conv2d(in_spectral_bands, base_features * 2, kernel_size=1),
            nn.BatchNorm2d(base_features * 2),
            nn.GELU(),
            SpectralAttentionModule(base_features * 2)
        )

        # U-Net Encoder
        self.enc1 = DoubleConv(base_features * 2, base_features)
        self.pool1 = nn.MaxPool2d(2)

        self.enc2 = DoubleConv(base_features, base_features * 2)
        self.pool2 = nn.MaxPool2d(2)

        self.enc3 = DoubleConv(base_features * 2, base_features * 4)
        self.pool3 = nn.MaxPool2d(2)

        # Bottleneck with dilated conv for wide receptive field (plume extent)
        self.bottleneck = nn.Sequential(
            nn.Conv2d(base_features * 4, base_features * 8, kernel_size=3, padding=2, dilation=2),
            nn.BatchNorm2d(base_features * 8),
            nn.GELU(),
            nn.Conv2d(base_features * 8, base_features * 4, kernel_size=3, padding=1),
            nn.BatchNorm2d(base_features * 4),
            nn.GELU()
        )

        # U-Net Decoder
        self.up3 = nn.ConvTranspose2d(base_features * 4, base_features * 4, kernel_size=2, stride=2)
        self.dec3 = DoubleConv(base_features * 8, base_features * 4)

        self.up2 = nn.ConvTranspose2d(base_features * 4, base_features * 2, kernel_size=2, stride=2)
        self.dec2 = DoubleConv(base_features * 4, base_features * 2)

        self.up1 = nn.ConvTranspose2d(base_features * 2, base_features, kernel_size=2, stride=2)
        self.dec1 = DoubleConv(base_features * 2, base_features)

        # Dual Heads:
        # 1. Segmentation Head (Plume probability: 0 to 1)
        self.head_mask = nn.Sequential(
            nn.Conv2d(base_features, 1, kernel_size=1),
            nn.Sigmoid()
        )

        # 2. Regression Head (Continuous column abundance enhancement in kilo-ppm*m -> scaled to ppm*m)
        self.head_enhancement = nn.Sequential(
            nn.Conv2d(base_features, 1, kernel_size=1),
            nn.ReLU()
        )

    def _preprocess_continuum_optical_depth(self, x: torch.Tensor) -> torch.Tensor:
        """
        Physics-informed spectral preprocessing:
        1. Sanitizes NaNs and resamples arbitrary SWIR band counts to `self.in_spectral_bands`.
        2. Divides each pixel by its broadband SWIR continuum mean to cancel surface albedo.
        3. Subtracts scene-wide background spectral shape to isolate molecular absorption depth.
        """
        x = torch.nan_to_num(x, nan=0.30, posinf=1.0, neginf=0.01)

        if x.size(1) != self.in_spectral_bands:
            b_sz, c_in, h_sz, w_sz = x.shape
            x_perm = x.permute(0, 2, 3, 1).reshape(-1, 1, c_in)
            x_res = F.interpolate(x_perm, size=self.in_spectral_bands, mode="linear", align_corners=True)
            x = x_res.reshape(b_sz, h_sz, w_sz, self.in_spectral_bands).permute(0, 3, 1, 2)

        pixel_continuum = torch.mean(x, dim=1, keepdim=True).clamp(min=1e-4)
        r_norm = x / pixel_continuum
        scene_bg = torch.mean(r_norm, dim=(2, 3), keepdim=True)
        optical_deficit = (scene_bg - r_norm) * 35.0
        return optical_deficit

    def forward(self, x: torch.Tensor):
        # x: (B, Bands, H, W)
        orig_h, orig_w = x.size(2), x.size(3)
        x_norm = self._preprocess_continuum_optical_depth(x)

        # Pad spatial dimensions cleanly to multiple of 8 for 3-level U-Net pooling
        pad_h = (8 - orig_h % 8) % 8
        pad_w = (8 - orig_w % 8) % 8
        if pad_h > 0 or pad_w > 0:
            x_norm = F.pad(x_norm, (0, pad_w, 0, pad_h), mode="reflect")

        x_proj = self.spectral_proj(x_norm)

        # Encoder
        e1 = self.enc1(x_proj)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(self.pool2(e2))

        # Bottleneck
        b = self.bottleneck(self.pool3(e3))

        # Decoder with skip connections
        d3 = self.dec3(torch.cat([self.up3(b), e3], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))

        if pad_h > 0 or pad_w > 0:
            d1 = d1[:, :, :orig_h, :orig_w]

        mask = self.head_mask(d1)
        enhancement = self.head_enhancement(d1) * 1000.0

        return {
            "mask": mask,
            "enhancement": enhancement
        }
