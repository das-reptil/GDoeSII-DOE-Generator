import csv
import math
from pathlib import Path


def make_ring_layout(frame_count, pitch_mm=2.5, radius_mm=0.0, orientation="tangential"):
    frame_count = int(frame_count)
    if frame_count < 1:
        raise ValueError("Frame count must be at least 1.")
    pitch_mm = float(pitch_mm)
    radius_mm = float(radius_mm)
    if pitch_mm <= 0:
        raise ValueError("Ring pitch must be greater than 0 mm.")
    if radius_mm < 0:
        raise ValueError("Ring radius must be 0 (auto) or greater than 0 mm.")
    if orientation not in ("radial", "tangential", "fixed"):
        raise ValueError("Ring orientation must be radial, tangential or fixed.")

    if radius_mm == 0.0:
        radius_mm = frame_count * pitch_mm / (2.0 * math.pi)

    rows = []
    for index in range(frame_count):
        sector_deg = index * 360.0 / frame_count
        angle = math.radians(sector_deg)
        center_x = radius_mm * math.cos(angle)
        center_y = radius_mm * math.sin(angle)

        if orientation == "radial":
            rotation_deg = sector_deg
        elif orientation == "tangential":
            rotation_deg = (sector_deg + 90.0) % 360.0
        else:
            rotation_deg = 0.0

        rows.append({
            "frame": index,
            "frame_name": f"frame_{index:03d}.png",
            "doe_name": f"DOE_{index:03d}.png",
            "center_x_mm": center_x,
            "center_y_mm": center_y,
            "sector_angle_deg": sector_deg,
            "rotation_deg": rotation_deg,
            "orientation": orientation,
            "ring_radius_mm": radius_mm,
            "ring_pitch_mm": pitch_mm,
        })
    return rows


def write_ring_layout_csv(rows, file_name):
    rows = list(rows)
    path = Path(file_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return str(path)

    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return str(path)
