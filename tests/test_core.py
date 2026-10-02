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


from atlas.core import Packer, out_of_bounds, overlapping


class SortOrderTest(unittest.TestCase):
    def test_biggest_first_then_area_then_name(self):
        items = [("small", 10, 10), ("tall", 10, 40), ("wide", 40, 12), ("other", 40, 12)]
        result = Packer(200, padding=0).pack(items)
        self.assertEqual(
            [p["name"] for p in result["placed"]],
            ["other", "wide", "tall", "small"],
        )

    def test_same_max_side_larger_area_first(self):
        items = [("slim", 20, 10), ("square", 20, 20)]
        result = Packer(200, padding=0).pack(items)
        self.assertEqual([p["name"] for p in result["placed"]], ["square", "slim"])


class PaddingTest(unittest.TestCase):
    def test_first_rect_at_padding_offset(self):
        result = Packer(64, padding=3).pack([("a", 10, 10)])
        rect = result["placed"][0]
        self.assertEqual((rect["x"], rect["y"]), (3, 3))

    def test_horizontal_gap_and_row_height(self):
        items = [("a", 30, 30), ("b", 30, 20), ("c", 30, 30)]
        result = Packer(64, padding=2).pack(items)
        rects = {p["name"]: p for p in result["placed"]}
        self.assertEqual(rects["a"]["x"], 2)
        self.assertEqual(rects["a"]["y"], 2)
        self.assertEqual(rects["c"]["x"], 2)
        self.assertEqual(rects["c"]["y"], 34)  # 2 + 行高30 + 2
        self.assertEqual(rects["b"]["x"], 34)  # 2 + 30 + 2
        self.assertEqual(rects["b"]["y"], 34)
        self.assertEqual(result["height"], 66)  # 34 + 行高30 + 2

    def test_zero_padding_touches_but_does_not_overlap(self):
        result = Packer(64, padding=0).pack([("a", 10, 10), ("b", 10, 10)])
        a, b = result["placed"]
        self.assertEqual(b["x"] - (a["x"] + a["w"]), 0)
        self.assertEqual(overlapping(result), 0)


class RotationTest(unittest.TestCase):
    def test_rotated_when_only_turned_fits(self):
        result = Packer(40, padding=2).pack([("banner", 44, 30)])
        self.assertEqual(len(result["placed"]), 1)
        rect = result["placed"][0]
        self.assertTrue(rect["rotated"])
        self.assertEqual((rect["w"], rect["h"]), (30, 44))
        self.assertEqual(out_of_bounds(result), 0)

    def test_never_rotated_when_disabled(self):
        result = Packer(40, padding=2, allow_rotate=False).pack([("banner", 44, 30)])
        self.assertEqual(result["placed"], [])
        self.assertEqual(result["rejected"], 1)


class RejectTest(unittest.TestCase):
    def test_too_wide_rect_rejected_without_coordinates(self):
        result = Packer(64, padding=2).pack([("sky", 80, 70), ("tile", 20, 20)])
        self.assertEqual(result["rejected"], 1)
        self.assertEqual([p["name"] for p in result["placed"]], ["tile"])
        self.assertEqual(out_of_bounds(result), 0)

    def test_placed_rects_stay_inside_width(self):
        items = [("n%d" % i, 12 + i % 9, 10 + i % 7) for i in range(50)]
        result = Packer(48, padding=2).pack(items)
        self.assertEqual(out_of_bounds(result), 0)
        for rect in result["placed"]:
            self.assertGreaterEqual(rect["x"], 2)
            self.assertLessEqual(rect["x"] + rect["w"] + 2, 48)


class CoverageTest(unittest.TestCase):
    def test_height_and_coverage_formula(self):
        result = Packer(64, padding=2).pack([("a", 30, 30), ("b", 30, 30)])
        self.assertEqual(result["height"], 66)
        self.assertAlmostEqual(result["coverage"], 1800 * 100.0 / (64 * 66), places=5)

    def test_single_rect_with_padding(self):
        result = Packer(64, padding=2).pack([("a", 10, 10)])
        self.assertEqual(result["height"], 14)  # 2 + 10 + 2
        self.assertAlmostEqual(result["coverage"], 100 * 100.0 / (64 * 14), places=5)


class ScaleAndDeterminismTest(unittest.TestCase):
    def test_overlap_checks_sublinear_in_placed_count(self):
        items = [("t-%d" % i, 8 + (i % 5), 8 + (i % 3)) for i in range(5000)]
        result = Packer(256, padding=1).pack(items)
        placed = len(result["placed"])
        self.assertLess(result["overlap_checks"], placed * 3)
        self.assertEqual(overlapping(result), 0)

    def test_ten_thousand_single_pass(self):
        items = [("t-%d" % i, 8 + (i % 5), 8 + (i % 3)) for i in range(10000)]
        result = Packer(256, padding=1).pack(items)
        self.assertEqual(result["rejected"], 0)
        self.assertEqual(out_of_bounds(result), 0)

    def test_repeated_pack_is_identical(self):
        items = [("n%d" % i, 8 + (i % 13), 8 + (i % 11)) for i in range(500)]
        packer = Packer(128, padding=2)
        first = packer.pack(items)
        second = packer.pack(items)
        self.assertEqual(first, second)
