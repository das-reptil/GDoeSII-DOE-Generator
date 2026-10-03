# Attribution and modification notice

This project is an adapted work derived from **GDoeSII**.

## Original software

**GDoeSII** was developed by:

- Raghu Dharmavarapu
- Shanti Bhattacharya
- Saulius Juodkazis

Original public source repository:

https://github.com/ElsevierSoftwareX/SOFTX_2018_239

Original software publication:

Raghu Dharmavarapu, Shanti Bhattacharya, Saulius Juodkazis,
“GDOESII: Software for design of diffractive optical elements and phase mask conversion to GDSII lithography files,”
SoftwareX 9 (2019), 126–131.

https://doi.org/10.1016/j.softx.2019.01.012

The original GDoeSII software is identified by its authors/project pages as licensed under the **Creative Commons Attribution-NonCommercial 3.0 (CC BY-NC 3.0)** license.

## Changes in this project

This repository is not a verbatim mirror of the original software. It is a standalone DOE-generator adaptation and contains substantial changes and updates, including:

### Software modernization

- migration from the legacy GDoeSII software stack to current Python 3, targeting CPython 3.13
- replacement of legacy Python 2 style constructs with Python 3 compatible code
- current NumPy/Pillow based numerical and image processing
- reproducible dependency definitions
- standalone DOE-focused user interface independent of the original main GDoeSII GUI
- dedicated Windows/PyInstaller packaging
- GitHub Actions based automated test and EXE build workflow

### DOE generation and simulation

- reusable standalone DOE synthesis engine
- continuous phase lens generation
- blazed phase grating generation
- binary Fresnel zone plate generation
- vortex / spiral phase generation
- arbitrary-image Gerchberg-Saxton phase synthesis
- FFT-based Fresnel forward and backward propagation
- propagated intensity simulation and preview

### 16-bit workflow

- native unsigned 16-bit phase-map generation using the full `0 ... 65535` code range
- linear wrapped phase mapping over `0 ... 2*pi`
- true 16-bit PNG phase output
- JSON sidecar metadata for generated phase maps and relief exports
- separation of DOE phase generation from lithography-machine exposure calibration

### Relief / GrayScribeX-oriented export

- phase-to-relief conversion based on wavelength and refractive-index contrast
- separate material/DOE and environment refractive indices
- use of `Delta n = n_material - n_environment`
- calculated maximum `2*pi` relief height
- unsigned 16-bit grayscale height-map export
- physical pixel pitch and image dimensions stored in metadata

### Off-axis steering

- off-axis steering by projected X/Y angles
- exact off-axis steering using a physical target point `(x, y, z)`
- normalized 3-D direction-cosine calculation for large offsets
- linear steering-phase ramp added to the exported DOE
- phase-ramp period and pixels-per-period sampling calculation
- warnings for marginal sampling and sub-Nyquist aliasing
- local target-coordinate simulation preview so large physical offsets remain visible
- off-axis geometry and sampling values included in JSON metadata

### Validation and testing

- numerical tests for analytical DOE generators
- Gerchberg-Saxton synthesis tests
- 16-bit phase conversion and PNG round-trip tests
- refractive-index / phase-to-height tests
- direct generated-DOE relief export tests
- off-axis geometry and sampling tests, including the representative `z=350 mm, x=y=100 mm` case
- automatic Windows EXE verification in CI

A more detailed development history is maintained in `CHANGELOG.md`.

These changes should not be interpreted as having been authored, reviewed, sponsored or endorsed by the original GDoeSII authors.

## Nanoscribe / GrayScribeX

References to Nanoscribe Quantum X and GrayScribeX describe an intended file/workflow use case only. This project is independent and is not an official Nanoscribe product. Nanoscribe and GrayScribeX names and trademarks belong to their respective owners.

## License

The adapted project is distributed under **CC BY-NC 3.0**. See `LICENSE` and the Creative Commons legal code:

https://creativecommons.org/licenses/by-nc/3.0/legalcode
