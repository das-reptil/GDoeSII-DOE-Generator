import math

import numpy as np

from gdoesii_doe import TWO_PI, normalize_intensity_uint16, wrap_phase


def target_plane_basis(pan_deg=0.0, tilt_deg=0.0):
    """Return target-plane basis vectors in global DOE coordinates.

    Coordinates use +x to the right, +y in the direction of increasing image
    rows, and +z from the DOE towards the target. Positive pan turns the target
    normal towards +x. Positive tilt turns the normal towards -y (upwards).
    Rotation order is tilt about global x followed by pan about global y.
    """
    pan = math.radians(float(pan_deg))
    tilt = math.radians(float(tilt_deg))
    cp, sp = math.cos(pan), math.sin(pan)
    ct, st = math.cos(tilt), math.sin(tilt)

    rotate_x = np.array(
        ((1.0, 0.0, 0.0), (0.0, ct, -st), (0.0, st, ct)),
        dtype=np.float64,
    )
    rotate_y = np.array(
        ((cp, 0.0, sp), (0.0, 1.0, 0.0), (-sp, 0.0, cp)),
        dtype=np.float64,
    )
    rotation = rotate_y @ rotate_x
    return rotation[:, 0], rotation[:, 1], rotation[:, 2]


def tilted_plane_sampling_info(pixel_size_nm, wavelength_nm, pan_deg=0.0, tilt_deg=0.0):
    """Estimate sampling of the carrier introduced by a tilted target plane."""
    pixel_m = float(pixel_size_nm) * 1e-9
    wavelength_m = float(wavelength_nm) * 1e-9
    if pixel_m <= 0 or wavelength_m <= 0:
        raise ValueError("Pixel size and wavelength must be greater than 0.")

    u_axis, v_axis, normal = target_plane_basis(pan_deg, tilt_deg)

    # A normally incident (+z) plane wave appears as a carrier in the local
    # coordinates of a tilted target plane.
    carrier_u = float(u_axis[2] / wavelength_m)
    carrier_v = float(v_axis[2] / wavelength_m)
    nyquist = float(1.0 / (2.0 * pixel_m))

    def pixels_per_period(frequency):
        if abs(frequency) < 1e-15:
            return None
        return float(1.0 / (abs(frequency) * pixel_m))

    pixels_u = pixels_per_period(carrier_u)
    pixels_v = pixels_per_period(carrier_v)
    candidates = [value for value in (pixels_u, pixels_v) if value is not None]
    minimum = min(candidates) if candidates else None

    warning = None
    if normal[2] <= 0:
        warning = "Target plane faces away from the +z propagation direction."
    elif abs(carrier_u) >= nyquist or abs(carrier_v) >= nyquist:
        warning = "Aliasing: target-plane tilt carrier exceeds the Nyquist frequency."
    elif minimum is not None and minimum < 3.0:
        warning = "Target-plane tilt sampling is marginal: fewer than 3 pixels per carrier period."

    return {
        "carrier_u_per_m": carrier_u,
        "carrier_v_per_m": carrier_v,
        "nyquist_per_m": nyquist,
        "pixels_per_carrier_u": pixels_u,
        "pixels_per_carrier_v": pixels_v,
        "minimum_pixels_per_carrier": minimum,
        "sampling_warning": warning,
    }


