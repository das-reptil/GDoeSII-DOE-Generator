# DOE Generator parameter reference

This document describes the user-facing parameters of the standalone **GDoeSII DOE Generator**, their physical meaning, units and practical interactions.

## DOE type

`Type` selects the phase element to generate:

- `Lens` – continuous wrapped quadratic phase profile.
- `Grating` – continuous blazed phase ramp.
- `Fresnel Zone Plate` – binary `0 / pi` phase zones.
- `Vortex` – azimuthal phase profile with selectable topological charge.
- `Vortex + Lens` – focused vortex combining the azimuthal vortex phase with the quadratic lens phase.
- `Arbitrary Image (GS)` – phase-only DOE synthesized for an arbitrary target-intensity image using Gerchberg-Saxton iterations.

Only parameters relevant to the selected generator affect the generated phase.

## Width (px) / Height (px)

These values define the number of pixels in the calculated DOE phase map.

The physical DOE size is

```text
DOE width  = width_px  * pixel_size_nm / 1000   [um]
DOE height = height_px * pixel_size_nm / 1000   [um]
```

Example:

```text
Width:       512 px
Height:      512 px
Pixel size:  500 nm

Physical DOE size: 256 x 256 um
```

Larger arrays improve the available spatial extent and numerical sampling but increase memory use and Gerchberg-Saxton computation time.

## Pixel size (nm)

`Pixel size (nm)` is the physical sampling pitch of the DOE.

It affects:

- the physical DOE dimensions,
- Fresnel propagation,
- grating and lens sampling,
- off-axis phase-ramp sampling,
- tilted target-plane sampling,
- the physical size of an Arbitrary Image target,
- the physical dimensions recorded in export metadata.

For off-axis designs the program reports the number of DOE pixels per steering-ramp period. A diagonal ramp below 3 pixels/period is flagged as marginal and below 2 pixels/period as aliasing.

For non-zero target pan/tilt, the GUI also reports a target-plane carrier sampling estimate. Configurations at or beyond Nyquist are rejected for the tilted GS solver.

## Wavelength (nm)

`Wavelength (nm)` is the design wavelength in vacuum/air units used by the scalar phase calculations.

It affects:

- lens phase,
- Fresnel zone plate phase,
- Fresnel propagation,
- tilted target-plane propagation,
- focused Vortex + Lens designs,
- off-axis steering ramp,
- phase-to-relief conversion for GrayScribeX-oriented export.

The same design wavelength should therefore be used consistently for DOE synthesis and the intended optical application.

## Focal / target z (mm)

This field is shared by several generator modes:

- `Lens` – focal length.
- `Fresnel Zone Plate` – focal length.
- `Vortex + Lens` – focal length of the combined focused-vortex DOE.
- `Arbitrary Image (GS)` – axial coordinate of the target-plane centre.
- `Target-plane distance` off-axis mode – axial target coordinate `z`.

The current GUI requires a positive value.

For `Vortex + Lens`, the local simulation is evaluated at this focal distance. For a suitable input field, the resulting focal-plane intensity is expected to show the characteristic dark center and ring-like / donut distribution of a focused optical vortex.

For a GS target with `Target pan = 0` and `Target tilt = 0`, the target image is synthesized in the historical parallel plane at this propagation distance. For a tilted target, the same value is the Z coordinate of the target-plane centre.

## Grating period (um)

Used only for `Grating`.

This is the physical period of one complete `0 ... 2*pi` blazed phase ramp.

Smaller periods produce larger diffraction angles but require finer DOE sampling. The period should contain enough DOE pixels to represent the phase ramp adequately.

Approximate pixels per grating period:

```text
pixels_per_period = grating_period_um / (pixel_size_nm / 1000)
```

## Grating angle (deg)

Used only for `Grating`.

This rotates the grating vector in the DOE plane. `0 deg` produces a phase variation along the X direction; other angles rotate the phase ramp accordingly.

## Vortex charge

Used by `Vortex` and `Vortex + Lens`.

The integer topological charge controls the azimuthal phase winding:

```text
phi_vortex = charge * atan2(y, x)
```

A charge of zero is not allowed. The sign changes the handedness of the vortex phase.

Examples:

```text
charge = +1   one positive 2*pi phase winding
charge = +2   two positive phase windings
charge = -1   one winding with opposite handedness
```

### Vortex

The pure `Vortex` mode generates only the azimuthal phase term. It is useful if focusing is supplied by another optical element or if the vortex phase is part of a larger optical setup.

