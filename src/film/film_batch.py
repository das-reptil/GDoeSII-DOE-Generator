import json
from pathlib import Path

import numpy as np
from PIL import Image

from gdoesii_doe import (
    apply_phase_offset,
    fresnel_propagate,
    gerchberg_saxton_phase,
    load_target_intensity,
    save_phase_png,
)
from gdoesii_tilt import (
    gerchberg_saxton_tilted_phase,
    target_plane_geometry,
    tilted_angular_spectrum_propagate,
)

from .film_config import FilmConfig
from .frame_analysis import IMAGE_EXTENSIONS, analyze_array, analyze_frame, write_csv
from .frame_normalization import brightness_compensation
from .physical_projection import (
    gerchberg_saxton_physical_phase,
    load_physical_target_intensity,
    physical_projection_sampling,
    scaled_fresnel_propagate,
)
from .ring_layout import make_ring_layout, write_ring_layout_csv


def discover_frames(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"Frame directory does not exist: {directory}")
    frames = sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not frames:
        raise ValueError("No supported image frames found in the selected directory.")
    return frames


def _generated_frame_reference_width(frame_directory):
    """Return the front-facing reference width from frames.json when available."""
    metadata_path = Path(frame_directory) / "frames.json"
    if not metadata_path.is_file():
        return None
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        frames = payload.get("frames") or []
        if frames:
            value = frames[0].get("actual_front_size_px")
            if value is not None and float(value) > 0:
                return float(value)
        value = payload.get("requested_front_size_px")
        if value is not None and float(value) > 0:
            return float(value)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    return None