def target_plane_geometry(
    distance_mm,
    pan_deg=0.0,
    tilt_deg=0.0,
    center_x_mm=0.0,
    center_y_mm=0.0,
    width_mm=None,
    height_mm=None,
    pixel_size_nm=None,
    wavelength_nm=None,
):
    """Return a JSON-serializable description of the target plane in 3-D."""
    distance_mm = float(distance_mm)
    if distance_mm <= 0:
        raise ValueError("Target distance z must be greater than 0 mm.")

    u_axis, v_axis, normal = target_plane_basis(pan_deg, tilt_deg)
    center = np.array(
        (float(center_x_mm), float(center_y_mm), distance_mm),
        dtype=np.float64,
    )

    info = {
        "center_mm": [float(value) for value in center],
        "pan_deg": float(pan_deg),
        "tilt_deg": float(tilt_deg),
        "rotation_order": "tilt-x then pan-y",
        "axis_convention": "+x right, +y increasing image rows, +z DOE-to-target; positive pan -> +x, positive tilt -> -y",
        "u_axis": [float(value) for value in u_axis],
        "v_axis": [float(value) for value in v_axis],
        "normal": [float(value) for value in normal],
        "corners_mm": None,
    }

    if width_mm is not None or height_mm is not None:
        if width_mm is None or height_mm is None:
            raise ValueError("Both target width and height are required to calculate target-plane corners.")
        width_mm = float(width_mm)
        height_mm = float(height_mm)
        if width_mm <= 0 or height_mm <= 0:
            raise ValueError("Target-plane width and height must be greater than 0.")

        corners = {}
        for name, sign_u, sign_v in (
            ("top_left", -1.0, -1.0),
            ("top_right", 1.0, -1.0),
            ("bottom_left", -1.0, 1.0),
            ("bottom_right", 1.0, 1.0),
        ):
            point = center + sign_u * 0.5 * width_mm * u_axis + sign_v * 0.5 * height_mm * v_axis
            corners[name] = [float(value) for value in point]

        info["width_mm"] = width_mm
        info["height_mm"] = height_mm
        info["corners_mm"] = corners

    if pixel_size_nm is not None and wavelength_nm is not None:
        info["sampling"] = tilted_plane_sampling_info(
            pixel_size_nm,
            wavelength_nm,
            pan_deg,
            tilt_deg,
        )

    return info


def _centered_spectrum(field):
    return np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(field)))


def _field_from_centered_spectrum(spectrum):
    return np.fft.fftshift(np.fft.ifft2(np.fft.ifftshift(spectrum)))


def _bilinear_sample_regular_grid(values, x_query, y_query, x0, dx, y0, dy):
    """Bilinearly sample a complex array on a regular, monotonically spaced grid."""
    height, width = values.shape
    ix = (x_query - x0) / dx
    iy = (y_query - y0) / dy
    i0 = np.floor(ix).astype(np.int64)
    j0 = np.floor(iy).astype(np.int64)
    weight_x = ix - i0
    weight_y = iy - j0

    valid = (i0 >= 0) & (i0 < width - 1) & (j0 >= 0) & (j0 < height - 1)
    ii = np.clip(i0, 0, width - 2)
    jj = np.clip(j0, 0, height - 2)

    sampled = (
        (1.0 - weight_x) * (1.0 - weight_y) * values[jj, ii]
        + weight_x * (1.0 - weight_y) * values[jj, ii + 1]
        + (1.0 - weight_x) * weight_y * values[jj + 1, ii]
        + weight_x * weight_y * values[jj + 1, ii + 1]
    )
    return np.where(valid, sampled, 0.0), valid


