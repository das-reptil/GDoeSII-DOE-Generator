import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


TWO_PI = 2.0 * math.pi
UINT16_MAX = 65535


def _validate_shape(width_px, height_px):
    width_px = int(width_px)
    height_px = int(height_px)
    if width_px < 2 or height_px < 2:
        raise ValueError("DOE width and height must be at least 2 pixels.")
    return width_px, height_px


def _validate_sampling(pixel_size_nm, wavelength_nm):
    pixel_size_nm = float(pixel_size_nm)
    wavelength_nm = float(wavelength_nm)
    if pixel_size_nm <= 0:
        raise ValueError("Pixel size must be greater than 0 nm.")
    if wavelength_nm <= 0:
        raise ValueError("Wavelength must be greater than 0 nm.")
    return pixel_size_nm, wavelength_nm


def coordinate_grid(width_px, height_px, pixel_size_nm):
    width_px, height_px = _validate_shape(width_px, height_px)
    pixel_size_nm = float(pixel_size_nm)
    if pixel_size_nm <= 0:
        raise ValueError("Pixel size must be greater than 0 nm.")

    pitch_m = pixel_size_nm * 1e-9
    x = (np.arange(width_px, dtype=np.float64) - (width_px - 1) / 2.0) * pitch_m
    y = (np.arange(height_px, dtype=np.float64) - (height_px - 1) / 2.0) * pitch_m
    return np.meshgrid(x, y)


def wrap_phase(phase_rad):
    return np.mod(np.asarray(phase_rad, dtype=np.float64), TWO_PI)


def phase_to_uint16(phase_rad):
    phase = wrap_phase(phase_rad)
    normalized = phase / TWO_PI
    return np.rint(normalized * UINT16_MAX).astype(np.uint16)


def uint16_to_phase(values):
    values = np.asarray(values, dtype=np.float64)
    return np.clip(values, 0.0, UINT16_MAX) / UINT16_MAX * TWO_PI


def lens_phase(width_px, height_px, pixel_size_nm, wavelength_nm, focal_length_mm):
    pixel_size_nm, wavelength_nm = _validate_sampling(pixel_size_nm, wavelength_nm)
    focal_length_mm = float(focal_length_mm)
    if focal_length_mm == 0:
        raise ValueError("Focal length must not be 0 mm.")
    x, y = coordinate_grid(width_px, height_px, pixel_size_nm)
    wavelength_m = wavelength_nm * 1e-9
    focal_m = focal_length_mm * 1e-3
    phase = -math.pi * (x * x + y * y) / (wavelength_m * focal_m)
    return wrap_phase(phase)


def grating_phase(width_px, height_px, pixel_size_nm, period_um, angle_deg=0.0):
    width_px, height_px = _validate_shape(width_px, height_px)
    period_um = float(period_um)
    if period_um <= 0:
        raise ValueError("Grating period must be greater than 0 um.")
    x, y = coordinate_grid(width_px, height_px, pixel_size_nm)
    angle_rad = math.radians(float(angle_deg))
    coordinate = x * math.cos(angle_rad) + y * math.sin(angle_rad)
    period_m = period_um * 1e-6
    return wrap_phase(TWO_PI * coordinate / period_m)


def fresnel_zone_plate_phase(width_px, height_px, pixel_size_nm, wavelength_nm, focal_length_mm):
    pixel_size_nm, wavelength_nm = _validate_sampling(pixel_size_nm, wavelength_nm)
    focal_length_mm = float(focal_length_mm)
    if focal_length_mm <= 0:
        raise ValueError("Focal length must be greater than 0 mm.")
    x, y = coordinate_grid(width_px, height_px, pixel_size_nm)
    wavelength_m = wavelength_nm * 1e-9
    focal_m = focal_length_mm * 1e-3
    r2 = x * x + y * y
    zone = np.floor(r2 / (wavelength_m * focal_m)).astype(np.int64)
    return (zone % 2).astype(np.float64) * math.pi


