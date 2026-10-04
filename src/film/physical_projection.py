import math
from pathlib import Path

import numpy as np
from PIL import Image

from gdoesii_doe import TWO_PI, normalize_intensity_uint16, wrap_phase


def physical_projection_sampling(width_px, height_px, pixel_size_nm, wavelength_nm, distance_mm):
    """Return single-FFT Fresnel source/target sampling for a physical projection.

    For a source pitch dx1 and propagation distance z, the single-FFT Fresnel
    transform samples the destination plane at

        dx2 = lambda * z / (N * dx1)

    independently in X and Y.  The target field width is therefore lambda*z/dx1.
    """
    width_px = int(width_px)
    height_px = int(height_px)
    pixel_m = float(pixel_size_nm) * 1e-9
    wavelength_m = float(wavelength_nm) * 1e-9
    distance_m = float(distance_mm) * 1e-3
    if width_px < 2 or height_px < 2:
        raise ValueError("DOE width and height must be at least 2 pixels.")
    if pixel_m <= 0 or wavelength_m <= 0 or distance_m <= 0:
        raise ValueError("Pixel size, wavelength and target distance must be greater than 0.")

    target_dx_m = wavelength_m * distance_m / (width_px * pixel_m)
    target_dy_m = wavelength_m * distance_m / (height_px * pixel_m)
    source_width_m = width_px * pixel_m
    source_height_m = height_px * pixel_m
    target_width_m = width_px * target_dx_m
    target_height_m = height_px * target_dy_m

    # Sampling of the input quadratic Fresnel chirp at the source aperture edge.
    # Values <= 1 are inside the source-grid Nyquist limit for the paraxial chirp.
    input_chirp_ratio_x = width_px * pixel_m * pixel_m / (wavelength_m * distance_m)
    input_chirp_ratio_y = height_px * pixel_m * pixel_m / (wavelength_m * distance_m)
    warning = None
    maximum_ratio = max(input_chirp_ratio_x, input_chirp_ratio_y)
    if maximum_ratio > 1.0:
        warning = "Input Fresnel chirp exceeds the source-grid Nyquist limit."
    elif maximum_ratio > 0.75:
        warning = "Input Fresnel chirp sampling is close to the source-grid Nyquist limit."

    return {
        "mode": "physical projection",
        "source_pixel_size_um": pixel_m * 1e6,
        "source_width_mm": source_width_m * 1e3,
        "source_height_mm": source_height_m * 1e3,
        "target_pixel_size_x_um": target_dx_m * 1e6,
        "target_pixel_size_y_um": target_dy_m * 1e6,
        "target_field_width_mm": target_width_m * 1e3,
        "target_field_height_mm": target_height_m * 1e3,
        "input_chirp_nyquist_ratio_x": input_chirp_ratio_x,
        "input_chirp_nyquist_ratio_y": input_chirp_ratio_y,
        "sampling_warning": warning,
    }


