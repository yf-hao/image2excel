from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

import cv2
import numpy as np

from .layout import Cell, detect_cells
from .models import StudentRecord, TextBox, text_join
from .ocr_engine import OcrEngine
from .parser import has_student_signal, parse_student
from .preprocess import correct_perspective, enhance_for_ocr, read_image, rotate_image
from .validator import validate_records


ProgressCallback = Callable[[str], None]


class ImageProcessor:
    def __init__(
        self,
        ocr: OcrEngine,
        columns: int = 5,
        expected_rows: int = 7,
        progress: ProgressCallback | None = None,
        full_orientation: bool = False,
    ):
        self.ocr = ocr
        self.columns = columns
        self.expected_rows = expected_rows
        self.progress = progress
        self.full_orientation = full_orientation

    def process(
        self,
        path: Path,
        page_index: int,
        orientation: int | None = None,
    ) -> list[StudentRecord]:
        self._report(f"[第{page_index}页] 正在读取：{path.name}")
        original = read_image(path)
        if orientation is None:
            orientation, _ = self._choose_orientation(
                original,
                page_index,
                full_orientation=self.full_orientation,
            )
        else:
            self._report(f"[第{page_index}页] 使用指定方向：{orientation}°")
        oriented = rotate_image(original, orientation)
        corrected = correct_perspective(oriented)
        enhanced = enhance_for_ocr(corrected)
        page_boxes = self.ocr.recognize(enhanced)
        cells = detect_cells(
            enhanced,
            page_boxes,
            columns=self.columns,
            expected_rows=self.expected_rows,
        )
        self._report(
            f"[第{page_index}页] 方向：{orientation}°，检测到 {len(cells)} 个区域，开始识别"
        )

        records: list[StudentRecord] = []
        for index, cell in enumerate(cells, start=1):
            self._report(f"[第{page_index}页] 识别区域 {index}/{len(cells)}")
            crop = self._crop(enhanced, cell)
            crop_boxes = self.ocr.recognize(crop)
            page_cell_boxes = _boxes_in_cell(page_boxes, cell)
            page_cell_text = text_join(page_cell_boxes)
            crop_fields, crop_confidence, _ = parse_student(crop_boxes)
            page_fields, page_confidence, _ = parse_student(page_cell_boxes)
            if not has_student_signal(crop_fields["raw_text"]) and not has_student_signal(
                page_cell_text
            ):
                continue

            fields = dict(crop_fields)
            for field in ("seat_number", "name", "student_id"):
                if not fields[field]:
                    fields[field] = page_fields[field]
            fields["raw_text"] = crop_fields["raw_text"] or page_fields["raw_text"]
            confidence = max(crop_confidence, page_confidence)
            record = StudentRecord(
                page_index=page_index,
                source_image=path.name,
                column=cell.column,
                row=cell.row,
                seat_number=fields["seat_number"],
                name=fields["name"],
                student_id=fields["student_id"],
                confidence=confidence,
                raw_text=fields["raw_text"],
                orientation=orientation,
                location=cell.bounds,
            )
            records.append(record)

        validate_records(records)
        self._report(f"[第{page_index}页] 完成，提取 {len(records)} 条记录")
        return records

    def _choose_orientation(
        self,
        image: np.ndarray,
        page_index: int,
        full_orientation: bool = False,
    ) -> tuple[int, list[TextBox]]:
        best_angle = 0
        best_boxes: list[TextBox] = []
        best_score = float("-inf")
        angles = (0, 90, 180, 270)
        for index, angle in enumerate(angles, start=1):
            self._report(f"[第{page_index}页] 方向检测 {index}/4（{angle}°）")
            rotated = rotate_image(image, angle)
            sample = _resize_for_detection(rotated)
            boxes = self.ocr.recognize(enhance_for_ocr(sample))
            score = _orientation_score(boxes)
            if score > best_score:
                best_angle, best_boxes, best_score = angle, boxes, score
            if not full_orientation and _is_reliable_orientation(boxes):
                self._report(f"[第{page_index}页] 方向检测提前结束：{angle}°")
                return angle, boxes
        return best_angle, best_boxes

    @staticmethod
    def _crop(image: np.ndarray, cell: Cell) -> np.ndarray:
        x1, y1, x2, y2 = cell.bounds
        return image[y1:y2, x1:x2]

    def _report(self, message: str) -> None:
        if self.progress is not None:
            self.progress(message)


def process_images(
    paths: list[Path],
    columns: int = 5,
    expected_rows: int = 7,
    orientations: list[int | None] | None = None,
    progress: ProgressCallback | None = None,
    full_orientation: bool = False,
) -> list[StudentRecord]:
    if orientations is None:
        orientations = [None] * len(paths)
    if len(orientations) != len(paths):
        raise ValueError("方向数量必须为1个或与图片数量相同。")

    processor = ImageProcessor(
        OcrEngine(),
        columns=columns,
        expected_rows=expected_rows,
        progress=progress,
        full_orientation=full_orientation,
    )
    records: list[StudentRecord] = []
    for page_index, (path, orientation) in enumerate(
        zip(paths, orientations),
        start=1,
    ):
        records.extend(processor.process(path, page_index, orientation))
    return records


def _orientation_score(boxes: list[TextBox]) -> float:
    anchor_count = sum(
        1
        for box in boxes
        if any(word in box.text.replace(" ", "") for word in ("座位", "姓名", "学号"))
    )
    id_count = sum(1 for box in boxes if re.search(r"20\d{8,20}", box.text))
    confidence = sum(box.score for box in boxes)
    return anchor_count * 10 + id_count * 5 + confidence


def _is_reliable_orientation(boxes: list[TextBox]) -> bool:
    anchor_count = sum(
        1
        for box in boxes
        if any(word in box.text.replace(" ", "") for word in ("座位", "姓名", "学号"))
    )
    id_count = sum(1 for box in boxes if re.search(r"20\d{8,20}", box.text))
    high_confidence_count = sum(1 for box in boxes if box.score >= 0.7)
    return (
        (anchor_count >= 2 and high_confidence_count >= 2)
        or (anchor_count >= 1 and id_count >= 2 and high_confidence_count >= 3)
    )


def _resize_for_detection(image: np.ndarray, max_width: int = 1400) -> np.ndarray:
    height, width = image.shape[:2]
    if width <= max_width:
        return image
    scale = max_width / width
    return cv2.resize(image, (int(width * scale), int(height * scale)))


def _boxes_in_cell(boxes: list[TextBox], cell: Cell) -> list[TextBox]:
    x1, y1, x2, y2 = cell.bounds
    return [
        box
        for box in boxes
        if x1 <= box.center_x <= x2 and y1 <= box.center_y <= y2
    ]
