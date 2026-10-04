import json
import math
from pathlib import Path

import numpy as np
from PIL import Image


MAPPING_MODES = (
    "grayscale as intensity",
    "invert grayscale",
)


def _target_intensity_image(source, mapping):
    rgb = np.asarray(source.convert("RGB"), dtype=np.float64) / 255.0
    gray = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    if mapping == "grayscale as intensity":
        values = gray
    elif mapping == "invert grayscale":
        values = 1.0 - gray
    else:
        raise ValueError(f"Unknown frame intensity mapping: {mapping}")
    return Image.fromarray(np.rint(np.clip(values, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L")


def _homography(source_points, destination_points):
    """Return a 3x3 homography mapping source to destination coordinates."""
    matrix = []
    vector = []
    for (x, y), (u, v) in zip(source_points, destination_points):
        matrix.append([x, y, 1.0, 0.0, 0.0, 0.0, -u * x, -u * y])
        vector.append(u)
        matrix.append([0.0, 0.0, 0.0, x, y, 1.0, -v * x, -v * y])
        vector.append(v)
    solution = np.linalg.solve(np.asarray(matrix, dtype=np.float64), np.asarray(vector, dtype=np.float64))
    return np.array(
        [
            [solution[0], solution[1], solution[2]],
            [solution[3], solution[4], solution[5]],
            [solution[6], solution[7], 1.0],
        ],
        dtype=np.float64,
    )


def _render_yaw(image, nominal_angle_deg, canvas_px, front_size_px, camera_distance):
    canvas_px = int(canvas_px)
    front_size_px = float(front_size_px)
    camera_distance = float(camera_distance)
    if canvas_px < 32:
        raise ValueError("Frame canvas must be at least 32 pixels.")
    if front_size_px <= 0:
        raise ValueError("Front-facing image size must be greater than 0 pixels.")
    if camera_distance <= 1.0:
        raise ValueError("Perspective camera distance must be greater than 1.0.")

    aspect = image.height / image.width
    safe_front = canvas_px * 0.90 * (camera_distance - 1.0) / camera_distance / max(1.0, aspect)
    actual_front = min(front_size_px, safe_front)
    center = canvas_px / 2.0
    focal_px = (actual_front / 2.0) * camera_distance

    nominal = float(nominal_angle_deg) % 360.0
    # Exactly edge-on gives a singular projective transform. Render an
    # imperceptibly offset narrow line while retaining the nominal angle in
    # metadata.
    render_angle = nominal
    if abs((nominal % 180.0) - 90.0) < 1e-12:
        render_angle = nominal - 0.15

    theta = math.radians(render_angle)
    c = math.cos(theta)
    s = math.sin(theta)
    local_corners = (
        (-1.0, -aspect),
        (1.0, -aspect),
        (1.0, aspect),
        (-1.0, aspect),
    )
    destination = []
    for x, y in local_corners:
        global_x = c * x
        global_z = -s * x
        z_camera = camera_distance + global_z
        u = center + focal_px * global_x / z_camera
        v = center + focal_px * y / z_camera
        destination.append((u, v))

    source_points = (
        (0.0, 0.0),
        (float(image.width - 1), 0.0),
        (float(image.width - 1), float(image.height - 1)),
        (0.0, float(image.height - 1)),
    )
    forward = _homography(source_points, destination)
    inverse = np.linalg.inv(forward)
    inverse /= inverse[2, 2]
    coeffs = (
        inverse[0, 0], inverse[0, 1], inverse[0, 2],
        inverse[1, 0], inverse[1, 1], inverse[1, 2],
        inverse[2, 0], inverse[2, 1],
    )

    rendered = image.transform(
        (canvas_px, canvas_px),
        Image.Transform.PERSPECTIVE,
        coeffs,
        resample=Image.Resampling.BICUBIC,
        fillcolor=0,
    )
    return rendered, render_angle, actual_front, destination


def generate_yaw_frames(
    source_file,
    output_directory,
    frame_count=48,
    canvas_px=1024,
    front_size_px=600,
    camera_distance=4.0,
    mapping="invert grayscale",
):
    """Generate evenly spaced 360-degree target frames around a vertical axis."""
    frame_count = int(frame_count)
    if frame_count < 2:
        raise ValueError("Frame count must be at least 2.")
    if mapping not in MAPPING_MODES:
        raise ValueError("Unknown target-intensity mapping.")

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    with Image.open(source_file) as source:
        target_source = _target_intensity_image(source, mapping)

    metadata = {
        "source_file": str(Path(source_file)),
        "frame_count": frame_count,
        "canvas_px": int(canvas_px),
        "requested_front_size_px": float(front_size_px),
        "camera_distance": float(camera_distance),
        "mapping": mapping,
        "frames": [],
    }

    for index in range(frame_count):
        nominal_angle = index * 360.0 / frame_count
        rendered, render_angle, actual_front, corners = _render_yaw(
            target_source,
            nominal_angle,
            canvas_px,
            front_size_px,
            camera_distance,
        )
        file_name = f"frame_{index:03d}.png"
        rendered.save(output / file_name, format="PNG")
        metadata["frames"].append(
            {
                "frame": index,
                "file_name": file_name,
                "nominal_angle_deg": nominal_angle,
                "render_angle_deg": render_angle,
                "actual_front_size_px": actual_front,
                "projected_corners_px": [[float(x), float(y)] for x, y in corners],
            }
        )

    (output / "frames.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8"
    )
    return metadata
