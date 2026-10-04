# Film brightness analysis

Strongly different GS target contents can reconstruct with different optical efficiency and therefore different apparent brightness.

The film batch records two classes of metrics.

## Source-frame metrics

`statistics/frame_source_statistics.csv` contains, per input frame:

- image dimensions,
- total normalized intensity,
- mean normalized intensity,
- active-pixel count and fraction,
- mean/sum intensity of active pixels,
- active bounding-box dimensions.

The active region is defined by `Active threshold` relative to the normalized frame maximum.

## Reconstructed-field metrics

`statistics/brightness_statistics.csv` additionally contains metrics derived from the propagated field:

- total propagated power,
- power inside the active target mask,
- background power,
- target-power fraction,
- mean power per target pixel,
- mean power per background pixel,
- target/background mean ratio,
- peak propagated power per pixel.

The most useful first-order frame-to-frame efficiency metric is `target_power_fraction`.

## Why a scalar target multiplier is not enough

The GS implementation normalizes the target intensity before applying the amplitude constraint. Therefore multiplying a complete target frame by a scalar does not change the GS solution in the desired way: the scalar is cancelled by target normalization.

For that reason the current batch does **not** pretend to equalize optical brightness by simply multiplying each target image.

Instead it derives a recommended external attenuation factor.

## Constant reconstructed brightness

For all valid frames the least efficient frame is used as the reference:

```text
reference = min(target_power_fraction)
recommended_equalization_factor_i = reference / target_power_fraction_i
```

The factor is limited to `0 ... 1`. It therefore only attenuates brighter/more efficient frames down to the reference frame and never asks for more optical power than the least efficient frame requires.

The resulting column is:

```text
recommended_laser_or_duty_factor
```

This value is a recommendation for synchronized laser-power or duty-cycle control. It is not automatically encoded into the phase-only DOE.

## Preserve geometric brightness

For rotating-object animations an optional geometric factor can be included:

```text
geometric_factor = abs(cos(frame_angle)) ** gamma
```

The final recommendation is then:

```text
recommended_laser_or_duty_factor = equalization_factor * geometric_factor
```

This allows an edge-on object to become intentionally darker instead of forcing every rotation angle to identical apparent brightness.

## Passive film limitation

If the disc is illuminated by a completely constant, unsynchronized laser and there is no additional amplitude-control mechanism, the recommended attenuation factors cannot by themselves remove frame-to-frame brightness variation.

A later extension could encode controlled power dumping/background into the phase optimization. That is deliberately separate from the initial batch architecture because it changes the optimization objective rather than merely the file workflow.
