# Geometry, assemblies, and existing edits

## Resolve the intended object

Start with component ownership and occurrence path, then geometry. Name matching alone is insufficient: bodies and components can share names. A face/edge index is not a stable semantic identity.

A useful selection chain is document -> component definition or occurrence path -> body -> geometric predicate -> expected candidate count. Stop and inspect if the count differs. Do not choose the first match when several are plausible.

For a few known members, reacquire the already observed name/path within its parent occurrence collection, for example with `Occurrences.itemByName`, then verify part number and ownership. Avoid enumerating the entire `root.allOccurrences` hierarchy just to recover a known target; reserve a full inventory for tasks that need it.

If the target is not yet known, a names/path inventory can be fast even when reading every `component.partNumber` is slow. Discover candidates with cheap identifiers, then read catalog metadata only for those candidates. See the timing guidance in [MCP operation and scripting](mcp-and-scripting.md#slow-reads-and-request-timeouts).

For a planar face, consider normal direction, plane location, centroid/point, area, loops, and adjacency. For a cylindrical face, consider axis, radius, axial extent, owner, and adjacency. For a circular edge, consider center, normal, radius, and adjacent faces. Query current surface/curve/evaluator APIs before coding a predicate.

Use tolerances in known units. Exact floating-point equality is unsuitable for geometry. Fusion's modeling tolerance can inform numerical comparisons, but it is not the user's manufacturing tolerance. A tolerance appropriate for finding a plane is different from a specified fit allowance.

## Tokens and topology

`entityToken` provides a handle that can be resolved with `Design.findEntityByToken`. It is not a persistent string identity to compare directly. The same entity can produce different token strings over time. Resolve tokens, then compare entities and verify context/geometry.

Resolution can return zero, one, or multiple entities. A face split by later modeling can make an old token resolve to several faces. Inspect all candidates; do not assume `[0]` is the only intended result. A missing entity may have been deleted or replaced. Re-identify it from design intent before further edits.

`tempId` only remains valid while the document stays open and the owning body remains unchanged. Collection indices and temp IDs cannot be carried across topology changes as a reliable plan. Reacquire references after cuts, splits, fillets, joins, and suppression changes.

Keep raw tokens out of ordinary user-facing reports. Store them in task data only when needed to continue the operation, together with context and intended geometric meaning.

## Coordinate frames

Distinguish:

- Native component coordinates, where a definition's geometry is authored.
- An occurrence's assembly context, where that definition is instantiated.
- Root assembly coordinates used for overall positioning/measurement.
- Sketch-local coordinates and its transform relative to model space.

Use `nativeObject`, `assemblyContext`, and `createForAssemblyContext` as documented to obtain the representation expected by an API. An occurrence's body proxy and the component's native body are not interchangeable for every selection.

Use `Occurrence.transform2`; the older `transform` property is retired in the audited API because it can give incorrect results. Understand the matrix's assembly context before composing nested transforms. A proxy may already embody part of the hierarchy; applying the same transform twice produces wrong coordinates. Check a known point in both frames when uncertain.

Use `Sketch.modelToSketchSpace` and `sketchToModelSpace` when positioning geometry from measured model points. Do not copy a root-space XYZ position directly into a rotated sketch.

An axis-aligned bounding box measures extents in its reported frame. It can overestimate a rotated part's physical width. Use an oriented box or direct geometric measurement when the requested dimension is along a part's own axis. Label the frame in numerical output.

### Diagnose a misplaced assembly member

Compare the occurrence's `transform2`, its native body geometry, and its body proxies or bounds in root assembly context. An unchanged occurrence transform does not prove the part stayed in place: a body move can change the geometry inside the component. Absence of a Move feature also does not establish unchanged geometry, especially with imported/base-feature bodies.

Restore an occurrence placement when the occurrence moved. Restore the affected body geometry or controlling feature when the bodies moved. Repeated instances share those body edits, so check every affected instance before changing a definition. Prefer a known baseline or supplier geometry to guessing a pose from a screenshot. Symmetric bounding boxes cannot uniquely establish orientation; use mounting points, faces, or axes as needed.

### Free-move feature frame conversion

Discover `MoveFeatures.createInput2`, `MoveFeatureInput.defineAsFreeMove`, and `MoveFeatureFreeMoveDefinition.transform`. A repair tested on 2026-10-19 with the root component active showed that native bodies and a component-owned feature collection did **not** make the supplied free-move matrix local to that component. A local correction applied as a root-space matrix restored orientation but left a large translation error. The resulting definition's transform getter also exposed a local representation, so matrix readback alone did not prove the correct assembled position.

Identify the input matrix's frame for the active context before mutation. Using column-vector notation, if `T` maps component coordinates to root and `M_local` is a local correction, the equivalent root correction is:

```text
M_root = T * M_local * inverse(T)
```

Apply the matrix once in the expected frame, then verify actual assembled geometry. A correct rotation with a large residual offset is a reason to audit frame conversion before attributing the result to cached bounds or rounding.

To edit an existing free-move definition, its documented setter requires `feature.timelineObject.rollTo(True)` before setting `feature.definition.transform`. Restore the intended timeline position afterward and recompute when required by that edit. Reacquire occurrences/bodies after recomputation. Prefer correcting the identified feature to stacking additional compensation moves.

## Measurements

Discover `MeasureManager` for distance, angle, and other relevant operations. Inspect `PhysicalProperties`, body volume/area, and appropriate bounding-box methods. Measurement choices should answer the actual question:

| Question | Suitable evidence |
|---|---|
| Overall extents | Bounding box in a stated frame |
| Hole diameter | Cylindrical geometry or controlling hole parameter |
| Hole-center spacing | Centers in a common frame |
| Clearance between parts | Minimum distance/interference in assembly context |
| Material mass | Physical properties with the actual material/density and accuracy |
| Wall thickness | Relevant opposing surfaces or documented thickness analysis |
| Thread identity | Thread metadata and modeled/cosmetic setting |

Do not infer a hole's diameter from a screenshot, mass from volume alone, or collision freedom from appearance. Hidden and suppressed geometry may affect the task differently; include or exclude it deliberately.

Interference and other analysis operations may construct transient inputs or trigger computation. Read their contract and respect the active task's read-only boundary; do not call a mutating analysis workflow under a read-only label.

### Test alternate poses with temporary geometry

For clearance checks that should preserve assembly placement, discover [TemporaryBRepManager](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_TemporaryBRepManager.htm): `copy`, `transform`, and `booleanOperation` operate on geometry outside the document. Copy the relevant bodies and express each candidate pose in one verified coordinate frame. Avoid applying an occurrence transform twice to geometry already in assembly context.

Use conservative bounding-box separation to discard distant pairs, then intersect candidate solids. A positive intersection volume establishes overlap; convert internal cubic centimeters explicitly when reporting cubic millimeters. Zero volume does not establish a specified clearance or rule out face contact. The [Boolean contract](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_TemporaryBRepManager_booleanOperation.htm) requires a temporary target body and modifies it on success; use a fresh copy for each test. A false return means failure, not clearance.

On 2026-10-19, a read-only script tested two temporary 20 mm cubes at seven offsets, with expected intersection volumes and unchanged modified state, timeline, and occurrence count. This verified transient geometry only. Real assembly frame handling, arbitrary topology, contact cases, and continuous travel still need their own checks; sampled poses alone do not prove an entire path is clear.

## Assembly structure and quantities

`allComponents` counts definitions. `allOccurrences` describes instances in the assembly. A component used eight times is one definition and eight occurrences. A native-body total is not a bill-of-materials quantity.

For repeated parts, reuse component definitions when changes should propagate. For a separately editable variant, discover the appropriate copy/new-component workflow. Do not duplicate bodies and call them independent assembled parts unless that is the intended representation.

For nested assemblies, use full occurrence paths. Inspect external-reference status before changing a definition. Editing a linked source, breaking a link, and making a local copy have different consequences. Preserve the requested link behavior and do not silently break references to bypass a restriction.

Ground or constrain the intended reference component. Use joints for intended relative motion; use as-built joints when the parts are already positioned and that is the desired relationship. Discover `JointGeometry`, `Joints`, `AsBuiltJoints`, motion definitions, and limits as needed. Constrain degrees of freedom deliberately; a transform alone is placement, not a persistent mechanical relationship.

Verify rigid/rotational/sliding behavior by inspecting the joint definition and limits. Motion simulation is a separate step if the user asks for it. A successfully created joint does not by itself prove the mechanism has no interference throughout travel.

`Occurrence.isGrounded` gets/sets whether an occurrence is pinned. Pin fixed members when that matches the assembly intent and verify the returned state. Pinning prevents ordinary occurrence dragging; it does not lock edits to bodies inside the component or replace joints between moving members.

### Verify assembly behavior, not only input values

In Fusion 2705.1.30, adding repeated occurrences after moving the first occurrence before recording its position produced unexpected transforms. After creating the instances, assign and read back every intended `transform2`; compare world-space body bounds with expected placements and capture pending position changes when appropriate.

For a nested moving member, reacquire the occurrence proxy through the intended root assembly instance. Changing the native child occurrence was observed not to update a position override in that instance, while setting the root-context child proxy did. Verify the member's assembled geometry after assignment. For repeated fixed members whose positions revert when snapshots are captured, test creating each occurrence with its intended initial matrix instead of initially creating every instance at identity.

Custom joint inputs using construction axes did not produce the intended rotation axes in one live assembly. Read `rotationAxisVector` and test a known angle against actual occurrence transforms. Standard joint directions worked in that case. Joint-motion setters may require timeline rollback even when their short member description omits it. Changing a joint axis also invalidated existing motion links; rebuild only the affected links after correcting the axes and verify the driven parts move correctly.

Ball-joint angle names are not proof of independent Cartesian X/Y/Z rotations. In the observed default configuration, pitch and roll both rotated about Z at zero yaw. Test the coordinate convention before locking an angle. If a mechanism requires two explicit orthogonal pivots, a clearly named, body-free reference component with two revolute joints can represent that motion without adding a manufactured part. Validate this representation against the real mechanism's geometry.

## Edit existing designs with minimal disruption

1. Identify the controlling feature or parameter and dependent geometry.
2. Record the current expression/value, feature health, document identity, and timeline marker.
3. Prefer editing the intended parameter/feature. Inspect dependency parameters before changing shared dimensions.
4. Read the exact member's timeline requirements. For example, `ExtrudeFeature.setOneSideExtent` requires the marker immediately before that feature; the similarly named input method for a new feature has a different context.
5. During an authorized edit, position the timeline as required, perform the edit, and restore the appropriate position. For an existing edit with no timeline-length change, preserving the prior marker is usually appropriate. For new appended features, restoring an old integer can accidentally roll back the new work; restore according to intended history position instead.
6. Recompute only if needed and authorized, then inspect dependent features and resulting geometry.

Do not delete and rebuild an entire component to change a hole or thickness. Do not roll history during an analysis-only task. If a setter requires a timeline position, that fact belongs in the modification plan, not an inspection workaround.

For direct/imported designs, inspect supported face/body edit APIs. Do not claim an original sketch parameter exists if the source contains only B-Rep. Explain when an edit changes direct geometry rather than reconstructing design history.

## Before/after evidence

Choose a compact baseline: target identity, relevant parameter expressions, feature health, body/component counts, and requested measurements. After editing, compare the same properties. Record new warnings separately from existing ones. An unrelated pre-existing underconstrained sketch does not authorize a redesign.

See [verification and recovery](verification-and-recovery.md) for partial scripts, undo, and bounded retries.
