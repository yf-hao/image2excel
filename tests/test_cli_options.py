import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from image2excel.cli import _default_output_path, build_parser, parse_orientation_spec


class OrientationOptionTests(unittest.TestCase):
    def test_single_orientation_applies_to_all_images(self):
        self.assertEqual(parse_orientation_spec("90", 3), [90, 90, 90])

    def test_per_image_orientations_preserve_order(self):
        self.assertEqual(parse_orientation_spec("0,90,auto", 3), [0, 90, None])

    def test_rejects_mismatched_count(self):
        with self.assertRaises(ValueError):
            parse_orientation_spec("0,90", 3)

    def test_rejects_invalid_angle(self):
        with self.assertRaises(ValueError):
            parse_orientation_spec("45", 1)

    def test_short_orientation_option(self):
        args = build_parser().parse_args(["-o", "90", "one.jpg", "two.jpg"])
        self.assertEqual(args.orientation, "90")

    def test_full_orientation_option(self):
        args = build_parser().parse_args(["--full-orientation", "one.jpg"])
        self.assertTrue(args.full_orientation)

    def test_negative_90_orientation_is_normalized_to_270(self):
        self.assertEqual(parse_orientation_spec("-90", 1), [270])

    def test_default_output_path_uses_timestamp_and_avoids_collision(self):
        with TemporaryDirectory() as directory:
            first_image = Path(directory) / "page1.jpg"
            first_image.touch()
            first = _default_output_path(first_image)
            first.touch()
            second = _default_output_path(first_image)
            self.assertRegex(second.name, r"^image2excel_\d{8}_\d{6}_01\.xlsx$")


if __name__ == "__main__":
    unittest.main()
