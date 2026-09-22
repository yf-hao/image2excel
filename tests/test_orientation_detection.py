import unittest

import numpy as np

from image2excel.models import TextBox
from image2excel.pipeline import ImageProcessor


def _text_box(text: str, score: float = 0.9) -> TextBox:
    return TextBox(
        text=text,
        score=score,
        points=((0, 0), (100, 0), (100, 20), (0, 20)),
    )


class _FakeOcr:
    def __init__(self):
        self.calls = 0

    def recognize(self, _image):
        self.calls += 1
        return [
            _text_box("姓名"),
            _text_box("学号"),
            _text_box("202401234567"),
        ]


class OrientationDetectionTests(unittest.TestCase):
    def test_reliable_result_stops_orientation_detection(self):
        ocr = _FakeOcr()
        processor = ImageProcessor(ocr)

        angle, _ = processor._choose_orientation(
            np.zeros((100, 100, 3), dtype=np.uint8),
            page_index=1,
        )

        self.assertEqual(angle, 0)
        self.assertEqual(ocr.calls, 1)

    def test_full_orientation_checks_all_four_angles(self):
        ocr = _FakeOcr()
        processor = ImageProcessor(ocr)

        processor._choose_orientation(
            np.zeros((100, 100, 3), dtype=np.uint8),
            page_index=1,
            full_orientation=True,
        )

        self.assertEqual(ocr.calls, 4)


if __name__ == "__main__":
    unittest.main()
