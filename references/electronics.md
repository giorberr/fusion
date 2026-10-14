# Electronics inspection

## Establish the active design

The structured `fusion_mcp_electronics_read` tool requires an active Electronics document. A mechanical CAD design of a PCB is not automatically a schematic or board document. The audited tool returned `isError: true` with `No active Electronics document.` in a CAD document; this means unavailable context, not an empty board.

Use an existing intended schematic, board, or library document. Opening another document changes context and must fit the requested task. Do not activate a different document during an analysis-only task without that being part of the user's request.

## Discover schemas instead of copying them

List the Fusion MCP's ordinary resources and read `resource://mcp.electronics_entity_types`, then the exact schemas for needed types. The initial catalog contained 50 entity schemas plus that index. Resource-template listing was unsupported.

Use exact returned URIs: multiword types use resource spellings such as `contact_ref`, `device_set`, and `port_net_mapping_entry`. Do not derive the URI by simply lowercasing the class name. Read fields, filterability, allowed operators, units, and relationships from each current schema.

Useful domain routes:

| Question | Start with |
|---|---|
| Design/sheet organization | Schematic, Board, Sheet, Module, ModuleInstance |
| Component/value inventory | Part, Instance, Element, Attribute |
| Logical connectivity | Net, Segment, PinRef, Instance, Pin, Gate |
| Board connectivity | Signal, ContactRef, Contact, Pad, Smd, Via, Wire |
| Copper and rules | NetClass, Layer, PolyPour, PolyShape, PolyCutout |
| Libraries and mappings | Library, DeviceSet, Device, Gate, Symbol, Package, Package3D |
| Population variants | Variant, VariantDef, Technology, Part, Element |
| Existing check messages | Error and the drawing's checked state |
| Hierarchical bus mapping | Port, PortRef, PortNetMappingEntry, Bus, ModuleInstance |

This is task routing, not a substitute for the individual schemas.

## Query shape and pagination

```json
{
  "entity_type":"electronics.Net",
  "object":{
    "fields":["object_id","sheet_object_id","name","net_class_number"],
    "filters":[{"property":"name","op":"eq","value":"GND"}],
    "pagination":{"limit":100,"offset":0}
  }
}
```

Verify those fields against the current schema before use. Omitted fields request all columns. Omitted query options do not guarantee all rows: the audited default page size was 100, maximum 1000. Follow returned `pagination.hasMore` and `nextOffset`; do not fabricate a complete total from the first page. Check errors on every page.

String filters support `eq`, not arbitrary substring, regex, or contains operators. Numeric `lt`/`gt` work only for properties that advertise them. Do not guess filter support from type alone. For unsupported filtering, retrieve the necessary fields with pagination and filter locally, retaining enough relationship context.

## Units and field inconsistencies

Properties marked `document_grid_unit` use the document's active grid unit, reported in the response's `coordinate_unit`. Filter values for these fields must use that same unit. Grid units can be mm, mil, inch, or mic. Do not apply CAD's internal-centimeter convention to electronics rows.

Some descriptions still say Eagle/internal units despite the schema's explicit grid-unit contract. Preserve raw value and returned unit, resolve conflicts against actual response/document state, and verify a known dimension before using ambiguous data for a critical dimensional decision. Do not silently rescale every field from descriptive wording.

Specific observed distinctions:

- `Schematic.objectId` uses camel case; most types use `object_id`.
- `Hole.diameter` is an encoded drill-size index; `Hole.drill` is the dimensional drill field.
- Angles are commonly documented in degrees, independently of coordinate units.
- Boolean-like flags are often integers; some are bitmasks. Decode from the schema rather than treating every nonzero flag as the same meaning.
- `Library.library_object_id` is a string reference/URN in its schema, while many other relationship IDs are integers.
- `PortNetMappingEntry` advertises only internal/external bus specifications with no object ID or filterable link. Do not invent a join key absent from the response/schema.

## Connectivity and quantities

Join through actual IDs and relationships. Names and screen positions are insufficient to prove a connection.

For schematic connectivity, follow the available Net -> Segment -> PinRef links, then resolve instance/part/pin/gate context. A library pin is a definition, not automatically a placed connected pin. Multipart devices can have multiple placed gate instances; counting Instance rows as parts can overcount a BOM.

For a board, follow Signal and ContactRef/contact relationships and distinguish a package template from an Element placement. A reference designator string alone may be insufficient in hierarchical designs. Package/library coordinates differ from placed board coordinates; account for placement, rotation, and mirroring using documented semantics.

For bus/hierarchical designs, inspect internal/external mappings and module instances. Do not equate same-named nets across scopes without checking hierarchy. Preserve unresolved or ambiguous connectivity in the report rather than fabricating a flattened netlist.

For a BOM, group actual parts/elements with value, device/package, relevant attributes, and variant population. Report whether quantities refer to the selected assembly variant. An unpopulated part can remain present in the design.

## Existing ERC/DRC information

`electronics.Error` describes stored check entries. Its schema distinguishes states (active, processed, approved) and types (warning, failure, consistency, airwire). Use the actual mappings from the current schema. A hidden airwire is not proof of routing completion.

Reading errors does not rerun a check. The drawing's checked flag does not prove the current design has a fresh comprehensive check. Report the check state and timing if available; do not say "DRC passed" based only on an empty paginated error result.

## Modification boundary

The audited electronics tool is read-only. No electronics create/update route was exposed. General Fusion script execution does not by itself prove schematic/board editing support. Discover a documented, available API before proposing electronics modifications; do not invent `adsk.electronics` APIs or EAGLE text-command syntax.

If editing requires a supported UI workflow and such tooling is available, continue within the user's request using its applicable instructions. If no suitable path exists, complete inspection and give the exact unsupported edit. Do not convert a PCB-edit request into an unrelated mechanical model silently.

The initial audit read every advertised electronics schema but could not inspect populated Electronics rows. Treat data retrieval, joins, and units as requiring validation in the actual document.
