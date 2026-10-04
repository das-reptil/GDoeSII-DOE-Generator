# GS film / batch generator

The film workflow is intentionally restricted to **Arbitrary Image / Gerchberg-Saxton (GS)** DOEs.

Analytical generators such as Lens, Grating, Fresnel Zone Plate and Vortex remain in the normal single-DOE application and are not exposed in the film GUI.

## Separation of applications

The repository now builds two Windows applications:

- `GDoeSII_DOE_Generator.exe` – general single-DOE generator.
- `GDoeSII_Film_GS_Batch.exe` – simplified GS-only film/batch generator.

The film implementation is kept under `src/film/` so frame analysis, brightness handling, batch processing and ring-layout generation do not clutter the general DOE GUI.

## Film batch workflow

The current film application expects a directory containing already prepared target frames. It then performs:

1. source-frame brightness analysis,
2. independent GS calculation for every frame,
3. target-plane simulation for every generated DOE,
4. reconstructed-power / brightness analysis,
5. per-frame brightness-compensation recommendations,
6. 16-bit DOE + JSON metadata export,
7. simulation PNG export,
8. ring-layout CSV generation.

Each frame is an independent GS problem. No analytical DOE type is mixed into the film workflow.

## Output structure

A batch output directory contains:

```text
film_config.json
summary.json

doe/
  DOE_000.png
  DOE_000.json
  DOE_001.png
  ...

simulation/
  sim_000.png
  sim_001.png
  ...

statistics/
  frame_source_statistics.csv
  brightness_statistics.csv

layout/
  DOE_ring_layout.csv
```

## Current optical scaling limitation

The film batch currently uses the same target sampling model as the existing GS implementation. `GS target width (um; 0=fit)` therefore refers to the current same-sampling calculation plane.

This is **not yet the physical-projection mode** required to directly represent, for example, a 50 mm projected target at 300 mm distance from a 4096 x 4096 DOE with 500 nm DOE pitch.

A scaled/physical Fresnel propagation mode remains a separate numerical extension. The film GUI states this explicitly so a user does not accidentally enter `50000 um` into the current same-sampling target-width field and assume it represents the intended projection geometry.

See also:

- [`BATCH_MODE.md`](BATCH_MODE.md)
- [`BRIGHTNESS.md`](BRIGHTNESS.md)
- [`RING_LAYOUT.md`](RING_LAYOUT.md)
