"""
test_physics_and_pipeline.py
Automated Scientific & Portability Verification Suite for SpectraPlume.

Tests:
    1. Molecular Matched Filter & HITRAN 2.3 um Doublet Absorption.
    2. Real NASA EMIT Orbit 2222205 Plume Complex 485 Retrieval & Geolocation.
    3. Zero-Gas Calcite False Alarm Suppression (100% rejection across sensitivity thresholds).
    4. AI Confidence Gating Threshold Slider Responsiveness (Neural + Physics Fusion).
    5. Hydrodynamic IME Flux Calculation & Gaussian Error Propagation.
    6. Working-Directory Independence & Self-Bootstrapping Portability.
    7. Interactive Satellite GIS Visualizer Map Generation.

Author: SpectraPlume Research Team (ISEF 2027)
Category: Earth & Environmental Sciences (EAEV - Atmospheric Science)
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.matched_filter import ClassicalMatchedFilter
from src.flux_calculator import IMEFluxCalculator
from src.gis_visualizer import SatelliteGISVisualizer
from pipeline_runner import SpectraPlumePipeline


class TestSpectraPlumePhysics(unittest.TestCase):
    """Rigorous scientific and cross-platform portability verification tests."""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = SpectraPlumePipeline()
        cls.mf = ClassicalMatchedFilter()
        cls.flux_calc = IMEFluxCalculator(pixel_size_m=60.0)
        cls.gis = SatelliteGISVisualizer()

        cls.deadsea_path = "./data/benchmark_scenes/EMIT_DeadSea_RealGranule_Plume485.nc"
        cls.permian_path = "./data/benchmark_scenes/EMIT_Permian_SuperEmitter_31N102W.nc"
        cls.sinai_path = "./data/benchmark_scenes/EMIT_Sinai_Calcite_FalseAlarm_Testbed.nc"
        cls.suez_path = "./data/benchmark_scenes/EMIT_GulfOfSuez_FlareLeak_28N33E.nc"

    def test_hitran_molecular_absorption_template(self):
        """Validates that the synthesized HITRAN absorption cross-section exhibits the 2.3 um doublet."""
        wl = np.linspace(2150.0, 2450.0, 40)
        template = self.mf.compute_unit_absorption_template(wl)

        self.assertEqual(len(template), 40)
        peak_idx = int(np.argmax(template))
        peak_wl = wl[peak_idx]
        self.assertAlmostEqual(peak_wl, 2315.0, delta=12.0)
        idx_2260 = int(np.argmin(np.abs(wl - 2260.0)))
        self.assertGreater(template[idx_2260], 0.3)

    def test_real_granule_plume485_detection(self):
        """Verifies default startup scene (NASA EMIT Orbit 2222205 Plume Complex 485) loads and quantifies cleanly."""
        results = self.pipeline.process_scene(self.deadsea_path)
        flux = results["flux_metrics"]

        self.assertGreater(flux["flux_ton_hr"], 0.15)
        self.assertGreater(results["comparison"]["ai_plume_pixels"], 20)
        self.assertTrue(31.05 < flux["source_lat"] < 31.20)
        self.assertTrue(35.12 < flux["source_lon"] < 35.28)
        self.assertGreater(float(np.max(results["neural_prob_map"])), 0.50)

    def test_calcite_false_alarm_complete_suppression(self):
        """
        Critical Science Fair Proof:
        NASA AMF triggers false alarm pixels on zero-gas calcite testbed.
        SpectraPlume must achieve 100% false alarm rejection (0 plume pixels) even at high sensitivity (0.30).
        """
        for thresh in (0.50, 0.30):
            results = self.pipeline.process_scene(self.sinai_path, mask_threshold=thresh)
            ai_pixels = results["comparison"]["ai_plume_pixels"]
            reduction_pct = results["comparison"]["false_alarm_reduction_pct"]
            flux_ton_hr = results["flux_metrics"]["flux_ton_hr"]

            self.assertEqual(ai_pixels, 0, f"Expected 0 pixels on pure calcite at thresh={thresh}, got {ai_pixels}")
            self.assertEqual(reduction_pct, 100.0)
            self.assertEqual(flux_ton_hr, 0.0)

    def test_confidence_threshold_slider_responsiveness(self):
        """Verifies that the AI Confidence Gating Threshold slider actively modulates plume segmentation."""
        r_low = self.pipeline.process_scene(self.permian_path, mask_threshold=0.30)
        r_mid = self.pipeline.process_scene(self.permian_path, mask_threshold=0.50)
        r_high = self.pipeline.process_scene(self.permian_path, mask_threshold=0.80)

        px_low = r_low["comparison"]["ai_plume_pixels"]
        px_mid = r_mid["comparison"]["ai_plume_pixels"]
        px_high = r_high["comparison"]["ai_plume_pixels"]

        self.assertGreater(px_low, px_high)
        self.assertGreaterEqual(px_low, px_mid)
        self.assertGreaterEqual(px_mid, px_high)
        self.assertGreater(px_high, 0)

    def test_super_emitter_flux_and_uncertainty(self):
        """Verifies quantitative emission rate and Gaussian error bounds on Permian super-emitter."""
        results = self.pipeline.process_scene(self.permian_path)
        flux = results["flux_metrics"]

        self.assertGreater(flux["flux_ton_hr"], 0.20)
        self.assertGreater(flux["ime_kg"], 50.0)
        self.assertGreater(flux["number_of_plume_pixels"], 15)

        self.assertIn("flux_uncertainty_ton_hr", flux)
        self.assertGreater(flux["flux_uncertainty_ton_hr"], 0.0)
        self.assertLess(flux["flux_ci95_low_ton_hr"], flux["flux_ton_hr"])
        self.assertGreater(flux["flux_ci95_high_ton_hr"], flux["flux_ton_hr"])

    def test_offshore_flare_detection(self):
        """Verifies offshore flaring gas leak retrieval in Gulf of Suez."""
        results = self.pipeline.process_scene(self.suez_path)
        flux = results["flux_metrics"]

        self.assertGreater(flux["flux_ton_hr"], 0.15)
        self.assertGreater(results["comparison"]["ai_plume_pixels"], 40)
        self.assertGreater(flux["daily_financial_loss_usd"], 500.0)

    def test_cwd_independence_portability(self):
        """Verifies pipeline resolves paths cleanly even when invoked from an external working directory."""
        orig_cwd = os.getcwd()
        try:
            os.chdir(tempfile.gettempdir())
            ext_pipeline = SpectraPlumePipeline()
            results = ext_pipeline.process_scene("EMIT_DeadSea_RealGranule_Plume485.nc")
            self.assertGreater(results["flux_metrics"]["flux_ton_hr"], 0.15)
        finally:
            os.chdir(orig_cwd)

    def test_satellite_gis_map_generation(self):
        """Verifies that the interactive Folium/Leaflet GIS map renders valid HTML."""
        results = self.pipeline.process_scene(self.permian_path)
        folium_map = self.gis.create_plume_map(results)
        html_str = folium_map._repr_html_()

        self.assertIsInstance(html_str, str)
        self.assertGreater(len(html_str), 5000)
        self.assertIn("Esri World Imagery", html_str)


if __name__ == "__main__":
    unittest.main()
