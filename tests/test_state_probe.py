"""Standalone state-probe unit tests using fake adsk modules, not a live session."""

from contextlib import redirect_stdout
from io import StringIO
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from _support import Collection, Design, load_script


class Document(SimpleNamespace):
    @property
    def dataFile(self):
        if not self.isSaved:
            raise AssertionError("An unsaved document's dataFile must not be read")
        return self.saved_data_file


class DirectDesign(Design):
    @property
    def timeline(self):
        raise AssertionError("A direct design's timeline must not be read")


def design_fixture(*, parametric=True):
    part = SimpleNamespace(bRepBodies=Collection(range(3)))
    root = SimpleNamespace(
        bRepBodies=Collection(range(2)),
        allOccurrences=Collection(SimpleNamespace(component=part) for _ in range(7)),
    )
    design = (Design if parametric else DirectDesign)(
        designType=1 if parametric else 0,
        rootComponent=root,
        allComponents=Collection([root, part]),
        userParameters=Collection(range(4)),
        allParameters=Collection(range(9)),
    )
    if parametric:
        design.timeline = SimpleNamespace(count=11, markerPosition=8)
    return design


def document_fixture(design, *, saved=True):
    return Document(
        name="Assembly Ω",
        creationId="creation-123",
        isSaved=saved,
        isModified=True,
        saved_data_file=SimpleNamespace(id="file-456"),
        products=SimpleNamespace(itemByProductType=Mock(return_value=design)),
    )


def probe_module(doc):
    # Deliberately omit activeProduct: the design must come from document.products.
    app = SimpleNamespace(
        version="fake-version",
        activeDocument=doc,
        userInterface=SimpleNamespace(activeCommand="FakeInspectCommand"),
    )
    return load_script("state_probe.py", app=app)


