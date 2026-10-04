import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from film.frame_generation import MAPPING_MODES, generate_yaw_frames  # noqa: E402


class FilmFrameGenerationTests(unittest.TestCase):
    def test_only_generic_mapping_modes_are_available(self):
        self.assertEqual(
            MAPPING_MODES,
            ("grayscale as intensity", "invert grayscale"),
        )

    def test_generate_yaw_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            output = root / "frames"

            rgb = np.full((64, 64, 3), 255, dtype=np.uint8)
            rgb[16:48, 20:44] = (0, 0, 0)
            rgb[26:38, 8:18] = (255, 0, 0)
            Image.fromarray(rgb, mode="RGB").save(source)

            metadata = generate_yaw_frames(
                source,
                output,
                frame_count=8,
                canvas_px=128,
                front_size_px=72,
                camera_distance=4.0,
                mapping="invert grayscale",
            )

            self.assertEqual(metadata["frame_count"], 8)
            self.assertEqual(metadata["mapping"], "invert grayscale")
            self.assertTrue((output / "frame_000.png").exists())
            self.assertTrue((output / "frame_007.png").exists())
            self.assertTrue((output / "frames.json").exists())

            frame0 = np.asarray(Image.open(output / "frame_000.png"), dtype=np.uint8)
            self.assertEqual(frame0.shape, (128, 128))
            self.assertGreater(int(frame0.max()), 0)
            self.assertEqual(int(frame0[0, 0]), 0)

            payload = json.loads((output / "frames.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["frames"][0]["nominal_angle_deg"], 0.0)
            self.assertEqual(payload["frames"][2]["nominal_angle_deg"], 90.0)
            self.assertNotEqual(payload["frames"][2]["render_angle_deg"], 90.0)


if __name__ == "__main__":
    unittest.main()