Typical applications include OAM mode generation, structured illumination, optical manipulation, phase-singularity experiments and mode conversion.

### Vortex + Lens

`Vortex + Lens` combines focusing and vortex generation in one phase profile:

```text
phi_total = wrap(phi_lens + phi_vortex)
```

with

```text
phi_lens = -pi * (x^2 + y^2) / (lambda * f)
```

The `Focal / target z` value is used as focal length `f`.

Typical applications include focused donut beams, optical tweezers, particle manipulation/rotation, ring-shaped laser processing, OAM experiments, structured illumination and vortex-based microscopy.

See [`VORTEX.md`](VORTEX.md) for a more detailed explanation and examples.

## GS iterations

Used only for `Arbitrary Image (GS)`.

This is the number of Gerchberg-Saxton forward/backward propagation cycles.

Higher values can improve convergence but increase computation time. A moderate value such as `50` is a useful starting point; the optimum depends on target complexity, sampling and propagation distance.

## GS target width (um; 0=fit)

Used only for `Arbitrary Image (GS)`.

This controls the physical width of the desired target image in the local target plane.

- `0` – legacy auto-fit mode: the target image is fitted as large as possible into the complete calculation window while preserving its aspect ratio.
- `> 0` – the requested physical target width in micrometres. The target height follows automatically from the source-image aspect ratio.

The requested dimensions are quantized to whole target-plane pixels. The actual physical size written to metadata can therefore differ slightly from the requested value.

Example:

```text
DOE:             512 x 512 px
Pixel size:      500 nm
Calculation field: 256 x 256 um
Target image:    2:1 aspect ratio
GS target width: 80 um

Target raster:   160 x 80 px
Actual target:   80 x 40 um
```

A requested target that does not fit inside the sampled target plane is rejected.

See also [`GS_TARGET_SIZE.md`](GS_TARGET_SIZE.md).

## Target image

`Select target image` is used only for `Arbitrary Image (GS)`.

The image is converted to grayscale intensity. It is resized while preserving aspect ratio, centered in the local target calculation field and normalized before Gerchberg-Saxton synthesis.

The physical target size is controlled separately by `GS target width`.

## Off-axis steering mode

The generator supports three steering modes:

### None

No steering phase ramp is added. The DOE remains on-axis.

### Angle

The user supplies projected steering angles `Theta X` and `Theta Y` in degrees.

The program converts these to normalized direction cosines and adds a linear phase ramp.

### Target-plane distance

The user supplies the physical target coordinates:

```text
Target X offset (mm)
Target Y offset (mm)
Focal / target z (mm)
```

The exact normalized direction is calculated from

```text
r  = sqrt(x^2 + y^2 + z^2)
sx = x / r
sy = y / r
sz = z / r
```

and the steering phase is

```text
phi_offset(X,Y) = 2*pi/lambda * (sx*X + sy*Y)
```

This separates **target position** from **target size**: for example a GS image can be 80 um wide while being directed to a point at `x=100 mm`, `y=100 mm`, `z=350 mm`.

For `Vortex + Lens`, off-axis steering adds a third phase contribution:

```text
phi_export = wrap(phi_lens + phi_vortex + phi_steering)
```

This can direct a focused vortex spot away from the optical axis.

For a tilted GS target in `Target-plane distance` mode, target translation is included in the tilted propagation itself so the steering ramp is not applied a second time.

## Theta X (deg) / Theta Y (deg)

Used in `Angle` off-axis mode.

These are projected steering angles relative to the optical axis in the X-Z and Y-Z planes.

The GUI also reports the resulting total steering angle and steering-ramp sampling.

## Target X offset (mm) / Target Y offset (mm)

Used in `Target-plane distance` mode.

These define the physical lateral target-plane centre at the selected axial coordinate `z`.

The program reports:

- projected X/Y angles,
- total angle,
- ray length,
- diagonal steering-ramp period,
- pixels per steering-ramp period,
- sampling warnings when appropriate.

When target pan/tilt is non-zero, these values define the **centre of the tilted plane**, not merely a point to which an otherwise parallel plane is steered.

## Target pan (deg) / Target tilt (deg)

These parameters orient the target plane in 3-D.

- `Target pan (deg)` rotates the target plane around the global Y axis.
- `Target tilt (deg)` rotates it around the global X axis.
- `0 / 0 deg` reproduces the historical parallel-plane behaviour.

Coordinate convention:

