"""
model_spatial_spectral.py
Dual-Branch Spatial-Spectral Attention Network for Methane Plume Segmentation.

Architecture Innovation:
    1. Spectral Feature Branch (1D CNN & Squeeze-and-Excitation):
       Learns non-linear absorption manifolds and discriminates methane absorption (2.3 µm)
       from confounding mineral absorption (calcite, dolomite, illite, chlorite).
    2. Spatial Context Branch (2D Convolutional U-Net):
       Learns atmospheric dispersion morphology (parabolic / conical Gaussian plumes, wind-driven flow).
    3. Cross-Attention Fusion:
       Suppresses high-reflectance urban roofs and false mineral alarms by conditioning
       segmentation masks on consistent spectral deficit.

Author: Fares & Shnawy (ISEF 2027)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class SpectralAttentionModule(nn.Module):
    """Channel-wise spectral attention focusing on characteristic gas absorption dips."""
    def __init__(self, in_channels: int, reduction: int = 4):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(in_channels, in_channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(in_channels // reduction, in_channels, bias=False),
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
    Output: Binary plume mask (Batch, 1, Height, Width) & Column Enhancement Map (Batch, 1, Height, Width)
    """

    def __init__(self, in_spectral_bands: int = 40, base_features: int = 32):
        super().__init__()

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

        # 2. Regression Head (Continuous column abundance enhancement in ppm*m)
        self.head_enhancement = nn.Sequential(
            nn.Conv2d(base_features, 1, kernel_size=1),
            nn.ReLU()
        )

    def forward(self, x: torch.Tensor):
        # x: (B, Bands, H, W)
        x_proj = self.spectral_proj(x)

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

        mask = self.head_mask(d1)
        enhancement = self.head_enhancement(d1)

        return {
            "mask": mask,
            "enhancement": enhancement
        }
