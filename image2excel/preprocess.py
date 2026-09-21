from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def read_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"无法读取图片：{path}")
    return image


def rotate_image(image: np.ndarray, clockwise_degrees: int) -> np.ndarray:
    normalized = clockwise_degrees % 360
    if normalized == 0:
        return image
    if normalized == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    if normalized == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    if normalized == 270:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    raise ValueError(f"旋转角度必须是0、90、180或270：{clockwise_degrees}")


def enhance_for_ocr(image: np.ndarray) -> np.ndarray:
    """Improve contrast without erasing thin printed strokes."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)


def correct_perspective(image: np.ndarray) -> np.ndarray:
    """Warp only when a reliable large page quadrilateral is found."""
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 40, 140)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidate: np.ndarray | None = None
    image_area = float(height * width)
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:20]:
        area = cv2.contourArea(contour)
        if area < image_area * 0.55:
            continue
        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(polygon) == 4 and cv2.isContourConvex(polygon):
            candidate = polygon.reshape(4, 2).astype(np.float32)
            break

    if candidate is None:
        return image

    ordered = _order_corners(candidate)
    target_width = max(_distance(ordered[0], ordered[1]), _distance(ordered[2], ordered[3]))
    target_height = max(_distance(ordered[0], ordered[3]), _distance(ordered[1], ordered[2]))
    if target_width < 100 or target_height < 100:
        return image

    destination = np.array(
        [
            [0, 0],
            [target_width - 1, 0],
            [target_width - 1, target_height - 1],
            [0, target_height - 1],
        ],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(ordered, destination)
    return cv2.warpPerspective(
        image,
        matrix,
        (int(target_width), int(target_height)),
        borderMode=cv2.BORDER_REPLICATE,
    )


def _order_corners(points: np.ndarray) -> np.ndarray:
    ordered = np.zeros((4, 2), dtype=np.float32)
    sums = points.sum(axis=1)
    differences = np.diff(points, axis=1).ravel()
    ordered[0] = points[np.argmin(sums)]
    ordered[2] = points[np.argmax(sums)]
    ordered[1] = points[np.argmin(differences)]
    ordered[3] = points[np.argmax(differences)]
    return ordered


def _distance(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.linalg.norm(first - second))
