# GS film batch mode

## Input

The batch GUI supports two input modes.

### Existing frame directory

Supported image extensions are:

```text
.png .tif .tiff .jpg .jpeg .bmp
```

Files are processed in sorted filename order. Numbered names such as
`frame_000.png ... frame_047.png` are therefore recommended.

### Generate 360-degree yaw frames

A source image can be converted into an evenly sampled vertical-axis rotation before GS processing. The generator exposes:

- frame count,
- square frame canvas size,
- front-facing image width,
- perspective camera distance,
- target-intensity mapping.

For a 48-frame full rotation the nominal angle increment is `7.5 deg`.

The default `black/red bright, white dark` mapping is intended for the current POF logo workflow. It maps black and saturated red source features to high target intensity while suppressing white/light areas. The generated monochromatic target frames are written to `frames_raw/` together with `frames.json` metadata.

Exactly edge-on views at 90 and 270 degrees make the projective transformation singular. They are rendered with a very small 0.15-degree numerical offset while retaining the exact nominal frame angle in metadata.

## GS parameters

The film GUI exposes only parameters relevant to arbitrary-image GS synthesis:

- DOE width / height,
- DOE pixel size,
- wavelength,
- target z,
- GS target width (`0 = fit`),
- GS iterations and seed,
- target X/Y,
- target pan / tilt.

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

The complete GS batch settings are written to `film_config.json`. Generated yaw frames additionally have `frames_raw/frames.json`. The GS random seed is explicit, making repeated calculations with the same software and settings deterministic.

## Performance

GS cost scales strongly with DOE raster size and iteration count. For workflow validation, use a smaller raster such as 256 or 512 pixels and a low/moderate iteration count before starting a final 4096 x 4096 batch.

Forty-eight independent 4096 x 4096 GS calculations are a large numerical workload. The current batch processes frames sequentially so memory use remains bounded and output is available frame by frame.
