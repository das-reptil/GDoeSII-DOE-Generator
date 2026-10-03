# Gerchberg-Saxton target size

For **Arbitrary Image (GS)** the physical size of the reconstructed target can be controlled independently from the DOE size and from the off-axis target position.

## GUI setting

Use:

```text
GS target width (um; 0=fit)
```

- `0` keeps the previous behaviour: the target image is fitted as large as possible into the complete sampled target-plane window.
- A positive value specifies the desired physical target-image width in micrometres.
- The target height is calculated automatically from the source image aspect ratio.
- The image remains centred in the local target-plane calculation window.

The requested physical size is converted to the nearest whole number of sampled target-plane pixels. The GUI reports the actual quantized width and height.

## Example

For:

```text
DOE size:        512 x 512 px
DOE pixel pitch: 500 nm
GS target width: 80 um
source image:    2:1 aspect ratio
```

the sampled target-plane window is:

```text
256 x 256 um
```

and the requested target becomes:

```text
160 x 80 px
80 x 40 um
```

centred in the target plane.

## Limits

The complete target must fit into the sampled target-plane window. If either the requested width or the aspect-ratio-derived height exceeds that window, generation is rejected with an explanatory error instead of silently clipping the image.

The target size is independent of off-axis steering. For example, a target can simultaneously be specified as:

```text
width = 80 um
z     = 350 mm
x     = 100 mm
y     = 100 mm
```

The GS algorithm defines the local target pattern and size; the off-axis phase ramp defines where that local target plane is directed.

The target geometry, requested width, actual quantized width/height, pixel dimensions and calculation-window dimensions are written into the generated DOE metadata.
