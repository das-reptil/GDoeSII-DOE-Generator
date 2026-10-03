# Generator modes

This page is the central index for the DOE Generator modes and their detailed documentation.

## Analytical generators

### Lens

A continuous quadratic phase profile for diffractive focusing.

Typical uses: compact focusing, micro-optics, detector/fiber illumination, laser processing and off-axis focal spots.

See [`LENS.md`](LENS.md).

### Grating

A continuous blazed linear phase ramp with configurable period and orientation.

Typical uses: beam steering, diffraction-order control, alignment/calibration and Fourier-optics experiments.

See [`GRATING.md`](GRATING.md).

### Fresnel Zone Plate

A binary `0 / pi` phase zone plate for diffractive focusing.

Typical uses: simple binary fabrication, micro-optical focusing, wavelength-dependent focusing and comparison with continuous-phase lenses.

See [`FRESNEL_ZONE_PLATE.md`](FRESNEL_ZONE_PLATE.md).

### Vortex

An azimuthal phase profile with integer topological charge.

Typical uses: optical vortices, OAM/mode conversion, structured illumination, optical manipulation and particle rotation.

### Vortex + Lens

A combined focusing lens and vortex phase profile.

Typical uses: focused donut beams, optical tweezers, ring-shaped laser processing, focused OAM beams and vortex-based structured illumination.

See [`VORTEX.md`](VORTEX.md) for both vortex modes.

## Iterative generator

### Arbitrary Image (GS)

A phase-only computer-generated hologram synthesized from an arbitrary target-intensity image using Gerchberg-Saxton iterations.

For a parallel target plane, the existing Fresnel forward/back propagation is used. With non-zero target pan or tilt, the GS loop propagates between the DOE plane and the physically inclined target plane using rotated-angular-spectrum propagation.

Typical uses: logos, symbols, custom illumination, holographic target fields, non-analytical laser-processing patterns and projection onto inclined surfaces.

See [`GERCHBERG_SAXTON.md`](GERCHBERG_SAXTON.md).

Physical target-size control is documented separately in [`GS_TARGET_SIZE.md`](GS_TARGET_SIZE.md).

## Common target geometry

Target position and target orientation are separate concepts.

The target centre can be displaced from the optical axis by the existing off-axis controls. The target plane can additionally be oriented in 3-D with:

```text
Target pan (deg)
Target tilt (deg)
```

`0 / 0 deg` keeps the historical parallel-plane behaviour.

For analytical generators, pan/tilt affects the target-plane simulation preview but does not redefine the analytic phase function. For `Arbitrary Image (GS)`, non-zero pan/tilt changes the forward/back propagation used during the iterative synthesis itself.

See [`TARGET_PLANE_PAN_TILT.md`](TARGET_PLANE_PAN_TILT.md) for the geometry, conventions, sampling limits and numerical method.

## Common parameters

All generator modes share at least some of the following concepts:

- DOE raster width/height,
- physical pixel pitch,
- wavelength,
- optional off-axis steering,
- optional target-plane pan/tilt,
- 16-bit phase-map export,
- DOE/environment refractive-index contrast,
- GrayScribeX-oriented phase-to-relief export.

See [`PARAMETERS.md`](PARAMETERS.md) for the complete parameter reference.

## Choosing a mode

A simple rule of thumb:

- need one focal spot -> `Lens`
- need a controlled linear phase gradient / diffraction angle -> `Grating`
- need simple binary focusing -> `Fresnel Zone Plate`
- need helical phase / OAM -> `Vortex`
- need a focused donut / vortex spot -> `Vortex + Lens`
- need an arbitrary intensity image -> `Arbitrary Image (GS)`

Off-axis steering can be added independently when the generated field should be directed away from the optical axis. Target-plane pan/tilt can be added independently when the field should be evaluated or synthesized on a physically inclined plane.
