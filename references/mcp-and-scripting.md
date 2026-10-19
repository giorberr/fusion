# MCP operation and scripting

## Routing

Use the installed schemas as authority. The audited tools expose:

| Tool | Route | Purpose |
|---|---|---|
| `fusion_mcp_read` | `apiDocumentation` | API classes, members, descriptions, signatures |
| `fusion_mcp_read` | `document`: `open`, `recent`, `search` | List or locate documents; `open` here only lists |
| `fusion_mcp_read` | `projects`, `activeCommand`, `screenshot`, `licensing` | Hub, command, view, relevant entitlement inspection |
| `fusion_mcp_execute` | `script` | Python API inspection or modeling |
| `fusion_mcp_execute` | `document`: `open`, `close`, `save` | Document actions |
| `fusion_mcp_execute` | `editImage`, `previewImage`, `generatePowerpoint`, `purchase` | Specialized workflows; read current instructions first |
| `fusion_mcp_electronics_read` | `entity_type` | Structured electronics queries |
| `fusion_mcp_update` | `undo`, `redo` | Change transaction history |

The audited read enum has no CAD `bodies`, `parameters`, `measure`, or `materialLibraries` routes despite broader prose in its description. Use Python APIs. Never invent a route from old examples or general wording.

In clients with the functions orchestrator, discover deferred tools by filtering `ALL_TOOLS` for `mcp__fusion` and invoke those names through `tools`. Other clients expose MCP tools directly. Adapt to the current client's tool transport.

## Initial reads

```json
{"queryType":"document","operation":"open"}
```

```json
{"queryType":"activeCommand"}
```

Independent reads can be batched. Finish target discovery before dependent scripts. Active-command fields may be at the top level. Treat `activeCommand: null` or an explicitly default command as no dialog; do not assume an example's wrapper shape.

Read-only scripts are documented to work during dialogs; mutation scripts are not. Let the user finish or close a blocking command. Do not cancel it or use internal text commands to bypass the block. Continue independent inspection when useful.

## API discovery

Find a class, then read exact members:

```json
{"queryType":"apiDocumentation","apiCategory":"class","filter":"adsk.fusion.ExtrudeFeatures","searchPattern":"^ExtrudeFeatures$"}
```

```json
{"queryType":"apiDocumentation","apiCategory":"member","filter":"adsk.fusion.ExtrudeFeatures","searchPattern":"^createInput$"}
```

For an unknown method name, search descriptions in a likely class:

```json
{"queryType":"apiDocumentation","apiCategory":"description","filter":"adsk.fusion.Occurrence","searchPattern":"orientation|position"}
```

- Class summaries provide short descriptions; member queries expose detailed preconditions.
- Six exact known classes or methods returned only five during the audit, without pagination or a truncation flag. Split searches into at most five expected symbols, preferably one critical symbol, and verify every expected match.
- `success: true` with no classes/members means no match. It does not prove the product lacks a capability.
- Query base classes for inherited properties: `Component` -> `BaseComponent`, `UserParameter` -> `Parameter`, `Design` -> `Product`.
- Enums can be found using the class category. Read their attributes for exact constant names.
- A `(*args)` signature is incomplete by itself. Read the full description; use current official Autodesk documentation if the MCP is insufficient.
- Generated signatures can disagree with the member prose. A forward test found `DistanceExtentDefinition.create` advertising `ValueInput` as its return type while its description correctly specified `DistanceExtentDefinition`. Resolve such conflicts against the exact member, returned class, and official documentation; check the actual returned object before using it to add a feature.
- Prefer supported APIs to preview, retired, or unofficial calls. Do not use `internalCommand` or undocumented text commands merely because they appear in discovery.
- Namespace-wide dumps hit the result limit and wrapper classes; they do not inventory the API.

If web research is necessary, use official Autodesk Fusion API documentation and samples. Check old samples for retired calls. Reconcile them against the installed member contract.

## Documents and identity

```json
{"queryType":"document","operation":"search","name":"requested name fragment","project":"project name or ID returned by projects"}
```

Use a returned file ID for authorized document opening, then read the active document again. `read` document `open` lists; `execute` document `open` changes the active document.

Observed issue: an open-document response's encoded `parentProjectId` was rejected by document search. The project name and the ID from `queryType: "projects"` worked. Obtain search scope there; do not decode IDs speculatively.

