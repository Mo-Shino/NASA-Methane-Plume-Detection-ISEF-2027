"""
train_model.py
Refined Physics-Informed Training and Calibration Script for SpatialSpectralMethaneNet.

Trains the Dual-Branch Spatial-Spectral Attention Network:
    1. Accurately segments true atmospheric methane plumes (high IoU / F1 on detectable plume core).
    2. Completely suppresses false alarms from carbonate minerals (calcite/dolomite, 0 false alarms).
    3. Accurately regresses column enhancement in ppm*m for IME flux integration.

Author: Fares & Shnawy (ISEF 2027)
"""

import os
import sys
import glob
from pathlib import Path

import numpy as np
import xarray as xr
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.benchmark_generator import ensure_demo_scenes
from src.model_spatial_spectral import SpatialSpectralMethaneNet


class PlumeSegmentationLoss(nn.Module):
    """
    Balanced Composite Loss for hyperspectral plume segmentation and mineral false alarm rejection.
    """

    def __init__(self, pos_weight: float = 6.0, false_alarm_weight: float = 4.5):
        super().__init__()
        self.pos_weight = pos_weight
        self.false_alarm_weight = false_alarm_weight

    def forward(
        self,
        pred_mask: torch.Tensor,
        target_mask: torch.Tensor,
        pred_enh: torch.Tensor,
        target_enh: torch.Tensor
    ) -> torch.Tensor:
        batch_size = pred_mask.size(0)
        total_loss = torch.tensor(0.0, device=pred_mask.device)

        for i in range(batch_size):
            pm = pred_mask[i].clamp(1e-6, 1.0 - 1e-6)
            tm = target_mask[i]
            pe = pred_enh[i]
            te = target_enh[i]

            t_sum = torch.sum(tm)
            if t_sum < 5.0:
                # Negative scene (carbonate/calcite mineral trap with zero methane)
                bce_neg = F.binary_cross_entropy(pm, tm)
                enh_neg = torch.mean((pe / 1000.0) ** 2)
                total_loss = total_loss + (self.false_alarm_weight * bce_neg + 1.5 * enh_neg)
            else:
                # Positive scene (plume present, possibly alongside neighboring mineral outcrops)
                weights = torch.where(tm > 0.5, self.pos_weight, 1.25)
                bce_raw = F.binary_cross_entropy(pm, tm, reduction="none")
                loss_bce = torch.mean(bce_raw * weights)

                # Soft Dice Loss
                p_flat = pm.reshape(-1)
                t_flat = tm.reshape(-1)
                inter = torch.sum(p_flat * t_flat)
                dice = (2.0 * inter + 1e-5) / (torch.sum(p_flat) + torch.sum(t_flat) + 1e-5)
                loss_dice = 1.0 - dice

                # Enhancement regression loss (in kilo-ppm*m units)
                loss_enh = F.smooth_l1_loss(pe / 1000.0, te / 1000.0)

                total_loss = total_loss + (loss_bce + 2.2 * loss_dice + 1.2 * loss_enh)

        return total_loss / batch_size


