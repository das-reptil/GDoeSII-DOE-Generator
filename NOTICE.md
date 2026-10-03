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

This repository is not a verbatim mirror of the original software. It is a standalone DOE-generator adaptation and contains substantial changes, including:

- migration to current Python 3
- standalone DOE-focused user interface
- continuous phase lens generation
- blazed phase grating generation
- binary Fresnel zone plate generation
- vortex / spiral phase generation
- arbitrary-image Gerchberg-Saxton phase synthesis
- Fresnel propagation using NumPy FFTs
- unsigned 16-bit phase PNG output
- 16-bit relief/height-map export with JSON metadata
- material/environment refractive-index contrast for phase-to-height conversion
- off-axis steering by projected angles
- exact off-axis steering using a physical target point `(x, y, z)`
- sampling checks for the added steering phase ramp
- Windows/PyInstaller build automation and automated tests

These changes should not be interpreted as having been authored, reviewed, sponsored or endorsed by the original GDoeSII authors.

## Nanoscribe / GrayScribeX

References to Nanoscribe Quantum X and GrayScribeX describe an intended file/workflow use case only. This project is independent and is not an official Nanoscribe product. Nanoscribe and GrayScribeX names and trademarks belong to their respective owners.

## License

The adapted project is distributed under **CC BY-NC 3.0**. See `LICENSE` and the Creative Commons legal code:

https://creativecommons.org/licenses/by-nc/3.0/legalcode
