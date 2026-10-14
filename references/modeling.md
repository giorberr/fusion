# Parametric modeling

## Turn a request into a buildable model

Define the coordinate convention and controlling dimensions before selecting APIs. Identify the primary profile, axis or path, wall thicknesses, openings, repeated features, interfaces, and separate parts. For an image reference, distinguish observed proportions from known dimensions. A picture does not establish scale, hidden geometry, thread specifications, or tolerances.

Use parametric history for an editable mechanical part unless the user requests another representation or the source is intentionally direct. Preserve existing mode. Creating a new parametric document is different from converting an existing direct model; the latter can alter how edits behave.

Separate stable construction references from finishing geometry. A hole positioned from origin planes or a layout sketch is usually more robust than one positioned from an edge that a later fillet will replace. Keep fillets/chamfers late when that suits intent, but do not impose a universal order when the feature is foundational to another operation.

## Document and component setup

For a new document, discover `adsk.core.Documents.add` and `DocumentTypes.FusionDesignDocumentType`. Create it only as part of the requested deliverable. Record the new document identity and re-read the product. Set parametric mode only on an appropriately new/empty design; never use mode switching as generic error recovery.

For a single part, the root component may be the right owner. For an assembly, use components per logical part. Discover `Occurrences.addNewComponent` and `Matrix3D.create` for a new local component. Recent versions expose design intent distinctions (part/assembly/hybrid); inspect `Design.designIntent` and its valid transitions if component creation is restricted. Do not silently change intent on a populated user model.

Use explicit component objects as owners. Activating a component in the UI is not a substitute for verifying which component receives a sketch or feature.

### Observed native-modeling pitfalls

These behaviors were observed in Fusion 2705.1.30; verify the current model rather than assuming every build behaves identically.

- Derive a sketch's local basis with `sketchToModelSpace`. An origin XZ sketch had local +Y along model -Z; angular construction-plane sketches changed their local axes. The plane's name or angle does not establish the sketch coordinate directions.
- `SketchArcs.addByCenterStartSweep` created a distinct center point even when passed `sketch.originPoint`. Explicitly constrain the returned `centerSketchPoint` coincident to the intended center when that relationship must persist, then inspect `isFullyConstrained`.
- When points share a coordinate, a horizontal/vertical point constraint to an already constrained point can avoid redundant absolute distance dimensions. Inspect existing constraints before adding either.
- A negative-direction extrusion's existing distance expression may be signed. Replacing it with a positive expression can reverse the feature and produce a disconnected body while feature health stays healthy. Preserve direction deliberately and verify actual bounds, solid count, and connectivity.
- A revolve cut in a non-active component failed to find its target until `participantBodies` was explicitly assigned. Set intended participants when the feature supports it; do not depend on active-component visibility.

## Units and parameters

CAD geometry coordinates and real-valued lengths are in centimeters; real-valued angles are radians. This applies even when the document displays mm or degrees. Area is cm² and volume cm³. Use `UnitsManager.convert` for explicit conversions or `evaluateExpression` for valid expressions. Validate expressions with `isValidExpression`; some conversion/expression errors return a sentinel rather than throwing, so inspect the documented behavior.

```python
units = design.unitsManager
x_cm = units.convert(40.0, "mm", "cm")
point = adsk.core.Point3D.create(x_cm, 0, 0)
distance = adsk.core.ValueInput.createByString("4 mm")
thickness = adsk.core.ValueInput.createByString("part_thickness")
```

`ValueInput.createByReal(4)` is four centimeters when a length is expected, not four displayed units. Creating a parameter with real value 4 and unit label `mm` also does not make that value four millimeters. Prefer unit-bearing string expressions.

For dimensions that should be editable, create clear task-specific user parameters. Check `userParameters.itemByName` before adding. Reuse a matching intended parameter; a name collision with a different meaning requires a different name, not silently changing the existing parameter.

```python
parameter = design.userParameters.add(
    "part_thickness", adsk.core.ValueInput.createByString("4 mm"),
    "mm", "Main plate thickness"
)
if parameter is None:
    raise RuntimeError("Could not create the thickness parameter.")
```

This is a construction fragment; run only within an authorized mutation script after collision checks. Driving dimensions and features must reference the parameter expression. Computing a coordinate once from the parameter and never constraining it does not create an enduring parametric relationship.

Edit existing dimensions through their controlling feature/parameter. Names such as `d12` can change between models and do not convey purpose. Resolve ownership and expression before editing. Keep text parameters distinct: they use `Text` and quoted string expressions; use `textValue` for plain text when appropriate. Boolean `ValueInput` is not supported by `UserParameters.add` in the audited API.

## Sketches that remain editable

Discover the specific `Sketches.add`, `SketchCurves`, line/arc/circle/spline collections, `GeometricConstraints`, and `SketchDimensions` members needed.

