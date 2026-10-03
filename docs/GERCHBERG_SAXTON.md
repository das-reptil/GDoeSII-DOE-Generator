# Arbitrary Image / Gerchberg-Saxton DOE mode

The `Arbitrary Image (GS)` generator synthesizes a phase-only DOE for a user-supplied target-intensity image using an iterative Gerchberg-Saxton algorithm.

For parallel target planes (`Target pan = 0`, `Target tilt = 0`) the historical Fresnel forward/back propagation is retained. For a physically tilted target plane, the solver uses rotated-angular-spectrum propagation between the DOE plane and the tilted target plane.

## Purpose

Unlike the analytical generators (`Lens`, `Grating`, `Fresnel Zone Plate`, `Vortex`), this mode does not start from a closed-form phase function. Instead, it searches iteratively for a phase pattern that produces a desired intensity distribution in a target plane.

Typical examples include:

- logos,
- symbols,
- text-like patterns,
- simple images,
- structured illumination patterns,
- custom laser-processing intensity distributions,
- experimental holographic target fields.

## Iterative principle

The implementation alternates between DOE plane and target plane:

1. start with a phase-only source field,
2. propagate to the target plane,
3. replace the target-plane amplitude with the desired target amplitude,
4. propagate back to the DOE plane,
5. keep only the resulting phase,
6. repeat for the selected number of iterations.

The final DOE remains phase-only.

With `pan = 0` and `tilt = 0`, steps 2 and 4 use the established same-sampling Fresnel propagator. With non-zero pan or tilt, the propagation is performed between the DOE plane and the actual tilted target plane using a rotated angular spectrum.

## Relevant GUI parameters

```text
Type:                    Arbitrary Image (GS)
Width / Height:          DOE calculation raster
Pixel size (nm):         physical sampling pitch
Wavelength (nm):         design wavelength
Focal / target z (mm):   Z coordinate of target-plane centre
GS iterations:           number of forward/back iterations
GS target width (um):    physical target width; 0 = auto fit
Select target image:     desired target-intensity image
Target X/Y offset (mm):  lateral target-plane centre, in distance mode
Target pan (deg):        target-plane rotation about global Y
Target tilt (deg):       target-plane rotation about global X
```

## Target image

The imported image is converted to grayscale intensity, normalized and centered in the local target-plane calculation window.

The physical target size is controlled separately from the image file resolution.

This is important: a `1000 x 500` input image does not mean a `1000 x 500 um` optical target. The optical target dimensions are defined by the DOE calculation grid, pixel size and `GS target width` setting.

If the target plane is tilted, the image still lives in the **local coordinates of that physical target plane**. It is not merely perspective-warped inside a parallel numerical plane.

## Physical target size

`GS target width (um; 0=fit)` controls the desired physical target width.

- `0` keeps the legacy auto-fit behavior.
- a positive value requests a physical width in micrometres.
- target height follows from the source-image aspect ratio.
- the result is quantized to whole target-plane pixels.

Example:

```text
DOE raster:          512 x 512 px
Pixel size:          500 nm
Target image ratio:  2:1
GS target width:     80 um
```

results in approximately

```text
Target raster:       160 x 80 px
Target size:         80 x 40 um
```

See [`GS_TARGET_SIZE.md`](GS_TARGET_SIZE.md) for details.

## GS iterations

`GS iterations` sets the number of optimization cycles.

More iterations can improve convergence, but not indefinitely. Increasing iterations cannot compensate for poor physical sampling or an impossible target.

A useful initial value is:

```text
50 iterations
```

For development it is often faster to test with a smaller raster and moderate iteration count before moving to a large final design.

## Target-plane position and orientation

The physical pose of the target plane is described by its centre and orientation.

For `Target-plane distance` steering mode, the centre is

```text
C = (Target X offset, Target Y offset, Focal / target z)
```

Pan and tilt then rotate the local target-plane basis about this centre.

Conventions:

```text
+X = right
+Y = increasing image rows
+Z = from DOE toward target
positive pan  -> target normal turns toward +X
positive tilt -> target normal turns toward -Y
rotation order: tilt around X, then pan around Y
```

At `pan = 0`, `tilt = 0`, the target plane is parallel to the DOE plane.

