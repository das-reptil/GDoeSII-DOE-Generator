import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class FilmConfig:
    """Configuration for a Gerchberg-Saxton film batch.

    The film workflow intentionally supports only Arbitrary Image / GS DOEs.
    """

    doe_width_px: int = 512
    doe_height_px: int = 512
    pixel_size_nm: float = 500.0
    wavelength_nm: float = 532.0
    target_distance_mm: float = 300.0
    target_width_um: float = 50000.0
    propagation_mode: str = "physical projection"
    gs_iterations: int = 50
    seed: int = 0

    target_x_mm: float = 0.0
    target_y_mm: float = 0.0
    target_pan_deg: float = 0.0
    target_tilt_deg: float = 0.0

    active_threshold: float = 0.05

    ring_pitch_mm: float = 2.5
    ring_radius_mm: float = 0.0
    ring_orientation: str = "tangential"

    brightness_mode: str = "constant reconstructed brightness"
    geometric_gamma: float = 0.5

    def validate(self):
        if int(self.doe_width_px) < 2 or int(self.doe_height_px) < 2:
            raise ValueError("DOE width and height must be at least 2 pixels.")
        if float(self.pixel_size_nm) <= 0:
            raise ValueError("DOE pixel size must be greater than 0 nm.")
        if float(self.wavelength_nm) <= 0:
            raise ValueError("Wavelength must be greater than 0 nm.")
        if float(self.target_distance_mm) <= 0:
            raise ValueError("Target distance must be greater than 0 mm.")
        if float(self.target_width_um) < 0:
            raise ValueError("GS target width must be 0 (fit) or greater than 0 um.")
        if self.propagation_mode not in ("physical projection", "same sampling"):
            raise ValueError("Propagation mode must be physical projection or same sampling.")
        if self.propagation_mode == "physical projection" and (
            abs(float(self.target_pan_deg)) > 1e-12 or abs(float(self.target_tilt_deg)) > 1e-12
        ):
            raise ValueError(
                "Physical projection currently requires pan = 0 deg and tilt = 0 deg. "
                "Use same sampling for a tilted target plane."
            )
        if int(self.gs_iterations) < 1:
            raise ValueError("GS iterations must be at least 1.")
        if not 0.0 <= float(self.active_threshold) < 1.0:
            raise ValueError("Active threshold must be in the range 0 ... <1.")
        if float(self.ring_pitch_mm) <= 0:
            raise ValueError("Ring pitch must be greater than 0 mm.")
        if float(self.ring_radius_mm) < 0:
            raise ValueError("Ring radius must be 0 (auto) or greater than 0 mm.")
        if self.ring_orientation not in ("radial", "tangential", "fixed"):
            raise ValueError("Ring orientation must be radial, tangential or fixed.")
        if self.brightness_mode not in (
            "constant reconstructed brightness",
            "preserve geometric brightness",
            "analysis only",
        ):
            raise ValueError("Unknown brightness mode.")
        if float(self.geometric_gamma) < 0:
            raise ValueError("Geometric gamma must be >= 0.")
        return self

    @property
    def target_width_mm(self):
        return float(self.target_width_um) / 1000.0

    def to_dict(self):
        data = asdict(self)
        data["target_width_mm"] = self.target_width_mm
        return data

    def save(self, file_name):
        path = Path(file_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return str(path)

    @classmethod
    def load(cls, file_name):
        data = json.loads(Path(file_name).read_text(encoding="utf-8"))
        # target_width_mm is a human-readable derived value written by current
        # versions; target_width_um remains the canonical stored field for
        # compatibility with older film project files.
        data.pop("target_width_mm", None)
        return cls(**data).validate()
