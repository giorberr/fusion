"""Local bounds regression tests; fake geometry is not Fusion integration proof."""

from itertools import product
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from _support import Collection, load_script


class Point:
    def __init__(self, values):
        self.values = tuple(values)

    @classmethod
    def create(cls, x, y, z):
        return cls((x, y, z))

    def asArray(self):
        return self.values

    def transformBy(self, transform):
        self.values = transform.apply(self.values)
        return True


class Transform:
    def __init__(
        self, translation=(0, 0, 0), rotation=((1, 0, 0), (0, 1, 0), (0, 0, 1))
    ):
        self.translation = translation
        self.rotation = rotation
        self.inputs = []

    def apply(self, values):
        self.inputs.append(tuple(values))
        return tuple(
            sum(a * b for a, b in zip(row, values)) + offset
            for row, offset in zip(self.rotation, self.translation)
        )


def box(low, high):
    return SimpleNamespace(minPoint=Point(low), maxPoint=Point(high))


def occurrence(boxes=(), *, transform=None, children=(), meshes=0, reported=None):
    return SimpleNamespace(
        boundingBox=reported,
        transform2=Transform() if transform is None else transform,
        component=SimpleNamespace(
            bRepBodies=Collection(SimpleNamespace(preciseBoundingBox=b) for b in boxes),
            meshBodies=Collection([object()] * meshes),
        ),
        childOccurrences=Collection(children),
    )


def summary(included=0, missing=0, meshes=0):
    return {
        "bounds_brep_bodies_included": included,
        "bounds_brep_bodies_missing": missing,
        "bounds_mesh_bodies_excluded": meshes,
    }


