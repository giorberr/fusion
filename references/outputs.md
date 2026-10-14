# Files and presentation outputs

## Deliver the requested artifact

Clarify through context whether the requested result is an editable Fusion design, a neutral solid, a mesh for printing, a 2D manufacturing outline, a drawing, a rendering, or machine output. These formats preserve different information. Do not imply a STEP file retains Fusion's full feature history or a rendered image contains editable CAD.

Keep the editable source when it is part of the request. Distinguish model creation from saving and exporting; report the actual completed state.

## Save and close

The audited `execute` document-save instructions require an express user request to save. A previous request to save in this task remains authorization; do not ask repeatedly. Creating geometry alone does not authorize an automatic save/version checkpoint under that tool contract.

Read current document identity and modified/saved state before save/close. For first-save workflows requiring a cloud project/folder, discover actual destinations and use the user's intended location. Do not invent folder IDs. Document names are not file IDs.

For close with unsaved changes, use the user's explicit choice to save or discard and populate the appropriate current-tool flag. Do not mark a confirmation boolean true merely to bypass the dialog. Do not close a user's model as incidental cleanup of a failed script.

Read back saved state and relevant identity/version. Some cloud processing is asynchronous; distinguish saving being initiated from completed cloud availability when the API exposes that difference.

## CAD and mesh exports

Discover `Design.exportManager`, the exact format-specific option constructor, options, and `execute` member. Use supported current routes. Exports write files and are not read-only inspection.

| Output | Important decisions and checks |
|---|---|
| Native Fusion archive | Intended document/component scope; history and references supported by the chosen format |
| STEP or other neutral B-Rep | Component/body scope, assembly structure, units, solids versus surfaces |
| STL/3MF or another mesh | Geometry scope, coordinate scale/units, binary/text choice, tessellation tolerance, closedness |
| DXF | Correct sketch/flat pattern, projection plane, intended profiles, units, supported export route |
| Drawing/PDF | Sheet/view scale, standards, units, dimensions, drawing-generation capability |
| NC code | CAM reference: exact machine/post, operations, WCS, units, output path |

Check whether exporting a body, component, entire design, or assembly is supported by the option type. Visibility alone does not necessarily constrain export scope. Linked designs can have format-specific limitations.

An export path is on the host where Fusion runs. Do not assume it is the agent's local filesystem if Fusion is remote. Use a destination actually accessible to that host, and a documented retrieval mechanism if needed. Do not invent download URLs.

Verify export success and file existence/size when accessible. For scale-critical or manufacturing output, inspect units and relevant geometry through a format reader or isolated reopen when available and authorized. A successful `execute` return only proves the export operation reported success.

The audited `Sketch.saveAsDXF` member was marked retired. Discover the supported export-manager or current sketch route instead of copying it into new automation. A manually projected outline is not a true sheet-metal flat pattern.

## Screenshots and camera

```json
{"queryType":"screenshot","direction":"current","width":1200,"height":900,"transparentBackground":false}
```

`current` preserves the viewing direction. Other directions instruct the tool to change the camera before capture. Use them during authorized visual review when appropriate; use `current` for an inspection that must preserve UI state. Do not state the camera was preserved if a standard view was requested.

Screenshots show the graphics viewport, not necessarily the whole Fusion UI or feature tree. Use active-command reads for dialog state and API reads for model structure. Image blocks can be displayed directly; do not expose base64 strings.

Use views that make the requested result reviewable: silhouette, relevant interfaces, hole placement, or assembly arrangement. A view is supporting evidence, not a dimensional inspection.

## Renderings and image editing

Determine whether the user wants actual Fusion material/appearance assignments, a physically rendered model view, or a generated contextual image. These are different workflows. Use the current environment's applicable rendering or image tool instructions.

For an applicable Fusion `editImage` workflow, the audited tool requires the source `image_url`, permanent `s3_url`, and the user's prompt verbatim. It consumes an AI media generation use and may return an allocation error. Follow current tool instructions about response handling and explicit retry requests.

The tested screenshot returned an image block without signed/S3 URLs. This did not establish the required handoff to `editImage`. Recheck actual screenshot/attachment metadata when the workflow is requested. Never fabricate a URL, infer an S3 path, or treat base64 as a valid permanent identifier. Use another supported image workflow when appropriate if this integration still lacks the handoff.

Generated visuals do not prove model geometry, materials, manufacturability, or engineering adequacy. Clearly distinguish the image deliverable from changes to the Fusion model.

## Media previews and presentations

Fusion's `previewImage` feature handles already generated files. Use genuine returned attachment identifiers and URLs. Follow the current action contract for preview, external opening, or download. Multi-file arrays require matching pairs and the supported download action. Do not fabricate output files or claim a download completed just because a save dialog opened.

The `generatePowerpoint` instructions require reading `resource://mcp.generate_powerpoint_schema` before outlining, approved full slide content, and explicit outline confirmation before generation. The initial resource catalog did not advertise that schema. Recheck current discovery; if unavailable, use an available presentation workflow and its applicable instructions rather than inventing layout IDs or placeholders.

Respect any actual confirmation required by that tool and explain its source if it blocks completion. Reuse information and approval already supplied; do not ask again for known audience/content or a previously approved outline.

## Licensing and extensions

Read licensing when the user asks about licensing/purchase or when a requested capability is plausibly entitlement-gated. Avoid fetching account entitlements for ordinary geometry operations that do not need them.

The response can include initializing/checking state; null values do not mean zero entitlement. Use the current response and exact extension names. Do not suggest obtaining an extension already active.

The audited purchase workflow requires explicit consent to open Purchase Manager. For Education, its instructions route extensions through free access and reject paid subscription/Flex tabs. Follow current license-specific instructions; do not turn a modeling request into an unsolicited purchase flow. A skill cannot grant entitlements or enable a missing extension by instruction alone.

## Handoff

Deliver the actual file or link through the current client's supported artifact mechanism. Use real accessible paths/URLs and preserve naming and destination preferences. Include a brief statement of source/editability, verified dimensions or checks, and any unsupported final step. Never claim the design was saved, exported, simulated, or rendered unless that operation actually completed.
