from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

import numpy as np

from .models import Point, TextBox


class OcrEngine:
    """Small compatibility wrapper for PaddleOCR 2.x and 3.x result formats."""

    def __init__(self) -> None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                "未安装 PaddleOCR。请先执行 `conda activate image2excel`，"
                "再执行 `python -m pip install -e .`。"
            ) from exc

        try:
            self._ocr = PaddleOCR(
                lang="ch",
                use_angle_cls=True,
                show_log=False,
            )
        except TypeError:
            self._ocr = PaddleOCR(
                lang="ch",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=True,
            )

    def recognize(self, image: np.ndarray) -> list[TextBox]:
        """Recognize text and normalize PaddleOCR's version-dependent output."""
        if image is None or image.size == 0:
            return []

        try:
            result = self._ocr.ocr(image, cls=True)
        except (AttributeError, TypeError):
            result = list(self._ocr.predict(image))

        boxes = self._parse_legacy_result(result)
        if boxes:
            return boxes
        return self._parse_predict_result(result)

    def _parse_legacy_result(self, result: Any) -> list[TextBox]:
        if not isinstance(result, (list, tuple)) or not result:
            return []

        first = result[0]
        if first is None:
            return []
        if isinstance(first, dict) or hasattr(first, "json"):
            return []

        # PaddleOCR 2.x returns: [[[points], (text, score)], ...].
        if isinstance(first, (list, tuple)) and first:
            candidates = first if self._looks_like_detection_list(first) else result
        else:
            return []

        parsed: list[TextBox] = []
        for item in candidates:
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue
            points, text_score = item[0], item[1]
            if not isinstance(text_score, (list, tuple)) or len(text_score) < 2:
                continue
            text, score = text_score[0], text_score[1]
            points = self._to_points(points)
            if points and isinstance(text, str):
                parsed.append(TextBox(text, self._to_float(score), tuple(points)))
        return parsed

    @staticmethod
    def _looks_like_detection_list(value: list[Any] | tuple[Any, ...]) -> bool:
        first = value[0]
        return (
            isinstance(first, (list, tuple))
            and len(first) >= 2
            and isinstance(first[1], (list, tuple))
        )

    def _parse_predict_result(self, result: Any) -> list[TextBox]:
        parsed: list[TextBox] = []
        if not isinstance(result, Iterable) or isinstance(result, (str, bytes, dict)):
            result = [result]

        for item in result:
            data = self._result_to_dict(item)
            if not data:
                continue
            if "res" in data and isinstance(data["res"], dict):
                data = data["res"]

            texts = data.get("rec_texts", data.get("texts", []))
            scores = data.get("rec_scores", data.get("scores", []))
            boxes = data.get("rec_boxes", data.get("dt_polys", data.get("boxes", [])))
            for text, score, box in zip(texts or [], scores or [], boxes or []):
                points = self._to_points(box)
                if points and isinstance(text, str):
                    parsed.append(TextBox(text, self._to_float(score), tuple(points)))
        return parsed

    @staticmethod
    def _result_to_dict(result: Any) -> dict[str, Any]:
        if isinstance(result, dict):
            return result
        raw = getattr(result, "json", None)
        if callable(raw):
            raw = raw()
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return {}
        return raw if isinstance(raw, dict) else {}

    @staticmethod
    def _to_points(value: Any) -> list[Point]:
        try:
            array = np.asarray(value, dtype=float)
            if array.size < 4:
                return []
            array = array.reshape(-1, 2)
            return [(float(x), float(y)) for x, y in array]
        except (TypeError, ValueError):
            return []

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
