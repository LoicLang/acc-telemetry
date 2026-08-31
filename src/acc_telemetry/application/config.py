"""Validated, immutable settings for telemetry processing."""

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import yaml


class ConfigurationError(ValueError):
    """Raised when versioned telemetry settings are incomplete or invalid."""


@dataclass(frozen=True)
class PositionSettings:
    frequency_threshold: float
    max_jump_per_frame: float


@dataclass(frozen=True)
class OCRSettings:
    max_speed_delta_kmh: int
    recovery_tolerance_kmh: int


@dataclass(frozen=True)
class NormalizationSettings:
    speed_min_kmh: float
    speed_max_kmh: float
    pedal_min_percent: float
    pedal_max_percent: float


@dataclass(frozen=True)
class ProfileSettings:
    name: str
    rois: Mapping[str, Mapping[str, int]]
    white_lower: tuple[int, int, int]
    white_upper: tuple[int, int, int]
    sample_count: int


@dataclass(frozen=True)
class TelemetrySettings:
    position: PositionSettings
    ocr: OCRSettings
    normalization: NormalizationSettings
    profiles: Mapping[str, ProfileSettings]

    def profile(self, name: str) -> ProfileSettings:
        try:
            return self.profiles[name]
        except KeyError as error:
            available = ", ".join(sorted(self.profiles))
            raise ConfigurationError(
                f"Unknown ROI profile '{name}'. Available profiles: {available}"
            ) from error


def _mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{path} must be a mapping")
    return value


def _number(mapping: Mapping[str, Any], key: str, path: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(f"{path}.{key} must be numeric")
    return float(value)


def _hsv(value: Any, path: str) -> tuple[int, int, int]:
    if not isinstance(value, list) or len(value) != 3:
        raise ConfigurationError(f"{path} must contain three integers")
    if any(isinstance(item, bool) or not isinstance(item, int) for item in value):
        raise ConfigurationError(f"{path} must contain three integers")
    hue, saturation, brightness = value
    if not (0 <= hue <= 180 and 0 <= saturation <= 255 and 0 <= brightness <= 255):
        raise ConfigurationError(f"{path} contains an out-of-range HSV value")
    return hue, saturation, brightness


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigurationError(f"Configuration file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        return _mapping(yaml.safe_load(handle), str(path))


def load_settings(root: Path | str | None = None) -> TelemetrySettings:
    """Load and validate shared thresholds and every ROI profile."""
    project_root = Path(root) if root is not None else Path(__file__).parents[3]
    telemetry = _load_yaml(project_root / "config" / "telemetry.yaml")
    roi_profiles = _load_yaml(project_root / "config" / "roi_config.yaml")

    position_raw = _mapping(telemetry.get("position"), "position")
    frequency_threshold = _number(position_raw, "frequency_threshold", "position")
    max_jump = _number(position_raw, "max_jump_per_frame", "position")
    if not 0 < frequency_threshold <= 1:
        raise ConfigurationError("position.frequency_threshold must be in (0, 1]")
    if max_jump <= 0:
        raise ConfigurationError("position.max_jump_per_frame must be positive")

    ocr_raw = _mapping(telemetry.get("ocr"), "ocr")
    max_speed_delta = _number(ocr_raw, "max_speed_delta_kmh", "ocr")
    recovery_tolerance = _number(ocr_raw, "recovery_tolerance_kmh", "ocr")
    if max_speed_delta <= 0 or recovery_tolerance < 0:
        raise ConfigurationError("OCR speed thresholds are invalid")

    normalization_raw = _mapping(telemetry.get("normalization"), "normalization")
    speed_min = _number(normalization_raw, "speed_min_kmh", "normalization")
    speed_max = _number(normalization_raw, "speed_max_kmh", "normalization")
    pedal_min = _number(normalization_raw, "pedal_min_percent", "normalization")
    pedal_max = _number(normalization_raw, "pedal_max_percent", "normalization")
    if not speed_min < speed_max:
        raise ConfigurationError("normalization speed range is invalid")
    if not 0 <= pedal_min < pedal_max <= 100:
        raise ConfigurationError("normalization pedal range is invalid")

    profiles: dict[str, ProfileSettings] = {}
    for name, raw_value in roi_profiles.items():
        raw = _mapping(raw_value, f"profiles.{name}")
        rois: dict[str, Mapping[str, int]] = {}
        required_rois = ("throttle", "brake", "steering")
        for roi_name in required_rois:
            if roi_name not in raw:
                raise ConfigurationError(f"profiles.{name}.{roi_name} must be a mapping")
        for roi_name, roi_value in raw.items():
            if roi_name == "position_tracking":
                continue
            if not isinstance(roi_value, dict) or not {"x", "y", "width", "height"}.issubset(roi_value):
                continue
            roi = _mapping(roi_value, f"profiles.{name}.{roi_name}")
            coordinates: dict[str, int] = {}
            for coordinate in ("x", "y", "width", "height"):
                value = roi.get(coordinate)
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ConfigurationError(
                        f"profiles.{name}.{roi_name}.{coordinate} must be an integer"
                    )
                if coordinate in ("width", "height") and value <= 0:
                    raise ConfigurationError(
                        f"profiles.{name}.{roi_name}.{coordinate} must be positive"
                    )
                coordinates[coordinate] = value
            rois[roi_name] = MappingProxyType(coordinates)

        tracking = _mapping(raw.get("position_tracking", {}), f"profiles.{name}.position_tracking")
        lower = _hsv(tracking.get("white_lower", [0, 0, 210]), f"profiles.{name}.white_lower")
        upper = _hsv(tracking.get("white_upper", [180, 30, 255]), f"profiles.{name}.white_upper")
        sample_count = tracking.get("sample_count", 11)
        if isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count <= 0:
            raise ConfigurationError(f"profiles.{name}.sample_count must be a positive integer")
        profiles[name] = ProfileSettings(
            name=name,
            rois=MappingProxyType(rois),
            white_lower=lower,
            white_upper=upper,
            sample_count=sample_count,
        )

    return TelemetrySettings(
        position=PositionSettings(frequency_threshold, max_jump),
        ocr=OCRSettings(int(max_speed_delta), int(recovery_tolerance)),
        normalization=NormalizationSettings(speed_min, speed_max, pedal_min, pedal_max),
        profiles=MappingProxyType(profiles),
    )