def _raw_target_power_metrics(intensity, target, active_threshold):
    intensity = np.asarray(intensity, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    target_max = float(np.max(target)) if target.size else 0.0
    threshold = target_max * float(active_threshold)
    mask = target > threshold

    total_power = float(np.sum(intensity))
    target_power = float(np.sum(intensity[mask])) if np.any(mask) else 0.0
    background_power = max(0.0, total_power - target_power)
    active_pixels = int(np.count_nonzero(mask))
    background_pixels = int(mask.size - active_pixels)

    target_mean = float(np.mean(intensity[mask])) if active_pixels else 0.0
    background_mean = float(np.mean(intensity[~mask])) if background_pixels else 0.0

    return {
        "propagated_total_power": total_power,
        "target_power": target_power,
        "background_power": background_power,
        "target_power_fraction": target_power / total_power if total_power > 0 else 0.0,
        "target_mean_power_per_pixel": target_mean,
        "background_mean_power_per_pixel": background_mean,
        "target_to_background_mean_ratio": (
            target_mean / background_mean if background_mean > 0 else None
        ),
        "propagated_peak_power_per_pixel": float(np.max(intensity)) if intensity.size else 0.0,
    }


def _save_uint16(values, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.asarray(values, dtype=np.uint16)).save(path, format="PNG")
    return str(path)


def run_batch(frame_directory, output_directory, config=None, progress_callback=None):
    """Generate one independent GS DOE for every target frame.

    Film mode is intentionally GS-only. Analytical DOE types are not accepted.
    """
    config = (config or FilmConfig()).validate()
    frames = discover_frames(frame_directory)
    output = Path(output_directory)

    doe_dir = output / "doe"
    sim_dir = output / "simulation"
    stats_dir = output / "statistics"
    layout_dir = output / "layout"
    for directory in (doe_dir, sim_dir, stats_dir, layout_dir):
        directory.mkdir(parents=True, exist_ok=True)

    config.save(output / "film_config.json")

    source_rows = []
    result_rows = []
    total_frames = len(frames)
    physical_mode = config.propagation_mode == "physical projection"
    use_tilted = (
        not physical_mode
        and (abs(config.target_pan_deg) > 1e-12 or abs(config.target_tilt_deg) > 1e-12)
    )
    reference_width_px = (
        _generated_frame_reference_width(frame_directory) if physical_mode else None
    )
    projection_sampling = None
    if physical_mode:
        projection_sampling = physical_projection_sampling(
            config.doe_width_px,
            config.doe_height_px,
            config.pixel_size_nm,
            config.wavelength_nm,
            config.target_distance_mm,
        )

    for index, frame_path in enumerate(frames):
        frame_angle_deg = index * 360.0 / total_frames
        source_stats = analyze_frame(frame_path, config.active_threshold)
        source_stats.update(frame_index=index, frame_angle_deg=frame_angle_deg)
        source_rows.append(source_stats)

        if physical_mode:
            target, target_info = load_physical_target_intensity(
                frame_path,
                config.doe_width_px,
                config.doe_height_px,
                config.pixel_size_nm,
                config.wavelength_nm,
                config.target_distance_mm,
                target_width_mm=config.target_width_mm,
                reference_width_px=reference_width_px,
                return_info=True,
            )
        else:
            target, target_info = load_target_intensity(
                frame_path,
                config.doe_width_px,
                config.doe_height_px,
                pixel_size_nm=config.pixel_size_nm,
                target_width_um=config.target_width_um,
                return_info=True,
            )
        target_stats = analyze_array(target, config.active_threshold)

        def gs_progress(current, total):
            if progress_callback is not None:
                progress_callback(
                    index,
                    total_frames,
                    current,
                    total,
                    f"GS frame {index + 1}/{total_frames}: iteration {current}/{total}",
                )

        if physical_mode:
            phase_base, simulation = gerchberg_saxton_physical_phase(
                target,
                config.pixel_size_nm,
                config.wavelength_nm,
                config.target_distance_mm,
                iterations=config.gs_iterations,
                seed=config.seed,
                progress_callback=gs_progress,
            )
            phase_export, _, offset = apply_phase_offset(
                phase_base,
                config.pixel_size_nm,
                config.wavelength_nm,
                offset_mode=(
                    "distance"
                    if abs(config.target_x_mm) > 1e-12 or abs(config.target_y_mm) > 1e-12
                    else "none"
                ),
                offset_x_mm=config.target_x_mm,
                offset_y_mm=config.target_y_mm,
                distance_mm=config.target_distance_mm,
            )
            # Brightness statistics remain in centered local target coordinates.
            propagated = scaled_fresnel_propagate(
                np.exp(1j * phase_base),
                config.pixel_size_nm,
                config.wavelength_nm,
                config.target_distance_mm,
            )
        elif use_tilted:
            phase_base, simulation = gerchberg_saxton_tilted_phase(
                target,
                config.pixel_size_nm,
                config.wavelength_nm,
                config.target_distance_mm,
                pan_deg=config.target_pan_deg,
                tilt_deg=config.target_tilt_deg,
                center_x_mm=config.target_x_mm,
                center_y_mm=config.target_y_mm,
                iterations=config.gs_iterations,
                seed=config.seed,
                progress_callback=gs_progress,
            )
            phase_export = phase_base
            propagated = tilted_angular_spectrum_propagate(
                np.exp(1j * phase_base),
                config.pixel_size_nm,
                config.wavelength_nm,
                config.target_distance_mm,
                pan_deg=config.target_pan_deg,
                tilt_deg=config.target_tilt_deg,
                center_x_mm=config.target_x_mm,
                center_y_mm=config.target_y_mm,
            )
            offset = {
                "mode": "included in tilted target-plane propagation",
                "offset_x_mm": config.target_x_mm,
                "offset_y_mm": config.target_y_mm,
            }
        else:
            phase_base, simulation = gerchberg_saxton_phase(
                target,
                config.pixel_size_nm,
                config.wavelength_nm,
                config.target_distance_mm,
                iterations=config.gs_iterations,
                seed=config.seed,
                progress_callback=gs_progress,
            )
            phase_export, _, offset = apply_phase_offset(
                phase_base,
                config.pixel_size_nm,
                config.wavelength_nm,
                offset_mode=(
                    "distance"
                    if abs(config.target_x_mm) > 1e-12 or abs(config.target_y_mm) > 1e-12
                    else "none"
                ),
                offset_x_mm=config.target_x_mm,
                offset_y_mm=config.target_y_mm,
                distance_mm=config.target_distance_mm,
            )
            # Brightness statistics are evaluated in local target coordinates.
            propagated = fresnel_propagate(
                np.exp(1j * phase_base),
                config.pixel_size_nm,
                config.wavelength_nm,
                config.target_distance_mm,
            )

        intensity = np.abs(propagated) ** 2
        power_metrics = _raw_target_power_metrics(
            intensity, target, config.active_threshold
        )

        target_width_mm = float(target_info["actual_width_um"]) / 1000.0
        target_height_mm = float(target_info["actual_height_um"]) / 1000.0
        plane = target_plane_geometry(
            config.target_distance_mm,
            pan_deg=config.target_pan_deg,
            tilt_deg=config.target_tilt_deg,
            center_x_mm=config.target_x_mm,
            center_y_mm=config.target_y_mm,
            width_mm=target_width_mm,
            height_mm=target_height_mm,
            pixel_size_nm=config.pixel_size_nm,
            wavelength_nm=config.wavelength_nm,
        )

        metadata = {
            "type": "Arbitrary Image (GS) film frame",
            "film_frame_index": index,
            "film_frame_count": total_frames,
            "film_frame_angle_deg": frame_angle_deg,
            "source_frame": frame_path.name,
            "width_px": int(config.doe_width_px),
            "height_px": int(config.doe_height_px),
            "pixel_size_nm": float(config.pixel_size_nm),
            "wavelength_nm": float(config.wavelength_nm),
            "distance_mm": float(config.target_distance_mm),
            "propagation_mode": config.propagation_mode,
            "gs_iterations": int(config.gs_iterations),
            "target_geometry": target_info,
            "target_plane": plane,
            "offset": offset,
            "brightness_analysis": power_metrics,
        }
        if projection_sampling is not None:
            metadata["physical_projection_sampling"] = projection_sampling

        doe_name = f"DOE_{index:03d}.png"
        doe_path = doe_dir / doe_name
        png_path, json_path = save_phase_png(phase_export, doe_path, metadata)
        sim_path = _save_uint16(simulation, sim_dir / f"sim_{index:03d}.png")

        row = {
            "frame_index": index,
            "frame_angle_deg": frame_angle_deg,
            "source_frame": frame_path.name,
            "doe_file": Path(png_path).name,
            "doe_metadata_file": Path(json_path).name,
            "simulation_file": Path(sim_path).name,
            "propagation_mode": config.propagation_mode,
            "target_width_px": target_info["target_width_px"],
            "target_height_px": target_info["target_height_px"],
            "target_width_um": target_info["actual_width_um"],
            "target_height_um": target_info["actual_height_um"],
            "target_active_fraction": target_stats["active_fraction"],
            "target_sum_intensity": target_stats["sum_intensity"],
            **power_metrics,
        }
        if physical_mode:
            row.update(
                target_reference_width_mm=target_info["actual_reference_width_mm"],
                target_pixel_size_x_um=target_info["target_pixel_size_x_um"],
                target_pixel_size_y_um=target_info["target_pixel_size_y_um"],
                target_field_width_mm=target_info["target_field_width_mm"],
                target_field_height_mm=target_info["target_field_height_mm"],
            )
        result_rows.append(row)

        if progress_callback is not None:
            progress_callback(
                index + 1,
                total_frames,
                config.gs_iterations,
                config.gs_iterations,
                f"Completed frame {index + 1}/{total_frames}",
            )

    write_csv(source_rows, stats_dir / "frame_source_statistics.csv")
    brightness_rows = brightness_compensation(
        result_rows,
        mode=config.brightness_mode,
        geometric_gamma=config.geometric_gamma,
    )
    write_csv(brightness_rows, stats_dir / "brightness_statistics.csv")

    layout_rows = make_ring_layout(
        total_frames,
        pitch_mm=config.ring_pitch_mm,
        radius_mm=config.ring_radius_mm,
        orientation=config.ring_orientation,
    )
    write_ring_layout_csv(layout_rows, layout_dir / "DOE_ring_layout.csv")

    summary = {
        "mode": "GS film batch",
        "propagation_mode": config.propagation_mode,
        "frame_count": total_frames,
        "input_directory": str(Path(frame_directory)),
        "output_directory": str(output),
        "config": config.to_dict(),
        "physical_projection_sampling": projection_sampling,
        "brightness_note": (
            "recommended_laser_or_duty_factor is an external attenuation recommendation. "
            "A global scalar target-intensity multiplier would be cancelled by GS target normalization."
        ),
        "files": {
            "source_statistics": "statistics/frame_source_statistics.csv",
            "brightness_statistics": "statistics/brightness_statistics.csv",
            "ring_layout": "layout/DOE_ring_layout.csv",
        },
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    return summary
