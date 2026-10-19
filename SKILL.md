---
name: fusion
description: "Create, inspect, edit, troubleshoot, and export Autodesk Fusion designs through the connected Fusion MCP and Fusion Python API. Use for Fusion CAD modeling, parametric parts, sketches, assemblies, sheet metal, mesh and surface workflows, CAM, and electronics inspection. Includes live API discovery, geometry selection, verification, and recovery. Does not apply to Blackmagic Fusion or unrelated products named Fusion."
---

# Autodesk Fusion

Turn the user's design intent into editable Fusion geometry and verifiable results. Use the connected MCP and the installed Fusion API. Support unfamiliar features through current API discovery instead of limiting work to the examples in this skill.

The MCP is a small gateway to a large application: most CAD creation, measurement, and modification happen through Python scripts. Availability depends on the installed API, active product, document, and entitlements. Do not promise that every Fusion UI command has an exposed API.

## Start here

1. Read the current Fusion tool definitions. Discover deferred tools if necessary; their names currently start with `mcp__fusion__fusion_mcp_`.
2. Read [MCP operation and scripting](references/mcp-and-scripting.md) for discovery, responses, document identity, execution, and observed integration quirks.
3. Read open documents and the active command. Inspect the relevant model structure. The bundled [inspection script](scripts/inspect_design.py) runs inside Fusion with `readOnly: true`.
4. Select the reference below. Load only relevant references and exact live API members.
5. Choose a feature sequence, implement the authorized work, verify it, and deliver the result. When the user requested a Fusion model, do not stop at a proposed script.

| Task | Reference |
|---|---|
| Parts, sketches, parameters, solid features, patterns, holes, threads | [Parametric modeling](references/modeling.md) |
| Feature edits, measurement, face/edge selection, assemblies, joints | [Geometry and assemblies](references/geometry-and-assemblies.md) |
| Purchased components, stock framing, supplier CAD, and McMaster parts lists | [Catalog parts and assemblies](references/catalog-parts.md) |
| Surfaces, meshes, sheet metal, freeform, configurations, unfamiliar capabilities | [Advanced modeling](references/advanced-modeling.md) |
| Manufacture workspace, setups, tools, toolpaths, NC output | [CAM](references/cam.md) |
| Schematics, PCB, libraries, connectivity, variants, ERC/DRC inspection | [Electronics](references/electronics.md) |
| Save, CAD export, drawings, renderings, media, presentations | [Files and outputs](references/outputs.md) |
| Failed scripts, unhealthy features, partial changes, undo | [Verification and recovery](references/verification-and-recovery.md) |

## Preserve intent and scope

Distinguish a new design, an addition to the current design, an edit to existing features, inspection, and export. A new-object request does not imply erasing the current model. A dimension edit usually calls for changing its controlling parameter or feature instead of replacing the body.

Extract units, dimensions, orientation, part count, interfaces, fit requirements, manufacturing intent, and deliverables from the request and model. Resolve routine implementation choices autonomously. Ask only for missing information that materially changes geometry, function, or destination; inspect first when the model can answer it. State reasonable assumptions for a concept model. Do not invent a critical mating dimension, thread standard, or tolerance.

Use existing authorization. Do not introduce an approval gate for every sketch, feature, or script. Follow actual tool requirements for saving, closing unsaved documents, purchases, and other consequential actions. For a request explicitly limited to inspection/no edits, use read-only scripts and preserve model, timeline, selection, workspace, and command state. Creating an explicitly requested report is a separate authorized file operation.

## Core workflow

### Establish context

- Identify the intended document from live results. Names can repeat; saved data-file IDs and document context help disambiguate. Never invent IDs.
- Read `activeCommand`. `SelectCommand` with `isDefaultCommand: true` is idle selection, not a blocking dialog.
- Obtain Design through `activeDocument.products.itemByProductType("DesignProductType")`. The active product may instead be CAM or another product.
- Inspect units, design type, active component, occurrence context, timeline position, and existing feature health. Check external references and repeated instances before editing a shared component definition.
- For a new design, choose the document and component structure appropriate to the request. Do not silently change an existing design's history mode or design intent to make a script work.

