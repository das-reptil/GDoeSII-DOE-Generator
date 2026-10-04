import csv
from pathlib import Path

import numpy as np
from PIL import Image


IMAGE_EXTENSIONS = {".png", ".tif", ".tiff", ".jpg", ".jpeg", ".bmp"}


def load_grayscale(file_name):
    with Image.open(file_name) as image:
        values = np.asarray(image.convert("L"), dtype=np.float64) / 255.0
    return np.clip(values, 0.0, 1.0)


def analyze_array(values, active_threshold=0.05):
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 2:
        raise ValueError("Frame data must be a 2-D grayscale array.")

    maximum = float(np.max(values)) if values.size else 0.0
    if maximum > 0:
        normalized = np.clip(values / maximum, 0.0, 1.0)
    else:
        normalized = np.zeros(values.shape, dtype=np.float64)

    threshold = float(active_threshold)
    mask = normalized > threshold
    active_pixels = int(np.count_nonzero(mask))
    total_pixels = int(normalized.size)

    if active_pixels:
        rows, cols = np.where(mask)
        bbox_width = int(cols.max() - cols.min() + 1)
        bbox_height = int(rows.max() - rows.min() + 1)
        active_mean = float(np.mean(normalized[mask]))
        active_sum = float(np.sum(normalized[mask]))
    else:
        bbox_width = 0
        bbox_height = 0
        active_mean = 0.0
        active_sum = 0.0

    return {
        "width_px": int(normalized.shape[1]),
        "height_px": int(normalized.shape[0]),
        "max_intensity": maximum,
        "sum_intensity": float(np.sum(normalized)),
        "mean_intensity": float(np.mean(normalized)) if total_pixels else 0.0,
        "active_threshold": threshold,
        "active_pixels": active_pixels,
        "active_fraction": float(active_pixels / total_pixels) if total_pixels else 0.0,
        "active_mean_intensity": active_mean,
        "active_sum_intensity": active_sum,
        "active_bbox_width_px": bbox_width,
        "active_bbox_height_px": bbox_height,
    }


def analyze_frame(file_name, active_threshold=0.05):
    result = analyze_array(load_grayscale(file_name), active_threshold)
    result["file_name"] = Path(file_name).name
    result["file_path"] = str(Path(file_name))
    return result


def write_csv(rows, file_name):
    rows = list(rows)
    path = Path(file_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return str(path)

    fieldnames = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return str(path)
