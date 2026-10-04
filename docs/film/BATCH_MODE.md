# GS film batch mode

## Input

The batch GUI accepts a directory of image frames. Supported image extensions are:

```text
.png .tif .tiff .jpg .jpeg .bmp
```

Files are processed in sorted filename order. Numbered names such as
`frame_000.png ... frame_047.png` are therefore recommended.

## GS parameters

The film GUI exposes only parameters relevant to arbitrary-image GS synthesis:

- DOE width / height
- DOE pixel size
- wavelength
- target z
- GS target width (`0 = fit`)
- GS iterations and seed
- target X/Y
- target pan / tilt

There is deliberately no DOE-type selector in this application.

## Target position and pan/tilt

For a parallel target plane, a non-zero X/Y target position is implemented using the existing off-axis steering phase ramp while brightness statistics remain evaluated in local target coordinates.

For a tilted target plane, X/Y translation and pan/tilt are handled by the tilted-plane GS propagation.

## Per-frame processing

For every frame the batch performs:

1. load and grayscale-normalize the target image,
2. place it in the GS target calculation field,
3. calculate an independent GS phase DOE,
4. add flat-plane off-axis steering when required,
5. simulate the reconstructed field in local target coordinates,
6. calculate target/background power metrics,
7. save `DOE_NNN.png` as a true 16-bit phase PNG,
8. save `DOE_NNN.json` metadata,
9. save `sim_NNN.png` as a 16-bit simulation image.

## Reproducibility

The complete batch settings are written to `film_config.json`. The GS random seed is explicit, making repeated calculations with the same software and settings deterministic.

## Performance

GS cost scales strongly with DOE raster size and iteration count. For workflow validation, use a smaller raster such as 256 or 512 pixels and a low/moderate iteration count before starting a final 4096 x 4096 batch.

Forty-eight independent 4096 x 4096 GS calculations are a large numerical workload. The current batch processes frames sequentially so memory use remains bounded and output is available frame by frame.
