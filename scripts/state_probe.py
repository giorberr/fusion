"""Submit the complete source to Fusion MCP execute with readOnly=True.

A compact before/after fingerprint, not proof that geometry is unchanged.
Requires Fusion's embedded Python; never saves, recomputes, or changes UI state.
"""

import json
import adsk.core
import adsk.fusion

EXPECTED_DOCUMENT_NAME = None
EXPECTED_DATA_FILE_ID = None
EXPECTED_CREATION_ID = None


def probe_state():
    app = adsk.core.Application.get()
    if app is None:
        raise RuntimeError("Fusion Application is unavailable.")
    result = {
        "fusion_version": app.version,
        "active_command_id": app.userInterface.activeCommand,
        "document": None,
        "design": None,
    }
    doc = app.activeDocument
    guards = (EXPECTED_DOCUMENT_NAME, EXPECTED_DATA_FILE_ID, EXPECTED_CREATION_ID)
    if doc is None:
        if any(value is not None for value in guards):
            raise RuntimeError("The expected document is not active.")
        result["status"] = "no_active_document"
        return result
    data_file = doc.dataFile if doc.isSaved else None
    identity = (doc.name, data_file.id if data_file else None, doc.creationId)
    if any(
        expected is not None and expected != actual
        for expected, actual in zip(guards, identity)
    ):
        raise RuntimeError("Active document differs from the expected target.")
    result["document"] = {
        "name": identity[0],
        "data_file_id": identity[1],
        "creation_id": identity[2],
        "is_saved": doc.isSaved,
        "is_modified": doc.isModified,
    }
    design = adsk.fusion.Design.cast(
        doc.products.itemByProductType("DesignProductType")
    )
    if design is None:
        result["status"] = "no_design_product"
        return result
    components = design.allComponents
    body_count = sum(
        components.item(i).bRepBodies.count for i in range(components.count)
    )
    parametric = design.designType == adsk.fusion.DesignTypes.ParametricDesignType
    timeline = design.timeline if parametric else None
    result["design"] = {
        "type": "parametric" if parametric else "direct",
        "counts": {
            "component_definitions_including_root": components.count,
            "occurrences": design.rootComponent.allOccurrences.count,
            "native_brep_bodies": body_count,
            "user_parameters": design.userParameters.count,
            "timeline_items": timeline.count if timeline else None,
        },
        "timeline_marker": timeline.markerPosition if timeline else None,
    }
    result["status"] = "ok"
    result["document"]["is_modified_after_inspection"] = doc.isModified
    return result


def run(_context: str):
    print(json.dumps(probe_state(), ensure_ascii=False))
