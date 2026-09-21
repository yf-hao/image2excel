from __future__ import annotations

from dataclasses import dataclass
from math import floor

import numpy as np

from .models import TextBox


@dataclass(frozen=True)
class Cell:
    row: int
    column: int
    bounds: tuple[int, int, int, int]
    has_anchor: bool


ANCHOR_WORDS = ("座位", "姓名", "学号", "学")


def detect_cells(
    image: np.ndarray,
    boxes: list[TextBox],
    columns: int,
    expected_rows: int,
) -> list[Cell]:
    height, width = image.shape[:2]
    anchors = [box for box in boxes if _is_anchor(box.text)]
    row_groups = _group_positions(
        [box.center_y for box in anchors],
        tolerance=max(28.0, min(110.0, height / max(expected_rows, 1) * 0.45)),
    )

    if not row_groups:
        row_centers = [(index + 0.5) * height / expected_rows for index in range(expected_rows)]
        row_anchors: list[list[TextBox]] = [[] for _ in row_centers]
    else:
        row_centers = [sum(group) / len(group) for group in row_groups]
        row_anchors = [
            [box for box in anchors if _nearest_index(box.center_y, row_centers) == index]
            for index in range(len(row_centers))
        ]

    column_centers = _cluster_column_centers(
        [box.center_x for box in anchors],
        width=width,
        columns=columns,
    )
    if not column_centers:
        column_centers = [
            (index + 0.5) * width / columns for index in range(columns)
        ]

    x_edges = _edges_from_centers(column_centers, width)
    y_edges = _edges_from_centers(row_centers, height)

    cells: list[Cell] = []
    for row_index in range(len(row_centers)):
        for column_index in range(len(column_centers)):
            has_anchor = any(
                _nearest_index(box.center_x, column_centers) == column_index
                for box in row_anchors[row_index]
            )
            x1, x2 = int(x_edges[column_index]), int(x_edges[column_index + 1])
            y1, y2 = int(y_edges[row_index]), int(y_edges[row_index + 1])
            if x2 > x1 and y2 > y1:
                cells.append(
                    Cell(
                        row=row_index + 1,
                        column=column_index + 1,
                        bounds=(max(0, x1), max(0, y1), min(width, x2), min(height, y2)),
                        has_anchor=has_anchor,
                    )
                )
    return cells


def _is_anchor(text: str) -> bool:
    normalized = text.replace(" ", "").replace("：", ":")
    return any(word in normalized for word in ANCHOR_WORDS)


def _group_positions(values: list[float], tolerance: float) -> list[list[float]]:
    if not values:
        return []
    groups: list[list[float]] = []
    for value in sorted(values):
        if not groups or value - sum(groups[-1]) / len(groups[-1]) > tolerance:
            groups.append([value])
        else:
            groups[-1].append(value)
    return groups


def _cluster_column_centers(values: list[float], width: int, columns: int) -> list[float]:
    if not values:
        return []
    groups = _group_positions(values, tolerance=max(25.0, width / (columns * 3)))
    centers = [sum(group) / len(group) for group in groups]
    if len(centers) > columns:
        # OCR may produce separate anchors for the same column. Fall back to
        # normalized equal-width lanes rather than silently dropping records.
        return []
    return centers


def _edges_from_centers(centers: list[float], limit: int) -> list[float]:
    if len(centers) == 1:
        half_width = limit / 2
        return [0.0, float(limit)] if centers[0] else [0.0, half_width]
    edges = [0.0]
    for first, second in zip(centers, centers[1:]):
        edges.append((first + second) / 2)
    edges.append(float(limit))
    return edges


def _nearest_index(value: float, centers: list[float]) -> int:
    return min(range(len(centers)), key=lambda index: abs(value - centers[index]))
