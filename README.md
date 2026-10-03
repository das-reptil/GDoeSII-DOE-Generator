# GDoeSII DOE Generator

Standalone diffractive optical element (DOE) generator derived from **GDoeSII**.

The application focuses on phase-only DOE synthesis, scalar Fresnel simulation, off-axis target steering, tilted target-plane propagation and 16-bit export for grayscale lithography workflows.

## Features

- continuous phase lens
- blazed phase grating
- binary Fresnel zone plate
- vortex / spiral phase
- focused `Vortex + Lens` mode for direct donut / optical-vortex focusing
- arbitrary target images using Gerchberg-Saxton phase retrieval
- physical target-width control for Gerchberg-Saxton target images
- Fresnel forward/back propagation for parallel target planes
- target-plane pan/tilt with rotated-angular-spectrum propagation
- true 16-bit phase PNG output
- local propagated-intensity preview
- off-axis steering by angle or by target-plane X/Y offset
- exact 3-D target direction for large offsets
- phase-ramp and tilted-plane sampling warnings
- material/environment refractive-index contrast
- phase-to-relief conversion
- direct 16-bit GrayScribeX-oriented height-map export
- JSON sidecar metadata
- standalone Windows EXE build via PyInstaller and GitHub Actions

## Origin and attribution

This project is derived from **GDoeSII**, originally developed by:

- Raghu Dharmavarapu
- Shanti Bhattacharya
- Saulius Juodkazis

Original public source repository:

https://github.com/raghu1153/GDoeSII

SoftwareX archive repository:

https://github.com/ElsevierSoftwareX/SOFTX_2018_239

Associated publication:

> Raghu Dharmavarapu, Shanti Bhattacharya, Saulius Juodkazis, “GDOESII: Software for design of diffractive optical elements and phase mask conversion to GDSII lithography files,” *SoftwareX* 9 (2019), 126–131.

DOI: https://doi.org/10.1016/j.softx.2019.01.012

The original software is distributed under the **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)** license. This repository retains that license for the adapted work. See `LICENSE` and `NOTICE.md`.

This standalone version contains substantial modifications and extensions, including Python 3 modernization, a dedicated DOE-synthesis engine, focused vortex generation, Gerchberg-Saxton synthesis, 16-bit output, refractive-index-based relief mapping, GrayScribeX-oriented export, physical target sizing, off-axis target steering and target-plane pan/tilt.

This project is not an official Nanoscribe product and is not affiliated with or endorsed by Nanoscribe GmbH.

## Software changes and modernization

Compared with the original GDoeSII software, this standalone project includes a substantial modernization and specialization of the DOE workflow:

- port to current Python 3 with CPython 3.13 as the primary target
- updated NumPy/Pillow based numerical and image processing
- standalone DOE application independent of the original GDoeSII main GUI
- reusable DOE calculation core separated from the user interface
- native unsigned 16-bit phase generation over the full `0 ... 65535` range
- deterministic `0 ... 2*pi` phase mapping and true 16-bit PNG output
- arbitrary-target Gerchberg-Saxton synthesis with FFT-based Fresnel forward/back propagation
- rotated-angular-spectrum propagation for physically tilted GS target planes
- target-plane pan/tilt geometry with local basis, normal and 3-D corner metadata
- physical GS target-width control with aspect-ratio-preserving target height
- continuous lens and grating generators, binary Fresnel zone plates and vortex phase elements
- combined focused `Vortex + Lens` phase profiles
- propagated intensity simulation for generated phase profiles
- wavelength- and refractive-index-based phase-to-relief conversion
- separate DOE/material and environment refractive indices using `Delta n = n_material - n_environment`
- calculated maximum `2*pi` relief height
- direct 16-bit grayscale relief export with JSON metadata
- exact off-axis target steering by physical `(x, y, z)` target coordinates or projected angles
- phase-ramp period and pixels-per-period sampling checks with aliasing warnings
- tilted-target carrier sampling checks with aliasing rejection for GS
- local target-coordinate simulation for large off-axis displacements
- automated numerical/export tests
- dedicated PyInstaller Windows packaging and GitHub Actions EXE builds

