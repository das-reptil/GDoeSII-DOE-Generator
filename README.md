# GDoeSII DOE Generator

Standalone diffractive optical element (DOE) generator derived from **GDoeSII**.

The application focuses on phase-only DOE synthesis, scalar Fresnel simulation, off-axis target steering and 16-bit export for grayscale lithography workflows.

## Features

- continuous phase lens
- blazed phase grating
- binary Fresnel zone plate
- vortex / spiral phase
- arbitrary target images using Gerchberg-Saxton phase retrieval
- Fresnel forward/back propagation
- true 16-bit phase PNG output
- local propagated-intensity preview
- off-axis steering by angle or by target-plane X/Y offset
- exact 3-D target direction for large offsets
- phase-ramp sampling / pixels-per-period warning
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

This standalone version contains substantial modifications and extensions, including Python 3 modernization, a dedicated DOE-synthesis engine, Gerchberg-Saxton synthesis, 16-bit output, refractive-index-based relief mapping, GrayScribeX-oriented export and off-axis target steering.

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
- continuous lens and grating generators, binary Fresnel zone plates and vortex phase elements
- propagated intensity simulation for generated phase profiles
- wavelength- and refractive-index-based phase-to-relief conversion
- separate DOE/material and environment refractive indices using `Delta n = n_material - n_environment`
- calculated maximum `2*pi` relief height
- direct 16-bit grayscale relief export with JSON metadata
- exact off-axis target steering by physical `(x, y, z)` target coordinates or projected angles
- phase-ramp period and pixels-per-period sampling checks with aliasing warnings
- local target-coordinate simulation for large off-axis displacements
- automated numerical/export tests
- dedicated PyInstaller Windows packaging and GitHub Actions EXE builds

The complete development and update history is documented in [`CHANGELOG.md`](CHANGELOG.md). Attribution and modification details are documented in [`NOTICE.md`](NOTICE.md).

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

Continuous wrapped quadratic phase profile.

### Grating

Continuous `0 ... 2π` blazed phase ramp with configurable period and angle.

### Fresnel Zone Plate

Binary `0 / π` phase zones.

### Vortex

Azimuthal phase profile with selectable topological charge.

### Arbitrary Image (GS)

Gerchberg-Saxton phase retrieval using Fresnel forward/back propagation.

Typical starting values:

```text
Width:                512 px
Height:               512 px
Pixel size:           500 nm
Wavelength:           633 nm
Target z:             10 mm
GS iterations:        50
DOE index:            1.52
Environment index:    1.00
```

For larger designs, first verify the result at 256 or 512 pixels and a moderate iteration count.

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

## 16-bit phase-map export

`Save 16-bit Phase PNG` writes a wrapped phase map with unsigned 16-bit grayscale encoding:

```text
gray 0        -> 0 rad
gray ~32768   -> pi rad
gray 65535    -> approximately 2*pi
```

A JSON sidecar records generator and off-axis parameters.

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

`Export GrayScribeX` writes:

```text
name.png
name.json
```

The PNG is unsigned 16-bit grayscale. The JSON contains optical parameters, refractive indices, physical dimensions, relief range, generator settings and off-axis geometry.

Machine-specific grayscale/exposure calibration remains the responsibility of the lithography system and its software.

## Repository layout

```text
src/GDoeSII_DOE_Generator.py   standalone GUI
src/gdoesii_doe.py             DOE generation, propagation and off-axis steering
src/gdoesii_grayscribe.py      16-bit relief/height-map export
config/                        PyInstaller configuration
tests/                         numerical and export tests
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