def tilted_angular_spectrum_propagate(
    field,
    pixel_size_nm,
    wavelength_nm,
    distance_mm,
    pan_deg=0.0,
    tilt_deg=0.0,
    center_x_mm=0.0,
    center_y_mm=0.0,
    inverse=False,
    chunk_rows=128,
):
    """Propagate a complex field between the DOE plane and a tilted plane.

    The implementation follows the rotated-angular-spectrum idea: the angular
    spectrum is rotated in spatial-frequency space and interpolated onto the
    destination grid. Translation to the target-plane center is applied as a
    spectral phase factor. The inverse path uses the reciprocal coordinate
    mapping and Jacobian, which is suitable for iterative GS propagation.
    """
    field = np.asarray(field, dtype=np.complex128)
    if field.ndim != 2:
        raise ValueError("Optical field must be a 2-D array.")
    height, width = field.shape
    if width < 2 or height < 2:
        raise ValueError("Optical field must be at least 2 x 2 pixels.")

    pixel_m = float(pixel_size_nm) * 1e-9
    wavelength_m = float(wavelength_nm) * 1e-9
    distance_m = float(distance_mm) * 1e-3
    if pixel_m <= 0 or wavelength_m <= 0:
        raise ValueError("Pixel size and wavelength must be greater than 0.")
    if distance_m <= 0:
        raise ValueError("Target distance z must be greater than 0 mm.")

    u_axis, v_axis, normal = target_plane_basis(pan_deg, tilt_deg)
    if normal[2] <= 0:
        raise ValueError("Target plane must face the +z propagation half-space.")

    fx = np.fft.fftshift(np.fft.fftfreq(width, d=pixel_m))
    fy = np.fft.fftshift(np.fft.fftfreq(height, d=pixel_m))
    delta_fx = float(fx[1] - fx[0])
    delta_fy = float(fy[1] - fy[0])
    wave_frequency = 1.0 / wavelength_m
    spectrum = _centered_spectrum(field)
    output_spectrum = np.zeros((height, width), dtype=np.complex128)

    center_x_m = float(center_x_mm) * 1e-3
    center_y_m = float(center_y_mm) * 1e-3
    chunk_rows = max(1, int(chunk_rows))

    if not inverse:
        local_u = fx[None, :]
        for start in range(0, height, chunk_rows):
            local_v = fy[start:start + chunk_rows, None]
            propagating = wave_frequency * wave_frequency - local_u * local_u - local_v * local_v
            local_n = np.sqrt(np.maximum(propagating, 0.0))

            global_x = local_u * u_axis[0] + local_v * v_axis[0] + local_n * normal[0]
            global_y = local_u * u_axis[1] + local_v * v_axis[1] + local_n * normal[1]
            global_z = local_u * u_axis[2] + local_v * v_axis[2] + local_n * normal[2]

            sampled, in_range = _bilinear_sample_regular_grid(
                spectrum,
                global_x,
                global_y,
                float(fx[0]),
                delta_fx,
                float(fy[0]),
                delta_fy,
            )
            valid = (propagating > 0.0) & (local_n > wave_frequency * 1e-12) & (global_z > 0.0) & in_range

            jacobian = np.zeros_like(local_n)
            np.divide(global_z, local_n, out=jacobian, where=valid)
            optical_cycles = global_x * center_x_m + global_y * center_y_m + global_z * distance_m
            phase = np.exp(1j * np.remainder(TWO_PI * optical_cycles, TWO_PI))
            output_spectrum[start:start + chunk_rows] = np.where(valid, sampled * jacobian * phase, 0.0)
    else:
        global_x = fx[None, :]
        for start in range(0, height, chunk_rows):
            global_y = fy[start:start + chunk_rows, None]
            propagating = wave_frequency * wave_frequency - global_x * global_x - global_y * global_y
            global_z = np.sqrt(np.maximum(propagating, 0.0))

            local_u = global_x * u_axis[0] + global_y * u_axis[1] + global_z * u_axis[2]
            local_v = global_x * v_axis[0] + global_y * v_axis[1] + global_z * v_axis[2]
            local_n = global_x * normal[0] + global_y * normal[1] + global_z * normal[2]

            sampled, in_range = _bilinear_sample_regular_grid(
                spectrum,
                local_u,
                local_v,
                float(fx[0]),
                delta_fx,
                float(fy[0]),
                delta_fy,
            )
            valid = (propagating > 0.0) & (global_z > wave_frequency * 1e-12) & (local_n > 0.0) & in_range

            jacobian = np.zeros_like(global_z)
            np.divide(local_n, global_z, out=jacobian, where=valid)
            optical_cycles = global_x * center_x_m + global_y * center_y_m + global_z * distance_m
            phase = np.exp(-1j * np.remainder(TWO_PI * optical_cycles, TWO_PI))
            output_spectrum[start:start + chunk_rows] = np.where(valid, sampled * jacobian * phase, 0.0)

    return _field_from_centered_spectrum(output_spectrum)


