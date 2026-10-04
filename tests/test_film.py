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

from film.film_batch import discover_frames, run_batch  # noqa: E402
from film.film_config import FilmConfig  # noqa: E402
from film.frame_analysis import analyze_array  # noqa: E402
from film.frame_normalization import brightness_compensation  # noqa: E402
from film.ring_layout import make_ring_layout  # noqa: E402


class FilmBatchTests(unittest.TestCase):
    def test_ring_layout_reference_geometry(self):
        rows = make_ring_layout(48, pitch_mm=2.5, radius_mm=0.0, orientation="tangential")
        self.assertEqual(len(rows), 48)
        expected_radius = 48 * 2.5 / (2 * math.pi)
        self.assertAlmostEqual(rows[0]["ring_radius_mm"], expected_radius, places=9)
        self.assertAlmostEqual(rows[0]["center_x_mm"], expected_radius, places=9)
        self.assertAlmostEqual(rows[0]["center_y_mm"], 0.0, places=9)
        self.assertAlmostEqual(rows[0]["rotation_deg"], 90.0, places=9)
        self.assertAlmostEqual(rows[1]["sector_angle_deg"], 7.5, places=9)

    def test_frame_analysis_detects_active_area(self):
        values = np.zeros((10, 12), dtype=np.float64)
        values[2:6, 3:8] = 1.0
        result = analyze_array(values, active_threshold=0.05)
        self.assertEqual(result["active_pixels"], 20)
        self.assertEqual(result["active_bbox_width_px"], 5)
        self.assertEqual(result["active_bbox_height_px"], 4)
        self.assertAlmostEqual(result["active_fraction"], 20 / 120)

    def test_brightness_compensation_only_attenuates(self):
        rows = [
            {"frame_angle_deg": 0.0, "target_power_fraction": 0.20},
            {"frame_angle_deg": 90.0, "target_power_fraction": 0.10},
        ]
        adjusted = brightness_compensation(rows, "constant reconstructed brightness")
        self.assertAlmostEqual(adjusted[0]["recommended_equalization_factor"], 0.5)
        self.assertAlmostEqual(adjusted[1]["recommended_equalization_factor"], 1.0)
        self.assertTrue(all(0.0 <= row["recommended_laser_or_duty_factor"] <= 1.0 for row in adjusted))

    def test_config_roundtrip(self):
        config = FilmConfig(doe_width_px=64, doe_height_px=32, gs_iterations=3)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "film_config.json"
            config.save(path)
            loaded = FilmConfig.load(path)
        self.assertEqual(loaded.doe_width_px, 64)
        self.assertEqual(loaded.doe_height_px, 32)
        self.assertEqual(loaded.gs_iterations, 3)

    def test_small_gs_batch_writes_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frames = root / "frames"
            output = root / "out"
            frames.mkdir()

            a = np.zeros((16, 16), dtype=np.uint8)
            a[5:11, 5:11] = 255
            b = np.zeros((16, 16), dtype=np.uint8)
            b[3:13, 7:9] = 255
            Image.fromarray(a).save(frames / "frame_000.png")
            Image.fromarray(b).save(frames / "frame_001.png")

            self.assertEqual(len(discover_frames(frames)), 2)
            config = FilmConfig(
                doe_width_px=16,
                doe_height_px=16,
                pixel_size_nm=1000,
                wavelength_nm=633,
                target_distance_mm=10,
                target_width_um=0,
                gs_iterations=1,
                ring_pitch_mm=2.5,
            )
            summary = run_batch(frames, output, config=config)

            self.assertEqual(summary["mode"], "GS film batch")
            self.assertEqual(summary["frame_count"], 2)
            self.assertTrue((output / "doe" / "DOE_000.png").exists())
            self.assertTrue((output / "doe" / "DOE_000.json").exists())
            self.assertTrue((output / "simulation" / "sim_001.png").exists())
            self.assertTrue((output / "statistics" / "brightness_statistics.csv").exists())
            self.assertTrue((output / "layout" / "DOE_ring_layout.csv").exists())
            payload = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["frame_count"], 2)


if __name__ == "__main__":
    unittest.main()