1. Choose an origin/construction plane or a verified planar face in the correct component context.
2. Create the intended geometry in sketch coordinates. Use model-to-sketch conversion when source points are in model coordinates.
3. Constrain location and relationships: coincident, horizontal/vertical, parallel/perpendicular, tangent, concentric, equal, symmetry, and dimensions as appropriate.
4. Set driving dimension expressions to controlling parameters. Use driven dimensions when measurement rather than constraint is intended.
5. Inspect health, constraint status, and computed profiles. An intentionally open construction sketch need not have an extrusion profile.

Avoid fixing every entity merely to get `isFullyConstrained: true`; that removes intended freedom and can defeat parameter edits. Do not add duplicate constraints to geometry already constrained by a creation helper. Reuse existing `SketchPoint` objects when the API supports them. For example, `addTwoPointRectangle` accepts sketch points or transient points, so an existing origin point can anchor a rectangle.

If bulk sketch creation benefits from deferred computation, read `Sketch.isComputeDeferred` first. Deferring computation is a mutation. Limit it to the creation stage, restore it with `finally`, and verify profiles after it is restored. Never leave computation deferred on a model handed back to the user.

For imported/projected sketches, inspect construction status, coincidence, duplicates, open endpoints, and tiny gaps before assuming a closed profile. Use the current projection API (`project2` in the audited version) rather than copying a retired method blindly. Read its linking behavior; projected geometry can introduce external dependencies.

### Reusable driven-rectangle example

This complete helper shows enduring parameter relationships without relying on implicit rectangle constraints. The caller must first resolve an authorized target component and two positive length user parameters in the same design. It creates a new sketch in that component; it is not an inspection helper. Include it in a script with the normal `run` entry point and document guards.

The helper is API-reviewed and syntax-checked, but its construction and solver behavior were not executed during skill validation. Read the current members before using it on a live model. If it fails after creation starts, inspect the partial sketch before retrying.

```python
import adsk.core
import adsk.fusion

def create_driven_rectangle(component, width_parameter, length_parameter):
    width, length = width_parameter.value, length_parameter.value  # cm
    if width <= 0 or length <= 0:
        raise ValueError("Rectangle dimensions must be positive lengths.")
    sketch = component.sketches.add(component.xYConstructionPlane)
    if sketch is None:
        raise RuntimeError("Could not create rectangle sketch.")
    sketch.name = "Driven rectangle"
    point = adsk.core.Point3D.create
    lines = sketch.sketchCurves.sketchLines
    bottom = lines.addByTwoPoints(sketch.originPoint, point(width, 0, 0))
    if bottom is None:
        raise RuntimeError("Could not create bottom edge.")
    right = lines.addByTwoPoints(bottom.endSketchPoint, point(width, length, 0))
    if right is None:
        raise RuntimeError("Could not create right edge.")
    top = lines.addByTwoPoints(right.endSketchPoint, point(0, length, 0))
    if top is None:
        raise RuntimeError("Could not create top edge.")
    left = lines.addByTwoPoints(top.endSketchPoint, sketch.originPoint)
    if left is None:
        raise RuntimeError("Could not close the rectangle.")
    constraints = sketch.geometricConstraints
    for edge, horizontal in ((bottom, True), (right, False),
                             (top, True), (left, False)):
        relation = (constraints.addHorizontal(edge) if horizontal
                    else constraints.addVertical(edge))
        if relation is None:
            raise RuntimeError("Could not constrain rectangle orientation.")
    orientations = adsk.fusion.DimensionOrientations
    width_dimension = sketch.sketchDimensions.addDistanceDimension(
        bottom.startSketchPoint, bottom.endSketchPoint,
        orientations.HorizontalDimensionOrientation,
        point(width / 2, -length / 5, 0), True
    )
    length_dimension = sketch.sketchDimensions.addDistanceDimension(
        right.startSketchPoint, right.endSketchPoint,
        orientations.VerticalDimensionOrientation,
        point(width * 1.2, length / 2, 0), True
    )
    if width_dimension is None or length_dimension is None:
        raise RuntimeError("Could not create driving dimensions.")
    width_dimension.parameter.expression = width_parameter.name
    length_dimension.parameter.expression = length_parameter.name
    if sketch.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
        raise RuntimeError("Rectangle sketch is not healthy.")
    if not sketch.isFullyConstrained or sketch.profiles.count != 1:
        raise RuntimeError("Expected one fully constrained rectangular region.")
    return sketch
```

The returned sketch has exactly one verified profile, so it can feed the extrusion pattern below. Keep the parameter expressions and resulting dimensions in the verification report. Other profiles need their own geometric and constraint logic; do not force every shape into a rectangle helper.

## Select profiles deliberately

Sketches may contain multiple regions, islands, and nested loops. Select by expected area, centroid, perimeter, loop structure, and source geometry. A ring region is not equivalent to either of its circular disks. Disjoint contours can create multiple bodies. A self-intersecting loop may have unexpected regions.

Using `profiles.item(0)` is acceptable when a freshly created sketch has been verified to contain exactly one desired profile. Otherwise inspect candidates and assert a unique selection. Distinguish single `Profile` from `ObjectCollection` inputs and satisfy coplanarity requirements.