The complete development and update history is documented in [`CHANGELOG.md`](CHANGELOG.md). Attribution and modification details are documented in [`NOTICE.md`](NOTICE.md).

## Documentation

- [`docs/GENERATORS.md`](docs/GENERATORS.md) – overview of all generator modes and guidance on choosing the appropriate mode.
- [`docs/LENS.md`](docs/LENS.md) – lens phase, focusing use cases, off-axis focusing, chromatic behavior and paraxial-model limitations.
- [`docs/GRATING.md`](docs/GRATING.md) – blazed grating principle, diffraction/beam-steering use cases, angle convention and sampling considerations.
- [`docs/FRESNEL_ZONE_PLATE.md`](docs/FRESNEL_ZONE_PLATE.md) – binary phase FZP operation, fabrication depth, use cases and outer-zone sampling limits.
- [`docs/VORTEX.md`](docs/VORTEX.md) – Vortex and focused Vortex + Lens operation, use cases, example settings and limitations.
- [`docs/GERCHBERG_SAXTON.md`](docs/GERCHBERG_SAXTON.md) – arbitrary-image GS synthesis, target preparation, convergence, target-plane tilt and limitations.
- [`docs/GS_TARGET_SIZE.md`](docs/GS_TARGET_SIZE.md) – detailed physical target sizing for Arbitrary Image / Gerchberg-Saxton designs.
- [`docs/TARGET_PLANE_PAN_TILT.md`](docs/TARGET_PLANE_PAN_TILT.md) – 3-D target-plane geometry, pan/tilt conventions, rotated-angular-spectrum propagation, sampling limits and metadata.
- [`docs/PARAMETERS.md`](docs/PARAMETERS.md) – complete GUI parameter reference, units, physical meaning and parameter interactions.

## Requirements

Recommended:

```text
CPython 3.13, 64-bit
```

Install on Windows:

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run from source:

```bat
.venv\Scripts\python.exe src\GDoeSII_DOE_Generator.py
```

## Build the Windows EXE

Double-click or run:

```text
build_windows.bat
```

The result is:

```text
dist\GDoeSII_DOE_Generator.exe
```

Manual build:

```bat
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm config\GDoeSII_DOE_Generator.spec
```

GitHub Actions also builds and uploads the artifact:

```text
GDoeSII-DOE-Generator-Windows-x64
```

## DOE generators

### Lens

Continuous wrapped quadratic phase profile for diffractive focusing.

Typical uses include compact focusing, micro-optics, detector/fiber illumination, laser processing and off-axis focal spots.

See [`docs/LENS.md`](docs/LENS.md).

### Grating

Continuous `0 ... 2π` blazed phase ramp with configurable period and angle.

Typical uses include beam steering, diffraction-order control, alignment/calibration and Fourier-optics experiments.

See [`docs/GRATING.md`](docs/GRATING.md).

### Fresnel Zone Plate

Binary `0 / π` phase zones for diffractive focusing.

Typical uses include simple binary fabrication, compact focusing and comparison of binary versus continuous phase optics.

See [`docs/FRESNEL_ZONE_PLATE.md`](docs/FRESNEL_ZONE_PLATE.md).

### Vortex

Azimuthal phase profile with selectable topological charge:

```text
phi_vortex = charge * atan2(y,x)
```

This mode applies only the vortex phase. It is useful when focusing is supplied by another optical element or when the phase element is used for OAM/mode-conversion experiments, structured illumination, optical manipulation or phase-singularity studies.

### Vortex + Lens

This mode combines the vortex phase with the quadratic phase of a focusing lens:

```text
phi_total = wrap(phi_lens + phi_vortex)
```

`Focal / target z (mm)` acts as the focal length. The local simulation is evaluated at this focal distance, where a suitable input beam produces the characteristic focused optical-vortex / donut-like intensity distribution.

Typical use cases include:

- focused donut beams,
- optical tweezers and particle manipulation,
- particle rotation / orbital-angular-momentum experiments,
- ring-shaped laser processing,
- mode conversion,
- structured illumination and vortex-based microscopy.