class BoundsTests(unittest.TestCase):
    def setUp(self):
        self.script = load_script("inspect_design.py", point_type=Point)
        self.units = SimpleNamespace(
            convert=Mock(side_effect=lambda v, src, dst: v * 10)
        )

    def assert_corners(self, transform, low, high):
        # Count duplicates too: every native corner must be transformed exactly once.
        self.assertCountEqual(transform.inputs, product(*zip(low, high)))

    def assert_fallback(self, row, status, counts):
        self.assertEqual(row["bounds_frame"], "occurrence assembly context")
        self.assertEqual(row["bounds_status"], status)
        self.assertEqual(row["bounds_source"], "transformed_native_brep_boxes")
        self.assertIs(row["bounds_is_conservative"], True)
        self.assertIn("excludes meshes", row["bounds_scope"])
        self.assertIn("does not prove the occurrence is empty", row["bounds_warning"])
        self.assertIn("overestimate rotated geometry", row["bounds_warning"])
        for key, value in counts.items():
            self.assertEqual(row[key], value)

    def test_box_limits_rejects_absent_points_and_inversions(self):
        invalid = [None, box((0, 0, 0), (0, 0, 0)), box((-3, 2, 5), (-3, 2, 5))]
        for axis in range(3):
            high = [1, 1, 1]
            high[axis] = -1
            invalid.append(box((0, 0, 0), high))
        for bounds in invalid:
            with self.subTest(bounds=bounds):
                self.assertIsNone(self.script.box_limits(bounds))

    def test_box_limits_rejects_nonfinite_values_in_either_endpoint(self):
        for value, endpoint, axis in product(
            (float("nan"), float("inf"), -float("inf")), range(2), range(3)
        ):
            with self.subTest(value=value, endpoint=endpoint, axis=axis):
                endpoints = [[-1, -2, -3], [1, 2, 3]]
                endpoints[endpoint][axis] = value
                self.assertIsNone(self.script.box_limits(box(*endpoints)))

    def test_box_limits_accepts_negative_planar_and_linear_boxes(self):
        pairs = [((-8, -6, -4), (-2, -1, -1)), ((0, 0, 0), (0, 0, 2))]
        for axis in range(3):
            low, high = [-1, -2, -3], [1, 2, 3]
            high[axis] = low[axis]
            pairs.append((low, high))
        for low, high in pairs:
            with self.subTest(low=low, high=high):
                self.assertEqual(
                    self.script.box_limits(box(low, high)), (list(low), list(high))
                )

    def test_definition_translates_negative_coordinates_once(self):
        low, high = (-4, -3, -2), (-1, -1, 1)
        transform = Transform(translation=(-10, 5, -7))
        occ = occurrence([box(low, high)], transform=transform)
        self.assertEqual(
            self.script.definition_bounds_in_context(occ),
            (([-14, 2, -9], [-11, 4, -6]), summary(included=1)),
        )
        self.assert_corners(transform, low, high)

    def test_definition_rotates_all_eight_corners(self):
        # This orthonormal rotation has extrema at mixed corners, not the min/max pair.
        third = 1 / 3
        transform = Transform(
            rotation=(
                (third, -2 * third, 2 * third),
                (2 * third, 2 * third, third),
                (-2 * third, third, 2 * third),
            )
        )
        low, high = (0, 0, 0), (3, 6, 9)
        limits, counts = self.script.definition_bounds_in_context(
            occurrence([box(low, high)], transform=transform)
        )
        for actual, expected in zip(limits[0] + limits[1], [-4, 0, -2, 7, 9, 8]):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(counts, summary(included=1))
        self.assert_corners(transform, low, high)

    def test_nested_children_already_have_root_context(self):
        grandchild = occurrence(
            [box((-1, -1, -1), (1, 1, 1))], transform=Transform((-20, -30, -40))
        )
        child = occurrence(
            [box((0, 0, 0), (2, 3, 4))],
            transform=Transform((110, -5, -2)),
            children=[grandchild],
        )
        parent = occurrence(
            [box((0, 0, 0), (1, 1, 1))],
            transform=Transform((100, 0, 0)),
            children=[child],
        )
        self.assertEqual(
            self.script.definition_bounds_in_context(parent),
            (([-21, -31, -41], [112, 1, 2]), summary(included=3)),
        )
        for occ in (parent, child, grandchild):
            native = occ.component.bRepBodies.item(0).preciseBoundingBox
            self.assert_corners(
                occ.transform2, native.minPoint.asArray(), native.maxPoint.asArray()
            )

    def test_definition_tracks_partial_brep_planar_bodies_and_excluded_meshes(self):
        child = occurrence(
            [box((0, 0, 0), (0, 2, 3))], transform=Transform((10, 0, 0)), meshes=3
        )
        occ = occurrence(
            [
                box((-5, -4, -3), (-1, 2, 3)),
                None,
                box((0, 0, 0), (0, 0, 0)),
                box((0, 0, 0), (float("nan"), 1, 1)),
            ],
            meshes=2,
            children=[child],
        )
        self.assertEqual(
            self.script.definition_bounds_in_context(occ),
            (([-5, -4, -3], [10, 2, 3]), summary(included=2, missing=3, meshes=5)),
        )
        self.assert_corners(child.transform2, (0, 0, 0), (0, 2, 3))

    def test_definition_without_valid_brep_returns_none_and_counts(self):
        for boxes, meshes in (([], 0), ([None], 0), ([], 2), ([None], 2)):
            with self.subTest(boxes=boxes, meshes=meshes):
                occ = occurrence(boxes, meshes=meshes)
                self.assertEqual(
                    self.script.definition_bounds_in_context(occ),
                    (None, summary(missing=len(boxes), meshes=meshes)),
                )
                self.assertEqual(occ.transform2.inputs, [])

    def test_valid_occurrence_box_is_used_directly_in_millimeters(self):
        for low, high in (((-3, -2, -1), (1, 2, 3)), ((-3, -2, 0), (1, 2, 0))):
            with self.subTest(low=low, high=high):
                self.units.convert.reset_mock()
                # No component or transform is available on this direct-bounds fixture.
                occ = SimpleNamespace(boundingBox=box(low, high))
                with patch.object(
                    self.script, "definition_bounds_in_context"
                ) as fallback:
                    row = self.script.occurrence_bounds(occ, self.units)
                fallback.assert_not_called()
                self.assertEqual(
                    row,
                    {
                        "bounds_frame": "occurrence assembly context",
                        "bounds_status": "reported",
                        "bounds_source": "Occurrence.boundingBox",
                        "bounds_scope": "API occurrence bounds; not guaranteed tight",
                        "bounds_min_mm": [v * 10 for v in low],
                        "bounds_max_mm": [v * 10 for v in high],
                    },
                )
                self.assertEqual(
                    self.units.convert.call_args_list,
                    [call(v, "cm", "mm") for v in low + high],
                )

    def test_invalid_occurrence_boxes_use_transformed_fallback(self):
        invalid = [
            None,
            box((0, 0, 0), (0, 0, 0)),
            box((5, 5, 5), (5, 5, 5)),
            box((1, 0, 0), (0, 1, 1)),
            box((0, 0, 0), (float("nan"), 1, 1)),
            box((0, 0, 0), (float("inf"), 1, 1)),
        ]
        for reported in invalid:
            with self.subTest(reported=reported):
                self.units.convert.reset_mock()
                occ = occurrence(
                    [box((-2, -1, 0), (1, 3, 2))],
                    transform=Transform((-5, -4, -3)),
                    reported=reported,
                )
                row = self.script.occurrence_bounds(occ, self.units)
                self.assert_fallback(row, "fallback", summary(included=1))
                self.assertEqual(row["bounds_min_mm"], [-70, -50, -30])
                self.assertEqual(row["bounds_max_mm"], [-40, -10, -10])
                self.assertEqual(
                    self.units.convert.call_args_list,
                    [call(v, "cm", "mm") for v in (-7, -5, -3, -4, -1, -1)],
                )

    def test_occurrence_fallback_status_and_unavailable_coordinates(self):
        valid = box((-1, -2, 0), (1, 2, 0))
        cases = [
            ([valid], 2, "fallback", summary(included=1, meshes=2)),
            ([valid, None], 2, "partial_fallback", summary(1, 1, 2)),
            ([], 0, "unavailable", summary()),
            ([None], 0, "unavailable", summary(missing=1)),
            ([], 2, "unavailable", summary(meshes=2)),
            ([None], 2, "unavailable", summary(missing=1, meshes=2)),
        ]
        for boxes, meshes, status, counts in cases:
            with self.subTest(status=status, counts=counts):
                self.units.convert.reset_mock()
                row = self.script.occurrence_bounds(
                    occurrence(boxes, meshes=meshes), self.units
                )
                self.assert_fallback(row, status, counts)
                if status == "unavailable":
                    self.assertNotIn("bounds_min_mm", row)
                    self.assertNotIn("bounds_max_mm", row)
                    self.units.convert.assert_not_called()
                else:
                    self.assertEqual(row["bounds_min_mm"], [-10, -20, 0])
                    self.assertEqual(row["bounds_max_mm"], [10, 20, 0])

    def test_transform_failure_and_exceptions_propagate_through_both_apis(self):
        occ = occurrence([box((0, 0, 0), (1, 2, 3))])
        operations = (
            self.script.definition_bounds_in_context,
            lambda occ: self.script.occurrence_bounds(occ, self.units),
        )
        for operation in operations:
            with self.subTest(operation=operation):
                with patch.object(Point, "transformBy", return_value=False):
                    with self.assertRaisesRegex(RuntimeError, "Could not transform"):
                        operation(occ)
                error = ValueError("transform API failed")
                with patch.object(Point, "transformBy", side_effect=error):
                    with self.assertRaises(ValueError) as caught:
                        operation(occ)
                self.assertIs(caught.exception, error)
        self.units.convert.assert_not_called()

    def test_nonfinite_transformed_corners_raise_in_both_apis(self):
        for value in (float("nan"), float("inf"), -float("inf")):
            for operation in (
                self.script.definition_bounds_in_context,
                lambda occ: self.script.occurrence_bounds(occ, self.units),
            ):
                with self.subTest(value=value, operation=operation):
                    occ = occurrence(
                        [box((0, 0, 0), (1, 2, 3))], transform=Transform((value, 0, 0))
                    )
                    with self.assertRaisesRegex(
                        RuntimeError, "Transformed bounds are nonfinite"
                    ):
                        operation(occ)
        self.units.convert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