Unsaved documents may have no cloud ID. Guard saved documents by observed `dataFile.id` when available. For unsaved documents combine observed name, `creationId`, and current context. Creation IDs can be shared by copied documents, so they are not globally unique identity proof. Resolve remaining ambiguity before mutation.

Recheck active document before meaningful changes. Separate calls may be interrupted by user activity. A model name left in a sample is never a valid guard for another task.

## Script contract

```python
import json
import adsk.core
import adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    document = app.activeDocument
    if document is None:
        raise RuntimeError("No active Fusion document.")
    design = adsk.fusion.Design.cast(
        document.products.itemByProductType("DesignProductType")
    )
    if design is None:
        raise RuntimeError("The document has no Design product.")
    print(json.dumps({"document": document.name,
                      "units": design.unitsManager.defaultLengthUnits,
                      "components": design.allComponents.count}))
```

Submit the actual complete source in `object.script`:

```json
{"featureType":"script","object":{"readOnly":true,"script":"the complete Python source"}}
```

The final string above illustrates the shape; replace it with source, not a path. The MCP calls `run`; do not invoke it at module scope. Do not assume Python globals or objects from earlier executions persist. Include imports and helper definitions in each script.

Use `readOnly: true` only for true inspection. Creating, setting, deleting, recomputing, exporting, saving, moving the timeline, selecting, changing camera, or changing workspace requires an appropriate mutating context. `Application.executeTextCommand` is excluded from read-only enforcement and must not be used in read-only scripts.

Let exceptions propagate. Do not copy the common sample wrapper `try/except: ui.messageBox(...)`; it hides errors from the MCP and interrupts the user. A `finally` block may restore task-owned temporary state during an authorized edit while allowing the original exception to escape. Avoid broad exception suppression for optional fields; instead inspect documented capabilities and omit unsupported branches explicitly.

Build and validate feature input objects before adding features. Check false/null returns. Print names, expressions, counts, measurements with units, relevant tokens, and health. Do not print wrapper objects, secrets, entire material libraries, or huge topology dumps.

## Slow reads and request timeouts

A short script is not necessarily a fast request. On 2026-10-19, listing names and `component.partNumber` for 136 top-level occurrences took 79 seconds end to end. Listing all 136 names without part numbers took 0.05 seconds. Five indexed metadata rows took 2.54 seconds inside Fusion but 38.8 seconds end to end during overlapping requests. The timings identify expensive metadata reads in that session; they are not universal API costs or proof of a configured timeout threshold.

When diagnosing a stall, compare a minimal script, collection count, names-only inventory, and a small metadata page. Use `time.perf_counter()` inside the script and separately measure the full tool request so API execution is not confused with queue/bridge/response overhead. A small output can still take a long time to produce.

For a known target, look it up directly and verify its identity. For broader discovery, list names/paths first, then retrieve needed part numbers. Paginate metadata reads; for a complete BOM, read each reused component definition's metadata once and join it back to its occurrences using verified component identity. Replacing a comprehension with an indexed loop alone does not remove expensive property reads. Avoid overlapping long script requests when measuring latency.

## Results

Keep image content as images; never print base64 into chat. Parse JSON text when appropriate. Check MCP `isError` and decoded `success`/`error`: a fulfilled call can still report failure. Script JSON output was observed as another JSON string inside `message`; parse that second level if the script intentionally printed one JSON object. If the script prints multiple stage records, use consistent JSON Lines and parse each line; the combined message is not one JSON object. One final JSON object is simplest for ordinary inspection.

Do not interpret an electronics error as zero components, an empty documentation match as a complete capability inventory, or a script success message as a verified model.

## Observations to recheck when relevant

| Initial audit observation | Working approach |
|---|---|
| Documentation limits matches to five | Exact symbols and class filters |
| Open-document project ID may not work for search | Use projects-list ID or project name |
| Inherited properties omitted | Query base class and member |
| Resource-template listing unsupported | Ordinary resource listing and exact returned URI |
| Screenshot has image content without media URLs | Inspect actual attachments; invent no URLs |
| Required PowerPoint schema absent | Recheck; use an available presentation workflow if absent |
| Unsaved document lacks ID | Observed context and appropriate guards |

These observations may change with versions. Do not repeatedly probe them during unrelated tasks. Recheck when the task depends on them or the environment changes.
