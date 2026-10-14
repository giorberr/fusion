"""Submit this source to Fusion MCP execute with readOnly=True.

Requires Fusion's embedded Python. Adjust constants in the submitted source.
Counts cover native definitions; occurrences represent assembly instances.
"""

import json
from collections import Counter
import adsk.core
import adsk.fusion

EXPECTED_DOCUMENT_NAME = None
EXPECTED_DATA_FILE_ID = None
EXPECTED_CREATION_ID = None
DETAIL_LIMIT = 40
COMPONENT_OFFSET = 0
BODY_OFFSET = 0
SKETCH_OFFSET = 0
OCCURRENCE_OFFSET = 0
PARAMETER_OFFSET = 0
TIMELINE_OFFSET = 0
INCLUDE_GEOMETRY = True
INCLUDE_ENTITY_TOKENS = False


def page(rows, total, offset):
    return {
        "total": total,
        "offset": offset,
        "returned": len(rows),
        "has_more": offset + len(rows) < total,
        "rows": rows,
    }


def indices(total, offset):
    return range(offset, min(total, offset + DETAIL_LIMIT))


def in_page(index, offset):
    return offset <= index < offset + DETAIL_LIMIT


def health_name(state):
    states = adsk.fusion.FeatureHealthStates
    names = {
        int(states.HealthyFeatureHealthState): "healthy",
        int(states.WarningFeatureHealthState): "warning",
        int(states.ErrorFeatureHealthState): "error",
        int(states.SuppressedFeatureHealthState): "suppressed",
        int(states.RolledBackFeatureHealthState): "rolled_back",
        int(states.UnknownFeatureHealthState): "unknown",
    }
    return names.get(int(state), "unrecognized:" + str(state))


def health_message(obj, health):
    return obj.errorOrWarningMessage if health in ("warning", "error") else ""


