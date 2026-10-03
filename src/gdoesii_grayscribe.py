import json
import math
from pathlib import Path

import numpy as np
from PIL import Image


UINT16_MAX = 65535


def load_normalized_grayscale(file_name):
    image = Image.open(file_name)
    original_mode = image.mode
    if image.mode not in ("I;16", "I;16L", "I;16B", "I", "F", "L"):
        image = image.convert("L")
    data = np.asarray(image)
    if image.mode in ("I;16", "I;16L", "I;16B") or data.dtype == np.uint16:
        code_max = 65535.0
        source_bit_depth = 16
    elif image.mode == "I" and data.size and np.min(data) >= 0 and np.max(data) <= 65535:
        code_max = 65535.0
        source_bit_depth = 16
    elif image.mode == "L" or data.dtype == np.uint8:
        code_max = 255.0
        source_bit_depth = 8
    elif image.mode == "F":
        values = np.asarray(data, dtype=np.float64)
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            normalized = np.zeros(values.shape, dtype=np.float64)
        else:
            minimum = float(np.min(finite))
            maximum = float(np.max(finite))
            normalized = np.zeros(values.shape, dtype=np.float64) if maximum <= minimum else (values - minimum) / (maximum - minimum)
        return np.clip(normalized, 0.0, 1.0), {
            "source_mode": original_mode,
            "source_bit_depth": "float",
            "source_code_max": None,
        }
    else:
        raise ValueError("Unsupported grayscale image mode: {}".format(image.mode))
    normalized = np.asarray(data, dtype=np.float64) / code_max
    normalized = np.nan_to_num(normalized)
    normalized = np.clip(normalized, 0.0, 1.0)
    return normalized, {
        "source_mode": original_mode,
        "source_bit_depth": source_bit_depth,
        "source_code_max": int(code_max),
    }


def validate_optical_parameters(wavelength_nm, refractive_index, phase_min_rad, phase_max_rad, pixel_size_nm=None, environment_refractive_index=1.0):
    wavelength_nm = float(wavelength_nm)
    refractive_index = float(refractive_index)
    environment_refractive_index = float(environment_refractive_index)
    phase_min_rad = float(phase_min_rad)
    phase_max_rad = float(phase_max_rad)
    if wavelength_nm <= 0:
        raise ValueError("Wavelength must be greater than 0 nm.")
    if refractive_index <= 0.0:
        raise ValueError("DOE refractive index must be greater than 0.")
    if environment_refractive_index <= 0.0:
        raise ValueError("Environment refractive index must be greater than 0.")
    if refractive_index <= environment_refractive_index:
        raise ValueError("DOE refractive index must be greater than the environment refractive index for a positive relief-height mapping.")
    if phase_max_rad <= phase_min_rad:
        raise ValueError("Maximum phase must be greater than minimum phase.")
    if pixel_size_nm is not None:
        pixel_size_nm = float(pixel_size_nm)
        if pixel_size_nm <= 0:
            raise ValueError("Pixel size must be greater than 0 nm.")
    return wavelength_nm, refractive_index, environment_refractive_index, phase_min_rad, phase_max_rad, pixel_size_nm


def phase_span_to_height_nm(wavelength_nm, refractive_index, phase_min_rad=0.0, phase_max_rad=2.0 * math.pi, environment_refractive_index=1.0):
    wavelength_nm, refractive_index, environment_refractive_index, phase_min_rad, phase_max_rad, _ = validate_optical_parameters(
        wavelength_nm, refractive_index, phase_min_rad, phase_max_rad,
        environment_refractive_index=environment_refractive_index,
    )
    phase_span = phase_max_rad - phase_min_rad
    delta_n = refractive_index - environment_refractive_index
    return phase_span * wavelength_nm / (2.0 * math.pi * delta_n)


def normalized_to_phase(normalized, phase_min_rad, phase_max_rad):
    normalized = np.clip(np.asarray(normalized, dtype=np.float64), 0.0, 1.0)
    return float(phase_min_rad) + normalized * (float(phase_max_rad) - float(phase_min_rad))


def normalized_to_uint16(normalized):
    normalized = np.clip(np.asarray(normalized, dtype=np.float64), 0.0, 1.0)
    return np.rint(normalized * UINT16_MAX).astype(np.uint16)


