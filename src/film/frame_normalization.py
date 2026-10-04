import math


def brightness_compensation(rows, mode="constant reconstructed brightness", geometric_gamma=0.5):
    """Add recommended per-frame attenuation factors to simulation metrics.

    A phase-only GS target is internally normalized, so multiplying an entire
    target bitmap by a scalar does not change the generated phase. Therefore
    brightness equalization is expressed as a recommended external laser/duty
    factor that only attenuates brighter frames down to the least-efficient
    valid frame. No claim is made that this factor is applied by the DOE itself.
    """
    rows = [dict(row) for row in rows]
    efficiencies = [
        float(row.get("target_power_fraction", 0.0))
        for row in rows
        if float(row.get("target_power_fraction", 0.0)) > 0.0
    ]
    reference = min(efficiencies) if efficiencies else 0.0

    for row in rows:
        efficiency = float(row.get("target_power_fraction", 0.0))
        if reference > 0.0 and efficiency > 0.0:
            equalization = min(1.0, reference / efficiency)
        else:
            equalization = 0.0

        angle = float(row.get("frame_angle_deg", 0.0))
        geometric_factor = 1.0
        if mode == "preserve geometric brightness":
            geometric_factor = abs(math.cos(math.radians(angle))) ** float(geometric_gamma)
        elif mode == "analysis only":
            equalization = 1.0

        row["brightness_reference_power_fraction"] = reference
        row["recommended_equalization_factor"] = equalization
        row["geometric_brightness_factor"] = geometric_factor
        row["recommended_laser_or_duty_factor"] = equalization * geometric_factor

    return rows