def _centered_coordinates(count, pitch_m):
    return (np.arange(int(count), dtype=np.float64) - int(count) // 2) * float(pitch_m)


def _scaled_fresnel_chirps(shape, pixel_size_nm, wavelength_nm, distance_mm):
    height, width = int(shape[0]), int(shape[1])
    sampling = physical_projection_sampling(
        width, height, pixel_size_nm, wavelength_nm, distance_mm
    )
    source_pitch_m = float(pixel_size_nm) * 1e-9
    wavelength_m = float(wavelength_nm) * 1e-9
    distance_m = float(distance_mm) * 1e-3
    target_dx_m = sampling["target_pixel_size_x_um"] * 1e-6
    target_dy_m = sampling["target_pixel_size_y_um"] * 1e-6

    x1 = _centered_coordinates(width, source_pitch_m)
    y1 = _centered_coordinates(height, source_pitch_m)
    x2 = _centered_coordinates(width, target_dx_m)
    y2 = _centered_coordinates(height, target_dy_m)

    q1 = np.exp(
        1j
        * math.pi
        / (wavelength_m * distance_m)
        * (y1[:, None] * y1[:, None] + x1[None, :] * x1[None, :])
    )
    q2 = np.exp(
        1j
        * math.pi
        / (wavelength_m * distance_m)
        * (y2[:, None] * y2[:, None] + x2[None, :] * x2[None, :])
    )
    return q1, q2, sampling


def scaled_fresnel_propagate(field, pixel_size_nm, wavelength_nm, distance_mm, inverse=False):
    """Propagate between the DOE plane and its physically scaled Fresnel plane.

    This uses the single-FFT Fresnel transform.  Constant global amplitude and
    phase prefactors are intentionally omitted; the orthonormal FFT makes the
    discrete forward/inverse pair reciprocal, which is useful for GS iterations.
    """
    field = np.asarray(field, dtype=np.complex128)
    if field.ndim != 2:
        raise ValueError("Optical field must be a 2-D array.")
    if field.shape[0] < 2 or field.shape[1] < 2:
        raise ValueError("Optical field must be at least 2 x 2 pixels.")

    q1, q2, _ = _scaled_fresnel_chirps(
        field.shape, pixel_size_nm, wavelength_nm, distance_mm
    )
    if not inverse:
        prepared = field * q1
        transformed = np.fft.fftshift(
            np.fft.fft2(np.fft.ifftshift(prepared), norm="ortho")
        )
        return transformed * q2

    prepared = field * np.conj(q2)
    transformed = np.fft.fftshift(
        np.fft.ifft2(np.fft.ifftshift(prepared), norm="ortho")
    )
    return transformed * np.conj(q1)


def simulate_phase_physical(phase_rad, pixel_size_nm, wavelength_nm, distance_mm):
    field = np.exp(1j * wrap_phase(phase_rad))
    propagated = scaled_fresnel_propagate(
        field, pixel_size_nm, wavelength_nm, distance_mm
    )
    return normalize_intensity_uint16(propagated)


def gerchberg_saxton_physical_phase(
    target_intensity,
    pixel_size_nm,
    wavelength_nm,
    distance_mm,
    iterations=50,
    seed=0,
    progress_callback=None,
):
    """GS iteration using reciprocal physically scaled Fresnel transforms."""
    target = np.asarray(target_intensity, dtype=np.float64)
    if target.ndim != 2:
        raise ValueError("Target intensity must be a 2-D array.")
    if not np.any(target > 0):
        raise ValueError("Target intensity contains no non-zero values.")
    iterations = int(iterations)
    if iterations < 1:
        raise ValueError("Gerchberg-Saxton iterations must be at least 1.")

    physical_projection_sampling(
        target.shape[1], target.shape[0], pixel_size_nm, wavelength_nm, distance_mm
    )
    target = np.clip(target, 0.0, None)
    target /= float(np.max(target))
    target_amplitude = np.sqrt(target)

    rng = np.random.default_rng(int(seed))
    source_field = np.exp(1j * rng.uniform(0.0, TWO_PI, target.shape))
    for iteration in range(iterations):
        target_field = scaled_fresnel_propagate(
            source_field, pixel_size_nm, wavelength_nm, distance_mm
        )
        target_field = target_amplitude * np.exp(1j * np.angle(target_field))
        source_back = scaled_fresnel_propagate(
            target_field, pixel_size_nm, wavelength_nm, distance_mm, inverse=True
        )
        source_field = np.exp(1j * np.angle(source_back))
        if progress_callback is not None:
            progress_callback(iteration + 1, iterations)

    phase = wrap_phase(np.angle(source_field))
    simulation = simulate_phase_physical(
        phase, pixel_size_nm, wavelength_nm, distance_mm
    )
    return phase, simulation


def load_physical_target_intensity(
    file_name,
    doe_width_px,
    doe_height_px,
    pixel_size_nm,
    wavelength_nm,
    distance_mm,
    target_width_mm=0.0,
    reference_width_px=None,
    return_info=False,
):
    """Load an image on the physical target-plane sampling grid.

    target_width_mm refers to reference_width_px inside the source frame.  With
    generated film frames this lets, for example, a 600 px front-facing logo be
    defined as 50 mm while the surrounding 1024 px frame remains a larger dark
    computational canvas.  If reference_width_px is omitted, the complete
    source image width is the reference.
    """
    sampling = physical_projection_sampling(
        doe_width_px,
        doe_height_px,
        pixel_size_nm,
        wavelength_nm,
        distance_mm,
    )
    target_width_mm = float(target_width_mm or 0.0)
    if target_width_mm < 0:
        raise ValueError("Physical target width must be 0 (fit) or greater than 0 mm.")

    target_dx_mm = sampling["target_pixel_size_x_um"] / 1000.0
    target_dy_mm = sampling["target_pixel_size_y_um"] / 1000.0
    field_width_mm = sampling["target_field_width_mm"]
    field_height_mm = sampling["target_field_height_mm"]

    with Image.open(file_name) as source:
        image = source.convert("L")
        source_width = int(image.width)
        source_height = int(image.height)
        reference = float(reference_width_px or source_width)
        if reference <= 0 or reference > source_width:
            raise ValueError("Reference target width in pixels must be >0 and <= source-frame width.")

        if target_width_mm > 0:
            canvas_width_mm = target_width_mm * source_width / reference
            canvas_height_mm = canvas_width_mm * source_height / source_width
            sizing_mode = "physical-projection-width"
        else:
            source_aspect = source_width / source_height
            field_aspect = field_width_mm / field_height_mm
            if field_aspect >= source_aspect:
                canvas_height_mm = field_height_mm
                canvas_width_mm = canvas_height_mm * source_aspect
            else:
                canvas_width_mm = field_width_mm
                canvas_height_mm = canvas_width_mm / source_aspect
            sizing_mode = "fit"

        if canvas_width_mm > field_width_mm + 1e-12:
            raise ValueError(
                "Target frame width {:.3f} mm exceeds physical target field width {:.3f} mm.".format(
                    canvas_width_mm, field_width_mm
                )
            )
        if canvas_height_mm > field_height_mm + 1e-12:
            raise ValueError(
                "Target frame height {:.3f} mm exceeds physical target field height {:.3f} mm.".format(
                    canvas_height_mm, field_height_mm
                )
            )

        resized_width = max(1, int(round(canvas_width_mm / target_dx_mm)))
        resized_height = max(1, int(round(canvas_height_mm / target_dy_mm)))
        if resized_width > int(doe_width_px) or resized_height > int(doe_height_px):
            raise ValueError("Target frame does not fit the physical projection raster after quantization.")

        resized = image.resize(
            (resized_width, resized_height), Image.Resampling.LANCZOS
        )
        canvas = Image.new("L", (int(doe_width_px), int(doe_height_px)), 0)
        placement_x = (int(doe_width_px) - resized_width) // 2
        placement_y = (int(doe_height_px) - resized_height) // 2
        canvas.paste(resized, (placement_x, placement_y))
        data = np.asarray(canvas, dtype=np.float64) / 255.0

    maximum = float(np.max(data)) if data.size else 0.0
    if maximum <= 0:
        raise ValueError("Target image contains no non-zero intensity.")
    normalized = np.clip(data / maximum, 0.0, 1.0)

    actual_canvas_width_mm = resized_width * target_dx_mm
    actual_canvas_height_mm = resized_height * target_dy_mm
    actual_reference_width_mm = actual_canvas_width_mm * reference / source_width
    info = {
        "sizing_mode": sizing_mode,
        "source_width_px": source_width,
        "source_height_px": source_height,
        "reference_width_px": reference,
        "requested_reference_width_mm": target_width_mm if target_width_mm > 0 else None,
        "actual_reference_width_mm": actual_reference_width_mm,
        "target_width_px": resized_width,
        "target_height_px": resized_height,
        "actual_width_um": actual_canvas_width_mm * 1000.0,
        "actual_height_um": actual_canvas_height_mm * 1000.0,
        "actual_width_mm": actual_canvas_width_mm,
        "actual_height_mm": actual_canvas_height_mm,
        "placement_x_px": placement_x,
        "placement_y_px": placement_y,
        "target_pixel_size_x_um": sampling["target_pixel_size_x_um"],
        "target_pixel_size_y_um": sampling["target_pixel_size_y_um"],
        "target_field_width_mm": field_width_mm,
        "target_field_height_mm": field_height_mm,
        "physical_projection_sampling": sampling,
    }
    if return_info:
        return normalized, info
    return normalized
