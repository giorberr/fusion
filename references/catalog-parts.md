# Catalog parts and assemblies

Use this guide when the user requests purchased components, a stock framing system, supplier CAD, or a parts list for assembly.

## Select purchased interfaces before custom geometry

Treat the user's sourcing and fabrication requirements as design inputs. When they request off-the-shelf parts, establish the layout, select actual catalog components, and verify their interfaces before detailing adapters. Do not finish a custom mechanism and then give its parts supplier-like names.

Use the requested supplier first. Prefer stock lengths, matching framing series, and included fastening kits when those meet the task. Check alternatives before introducing a fabricated part. Explain each necessary custom part by the interface it connects, and honor the user's allowed fabrication process and material thickness. A blanket preference from one project is not a default for other users.

Verify critical specifications from current supplier data: actual orderable size, travel, mounting pattern, thread and engagement depth, clearance envelope, load rating, power requirements, and included accessories. A family page or nominal product name is not sufficient evidence for a mating interface. Separate confirmed selections from provisional candidates that depend on a sample test or unfinished subsystem.

## Supplier CAD and traceability

Fusion offers an Insert McMaster-Carr Component workflow in supported installations; discover its current availability rather than assuming that UI command has a callable Python equivalent. If direct insertion is unavailable, use genuine supplier STEP files through the supported import API. If the files cannot be retrieved, provide exact part numbers, quantities, and links for user import; identify any layout placeholders explicitly.

Keep the supplier source file and identify the selected variant. Set the component part number to the actual purchasable SKU and record its supplier/link and assembly role. Preserve the supplier geometry unless modification is necessary and explicitly included in the fabrication plan.

Inspect imported structure before counting or positioning it. One STEP may contain a carriage, housing, controller, mounting hardware, and several solids. Distinguish purchased assemblies from their included items so a controller supplied with an actuator is not ordered twice. Verify moved or separated accessory bodies against the source geometry and assembly context.

Repeated occurrences share their component definition. Use that intentionally for identical parts. An independently movable subassembly member needs the appropriate occurrence/proxy and motion relationship; renaming or copying an import alone does not establish either.

## Fit and movement checks

Lay out the mechanism using actual mounting datums and usable travel, including stem, fastener, cable, and actuator-body envelopes. Keep adjustment parameters separate from fixed catalog geometry. Check the requested adjustment extremes as well as nominal size when they alter interfaces or clearances.

Check relevant operating positions with actual solids. Record any supplier fasteners intentionally excluded from interference analysis because threaded fits overlap in CAD; retain the structural casting and check external clearance. Do not describe a few clear poses as continuous collision-free motion, a constrained mechanism, or a validated interaction with flexible material.

For fixed purchased members, pinning can prevent ordinary occurrence dragging. For intended motion, use appropriate joints and limits when supported. An assembly positioned by transforms or a pose script remains an explicitly posed assembly until its mechanical relationships are constrained and verified.

## Parts list and purchasing handoff

List assembly quantities as individual pieces, and separately record purchase units, pack sizes, and purchased totals. For example, 14 required screws sold in packs of 50 means one purchase unit, not 14 packs. Use `ceil(required pieces / pieces per purchase unit)` where no other minimum-order rule applies. Included bracket fasteners do not need duplicate line items.

For McMaster, a catalog URL can combine a family number and a selected SKU with a hyphen. Do not paste that composite URL identifier into bulk order entry: it was observed to create two incomplete lines. Use the actual SKU verified by the catalog/cart, then check its description, selected length, quantity, and purchase unit.

Resolve generic fastener descriptions to actual orderable SKUs before calling a cart complete. Keep custom fabrication, provisional vacuum/electrical items, and unresolved hardware visible as separate scope. Verify the cart against the parts list after pack conversion and retain a plain part-number/quantity bulk-entry backup. An anonymous browser cart is session-bound; a generic orders-page URL is not a portable saved-cart link. Creating a cart does not place an order.