def normalized_to_height_nm(normalized, wavelength_nm, refractive_index, phase_min_rad, phase_max_rad, environment_refractive_index=1.0):
    max_height_nm = phase_span_to_height_nm(
        wavelength_nm, refractive_index, phase_min_rad, phase_max_rad,
        environment_refractive_index=environment_refractive_index,
    )
    normalized = np.clip(np.asarray(normalized, dtype=np.float64), 0.0, 1.0)
    return normalized * max_height_nm


def export_grayscribex_normalized(normalized, output_file, wavelength_nm, refractive_index, phase_min_rad, phase_max_rad, pixel_size_nm=None, environment_refractive_index=1.0, source_info=None, extra_metadata=None):
    wavelength_nm, refractive_index, environment_refractive_index, phase_min_rad, phase_max_rad, pixel_size_nm = validate_optical_parameters(
        wavelength_nm, refractive_index, phase_min_rad, phase_max_rad, pixel_size_nm,
        environment_refractive_index=environment_refractive_index,
    )
    normalized = np.asarray(normalized, dtype=np.float64)
    if normalized.ndim != 2:
        raise ValueError("GrayScribeX height map must be a 2-D array.")
    normalized = np.clip(np.nan_to_num(normalized), 0.0, 1.0)
    height_map_uint16 = normalized_to_uint16(normalized)
    max_height_nm = phase_span_to_height_nm(
        wavelength_nm, refractive_index, phase_min_rad, phase_max_rad,
        environment_refractive_index=environment_refractive_index,
    )
    output_path = Path(output_file)
    if output_path.suffix.lower() != ".png":
        output_path = output_path.with_suffix(".png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(height_map_uint16).save(output_path, format="PNG")
    height_px, width_px = height_map_uint16.shape
    image_info = {"width_px": int(width_px), "height_px": int(height_px), "pixel_size_nm": pixel_size_nm}
    if pixel_size_nm is not None:
        image_info.update({
            "physical_width_um": width_px * pixel_size_nm / 1000.0,
            "physical_height_um": height_px * pixel_size_nm / 1000.0,
        })
    metadata = {
        "format_version": 2,
        "target_workflow": "Nanoscribe Quantum X / GrayScribeX",
        "encoding": {
            "type": "unsigned 16-bit grayscale height map",
            "gray_min": 0,
            "gray_max": UINT16_MAX,
            "height_min_nm": 0.0,
            "height_max_nm": max_height_nm,
            "mapping": "linear",
        },
        "optics": {
            "wavelength_nm": wavelength_nm,
            "refractive_index": refractive_index,
            "material_refractive_index": refractive_index,
            "environment_refractive_index": environment_refractive_index,
            "delta_refractive_index": refractive_index - environment_refractive_index,
            "phase_min_rad": phase_min_rad,
            "phase_max_rad": phase_max_rad,
            "phase_span_rad": phase_max_rad - phase_min_rad,
        },
        "image": image_info,
        "source": source_info or {"type": "generated"},
        "model": {
            "formula": "h = (phi - phase_min) * lambda / (2*pi*(n_material - n_environment))",
            "note": "The PNG encodes the requested relative surface height. GrayScribeX/Nanoscribe calibration remains responsible for mapping gray values to machine writing parameters.",
        },
    }
    if extra_metadata:
        metadata["generator"] = extra_metadata
    metadata_path = output_path.with_suffix(".json")
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "png_path": str(output_path),
        "metadata_path": str(metadata_path),
        "max_height_nm": max_height_nm,
        "width_px": int(width_px),
        "height_px": int(height_px),
        "height_map_uint16": height_map_uint16,
        "metadata": metadata,
    }


def export_grayscribex_png(source_file, output_file, wavelength_nm, refractive_index, phase_min_rad, phase_max_rad, pixel_size_nm=None, environment_refractive_index=1.0):
    normalized, source_info = load_normalized_grayscale(source_file)
    source_info = {"file_name": Path(source_file).name, **source_info}
    return export_grayscribex_normalized(
        normalized=normalized,
        output_file=output_file,
        wavelength_nm=wavelength_nm,
        refractive_index=refractive_index,
        phase_min_rad=phase_min_rad,
        phase_max_rad=phase_max_rad,
        pixel_size_nm=pixel_size_nm,
        environment_refractive_index=environment_refractive_index,
        source_info=source_info,
    )
