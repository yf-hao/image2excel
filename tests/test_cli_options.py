import unittest

from image2excel.cli import build_parser, parse_orientation_spec


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


if __name__ == "__main__":
    unittest.main()