The mode remains compatible with off-axis steering. The exported phase can therefore contain:

```text
phi_export = wrap(phi_lens + phi_vortex + phi_steering)
```

See [`docs/VORTEX.md`](docs/VORTEX.md) for details.

### Arbitrary Image (GS)

Gerchberg-Saxton phase retrieval for arbitrary target-intensity images.

With `Target pan = 0` and `Target tilt = 0`, the historical Fresnel forward/back propagation path is retained. With a non-zero pan or tilt, the GS loop propagates between the DOE plane and the physically tilted target plane using a rotated angular spectrum.

Typical uses include arbitrary beam shaping, structured illumination, logos/symbols, custom laser-processing patterns, phase-only holographic target fields and projection onto inclined surfaces.

The physical target width can be controlled with:

```text
GS target width (um; 0=fit)
```

`0` preserves the previous auto-fit behavior. A positive value specifies the desired physical target width in micrometres. The target height is derived automatically from the source-image aspect ratio, the image is centered in the local target plane, and the requested dimensions are quantized to whole target-plane pixels.

Example:

```text
DOE:               512 x 512 px
Pixel size:         500 nm
Calculation field:  256 x 256 um
Target image:       2:1 aspect ratio
GS target width:    80 um

Target raster:      160 x 80 px
Actual target size: 80 x 40 um
```

The requested target size is validated against the sampled target-plane field. Target geometry is included in the JSON metadata.

Typical starting values:

```text
Width:                512 px
Height:               512 px
Pixel size:           500 nm
Wavelength:           633 nm
Target z:             10 mm
GS iterations:        50
GS target width:      0 um (auto fit)
Target pan:           0 deg
Target tilt:          0 deg
DOE index:            1.52
Environment index:    1.00
```

For larger designs, first verify the result at 256 or 512 pixels and a moderate iteration count.

See [`docs/GERCHBERG_SAXTON.md`](docs/GERCHBERG_SAXTON.md), [`docs/GS_TARGET_SIZE.md`](docs/GS_TARGET_SIZE.md) and [`docs/TARGET_PLANE_PAN_TILT.md`](docs/TARGET_PLANE_PAN_TILT.md) for details.

## Off-axis target steering

Three modes are available:

```text
None
Angle
Target-plane distance
```

### Angle mode

Enter projected steering angles:

```text
Theta X (deg)
Theta Y (deg)
```

### Target-plane distance mode

Enter the physical target coordinates relative to the optical axis:

```text
Target z:          axial distance in mm
Target X offset:   x in mm
Target Y offset:   y in mm
```

The target direction is calculated exactly from:

```text
r  = sqrt(x^2 + y^2 + z^2)
sx = x / r
sy = y / r
sz = z / r
```

and the steering phase is:

```text
phi_offset(X,Y) = 2*pi/lambda * (sx*X + sy*Y)
```

Example:

```text
z = 350 mm
x = 100 mm
y = 100 mm
lambda = 633 nm
DOE pixel = 500 nm
```

approximately gives:

```text
Theta X:              15.9454 deg
Theta Y:              15.9454 deg
Total angle:          22.0017 deg
Ray length:           377.4917 mm
Diagonal ramp period: 1.690 um
Pixels / period:      3.38
```

The program warns when the phase ramp is poorly sampled. Below 2 pixels per diagonal ramp period it is below the Nyquist limit; below 3 pixels per period it is flagged as marginal.

The exported phase map contains the steering ramp. The displayed intensity simulation remains centered in local target coordinates, so large physical offsets do not disappear outside the small numerical preview window.

Target position and target size are independent: for example an 80 um wide GS target can be directed to a physical target coordinate such as `x=100 mm`, `y=100 mm`, `z=350 mm`.

## Target-plane pan / tilt

The target plane can additionally be oriented in 3-D:

```text
Target pan (deg)
Target tilt (deg)
```

`0 / 0 deg` reproduces the historical parallel target plane.

Conventions:

