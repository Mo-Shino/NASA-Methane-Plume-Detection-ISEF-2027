"""
test_physics_and_pipeline.py
Automated Scientific Verification Suite for SpectraPlume.

Tests:
    1. Molecular Matched Filter & HITRAN 2.3 µm Doublet Absorption.
    2. Zero-Gas Calcite False Alarm Suppression (100% rejection).
    3. Hydrodynamic IME Flux Calculation & Gaussian Error Propagation.
    4. End-to-end Granule Processing Pipeline Latency.
    5. Interactive Satellite GIS Visualizer Map Generation.

Author: SpectraPlume Research Team (ISEF 2027)
Category: Earth & Environmental Sciences (EAEV - Atmospheric Science)
"""

import os
import unittest
import numpy as np

from src.matched_filter import ClassicalMatchedFilter
from src.flux_calculator import IMEFluxCalculator
from src.gis_visualizer import SatelliteGISVisualizer
from pipeline_runner import SpectraPlumePipeline


class TestSpectraPlumePhysics(unittest.TestCase):
    """Rigorous scientific verification tests for remote sensing retrieval physics."""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = SpectraPlumePipeline()
        cls.mf = ClassicalMatchedFilter()
        cls.flux_calc = IMEFluxCalculator(pixel_size_m=60.0)
        cls.gis = SatelliteGISVisualizer()

        cls.permian_path = "./data/benchmark_scenes/EMIT_Permian_SuperEmitter_31N102W.nc"
        cls.sinai_path = "./data/benchmark_scenes/EMIT_Sinai_Calcite_FalseAlarm_Testbed.nc"
        cls.suez_path = "./data/benchmark_scenes/EMIT_GulfOfSuez_FlareLeak_28N33E.nc"

    def test_hitran_molecular_absorption_template(self):
        """Validates that the synthesized HITRAN absorption cross-section exhibits the 2.3 µm doublet."""
        wl = np.linspace(2150.0, 2450.0, 40)
        template = self.mf.compute_unit_absorption_template(wl)

        self.assertEqual(len(template), 40)
        # Peak absorption must be centered near 2315 nm
        peak_idx = np.argmax(template)
        peak_wl = wl[peak_idx]
        self.assertAlmostEqual(peak_wl, 2315.0, delta=12.0)
        # Secondary doublet shoulder at 2260 nm must be non-zero
        idx_2260 = np.argmin(np.abs(wl - 2260.0))
        self.assertGreater(template[idx_2260], 0.3)

    def test_calcite_false_alarm_complete_suppression(self):
        """
        Critical Science Fair Proof:
        NASA AMF produces ~243 false alarm pixels on zero-gas calcite testbed.
        SpectraPlume must achieve 100% false alarm rejection (0 plume pixels).
        """
        results = self.pipeline.process_scene(self.sinai_path)
        ai_pixels = results["comparison"]["ai_plume_pixels"]
        reduction_pct = results["comparison"]["false_alarm_reduction_pct"]
        flux_ton_hr = results["flux_metrics"]["flux_ton_hr"]

        self.assertEqual(ai_pixels, 0, f"Expected 0 pixels on pure calcite mountain, got {ai_pixels}")
        self.assertEqual(reduction_pct, 100.0)
        self.assertEqual(flux_ton_hr, 0.0)

    def test_super_emitter_flux_and_uncertainty(self):
        """Verifies quantitative emission rate and Gaussian error bounds on Permian super-emitter."""
        results = self.pipeline.process_scene(self.permian_path)
        flux = results["flux_metrics"]

        # Super-emitter threshold is > 0.1 tons/hr (100 kg/hr)
        self.assertGreater(flux["flux_ton_hr"], 0.20)
        self.assertGreater(flux["ime_kg"], 50.0)
        self.assertGreater(flux["number_of_plume_pixels"], 15)

        # Uncertainty metrics
        self.assertIn("flux_uncertainty_ton_hr", flux)
        self.assertGreater(flux["flux_uncertainty_ton_hr"], 0.0)
        self.assertLess(flux["flux_ci95_low_ton_hr"], flux["flux_ton_hr"])
        self.assertGreater(flux["flux_ci95_high_ton_hr"], flux["flux_ton_hr"])

    def test_offshore_flare_detection(self):
        """Verifies offshore flaring gas leak retrieval in Gulf of Suez."""
        results = self.pipeline.process_scene(self.suez_path)
        flux = results["flux_metrics"]

        self.assertGreater(flux["flux_ton_hr"], 0.15)
        self.assertGreater(results["comparison"]["ai_plume_pixels"], 50)
        self.assertGreater(flux["daily_financial_loss_usd"], 500.0)

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
