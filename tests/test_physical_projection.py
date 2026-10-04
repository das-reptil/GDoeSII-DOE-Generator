import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from film.physical_projection import (  # noqa: E402
    gerchberg_saxton_physical_phase,
    load_physical_target_intensity,
    physical_projection_sampling,
    scaled_fresnel_propagate,
)


class PhysicalProjectionTests(unittest.TestCase):
    def test_reference_film_sampling(self):
        info = physical_projection_sampling(
            4096,
            4096,
            pixel_size_nm=500,
            wavelength_nm=532,
            distance_mm=300,
        )
        self.assertAlmostEqual(info["source_width_mm"], 2.048, places=9)
        self.assertAlmostEqual(info["target_pixel_size_x_um"], 77.9296875, places=9)
        self.assertAlmostEqual(info["target_pixel_size_y_um"], 77.9296875, places=9)
        self.assertAlmostEqual(info["target_field_width_mm"], 319.2, places=9)
        self.assertAlmostEqual(info["target_field_height_mm"], 319.2, places=9)
        self.assertIsNone(info["sampling_warning"])

    def test_scaled_fresnel_forward_inverse_roundtrip(self):
        rng = np.random.default_rng(4)
        field = rng.normal(size=(24, 32)) + 1j * rng.normal(size=(24, 32))
        propagated = scaled_fresnel_propagate(field, 1000, 633, 10)
        recovered = scaled_fresnel_propagate(
            propagated, 1000, 633, 10, inverse=True
        )
        self.assertTrue(np.allclose(recovered, field, rtol=1e-12, atol=1e-12))

    def test_physical_target_reference_width(self):
        values = np.full((100, 100), 255, dtype=np.uint8)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "frame.png"
            Image.fromarray(values).save(source)
            target, info = load_physical_target_intensity(
                source,
                64,
                64,
                pixel_size_nm=1000,
                wavelength_nm=633,
                distance_mm=10,
                target_width_mm=2.0,
                reference_width_px=50,
                return_info=True,
            )
        self.assertEqual(target.shape, (64, 64))
        self.assertAlmostEqual(info["requested_reference_width_mm"], 2.0)
        self.assertAlmostEqual(info["actual_reference_width_mm"], 2.0, delta=0.06)
        self.assertAlmostEqual(info["actual_width_mm"], 4.0, delta=0.12)
        self.assertGreater(info["target_width_px"], 1)

    def test_physical_gs_small_target(self):
        target = np.zeros((32, 32), dtype=np.float64)
        target[12:20, 10:22] = 1.0
        phase, simulation = gerchberg_saxton_physical_phase(
            target,
            pixel_size_nm=1000,
            wavelength_nm=633,
            distance_mm=10,
            iterations=2,
            seed=0,
        )
        self.assertEqual(phase.shape, target.shape)
        self.assertEqual(simulation.shape, target.shape)
        self.assertEqual(simulation.dtype, np.uint16)
        self.assertGreater(int(np.max(simulation)), 0)


if __name__ == "__main__":
    unittest.main()
