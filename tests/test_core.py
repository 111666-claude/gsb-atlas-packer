import unittest

from atlas.core import Packer, out_of_bounds, overlapping


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


class SortOrderTest(unittest.TestCase):
    def test_largest_max_side_placed_first(self):
        result = Packer(128, padding=0).pack(
            [("small", 4, 4), ("big", 60, 10), ("mid", 30, 20)])
        self.assertEqual([p["name"] for p in result["placed"]],
                         ["big", "mid", "small"])

    def test_tie_breaks_by_area_then_name(self):
        result = Packer(128, padding=0).pack(
            [("b", 10, 10), ("c", 10, 5), ("a", 10, 10)])
        self.assertEqual([p["name"] for p in result["placed"]],
                         ["a", "b", "c"])


class PaddingTest(unittest.TestCase):
    def test_first_item_top_left_is_padding(self):
        result = Packer(64, padding=2).pack([("a", 10, 10)])
        placed = result["placed"][0]
        self.assertEqual((placed["x"], placed["y"]), (2, 2))

    def test_row_neighbors_keep_padding_gap(self):
        result = Packer(64, padding=2).pack(
            [("a", 18, 18), ("b", 18, 18), ("c", 18, 18)])
        rects = sorted(result["placed"], key=lambda p: p["x"])
        gaps = [rects[i + 1]["x"] - (rects[i]["x"] + rects[i]["w"])
                for i in range(len(rects) - 1)]
        self.assertTrue(gaps)
        self.assertGreaterEqual(min(gaps), 2)

    def test_row_height_is_max_and_next_row_offsets_by_padding(self):
        result = Packer(64, padding=2).pack(
            [("tall", 30, 30), ("short", 10, 10), ("wide", 40, 8)])
        rows = {p["name"]: p for p in result["placed"]}
        self.assertEqual(rows["wide"]["y"], 2)
        self.assertEqual(rows["tall"]["y"], 2 + 8 + 2)
        self.assertEqual(rows["short"]["y"], 2 + 8 + 2)
        self.assertEqual(result["height"], 2 + 8 + 2 + 30 + 2)


class RotationTest(unittest.TestCase):
    def test_rotates_when_only_rotated_fits(self):
        result = Packer(40, padding=2).pack([("banner", 44, 30)])
        placed = result["placed"][0]
        self.assertTrue(placed["rotated"])
        self.assertEqual((placed["w"], placed["h"]), (30, 44))
        self.assertEqual(out_of_bounds(result), 0)

    def test_prefers_unrotated_when_it_fits(self):
        result = Packer(64, padding=2).pack([("a", 20, 10)])
        self.assertFalse(result["placed"][0]["rotated"])

    def test_rotation_disabled_never_marks_and_rejects_unfittable(self):
        result = Packer(40, padding=2, allow_rotate=False).pack(
            [("banner", 44, 30), ("ok", 10, 10)])
        self.assertEqual(result["rejected"], 1)
        self.assertFalse(any(p["rotated"] for p in result["placed"]))


class RejectTest(unittest.TestCase):
    def test_unfittable_in_both_orientations_is_rejected(self):
        result = Packer(64, padding=2).pack([("sky", 80, 70), ("tile", 20, 20)])
        self.assertEqual(result["rejected"], 1)
        self.assertEqual([p["name"] for p in result["placed"]], ["tile"])

    def test_rejected_occupies_no_coordinates(self):
        result = Packer(64, padding=2).pack([("sky", 80, 70), ("tile", 20, 20)])
        placed = result["placed"][0]
        self.assertEqual((placed["x"], placed["y"]), (2, 2))

    def test_placed_items_stay_within_width(self):
        items = [("t%d" % i, 5 + i % 17, 3 + i % 11) for i in range(200)]
        result = Packer(48, padding=1).pack(items)
        self.assertEqual(out_of_bounds(result), 0)
        self.assertEqual(overlapping(result), 0)


class CoverageTest(unittest.TestCase):
    def test_height_is_last_row_plus_padding(self):
        result = Packer(64, padding=2).pack([("a", 30, 30), ("b", 30, 30)])
        self.assertEqual(result["height"], 2 + 30 + 2 + 30 + 2)

    def test_coverage_is_placed_area_over_atlas_area(self):
        result = Packer(64, padding=2).pack([("a", 30, 30), ("b", 30, 30)])
        self.assertAlmostEqual(result["coverage"],
                               2 * 30 * 30 * 100.0 / (64 * result["height"]))


class ScaleTest(unittest.TestCase):
    def test_overlap_checks_do_not_grow_with_placed_count(self):
        items = [("t-%d" % i, 8 + (i % 5), 8 + (i % 3)) for i in range(5000)]
        result = Packer(256, padding=1).pack(items)
        self.assertLessEqual(result["overlap_checks"], 15000)

    def test_ten_thousand_items_pack_in_single_pass(self):
        items = [("t-%d" % i, 4 + (i % 9), 4 + (i % 7)) for i in range(10000)]
        result = Packer(256, padding=1).pack(items)
        self.assertEqual(len(result["placed"]) + result["rejected"], 10000)
        self.assertEqual(out_of_bounds(result), 0)

    def test_repeated_pack_is_deterministic(self):
        items = [("t-%d" % i, 8 + (i % 7), 5 + (i % 4)) for i in range(1000)]
        first = Packer(128, padding=1).pack(items)
        second = Packer(128, padding=1).pack(items)
        self.assertEqual(first["placed"], second["placed"])
        self.assertEqual(first["height"], second["height"])
        self.assertEqual(first["coverage"], second["coverage"])


if __name__ == "__main__":
    unittest.main()