For a tilted target, translation to the target centre is included in the tilted propagation. The normal off-axis steering ramp is therefore not added a second time.

See [`TARGET_PLANE_PAN_TILT.md`](TARGET_PLANE_PAN_TILT.md) for the full geometry, sampling rules and numerical method.

## Typical use cases

This mode is useful for:

- arbitrary beam shaping,
- holographic projection of simple intensity patterns,
- structured illumination,
- projecting logos or registration marks,
- distributing optical power into non-analytical shapes,
- custom laser-writing or exposure patterns,
- optical trapping landscapes with several bright regions,
- research on phase-only computer-generated holograms,
- projection onto physically inclined surfaces.

## Target position versus target size

The target size, target centre and target orientation are independent concepts.

For example:

```text
GS target width: 80 um
Target X:        100 mm
Target Y:        100 mm
Target z:        350 mm
Target pan:      15 deg
Target tilt:     -5 deg
```

means that the GS solver synthesizes an `80 um`-wide local target image on a plane centred at the specified 3-D coordinate and physically rotated by the requested pan and tilt.

With `pan = tilt = 0`, the established off-axis behaviour remains conceptually

```text
phi_export = wrap(phi_GS + phi_steering)
```

For a tilted GS target, the target displacement and target orientation are included together in the tilted-plane propagation instead of being represented as a separate second steering ramp.

## Simulation preview

The intensity preview is shown in local target-plane coordinates.

For large off-axis targets the preview therefore remains centered instead of disappearing far outside the numerical display window. With pan/tilt, the preview corresponds to the field evaluated on the inclined physical target plane.

## Input-image considerations

Best results are generally obtained with targets that are compatible with the available spatial bandwidth and aperture.

Difficult targets include:

- very fine isolated features,
- abrupt high-frequency detail near the sampling limit,
- targets much smaller than a few raster pixels,
- highly complex targets on a very small DOE aperture.

A clean high-contrast grayscale target is usually a good starting point.

## Sampling and achievable detail

The target resolution is limited by the numerical and physical system, including:

- DOE width and height,
- DOE pixel size,
- wavelength,
- propagation distance,
- physical DOE aperture,
- target size,
- target pan and tilt,
- input-beam amplitude profile.

The program rejects targets that do not fit inside the sampled target-plane field, but a target can still be numerically legal and optically poorly resolved if its features are too fine.

Tilting a sampled plane introduces an additional spatial-frequency carrier. The GUI reports a carrier-sampling estimate. Below 3 pixels per carrier period the configuration is flagged as marginal; when Nyquist is reached or exceeded, the tilted GS calculation is rejected.

## Off-axis steering

The mode can be combined with either off-axis method:

- `Angle`,
- `Target-plane distance`.

For parallel target planes, the existing steering-ramp sampling checks apply as before.

For a tilted target used with `Target-plane distance`, the target centre translation is part of the tilted propagation so the lateral displacement is not applied twice.

## GrayScribeX export

The final GS phase can be exported as a true 16-bit phase map and as a GrayScribeX-oriented relative height map.

The JSON metadata includes:

- target file,
- GS iteration count,
- requested and actual target size,
- target raster dimensions,
- target placement,
- off-axis geometry,
- target-plane centre,
- target pan and tilt,
- local target-plane basis vectors,
- target-plane normal,
- tilted-plane sampling information,
- 3-D coordinates of all four image-target corners,
- wavelength and sampling parameters.

The relief conversion again uses

```text
Delta n = n_DOE - n_environment
h_2pi = lambda / Delta n
```

## Important limitations

The current Gerchberg-Saxton implementation is a scalar phase-only design method. It does not guarantee a unique or globally optimal solution.

The displayed simulation assumes a uniform source amplitude. A real Gaussian input beam can change the resulting intensity pattern.

The tilted-plane solver uses rotated angular-spectrum interpolation. As with every sampled diffraction method, large tilts and spectra close to the numerical bandwidth limit require particular care. The central carrier sampling check is useful but does not by itself guarantee that the entire field spectrum is alias-free.

The algorithm also does not directly model:

- polarization,
- vector diffraction,
- fabrication errors,
- material absorption,
- machine exposure nonlinearity,
- rigorous electromagnetic effects.

For demanding applications, experimental feedback or a more advanced optimization method may be useful after the initial GS design.
