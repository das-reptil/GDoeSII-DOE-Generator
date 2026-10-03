# Lens DOE mode

The `Lens` generator creates a continuous wrapped quadratic phase profile that acts as a diffractive focusing lens.

## Phase model

The implemented phase is

```text
phi_lens(x,y) = -pi * (x^2 + y^2) / (lambda * f)
```

where

- `lambda` is the design wavelength,
- `f` is the focal length,
- `x` and `y` are physical DOE-plane coordinates.

The phase is wrapped into the interval `0 ... 2*pi` before export.

## Relevant GUI parameters

```text
Type:                 Lens
Width / Height:       DOE raster size
Pixel size (nm):      physical DOE sampling pitch
Wavelength (nm):      design wavelength
Focal / target z:     focal length f in mm
```

`Vortex charge`, grating settings and GS settings do not affect this mode.

## Typical use cases

A phase-only lens DOE can be used for:

- compact diffractive focusing,
- replacing a separate refractive lens in a simple optical path,
- integrated micro-optical elements,
- focusing light onto detectors, fibers or microstructures,
- generation of a focal spot for laser processing,
- test structures for validating fabrication depth and optical efficiency,
- combining focusing with off-axis steering to move the focal spot away from the optical axis.

Because the DOE is phase-only, the same 16-bit phase and GrayScribeX-oriented fabrication path can be used as for the other generator modes.

## Example

```text
Type:                 Lens
Width:                512 px
Height:               512 px
Pixel size:           500 nm
Wavelength:           633 nm
Focal / target z:     10 mm
Off-axis mode:        None
```

This describes a `256 x 256 um` DOE aperture with a nominal focal length of `10 mm` at `633 nm`.

## Combining with off-axis steering

The lens can be combined with the existing steering phase:

```text
phi_export = wrap(phi_lens + phi_steering)
```

This is useful for creating an off-axis focal spot without mechanically tilting the DOE.

The off-axis sampling warning remains important: a large steering angle can require a smaller pixel pitch even when the lens phase itself is well sampled.

## Relation between aperture and focus

The focal spot is not determined by focal length alone. It also depends on:

- illuminated DOE aperture,
- wavelength,
- input-beam amplitude profile,
- DOE pixel pitch,
- fabrication accuracy,
- aberrations.

A larger illuminated aperture generally permits a smaller diffraction-limited focal spot, while insufficient sampling can distort the phase profile.

## Chromatic behavior

The DOE is designed for one wavelength. Diffractive lenses are intrinsically wavelength dependent, so changing the operating wavelength changes the effective focusing behavior.

The `Wavelength (nm)` parameter should therefore match the intended optical design wavelength.

## Fabrication / GrayScribeX export

The optical phase is converted to a relative relief using

```text
Delta n = n_DOE - n_environment
h_2pi = lambda / Delta n
```

The environment is not assumed to be air; immersion or another surrounding refractive index can be entered explicitly.

## Important limitation

The current lens generator uses the scalar paraxial quadratic phase approximation. It is well suited to moderate numerical apertures and conventional Fresnel-type designs.

For very high numerical aperture, very short focal length or very large apertures, an exact spherical phase profile may be preferable. The present generator does not yet switch automatically from the paraxial expression to an exact high-NA lens phase.

The displayed simulation also assumes a uniform phase-only source field. A real Gaussian or otherwise non-uniform input beam can produce a different focal intensity distribution.