class StateProbeTests(unittest.TestCase):
    def test_application_unavailable(self):
        module = load_script("state_probe.py")
        with self.assertRaisesRegex(RuntimeError, "Application is unavailable"):
            module.probe_state()

    def test_no_document_still_reports_version_and_command(self):
        self.assertEqual(
            probe_module(None).probe_state(),
            {
                "fusion_version": "fake-version",
                "active_command_id": "FakeInspectCommand",
                "document": None,
                "design": None,
                "status": "no_active_document",
            },
        )

    def test_any_identity_guard_rejects_no_document(self):
        for guard in (
            "EXPECTED_DOCUMENT_NAME",
            "EXPECTED_DATA_FILE_ID",
            "EXPECTED_CREATION_ID",
        ):
            for expected in ("expected-target", ""):
                with self.subTest(guard=guard, expected=expected):
                    module = probe_module(None)
                    setattr(module, guard, expected)
                    with self.assertRaisesRegex(
                        RuntimeError, "expected document is not active"
                    ):
                        module.probe_state()

    def test_no_design_product(self):
        for product in (None, SimpleNamespace(productType="CAMProductType")):
            with self.subTest(product=product):
                doc = document_fixture(product)
                result = probe_module(doc).probe_state()
                self.assertEqual(result["status"], "no_design_product")
                self.assertIsNone(result["design"])
                self.assertEqual(result["document"]["data_file_id"], "file-456")
                self.assertEqual(result["active_command_id"], "FakeInspectCommand")
                doc.products.itemByProductType.assert_called_once_with(
                    "DesignProductType"
                )

    def test_parametric_counts_native_definitions_including_root_not_instances(self):
        doc = document_fixture(design_fixture())
        module = probe_module(doc)
        module.EXPECTED_DOCUMENT_NAME = doc.name
        module.EXPECTED_DATA_FILE_ID = "file-456"
        module.EXPECTED_CREATION_ID = doc.creationId
        result = module.probe_state()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["fusion_version"], "fake-version")
        self.assertEqual(result["active_command_id"], "FakeInspectCommand")
        self.assertEqual(
            result["design"],
            {
                "type": "parametric",
                "counts": {
                    "component_definitions_including_root": 2,
                    "occurrences": 7,
                    "native_brep_bodies": 5,
                    "user_parameters": 4,
                    "timeline_items": 11,
                },
                "timeline_marker": 8,
            },
        )
        self.assertEqual(
            result["document"],
            {
                "name": "Assembly Ω",
                "data_file_id": "file-456",
                "creation_id": "creation-123",
                "is_saved": True,
                "is_modified": True,
                "is_modified_after_inspection": True,
            },
        )
        doc.products.itemByProductType.assert_called_once_with("DesignProductType")

    def test_root_bodies_are_counted_without_occurrences(self):
        design = design_fixture()
        design.allComponents = Collection([design.rootComponent])
        design.rootComponent.allOccurrences = Collection()
        counts = probe_module(document_fixture(design)).probe_state()["design"][
            "counts"
        ]
        self.assertEqual(counts["component_definitions_including_root"], 1)
        self.assertEqual(counts["native_brep_bodies"], 2)
        self.assertEqual(counts["occurrences"], 0)

    def test_direct_design_does_not_read_timeline(self):
        doc = document_fixture(design_fixture(parametric=False))
        result = probe_module(doc).probe_state()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            result["design"],
            {
                "type": "direct",
                "counts": {
                    "component_definitions_including_root": 2,
                    "occurrences": 7,
                    "native_brep_bodies": 5,
                    "user_parameters": 4,
                    "timeline_items": None,
                },
                "timeline_marker": None,
            },
        )

    def test_empty_parametric_timeline_reports_zero_not_unavailable(self):
        design = design_fixture()
        design.timeline = SimpleNamespace(count=0, markerPosition=0)
        result = probe_module(document_fixture(design)).probe_state()["design"]
        self.assertEqual(result["counts"]["timeline_items"], 0)
        self.assertEqual(result["timeline_marker"], 0)

    def test_unsaved_identity_does_not_read_data_file(self):
        doc = document_fixture(design_fixture(), saved=False)
        doc.isModified = False
        module = probe_module(doc)
        module.EXPECTED_DOCUMENT_NAME = doc.name
        module.EXPECTED_CREATION_ID = doc.creationId
        result = module.probe_state()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            result["document"],
            {
                "name": "Assembly Ω",
                "data_file_id": None,
                "creation_id": "creation-123",
                "is_saved": False,
                "is_modified": False,
                "is_modified_after_inspection": False,
            },
        )

    def test_wrong_identity_guards_reject_before_design_lookup(self):
        expected = {
            "EXPECTED_DOCUMENT_NAME": "Assembly Ω",
            "EXPECTED_DATA_FILE_ID": "file-456",
            "EXPECTED_CREATION_ID": "creation-123",
        }
        for guard in expected:
            with self.subTest(guard=guard):
                doc = document_fixture(design_fixture())
                module = probe_module(doc)
                for key, value in expected.items():
                    setattr(module, key, value)
                setattr(module, guard, "wrong-target")
                with self.assertRaisesRegex(
                    RuntimeError, "differs from the expected target"
                ):
                    module.probe_state()
                doc.products.itemByProductType.assert_not_called()

    def test_unsaved_document_cannot_match_a_data_file_guard(self):
        doc = document_fixture(design_fixture(), saved=False)
        module = probe_module(doc)
        module.EXPECTED_DATA_FILE_ID = "file-456"
        with self.assertRaisesRegex(RuntimeError, "differs from the expected target"):
            module.probe_state()
        doc.products.itemByProductType.assert_not_called()

    def test_run_prints_one_json_result_with_unicode_identity(self):
        module = probe_module(document_fixture(design_fixture()))
        expected = module.probe_state()
        output = StringIO()
        with redirect_stdout(output):
            module.run("")
        text = output.getvalue()
        self.assertEqual(len(text.splitlines()), 1)
        self.assertIn("Assembly Ω", text)
        self.assertEqual(json.loads(text), expected)


if __name__ == "__main__":
    unittest.main()