```text
+X = right
+Y = increasing image rows
+Z = from DOE toward target
```

Sign convention:

```text
positive pan  -> target normal turns toward +X
positive tilt -> target normal turns toward -Y
```

Rotation order is tilt around X followed by pan around Y.

For `Arbitrary Image (GS)`, a non-zero pan or tilt switches the iterative forward/back propagation to the rotated-angular-spectrum tilted-plane solver. The imported target image is therefore interpreted in the local coordinates of the tilted physical plane rather than being perspective-warped in a parallel plane.

For analytical modes (`Lens`, `Grating`, `Fresnel Zone Plate`, `Vortex`, `Vortex + Lens`), the analytic phase definition is not changed by pan/tilt. If pan/tilt is non-zero, the simulation preview is evaluated on the tilted plane.

The GUI reports the target-plane normal and carrier sampling. A tilted GS configuration that exceeds the supported Nyquist sampling is rejected.

For details, equations, metadata and numerical-method notes see [`TARGET_PLANE_PAN_TILT.md`](TARGET_PLANE_PAN_TILT.md).

## DOE index

`DOE index` is the refractive index of the fabricated DOE material used for phase-to-relief conversion.

It does not alter the phase synthesis itself; it affects the physical height map exported for GrayScribeX-oriented fabrication.

## Environment index

`Environment index` is the refractive index of the medium surrounding the DOE in the intended optical application.

It is **not fixed to air**. This allows the physical relief to be calculated for immersion or other surrounding media.

The relevant refractive-index contrast is

```text
Delta n = n_DOE - n_environment
```

The current implementation requires `n_DOE > n_environment` for the positive relief mapping.

## Phase-to-relief conversion

For a phase value `phi`, the relative height is calculated as

```text
h = phi * lambda / (2*pi*Delta n)
```

For a full `2*pi` phase span:

```text
h_2pi = lambda / Delta n
```

Example:

```text
lambda        = 633 nm
n_DOE         = 1.52
n_environment = 1.00
Delta n       = 0.52
h_2pi         = 1217.31 nm
```

If the environment has `n = 1.33` instead of air, the same material gives a smaller `Delta n` and therefore requires a larger physical relief for the same `2*pi` phase range.

## Save 16-bit Phase PNG

This exports the generated wrapped phase map as a true unsigned 16-bit PNG:

```text
gray 0        -> 0 rad
gray ~32768   -> pi rad
gray 65535    -> approximately 2*pi
```

A JSON sidecar stores generator, sampling and off-axis parameters. For GS targets it also stores the requested and actual target geometry. When pan/tilt is used it additionally stores target-plane orientation, basis/normal vectors and, for GS image targets, 3-D corner coordinates. For `Vortex + Lens` it stores the vortex charge, focal length and the combined `lens + vortex` phase type.

## Export GrayScribeX

This exports the current DOE as a true unsigned 16-bit grayscale height map together with JSON metadata.

The export includes, where applicable:

- wavelength,
- DOE/material refractive index,
- environment refractive index,
- `Delta n`,
- phase span,
- maximum relief height,
- DOE pixel pitch,
- DOE physical dimensions,
- generator parameters,
- Vortex charge and focused-vortex focal length,
- GS target geometry,
- off-axis target geometry and steering sampling,
- target-plane centre, pan/tilt, basis vectors, normal and sampling information.

The generator provides the desired relative physical topography. Machine-specific grayscale-to-exposure calibration remains the responsibility of GrayScribeX / the lithography system.

## Practical parameter interactions

Several parameters should be considered together rather than independently:

- **Width/height + pixel size** determine the physical DOE aperture and target calculation field.
- **Pixel size + wavelength + off-axis angle** determine whether the steering ramp is adequately sampled.
- **Pixel size + wavelength + target pan/tilt** determine whether the tilted-plane angular-spectrum carrier is adequately sampled.
- **Target X/Y/Z + pan/tilt** define the complete 3-D target-plane pose.
- **Pixel size + GS target width** determine the number of raster pixels across the requested target.
- **Wavelength + DOE index + environment index** determine the required physical relief height.
- **Target z + DOE aperture + wavelength** influence the spatial scale and quality achievable in Fresnel propagation.
- **Vortex charge + aperture + focal length + input-beam amplitude** influence the structure of a focused vortex field.
- **GS iterations** affect convergence but cannot compensate for inadequate spatial sampling.

The GUI reports the most important derived values and rejects physically or numerically incompatible inputs where implemented.