def inspect_design():
    offsets = (
        COMPONENT_OFFSET,
        BODY_OFFSET,
        SKETCH_OFFSET,
        OCCURRENCE_OFFSET,
        PARAMETER_OFFSET,
        TIMELINE_OFFSET,
    )
    if type(DETAIL_LIMIT) is not int or DETAIL_LIMIT < 1:
        raise ValueError("DETAIL_LIMIT must be a positive integer.")
    if any(type(x) is not int or x < 0 for x in offsets):
        raise ValueError("Offsets must be nonnegative integers.")
    app = adsk.core.Application.get()
    if app is None:
        raise RuntimeError("Fusion Application is unavailable.")
    doc = app.activeDocument
    result = {"fusion_version": app.version, "document": None, "design": None}
    if doc is None:
        if any(
            x is not None
            for x in (
                EXPECTED_DOCUMENT_NAME,
                EXPECTED_DATA_FILE_ID,
                EXPECTED_CREATION_ID,
            )
        ):
            raise RuntimeError("The expected document is not active.")
        result["status"] = "no_active_document"
        return result
    data_file = doc.dataFile if doc.isSaved else None
    file_id = data_file.id if data_file else None
    creation_id = doc.creationId
    if EXPECTED_DOCUMENT_NAME is not None and doc.name != EXPECTED_DOCUMENT_NAME:
        raise RuntimeError("Active document name differs from the target.")
    if EXPECTED_DATA_FILE_ID is not None and file_id != EXPECTED_DATA_FILE_ID:
        raise RuntimeError("Active data-file ID differs from the target.")
    if EXPECTED_CREATION_ID is not None and creation_id != EXPECTED_CREATION_ID:
        raise RuntimeError("Active document creation ID differs from the target.")
    result["document"] = {
        "name": doc.name,
        "data_file_id": file_id,
        "creation_id": creation_id,
        "is_saved": doc.isSaved,
        "is_modified": doc.isModified,
    }
    workspace = app.userInterface.activeWorkspace
    result["workspace"] = (
        {"id": workspace.id, "name": workspace.name} if workspace else None
    )
    result["active_product_type"] = (
        app.activeProduct.productType if app.activeProduct else None
    )
    result["document_product_types"] = [
        doc.products.item(i).productType for i in range(doc.products.count)
    ]
    design = adsk.fusion.Design.cast(
        doc.products.itemByProductType("DesignProductType")
    )
    if design is None:
        result["status"] = "no_design_product"
        return result
    parametric = design.designType == adsk.fusion.DesignTypes.ParametricDesignType
    units, root = design.unitsManager, design.rootComponent
    component_rows, body_rows, sketch_rows = [], [], []
    bodies = meshes = sketches = joints = as_built_joints = fully_constrained = 0
    sketch_health = Counter()
    for ci in range(design.allComponents.count):
        comp = design.allComponents.item(ci)
        if in_page(ci, COMPONENT_OFFSET):
            row = {
                "index": ci,
                "name": comp.name,
                "bodies": comp.bRepBodies.count,
                "mesh_bodies": comp.meshBodies.count,
                "sketches": comp.sketches.count,
                "child_occurrences": comp.occurrences.count,
                "joints": comp.joints.count,
                "as_built_joints": comp.asBuiltJoints.count,
            }
            if INCLUDE_ENTITY_TOKENS:
                row["entity_token"] = comp.entityToken
            component_rows.append(row)
        meshes += comp.meshBodies.count
        joints += comp.joints.count
        as_built_joints += comp.asBuiltJoints.count
        for bi in range(comp.bRepBodies.count):
            if in_page(bodies, BODY_OFFSET):
                body = comp.bRepBodies.item(bi)
                row = {
                    "index": bodies,
                    "component_index": ci,
                    "component": comp.name,
                    "name": body.name,
                    "is_solid": body.isSolid,
                    "is_visible": body.isVisible,
                    "faces": body.faces.count,
                    "edges": body.edges.count,
                }
                if INCLUDE_GEOMETRY:
                    box = body.preciseBoundingBox
                    if box:
                        low, high = box.minPoint.asArray(), box.maxPoint.asArray()
                        row["bounds_frame"] = "native_component"
                        row["bounds_min_mm"] = [
                            units.convert(x, "cm", "mm") for x in low
                        ]
                        row["bounds_max_mm"] = [
                            units.convert(x, "cm", "mm") for x in high
                        ]
                        row["bounds_size_mm"] = [
                            units.convert(high[k] - low[k], "cm", "mm")
                            for k in range(3)
                        ]
                    row["volume_mm3"] = (
                        units.convert(body.volume, "cm^3", "mm^3")
                        if body.isSolid
                        else None
                    )
                if INCLUDE_ENTITY_TOKENS:
                    row["entity_token"] = body.entityToken
                body_rows.append(row)
            bodies += 1
        for si in range(comp.sketches.count):
            sketch = comp.sketches.item(si)
            health = health_name(sketch.healthState)
            constrained = sketch.isFullyConstrained
            sketch_health[health] += 1
            fully_constrained += int(constrained)
            if in_page(sketches, SKETCH_OFFSET):
                sketch_rows.append(
                    {
                        "index": sketches,
                        "component_index": ci,
                        "component": comp.name,
                        "name": sketch.name,
                        "is_parametric": sketch.isParametric,
                        "is_fully_constrained": constrained,
                        "health": health,
                        "message": health_message(sketch, health),
                    }
                )
            sketches += 1
    occurrences = root.allOccurrences
    occurrence_rows = []
    for i in indices(occurrences.count, OCCURRENCE_OFFSET):
        occ = occurrences.item(i)
        row = {
            "index": i,
            "path": occ.fullPathName,
            "component": occ.component.name,
            "is_external_reference": occ.isReferencedComponent,
            "is_visible": occ.isVisible,
            "transform2": occ.transform2.asArray(),
            "transform_context": "occurrence assembly context; translation in cm",
        }
        if INCLUDE_ENTITY_TOKENS:
            row["entity_token"] = occ.entityToken
        occurrence_rows.append(row)
    parameters = design.allParameters
    parameter_rows = []
    for i in indices(parameters.count, PARAMETER_OFFSET):
        p = parameters.item(i)
        parameter_rows.append(
            {"index": i, "name": p.name, "expression": p.expression, "unit": p.unit}
        )
    timeline_summary = {"available": False, "reason": "direct_design"}
    if parametric:
        timeline = design.timeline
        timeline_rows, issue_rows = [], []
        timeline_health = Counter()
        issue_count = 0
        for i in range(timeline.count):
            obj = timeline.item(i)
            health = health_name(obj.healthState)
            timeline_health[health] += 1
            row = {
                "index": i,
                "name": obj.name,
                "health": health,
                "message": health_message(obj, health),
                "is_suppressed": obj.isSuppressed,
                "is_rolled_back": obj.isRolledBack,
            }
            if in_page(i, TIMELINE_OFFSET):
                timeline_rows.append(row)
            if health in ("warning", "error"):
                issue_count += 1
                if len(issue_rows) < DETAIL_LIMIT:
                    issue_rows.append(row)
        timeline_summary = {
            "available": True,
            "count": timeline.count,
            "marker_position": timeline.markerPosition,
            "health_counts": dict(timeline_health),
            "details": page(timeline_rows, timeline.count, TIMELINE_OFFSET),
            "issues": page(issue_rows, issue_count, 0),
        }
    active = design.activeComponent
    result["design"] = {
        "type": "parametric" if parametric else "direct",
        "display_length_unit": units.defaultLengthUnits,
        "root_component": root.name,
        "active_component": active.name if active else None,
        "count_scope": "native definitions; occurrences list assembly instances",
        "counts": {
            "components": design.allComponents.count,
            "bodies": bodies,
            "mesh_bodies": meshes,
            "sketches": sketches,
            "fully_constrained_sketches": fully_constrained,
            "occurrences": occurrences.count,
            "joints": joints,
            "as_built_joints": as_built_joints,
            "user_parameters": design.userParameters.count,
            "all_parameters": parameters.count,
        },
        "components": page(
            component_rows, design.allComponents.count, COMPONENT_OFFSET
        ),
        "bodies": page(body_rows, bodies, BODY_OFFSET),
        "sketches": page(sketch_rows, sketches, SKETCH_OFFSET),
        "sketch_health_counts": dict(sketch_health),
        "occurrences": page(occurrence_rows, occurrences.count, OCCURRENCE_OFFSET),
        "parameters": page(parameter_rows, parameters.count, PARAMETER_OFFSET),
        "timeline": timeline_summary,
    }
    result["status"] = "ok"
    result["document"]["is_modified_after_inspection"] = doc.isModified
    return result


def run(_context: str):
    print(json.dumps(inspect_design(), ensure_ascii=False))
