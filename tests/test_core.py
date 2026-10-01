import unittest

from atlas.core import Packer, overlapping


class EmptyTest(unittest.TestCase):
    def test_empty_pack_has_no_height(self):
        result = Packer(64).pack([])
        self.assertEqual(result["height"], 0)
        self.assertEqual(result["placed"], [])
        self.assertEqual(result["rejected"], 0)


class ShapeTest(unittest.TestCase):
    def test_width_is_reported(self):
        self.assertEqual(Packer(96).pack([])["width"], 96)

    def test_result_keys_are_stable(self):
        result = Packer(64).pack([("a", 10, 10)])
        for key in ("width", "height", "placed", "rejected", "coverage", "overlap_checks"):
            self.assertIn(key, result)

    def test_names_are_preserved(self):
        result = Packer(64).pack([("a", 10, 10), ("b", 12, 12)])
        self.assertEqual(sorted(p["name"] for p in result["placed"]), ["a", "b"])


class RotateOptionTest(unittest.TestCase):
    def test_no_rotation_when_disabled(self):
        result = Packer(64, allow_rotate=False).pack([("a", 10, 40)])
        self.assertFalse(any(p["rotated"] for p in result["placed"]))

    def test_padding_zero_keeps_touching_rects(self):
        result = Packer(64, padding=0).pack([("a", 10, 10), ("b", 10, 10)])
        self.assertEqual(overlapping(result), 0)


if __name__ == "__main__":
    unittest.main()
