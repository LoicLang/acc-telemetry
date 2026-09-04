"""OpenCV-bound extraction for generic minimap progress evidence."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, pi

import cv2
import numpy as np

from acc_telemetry.domain.progress import Centerline, RedDotCandidate


_RED_LOWER_1 = np.array([0, 150, 150], dtype=np.uint8)
_RED_UPPER_1 = np.array([10, 255, 255], dtype=np.uint8)
_RED_LOWER_2 = np.array([170, 150, 150], dtype=np.uint8)
_RED_UPPER_2 = np.array([180, 255, 255], dtype=np.uint8)


class CenterlineTopologyError(ValueError):
    """Raised when a stable map mask cannot yield one trustworthy closed cycle."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class VisualProjection:
    """One candidate projected onto one compatible centerline segment."""

    s_visual: float
    distance_px: float
    projected_xy: tuple[float, float]
    centroid: tuple[float, float]


def build_white_probability(
    map_rois: list[np.ndarray],
    *,
    white_lower: tuple[int, int, int],
    white_upper: tuple[int, int, int],
) -> np.ndarray:
    """Aggregate stable white-map evidence without choosing centerline topology."""
    masks = []
    lower = np.array(white_lower, dtype=np.uint8)
    upper = np.array(white_upper, dtype=np.uint8)
    for map_roi in map_rois:
        if map_roi is None or map_roi.size == 0:
            continue
        hsv = cv2.cvtColor(map_roi, cv2.COLOR_BGR2HSV)
        masks.append(cv2.inRange(hsv, lower, upper) > 0)
    if not masks:
        raise ValueError("no valid map ROI")
    return np.mean(np.stack(masks), axis=0).astype(np.float32)


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

    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (candidate.centroid[1], candidate.centroid[0]),
        )
    )


def _thin(binary: np.ndarray) -> np.ndarray:
    """Reduce a binary component to a one-pixel Zhang-Suen skeleton."""
    image = (binary > 0).astype(np.uint8)
    changed = True
    while changed:
        changed = False
        for first_pass in (True, False):
            padded = np.pad(image, 1)
            p2 = padded[:-2, 1:-1]
            p3 = padded[:-2, 2:]
            p4 = padded[1:-1, 2:]
            p5 = padded[2:, 2:]
            p6 = padded[2:, 1:-1]
            p7 = padded[2:, :-2]
            p8 = padded[1:-1, :-2]
            p9 = padded[:-2, :-2]
            neighbours = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            transitions = (
                ((p2 == 0) & (p3 == 1)).astype(np.uint8)
                + ((p3 == 0) & (p4 == 1)).astype(np.uint8)
                + ((p4 == 0) & (p5 == 1)).astype(np.uint8)
                + ((p5 == 0) & (p6 == 1)).astype(np.uint8)
                + ((p6 == 0) & (p7 == 1)).astype(np.uint8)
                + ((p7 == 0) & (p8 == 1)).astype(np.uint8)
                + ((p8 == 0) & (p9 == 1)).astype(np.uint8)
                + ((p9 == 0) & (p2 == 1)).astype(np.uint8)
            )
            if first_pass:
                preserve_a = p2 * p4 * p6 == 0
                preserve_b = p4 * p6 * p8 == 0
            else:
                preserve_a = p2 * p4 * p8 == 0
                preserve_b = p2 * p6 * p8 == 0
            remove = (
                (image == 1)
                & (neighbours >= 2)
                & (neighbours <= 6)
                & (transitions == 1)
                & preserve_a
                & preserve_b
            )
            if np.any(remove):
                image[remove] = 0
                changed = True
    return image


Pixel = tuple[int, int]
PixelGraph = dict[Pixel, set[Pixel]]


def _pixel_graph(skeleton: np.ndarray) -> PixelGraph:
    nodes = {tuple(point) for point in np.argwhere(skeleton > 0)}
    graph: PixelGraph = {node: set() for node in nodes}
    for y, x in nodes:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                neighbour = (y + dy, x + dx)
                if neighbour not in nodes:
                    continue
                if dy != 0 and dx != 0:
                    if (y, x + dx) in nodes or (y + dy, x) in nodes:
                        continue
                graph[(y, x)].add(neighbour)
    return graph


