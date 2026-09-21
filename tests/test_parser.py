import unittest

from image2excel.models import TextBox
from image2excel.parser import has_student_signal, parse_student


class ParserTests(unittest.TestCase):
    def test_extracts_student_fields(self):
        boxes = [
            TextBox("座位号：37", 0.99, ((0, 0), (100, 0), (100, 20), (0, 20))),
            TextBox("姓名：张三", 0.98, ((0, 20), (100, 20), (100, 40), (0, 40))),
            TextBox("学号：2025101510154", 0.97, ((0, 40), (150, 40), (150, 60), (0, 60))),
        ]
        fields, confidence, _ = parse_student(boxes)
        self.assertEqual(fields["seat_number"], "37")
        self.assertEqual(fields["name"], "张三")
        self.assertEqual(fields["student_id"], "2025101510154")
        self.assertGreater(confidence, 0.9)

    def test_ignores_signature_only_cell(self):
        self.assertFalse(has_student_signal("签名："))

    def test_ignores_empty_student_template(self):
        self.assertFalse(has_student_signal("座位号：\n姓名：\n学号："))

    def test_detects_generic_student_id(self):
        boxes = [
            TextBox("2025101510154", 0.9, ((0, 0), (120, 0), (120, 20), (0, 20))),
        ]
        fields, _, _ = parse_student(boxes)
        self.assertEqual(fields["student_id"], "2025101510154")


if __name__ == "__main__":
    unittest.main()