def vortex_phase(width_px, height_px, pixel_size_nm, charge=1):
    charge = int(charge)
    if charge == 0:
        raise ValueError("Vortex charge must not be 0.")
    x, y = coordinate_grid(width_px, height_px, pixel_size_nm)
    return wrap_phase(charge * np.arctan2(y, x))


def fresnel_transfer_function(shape, pixel_size_nm, wavelength_nm, distance_mm):
    height_px, width_px = int(shape[0]), int(shape[1])
    _validate_shape(width_px, height_px)
    pixel_size_nm, wavelength_nm = _validate_sampling(pixel_size_nm, wavelength_nm)
    distance_m = float(distance_mm) * 1e-3
    if distance_m == 0:
        return np.ones((height_px, width_px), dtype=np.complex128)
    pitch_m = pixel_size_nm * 1e-9
    wavelength_m = wavelength_nm * 1e-9
    fx = np.fft.fftfreq(width_px, d=pitch_m)
    fy = np.fft.fftfreq(height_px, d=pitch_m)
    fx_grid, fy_grid = np.meshgrid(fx, fy)
    return np.exp(-1j * math.pi * wavelength_m * distance_m * (fx_grid * fx_grid + fy_grid * fy_grid))


def fresnel_propagate(field, pixel_size_nm, wavelength_nm, distance_mm):
    field = np.asarray(field, dtype=np.complex128)
    if field.ndim != 2:
        raise ValueError("Optical field must be a 2-D array.")
    transfer = fresnel_transfer_function(field.shape, pixel_size_nm, wavelength_nm, distance_mm)
    return np.fft.ifft2(np.fft.fft2(field) * transfer)


def normalize_intensity_uint16(field):
    intensity = np.abs(np.asarray(field)) ** 2
    maximum = float(np.max(intensity)) if intensity.size else 0.0
    if maximum <= 0:
        return np.zeros(intensity.shape, dtype=np.uint16)
    normalized = np.clip(intensity / maximum, 0.0, 1.0)
    return np.rint(normalized * UINT16_MAX).astype(np.uint16)


def simulate_phase(phase_rad, pixel_size_nm, wavelength_nm, distance_mm):
    field = np.exp(1j * wrap_phase(phase_rad))
    propagated = fresnel_propagate(field, pixel_size_nm, wavelength_nm, distance_mm)
    return normalize_intensity_uint16(propagated)


def direction_cosines_from_target_offset(offset_x_mm, offset_y_mm, distance_mm):
    offset_x_mm = float(offset_x_mm)
    offset_y_mm = float(offset_y_mm)
    distance_mm = float(distance_mm)
    if distance_mm <= 0:
        raise ValueError("Target distance z must be greater than 0 mm.")
    length_mm = math.sqrt(offset_x_mm * offset_x_mm + offset_y_mm * offset_y_mm + distance_mm * distance_mm)
    sx = offset_x_mm / length_mm
    sy = offset_y_mm / length_mm
    sz = distance_mm / length_mm
    return {
        "mode": "target-plane distance",
        "sx": sx,
        "sy": sy,
        "sz": sz,
        "theta_x_deg": math.degrees(math.atan2(offset_x_mm, distance_mm)),
        "theta_y_deg": math.degrees(math.atan2(offset_y_mm, distance_mm)),
        "total_angle_deg": math.degrees(math.atan2(math.hypot(offset_x_mm, offset_y_mm), distance_mm)),
        "offset_x_mm": offset_x_mm,
        "offset_y_mm": offset_y_mm,
        "distance_mm": distance_mm,
        "ray_length_mm": length_mm,
    }