def simulate_phase_tilted(
    phase_rad,
    pixel_size_nm,
    wavelength_nm,
    distance_mm,
    pan_deg=0.0,
    tilt_deg=0.0,
    center_x_mm=0.0,
    center_y_mm=0.0,
):
    field = np.exp(1j * wrap_phase(phase_rad))
    propagated = tilted_angular_spectrum_propagate(
        field,
        pixel_size_nm,
        wavelength_nm,
        distance_mm,
        pan_deg=pan_deg,
        tilt_deg=tilt_deg,
        center_x_mm=center_x_mm,
        center_y_mm=center_y_mm,
    )
    return normalize_intensity_uint16(propagated)


def gerchberg_saxton_tilted_phase(
    target_intensity,
    pixel_size_nm,
    wavelength_nm,
    distance_mm,
    pan_deg=0.0,
    tilt_deg=0.0,
    center_x_mm=0.0,
    center_y_mm=0.0,
    iterations=50,
    seed=0,
    progress_callback=None,
):
    """Gerchberg-Saxton iteration for a physically tilted destination plane."""
    pan_deg = float(pan_deg)
    tilt_deg = float(tilt_deg)

    # Preserve the historical result bit-for-bit when the target is parallel.
    if abs(pan_deg) < 1e-12 and abs(tilt_deg) < 1e-12:
        from gdoesii_doe import gerchberg_saxton_phase

        return gerchberg_saxton_phase(
            target_intensity,
            pixel_size_nm,
            wavelength_nm,
            distance_mm,
            iterations=iterations,
            seed=seed,
            progress_callback=progress_callback,
        )

    sampling = tilted_plane_sampling_info(pixel_size_nm, wavelength_nm, pan_deg, tilt_deg)
    if sampling["sampling_warning"] and "Aliasing" in sampling["sampling_warning"]:
        raise ValueError(
            sampling["sampling_warning"]
            + " Reduce pan/tilt, reduce pixel size, or increase wavelength."
        )

    target = np.asarray(target_intensity, dtype=np.float64)
    if target.ndim != 2:
        raise ValueError("Target intensity must be a 2-D array.")
    if not np.any(target > 0):
        raise ValueError("Target intensity contains no non-zero values.")

    iterations = int(iterations)
    if iterations < 1:
        raise ValueError("Gerchberg-Saxton iterations must be at least 1.")

    target = np.clip(target, 0.0, None)
    target /= float(np.max(target))
    target_amplitude = np.sqrt(target)

    rng = np.random.default_rng(int(seed))
    source_field = np.exp(1j * rng.uniform(0.0, TWO_PI, target.shape))

    for iteration in range(iterations):
        target_field = tilted_angular_spectrum_propagate(
            source_field,
            pixel_size_nm,
            wavelength_nm,
            distance_mm,
            pan_deg=pan_deg,
            tilt_deg=tilt_deg,
            center_x_mm=center_x_mm,
            center_y_mm=center_y_mm,
        )
        target_field = target_amplitude * np.exp(1j * np.angle(target_field))

        source_back = tilted_angular_spectrum_propagate(
            target_field,
            pixel_size_nm,
            wavelength_nm,
            distance_mm,
            pan_deg=pan_deg,
            tilt_deg=tilt_deg,
            center_x_mm=center_x_mm,
            center_y_mm=center_y_mm,
            inverse=True,
        )
        if not np.any(np.abs(source_back) > 0):
            raise ValueError(
                "Tilted-plane propagation produced no sampled spectrum; reduce pan/tilt or pixel size."
            )
        source_field = np.exp(1j * np.angle(source_back))
        if progress_callback is not None:
            progress_callback(iteration + 1, iterations)

    phase = wrap_phase(np.angle(source_field))
    simulation = simulate_phase_tilted(
        phase,
        pixel_size_nm,
        wavelength_nm,
        distance_mm,
        pan_deg=pan_deg,
        tilt_deg=tilt_deg,
        center_x_mm=center_x_mm,
        center_y_mm=center_y_mm,
    )
    return phase, simulation
