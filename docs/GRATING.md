# Grating DOE mode

The `Grating` generator creates a continuous blazed phase ramp. The phase increases linearly along a selected direction and wraps after each `2*pi` period.

## Phase model

The implemented phase is

```text
coordinate = x*cos(alpha) + y*sin(alpha)
phi_grating = 2*pi * coordinate / period
```

where

- `period` is the physical grating period,
- `alpha` is the grating angle in the DOE plane.

The resulting phase is wrapped into `0 ... 2*pi`.

## Relevant GUI parameters

```text
Type:                 Grating
Width / Height:       DOE raster size
Pixel size (nm):      physical sampling pitch
Grating period (um):  one full 2*pi phase period
Grating angle (deg):  orientation of the phase ramp
```

The wavelength is used by simulation, off-axis steering and relief export, although the analytical grating phase itself is specified directly through its physical period.

## Typical use cases

A blazed phase grating can be used for:

- beam steering,
- shifting light into a selected diffraction order,
- alignment and calibration structures,
- coupling light into a desired angular direction,
- testing diffraction efficiency and fabrication fidelity,
- spatial-frequency or Fourier-optics experiments,
- combining a regular grating with another phase function in a larger DOE design.

For a well-sampled continuous blaze, much of the optical power can be directed toward the intended diffraction order compared with a simple binary amplitude grating.

## Example

```text
Type:                 Grating
Width:                512 px
Height:               512 px
Pixel size:           500 nm
Wavelength:           633 nm
Grating period:       20 um
Grating angle:        0 deg
```

The grating period is represented by

```text
20 um / 0.5 um = 40 pixels per period
```

which is comfortably sampled.

## Grating angle

`0 deg` produces phase variation along the X direction. Rotating the grating angle rotates the phase-gradient vector in the DOE plane.

Examples:

```text
0 deg    ramp along X
90 deg   ramp along Y
45 deg   diagonal ramp
```

The sign/orientation of the phase gradient determines the steering direction.

## Approximate diffraction angle

For a simple first-order free-space interpretation at normal incidence, the grating equation gives approximately

```text
sin(theta) = lambda / period
```

for the first order, provided the chosen period and wavelength make that order physically propagating.

This relation is a useful design estimate, but the actual experimental angle and efficiency also depend on illumination, refractive-index interfaces, fabrication accuracy and the realized phase depth.

## Sampling

A key parameter is the number of DOE pixels per grating period:

```text
pixels_per_period = grating_period_um / (pixel_size_nm / 1000)
```

Too few samples per period distort the intended continuous phase ramp and can reduce diffraction efficiency or introduce unwanted orders.

Unlike the dedicated off-axis steering function, the current GUI does not yet issue an automatic sampling warning specifically for the analytical `Grating` period, so this value should be checked manually.

## Relation to off-axis steering

The analytical grating and the off-axis steering ramp are mathematically related: both are linear phase gradients.

The `Grating` generator is convenient when the period and orientation are the natural design parameters. The off-axis steering modes are more convenient when the desired output angle or physical `(x, y, z)` target coordinate is known.

Applying off-axis steering to an existing grating adds another linear phase term:

```text
phi_export = wrap(phi_grating + phi_steering)
```

The resulting effective gradient is the vector sum of both contributions.

## Fabrication / GrayScribeX export

The wrapped phase is exported through the same 16-bit phase and relief pipeline as the other generators.

For a complete `2*pi` blaze depth:

```text
Delta n = n_DOE - n_environment
h_2pi = lambda / Delta n
```

Correct phase depth is important for achieving the intended blazed-grating efficiency.

## Important limitations

The generator models an ideal scalar phase grating. It does not directly predict:

- rigorous electromagnetic diffraction efficiency,
- polarization effects,
- material absorption,
- fabrication sidewall effects,
- coupling at high numerical aperture or strongly subwavelength periods.

For periods approaching the wavelength or feature sizes near the fabrication/sampling limit, rigorous electromagnetic methods may be required instead of the scalar model.
