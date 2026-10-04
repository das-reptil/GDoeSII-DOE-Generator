# Film module changelog

## 2026-10-04 - GS-only film batch architecture

- Added a dedicated `src/film/` package instead of mixing film logic into the general DOE GUI.
- Restricted the film DOE workflow to `Arbitrary Image / Gerchberg-Saxton` only.
- Added a separate `GDoeSII_Film_GS_Batch.exe` build.
- Added input from an existing target-frame directory.
- Added optional 360-degree vertical-axis/yaw target-frame generation from a source image.
- Added the `black/red bright, white dark` monochromatic target mapping used by the current POF logo workflow.
- Added source-frame intensity and active-area statistics.
- Added per-frame GS generation, 16-bit phase PNG output and JSON metadata.
- Added per-frame target-plane simulation output.
- Added reconstructed target/background power analysis.
- Added recommended external laser/duty-cycle attenuation factors for brightness equalization.
- Added optional geometric brightness preservation using `abs(cos(angle)) ** gamma`.
- Added automatic ring-center coordinates and radial/tangential/fixed DOE orientation output.
- Added batch tests, target-frame-generation tests and a dedicated PyInstaller configuration under `config/film/`.
- Documented the current same-sampling GS target-size limitation and the need for a later physical-projection propagation mode for the planned 50 mm projection geometry.
