# Arbitrary Image / Gerchberg-Saxton DOE mode

The `Arbitrary Image (GS)` generator synthesizes a phase-only DOE for a user-supplied target-intensity image using an iterative Gerchberg-Saxton algorithm with Fresnel forward/back propagation.

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

## Relevant GUI parameters

```text
Type:                    Arbitrary Image (GS)
Width / Height:          DOE calculation raster
Pixel size (nm):         physical sampling pitch
Wavelength (nm):         design wavelength
Focal / target z (mm):   propagation distance to target plane
GS iterations:           number of forward/back iterations
GS target width (um):    physical target width; 0 = auto fit
Select target image:     desired target-intensity image
```

## Target image

The imported image is converted to grayscale intensity, normalized and centered in the local target-plane calculation window.

The physical target size is controlled separately from the image file resolution.

This is important: a `1000 x 500` input image does not mean a `1000 x 500 um` optical target. The optical target dimensions are defined by the DOE calculation grid, pixel size and `GS target width` setting.

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

## Typical use cases

This mode is useful for:

- arbitrary beam shaping,
- holographic projection of simple intensity patterns,
- structured illumination,
- projecting logos or registration marks,
- distributing optical power into non-analytical shapes,
- custom laser-writing or exposure patterns,
- optical trapping landscapes with several bright regions,
- research on phase-only computer-generated holograms.

## Target position versus target size

The target size and target position are independent.

For example:

```text
GS target width: 80 um
Target X:        100 mm
Target Y:        100 mm
Target z:        350 mm
```

means that the GS algorithm synthesizes the local `80 um`-wide image, while the off-axis steering ramp directs that local target field toward the specified physical direction.

The exported phase is conceptually

```text
phi_export = wrap(phi_GS + phi_steering)
```

## Simulation preview

The intensity preview is shown in local target coordinates.

For large off-axis targets the preview therefore remains centered instead of disappearing far outside the numerical display window. The exported phase map still contains the steering ramp.

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
- input-beam amplitude profile.

The program rejects targets that do not fit inside the sampled target-plane field, but a target can still be numerically legal and optically poorly resolved if its features are too fine.

## Off-axis steering

The mode can be combined with either off-axis method:

- `Angle`,
- `Target-plane distance`.

The same steering-ramp sampling checks apply as for the analytical generator modes.

## GrayScribeX export

The final GS phase can be exported as a true 16-bit phase map and as a GrayScribeX-oriented relative height map.

The JSON metadata includes:

- target file,
- GS iteration count,
- requested and actual target size,
- target raster dimensions,
- target placement,
- off-axis geometry,
- wavelength and sampling parameters.

The relief conversion again uses

```text
Delta n = n_DOE - n_environment
h_2pi = lambda / Delta n
```

## Important limitations

The current Gerchberg-Saxton implementation is a scalar phase-only design method. It does not guarantee a unique or globally optimal solution.

The displayed simulation assumes a uniform source amplitude. A real Gaussian input beam can change the resulting intensity pattern.

The algorithm also does not directly model:

- polarization,
- vector diffraction,
- fabrication errors,
- material absorption,
- machine exposure nonlinearity,
- rigorous electromagnetic effects.

For demanding applications, experimental feedback or a more advanced optimization method may be useful after the initial GS design.
