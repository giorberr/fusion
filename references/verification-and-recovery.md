# Verification and recovery

## Choose evidence that tests the request

Check the intended outcome, not a mirror of the implementation. Do not equate a successful API return with a correct design. Scale verification to the change: a label edit does not require a full engineering audit; a hole-pattern edit needs count, location, size, and dependent-feature checks.

| Work performed | Useful independent evidence |
|---|---|
| Create solid part | Solid/body count, dimensions, volume plausibility, feature health, view |
| Change thickness | Controlling expression, actual surface separation, dependent feature health |
| Hole pattern | Actual hole count/centers/diameters and intended axis/spacing |
| Thread feature | Standard/designation/class, handedness, extent, modeled/cosmetic status |
| Shell or surface-to-solid | Closedness, wall thickness, openings, unwanted disconnected bodies |
| Assembly placement | Occurrence paths, transformed positions, joints/limits, relevant interference |
| Parameterization | Driving expressions and dependencies; controlled perturbation only when authorized and fully restored |
| Export | File existence/format/scope/units, relevant geometry validation |
| CAM | Intended setup, valid completed toolpaths, actual simulation/post status |
| Electronics report | Complete pagination, correct joins/units/variant, check freshness limitations |

Do not perform parameter perturbation as part of read-only analysis. Read expressions/dependencies instead and state what they establish.

## Baselines

Before a meaningful existing-model edit, record identity, timeline position, relevant counts, parameters, health, and measurements. A baseline is a read, not an automatic save checkpoint. The document may already contain user changes; preserve them.

After the stage, read the same properties. Separate pre-existing warnings from newly introduced ones. Verify the target stayed the same and no unrelated bodies/components were unintentionally created, joined, cut, or removed. Retain enough task data to identify only the objects created by the stage if cleanup is necessary.

## Health interpretation

The audited `FeatureHealthStates` includes healthy, warning, error, suppressed, rolled back, and unknown. Read `errorOrWarningMessage` for warnings/errors. Unknown can occur for timeline groups or position snapshots; it is not automatically a failed feature.

`Sketch.isFullyConstrained` is a separate property. A healthy sketch can be underconstrained intentionally. Conversely, all dimensions being present does not prove the constraint system solved successfully. Do not change unrelated sketch constraints just to make a general report look cleaner.

In a direct design, the parametric timeline may not be available. Inspect body geometry and supported direct features instead. Do not enable history merely to obtain a familiar health report.

## When a script fails

1. Preserve the exact error/traceback and determine whether failure occurred before or after mutation began.
2. Read the active document, command, relevant objects, and timeline. Scripts may have partially succeeded; never assume automatic rollback.
3. Compare with the baseline and identify completed task-owned steps.
4. Choose a targeted correction, continuation, or rollback based on actual state. Do not rerun the complete creation script blindly.
5. Read the failing API's current member contract and correct the specific issue. Verify the result of the corrected stage.

Do not assume one script equals one undo transaction. The MCP update tool undoes the most recent committed transaction; its scope is not proven to match an arbitrary script. If the user interacted between calls, the newest operation may be theirs.

Undo/redo must be deliberate and within the user's requested task. Read `canUndo`/`canRedo` in responses and stop on failure. Never issue a chain of undo calls in the hope of reaching the original state. For targeted cleanup, delete only clearly identified task-created entities whose dependency effects are understood.

## Typical failures and diagnostic routes

| Failure | Inspect before changing anything else |
|---|---|
| No Design product | Document product types; a drawing/CAM context may not be a CAD Design |
| Command blocks execution | `activeCommand`; keep user dialog state intact |
| Wrong object/null selection | Document/component context, token resolution, candidate count |
| No closed profile | Sketch loops, construction curves, duplicate curves, gaps, compute state |
| Overconstraint | Existing constraints and driving/driven dimensions; remove only the mistaken task constraint |
| Cut misses body | Sketch normal, extent direction, frame, body participants |
| Join fails | Actual overlap/contact and solid/surface status |
| Fillet/chamfer fails | Selected edges, tangent chains, neighboring small faces, requested radius/distance |
| Shell/thicken fails | Self-intersections, small radii, wall direction, open faces |
| Setter requires rollback | Exact feature member's timeline precondition |
| API attribute missing | Exact symbol, inheritance, supported replacement, preview/version availability |
| Project not found | ID source; projects-list ID or unambiguous name |
| Toolpath incomplete | Generation state, invalid operations, selections, tool/setup inputs |
| Electronics unavailable | Active Electronics document, not row count |

Do not reduce requested dimensions, simplify geometry, change manufacturing intent, or convert representation silently to make an operation succeed. If a legitimate alternative is needed, explain the effect on the requested result and resolve it with the user when material.

## Bounded retries

A retry should follow new evidence or a specific correction. If the same failure recurs with the same cause, stop repeating that approach and investigate a different supported path. If no path exists without missing user input or capability, finish independent work and report the concrete blocker. Do not introduce arbitrary confirmation steps for routine repairs already within scope.

## Recompute and temporary state

Read the relevant compute contract. `Design.computeAll` forces recomputation and is a mutation, not an inspection read. Use it when required by the authorized edit, then inspect health. Do not call it to conceal warnings without understanding their source.

Restore only task-owned temporary state, such as deferred sketch computation or an intentionally moved timeline marker. A `finally` block can help during modification scripts, but must not swallow the original error. Avoid a cleanup failure obscuring the first failure. Re-read the actual state afterward if the script did not finish.

## Completion language

Report the concrete result and checks. Distinguish measured facts from visual assessment and assumptions. State whether save/export occurred and whether any required task portion remains unsupported. Do not claim an entire API family is tested because one read-only example worked, or describe a model as production-ready solely because its timeline is healthy.
