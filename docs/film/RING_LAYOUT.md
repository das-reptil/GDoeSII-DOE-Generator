# Film ring layout

The batch generator writes `layout/DOE_ring_layout.csv` for the generated DOE sequence.

## Automatic radius

If `Ring radius (mm)` is `0`, the radius is calculated from frame count and tangential center-to-center pitch:

```text
R = frame_count * pitch / (2*pi)
```

For the current 48-frame concept with a 2.5 mm pitch:

```text
frame_count = 48
pitch       = 2.5 mm
circumference = 120 mm
R = 19.0986 mm
```

## DOE center coordinates

Frame `i` is placed at

```text
alpha_i = i * 360 / frame_count
x_i = R * cos(alpha_i)
y_i = R * sin(alpha_i)
```

Coordinates are relative to the disc center.

## Orientation modes

Three layout orientations are available:

- `radial` – DOE rotation angle equals the sector angle.
- `tangential` – DOE rotation angle equals sector angle + 90 degrees.
- `fixed` – all DOE fields keep 0 degree orientation.

The CSV contains:

```text
frame
frame_name
doe_name
center_x_mm
center_y_mm
sector_angle_deg
rotation_deg
orientation
ring_radius_mm
ring_pitch_mm
```

The ring layout is deliberately a separate layout-stage description. The GS calculation itself is performed in the local DOE coordinate system and is not rotated merely because the finished DOE will later be positioned around a disc.
