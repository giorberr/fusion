# Autodesk Fusion Agent Skill

An agent skill for creating, inspecting, editing, troubleshooting, and exporting **Autodesk Fusion** designs through a connected Fusion MCP server and Fusion's Python API.

The skill turns design requests into editable geometry, discovers the installed API before using it, and verifies results with measurements and feature health rather than relying on screenshots alone. It applies to Autodesk Fusion, not Blackmagic Fusion or other products with the same name.

This repository contains agent instructions, reference guides, and an inspection script. It does **not** include Autodesk Fusion, an MCP server, or a standalone Python application.

## Requirements

- Autodesk Fusion installed and running, with access to the products and entitlements required for the task.
- A connected Fusion MCP server exposing document discovery, API documentation, and Python script execution. Additional workflows depend on the tools available in that server.
- An agent client that can load `SKILL.md` skills and use the connected MCP tools.

The bundled Python script requires Fusion's embedded Python environment and its `adsk` modules. It cannot be run as a normal local Python CLI.

## Installation

For Zed, clone the repository into the global skills directory:

```sh
git clone https://github.com/giorberr/fusion.git ~/.agents/skills/fusion
```

For another skill-compatible client, use its configured skills directory instead. Keep `SKILL.md`, `references/`, `scripts/`, and `agents/` together so relative paths continue to resolve.

Configure and connect your Fusion MCP server separately. The agent metadata in [`agents/openai.yaml`](agents/openai.yaml) declares an MCP dependency named `fusion`; it does not install or launch that server.

## Getting started

1. Start Fusion and open the intended document, or request a new design explicitly.
2. Ensure your agent client has loaded the skill and can access the Fusion MCP tools.
3. Describe the task, including relevant units, dimensions, fit requirements, and deliverables. Specify whether the agent should inspect, create, edit, save, or export.

Example requests:

> Inspect the active Fusion design without changing the model or UI state. Report its units, components, bodies, parameters, and feature warnings.

> Create a new parametric mounting plate, 60 x 40 x 4 mm, with four 5 mm through-holes, each centered 8 mm from its two adjacent edges. Use editable parameters and verify the dimensions and hole count.

> Inspect the current assembly's components, occurrence transforms, and joint definitions. Report external references and any feature errors without changing the design.

The agent starts from live document and command state, reads the relevant guide, discovers exact API members, executes authorized work in coherent stages, and checks the result. Saving and exporting are separate actions and should be requested explicitly.

## Reference guides

These guides describe workflows and capability discovery, not a guarantee that every Fusion UI command is available through the API.

| Area | Guide |
|---|---|
| MCP tools, API discovery, document identity, and script execution | [MCP operation and scripting](references/mcp-and-scripting.md) |
| Sketches, parameters, solid features, holes, threads, and patterns | [Parametric modeling](references/modeling.md) |
| Geometry selection, measurements, assemblies, joints, and existing edits | [Geometry and assemblies](references/geometry-and-assemblies.md) |
| Purchased components, stock framing, supplier CAD, and McMaster parts lists | [Catalog parts and assemblies](references/catalog-parts.md) |
| Surfaces, meshes, sheet metal, freeform, configurations, and capability discovery | [Advanced modeling](references/advanced-modeling.md) |
| Manufacturing setups, operations, toolpaths, and NC output | [CAM](references/cam.md) |
| Schematics, boards, libraries, connectivity, and stored ERC/DRC information | [Electronics inspection](references/electronics.md) |
| Saving, CAD exports, screenshots, renderings, and presentation outputs | [Files and outputs](references/outputs.md) |
| Verification, partial failures, targeted recovery, and undo boundaries | [Verification and recovery](references/verification-and-recovery.md) |

## Bundled design inspector

[`scripts/inspect_design.py`](scripts/inspect_design.py) produces a structured JSON report of the active Fusion design, including:

- Document identity, saved/modified state, workspace, product types, and Fusion version.
- Design type, display units, component and body counts, and assembly occurrences.
- Body bounds and volume, sketch constraint status, parameters, and timeline health.
- Paginated detail rows with totals and a `has_more` indicator.

To use it, read the source and submit the **complete source text** as `object.script` to `fusion_mcp_execute`, with `featureType: "script"` and `object.readOnly: true`. A filesystem path is not a substitute for the script source. See the [script contract](references/mcp-and-scripting.md#script-contract) for the execution format.

Adjust the constants in the submitted source to set document guards, page offsets, `DETAIL_LIMIT`, geometry detail, or entity-token output. The inspector does not save, recompute, change the camera, or move the timeline. Its body counts describe native component definitions, not assembly quantities.

Occurrence rows include pin state. Enable `INCLUDE_PART_NUMBERS` for catalog identifiers; those getters can be much slower than names. Enable `INCLUDE_OCCURRENCE_BOUNDS` when diagnosing a misplaced member; this reports actual geometry bounds in occurrence assembly context, which can change even when its occurrence transform has not.

## Safety and scope

- Preserve existing documents, design intent, history, and unrelated user work.
- Use explicit read-only execution for inspection; model edits, exports, saves, and UI changes are not inspection.
- Guard the target document and select geometry by ownership and geometric properties rather than collection order alone.
- Handle units explicitly: CAD internal lengths are centimeters and angles are radians; electronics uses its own grid-unit conventions.
- Inspect partial state before retrying a failed script. Do not assume a script is one undo transaction.
- Treat generated toolpaths and NC output as distinct from simulated or proven machine execution.

## Validation and limitations

The initial audit on **2026-10-13** used Fusion reporting version **2705.1.30**. It exercised read-only CAD inspection, API documentation queries, document discovery, screenshots, parameters, feature health, thread inspection, and token resolution.

All 50 advertised electronics schemas were read, but populated electronics data was unavailable. Work on **2026-10-19** additionally exercised supplier STEP assemblies, body-move repair, pinning, native/STEP/DXF/STL exports, and mesh scale/closedness checks. CAM execution, other advanced operations, engineering performance, and media workflows still require task-specific runtime verification.

Capabilities depend on the installed Fusion API, active document and product, connected MCP tools, and entitlements. The skill instructs the agent to discover current support and report precise limitations rather than inventing unavailable operations. See [`SKILL.md`](SKILL.md) for the full workflow and validation scope.
