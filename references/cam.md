# CAM and manufacturing

Use this reference for Manufacture workspace tasks. CAD geometry, a configured machining operation, a generated toolpath, an NC file, and proven machine execution are different deliverables. Establish which the user requested.

## Context and capability

Retrieve the document's `CAMProductType` product and cast it with the current `adsk.cam.CAM` API. Do not assume `activeProduct` is CAM or that a CAM product already exists. Discover how the installed environment initializes the manufacturing context when creation is needed; opening/activating it changes application state and belongs to the authorized manufacturing task.

Read existing setups, selected models, stock, fixtures, tools, operations, machines, and NC programs before adding or changing them. In an inspection-only task do not generate toolpaths, invalidate operations, create setups, or run `CAM.checkValidity` without checking its effects: its documentation says it can invalidate affected operations.

Check licensing when the requested strategy or operation depends on an extension. Do not assume installed API classes prove entitlement. See the output reference for licensing behavior.

## Manufacturing inputs

Use the model and existing setup to infer context where supported. Resolve missing essentials that affect the result: process type, machine/controller, work coordinate system, stock, workholding/fixtures, material, tools, required finish/tolerance, and intended output location/post. Do not invent these as production-ready values.

For a concept or demonstration setup, clearly identify assumed inputs and keep the output labeled accordingly. Do not apply generic feeds and speeds to a real machine without tool/material/process context. Reuse the user's established choices when present; do not ask for information already in the setup.

## Setup workflow

1. Read `Setups` creation and `SetupInput` members for the process type.
2. Resolve model bodies/occurrences in manufacturing context. Inspect `CAM.designRootOccurrence` where relevant; CAM's root is distinct from the CAD root.
3. Set models, stock mode/solids, fixtures, machine, and setup parameters using the current types.
4. Define work origin, axes, and stock dimensions/offsets explicitly. A visually plausible placement is not sufficient evidence of WCS correctness.
5. Add the setup and read it back. Check actual model selection, stock, WCS matrix, units, and operation type.

The audited `SetupInput` exposes `models`, `stockMode`, `stockSolids`, `fixtureEnabled`, `fixtures`, `machine`, `printSetting`, `parameters`, and previous-setup-data behavior. Their semantics and accepted types must be read before use. Do not inherit previous setup values unintentionally.

## Tools, strategies, and parameters

Discover tool libraries and available strategies through the current CAM API. Use exact identifiers from the environment. UI labels are not necessarily strategy IDs or parameter names.

Read the chosen strategy's `OperationInput` and parameter collection. Set documented expressions or typed values appropriate to each parameter. Geometry/selection parameters may require special selection objects; do not assign strings to them as if they were numeric fields.

The audited `OperationInput` contains `strategy`, `parameters`, `tool`, `toolPreset`, `displayName`, `generationMode`, and `referenceTool`. Its `generationMode` can trigger generation when an operation is added. Choose that behavior deliberately rather than assuming creation is always inert.

Use the actual tool geometry and preset: cutting diameter, flute length, overall length, holder, corner radius, and relevant process limitations. Validate heights, depths, stock to leave, stepdown/stepover, approach/retract, and boundaries. Update the intended operation rather than duplicating every operation when correcting one input.

## Toolpath generation and completion

Read the current `CAM.generateToolpath` or related method. Generation may return `GenerateToolpathFuture`. The audited future exposes operation counts, completion counts, task counts, and `isGenerationCompleted`.

Do not treat receipt of a future as a completed toolpath. Monitor through documented mechanisms without blocking Fusion's UI thread indefinitely. Do not assume a Python future reference survives separate MCP scripts; if it cannot be retained safely, read operation generation state through subsequent scripts or use a documented event-based approach.

Use short bounded checks and report meaningful progress. If generation fails, inspect operation messages and parameters before retrying. A model change can invalidate a previously generated toolpath.

After generation, inspect `isGenerating`, `hasToolpath`, `isToolpathValid`, and the operation state. Verify the intended setup/operation counts and selections. Simulation/collision verification is a separate workflow when required and supported; a valid generated path alone does not prove safe machine motion.

## NC output

Discover `NCPrograms`, `NCProgramInput`, `NCProgram`, post configurations, and current post-processing methods. Some older `CAM.postProcess` workflows are retired; prefer the supported route in the installed API.

Resolve the machine/controller, exact post, work offset, program identifiers, operations, units, and destination before generating machine-specific output. Do not choose a post solely because its name sounds similar to the machine. The audited `NCProgram` supports operation selection, `postConfiguration`, `machine`, post parameters, and `postProcess`.

Only generate/write NC output when it is part of the requested task. Do not upload it to a machine, send it elsewhere, or initiate execution as an implied extension of CAD/CAM creation. Verify that the expected file exists and inspect relevant output headers, units, and setup mapping. Do not report machine verification unless it actually occurred.

## Report the achieved state

State whether the result is a setup, configured operations, generated/valid toolpaths, simulated paths, or an exported NC program. Include unresolved material assumptions and the specific verification performed. Avoid a blanket claim that a job is ready to run if the task only produced geometry or operation definitions.

This reference is based on API discovery. CAM execution was not part of the initial live CAD audit; perform task-specific validation on the actual manufacturing document.
