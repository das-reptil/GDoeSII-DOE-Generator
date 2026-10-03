# Changelog

This file documents the major software changes that led from the original GDoeSII codebase to this standalone DOE generator.

The entries below describe functional and architectural changes in the adapted software. They do not imply authorship or endorsement by the original GDoeSII authors. See `NOTICE.md` for attribution and licensing information.

## 2026-10-03 - Initial public standalone state

### Licensing and attribution

- Aligned the standalone repository with the original GDoeSII software license: **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**.
- Added the original author repository `https://github.com/raghu1153/GDoeSII` as the primary upstream source reference.
- Retained the Elsevier SoftwareX archive and publication DOI as additional provenance references.
- Updated `LICENSE`, `README.md`, `NOTICE.md` and `CITATION.cff` consistently.

### Standalone application

- Split DOE synthesis into a dedicated standalone application: `GDoeSII_DOE_Generator.py`.
- Removed the dependency on the original GDoeSII main GUI for DOE creation.
- Reduced the public repository to the files required for DOE synthesis, simulation, 16-bit export, testing and Windows builds.
- Added a dedicated PyInstaller specification and a one-click Windows build script.
- Added GitHub Actions CI that tests the numerical core, builds the Windows EXE, verifies the executable and uploads it as an artifact.
- Made the GUI resizable and screen-aware, with horizontal/vertical scrolling for small displays or high DPI scaling.

### Python modernization

- Ported the DOE workflow to current Python 3, targeting CPython 3.13.
- Replaced legacy Python 2 style constructs with Python 3 compatible code.
- Standardized numerical calculations on NumPy arrays using floating-point and complex-valued fields where appropriate.
- Updated image handling to current Pillow APIs.
- Added reproducible dependency versions in `requirements.txt`.
- Added automated syntax/numerical/export tests suitable for current Python versions.
- Updated GitHub Actions dependencies to Node 24 compatible major versions.

### 16-bit phase pipeline

- Added native unsigned 16-bit phase-map generation with the full `0 ... 65535` code range.
- Added deterministic linear mapping between wrapped phase `0 ... 2*pi` and the 16-bit grayscale code space.
- Added true 16-bit PNG export instead of reducing DOE data to 8-bit grayscale.
- Added JSON sidecar metadata for generated phase maps.
- Kept optical phase generation separate from lithography-machine calibration.

### DOE synthesis engine

- Added a reusable DOE calculation module independent of the GUI.
- Added continuous wrapped quadratic phase lenses.
- Added blazed phase gratings with configurable period and orientation.
- Added binary Fresnel zone plates with `0 / pi` phase levels.
- Added vortex / spiral phase elements with configurable topological charge.
- Added arbitrary-target DOE synthesis using an iterative Gerchberg-Saxton algorithm.

### Focused Vortex + Lens mode

- Added a dedicated `Vortex + Lens` generator mode while retaining the original pure `Vortex` mode.
- Combined the quadratic lens phase and azimuthal vortex phase as `wrap(phi_lens + phi_vortex)`.
- Reused `Focal / target z (mm)` as the focal length of the combined focused-vortex DOE.
- Added focal-plane simulation of the combined phase profile.
- Added vortex charge and focal-length information to generator metadata.
- Kept off-axis steering compatible with the combined mode, allowing `phi_lens + phi_vortex + phi_steering`.
- Added automated tests for the combined phase construction.
- Added `docs/VORTEX.md` with physical background, use cases, example parameters, off-axis interaction and fabrication notes.
- Expanded `docs/PARAMETERS.md` with focused-vortex parameter descriptions and use cases.

### Physical Gerchberg-Saxton target sizing

- Added `GS target width (um; 0=fit)` to the standalone GUI.
- Preserved the previous auto-fit behavior when the value is `0`.
- Added physical target-width specification in micrometres for Arbitrary Image / Gerchberg-Saxton designs.
- Derived the target height automatically from the source-image aspect ratio.
- Quantized requested target dimensions to whole target-plane pixels and reported the actual resulting physical size.
- Centered the resized target inside the local target calculation field.
- Added validation that rejects requested target dimensions larger than the sampled target-plane field.
- Added requested/actual target geometry, raster dimensions and placement to generated metadata.
- Kept physical target size independent from off-axis target position, so a target can be sized locally and then steered to a physical `(x, y, z)` location.
- Added tests for physical target sizing, auto-fit compatibility and oversized-target rejection.

### Fresnel propagation and simulation

- Added scalar Fresnel propagation using FFT-based transfer functions.
- Added forward and backward propagation for Gerchberg-Saxton iterations.
- Added propagated intensity simulation for generated phase profiles.
- Added normalized 16-bit simulation previews.
- For off-axis designs, the preview remains centered in local target coordinates while the exported phase map contains the steering ramp.

### Phase-to-relief / GrayScribeX-oriented export

- Added direct conversion from normalized phase to a relative grayscale height map.
- Added wavelength-dependent phase-to-height conversion.
- Changed relief calculation to use the material/environment refractive-index contrast:

  `Delta n = n_material - n_environment`

- Added the physical mapping:

  `h = (phi - phi_min) * lambda / (2*pi*Delta n)`

- Added explicit DOE/material refractive index and environment refractive index fields.
- Added calculated `Delta n` and maximum `2*pi` relief height to the GUI and metadata.
- Added direct unsigned 16-bit PNG export intended for GrayScribeX-oriented workflows.
- Added JSON metadata containing optical parameters, pixel pitch, physical image size, index contrast, phase range and height range.
- Left machine-specific grayscale/exposure calibration to the lithography system rather than reproducing it in the generator.

### Off-axis target steering

