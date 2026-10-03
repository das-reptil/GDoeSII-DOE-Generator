import math
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from gdoesii_tilt import (  # noqa: E402
    gerchberg_saxton_tilted_phase,
    target_plane_geometry,
    tilted_plane_sampling_info,
)


class TiltedTargetTests(unittest.TestCase):
    def test_parallel_plane_geometry(self):
        info = target_plane_geometry(
            300,
            pan_deg=0,
            tilt_deg=0,
            width_mm=50,
            height_mm=40,
            pixel_size_nm=500,
            wavelength_nm=532,
        )
        self.assertEqual(info["center_mm"], [0.0, 0.0, 300.0])
        self.assertTrue(np.allclose(info["u_axis"], [1.0, 0.0, 0.0]))
        self.assertTrue(np.allclose(info["v_axis"], [0.0, 1.0, 0.0]))
        self.assertTrue(np.allclose(info["normal"], [0.0, 0.0, 1.0]))
        self.assertTrue(np.allclose(info["corners_mm"]["top_left"], [-25.0, -20.0, 300.0]))
        self.assertIsNone(info["sampling"]["sampling_warning"])

    def test_pan_and_tilt_normal(self):
        info = target_plane_geometry(300, pan_deg=30, tilt_deg=0)
        self.assertAlmostEqual(info["normal"][0], 0.5, places=12)
        self.assertAlmostEqual(info["normal"][1], 0.0, places=12)
        self.assertAlmostEqual(info["normal"][2], math.sqrt(3.0) / 2.0, places=12)

        tilted = target_plane_geometry(300, pan_deg=0, tilt_deg=20)
        self.assertAlmostEqual(tilted["normal"][0], 0.0, places=12)
        self.assertAlmostEqual(tilted["normal"][1], -math.sin(math.radians(20)), places=12)
        self.assertAlmostEqual(tilted["normal"][2], math.cos(math.radians(20)), places=12)

    def test_tilt_sampling_warns_before_aliasing(self):
        safe = tilted_plane_sampling_info(500, 532, pan_deg=20, tilt_deg=0)
        self.assertIsNone(safe["sampling_warning"])
        self.assertGreater(safe["pixels_per_carrier_u"], 2.0)

        aliased = tilted_plane_sampling_info(500, 532, pan_deg=35, tilt_deg=0)
        self.assertIsNotNone(aliased["sampling_warning"])
        self.assertIn("Aliasing", aliased["sampling_warning"])

    def test_tilted_gs_returns_phase_and_simulation(self):
        target = np.zeros((32, 32), dtype=np.float64)
        target[12:20, 12:20] = 1.0
        phase, simulation = gerchberg_saxton_tilted_phase(
            target,
            pixel_size_nm=500,
            wavelength_nm=633,
            distance_mm=10,
            pan_deg=5,
            tilt_deg=3,
            iterations=2,
            seed=0,
        )
        self.assertEqual(phase.shape, target.shape)
        self.assertTrue(np.all(np.isfinite(phase)))
        self.assertEqual(simulation.dtype, np.uint16)
        self.assertGreater(int(np.max(simulation)), 0)


if __name__ == "__main__":
    unittest.main()