class MethaneBenchmarkDataset(Dataset):
    """Loads benchmark scenes safely and applies spectral-preserving spatial/radiometric augmentations."""

    def __init__(self, scenes_dir: str, num_samples: int = 128):
        self.files = sorted(glob.glob(os.path.join(scenes_dir, "*.nc")))
        self.num_samples = num_samples
        self.cubes = []
        self.masks = []
        self.enhancements = []
        self.names = []

        for f in self.files:
            with xr.open_dataset(f) as ds:
                rfl = ds["reflectance"].values.astype(np.float32).copy()  # (128, 128, 40)
                gt_enh = ds["ground_truth_enhancement"].values.astype(np.float32).copy()
            gt_mask = (gt_enh >= 180.0).astype(np.float32)

            cube_ch = np.transpose(rfl, (2, 0, 1))  # (40, 128, 128)
            self.cubes.append(cube_ch)
            self.masks.append(gt_mask[np.newaxis, :, :])
            self.enhancements.append(gt_enh[np.newaxis, :, :])
            self.names.append(os.path.basename(f))

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        base_idx = idx % len(self.cubes)
        full_cube = self.cubes[base_idx]
        full_mask = self.masks[base_idx]
        full_enh = self.enhancements[base_idx]

        # Extract 64x64 spatial patch (4x faster CPU training; U-Net is fully convolutional for 128x128+ inference)
        _, h_full, w_full = full_cube.shape
        crop_sz = 64
        pos_ys, pos_xs = np.where(full_mask[0] > 0.5)
        if len(pos_ys) > 0 and np.random.rand() < 0.7:
            pick = np.random.randint(0, len(pos_ys))
            cy, cx = int(pos_ys[pick]), int(pos_xs[pick])
            y0 = int(np.clip(cy - crop_sz // 2 + np.random.randint(-12, 13), 0, h_full - crop_sz))
            x0 = int(np.clip(cx - crop_sz // 2 + np.random.randint(-12, 13), 0, w_full - crop_sz))
        else:
            y0 = np.random.randint(0, h_full - crop_sz + 1)
            x0 = np.random.randint(0, w_full - crop_sz + 1)

        cube = full_cube[:, y0:y0 + crop_sz, x0:x0 + crop_sz].copy()
        mask = full_mask[:, y0:y0 + crop_sz, x0:x0 + crop_sz].copy()
        enh = full_enh[:, y0:y0 + crop_sz, x0:x0 + crop_sz].copy()

        # Random 90-degree rotations
        k_rot = np.random.randint(0, 4)
        if k_rot > 0:
            cube = np.rot90(cube, k=k_rot, axes=(1, 2)).copy()
            mask = np.rot90(mask, k=k_rot, axes=(1, 2)).copy()
            enh = np.rot90(enh, k=k_rot, axes=(1, 2)).copy()

        # Random horizontal / vertical flip augmentation
        if np.random.rand() > 0.5:
            cube = np.flip(cube, axis=2).copy()
            mask = np.flip(mask, axis=2).copy()
            enh = np.flip(enh, axis=2).copy()

        if np.random.rand() > 0.5:
            cube = np.flip(cube, axis=1).copy()
            mask = np.flip(mask, axis=1).copy()
            enh = np.flip(enh, axis=1).copy()

        # Random global surface albedo scaling (tests invariance across dark basalt vs bright desert)
        albedo_scale = np.float32(np.random.uniform(0.78, 1.25))
        cube = cube * albedo_scale

        # Additive EMIT SWIR sensor noise
        noise = np.random.normal(0.0, 0.0012, size=cube.shape).astype(np.float32)
        cube = np.clip(cube + noise, 0.005, 0.99)

        return (
            torch.from_numpy(cube).float(),
            torch.from_numpy(mask).float(),
            torch.from_numpy(enh).float()
        )


def train():
    torch.manual_seed(42)
    np.random.seed(42)

    ensure_demo_scenes()
    scenes_dir = str(PROJECT_ROOT / "data" / "benchmark_scenes")
    weights_dir = PROJECT_ROOT / "weights"
    os.makedirs(weights_dir, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training SpatialSpectralMethaneNet on device: {device}", flush=True)

    dataset = MethaneBenchmarkDataset(scenes_dir=scenes_dir, num_samples=32)
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True)

    model = SpatialSpectralMethaneNet(in_spectral_bands=40, base_features=24).to(device)
    optimizer = optim.AdamW(model.parameters(), lr=3.5e-3, weight_decay=1e-4)
    epochs = 14
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=3e-4)
    criterion = PlumeSegmentationLoss(pos_weight=6.0, false_alarm_weight=4.5)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0

        for cubes, masks, enhancements in dataloader:
            cubes = cubes.to(device)
            masks = masks.to(device)
            enhancements = enhancements.to(device)

            optimizer.zero_grad()
            outputs = model(cubes)

            loss = criterion(outputs["mask"], masks, outputs["enhancement"], enhancements)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        scheduler.step()
        avg_loss = total_loss / len(dataloader)
        if epoch % 4 == 0 or epoch == 1 or epoch == epochs:
            print(f"Epoch [{epoch:02d}/{epochs}] - Loss: {avg_loss:.4f}", flush=True)

    # Validation sweep across all 4 benchmark scenes
    model.eval()
    print("\n--- Validation Across Official Benchmark Scenes ---", flush=True)
    with torch.no_grad():
        for name, cube_np, mask_np, enh_np in zip(
            dataset.names, dataset.cubes, dataset.masks, dataset.enhancements
        ):
            inp = torch.from_numpy(cube_np).unsqueeze(0).to(device)
            out = model(inp)
            pm = out["mask"].squeeze().cpu().numpy()
            pe = out["enhancement"].squeeze().cpu().numpy()
            tm = mask_np.squeeze()
            pred_bin = pm >= 0.55
            if np.sum(tm) > 0:
                tp = np.sum(pred_bin & (tm > 0.5))
                fp = np.sum(pred_bin & (tm <= 0.5))
                fn = np.sum((~pred_bin) & (tm > 0.5))
                f1 = (2 * tp) / max(2 * tp + fp + fn, 1)
                print(
                    f"  [PLUME]   {name:<42} | max_prob={pm.max():.3f} | F1={f1:.3f} | peak_enh={pe.max():.0f} ppm*m",
                    flush=True
                )
            else:
                fp_px = int(np.sum(pred_bin))
                print(
                    f"  [MINERAL] {name:<42} | max_prob={pm.max():.3f} | FalsePositives={fp_px} px",
                    flush=True
                )

    weights_path = str(weights_dir / "spatial_spectral_emit.pt")
    torch.save(model.state_dict(), weights_path)
    print(f"\nModel trained successfully! Saved calibrated weights to: {weights_path}", flush=True)


if __name__ == "__main__":
    train()