```text
+X = right
+Y = increasing image rows
+Z = from DOE toward target
positive pan  -> target normal toward +X
positive tilt -> target normal toward -Y
rotation order: tilt around X, then pan around Y
```

Target position and target orientation are independent. In `Target-plane distance` mode, `Target X`, `Target Y` and `Target z` define the **centre** of the target plane, while pan/tilt define its orientation about that centre.

For `Arbitrary Image (GS)`, a non-zero pan or tilt switches the iterative propagation to the tilted-plane solver. The target image is therefore synthesized in the local coordinates of the physical inclined surface, rather than being represented by a perspective-warped image in a parallel plane.

For analytical generator modes, pan/tilt does not change the analytic phase equation itself; it changes the plane on which the simulation preview is evaluated.

The GUI reports the target normal and tilted-plane carrier sampling. Marginal sampling is warned about and an aliased tilted GS configuration is rejected.

See [`docs/TARGET_PLANE_PAN_TILT.md`](docs/TARGET_PLANE_PAN_TILT.md) for the numerical method, geometry and limitations.

## 16-bit phase-map export

`Save 16-bit Phase PNG` writes a wrapped phase map with unsigned 16-bit grayscale encoding:

```text
gray 0        -> 0 rad
gray ~32768   -> pi rad
gray 65535    -> approximately 2*pi
```

A JSON sidecar records generator, target-size, off-axis and target-plane orientation parameters where applicable. Focused vortex metadata additionally records vortex charge and focal length.

## Relief / GrayScribeX-oriented export

The relative relief height is calculated from the material/environment index contrast:

```text
Delta n = n_DOE - n_environment
h = phi * lambda / (2*pi*Delta n)
```

For a complete `2π` phase period:

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

The environment index is not fixed to air. A surrounding medium with a refractive index different from `1.0` can be entered explicitly, so the relief is calculated from the actual `Delta n`.

`Export GrayScribeX` writes:

```text
name.png
name.json
```

The PNG is unsigned 16-bit grayscale. The JSON contains optical parameters, refractive indices, physical dimensions, relief range, generator settings, GS target geometry, off-axis geometry and target-plane pan/tilt geometry where applicable.

Machine-specific grayscale/exposure calibration remains the responsibility of the lithography system and its software.

## Repository layout

```text
src/GDoeSII_DOE_Generator.py   standalone GUI
src/gdoesii_doe.py             DOE generation, Fresnel propagation and off-axis steering
src/gdoesii_tilt.py            tilted target-plane geometry and angular-spectrum propagation
src/gdoesii_grayscribe.py      16-bit relief/height-map export
config/                        PyInstaller configuration
tests/                         numerical and export tests
docs/GENERATORS.md             generator overview and mode selection
docs/LENS.md                   lens operation and use cases
docs/GRATING.md                grating operation and use cases
docs/FRESNEL_ZONE_PLATE.md     binary phase FZP operation and use cases
docs/VORTEX.md                 vortex modes, focused vortex and use cases
docs/GERCHBERG_SAXTON.md       arbitrary-image GS operation and use cases
docs/GS_TARGET_SIZE.md         detailed GS physical target sizing
docs/TARGET_PLANE_PAN_TILT.md  target-plane orientation and tilted propagation
docs/PARAMETERS.md             complete parameter reference
.github/workflows/             Windows CI/EXE build
CHANGELOG.md                   software modernization and update history
NOTICE.md                      origin, attribution and modification notice
```

## License

Code in this adapted project is distributed under **CC BY-NC 4.0** in accordance with the original GDoeSII software license.

See:

- `LICENSE`
- `NOTICE.md`

Creative Commons legal code: https://creativecommons.org/licenses/by-nc/4.0/legalcode

## Citation

If you use this project in research, please cite the original GDoeSII publication:

R. Dharmavarapu, S. Bhattacharya, S. Juodkazis, *GDOESII: Software for design of diffractive optical elements and phase mask conversion to GDSII lithography files*, SoftwareX 9 (2019), 126–131. https://doi.org/10.1016/j.softx.2019.01.012
