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

### Mesh and manufacturing unit checks

For the tested Fusion STL exporter, `STLExportOptions.unitType` uses `adsk.fusion.DistanceUnits`, for example:

```python
options = design.exportManager.createSTLExportOptions(component, output_path)
options.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
```

Do not substitute `MeshUnits.MillimeterMeshUnit` or a raw integer because its name/value looks similar. That substitution produced an STL ten times the intended size even though export succeeded. Recheck the current option type when using another mesh API.

STL does not encode a unit declaration. Parse the exported vertices or reopen the mesh with an explicit unit choice and compare its numeric extents to known CAD dimensions. For printable solids, also check closedness/non-manifold edges; neither scale nor manifoldness alone proves printability. Check STEP unit declarations and DXF `$INSUNITS` when manufacturing dimensions depend on them.

An outline-and-drill DXF does not communicate all of a plate's machining requirements. Supply tapping, countersink/counterbore side and dimensions, stock thickness, and other necessary operations in a drawing or companion manufacturing notes. Distinguish tap-drill geometry from finished threads and a nominal countersink from a modeled finished feature.

The audited `Sketch.saveAsDXF` member was marked retired. Discover the supported export-manager or current sketch route instead of copying it into new automation. A manually projected outline is not a true sheet-metal flat pattern.

## Model appearances

For an actual model finish, read the available `Application.materialLibraries` and the chosen library's `appearances`, then use exact discovered names. Names are localized, and appearance names need not be unique; resolve ambiguity to a verified entry rather than assuming a name identifies one. Names such as `Fusion Appearance Library` and `Oak - Semigloss` were found in one session, not guaranteed for every installation.

This helper takes a previously validated native body and unambiguous discovered names. Both lookups must succeed before assignment: accidentally assigning a missing appearance (`None`) would clear an existing body override.

```python
def apply_body_appearance(app, body, library_name, appearance_name):
    library = app.materialLibraries.itemByName(library_name)
    if library is None:
        raise ValueError(f"Appearance library not found: {library_name}")
    appearance = library.appearances.itemByName(appearance_name)
    if appearance is None:
        raise ValueError(f"Appearance not found in {library_name}: {appearance_name}")
    body.appearance = appearance
```

The documented `BRepBody.appearance` setter does not require an explicit copy into the design first; direct library assignment is consistent with that contract but was not mutation-tested in this audit. For a deliberately named/design-owned copy, optionally use `design.appearances.addByCopy(appearance, copy_name)`, check its result for `None`, then assign the copy. Autodesk's [Material API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/MaterialSample_Sample.htm) demonstrates copy-first, not a mandatory-copy rule. Do not promise undocumented automatic-copy behavior.

Setting `body.appearance = None` intentionally removes only that body's override. A native body belongs to a shared component definition, so its appearance affects that definition across occurrences; face or occurrence overrides may affect the visible result. Do not silently clear those other overrides. An appearance assignment changes visual finish, not `body.material` or density; see [Materials and appearances](advanced-modeling.md#materials-and-appearances). Verify the assigned appearance/source and relevant instance/face display, not just script success. Assignment and `addByCopy` are model mutations, never `readOnly: true` inspection.

## Screenshots and camera

```json
{"queryType":"screenshot","direction":"current","width":1200,"height":900,"transparentBackground":false}
```

`current` preserves the viewing direction. Other directions instruct the tool to change the camera before capture. Use them during authorized visual review when appropriate; use `current` for an inspection that must preserve UI state. Do not state the camera was preserved if a standard view was requested.

A direction such as `iso-top-right` specifies orientation, not a documented fit guarantee. Set up a fitted camera explicitly when framing matters, then capture with `direction: "current"` so the screenshot request does not replace that orientation.

Screenshots show the graphics viewport, not necessarily the whole Fusion UI or feature tree. Use active-command reads for dialog state and API reads for model structure. Image blocks can be displayed directly; do not expose base64 strings.

When saving a viewport immediately after a camera change, a smooth transition can capture an intermediate view. For a deterministic scripted capture, set `camera.isSmoothTransition = False`, assign the intended camera/fit, refresh the viewport, and inspect the resulting image.

`viewport.camera` returns a copy; changing it has no viewport effect until assigned back. `camera.isFitView = True` requests fitting the entire model when that assignment happens, not a crop to selected bodies. For this helper, obtain bounds in root/world coordinates (for example, the current `design.rootComponent.boundingBox`), and choose target-to-eye and up directions from the intended model orientation. Do not pass a nested component's local bounds as world bounds or reuse eye/target coordinates from another model.

```python
import adsk.core


def fit_orthographic(viewport, world_bounds, eye_direction, up_direction):
    low, high = world_bounds.minPoint, world_bounds.maxPoint
    distance = low.distanceTo(high)
    direction, up = eye_direction.copy(), up_direction.copy()
    if distance <= 0 or not direction.normalize() or not up.normalize():
        raise ValueError("Nonzero model bounds and camera directions are required.")
    if direction.crossProduct(up).length < 1e-9:
        raise ValueError("Camera eye and up directions must not be parallel.")
    target = adsk.core.Point3D.create(
        (low.x + high.x) / 2, (low.y + high.y) / 2, (low.z + high.z) / 2
    )
    camera = viewport.camera
    camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    camera.target = target
    camera.eye = adsk.core.Point3D.create(
        target.x + distance * direction.x,
        target.y + distance * direction.y,
        target.z + distance * direction.z,
    )
    camera.upVector = up
    camera.isSmoothTransition = False
    camera.isFitView = True
    viewport.camera = camera
    if not viewport.refresh():
        raise RuntimeError("Camera was assigned, but viewport refresh failed.")
```

Call helpers from `run(_context: str)` only after document/target validation and authorization for the changes. Camera application, viewport refresh, and non-current screenshot directions change UI state: do not perform them in a `readOnly: true` script or a preserve-UI inspection. The camera helper is documentation-based, not live mutation-tested here.

The installed `Camera.viewExtents` documentation explicitly marks it retired, replaced by `getExtents()` and `setExtents(width, height)`. Those methods apply only to orthographic cameras and use width/height in centimeters; use `isFitView` for automatic fitting rather than copying old `viewExtents` examples. Recheck exact current contracts when implementing manual framing.

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