## Feature construction pattern

Use the feature collection's `createInput`, configure the input, then `add`. Read both input and feature documentation. Input setters before creation can differ from setters on an existing feature.

This current-style extrusion fragment assumes `component` and a verified `profile` were resolved, and `part_thickness` exists. It is API-reviewed guidance, not an executed mutation test:

```python
extrudes = component.features.extrudeFeatures
feature_input = extrudes.createInput(
    profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
extent = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString("part_thickness")
)
if not feature_input.setOneSideExtent(
    extent, adsk.fusion.ExtentDirections.PositiveExtentDirection
):
    raise RuntimeError("Could not define extrusion extent.")
feature = extrudes.add(feature_input)
if feature is None:
    raise RuntimeError("Extrusion did not create a feature.")
feature.name = "Base thickness"
```

Verify the current members before use. Extend the fragment with task-specific guards, semantic names, feature/body output checks, and health reporting.

Choose `NewBody`, `Join`, `Cut`, or `Intersect` according to intent. For cuts/joins in multibody contexts, inspect participant-body settings and constrain affected bodies when supported. Do not rely on whatever bodies happen to intersect in the active component. Extent direction follows the sketch normal, not a screen direction. Prefer a to-object or through-all extent when that dependency is intended; a guessed large distance can cut unrelated geometry.

## Recipe map

| Requested shape | Construction approach | Discovery targets and verification |
|---|---|---|
| Plate, bracket, adapter | Parameterized profile, thickness, holes, optional bends/ribs | Sketch dimensions, `ExtrudeFeatures`; dimensions and body count |
| Ring, bushing, stepped shaft | Concentric profiles or revolved section | `RevolveFeatures`, axis context; inner/outer diameters and axial lengths |
| Enclosure | Base solid plus shell, or walls assembled from profiles | `ShellFeatures`, openings and wall direction; wall thickness and remaining faces |
| Rib/gusset | Sketch web with appropriate extent/thickness | Discover rib/web feature support or extrude; joins and load-path geometry |
| Varying cross section | Loft sections and optional rails | `LoftFeatures`, section ordering, seam alignment; twist and continuity |
| Tube along a path | Sweep or pipe with intended section and corner behavior | `SweepFeatures`/pipe support, `Path`; self-intersection and wall thickness |
| Rounded edges | Fillet selected semantic edges | `FilletFeatures` and edge sets; tangent-chain extent and radius feasibility |
| Beveled edges | Chamfer selected edges | `ChamferFeatures`; distance/angle definition and affected edges |
| Repeated holes/features | Pattern the intended feature/body/component | Rectangular/circular pattern collections; axis, quantities, spacing, total extent |
| Mirror | Mirror features/bodies/components around a defined plane | Mirror collection and plane context; handedness and result ownership |
| Split part or cavity | Split/combine with explicit tool/target bodies | `SplitBodyFeatures`, `CombineFeatures`; retained tool bodies and connected volumes |

Feature/member availability changes; these are discovery targets, not a promise that every exact API is installed. Read the advanced-modeling reference when the intended representation requires another route.

## Holes, threads, and patterns

Prefer a hole feature when its semantic parameters matter: simple, counterbore, countersink, tapped, blind, or through. Discover `HoleFeatures` and the applicable input positioning and extent methods. Confirm hole-center reference frame, axis, diameter, depth, tip definition, and countersink/counterbore dimensions independently.

Use thread metadata supplied by the installed thread library. Discover `ThreadDataQuery`, `ThreadInfo`, and `ThreadFeatures`; confirm type, size, designation, class, handedness, internal/external status, and full/partial length. Do not invent an ISO designation or imperial pitch. A modeled thread changes geometry; a cosmetic thread does not. Set and verify `isModeled` according to the deliverable. Do not confuse a helical visual groove with a standards-based thread feature.

Pattern the right entity type. Feature patterns preserve manufacturing intent; component patterns represent repeated parts; body patterns create geometry within an owner. Interpret quantity as the documented total or additional count, and spacing as the documented per-step or extent value. Verify the actual instance count and positions, not only the input fields.

## A complete execution plan for an unfamiliar part

For a parameterized flange with four holes, an agent should:

1. Resolve document/component and units; choose diameters, thickness, hole diameter, and bolt-circle diameter from the user/model.
2. Establish parameters and a reference axis. Create the annular base profile with concentricity and diameter constraints, then extrude the thickness expression.
3. Locate one hole from the bolt-circle definition and orientation. Create the specified hole, then pattern it around the intended axis if that expresses the design.
4. Add verified thread metadata only if threads were requested. Apply justified finishing features to selected edges.
5. Verify annulus diameters, thickness, hole count, center spacing, thread definition, solid/body count, parameter dependencies, health, and a view.

This workflow generalizes by choosing the right feature families and discovering their current contracts. Avoid hardcoding dimensions from an example into the user's new part.