def direction_cosines_from_angles(theta_x_deg, theta_y_deg):
    theta_x_deg = float(theta_x_deg)
    theta_y_deg = float(theta_y_deg)
    tx = math.tan(math.radians(theta_x_deg))
    ty = math.tan(math.radians(theta_y_deg))
    norm = math.sqrt(1.0 + tx * tx + ty * ty)
    sx = tx / norm
    sy = ty / norm
    sz = 1.0 / norm
    return {
        "mode": "angle",
        "sx": sx,
        "sy": sy,
        "sz": sz,
        "theta_x_deg": theta_x_deg,
        "theta_y_deg": theta_y_deg,
        "total_angle_deg": math.degrees(math.acos(sz)),
        "offset_x_mm": None,
        "offset_y_mm": None,
        "distance_mm": None,
        "ray_length_mm": None,
    }


def offset_sampling_info(sx, sy, wavelength_nm, pixel_size_nm):
    pixel_size_nm, wavelength_nm = _validate_sampling(pixel_size_nm, wavelength_nm)
    wavelength_um = wavelength_nm / 1000.0
    pixel_um = pixel_size_nm / 1000.0
    transverse = math.hypot(float(sx), float(sy))

    def metrics(component):
        if abs(component) < 1e-15:
            return None, None
        period_um = wavelength_um / abs(component)
        return period_um, period_um / pixel_um

    period_x_um, pixels_per_period_x = metrics(float(sx))
    period_y_um, pixels_per_period_y = metrics(float(sy))
    period_diag_um, pixels_per_period_diag = metrics(transverse)
    warning = None
    if pixels_per_period_diag is not None:
        if pixels_per_period_diag < 2.0:
            warning = "Aliasing: fewer than 2 pixels per diagonal phase-ramp period."
        elif pixels_per_period_diag < 3.0:
            warning = "Sampling is marginal: fewer than 3 pixels per diagonal phase-ramp period."
    return {
        "period_x_um": period_x_um,
        "period_y_um": period_y_um,
        "period_diag_um": period_diag_um,
        "pixels_per_period_x": pixels_per_period_x,
        "pixels_per_period_y": pixels_per_period_y,
        "pixels_per_period_diag": pixels_per_period_diag,
        "sampling_warning": warning,
    }


def offset_phase_ramp(width_px, height_px, pixel_size_nm, wavelength_nm, sx, sy):
    _, wavelength_nm = _validate_sampling(pixel_size_nm, wavelength_nm)
    x, y = coordinate_grid(width_px, height_px, pixel_size_nm)
    wavelength_m = wavelength_nm * 1e-9
    return TWO_PI * (float(sx) * x + float(sy) * y) / wavelength_m


def apply_phase_offset(phase_rad, pixel_size_nm, wavelength_nm, offset_mode="none", theta_x_deg=0.0, theta_y_deg=0.0, offset_x_mm=0.0, offset_y_mm=0.0, distance_mm=None):
    phase = np.asarray(phase_rad, dtype=np.float64)
    if phase.ndim != 2:
        raise ValueError("Phase array must be 2-D.")
    mode = str(offset_mode or "none").strip().lower()
    if mode in ("none", "off", "0"):
        info = {
            "mode": "none", "sx": 0.0, "sy": 0.0, "sz": 1.0,
            "theta_x_deg": 0.0, "theta_y_deg": 0.0, "total_angle_deg": 0.0,
            "offset_x_mm": 0.0, "offset_y_mm": 0.0,
            "distance_mm": float(distance_mm) if distance_mm is not None else None,
            "ray_length_mm": float(distance_mm) if distance_mm is not None else None,
        }
    elif mode in ("angle", "angles"):
        info = direction_cosines_from_angles(theta_x_deg, theta_y_deg)
    elif mode in ("distance", "target", "target-plane distance", "target plane distance"):
        if distance_mm is None:
            raise ValueError("Target distance z is required for target-plane offset mode.")
        info = direction_cosines_from_target_offset(offset_x_mm, offset_y_mm, distance_mm)
    else:
        raise ValueError("Unknown offset mode: {}".format(offset_mode))
    info.update(offset_sampling_info(info["sx"], info["sy"], wavelength_nm, pixel_size_nm))
    height_px, width_px = phase.shape
    ramp = offset_phase_ramp(width_px, height_px, pixel_size_nm, wavelength_nm, info["sx"], info["sy"])
    return wrap_phase(phase + ramp), ramp, info