### Choose a feature sequence

Express the shape as editable stages: reference geometry, constrained sketches, primary solids, additive/subtractive features, patterns, and finishing details. Use user parameters for dimensions intended to change. Use components for distinct manufactured parts or moving members.

A hole feature, modeled thread, patterned component, and mesh body carry different intent. Do not substitute a visual approximation for a required mechanical feature without stating the limitation.

### Discover and implement

- Read exact classes and members before generating the script. Class summaries may omit inherited properties. Broad searches were observed to return only five results without a truncation flag; use precise symbols.
- Define `run(_context: str)` and let exceptions reach the MCP. Print compact structured results.
- Keep scripts to coherent modeling stages when partial failure would be hard to locate. Reuse returned objects and resolve tokens with ownership and geometric checks.
- Guard document and target before mutation. Validate dimensions and selection cardinalities before adding geometry. Inspect partial state before retrying a failed stage.
- Run dependent operations sequentially. Do not execute simultaneous mutation scripts against the shared Fusion session.

### Verify and deliver

Check requested dimensions and topology, feature health, parameter relationships, and a relevant view. A screenshot, nonempty body collection, or script success message alone does not establish correctness. Use checks proportionate to the change.

Report what changed, supporting measurements or checks, material limitations, and save/export status. If a requested capability is unavailable, complete supported work and identify the precise remaining step.

## Non-obvious invariants

- CAD internal length is centimeters and angles are radians. Millimeter display units do not change this. Prefer unit-bearing expressions and explicit conversion. Electronics has a separate grid-unit convention.
- Component definitions, occurrence instances, native objects, and assembly proxies have different contexts. Repeated occurrences share a definition.
- Collection order is not design intent. Select profiles, faces, and edges by geometry and ownership; assert the expected number of candidates.
- Token strings can change, and an old face token can resolve to multiple faces after a split. Temporary topology IDs expire when their body changes.
- Switching parametric to direct design can remove history. Some feature edits require rolling the timeline immediately before the feature and restoring the intended position afterward.
- Unhealthy, underconstrained, suppressed, and rolled-back are different conditions.
- Set `readOnly: true` explicitly for inspection. Do not use `Application.executeTextCommand` in a read-only script. Exports, recomputation, saving, and UI changes are not inspection.
- Discover current capabilities rather than hardcoding this audit's version, account, or model state.

## Bundled inspector

Read `scripts/inspect_design.py` and send its source as `object.script` to `fusion_mcp_execute` with `featureType: "script"` and `readOnly: true`. It is not a local Python CLI; `adsk` belongs to Fusion's embedded Python.

Adjust its constants in the submitted source for document guards, pagination, and geometry detail. It reports identity, product types, units, counts, parameters, occurrence transforms, and health. It never saves, recomputes, changes the camera, or moves the timeline. Detail pages report their total and whether more rows exist. Body counts cover native definitions, not assembly quantities.

For a misplaced assembly member, compare its occurrence transform with its actual geometry. The inspector includes pin state; enable `INCLUDE_PART_NUMBERS` for catalog identifiers and `INCLUDE_OCCURRENCE_BOUNDS` for bounds in occurrence assembly context. Leave these optional reads off when a structural read is sufficient; part-number getters can be much slower than names.

Use targeted reads for large assemblies or small edits; running a full inspector is not mandatory every time.

## Validation scope

The initial audit on 2026-10-13 used Fusion reporting version `2705.1.30`. Read-only CAD inspection, documentation queries, document discovery, screenshots, parameters, health, thread inspection, and token resolution were exercised. All 50 electronics schemas were read, but actual electronics rows were unavailable.

Work on 2026-10-19 also exercised supplier STEP assemblies, body-move repair, component pinning, native/STEP/DXF/STL exports, and mesh scale/closedness checks. These observations support the specific guidance in the references; CAM, other advanced operations, engineering performance, and media handoffs still require their own verification.

Never carry model names, file IDs, license state, or selections from another chat into a new task. Begin with live context.
