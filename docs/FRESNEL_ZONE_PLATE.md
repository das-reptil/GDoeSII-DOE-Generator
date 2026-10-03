# Fresnel Zone Plate DOE mode

The `Fresnel Zone Plate` generator creates a binary phase zone plate with alternating `0` and `pi` phase regions.

## Phase model

The implemented zone index is based on

```text
zone = floor((x^2 + y^2) / (lambda * f))
```

and the phase is

```text
phi_FZP = (zone mod 2) * pi
```

This produces concentric binary phase zones that focus light at the selected focal distance.

## Relevant GUI parameters

```text
Type:                 Fresnel Zone Plate
Width / Height:       DOE raster size
Pixel size (nm):      physical DOE sampling pitch
Wavelength (nm):      design wavelength
Focal / target z:     focal length in mm
```

## Typical use cases

A binary phase Fresnel zone plate can be used for:

- diffractive focusing with only two phase levels,
- fabrication tests where a binary relief is easier to manufacture than a continuous profile,
- compact micro-optical focusing elements,
- wavelength-selective focusing experiments,
- detector illumination and alignment,
- comparison of binary and multilevel/continuous DOE efficiency,
- educational and characterization experiments in Fresnel diffraction.

Because only two phase states are required, a phase FZP can be attractive when fabrication simplicity is more important than maximum diffraction efficiency.

## Example

```text
Type:                 Fresnel Zone Plate
Width:                512 px
Height:               512 px
Pixel size:           500 nm
Wavelength:           633 nm
Focal / target z:     10 mm
```

The resulting DOE contains alternating `0` and `pi` phase rings designed for approximately `10 mm` focal distance at `633 nm`.

## Binary phase versus amplitude zone plate

This generator produces a **binary phase** zone plate, not a black/transparent amplitude mask.

The two states are

```text
0 rad
pi rad
```

so both zones can transmit light while imposing different optical phase delays.

This can provide higher optical throughput than an amplitude zone plate because light is not intentionally blocked in every second zone.

## Fabrication depth

For a phase difference of `pi`, the required relative relief is half the full `2*pi` relief:

```text
h_pi = lambda / (2 * Delta n)
```

with

```text
Delta n = n_DOE - n_environment
```

For example, with

```text
lambda = 633 nm
n_DOE = 1.52
n_environment = 1.00
Delta n = 0.52
```

the nominal `pi` height difference is approximately

```text
633 / (2 * 0.52) = 608.65 nm
```

The generic GrayScribeX export still represents the wrapped phase continuously in 16-bit form, but an ideal binary FZP itself contains only the two phase states.

## Sampling and outer zones

The outer Fresnel zones become progressively narrower with increasing radius. Therefore the smallest zone width near the aperture edge is often the critical sampling and fabrication constraint.

A design can become poorly represented if the outer zones approach only one or a few DOE pixels in width.

Important coupled parameters are:

- wavelength,
- focal length,
- DOE aperture,
- pixel size.

A shorter focal length or larger aperture produces narrower outer zones and therefore requires finer sampling.

## Combining with off-axis steering

An additional steering phase can be added:

```text
phi_export = wrap(phi_FZP + phi_steering)
```

This shifts the focused output away from the optical axis.

Note that adding a continuous steering ramp means the final exported phase is no longer strictly binary even though the base FZP is binary.

## Chromatic behavior

Like other diffractive focusing elements, the FZP is strongly wavelength dependent. A design generated for one wavelength will generally focus a different wavelength at a different axial position and with different efficiency.

## Important limitations

The current implementation uses the scalar binary phase-zone approximation. It does not directly model:

- rigorous electromagnetic effects,
- polarization dependence,
- fabrication edge rounding,
- finite sidewall slope,
- high-NA corrections,
- material absorption.

For very small outer-zone widths or high numerical aperture, more rigorous modeling may be necessary.