def target_image_geometry(source_width_px, source_height_px, doe_width_px, doe_height_px, pixel_size_nm, target_width_um=0.0):
    """Calculate centered target-image dimensions in the sampled target plane.

    A target_width_um of 0 keeps the legacy behaviour and fits the image as
    large as possible into the complete target-plane calculation window.
    Positive values request a physical target width; height follows the source
    image aspect ratio. The resulting dimensions are quantized to whole pixels.
    """
    doe_width_px, doe_height_px = _validate_shape(doe_width_px, doe_height_px)
    source_width_px = int(source_width_px)
    source_height_px = int(source_height_px)
    if source_width_px < 1 or source_height_px < 1:
        raise ValueError("Target image width and height must be at least 1 pixel.")

    pixel_size_nm = float(pixel_size_nm)
    if pixel_size_nm <= 0:
        raise ValueError("Pixel size must be greater than 0 nm.")
    pixel_um = pixel_size_nm / 1000.0
    field_width_um = doe_width_px * pixel_um
    field_height_um = doe_height_px * pixel_um
    requested_width_um = float(target_width_um or 0.0)
    if requested_width_um < 0:
        raise ValueError("GS target width must be 0 (auto fit) or greater than 0 um.")

    if requested_width_um == 0.0:
        scale = min(doe_width_px / source_width_px, doe_height_px / source_height_px)
        target_width_px = max(1, min(doe_width_px, int(math.floor(source_width_px * scale))))
        target_height_px = max(1, min(doe_height_px, int(math.floor(source_height_px * scale))))
        sizing_mode = "fit"
    else:
        requested_height_um = requested_width_um * source_height_px / source_width_px
        if requested_width_um > field_width_um + 1e-12:
            raise ValueError(
                "Requested GS target width {:.3f} um exceeds target-plane width {:.3f} um.".format(
                    requested_width_um, field_width_um
                )
            )
        if requested_height_um > field_height_um + 1e-12:
            raise ValueError(
                "Requested GS target height {:.3f} um exceeds target-plane height {:.3f} um.".format(
                    requested_height_um, field_height_um
                )
            )
        target_width_px = max(1, int(round(requested_width_um / pixel_um)))
        target_height_px = max(1, int(round(requested_height_um / pixel_um)))
        if target_width_px > doe_width_px or target_height_px > doe_height_px:
            raise ValueError("Requested GS target does not fit into the sampled target plane after pixel quantization.")
        sizing_mode = "physical-width"

    actual_width_um = target_width_px * pixel_um
    actual_height_um = target_height_px * pixel_um
    return {
        "sizing_mode": sizing_mode,
        "source_width_px": source_width_px,
        "source_height_px": source_height_px,
        "requested_width_um": requested_width_um if requested_width_um > 0 else None,
        "target_width_px": target_width_px,
        "target_height_px": target_height_px,
        "actual_width_um": actual_width_um,
        "actual_height_um": actual_height_um,
        "field_width_um": field_width_um,
        "field_height_um": field_height_um,
        "pixel_size_um": pixel_um,
    }


