# Advanced modeling and capability discovery

## An unfamiliar request is a discovery task

Identify the desired representation and find its owning product, collection, input type, creation method, and verification properties. A class being documented does not establish that it supports creation. Inspect whether the collection actually has `createInput`/`add` or another supported constructor. Do not infer writes from read access.

For each unfamiliar capability:

1. Read the active document's product types and the relevant API namespace.
2. Query one likely class and the exact needed members. Follow base classes and returned types.
3. Classify the available operation as inspection, creation, edit, export, preview, or unsupported.
4. Resolve required geometry, inputs, entitlement, and operating context.
5. Implement a small meaningful stage and validate the result before scaling it.

An empty broad documentation query is insufficient evidence of absence because of filtering, inheritance, and the five-result limit. Conversely, the installed UI exposing a feature is insufficient evidence of API access. Read exact contracts or authoritative Autodesk documentation.

### Installed support versus online releases

Online [API release notes](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/WhatsNew.htm) can describe newer or preview interfaces that the running installation does not expose. Record `Application.version`, check the exact owning class/member locally, then distinguish presence from an exercised workflow. For example, the October 2026 documentation describes preview drawing and configuration-rule APIs; this does not establish their availability in every installed build. Keep preview-dependent automation version-specific and recheck its contracts after upgrades.

## Surface modeling

Use surface construction when the design calls for open surfaces, controlled continuity, a complex outer skin, or geometry that will later be thickened/stitched. Discover the applicable extrusion, revolve, sweep, loft, patch, stitch, trim, extend, replace-face, and thicken collections; do not assume every one exists in the current release.

For a surface extrusion, the audited `ExtrudeFeatures.createInput` documentation describes open profiles through `Component.createOpenProfile` or `createBRepEdgeProfile`, together with the input's `isSolid = False`. Verify the specific profile and input properties before running.

Track open boundaries and intended face orientation. Stitching close surfaces does not establish a valid closed solid until the resulting body says so. Check gaps, continuity requirements, shell/body count, normals, and thickness direction. If a thicken/shell operation fails, inspect local radius, self-intersection, and tiny faces; do not repeatedly reduce tolerances without relating the change to the design.

Preserve surface inputs or construction geometry when they are needed to keep the design editable. Removing them merely to clean the browser can break dependencies.

## Meshes and imported scans

Distinguish a `MeshBody` from a `BRepBody` before selecting features. Inspect source units, scale, orientation, closedness, face/triangle count, and intended fidelity. A mesh is not automatically a solid CAD model even if it looks closed on screen.

The audited API exposes mesh inspection and some mesh-operation classes marked preview. `MeshConvertFeatures` and `MeshReduceFeatures` explicitly said they were preview features and should not be used in distributed programs. Do not package these as a guaranteed stable workflow. If a task needs a preview call in the local installation, verify its exact contract, disclose the material limitation, and keep the procedure version-specific.

Choose representation according to the task:

- Retain a mesh for visualization or mesh-native output when that satisfies the request.
- Repair or reduce only when needed, preserving a source or an authorized recoverable state and checking deviation.
- Convert to B-Rep only when suitable for the geometry and current API. A dense faceted conversion can create huge topology and still lack editable design intent.
- Reconstruct analytic features when accurate planes, cylinders, interfaces, and parameters matter more than reproducing every scan triangle.

Do not treat a unitless mesh file's numeric coordinates as known millimeters. Establish the intended scale using metadata or a known dimension. Export verification should include scale, closedness, and tessellation accuracy relevant to the deliverable.

## Sheet metal

Sheet metal requires a rule and folded/flat semantics, not merely a thin extruded solid. Inspect thickness, inside bend radius, K factor, relief, gaps, seams, and manufacturing intent. Use installed rules or user-provided values; do not invent bend allowances for production.

Discover `SheetMetalRule`, the design/library rule collections, supported component creation methods, folded-body status, and flat-pattern APIs. The initial audit's `FlangeFeatures` collection exposed inspection (`item`, `itemByName`, `count`) but no creation methods. That is a concrete reason to verify flange creation separately rather than assume `add` exists.

`Component.createFlatPattern` and `FlatPattern` are discovery targets for existing valid folded parts. Read creation preconditions, stationary-face selection, and the export route. A flat pattern restricts some regular component operations; the audited class explicitly disallows creating occurrences/components and sheet-metal features within it.

If true sheet-metal feature creation is unavailable, separate any supported geometric concept work from the remaining folded/flat workflow. Do not label a thin solid or manually drawn flattened outline as a valid manufacturing flat pattern. Continue through a supported UI workflow only when that capability is actually available and within scope.

## Freeform and organic shapes

Identify whether the goal is an editable freeform control cage, a smooth surface/solid, or an approximate mesh. Query the installed Form/T-spline-related APIs before proposing automation. Existence of a form/base feature container does not imply that all interactive sculpting operations are scriptable.

Where supported, use lofts, sweeps, patches, and section curves for controlled analytic reconstruction. A mesh approximation is an alternative only if it meets the user's intent; it is not equivalent to an editable T-spline cage. Preserve symmetry, section correspondence, seams, curvature expectations, and physical wall thickness as relevant.

## Configurations and variants

Read whether the design is configured or a configuration, the relevant configuration table/row, and whether occurrences reference configurations. Discover current configuration APIs and entitlements. Do not change the active row globally just to edit one intended variant without checking scope.

Determine whether a dimension change belongs in a shared definition, one configuration row, or a copied variant. Verify the intended row and resulting geometry after editing. Configuration switching can change available geometry and invalidate stored topology references.

## Materials and appearances

Material controls physical properties; appearance controls visual finish. Read the actual libraries available through the API, search narrowly, and select exact entries. Do not present a metallic-looking appearance as proof of steel mass or strength.

An image edit changes pixels and does not assign Fusion materials. Use actual design/body/component material APIs when the requested result is a model property. Report which representation was changed.

## Drawings, simulation, and other workspaces

The application may advertise product types for drawings, simulation, animation, or manufacturing. Their presence is not proof that every workflow is available through the MCP script interface. Discover the owning product and exact API operations, and read relevant entitlements only when needed.

For drawings, confirm standards, units, scale, views, dimensions, and output requirements. For simulation, loads, fixtures, contacts, material properties, mesh, solver, and result interpretation form a separate engineering task. Do not infer design adequacy from geometric health or a rendered picture. If the requested analysis is unsupported, state the precise missing operation and preserve the completed geometry.