def _connected_components(graph: PixelGraph) -> list[set[Pixel]]:
    remaining = set(graph)
    components: list[set[Pixel]] = []
    while remaining:
        start = min(remaining)
        component = {start}
        stack = [start]
        while stack:
            node = stack.pop()
            for neighbour in graph[node]:
                if neighbour not in component:
                    component.add(neighbour)
                    stack.append(neighbour)
        remaining.difference_update(component)
        components.append(component)
    return components


def _component_masks(binary: np.ndarray) -> tuple[np.ndarray, ...]:
    """Return connected foreground components from largest to smallest."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    labels_present = sorted(
        range(1, count),
        key=lambda label: int(stats[label, cv2.CC_STAT_AREA]),
        reverse=True,
    )
    components = []
    for label in labels_present:
        component = np.zeros_like(binary)
        component[labels == label] = 255
        components.append(component)
    return tuple(components)


def _remove_nodes(graph: PixelGraph, nodes: set[Pixel]) -> None:
    for node in nodes:
        for neighbour in graph.get(node, ()):
            graph[neighbour].discard(node)
        graph.pop(node, None)


def _prune_short_terminal_branches(
    graph: PixelGraph,
    max_branch_length_fraction: float,
) -> PixelGraph:
    graph = {node: set(neighbours) for node, neighbours in graph.items()}
    while True:
        endpoints = [node for node, neighbours in graph.items() if len(neighbours) == 1]
        if not endpoints:
            return graph
        changed = False
        maximum = max(1, int(round(max_branch_length_fraction * len(graph))))
        for endpoint in sorted(endpoints):
            if endpoint not in graph or len(graph[endpoint]) != 1:
                continue
            path = [endpoint]
            previous: Pixel | None = None
            current = endpoint
            while True:
                onward = graph[current] - ({previous} if previous is not None else set())
                if len(graph[current]) != 2 and current != endpoint:
                    break
                if not onward:
                    break
                previous, current = current, next(iter(onward))
                path.append(current)
            if len(graph.get(current, ())) >= 3:
                removable = set(path[:-1])
                if len(removable) > maximum:
                    raise CenterlineTopologyError("excessive_branches")
                _remove_nodes(graph, removable)
                changed = True
        if not changed:
            return graph


def _order_cycle(graph: PixelGraph) -> list[tuple[float, float]]:
    if not graph or any(len(neighbours) != 2 for neighbours in graph.values()):
        if any(len(neighbours) > 2 for neighbours in graph.values()):
            raise CenterlineTopologyError("excessive_branches")
        raise CenterlineTopologyError("no_closed_cycle")
    if len(_connected_components(graph)) != 1:
        raise CenterlineTopologyError("discontinuous_path")

    start = min(graph)
    previous: Pixel | None = None
    current = start
    ordered: list[Pixel] = []
    while True:
        ordered.append(current)
        choices = sorted(
            neighbour for neighbour in graph[current] if neighbour != previous
        )
        following = choices[0]
        if following == start:
            break
        if following in ordered:
            raise CenterlineTopologyError("multiple_cycles")
        previous, current = current, following
    if len(ordered) != len(graph):
        raise CenterlineTopologyError("multiple_cycles")
    return [(float(x), float(y)) for y, x in ordered]


def _cycle_basis(graph: PixelGraph) -> list[list[Pixel]]:
    """Return an undirected fundamental cycle basis in adjacency order."""
    cycles: list[list[Pixel]] = []
    remaining = set(graph)
    while remaining:
        root = min(remaining)
        stack = [root]
        predecessors: dict[Pixel, Pixel] = {root: root}
        used: dict[Pixel, set[Pixel]] = {root: set()}
        while stack:
            node = stack.pop()
            node_used = used[node]
            for neighbour in sorted(graph[node]):
                if neighbour not in used:
                    predecessors[neighbour] = node
                    stack.append(neighbour)
                    used[neighbour] = {node}
                elif neighbour == node:
                    cycles.append([node])
                elif neighbour not in node_used:
                    neighbour_used = used[neighbour]
                    cycle = [neighbour, node]
                    parent = predecessors[node]
                    while parent not in neighbour_used:
                        cycle.append(parent)
                        parent = predecessors[parent]
                    cycle.append(parent)
                    cycles.append(cycle)
                    used[neighbour].add(node)
        remaining.difference_update(predecessors)
    return cycles


def _cycle_length(cycle: list[Pixel]) -> float:
    return sum(
        hypot(
            cycle[(index + 1) % len(cycle)][0] - node[0],
            cycle[(index + 1) % len(cycle)][1] - node[1],
        )
        for index, node in enumerate(cycle)
    )


def _order_dominant_cycle(
    graph: PixelGraph,
    max_artifact_fraction: float,
) -> list[tuple[float, float]]:
    """Keep one dominant cycle when all alternatives are local marker artifacts."""
    cycles = _cycle_basis(graph)
    if not cycles:
        raise CenterlineTopologyError("no_closed_cycle")
    ranked = sorted(
        ((_cycle_length(cycle), cycle) for cycle in cycles),
        key=lambda item: item[0],
        reverse=True,
    )
    dominant_length, dominant = ranked[0]
    maximum_artifact_length = max_artifact_fraction * dominant_length
    if any(length > maximum_artifact_length for length, _ in ranked[1:]):
        raise CenterlineTopologyError("multiple_cycles")

    dominant_nodes = set(dominant)
    excluded = set(graph) - dominant_nodes
    if excluded:
        excluded_graph = {
            node: graph[node] & excluded
            for node in excluded
        }
        maximum_artifact_nodes = max(1, int(round(max_artifact_fraction * len(dominant))))
        if any(
            len(component) > maximum_artifact_nodes
            for component in _connected_components(excluded_graph)
        ):
            raise CenterlineTopologyError("excessive_branches")
    return [(float(x), float(y)) for y, x in dominant]


def _order_component_cycle(
    component: np.ndarray,
    max_branch_length_fraction: float,
) -> list[tuple[float, float]]:
    """Order the usable cycle within one disconnected white component."""
    graph = _pixel_graph(_thin(component))
    graph = _prune_short_terminal_branches(graph, max_branch_length_fraction)
    if all(len(neighbours) == 2 for neighbours in graph.values()):
        return _order_cycle(graph)
    return _order_dominant_cycle(graph, max_branch_length_fraction)


def _closed_path_length(points: list[tuple[float, float]]) -> float:
    return sum(
        hypot(
            points[(index + 1) % len(points)][0] - point[0],
            points[(index + 1) % len(points)][1] - point[1],
        )
        for index, point in enumerate(points)
    )


def _resample_closed_path(
    points: list[tuple[float, float]],
    spacing: float,
) -> Centerline:
    segment_lengths = [
        hypot(
            points[(index + 1) % len(points)][0] - point[0],
            points[(index + 1) % len(points)][1] - point[1],
        )
        for index, point in enumerate(points)
    ]
    cumulative = np.concatenate(([0.0], np.cumsum(segment_lengths)))
    total = float(cumulative[-1])
    targets = np.arange(0.0, total, spacing)
    resampled: list[tuple[float, float]] = []
    for target in targets:
        index = min(
            int(np.searchsorted(cumulative, target, side="right") - 1),
            len(points) - 1,
        )
        segment_length = segment_lengths[index]
        fraction = (target - cumulative[index]) / segment_length
        start = points[index]
        end = points[(index + 1) % len(points)]
        resampled.append(
            (
                start[0] + fraction * (end[0] - start[0]),
                start[1] + fraction * (end[1] - start[1]),
            )
        )
    return Centerline(
        points=tuple(resampled),
        cumulative_length_px=tuple(float(target) for target in targets),
        total_length_px=total,
    )


def build_centerline(
    white_probability: np.ndarray,
    *,
    frequency_threshold: float,
    max_branch_length_fraction: float,
    min_cycle_diagonal_fraction: float,
    resample_spacing_diagonal_fraction: float,
) -> Centerline:
    """Build one ordered centerline or report why topology is not trustworthy."""
    if white_probability.ndim != 2 or white_probability.size == 0:
        raise CenterlineTopologyError("no_closed_cycle")
    binary = (white_probability >= frequency_threshold).astype(np.uint8) * 255
    height, width = white_probability.shape
    diagonal = hypot(height, width)
    minimum_length = min_cycle_diagonal_fraction * diagonal
    components = _component_masks(binary)
    if not components:
        raise CenterlineTopologyError("no_closed_cycle")

    ordered_cycles: list[tuple[float, list[tuple[float, float]]]] = []
    failures: list[str] = []
    for component in components:
        try:
            ordered = _order_component_cycle(
                component,
                max_branch_length_fraction,
            )
        except CenterlineTopologyError as error:
            failures.append(error.reason)
            continue
        ordered_cycles.append((_closed_path_length(ordered), ordered))

    valid_cycles = [
        (length, ordered)
        for length, ordered in ordered_cycles
        if length >= minimum_length
    ]
    if len(valid_cycles) > 1:
        raise CenterlineTopologyError("multiple_cycles")
    if len(valid_cycles) == 1:
        source_length, ordered = valid_cycles[0]
    elif len(ordered_cycles) > 1:
        raise CenterlineTopologyError("multiple_cycles")
    elif len(ordered_cycles) == 1:
        raise CenterlineTopologyError("implausibly_short_path")
    elif len(components) > 1 and all(
        reason == "no_closed_cycle" for reason in failures
    ):
        raise CenterlineTopologyError("discontinuous_path")
    elif failures:
        raise CenterlineTopologyError(failures[0])
    else:
        raise CenterlineTopologyError("no_closed_cycle")

    if source_length < minimum_length:
        raise CenterlineTopologyError("implausibly_short_path")
    spacing = resample_spacing_diagonal_fraction * diagonal
    return _resample_closed_path(ordered, spacing)


def project_candidate(
    candidate: RedDotCandidate,
    centerline: Centerline,
    *,
    max_distance_px: float,
) -> tuple[VisualProjection, ...]:
    """Project one image candidate onto every geometrically compatible segment."""
    indexed_projections: list[tuple[int, VisualProjection]] = []
    candidate_x, candidate_y = candidate.centroid
    for index, start in enumerate(centerline.points):
        end = centerline.points[(index + 1) % len(centerline.points)]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        squared_length = dx * dx + dy * dy
        if squared_length <= 0:
            continue
        fraction = (
            (candidate_x - start[0]) * dx + (candidate_y - start[1]) * dy
        ) / squared_length
        fraction = max(0.0, min(1.0, fraction))
        projected = (
            start[0] + fraction * dx,
            start[1] + fraction * dy,
        )
        distance = hypot(
            candidate_x - projected[0],
            candidate_y - projected[1],
        )
        if distance > max_distance_px:
            continue
        segment_length = squared_length**0.5
        arc_length = (
            centerline.cumulative_length_px[index] + fraction * segment_length
        )
        indexed_projections.append(
            (
                index,
                VisualProjection(
                    s_visual=(arc_length / centerline.total_length_px) % 1.0,
                    distance_px=distance,
                    projected_xy=projected,
                    centroid=candidate.centroid,
                ),
            )
        )
    groups: list[list[VisualProjection]] = []
    previous_index: int | None = None
    for index, projection in indexed_projections:
        if previous_index is None or index != previous_index + 1:
            groups.append([])
        groups[-1].append(projection)
        previous_index = index
    projections = [
        min(
            group,
            key=lambda projection: (
                projection.distance_px,
                projection.s_visual,
            ),
        )
        for group in groups
    ]
    return tuple(
        sorted(
            projections,
            key=lambda projection: (
                projection.distance_px,
                projection.s_visual,
                projection.projected_xy[1],
                projection.projected_xy[0],
            ),
        )
    )