def load_target_intensity(file_name, width_px, height_px, pixel_size_nm=None, target_width_um=0.0, return_info=False):
    width_px, height_px = _validate_shape(width_px, height_px)
    requested_width_um = float(target_width_um or 0.0)
    if requested_width_um < 0:
        raise ValueError("GS target width must be 0 (auto fit) or greater than 0 um.")
    if requested_width_um > 0 and pixel_size_nm is None:
        raise ValueError("Pixel size is required when a physical GS target width is specified.")

    with Image.open(file_name) as source:
        image = source.convert("L")
        if pixel_size_nm is not None:
            info = target_image_geometry(
                image.width,
                image.height,
                width_px,
                height_px,
                pixel_size_nm,
                requested_width_um,
            )
            target_size = (info["target_width_px"], info["target_height_px"])
            resized = image.resize(target_size, Image.Resampling.LANCZOS)
        else:
            resized = ImageOps.contain(image, (width_px, height_px), method=Image.Resampling.LANCZOS)
            info = {
                "sizing_mode": "fit",
                "source_width_px": image.width,
                "source_height_px": image.height,
                "requested_width_um": None,
                "target_width_px": resized.width,
                "target_height_px": resized.height,
                "actual_width_um": None,
                "actual_height_um": None,
                "field_width_um": None,
                "field_height_um": None,
                "pixel_size_um": None,
            }

        canvas = Image.new("L", (width_px, height_px), 0)
        x = (width_px - resized.width) // 2
        y = (height_px - resized.height) // 2
        canvas.paste(resized, (x, y))
        data = np.asarray(canvas, dtype=np.float64) / 255.0
        info["placement_x_px"] = x
        info["placement_y_px"] = y

    maximum = float(np.max(data)) if data.size else 0.0
    if maximum <= 0:
        raise ValueError("Target image contains no non-zero intensity.")
    normalized = np.clip(data / maximum, 0.0, 1.0)
    if return_info:
        return normalized, info
    return normalized


def gerchberg_saxton_phase(target_intensity, pixel_size_nm, wavelength_nm, distance_mm, iterations=50, seed=0, progress_callback=None):
    target = np.asarray(target_intensity, dtype=np.float64)
    if target.ndim != 2:
        raise ValueError("Target intensity must be a 2-D array.")
    if not np.any(target > 0):
        raise ValueError("Target intensity contains no non-zero values.")
    pixel_size_nm, wavelength_nm = _validate_sampling(pixel_size_nm, wavelength_nm)
    distance_mm = float(distance_mm)
    if distance_mm == 0:
        raise ValueError("Target distance must not be 0 mm.")
    iterations = int(iterations)
    if iterations < 1:
        raise ValueError("Gerchberg-Saxton iterations must be at least 1.")
    target = np.clip(target, 0.0, None)
    target /= float(np.max(target))
    target_amplitude = np.sqrt(target)
    rng = np.random.default_rng(int(seed))
    source_phase = rng.uniform(0.0, TWO_PI, target.shape)
    source_field = np.exp(1j * source_phase)
    for iteration in range(iterations):
        target_field = fresnel_propagate(source_field, pixel_size_nm, wavelength_nm, distance_mm)
        target_field = target_amplitude * np.exp(1j * np.angle(target_field))
        source_back = fresnel_propagate(target_field, pixel_size_nm, wavelength_nm, -distance_mm)
        source_field = np.exp(1j * np.angle(source_back))
        if progress_callback is not None:
            progress_callback(iteration + 1, iterations)
    phase = wrap_phase(np.angle(source_field))
    simulation = simulate_phase(phase, pixel_size_nm, wavelength_nm, distance_mm)
    return phase, simulation


def save_phase_png(phase_rad, output_file, metadata=None):
    output_path = Path(output_file)
    if output_path.suffix.lower() != ".png":
        output_path = output_path.with_suffix(".png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    phase_uint16 = phase_to_uint16(phase_rad)
    Image.fromarray(phase_uint16).save(output_path, format="PNG")
    metadata_path = output_path.with_suffix(".json")
    payload = {
        "format_version": 1,
        "type": "GDoeSII 16-bit phase map",
        "encoding": {
            "gray_min": 0, "gray_max": UINT16_MAX,
            "phase_min_rad": 0.0, "phase_max_rad": TWO_PI,
            "mapping": "linear modulo 2*pi",
        },
        "image": {"width_px": int(phase_uint16.shape[1]), "height_px": int(phase_uint16.shape[0])},
    }
    if metadata:
        payload["generator"] = metadata
    metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return str(output_path), str(metadata_path)
