# Target-plane pan / tilt

The DOE Generator can model a target plane that is not parallel to the DOE plane.
This is a general optical target-plane feature and is independent of any rotating-disc or animation workflow.

## GUI parameters

- `Target pan (deg)` rotates the target plane around the global vertical Y axis.
- `Target tilt (deg)` rotates the target plane around the global horizontal X axis.
- `0 / 0 deg` keeps the historical parallel-plane behaviour.
- Target X/Y displacement continues to come from the existing off-axis steering controls.
- `Focal / target z (mm)` is the Z coordinate of the target-plane centre.

Coordinate convention:

- +X: right
- +Y: increasing image rows
- +Z: from DOE towards the target
- positive pan turns the target normal towards +X
- positive tilt turns the target normal towards -Y
- rotation order: tilt around X, then pan around Y

## Gerchberg-Saxton targets

For `Arbitrary Image (GS)`, non-zero pan or tilt switches the iterative propagation to a rotated angular-spectrum calculation. The forward and backward GS steps therefore propagate between the DOE plane and the physically tilted target plane rather than merely perspective-warping the target bitmap.

The target centre can also be off axis. In this case the translation to the target centre is included in the tilted propagation itself, so an additional steering ramp is not applied a second time.

For exactly `pan = 0` and `tilt = 0`, the legacy same-sampling Fresnel GS path is retained unchanged.

## Other generator modes

Analytic generators such as Lens, Grating, Fresnel Zone Plate and Vortex retain their analytic phase definition. If pan/tilt is non-zero, the simulation preview is evaluated on the tilted target plane. This is useful for inspecting the field on that physical plane without redefining the analytic optical element.

## Geometry and metadata

The exported metadata contains a `target_plane` section with:

- target centre `[X, Y, Z]` in mm
- pan and tilt angles
- local U and V basis vectors
- target-plane normal vector
- sampling information and warnings
- for GS image targets, the 3-D coordinates of all four target corners

The GUI also displays the target normal and the minimum pixels per tilt-carrier period.

## Sampling limits

Tilting a sampled plane introduces a spatial-frequency carrier. The GUI estimates its sampling and reports:

- a warning below 3 pixels per carrier period
- an aliasing warning when the carrier reaches or exceeds the Nyquist frequency

An aliased tilted GS calculation is rejected. Reducing pan/tilt, using a smaller DOE pixel size, or increasing wavelength increases the available angular sampling range.

The carrier check describes the central on-axis component. A real DOE also has spectral bandwidth, so configurations close to the warning limit should be validated by simulation and, ultimately, experiment.

## Numerical method

The implementation uses coordinate rotation of the angular spectrum followed by bilinear spectrum interpolation and the appropriate spectral Jacobian for forward and reverse propagation. The approach follows the rotated-angular-spectrum family of methods described by K. Matsushima, H. Schimmel and F. Wyrowski, *Fast calculation method for optical diffraction on tilted planes by use of the angular spectrum of plane waves*, JOSA A 20(9), 1755-1762 (2003), DOI: 10.1364/JOSAA.20.001755.
