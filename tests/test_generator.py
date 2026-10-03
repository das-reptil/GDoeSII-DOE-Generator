import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from gdoesii_doe import (  # noqa: E402
    TWO_PI,
    apply_phase_offset,
    direction_cosines_from_target_offset,
    fresnel_zone_plate_phase,
    gerchberg_saxton_phase,
    grating_phase,
    lens_phase,
    load_target_intensity,
    phase_to_uint16,
    save_phase_png,
    simulate_phase,
    target_image_geometry,
    vortex_phase,
    wrap_phase,
)
from gdoesii_grayscribe import (  # noqa: E402
    export_grayscribex_normalized,
    phase_span_to_height_nm,
)


class DOEGeneratorTests(unittest.TestCase):
    def test_source_files_compile(self):
        for path in (
            SRC / "GDoeSII_DOE_Generator.py",
            SRC / "gdoesii_doe.py",
            SRC / "gdoesii_grayscribe.py",
        ):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_analytic_generators(self):
        focused_vortex = wrap_phase(
            lens_phase(65, 65, 500, 633, 10)
            + vortex_phase(65, 65, 500, 1)
        )
        phases = [
            lens_phase(65, 65, 500, 633, 10),
            grating_phase(65, 65, 500, 20, 30),
            fresnel_zone_plate_phase(65, 65, 500, 633, 10),
            vortex_phase(65, 65, 500, 1),
            focused_vortex,
        ]
        for phase in phases:
            self.assertEqual(phase.shape, (65, 65))
            self.assertTrue(np.all(np.isfinite(phase)))
            self.assertGreaterEqual(float(np.min(phase)), 0.0)
            self.assertLess(float(np.max(phase)), TWO_PI + 1e-12)

    def test_focused_vortex_combines_lens_and_vortex_phase(self):
        lens = lens_phase(65, 65, 500, 633, 10)
        vortex = vortex_phase(65, 65, 500, charge=2)
        combined = wrap_phase(lens + vortex)
        self.assertEqual(combined.shape, lens.shape)
        self.assertTrue(np.allclose(combined, wrap_phase(lens + vortex)))
        self.assertFalse(np.allclose(combined, lens))
        self.assertFalse(np.allclose(combined, vortex))

    def test_zone_plate_is_binary_phase(self):
        phase = fresnel_zone_plate_phase(65, 65, 500, 633, 10)
        values = set(np.round(np.unique(phase), 12))
        self.assertTrue(values.issubset({0.0, round(math.pi, 12)}))

    def test_gerchberg_saxton(self):
        target = np.zeros((32, 32), dtype=np.float64)
        target[12:20, 12:20] = 1.0
        phase, simulation = gerchberg_saxton_phase(
            target, 1000, 633, 10, iterations=5, seed=0
        )
        self.assertEqual(phase.shape, target.shape)
        self.assertEqual(simulation.dtype, np.uint16)
        self.assertGreater(int(np.max(phase_to_uint16(phase))), 0)
        self.assertGreater(int(np.max(simulation)), 0)

    def test_gs_target_geometry_physical_width(self):
        info = target_image_geometry(
            source_width_px=200,
            source_height_px=100,
            doe_width_px=512,
            doe_height_px=512,
            pixel_size_nm=500,
            target_width_um=80,
        )
        self.assertEqual(info["sizing_mode"], "physical-width")
        self.assertEqual(info["target_width_px"], 160)
        self.assertEqual(info["target_height_px"], 80)
        self.assertAlmostEqual(info["actual_width_um"], 80.0, places=12)
        self.assertAlmostEqual(info["actual_height_um"], 40.0, places=12)
        self.assertAlmostEqual(info["field_width_um"], 256.0, places=12)
        self.assertAlmostEqual(info["field_height_um"], 256.0, places=12)

    def test_gs_target_geometry_auto_fit_preserves_aspect_ratio(self):
        info = target_image_geometry(200, 100, 512, 512, 500, 0)
        self.assertEqual(info["sizing_mode"], "fit")
        self.assertIsNone(info["requested_width_um"])
        self.assertEqual(info["target_width_px"], 512)
        self.assertEqual(info["target_height_px"], 256)
        self.assertAlmostEqual(info["actual_width_um"], 256.0, places=12)
        self.assertAlmostEqual(info["actual_height_um"], 128.0, places=12)

    def test_gs_target_image_is_centered_at_requested_physical_size(self):
        source_values = np.full((100, 200), 255, dtype=np.uint8)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "target.png"
            Image.fromarray(source_values).save(source)
            target, info = load_target_intensity(
                source,
                512,
                512,
                pixel_size_nm=500,
                target_width_um=80,
                return_info=True,
            )

        rows, cols = np.where(target > 0)
        self.assertEqual(target.shape, (512, 512))
        self.assertEqual(cols.max() - cols.min() + 1, 160)
        self.assertEqual(rows.max() - rows.min() + 1, 80)
        self.assertEqual(info["placement_x_px"], 176)
        self.assertEqual(info["placement_y_px"], 216)
        self.assertAlmostEqual(info["actual_width_um"], 80.0, places=12)
        self.assertAlmostEqual(info["actual_height_um"], 40.0, places=12)

    def test_gs_target_width_rejects_target_larger_than_field(self):
        with self.assertRaises(ValueError):
            target_image_geometry(200, 100, 512, 512, 500, 300)

        with self.assertRaises(ValueError):
            target_image_geometry(100, 200, 512, 512, 500, 200)

    def test_reference_off_axis_geometry(self):
        info = direction_cosines_from_target_offset(100, 100, 350)
        self.assertAlmostEqual(info["theta_x_deg"], 15.9453959, places=5)
        self.assertAlmostEqual(info["theta_y_deg"], 15.9453959, places=5)
        self.assertAlmostEqual(info["total_angle_deg"], 22.0017137, places=5)
        self.assertAlmostEqual(info["ray_length_mm"], 377.4917218, places=5)

        phase = np.zeros((32, 32), dtype=np.float64)
        shifted, ramp, offset = apply_phase_offset(
            phase,
            pixel_size_nm=500,
            wavelength_nm=633,
            offset_mode="distance",
            offset_x_mm=100,
            offset_y_mm=100,
            distance_mm=350,
        )
        self.assertEqual(shifted.shape, phase.shape)
        self.assertEqual(ramp.shape, phase.shape)
        self.assertAlmostEqual(offset["period_diag_um"], 1.6896, places=3)
        self.assertAlmostEqual(offset["pixels_per_period_diag"], 3.3792, places=3)
        self.assertIsNone(offset["sampling_warning"])

    def test_alias_warning_at_one_micron_pixels(self):
        phase = np.zeros((16, 16), dtype=np.float64)
        _, _, info = apply_phase_offset(
            phase,
            pixel_size_nm=1000,
            wavelength_nm=633,
            offset_mode="distance",
            offset_x_mm=100,
            offset_y_mm=100,
            distance_mm=350,
        )
        self.assertLess(info["pixels_per_period_diag"], 2.0)
        self.assertIsNotNone(info["sampling_warning"])

    def test_phase_png_roundtrip(self):
        phase = lens_phase(33, 31, 500, 633, 10)
        expected = phase_to_uint16(phase)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "phase.png"
            png_path, json_path = save_phase_png(phase, output, {"type": "Lens"})
            actual = np.asarray(Image.open(png_path), dtype=np.uint16)
            self.assertTrue(np.array_equal(actual, expected))
            metadata = json.loads(Path(json_path).read_text(encoding="utf-8"))
            self.assertEqual(metadata["generator"]["type"], "Lens")

    def test_grayscribex_export(self):
        phase = lens_phase(16, 12, 500, 633, 10)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "grayscribe.png"
            result = export_grayscribex_normalized(
                phase / TWO_PI,
                output,
                wavelength_nm=633,
                refractive_index=1.52,
                phase_min_rad=0.0,
                phase_max_rad=TWO_PI,
                pixel_size_nm=500,
                environment_refractive_index=1.0,
                source_info={"type": "test"},
                extra_metadata={"type": "Lens"},
            )
            image = np.asarray(Image.open(output), dtype=np.uint16)
            self.assertEqual(image.shape, phase.shape)
            self.assertTrue(Path(result["metadata_path"]).exists())
            self.assertAlmostEqual(result["max_height_nm"], 633 / 0.52, places=6)

    def test_relief_index_contrast(self):
        self.assertAlmostEqual(
            phase_span_to_height_nm(633, 1.52, 0.0, TWO_PI, 1.0),
            633 / 0.52,
            places=6,
        )

    def test_simulation_uint16(self):
        phase = vortex_phase(32, 32, 750, charge=2)
        simulation = simulate_phase(phase, 750, 633, 5)
        self.assertEqual(simulation.dtype, np.uint16)
        self.assertGreater(int(np.max(simulation)), 0)


if __name__ == "__main__":
    unittest.main()
