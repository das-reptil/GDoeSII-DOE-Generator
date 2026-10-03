# Vortex and focused Vortex DOE modes

The standalone DOE Generator provides two related vortex modes:

- `Vortex`
- `Vortex + Lens`

Both use an azimuthal phase term with integer topological charge `l`:

```text
phi_vortex(x,y) = l * atan2(y,x)
```

The phase winds by `2*pi*l` around the optical axis. The center is a phase singularity.

## Vortex

`Vortex` generates only the azimuthal phase term.

This is useful when focusing is provided by another optical element, or when the vortex phase is intentionally combined with an existing optical system.

Typical use cases include:

- orbital-angular-momentum (OAM) mode generation,
- conversion of a Gaussian-like input beam toward a vortex / Laguerre-Gaussian-like mode,
- structured illumination,
- optical manipulation and particle-rotation experiments,
- studies of phase singularities and optical vortices,
- use as a phase element in a larger optical system that already contains a focusing lens.

The pure Vortex mode does not by itself define a focal plane.

## Vortex + Lens

`Vortex + Lens` combines the vortex phase with the quadratic phase of a focusing lens:

```text
phi_total = wrap(phi_lens + phi_vortex)
```

with

```text
phi_lens = -pi * (x^2 + y^2) / (lambda * f)
phi_vortex = l * atan2(y,x)
```

The GUI field

```text
Focal / target z (mm)
```

acts as the focal length `f` for this mode.

The local simulation is calculated at this focal distance. For a suitable input beam, the focal-plane intensity is expected to show the characteristic dark central region and ring-like / donut intensity distribution associated with a focused optical vortex.

This mode is useful when the DOE itself should provide both functions in one fabricated phase profile:

- focusing,
- vortex / helical phase generation.

Typical applications include:

- focused donut beams,
- optical trapping and optical tweezers,
- particle manipulation and rotation,
- structured laser processing with ring-shaped intensity distributions,
- mode conversion and OAM experiments,
- vortex-based microscopy and structured illumination,
- experimental beam shaping where a separate focusing lens should be avoided.

## Vortex charge

`Vortex charge` selects the integer topological charge `l`.

Examples:

```text
l = +1   one positive 2*pi phase winding
l = +2   two positive windings
l = -1   one winding with opposite handedness
```

A charge of `0` is rejected because it would contain no vortex phase.

Increasing `|l|` changes the phase winding and generally changes the resulting vortex-mode structure. The exact intensity distribution also depends on the input-beam amplitude, DOE aperture, wavelength, pixel sampling and focal length.

The sign of `l` changes the handedness of the phase helix. It does not simply produce a different grayscale contrast; it represents the opposite phase winding direction.

## Example

A simple starting configuration is:

```text
Type:                 Vortex + Lens
Width:                512 px
Height:               512 px
Pixel size:           500 nm
Wavelength:           633 nm
Focal / target z:     10 mm
Vortex charge:        1
Off-axis mode:        None
```

The DOE phase is then the wrapped sum of a 10 mm focal-length lens phase and a charge-1 vortex phase.

## Combining with off-axis steering

`Vortex + Lens` can also be combined with the existing off-axis steering modes.

The complete exported phase can therefore contain three contributions:

```text
phi_export = wrap(phi_lens + phi_vortex + phi_steering)
```

This allows a focused vortex spot to be directed away from the optical axis while retaining its focusing and vortex phase structure.

As with all off-axis designs, the steering-ramp sampling warning must be observed. Large steering angles can require a smaller DOE pixel pitch.

## Fabrication / GrayScribeX export

Both vortex modes use the same 16-bit phase and GrayScribeX-oriented export path as the other generators.

For the physical relief, the generator uses

```text
Delta n = n_DOE - n_environment
h_2pi = lambda / Delta n
```

so the required relief can also be calculated for an environment with a refractive index different from air.

The exported JSON metadata records the generator type and vortex charge. For `Vortex + Lens` it also records the focal length and the fact that the phase is a combined `lens + vortex` profile.

## Important limitation

The generated intensity preview assumes a uniform phase-only source field in the scalar Fresnel model. A real measured beam can have a Gaussian or otherwise non-uniform amplitude profile, aberrations and finite aperture effects. Therefore the preview should be treated as a numerical design check rather than a complete prediction of the experimental beam profile.