- Added optional steering of the generated DOE away from the optical axis.
- Added steering by projected X/Y angles.
- Added steering by physical target coordinates `(x, y, z)` in millimeters.
- Added exact normalized 3-D direction cosines for large offsets instead of relying only on a small-angle approximation:

  `r = sqrt(x^2 + y^2 + z^2)`

  `sx = x / r`, `sy = y / r`, `sz = z / r`

- Added the corresponding linear steering phase:

  `phi_offset(X,Y) = 2*pi/lambda * (sx*X + sy*Y)`

- Added phase-ramp period calculation in X, Y and the transverse diagonal direction.
- Added pixels-per-period sampling checks.
- Added warnings below 3 pixels per diagonal period and an aliasing warning below 2 pixels per period.
- Added off-axis geometry and sampling information to exported metadata.

### Target-plane pan / tilt

- Added general 3-D target-plane orientation independent of any rotating-disc or animation workflow.
- Added `Target pan (deg)` and `Target tilt (deg)` GUI parameters.
- Defined `0 / 0 deg` as the historical target plane parallel to the DOE plane.
- Defined positive pan as rotating the target normal toward `+X` and positive tilt as rotating it toward `-Y`.
- Defined rotation order as tilt about global X followed by pan about global Y.
- Added target-plane centre, local U/V basis vectors and normal-vector calculation.
- Added 3-D coordinates for all four corners of GS image targets.
- Added rotated-angular-spectrum propagation for non-zero GS pan/tilt, including forward and reverse propagation in the iterative GS loop.
- Kept the historical same-sampling Fresnel GS path unchanged for exactly zero pan and tilt.
- Included off-axis target-centre translation directly in tilted GS propagation so steering is not applied twice.
- Added tilted-plane simulation for analytical generator modes without redefining their analytic phase functions.
- Added tilt-carrier sampling estimates, marginal-sampling warnings and Nyquist rejection for aliased tilted GS configurations.
- Added target-plane orientation and sampling data to generated/exported metadata.
- Added numerical tests for target geometry, zero-tilt compatibility, propagation and GS behaviour.
- Added `src/gdoesii_tilt.py` as the dedicated target-plane geometry/propagation module.

### Reference off-axis validation

The numerical tests include the representative target geometry:

- `z = 350 mm`
- `x = 100 mm`
- `y = 100 mm`
- `lambda = 633 nm`
- `DOE pixel pitch = 500 nm`

The expected geometry is approximately:

- `Theta X = 15.9454 deg`
- `Theta Y = 15.9454 deg`
- `Total angle = 22.0017 deg`
- `Ray length = 377.4917 mm`
- `Diagonal phase-ramp period = 1.690 um`
- `Pixels per diagonal period = 3.38`

The tests also verify that a `1000 nm` DOE pixel pitch falls below two pixels per diagonal ramp period for this geometry and therefore produces an aliasing warning.

### Documentation

- Added `docs/GENERATORS.md` as a central overview of all generator modes and a quick mode-selection guide.
- Added `docs/LENS.md` with the quadratic lens phase model, focusing use cases, off-axis focusing, chromatic behavior, fabrication notes and paraxial-model limitations.
- Added `docs/GRATING.md` with the blazed-phase model, beam-steering/diffraction use cases, grating-angle convention, sampling guidance and scalar-model limitations.
- Added `docs/FRESNEL_ZONE_PLATE.md` with binary phase-zone operation, typical applications, `pi` relief-depth relation, outer-zone sampling constraints and limitations.
- Added `docs/VORTEX.md` for Vortex and focused Vortex + Lens operation, physical interpretation, use cases and example settings.
- Added `docs/GERCHBERG_SAXTON.md` with iterative GS operation, target-image preparation, convergence guidance, target-plane pan/tilt, arbitrary beam-shaping use cases and limitations.
- Added `docs/GS_TARGET_SIZE.md` with a focused explanation of physical Gerchberg-Saxton target sizing.
- Added `docs/TARGET_PLANE_PAN_TILT.md` describing target-plane coordinates, sign conventions, rotated-angular-spectrum propagation, sampling limits and metadata.
- Added `docs/PARAMETERS.md` as a complete GUI parameter reference covering units, physical meaning, generator-specific use, off-axis steering, target-plane pan/tilt, refractive indices, phase-to-relief conversion and export behavior.
- Added parameter-interaction guidance, including DOE dimensions versus pixel pitch, GS target size versus sampling, off-axis ramp sampling, tilted-plane sampling and relief height versus refractive-index contrast.
- Linked all generator-specific and target-plane documentation prominently from `README.md`.

### Testing and build automation

- Added tests for all analytical DOE generators.
- Added tests for the focused Vortex + Lens phase combination.
- Added tests for the Gerchberg-Saxton synthesis path.
- Added tests for phase wrapping and 16-bit conversion.
- Added tests for 16-bit PNG round-tripping.
- Added tests for refractive-index contrast and phase-to-height conversion.
- Added tests for direct generated-DOE to 16-bit relief export.
- Added tests for off-axis geometry and sampling limits.
- Added tests for physical GS target sizing and bounds checking.
- Added tests for target-plane pan/tilt geometry and tilted propagation.
- Added a regression test for Tkinter sticky constants used by the responsive GUI.
- Added a Windows CI build using Python 3.13 and PyInstaller.
- Added automatic executable verification and GitHub Actions artifact upload.

## Relationship to original GDoeSII

The original GDoeSII software provided the historical foundation and motivation for this project. This standalone repository is intentionally narrower in scope: it focuses on DOE synthesis, simulation and grayscale/relief export rather than the complete original GDoeSII GDSII conversion workflow.

For the original software, publication and authorship information, see `NOTICE.md` and `CITATION.cff`.
