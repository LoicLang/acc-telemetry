"""OpenCV-bound extraction for generic minimap progress evidence."""

from __future__ import annotations

from math import pi

import cv2
import numpy as np

from acc_telemetry.domain.progress import RedDotCandidate


_RED_LOWER_1 = np.array([0, 150, 150], dtype=np.uint8)
_RED_UPPER_1 = np.array([10, 255, 255], dtype=np.uint8)
_RED_LOWER_2 = np.array([170, 150, 150], dtype=np.uint8)
_RED_UPPER_2 = np.array([180, 255, 255], dtype=np.uint8)


def extract_red_candidates(
    map_roi: np.ndarray | None,
    *,
    min_area_fraction: float,
    max_area_fraction: float,
    min_circularity: float,
) -> tuple[RedDotCandidate, ...]:
    """Return every independently plausible red contour in stable image order."""
    if map_roi is None or map_roi.size == 0:
        return ()

    height, width = map_roi.shape[:2]
    image_area = float(height * width)
    hsv = cv2.cvtColor(map_roi, cv2.COLOR_BGR2HSV)
    red_mask = cv2.bitwise_or(
        cv2.inRange(hsv, _RED_LOWER_1, _RED_UPPER_1),
        cv2.inRange(hsv, _RED_LOWER_2, _RED_UPPER_2),
    )
    contours, _ = cv2.findContours(
        red_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    candidates: list[RedDotCandidate] = []
    for contour in contours:
        area_px = float(cv2.contourArea(contour))
        area_fraction = area_px / image_area
        if not min_area_fraction <= area_fraction <= max_area_fraction:
            continue
        perimeter = float(cv2.arcLength(contour, True))
        if perimeter <= 0:
            continue
        circularity = 4.0 * pi * area_px / (perimeter * perimeter)
        if circularity < min_circularity:
            continue
        moments = cv2.moments(contour)
        if moments["m00"] == 0:
            continue
        centroid = (
            float(moments["m10"] / moments["m00"]),
            float(moments["m01"] / moments["m00"]),
        )
        candidates.append(
            RedDotCandidate(
                centroid=centroid,
                area_px=area_px,
                area_fraction=area_fraction,
                circularity=circularity,
            )
        )

    return tuple(sorted(candidates, key=lambda candidate: (candidate.centroid[1], candidate.centroid[0])))
